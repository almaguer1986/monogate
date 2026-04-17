"""Tests for monogate.information_geometry — Session 28."""

from __future__ import annotations

import math
import pytest
import numpy as np

from monogate.information_geometry import (
    log_partition_poisson,
    log_partition_bernoulli,
    log_partition_gaussian_1d,
    log_partition_exponential,
    fisher_metric_poisson,
    fisher_metric_bernoulli,
    fisher_metric_gaussian_1d,
    bregman_divergence,
    kl_divergence_poisson,
    kl_divergence_bernoulli,
    kl_divergence_exponential,
    geodesic_exponential_family,
    eml_information_geometry_summary,
)


# ── Log-partition functions ───────────────────────────────────────────────────

class TestLogPartitionPoisson:
    def test_zero(self):
        assert log_partition_poisson(0.0) == pytest.approx(1.0)

    def test_positive(self):
        assert log_partition_poisson(1.0) == pytest.approx(math.e)

    def test_negative(self):
        assert log_partition_poisson(-1.0) == pytest.approx(math.exp(-1.0))

    def test_is_exp(self):
        for eta in [-2.0, 0.5, 1.5]:
            assert log_partition_poisson(eta) == pytest.approx(math.exp(eta))


class TestLogPartitionBernoulli:
    def test_zero(self):
        assert log_partition_bernoulli(0.0) == pytest.approx(math.log(2))

    def test_large_positive_clipped(self):
        assert log_partition_bernoulli(200.0) == pytest.approx(200.0)

    def test_large_negative_clipped(self):
        assert log_partition_bernoulli(-200.0) == pytest.approx(0.0, abs=1e-10)

    def test_softplus_formula(self):
        for eta in [-1.0, 0.0, 1.0, 2.0]:
            expected = math.log1p(math.exp(eta)) if abs(eta) <= 100 else (eta if eta > 0 else 0.0)
            assert log_partition_bernoulli(eta) == pytest.approx(expected, rel=1e-9)

    def test_convex(self):
        # A(eta) is convex: A((a+b)/2) <= (A(a)+A(b))/2
        a, b = -1.0, 2.0
        mid = (a + b) / 2
        assert log_partition_bernoulli(mid) <= (log_partition_bernoulli(a) + log_partition_bernoulli(b)) / 2 + 1e-10


class TestLogPartitionGaussian:
    def test_invalid_eta1_positive(self):
        assert log_partition_gaussian_1d(0.1, 1.0) == float('inf')

    def test_invalid_eta1_zero(self):
        assert log_partition_gaussian_1d(0.0, 1.0) == float('inf')

    def test_standard_normal(self):
        # Standard normal: mu=0, sigma=1 → eta1=-0.5, eta2=0
        # A(eta1, eta2) = -0/(4*-0.5) - ln(1)/2 = 0
        val = log_partition_gaussian_1d(-0.5, 0.0)
        assert math.isfinite(val)

    def test_symmetric_in_eta2(self):
        # A(-1, eta2) = A(-1, -eta2) due to eta2^2
        v1 = log_partition_gaussian_1d(-1.0, 2.0)
        v2 = log_partition_gaussian_1d(-1.0, -2.0)
        assert v1 == pytest.approx(v2, rel=1e-9)


class TestLogPartitionExponential:
    def test_invalid_positive(self):
        assert log_partition_exponential(0.0) == float('inf')
        assert log_partition_exponential(1.0) == float('inf')

    def test_minus_one(self):
        # A(-1) = -ln(1) = 0
        assert log_partition_exponential(-1.0) == pytest.approx(0.0, abs=1e-12)

    def test_minus_e(self):
        # A(-e) = -ln(e) = -1
        assert log_partition_exponential(-math.e) == pytest.approx(-1.0, rel=1e-9)

    def test_formula(self):
        for eta in [-0.5, -1.0, -2.0, -5.0]:
            assert log_partition_exponential(eta) == pytest.approx(-math.log(-eta), rel=1e-9)


