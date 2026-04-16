# Complex Bypass — Exact sin(x) in One Node

## The barrier

Every finite *real-valued* EML tree is real-analytic on its domain, so it has finitely many zeros. But `sin(x)` has infinitely many zeros (one at every `nπ`). Therefore:

> **No finite real EML tree can represent sin(x) exactly.**

This was proved algebraically and confirmed by exhaustive search over all 281 million+ real EML trees up to N=11 nodes.

## The bypass

The barrier is *real-domain only*. One complex EML node is sufficient:

```
eml(i·x, 1) = exp(i·x) − ln(1) = exp(ix)
```

By Euler's formula: `Im(exp(ix)) = sin(x)` exactly for all x ∈ R.

**sin(x) requires 1 complex EML node — it cannot be done with any number of real nodes.**

## Implementation

```python
from monogate import sin_via_euler, cos_via_euler
import math

sin_via_euler(math.pi / 6)     # 0.5 (exact)
cos_via_euler(math.pi / 3)     # 0.5 (exact)

# Or via the CBEST complex operator
from monogate.complex_best import CBEST, im, re
from monogate.special import sin_cb, cos_cb

sin_cb(math.pi / 4)            # 0.7071... (exact, 1 node)
cos_cb(math.pi / 4)            # 0.7071... (exact, 1 node)
```

## CBEST — Complex BEST

CBEST extends BEST routing to the complex domain. Complex EML nodes evaluate:

```
eml(z, w) = exp(z) − ln(w)   for z, w ∈ C
```

Using the complex branch and projecting back to real:

```python
from monogate.complex_best import CBEST

# exp(iz) path
z = complex(0, math.pi / 2)   # i·π/2
result = CBEST.eml(z, 1)       # exp(iπ/2) = i
print(result.imag)             # 1.0 = sin(π/2)
```

## Special functions catalog

The complex bypass enables exact 1-node representations for:

| Function | Nodes | Construction |
|----------|-------|-------------|
| `sin(x)` | 1 | `Im(exp(ix))` |
| `cos(x)` | 1 | `Re(exp(ix))` |
| `sinh(x)` | 1 | `Im(exp(-ix))·(-1)` via sinh identity |
| `cosh(x)` | 1 | `Re(exp(-ix))` |

And short approximations (via MCTS) for:

| Function | Nodes | Max error |
|----------|-------|---------|
| `erf(x)` | 5 | ~10⁻³ |
| `J₀(x)` | 7 | ~10⁻³ |
| `Ai(x)` | 9 | ~10⁻³ |

See `monogate.special.CATALOG` for the full catalog.

## Physics applications

The complex bypass also gives compact representations for PDE solutions:

```python
from monogate.physics import schrodinger_free_cb, wave_cos_cb

# Free particle: exp(ikx) is exactly 1 CBEST node
psi = schrodinger_free_cb(x=1.0, k=2.0)   # complex exp(2ix)

# Wave equation: cos(kx-ωt) is 1 CBEST node
u = wave_cos_cb(x=1.0, k=2.0, omega=3.0, t=0.5)
```

## See also

- `monogate.special` — precomputed catalog (15 functions)
- `monogate.physics` — PDE solution catalog
- `monogate.complex_best.CBEST` — complex BEST operator
- `research/exhaustive_search.md` — N=11 proof
- `THEORY.md` R2 (barrier), R3 (bypass)
