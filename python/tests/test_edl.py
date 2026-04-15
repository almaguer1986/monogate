"""Tests for the EDL operator and Operator abstraction."""
import cmath
import math

import pytest
import torch

from monogate.core import EDL, EML, Operator, exp_edl, ln_edl, make_exp, make_ln
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
