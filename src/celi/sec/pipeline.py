"""Fetch (network) and process (offline, from the raw store) steps, plus the deliverable reports."""
from __future__ import annotations

import json
from pathlib import Path

from ..canonical import canonical_json, sha256_hex
from ..methodology import v3_0
from . import bridge
from .client import RawStore, SecClient, cik10, companyfacts_url, submissions_page_url, submissions_url, utcnow
from .facts import FactIndex, parse_companyfacts, to_millions
from .metrics import compute_metrics, summary
from .registry import check_identity, company_profile, filings_table, pages_needed
from .statements import annual_history
from .store import add_assessment, add_company, add_facts, add_filings, add_source, connect

SINCE = "2015-01-01"


def code_fingerprint() -> str:
    """sha256 of the extraction, metric and engine source, so a code change always yields a new assessment id."""
    here = Path(__file__).resolve().parent
    files = [here / f for f in ("facts.py", "statements.py", "metrics.py", "bridge.py")] + [here.parent / "methodology" / "v3_0.py"]
    return sha256_hex("".join(f.read_text() for f in files))


def load_registry(root: Path) -> list[dict]:
    return json.loads((root / "config" / "companies.json").read_text())["companies"]


# ---------------------------------------------------------------- fetch (needs SEC access)
def fetch(root: Path, client: SecClient, documents: bool = False) -> list[dict]:
    log = []
    for c in load_registry(root):
        sub, rec = client.get_json(submissions_url(c["cik"]), "submissions")
        check_identity(c["cik"], sub, c["expect"])
        log.append(rec)
        for name in pages_needed(sub, SINCE):
            log.append(client.get(submissions_page_url(name), "submissions_page"))
        cf, rec = client.get_json(companyfacts_url(c["cik"]), "companyfacts")
        check_identity(c["cik"], cf, c["expect"])
        log.append(rec)
        if documents:
            pages = [json.loads(client.store.read(client.store.latest(submissions_page_url(n)))) for n in pages_needed(sub, SINCE)]
            rows = filings_table(c["cik"], sub, pages)
            pick = [r for r in rows if r["base_form"] == "10-K"][-5:] + [r for r in rows if r["base_form"] == "10-Q"][-4:] + [r for r in rows if r["form"] == "DEF 14A"][-1:]
            for r in pick:
                if r["url_primary"]:
                    log.append(client.get(r["url_primary"], "filing_document"))
    return log


# ---------------------------------------------------------------- process (offline)
def _sel_json(s):
    return None if s is None else s.as_dict()


