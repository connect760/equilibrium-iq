"""CELI-100 v3.0 — deterministic calculation.

Pure functions only: no I/O, no clock, no randomness, no AI. The same entity
snapshot always produces the same result, and the result records every
intermediate so it can be audited and re-run.

Input contract (an "entity snapshot", plain dict):
    archetype: str            one of ARCHETYPES (default 'general')
    cutoff: 'YYYY-MM-DD'      evidence cutoff; governs which events are live
    rol: float | None         entity-level rule-of-law score in [0,1]
    provisional: bool
    ev: {indicator_id: {state, cls, method, score, A, B, conf, ...}}
    events: [ {id, conductId, kind, date, resolvedDate, remediatedDate,
               proximity, rol, materiality, ...} ]

Sector parameters are PRIORS pending calibration (see README, validation plan).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..indicators import COMPONENTS
from ..numeric import days_between, is_num, r2, r4, sigmoid, softplus

VERSION = "CELI-100 v3.0"

MIN_COVERAGE = 0.80
MIN_DCS = 50.0
BETA = 25.0  # conservative baseline for unavailable / conflicting / abstained evidence
ABSTAIN_CONF = 0.85
ABSTAIN_GAP = 20.0
SOFTPLUS_H = 2.0
HALF_LIFE_ADJ_Q = 8.0
HALF_LIFE_CONT_Q = 4.0
E_LEGAL_MAX = 30.0
S_FLOOR = 0.5
DAYS_PER_QUARTER = 91.3125


@dataclass(frozen=True)
class Archetype:
    label: str
    wP: float
    wR: float
    wL: float
    tau: float
    k: float
    Emax: float

    def __post_init__(self):
        if abs(self.wP + self.wR + self.wL - 1.0) > 1e-12:
            raise ValueError("component weights must sum to 1")
        if not self.k < min(self.wP, self.wR):
            raise ValueError("monotonicity constraint violated: k must be < min(wP, wR)")


ARCHETYPES = {
    "tech": Archetype("High-growth technology", 0.40, 0.40, 0.20, 25, 0.20, 15),
    "industrial": Archetype("Asset-heavy industrials", 0.35, 0.45, 0.20, 20, 0.25, 15),
    "utility": Archetype("Regulated utilities", 0.30, 0.50, 0.20, 30, 0.20, 12),
    "financial": Archetype("Financials", 0.30, 0.50, 0.20, 15, 0.25, 15),
    "general": Archetype("General (unclassified)", 0.40, 0.40, 0.20, 20, 0.25, 15),
}

VERIFICATION = {
    "independently_assured": 1.00,
    "signed_telemetry": 0.97,
    "statutory_filing": 0.95,
    "government_inspection": 0.95,
    "externally_corroborated": 0.90,
    "company_reported": 0.80,
}

# disclosure state -> treatment
TREATMENT = {
    "disclosed": "score",
    "not_disclosed": "zero",
    "unsupported_claim": "zero",
    "unavailable": "base",
    "conflicting": "base",
    "under_verification": "base",
    "not_applicable": "exclude",
}

ADJUDICATED_SIGMA = {"settlement_order": 0.15, "finding": 0.25, "final": 0.30, "catastrophic": 0.50}
CONTESTED_THETA = {"investigation": 6, "whistleblower": 8, "restatement": 15, "audit_qualification": 15, "charge": 20, "going_concern": 25}
DISPLAY_ONLY = {"allegation"}
PROXIMITY = {"parent": 1.0, "wholly_owned": 0.7, "partial": 0.4, "jv": 0.25}
DEFAULT_ROL = 0.6


def verification_factor(cls: str | None) -> float:
    return VERIFICATION.get(cls or "", VERIFICATION["company_reported"])


def rule_of_law_weight(rho: float) -> float:
    """omega = 0.4 + 0.6 * rho, rho in [0, 1] (WJP Rule of Law Index overall score)."""
    return 0.4 + 0.6 * rho


def resolve_indicator(component: str, e: dict, rater: str | None = None) -> dict:
    """Return treatment, raw value x, verification v, contribution y, abstention reason."""
    treat = TREATMENT.get(e.get("state"), "base")
    x = v = abst = None
    if treat == "score":
        A, B = e.get("A"), e.get("B")
        dual = e.get("method") == "dual_blind" and is_num(A) and is_num(B)
        if dual:
            x = A if rater == "A" else B if rater == "B" else (A + B) / 2
        else:
            x = e.get("score")
        conf = e.get("conf")
        if not is_num(x):
            treat, abst = "base", "No value recorded"
        elif is_num(conf) and conf < ABSTAIN_CONF:
            treat, abst = "base", f"Extraction confidence {conf:.2f} < {ABSTAIN_CONF}"
        elif dual and abs(A - B) > ABSTAIN_GAP:
            treat, abst = "base", f"Rater disagreement {abs(A - B):g} > {ABSTAIN_GAP:g}"
        else:
            v = verification_factor(e.get("cls"))
    if treat == "score":
        y = v * (100 - x) if component == "risk" else v * x
    elif treat == "zero":
        y = 0.0
    elif treat == "base":
        y = BETA
    else:
        y = None
    return {"treat": treat, "x": x, "v": v, "y": y, "abstention": abst}


def aggregate(component: str, ev: dict, rater: str | None = None) -> dict:
    """Weighted mean of y over applicable indicators; coverage = scored weight / applicable weight."""
    wa = ws = s = 0.0
    rows = []
    for ind in COMPONENTS[component]:
        e = ev.get(ind.id) or {"state": "unavailable"}
        r = resolve_indicator(component, e, rater)
        if r["treat"] != "exclude":
            wa += ind.weight
            s += ind.weight * r["y"]
            if r["treat"] == "score":
                ws += ind.weight
        rows.append({"id": ind.id, "w": ind.weight, **r})
    for row in rows:
        row["w_norm"] = 0.0 if row["treat"] == "exclude" or not wa else row["w"] / wa
        row["contribution"] = 0.0 if row["treat"] == "exclude" else row["w_norm"] * row["y"]
    return {"value": r2(s / wa) if wa > 0 else None, "coverage": r2(ws / wa) if wa > 0 else 0.0, "rows": rows}


def data_confidence(parts: dict, arch: Archetype) -> float:
    cw = {"cap": arch.wP, "risk": arch.wR, "adapt": arch.wL}
    dw = dc = 0.0
    for k, part in parts.items():
        for row in part["rows"]:
            if row["treat"] == "exclude":
                continue
            w = cw[k] * row["w"]
            dw += w
            c = row["v"] if row["treat"] == "score" else 0.25 if row["treat"] == "base" else 0.0
            dc += w * c
    return r2(100 * dc / dw) if dw else 0.0


def legal_layer(snapshot: dict) -> dict:
    """Two-tier legal mechanism.

    Adjudicated events reduce S_gov multiplicatively; contested events add points to
    E_legal. Events sharing a conductId are grouped and only the strongest counts.
    """
    ref = snapshot.get("cutoff") or "9999-12-31"
    ent_rol = snapshot.get("rol")
    groups_a: dict[str, float] = {}
    groups_b: dict[str, float] = {}
    rows = []
    for e in snapshot.get("events") or []:
        live = bool(e.get("date")) and e["date"] <= ref
        q = max(0.0, days_between(e["date"], ref)) / DAYS_PER_QUARTER if live else 0.0
        g = PROXIMITY.get(e.get("proximity"), 1.0)
        rho = e.get("rol") if is_num(e.get("rol")) else (ent_rol if is_num(ent_rol) else DEFAULT_ROL)
        w = rule_of_law_weight(rho)
        m = max(0.0, min(1.0, e["materiality"])) if is_num(e.get("materiality")) else 1.0
        a = b = d = 0.0
        status = "not_yet_effective"
        kind = e.get("kind")
        if live and kind in ADJUDICATED_SIGMA:
            remediated = bool(e.get("remediatedDate")) and e["remediatedDate"] <= ref
            d = math.pow(2, -q / HALF_LIFE_ADJ_Q) * (0.5 if remediated else 1.0)
            a = ADJUDICATED_SIGMA[kind] * m * g * w * d
            status = "adjudicated"
        elif live and kind in CONTESTED_THETA:
            resolved = bool(e.get("resolvedDate")) and e["resolvedDate"] <= ref
            if resolved:
                status = "resolved"
            else:
                d = math.pow(2, -q / HALF_LIFE_CONT_Q)
                b = CONTESTED_THETA[kind] * m * g * w * d
                status = "contested_active"
        elif live:
            status = "display_only"
        key = e.get("conductId") or e.get("id")
        if a > groups_a.get(key, 0.0):
            groups_a[key] = a
        if b > groups_b.get(key, 0.0):
            groups_b[key] = b
        rows.append({"id": e.get("id"), "kind": kind, "group": key, "status": status, "m": m, "g": g, "omega": w, "decay": d, "s_reduction": a, "e_points": b})
    prod = 1.0
    for a in groups_a.values():
        prod *= 1 - a
    S = r4(max(S_FLOOR, prod))
    E_legal = r2(min(E_LEGAL_MAX, sum(groups_b.values())))
    for row in rows:
        row["binding"] = (row["s_reduction"] > 0 and groups_a.get(row["group"]) == row["s_reduction"]) or (row["e_points"] > 0 and groups_b.get(row["group"]) == row["e_points"])
    return {"S_gov": S, "E_legal": E_legal, "rows": rows}


def balance_penalty(gap: float, arch: Archetype) -> tuple[float, float]:
    """Smooth, bounded equilibrium penalty and its derivative d(E_bal)/d(gap).

    E_bal = Emax * tanh(k * softplus_h(gap - tau) / Emax); 0 < dE/dgap < k.
    """
    z = gap - arch.tau
    th = math.tanh(arch.k * softplus(z, SOFTPLUS_H) / arch.Emax)
    deriv = arch.k * (1 - th * th) * sigmoid(z / SOFTPLUS_H)
    return arch.Emax * th, deriv


def compute(snapshot: dict, rater: str | None = None) -> dict:
    arch = ARCHETYPES.get(snapshot.get("archetype"), ARCHETYPES["general"])
    ev = snapshot.get("ev") or {}
    parts = {k: aggregate(k, ev, rater) for k in ("cap", "risk", "adapt")}
    P, C, L = parts["cap"]["value"], parts["risk"]["value"], parts["adapt"]["value"]
    R_tilde = None if C is None else r2(100 - C)
    dcs = data_confidence(parts, arch)
    lg = legal_layer(snapshot)
    S, E_legal = lg["S_gov"], lg["E_legal"]
    R_eff = None if R_tilde is None else r2(min(100.0, R_tilde + E_legal))
    RC = None if R_eff is None else r2(100 - R_eff)
    gap = E_bal = base = raw = celi = None
    dEb = 0.0
    sens = None
    if None not in (P, RC, L):
        gap = r2(abs(P - RC))
        eb, dEb = balance_penalty(gap, arch)
        E_bal = r2(eb)
        base = r2(arch.wP * P + arch.wR * RC + arch.wL * L - E_bal)
        raw = r2(base * S)
        celi = r2(min(100.0, max(0.0, raw)))
        sg = (P > RC) - (P < RC)
        clamped = raw < 0 or raw > 100
        dP = 0.0 if clamped else S * (arch.wP - dEb * sg)
        dRC = 0.0 if clamped else S * (arch.wR + dEb * sg)
        dL = 0.0 if clamped else S * arch.wL
        sens = {"dP": r4(dP), "dRC": r4(dRC), "dL": r4(dL), "dE_legal": r4(-dRC), "dS_gov": 0.0 if clamped else r4(base)}
    reasons = []
    labels = {"cap": "Constructive Capability", "risk": "Systemic Risk", "adapt": "Adaptability"}
    for k in ("cap", "risk", "adapt"):
        if parts[k]["coverage"] < MIN_COVERAGE:
            reasons.append(f"{labels[k]} scored coverage {parts[k]['coverage']:.0%} below {MIN_COVERAGE:.0%}")
    if dcs < MIN_DCS:
        reasons.append(f"Data Confidence {dcs:.1f} below {MIN_DCS:g}")
    eligible = not reasons and celi is not None
    status = "insufficient" if not eligible else ("provisional" if snapshot.get("provisional") else "final")
    return {
        "methodology": VERSION,
        "archetype": arch.label,
        "parameters": {"wP": arch.wP, "wR": arch.wR, "wL": arch.wL, "tau": arch.tau, "k": arch.k, "Emax": arch.Emax},
        "P": P, "C": C, "R_tilde": R_tilde, "E_legal": E_legal, "R_eff": R_eff, "risk_control": RC, "L": L,
        "gap": gap, "E_bal": E_bal, "dE_bal_dgap": dEb, "base": base, "S_gov": S, "raw": raw, "celi": celi,
        "dcs": dcs, "coverage": {k: parts[k]["coverage"] for k in parts}, "components": parts, "legal": lg,
        "eligible": eligible, "status": status, "reasons": reasons, "sensitivity": sens,
    }


def summarize(result: dict) -> dict:
    """The fields the reference engine stores in a published record."""
    return {
        "P": result["P"], "Rt": result["R_tilde"], "El": result["E_legal"], "Reff": result["R_eff"], "L": result["L"],
        "gap": result["gap"], "Eb": result["E_bal"], "S": result["S_gov"], "raw": result["raw"], "celi": result["celi"],
        "dcs": result["dcs"], "status": result["status"], "archetype": result["archetype"], "coverage": dict(result["coverage"]),
    }


def rater_band(snapshot: dict) -> tuple[float, float] | None:
    a, b = compute(snapshot, "A")["celi"], compute(snapshot, "B")["celi"]
    if a is None or b is None:
        return None
    return (min(a, b), max(a, b))
