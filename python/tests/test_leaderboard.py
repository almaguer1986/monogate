"""
Tests for monogate.leaderboard — symbolic regression benchmark runner.

Covers:
- PROBLEMS dict is populated with BenchmarkProblem entries
- Each problem target_fn is callable and returns a finite float in its domain
- _probe_points returns the correct number of points within domain bounds
- run_leaderboard returns LeaderboardEntry objects for each (problem, method) pair
- LeaderboardEntry fields are type-correct and logically consistent
- save_leaderboard writes valid JSON; load_leaderboard round-trips correctly
- markdown_leaderboard returns a non-empty string containing expected headers
- Unknown problem or method raises ValueError
- Fast mode: n_simulations=100 so tests complete quickly
"""

import json
import math
import os
import tempfile

import pytest

from monogate.leaderboard import (
    PROBLEMS,
    BenchmarkProblem,
    LeaderboardEntry,
    _probe_points,
    load_leaderboard,
    markdown_leaderboard,
    run_leaderboard,
    save_leaderboard,
)


# ── Problem registry ──────────────────────────────────────────────────────────

class TestProblems:
    def test_problems_nonempty(self):
        assert len(PROBLEMS) >= 8

    def test_all_entries_are_benchmark_problem(self):
        for name, prob in PROBLEMS.items():
            assert isinstance(prob, BenchmarkProblem), f"{name} is not a BenchmarkProblem"

    def test_expected_problems_present(self):
        expected = [
            "nguyen-1", "nguyen-2", "nguyen-5", "nguyen-7", "nguyen-8",
            "keijzer-6", "keijzer-11",
        ]
        for name in expected:
            assert name in PROBLEMS, f"Missing problem: {name}"

    @pytest.mark.parametrize("name", list(PROBLEMS.keys()))
    def test_target_fn_returns_finite_at_midpoint(self, name: str):
        prob = PROBLEMS[name]
        mid = (prob.domain[0] + prob.domain[1]) / 2.0
        val = prob.target_fn(mid)
        assert math.isfinite(val), f"{name}: target_fn({mid}) = {val}"

    def test_domain_lo_lt_hi(self):
        for name, prob in PROBLEMS.items():
            assert prob.domain[0] < prob.domain[1], f"{name}: domain lo >= hi"

    def test_mse_threshold_positive(self):
        for name, prob in PROBLEMS.items():
            assert prob.mse_threshold > 0.0


# ── Probe points ──────────────────────────────────────────────────────────────

class TestProbePoints:
    def test_default_count(self):
        prob = PROBLEMS["nguyen-1"]
        pts = _probe_points(prob, n=40)
        assert len(pts) == 40

    def test_custom_count(self):
        prob = PROBLEMS["nguyen-1"]
        pts = _probe_points(prob, n=10)
        assert len(pts) == 10

    def test_within_domain(self):
        for name, prob in PROBLEMS.items():
            pts = _probe_points(prob, n=20)
            lo, hi = prob.domain
            for p in pts:
                assert lo <= p <= hi, f"{name}: probe point {p} outside [{lo}, {hi}]"

    def test_returns_list(self):
        prob = PROBLEMS["nguyen-1"]
        assert isinstance(_probe_points(prob), list)


# ── run_leaderboard (fast mode, n_sim=100) ────────────────────────────────────

_FAST_PROBLEMS = ["nguyen-1", "nguyen-8"]
_FAST_METHODS = ["beam"]   # beam is faster than mcts for smoke tests


