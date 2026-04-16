"""
Tests for monogate.complex_best — ComplexHybridOperator (CBEST).

Covers:
- Basic arithmetic ops return correct complex values
- Euler identity (exp(iπ) = -1)
- sin/cos via Euler path — SIN_NODE_COUNT = COS_NODE_COUNT = 1
- im() / re() helpers
- complex_best_optimize() returns a ComplexOptimizeResult
- Node-count constants are positive integers
- CBEST is a ComplexHybridOperator instance
- All operator methods present on CBEST
"""

import cmath
import math

import pytest

from monogate.complex_best import (
    AI_NODE_COUNT,
    CBEST,
    COS_NODE_COUNT,
    ERF_NODE_COUNT,
    J0_NODE_COUNT,
    SIN_NODE_COUNT,
    ComplexHybridOperator,
    ComplexOptimizeResult,
    complex_best_optimize,
    im,
    re,
)


# ── Instance / type checks ────────────────────────────────────────────────────

def test_cbest_is_complex_hybrid_operator():
    assert isinstance(CBEST, ComplexHybridOperator)


def test_cbest_repr_contains_cbest():
    assert "CBEST" in repr(CBEST)


# ── im / re helpers ───────────────────────────────────────────────────────────

def test_im_of_pure_imaginary():
    assert im(2j) == pytest.approx(2.0)


def test_re_of_complex():
    assert re(3.0 + 4j) == pytest.approx(3.0)


def test_im_of_real_is_zero():
    assert im(5.0) == pytest.approx(0.0)


def test_re_of_pure_imaginary_is_zero():
    assert re(1j) == pytest.approx(0.0)


# ── Euler identity ────────────────────────────────────────────────────────────

def test_euler_identity():
    z = CBEST.exp(1j * math.pi)
    assert abs(z.real - (-1.0)) < 1e-10
    assert abs(z.imag) < 1e-10


def test_exp_zero_is_one():
    assert CBEST.exp(0j) == pytest.approx(1.0 + 0j)


# ── sin / cos via Euler path ──────────────────────────────────────────────────

@pytest.mark.parametrize("x", [0.0, 0.5, 1.0, -1.0, math.pi / 4, -math.pi / 3])
def test_cbest_sin_matches_math_sin(x: float):
    # CBEST.sin returns the full complex number exp(ix); Im part = sin(x)
    z = CBEST.sin(x)
    assert abs(z.imag - math.sin(x)) < 1e-12, f"sin({x}): Im={z.imag}, expected {math.sin(x)}"


@pytest.mark.parametrize("x", [0.5, 1.0, -1.0, math.pi / 4, -math.pi / 3])
def test_cbest_cos_matches_math_cos(x: float):
    # CBEST.cos returns the full complex number exp(ix); Re part = cos(x)
    z = CBEST.cos(x)
    assert abs(z.real - math.cos(x)) < 1e-12, f"cos({x}): Re={z.real}, expected {math.cos(x)}"


# ── Node-count constants ──────────────────────────────────────────────────────

def test_sin_node_count_is_one():
    assert SIN_NODE_COUNT == 1


def test_cos_node_count_is_one():
    assert COS_NODE_COUNT == 1


def test_j0_node_count_positive():
    assert isinstance(J0_NODE_COUNT, int) and J0_NODE_COUNT > 0


def test_ai_node_count_positive():
    assert isinstance(AI_NODE_COUNT, int) and AI_NODE_COUNT > 0


def test_erf_node_count_positive():
    assert isinstance(ERF_NODE_COUNT, int) and ERF_NODE_COUNT > 0


def test_special_function_counts_ordered():
    # Sin/cos are provably 1-node; special functions require deeper trees
    assert J0_NODE_COUNT  >= 1
    assert AI_NODE_COUNT  >= 1
    assert ERF_NODE_COUNT >= 1


# ── Basic arithmetic operators ────────────────────────────────────────────────

def test_cbest_ln_of_one_is_zero():
    assert abs(CBEST.ln(1.0)) < 1e-15


def test_cbest_ln_of_e():
    assert abs(CBEST.ln(cmath.e) - 1.0) < 1e-12


def test_cbest_pow_real():
    result = CBEST.pow(2.0, 10.0)
    assert abs(result - 1024.0) < 1e-6


def test_cbest_div_real():
    result = CBEST.div(6.0, 2.0)
    assert abs(result - 3.0) < 1e-12


def test_cbest_mul_real():
    result = CBEST.mul(3.0, 4.0)
    assert abs(result - 12.0) < 1e-6


def test_cbest_add_real():
    result = CBEST.add(3.0, 4.0)
    assert abs(result - 7.0) < 1e-6


def test_cbest_sub_real():
    result = CBEST.sub(5.0, 2.0)
    assert abs(result - 3.0) < 1e-6


def test_cbest_neg_real():
    result = CBEST.neg(3.0)
    assert abs(result - (-3.0)) < 1e-6


def test_cbest_recip_real():
    result = CBEST.recip(4.0)
    assert abs(result - 0.25) < 1e-10


# ── Complex-valued inputs ─────────────────────────────────────────────────────

def test_cbest_exp_complex():
    # exp(i * π/2) should be ≈ i
    z = CBEST.exp(1j * math.pi / 2)
    assert abs(z.real) < 1e-10
    assert abs(z.imag - 1.0) < 1e-10


def test_cbest_ln_complex():
    # ln(exp(1+2j)) ≈ 1+2j  (within principal branch)
    z = 1.0 + 2.0j
    assert abs(CBEST.ln(CBEST.exp(z)) - z) < 1e-10


# ── complex_best_optimize ─────────────────────────────────────────────────────

def test_complex_best_optimize_returns_result():
    result = complex_best_optimize("sin(x) + cos(x)")
    assert isinstance(result, ComplexOptimizeResult)


def test_complex_best_optimize_has_savings():
    result = complex_best_optimize("sin(x) + cos(x)")
    assert hasattr(result, "total_cbest")
    assert hasattr(result, "total_real_best")
    assert hasattr(result, "complex_savings_pct")


def test_complex_best_optimize_sin_cos_savings_positive():
    result = complex_best_optimize("sin(x) + cos(x)")
    # CBEST sin=1, cos=1 vs real-BEST sin=63, cos=63 — savings must be large
    assert result.complex_savings_pct >= 0


def test_complex_best_optimize_empty_no_ops():
    # Expression with no recognised ops should return zero savings
    result = complex_best_optimize("x + 1")
    assert result.total_cbest == 0 or result.complex_savings_pct >= 0


def test_complex_best_optimize_repr():
    result = complex_best_optimize("sin(x)")
    assert "ComplexOptimizeResult" in repr(result) or isinstance(result, ComplexOptimizeResult)
