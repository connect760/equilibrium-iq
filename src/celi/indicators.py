"""Indicator dictionary shared by all methodology versions (weights per version may differ)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Indicator:
    id: str
    name: str
    weight: float
    component: str  # 'cap' | 'risk' | 'adapt'


CAP = (
    Indicator("ROIC_5Y", "Return on invested capital", 0.25, "cap"),
    Indicator("FCF_DUR", "Cash-flow durability", 0.20, "cap"),
    Indicator("REINVEST", "Productive reinvestment", 0.20, "cap"),
    Indicator("REV_DUR", "Revenue & operating durability", 0.15, "cap"),
    Indicator("WORKFORCE", "Workforce & stakeholder stewardship", 0.10, "cap"),
    Indicator("ENV_OUT", "Environmental operating outcomes", 0.10, "cap"),
)
RISK = (
    Indicator("FIN_FRAG", "Financial fragility", 0.25, "risk"),
    Indicator("GOV_CONC", "Governance concentration", 0.20, "risk"),
    Indicator("AUDIT_INT", "Audit & reporting integrity", 0.20, "risk"),
    Indicator("REG_LEGAL", "Regulatory & legal record", 0.20, "risk"),
    Indicator("OP_HARM", "Verified operational & stakeholder harm", 0.15, "risk"),
)
ADAPT = (
    Indicator("OP_RES", "Operating resilience", 0.25, "adapt"),
    Indicator("BM_ADAPT", "Business-model adaptability", 0.25, "adapt"),
    Indicator("REV_DIV", "Revenue & product diversification", 0.20, "adapt"),
    Indicator("GEO_SUPPLY", "Geographic & supply-chain resilience", 0.15, "adapt"),
    Indicator("INNOV", "Innovation & transition capability", 0.15, "adapt"),
)
COMPONENTS = {"cap": CAP, "risk": RISK, "adapt": ADAPT}
ALL = CAP + RISK + ADAPT
IDS = tuple(i.id for i in ALL)

for _k, _group in COMPONENTS.items():
    assert abs(sum(i.weight for i in _group) - 1.0) < 1e-12, f"weights in {_k} must sum to 1"
