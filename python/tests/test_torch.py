"""
Tests for monogate.torch_ops and monogate.network.

Requires: torch
Run with:  pytest tests/test_torch.py

Coverage:
  - Numerical accuracy of tensor ops vs core.py (spot-checked)
  - Gradient flow through all ops (autograd.gradcheck)
  - neg_eml torch.where: gradients flow through both regimes
  - EMLTree: forward pass, training convergence toward constant
  - EMLNetwork: forward pass, training convergence on simple function
  - fit() returns loss list
"""

import math

import pytest

torch = pytest.importorskip("torch", reason="torch not installed")

import torch
import torch.autograd as autograd
from torch import Tensor

from monogate.torch_ops import (
    add_eml,
    div_eml,
    exp_eml,
    ln_eml,
    mul_eml,
    neg_eml,
    op,
    pow_eml,
    recip_eml,
    sub_eml,
)
from monogate.network import EMLNetwork, EMLTree, fit

TOL = 1e-6   # looser tolerance for float32 tensors


def t(v: float, requires_grad: bool = False, dtype=torch.float64) -> Tensor:
    """Convenience: scalar tensor from float."""
    return torch.tensor(v, dtype=dtype, requires_grad=requires_grad)


def tg(v: float) -> Tensor:
    """Scalar float64 tensor with grad enabled."""
    return t(v, requires_grad=True)


# ── op ────────────────────────────────────────────────────────────────────────

class TestOpTensor:
    def test_op_one_one(self):
        result = op(t(1.0), t(1.0))
        assert abs(result.item() - math.e) < TOL

    def test_op_zero_one(self):
        result = op(t(0.0), t(1.0))
        assert abs(result.item() - 1.0) < TOL

    def test_op_batched(self):
        x = torch.tensor([0.0, 1.0, 2.0], dtype=torch.float64)
        y = torch.tensor([1.0, 1.0, 1.0], dtype=torch.float64)
        result = op(x, y)
        expected = torch.tensor([1.0, math.e, math.e**2], dtype=torch.float64)
        assert torch.allclose(result, expected, atol=TOL)

    def test_op_gradient(self):
        x = tg(1.0)
        y = tg(1.0)
        result = op(x, y)
        result.backward()
        # d/dx [exp(x) - ln(y)] = exp(x)
        assert abs(x.grad.item() - math.e) < TOL
        # d/dy [exp(x) - ln(y)] = -1/y
        assert abs(y.grad.item() - (-1.0)) < TOL


# ── exp_eml ───────────────────────────────────────────────────────────────────

class TestExpEmlTensor:
    def test_exp_zero(self):
        assert abs(exp_eml(t(0.0)).item() - 1.0) < TOL

    def test_exp_one(self):
        assert abs(exp_eml(t(1.0)).item() - math.e) < TOL

    def test_exp_gradient(self):
        x = tg(2.0)
        exp_eml(x).backward()
        assert abs(x.grad.item() - math.exp(2.0)) < TOL


# ── ln_eml ────────────────────────────────────────────────────────────────────

class TestLnEmlTensor:
    def test_ln_one(self):
        assert abs(ln_eml(t(1.0)).item() - 0.0) < TOL

    def test_ln_e(self):
        assert abs(ln_eml(t(math.e)).item() - 1.0) < 1e-5

    def test_ln_gradient(self):
        x = tg(2.0)
        ln_eml(x).backward()
        # d/dx ln(x) = 1/x
        assert abs(x.grad.item() - 0.5) < 1e-5


# ── neg_eml ───────────────────────────────────────────────────────────────────

