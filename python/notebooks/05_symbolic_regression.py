"""
Tutorial 05: Symbolic Regression — EMLRegressor on Real Data
=============================================================
Demonstrates EMLRegressor as a sklearn-compatible symbolic regressor.
Fits EML expression trees to real datasets.

Run time: 1-3 minutes (scales with n_simulations)
"""

# %% [markdown]
# # Symbolic Regression with EMLRegressor
#
# `EMLRegressor` is a scikit-learn compatible estimator that uses MCTS
# to find compact, interpretable EML expression trees.

# %% Import
import math
import numpy as np
from monogate.sklearn_wrapper import EMLRegressor

# %% Example 1: Fit x²
print("=== Example 1: Fitting x² ===\n")

X = np.linspace(-2, 2, 50).reshape(-1, 1)
y = X.ravel() ** 2

reg = EMLRegressor(max_depth=3, n_simulations=500, random_state=42)
reg.fit(X, y)

preds = reg.predict(X)
mse   = np.nanmean((preds - y) ** 2)

print(f"Formula: {reg.get_formula()}")
print(f"MSE:     {mse:.4e}")

# %% Example 2: Fit exp(x)
print("\n=== Example 2: Fitting exp(x) ===\n")

y_exp = np.exp(X.ravel())
reg2  = EMLRegressor(max_depth=2, n_simulations=300, random_state=7)
reg2.fit(X, y_exp)

preds2 = reg2.predict(X)
mse2   = np.nanmean((preds2 - y_exp) ** 2)

print(f"Formula: {reg2.get_formula()}")
print(f"MSE:     {mse2:.4e}")

# %% Example 3: Minimax objective
print("\n=== Example 3: Minimax (L∞) objective ===\n")

y_sin = np.sin(X.ravel())
reg3  = EMLRegressor(
    max_depth=4,
    n_simulations=300,
    objective="minimax",
    random_state=42,
)
reg3.fit(X, y_sin)

preds3  = reg3.predict(X)
max_err = np.nanmax(np.abs(preds3 - y_sin))
print(f"Formula:    {reg3.get_formula()}")
print(f"Max error:  {max_err:.4e}")

# %% Sklearn integration
print("\n=== Sklearn integration ===\n")

try:
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("eml",    EMLRegressor(max_depth=3, n_simulations=200, random_state=0)),
    ])

    X_large = np.linspace(-3, 3, 80).reshape(-1, 1)
    y_large = X_large.ravel() ** 2 + 0.1 * np.random.default_rng(0).standard_normal(80)

    scores = cross_val_score(pipe, X_large, y_large, cv=3, scoring="r2")
    print(f"Pipeline CV R²: {scores.mean():.3f} ± {scores.std():.3f}")

except ImportError:
    print("scikit-learn not installed — skipping CV example")
    print("Install: pip install scikit-learn")

# %% Convert to SymPy
print("\n=== Convert to SymPy (if sympy installed) ===\n")

try:
    from monogate.sympy_bridge import to_sympy, latex_eml

    tree  = reg.get_tree()
    expr  = to_sympy(tree)
    latex = latex_eml(tree)

    print(f"SymPy expression: {expr}")
    print(f"LaTeX:            {latex[:60]}...")

except ImportError:
    print("sympy not installed — skipping")
    print("Install: pip install sympy")

# %% Summary
print("\n Tutorial 05 complete.")
print(" Key points:")
print("  - EMLRegressor is fully sklearn-compatible")
print("  - Supports both MSE and minimax objectives")
print("  - Results are symbolic formulas, not black-box models")
print("  - Works in pipelines and with cross-validation")
