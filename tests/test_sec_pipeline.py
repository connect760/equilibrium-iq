"""Tests for the SEC pipeline. Offline tests use SYNTHETIC data (tests/fixtures/synthetic) and a local
HTTP server; the `live` tests hit the real SEC API and run only with SEC_LIVE=1."""
import gzip
import http.server
import json
import os
import sqlite3
import threading
from pathlib import Path

import pytest

import sec_fixture as SYN
from celi.sec import bridge
from celi.sec.client import (RawStore, SecClient, SecError, archive_url, cik10, companyfacts_url, load_user_agent,
                             submissions_url, validate_user_agent)
from celi.sec.facts import FactIndex, UnitError, fiscal_year_ends, normalize_unit, parse_companyfacts, to_millions
from celi.sec.metrics import compute_metrics, summary
from celi.sec.registry import IdentityError, check_identity, company_profile, filings_table, pages_needed
from celi.sec.statements import ANCHORS, annual_history
from celi.sec import store as st

UA = "Test Org test@example.org"
ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ local SEC stand-in
class Handler(http.server.BaseHTTPRequestHandler):
    seen = []
    plan = {}

    def do_GET(self):
        Handler.seen.append({"path": self.path, "ua": self.headers.get("User-Agent")})
        steps = Handler.plan.get(self.path, [(200, b"{}")])
        code, body = steps.pop(0) if len(steps) > 1 else steps[0]
        self.send_response(code)
        if code == 429:
            self.send_header("Retry-After", "0")
        gz = self.path.endswith("gz")
        if gz:
            body = gzip.compress(body)
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture
def server():
    Handler.seen, Handler.plan = [], {}
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def client(tmp_path, **kw):
    return SecClient(UA, RawStore(tmp_path / "raw"), sleep=lambda s: None, **kw)


# ------------------------------------------------------------------ SEC API retrieval
def test_user_agent_required():
    with pytest.raises(SecError):
        validate_user_agent("python-urllib")
    with pytest.raises(SecError):
        SecClient("", RawStore("/tmp/x"))
    assert validate_user_agent(UA) == UA


@pytest.mark.skipif(not (os.environ.get("SEC_USER_AGENT") or (ROOT / "config" / "sec_user_agent.txt").exists()), reason="no SEC User-Agent configured here")
def test_configured_user_agent_is_valid():
    ua = load_user_agent(ROOT)
    assert "@" in ua and ua.split()[0]


def test_request_sends_user_agent_and_stores_body(server, tmp_path):
    Handler.plan["/a"] = [(200, b'{"cik": 1}')]
    c = client(tmp_path)
    data, rec = c.get_json(server + "/a", "test")
    assert data == {"cik": 1} and rec["status"] == 200 and rec["user_agent"] == UA
    assert Handler.seen[0]["ua"] == UA
    assert c.store.read(rec) == b'{"cik": 1}'


def test_gzip_responses_are_decoded(server, tmp_path):
    Handler.plan["/x.gz"] = [(200, b'{"ok": true}')]
    data, _ = client(tmp_path).get_json(server + "/x.gz", "test")
    assert data == {"ok": True}


def test_retry_on_429_then_success(server, tmp_path):
    Handler.plan["/r"] = [(429, b""), (503, b""), (200, b'{"n": 2}')]
    data, _ = client(tmp_path).get_json(server + "/r", "test")
    assert data == {"n": 2} and len(Handler.seen) == 3


def test_404_raises(server, tmp_path):
    Handler.plan["/missing"] = [(404, b"")]
    with pytest.raises(SecError, match="404"):
        client(tmp_path).get(server + "/missing", "test")


def test_throttle_never_exceeds_rate():
    t = [0.0]
    waits = []
    c = SecClient(UA, RawStore("/tmp/throttle"), max_rps=5, clock=lambda: t[0], sleep=lambda s: (waits.append(s), t.__setitem__(0, t[0] + s)))
    for _ in range(3):
        c._throttle()
    assert waits and all(abs(w - 0.2) < 1e-9 for w in waits)


def test_raw_store_never_overwrites(server, tmp_path):
    c = client(tmp_path)
    Handler.plan["/v"] = [(200, b'{"v": 1}')]
    r1 = c.get(server + "/v", "t")
    Handler.plan["/v"] = [(200, b'{"v": 2}')]
    r2 = c.get(server + "/v", "t")
    assert r1["sha256"] != r2["sha256"]
    assert c.store.read(r1) == b'{"v": 1}' and c.store.read(r2) == b'{"v": 2}'
    assert len([r for r in c.store.records() if r["url"].endswith("/v")]) == 2


