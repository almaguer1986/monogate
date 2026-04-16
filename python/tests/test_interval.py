"""
Tests for monogate.interval — certified interval arithmetic for EML trees.

Covers:
- Interval constructor: valid, lo > hi raises ValueError
- Interval methods: width, midpoint, contains
- eml_interval: correct bounds, b.lo ≤ 0 raises ValueError
- eval_interval: leaf constants, leaf "x", eml nodes, nested trees
- eval_interval: unrecognised op raises TypeError
- eval_interval: placeholder '?' raises ValueError
- bound_expression: parsing and evaluating simple formula strings
- Monotonicity: output interval contains point evaluation for any x in x_interval
"""

from __future__ import annotations

import math

import pytest

from monogate.interval import (
    Interval,
    bound_expression,
    eml_interval,
    eval_interval,
)


# ── Interval constructor ──────────────────────────────────────────────────────

class TestIntervalConstructor:
    def test_valid_interval(self):
        iv = Interval(0.0, 1.0)
        assert iv.lo == 0.0
        assert iv.hi == 1.0

    def test_degenerate_interval(self):
        iv = Interval(1.5, 1.5)
        assert iv.lo == iv.hi == 1.5

    def test_lo_gt_hi_raises(self):
        with pytest.raises(ValueError, match="lo.*must be ≤ hi"):
            Interval(2.0, 1.0)

    def test_negative_interval(self):
        iv = Interval(-3.0, -1.0)
        assert iv.lo == -3.0
        assert iv.hi == -1.0


class TestIntervalMethods:
    def test_width(self):
        assert Interval(1.0, 3.0).width() == pytest.approx(2.0)

    def test_width_degenerate(self):
        assert Interval(5.0, 5.0).width() == pytest.approx(0.0)

    def test_midpoint(self):
        assert Interval(0.0, 4.0).midpoint() == pytest.approx(2.0)

    def test_contains_interior(self):
        iv = Interval(0.0, 2.0)
        assert iv.contains(1.0)
        assert 1.0 in iv

    def test_contains_boundary(self):
        iv = Interval(0.0, 2.0)
        assert iv.contains(0.0)
        assert iv.contains(2.0)

    def test_not_contains_outside(self):
        iv = Interval(0.0, 1.0)
        assert not iv.contains(-0.1)
        assert not iv.contains(1.1)

    def test_repr(self):
        s = repr(Interval(1.0, math.e))
        assert "[" in s and "]" in s


# ── eml_interval ─────────────────────────────────────────────────────────────

class TestEmlInterval:
    def test_constant_case(self):
        # eml([0,0], [1,1]) = exp(0) - ln(1) = 1 - 0 = 1
        result = eml_interval(Interval(0.0, 0.0), Interval(1.0, 1.0))
        assert result.lo == pytest.approx(1.0, abs=1e-12)
        assert result.hi == pytest.approx(1.0, abs=1e-12)

    def test_exp_x_minus_ln1(self):
        # eml([0,1], [1,1]) = [exp(0)-ln(1), exp(1)-ln(1)] = [1, e]
        result = eml_interval(Interval(0.0, 1.0), Interval(1.0, 1.0))
        assert result.lo == pytest.approx(1.0, abs=1e-12)
        assert result.hi == pytest.approx(math.e, abs=1e-12)

    def test_bounds_correct_direction(self):
        # lo should be ≤ hi
        result = eml_interval(Interval(-1.0, 1.0), Interval(1.0, 2.0))
        assert result.lo <= result.hi

    def test_contains_point_evaluation(self):
        # For any x in [a_lo, a_hi], eml(x, b) should be in result
        a = Interval(0.0, 1.0)
        b = Interval(1.0, 1.0)
        result = eml_interval(a, b)
        for x_a in [0.0, 0.3, 0.7, 1.0]:
            v = math.exp(x_a) - math.log(1.0)
            assert result.contains(v), f"eml({x_a}, 1) = {v} not in {result}"

    def test_b_lo_zero_raises(self):
        with pytest.raises(ValueError, match="b.lo must be > 0"):
            eml_interval(Interval(0.0, 1.0), Interval(0.0, 1.0))

    def test_b_lo_negative_raises(self):
        with pytest.raises(ValueError, match="b.lo must be > 0"):
            eml_interval(Interval(0.0, 1.0), Interval(-1.0, 1.0))

    def test_result_is_interval(self):
        result = eml_interval(Interval(0.0, 1.0), Interval(1.0, 2.0))
        assert isinstance(result, Interval)

    def test_wide_a_interval(self):
        # eml([-2, 2], [1, 1]) = [exp(-2)-0, exp(2)-0] = [e^-2, e^2]
        result = eml_interval(Interval(-2.0, 2.0), Interval(1.0, 1.0))
        assert result.lo == pytest.approx(math.exp(-2), abs=1e-12)
        assert result.hi == pytest.approx(math.exp(2), abs=1e-12)


# ── eval_interval ─────────────────────────────────────────────────────────────

