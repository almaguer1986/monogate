"""Tests for monogate.physics — compact EML constructions for PDEs/ODEs."""

from __future__ import annotations

import math
import cmath
import pytest

from monogate.physics import (
    schrodinger_free_cb,
    potential_well_cb,
    nls_soliton_amplitude_cb,
    heat_kernel_cb,
    kdv_soliton_cb,
    wave_cos_cb,
    wave_sin_cb,
    PHYSICS_CATALOG,
)


# ── Schrödinger free particle ─────────────────────────────────────────────────

def test_schrodinger_free_complex():
    """schrodinger_free_cb with part='complex' returns exp(ikx)."""
    for x in [0.0, 0.5, 1.0, math.pi]:
        result = schrodinger_free_cb(x, k=1.0, part="complex")
        expected = cmath.exp(1j * x)
        assert abs(result - expected) < 1e-14


def test_schrodinger_free_re():
    """Real part = cos(kx)."""
    for x in [0.0, 0.5, 1.0, 2.0]:
        assert schrodinger_free_cb(x, k=2.0, part="re") == pytest.approx(
            math.cos(2.0 * x), abs=1e-14
        )


def test_schrodinger_free_im():
    """Imaginary part = sin(kx)."""
    for x in [0.0, 0.5, 1.0, 2.0]:
        assert schrodinger_free_cb(x, k=1.0, part="im") == pytest.approx(
            math.sin(x), abs=1e-14
        )


def test_schrodinger_free_zero_k():
    """k=0 → constant 1 (exp(0))."""
    result = schrodinger_free_cb(5.0, k=0.0, part="complex")
    assert abs(result - 1.0) < 1e-14


def test_schrodinger_obeys_equation():
    """Verify -d²/dx² exp(ikx) = k² exp(ikx) numerically."""
    # Use h=1e-4 to avoid catastrophic cancellation in complex finite differences
    k, x, h = 2.0, 1.0, 1e-4
    u_x   = schrodinger_free_cb(x, k=k)
    u_xph = schrodinger_free_cb(x + h, k=k)
    u_xmh = schrodinger_free_cb(x - h, k=k)
    d2u   = (u_xph - 2 * u_x + u_xmh) / h**2
    # Tolerance 1e-3: finite differences have O(h²) = 1e-8 truncation error
    # plus floating-point cancellation; 1e-3 is conservative but reliable
    assert abs(-d2u - k**2 * u_x) < 1e-3


# ── Potential well ────────────────────────────────────────────────────────────

def test_potential_well_boundary_conditions():
    """Eigenfunction must vanish at x=0 and x=L."""
    for n in [1, 2, 3]:
        assert potential_well_cb(0.0, n=n, L=1.0) == pytest.approx(0.0, abs=1e-14)
        assert potential_well_cb(1.0, n=n, L=1.0) == pytest.approx(0.0, abs=1e-14)


def test_potential_well_values():
    """Spot-check: sin(nπx/L)."""
    assert potential_well_cb(0.5, n=1, L=1.0) == pytest.approx(1.0, abs=1e-14)
    assert potential_well_cb(0.5, n=2, L=1.0) == pytest.approx(0.0, abs=1e-14)


def test_potential_well_n2_nodes():
    """Higher quantum numbers produce more oscillations."""
    # n=2 has a node at x=0.5
    assert abs(potential_well_cb(0.5, n=2, L=1.0)) < 1e-14


# ── NLS soliton amplitude ─────────────────────────────────────────────────────

def test_nls_soliton_amplitude_at_zero():
    """sech(0) = 1."""
    assert nls_soliton_amplitude_cb(0.0) == pytest.approx(1.0, abs=1e-14)


def test_nls_soliton_amplitude_even():
    """sech is an even function."""
    for x in [0.5, 1.0, 2.0]:
        assert nls_soliton_amplitude_cb(x) == pytest.approx(
            nls_soliton_amplitude_cb(-x), abs=1e-14
        )


def test_nls_soliton_amplitude_positive():
    """sech is always positive."""
    for x in [-3.0, -1.0, 0.0, 1.0, 3.0]:
        assert nls_soliton_amplitude_cb(x) > 0.0


def test_nls_soliton_amplitude_decay():
    """sech(x) → 0 as |x| → ∞."""
    assert nls_soliton_amplitude_cb(10.0) < 1e-4


# ── Heat kernel ───────────────────────────────────────────────────────────────

