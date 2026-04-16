"""
tests/test_prover.py — Test suite for monogate.prover and monogate.identities.

Covers:
- ProofResult dataclass creation and fields
- EMLProver construction
- prove() on trivial and easy identities
- prove() on trig identities
- prove_batch() behaviour
- benchmark() returns BenchmarkReport
- Identity dataclass validation
- Catalog sizes and categories
- prove() graceful failure on false identities
- All proof modes: exact, numerical, certified
- BenchmarkReport summary/to_json
- Integration with sympy_bridge
"""

from __future__ import annotations

import math
import pytest

# ── Module imports ────────────────────────────────────────────────────────────

from monogate.prover import EMLProver, ProofResult, BenchmarkReport
from monogate.identities import (
    Identity,
    TRIG_IDENTITIES,
    HYPERBOLIC_IDENTITIES,
    EXPONENTIAL_IDENTITIES,
    SPECIAL_IDENTITIES,
    PHYSICS_IDENTITIES,
    EML_IDENTITIES,
    OPEN_IDENTITIES,
    ALL_IDENTITIES,
    get_by_difficulty,
    get_by_category,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def prover():
    """A shared EMLProver instance for fast tests (no verbose output)."""
    return EMLProver(verbose=False, n_probe=100)


@pytest.fixture(scope="module")
def verbose_prover():
    """A verbose EMLProver for diagnostic tests."""
    return EMLProver(verbose=True, n_probe=50)


# ── ProofResult dataclass tests ───────────────────────────────────────────────

class TestProofResult:
    def test_creation_minimal(self):
        r = ProofResult(
            identity_str="exp(x)*exp(-x) == 1",
            status="proved_exact",
            verification_method="sympy",
            confidence=1.0,
            max_residual=0.0,
            n_test_points=100,
            elapsed_s=0.1,
            lhs_tree=None,
            rhs_tree=None,
            witness_tree=None,
            node_count=0,
            lhs_formula=None,
            latex_proof=None,
            sympy_simplification="0",
            notes=["Proved exactly"],
        )
        assert r.status == "proved_exact"
        assert r.confidence == 1.0
        assert r.proved() is True

    def test_creation_failed(self):
        r = ProofResult(
            identity_str="sin(x) == 2",
            status="failed",
            verification_method="numerical",
            confidence=0.0,
            max_residual=1.5,
            n_test_points=50,
            elapsed_s=0.05,
            lhs_tree=None,
            rhs_tree=None,
            witness_tree=None,
            node_count=0,
            lhs_formula=None,
            latex_proof=None,
            sympy_simplification=None,
            notes=["Max residual > threshold"],
        )
        assert r.proved() is False
        assert r.status == "failed"

    def test_proved_method_statuses(self):
        for status in ("proved_exact", "proved_numerical", "proved_certified", "proved_witness"):
            r = ProofResult(
                identity_str="x == x",
                status=status,
                verification_method="sympy",
                confidence=1.0,
                max_residual=0.0,
                n_test_points=0,
                elapsed_s=0.0,
                lhs_tree=None, rhs_tree=None, witness_tree=None,
                node_count=0, lhs_formula=None, latex_proof=None,
                sympy_simplification=None, notes=[],
            )
            assert r.proved() is True

    def test_inconclusive_not_proved(self):
        r = ProofResult(
            identity_str="sin(x) == approx",
            status="inconclusive",
            verification_method="numerical",
            confidence=0.5,
            max_residual=1e-5,
            n_test_points=100,
            elapsed_s=0.1,
            lhs_tree=None, rhs_tree=None, witness_tree=None,
            node_count=0, lhs_formula=None, latex_proof=None,
            sympy_simplification=None, notes=["Small but inconclusive residual"],
        )
        assert r.proved() is False

    def test_str_representation(self):
        r = ProofResult(
            identity_str="x == x",
            status="proved_exact",
            verification_method="sympy",
            confidence=1.0,
            max_residual=0.0,
            n_test_points=100,
            elapsed_s=0.05,
            lhs_tree=None, rhs_tree=None, witness_tree=None,
            node_count=0, lhs_formula=None, latex_proof=None,
            sympy_simplification="0", notes=[],
        )
        s = str(r)
        assert "proved_exact" in s
        assert "x == x" in s

    def test_frozen_immutability(self):
        r = ProofResult(
            identity_str="x == x",
            status="proved_exact",
            verification_method="sympy",
            confidence=1.0,
            max_residual=0.0,
            n_test_points=0,
            elapsed_s=0.0,
            lhs_tree=None, rhs_tree=None, witness_tree=None,
            node_count=0, lhs_formula=None, latex_proof=None,
            sympy_simplification=None, notes=[],
        )
        with pytest.raises((AttributeError, TypeError)):
            r.status = "failed"  # type: ignore[misc]

    def test_notes_is_list(self):
        r = ProofResult(
            identity_str="a == b",
            status="failed",
            verification_method="none",
            confidence=0.0,
            max_residual=float("inf"),
            n_test_points=0,
            elapsed_s=0.0,
            lhs_tree=None, rhs_tree=None, witness_tree=None,
            node_count=0, lhs_formula=None, latex_proof=None,
            sympy_simplification=None, notes=["step1", "step2"],
        )
        assert isinstance(r.notes, list)
        assert len(r.notes) == 2


# ── EMLProver construction tests ──────────────────────────────────────────────

class TestEMLProverConstruction:
    def test_default_construction(self):
        p = EMLProver()
        assert p.n_probe == 500
        assert p.verbose is False

    def test_custom_params(self):
        p = EMLProver(verbose=True, n_probe=100)
        assert p.n_probe == 100
        assert p.verbose is True

    def test_prover_has_prove_method(self):
        p = EMLProver()
        assert callable(p.prove)

    def test_prover_has_prove_batch_method(self):
        p = EMLProver()
        assert callable(p.prove_batch)

    def test_prover_has_benchmark_method(self):
        p = EMLProver()
        assert callable(p.benchmark)


# ── prove() on trivial / easy identities ─────────────────────────────────────

class TestProveSimple:
    def test_exp_exp_neg(self, prover):
        r = prover.prove("exp(x) * exp(-x) == 1", domain=(-2.0, 2.0))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_log_exp_roundtrip(self, prover):
        r = prover.prove("log(exp(x)) == x", domain=(-2.0, 2.0))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_exp_log_roundtrip(self, prover):
        r = prover.prove("exp(log(x)) == x", domain=(0.1, 3.0))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_exp_zero(self, prover):
        r = prover.prove("exp(0) == 1", domain=(0.0, 0.0))
        # Constant identity — may be exact or numerical
        assert r.proved() or r.status == "inconclusive", f"Status: {r.status}, notes: {r.notes}"

    def test_cosh_plus_sinh(self, prover):
        r = prover.prove("cosh(x) + sinh(x) == exp(x)", domain=(-2.0, 2.0))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_cosh_minus_sinh(self, prover):
        r = prover.prove("cosh(x) - sinh(x) == exp(-x)", domain=(-2.0, 2.0))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"


# ── prove() on trig identities ────────────────────────────────────────────────

class TestProveTrig:
    def test_pythagorean(self, prover):
        r = prover.prove("sin(x)**2 + cos(x)**2 == 1", domain=(-math.pi, math.pi))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_double_angle_sin(self, prover):
        r = prover.prove("sin(2*x) == 2*sin(x)*cos(x)", domain=(-math.pi, math.pi))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_double_angle_cos(self, prover):
        r = prover.prove("cos(2*x) == cos(x)**2 - sin(x)**2", domain=(-math.pi, math.pi))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_cos_negation(self, prover):
        r = prover.prove("cos(-x) == cos(x)", domain=(-math.pi, math.pi))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_sin_negation(self, prover):
        r = prover.prove("sin(-x) == -sin(x)", domain=(-math.pi, math.pi))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_max_residual_is_finite(self, prover):
        r = prover.prove("sin(x)**2 + cos(x)**2 == 1", domain=(-math.pi, math.pi))
        assert math.isfinite(r.max_residual)

    def test_n_test_points_positive(self, prover):
        r = prover.prove("sin(x)**2 + cos(x)**2 == 1", domain=(-math.pi, math.pi))
        assert r.n_test_points > 0


# ── prove() on hyperbolic identities ─────────────────────────────────────────

class TestProveHyperbolic:
    def test_hyperbolic_pythagorean(self, prover):
        r = prover.prove("cosh(x)**2 - sinh(x)**2 == 1", domain=(-2.0, 2.0))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_tanh_definition(self, prover):
        r = prover.prove("tanh(x) == sinh(x)/cosh(x)", domain=(-2.0, 2.0))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_sinh_double_angle(self, prover):
        r = prover.prove("sinh(2*x) == 2*sinh(x)*cosh(x)", domain=(-2.0, 2.0))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"


# ── prove() graceful failure on false identities ──────────────────────────────

class TestProveFalse:
    def test_false_identity_sin_eq_2(self, prover):
        r = prover.prove("sin(x) == 2", domain=(-math.pi, math.pi))
        assert not r.proved()
        assert r.status in ("failed", "inconclusive")

    def test_false_constant_identity(self, prover):
        r = prover.prove("exp(x) == exp(x) + 1", domain=(-1.0, 1.0))
        assert not r.proved()

    def test_malformed_identity_no_equals(self, prover):
        r = prover.prove("sin(x) + cos(x)")
        assert r.status == "failed"
        assert any("==" in note or "parse" in note.lower() for note in r.notes)

    def test_false_trig_identity(self, prover):
        r = prover.prove("sin(x) == cos(x)", domain=(-math.pi, math.pi))
        assert not r.proved()


# ── prove() timeout handling ──────────────────────────────────────────────────

class TestProveTimeout:
    def test_short_timeout_returns_result(self, prover):
        # Should return a result even with a very short timeout
        r = prover.prove(
            "sin(x)**2 + cos(x)**2 == 1",
            timeout=0.01,
            n_simulations=10,
            domain=(-math.pi, math.pi),
        )
        assert isinstance(r, ProofResult)
        # With 10ms timeout, might or might not prove — just check no crash
        assert r.status in (
            "proved_exact", "proved_numerical", "proved_certified",
            "proved_witness", "inconclusive", "failed"
        )

    def test_elapsed_time_recorded(self, prover):
        r = prover.prove("exp(x)*exp(-x) == 1", domain=(-1.0, 1.0))
        assert r.elapsed_s >= 0.0
        assert math.isfinite(r.elapsed_s)


# ── prove_batch() tests ───────────────────────────────────────────────────────

class TestProveBatch:
    def test_batch_returns_list(self, prover):
        idents = [
            "exp(x) * exp(-x) == 1",
            "log(exp(x)) == x",
        ]
        results = prover.prove_batch(idents, domain=(-1.0, 1.0))
        assert isinstance(results, list)
        assert len(results) == 2

    def test_batch_all_proof_results(self, prover):
        idents = [
            "exp(x) * exp(-x) == 1",
            "cosh(x)**2 - sinh(x)**2 == 1",
        ]
        results = prover.prove_batch(idents, domain=(-1.0, 1.0))
        assert all(isinstance(r, ProofResult) for r in results)

    def test_batch_empty_list(self, prover):
        results = prover.prove_batch([])
        assert results == []

    def test_batch_single_identity(self, prover):
        results = prover.prove_batch(["exp(x)*exp(-x) == 1"], domain=(-1.0, 1.0))
        assert len(results) == 1
        assert results[0].proved()

    def test_batch_order_preserved(self, prover):
        idents = [
            "exp(x)*exp(-x) == 1",
            "sin(x) == 2",
        ]
        results = prover.prove_batch(idents, domain=(-1.0, 1.0))
        assert results[0].proved()
        assert not results[1].proved()


# ── benchmark() tests ─────────────────────────────────────────────────────────

class TestBenchmark:
    def test_benchmark_returns_report(self, prover):
        report = prover.benchmark(
            catalog=["exp(x)*exp(-x) == 1", "log(exp(x)) == x"],
            n_simulations=100,
            timeout=5.0,
        )
        assert isinstance(report, BenchmarkReport)

    def test_benchmark_report_fields(self, prover):
        report = prover.benchmark(
            catalog=["exp(x)*exp(-x) == 1"],
            n_simulations=100,
            timeout=5.0,
        )
        assert report.n_total == 1
        assert report.n_proved <= report.n_total
        assert report.n_failed == report.n_total - report.n_proved
        assert 0.0 <= report.success_rate <= 1.0
        assert report.mean_elapsed_s >= 0.0

    def test_benchmark_summary_string(self, prover):
        report = prover.benchmark(
            catalog=["exp(x)*exp(-x) == 1"],
            n_simulations=100,
            timeout=5.0,
        )
        summary = report.summary()
        assert isinstance(summary, str)
        assert "Proved" in summary or "proved" in summary.lower()

    def test_benchmark_to_json(self, prover):
        report = prover.benchmark(
            catalog=["exp(x)*exp(-x) == 1"],
            n_simulations=100,
            timeout=5.0,
        )
        data = report.to_json()
        assert isinstance(data, dict)
        assert "n_total" in data
        assert "n_proved" in data
        assert "success_rate" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_benchmark_with_identity_objects(self, prover):
        catalog = [i for i in ALL_IDENTITIES if i.difficulty == "trivial"][:5]
        report = prover.benchmark(
            catalog=catalog,
            n_simulations=50,
            timeout=5.0,
        )
        assert report.n_total == len(catalog)

    def test_benchmark_default_catalog(self, prover):
        # Default catalog uses trivial/easy identities
        report = prover.benchmark(n_simulations=50, timeout=5.0)
        assert report.n_total > 0
        assert isinstance(report, BenchmarkReport)


# ── Identity dataclass tests ──────────────────────────────────────────────────

class TestIdentityDataclass:
    def test_creation(self):
        ident = Identity(
            name="Test",
            expression="sin(x)**2 + cos(x)**2 == 1",
            latex=r"\sin^2(x) + \cos^2(x) = 1",
            category="trigonometric",
            domain=(-math.pi, math.pi),
            difficulty="easy",
        )
        assert ident.name == "Test"
        assert ident.category == "trigonometric"
        assert ident.difficulty == "easy"

    def test_default_fields(self):
        ident = Identity(
            name="X",
            expression="x == x",
            latex=r"x = x",
            category="eml",
            domain=(-1.0, 1.0),
            difficulty="trivial",
        )
        assert ident.notes == ""
        assert ident.expected_method == "exact"

    def test_frozen_immutability(self):
        ident = Identity(
            name="X",
            expression="x == x",
            latex=r"x = x",
            category="eml",
            domain=(-1.0, 1.0),
            difficulty="trivial",
        )
        with pytest.raises((AttributeError, TypeError)):
            ident.name = "Y"  # type: ignore[misc]

    def test_domain_is_tuple(self):
        ident = Identity(
            name="X",
            expression="x == x",
            latex=r"x = x",
            category="eml",
            domain=(-1.0, 1.0),
            difficulty="trivial",
        )
        assert isinstance(ident.domain, tuple)
        assert len(ident.domain) == 2


# ── Catalog size and category tests ──────────────────────────────────────────

class TestCatalogs:
    def test_trig_catalog_size(self):
        assert len(TRIG_IDENTITIES) >= 15

    def test_hyperbolic_catalog_size(self):
        assert len(HYPERBOLIC_IDENTITIES) >= 10

    def test_exponential_catalog_size(self):
        assert len(EXPONENTIAL_IDENTITIES) >= 10

    def test_special_catalog_size(self):
        assert len(SPECIAL_IDENTITIES) >= 10

    def test_physics_catalog_size(self):
        assert len(PHYSICS_IDENTITIES) >= 5

    def test_eml_catalog_size(self):
        assert len(EML_IDENTITIES) >= 5

    def test_open_catalog_size(self):
        assert len(OPEN_IDENTITIES) >= 5

    def test_all_identities_size(self):
        assert len(ALL_IDENTITIES) >= 50

    def test_all_identities_union(self):
        expected = (
            len(TRIG_IDENTITIES)
            + len(HYPERBOLIC_IDENTITIES)
            + len(EXPONENTIAL_IDENTITIES)
            + len(SPECIAL_IDENTITIES)
            + len(PHYSICS_IDENTITIES)
            + len(EML_IDENTITIES)
            + len(OPEN_IDENTITIES)
        )
        assert len(ALL_IDENTITIES) == expected

    def test_all_have_expressions(self):
        for ident in ALL_IDENTITIES:
            assert isinstance(ident.expression, str)
            assert len(ident.expression) > 0

    def test_all_have_domains(self):
        for ident in ALL_IDENTITIES:
            lo, hi = ident.domain
            assert lo <= hi

    def test_all_have_valid_categories(self):
        valid = {"trigonometric", "hyperbolic", "exponential", "special", "physics", "eml", "open"}
        for ident in ALL_IDENTITIES:
            assert ident.category in valid, f"{ident.name}: unknown category {ident.category}"

    def test_all_have_valid_difficulties(self):
        valid = {"trivial", "easy", "medium", "hard", "open"}
        for ident in ALL_IDENTITIES:
            assert ident.difficulty in valid, f"{ident.name}: unknown difficulty {ident.difficulty}"


# ── get_by_difficulty / get_by_category tests ─────────────────────────────────

class TestQueryFunctions:
    def test_get_by_difficulty_trivial(self):
        trivials = get_by_difficulty("trivial")
        assert len(trivials) > 0
        assert all(i.difficulty == "trivial" for i in trivials)

    def test_get_by_difficulty_easy(self):
        easy = get_by_difficulty("easy")
        assert len(easy) > 0
        assert all(i.difficulty == "easy" for i in easy)

    def test_get_by_difficulty_unknown(self):
        result = get_by_difficulty("nonexistent")
        assert result == []

    def test_get_by_category_trig(self):
        trigs = get_by_category("trigonometric")
        assert len(trigs) == len(TRIG_IDENTITIES)
        assert all(i.category == "trigonometric" for i in trigs)

    def test_get_by_category_hyperbolic(self):
        hyps = get_by_category("hyperbolic")
        assert len(hyps) == len(HYPERBOLIC_IDENTITIES)

    def test_get_by_category_unknown(self):
        result = get_by_category("unknown_category")
        assert result == []


# ── BenchmarkReport unit tests ─────────────────────────────────────────────────

class TestBenchmarkReport:
    def _make_report(self, n=3):
        """Build a minimal BenchmarkReport for testing."""
        def make_r(status):
            return ProofResult(
                identity_str="x == x",
                status=status,
                verification_method="sympy",
                confidence=1.0 if status.startswith("proved") else 0.0,
                max_residual=0.0,
                n_test_points=100,
                elapsed_s=0.1,
                lhs_tree=None, rhs_tree=None, witness_tree=None,
                node_count=0, lhs_formula=None, latex_proof=None,
                sympy_simplification="0", notes=[],
            )

        results = [make_r("proved_exact"), make_r("proved_numerical"), make_r("failed")]
        return BenchmarkReport(
            results=results,
            n_total=3,
            n_proved=2,
            n_exact=1,
            n_numerical=1,
            n_failed=1,
            success_rate=2/3,
            mean_elapsed_s=0.1,
            mean_nodes=0.0,
        )

    def test_summary_is_string(self):
        report = self._make_report()
        s = report.summary()
        assert isinstance(s, str)
        assert len(s) > 0

    def test_summary_contains_counts(self):
        report = self._make_report()
        s = report.summary()
        assert "2" in s  # n_proved
        assert "3" in s  # n_total

    def test_to_json_structure(self):
        report = self._make_report()
        data = report.to_json()
        required_keys = {"n_total", "n_proved", "n_exact", "n_numerical",
                         "n_failed", "success_rate", "mean_elapsed_s",
                         "mean_nodes", "results"}
        assert required_keys.issubset(data.keys())

    def test_to_json_results_length(self):
        report = self._make_report()
        data = report.to_json()
        assert len(data["results"]) == 3

    def test_success_rate_range(self):
        report = self._make_report()
        assert 0.0 <= report.success_rate <= 1.0


# ── Integration with sympy_bridge ─────────────────────────────────────────────

class TestSympyBridgeIntegration:
    def test_exact_proof_has_simplification(self, prover):
        r = prover.prove("exp(x)*exp(-x) == 1", domain=(-1.0, 1.0))
        if r.status == "proved_exact":
            assert r.sympy_simplification is not None

    def test_exact_proof_has_latex(self, prover):
        r = prover.prove("exp(x)*exp(-x) == 1", domain=(-1.0, 1.0))
        if r.status == "proved_exact":
            assert r.latex_proof is not None
            assert len(r.latex_proof) > 0

    def test_latex_proof_contains_proof_env(self, prover):
        r = prover.prove("exp(x)*exp(-x) == 1", domain=(-1.0, 1.0))
        if r.latex_proof is not None:
            assert r"begin{proof}" in r.latex_proof or "proof" in r.latex_proof.lower()

    def test_prove_log_squared(self, prover):
        # log(x**2) == 2*log(x) for x > 0
        r = prover.prove("log(x**2) == 2*log(x)", domain=(0.1, 5.0))
        assert r.proved(), f"Expected proof, got {r.status}: {r.notes}"

    def test_cosh_def_via_exp(self, prover):
        r = prover.prove("cosh(x) + sinh(x) == exp(x)", domain=(-2.0, 2.0))
        assert r.proved(), f"Expected proof: {r.notes}"
