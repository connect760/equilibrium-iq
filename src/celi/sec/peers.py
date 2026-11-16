"""Peer-percentile scale for the financial (Layer A) CELI indicators.

Instead of assumed thresholds (a WACC, a 'safe' leverage level), each indicator is scored by
where the company ranks among its industry peers on the same filed, point-in-time metric:

    percentile = 100 * (#peers strictly worse + 0.5 * #peers tied) / #peers

* Peers: S&P 500 members in the same GICS sector (non-financial companies) or, for banks, the
  Diversified + Regional Banks sub-industries. The company itself is never its own peer.
* Every peer metric is computed by the same pipeline, as of the same assessment date, from
  filings dated on or before it. Peers whose metric is missing are left out (never zero-filled).
* At least MIN_PEERS peers with a value are required, otherwise the indicator stays unavailable.
* Membership limitation: the constituent list is today's list, so it is not point-in-time.
  Assessments dated more than MEMBERSHIP_TOLERANCE_DAYS before the list date are refused.
* Scores are indicative: a percentile says how a company compares with large US peers, not
  whether the level is good in absolute terms.
"""
from __future__ import annotations

import csv
import statistics
from datetime import date
from pathlib import Path

MIN_PEERS = 10
MEMBERSHIP_TOLERANCE_DAYS = 365
LIST_DATE = "2026-11-16"
BANK_SUBS = {"Diversified Banks", "Regional Banks"}
SECTOR_ARCHETYPE = {"Information Technology": "tech", "Utilities": "utility", "Industrials": "industrial", "Energy": "industrial", "Materials": "industrial"}

# indicator -> [(input name, direction)]; +1: higher is better (capability) / higher is MORE fragile (risk)
CORP_SPEC = {
    "ROIC_5Y": [("roic_mean", +1)],
    "FCF_DUR": [("fcf_conversion_cum", +1)],
    "REV_DUR": [("revenue_drawdown_worst", -1), ("operating_margin_sd", -1)],
    "FIN_FRAG": [("net_debt_to_ebitda", +1), ("interest_cover", -1)],
}
BANK_SPEC = {
    "ROIC_5Y": [("roe_mean", +1)],
    "REV_DUR": [("revenue_drawdown_worst", -1), ("revenue_growth_sd", -1)],
}


def load_peer_list(path: str | Path) -> list[dict]:
    lines = [ln for ln in Path(path).read_text().splitlines() if not ln.startswith("#")]
    rows = list(csv.DictReader(lines))
    out = []
    for r in rows:
        if not (r.get("CIK") or "").strip().isdigit():
            continue
        sub, sector = r["GICS Sub-Industry"], r["GICS Sector"]
        model = "bank" if sub in BANK_SUBS else ("other_financial" if sector in {"Financials", "Real Estate"} else "corporate")
        out.append({"cik": f"{int(r['CIK']):010d}", "symbol": r["Symbol"], "name": r["Security"], "sector": sector, "sub_industry": sub,
                    "model": model, "group": "Banks" if model == "bank" else sector,
                    "archetype": "financial" if model == "bank" else SECTOR_ARCHETYPE.get(sector, "general")})
    return out


def _mean(xs):
    return statistics.fmean(xs) if len(xs) >= 3 else None


def _sd(xs):
    return statistics.pstdev(xs) if len(xs) >= 3 else None


def indicator_inputs(hist: dict, metrics: list[dict]) -> dict:
    """Raw, filed-figure inputs for the peer scale (None = not computable)."""
    def ser(name):
        return [m["value"] for m in metrics if m["metric"] == name and m["value"] is not None]

    def latest(name):
        last = hist["periods"][-1] if hist["periods"] else None
        m = next((m for m in metrics if m["metric"] == name and m["period_end"] == last), None)
        return None if m is None else m["value"]

    ends = hist["periods"][-5:]
    rev = [s.value for s in (hist["items"]["revenue"].get(e) for e in hist["periods"]) if s is not None]
    dd = None
    if len(rev) >= 3:
        peak, dd = None, 0.0
        for v in rev:
            peak = v if peak is None else max(peak, v)
            if peak > 0:
                dd = max(dd, 1 - v / peak)
    out = {"periods": ends, "latest_period": hist["periods"][-1] if hist["periods"] else None,
           "revenue_drawdown_worst": dd, "revenue_growth_sd": _sd(ser("revenue_growth"))}
    if hist["model"] == "bank":
        out["roe_mean"] = _mean(ser("return_on_equity"))
        return out
    fcf, oi = [], []
    for e in ends:
        f = next((m["value"] for m in metrics if m["metric"] == "free_cash_flow" and m["period_end"] == e), None)
        o = hist["items"]["operating_income"].get(e)
        if f is not None and o is not None:
            fcf.append(f)
            oi.append(o.value)
    out.update({"roic_mean": _mean(ser("return_on_invested_capital")), "operating_margin_sd": _sd(ser("operating_margin")),
                "fcf_conversion_cum": (sum(fcf) / sum(oi)) if len(fcf) >= 3 and sum(oi) > 0 else None,
                "net_debt_to_ebitda": latest("net_debt_to_ebitda"), "interest_cover": latest("interest_cover")})
    return out


def percentile(value: float, peers: list[float], direction: int) -> float:
    v = value * direction
    ps = [p * direction for p in peers]
    below = sum(1 for p in ps if p < v)
    ties = sum(1 for p in ps if p == v)
    return 100.0 * (below + 0.5 * ties) / len(ps)


def score_indicators(model: str, asof: str, target: dict, peer_rows: list[dict], target_cik: str, group: str) -> dict:
    """{indicator: {score|None, parts, reason}}. Parts record value, peer count and percentile."""
    if (date.fromisoformat(LIST_DATE) - date.fromisoformat(asof)).days > MEMBERSHIP_TOLERANCE_DAYS:
        return {ind: {"score": None, "parts": [], "reason": "Peer membership list is not point-in-time for this assessment date"}
                for ind in (BANK_SPEC if model == "bank" else CORP_SPEC)}
    peers = [p for p in peer_rows if p["group"] == group and p["cik"] != target_cik and p.get("asof") == asof]
    spec = BANK_SPEC if model == "bank" else CORP_SPEC
    out = {}
    for ind, parts in spec.items():
        res = []
        for name, direction in parts:
            v = target.get(name)
            vals = [p["inputs"].get(name) for p in peers if p["inputs"].get(name) is not None]
            if v is None:
                res.append({"input": name, "direction": direction, "value": None, "peers": len(vals), "percentile": None, "reason": "company value not computable"})
            elif len(vals) < MIN_PEERS:
                res.append({"input": name, "direction": direction, "value": v, "peers": len(vals), "percentile": None, "reason": f"fewer than {MIN_PEERS} peers with a value"})
            else:
                res.append({"input": name, "direction": direction, "value": v, "peers": len(vals), "percentile": round(percentile(v, vals, direction), 2),
                            "peer_median": statistics.median(vals)})
        got = [r["percentile"] for r in res if r["percentile"] is not None]
        out[ind] = {"score": round(statistics.fmean(got), 2) if got else None, "parts": res, "group": group, "peer_count": len(peers),
                    "reason": "" if got else "No input could be scored against peers"}
    return out
