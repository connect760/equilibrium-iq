"""Financial indicator normalisation engine.

Only ratios defined entirely by filed figures. No cost of capital, no sector thresholds, no
scoring scale, no imputation. Every metric records its formula, its status and the exact
filed inputs (concept, accession, filing date) it used.

Statuses
  computed          all inputs present and the ratio is defined
  computed_partial  computed, but an optional component (e.g. commercial paper) was not tagged;
                    an untagged component is NOT assumed to be zero; the missing parts are listed
  missing_input     a required input was not reported for that period
  undefined         inputs present but the ratio is not meaningful (zero/negative denominator)
Bank and non-financial corporate metrics are separate functions with separate formulas.
"""
from __future__ import annotations

import statistics


def _v(hist: dict, item: str, end: str):
    s = hist["items"].get(item, {}).get(end)
    return None if s is None else s.value


def _ref(hist: dict, item: str, end: str) -> dict | None:
    s = hist["items"].get(item, {}).get(end)
    return None if s is None else {"item": item, "concept": s.concept, "end": end, "value": s.value, "accession": s.accession, "filed": s.filed, "form": s.form}


def _metric(name, end, formula, value=None, status="computed", inputs=(), missing=(), note=""):
    return {"metric": name, "period_end": end, "value": value, "status": status, "formula": formula,
            "inputs": [i for i in inputs if i], "missing": list(missing), "note": note}


def _ratio(hist, name, end, num, den, formula, positive_den=True):
    a, b = _v(hist, num, end), _v(hist, den, end)
    refs = [_ref(hist, num, end), _ref(hist, den, end)]
    miss = [x for x, v in ((num, a), (den, b)) if v is None]
    if miss:
        return _metric(name, end, formula, status="missing_input", inputs=refs, missing=miss)
    if b == 0 or (positive_den and b < 0):
        return _metric(name, end, formula, status="undefined", inputs=refs, note=f"{den} is {b}")
    return _metric(name, end, formula, a / b, inputs=refs)


def _growth(hist, item, ends, i, name):
    end, prev = ends[i], ends[i - 1] if i > 0 else None
    formula = f"{item}[t] / {item}[t-1] - 1"
    if prev is None:
        return _metric(name, end, formula, status="missing_input", missing=[f"{item}[t-1]"], note="no prior fiscal year in window")
    a, b = _v(hist, item, end), _v(hist, item, prev)
    refs = [_ref(hist, item, end), _ref(hist, item, prev)]
    if a is None or b is None:
        return _metric(name, end, formula, status="missing_input", inputs=refs, missing=[x for x, v in ((f"{item}[t]", a), (f"{item}[t-1]", b)) if v is None])
    if b <= 0:
        return _metric(name, end, formula, status="undefined", inputs=refs, note="prior value not positive")
    return _metric(name, end, formula, a / b - 1, inputs=refs)


def _total_debt(hist, end):
    formula = "debt_noncurrent + debt_current + commercial_paper + short_term_borrowings"
    parts = ["debt_noncurrent", "debt_current", "commercial_paper", "short_term_borrowings"]
    vals = {p: _v(hist, p, end) for p in parts}
    refs = [_ref(hist, p, end) for p in parts]
    if vals["debt_noncurrent"] is None:
        return _metric("total_debt", end, formula, status="missing_input", inputs=refs, missing=["debt_noncurrent"])
    absent = [p for p in parts[1:] if vals[p] is None]
    total = sum(v for v in vals.values() if v is not None)
    return _metric("total_debt", end, formula, total, "computed_partial" if absent else "computed", refs, absent,
                   "untagged components are excluded, not assumed zero; lease liabilities not included" if absent else "lease liabilities not included")


