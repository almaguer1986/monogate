"""SymPy integration for monogate EML cost analysis.

This module exposes :func:`eml_cost`, a SymPy-compatible *measure* function
that scores a SymPy expression by its EML node count under the standard
``23op+FMA`` basis used by the monogate catalog and SuperBEST routing tables.

It is designed as a drop-in for SymPy's :func:`sympy.simplify` ``measure=``
parameter, so users can get EML-aware simplification inside their existing
SymPy workflows with no code changes beyond the import:

    >>> import sympy as sp
    >>> from monogate.sympy_integration import eml_cost
    >>> x = sp.Symbol('x')
    >>> e = sp.log(sp.sqrt(x))
    >>> sp.simplify(e)                        # default measure
    log(x)/2
    >>> sp.simplify(e, measure=eml_cost)      # EML-aware
    log(sqrt(x))

The two outputs are mathematically equivalent for ``x > 0``.  The default
``count_ops`` measure prefers ``log(x)/2`` (it sees a smaller op count after
``sqrt`` is unrolled), while ``eml_cost`` keeps the original form because
the EML node accounting prices the expanded ``log/div/2`` slightly higher
than ``log(sqrt(...))``.

Empirical comparison on a 10-expression test panel
(see ``cas-bridge/SESSION_symbolic_numerical.json``):

    eml_cost as measure:  better in 2/10,  same in 8/10,  never worse.

Cost model
----------

Costs follow the deep10 / SuperBEST ``23op+FMA`` convention:

    leaf (number / symbol / NumberSymbol):  0
    exp / log / sqrt:                        1 + cost(arg)
    Add (n-ary):                             sum(args) + 2 * (n - 1)
    Mul (n-ary):                             sum(args) + 2 * (n - 1)
    Pow:                                     1 + cost(base) + cost(exponent)
    sin / cos / tan / sinh / cosh / tanh
        (and their inverses):                5 + cost(arg)        (boundary)
    other (unknown function):                2 + sum(args)        (default)

The boundary trig cost (5n) is a conservative placeholder reflecting the
real-arithmetic cost of CORDIC-style approximation; see
``D:/monogate-research/exploration/bypass-theory/SUMMARY.md`` for the full
bypass-cost discussion.

This module has no runtime dependency on the rest of monogate beyond
``sympy``.  It is a candidate for upstreaming as a small SymPy extension
or a standalone PyPI package.
"""
from __future__ import annotations

from typing import Any

try:
    import sympy as sp
except ImportError as exc:                       # pragma: no cover
    raise ImportError(
        "monogate.sympy_integration requires sympy; install with `pip install sympy`."
    ) from exc


__all__ = ["eml_cost"]


# Per-class cost coefficients for the F16 + FMA basis.
# Note: sp.sqrt(x) returns Pow(x, 1/2) so sqrt is priced via the Pow branch,
# which charges 1n + cost(arg) — equivalent to a sqrt-as-unary entry.
_UNARY_NODE_COST: dict[Any, int] = {
    sp.exp: 1,
    sp.log: 1,
}

_BOUNDARY_NODE_COST: dict[Any, int] = {
    sp.sin: 5, sp.cos: 5, sp.tan: 5,
    sp.sinh: 5, sp.cosh: 5, sp.tanh: 5,
    sp.asin: 5, sp.acos: 5, sp.atan: 5,
    sp.asinh: 5, sp.acosh: 5, sp.atanh: 5,
}


def eml_cost(expr: Any) -> int:
    """Return the EML node count of a SymPy expression under 23op+FMA.

    Suitable as a ``measure`` argument to :func:`sympy.simplify`.

    Parameters
    ----------
    expr
        A SymPy expression (anything :func:`sympy.sympify` accepts).

    Returns
    -------
    int
        The EML node count.  Leaves cost 0; inner nodes cost ``1`` to ``5``
        plus their children.

    Examples
    --------
    >>> import sympy as sp
    >>> from monogate.sympy_integration import eml_cost
    >>> x, y = sp.symbols("x y")
    >>> eml_cost(x)
    0
    >>> eml_cost(sp.exp(x))
    1
    >>> eml_cost(sp.exp(x) * sp.exp(y))      # 2 exps + Mul of 2 args
    4
    >>> eml_cost(sp.exp(x + y))              # 1 exp + 1 Add
    3
    """
    expr = sp.sympify(expr)
    return _eml_cost_inner(expr)


def _eml_cost_inner(expr: Any) -> int:
    if expr.is_Number or expr.is_Symbol or expr.is_NumberSymbol:
        return 0

    func = expr.func
    children_cost = sum(_eml_cost_inner(a) for a in expr.args)

    if func in _UNARY_NODE_COST:
        return _UNARY_NODE_COST[func] + children_cost
    if func in _BOUNDARY_NODE_COST:
        return _BOUNDARY_NODE_COST[func] + children_cost
    if func is sp.Add or func is sp.Mul:
        return children_cost + 2 * (len(expr.args) - 1)
    if func is sp.Pow:
        return 1 + children_cost

    # Default: unknown function — charge a single node + children.
    return 2 + children_cost
