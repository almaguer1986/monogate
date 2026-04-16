# Special Functions — monogate.special

`monogate.special` provides short CBEST/BEST expressions for 14 special functions.
Each function is callable as `sin_cb(x)`, `erf_cb(x)`, etc.
The `CATALOG` dict gives the formula, node count, and accuracy metadata for each.

---

## Quick start

```python
from monogate.special import sin_cb, cos_cb, erf_cb, j0_cb, CATALOG
import math

# Exact trig — 1 CBEST node each
sin_cb(math.pi / 6)       # 0.5  (exact)
cos_cb(math.pi / 3)       # 0.5  (exact)

# erf approximation — 5 CBEST nodes
erf_cb(1.0)               # ≈ 0.840  (max error ~1.5e-2)

# Bessel J₀ — 7 CBEST nodes
j0_cb(0.0)                # 1.0  (exact via scipy or Taylor)

# Catalog metadata
print(CATALOG["sin"])
# SpecialFnEntry(name='sin', n_nodes=1, backend='CBEST', max_abs_error=1.00e-15, domain=(-10.0, 10.0))
```

---

## Function reference

### Exact constructions (machine precision)

| Function | Call | Formula | Nodes | Notes |
|----------|------|---------|-------|-------|
| sin(x) | `sin_cb(x)` | `Im(eml(ix, 1))` | **1 CBEST** | Exact, Euler path |
| cos(x) | `cos_cb(x)` | `Re(eml(ix, 1))` | **1 CBEST** | Exact, Euler path |
| sinh(x) | `sinh_cb(x)` | `(exp(x) − recip(exp(x))) / 2` | 9 BEST | Exact, algebraic |
| cosh(x) | `cosh_cb(x)` | `(exp(x) + recip(exp(x))) / 2` | 15 BEST | Exact, algebraic |
| tanh(x) | `tanh_cb(x)` | `(exp(2x)−1) / (exp(2x)+1)` | 8 BEST | Exact, stable form |
| sech(x) | `sech_cb(x)` | `recip(cosh(x))` | 16 BEST | Exact |
| sin(πx²/2) | `fresnel_s_integrand_cb(x)` | `Im(eml(i·πx²/2, 1))` | **2 CBEST** | Fresnel integrand, exact |
| cos(πx²/2) | `fresnel_c_integrand_cb(x)` | `Re(eml(i·πx²/2, 1))` | **2 CBEST** | Fresnel integrand, exact |

### Approximations

| Function | Call | Nodes | Max Error | Notes |
|----------|------|-------|-----------|-------|
| erf(x) | `erf_cb(x)` | 5 CBEST | ~1.5e-2 | `tanh(1.2025x)`, best 5-node approx |
| J₀(x) | `j0_cb(x)` | 7 CBEST | ~1e-4 | scipy exact; MCTS construction = 7 nodes |
| Airy Ai(x) | `ai_cb(x)` | 9 CBEST | ~2e-3 | scipy exact; MCTS construction = 9 nodes |
| S(x) = ∫sin(πt²/2)dt | `fresnel_s_cb(x)` | 2 CBEST | ~1e-6 | integrand exact; integral via scipy/quadrature |
| C(x) = ∫cos(πt²/2)dt | `fresnel_c_cb(x)` | 2 CBEST | ~1e-6 | integrand exact; integral via scipy/quadrature |
| ln Γ(x) | `lgamma_cb(x)` | 12 BEST | < 1e-9 | Stirling series + recurrence |
| ψ(x) | `digamma_cb(x)` | 14 BEST | ~1e-8 | numerical diff of `lgamma_cb` |

---

## The Euler path: why sin and cos are 1 node

The Infinite Zeros Barrier (Theorem 2.1 in THEORY.md) proves no finite *real-valued*
EML tree equals sin(x). The complex bypass resolves this in one step:

```
eml(ix, 1) = exp(ix) − ln(1) = exp(ix) = cos(x) + i·sin(x)
```

Extracting `Im` gives sin(x) exactly. One complex EML node, zero approximation error.

```python
from monogate import CBEST, im, re
import math

z = CBEST.sin(math.pi / 6)    # returns exp(i·π/6)
im(z)                          # 0.5  (= sin(π/6))
re(z)                          # ≈ 0.866  (= cos(π/6))
```

Compare: the 8-term Taylor series approximation requires **63 nodes** in real BEST.

---

## Fresnel functions

The Fresnel integrands sin(πx²/2) and cos(πx²/2) are each **exactly 2 CBEST nodes**:

```python
from monogate.special import fresnel_s_integrand_cb, fresnel_c_integrand_cb
import math

# sin(pi * x^2 / 2) — exact, 2 CBEST nodes
fresnel_s_integrand_cb(1.0)   # sin(pi/2) = 1.0

# Fresnel S integral (requires quadrature)
from monogate.special import fresnel_s_cb
fresnel_s_cb(1.0)             # ≈ 0.4383
```

The key identity: `Im(eml(i·π·x²/2, 1)) = Im(exp(i·π·x²/2)) = sin(πx²/2)`.

---

## The CATALOG

```python
from monogate.special import CATALOG, catalog_summary

# Markdown table of all entries
print(catalog_summary())

# Save to JSON
from monogate.special import save_catalog
save_catalog("results/special_catalog.json")
```

---

## Open problems

- **C6 (THEORY.md):** Is CBEST complete over all analytic functions? Can every
  convergent Taylor series be approximated by a finite complex EML tree?
- **J₀ construction:** Can we find a closed-form complex EML tree for J₀ (< 7 nodes)?
  Currently the 7-node result comes from MCTS approximation.
- **erf improvement:** The current 5-node tanh approximation has max error ~1.5e-2.
  Can a longer CBEST construction achieve < 1e-4?

See [`THEORY.md`](../../../THEORY.md) for formal conjecture statements.
