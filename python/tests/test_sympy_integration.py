"""Tests for monogate.sympy_integration.eml_cost."""
from __future__ import annotations

import sympy as sp

from monogate.sympy_integration import eml_cost


def test_leaves_cost_zero() -> None:
    x = sp.Symbol("x")
    assert eml_cost(x) == 0
    assert eml_cost(sp.Integer(7)) == 0
    assert eml_cost(sp.pi) == 0


def test_unary_costs_one_plus_arg() -> None:
    x, y = sp.symbols("x y")
    # Each unary call adds exactly one node beyond its argument cost.
    # SymPy's sqrt is internally Pow(arg, 1/2), so it is priced via the
    # Pow branch (1n + cost(arg)) — same total as a unary 1n entry.
    assert eml_cost(sp.exp(x)) == 1
    assert eml_cost(sp.log(x)) == 1
    assert eml_cost(sp.sqrt(x)) == 1
    # Non-trivial argument (SymPy doesn't auto-simplify these):
    # exp(x*y): 1 (exp) + 2 (Mul of 2 args) = 3
    # log(x+y): 1 (log) + 2 (Add of 2 args) = 3
    assert eml_cost(sp.exp(x * y)) == 3
    assert eml_cost(sp.log(x + y)) == 3


def test_add_and_mul_are_n_ary() -> None:
    x, y, z = sp.symbols("x y z")
    # Add(x, y) -> 0 + 0 + 2*(2-1) = 2
    assert eml_cost(x + y) == 2
    # Mul(x, y) -> 0 + 0 + 2*(2-1) = 2
    assert eml_cost(x * y) == 2
    # Add(x, y, z) -> 0 + 0 + 0 + 2*(3-1) = 4
    assert eml_cost(x + y + z) == 4


def test_classic_routing_identity() -> None:
    """exp(x)*exp(y) costs more than exp(x+y) under EML accounting."""
    x, y = sp.symbols("x y")
    expanded = sp.exp(x) * sp.exp(y)        # 1 + 1 + Mul(2 args)
    routed   = sp.exp(x + y)                 # exp(Add(x, y)) = 1 + 2
    assert eml_cost(expanded) == 4
    assert eml_cost(routed) == 3
    assert eml_cost(routed) < eml_cost(expanded)


def test_satisfies_sympy_measure_contract() -> None:
    """eml_cost satisfies the SymPy `measure=` API contract.

    SymPy's ``simplify(expr, measure=fn)`` requires ``fn`` to:
      - accept a single SymPy expression
      - return a comparable scalar (typically int or float)
      - return a finite, non-negative value for any well-formed expression

    This test verifies the contract without actually invoking
    ``sympy.simplify`` (which is slow under a Python-callable measure).
    The qualitative comparison "eml_cost as measure beats / matches /
    loses to default measure" is documented separately in the cas-bridge
    SN-4 session report; here we only assert the API contract.
    """
    x, y = sp.symbols("x y")
    sample_exprs = [
        x,
        x + y,
        sp.exp(x) * sp.exp(y),
        sp.log(sp.sqrt(x)),
        1 / (1 + sp.exp(-x)),
    ]
    for expr in sample_exprs:
        v = eml_cost(expr)
        assert isinstance(v, int)
        assert v >= 0
        # Idempotent: calling twice gives the same number
        assert eml_cost(expr) == v