# ── Fisher metric ─────────────────────────────────────────────────────────────

class TestFisherMetricPoisson:
    def test_equals_log_partition(self):
        # A''(eta) = exp(eta) = A(eta) for Poisson
        for eta in [-1.0, 0.0, 1.0, 2.0]:
            assert fisher_metric_poisson(eta) == pytest.approx(log_partition_poisson(eta))

    def test_positive(self):
        for eta in [-2.0, 0.0, 2.0]:
            assert fisher_metric_poisson(eta) > 0


class TestFisherMetricBernoulli:
    def test_max_at_zero(self):
        # Fisher metric is maximized at eta=0 (p=0.5)
        g0 = fisher_metric_bernoulli(0.0)
        g1 = fisher_metric_bernoulli(1.0)
        assert g0 > g1

    def test_symmetric(self):
        # g(eta) = g(-eta)
        for eta in [0.5, 1.0, 2.0]:
            assert fisher_metric_bernoulli(eta) == pytest.approx(fisher_metric_bernoulli(-eta))

    def test_large_clipped(self):
        assert fisher_metric_bernoulli(200.0) == pytest.approx(0.0, abs=1e-5)
        assert fisher_metric_bernoulli(-200.0) == pytest.approx(0.0, abs=1e-5)

    def test_formula_p_times_one_minus_p(self):
        eta = 1.0
        sig = 1.0 / (1.0 + math.exp(-eta))
        expected = sig * (1.0 - sig)
        assert fisher_metric_bernoulli(eta) == pytest.approx(expected, rel=1e-9)


class TestFisherMetricGaussian:
    def test_invalid_eta1(self):
        with pytest.raises(ValueError):
            fisher_metric_gaussian_1d(0.0, 1.0)

    def test_shape(self):
        g = fisher_metric_gaussian_1d(-0.5, 0.0)
        assert g.shape == (2, 2)

    def test_symmetric_matrix(self):
        g = fisher_metric_gaussian_1d(-1.0, 1.0)
        assert g[0, 1] == pytest.approx(g[1, 0], rel=1e-9)

    def test_positive_definite(self):
        g = fisher_metric_gaussian_1d(-1.0, 0.5)
        eigenvalues = np.linalg.eigvalsh(g)
        assert all(ev > 0 for ev in eigenvalues)


# ── Bregman divergence ────────────────────────────────────────────────────────

class TestBregmanDivergence:
    def test_self_divergence_zero(self):
        # D_A(p||p) = 0
        import math
        result = bregman_divergence(math.exp, math.exp, 1.0, 1.0)
        assert result == pytest.approx(0.0, abs=1e-12)

    def test_asymmetric(self):
        # Bregman divergence is not symmetric in general
        d_pq = bregman_divergence(math.exp, math.exp, 1.0, 2.0)
        d_qp = bregman_divergence(math.exp, math.exp, 2.0, 1.0)
        assert d_pq != pytest.approx(d_qp, rel=1e-3)

    def test_nonnegative(self):
        # Bregman divergence of a convex function is nonneg
        for p, q in [(0.0, 1.0), (1.0, 2.0), (-1.0, 0.5)]:
            result = bregman_divergence(math.exp, math.exp, p, q)
            assert result >= -1e-10


# ── KL divergences ────────────────────────────────────────────────────────────

class TestKLDivergencePoisson:
    def test_self_zero(self):
        assert kl_divergence_poisson(1.0, 1.0) == pytest.approx(0.0, abs=1e-12)

    def test_nonnegative(self):
        for p, q in [(0.0, 1.0), (1.0, 0.0), (-1.0, 1.0)]:
            assert kl_divergence_poisson(p, q) >= -1e-10

    def test_known_value(self):
        # KL(Poi(mu=1)||Poi(mu=e)): eta_p=0 (mu=1), eta_q=1 (mu=e)
        # D_A(p||q) = A(q)-A(p)-(q-p)*A'(p) = e - 1 - (1-0)*1 = e - 2
        result = kl_divergence_poisson(0.0, 1.0)
        assert result == pytest.approx(math.e - 2.0, rel=1e-9)


