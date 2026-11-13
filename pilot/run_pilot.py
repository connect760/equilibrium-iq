"""Run the US 10-company pilot through the same Layer-A extractor and v3.0 engine.

python3 -I run_pilot.py  -> writes pilot_results.json and pilot_entities.json
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from celi import sec_xbrl  # noqa: E402
from celi.methodology import v3_0  # noqa: E402
from celi.canonical import sha256_hex as sha256, canonical_json  # noqa: E402
from pilot_data import COMPANIES, CUTOFF, EDGAR  # noqa: E402

KEYS = ["revenue", "op_income", "net_income", "pretax", "tax", "cfo", "capex", "da", "interest", "equity", "lt_debt", "st_debt", "cash"]
JUDGEMENT = {
    "WORKFORCE": "Workforce stewardship needs human-capital disclosures and analyst reading",
    "GOV_CONC": "Board / control concentration needs proxy-statement extraction",
    "AUDIT_INT": "Audit opinion, restatements and material weaknesses need 10-K Item 9A / auditor report extraction",
    "REG_LEGAL": "Regulatory and legal record needs enforcement-database and contingency-note review",
    "OP_HARM": "Verified harm events need incident and enforcement sources",
    "BM_ADAPT": "Business-model adaptability is an analyst judgement",
    "GEO_SUPPLY": "Geographic / supply-chain resilience needs segment and risk-factor extraction",
    "INNOV": "Innovation capability needs R&D quality review, not intensity alone",
}


def derived_op_income(c):
    """EBIT proxy for companies with no operating-income line: pretax + interest expense - interest income."""
    ii = c.get("interest_income") or [0] * len(c["fy"])
    return [None if p is None else p + (i or 0) - (j or 0) for p, i, j in zip(c["pretax"], c["interest"] or [0] * len(c["fy"]), ii)]


def to_facts(t, c):
    """Shape the recorded figures like SEC companyfacts so the published extractor runs unchanged."""
    gaap = {}
    series = {k: c.get(k) for k in KEYS}
    if series["op_income"] is None and c["archetype"] != "financial":
        series["op_income"] = derived_op_income(c)
    for k, vals in series.items():
        if not vals:
            continue
        rows = []
        for end, v in zip(c["fy"], vals):
            if v is None:
                continue
            filed = c.get("ten_k_filed") if end == c["fy"][-1] and c.get("ten_k_filed") else (date.fromisoformat(end) + timedelta(days=60)).isoformat()
            r = {"val": v, "end": end, "fy": int(end[:4]), "fp": "FY", "form": "10-K", "filed": filed, "accn": f"web-rendering:{t}:{end}"}
            if k not in sec_xbrl.STOCKS:
                r["start"] = (date.fromisoformat(end) - timedelta(days=364)).isoformat()
            rows.append(r)
        gaap[sec_xbrl.CONCEPTS[k][0]] = {"units": {"USD": rows}}
    return {"cik": c["cik"], "facts": {"us-gaap": gaap}}, series["op_income"] is not c.get("op_income")


def build(t, c):
    facts, ebit_proxy = to_facts(t, c)
    out = sec_xbrl.extract(facts, CUTOFF, c["archetype"])
    ev = out["ev"]
    for ind, e in ev.items():
        if e.get("state") == "disclosed":
            e["source"] = "Third-party rendering of 10-K data (" + ", ".join(c["src"]) + "); re-verify against EDGAR"
            e["url"] = c["src"][0]
            e["edgar"] = EDGAR + c["cik"]
            e["cls"] = "company_reported" if ebit_proxy and ind in ("ROIC_5Y", "FCF_DUR", "REV_DUR", "FIN_FRAG") else "statutory_filing"
            if ebit_proxy and ind in ("ROIC_5Y", "FCF_DUR", "REV_DUR", "FIN_FRAG"):
                e["raw"] += " [operating income derived: pretax + interest expense - interest income]"
        else:
            e["source"] = "Pending analyst extraction" if e.get("state") == "unavailable" else e.get("source", "")
    for ind, why in JUDGEMENT.items():
        ev[ind] = {"state": "unavailable", "score": None, "cls": "company_reported", "method": "taxonomy", "conf": None,
                   "raw": why, "source": "Pending analyst extraction", "tag": "", "url": "", "filed": "", "page": "", "bbox": None, "period": ""}
    snap = {"archetype": c["archetype"], "cutoff": CUTOFF, "rol": 0.7, "provisional": True, "ev": ev, "events": []}
    res = v3_0.compute(snap)
    return snap, res, out["log"], ebit_proxy


def main():
    results, entities = {}, []
    for t, c in COMPANIES.items():
        snap, res, log, proxy = build(t, c)
        s = v3_0.summarize(res)
        layer_a = {k: v for k, v in snap["ev"].items() if v["state"] == "disclosed"}
        results[t] = {"name": c["name"], "archetype": c["archetype"], "summary": s, "reasons": res["reasons"],
                      "layerA": {k: {"score": v["score"], "raw": v["raw"]} for k, v in layer_a.items()},
                      "not_applicable": [k for k, v in snap["ev"].items() if v["state"] == "not_applicable"],
                      "ebit_proxy": proxy, "input_hash": sha256(canonical_json(snap))}
        entities.append({
            "id": "pilot-" + t.lower(), "gipId": "GIP-US-PILOT-" + t, "name": c["name"], "legalName": c["name"],
            "sector": c["sector"], "archetype": c["archetype"], "jurisdiction": "United States", "rol": 0.7,
            "exchange": "NYSE" if t in ("JPM", "NEE", "DUK", "CAT", "XOM", "JNJ", "PG") else "NASDAQ", "ticker": t,
            "entityType": "Listed parent", "lei": "", "period": f"Fiscal years {c['fy'][0][:4]}-{c['fy'][-1][:4]} (annual, 10-K)",
            "quarter": "FY" + c["fy"][-1][:4], "cutoff": CUTOFF, "ingested": CUTOFF, "assessed": CUTOFF,
            "provisional": True,
            "provisionalReason": "US pilot: Layer-A financial indicators only, from third-party renderings of 10-K data pending EDGAR re-verification; judgement indicators await analyst extraction.",
            "ev": snap["ev"], "events": [], "history": [], "alertReview": {"status": "open", "checks": {}, "note": ""},
            "notes": "; ".join(x for x in (c.get("capex_note"), c.get("debt_note"), c.get("ni_note")) if x),
            "illustrative": False, "pilot": True,
        })
    (HERE / "pilot_results.json").write_text(json.dumps(results, indent=1))
    (HERE / "pilot_entities.json").write_text(json.dumps(entities))
    print(f"{'Ticker':6} {'Arch':10} {'P':>6} {'C':>6} {'L':>6} {'CELI':>6} {'DCS':>5}  status   cov(cap/risk/adapt)")
    for t, r in results.items():
        s = r["summary"]
        cv = s["coverage"]
        print(f"{t:6} {r['archetype']:10} {s['P']:6.1f} {100-s['Rt']:6.1f} {s['L']:6.1f} {s['celi']:6.1f} {s['dcs']:5.1f}  {s['status']:12} {cv['cap']:.2f}/{cv['risk']:.2f}/{cv['adapt']:.2f}")
        for k, v in r["layerA"].items():
            print(f"        {k:9} {v['score']:5.1f}  {v['raw']}")


if __name__ == "__main__":
    main()