class TestRunLeaderboard:
    def test_returns_list_of_entries(self):
        entries = run_leaderboard(
            problems=_FAST_PROBLEMS,
            n_simulations=100,
            depth=3,
            methods=_FAST_METHODS,
        )
        assert isinstance(entries, list)
        assert len(entries) == len(_FAST_PROBLEMS) * len(_FAST_METHODS)

    def test_entries_are_leaderboard_entry(self):
        entries = run_leaderboard(
            problems=["nguyen-1"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        for e in entries:
            assert isinstance(e, LeaderboardEntry)

    def test_entry_fields_type_correct(self):
        entries = run_leaderboard(
            problems=["nguyen-8"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        e = entries[0]
        assert isinstance(e.problem, str)
        assert isinstance(e.formula, str)
        assert isinstance(e.n_nodes, int)
        assert isinstance(e.best_mse, float)
        assert isinstance(e.solved, bool)
        assert isinstance(e.method, str)
        assert isinstance(e.elapsed_s, float)

    def test_entry_n_nodes_nonnegative(self):
        entries = run_leaderboard(
            problems=["nguyen-1"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        for e in entries:
            assert e.n_nodes >= 0

    def test_entry_mse_nonnegative(self):
        entries = run_leaderboard(
            problems=["nguyen-1"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        for e in entries:
            assert e.best_mse >= 0.0

    def test_solved_consistent_with_mse(self):
        entries = run_leaderboard(
            problems=["nguyen-1"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        for e in entries:
            prob = PROBLEMS[e.problem]
            expected_solved = e.best_mse < prob.mse_threshold
            assert e.solved == expected_solved

    def test_elapsed_positive(self):
        entries = run_leaderboard(
            problems=["nguyen-1"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        for e in entries:
            assert e.elapsed_s > 0.0

    def test_unknown_problem_raises(self):
        with pytest.raises(ValueError, match="Unknown problem"):
            run_leaderboard(
                problems=["nguyen-999"],
                n_simulations=50,
                methods=["beam"],
            )

    def test_correct_problem_method_pairs(self):
        entries = run_leaderboard(
            problems=["nguyen-1", "nguyen-8"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        problems_found = {e.problem for e in entries}
        assert "nguyen-1" in problems_found
        assert "nguyen-8" in problems_found


# ── Serialization ─────────────────────────────────────────────────────────────

class TestSerialization:
    def _make_entry(self) -> LeaderboardEntry:
        return LeaderboardEntry(
            problem="nguyen-1",
            formula="eml(x, 1)",
            n_nodes=1,
            best_mse=0.5,
            solved=False,
            method="beam",
            elapsed_s=0.1,
        )

    def test_save_creates_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
            path = fh.name
        save_leaderboard([self._make_entry()], path)
        assert os.path.isfile(path)

    def test_save_valid_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
            path = fh.name
        save_leaderboard([self._make_entry()], path)
        with open(path) as fh:
            data = json.load(fh)
        assert isinstance(data, list)
        assert data[0]["problem"] == "nguyen-1"

    def test_round_trip(self):
        entry = self._make_entry()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
            path = fh.name
        save_leaderboard([entry], path)
        loaded = load_leaderboard(path)
        assert len(loaded) == 1
        assert loaded[0].problem == entry.problem
        assert loaded[0].n_nodes == entry.n_nodes
        assert loaded[0].best_mse == pytest.approx(entry.best_mse)
        assert loaded[0].solved == entry.solved
        assert loaded[0].method == entry.method

    def test_save_with_run_results(self):
        entries = run_leaderboard(
            problems=["nguyen-1"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
            path = fh.name
        save_leaderboard(entries, path)
        loaded = load_leaderboard(path)
        assert len(loaded) == len(entries)
        assert loaded[0].problem == entries[0].problem


# ── Markdown output ───────────────────────────────────────────────────────────

class TestMarkdown:
    def test_returns_string(self):
        entries = run_leaderboard(
            problems=["nguyen-1"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        md = markdown_leaderboard(entries)
        assert isinstance(md, str)
        assert len(md) > 50

    def test_contains_problem_name(self):
        entries = run_leaderboard(
            problems=["nguyen-8"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        md = markdown_leaderboard(entries)
        assert "nguyen-8" in md

    def test_contains_header(self):
        entries = run_leaderboard(
            problems=["nguyen-1"],
            n_simulations=100,
            depth=3,
            methods=["beam"],
        )
        md = markdown_leaderboard(entries)
        assert "Problem" in md
        assert "MSE" in md

    def test_empty_list(self):
        md = markdown_leaderboard([])
        assert isinstance(md, str)
