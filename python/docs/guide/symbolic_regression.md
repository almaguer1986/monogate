# Symbolic Regression with EMLRegressor

> Module: `monogate.sklearn_wrapper`
> Class: `EMLRegressor`

---

## Overview

`EMLRegressor` is a scikit-learn compatible estimator that uses MCTS or beam search to fit an EML expression tree to numerical data. Unlike neural network regressors, the result is a *symbolic* formula you can inspect, simplify, and reason about.

```python
from monogate.sklearn_wrapper import EMLRegressor
import numpy as np

X = np.linspace(-3, 3, 100).reshape(-1, 1)
y = np.exp(X.ravel())

reg = EMLRegressor(max_depth=4, n_simulations=3000, random_state=42)
reg.fit(X, y)

print(reg.get_formula())   # e.g. "eml(eml(x, 1.0), eml(1.0, 1.0))"
print(f"R² = {reg.score(X, y):.4f}")
```

---

## Installation

```bash
pip install monogate
# Optional: for sklearn check_estimator
pip install scikit-learn>=1.0
```

---

## Quick Start

### Fit a sine approximation

```python
import math, numpy as np
from monogate.sklearn_wrapper import EMLRegressor

X = np.linspace(-3, 3, 200).reshape(-1, 1)
y = np.sin(X.ravel())

reg = EMLRegressor(
    max_depth=5,
    n_simulations=5000,
    objective="minimax",   # minimize max |error|
    random_state=0,
)
reg.fit(X, y)
print(reg.get_formula())
```

### Fit x² (should find exact or near-exact)

```python
X = np.linspace(-2, 2, 50).reshape(-1, 1)
y = X.ravel() ** 2

reg = EMLRegressor(max_depth=3, n_simulations=1000, random_state=42)
reg.fit(X, y)
preds = reg.predict(X)
mse   = np.mean((preds - y) ** 2)
print(f"Formula: {reg.get_formula()}")
print(f"MSE: {mse:.4e}")
```

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_depth` | int | 5 | Maximum tree depth (depth `d` → up to 2^d−1 nodes) |
| `n_simulations` | int | 5000 | MCTS simulation budget |
| `search_method` | str | `'mcts'` | `'mcts'` or `'beam'` |
| `operator` | str | `'EML'` | Reserved for future multi-operator routing |
| `objective` | str | `'mse'` | `'mse'` or `'minimax'` |
| `n_probe` | int | 100 | Training samples used as MCTS probe points |
| `random_state` | int or None | None | Seed for reproducibility |

---

## Attributes after fit

| Attribute | Description |
|-----------|-------------|
| `tree_` | Fitted EML tree dict |
| `formula_` | Human-readable EML formula |
| `best_score_` | Training loss (MSE or max abs error) |
| `n_features_in_` | Number of input features |

---

## Methods

### `fit(X, y)`

Fits the EML tree to training data. `X` must have shape `(n_samples, n_features)`. Only the first feature column is used as the symbolic variable.

### `predict(X)`

Returns predicted values as a NumPy array of shape `(n_samples,)`.

### `get_formula()`

Returns the fitted EML expression as a human-readable string.

### `get_tree()`

Returns the fitted EML tree as a plain dict. Compatible with `monogate.sympy_bridge.to_sympy()`:

```python
from monogate.sympy_bridge import to_sympy, latex_eml

tree   = reg.get_tree()
expr   = to_sympy(tree)          # SymPy expression
latex  = latex_eml(tree)         # LaTeX string
```

### `score(X, y)`

Returns R² (coefficient of determination) via the sklearn `RegressorMixin.score()` default.

---

## sklearn Integration

`EMLRegressor` is a full sklearn estimator. It supports:

- `get_params()` / `set_params()` for pipeline integration
- `clone()` compatibility
- Cross-validation via `cross_val_score`

```python
from sklearn.model_selection import cross_val_score
scores = cross_val_score(
    EMLRegressor(max_depth=3, n_simulations=500, random_state=42),
    X, y, cv=5, scoring="r2"
)
print(f"CV R² = {scores.mean():.3f} ± {scores.std():.3f}")
```

---

## Pipeline example

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("eml",    EMLRegressor(max_depth=4, n_simulations=2000)),
])
pipe.fit(X_train, y_train)
print(pipe.score(X_test, y_test))
```

---

## Limitations

- **Univariate:** Only the first feature column is used as the symbolic variable `x`. Multi-feature support (via `EMLNetwork`) is planned for v1.1.
- **Discrete search:** MCTS explores a finite grammar; deep or complex targets may need large `n_simulations`.
- **Non-deterministic:** Results vary with `random_state`. Set `random_state` for reproducibility.

---

## Benchmarks (SRBench)

See `python/SRBENCH.md` for results on the Nguyen-1..12 and Keijzer-1..15 benchmark suites.

---

## See also

- `monogate.minimax` — minimax (L∞) approximation wrapper
- `monogate.search.mcts_search` — low-level MCTS API
- `monogate.sympy_bridge` — convert fitted tree to SymPy
- `python/experiments/srbench_runner.py` — SRBench benchmark script
