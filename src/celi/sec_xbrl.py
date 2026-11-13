"""Deterministic Layer-A extraction from SEC EDGAR XBRL "companyfacts" JSON.

Rules:
* Only facts from annual reports (form 10-K / 10-K/A, fp == "FY") are used.
* Flow concepts must cover ~12 months (330-400 days); stock concepts are instants.
* Point-in-time: for each fiscal period end, the latest filing filed on or before the
  assessment cutoff is used, so restatements are honoured but no future data leaks in.
* Every derived indicator keeps the concept names and accession numbers it used.
* Nothing is estimated or imputed here. A missing concept means the indicator is
  'unavailable' and the engine applies its conservative baseline.

Scoring functions below are GIP PILOT PRIORS. They are published so anyone can
reproduce a score; they are not calibrated (see white paper section 5.4).
"""
from __future__ import annotations

import statistics
from datetime import date

ASSUMPTIONS = {
    "wacc": 0.08,            # prior cost of capital for non-financials
    "cost_of_equity": 0.10,  # prior for financials (ROE comparison)
    "default_tax_rate": 0.21,
    "years": 5,
}

CONCEPTS = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "RevenuesNetOfInterestExpense"],
    "op_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "pretax": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic"],
    "tax": ["IncomeTaxExpenseBenefit"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "da": ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "DepreciationAmortizationAndAccretionNet"],
    "interest": ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "lt_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "st_debt": ["LongTermDebtCurrent", "DebtCurrent", "ShortTermBorrowings", "CommercialPaper"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
}
STOCKS = {"equity", "lt_debt", "st_debt", "cash"}


def _days(a: str, b: str) -> int:
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def annual_series(facts: dict, key: str, cutoff: str) -> tuple[dict[str, dict], str | None]:
    """Return {fiscal_end: fact} for the first concept in CONCEPTS[key] that has data, and the concept used."""
    gaap = (facts.get("facts") or {}).get("us-gaap") or {}
    for concept in CONCEPTS[key]:
        units = (gaap.get(concept) or {}).get("units") or {}
        rows = units.get("USD") or []
        out: dict[str, dict] = {}
        for r in rows:
            form = r.get("form") or ""
            if not form.startswith("10-K") or r.get("fp") != "FY" or not r.get("end") or (r.get("filed") or "9999") > cutoff:
                continue
            if key in STOCKS:
                if r.get("start"):
                    continue
            else:
                if not r.get("start") or not 330 <= _days(r["start"], r["end"]) <= 400:
                    continue
            prev = out.get(r["end"])
            if prev is None or r["filed"] > prev["filed"]:
                out[r["end"]] = {"val": r["val"], "filed": r["filed"], "accn": r.get("accn"), "form": form, "concept": concept}
        if out:
            return out, concept
    return {}, None


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _last(series: dict, n: int) -> list[tuple[str, dict]]:
    return sorted(series.items())[-n:]


def _aligned(n: int, *series: dict) -> list[str]:
    ends = set(series[0])
    for s in series[1:]:
        ends &= set(s)
    return sorted(ends)[-n:]


