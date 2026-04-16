"""
tests/test_complex.py — Unit tests for monogate.complex_eval.

Tests cover:
    - Basic complex EML operator correctness
    - Euler path: eml(ix, 1) = cos(x) + i*sin(x)
    - sin_via_euler and cos_via_euler exact values
    - eval_complex with all terminal types ('x', 'ix', 'i', numeric)
    - score_complex_projection MSE helper
    - formula_complex rendering
    - Edge cases: ln(0) domain error, incomplete tree error
"""

from __future__ import annotations

import cmath
import math

import pytest

from monogate.complex_eval import (
    COMPLEX_TERMINALS,
    cos_via_euler,
    eml_complex,
    euler_path_node,
    eval_complex,
    formula_complex,
    score_complex_projection,
    sin_via_euler,
)


# ── eml_complex ───────────────────────────────────────────────────────────────

class TestEmlComplex:
    def test_real_inputs_match_real_eml(self) -> None:
        """eml_complex on real inputs must equal math.exp(a) - math.log(b)."""
        for a, b in [(0.0, 1.0), (1.0, 1.0), (-1.0, 2.5), (2.0, 0.5)]:
            expected = math.exp(a) - math.log(b)
            result   = eml_complex(complex(a), complex(b))
            assert abs(result.imag) < 1e-15, "imaginary part should be zero for real inputs"
            assert abs(result.real - expected) < 1e-12

    def test_euler_formula(self) -> None:
        """eml(ix, 1) = exp(ix) = cos(x) + i*sin(x) for several x values."""
        for x in [0.0, 0.5, 1.0, math.pi / 4, math.pi / 2, math.pi, -1.5]:
            z = eml_complex(complex(0, x), 1.0)
            assert abs(z.real - math.cos(x)) < 1e-14, f"Re mismatch at x={x}"
            assert abs(z.imag - math.sin(x)) < 1e-14, f"Im mismatch at x={x}"

    def test_complex_b_nonzero(self) -> None:
        """eml_complex(a, b) with non-real b should not raise (principal branch)."""
        z = eml_complex(1.0, 1j)   # ln(i) = i*pi/2
        expected = cmath.exp(1.0) - cmath.log(1j)
        assert abs(z - expected) < 1e-12

    def test_b_zero_raises(self) -> None:
        """eml_complex(a, 0) must raise ValueError (ln undefined at 0)."""
        with pytest.raises(ValueError, match="non-zero"):
            eml_complex(1.0, 0.0)

    def test_eml_one_one_equals_e(self) -> None:
        """eml_complex(1, 1) = e."""
        z = eml_complex(1.0, 1.0)
        assert abs(z.imag) < 1e-15
        assert abs(z.real - math.e) < 1e-12


# ── sin_via_euler / cos_via_euler ─────────────────────────────────────────────

class TestEulerProjections:
    _ANGLES = [0.0, 0.1, 0.5, 1.0, math.pi / 6, math.pi / 4, math.pi / 3,
               math.pi / 2, math.pi, -math.pi / 4, -1.0, 2.5]

    def test_sin_via_euler_exact(self) -> None:
        """Im(eml(ix, 1)) == sin(x) to full float precision."""
        for x in self._ANGLES:
            assert abs(sin_via_euler(x) - math.sin(x)) < 1e-14, (
                f"sin_via_euler({x}) = {sin_via_euler(x)!r}  "
                f"expected {math.sin(x)!r}"
            )

    def test_cos_via_euler_exact(self) -> None:
        """Re(eml(ix, 1)) == cos(x) to full float precision."""
        for x in self._ANGLES:
            assert abs(cos_via_euler(x) - math.cos(x)) < 1e-14, (
                f"cos_via_euler({x}) = {cos_via_euler(x)!r}  "
                f"expected {math.cos(x)!r}"
            )

    def test_sin_zero(self) -> None:
        assert abs(sin_via_euler(0.0)) < 1e-15

    def test_cos_zero(self) -> None:
        assert abs(cos_via_euler(0.0) - 1.0) < 1e-15

    def test_sin_half_pi(self) -> None:
        assert abs(sin_via_euler(math.pi / 2) - 1.0) < 1e-14

    def test_cos_pi(self) -> None:
        assert abs(cos_via_euler(math.pi) - (-1.0)) < 1e-14

    def test_pythagorean_identity(self) -> None:
        """sin^2(x) + cos^2(x) == 1 for all test angles."""
        for x in self._ANGLES:
            s = sin_via_euler(x)
            c = cos_via_euler(x)
            assert abs(s * s + c * c - 1.0) < 1e-13, f"identity failed at x={x}"


