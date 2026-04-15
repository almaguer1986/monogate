"""
monogate.torch_ops — Differentiable EML arithmetic for PyTorch.

Mirrors core.py exactly, but all operations accept and return Tensors so that
autograd can differentiate through any EML expression tree.

Key design note — neg_eml:
    The two-regime negation (tower formula for y ≤ 0, shift formula for y > 0)
    is implemented via torch.where so both branches are fully traced and gradients
    flow through whichever branch is active.  A Python if-else would only trace
    one branch per forward pass and break gradient flow for the other.

    Inputs are clamped per-regime to prevent inf/NaN in the inactive branch from
    corrupting gradients through torch.where:
        Regime A uses y.clamp(max=0)  → exp(y_A) ≤ 1, no overflow
        Regime B uses y.clamp(min=ε) → ln(y_B) is finite

Strict domain contract (mirrors core.py):
    op(x, y)    — y > 0 element-wise (log returns -inf / NaN otherwise)
    ln_eml(x)   — x > 0
    sub_eml(x,y)— x > 0
    mul_eml(x,y)— x, y > 0
    div_eml(x,y)— x, y > 0
    pow_eml(x,n)— x > 0, n > 0
    recip_eml(x)— x > 0

Constants E, ZERO, NEG_ONE are plain Python floats from core so they can be
broadcast against any tensor dtype/device at runtime.
"""

import torch
from torch import Tensor

from .core import E as _E, NEG_ONE as _NEG_ONE, ZERO as _ZERO  # noqa: F401

__all__ = [
    "op",
    "edl_op",
    "edl_op_safe",
    "exl_op",
    "eal_op",
    "exp_eml",
    "ln_eml",
    "sub_eml",
    "neg_eml",
    "add_eml",
    "mul_eml",
    "div_eml",
    "pow_eml",
    "recip_eml",
]

_EPS = 1e-38  # clamp floor for log-domain inputs


# ── Core operator ─────────────────────────────────────────────────────────────

def op(x: Tensor, y: Tensor) -> Tensor:
    """eml(x, y) = exp(x) − ln(y).  Domain: y > 0 element-wise."""
    return torch.exp(x) - torch.log(y)


def edl_op(x: Tensor, y: Tensor) -> Tensor:
    """edl(x, y) = exp(x) / ln(y).  Domain: y > 0, y != 1 element-wise."""
    return torch.exp(x) / torch.log(y)


def edl_op_safe(x: Tensor, y: Tensor) -> Tensor:
    """EDL gate safe for training from softplus output.

    When y comes from softplus (range (0, inf)), adding 1 shifts it to
    (1, inf), guaranteeing ln(y_safe) > 0 and bounded away from 0.
    This eliminates the division-by-zero that kills plain edl_op when
    softplus outputs land near 1 (the dead zone) early in training.

    Natural constant: effective c = e - 1, since ln((e-1)+1) = ln(e) = 1
    => edl_safe(x, e-1) = exp(x) / 1 = exp(x).

    Note: use EDL_SAFE_CONSTANT (= e - 1) as the right-argument constant
    anywhere you would use cmath.e with plain EDL.
    """
    y_safe = y + 1.0 + 1e-6
    return torch.exp(x) / torch.log(y_safe)


# Natural constant for edl_op_safe (replaces cmath.e)
EDL_SAFE_CONSTANT: float = 2.718281828459045 - 1.0  # e - 1


def exl_op(x: Tensor, y: Tensor) -> Tensor:
    """exl(x, y) = exp(x) * ln(y).  Domain: y > 0 element-wise."""
    return torch.exp(x) * torch.log(y)


def eal_op(x: Tensor, y: Tensor) -> Tensor:
    """eal(x, y) = exp(x) + ln(y).  Domain: y > 0 element-wise."""
    return torch.exp(x) + torch.log(y)


# ── Elementary functions ──────────────────────────────────────────────────────

def exp_eml(x: Tensor) -> Tensor:
    """eˣ = eml(x, 1)."""
    return op(x, torch.ones_like(x))


def ln_eml(x: Tensor) -> Tensor:
    """
    ln(x) = eml(1, eml(eml(1, x), 1)).

    Proof: let s = e − ln(x); eml(s, 1) = eˢ = eᵉ/x;
    eml(1, eᵉ/x) = e − (e − ln(x)) = ln(x). ∎
    Domain: x > 0.
    """
    ones = torch.ones_like(x)
    return op(ones, op(op(ones, x), ones))


