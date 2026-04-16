"""
Tests for monogate.pinn — EMLPINN and fit_pinn.

Covers:
- EMLPINN constructor with all supported equations
- Invalid equation raises ValueError
- forward() returns correct tensor shape
- residual() returns correct tensor shape
- fit_pinn() returns PINNResult with expected fields
- Loss does not blow up (finite after training)
- history records (step, data_loss, physics_loss) tuples
- formula() returns a non-empty string
- lam_physics override works
- fit_pinn raises TypeError for non-EMLPINN model
- New equations: schrodinger, kdv_soliton, nls, lotka_volterra
  — constructor, parameter storage, residual shape, fit smoke test
"""

from __future__ import annotations

import math

import pytest

torch = pytest.importorskip("torch")

import torch as th
from monogate.pinn import EMLPINN, PINNResult, fit_pinn


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def harmonic_model() -> EMLPINN:
    return EMLPINN(equation="harmonic", omega=1.0, backbone_depth=2)


@pytest.fixture
def burgers_model() -> EMLPINN:
    return EMLPINN(equation="burgers", nu=0.05, backbone_depth=2)


@pytest.fixture
def heat_model() -> EMLPINN:
    return EMLPINN(equation="heat", backbone_depth=2)


@pytest.fixture
def small_data():
    x_d = th.linspace(0, math.pi, 20).unsqueeze(1)
    y_d = th.sin(x_d.squeeze(1))
    x_p = th.linspace(0, math.pi, 40).unsqueeze(1)
    return x_d, y_d, x_p


# ── Constructor ───────────────────────────────────────────────────────────────

def test_emlpinn_creates_harmonic():
    m = EMLPINN(equation="harmonic")
    assert m.equation == "harmonic"


def test_emlpinn_creates_burgers():
    m = EMLPINN(equation="burgers")
    assert m.equation == "burgers"


def test_emlpinn_creates_heat():
    m = EMLPINN(equation="heat")
    assert m.equation == "heat"


def test_emlpinn_invalid_equation_raises():
    with pytest.raises(ValueError, match="equation must be one of"):
        EMLPINN(equation="wave")


def test_emlpinn_default_equation_is_harmonic():
    m = EMLPINN()
    assert m.equation == "harmonic"


def test_emlpinn_omega_stored(harmonic_model):
    assert harmonic_model.omega == 1.0


def test_emlpinn_nu_stored(burgers_model):
    assert burgers_model.nu == pytest.approx(0.05)


# ── forward shape ─────────────────────────────────────────────────────────────

def test_forward_shape_harmonic(harmonic_model):
    x = th.linspace(0, 1, 10).unsqueeze(1)
    out = harmonic_model(x)
    assert out.shape == (10,)


def test_forward_shape_burgers(burgers_model):
    x = th.linspace(-1, 1, 15).unsqueeze(1)
    out = burgers_model(x)
    assert out.shape == (15,)


def test_forward_shape_heat(heat_model):
    x = th.linspace(0, 1, 8).unsqueeze(1)
    out = heat_model(x)
    assert out.shape == (8,)


# ── residual shape ────────────────────────────────────────────────────────────

def test_residual_shape_harmonic(harmonic_model):
    x = th.linspace(0, 1, 12).unsqueeze(1)
    r = harmonic_model.residual(x)
    assert r.shape == (12,)


def test_residual_shape_burgers(burgers_model):
    x = th.linspace(-1, 1, 10).unsqueeze(1)
    r = burgers_model.residual(x)
    assert r.shape == (10,)


def test_residual_shape_heat(heat_model):
    x = th.linspace(0, 1, 8).unsqueeze(1)
    r = heat_model.residual(x)
    assert r.shape == (8,)


def test_residual_is_tensor(harmonic_model):
    x = th.tensor([[0.5]])
    r = harmonic_model.residual(x)
    assert isinstance(r, th.Tensor)


# ── fit_pinn returns PINNResult ───────────────────────────────────────────────

def test_fit_pinn_returns_pinnresult(harmonic_model, small_data):
    x_d, y_d, x_p = small_data
    result = fit_pinn(harmonic_model, x_d, y_d, x_p, steps=50, log_every=0)
    assert isinstance(result, PINNResult)


def test_fit_pinn_data_loss_finite(harmonic_model, small_data):
    x_d, y_d, x_p = small_data
    result = fit_pinn(harmonic_model, x_d, y_d, x_p, steps=50, log_every=0)
    assert math.isfinite(result.data_loss)


def test_fit_pinn_physics_loss_finite(harmonic_model, small_data):
    x_d, y_d, x_p = small_data
    result = fit_pinn(harmonic_model, x_d, y_d, x_p, steps=50, log_every=0)
    assert math.isfinite(result.physics_loss)


