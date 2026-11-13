"""Numeric helpers that reproduce the reference (JavaScript) engine bit-for-bit.

Determinism rule: every rounding in the engine goes through these functions.
Python's built-in round() uses banker's rounding; JavaScript's Math.round rounds
half toward +infinity. Mixing them would make two implementations disagree on
x.xx5 boundaries, so we never use round() in scoring code.
"""
from __future__ import annotations

import math
from datetime import date


def js_round(x: float) -> float:
    """Equivalent of JavaScript Math.round."""
    return math.floor(x + 0.5)


def r2(x: float) -> float:
    """Round to 2 decimals, JS semantics: Math.round(x*100)/100."""
    return js_round(x * 100) / 100


def r4(x: float) -> float:
    """Round to 4 decimals, JS semantics."""
    return js_round(x * 10000) / 10000


def clamp(x: float, lo: float, hi: float) -> float:
    return min(hi, max(lo, x))


def is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and not math.isnan(x)


def days_between(a: str, b: str) -> float:
    """Days from ISO date a to ISO date b (b - a). Dates are YYYY-MM-DD, UTC."""
    return float((date.fromisoformat(b[:10]) - date.fromisoformat(a[:10])).days)


def softplus(z: float, h: float) -> float:
    """h * ln(1 + e^(z/h)), computed stably."""
    t = z / h
    if t > 30:  # avoid overflow; log1p(e^t) == t + log1p(e^-t)
        return h * (t + math.log1p(math.exp(-t)))
    return h * math.log1p(math.exp(t))


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))
