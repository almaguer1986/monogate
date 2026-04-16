# Special Functions Catalog

> Module: `monogate.special`
> Version: 0.12.0 · 15 functions

---

## Overview

`monogate.special` provides pre-computed CBEST/BEST expressions for 15 special functions. Each entry records the EML formula, node count, domain, and maximum absolute error versus a reference implementation.

```python
from monogate.special import sin_cb, cos_cb, erf_cb, CATALOG

# Direct callables
sin_cb(3.14159 / 6)   # 0.5 (exact, 1 CBEST node)
erf_cb(1.0)           # ≈ 0.8427 (5 CBEST nodes)

# Catalog metadata
for name, entry in CATALOG.items():
    print(f"{name}: {entry.n_nodes} nodes, max_err={entry.max_abs_error:.2e}")
```

---

## Catalog

| Function | Backend | Nodes | Max Error | Domain |
|----------|---------|-------|-----------|--------|
| sin | CBEST | 1 | 0 (exact) | ℝ |
| cos | CBEST | 1 | 0 (exact) | ℝ |
| sinh | CBEST | 1 | ~1e-15 | ℝ |
| cosh | CBEST | 1 | ~1e-15 | ℝ |
| tanh | CBEST | 3 | ~1e-15 | ℝ |
| sech | BEST | 2 | 0 (exact) | ℝ |
| erf | CBEST | 5 | ~1e-3 | [-3, 3] |
| Fresnel S (integrand) | CBEST | 1 | 0 (exact) | ℝ |
| Fresnel C (integrand) | CBEST | 1 | 0 (exact) | ℝ |
| Fresnel S | CBEST | adaptive | ~1e-6 | [0, 5] |
| Fresnel C | CBEST | adaptive | ~1e-6 | [0, 5] |
| J₀ (Bessel) | CBEST | 7 | ~1e-3 | [-10, 10] |
| Ai (Airy) | CBEST | 9 | ~1e-3 | [-5, 5] |
| lgamma | BEST | 11 | ~1e-5 | (0, 20] |
| digamma | BEST | 12 | ~1e-5 | (0, 20] |

---

## Exact functions (0 error)

Functions with **exact** CBEST representations use the complex Euler path:

```python
from monogate.special import sin_cb, cos_cb

# Both are exactly Im/Re of eml(ix, 1) = exp(ix)
import math
assert abs(sin_cb(math.pi / 2) - 1.0) < 1e-15
assert abs(cos_cb(0.0) - 1.0) < 1e-15
```

The Fresnel integrands are also exact because they are themselves sin(πx²/2) and cos(πx²/2), each a 1-node CBEST expression.

---

## Approximate functions

Functions like `erf`, `J₀`, and `Ai` have no closed-form complex EML representation. Their entries use **MCTS-discovered approximations** that minimize maximum absolute error on a test domain.

```python
from monogate.special import erf_cb, j0_cb, ai_cb

# 5-node CBEST approximation of erf
erf_cb(0.5)    # ≈ 0.5205   (ref: 0.5205...)
erf_cb(2.0)    # ≈ 0.9953   (ref: 0.9953...)

# 7-node CBEST approximation of Bessel J₀
j0_cb(1.0)     # ≈ 0.7652   (ref: 0.7652...)

# 9-node CBEST approximation of Airy Ai
ai_cb(0.0)     # ≈ 0.3551   (ref: 0.3551...)
```

---

## Catalog summary

```python
from monogate.special import catalog_summary

catalog_summary()
# Prints a formatted table of all 15 functions
```

---

## Adding new functions

```python
from monogate.minimax import minimax_eml
import scipy.special

# Find a compact EML approximation for the Gamma function
result = minimax_eml(
    scipy.special.gamma,
    n_nodes=9,
    domain=(0.1, 4.0),
    n_simulations=10_000,
)
print(result.best_formula, f"L∞={result.linf:.4e}")
```

---

## See also

- `monogate.special` — module source
- `monogate.physics.PHYSICS_CATALOG` — PDE solutions
- `monogate.minimax` — find your own compact approximations
