# monogate

**`eml(x, y) = exp(x) − ln(y)`** — one binary operator. Open problem: can sin(x) be constructed from it?

Based on [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) (Odrzywołek, 2026).  
Challenge board: **[monogate.dev](https://monogate.dev)** · [![PyPI](https://img.shields.io/pypi/v/monogate)](https://pypi.org/project/monogate/) · [![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://monogate.streamlit.app)

```bash
pip install monogate          # core — no dependencies
pip install "monogate[sympy]" # + symbolic simplification
```

---

## Quick start — expression construction

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

## For Researchers

**Challenge board:** [monogate.dev](https://monogate.dev) — submit a construction for sin, cos, π, or i. Get credited permanently.

**Theorem catalog:** [monogate.dev/theorems](https://monogate.dev/theorems) — every result labeled honestly: theorem, conjecture, observation, or speculation.

**Open problems:**
- Construct sin(x) from eml(x,y) using only grammar terminals {1, x}
- Construct i (the imaginary unit) from terminal {1} alone
- Prove or disprove: the EML depth hierarchy has no level 4

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

## Research Notes

Detailed working documents, raw session logs, and full research context are
maintained in a private repository for cleanliness and strategic reasons.

Public artifacts in this repo include:
- **`python/paper/preprint.tex`** — the authoritative arXiv preprint
- **`python/notebooks/`** — clean, reproducible session benchmarks
- **`python/results/`** — benchmark outputs and figures
- **`python/monogate/`** — the full Python library
- **`capability_card.json`** — machine-readable capability profile

## License

MIT. The underlying mathematics is CC BY 4.0 per the original paper.
