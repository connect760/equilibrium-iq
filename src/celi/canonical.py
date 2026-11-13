"""Canonical serialisation, hashing and Merkle commitments.

canonical_json() must produce byte-identical output to the reference engine's
canon() so that a hash computed in the browser verifies on the server and
vice versa. Rules: object keys sorted, no whitespace, None/undefined -> null,
integers without a trailing .0 (JavaScript has one number type).
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Sequence


def _num(x: float) -> str:
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, int):
        return str(x)
    if math.isnan(x) or math.isinf(x):
        return "null"  # JSON.stringify(NaN) === "null"
    if x == int(x) and abs(x) < 1e21:
        return str(int(x))
    # JavaScript shortest round-trip representation; Python's repr matches for
    # ordinary magnitudes used here (|x| between 1e-6 and 1e21).
    r = repr(x)
    if "e" in r or "E" in r:
        raise ValueError(f"exponent notation not supported in canonical form: {r}")
    return r


def canonical_json(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return _num(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(canonical_json(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + canonical_json(v[k]) for k in sorted(v)) + "}"
    raise TypeError(f"not serialisable: {type(v).__name__}")


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def hash_record(record: dict) -> str:
    return sha256_hex(canonical_json(record))


def merkle_levels(leaves: Sequence[str]) -> list[list[str]]:
    """Binary Merkle tree over hex leaf hashes; an odd node is paired with itself."""
    if not leaves:
        return []
    level = list(leaves)
    levels = [level]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            nxt.append(sha256_hex(left + right))
        level = nxt
        levels.append(level)
    return levels


def merkle_root(leaves: Sequence[str]) -> str | None:
    lv = merkle_levels(leaves)
    return lv[-1][0] if lv else None


def inclusion_proof(levels: list[list[str]], index: int) -> list[tuple[str, str]]:
    """Sibling path from leaf to root as (side, hash) where side is 'L' or 'R'."""
    proof = []
    i = index
    for level in levels[:-1]:
        if i % 2:
            proof.append(("L", level[i - 1]))
        else:
            proof.append(("R", level[i + 1] if i + 1 < len(level) else level[i]))
        i //= 2
    return proof


def verify_inclusion(leaf: str, proof: list[tuple[str, str]], root: str) -> bool:
    h = leaf
    for side, sib in proof:
        h = sha256_hex(sib + h) if side == "L" else sha256_hex(h + sib)
    return h == root