class TestKLDivergenceBernoulli:
    def test_self_zero(self):
        assert kl_divergence_bernoulli(0.5, 0.5) == pytest.approx(0.0, abs=1e-10)

    def test_nonnegative(self):
        for p, q in [(0.0, 1.0), (1.0, -1.0), (-2.0, 2.0)]:
            assert kl_divergence_bernoulli(p, q) >= -1e-10

    def test_asymmetric(self):
        d1 = kl_divergence_bernoulli(0.0, 1.0)
        d2 = kl_divergence_bernoulli(1.0, 0.0)
        assert d1 != pytest.approx(d2, rel=1e-3)


class TestKLDivergenceExponential:
    def test_self_zero(self):
        assert kl_divergence_exponential(-1.0, -1.0) == pytest.approx(0.0, abs=1e-12)

    def test_nonnegative(self):
        for p, q in [(-1.0, -2.0), (-2.0, -0.5), (-0.5, -3.0)]:
            assert kl_divergence_exponential(p, q) >= -1e-10

    def test_known_formula(self):
        # KL(Exp(lam=1)||Exp(lam=2)): eta_p=-1, eta_q=-2
        # Direct integration: KL = ln(lam_p/lam_q) + lam_q/lam_p - 1
        #                        = ln(0.5) + 2 - 1 = 1 - ln2
        eta_p, eta_q = -1.0, -2.0
        result = kl_divergence_exponential(eta_p, eta_q)
        assert result == pytest.approx(1.0 - math.log(2), rel=1e-6)


# ── Geodesics ─────────────────────────────────────────────────────────────────

class TestGeodesicExponentialFamily:
    def test_returns_list(self):
        path = geodesic_exponential_family(0.0, 1.0, "poisson", n_steps=10)
        assert isinstance(path, list)
        assert len(path) > 0

    def test_starts_at_eta1(self):
        path = geodesic_exponential_family(0.0, 2.0, "poisson", n_steps=10)
        t0, a0 = path[0]
        assert t0 == pytest.approx(0.0, abs=1e-10)
        assert a0 == pytest.approx(log_partition_poisson(0.0), rel=1e-9)

    def test_ends_at_eta2(self):
        path = geodesic_exponential_family(0.0, 2.0, "poisson", n_steps=10)
        t1, a1 = path[-1]
        assert t1 == pytest.approx(1.0, abs=1e-10)
        assert a1 == pytest.approx(log_partition_poisson(2.0), rel=1e-9)

    def test_bernoulli_geodesic(self):
        path = geodesic_exponential_family(-1.0, 1.0, "bernoulli", n_steps=5)
        assert len(path) == 5

    def test_exponential_valid_range(self):
        # eta must be < 0 for exponential
        path = geodesic_exponential_family(-2.0, -0.5, "exponential", n_steps=10)
        assert len(path) > 0
        for _, a_val in path:
            assert math.isfinite(a_val)

    def test_n_steps_respected(self):
        path = geodesic_exponential_family(0.0, 1.0, "poisson", n_steps=20)
        assert len(path) == 20


# ── Summary ───────────────────────────────────────────────────────────────────

class TestSummary:
    def test_returns_string(self):
        s = eml_information_geometry_summary()
        assert isinstance(s, str)

    def test_contains_distributions(self):
        s = eml_information_geometry_summary()
        for dist in ("Poisson", "Bernoulli", "Gaussian", "Exponential"):
            assert dist in s

    def test_contains_theorem(self):
        s = eml_information_geometry_summary()
        assert "Bregman" in s or "KL" in s

    def test_contains_eml_references(self):
        s = eml_information_geometry_summary()
        assert "EML" in s
