"""
monogate.core — Pure-Python EML arithmetic.

Mirrors the JS library (lib/src/index.js) exactly.
No external dependencies — uses only math.exp and math.log.

Grammar:   S → 1 | eml(S, S)
Operator:  eml(x, y) = exp(x) − ln(y)

Strict principal-branch ln: raises ValueError if y ≤ 0.
"""

import math

__all__ = [
    "op",
    "E",
    "ZERO",
    "NEG_ONE",
    "exp_eml",
    "ln_eml",
    "sub_eml",
    "neg_eml",
    "add_eml",
    "mul_eml",
    "div_eml",
    "pow_eml",
    "recip_eml",
    "IDENTITIES",
    "Operator",
    "EML",
    "EDL",
    "make_exp",
    "make_ln",
    "exp_edl",
    "ln_edl",
]


# ── Core operator ─────────────────────────────────────────────────────────────

def op(x: float, y: float) -> float:
    """
    The EML operator: eml(x, y) = exp(x) − ln(y).

    Strict: raises ValueError if y ≤ 0 (argument of ln must be positive).

    >>> import math
    >>> abs(op(1, 1) - math.e) < 1e-14
    True
    """
    if y <= 0:
        raise ValueError(f"op: y must be > 0, got {y!r}")
    return math.exp(x) - math.log(y)


# ── Constants ─────────────────────────────────────────────────────────────────

E       = op(1, 1)                    # e        Proof: exp(1)−ln(1)=e.        Nodes:1 Depth:1
ZERO    = op(1, op(op(1, 1), 1))     # 0        Proof: eml(1,1)=e; eml(e,1)=eᵉ; eml(1,eᵉ)=e−e=0. Nodes:3 Depth:3
NEG_ONE = op(ZERO, op(2, 1))         # −1       Proof: exp(0)−ln(e²)=1−2=−1.  Nodes:5 Depth:4 (uses terminal 2)


# ── Elementary functions ──────────────────────────────────────────────────────

def exp_eml(x: float) -> float:
    """
    eˣ = eml(x, 1).

    Proof: exp(x) − ln(1) = exp(x). ∎
    Nodes:1  Depth:1

    >>> import math
    >>> abs(exp_eml(1) - math.e) < 1e-14
    True
    >>> abs(exp_eml(0) - 1) < 1e-14
    True
    """
    return op(x, 1)


def ln_eml(x: float) -> float:
    """
    ln(x) = eml(1, eml(eml(1, x), 1)).

    Proof: let s = e − ln(x); eml(s, 1) = eˢ = eᵉ/x;
    eml(1, eᵉ/x) = e − (e − ln(x)) = ln(x). ∎
    Nodes:3  Depth:3  Domain: x > 0

    >>> import math
    >>> abs(ln_eml(math.e) - 1) < 1e-10
    True
    >>> abs(ln_eml(1) - 0) < 1e-14
    True
    """
    return op(1, op(op(1, x), 1))


def sub_eml(x: float, y: float) -> float:
    """
    x − y = eml(ln(x), exp(y)).

    Proof: exp(ln(x)) − ln(exp(y)) = x − y. ∎
    Nodes:5  Depth:4  Domain: x > 0

    >>> abs(sub_eml(5, 2) - 3) < 1e-10
    True
    """
    return op(ln_eml(x), exp_eml(y))


def neg_eml(y: float) -> float:
    """
    −y  (two-regime negation for numerical stability).

    Regime A — y ≤ 0 (tower formula):
        a = eml(y, 1) = exp(y).
        A = eml(a, a) = exp(a) − ln(a) = exp(exp(y)) − y.
        B = eml(a, 1) = exp(a) = exp(exp(y)).
        A − B = −y. ∎
        Stable: exp(y) ≤ 1 so exp(exp(y)) ≤ e for all y ≤ 0.

    Regime B — y > 0 (shift formula):
        y+1 = sub_eml(y, NEG_ONE) = exp(ln(y)) − ln(exp(−1)·exp(y)/y)
            ... simplifies to: y + 1.
        eml(ZERO, eml(y+1, 1)) = exp(0) − ln(exp(y+1)) = 1 − (y+1) = −y. ∎
        Stable for |y| < 708 (IEEE 754 double limit on exp).

    Nodes:9  Depth:5  Valid for all y ∈ ℝ with |y| < 708.

    >>> abs(neg_eml(3) + 3) < 1e-10
    True
    >>> abs(neg_eml(-5) - 5) < 1e-10
    True
    >>> abs(neg_eml(0)) < 1e-14
    True
    """
    if y <= 0:
        a = op(y, 1)                              # exp(y) ∈ (0, 1]
        return op(ln_eml(op(a, a)), op(op(a, 1), 1))
    y1 = op(ln_eml(y), op(NEG_ONE, 1))           # y + 1  (shift by 1)
    return op(ZERO, op(y1, 1))                    # 1 − (y+1) = −y


