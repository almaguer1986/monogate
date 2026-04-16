"""
monogate.sklearn_wrapper — scikit-learn compatible EML symbolic regressor.

Provides ``EMLRegressor``, a ``BaseEstimator + RegressorMixin`` that uses
MCTS/beam search to fit an EML expression tree to (X, y) data.

Usage::

    from monogate.sklearn_wrapper import EMLRegressor
    import numpy as np

    X = np.linspace(-3, 3, 100).reshape(-1, 1)
    y = np.sin(X.ravel())

    reg = EMLRegressor(max_depth=5, n_simulations=2000)
    reg.fit(X, y)
    print(reg.get_formula())           # EML expression string
    print(reg.score(X, y))             # R²

scikit-learn estimator check::

    from sklearn.utils.estimator_checks import check_estimator
    for est, check in check_estimator(EMLRegressor(), generate_only=True):
        check(est)  # raises on failure

Note: EMLRegressor fits a *univariate* EML tree (one input feature used by
the EML tree is the first PCA component when X has multiple columns).
Multi-feature support with named leaves (EMLNetwork) is planned for v1.1.
"""

from __future__ import annotations

import math
import warnings
from typing import Any

import numpy as np

try:
    from sklearn.base import BaseEstimator, RegressorMixin
    from sklearn.utils.validation import check_is_fitted, check_array, check_X_y
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False

from .search.mcts import mcts_search, beam_search, _eval_tree, _is_complete

__all__ = ["EMLRegressor"]

_SKLEARN_MISSING = (
    "scikit-learn is required for EMLRegressor.\n"
    "Install it with:  pip install scikit-learn>=1.0"
)


def _make_base_classes():
    """Return (BaseEstimator, RegressorMixin) or stub no-op classes."""
    if _HAS_SKLEARN:
        return BaseEstimator, RegressorMixin
    # Stub classes so the module still imports without sklearn
    import inspect as _inspect

    class _BaseStub:
        def get_params(self, deep: bool = True) -> dict:
            """Return constructor parameters (mirrors sklearn BaseEstimator)."""
            init = getattr(self.__class__.__init__, "__func__",
                           self.__class__.__init__)
            sig = _inspect.signature(init)
            params = {}
            for name, param in sig.parameters.items():
                if name == "self":
                    continue
                if param.kind in (_inspect.Parameter.VAR_POSITIONAL,
                                  _inspect.Parameter.VAR_KEYWORD):
                    continue
                params[name] = getattr(self, name, param.default)
            return params

        def set_params(self, **params):
            for k, v in params.items():
                setattr(self, k, v)
            return self
    class _MixinStub:
        def score(self, X, y):
            raise ImportError(_SKLEARN_MISSING)
    return _BaseStub, _MixinStub


_Base, _Mixin = _make_base_classes()


