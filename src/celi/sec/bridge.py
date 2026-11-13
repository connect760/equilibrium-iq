"""CELI-100 calculation integration for real SEC data.

The engine's indicators are 0-100 scores. Turning a filed ratio into such a score needs a
calibrated scale (e.g. a cost-of-capital benchmark or sector thresholds). None has been
calibrated, and none is assumed here. So every indicator is passed to the engine as
'unavailable', carrying the raw filed evidence it would be scored from, and the engine's own
coverage rule then returns 'insufficient evidence' instead of a number. When a calibrated
scale is published it is added to SCALES and the same evidence becomes scorable.
"""
from __future__ import annotations

from ..methodology import v3_0

SCALES: dict = {}  # indicator_id -> published, calibrated scoring function. Deliberately empty.


class SyntheticDataError(RuntimeError):
    pass


def assert_real(payload: dict):
    if payload.get("_synthetic"):
        raise SyntheticDataError("Synthetic test data cannot be used in a real company assessment")


CORP = {
    "ROIC_5Y": (["return_on_invested_capital", "return_on_equity"], "No calibrated cost-of-capital benchmark; WACC is not assumed"),
    "FCF_DUR": (["free_cash_flow", "fcf_to_operating_income"], "No calibrated scale for cash-flow conversion"),
    "REV_DUR": (["revenue_growth", "operating_margin"], "No calibrated volatility scale; the pilot found growth was penalised as volatility"),
    "FIN_FRAG": (["net_debt_to_ebitda", "interest_cover", "liabilities_to_assets", "current_ratio"], "No sector leverage thresholds calibrated"),
    "OP_RES": (["revenue_growth"], "Needs a longer window (10y) and a calibrated drawdown scale"),
    "INNOV": (["rnd_to_revenue"], "R&D intensity alone does not measure innovation capability; analyst review needed"),
    "REINVEST": (["capex_to_revenue", "rnd_to_revenue"], "Reinvestment quality is an analyst judgement"),
}
BANKM = {
    "ROIC_5Y": (["return_on_equity", "return_on_assets"], "No calibrated cost-of-equity benchmark; not assumed"),
    "REV_DUR": (["revenue_growth", "efficiency_ratio"], "No calibrated volatility scale"),
    "FIN_FRAG": (["equity_to_assets", "loans_to_deposits", "deposits_to_assets"], "Bank fragility needs CET1, LCR and NSFR from regulatory reports (FR Y-9C / Pillar 3), not in XBRL companyfacts"),
    "OP_RES": (["revenue_growth", "provision_to_loans"], "Needs a longer window and a calibrated scale"),
}
UNSUPPORTED = {
    "REV_DIV": "Segment and product revenue are dimensional XBRL, not in companyfacts; needs filing-level XBRL parsing",
    "ENV_OUT": "Emissions and environmental outcomes are in sustainability reports / EPA data, not SEC XBRL",
    "WORKFORCE": "Human-capital disclosures are narrative (10-K Item 1); needs analyst extraction",
    "GOV_CONC": "Board and control concentration need DEF 14A proxy extraction",
    "AUDIT_INT": "Needs auditor's report, Item 9A controls and restatement review; amendment/restatement flags below are an input, not a score",
    "REG_LEGAL": "Needs enforcement databases (SEC litigation, DOJ, CFPB, EPA) and contingency notes",
    "OP_HARM": "Needs verified incident sources (OSHA, EPA ECHO, recalls)",
    "BM_ADAPT": "Business-model adaptability is an analyst judgement",
    "GEO_SUPPLY": "Geographic revenue is dimensional XBRL; supply-chain risk needs risk-factor extraction",
}


def indicator_status(model: str, metrics: list[dict]) -> dict:
    spec = BANKM if model == "bank" else CORP
    have = {m["metric"] for m in metrics if m["value"] is not None}
    out = {}
    for ind in [i.id for i in v3_0.COMPONENTS["cap"] + v3_0.COMPONENTS["risk"] + v3_0.COMPONENTS["adapt"]]:
        if model == "bank" and ind == "FCF_DUR":
            out[ind] = {"status": "not_applicable", "reason": "Free-cash-flow conversion is not meaningful for a bank", "evidence_metrics": []}
        elif ind in spec:
            names, why = spec[ind]
            avail = [n for n in names if n in have]
            out[ind] = {"status": "evidence_available_not_scored" if avail else "evidence_missing", "reason": why if avail else "Required filed figures not reported",
                        "evidence_metrics": avail, "missing_metrics": [n for n in names if n not in have]}
        else:
            out[ind] = {"status": "unsupported_by_sec_xbrl", "reason": UNSUPPORTED.get(ind, "Not derivable from SEC XBRL"), "evidence_metrics": []}
    return out


def run_engine(model: str, asof: str, status: dict) -> dict:
    ev = {}
    for ind, s in status.items():
        if s["status"] == "not_applicable":
            ev[ind] = {"state": "not_applicable", "score": None}
        elif ind in SCALES:  # pragma: no cover - no calibrated scales exist yet
            raise NotImplementedError
        else:
            ev[ind] = {"state": "unavailable", "score": None, "raw": s["reason"]}
    snap = {"archetype": "financial" if model == "bank" else "general", "cutoff": asof, "rol": None, "provisional": True, "ev": ev, "events": []}
    return v3_0.compute(snap)