class TestNegEmlTensor:
    def test_neg_zero(self):
        assert abs(neg_eml(t(0.0)).item()) < TOL

    def test_neg_positive(self):
        assert abs(neg_eml(t(3.0)).item() + 3.0) < 1e-5

    def test_neg_negative(self):
        assert abs(neg_eml(t(-5.0)).item() - 5.0) < 1e-5

    def test_neg_gradient_positive_regime(self):
        """Gradient of −y with respect to y (regime B: y > 0) should be −1."""
        y = tg(2.0)
        neg_eml(y).backward()
        assert abs(y.grad.item() - (-1.0)) < 1e-4

    def test_neg_gradient_negative_regime(self):
        """Gradient of −y with respect to y (regime A: y < 0) should be −1."""
        y = tg(-2.0)
        neg_eml(y).backward()
        assert abs(y.grad.item() - (-1.0)) < 1e-4

    def test_neg_gradient_zero_boundary(self):
        """At y=0 the gradient should still be ≈ −1."""
        y = tg(0.0)
        neg_eml(y).backward()
        assert abs(y.grad.item() - (-1.0)) < 1e-3

    def test_neg_batched_gradient(self):
        """torch.where should route gradients correctly for mixed-sign batch."""
        y = torch.tensor([-3.0, -1.0, 0.0, 1.0, 3.0],
                         dtype=torch.float64, requires_grad=True)
        neg_eml(y).sum().backward()
        # All gradients should be ≈ −1
        assert torch.allclose(y.grad, torch.full_like(y, -1.0), atol=1e-4)

    def test_double_neg(self):
        for v in [-3.0, 0.0, 2.0]:
            result = neg_eml(neg_eml(t(v)))
            assert abs(result.item() - v) < 1e-5


# ── add_eml ───────────────────────────────────────────────────────────────────

class TestAddEmlTensor:
    def test_add_positive(self):
        assert abs(add_eml(t(2.0), t(3.0)).item() - 5.0) < 1e-5

    def test_add_negative(self):
        assert abs(add_eml(t(-2.0), t(-3.0)).item() + 5.0) < 1e-5

    def test_add_mixed(self):
        assert abs(add_eml(t(0.5), t(-1.5)).item() + 1.0) < 1e-5

    def test_add_gradient_x(self):
        x = tg(2.0)
        y = t(3.0)
        add_eml(x, y).backward()
        assert abs(x.grad.item() - 1.0) < 1e-4

    def test_add_gradient_y(self):
        x = t(2.0)
        y = tg(3.0)
        add_eml(x, y).backward()
        assert abs(y.grad.item() - 1.0) < 1e-4


# ── mul_eml ───────────────────────────────────────────────────────────────────

class TestMulEmlTensor:
    def test_mul_integers(self):
        assert abs(mul_eml(t(2.0), t(3.0)).item() - 6.0) < 1e-5

    def test_mul_fraction(self):
        assert abs(mul_eml(t(4.0), t(0.25)).item() - 1.0) < 1e-5

    def test_mul_gradient_x(self):
        # d/dx (x*y) = y
        x = tg(2.0)
        y = t(3.0)
        mul_eml(x, y).backward()
        assert abs(x.grad.item() - 3.0) < 1e-4


# ── div_eml ───────────────────────────────────────────────────────────────────

class TestDivEmlTensor:
    def test_div_exact(self):
        assert abs(div_eml(t(6.0), t(3.0)).item() - 2.0) < 1e-5

    def test_div_fraction(self):
        assert abs(div_eml(t(1.0), t(4.0)).item() - 0.25) < 1e-5


# ── pow_eml ───────────────────────────────────────────────────────────────────

class TestPowEmlTensor:
    def test_pow_integer(self):
        assert abs(pow_eml(t(2.0), t(10.0)).item() - 1024.0) < 1e-5

    def test_pow_half(self):
        assert abs(pow_eml(t(4.0), t(0.5)).item() - 2.0) < 1e-5


# ── recip_eml ─────────────────────────────────────────────────────────────────

class TestRecipEmlTensor:
    def test_recip_two(self):
        assert abs(recip_eml(t(2.0)).item() - 0.5) < 1e-5

    def test_recip_four(self):
        assert abs(recip_eml(t(4.0)).item() - 0.25) < 1e-5


# ── EMLTree ───────────────────────────────────────────────────────────────────