def add_eml(x: float, y: float) -> float:
    """
    x + y = eml(ln(x), eml(−y, 1))  (x > 0).

    Generalised for all signs via commutativity and double-negation.
    Nodes:11  Depth:6

    >>> abs(add_eml(2, 3) - 5) < 1e-10
    True
    >>> abs(add_eml(-2, -3) + 5) < 1e-10
    True
    >>> abs(add_eml(0.5, -1.5) + 1) < 1e-10
    True
    """
    if x > 0:
        return op(ln_eml(x), op(neg_eml(y), 1))
    if y > 0:
        return op(ln_eml(y), op(neg_eml(x), 1))
    return neg_eml(op(ln_eml(neg_eml(x)), op(neg_eml(neg_eml(y)), 1)))


def mul_eml(x: float, y: float) -> float:
    """
    x × y = exp(ln(x) + ln(y)).

    Proof: exp(ln(x) + ln(y)) = exp(ln(xy)) = xy. ∎
    Nodes:13  Depth:7  Domain: x, y > 0

    >>> abs(mul_eml(2, 3) - 6) < 1e-10
    True
    >>> abs(mul_eml(4, 0.25) - 1) < 1e-10
    True
    """
    return op(add_eml(ln_eml(x), ln_eml(y)), 1)


def div_eml(x: float, y: float) -> float:
    """
    x / y = exp(ln(x) − ln(y)).

    Proof: exp(ln(x) − ln(y)) = exp(ln(x/y)) = x/y. ∎
    Nodes:15  Depth:8  Domain: x, y > 0

    >>> abs(div_eml(6, 3) - 2) < 1e-10
    True
    >>> abs(div_eml(1, 4) - 0.25) < 1e-10
    True
    """
    return op(add_eml(ln_eml(x), neg_eml(ln_eml(y))), 1)


def pow_eml(x: float, n: float) -> float:
    """
    xⁿ = exp(n · ln(x)).

    Proof: exp(n·ln(x)) = exp(ln(xⁿ)) = xⁿ. ∎
    Nodes:15  Depth:8  Domain: x > 0, n ∈ ℝ

    >>> abs(pow_eml(2, 10) - 1024) < 1e-8
    True
    >>> abs(pow_eml(4, 0.5) - 2) < 1e-10
    True
    """
    return op(mul_eml(n, ln_eml(x)), 1)


def recip_eml(x: float) -> float:
    """
    1/x = exp(−ln(x)).

    Proof: exp(−ln(x)) = x⁻¹. ∎
    Nodes:5  Depth:4  Domain: x > 0

    >>> abs(recip_eml(2) - 0.5) < 1e-10
    True
    >>> abs(recip_eml(4) - 0.25) < 1e-10
    True
    """
    return op(neg_eml(ln_eml(x)), 1)


# ── Identity table ────────────────────────────────────────────────────────────

IDENTITIES: list[dict] = [
    {
        "name":     "eˣ",
        "eml_form": "eml(x, 1)",
        "nodes":    1,
        "depth":    1,
        "status":   "verified",
    },
    {
        "name":     "ln x",
        "eml_form": "eml(1, eml(eml(1, x), 1))",
        "nodes":    3,
        "depth":    3,
        "status":   "verified",
    },
    {
        "name":     "e",
        "eml_form": "eml(1, 1)",
        "nodes":    1,
        "depth":    1,
        "status":   "verified",
    },
    {
        "name":     "0",
        "eml_form": "eml(1, eml(eml(1, 1), 1))",
        "nodes":    3,
        "depth":    3,
        "status":   "verified",
    },
    {
        "name":     "x − y",
        "eml_form": "eml(ln(x), exp(y))",
        "nodes":    5,
        "depth":    4,
        "status":   "verified",
    },
    {
        "name":     "−y",
        "eml_form": "two-regime (see source)",
        "nodes":    9,
        "depth":    5,
        "status":   "proven",
    },
    {
        "name":     "x + y",
        "eml_form": "eml(ln(x), eml(neg(y), 1))",
        "nodes":    11,
        "depth":    6,
        "status":   "proven",
    },
    {
        "name":     "x × y",
        "eml_form": "eml(add(ln(x), ln(y)), 1)",
        "nodes":    13,
        "depth":    7,
        "status":   "proven",
    },
    {
        "name":     "x / y",
        "eml_form": "eml(add(ln(x), neg(ln(y))), 1)",
        "nodes":    15,
        "depth":    8,
        "status":   "proven",
    },
    {
        "name":     "xⁿ",
        "eml_form": "eml(mul(n, ln(x)), 1)",
        "nodes":    15,
        "depth":    8,
        "status":   "proven",
    },
    {
        "name":     "1/x",
        "eml_form": "eml(neg(ln(x)), 1)",
        "nodes":    5,
        "depth":    4,
        "status":   "verified",
    },
]