def corporate_metrics(hist: dict, years: int = 5) -> list[dict]:
    ends = hist["periods"]
    out = []
    for i, e in enumerate(ends):
        if i < len(ends) - years:
            continue
        out.append(_growth(hist, "revenue", ends, i, "revenue_growth"))
        out.append(_ratio(hist, "operating_margin", e, "operating_income", "revenue", "operating_income / revenue"))
        out.append(_ratio(hist, "net_margin", e, "net_income", "revenue", "net_income / revenue"))
        out.append(_ratio(hist, "rnd_to_revenue", e, "rnd", "revenue", "rnd / revenue"))
        out.append(_ratio(hist, "capex_to_revenue", e, "capex", "revenue", "capex / revenue"))
        out.append(_ratio(hist, "effective_tax_rate", e, "income_tax", "pretax_income", "income_tax / pretax_income"))
        out.append(_ratio(hist, "liabilities_to_assets", e, "total_liabilities", "total_assets", "total_liabilities / total_assets"))
        out.append(_ratio(hist, "current_ratio", e, "current_assets", "current_liabilities", "current_assets / current_liabilities"))
        out.append(_ratio(hist, "return_on_equity", e, "net_income", "equity", "net_income / equity (period-end)"))
        out.append(_ratio(hist, "interest_cover", e, "operating_income", "interest_expense", "operating_income / interest_expense"))
        cfo, capex, oi, dna = (_v(hist, k, e) for k in ("cfo", "capex", "operating_income", "dna"))
        fcf_refs = [_ref(hist, "cfo", e), _ref(hist, "capex", e)]
        fcf = None
        if cfo is None or capex is None:
            out.append(_metric("free_cash_flow", e, "cfo - capex", status="missing_input", inputs=fcf_refs, missing=[k for k, v in (("cfo", cfo), ("capex", capex)) if v is None]))
        else:
            fcf = cfo - capex
            out.append(_metric("free_cash_flow", e, "cfo - capex", fcf, inputs=fcf_refs))
        if fcf is None or oi is None:
            out.append(_metric("fcf_to_operating_income", e, "(cfo - capex) / operating_income", status="missing_input", inputs=fcf_refs + [_ref(hist, "operating_income", e)], missing=[k for k, v in (("free_cash_flow", fcf), ("operating_income", oi)) if v is None]))
        elif oi <= 0:
            out.append(_metric("fcf_to_operating_income", e, "(cfo - capex) / operating_income", status="undefined", inputs=fcf_refs, note="operating income not positive"))
        else:
            out.append(_metric("fcf_to_operating_income", e, "(cfo - capex) / operating_income", fcf / oi, inputs=fcf_refs + [_ref(hist, "operating_income", e)]))
        ebitda = None if oi is None or dna is None else oi + dna
        out.append(_metric("ebitda", e, "operating_income + dna", ebitda, "computed" if ebitda is not None else "missing_input",
                           [_ref(hist, "operating_income", e), _ref(hist, "dna", e)], [k for k, v in (("operating_income", oi), ("dna", dna)) if v is None]))
        td = _total_debt(hist, e)
        out.append(td)
        cash = _v(hist, "cash", e)
        if td["value"] is None or cash is None:
            nd = _metric("net_debt", e, "total_debt - cash", status="missing_input", inputs=[_ref(hist, "cash", e)], missing=(["total_debt"] if td["value"] is None else []) + (["cash"] if cash is None else []))
        else:
            nd = _metric("net_debt", e, "total_debt - cash", td["value"] - cash, td["status"], td["inputs"] + [_ref(hist, "cash", e)], td["missing"], td["note"])
        out.append(nd)
        if nd["value"] is None or ebitda is None:
            out.append(_metric("net_debt_to_ebitda", e, "net_debt / ebitda", status="missing_input", missing=[k for k, v in (("net_debt", nd["value"]), ("ebitda", ebitda)) if v is None]))
        elif ebitda <= 0:
            out.append(_metric("net_debt_to_ebitda", e, "net_debt / ebitda", status="undefined", note="EBITDA not positive"))
        else:
            out.append(_metric("net_debt_to_ebitda", e, "net_debt / ebitda", nd["value"] / ebitda, nd["status"], nd["inputs"], nd["missing"]))
        # after-tax return on invested capital, using the company's own effective tax rate; NOT compared with any cost of capital
        pt, tx, eq = _v(hist, "pretax_income", e), _v(hist, "income_tax", e), _v(hist, "equity", e)
        f = "operating_income * (1 - income_tax/pretax_income) / (equity + total_debt - cash)"
        need = {"operating_income": oi, "pretax_income": pt, "income_tax": tx, "equity": eq, "total_debt": td["value"], "cash": cash}
        if any(v is None for v in need.values()):
            out.append(_metric("return_on_invested_capital", e, f, status="missing_input", missing=[k for k, v in need.items() if v is None]))
        elif pt <= 0 or (eq + td["value"] - cash) <= 0:
            out.append(_metric("return_on_invested_capital", e, f, status="undefined", note="pretax income or invested capital not positive"))
        else:
            out.append(_metric("return_on_invested_capital", e, f, oi * (1 - tx / pt) / (eq + td["value"] - cash), td["status"],
                               td["inputs"] + [_ref(hist, k, e) for k in ("operating_income", "pretax_income", "income_tax", "equity", "cash")], td["missing"]))
    return out