def test_fit_pinn_elapsed_positive(harmonic_model, small_data):
    x_d, y_d, x_p = small_data
    result = fit_pinn(harmonic_model, x_d, y_d, x_p, steps=50, log_every=0)
    assert result.elapsed_s > 0.0


def test_fit_pinn_formula_nonempty(harmonic_model, small_data):
    x_d, y_d, x_p = small_data
    result = fit_pinn(harmonic_model, x_d, y_d, x_p, steps=50, log_every=0)
    assert len(result.formula) > 0


def test_fit_pinn_history_populated(harmonic_model, small_data):
    x_d, y_d, x_p = small_data
    result = fit_pinn(harmonic_model, x_d, y_d, x_p, steps=100, log_every=0)
    assert len(result.history) > 0


def test_fit_pinn_history_tuple_length(harmonic_model, small_data):
    x_d, y_d, x_p = small_data
    result = fit_pinn(harmonic_model, x_d, y_d, x_p, steps=50, log_every=0)
    if result.history:
        step, dl, pl = result.history[0]
        assert isinstance(step, int)
        assert isinstance(dl, float)
        assert isinstance(pl, float)


# ── All equations smoke-test ──────────────────────────────────────────────────

@pytest.mark.parametrize("equation", ["harmonic", "burgers", "heat"])
def test_fit_pinn_all_equations(equation):
    m = EMLPINN(equation=equation, backbone_depth=2)
    x_d = th.linspace(0, 1, 15).unsqueeze(1)
    y_d = x_d.squeeze(1) * 0.5          # trivial target
    x_p = th.linspace(0, 1, 20).unsqueeze(1)
    result = fit_pinn(m, x_d, y_d, x_p, steps=30, log_every=0)
    assert math.isfinite(result.data_loss)
    assert math.isfinite(result.physics_loss)


# ── lam_physics override ──────────────────────────────────────────────────────

def test_lam_physics_override(small_data):
    x_d, y_d, x_p = small_data
    m = EMLPINN(equation="harmonic", lam_physics=0.5)
    # override to zero — physics loss should be ignored
    result = fit_pinn(m, x_d, y_d, x_p, steps=30, lam_physics=0.0, log_every=0)
    assert math.isfinite(result.data_loss)


# ── TypeError for wrong model ─────────────────────────────────────────────────

def test_fit_pinn_wrong_model_type():
    import torch.nn as nn
    bad_model = nn.Linear(1, 1)
    x = th.ones(5, 1)
    y = th.ones(5)
    with pytest.raises(TypeError, match="fit_pinn: model must be EMLPINN"):
        fit_pinn(bad_model, x, y, x, steps=10)


# ── PINNResult repr ───────────────────────────────────────────────────────────

def test_pinnresult_repr_contains_data_loss(harmonic_model, small_data):
    x_d, y_d, x_p = small_data
    result = fit_pinn(harmonic_model, x_d, y_d, x_p, steps=20, log_every=0)
    r = repr(result)
    assert "data_loss" in r
    assert "physics_loss" in r


# ── formula contains EML ──────────────────────────────────────────────────────

def test_formula_contains_eml(harmonic_model, small_data):
    x_d, y_d, x_p = small_data
    result = fit_pinn(harmonic_model, x_d, y_d, x_p, steps=20, log_every=0)
    # Depth-2 EMLNetwork always has eml(eml(…), eml(…))
    assert "eml" in result.formula


# ── New equations: constructor ────────────────────────────────────────────────

def test_emlpinn_creates_schrodinger():
    m = EMLPINN(equation="schrodinger", k=2.0)
    assert m.equation == "schrodinger"
    assert m.k == pytest.approx(2.0)


def test_emlpinn_creates_kdv_soliton():
    m = EMLPINN(equation="kdv_soliton", c=1.5)
    assert m.equation == "kdv_soliton"
    assert m.c == pytest.approx(1.5)


def test_emlpinn_creates_nls():
    m = EMLPINN(equation="nls")
    assert m.equation == "nls"


def test_emlpinn_creates_lotka_volterra():
    m = EMLPINN(equation="lotka_volterra", alpha=0.5, beta=2.0)
    assert m.equation == "lotka_volterra"
    assert m.alpha == pytest.approx(0.5)
    assert m.beta == pytest.approx(2.0)


# ── New equations: forward shape ─────────────────────────────────────────────

@pytest.mark.parametrize("equation,kwargs", [
    ("schrodinger", {"k": 1.0}),
    ("kdv_soliton", {"c": 1.0}),
    ("nls", {}),
    ("lotka_volterra", {"alpha": 1.0, "beta": 1.0}),
])
def test_forward_shape_new_equations(equation, kwargs):
    m = EMLPINN(equation=equation, backbone_depth=2, **kwargs)
    x = th.linspace(-1, 1, 10).unsqueeze(1)
    out = m(x)
    assert out.shape == (10,)