def process(root: Path, raw: RawStore, db_path: Path, asof: str, out_dir: Path) -> dict:
    db = connect(db_path)
    for r in raw.records():
        if r.get("status") == 200:
            add_source(db, r)
    created = utcnow()
    dataset = {"generated_at": created, "asof": asof, "methodology": v3_0.VERSION, "source": "SEC EDGAR (data.sec.gov companyfacts + submissions)", "companies": []}
    for c in load_registry(root):
        sub, srec = raw.read_json(submissions_url(c["cik"]))
        check_identity(c["cik"], sub, c["expect"])
        pages = [raw.read_json(submissions_page_url(n))[0] for n in pages_needed(sub, SINCE)]
        cf, crec = raw.read_json(companyfacts_url(c["cik"]))
        bridge.assert_real(cf)
        check_identity(c["cik"], cf, c["expect"])
        prof = company_profile(sub, c["model"])
        filings = filings_table(c["cik"], sub, pages)
        facts = parse_companyfacts(cf)
        add_company(db, prof, srec["sha256"])
        add_filings(db, filings, srec["sha256"])
        new_facts = add_facts(db, prof["cik"], facts, crec["sha256"])
        idx = FactIndex(facts)
        hist = annual_history(idx, c["model"], asof)
        mets = compute_metrics(hist)
        summ = summary(hist, mets)
        status = bridge.indicator_status(c["model"], mets)
        result = bridge.run_engine(c["model"], asof, status)
        inputs = {"cik": prof["cik"], "asof": asof, "companyfacts_sha256": crec["sha256"], "submissions_sha256": srec["sha256"], "model": c["model"], "code": code_fingerprint()}
        input_hash = sha256_hex(canonical_json(inputs))
        aid = f"{prof['cik']}-{asof}-{input_hash[:12]}"
        exists = db.execute("SELECT 1 FROM assessments WHERE id=?", (aid,)).fetchone()
        if not exists:
            add_assessment(db, aid, prof["cik"], asof, created, v3_0.VERSION, input_hash, v3_0.summarize(result), hist, mets)
        fmap = {f["accession"]: f for f in filings}
        amendments = [f for f in filings if f["is_amendment"] and f["base_form"] in {"10-K", "10-Q"}]
        restated = [{"item": item, **s.as_dict()} for item, by in hist["items"].items() for s in by.values() if s is not None and s.restated]
        dataset["companies"].append({
            "ticker": c["ticker"], "profile": prof, "assessment_id": aid, "input_hash": input_hash, "code_fingerprint": inputs["code"],
            "sources": {"companyfacts": {k: crec[k] for k in ("url", "sha256", "fetched_at", "bytes")}, "submissions": {k: srec[k] for k in ("url", "sha256", "fetched_at", "bytes")}},
            "counts": {"facts": len(facts), "facts_new_in_db": new_facts, "filings_registered": len(filings),
                       "ten_k": sum(1 for f in filings if f["base_form"] == "10-K"), "ten_q": sum(1 for f in filings if f["base_form"] == "10-Q"),
                       "proxy": sum(1 for f in filings if f["form"] == "DEF 14A"), "amendments": len(amendments)},
            "periods": hist["periods"],
            "statements": {item: {e: _sel_json(s) for e, s in by.items()} for item, by in hist["items"].items()},
            "filing_links": {s.accession: {"form": s.form, "filed": s.filed, "url": (fmap.get(s.accession) or {}).get("url_primary") or (fmap.get(s.accession) or {}).get("url_index")}
                             for by in hist["items"].values() for s in by.values() if s is not None},
            "metrics": mets, "summary": summ, "indicators": status, "celi": v3_0.summarize(result), "celi_reasons": result["reasons"],
            "amendment_filings": amendments[-10:], "restated_values": restated,
        })
    db.commit()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dataset.json").write_text(json.dumps(dataset, indent=1, default=str))
    write_reports(dataset, out_dir)
    return dataset


# ---------------------------------------------------------------- reports C, D, E
def _m(v):
    x = to_millions(v)
    if x is None:
        return "—"
    return f"{x:,.0f}" if abs(x) >= 100 else f"{x:,.2f}"


def _pct(v):
    return "—" if v is None else f"{v*100:.1f}%"


