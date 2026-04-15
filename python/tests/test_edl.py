"""Tests for the EDL operator and Operator abstraction."""
import cmath
import math

import pytest
import torch

from monogate.core import (
    EDL, EML, EDL_NEG_ONE, EDL_ONE, Operator,
    div_edl, exp_edl, ln_edl, make_exp, make_ln, mul_edl, neg_edl, pow_edl, recip_edl,
)
from monogate.torch_ops import edl_op


# ── Operator class ────────────────────────────────────────────────────────────

def test_operator_has_name():
    assert EML.name == "EML"
    assert EDL.name == "EDL"


def test_eml_constant():
    assert EML.constant == 1.0 + 0j


def test_edl_constant():
    assert abs(EDL.constant - cmath.e) < 1e-14


def test_operator_repr():
    assert "EML" in repr(EML)
    assert "EDL" in repr(EDL)


# ── EDL gate (Python / cmath) ─────────────────────────────────────────────────

def test_edl_fundamental_identity():
    # edl(x, e) = exp(x) — EDL's natural identity (ln(e)=1)
    x = 1.5
    result = EDL.func(x, cmath.e)
    assert abs(result - cmath.exp(x)) < 1e-14


def test_edl_various_inputs():
    # edl(0, e) = exp(0)/ln(e) = 1/1 = 1
    assert abs(EDL.func(0, cmath.e) - 1.0) < 1e-14
    # edl(1, e²) = exp(1)/ln(e²) = e/2
    e2 = cmath.e ** 2
    assert abs(EDL.func(1, e2) - cmath.e / 2) < 1e-14


def test_edl_domain_error_y_equals_1():
    with pytest.raises(ValueError, match="EDL domain error"):
        EDL.func(0, 1)


def test_edl_domain_error_y_equals_0():
    with pytest.raises(ValueError, match="EDL domain error"):
        EDL.func(0, 0)


# ── EML gate unchanged ────────────────────────────────────────────────────────

def test_eml_func_smoke():
    # eml(1, 1) = e^1 - ln(1) = e
    result = EML.func(1, 1)
    assert abs(result - cmath.e) < 1e-14


def test_eml_op_unchanged():
    # Existing op() function still works — regression guard
    from monogate import op
    assert abs(op(1, 1) - math.e) < 1e-14


# ── EDL tensor op ─────────────────────────────────────────────────────────────

def test_edl_op_tensor_identity():
    # edl_op(x, e) ≈ exp(x)
    x = torch.tensor(1.5)
    e = torch.tensor(math.e)
    result = edl_op(x, e)
    assert abs(result.item() - math.exp(1.5)) < 1e-6


def test_edl_op_tensor_batch():
    x = torch.tensor([0.0, 1.0, 2.0])
    e = torch.full_like(x, math.e)
    result = edl_op(x, e)
    expected = torch.exp(x)
    assert torch.allclose(result, expected, atol=1e-6)


def test_edl_op_tensor_gradients():
    # Gradients must flow through edl_op
    x = torch.tensor(1.0, requires_grad=True)
    y = torch.tensor(math.e, requires_grad=True)
    out = edl_op(x, y)
    out.backward()
    assert x.grad is not None
    assert y.grad is not None


# ── EMLTree with op_func=edl_op ───────────────────────────────────────────────

def test_emltree_edl_forward():
    from monogate.network import EMLTree
    model = EMLTree(depth=1, op_func=edl_op)
    out = model()
    assert torch.isfinite(out)


def test_emltree_default_still_eml():
    from monogate.network import EMLTree
    model = EMLTree(depth=1)
    out = model()
    assert torch.isfinite(out)


# ── EMLNetwork with op_func=edl_op ────────────────────────────────────────────

def test_emlnetwork_edl_forward():
    from monogate.network import EMLNetwork
    model = EMLNetwork(in_features=1, depth=1, op_func=edl_op)
    x = torch.ones(4, 1)
    out = model(x)
    assert out.shape == (4,)
    assert torch.all(torch.isfinite(out))


