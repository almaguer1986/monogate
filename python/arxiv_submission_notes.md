# arXiv Submission Notes — monogate EML Extensions

## Suggested title

```
Practical Extensions to the EML Universal Operator:
Hybrid Routing, Phantom Attractors, Performance Kernels,
and the N=11 Sin Barrier
```

## Abstract (for arXiv submission form — ≤ 250 words)

```
Odrzywołek (2026) showed that the binary operator eml(x,y) = exp(x) - ln(y),
with constant 1, generates every elementary function as a finite binary tree of
identical nodes. We report five independent extensions developed while building
monogate v0.8.0 (641 passing tests, PyPI-installable):

(1) BEST hybrid routing selects among EML, EDL (exp/ln), and EXL (exp*ln) per
operation, cutting node count by 52% on average and 74% for Taylor-series
sin/cos, with 2.8x wall-clock speedup.

(2) Phantom attractors: gradient training of depth-3 EML trees to pi converges
to a wrong fixed point (~3.1696) in 40/40 seeds (lambda=0). A tiny L1 penalty
lambda_crit = 0.001 induces a sharp phase transition to 40/40 correct.

(3) The Infinite Zeros Barrier: no finite real-valued EML tree equals sin(x).
Proof: sin has infinitely many zeros; every finite EML tree is real-analytic
with finitely many zeros. Contradiction. Supported by exhaustive search of
281,026,468 trees (N <= 11 internal nodes), zero candidates at tolerances
from 1e-4 to 1e-9. The complex bypass Im(eml(ix,1)) = sin(x) recovers the
function exactly in one node.

(4) Performance kernels: a fused vectorized Python kernel (FusedEMLActivation,
3.6x speedup) and a Rust/PyO3 compiled extension (monogate-core, 5.9x speedup)
make EML competitive with native activations.

(5) EMLLayer: a drop-in nn.Module for SIREN, NeRF, and PINN activation
replacement, with ONNX export (opset 17), torch.compile support, and full
state_dict() serialization.

Source code, data, and interactive explorer: github.com/almaguer1986/monogate
```

## arXiv categories

- **Primary:** `cs.SC` — Symbolic Computation
- **Secondary 1:** `cs.LG` — Machine Learning
- **Secondary 2:** `math.NA` — Numerical Analysis  
  *(alternative: `math.OC` for Optimization and Control — choose based on emphasis)*

## Keywords (for MSC / arXiv metadata)

```
symbolic computation, elementary functions, expression trees, operator routing,
phantom attractors, gradient descent, exhaustive search, neural network activation,
PyTorch, Rust, performance kernels, SIREN, implicit neural representations
```

## Submission checklist

- [ ] Run `pdflatex preprint.tex` twice — zero errors, zero undefined references
- [ ] Abstract word count ≤ 250 (form field limit)
- [ ] Author name and email correct in `\author{}`
- [ ] ORCID registered? Add to author block if so:
      `\orcid{0000-0000-0000-0000}` (requires `orcidlink` package — optional)
- [ ] Figures: replace `\fbox{...screenshot...}` with actual figure PDF/PNG before submission
  - Generate: run explorer, screenshot AttractorViz tab, save as `paper/figures/attractor.pdf`
  - Then: `\includegraphics[width=0.9\linewidth]{figures/attractor}` in `preprint.tex`
- [ ] License: arXiv default is CC BY 4.0 — check "I grant arXiv a non-exclusive license"
- [ ] Ancillary files: upload `results/sin_n11.json` in the `anc/` folder inside the .tar.gz
- [ ] Supplementary note: add to end of paper or ancillary a note pointing to the GitHub
      for full reproduction instructions
- [ ] After submission: record arXiv ID (e.g. 2604.XXXXX) and update:
  - `README.md`: replace `[arXiv — link pending]` with actual link
  - `assets/n11_share_card.md`: replace `ARXIV_ID_PLACEHOLDER`
  - `explorer/src/components/ResearchTab.jsx`: replace `ARXIV_ID_PLACEHOLDER`
  - `explorer/src/components/LeaderboardTab.jsx`: replace `ARXIV_ID_PLACEHOLDER`

## Upload package structure

```
monogate_arxiv_submission.tar.gz
├── preprint.tex
├── paper/figures/          (optional — if you have actual figures)
│   └── attractor.pdf
└── anc/
    └── sin_n11.json        (ancillary data file)
```

Build command from `python/` directory:
```bash
cd paper/
pdflatex preprint.tex
pdflatex preprint.tex      # second pass for cross-references
# Output: preprint.pdf
```

## Recommended cover letter snippet (optional)

```
This paper reports five independent extensions to the EML universal operator
(Odrzywołek 2026). The main scientific contribution is the N=11 exhaustive
search: 281,026,468 real-valued EML trees enumerated with zero matches to
sin(x), combined with the Infinite Zeros Barrier theorem which rules out exact
real-valued sin constructions for all N. The paper also covers BEST routing
(52-74% node savings), phantom attractor characterization (lambda_crit = 0.001),
and Rust-accelerated performance kernels (5.9x speedup).

All code, data, and an interactive explorer are available at
github.com/almaguer1986/monogate.
```