# ── Operator abstraction ──────────────────────────────────────────────────────

import cmath
from typing import Callable


class Operator:
    """Container for a universal operator and its natural constant."""

    def __init__(self, name: str, func: Callable, constant: complex) -> None:
        self.name = name
        self.func = func
        self.constant = constant

    def __repr__(self) -> str:
        return f"Operator({self.name!r}, constant={self.constant})"


def _eml_func(x: complex, y: complex) -> complex:
    return cmath.exp(x) - cmath.log(y)


EML = Operator("EML", _eml_func, 1.0 + 0j)


def _edl_func(x: complex, y: complex) -> complex:
    if y == 0 or y == 1:
        raise ValueError(f"EDL domain error: y={y}")
    return cmath.exp(x) / cmath.log(y)


EDL = Operator("EDL", _edl_func, cmath.e)


# ── Derived helpers (operator-agnostic) ───────────────────────────────────────
#
# Both EML and EDL share the same *structure* for exp and ln, but the constants
# differ.  The two neutral elements are:
#
#   EML: right-neutral = 1      (eml(x, 1) = exp(x))
#        "left probe" = 1       (eml(1, x) = e − ln(x), used to extract ln)
#
#   EDL: right-neutral = e      (edl(x, e) = exp(x))
#        left-neutral  = 0      (edl(0, x) = 1/ln(x))
#
# exp — same 1-node form for both operators:
#   EML: eml(x, 1) = exp(x) − ln(1) = exp(x)
#   EDL: edl(x, e) = exp(x) / ln(e) = exp(x) / 1 = exp(x)
#
# ln — 3-node trees with parallel but distinct structure:
#   EML: eml(1, eml(eml(1, x), 1))
#        step 1: eml(1, x)       = e − ln(x)
#        step 2: eml(s, 1)       = exp(e − ln(x)) = eᵉ/x
#        step 3: eml(1, eᵉ/x)   = e − (e − ln(x)) = ln(x)  ✓
#
#   EDL: edl(0, edl(edl(0, x), e))
#        step 1: edl(0, x)       = 1/ln(x)
#        step 2: edl(s, e)       = exp(1/ln(x)) / 1 = exp(1/ln(x))
#        step 3: edl(0, t)       = 1/ln(exp(1/ln(x))) = 1/(1/ln(x)) = ln(x)  ✓

def make_exp(operator: Operator) -> Callable[[complex], complex]:
    """Return a function computing exp(x) as a 1-node operator tree."""
    c = operator.constant
    return lambda x: operator.func(x, c)


def make_ln(operator: Operator) -> Callable[[complex], complex]:
    """Return a function computing ln(x) as a 3-node operator tree.

    EML route: eml(1, eml(eml(1, x), 1))
    EDL route: edl(0, edl(edl(0, x), e))
    """
    f = operator.func
    c = operator.constant
    if operator is EML:
        # c = 1; uses right-neutral in all three positions
        return lambda x: f(c, f(f(c, x), c))
    if operator is EDL:
        # left-neutral 0; right-neutral e (the constant)
        zero = 0j
        return lambda x: f(zero, f(f(zero, x), c))
    raise NotImplementedError(
        f"make_ln: no ln derivation registered for operator {operator.name!r}"
    )


# Convenience singletons — mirrors the existing exp_eml / ln_eml names
exp_edl: Callable[[complex], complex] = make_exp(EDL)
ln_edl:  Callable[[complex], complex] = make_ln(EDL)