# ── make_exp / make_ln ────────────────────────────────────────────────────────

def test_make_exp_eml():
    f = make_exp(EML)
    assert abs(f(1.5) - cmath.exp(1.5)) < 1e-12


def test_make_exp_edl():
    f = make_exp(EDL)
    assert abs(f(1.5) - cmath.exp(1.5)) < 1e-12


def test_exp_edl_singleton():
    assert abs(exp_edl(0) - 1.0) < 1e-14
    assert abs(exp_edl(1) - cmath.e) < 1e-14


def test_make_ln_eml():
    f = make_ln(EML)
    assert abs(f(math.e) - 1.0) < 1e-12
    assert abs(f(1) - 0.0) < 1e-12
    assert abs(f(2) - math.log(2)) < 1e-12


def test_make_ln_edl():
    # 3-node formula: edl(0, edl(edl(0, x), e))
    f = make_ln(EDL)
    assert abs(f(math.e) - 1.0) < 1e-12
    assert abs(f(2) - math.log(2)) < 1e-12
    assert abs(f(10) - math.log(10)) < 1e-12


def test_ln_edl_singleton():
    assert abs(ln_edl(math.e) - 1.0) < 1e-12
    assert abs(ln_edl(2) - math.log(2)) < 1e-12


def test_ln_is_inverse_of_exp_eml():
    f_exp = make_exp(EML)
    f_ln  = make_ln(EML)
    for x in (0.5, 1.0, 2.0, 3.7):
        assert abs(f_ln(f_exp(x)) - x) < 1e-10


def test_ln_is_inverse_of_exp_edl():
    f_exp = make_exp(EDL)
    f_ln  = make_ln(EDL)
    for x in (0.5, 1.0, 2.0, 3.7):
        assert abs(f_ln(f_exp(x)) - x) < 1e-10


def test_make_ln_unknown_operator_raises():
    other = Operator("OTHER", lambda x, y: x + y, 0j)
    with pytest.raises(NotImplementedError):
        make_ln(other)


# ── div_edl ───────────────────────────────────────────────────────────────────

def test_div_edl_basic():
    # edl(ln(x), exp(y)) = x / y
    assert abs(div_edl(6 + 0j, 3 + 0j) - 2.0) < 1e-12
    assert abs(div_edl(5 + 0j, 2 + 0j) - 2.5) < 1e-12


def test_div_edl_matches_true_division():
    # Note: x=1 excluded — ln_edl(1) hits the EDL singularity in the intermediate
    # step edl(0, 1).  Mathematically ln(1)=0 but the 3-node formula can't reach it.
    for x, y in [(10, 4), (7, 3), (2, 5), (2.5, 0.5)]:
        result = div_edl(complex(x), complex(y))
        assert abs(result - x / y) < 1e-10, f"div_edl({x},{y}) = {result}, expected {x/y}"


def test_div_edl_is_not_subtraction():
    # Direct proof that the "sub" parallel does NOT give subtraction for EDL
    result = div_edl(5 + 0j, 2 + 0j)
    assert abs(result - 2.5) < 1e-12   # = 5/2
    assert abs(result - 3.0) > 0.1     # NOT 5-2


# ── recip_edl ─────────────────────────────────────────────────────────────────

def test_recip_edl_basic():
    assert abs(recip_edl(2 + 0j) - 0.5) < 1e-12
    assert abs(recip_edl(4 + 0j) - 0.25) < 1e-12
    assert abs(recip_edl(10 + 0j) - 0.1) < 1e-12


def test_recip_edl_self_inverse():
    for x in (2.0, 5.0, 0.3, 7.5):
        assert abs(recip_edl(recip_edl(complex(x))) - x) < 1e-10


def test_recip_edl_consistent_with_div():
    # 1/x = div_edl(1, x) is NOT available via the ln_edl path (hits singularity),
    # but recip_edl bypasses that by using edl(0, edl(x, e)) directly.
    # Confirm recip_edl agrees with plain Python division.
    for x in (2.5, 3.0, 0.7):
        assert abs(recip_edl(complex(x)) - 1/x) < 1e-12


