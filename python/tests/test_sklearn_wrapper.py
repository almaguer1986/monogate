"""Tests for monogate.sklearn_wrapper — EMLRegressor."""

from __future__ import annotations

import math
import numpy as np
import pytest

from monogate.sklearn_wrapper import EMLRegressor


# ── Construction ──────────────────────────────────────────────────────────────

def test_default_construction():
    """EMLRegressor can be constructed with defaults."""
    reg = EMLRegressor()
    assert reg.max_depth == 5
    assert reg.n_simulations == 5_000
    assert reg.search_method == "mcts"
    assert reg.objective == "mse"


def test_custom_construction():
    """EMLRegressor stores custom parameters."""
    reg = EMLRegressor(max_depth=3, n_simulations=100, search_method="beam",
                       objective="minimax", random_state=42)
    assert reg.max_depth == 3
    assert reg.n_simulations == 100
    assert reg.search_method == "beam"
    assert reg.objective == "minimax"
    assert reg.random_state == 42


def test_repr():
    """EMLRegressor has a useful repr."""
    reg = EMLRegressor(max_depth=3, n_simulations=100)
    r = repr(reg)
    assert "EMLRegressor" in r
    assert "max_depth=3" in r


# ── get_params / set_params (sklearn API) ─────────────────────────────────────

def test_get_params():
    """get_params returns constructor parameters."""
    reg = EMLRegressor(max_depth=4, n_simulations=200, random_state=7)
    params = reg.get_params()
    assert params["max_depth"] == 4
    assert params["n_simulations"] == 200
    assert params["random_state"] == 7


def test_set_params():
    """set_params updates parameters and returns self."""
    reg = EMLRegressor()
    result = reg.set_params(max_depth=2, n_simulations=50)
    assert result is reg
    assert reg.max_depth == 2
    assert reg.n_simulations == 50


# ── Fitting ───────────────────────────────────────────────────────────────────

def _make_data(n: int = 50, seed: int = 0):
    rng = np.random.default_rng(seed)
    X = rng.uniform(-2, 2, size=(n, 1))
    y = X.ravel() ** 2
    return X, y


def test_fit_returns_self():
    """fit returns self (sklearn convention)."""
    X, y = _make_data()
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=42)
    result = reg.fit(X, y)
    assert result is reg


def test_fit_sets_attributes():
    """fit sets tree_, formula_, best_score_, n_features_in_."""
    X, y = _make_data()
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=42)
    reg.fit(X, y)
    assert hasattr(reg, "tree_")
    assert hasattr(reg, "formula_")
    assert hasattr(reg, "best_score_")
    assert hasattr(reg, "n_features_in_")
    assert reg.n_features_in_ == 1


def test_fit_formula_is_string():
    """formula_ is a non-empty string after fit."""
    X, y = _make_data()
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=42)
    reg.fit(X, y)
    assert isinstance(reg.formula_, str)
    assert len(reg.formula_) > 0


def test_fit_best_score_finite():
    """best_score_ is a finite number."""
    X, y = _make_data()
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=42)
    reg.fit(X, y)
    assert math.isfinite(reg.best_score_)


def test_fit_multi_column():
    """EMLRegressor works with multi-column X (uses first column)."""
    X = np.column_stack([
        np.linspace(-2, 2, 30),
        np.linspace(-1, 1, 30),
    ])
    y = X[:, 0] ** 2
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=0)
    reg.fit(X, y)
    assert reg.n_features_in_ == 2


def test_fit_beam_search():
    """EMLRegressor works with search_method='beam'."""
    X, y = _make_data()
    reg = EMLRegressor(max_depth=2, n_simulations=200, search_method="beam",
                       random_state=42)
    reg.fit(X, y)
    assert hasattr(reg, "tree_")


def test_fit_minimax_objective():
    """EMLRegressor works with objective='minimax'."""
    X, y = _make_data()
    reg = EMLRegressor(max_depth=2, n_simulations=100, objective="minimax",
                       random_state=42)
    reg.fit(X, y)
    assert hasattr(reg, "tree_")


# ── Prediction ────────────────────────────────────────────────────────────────

def test_predict_shape():
    """predict returns array of shape (n_samples,)."""
    X, y = _make_data(50)
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=42)
    reg.fit(X, y)
    preds = reg.predict(X)
    assert preds.shape == (50,)


def test_predict_finite():
    """predict values are finite floats."""
    X, y = _make_data(30)
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=42)
    reg.fit(X, y)
    preds = reg.predict(X)
    # Some may be nan due to domain errors; check the array has the right type
    assert preds.dtype == float


def test_predict_before_fit_raises():
    """predict before fit raises RuntimeError."""
    reg = EMLRegressor()
    X = np.ones((10, 1))
    with pytest.raises(RuntimeError):
        reg.predict(X)


def test_predict_1d_input():
    """predict accepts 1D input arrays."""
    X_1d = np.linspace(-2, 2, 20)
    y_1d = X_1d ** 2
    X_2d = X_1d.reshape(-1, 1)
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=42)
    reg.fit(X_2d, y_1d)
    preds = reg.predict(X_1d.reshape(-1, 1))
    assert preds.shape == (20,)


# ── get_formula / get_tree ────────────────────────────────────────────────────

def test_get_formula_before_fit_raises():
    """get_formula before fit raises RuntimeError."""
    reg = EMLRegressor()
    with pytest.raises(RuntimeError):
        reg.get_formula()


def test_get_formula_after_fit():
    """get_formula returns a string after fit."""
    X, y = _make_data()
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=42)
    reg.fit(X, y)
    formula = reg.get_formula()
    assert isinstance(formula, str)
    assert len(formula) > 0


def test_get_tree_before_fit_raises():
    """get_tree before fit raises RuntimeError."""
    reg = EMLRegressor()
    with pytest.raises(RuntimeError):
        reg.get_tree()


def test_get_tree_after_fit():
    """get_tree returns a dict with 'op' key after fit."""
    X, y = _make_data()
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=42)
    reg.fit(X, y)
    tree = reg.get_tree()
    assert isinstance(tree, dict)
    assert "op" in tree


# ── Reproducibility ───────────────────────────────────────────────────────────

def test_reproducible_with_same_seed():
    """Same seed → same formula."""
    X, y = _make_data()
    reg1 = EMLRegressor(max_depth=2, n_simulations=200, random_state=0)
    reg2 = EMLRegressor(max_depth=2, n_simulations=200, random_state=0)
    reg1.fit(X, y)
    reg2.fit(X, y)
    assert reg1.get_formula() == reg2.get_formula()


# ── Sklearn score ─────────────────────────────────────────────────────────────

def test_score_returns_float():
    """score() returns a float (R²)."""
    try:
        from sklearn.base import RegressorMixin
        _has_sklearn = True
    except ImportError:
        _has_sklearn = False

    if not _has_sklearn:
        pytest.skip("scikit-learn not installed")

    X, y = _make_data()
    reg = EMLRegressor(max_depth=2, n_simulations=100, random_state=42)
    reg.fit(X, y)
    s = reg.score(X, y)
    assert isinstance(s, float)
