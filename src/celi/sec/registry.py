"""Company identifier registry and filing / accession-number registry (from SEC submissions JSON)."""
from __future__ import annotations

from .client import archive_url, cik10, filing_index_url

# SIC codes handled by the bank model. Other financials (insurers, brokers, REITs) have no model yet.
BANK_SIC = {"6021", "6022", "6029", "6035", "6036"}
FORMS_OF_INTEREST = {"10-K", "10-K/A", "10-KT", "10-KT/A", "10-Q", "10-Q/A", "DEF 14A", "DEFA14A", "8-K", "8-K/A", "20-F", "20-F/A"}


class IdentityError(ValueError):
    pass


def check_identity(requested_cik, payload: dict, expect_name: str | None = None) -> None:
    """Fail if a payload is not for the requested CIK, or the registered name does not match expectations."""
    got = payload.get("cik")
    if got is None or cik10(got) != cik10(requested_cik):
        raise IdentityError(f"Payload CIK {got!r} does not match requested CIK {cik10(requested_cik)}")
    name = (payload.get("entityName") or payload.get("name") or "").upper()
    if expect_name and expect_name.upper() not in name:
        raise IdentityError(f"CIK {cik10(requested_cik)} is registered to {name!r}, expected a name containing {expect_name!r}")


def company_profile(sub: dict, model_declared: str) -> dict:
    sic = str(sub.get("sic") or "")
    detected = "bank" if sic in BANK_SIC else ("financial_other" if sic.startswith("6") and sic[:2] in {"60", "61", "62", "63", "64", "67"} else "corporate")
    return {
        "cik": cik10(sub["cik"]), "name": sub.get("name"), "tickers": sub.get("tickers") or [], "exchanges": sub.get("exchanges") or [],
        "sic": sic, "sic_description": sub.get("sicDescription"), "fiscal_year_end": sub.get("fiscalYearEnd"),
        "entity_type": sub.get("entityType"), "filer_category": sub.get("category"), "state_of_incorporation": sub.get("stateOfIncorporation"),
        "former_names": sub.get("formerNames") or [], "model_declared": model_declared, "model_detected": detected,
        "model_conflict": model_declared != detected,
    }


def _columns(block: dict) -> list[dict]:
    keys = list(block)
    n = len(block.get("accessionNumber", []))
    return [{k: block[k][i] for k in keys if i < len(block[k])} for i in range(n)]


def filings_table(cik, sub: dict, pages: list[dict] = (), forms: set[str] | None = FORMS_OF_INTEREST) -> list[dict]:
    """Every filing in the submissions history (recent block + older pages), de-duplicated by accession."""
    rows = _columns((sub.get("filings") or {}).get("recent") or {})
    for p in pages:
        rows += _columns(p)
    out, seen = [], set()
    for r in rows:
        acc, form = r.get("accessionNumber"), r.get("form", "")
        if not acc or acc in seen or (forms and form not in forms):
            continue
        seen.add(acc)
        doc = r.get("primaryDocument") or ""
        out.append({
            "cik": cik10(cik), "accession": acc, "form": form, "base_form": form.removesuffix("/A"), "is_amendment": form.endswith("/A"),
            "filing_date": r.get("filingDate") or None, "report_date": r.get("reportDate") or None, "acceptance": r.get("acceptanceDateTime") or None,
            "primary_document": doc or None, "is_xbrl": bool(r.get("isXBRL")),
            "url_primary": archive_url(cik, acc, doc) if doc else None, "url_index": filing_index_url(cik, acc),
        })
    return sorted(out, key=lambda r: (r["filing_date"] or "", r["accession"]))


def pages_needed(sub: dict, since: str) -> list[str]:
    """Older submission pages whose date range reaches back to `since`."""
    return [f["name"] for f in (sub.get("filings") or {}).get("files") or [] if (f.get("filingTo") or "9999") >= since]