# ── euler_path_node ───────────────────────────────────────────────────────────

class TestEulerPathNode:
    def test_structure(self) -> None:
        node = euler_path_node()
        assert node["op"] == "eml"
        assert node["left"]["op"]  == "leaf"
        assert node["left"]["val"] == "ix"
        assert node["right"]["op"] == "leaf"
        assert node["right"]["val"] == 1.0

    def test_eval_gives_euler(self) -> None:
        """eval_complex on euler_path_node should equal cos(x) + i*sin(x)."""
        node = euler_path_node()
        for x in [0.0, 0.7, 1.5, -2.0]:
            z = eval_complex(node, x)
            assert abs(z.real - math.cos(x)) < 1e-14
            assert abs(z.imag - math.sin(x)) < 1e-14

    def test_formula(self) -> None:
        assert formula_complex(euler_path_node()) == "eml(ix, 1.0)"


# ── eval_complex ──────────────────────────────────────────────────────────────

class TestEvalComplex:
    def test_leaf_x(self) -> None:
        node = {"op": "leaf", "val": "x"}
        assert eval_complex(node, 3.7) == complex(3.7)

    def test_leaf_ix(self) -> None:
        node = {"op": "leaf", "val": "ix"}
        result = eval_complex(node, 2.5)
        assert result == complex(0, 2.5)

    def test_leaf_i(self) -> None:
        node = {"op": "leaf", "val": "i"}
        assert eval_complex(node, 99.0) == 1j

    def test_leaf_numeric(self) -> None:
        node = {"op": "leaf", "val": 1.0}
        assert eval_complex(node, 5.0) == complex(1.0)

    def test_nested_eml(self) -> None:
        """eml(eml(x, 1), 1) = exp(exp(x) - 0) - 0 = exp(exp(x))."""
        inner = {"op": "eml", "left": {"op": "leaf", "val": "x"},
                 "right": {"op": "leaf", "val": 1.0}}
        outer = {"op": "eml", "left": inner, "right": {"op": "leaf", "val": 1.0}}
        for x in [-0.5, 0.0, 0.3]:
            expected = cmath.exp(cmath.exp(x) - cmath.log(1.0)) - cmath.log(1.0)
            result   = eval_complex(outer, x)
            assert abs(result - expected) < 1e-12

    def test_incomplete_raises(self) -> None:
        node = {"op": "?"}
        with pytest.raises(ValueError, match="incomplete"):
            eval_complex(node, 1.0)

    def test_ln_zero_raises(self) -> None:
        """eml(a, 0) inside a tree should raise ValueError."""
        node = {"op": "eml",
                "left":  {"op": "leaf", "val": 0.0},
                "right": {"op": "leaf", "val": 0.0}}
        with pytest.raises(ValueError):
            eval_complex(node, 1.0)


# ── score_complex_projection ──────────────────────────────────────────────────