def extract(facts: dict, cutoff: str, archetype: str) -> dict:
    """Compute Layer-A indicators. Returns {indicator_id: evidence record} and a provenance log."""
    S = {k: annual_series(facts, k, cutoff) for k in CONCEPTS}
    ser = {k: v[0] for k, v in S.items()}
    used = {k: v[1] for k, v in S.items()}
    n = ASSUMPTIONS["years"]
    ev: dict[str, dict] = {}
    log: dict[str, dict] = {}
    cik = str(facts.get("cik", "")).lstrip("0")

    def cite(ends: list[str], keys: list[str]) -> dict:
        accns = sorted({ser[k][e]["accn"] for k in keys for e in ends if e in ser[k] and ser[k][e].get("accn")})
        latest = max((ser[k][e]["filed"] for k in keys for e in ends if e in ser[k]), default="")
        first = accns[-1] if accns else ""
        return {
            "source": f"Form 10-K XBRL facts ({len(ends)} fiscal years to {ends[-1] if ends else '—'})",
            "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K" if cik else "",
            "filed": latest, "page": "XBRL fact (no page)", "bbox": None, "period": f"FY to {ends[-1]}" if ends else "",
            "tag": "; ".join(f"us-gaap:{used[k]}" for k in keys if used[k]), "accessions": accns, "latest_accession": first,
        }

    def unavailable(ind: str, why: str):
        ev[ind] = {"state": "unavailable", "score": None, "cls": "independently_assured", "method": "taxonomy", "conf": None, "raw": why, "source": "SEC XBRL companyfacts", "tag": "", "url": "", "filed": "", "page": "", "bbox": None, "period": ""}

    def scored(ind: str, score: float, raw: str, ends: list[str], keys: list[str], detail: dict):
        ev[ind] = {"state": "disclosed", "score": round(_clamp(score), 1), "cls": "independently_assured", "method": "taxonomy", "conf": 1.0, "raw": raw, **cite(ends, keys)}
        log[ind] = detail

    fin = archetype == "financial"

    # ROIC_5Y (non-financial) / ROE vs cost of equity (financial)
    if fin:
        ends = _aligned(n, ser["net_income"], ser["equity"])
        if len(ends) >= 3:
            roe = [ser["net_income"][e]["val"] / ser["equity"][e]["val"] for e in ends if ser["equity"][e]["val"] > 0]
            m = statistics.fmean(roe)
            spread = m - ASSUMPTIONS["cost_of_equity"]
            scored("ROIC_5Y", 50 + 250 * spread, f"ROE {len(roe)}y avg {m:.1%} vs cost of equity {ASSUMPTIONS['cost_of_equity']:.0%} (spread {spread*100:+.1f} pp)", ends, ["net_income", "equity"], {"roe": roe})
        else:
            unavailable("ROIC_5Y", "Fewer than 3 aligned fiscal years of net income and equity")
    else:
        ends = _aligned(n, ser["op_income"], ser["equity"], ser["lt_debt"])
        if len(ends) >= 3:
            vals = []
            for e in ends:
                pt, tx = ser["pretax"].get(e), ser["tax"].get(e)
                rate = tx["val"] / pt["val"] if pt and tx and pt["val"] > 0 else ASSUMPTIONS["default_tax_rate"]
                rate = min(0.5, max(0.0, rate))
                debt = ser["lt_debt"][e]["val"] + (ser["st_debt"].get(e, {}).get("val") or 0)
                ic = ser["equity"][e]["val"] + debt - (ser["cash"].get(e, {}).get("val") or 0)
                if ic > 0:
                    vals.append(ser["op_income"][e]["val"] * (1 - rate) / ic)
            if vals:
                m = statistics.fmean(vals)
                spread = m - ASSUMPTIONS["wacc"]
                scored("ROIC_5Y", 50 + 250 * spread, f"ROIC {len(vals)}y avg {m:.1%} vs WACC prior {ASSUMPTIONS['wacc']:.0%} (spread {spread*100:+.1f} pp)", ends, ["op_income", "pretax", "tax", "equity", "lt_debt", "st_debt", "cash"], {"roic": vals})
            else:
                unavailable("ROIC_5Y", "Invested capital not positive in any year")
        else:
            unavailable("ROIC_5Y", "Fewer than 3 aligned fiscal years of operating income, equity and debt")

    # FCF_DUR
    if fin:
        ev["FCF_DUR"] = {"state": "not_applicable", "score": None, "cls": "independently_assured", "method": "taxonomy", "conf": None, "raw": "Free-cash-flow conversion is not meaningful for banks (dedicated bank model)", "source": "", "tag": "", "url": "", "filed": "", "page": "", "bbox": None, "period": ""}
    else:
        ends = _aligned(n, ser["cfo"], ser["capex"], ser["op_income"])
        if len(ends) >= 3:
            fcf = [ser["cfo"][e]["val"] - ser["capex"][e]["val"] for e in ends]
            oi = sum(ser["op_income"][e]["val"] for e in ends)
            conv = sum(fcf) / oi if oi > 0 else 0.0
            pos = sum(1 for f in fcf if f > 0) / len(fcf)
            scored("FCF_DUR", 70 * _clamp(conv, 0, 1) + 30 * pos, f"FCF/operating income {conv:.2f} over {len(ends)}y; FCF positive in {pos:.0%} of years", ends, ["cfo", "capex", "op_income"], {"fcf": fcf, "conv": conv, "pos": pos})
        else:
            unavailable("FCF_DUR", "Fewer than 3 aligned fiscal years of cash flow, capex and operating income")

    # REV_DUR: growth volatility and (non-financial) operating-margin volatility
    rev_ends = [e for e, _ in _last(ser["revenue"], n + 1)]
    if len(rev_ends) >= 4:
        rv = [ser["revenue"][e]["val"] for e in rev_ends]
        g = [rv[i] / rv[i - 1] - 1 for i in range(1, len(rv)) if rv[i - 1] > 0]
        s1 = _clamp(100 - 250 * statistics.pstdev(g))
        if not fin and all(e in ser["op_income"] for e in rev_ends[1:]):
            mg = [ser["op_income"][e]["val"] / ser["revenue"][e]["val"] for e in rev_ends[1:]]
            s2 = _clamp(100 - 500 * statistics.pstdev(mg))
            score, raw = (s1 + s2) / 2, f"Revenue growth s.d. {statistics.pstdev(g):.1%}; operating-margin s.d. {statistics.pstdev(mg):.1%}"
        else:
            score, raw = s1, f"Revenue growth s.d. {statistics.pstdev(g):.1%}"
        scored("REV_DUR", score, raw, rev_ends, ["revenue", "op_income"], {"growth": g})
    else:
        unavailable("REV_DUR", "Fewer than 4 fiscal years of revenue")

    # FIN_FRAG (severity): net debt / EBITDA and interest cover; utilities tolerate more leverage
    if fin:
        unavailable("FIN_FRAG", "Bank fragility needs capital and liquidity ratios (CET1, LCR, NSFR) from regulatory reports, not in companyfacts")
    else:
        e = sorted(set(ser["op_income"]) & set(ser["lt_debt"]))[-1:] if ser["op_income"] and ser["lt_debt"] else []
        if e:
            e = e[0]
            ebitda = ser["op_income"][e]["val"] + (ser["da"].get(e, {}).get("val") or 0)
            debt = ser["lt_debt"][e]["val"] + (ser["st_debt"].get(e, {}).get("val") or 0)
            nd = debt - (ser["cash"].get(e, {}).get("val") or 0)
            lev = nd / ebitda if ebitda > 0 else 99.0
            scale = 8.0 if archetype == "utility" else 5.0
            sev1 = _clamp(100 * lev / scale)
            it = ser["interest"].get(e)
            if it and it["val"] > 0:
                cover = ser["op_income"][e]["val"] / it["val"]
                sev2 = _clamp(100 - 10 * cover)
                sev, raw = (sev1 + sev2) / 2, f"Net debt/EBITDA {lev:.2f}x (scale {scale:g}x); interest cover {cover:.1f}x"
            else:
                sev, raw = sev1, f"Net debt/EBITDA {lev:.2f}x (scale {scale:g}x); interest expense not tagged"
            scored("FIN_FRAG", sev, raw, [e], ["op_income", "da", "lt_debt", "st_debt", "cash", "interest"], {"net_debt_ebitda": lev})
        else:
            unavailable("FIN_FRAG", "Operating income or debt not tagged")

    # OP_RES: worst peak-to-trough revenue decline over up to 10 fiscal years
    long = [ser["revenue"][e]["val"] for e, _ in _last(ser["revenue"], 10)]
    if len(long) >= 5:
        peak, dd = long[0], 0.0
        for v in long:
            peak = max(peak, v)
            if peak > 0:
                dd = max(dd, 1 - v / peak)
        ends10 = [e for e, _ in _last(ser["revenue"], 10)]
        scored("OP_RES", 100 - 250 * dd, f"Worst revenue drawdown {dd:.1%} over {len(long)} fiscal years", ends10, ["revenue"], {"drawdown": dd})
    else:
        unavailable("OP_RES", "Fewer than 5 fiscal years of revenue")

    # Not derivable from companyfacts: left for analysts, never guessed.
    for ind, why in {
        "REV_DIV": "Segment revenues are dimensional XBRL, not in companyfacts; analyst extraction needed",
        "REINVEST": "Reinvestment quality is a judgement; analyst extraction needed",
        "ENV_OUT": "Emissions outcomes are in sustainability reports, not XBRL; analyst extraction needed",
    }.items():
        unavailable(ind, why)
    return {"ev": ev, "log": log, "concepts": used}
