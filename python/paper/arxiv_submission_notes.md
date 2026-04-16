# arXiv Submission Notes — monogate v0.11.0

---

## Final Abstract (≤ 250 words)

```
We present monogate, a library and formal framework built on the EML operator
eml(x,y) = exp(x) − ln(y). From this single binary gate and the constant 1,
every elementary function is an exact finite expression tree (Odrzywołek, 2026).

Our main theoretical contribution is the Infinite Zeros Barrier (Theorem 1):
no finite real-valued EML tree with terminals {1, x} equals sin(x) for all
x ∈ R. The proof follows from real-analyticity — every EML tree has at most
finitely many zeros, while sin has zeros at {kπ : k ∈ Z}. We confirm
empirically by exhaustively evaluating 208,901,719 trees up to N=11 internal
nodes (zero candidates at tolerances 1e-4 through 1e-9; best near-miss MSE
1.478e-4, runtime ~5 minutes on a single CPU core).

The complex bypass is exact in one node: Im(eml(ix,1)) = Im(exp(ix)) = sin(x).
We formalise this into Complex BEST routing (CBEST), which dispatches
EML/EDL/EXL operators in C via cmath, reducing sin and cos from 63 nodes to
1 each. Complex MCTS search over terminals {1, x, ix, i} finds near-exact
constructions for Bessel J0, erf, and Airy Ai.

We introduce Physics-Informed EML Networks (EMLPINN): interpretable neural
networks that simultaneously fit data and satisfy a differential equation via
autograd-computed residuals. After training, the model emits a symbolic EML
formula — a readable approximate solution to the ODE.

We also provide BEST hybrid routing (52% node reduction over all-EML), a
formal conjecture index (C1–C7 in THEORY.md), and full reproducibility
infrastructure (Dockerfile, Makefile, scripts/reproduce_n11.py — all 12/12
N=11 claims independently verified).

Code: https://github.com/almaguer1986/monogate
```

Word count: ~230

---

## arXiv Upload Instructions

### Categories
- **Primary:** cs.SC (Symbolic Computation)
- **Cross-list:** cs.LG (Machine Learning), math.CA (Classical Analysis and ODEs)

### Keywords (MSC / ACM)
```
EML operator, symbolic regression, expression trees, universal approximation,
BEST routing, complex exponential, Euler identity, physics-informed neural networks,
MCTS symbolic search, phantom attractor, interpretable ML
```

### License
- **CC BY 4.0** (matches the underlying Odrzywołek 2026 paper)

### Files to upload
```
preprint.tex            ← main source
paper/figures/          ← all .pdf and .eps figures
```

Do NOT upload:
- `*.py` source files (link to GitHub instead)
- `*.json` result files
- `Dockerfile` / `Makefile`

The abstract, introduction, and conclusion must be self-contained without
the supplementary code — arXiv readers should be able to read the PDF without
cloning the repo.

### arXiv metadata
```
Title:   monogate: Universal Expression Trees from a Single Binary Operator
Authors: [your name]
Comments: 25 pages, 7 figures, 3 tables. Code: https://github.com/almaguer1986/monogate
Report-No: (leave blank)
```

---

## Submission Checklist

### Pre-submission
- [ ] All figures regenerated from source: `python experiments/plot_attractor_landscape.py`
- [ ] Preprint compiled twice (cross-refs): `cd paper && pdflatex preprint.tex && pdflatex preprint.tex`
- [ ] `make reproduce-n11` passes — 12/12 claims verified
- [ ] `make test` passes — 662 passed, 8 skipped
- [ ] `python scripts/release_v0.11.0.py` passes — all readiness checks green
- [ ] Version is 0.11.0 in both `monogate/__init__.py` and `pyproject.toml`
- [ ] Abstract word count ≤ 250
- [ ] All `ARXIV_ID_PLACEHOLDER` tokens still in source (replace AFTER submission)

### Submission
- [ ] Upload `preprint.tex` + `paper/figures/` to arXiv
- [ ] Primary category: cs.SC; cross-list: cs.LG, math.CA
- [ ] License: CC BY 4.0
- [ ] Embargo: None (immediate)

### Post-submission (once arXiv ID is assigned)
- [ ] Run: `python scripts/update_arxiv_id.py 2604.XXXXX`
  - Updates README.md, ANNOUNCEMENT.md, preprint.tex, explorer components
- [ ] Tag release: `git tag v0.11.0 && git push origin v0.11.0`
- [ ] Publish to PyPI: `python -m build && twine upload dist/*`
- [ ] Post ANNOUNCEMENT.md content to HN, r/MachineLearning, r/math, X, LinkedIn
- [ ] Update monogate.dev arXiv link

---

## Phase history

### v0.9.0 — arXiv:2603.21852
Initial submission. Core EML theory, BEST routing, Infinite Zeros Barrier,
N=11 exhaustive search, phantom attractor study, SIREN/NeRF benchmarks.

### v0.10.0 (revision or companion note)
Complex BEST routing (CBEST) — sin/cos at 1 node via Euler path.
Complex MCTS for J₀, erf, Airy Ai. Physics-Informed EML Networks (EMLPINN).
Minimax and GPU search extensions. 69 new tests.

### v0.11.0 (current)
THEORY.md formal conjecture index (C1–C7). §"Formal Statements" in preprint.
Full reproducibility infrastructure. 662 tests. Version: 0.11.0.
