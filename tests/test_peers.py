"""Peer-percentile scale tests (synthetic peers; tests/fixtures/synthetic)."""
import pytest

import sec_fixture as SYN
from celi.sec import bridge, peers as P
from celi.sec.facts import FactIndex, parse_companyfacts
from celi.sec.metrics import compute_metrics
from celi.sec.statements import annual_history

ASOF = "2026-11-16"


def peer(cik, group="Information Technology", asof=ASOF, **inputs):
    return {"cik": f"{cik:010d}", "symbol": f"P{cik}", "group": group, "asof": asof, "inputs": inputs}


def test_percentile_basic_and_ties():
    assert P.percentile(5, [1, 2, 3, 4], +1) == 100.0
    assert P.percentile(0, [1, 2, 3, 4], +1) == 0.0
    assert P.percentile(2, [1, 2, 3, 4], +1) == pytest.approx(37.5)   # 1 below + half of 1 tie, / 4
    assert P.percentile(2, [1, 2, 3, 4], -1) == pytest.approx(62.5)   # lower is better


def test_scores_use_group_exclude_self_and_need_min_peers():
    rows = [peer(i, roic_mean=i / 100) for i in range(1, 21)] + [peer(99, group="Energy", roic_mean=9.0), peer(7, roic_mean=0.07)]
    s = P.score_indicators("corporate", ASOF, {"roic_mean": 0.105}, rows, f"{7:010d}", "Information Technology")
    part = s["ROIC_5Y"]["parts"][0]
    assert part["peers"] == 19 and s["ROIC_5Y"]["score"] == pytest.approx(100 * 9 / 19, abs=0.01)  # self (cik 7, value 0.07) and Energy excluded: 9 of 19 peers below
    few = P.score_indicators("corporate", ASOF, {"roic_mean": 0.1}, rows[:5], "x", "Information Technology")
    assert few["ROIC_5Y"]["score"] is None and "fewer than" in few["ROIC_5Y"]["parts"][0]["reason"]


def test_missing_peer_values_are_excluded_not_zero():
    rows = [peer(i, roic_mean=i / 100) for i in range(1, 13)] + [peer(50 + i, roic_mean=None) for i in range(10)]
    s = P.score_indicators("corporate", ASOF, {"roic_mean": 0.125}, rows, "x", "Information Technology")
    assert s["ROIC_5Y"]["parts"][0]["peers"] == 12 and s["ROIC_5Y"]["score"] == 100.0


def test_risk_direction_more_leverage_is_more_fragile():
    rows = [peer(i, net_debt_to_ebitda=float(i), interest_cover=float(20 - i)) for i in range(1, 15)]
    hi = P.score_indicators("corporate", ASOF, {"net_debt_to_ebitda": 13.5, "interest_cover": 1.0}, rows, "x", "Information Technology")["FIN_FRAG"]
    lo = P.score_indicators("corporate", ASOF, {"net_debt_to_ebitda": 0.5, "interest_cover": 50.0}, rows, "x", "Information Technology")["FIN_FRAG"]
    assert hi["score"] > 90 and lo["score"] < 10


def test_peers_from_other_assessment_dates_never_used():
    rows = [peer(i, asof="2027-01-01", roic_mean=i / 100) for i in range(1, 20)]
    s = P.score_indicators("corporate", ASOF, {"roic_mean": 0.1}, rows, "x", "Information Technology")
    assert s["ROIC_5Y"]["score"] is None


def test_membership_list_not_point_in_time_guard():
    rows = [peer(i, asof="2020-01-01", roic_mean=i / 100) for i in range(1, 20)]
    s = P.score_indicators("corporate", "2020-01-01", {"roic_mean": 0.1}, rows, "x", "Information Technology")
    assert all(v["score"] is None and "not point-in-time" in v["reason"] for v in s.values())


def test_bank_scale_separate():
    rows = [peer(i, group="Banks", roe_mean=i / 100) for i in range(1, 13)]
    s = P.score_indicators("bank", ASOF, {"roe_mean": 0.2, "revenue_drawdown_worst": 0.0, "revenue_growth_sd": 0.05}, rows, "x", "Banks")
    assert set(s) == {"ROIC_5Y", "REV_DUR"} and s["ROIC_5Y"]["score"] == 100.0


def test_indicator_inputs_point_in_time():
    idx = FactIndex(parse_companyfacts(SYN.companyfacts()))
    h_old = annual_history(idx, "corporate", "2024-03-01")
    h_new = annual_history(idx, "corporate", "2026-03-01")
    a, b = P.indicator_inputs(h_old, compute_metrics(h_old)), P.indicator_inputs(h_new, compute_metrics(h_new))
    assert a["latest_period"] == "2023-12-31" and b["latest_period"] == "2025-12-31"
    assert b["fcf_conversion_cum"] == pytest.approx((200 + 200 + 200 + 220 + 240) / (200 + 220 + 240 + 260 + 300))  # FY21-25: sum(cfo - capex) / sum(operating income)


def test_peer_scores_feed_engine_as_scored_evidence():
    idx = FactIndex(parse_companyfacts(SYN.companyfacts()))
    h = annual_history(idx, "corporate", "2026-03-01")
    m = compute_metrics(h)
    st = bridge.indicator_status("corporate", m)
    rows = [peer(i, asof="2026-03-01", roic_mean=i / 100, fcf_conversion_cum=i / 20) for i in range(1, 15)]
    ps = P.score_indicators("corporate", "2026-03-01", P.indicator_inputs(h, m), rows, "x", "Information Technology")
    st2 = bridge.apply_peer_scores(st, ps)
    assert st2["ROIC_5Y"]["status"] == "scored_peer_percentile" and st["ROIC_5Y"]["status"] != "scored_peer_percentile"
    r = bridge.run_engine("corporate", "2026-03-01", st2, "tech")
    assert r["status"] == "insufficient"  # judgement indicators still pending: no definitive score
    assert r["celi"] is not None          # but an indicative value exists
