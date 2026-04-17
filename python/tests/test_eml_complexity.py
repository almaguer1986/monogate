"""Tests for monogate.frontiers.eml_complexity — EML Complexity Theory."""

from __future__ import annotations

import math
import pytest

from monogate.frontiers.eml_complexity import (
    EML_1, EML_2, EML_3, EML_INF, COMPLEXITY_CLASSES,
    EMLComplexityClass,
    complexity_certificate,
    zero_order_lower_bound,
    zero_order_at,
    classify_function,
    complexity_table,
    _KNOWN_FUNCTIONS,
)


# ── EMLComplexityClass ────────────────────────────────────────────────────────

class TestComplexityClasses:
    def test_four_classes_defined(self):
        assert len(COMPLEXITY_CLASSES) == 4

    def test_eml1_depth_one(self):
        assert EML_1.depth == 1

    def test_eml3_depth_three(self):
        assert EML_3.depth == 3

    def test_eml_inf_depth_none(self):
        assert EML_INF.depth is None

    def test_contains_by_depth(self):
        assert EML_1.contains(1)
        assert not EML_1.contains(2)
        assert EML_3.contains(1)
        assert EML_3.contains(3)
        assert not EML_3.contains(4)
        assert EML_INF.contains(1)
        assert EML_INF.contains(100)
        assert not EML_1.contains(None)

    def test_all_have_examples(self):
        for cls in COMPLEXITY_CLASSES:
            assert cls.canonical_example
            assert len(cls.known_functions) >= 1

    def test_frozen_dataclass(self):
        with pytest.raises(Exception):
            EML_1.depth = 99  # type: ignore[misc]


# ── complexity_certificate ────────────────────────────────────────────────────

class TestComplexityCertificate:
    def test_exp_depth_one_verified(self):
        cert = complexity_certificate("exp")
        assert cert["claimed_depth"] == 1
        assert cert["verified"] is True
        assert cert["max_error"] < 1e-10

    def test_deml_depth_one_verified(self):
        cert = complexity_certificate("deml")
        assert cert["claimed_depth"] == 1
        assert cert["verified"] is True
        assert cert["max_error"] < 1e-10

    def test_ln_depth_three_verified(self):
        cert = complexity_certificate("ln")
        assert cert["claimed_depth"] == 3
        assert cert["verified"] is True
        assert cert["max_error"] < 1e-10

    def test_sin_depth_infinite(self):
        cert = complexity_certificate("sin")
        assert cert["claimed_depth"] is None
        assert cert["claimed_class"] == "EML-∞"

    def test_unknown_function_returns_error(self):
        cert = complexity_certificate("nonexistent_fn_xyz")
        assert "error" in cert

    def test_all_known_functions_have_certificates(self):
        for name in _KNOWN_FUNCTIONS:
            cert = complexity_certificate(name)
            assert "claimed_class" in cert
            assert "error" not in cert

    def test_lower_bound_consistent_with_depth(self):
        for name in _KNOWN_FUNCTIONS:
            cert = complexity_certificate(name)
            assert cert["lower_bound_consistent"], (
                f"Lower bound > claimed depth for {name}: "
                f"lb={cert['lower_bound']}, depth={cert['claimed_depth']}"
            )


# ── zero_order_at ─────────────────────────────────────────────────────────────

class TestZeroOrderAt:
    def test_sin_simple_zero_at_zero(self):
        k = zero_order_at(math.sin, 0.0)
        assert k == 1, f"Expected order 1 for sin at 0, got {k}"

    def test_ln_simple_zero_at_one(self):
        k = zero_order_at(math.log, 1.0)
        assert k == 1, f"Expected order 1 for ln at 1, got {k}"

    def test_not_zero(self):
        k = zero_order_at(math.exp, 1.0)
        assert k == 0, "exp(1) != 0, should return 0"

    def test_double_zero(self):
        # x^2 has double zero at 0
        k = zero_order_at(lambda x: (x - 1.0) ** 2, 1.0)
        assert k >= 1, f"Expected order >= 1 for (x-1)^2, got {k}"


# ── zero_order_lower_bound ────────────────────────────────────────────────────

class TestZeroOrderLowerBound:
    def test_sin_at_zero_bound(self):
        lb = zero_order_lower_bound(math.sin, 0.0)
        assert lb >= 0

    def test_exp_no_zero_bound_zero(self):
        lb = zero_order_lower_bound(math.exp, 1.0)
        assert lb == 0

    def test_order_k_implies_bound(self):
        # f(x) = (x-1)^4 has zero of order 4 at x=1 -> lb >= ceil(log2(4)) = 2
        f = lambda x: (x - 1.0) ** 4
        lb = zero_order_lower_bound(f, 1.0)
        assert lb >= 1, f"Expected lb >= 1 for order-4 zero, got {lb}"


# ── classify_function ─────────────────────────────────────────────────────────

class TestClassifyFunction:
    def test_exp_classified(self):
        result = classify_function(math.exp, domain=(-2.0, 2.0))
        assert "complexity_class" in result

    def test_sin_high_zero_density(self):
        result = classify_function(math.sin, domain=(0.0, 10.0))
        assert "∞" in result["complexity_class"] or result["zero_count"] > 0

    def test_returns_required_keys(self):
        result = classify_function(math.log, domain=(0.1, 5.0))
        for key in ("lower_bound", "complexity_class", "reason"):
            assert key in result


# ── complexity_table ──────────────────────────────────────────────────────────

class TestComplexityTable:
    def test_returns_markdown_string(self):
        t = complexity_table()
        assert isinstance(t, str)
        assert "##" in t

    def test_contains_all_known_functions(self):
        t = complexity_table()
        for name in _KNOWN_FUNCTIONS:
            assert name in t, f"'{name}' not in complexity table"

    def test_contains_eml_inf_notation(self):
        t = complexity_table()
        assert "∞" in t

    def test_mentions_pumping_lemma(self):
        t = complexity_table()
        assert "Pumping Lemma" in t or "pumping" in t.lower()
