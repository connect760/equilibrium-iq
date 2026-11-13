"""Evidence provenance database (SQLite). Source, filing and fact tables are insert-only:
UPDATE and DELETE are rejected by triggers, so historical information can never be replaced
silently. A changed value arrives as a new row with its own accession and filing date."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_sources (sha256 TEXT, url TEXT, kind TEXT, bytes INTEGER, fetched_at TEXT, last_modified TEXT, object TEXT,
  PRIMARY KEY (sha256, url));
CREATE TABLE IF NOT EXISTS companies (cik TEXT, name TEXT, tickers TEXT, sic TEXT, sic_description TEXT, fiscal_year_end TEXT,
  model_declared TEXT, model_detected TEXT, source_sha256 TEXT, PRIMARY KEY (cik, source_sha256));
CREATE TABLE IF NOT EXISTS filings (cik TEXT, accession TEXT, form TEXT, base_form TEXT, is_amendment INTEGER, filing_date TEXT, report_date TEXT,
  acceptance TEXT, primary_document TEXT, url_primary TEXT, url_index TEXT, is_xbrl INTEGER, source_sha256 TEXT, PRIMARY KEY (cik, accession));
CREATE TABLE IF NOT EXISTS facts (cik TEXT, taxonomy TEXT, concept TEXT, unit TEXT, value TEXT, start TEXT, "end" TEXT, fy INTEGER, fp TEXT,
  form TEXT, filed TEXT, accession TEXT, frame TEXT, source_sha256 TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS facts_identity ON facts (cik, taxonomy, concept, unit, COALESCE(start, ''), "end", accession, value);
CREATE TABLE IF NOT EXISTS assessments (id TEXT PRIMARY KEY, cik TEXT, asof TEXT, created_at TEXT, methodology TEXT, input_hash TEXT, result TEXT);
CREATE TABLE IF NOT EXISTS selections (assessment_id TEXT, cik TEXT, item TEXT, period_end TEXT, concept TEXT, value TEXT, unit TEXT,
  accession TEXT, form TEXT, filed TEXT, original_value TEXT, original_accession TEXT, original_filed TEXT, restated INTEGER, amended INTEGER, versions_visible INTEGER);
CREATE TABLE IF NOT EXISTS metrics (assessment_id TEXT, cik TEXT, metric TEXT, period_end TEXT, value REAL, status TEXT, formula TEXT, inputs TEXT, missing TEXT, note TEXT);
CREATE INDEX IF NOT EXISTS facts_concept ON facts (cik, concept, "end");
"""
IMMUTABLE = ("raw_sources", "companies", "filings", "facts", "assessments")


def connect(path: str | Path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    for t in IMMUTABLE:
        for op in ("UPDATE", "DELETE"):
            db.execute(f"CREATE TRIGGER IF NOT EXISTS no_{op.lower()}_{t} BEFORE {op} ON {t} BEGIN SELECT RAISE(ABORT, '{t} is append-only'); END")
    db.commit()
    return db


def num_text(v) -> str | None:
    """Exact text form of a filed number (keeps integers exact; None stays NULL, never 0)."""
    return None if v is None else json.dumps(v)


def add_source(db, rec: dict):
    db.execute("INSERT OR IGNORE INTO raw_sources VALUES (?,?,?,?,?,?,?)",
               (rec["sha256"], rec["url"], rec.get("kind"), rec.get("bytes"), rec.get("fetched_at"), rec.get("last_modified"), rec.get("object")))


def add_company(db, prof: dict, sha: str):
    db.execute("INSERT OR IGNORE INTO companies VALUES (?,?,?,?,?,?,?,?,?)",
               (prof["cik"], prof["name"], ",".join(prof["tickers"]), prof["sic"], prof["sic_description"], prof["fiscal_year_end"],
                prof["model_declared"], prof["model_detected"], sha))


def add_filings(db, rows: list[dict], sha: str):
    db.executemany("INSERT OR IGNORE INTO filings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   [(r["cik"], r["accession"], r["form"], r["base_form"], int(r["is_amendment"]), r["filing_date"], r["report_date"], r["acceptance"],
                     r["primary_document"], r["url_primary"], r["url_index"], int(r["is_xbrl"]), sha) for r in rows])


def add_facts(db, cik: str, facts, sha: str) -> int:
    before = db.total_changes
    db.executemany("INSERT OR IGNORE INTO facts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   [(cik, f.taxonomy, f.concept, f.unit, num_text(f.value), f.start, f.end, f.fy, f.fp, f.form, f.filed, f.accession, f.frame, sha) for f in facts])
    return db.total_changes - before


def add_assessment(db, aid: str, cik: str, asof: str, created: str, methodology: str, input_hash: str, result: dict, hist: dict, metrics: list[dict]):
    db.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?,?)", (aid, cik, asof, created, methodology, input_hash, json.dumps(result, sort_keys=True)))
    for item, by_end in hist["items"].items():
        for end, s in by_end.items():
            if s is None:
                db.execute("INSERT INTO selections (assessment_id, cik, item, period_end) VALUES (?,?,?,?)", (aid, cik, item, end))
            else:
                db.execute("INSERT INTO selections VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (aid, cik, item, end, s.concept, num_text(s.value), s.unit, s.accession, s.form, s.filed, num_text(s.original_value),
                            s.original_accession, s.original_filed, int(s.restated), int(s.amended), s.versions_visible))
    db.executemany("INSERT INTO metrics VALUES (?,?,?,?,?,?,?,?,?,?)",
                   [(aid, cik, m["metric"], m["period_end"], m["value"], m["status"], m["formula"], json.dumps(m["inputs"]), json.dumps(m["missing"]), m["note"]) for m in metrics])