def bank_metrics(hist: dict, years: int = 5) -> list[dict]:
    ends = hist["periods"]
    out = []
    for i, e in enumerate(ends):
        if i < len(ends) - years:
            continue
        out.append(_growth(hist, "revenue", ends, i, "revenue_growth"))
        out.append(_ratio(hist, "return_on_equity", e, "net_income", "equity", "net_income / equity (period-end)"))
        out.append(_ratio(hist, "return_on_assets", e, "net_income", "total_assets", "net_income / total_assets (period-end)"))
        out.append(_ratio(hist, "equity_to_assets", e, "equity", "total_assets", "equity / total_assets"))
        out.append(_ratio(hist, "deposits_to_assets", e, "deposits", "total_assets", "deposits / total_assets"))
        out.append(_ratio(hist, "loans_to_deposits", e, "loans_net", "deposits", "loans_net / deposits"))
        out.append(_ratio(hist, "efficiency_ratio", e, "noninterest_expense", "revenue", "noninterest_expense / revenue"))
        out.append(_ratio(hist, "provision_to_loans", e, "provision_credit_losses", "loans_net", "provision_credit_losses / loans_net"))
        out.append(_ratio(hist, "net_interest_income_share", e, "net_interest_income", "revenue", "net_interest_income / revenue"))
    return out


def compute_metrics(hist: dict, years: int = 5) -> list[dict]:
    if hist["model"] == "bank":
        return bank_metrics(hist, years)
    if hist["model"] == "corporate":
        return corporate_metrics(hist, years)
    raise ValueError(f"No metric model for {hist['model']!r}")


def series(metrics: list[dict], name: str) -> list[float]:
    return [m["value"] for m in metrics if m["metric"] == name and m["value"] is not None]


def summary(hist: dict, metrics: list[dict]) -> dict:
    """Multi-year descriptive statistics. Descriptive only: no thresholds, no scores."""
    def sd(xs):
        return statistics.pstdev(xs) if len(xs) >= 3 else None

    rev = [s.value for s in (hist["items"]["revenue"].get(e) for e in hist["periods"]) if s is not None]
    peak, dd = None, 0.0
    for v in rev:
        peak = v if peak is None else max(peak, v)
        if peak and peak > 0:
            dd = max(dd, 1 - v / peak)
    g = series(metrics, "revenue_growth")
    out = {"years_in_window": len(hist["periods"]), "revenue_growth_sd": sd(g), "revenue_growth_mean": statistics.fmean(g) if g else None,
           "worst_revenue_drawdown": dd if len(rev) >= 3 else None}
    if hist["model"] == "corporate":
        om = series(metrics, "operating_margin")
        fcf = series(metrics, "free_cash_flow")
        out.update({"operating_margin_sd": sd(om), "fcf_positive_share": (sum(1 for x in fcf if x > 0) / len(fcf)) if fcf else None,
                    "roic_mean": statistics.fmean(series(metrics, "return_on_invested_capital")) if series(metrics, "return_on_invested_capital") else None})
    else:
        roe = series(metrics, "return_on_equity")
        out.update({"roe_mean": statistics.fmean(roe) if roe else None, "efficiency_ratio_mean": statistics.fmean(series(metrics, "efficiency_ratio")) if series(metrics, "efficiency_ratio") else None})
    return out
