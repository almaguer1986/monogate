"""
Tests for monogate.special — short CBEST/BEST expressions for special functions.

Covers:
- All callables return finite floats in their documented domains
- Exact constructions (sin_cb, cos_cb, sinh_cb, cosh_cb, tanh_cb, sech_cb) match math.*
- Fresnel integrand functions match the analytic formula
- fresnel_s_cb / fresnel_c_cb return finite values; S(0)=C(0)=0
- erf_cb is odd and bounded in [-1, 1]
- lgamma_cb matches math.lgamma within 1e-6 for x > 0.5
- digamma_cb matches finite differences of math.lgamma within 1e-3
- j0_cb and ai_cb return finite floats; J0(0)=1, Ai(0)≈0.3550
- CATALOG is populated with SpecialFnEntry objects for all expected keys
- catalog_summary() returns a non-empty string
- save_catalog() writes valid JSON
"""

import json
import math
import tempfile

import pytest

from monogate.special import (
    CATALOG,
    SpecialFnEntry,
    ai_cb,
    catalog_summary,
    cos_cb,
    cosh_cb,
    digamma_cb,
    erf_cb,
    fresnel_c_cb,
    fresnel_c_integrand_cb,
    fresnel_s_cb,
    fresnel_s_integrand_cb,
    j0_cb,
    lgamma_cb,
    save_catalog,
    sech_cb,
    sin_cb,
    sinh_cb,
    tanh_cb,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

_PROBE = [0.0, 0.1, 0.5, 1.0, 1.5, 2.0, math.pi / 4, math.pi / 3, math.pi / 2]
_PROBE_NONZERO = [0.1, 0.5, 1.0, 1.5, 2.0, math.pi / 4, math.pi / 3]


# ── Exact trig: sin_cb / cos_cb ───────────────────────────────────────────────

class TestSinCb:
    @pytest.mark.parametrize("x", _PROBE)
    def test_matches_math_sin(self, x: float):
        assert sin_cb(x) == pytest.approx(math.sin(x), abs=1e-13)

    @pytest.mark.parametrize("x", _PROBE)
    def test_negative_symmetry(self, x: float):
        assert sin_cb(-x) == pytest.approx(-sin_cb(x), abs=1e-13)

    def test_special_values(self):
        assert sin_cb(0.0) == pytest.approx(0.0, abs=1e-14)
        assert sin_cb(math.pi / 6) == pytest.approx(0.5, abs=1e-14)
        assert sin_cb(math.pi / 2) == pytest.approx(1.0, abs=1e-14)


class TestCosCb:
    @pytest.mark.parametrize("x", _PROBE)
    def test_matches_math_cos(self, x: float):
        assert cos_cb(x) == pytest.approx(math.cos(x), abs=1e-13)

    def test_special_values(self):
        assert cos_cb(0.0) == pytest.approx(1.0, abs=1e-14)
        assert cos_cb(math.pi / 3) == pytest.approx(0.5, abs=1e-14)
        assert cos_cb(math.pi / 2) == pytest.approx(0.0, abs=1e-13)


# ── Hyperbolic: sinh, cosh, tanh, sech ───────────────────────────────────────

class TestHyperbolicCb:
    @pytest.mark.parametrize("x", _PROBE)
    def test_sinh_matches_math(self, x: float):
        assert sinh_cb(x) == pytest.approx(math.sinh(x), abs=1e-12)

    @pytest.mark.parametrize("x", _PROBE)
    def test_cosh_matches_math(self, x: float):
        assert cosh_cb(x) == pytest.approx(math.cosh(x), abs=1e-12)

    @pytest.mark.parametrize("x", _PROBE)
    def test_tanh_matches_math(self, x: float):
        assert tanh_cb(x) == pytest.approx(math.tanh(x), abs=1e-12)

    @pytest.mark.parametrize("x", _PROBE_NONZERO)
    def test_sech_is_recip_cosh(self, x: float):
        assert sech_cb(x) == pytest.approx(1.0 / math.cosh(x), abs=1e-12)

    def test_cosh_sinh_identity(self):
        """cosh²(x) - sinh²(x) == 1."""
        for x in [0.5, 1.0, 2.0]:
            assert cosh_cb(x) ** 2 - sinh_cb(x) ** 2 == pytest.approx(1.0, abs=1e-10)

    def test_tanh_large_positive(self):
        assert tanh_cb(50.0) == pytest.approx(1.0, abs=1e-10)

    def test_tanh_large_negative(self):
        assert tanh_cb(-50.0) == pytest.approx(-1.0, abs=1e-10)


# ── Fresnel integrand ─────────────────────────────────────────────────────────

class TestFresnelIntegrand:
    @pytest.mark.parametrize("x", _PROBE)
    def test_s_integrand_matches_sin(self, x: float):
        expected = math.sin(math.pi * x * x / 2.0)
        assert fresnel_s_integrand_cb(x) == pytest.approx(expected, abs=1e-13)

    @pytest.mark.parametrize("x", _PROBE)
    def test_c_integrand_matches_cos(self, x: float):
        expected = math.cos(math.pi * x * x / 2.0)
        assert fresnel_c_integrand_cb(x) == pytest.approx(expected, abs=1e-13)

    def test_s_integrand_at_zero(self):
        assert fresnel_s_integrand_cb(0.0) == pytest.approx(0.0, abs=1e-14)

    def test_c_integrand_at_zero(self):
        assert fresnel_c_integrand_cb(0.0) == pytest.approx(1.0, abs=1e-14)


# ── Fresnel integrals ─────────────────────────────────────────────────────────

class TestFresnelIntegral:
    def test_fresnel_s_at_zero(self):
        assert fresnel_s_cb(0.0) == pytest.approx(0.0, abs=1e-10)

    def test_fresnel_c_at_zero(self):
        assert fresnel_c_cb(0.0) == pytest.approx(0.0, abs=1e-10)

    def test_fresnel_s_finite(self):
        for x in [0.5, 1.0, 2.0, 3.0]:
            val = fresnel_s_cb(x)
            assert math.isfinite(val)
            assert -1.0 < val < 1.0  # Fresnel integrals are bounded

    def test_fresnel_c_finite(self):
        for x in [0.5, 1.0, 2.0, 3.0]:
            val = fresnel_c_cb(x)
            assert math.isfinite(val)

    def test_fresnel_s_known_value(self):
        # S(1) ≈ 0.43826 (from scipy / standard tables)
        val = fresnel_s_cb(1.0)
        assert val == pytest.approx(0.43826, abs=2e-4)

    def test_fresnel_c_known_value(self):
        # C(1) = ∫₀¹ cos(πt²/2) dt ≈ 0.7799 (pi*t^2/2 convention)
        val = fresnel_c_cb(1.0)
        assert val == pytest.approx(0.7799, abs=2e-4)

    def test_fresnel_s_odd(self):
        # S(-x) = -S(x)
        assert fresnel_s_cb(-1.0) == pytest.approx(-fresnel_s_cb(1.0), abs=1e-8)


# ── erf_cb ────────────────────────────────────────────────────────────────────

class TestErfCb:
    def test_erf_at_zero(self):
        assert erf_cb(0.0) == pytest.approx(0.0, abs=1e-14)

    def test_erf_odd(self):
        for x in [0.5, 1.0, 2.0]:
            assert erf_cb(-x) == pytest.approx(-erf_cb(x), abs=1e-14)

    def test_erf_bounded(self):
        for x in [-3.0, -1.0, 0.0, 1.0, 3.0]:
            assert -1.0 <= erf_cb(x) <= 1.0

    def test_erf_monotone(self):
        vals = [erf_cb(x) for x in [-2.0, -1.0, 0.0, 1.0, 2.0]]
        assert all(vals[i] < vals[i + 1] for i in range(len(vals) - 1))

    def test_erf_within_tolerance(self):
        # Within ±2e-2 of math.erf
        for x in [0.0, 0.5, 1.0, 2.0]:
            assert abs(erf_cb(x) - math.erf(x)) < 2e-2


# ── lgamma_cb ─────────────────────────────────────────────────────────────────

class TestLgammaCb:
    @pytest.mark.parametrize("x", [0.5, 1.0, 2.0, 5.0, 10.0, 50.0])
    def test_matches_math_lgamma(self, x: float):
        assert lgamma_cb(x) == pytest.approx(math.lgamma(x), abs=1e-6)

    def test_lgamma_at_one(self):
        # Γ(1) = 1, ln(1) = 0; Stirling series with recurrence gives ~1e-8 error
        assert lgamma_cb(1.0) == pytest.approx(0.0, abs=1e-6)

    def test_lgamma_at_two(self):
        # Γ(2) = 1, ln(1) = 0; Stirling series with recurrence gives ~1e-8 error
        assert lgamma_cb(2.0) == pytest.approx(0.0, abs=1e-6)

    def test_lgamma_raises_for_nonpositive(self):
        with pytest.raises(ValueError):
            lgamma_cb(0.0)
        with pytest.raises(ValueError):
            lgamma_cb(-1.0)


# ── digamma_cb ────────────────────────────────────────────────────────────────

class TestDigammaCb:
    def test_digamma_at_one(self):
        # ψ(1) = -γ ≈ -0.5772156649; central-diff h=1e-5 gives O(h²) error ~1e-3
        assert digamma_cb(1.0) == pytest.approx(-0.5772156649, abs=2e-3)

    def test_digamma_positive_for_large_x(self):
        # ψ(x) > 0 for x > 1.46
        assert digamma_cb(2.0) > 0.0
        assert digamma_cb(10.0) > 0.0

    def test_digamma_finite(self):
        for x in [0.5, 1.0, 2.0, 5.0, 10.0]:
            assert math.isfinite(digamma_cb(x))


# ── j0_cb ─────────────────────────────────────────────────────────────────────

class TestJ0Cb:
    def test_j0_at_zero(self):
        assert j0_cb(0.0) == pytest.approx(1.0, abs=1e-10)

    def test_j0_positive_small(self):
        # J0 starts at 1, first zero near x=2.4048
        assert j0_cb(1.0) > 0.0
        assert j0_cb(2.0) > 0.0

    def test_j0_finite(self):
        for x in [0.0, 1.0, 3.0, 5.0, 10.0]:
            assert math.isfinite(j0_cb(x))

    def test_j0_bounded(self):
        # |J0(x)| ≤ 1 for all x
        for x in [0.0, 1.0, 3.0, 5.0, 8.0]:
            assert abs(j0_cb(x)) <= 1.0 + 1e-10


# ── ai_cb ─────────────────────────────────────────────────────────────────────

class TestAiCb:
    def test_ai_at_zero(self):
        # Ai(0) = 3^(-2/3) / Γ(2/3) ≈ 0.3550280539
        assert ai_cb(0.0) == pytest.approx(0.3550280539, abs=1e-4)

    def test_ai_positive_large_x(self):
        # Ai decays to 0 for large positive x
        assert 0.0 < ai_cb(5.0) < 0.1

    def test_ai_finite(self):
        for x in [-5.0, -2.0, 0.0, 2.0, 5.0]:
            assert math.isfinite(ai_cb(x))


# ── CATALOG ───────────────────────────────────────────────────────────────────

class TestCatalog:
    _EXPECTED_KEYS = {
        "sin", "cos", "sinh", "cosh", "tanh", "sech",
        "erf", "fresnel_s_integrand", "fresnel_c_integrand",
        "fresnel_s", "fresnel_c",
        "j0", "airy_ai", "lgamma", "digamma",
    }

    def test_catalog_has_expected_keys(self):
        for key in self._EXPECTED_KEYS:
            assert key in CATALOG, f"Missing catalog entry: {key!r}"

    def test_catalog_entries_are_special_fn_entry(self):
        for key, entry in CATALOG.items():
            assert isinstance(entry, SpecialFnEntry), f"{key} not a SpecialFnEntry"

    def test_catalog_n_nodes_positive(self):
        for key, entry in CATALOG.items():
            assert entry.n_nodes >= 1, f"{key}: n_nodes must be >= 1"

    def test_catalog_max_abs_error_nonnegative(self):
        for key, entry in CATALOG.items():
            assert entry.max_abs_error >= 0.0

    def test_catalog_backend_valid(self):
        for key, entry in CATALOG.items():
            assert entry.backend in ("CBEST", "BEST"), f"{key}: unknown backend"

    def test_sin_node_count_is_one(self):
        assert CATALOG["sin"].n_nodes == 1

    def test_cos_node_count_is_one(self):
        assert CATALOG["cos"].n_nodes == 1


# ── Utilities ─────────────────────────────────────────────────────────────────

def test_catalog_summary_nonempty():
    s = catalog_summary()
    assert isinstance(s, str)
    assert len(s) > 50
    assert "sin" in s
    assert "CBEST" in s


def test_save_catalog_valid_json():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as fh:
        path = fh.name
    save_catalog(path)
    with open(path) as fh:
        data = json.load(fh)
    assert "sin" in data
    assert "n_nodes" in data["sin"]
    assert data["sin"]["n_nodes"] == 1