def sub_eml(x: Tensor, y: Tensor) -> Tensor:
    """
    x − y = eml(ln(x), exp(y)).

    Proof: exp(ln(x)) − ln(exp(y)) = x − y. ∎
    Domain: x > 0.
    """
    return op(ln_eml(x), exp_eml(y))


def neg_eml(y: Tensor) -> Tensor:
    """
    −y  via torch.where so both branches are traced for autograd.

    Regime A — y ≤ 0 (tower formula, stable since exp(y) ≤ 1):
        a = exp(y) ∈ (0, 1]
        op(a, a) = exp(a) − ln(a) = exp(exp(y)) − y          [ln(exp(y)) = y]
        op(op(a,1), 1) = exp(exp(exp(y)))
        result = (exp(exp(y)) − y) − exp(exp(y)) = −y  ∎

    Regime B — y > 0 (shift formula):
        y1 = op(ln_eml(y), op(NEG_ONE, 1)) = y − NEG_ONE = y + 1
        result = op(ZERO, op(y1, 1)) = 1 − (y+1) = −y  ∎
    """
    ones = torch.ones_like(y)

    # ── Regime A: tower formula (y ≤ 0) ──────────────────────────────────────
    y_A     = y.clamp(max=0.0)                      # exp(y_A) ≤ 1, no overflow
    a       = op(y_A, ones)                          # exp(y_A)
    inner_A = op(a, a)                               # exp(exp(y)) − y
    lhs_A   = ln_eml(inner_A.clamp(min=_EPS))        # ln(exp(exp(y)) − y)
    rhs_A   = op(op(a, ones), ones)                  # exp(exp(exp(y)))
    result_A = op(lhs_A, rhs_A)                      # (exp(exp(y)) − y) − exp(exp(y)) = −y

    # ── Regime B: shift formula (y > 0) ──────────────────────────────────────
    y_B       = y.clamp(min=_EPS)                    # ln(y_B) finite
    neg_one_t = torch.full_like(y, _NEG_ONE)
    zero_t    = torch.full_like(y, _ZERO)
    y1        = op(ln_eml(y_B), op(neg_one_t, ones)) # y + 1
    result_B  = op(zero_t, op(y1, ones))              # 1 − (y+1) = −y

    return torch.where(y <= 0, result_A, result_B)


def add_eml(x: Tensor, y: Tensor) -> Tensor:
    """
    x + y, generalised for all signs via torch.where.

    Three cases (mirrors core.py):
        x > 0:           eml(ln(x), eml(neg(y), 1))
        y > 0 (x ≤ 0):  eml(ln(y), eml(neg(x), 1))
        both ≤ 0:        −(neg(x) + neg(y))

    Inputs clamped per-case to keep ln finite in inactive branches.
    """
    ones  = torch.ones_like(x)
    x_p   = x.clamp(min=_EPS)
    y_p   = y.clamp(min=_EPS)

    # Case A: x > 0
    result_A = op(ln_eml(x_p), op(neg_eml(y), ones))

    # Case B: y > 0, x ≤ 0
    result_B = op(ln_eml(y_p), op(neg_eml(x), ones))

    # Case C: both ≤ 0  →  neg(x), neg(y) ≥ 0
    neg_x    = neg_eml(x)
    neg_y    = neg_eml(y)
    nx_p     = neg_x.clamp(min=_EPS)
    sum_pos  = op(ln_eml(nx_p), op(neg_eml(neg_y), ones))
    result_C = neg_eml(sum_pos)

    return torch.where(x > 0, result_A, torch.where(y > 0, result_B, result_C))


def mul_eml(x: Tensor, y: Tensor) -> Tensor:
    """x × y = exp(ln(x) + ln(y)).  Domain: x, y > 0."""
    return op(add_eml(ln_eml(x), ln_eml(y)), torch.ones_like(x))


def div_eml(x: Tensor, y: Tensor) -> Tensor:
    """x / y = exp(ln(x) − ln(y)).  Domain: x, y > 0."""
    return op(add_eml(ln_eml(x), neg_eml(ln_eml(y))), torch.ones_like(x))


def pow_eml(x: Tensor, n: Tensor) -> Tensor:
    """xⁿ = exp(n · ln(x)).  Domain: x > 0, n > 0."""
    return op(mul_eml(n, ln_eml(x)), torch.ones_like(x))


def recip_eml(x: Tensor) -> Tensor:
    """1/x = exp(−ln(x)).  Domain: x > 0."""
    return op(neg_eml(ln_eml(x)), torch.ones_like(x))
