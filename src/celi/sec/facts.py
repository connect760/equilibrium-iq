"""XBRL companyfacts parsing, unit normalisation and point-in-time selection.

Point-in-time rule: for an assessment date D, a value is taken only from filings with
filed <= D. Among those, the latest filing wins (so a 10-K/A or a later 10-K that restates a
comparative period replaces the earlier figure from that date on). The first-filed value is
always kept beside it, and a difference is flagged as a restatement. Filings after D are never
consulted when choosing a value.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

ANNUAL_FORMS = {"10-K", "10-K/A", "10-KT", "10-KT/A"}
ANNUAL_MIN_DAYS, ANNUAL_MAX_DAYS = 350, 380  # 52/53-week years included; quarters, half-years and transition periods excluded


class UnitError(ValueError):
    pass


@dataclass(frozen=True)
class Fact:
    taxonomy: str
    concept: str
    unit: str
    value: int | float
    start: str | None
    end: str
    fy: int | None
    fp: str | None
    form: str
    filed: str
    accession: str
    frame: str | None = None

    @property
    def is_instant(self) -> bool:
        return self.start is None

    @property
    def days(self) -> int | None:
        return None if self.start is None else (date.fromisoformat(self.end) - date.fromisoformat(self.start)).days

    @property
    def is_annual_duration(self) -> bool:
        return self.days is not None and ANNUAL_MIN_DAYS <= self.days <= ANNUAL_MAX_DAYS


def parse_companyfacts(cf: dict) -> list[Fact]:
    out = []
    for tax, concepts in (cf.get("facts") or {}).items():
        for concept, body in concepts.items():
            for unit, rows in (body.get("units") or {}).items():
                for r in rows:
                    if r.get("val") is None or not r.get("end") or not r.get("filed") or not r.get("accn"):
                        continue  # incomplete rows are never repaired or guessed
                    out.append(Fact(tax, concept, unit, r["val"], r.get("start"), r["end"], r.get("fy"), r.get("fp"),
                                    r.get("form") or "", r["filed"], r["accn"], r.get("frame")))
    return out


# ---- units -------------------------------------------------------------------------------
MONETARY = "USD"
UNIT_KINDS = {"monetary": {"USD"}, "per_share": {"USD/shares"}, "shares": {"shares"}, "pure": {"pure"}}


def normalize_unit(unit: str, kind: str) -> str:
    """Return the canonical unit or raise. No FX conversion is ever performed."""
    allowed = UNIT_KINDS.get(kind)
    if allowed is None:
        raise UnitError(f"Unknown unit kind {kind!r}")
    if unit in allowed:
        return unit
    if kind == "monetary" and len(unit) == 3 and unit.isalpha() and unit.isupper():
        raise UnitError(f"Monetary value reported in {unit}; no FX conversion is applied, value treated as unsupported")
    raise UnitError(f"Unit {unit!r} is not valid for a {kind} item")


def to_millions(value: int | float | None) -> float | None:
    return None if value is None else value / 1_000_000


# ---- point-in-time -----------------------------------------------------------------------
@dataclass
class Selection:
    concept: str
    taxonomy: str
    unit: str
    start: str | None
    end: str
    value: int | float
    accession: str
    form: str
    filed: str
    original_value: int | float
    original_accession: str
    original_filed: str
    versions_visible: int
    restated: bool
    amended: bool
    history: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in ("concept", "taxonomy", "unit", "start", "end", "value", "accession", "form", "filed",
                                              "original_value", "original_accession", "original_filed", "versions_visible", "restated", "amended", "history")}


class FactIndex:
    def __init__(self, facts: list[Fact]):
        self.by_concept: dict[tuple[str, str], list[Fact]] = {}
        for f in facts:
            self.by_concept.setdefault((f.taxonomy, f.concept), []).append(f)

    def concept_rows(self, concept: str, taxonomy: str = "us-gaap") -> list[Fact]:
        return self.by_concept.get((taxonomy, concept), [])

    def select(self, concept: str, end: str, asof: str, *, flow: bool, kind: str = "monetary",
               forms: set[str] = ANNUAL_FORMS, taxonomy: str = "us-gaap") -> Selection | None:
        """Value of `concept` for the annual period ending `end`, as known on `asof`. None means missing."""
        cands = []
        for f in self.concept_rows(concept, taxonomy):
            if f.end != end or f.filed > asof or f.form not in forms:
                continue
            if flow != (not f.is_instant):
                continue
            if flow and not f.is_annual_duration:
                continue
            try:
                normalize_unit(f.unit, kind)
            except UnitError:
                continue
            cands.append(f)
        if not cands:
            return None
        if flow:  # if several annual windows end on the same date, keep the one closest to a year
            best_start = min({f.start for f in cands}, key=lambda s: abs((date.fromisoformat(end) - date.fromisoformat(s)).days - 365))
            cands = [f for f in cands if f.start == best_start]
        # de-duplicate one value per accession (the same filing can tag a fact more than once)
        per_acc: dict[str, Fact] = {}
        for f in sorted(cands, key=lambda f: (f.filed, f.accession)):
            per_acc.setdefault(f.accession, f)
        ordered = sorted(per_acc.values(), key=lambda f: (f.filed, f.form.endswith("/A"), f.accession))
        first, cur = ordered[0], ordered[-1]
        hist = [{"value": f.value, "accession": f.accession, "form": f.form, "filed": f.filed} for f in ordered]
        return Selection(concept, taxonomy, cur.unit, cur.start, end, cur.value, cur.accession, cur.form, cur.filed,
                         first.value, first.accession, first.filed, len(ordered),
                         restated=any(h["value"] != first.value for h in hist), amended=cur.form.endswith("/A"), history=hist)


def fiscal_year_ends(index: FactIndex, asof: str, anchor_concepts: list[str]) -> list[str]:
    """Fiscal-year end dates of the company's own annual reports filed on or before `asof`.

    A 10-K's own period is the latest annual-duration end date it reports (comparative years
    end earlier). Original 10-Ks only, so an amendment never invents a new fiscal year.
    The companyfacts 'fy' field is NOT used: it is the fiscal year of the filing, not of the fact.
    """
    own: dict[str, str] = {}
    for c in anchor_concepts:
        for f in index.concept_rows(c):
            if f.form in {"10-K", "10-KT"} and f.filed <= asof and f.is_annual_duration:
                if f.end > own.get(f.accession, ""):
                    own[f.accession] = f.end
    return sorted(set(own.values()))