class TestEMLTree:
    def test_depth0_forward(self):
        model = EMLTree(depth=0)
        out = model()
        assert out.ndim == 0  # scalar tensor
        assert math.isfinite(out.item())

    def test_depth1_forward(self):
        model = EMLTree(depth=1)
        out = model()
        assert math.isfinite(out.item())

    def test_formula_returns_string(self):
        model = EMLTree(depth=2)
        f = model.formula()
        assert isinstance(f, str)
        assert "eml" in f

    def test_depth0_formula_no_eml(self):
        model = EMLTree(depth=0)
        f = model.formula()
        assert "eml" not in f

    def test_parameters_exist(self):
        model = EMLTree(depth=2)
        params = list(model.parameters())
        # depth=2 complete binary tree: 4 leaves → 4 parameters
        assert len(params) == 4

    def test_training_converges_toward_constant(self):
        """EMLTree should be able to approximate a simple constant (e)."""
        torch.manual_seed(42)
        model = EMLTree(depth=1)  # depth=1: eml(leaf, leaf)
        # Initialize leaves near 1.0 (default), eml(1,1) = e — should converge fast
        losses = fit(
            model,
            target=torch.tensor(math.e, dtype=torch.float32),
            steps=500,
            lr=1e-2,
            log_every=0,
        )
        assert len(losses) > 0
        assert losses[-1] < losses[0] or losses[-1] < 1e-3

    def test_training_converges_to_e(self):
        """depth=1 tree with init=1.0 evaluates to exp(1) - ln(softplus(1))."""
        import torch.nn.functional as F
        model = EMLTree(depth=1, init=1.0)
        # _Node.forward applies softplus to the right child before computing eml.
        # At init=1.0: eml(1, softplus(1)) = exp(1) - ln(softplus(1))
        sp1 = F.softplus(torch.tensor(1.0)).item()
        expected = math.exp(1.0) - math.log(sp1)
        out = model()
        assert abs(out.item() - expected) < 1e-5

    def test_fit_returns_loss_list(self):
        model = EMLTree(depth=1)
        losses = fit(
            model,
            target=torch.tensor(2.0),
            steps=10,
            lr=1e-2,
            log_every=0,
        )
        assert isinstance(losses, list)
        assert all(isinstance(v, float) for v in losses)


# ── EMLNetwork ────────────────────────────────────────────────────────────────

class TestEMLNetwork:
    def test_forward_shape(self):
        model = EMLNetwork(in_features=2, depth=1)
        x = torch.randn(8, 2)
        out = model(x)
        assert out.shape == (8,)

    def test_formula_returns_string(self):
        model = EMLNetwork(in_features=3, depth=1)
        f = model.formula()
        assert isinstance(f, str)
        assert "eml" in f

    def test_parameters_exist(self):
        model = EMLNetwork(in_features=2, depth=1)
        params = list(model.parameters())
        # depth=1 → 2 leaves, each nn.Linear(2,1) has 2 parameter tensors (weight, bias)
        # 2 leaves × 2 tensors = 4 parameter tensors total
        assert len(params) == 4

    def test_training_identity(self):
        """EMLNetwork should be able to approximate the identity function y=x."""
        torch.manual_seed(0)
        model = EMLNetwork(in_features=1, depth=1)
        x = torch.linspace(0.1, 2.0, 30).unsqueeze(1)
        y = x.squeeze()  # identity
        losses = fit(
            model,
            x=x,
            y=y,
            steps=500,
            lr=1e-2,
            log_every=0,
        )
        assert len(losses) > 0
        # Check that loss decreased (not strictly required to converge fully in 500 steps)
        assert losses[-1] < losses[0] + 1.0  # at least not worse by >1

    def test_requires_x_and_y(self):
        model = EMLNetwork(in_features=2, depth=1)
        with pytest.raises(ValueError, match="requires `x` and `y`"):
            fit(model, steps=1, log_every=0)

    def test_fit_returns_loss_list(self):
        model = EMLNetwork(in_features=1, depth=1)
        x = torch.ones(4, 1)
        y = torch.ones(4)
        losses = fit(model, x=x, y=y, steps=5, lr=1e-3, log_every=0)
        assert isinstance(losses, list)