def test_tampered_object_detected(server, tmp_path):
    Handler.plan["/t"] = [(200, b'{"a": 1}')]
    c = client(tmp_path)
    rec = c.get(server + "/t", "t")
    (c.store.root / rec["object"]).write_bytes(gzip.compress(b'{"a": 2}'))
    with pytest.raises(SecError, match="Integrity"):
        c.store.read(rec)


# ------------------------------------------------------------------ CIK matching
def test_cik_padding_and_urls():
    assert cik10(789019) == "0000789019" and cik10("CIK0001045810") == "0001045810"
    assert companyfacts_url(19617) == "https://data.sec.gov/api/xbrl/companyfacts/CIK0000019617.json"
    assert submissions_url("320193") == "https://data.sec.gov/submissions/CIK0000320193.json"
    assert archive_url(1018724, "0001018724-24-000008", "amzn.htm") == "https://www.sec.gov/Archives/edgar/data/1018724/000101872424000008/amzn.htm"
    for bad in ("", "abc", "0", "12345678901", "-5"):
        with pytest.raises(ValueError):
            cik10(bad)


def test_identity_check():
    check_identity(SYN.CIK, SYN.companyfacts(), "SYNTHETIC")
    with pytest.raises(IdentityError):
        check_identity(1234, SYN.companyfacts())
    with pytest.raises(IdentityError):
        check_identity(SYN.CIK, SYN.companyfacts(), "MICROSOFT")


def test_registry_and_model_detection():
    p = company_profile(SYN.submissions(), "corporate")
    assert p["cik"] == "0009999999" and not p["model_conflict"]
    bank = dict(SYN.submissions(), sic="6021")
    assert company_profile(bank, "corporate")["model_conflict"]


# ------------------------------------------------------------------ accession registry
def test_filings_table_and_amendments():
    rows = filings_table(SYN.CIK, SYN.submissions())
    by = {r["accession"]: r for r in rows}
    a = by["0009999999-24-000077"]
    assert a["is_amendment"] and a["base_form"] == "10-K" and a["url_primary"].endswith("/000999999924000077/ka2023.htm")
    assert by["0009999999-24-000099"]["report_date"] is None  # empty string -> None, not a fake date
    assert [r["filing_date"] for r in rows] == sorted(r["filing_date"] for r in rows)
    assert pages_needed(SYN.submissions(), "2015-01-01") == ["CIK0009999999-submissions-002.json"]


# ------------------------------------------------------------------ XBRL tag mapping
def hist(asof="2026-03-01"):
    return annual_history(FactIndex(parse_companyfacts(SYN.companyfacts())), "corporate", asof)


def test_tag_fallback_per_period():
    h = hist()
    rev = h["items"]["revenue"]
    assert rev["2021-12-31"].concept == "SalesRevenueNet" and rev["2025-12-31"].concept == "Revenues"


# ------------------------------------------------------------------ reporting-period selection
def test_fiscal_years_use_period_end_not_fy_field():
    idx = FactIndex(parse_companyfacts(SYN.companyfacts()))
    ends = fiscal_year_ends(idx, "2026-03-01", ANCHORS)
    assert ends == ["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31"]  # 2020 is only a comparative, never a 10-K's own year


def test_quarterly_values_never_used_for_annual():
    idx = FactIndex(parse_companyfacts(SYN.companyfacts()))
    assert idx.select("Revenues", "2025-03-31", "2026-03-01", flow=True) is None


def test_52_53_week_year_accepted_but_half_year_rejected():
    cf = {"cik": 1, "facts": {"us-gaap": {"Revenues": {"units": {"USD": [
        {"val": 10, "start": "2023-10-01", "end": "2024-09-28", "filed": "2024-11-01", "accn": "a", "form": "10-K", "fp": "FY"},
        {"val": 5, "start": "2024-04-01", "end": "2024-09-28", "filed": "2024-11-01", "accn": "a", "form": "10-K", "fp": "FY"}]}}}}}
    s = FactIndex(parse_companyfacts(cf)).select("Revenues", "2024-09-28", "2025-01-01", flow=True)
    assert s.value == 10


# ------------------------------------------------------------------ units
def test_unit_normalisation():
    assert normalize_unit("USD", "monetary") == "USD"
    with pytest.raises(UnitError, match="no FX"):
        normalize_unit("EUR", "monetary")
    with pytest.raises(UnitError):
        normalize_unit("shares", "monetary")
    assert to_millions(1_500_000) == 1.5 and to_millions(None) is None


def test_foreign_currency_fact_is_not_converted():
    h = hist()
    assert all(v is None for v in h["items"]["rnd"].values())  # synthetic R&D is EUR-only


def test_per_share_kept_separate():
    h = hist()
    assert h["items"]["diluted_eps"]["2025-12-31"].value == 2.2 and h["items"]["diluted_eps"]["2025-12-31"].unit == "USD/shares"