class TestScoreComplexProjection:
    def test_euler_path_scores_zero_for_sin(self) -> None:
        """Im(eml(ix, 1)) should give MSE=0 when target is sin(x)."""
        probe_x = [-2.0 + 4.0 * i / 49 for i in range(50)]
        probe_y = [math.sin(xi) for xi in probe_x]
        node    = euler_path_node()
        mse     = score_complex_projection(node, probe_x, probe_y, projection="imag")
        assert mse < 1e-28, f"Expected near-zero MSE, got {mse}"

    def test_euler_path_scores_zero_for_cos(self) -> None:
        """Re(eml(ix, 1)) should give MSE=0 when target is cos(x)."""
        probe_x = [-2.0 + 4.0 * i / 49 for i in range(50)]
        probe_y = [math.cos(xi) for xi in probe_x]
        node    = euler_path_node()
        mse     = score_complex_projection(node, probe_x, probe_y, projection="real")
        assert mse < 1e-28, f"Expected near-zero MSE, got {mse}"

    def test_bad_tree_returns_inf(self) -> None:
        """A tree with ln(0) domain error should score INF."""
        bad = {"op": "eml",
               "left":  {"op": "leaf", "val": 0.0},
               "right": {"op": "leaf", "val": 0.0}}
        probe_x = [0.5, 1.0]
        probe_y = [0.5, 1.0]
        mse = score_complex_projection(bad, probe_x, probe_y)
        assert mse == float("inf")

    def test_constant_tree_nonzero_mse(self) -> None:
        """Constant-1 tree should have nonzero MSE against sin(x)."""
        probe_x = [-1.0, 0.0, 1.0]
        probe_y = [math.sin(xi) for xi in probe_x]
        node    = {"op": "leaf", "val": 1.0}
        mse     = score_complex_projection(node, probe_x, probe_y, projection="real")
        assert mse > 0.1


# ── formula_complex ───────────────────────────────────────────────────────────

class TestFormulaComplex:
    def test_euler_path(self) -> None:
        assert formula_complex(euler_path_node()) == "eml(ix, 1.0)"

    def test_leaf_x(self) -> None:
        assert formula_complex({"op": "leaf", "val": "x"}) == "x"

    def test_leaf_i(self) -> None:
        assert formula_complex({"op": "leaf", "val": "i"}) == "i"

    def test_leaf_ix(self) -> None:
        assert formula_complex({"op": "leaf", "val": "ix"}) == "ix"

    def test_leaf_numeric(self) -> None:
        assert formula_complex({"op": "leaf", "val": 1.0}) == "1.0"

    def test_placeholder(self) -> None:
        assert formula_complex({"op": "?"}) == "?"

    def test_nested(self) -> None:
        node = {
            "op": "eml",
            "left":  {"op": "leaf", "val": "ix"},
            "right": {
                "op": "eml",
                "left":  {"op": "leaf", "val": 1.0},
                "right": {"op": "leaf", "val": "x"},
            },
        }
        assert formula_complex(node) == "eml(ix, eml(1.0, x))"


# ── COMPLEX_TERMINALS ─────────────────────────────────────────────────────────

class TestComplexTerminals:
    def test_contains_extended_set(self) -> None:
        assert 1.0   in COMPLEX_TERMINALS
        assert "x"   in COMPLEX_TERMINALS
        assert "ix"  in COMPLEX_TERMINALS
        assert "i"   in COMPLEX_TERMINALS
        assert len(COMPLEX_TERMINALS) == 4


# ── Integration: Euler path bypasses Infinite Zeros Barrier ──────────────────

class TestInfiniteZerosBarrierBypass:
    """
    The Infinite Zeros Barrier states that no *real-valued* EML tree can
    equal sin(x) because such a tree is real-analytic with finitely many
    zeros, while sin has infinitely many.

    This test confirms that *complex* EML trees bypass the barrier:
    Im(eml(ix, 1)) = sin(x) exactly, to machine precision, across a range
    that includes many zeros of sin.
    """

    def test_sin_zeros_matched(self) -> None:
        """Im(eml(ix, 1)) = 0 exactly at x = k*pi for k in range."""
        for k in range(-5, 6):
            x   = k * math.pi
            val = sin_via_euler(x)
            assert abs(val) < 2e-14, (
                f"sin_via_euler({k}*pi) = {val!r}, expected 0"
            )

    def test_sin_full_period(self) -> None:
        """Im(eml(ix, 1)) matches math.sin across full [-4pi, 4pi] range."""
        probe_x = [-4 * math.pi + 8 * math.pi * i / 999 for i in range(1000)]
        max_err = max(abs(sin_via_euler(x) - math.sin(x)) for x in probe_x)
        assert max_err < 1e-14, f"Max error over [-4pi, 4pi]: {max_err}"
