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
from .pipeline import build_peers, fetch, fetch_peers, process

ROOT = Path(__file__).resolve().parents[3]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="celi.sec")
    ap.add_argument("cmd", choices=["fetch", "process", "selftest", "fetch-peers", "build-peers"])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--asof", default=date.today().isoformat())
    ap.add_argument("--documents", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    raw = RawStore(root / "data" / "raw")
    if a.cmd == "fetch-peers":
        peer_raw = RawStore(root / "data" / "peer_raw")
        res = fetch_peers(root, SecClient(load_user_agent(root), peer_raw))
        print(json.dumps({"fetched": res["fetched"], "failed": len(res["failed"])}))
        (root / "data" / "peers").mkdir(parents=True, exist_ok=True)
        (root / "data" / "peers" / "fetch_failures.json").write_text(json.dumps(res["failed"], indent=1))
        return 0
    if a.cmd == "build-peers":
        doc = build_peers(root, RawStore(root / "data" / "peer_raw"), a.asof)
        print(json.dumps({"peers": len(doc["peers"]), "skipped": len(doc["skipped"])}))
        return 0
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
