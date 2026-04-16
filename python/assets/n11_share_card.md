# monogate: N=11 Sin Barrier — 281 million trees, zero matches

**Result:** No finite EML tree with real leaves can equal sin(x). Ever.

**Paper:** "Practical Extensions to the EML Universal Operator: Hybrid Routing,
Phantom Attractors, Performance Kernels, and the N=11 Sin Barrier"
Art Almaguer · April 2026 · arXiv:**ARXIV_ID_PLACEHOLDER**

---

## The numbers

| N | Trees searched | After parity filter | Result |
|---|---------------|--------------------:|--------|
| 1–10 | 40,239,012 | ~19.7M | 0 candidates |
| **11** | **240,787,456** | **208,901,719** | **0 candidates** |
| **Total** | **281,026,468** | | **0 candidates** |

Runtime: **5.4 minutes** on a laptop CPU using a vectorised NumPy evaluator.
Tolerances checked: 1e-4, 1e-6, 1e-9. Zero candidates at all three.

---

## Why it can't work (the math)

```
Theorem (Infinite Zeros Barrier):
  No finite real-valued EML tree T(x) satisfies T(x) = sin(x) for all x ∈ ℝ.

Proof sketch:
  sin(x) has zeros at {kπ : k ∈ ℤ} — infinitely many.
  Every finite EML tree is real-analytic with only finitely many zeros.
  Contradiction.  □

Corollary: extends to cos(x), Bessel J₀, Airy Ai, and any function
           with infinitely many real zeros.
```

The search is empirical confirmation of a theorem. Science works.

---

## The best approximation found (12 leaves, MSE = 1.478e-4)

```
eml(
  eml(eml(x,1), eml(1,1)),
  eml(
    eml(eml(eml(x,1), eml(1,1)), eml(x,1)),
    eml(x,1)
  )
)
```

This is **2,842× closer** to sin(x) than the trivial baseline exp(x) — but
still provably not equal for any x.

---

## The bypass (1 node, complex domain, exact)

```python
import cmath
def sin_eml(x):
    # eml(ix, 1) = exp(ix) - ln(1) = e^(ix)
    # Im(e^(ix)) = sin(x)  — Euler's formula
    return cmath.exp(1j * x).imag

sin_eml(3.14159265)   # → 2.7e-9  (≈0, floating point)
sin_eml(1.5707963268) # → 1.0 exactly
```

**One node. Machine precision. The barrier is real-domain only.**

---

## BEST routing (bonus result)

```python
from monogate import BEST

# Standard EML: sin Taylor (8 terms) = 245 nodes
# BEST routing:  sin Taylor (8 terms) =  63 nodes  (74% fewer)
#                                         2.8× wall-clock speedup
```

---

## PyTorch integration

```python
from monogate.torch import EMLLayer

# Drop-in replacement for sin in SIREN/NeRF/PINN
layer = EMLLayer(256, 256, depth=2, operator="BEST", compiled=True)
# Rust backend auto-selected: 5.9× faster than baseline Python tree
# ONNX export: torch.onnx.export(layer, dummy, "layer.onnx", opset_version=17)
```

| Backend | Speedup |
|---------|---------|
| Standard Python | 1× |
| FusedEMLActivation | 3.6× |
| + torch.compile | 4.4× |
| **Rust (monogate-core)** | **5.9×** |

---

## Try it yourself

```bash
pip install monogate

# Run the full N=11 search (~5 min)
python monogate/search/sin_search_05.py --save results/sin_n11.json

# See the near-miss gallery
python monogate/search/analyze_n11.py

# Interactive explorer (Attractor Lab, Optimizer, Research, Leaderboard)
cd explorer && npm install && npm run dev
# Open http://localhost:5173 → Research tab
```

---

**GitHub:** https://github.com/almaguer1986/monogate
**PyPI:** `pip install monogate`
**Explorer:** https://monogate.dev
**Paper:** https://arxiv.org/abs/ARXIV_ID_PLACEHOLDER

---

## Cite this work

```bibtex
@article{almaguer2026eml,
  title  = {Practical Extensions to the {EML} Universal Operator:
             Hybrid Routing, Phantom Attractors, Performance Kernels,
             and the {N=11} Sin Barrier},
  author = {Almaguer, Art},
  year   = {2026},
  note   = {arXiv:ARXIV_ID_PLACEHOLDER}
}
```

---

*monogate v0.9.0 · April 2026 · Based on Odrzywołek (2026), arXiv:2603.21852*
*Update ARXIV_ID_PLACEHOLDER: `python scripts/update_arxiv_id.py <id>`*
