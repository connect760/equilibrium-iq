# GIP Equilibrium IQ — CELI-100 engine and SEC data pipeline

## Layout
- `src/celi/methodology/v3_0.py`: CELI-100 v3.0 engine. Pure functions, mirrored exactly by the Equilibra app.
- `src/celi/sec/`: official SEC pipeline for real companies.
  - `client.py`: declared User-Agent, request limit of 5 per second, retries, immutable store of every SEC response (identified by sha256).
  - `registry.py`: company identity checks, plus a register of every filing by accession number with its original filing date and archive address.
  - `facts.py`: reads XBRL companyfacts, normalises units (no currency conversion), and selects values as known on a given date, keeping amendments and restatements.
  - `statements.py`: maps XBRL tags to statement items and builds the five-year history.
  - `metrics.py`: computes only ratios defined by filed figures. Banks and non-financial companies have separate formulas.
  - `store.py`: SQLite evidence database. Sources, filings and facts can only be added to, never changed or deleted.
  - `bridge.py`: connects the data to the CELI engine. No calibrated scoring scales exist yet, so every indicator is recorded as unscored and the engine reports "insufficient evidence".
  - `pipeline.py`: the fetch and process steps, plus reports C, D and E.
- `config/companies.json`: the company registry. The SEC User-Agent comes from the `SEC_USER_AGENT` repository variable (or a local, git-ignored `config/sec_user_agent.txt`).
- `tests/`: automated tests. **Synthetic data lives only in `tests/fixtures/synthetic/`** and carries the flag `_synthetic: true`; the pipeline refuses it in real assessments.
- `src/celi/sec_xbrl.py` and `pilot/`: the earlier pilot. Its scoring priors (8% WACC, leverage scales) are uncalibrated and are **not** used for real-company assessments.

## Run
```
PYTHONPATH=src python -m celi.sec selftest                  # A: one live request to SEC
PYTHONPATH=src python -m celi.sec fetch [--documents]       # B: download into data/raw
PYTHONPATH=src SEC_LIVE=1 python -m pytest -v               # F: tests, including the live SEC test
PYTHONPATH=src python -m celi.sec process --asof 2026-11-13 # C, D, E: written to reports/
```
GitHub Actions: `.github/workflows/sec-pipeline.yml` runs all of the above when started manually and every week, then commits `data/` and `reports/`.

## Point-in-time rule
For an assessment date D, only filings with a filing date on or before D are used. The latest of those supplies the value. The first-filed value is always kept beside it, and any difference is flagged as a restatement. Nothing filed after D is consulted.
