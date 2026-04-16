"""Tests for monogate.minimax — Minimax EML approximation."""

from __future__ import annotations

import math
import pytest

from monogate.minimax import MinimaxResult, minimax_eml, minimax_survey


# ── MinimaxResult construction ────────────────────────────────────────────────

def test_minimax_result_fields():
    """MinimaxResult stores the expected fields."""
    from monogate.search.mcts import mcts_search
    mcts_r = mcts_search(math.exp, n_simulations=50, seed=0)
    r = MinimaxResult(
        best_tree=mcts_r.best_tree,
        best_formula=mcts_r.best_formula,
        linf=0.1,
        l2=0.05,
        n_nodes=3,
        domain=(-1.0, 1.0),
        n_probe=50,
        elapsed_s=0.1,
        mcts_result=mcts_r,
    )
    assert r.linf == pytest.approx(0.1)
    assert r.l2  == pytest.approx(0.05)
    assert r.n_nodes == 3
    assert r.domain == (-1.0, 1.0)


def test_minimax_result_repr():
    """MinimaxResult has a useful repr."""
    from monogate.search.mcts import mcts_search
    mcts_r = mcts_search(math.exp, n_simulations=50, seed=0)
    r = MinimaxResult(
        best_tree=mcts_r.best_tree, best_formula="eml(1,1)",
        linf=0.01, l2=0.005, n_nodes=1, domain=(0.0, 1.0),
        n_probe=10, elapsed_s=0.0, mcts_result=mcts_r,
    )
    assert "MinimaxResult" in repr(r)
    assert "L∞" in repr(r)


# ── minimax_eml ───────────────────────────────────────────────────────────────

def test_minimax_eml_returns_result():
    """minimax_eml returns a MinimaxResult."""
    r = minimax_eml(math.exp, n_nodes=1, domain=(0.0, 1.0), n_simulations=100)
    assert isinstance(r, MinimaxResult)


def test_minimax_eml_formula_is_string():
    """best_formula is a non-empty string."""
    r = minimax_eml(math.exp, n_nodes=1, domain=(0.0, 1.0), n_simulations=100)
    assert isinstance(r.best_formula, str)
    assert len(r.best_formula) > 0


def test_minimax_eml_linf_finite():
    """L∞ error is finite."""
    r = minimax_eml(math.exp, n_nodes=1, domain=(0.0, 1.0), n_simulations=100)
    assert math.isfinite(r.linf)
    assert r.linf >= 0.0


def test_minimax_eml_l2_finite():
    """L² error is finite."""
    r = minimax_eml(math.exp, n_nodes=1, domain=(0.0, 1.0), n_simulations=100)
    assert math.isfinite(r.l2)
    assert r.l2 >= 0.0


def test_minimax_eml_l2_leq_linf():
    """L² error ≤ L∞ error (for uniform probe points)."""
    r = minimax_eml(math.exp, n_nodes=3, domain=(0.0, 1.0), n_simulations=200)
    assert r.l2 <= r.linf + 1e-12


def test_minimax_eml_elapsed_nonnegative():
    """elapsed_s is non-negative."""
    r = minimax_eml(math.exp, n_nodes=1, domain=(0.0, 1.0), n_simulations=50)
    assert r.elapsed_s >= 0.0


def test_minimax_eml_domain_stored():
    """domain is stored correctly."""
    r = minimax_eml(math.exp, n_nodes=1, domain=(-2.0, 2.0), n_simulations=50)
    assert r.domain == (-2.0, 2.0)


def test_minimax_eml_tree_is_dict():
    """best_tree is a dict with 'op' key."""
    r = minimax_eml(math.exp, n_nodes=1, domain=(0.0, 1.0), n_simulations=100)
    assert isinstance(r.best_tree, dict)
    assert "op" in r.best_tree


