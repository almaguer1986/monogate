"""Smoke tests for SRBench benchmark infrastructure."""

from __future__ import annotations

import pytest
import numpy as np

from benchmarks.srbench.functions import (
    NGUYEN,
    KEIJZER,
    VLADISLAVLEVA,
    ALL_BENCHMARKS,
    EML_FRIENDLY,
    BenchmarkFn,
)
from benchmarks.srbench.report import generate_report
from benchmarks.srbench.runner import BenchmarkResult


class TestBenchmarkFunctions:
    def test_nguyen_count(self):
        assert len(NGUYEN) == 12

    def test_keijzer_count(self):
        assert len(KEIJZER) == 15

    def test_vladislavleva_count(self):
        assert len(VLADISLAVLEVA) == 8

    def test_all_benchmarks_total(self):
        assert len(ALL_BENCHMARKS) == 35

    def test_eml_friendly_tagged(self):
        assert len(EML_FRIENDLY) >= 3

    def test_sample_returns_finite_values(self):
        for fn in NGUYEN[:3]:
            X, y = fn.sample(n=20)
            assert len(X) > 0
            assert np.all(np.isfinite(y)), f"{fn.name} returned non-finite values"

    def test_test_sample_larger_than_train(self):
        fn = NGUYEN[0]
        X_tr, _ = fn.sample(n=20)
        X_te, _ = fn.test_sample(n=100)
        assert len(X_te) >= len(X_tr)

    def test_domains_valid(self):
        for fn in ALL_BENCHMARKS:
            lo, hi = fn.domain
            assert lo < hi, f"{fn.name}: invalid domain [{lo}, {hi}]"

    def test_sample_within_domain(self):
        for fn in NGUYEN[:4]:
            X, _ = fn.sample(n=50)
            assert np.all(X >= fn.domain[0])
            assert np.all(X <= fn.domain[1])

    def test_nguyen_7_uses_log(self):
        fn = next(f for f in NGUYEN if f.name == "Nguyen-7")
        X, y = fn.sample(n=10)
        # Nguyen-7 = log(x+1) + log(x^2+1), should be positive for x in (0,2)
        assert np.all(y >= 0)

    def test_nguyen_11_xpowx(self):
        fn = next(f for f in NGUYEN if f.name == "Nguyen-11")
        X, y = fn.sample(n=10)
        # x^x at x=1 should be 1
        assert np.isfinite(y).all()


class TestReport:
    def test_generate_report_empty(self):
        table = generate_report([])
        assert "SRBench" in table

    def test_generate_report_with_results(self):
        results = [
            BenchmarkResult(
                fn_name="Nguyen-7",
                suite="Nguyen",
                best_formula="log(x+1)+log(x^2+1)",
                train_r2=0.98,
                test_r2=0.97,
                best_mse=0.001,
                n_nodes=5,
                elapsed_s=1.2,
                method="mcts",
                tags=["logarithm", "eml-friendly"],
            ),
            BenchmarkResult(
                fn_name="Nguyen-1",
                suite="Nguyen",
                best_formula="x^3+x^2+x",
                train_r2=0.85,
                test_r2=0.80,
                best_mse=0.05,
                n_nodes=7,
                elapsed_s=0.8,
                method="beam",
                tags=["polynomial"],
            ),
        ]
        table = generate_report(results)
        assert "Nguyen-7" in table
        assert "monogate" in table or "baseline" in table