def test_heat_kernel_at_origin():
    """At x=0, heat_kernel = 1/sqrt(4πt)."""
    t = 0.5
    expected = 1.0 / math.sqrt(4 * math.pi * t)
    assert heat_kernel_cb(0.0, t=t) == pytest.approx(expected, rel=1e-12)


def test_heat_kernel_normalizes_to_one():
    """Integral of heat kernel over R ≈ 1 (checked via Riemann sum)."""
    t = 1.0
    xs = [-10.0 + 0.1 * i for i in range(201)]
    integral = sum(heat_kernel_cb(x, t=t) * 0.1 for x in xs)
    assert abs(integral - 1.0) < 0.01


def test_heat_kernel_invalid_t():
    """Raises ValueError for t ≤ 0."""
    with pytest.raises(ValueError):
        heat_kernel_cb(0.0, t=0.0)
    with pytest.raises(ValueError):
        heat_kernel_cb(0.0, t=-1.0)


def test_heat_kernel_symmetric():
    """Heat kernel is symmetric in x."""
    for x in [0.5, 1.0, 2.0]:
        assert heat_kernel_cb(x) == pytest.approx(heat_kernel_cb(-x), rel=1e-12)


# ── KdV soliton ───────────────────────────────────────────────────────────────

def test_kdv_soliton_at_center():
    """Peak of KdV soliton is at x=ct, amplitude c/2."""
    c = 4.0
    peak = kdv_soliton_cb(0.0, t=0.0, c=c)
    assert peak == pytest.approx(c / 2.0, rel=1e-12)


def test_kdv_soliton_positive():
    """KdV soliton is always positive."""
    for x in [-5.0, -1.0, 0.0, 1.0, 5.0]:
        assert kdv_soliton_cb(x, t=0.0, c=4.0) > 0.0


def test_kdv_soliton_traveling():
    """KdV soliton center moves at speed c."""
    c = 2.0
    # At t=0 peak is at x=0; at t=1 peak is at x=c
    peak_t0 = kdv_soliton_cb(0.0, t=0.0, c=c)
    peak_t1 = kdv_soliton_cb(c * 1.0, t=1.0, c=c)
    assert peak_t0 == pytest.approx(peak_t1, rel=1e-12)


# ── Wave equation ─────────────────────────────────────────────────────────────

def test_wave_cos_identity():
    """wave_cos_cb at t=0 = cos(kx)."""
    k = 2.0
    for x in [0.0, 0.5, 1.0, math.pi]:
        assert wave_cos_cb(x, k=k, t=0.0) == pytest.approx(math.cos(k * x), abs=1e-14)


def test_wave_sin_identity():
    """wave_sin_cb at t=0 = sin(kx)."""
    k = 1.5
    for x in [0.0, 0.5, 1.0, math.pi]:
        assert wave_sin_cb(x, k=k, t=0.0) == pytest.approx(math.sin(k * x), abs=1e-14)


def test_wave_cos_traveling():
    """cos(kx - ωt) travels with phase velocity ω/k."""
    k, omega = 2.0, 3.0
    for x in [0.0, 1.0, 2.0]:
        for t in [0.0, 0.5, 1.0]:
            assert wave_cos_cb(x, k=k, omega=omega, t=t) == pytest.approx(
                math.cos(k * x - omega * t), abs=1e-14
            )


# ── PHYSICS_CATALOG ───────────────────────────────────────────────────────────

def test_catalog_is_dict():
    """PHYSICS_CATALOG is a dict."""
    assert isinstance(PHYSICS_CATALOG, dict)


def test_catalog_nonempty():
    """PHYSICS_CATALOG has at least 5 entries."""
    assert len(PHYSICS_CATALOG) >= 5


def test_catalog_entry_has_required_keys():
    """Each catalog entry has the required keys."""
    required = {"equation", "callable", "formula", "n_nodes", "backend",
                "max_abs_error", "notes"}
    for name, entry in PHYSICS_CATALOG.items():
        for key in required:
            assert key in entry, f"Entry {name!r} missing key {key!r}"


def test_catalog_n_nodes_positive():
    """All n_nodes values are positive integers."""
    for name, entry in PHYSICS_CATALOG.items():
        assert isinstance(entry["n_nodes"], int), f"{name}: n_nodes not int"
        assert entry["n_nodes"] >= 1, f"{name}: n_nodes < 1"


def test_catalog_max_abs_error_nonnegative():
    """max_abs_error is non-negative."""
    for name, entry in PHYSICS_CATALOG.items():
        assert entry["max_abs_error"] >= 0.0, f"{name}: max_abs_error < 0"
