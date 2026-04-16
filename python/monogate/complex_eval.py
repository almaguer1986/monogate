"""
monogate.complex_eval — Complex-domain EML evaluation.

The EML operator extends naturally to complex numbers:

    eml(a, b) = exp(a) - ln(b)

where exp and ln use their principal-branch complex definitions
(cmath.exp, cmath.log).

Key identity — Euler path to sin/cos:

    eml(ix, 1) = exp(ix) - ln(1) = exp(ix) - 0 = cos(x) + i·sin(x)

so:
    Re(eml(ix, 1)) = cos(x)
    Im(eml(ix, 1)) = sin(x)

This lets us *construct* sin and cos exactly as projections of a single
EML expression, bypassing the Infinite Zeros Barrier (which only blocks
*real-valued* EML trees from equalling sin).

Public API
----------
eml_complex(a, b)
    Complex EML operator.

eval_complex(node, x, *, i_terminal='i')
    Evaluate an EML tree node (dict) at a real x, with support for
    complex terminals 'i', 'ix'.

sin_via_euler(x)
    Im(eml(ix, 1)) — exact sin(x) via the Euler path.

cos_via_euler(x)
    Re(eml(ix, 1)) — exact cos(x) via the Euler path.

euler_path_node()
    Returns the tree dict {"op":"eml","left":{"op":"leaf","val":"ix"},
    "right":{"op":"leaf","val":1.0}} representing the Euler path.
"""

from __future__ import annotations

import cmath
import math
from typing import Any


# ── Types ─────────────────────────────────────────────────────────────────────

Node = dict[str, Any]


# ── Complex EML operator ──────────────────────────────────────────────────────

def eml_complex(a: complex, b: complex) -> complex:
    """
    Complex EML operator: eml(a, b) = exp(a) - ln(b).

    Uses cmath principal-branch logarithm (branch cut on the negative real
    axis).  Raises ValueError if b == 0 (ln is undefined there).

    >>> import cmath, math
    >>> z = eml_complex(1j * math.pi, 1.0)   # eml(i*pi, 1)
    >>> abs(z.real - (-1)) < 1e-12            # cos(pi) = -1
    True
    >>> abs(z.imag) < 1e-12                   # sin(pi) ≈ 0
    True
    """
    if b == 0:
        raise ValueError("eml_complex: b must be non-zero (ln(0) undefined)")
    return cmath.exp(a) - cmath.log(b)


# ── Tree evaluation with complex terminals ────────────────────────────────────

def eval_complex(node: Node, x: float) -> complex:
    """
    Evaluate an EML tree node at real x, supporting complex terminals.

    Terminal values
    ---------------
    "x"   : the real input x (as complex)
    "ix"  : i * x  (imaginary x)
    "i"   : the imaginary unit i = 1j
    1.0   : constant 1 (or any numeric literal)

    Uses complex EML at every node, so the result is complex in general.
    Call .real or .imag on the result to extract the desired component.

    Args:
        node: EML tree dict (same format as monogate.search.mcts).
        x:    Real evaluation point.

    Returns:
        complex result of evaluating the tree.

    Raises:
        ValueError: if node is incomplete ("?") or if ln domain is violated.
    """
    op = node["op"]
    if op == "leaf":
        val = node["val"]
        if val == "x":
            return complex(x)
        if val == "ix":
            return complex(0, x)   # i * x
        if val == "i":
            return 1j
        return complex(val)
    if op == "?":
        raise ValueError("eval_complex: incomplete tree (contains '?' node)")
    a = eval_complex(node["left"],  x)
    b = eval_complex(node["right"], x)
    return eml_complex(a, b)


# ── Euler path constructors ───────────────────────────────────────────────────

def euler_path_node() -> Node:
    """
    Return the EML tree node representing eml(ix, 1).

    This is the *Euler path*:
        eml(ix, 1) = exp(ix) - ln(1) = exp(ix) = cos(x) + i·sin(x)

    The node uses the 'ix' terminal (i*x), avoiding the need for a
    separate multiplication node for the imaginary unit.

    Returns:
        dict: {"op": "eml",
               "left":  {"op": "leaf", "val": "ix"},
               "right": {"op": "leaf", "val": 1.0}}
    """
    return {
        "op": "eml",
        "left":  {"op": "leaf", "val": "ix"},
        "right": {"op": "leaf", "val": 1.0},
    }


def sin_via_euler(x: float) -> float:
    """
    Exact sin(x) via the Euler path: Im(eml(ix, 1)).

    This is a *single EML node* computation.  It yields sin(x) to full
    floating-point precision for any real x, despite no real-valued EML
    tree being able to equal sin (Infinite Zeros Barrier).

    The key insight: the Barrier applies to *real-valued* trees.  Moving
    to the complex domain removes it — sin lives on the imaginary axis of
    the complex exponential.

    >>> import math
    >>> abs(sin_via_euler(math.pi / 6) - 0.5) < 1e-15
    True
    >>> abs(sin_via_euler(0.0)) < 1e-15
    True
    """
    return eml_complex(complex(0, x), 1.0).imag


def cos_via_euler(x: float) -> float:
    """
    Exact cos(x) via the Euler path: Re(eml(ix, 1)).

    Same single-node computation as sin_via_euler; takes the real part.

    >>> import math
    >>> abs(cos_via_euler(0.0) - 1.0) < 1e-15
    True
    >>> abs(cos_via_euler(math.pi) - (-1.0)) < 1e-14
    True
    """
    return eml_complex(complex(0, x), 1.0).real


# ── MCTS grammar extension helpers ───────────────────────────────────────────

#: Extended terminal set for complex-mode MCTS search.
#: Adds 'ix' (i*x) and 'i' to the standard {1.0, 'x'} set.
COMPLEX_TERMINALS: list[Any] = [1.0, "x", "ix", "i"]


def score_complex_projection(
    node: Node,
    probe_x: list[float],
    probe_y: list[float],
    projection: str = "imag",
) -> float:
    """
    MSE of Im(tree(x)) or Re(tree(x)) against probe_y.

    Useful when searching for trees whose imaginary (or real) part
    approximates a target function.  For example, searching for
    Im(tree(x)) ≈ sin(x).

    Args:
        node:       Complete EML tree dict (may use 'ix', 'i' terminals).
        probe_x:    List of real evaluation points.
        probe_y:    Target values at those points.
        projection: 'imag' (default) or 'real'.

    Returns:
        MSE as float; returns float('inf') on any evaluation error.
    """
    total = 0.0
    try:
        for xi, yi in zip(probe_x, probe_y):
            z     = eval_complex(node, xi)
            pred  = z.imag if projection == "imag" else z.real
            diff  = pred - yi
            total += diff * diff
    except (ValueError, OverflowError, ZeroDivisionError):
        return float("inf")
    if not math.isfinite(total):
        return float("inf")
    return total / len(probe_x)


# ── Human-readable formula with complex terminals ─────────────────────────────

def formula_complex(node: Node) -> str:
    """
    Human-readable formula string, with 'ix' and 'i' rendered correctly.

    >>> formula_complex(euler_path_node())
    'eml(ix, 1.0)'
    """
    op = node["op"]
    if op == "leaf":
        val = node["val"]
        if val == "ix":
            return "ix"
        if val == "i":
            return "i"
        return str(val) if val != "x" else "x"
    if op == "?":
        return "?"
    return f"eml({formula_complex(node['left'])}, {formula_complex(node['right'])})"