# ------------------------------------------------------------------ filing-date filtering (point in time)
def test_no_future_filings_leak():
    h = hist("2023-06-30")
    assert h["periods"][-1] == "2022-12-31"
    assert "2023-12-31" not in h["items"]["revenue"]
    assert hist("2024-02-09")["periods"][-1] == "2022-12-31"  # FY2023 10-K filed 2024-02-10
    assert hist("2024-02-10")["periods"][-1] == "2023-12-31"


def test_value_as_known_on_date():
    idx = FactIndex(parse_companyfacts(SYN.companyfacts()))
    assert idx.select("Revenues", "2023-12-31", "2024-02-09", flow=True) is None
    assert idx.select("Revenues", "2023-12-31", "2024-03-01", flow=True).value == 1200
    assert idx.select("Revenues", "2023-12-31", "2024-06-15", flow=True).value == 1150


# ------------------------------------------------------------------ amendments & restatements
def test_amendment_restates_without_erasing_original():
    idx = FactIndex(parse_companyfacts(SYN.companyfacts()))
    before = idx.select("Revenues", "2023-12-31", "2024-06-14", flow=True)
    after = idx.select("Revenues", "2023-12-31", "2024-06-15", flow=True)
    assert before.value == 1200 and not before.restated
    assert after.value == 1150 and after.amended and after.restated
    assert after.original_value == 1200 and after.original_accession == "0009999999-24-000001"
    later = idx.select("Revenues", "2023-12-31", "2026-03-01", flow=True)
    assert later.value == 1150 and not later.amended and later.restated and later.versions_visible == 3


def test_database_is_append_only(tmp_path):
    db = st.connect(tmp_path / "e.sqlite")
    facts = parse_companyfacts(SYN.companyfacts())
    n = st.add_facts(db, "0009999999", facts, "sha")
    assert n > 0 and st.add_facts(db, "0009999999", facts, "sha") == 0  # idempotent
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE facts SET value='1' WHERE concept='Revenues'")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("DELETE FROM facts")
    vals = {r[0] for r in db.execute("SELECT value FROM facts WHERE concept='Revenues' AND \"end\"='2023-12-31'")}
    assert vals == {"1200", "1150"}  # both versions kept


# ------------------------------------------------------------------ missing data
def test_missing_is_not_zero():
    h = hist()
    assert h["items"]["interest_expense"]["2024-12-31"] is None
    assert h["items"]["net_income"]["2023-12-31"].value == 0  # a reported zero stays zero
    m = {(x["metric"], x["period_end"]): x for x in compute_metrics(h)}
    ic = m[("interest_cover", "2024-12-31")]
    assert ic["status"] == "missing_input" and ic["value"] is None and ic["missing"] == ["interest_expense"]
    assert m[("net_margin", "2023-12-31")]["value"] == 0.0 and m[("net_margin", "2023-12-31")]["status"] == "computed"


def test_untagged_debt_component_flagged_not_zeroed():
    m = {(x["metric"], x["period_end"]): x for x in compute_metrics(hist())}
    td = m[("total_debt", "2025-12-31")]
    assert td["status"] == "computed_partial" and set(td["missing"]) == {"commercial_paper", "short_term_borrowings"}


# ------------------------------------------------------------------ formulas & reproducibility
def test_formula_values():
    m = {(x["metric"], x["period_end"]): x["value"] for x in compute_metrics(hist())}
    assert m[("revenue_growth", "2025-12-31")] == pytest.approx(1500 / 1300 - 1)
    assert m[("operating_margin", "2025-12-31")] == pytest.approx(0.2)
    assert m[("free_cash_flow", "2025-12-31")] == 240
    assert m[("net_debt_to_ebitda", "2025-12-31")] == pytest.approx((340 + 20 - 180) / 340)
    assert m[("return_on_invested_capital", "2025-12-31")] == pytest.approx(300 * (1 - 56 / 280) / (1200 + 360 - 180))
    assert m[("revenue_growth", "2024-12-31")] == pytest.approx(1300 / 1150 - 1)  # uses the restated FY2023 figure as known today


def test_reproducible():
    a, b = compute_metrics(hist()), compute_metrics(hist())
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ------------------------------------------------------------------ bank vs corporate separation, CELI integration
def test_bank_and_corporate_separate():
    hb = annual_history(FactIndex(parse_companyfacts(SYN.companyfacts())), "bank", "2026-03-01")
    names = {m["metric"] for m in compute_metrics(hb)}
    assert "free_cash_flow" not in names and "return_on_invested_capital" not in names and "efficiency_ratio" in names
    corp = {m["metric"] for m in compute_metrics(hist())}
    assert "efficiency_ratio" not in corp and "deposits_to_assets" not in corp
    st_b = bridge.indicator_status("bank", compute_metrics(hb))
    assert st_b["FCF_DUR"]["status"] == "not_applicable"