class TestEvalInterval:
    def _x_iv(self):
        return Interval(0.0, 1.0)

    def test_leaf_x(self):
        tree = {"op": "leaf", "val": "x"}
        result = eval_interval(tree, self._x_iv())
        assert result.lo == pytest.approx(0.0)
        assert result.hi == pytest.approx(1.0)

    def test_leaf_constant_one(self):
        tree = {"op": "leaf", "val": 1.0}
        result = eval_interval(tree, self._x_iv())
        assert result.lo == pytest.approx(1.0)
        assert result.hi == pytest.approx(1.0)

    def test_leaf_constant_zero(self):
        tree = {"op": "leaf", "val": 0.0}
        result = eval_interval(tree, self._x_iv())
        assert result.lo == pytest.approx(0.0)
        assert result.hi == pytest.approx(0.0)

    def test_eml_node_exp_x(self):
        # eml(x, 1) = exp(x) - ln(1) = exp(x)
        # Over [0,1]: [1, e]
        tree = {
            "op": "eml",
            "left":  {"op": "leaf", "val": "x"},
            "right": {"op": "leaf", "val": 1.0},
        }
        result = eval_interval(tree, Interval(0.0, 1.0))
        assert result.lo == pytest.approx(1.0, abs=1e-12)
        assert result.hi == pytest.approx(math.e, abs=1e-12)

    def test_eml_node_nested(self):
        # eml(eml(x,1), 1) = exp(exp(x)) - ln(1) = exp(exp(x))
        # Over x ∈ [0,1]: [exp(1), exp(e)]
        inner = {
            "op": "eml",
            "left":  {"op": "leaf", "val": "x"},
            "right": {"op": "leaf", "val": 1.0},
        }
        outer = {
            "op": "eml",
            "left":  inner,
            "right": {"op": "leaf", "val": 1.0},
        }
        result = eval_interval(outer, Interval(0.0, 1.0))
        assert result.lo == pytest.approx(math.exp(1.0), abs=1e-10)
        assert result.hi == pytest.approx(math.exp(math.e), abs=1e-10)

    def test_string_x_shorthand(self):
        result = eval_interval("x", Interval(-1.0, 1.0))
        assert result.lo == pytest.approx(-1.0)
        assert result.hi == pytest.approx(1.0)

    def test_string_constant_shorthand(self):
        result = eval_interval("1", Interval(0.0, 1.0))
        assert result.lo == pytest.approx(1.0)
        assert result.hi == pytest.approx(1.0)

    def test_unknown_op_raises_type_error(self):
        tree = {"op": "add", "left": {"op": "leaf", "val": "x"},
                "right": {"op": "leaf", "val": 1.0}}
        with pytest.raises(TypeError, match="unknown op"):
            eval_interval(tree, self._x_iv())

    def test_placeholder_raises_value_error(self):
        tree = {"op": "?"}
        with pytest.raises(ValueError, match="unexpanded placeholder"):
            eval_interval(tree, self._x_iv())

    def test_non_dict_non_str_raises_type_error(self):
        with pytest.raises(TypeError):
            eval_interval(42, self._x_iv())

    def test_result_contains_point_evaluations(self):
        # Verify containment: for each x in x_interval, f(x) ∈ result
        tree = {
            "op": "eml",
            "left":  {"op": "leaf", "val": "x"},
            "right": {"op": "leaf", "val": 1.0},
        }
        x_interval = Interval(0.0, 2.0)
        result = eval_interval(tree, x_interval)
        for x_val in [0.0, 0.5, 1.0, 1.5, 2.0]:
            v = math.exp(x_val) - math.log(1.0)
            assert result.contains(v), f"f({x_val}) = {v} not in {result}"


# ── bound_expression ──────────────────────────────────────────────────────────

class TestBoundExpression:
    def test_constant_expression(self):
        result = bound_expression("1", 0.0, 1.0)
        assert result.lo == pytest.approx(1.0)
        assert result.hi == pytest.approx(1.0)

    def test_x_expression(self):
        result = bound_expression("x", -1.0, 3.0)
        assert result.lo == pytest.approx(-1.0)
        assert result.hi == pytest.approx(3.0)

    def test_eml_x_1(self):
        # eml(x, 1) = exp(x) over [0,1] → [1, e]
        result = bound_expression("eml(x, 1)", 0.0, 1.0)
        assert result.lo == pytest.approx(1.0, abs=1e-10)
        assert result.hi == pytest.approx(math.e, abs=1e-10)

    def test_eml_1_x(self):
        # eml(1, x) = exp(1) - ln(x) = e - ln(x)
        # Over x ∈ [1, 2]: [e - ln(2), e - ln(1)] = [e - ln2, e]
        result = bound_expression("eml(1, x)", 1.0, 2.0)
        assert result.lo == pytest.approx(math.e - math.log(2), abs=1e-10)
        assert result.hi == pytest.approx(math.e, abs=1e-10)

    def test_nested_eml(self):
        # eml(eml(x, 1), 1) = exp(exp(x)) over [0, 1]: [e, exp(e)]
        result = bound_expression("eml(eml(x, 1), 1)", 0.0, 1.0)
        assert result.lo == pytest.approx(math.e, abs=1e-10)
        assert result.hi == pytest.approx(math.exp(math.e), abs=1e-10)

    def test_returns_interval(self):
        result = bound_expression("eml(x, 1)", 0.0, 1.0)
        assert isinstance(result, Interval)

    def test_invalid_expression_raises(self):
        with pytest.raises(ValueError):
            bound_expression("foo(x)", 0.0, 1.0)
