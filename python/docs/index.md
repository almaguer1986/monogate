# monogate

**All elementary functions from one binary gate.**

```
eml(x, y) = exp(x) − ln(y)
```

monogate shows that every elementary arithmetic function — exponential, logarithm, addition, multiplication, division, power, sine, cosine, and more — can be expressed as a pure expression tree built from a single binary operator and the constant `1`.

The **BEST** router then dispatches each primitive to the cheapest operator family (EML, EDL, or EXL), achieving up to **74% node reduction** for sin/cos and **52% average** across common functions.

**v0.5.0** adds:

- `EMLLayer` / `EMLActivation` — differentiable PyTorch layers with EML activation
- `monogate.search` — MCTS and Beam Search over the EML grammar
- `monogate.complex_eval` — Euler-path constructions: `Im(eml(ix, 1)) = sin(x)` exactly
- N=10 exhaustive search (40,239,012 trees) confirming no real-valued EML tree equals sin

---

## Quick start

```bash
pip install monogate            # pure Python, no dependencies
pip install "monogate[torch]"   # + PyTorch integration
```

```python
import monogate

# Node count for sin (8-term Taylor)
result = monogate.optimize("sin")
print(result.eml_nodes)   # 245
print(result.best_nodes)  # 63  (74% savings with BEST routing)

# Exact sin(x) via Euler path — one EML node in the complex domain
from monogate import sin_via_euler
import math
print(abs(sin_via_euler(math.pi / 6) - 0.5))   # < 1e-15
```

```python
# PyTorch: replace sin activation in SIREN with learnable EML layer
from monogate.torch import EMLLayer
import torch

layer = EMLLayer(256, 256, depth=2, operator="EML")
x = torch.randn(8, 256)
y = layer(x)   # (8, 256)
```

---

## Key findings

| Finding | Details |
|---------|---------|
| **EML completeness** | Every elementary function is an exact EML tree |
| **BEST routing** | 52% average / 74% sin-cos node savings |
| **Phantom attractor** | depth=3 EMLTree converges to 3.1696 (not pi) at λ=0 |
| **Phase transition** | λ_crit = 0.001 separates attractor from pi convergence |
| **Exhaustive search** | 40M trees searched (N ≤ 10), zero real EML trees equal sin |
| **Infinite Zeros Barrier** | Theorem: no finite real EML tree can equal sin (infinitely many zeros) |
| **Euler bypass** | Im(eml(ix, 1)) = sin(x) exactly — complex domain breaks the barrier |

---

## Live Explorer

Try the [**monogate.dev**](https://monogate.dev) interactive explorer — paste any expression and see instant BEST optimization with node savings.

---

## Reference

Based on [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) (Odrzywołek, 2026), CC BY 4.0.