def test_engine_gives_no_score_without_calibrated_scales():
    h = hist()
    s = bridge.indicator_status("corporate", compute_metrics(h))
    assert not bridge.SCALES
    assert s["ROIC_5Y"]["status"] == "evidence_available_not_scored" and s["GOV_CONC"]["status"] == "unsupported_by_sec_xbrl"
    r = bridge.run_engine("corporate", "2026-03-01", s)
    assert r["status"] == "insufficient" and not r["eligible"]


def test_synthetic_data_refused_in_real_assessment():
    with pytest.raises(bridge.SyntheticDataError):
        bridge.assert_real(SYN.companyfacts())


def test_summary_descriptive_only():
    h = hist()
    s = summary(h, compute_metrics(h))
    assert s["years_in_window"] == 5 and 0 <= s["worst_revenue_drawdown"] < 0.1


# ------------------------------------------------------------------ live SEC (GitHub Action)
live = pytest.mark.skipif(os.environ.get("SEC_LIVE") != "1", reason="live SEC test: set SEC_LIVE=1")


@pytest.mark.live
@live
def test_live_sec_submissions_and_companyfacts(tmp_path):
    c = SecClient(load_user_agent(ROOT), RawStore(tmp_path / "raw"))
    sub, _ = c.get_json(submissions_url(789019), "live")
    check_identity(789019, sub, "MICROSOFT")
    cf, rec = c.get_json(companyfacts_url(789019), "live")
    check_identity(789019, cf, "MICROSOFT")
    h = annual_history(FactIndex(parse_companyfacts(cf)), "corporate", "2026-11-13")
    assert len(h["periods"]) >= 5 and h["items"]["revenue"][h["periods"][-1]].value > 0


# ------------------------------------------------------------------ end-to-end (local stand-in for SEC, synthetic payloads)
def test_end_to_end_fetch_process_reports(server, tmp_path, monkeypatch):
    import celi.sec.client as C
    from celi.sec import pipeline
    root = tmp_path / "proj"
    (root / "config").mkdir(parents=True)
    (root / "config" / "companies.json").write_text(json.dumps({"companies": [{"cik": str(SYN.CIK), "ticker": "SYNT", "expect": "SYNTHETIC", "model": "corporate"}]}))
    monkeypatch.setattr(C, "DATA_BASE", server)
    monkeypatch.setattr(pipeline, "submissions_url", lambda cik: f"{server}/submissions/CIK{cik10(cik)}.json")
    monkeypatch.setattr(pipeline, "companyfacts_url", lambda cik: f"{server}/api/xbrl/companyfacts/CIK{cik10(cik)}.json")
    monkeypatch.setattr(pipeline, "submissions_page_url", lambda n: f"{server}/submissions/{n}")
    page = {"accessionNumber": [], "filingDate": [], "form": []}
    Handler.plan[f"/submissions/CIK{cik10(SYN.CIK)}.json"] = [(200, json.dumps(SYN.submissions()).encode())]
    Handler.plan["/submissions/CIK0009999999-submissions-002.json"] = [(200, json.dumps(page).encode())]
    Handler.plan[f"/api/xbrl/companyfacts/CIK{cik10(SYN.CIK)}.json"] = [(200, json.dumps(SYN.companyfacts()).encode())]
    raw = RawStore(root / "data" / "raw")
    log = pipeline.fetch(root, SecClient(UA, raw, sleep=lambda s: None))
    assert len(log) == 3 and all(h["ua"] == UA for h in Handler.seen)
    # the real pipeline refuses synthetic payloads...
    with pytest.raises(bridge.SyntheticDataError):
        pipeline.process(root, raw, root / "e.sqlite", "2026-03-01", root / "reports")
    # ...so to exercise the report code the guard is disabled inside this test only
    monkeypatch.setattr(bridge, "assert_real", lambda cf: None)
    ds = pipeline.process(root, raw, root / "e2.sqlite", "2026-03-01", root / "reports")
    co = ds["companies"][0]
    assert co["periods"][-1] == "2025-12-31" and co["celi"]["status"] == "insufficient"
    assert any(r["item"] == "revenue" and r["original_value"] == 1200 for r in co["restated_values"])
    for f in ("C_extraction_report.md", "D_provenance_report.md", "E_missing_unsupported.md", "dataset.json"):
        assert (root / "reports" / f).stat().st_size > 200
    assert "0009999999-24-000077" in (root / "reports" / "D_provenance_report.md").read_text()
    # re-processing the same inputs is idempotent
    ds2 = pipeline.process(root, raw, root / "e2.sqlite", "2026-03-01", root / "reports")
    assert ds2["companies"][0]["assessment_id"] == co["assessment_id"]
