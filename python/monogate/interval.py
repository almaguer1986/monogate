"""
monogate.interval — Certified interval arithmetic for EML expressions.

Propagates tight, guaranteed bounds through any EML tree using interval
arithmetic.  Since exp and ln are both monotone, bounds are exact (no
wrapping or excess widening).

Key identity::

    eml([a_lo, a_hi], [b_lo, b_hi]) = exp(a) − ln(b)
        lo = exp(a_lo) − ln(b_hi)
        hi = exp(a_hi) − ln(b_lo)

    Condition: b_lo > 0 (ln is undefined for b ≤ 0).

Public API
----------
Interval(lo, hi)
eml_interval(a, b) -> Interval
eval_interval(tree, x_interval) -> Interval
bound_expression(expr_str, x_lo, x_hi) -> Interval
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

__all__ = [
    "Interval",
    "eml_interval",
    "eval_interval",
    "bound_expression",
]


# ── Interval type ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Interval:
    """A certified real interval [lo, hi].

    Args:
        lo: Lower bound (inclusive).
        hi: Upper bound (inclusive).

    Raises:
        ValueError: If lo > hi.
    """

    lo: float
    hi: float

    def __post_init__(self) -> None:
        if self.lo > self.hi:
            raise ValueError(
                f"Interval: lo ({self.lo}) must be ≤ hi ({self.hi})"
            )

    def __repr__(self) -> str:
        return f"[{self.lo:.6g}, {self.hi:.6g}]"

    def width(self) -> float:
        """Width of the interval."""
        return self.hi - self.lo

    def midpoint(self) -> float:
        """Midpoint of the interval."""
        return (self.lo + self.hi) * 0.5

    def contains(self, x: float) -> bool:
        """Return True if x ∈ [lo, hi]."""
        return self.lo <= x <= self.hi

    def __contains__(self, x: float) -> bool:
        return self.contains(x)


# ── Core EML interval operation ───────────────────────────────────────────────


def eml_interval(a: Interval, b: Interval) -> Interval:
    """Certified interval arithmetic for eml(a, b) = exp(a) − ln(b).

    Both exp and ln are monotone, so bounds are tight:
        lo = exp(a.lo) − ln(b.hi)
        hi = exp(a.hi) − ln(b.lo)

    Args:
        a: Interval for the first argument (exponent).
        b: Interval for the second argument (log argument).  Must have b.lo > 0.

    Returns:
        Interval bounding exp(a) − ln(b).

    Raises:
        ValueError: If b.lo ≤ 0 (ln undefined).

    Examples::

        >>> eml_interval(Interval(0, 1), Interval(1, 1))
        [1, 1.71828]
        # exp(0)−ln(1)=1, exp(1)−ln(1)=e ≈ 2.71828
        # Note: b=[1,1] so ln(1)=0; result = [exp(0), exp(1)] = [1, e]
    """
    if b.lo <= 0.0:
        raise ValueError(
            f"eml_interval: b.lo must be > 0 (got b = {b}); "
            "ln is undefined for non-positive arguments."
        )
    lo = math.exp(a.lo) - math.log(b.hi)
    hi = math.exp(a.hi) - math.log(b.lo)
    return Interval(lo, hi)


# ── Expression-tree interval evaluator ────────────────────────────────────────


def eval_interval(
    tree: dict[str, Any] | str,
    x_interval: Interval,
) -> Interval:
    """Propagate interval bounds through an EML expression tree.

    Supports the same tree format used by monogate.search.mcts:
        {"op": "leaf", "val": 1.0}    — constant
        {"op": "leaf", "val": "x"}    — input variable
        {"op": "eml", "left": ..., "right": ...}

    Also accepts a string ``"x"`` or ``"1"`` (leaf shorthand).

    Args:
        tree:       EML tree dict (or string leaf shorthand).
        x_interval: Interval for the input variable x.

    Returns:
        Interval bounding the tree's output over x_interval.

    Raises:
        ValueError: If b ≤ 0 in any eml node (log domain error).
        TypeError:  If tree has an unrecognised structure.

    Examples::

        # eml("x", "1") = exp(x) − ln(1) = exp(x)
        # Over x ∈ [0, 1]: [exp(0), exp(1)] = [1, e]
        >>> t = {"op": "eml", "left": {"op": "leaf", "val": "x"},
        ...                   "right": {"op": "leaf", "val": 1.0}}
        >>> eval_interval(t, Interval(0, 1))
        [1, 2.71828]
    """
    # String shorthand
    if isinstance(tree, str):
        if tree == "x":
            return x_interval
        try:
            v = float(tree)
            return Interval(v, v)
        except ValueError:
            raise TypeError(f"eval_interval: unknown string leaf {tree!r}")

    if not isinstance(tree, dict):
        raise TypeError(f"eval_interval: expected dict or str, got {type(tree)!r}")

    op = tree.get("op")

    if op == "leaf":
        val = tree["val"]
        if val == "x":
            return x_interval
        if isinstance(val, (int, float)):
            v = float(val)
            return Interval(v, v)
        raise TypeError(f"eval_interval: unknown leaf val {val!r}")

    if op == "eml":
        a_iv = eval_interval(tree["left"], x_interval)
        b_iv = eval_interval(tree["right"], x_interval)
        return eml_interval(a_iv, b_iv)

    if op == "?":
        raise ValueError(
            "eval_interval: tree contains unexpanded placeholder node '?'. "
            "Fully expand the tree before calling eval_interval."
        )

    raise TypeError(f"eval_interval: unknown op {op!r}")


# ── High-level bound_expression ───────────────────────────────────────────────


def bound_expression(
    expr_str: str,
    x_lo: float,
    x_hi: float,
) -> Interval:
    """Parse a simple EML expression string and return certified output bounds.

    Supported syntax (subset of monogate formula strings)::

        "1"           — constant 1
        "x"           — variable
        "eml(A, B)"   — EML node (nested expressions allowed)

    This parser handles the formulas produced by monogate search functions.

    Args:
        expr_str: Formula string (e.g. ``"eml(x, 1)"``).
        x_lo:     Lower bound for input variable x.
        x_hi:     Upper bound for input variable x.

    Returns:
        Interval bounding the expression over [x_lo, x_hi].

    Raises:
        ValueError: If the expression string cannot be parsed or if a log
                    argument evaluates to a non-positive interval.

    Examples::

        # eml(x, 1) = exp(x) over x ∈ [0, 1]
        >>> bound_expression("eml(x, 1)", 0.0, 1.0)
        [1, 2.71828]

        # eml(1, x) = exp(1) - ln(x) over x ∈ [1, 2]
        # lo = e - ln(2) ≈ 2.026,  hi = e - ln(1) = e
        >>> bound_expression("eml(1, x)", 1.0, 2.0)
        [2.02649, 2.71828]
    """
    x_interval = Interval(x_lo, x_hi)
    tree = _parse(expr_str.strip())
    return eval_interval(tree, x_interval)


# ── Simple recursive parser ────────────────────────────────────────────────────


def _parse(s: str) -> dict[str, Any]:
    """Parse a monogate formula string into a tree dict."""
    s = s.strip()
    if s == "x":
        return {"op": "leaf", "val": "x"}
    if s.startswith("eml("):
        # Find matching closing paren
        if not s.endswith(")"):
            raise ValueError(f"_parse: malformed eml expression: {s!r}")
        inner = s[4:-1]   # strip "eml(" and ")"
        left_s, right_s = _split_args(inner)
        return {"op": "eml", "left": _parse(left_s), "right": _parse(right_s)}
    # Try to parse as float constant
    try:
        v = float(s)
        return {"op": "leaf", "val": v}
    except ValueError:
        pass
    raise ValueError(f"_parse: cannot parse expression fragment: {s!r}")


def _split_args(s: str) -> tuple[str, str]:
    """Split 'A, B' into ('A', 'B') respecting nested parens."""
    depth = 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            return s[:i].strip(), s[i + 1:].strip()
    raise ValueError(f"_split_args: no top-level comma in {s!r}")