# ── New equations: residual shape ────────────────────────────────────────────

@pytest.mark.parametrize("equation,kwargs", [
    ("schrodinger", {"k": 1.0}),
    ("kdv_soliton", {"c": 1.0}),
    ("nls", {}),
    ("lotka_volterra", {"alpha": 1.0, "beta": 1.0}),
])
def test_residual_shape_new_equations(equation, kwargs):
    m = EMLPINN(equation=equation, backbone_depth=2, **kwargs)
    x = th.linspace(-1, 1, 8).unsqueeze(1)
    r = m.residual(x)
    assert r.shape == (8,)
    assert isinstance(r, th.Tensor)


# ── New equations: residual is finite ────────────────────────────────────────

@pytest.mark.parametrize("equation,kwargs", [
    ("schrodinger", {"k": 1.0}),
    ("nls", {}),
    ("lotka_volterra", {"alpha": 1.0, "beta": 1.0}),
])
def test_residual_finite_new_equations(equation, kwargs):
    m = EMLPINN(equation=equation, backbone_depth=2, **kwargs)
    x = th.linspace(-0.5, 0.5, 8).unsqueeze(1)
    r = m.residual(x)
    assert all(math.isfinite(v.item()) for v in r)


# ── New equations: fit smoke test ─────────────────────────────────────────────

@pytest.mark.parametrize("equation,kwargs", [
    ("schrodinger", {"k": 1.0}),
    ("nls", {}),
    ("lotka_volterra", {"alpha": 1.0, "beta": 1.0}),
])
def test_fit_pinn_new_equations(equation, kwargs):
    m = EMLPINN(equation=equation, backbone_depth=2, **kwargs)
    x_d = th.linspace(-0.5, 0.5, 15).unsqueeze(1)
    y_d = th.cos(x_d.squeeze(1))
    x_p = th.linspace(-0.5, 0.5, 20).unsqueeze(1)
    result = fit_pinn(m, x_d, y_d, x_p, steps=30, log_every=0)
    assert math.isfinite(result.data_loss)
    assert math.isfinite(result.physics_loss)


def test_fit_pinn_kdv_soliton():
    """KdV needs u_xxx — verify it trains without error."""
    m = EMLPINN(equation="kdv_soliton", backbone_depth=2, c=1.0)
    x_d = th.linspace(-2.0, 2.0, 20).unsqueeze(1)
    # sech²(x)/2 is the analytic KdV soliton solution
    y_d = (1.0 / th.cosh(x_d.squeeze(1))) ** 2 * 0.5
    x_p = th.linspace(-2.0, 2.0, 30).unsqueeze(1)
    result = fit_pinn(m, x_d, y_d, x_p, steps=30, log_every=0)
    assert math.isfinite(result.data_loss)
    assert math.isfinite(result.physics_loss)


# ── All equations parametrized (updated list) ─────────────────────────────────

@pytest.mark.parametrize("equation", [
    "harmonic", "burgers", "heat",
    "schrodinger", "nls", "lotka_volterra",
])
def test_fit_pinn_all_supported_equations(equation):
    m = EMLPINN(equation=equation, backbone_depth=2)
    x_d = th.linspace(0, 1, 15).unsqueeze(1)
    y_d = x_d.squeeze(1) * 0.5
    x_p = th.linspace(0, 1, 20).unsqueeze(1)
    result = fit_pinn(m, x_d, y_d, x_p, steps=30, log_every=0)
    assert math.isfinite(result.data_loss)
    assert math.isfinite(result.physics_loss)


# ── Schrödinger: known analytic solution (CBEST identity) ────────────────────

def test_schrodinger_analytic_solution_is_1_cbest_node():
    """
    The free-particle Schrödinger solution u(x) = exp(ikx) = eml(ikx, 1)
    is exactly 1 complex EML node — a key theoretical result.
    Verify: −d²/dx² exp(ikx) = k²·exp(ikx).
    """
    import cmath
    k = 1.0

    def u(x_val: float) -> complex:
        return cmath.exp(1j * k * x_val)

    # Numerical second derivative at x=1
    h = 1e-5
    x0 = 1.0
    u_xx_num = (u(x0 + h) - 2 * u(x0) + u(x0 - h)) / h ** 2

    expected = -(k ** 2) * u(x0)   # −k²·exp(ikx)

    assert abs(u_xx_num.real - expected.real) < 1e-5
    assert abs(u_xx_num.imag - expected.imag) < 1e-5