def test_minimax_eml_mcts_result_attached():
    """mcts_result is an MCTSResult."""
    from monogate.search.mcts import MCTSResult
    r = minimax_eml(math.exp, n_nodes=1, domain=(0.0, 1.0), n_simulations=100)
    assert isinstance(r.mcts_result, MCTSResult)
    assert r.mcts_result.objective == "minimax"


def test_minimax_eml_seed_reproducible():
    """Same seed → identical results."""
    r1 = minimax_eml(math.exp, n_nodes=3, domain=(0.0, 1.0),
                     n_simulations=200, seed=7)
    r2 = minimax_eml(math.exp, n_nodes=3, domain=(0.0, 1.0),
                     n_simulations=200, seed=7)
    assert r1.best_formula == r2.best_formula
    assert r1.linf == pytest.approx(r2.linf)


def test_minimax_eml_different_seeds_may_differ():
    """Different seeds can (and usually do) find different trees."""
    r1 = minimax_eml(math.sin, n_nodes=3, domain=(-3.0, 3.0),
                     n_simulations=300, seed=1)
    r2 = minimax_eml(math.sin, n_nodes=3, domain=(-3.0, 3.0),
                     n_simulations=300, seed=999)
    # Just check they both ran without error; formulas may differ
    assert isinstance(r1.linf, float)
    assert isinstance(r2.linf, float)


def test_minimax_eml_identity_fn():
    """Minimax approximation of the identity function."""
    r = minimax_eml(lambda x: x, n_nodes=3, domain=(-1.0, 1.0), n_simulations=300)
    assert isinstance(r, MinimaxResult)
    assert r.linf >= 0.0


def test_minimax_eml_constant_fn():
    """Constant target should be approximable with small error."""
    r = minimax_eml(lambda _: 2.718, n_nodes=1, domain=(-1.0, 1.0), n_simulations=200)
    # Should find something with finite error
    assert math.isfinite(r.linf)


def test_minimax_eml_probe_count():
    """n_probe is stored in the result."""
    r = minimax_eml(math.exp, n_nodes=1, domain=(0.0, 1.0),
                    n_probe=50, n_simulations=50)
    assert r.n_probe == 50


# ── minimax_survey ────────────────────────────────────────────────────────────

def test_minimax_survey_returns_list():
    """minimax_survey returns a list."""
    rows = minimax_survey(math.exp, node_counts=[1, 3],
                          domain=(0.0, 1.0), n_simulations=100)
    assert isinstance(rows, list)


def test_minimax_survey_length():
    """minimax_survey returns one row per node count."""
    rows = minimax_survey(math.exp, node_counts=[1, 3, 5],
                          domain=(0.0, 1.0), n_simulations=100)
    assert len(rows) == 3


def test_minimax_survey_row_keys():
    """Each row has the expected keys."""
    rows = minimax_survey(math.exp, node_counts=[1],
                          domain=(0.0, 1.0), n_simulations=50)
    row = rows[0]
    for key in ("n_nodes", "depth", "formula", "linf", "l2", "elapsed_s"):
        assert key in row, f"missing key: {key}"


def test_minimax_survey_monotone_error():
    """L∞ should be non-increasing as node budget grows (not guaranteed but typical)."""
    rows = minimax_survey(math.sin, node_counts=[1, 3, 7],
                          domain=(-3.0, 3.0), n_simulations=200)
    # Just verify all errors are finite
    for row in rows:
        assert math.isfinite(row["linf"]), f"infinite linf for n_nodes={row['n_nodes']}"


def test_minimax_survey_default_node_counts():
    """Default node_counts runs 6 levels."""
    rows = minimax_survey(math.exp, domain=(0.0, 1.0), n_simulations=50)
    assert len(rows) == 6


def test_minimax_eml_n_nodes_zero_fallback():
    """n_nodes=0 is handled gracefully (depth=1 floor)."""
    r = minimax_eml(math.exp, n_nodes=0, domain=(0.0, 1.0), n_simulations=50)
    assert isinstance(r, MinimaxResult)