# ── neg_edl ───────────────────────────────────────────────────────────────────

def test_neg_edl_basic():
    assert abs(neg_edl(2 + 0j) - (-2)) < 1e-12
    assert abs(neg_edl(5 + 0j) - (-5)) < 1e-12
    assert abs(neg_edl(0.5 + 0j) - (-0.5)) < 1e-12


def test_neg_edl_double_negation():
    for x in (2.0, 3.7, 0.4):
        # neg_edl(-x) requires x<0 which hits domain issues; test x>1 roundtrip
        # via neg_edl(neg_edl(x)) — but neg_edl(x)<0 so ln_edl fails on that.
        # Instead confirm neg_edl(-neg_edl(x)) = x using recip and a workaround.
        neg_x = neg_edl(complex(x))
        # -(-x) = x: use div_edl(neg_x, EDL_NEG_ONE)
        # div_edl(-x, -1) = -x / -1 = x
        back = div_edl(neg_x, EDL_NEG_ONE)
        assert abs(back - x) < 1e-10, f"round-trip failed for x={x}: got {back}"


# ── EDL constants ─────────────────────────────────────────────────────────────

def test_edl_one():
    assert abs(EDL_ONE - 1.0) < 1e-14


def test_edl_neg_one():
    assert abs(EDL_NEG_ONE - (-1.0)) < 1e-14


def test_edl_neg_one_via_neg_edl():
    # neg_edl applied to EDL_ONE should give EDL_NEG_ONE
    # but EDL_ONE = 1 and ln_edl(1) hits the singularity — confirms the dead zone
    import pytest
    with pytest.raises(ValueError, match="EDL domain error"):
        neg_edl(EDL_ONE)


# ── mul_edl ───────────────────────────────────────────────────────────────────

def test_mul_edl_integers():
    assert abs(mul_edl(3 + 0j, 4 + 0j) - 12) < 1e-10
    assert abs(mul_edl(2 + 0j, 5 + 0j) - 10) < 1e-10


def test_mul_edl_fractions():
    assert abs(mul_edl(6 + 0j, 0.5 + 0j) - 3.0) < 1e-10
    assert abs(mul_edl(2.5 + 0j, 4.0 + 0j) - 10.0) < 1e-10


def test_mul_edl_identity():
    # x * 1 = x  (but x=1 is a domain hole for ln_edl, so test x=e)
    assert abs(mul_edl(math.e + 0j, 1.0 + 0j) - math.e) < 1e-10


def test_mul_edl_commutative():
    for x, y in [(3, 4), (2.5, 1.5), (7, 0.2)]:
        assert abs(mul_edl(complex(x), complex(y)) - mul_edl(complex(y), complex(x))) < 1e-10


def test_mul_edl_consistent_with_div():
    # x * y / y = x
    for x, y in [(6, 3), (5, 2), (10, 4)]:
        product = mul_edl(complex(x), complex(y))
        back = div_edl(product, complex(y))
        assert abs(back - x) < 1e-9, f"round-trip failed: x={x}, y={y}"


# ── pow_edl ───────────────────────────────────────────────────────────────────

def test_pow_edl_square():
    assert abs(pow_edl(3 + 0j, 2) - 9) < 1e-9
    assert abs(pow_edl(4 + 0j, 2) - 16) < 1e-9


def test_pow_edl_half():
    assert abs(pow_edl(9 + 0j, 0.5) - 3) < 1e-9
    assert abs(pow_edl(4 + 0j, 0.5) - 2) < 1e-9


def test_pow_edl_matches_math():
    for x, n in [(2, 10), (3, 3), (5, 0.5), (math.e, 2)]:
        result = pow_edl(complex(x), n)
        assert abs(result - x**n) < 1e-8, f"pow_edl({x},{n})={result}, expected {x**n}"


# ── add_edl not possible ──────────────────────────────────────────────────────

def test_add_edl_raises():
    from monogate.core import add_edl
    with pytest.raises(NotImplementedError):
        add_edl(3 + 0j, 4 + 0j)
