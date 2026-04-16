# monogate

**`eml(x, y) = exp(x) − ln(y)`** — a single binary operator that generates every elementary function as a finite expression tree.

From this one gate and the constant `1`: exp, ln, sqrt, pow, div, mul, sin (complex), GELU, tanh — all exact, no look-up tables. BEST routing then dispatches each primitive to whichever of three operator families (EML, EDL, EXL) uses the fewest nodes.

Based on [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) (Odrzywołek, 2026).  
Paper: **[arXiv:ARXIV_ID_PLACEHOLDER](https://arxiv.org/abs/ARXIV_ID_PLACEHOLDER)** · Live explorer: **[monogate.dev](https://monogate.dev)** · [![PyPI](https://img.shields.io/pypi/v/monogate)](https://pypi.org/project/monogate/)

```bash
pip install monogate==0.11.0
```

---

## Quick start

```python
from monogate import BEST, best_optimize, CBEST, im

# BEST routing — cheapest gate per operation
BEST.pow(2.0, 10.0)   # 1024.0  (EXL, 3 nodes vs 15)
BEST.div(6.0, 2.0)    # 3.0     (EDL, 1 node  vs 15)
BEST.ln(2.718)        # ~1.0    (EXL, 1 node  vs  3)

# Complex BEST — sin and cos in 1 node via Euler path
import math
im(CBEST.sin(math.pi / 6))   # 0.5  (= sin(π/6), exact)

# Code optimizer — rewrite any Python/NumPy/PyTorch expression
r = best_optimize("torch.sin(x)**2 + torch.cos(x) * x**3")
print(r.rewritten_code)   # 72% fewer nodes
```

**Try it now in Colab:** [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/almaguer1986/monogate/blob/master/python/notebooks/colab_demo.ipynb)

---

## For Researchers

**Theory and open problems:** [`THEORY.md`](THEORY.md) — formal definitions, proven theorems, seven open conjectures (C1–C7), and a structured research roadmap. **Start here** if you want to build on the EML framework.

**Tractable entry points:**
- **C1** — EDL additive incompleteness: a clean structural proof is missing
- **C3** — The phantom attractor at ~3.1696: what is this value in closed form?
- **C5** — N=12 sin search: GPU MCTS is already implemented, needs a run

Pull requests solving any open problem are welcome. Crack one and it's publishable.

**Reproduce the paper results:**
```bash
git clone https://github.com/almaguer1986/monogate
cd monogate
make reproduce-n11    # verify N=11 exhaustive search (~30s from cache)
make reproduce-all    # full readiness check
make paper            # compile preprint.tex (requires TeX Live)
```

**Docker (clean-room, no local install):**
```bash
make docker-build
make docker-run       # runs reproduce-all inside container
```

**Cite:**
```bibtex
@misc{monogate2026,
  title  = {monogate: Universal Expression Trees from a Single Binary Operator},
  author = {[Author]},
  year   = {2026},
  eprint = {ARXIV_ID_PLACEHOLDER},
  archivePrefix = {arXiv},
}
```

---

## What's new in v0.11.0

**THEORY.md** — canonical formal theory reference: proven theorem index, open conjecture statements (C1–C7), research roadmap (T1–T7). See [`THEORY.md`](THEORY.md).

**Reproducibility infrastructure:**
```bash
make reproduce-all     # verifies every paper claim end-to-end
make docker-run        # fully isolated clean-room run
python python/scripts/reproduce_n11.py   # 12/12 N=11 claims verified
```

**Full test suite:** 662 tests, 8 skipped (CUDA-only paths).

---

## What's new in v0.10.0

**Complex BEST routing (CBEST)** — sin and cos at 1 node each via the Euler path `Im(eml(ix,1)) = sin x`:

```python
from monogate import CBEST, im
im(CBEST.sin(1.0))   # 0.8414709848  (= math.sin(1.0), exact, 1 node)
```

Real BEST requires 63 nodes for an 8-term Taylor series. CBEST: 1.

**Physics-Informed EML Networks (EMLPINN):**

```python
import torch, math
from monogate import EMLPINN, fit_pinn

model = EMLPINN(equation='harmonic', omega=2.0)
x = torch.linspace(0, math.pi, 50).unsqueeze(1)
y = torch.sin(2.0 * x.squeeze(1))
result = fit_pinn(model, x, y, x_phys=x, steps=500)
print(result.formula)   # symbolic EML approximate ODE solution
```

Also: `mcts_search(..., objective='minimax')` for Chebyshev bounds; `gpu_mcts_search(device='cuda')`.

---

## The sin(x) barrier

**Theorem (Infinite Zeros Barrier):** No finite real-valued EML tree with terminals `{1, x}` equals sin(x) for all x ∈ ℝ.

**Proof:** Every EML tree is real-analytic → finitely many zeros. sin has zeros at {kπ : k ∈ ℤ}. Contradiction.

**Empirical confirmation:** 208,901,719 trees evaluated (N ≤ 11, ~5 min on one CPU core). Zero candidates at tolerances 1e-4, 1e-6, 1e-9. Best near-miss MSE: 1.478e-4.

**Complex bypass (1 node, exact):** `Im(eml(ix, 1)) = Im(exp(ix)) = sin(x)`.

---

## BEST routing table

| Operation | BEST family | BEST nodes | EML baseline | Saving |
|-----------|-------------|-----------|--------------|--------|
| pow | EXL | 3 | 15 | −12 |
| div | EDL | 1 | 15 | −14 |
| mul | EDL | 7 | 13 | −6 |
| ln  | EXL | 1 |  3 | −2 |
| recip | EDL | 2 | 5 | −3 |
| neg | EDL | 6 | 9 | −3 |
| sub | EML | 5 | 5 | — |
| add | EML | 11 | 11 | — |

Total: **37 nodes** (BEST) vs 77 (all-EML) — **52% fewer.**

---

## When to use it

BEST routing pays off when your workload:
- Does symbolic regression or interpretable expression search
- Is dominated by `pow`, `ln`, `mul`, or `div` (all save ≥6 nodes each)
- Uses sin/cos activations (NeRF, SIREN, Fourier features, physics ML)
- Needs human-readable formula output from a differentiable tree

**monogate is not a PyTorch inference accelerator.** Native `torch.sin` is ~9,000× faster than any EML variant. The EML substrate computes in Python scalars via `math.exp` / `math.log`. It is the right tool for symbolic analysis, formula construction, interpretable regression, and research into operator families.

---

## Install

```bash
pip install monogate                # core only, no dependencies
pip install "monogate[torch]"       # + PyTorch ops, EMLTree, EMLNetwork, HybridNetwork
```

**JavaScript / Node:**
```bash
npm install monogate                # EML, EDL, EXL, BEST, sin_best, cos_best
```

---

## Explorer (monogate.dev)

| Tab | What it shows |
|-----|---------------|
| **✦ viz** | Expression tree for any math input — nodes colored by EML / EDL / EXL routing |
| **sin↗** | sin(x) Taylor accuracy chart; BEST vs EML node count at every precision level |
| **⚡ demo** | Live JS GELU FFN timing + Python benchmark numbers |
| **Calc** | Evaluate any expression in BEST / EML / EXL / EDL mode with node breakdown |
| **Opt** | Paste Python/NumPy/PyTorch code → BEST-rewritten version + savings estimate |
| **Board** | Challenge leaderboard — open problems in EML construction |

---

## Repository structure

```
monogate/
├── python/          # pip install monogate  — core, torch_ops, network, optimize
├── lib/             # npm install monogate  — JS/Node library
├── explorer/        # monogate.dev          — Vite/React browser app
├── api/             # Python FastAPI server — powers Opt tab in local mode
├── THEORY.md        # formal theorem/conjecture reference
├── Makefile         # make reproduce-all, make test, make docker-run
└── Dockerfile       # clean-room reproducibility environment
```

## License

MIT. The underlying mathematics is CC BY 4.0 per the original paper.
