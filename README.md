# monogate

**`eml(x, y) = exp(x) − ln(y)`** — one binary operator that generates every elementary function as a finite expression tree. In v1.1, that same substrate powers a **neurosymbolic theorem prover** that discovers and certifies new mathematical identities.

Based on [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) (Odrzywołek, 2026).  
Paper: **[arXiv:ARXIV_ID_PLACEHOLDER](https://arxiv.org/abs/ARXIV_ID_PLACEHOLDER)** · Live explorer: **[monogate.dev](https://monogate.dev)** · [![PyPI](https://img.shields.io/pypi/v/monogate)](https://pypi.org/project/monogate/) · [![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://monogate.streamlit.app)

```bash
pip install monogate          # core — no dependencies
pip install "monogate[sympy]" # + prover (recommended)
```

---

## Neurosymbolic Prover  ✦ new in v1.1

monogate now includes a four-tier theorem prover that can prove — or find
counterexamples to — any single-variable mathematical identity. The prover
combines exact SymPy simplification, interval arithmetic certification, MCTS
witness search, and an online-learning neural scorer that improves with each
proof it completes.

```python
from monogate.prover import EMLProverV2

p = EMLProverV2(enable_learning=True)

# Tier 2: exact SymPy proof
r = p.prove("sin(x)**2 + cos(x)**2 == 1")
print(r.status, r.confidence)   # proved_exact  1.0

# Tier 2: Euler identity
r = p.prove("exp(x + y) == exp(x) * exp(y)")
print(r.status)   # proved_exact

# Tier 4: EML witness search (MCTS finds a tree that matches numerically)
r = p.prove("cosh(x)**2 - sinh(x)**2 == 1")
print(r.status, r.node_count)   # proved_witness  7

# Neural scorer updates automatically after each witness proof
p.scorer.save("scorer.json")   # checkpoint learned weights
```

**Generate new conjectures:**

```python
candidates = p.generate_conjectures(n=20, depth=3, min_confidence=0.7)
for c in candidates:
    print(f"{c.expression:50s}  conf={c.confidence:.2f}")
```

**Interactive proof visualization** (Plotly HTML, one click):

```python
result = p.prove("sin(x)**2 + cos(x)**2 == 1")
fig = p.visualize_proof_interactive(result, output_path="proof.html")
```

The interactive tree shows each EML node colored by role (operator / constant / variable),
with hover text displaying the sub-formula at every node.

**Batch proving and compression:**

```python
from monogate.identities import TRIG_IDENTITIES

report = p.batch_prove(TRIG_IDENTITIES)
print(f"proved {report.proved_rate:.0%} of trig identities")

# Shrink a witness proof tree
compressed = p.compress_proof(result)
print(f"{result.node_count} → {compressed.node_count} nodes")
```

**Try the showcase notebook:**
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/almaguer1986/monogate/blob/master/python/notebooks/prover_showcase.ipynb)

---

## Quick start — function approximation

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

**Interactive web demo (Streamlit):** [![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://monogate.streamlit.app) — Optimizer · Special Functions · PINN Demo · MCTS Explorer · Phantom Attractor

Run locally:
```bash
pip install -r requirements-streamlit.txt
streamlit run streamlit_app.py
```

---

## Identity catalog

v1.1 ships with **151 proved identities** across six categories:

| Category | Count | Examples |
|----------|------:|---------|
| Trigonometric | 32 | Pythagorean, double-angle, Chebyshev T5/T6, triple-product |
| Hyperbolic | 25 | Pythagorean, inverse-trig connections, Gudermann |
| Exponential | 18 | Addition, shift, ln-exp compositions |
| Special functions | 25 | erf, Bessel J0/J1, Airy Ai, digamma recurrence |
| Physics | 17 | Schrödinger free, KdV soliton, Boltzmann, Planck |
| Open conjectures | 21 | EML structure conjectures under active investigation |

```python
from monogate.identities import ALL_IDENTITIES, get_by_category, get_by_difficulty

print(len(ALL_IDENTITIES))                    # 151
hard = get_by_difficulty("hard")              # curated hard targets
physics = get_by_category("physics")          # 17 physics equations
```

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

## What's new in v1.1.0

- **Neurosymbolic prover** (`EMLProver`, `EMLProverV2`) — four-tier pipeline
- **Neural scorer** (`FeatureBasedEMLScorer`) — online MLP, numpy inference, torch training
- **Conjecture generation** — auto-generate and filter candidate identities
- **Proof compression** — minimax tree reduction on witness proofs
- **Interactive Plotly visualization** — `visualize_proof_interactive()`
- **Identity catalog** — 120 → 151 identities
- **1184 tests**, 0 failed

Full details: [`python/CHANGELOG.md`](python/CHANGELOG.md)

---

## What's new in v1.0.0

**Five new research modules** — minimax approximation, CBEST physics survey,
sklearn-compatible `EMLRegressor`, p-adic EML arithmetic, chemistry reaction
catalogs, causal EML models. **THEORY.md** canonical formal reference.
983 tests.

---

## The sin(x) barrier

**Theorem (Infinite Zeros Barrier):** No finite real-valued EML tree with terminals `{1, x}` equals sin(x) for all x ∈ ℝ.

**Proof:** Every EML tree is real-analytic → finitely many zeros. sin has zeros at {kπ : k ∈ ℤ}. Contradiction.

**Empirical confirmation:** 208,901,719 trees evaluated (N ≤ 11, ~5 min on one CPU core). Best near-miss MSE: 1.478e-4.

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

monogate is the right tool when your workload:
- Does **symbolic regression** or interpretable expression search
- Needs **theorem proving** or **conjecture generation** over single-variable identities
- Is dominated by `pow`, `ln`, `mul`, or `div` (all save ≥6 nodes each)
- Uses sin/cos activations (NeRF, SIREN, Fourier features, physics ML)
- Needs human-readable formula output from a differentiable tree

**monogate is not a PyTorch inference accelerator.** Native `torch.sin` is ~9,000× faster than any EML variant. The EML substrate computes in Python scalars. It is the right tool for symbolic analysis, formula construction, interpretable regression, and mathematical research.

---

## Install

```bash
pip install monogate                # core — no dependencies
pip install "monogate[sympy]"       # + prover (SymPy exact tier)
pip install "monogate[torch]"       # + EMLTree, EMLNetwork, HybridNetwork
pip install "monogate[llm]"         # + LLM-guided optimizer
```

**JavaScript / Node:**
```bash
npm install monogate
```

---

## Repository structure

```
monogate/
├── python/          # pip install monogate
│   ├── monogate/    # core library
│   ├── tests/       # 1184 tests
│   ├── notebooks/   # tutorials + prover_showcase.ipynb
│   └── docs/        # MkDocs site
├── lib/             # npm install monogate  — JS/Node library
├── explorer/        # monogate.dev          — Vite/React browser app
├── THEORY.md        # formal theorem/conjecture reference
├── Makefile         # make reproduce-all, make test, make docker-run
└── Dockerfile       # clean-room reproducibility environment
```

## License

MIT. The underlying mathematics is CC BY 4.0 per the original paper.
