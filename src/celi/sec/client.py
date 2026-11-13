"""SEC EDGAR client: declared User-Agent, request throttling, retries, immutable raw store.

* Every request carries the declared User-Agent (SEC fair-access policy). The client refuses
  to run without one in the form "<organisation> <contact email>".
* Requests are throttled to MAX_RPS (default 5/s, half of SEC's published 10/s ceiling).
* 429/5xx and network errors are retried with backoff, honouring Retry-After.
* Every response body is stored content-addressed (sha256 of the decompressed body) and
  logged in an append-only manifest with URL, fetch time, status and size. A later fetch of
  the same URL that returns different bytes is stored beside the earlier one, never over it.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path

DATA_BASE = "https://data.sec.gov"
WWW_BASE = "https://www.sec.gov"
MAX_RPS = 5.0
RETRY_STATUS = {429, 500, 502, 503, 504}
UA_RE = re.compile(r"^\S.*\s<?[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}>?$")


class SecError(RuntimeError):
    pass


def validate_user_agent(ua: str) -> str:
    ua = (ua or "").strip()
    if not UA_RE.match(ua):
        raise SecError("SEC requires a declared User-Agent: '<organisation name> <contact email>'")
    return ua


def load_user_agent(root: str | Path) -> str:
    env = os.environ.get("SEC_USER_AGENT")
    if env:
        return validate_user_agent(env)
    p = Path(root) / "config" / "sec_user_agent.txt"
    if not p.exists():
        raise SecError(f"No SEC User-Agent: set SEC_USER_AGENT or create {p}")
    return validate_user_agent(p.read_text())


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RawStore:
    """Content-addressed, append-only store of everything fetched from SEC."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest = self.root / "manifest.jsonl"

    def put(self, body: bytes, meta: dict) -> dict:
        sha = hashlib.sha256(body).hexdigest()
        path = self.root / "objects" / sha[:2] / f"{sha}.gz"
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(gzip.compress(body, mtime=0))
            tmp.replace(path)
        rec = {**meta, "sha256": sha, "bytes": len(body), "object": str(path.relative_to(self.root))}
        with self.manifest.open("a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        return rec

    def records(self) -> list[dict]:
        if not self.manifest.exists():
            return []
        return [json.loads(line) for line in self.manifest.read_text().splitlines() if line.strip()]

    def latest(self, url: str) -> dict | None:
        """Most recent successful fetch of a URL (by fetch time; manifest order breaks ties)."""
        best = None
        for r in self.records():
            if r.get("url") == url and r.get("status") == 200 and (best is None or r["fetched_at"] >= best["fetched_at"]):
                best = r
        return best

    def read(self, rec: dict) -> bytes:
        body = gzip.decompress((self.root / rec["object"]).read_bytes())
        if hashlib.sha256(body).hexdigest() != rec["sha256"]:
            raise SecError(f"Integrity failure for {rec['url']}: stored object does not match its sha256")
        return body

    def read_json(self, url: str) -> tuple[dict, dict]:
        rec = self.latest(url)
        if rec is None:
            raise SecError(f"Not in raw store (fetch it first): {url}")
        return json.loads(self.read(rec)), rec


def cik10(cik) -> str:
    s = str(cik).strip()
    if s.upper().startswith("CIK"):
        s = s[3:]
    if not s.isdigit() or not 0 < int(s) < 10**10:
        raise ValueError(f"Invalid CIK: {cik!r}")
    return f"{int(s):010d}"


def companyfacts_url(cik) -> str:
    return f"{DATA_BASE}/api/xbrl/companyfacts/CIK{cik10(cik)}.json"


def submissions_url(cik) -> str:
    return f"{DATA_BASE}/submissions/CIK{cik10(cik)}.json"


def submissions_page_url(name: str) -> str:
    return f"{DATA_BASE}/submissions/{name}"


def archive_url(cik, accession: str, document: str = "") -> str:
    base = f"{WWW_BASE}/Archives/edgar/data/{int(cik10(cik))}/{accession.replace('-', '')}"
    return f"{base}/{document}" if document else f"{base}/"


def filing_index_url(cik, accession: str) -> str:
    return f"{archive_url(cik, accession)}{accession}-index.htm"


class SecClient:
    def __init__(self, user_agent: str, store: RawStore, max_rps: float = MAX_RPS, retries: int = 4,
                 opener=None, clock=time.monotonic, sleep=time.sleep, timeout: float = 60.0):
        self.ua = validate_user_agent(user_agent)
        self.store = store
        self.min_interval = 1.0 / max_rps
        self.retries = retries
        self.open = opener or urllib.request.urlopen
        self.clock, self.sleep, self.timeout = clock, sleep, timeout
        self._last = None
        self.requests = 0

    def _throttle(self):
        now = self.clock()
        if self._last is not None:
            wait = self.min_interval - (now - self._last)
            if wait > 0:
                self.sleep(wait)
        self._last = self.clock()

    def get(self, url: str, kind: str) -> dict:
        attempt = 0
        while True:
            self._throttle()
            self.requests += 1
            req = urllib.request.Request(url, headers={"User-Agent": self.ua, "Accept-Encoding": "gzip, deflate"})
            try:
                with self.open(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    enc = (resp.headers.get("Content-Encoding") or "").lower()
                    body = gzip.decompress(raw) if enc == "gzip" else zlib.decompress(raw) if enc == "deflate" else raw
                    return self.store.put(body, {"url": url, "kind": kind, "status": resp.status, "fetched_at": utcnow(),
                                                 "content_type": resp.headers.get("Content-Type", ""),
                                                 "last_modified": resp.headers.get("Last-Modified", ""), "user_agent": self.ua})
            except urllib.error.HTTPError as e:
                if e.code in RETRY_STATUS and attempt < self.retries:
                    ra = e.headers.get("Retry-After") if e.headers else None
                    self.sleep(float(ra) if ra and ra.isdigit() else min(60.0, 2.0 ** attempt))
                    attempt += 1
                    continue
                if e.code == 403:
                    raise SecError(f"403 from SEC for {url}: check the declared User-Agent and request rate") from e
                raise SecError(f"HTTP {e.code} for {url}") from e
            except urllib.error.URLError as e:
                if attempt < self.retries:
                    self.sleep(min(60.0, 2.0 ** attempt))
                    attempt += 1
                    continue
                raise SecError(f"Network error for {url}: {e.reason}") from e

    def get_json(self, url: str, kind: str) -> tuple[dict, dict]:
        rec = self.get(url, kind)
        return json.loads(self.store.read(rec)), rec