class EMLRegressor(_Base, _Mixin):  # type: ignore[misc]
    """scikit-learn compatible EML symbolic regressor.

    Fits an EML expression tree to ``(X, y)`` regression data using MCTS or
    beam search.  The fitted tree can be inspected symbolically.

    Parameters
    ----------
    max_depth : int, default=5
        Maximum tree depth.  Depth ``d`` yields at most ``2**d − 1`` internal
        EML nodes.  Higher depths allow more complex expressions but require
        more simulations to find good trees.
    n_simulations : int, default=5000
        MCTS simulation budget (ignored when ``search_method='beam'``).
    search_method : {'mcts', 'beam'}, default='mcts'
        Search algorithm.  ``'mcts'`` for Monte-Carlo Tree Search;
        ``'beam'`` for beam search with ``width=n_simulations // 100``.
    operator : str, default='EML'
        Reserved for future use (multi-operator routing).  Currently always
        uses the standard EML grammar.
    objective : {'mse', 'minimax'}, default='mse'
        Loss objective for MCTS.  ``'mse'`` minimises mean squared error;
        ``'minimax'`` minimises max absolute error (Chebyshev approximation).
    n_probe : int, default=100
        Number of probe points extracted from the training data for MCTS.
        Larger values give a better approximation of the true loss but slow
        down each simulation.
    random_state : int or None, default=None
        Random seed for reproducibility.

    Attributes
    ----------
    tree_ : dict
        Fitted EML tree node dict.
    formula_ : str
        Human-readable EML expression.
    best_score_ : float
        Training loss (MSE or max abs error) of the fitted tree.
    n_features_in_ : int
        Number of features seen during ``fit``.

    Examples
    --------
    >>> import numpy as np
    >>> from monogate.sklearn_wrapper import EMLRegressor
    >>> X = np.linspace(-3, 3, 50).reshape(-1, 1)
    >>> y = X.ravel() ** 2
    >>> reg = EMLRegressor(max_depth=3, n_simulations=500, random_state=42)
    >>> _ = reg.fit(X, y)
    >>> reg.get_formula()
    'eml(...)'
    """

    def __init__(
        self,
        max_depth: int = 5,
        n_simulations: int = 5_000,
        search_method: str = "mcts",
        operator: str = "EML",
        objective: str = "mse",
        n_probe: int = 100,
        random_state: int | None = None,
    ) -> None:
        self.max_depth      = max_depth
        self.n_simulations  = n_simulations
        self.search_method  = search_method
        self.operator       = operator
        self.objective      = objective
        self.n_probe        = n_probe
        self.random_state   = random_state

    # ── Fitting ───────────────────────────────────────────────────────────────

    def fit(self, X: np.ndarray, y: np.ndarray) -> "EMLRegressor":
        """Fit the EML tree to training data.

        Args:
            X: Training features of shape ``(n_samples, n_features)``.
               Currently uses only the first feature column.
            y: Target values of shape ``(n_samples,)``.

        Returns:
            self
        """
        if _HAS_SKLEARN:
            X, y = check_X_y(X, y, ensure_2d=True)
        else:
            X = np.asarray(X, dtype=float)
            y = np.asarray(y, dtype=float)
            if X.ndim == 1:
                X = X.reshape(-1, 1)

        self.n_features_in_ = X.shape[1]

        # Use first feature column as the single symbolic variable
        x_col = X[:, 0].ravel()

        # Sub-sample for MCTS probe points
        n = len(x_col)
        seed = self.random_state if self.random_state is not None else 42
        rng  = np.random.default_rng(seed)

        if n <= self.n_probe:
            idx = np.arange(n)
        else:
            idx = rng.choice(n, size=self.n_probe, replace=False)
            idx.sort()

        probe_x = x_col[idx].tolist()
        probe_y = y[idx].tolist()

        # Build target function that interpolates from probe points
        # (MCTS calls target_fn(x) for arbitrary x; we use piecewise linear interpolation)
        sorted_pairs = sorted(zip(probe_x, probe_y))
        xs_sorted = [p[0] for p in sorted_pairs]
        ys_sorted = [p[1] for p in sorted_pairs]

        def _target_fn(x: float) -> float:
            return float(np.interp(x, xs_sorted, ys_sorted))

        if self.search_method == "beam":
            width = max(10, self.n_simulations // 100)
            result = beam_search(
                target_fn=_target_fn,
                probe_points=probe_x,
                depth=self.max_depth,
                width=width,
                objective=self.objective,
            )
            self.tree_       = result.best_tree
            self.formula_    = result.best_formula
            self.best_score_ = result.best_mse
        else:
            result = mcts_search(
                target_fn=_target_fn,
                probe_points=probe_x,
                depth=self.max_depth,
                n_simulations=self.n_simulations,
                seed=seed,
                objective=self.objective,
            )
            self.tree_       = result.best_tree
            self.formula_    = result.best_formula
            self.best_score_ = result.best_mse

        return self

    # ── Prediction ────────────────────────────────────────────────────────────

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict target values for X.

        Args:
            X: Feature matrix of shape ``(n_samples, n_features)``.

        Returns:
            Predicted values of shape ``(n_samples,)``.
        """
        if _HAS_SKLEARN:
            check_is_fitted(self)
            X = check_array(X, ensure_2d=True)
        else:
            X = np.asarray(X, dtype=float)
            if X.ndim == 1:
                X = X.reshape(-1, 1)
            if not hasattr(self, "tree_"):
                raise RuntimeError("EMLRegressor is not fitted yet. Call fit() first.")

        x_col = X[:, 0].ravel()
        preds = np.empty(len(x_col), dtype=float)
        for i, xi in enumerate(x_col):
            try:
                if _is_complete(self.tree_):
                    preds[i] = _eval_tree(self.tree_, float(xi))
                else:
                    preds[i] = float("nan")
            except (ValueError, OverflowError):
                preds[i] = float("nan")
        return preds

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get_formula(self) -> str:
        """Return the fitted EML expression as a human-readable string.

        Returns:
            Formula string, e.g. ``'eml(eml(1.0, x), eml(x, 1.0))'``.

        Raises:
            RuntimeError: If called before ``fit()``.
        """
        if not hasattr(self, "formula_"):
            raise RuntimeError("EMLRegressor is not fitted yet. Call fit() first.")
        return self.formula_

    def get_tree(self) -> dict[str, Any]:
        """Return the fitted EML tree as a plain dict.

        The dict structure is compatible with ``monogate.sympy_bridge.to_sympy()``.

        Returns:
            Tree dict with keys ``'op'``, ``'left'``, ``'right'`` (or ``'val'``
            for leaves).

        Raises:
            RuntimeError: If called before ``fit()``.
        """
        if not hasattr(self, "tree_"):
            raise RuntimeError("EMLRegressor is not fitted yet. Call fit() first.")
        return self.tree_

    def __repr__(self) -> str:
        return (
            f"EMLRegressor(max_depth={self.max_depth}, "
            f"n_simulations={self.n_simulations}, "
            f"search_method={self.search_method!r}, "
            f"objective={self.objective!r})"
        )
