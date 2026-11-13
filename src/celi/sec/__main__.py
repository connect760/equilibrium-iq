"""python -m celi.sec fetch [--documents]      download from SEC into data/raw (needs SEC access)
python -m celi.sec process --asof YYYY-MM-DD  build the provenance DB, metrics, CELI run and reports C-E
python -m celi.sec selftest                   one live request to confirm the SEC connection (deliverable A)"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .client import RawStore, SecClient, load_user_agent, submissions_url
from .pipeline import fetch, process

ROOT = Path(__file__).resolve().parents[3]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="celi.sec")
    ap.add_argument("cmd", choices=["fetch", "process", "selftest"])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--asof", default=date.today().isoformat())
    ap.add_argument("--documents", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    raw = RawStore(root / "data" / "raw")
    if a.cmd in ("fetch", "selftest"):
        client = SecClient(load_user_agent(root), raw)
        if a.cmd == "selftest":
            rec = client.get(submissions_url("789019"), "selftest")
            body = json.loads(raw.read(rec))
            print(json.dumps({"ok": True, "url": rec["url"], "status": rec["status"], "bytes": rec["bytes"], "sha256": rec["sha256"],
                              "fetched_at": rec["fetched_at"], "entity": body.get("name"), "cik": body.get("cik")}, indent=1))
            return 0
        log = fetch(root, client, a.documents)
        print(f"fetched {len(log)} objects in {client.requests} requests")
        return 0
    ds = process(root, raw, root / "data" / "evidence.sqlite", a.asof, root / "reports")
    for c in ds["companies"]:
        print(c["ticker"], c["profile"]["name"], "periods", c["periods"], "facts", c["counts"]["facts"], "celi", c["celi"]["status"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