def write_reports(ds: dict, out: Path):
    C = [f"# C. Financial-data extraction report\n\nAssessment date {ds['asof']} · generated {ds['generated_at']} · source: {ds['source']}\n",
         "Values are USD millions as filed. '—' means the item was not reported for that period (never zero-filled). Concept = the us-gaap tag actually used.\n"]
    D = [f"# D. Source provenance report\n\nEvery figure below is traceable to one SEC accession number and filing date. Raw responses are stored content-addressed (sha256).\n"]
    E = [f"# E. Missing and unsupported indicators\n\nAssessment date {ds['asof']}. No WACC, cost of equity, sector threshold or scoring scale is assumed, so no CELI indicator is scored yet.\n"]
    for co in ds["companies"]:
        p = co["profile"]
        C.append(f"\n## {p['name']} ({co['ticker']}) · CIK {p['cik']} · model: {p['model_declared']}" + (" ⚠ model conflict with SIC" if p["model_conflict"] else "") + "\n")
        C.append(f"SIC {p['sic']} {p['sic_description']} · fiscal year end {p['fiscal_year_end']} · {co['counts']['facts']:,} XBRL facts · {co['counts']['filings_registered']:,} filings registered "
                 f"({co['counts']['ten_k']} 10-K, {co['counts']['ten_q']} 10-Q, {co['counts']['proxy']} DEF 14A, {co['counts']['amendments']} 10-K/10-Q amendments)\n")
        ends = co["periods"]
        C.append("| Item | concept | " + " | ".join(ends) + " |\n|---|---|" + "---:|" * len(ends))
        for item, by in co["statements"].items():
            concepts = sorted({s["concept"] for s in by.values() if s})
            C.append(f"| {item} | {', '.join(concepts) or '—'} | " + " | ".join(("—" if by[e] is None else (f"{by[e]['value']:.2f}" if by[e]["unit"] == "USD/shares" else _m(by[e]["value"])) + (" ᴿ" if by[e]["restated"] else "")) for e in ends) + " |")
        C.append("\nᴿ = value differs from the first-filed figure (restated or reclassified); both are kept.\n")
        C.append("**Normalised metrics (latest fiscal year)**\n\n| Metric | value | status | formula |\n|---|---:|---|---|")
        last = ends[-1] if ends else None
        for m in co["metrics"]:
            if m["period_end"] == last:
                val = "—" if m["value"] is None else (_m(m["value"]) if m["metric"] in {"free_cash_flow", "ebitda", "total_debt", "net_debt"} else (f"{m['value']:.2f}x" if m["metric"] in {"net_debt_to_ebitda", "interest_cover", "current_ratio"} else _pct(m["value"])))
                C.append(f"| {m['metric']} | {val} | {m['status']}{(' (' + ', '.join(m['missing']) + ')') if m['missing'] else ''} | `{m['formula']}` |")
        s = co["summary"]
        C.append("\n**Five-year summary (descriptive, unscored):** " + "; ".join(f"{k} {(_pct(v) if isinstance(v, float) and k != 'years_in_window' else v) if v is not None else '—'}" for k, v in s.items()) + "\n")
        r = co["celi"]
        C.append(f"**CELI-100 engine:** status `{r['status']}` · reasons: {'; '.join(co['celi_reasons'])}\n")

        D.append(f"\n## {p['name']} ({co['ticker']})\n")
        for k, src in co["sources"].items():
            D.append(f"- {k}: {src['url']} · fetched {src['fetched_at']} · {src['bytes']:,} bytes · sha256 `{src['sha256']}`")
        D.append(f"- assessment id `{co['assessment_id']}` · input hash `{co['input_hash']}`\n")
        D.append("| Accession | form | filed | document |\n|---|---|---|---|")
        for acc, f in sorted(co["filing_links"].items(), key=lambda kv: kv[1]["filed"]):
            D.append(f"| {acc} | {f['form']} | {f['filed']} | {f['url'] or '—'} |")
        if co["restated_values"]:
            D.append("\n**Values changed by a later filing (both versions kept):**\n\n| item | period | first filed | value | current | value |\n|---|---|---|---:|---|---:|")
            for x in co["restated_values"]:
                D.append(f"| {x['item']} | {x['end']} | {x['original_accession']} ({x['original_filed']}) | {_m(x['original_value'])} | {x['accession']} ({x['filed']}) | {_m(x['value'])} |")
        if co["amendment_filings"]:
            D.append("\n**Amended periodic reports on file:** " + ", ".join(f"{a['form']} {a['accession']} ({a['filing_date']})" for a in co["amendment_filings"]))

        E.append(f"\n## {p['name']} ({co['ticker']}) · {p['model_declared']} model\n\n| Indicator | status | reason | evidence available |\n|---|---|---|---|")
        for ind, st in co["indicators"].items():
            E.append(f"| {ind} | {st['status']} | {st['reason']} | {', '.join(st['evidence_metrics']) or '—'} |")
        miss = sorted({(m["metric"], m["status"], ", ".join(m["missing"]) or m["note"]) for m in co["metrics"] if m["status"] in {"missing_input", "undefined", "computed_partial"}})
        if miss:
            E.append("\n**Metrics not fully computable (any year in window):**\n")
            E += [f"- {a}: {b} ({c})" for a, b, c in miss]
        nulls = sorted({item for item, by in co["statements"].items() if any(v is None for v in by.values())})
        if nulls:
            E.append(f"\n**Statement items not reported for at least one year:** {', '.join(nulls)}")
    (out / "C_extraction_report.md").write_text("\n".join(C) + "\n")
    (out / "D_provenance_report.md").write_text("\n".join(D) + "\n")
    (out / "E_missing_unsupported.md").write_text("\n".join(E) + "\n")
