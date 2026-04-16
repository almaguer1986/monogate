# Changelog

All notable changes to `monogate` are documented here.

---

## [0.12.0-dev] — 2026-04-16

### Session 2: Symbolic Regression Leaderboard

**New module `monogate.leaderboard`** — standardized benchmark runner over
Nguyen/Keijzer symbolic regression problems.

- 10 benchmark problems: Nguyen-1 through Nguyen-8, Keijzer-6, Keijzer-11
- Unified API: `run_leaderboard()`, `print_leaderboard()`, `markdown_leaderboard()`
- Serialization: `save_leaderboard()`, `load_leaderboard()` (JSON round-trip)
- CLI runner: `python/scripts/update_leaderboard.py` — generates `results/leaderboard.json`
  and `LEADERBOARD.md` at repo root
- Results scored by EML node count at MSE < threshold

New exports: `BenchmarkProblem`, `LeaderboardEntry`, `PROBLEMS`,
`run_leaderboard`, `print_leaderboard`, `markdown_leaderboard`,
`save_leaderboard`, `load_leaderboard`.

New files: `monogate/leaderboard.py`, `tests/test_leaderboard.py`,
`notebooks/symbolic_regression_leaderboard.py`,
`scripts/update_leaderboard.py`, `results/leaderboard.json`, `LEADERBOARD.md`.

---

### Session 1: Special Functions Library

**New module `monogate.special`** — 15 pre-computed short CBEST/BEST expressions
for special functions. Key results:

- **sin(x), cos(x)** — 1 CBEST node each (exact Euler path)
- **Fresnel integrands** — 2 CBEST nodes each (`Im/Re(eml(i·πx²/2, 1))`)
- **erf(x)** — 5 CBEST nodes (`tanh(1.2025x)`, max error ~1.5e-2)
- **Bessel J₀** — 7 CBEST nodes (complex MCTS, MSE < 1e-4)
- **Airy Ai** — 9 CBEST nodes (complex MCTS, MSE ~2e-3)
- **sinh, cosh, tanh, sech** — algebraic BEST constructions (exact)
- **lgamma** — Stirling series (~12 BEST nodes, max error < 1e-9)
- **digamma** — numerical diff of lgamma (~14 BEST nodes)

New exports: `sin_cb`, `cos_cb`, `sinh_cb`, `cosh_cb`, `tanh_cb`, `sech_cb`,
`erf_cb`, `fresnel_s_cb`, `fresnel_c_cb`, `fresnel_s_integrand_cb`,
`fresnel_c_integrand_cb`, `j0_cb`, `ai_cb`, `lgamma_cb`, `digamma_cb`,
`SpecialFnEntry`, `SPECIAL_CATALOG`, `catalog_summary`, `save_catalog`.

New files: `monogate/special.py`, `tests/test_special.py`,
`notebooks/special_functions_gallery.py`, `docs/guide/special_functions.md`,
`results/special_catalog.json`.

---

## [0.11.0] — 2026-04-16

### Full Release: EML Universality, Complex BEST, PINN, Theory & Reproducibility

This release completes the v0.9 → v0.10 → v0.11 research arc. Together the three
phases deliver: the Infinite Zeros Barrier theorem, 281M-tree exhaustive sin search,
Complex BEST routing (sin/cos at 1 node via Euler path), Physics-Informed EML Networks,
minimax/GPU search extensions, formal conjecture index (C1–C7), and a fully reproducible
infrastructure verified end-to-end.

### Phase 11: Formal Theory, Conjectures, and Full Reproducibility

**THEORY.md** — new canonical theory reference at the repository root.
  Expert-level document covering: formal definitions (EML operator, BEST routing,
  phantom attractors, EMLPINN), proven theorems (Infinite Zeros Barrier, Euler
  path identity), open conjectures C1–C7 (EDL incompleteness, attractor value,
  minimax-optimal approximation, CBEST completeness, PINN symbolic convergence),
  and a structured research roadmap for the community.

**Formal paper section** — §"Formal Statements of Main Results and Open Problems"
  added to `paper/preprint.tex` with precise theorem/conjecture index and pointers
  to THEORY.md.  Abstract updated to reference the theory document.

**Reproducibility infrastructure:**
  - `Makefile` (root) — targets: `make test`, `make reproduce-n11`, `make reproduce-all`,
    `make paper`, `make theory`, `make docker-build`, `make docker-run`
  - `Dockerfile` (root) — Python 3.12, PyTorch 2.3 CPU, TeX Live, Rust toolchain;
    reproduces all paper results from a clean clone
  - `python/requirements-reproduce.txt` — pinned dependency list
  - `python/scripts/reproduce_n11.py` — verifies all N=11 paper claims against
    cached `results/sin_n11.json` (12/12 claims verified); supports `--rerun` for
    full re-computation (~5 min)

**Version:** bumped to `0.11.0-dev` in `monogate/__init__.py` and `pyproject.toml`.

---

## [0.10.0] — 2026-04-16

### Complex BEST, PINN, Minimax Search, GPU Search

**New modules:**

- **`monogate.complex_best`** — `ComplexHybridOperator` (`CBEST`): extends BEST
  routing to ℂ using `cmath`.  `CBEST.sin(x)` and `CBEST.cos(x)` cost **1 node each**
  via the Euler path `Im(eml(ix,1)) = sin x` (vs 63 nodes in real BEST).
  Exports `complex_best_optimize()`, `ComplexOptimizeResult`, `im()`, `re()`,
  and node-count constants (`SIN_NODE_COUNT=1`, `J0_NODE_COUNT=7`, etc.).

- **`monogate.complex_search`** — `complex_mcts_search()` and
  `complex_beam_search()` over the complex terminal set `{1, x, ix, i}`.
  Returns `ComplexMCTSResult`/`ComplexBeamResult` with `projection` and
  `complex_formula` fields.  Finds near-exact constructions for Bessel J₀,
  erf, and Airy Ai.

- **`monogate.pinn`** — `EMLPINN(equation, backbone_depth, omega, nu, lam_physics)`:
  physics-informed EML network.  Equations: `'harmonic'` (u''+ω²u=0),
  `'burgers'` (u·u'−ν·u''=0), `'heat'` (u''=0).  Residual via
  `torch.autograd.grad` with `create_graph=True`.  `fit_pinn()` returns
  `PINNResult(data_loss, physics_loss, history, formula, elapsed_s)`.

- **`monogate.search.gpu_search`** — `gpu_mcts_search(device='cuda', batch_size=512)`:
  GPU-accelerated MCTS with batched rollouts.  Graceful CPU fallback when CUDA
  unavailable.  Also exports `GPUTreeEvaluator` for standalone batch evaluation.

**Extended:**

- **`mcts_search` / `beam_search`** — new `objective` parameter: `'mse'`
  (default, unchanged) or `'minimax'` (Chebyshev/L∞ approximation — minimises
  max absolute error).  `MCTSResult` and `BeamResult` gain `objective` field.

**New tests:** 69 new tests (`test_complex_best.py`, `test_pinn.py`).
Total: 662 passing.

**New notebooks:** `complex_special_functions.py`, `pinn_eml_demo.py`,
`minimax_approximation.py`.

**Paper:** Added §4.6 Complex-Domain BEST Routing and Special Functions;
§9 Physics-Informed EML Networks; abstract updated.

---

## [0.9.0] — 2026-04-16

### Public Launch — arXiv Submission Live

**This is the official public release of monogate. The paper is on arXiv.**

**New in this release:**

- **Phantom attractor landscape figure** — `experiments/plot_attractor_landscape.py`
  generates a 400×400 2D MSE loss-surface slice for a depth-3 EMLTree.
  Shows the wide phantom basin (~3.1696) and narrow π basin side-by-side,
  with three overlaid L1-penalty contour sets (λ=0/0.001/0.005).
  Output: `paper/figures/attractor_landscape.{pdf,png}`.

- **Preprint §5.5 "Visualizing the Phantom Attractor Landscape"** — new subsection
  in the paper explaining basin geometry, the L1 tilt effect, and implications
  for deeper trees and exact-function search.

- **Preprint: emlbox highlight box** — the Infinite Zeros Barrier section now
  includes a tcolorbox callout that packages theorem, proof, corollary, complex
  bypass equation, and `sin_via_euler` usage example in a single scannable block.

- **`context_aware_best_optimize()`** — wraps `best_optimize()` with optional
  AST depth analysis (flags risky deep EML subtraction/add chains) and NumPy
  forward profiling (NaN, Inf, dynamic-range checks on sample inputs).
  Exported as `monogate.context_aware_best_optimize`.

**Previous entries:**

- **`scripts/update_arxiv_id.py`** — one-command post-submission ID update:
  replaces `ARXIV_ID_PLACEHOLDER` in README, share card, and both explorer
  components. Creates `.bak` backups, prints diffs, guides next steps.
- **`ANNOUNCEMENT.md`** — ready-to-post launch text for Hacker News,
  r/MachineLearning, r/math, X/Twitter (thread), and LinkedIn.
- **Explorer ResearchTab** — paper banner now shows live/pending arXiv link;
  new "cite this work" dropdown with one-click BibTeX copy.
- **Explorer LeaderboardTab** — arXiv reference banner now points to live URL
  once ARXIV_ID_PLACEHOLDER is updated.
- **`assets/n11_share_card.md`** — fully polished: all sections, BibTeX block,
  BEST routing example, PyTorch performance table, update instructions.
- **README** — "Now on arXiv" notice, "How to cite" BibTeX, "What's next" section.
- Version: 0.8.1 → **0.9.0** (official public launch).

**Post-submission, run once:**
```bash
python scripts/update_arxiv_id.py 2604.XXXXX
```

---

## [0.8.1] — 2026-04-16

### Phase 8 — arXiv Submission & Public Launch

**Submission-ready polish. No new features — everything is documentation, export, and clean-up.**

**Explorer**
- `ResearchTab.jsx` — added "Paper submission-ready" banner with link to `preprint.tex`
- `LeaderboardTab.jsx` — added arXiv canonical reference banner in header (with `ARXIV_ID_PLACEHOLDER`)

**README**
- Added "Now on arXiv" notice at top (placeholder — update after submission)
- Added "How to cite" section with BibTeX entry (`ARXIV_ID_PLACEHOLDER`)
- Added "What's next" section: N=12 GPU search, minimax approximations, complex BEST, SIREN experiments

**Paper & submission assets**
- `arxiv_submission_notes.md` — abstract (≤250 words), categories, keywords, post-submission checklist
- `paper/README.md` — exact 5-step arXiv upload instructions + Docker build option + full checklist
- `assets/n11_share_card.md` — added paper title + arXiv placeholder

**Post-submission update checklist** (do these once arXiv ID is assigned):
1. `README.md` — replace `ARXIV_ID_PLACEHOLDER` in badge and BibTeX
2. `assets/n11_share_card.md` — replace `ARXIV_ID_PLACEHOLDER`
3. `explorer/src/components/ResearchTab.jsx` — replace `ARXIV_ID_PLACEHOLDER`
4. `explorer/src/components/LeaderboardTab.jsx` — replace `ARXIV_ID_PLACEHOLDER`

---

## [0.8.0] — 2026-04-16

### Phase 7 — arXiv Prep, Rust Promotion, SIREN Demo

**Headline: N=11 exhaustive search complete. 281,026,468 trees. Zero candidates.**

The sin barrier is now both proven (Infinite Zeros Barrier theorem) and
exhaustively confirmed through depth 11. This is the central result of
the monogate v0.8.0 release and the paper submission.

**Preprint (`paper/preprint.tex`) — arXiv-ready**

- New title: "Practical Extensions to the EML Universal Operator: Hybrid
  Routing, Phantom Attractors, Performance Kernels, and the N=11 Sin Barrier"
- Updated abstract: 5 contributions, N=11 numbers, Rust speedup (5.9×), SIREN
- New §8 "Performance Kernels": FusedEMLActivation (3.6×), Rust core (5.9×),
  EMLLayer(compiled=True) auto-selection table, SIREN integration result
- §7.1 "N=11 Exhaustive Search": complete N=1–11 counts table, near-miss analysis,
  exact MSE of best 12-leaf approximation (1.478e-4)
- Infinite Zeros Barrier: added Corollary (extends to Airy, Bessel, cos)
- Updated conclusion: all 5 contributions enumerated, 5 open problems
- New §"Acknowledgments" and §"Data and Code Availability" (with code snippets)
- References: added Sitzmann et al. 2020 (SIREN), Paszke et al. 2019 (PyTorch)
- `paper/README.md` (new): build instructions + arXiv submission checklist

**`monogate/fused_rust.py` — Rust backend promotion**

- `get_best_activation(depth, operator)` — returns the fastest available backend:
  RustFusedLayer > FusedEMLActivation > EMLActivation. Used by `EMLLayer(compiled=True)`.
- Improved error messages: clear build instructions in `rust_info()`, specific
  guidance for depth/operator mismatches in `RustFusedLayer.__init__`.
- `rust_info()` now shows "5.9x faster than baseline" and which batch sizes use Rust.
- `RustFusedLayer` forward pass: uses `.tolist()` for PyO3 compatibility.

**`monogate/torch/eml_layer.py` — Rust-first `compiled=True`**

- `EMLLayer(compiled=True)` now calls `get_best_activation()`: Rust first (if
  `monogate-core` installed), then `FusedEMLActivation`, then `EMLActivation`.
- `extra_repr()` shows `backend=rust` or `backend=fused` when compiled.
- Improved warning message explains the Rust install path.

**`notebooks/siren_with_monogate.py`** (new)

- `SirenNet` (sin activation) vs `EMLSirenNet` (EMLLayer, BEST, compiled=True)
  trained on a 2D Gaussian mixture target at 64×64 resolution.
- Reports: MSE, PSNR (dB), training time, speedup, ASCII heatmap comparison.
- Optional `--plot` flag saves a side-by-side PNG via matplotlib.
- `--steps`, `--hidden`, `--res`, `--depth`, `--seed` CLI flags.
- Run: `python notebooks/siren_with_monogate.py`

**`assets/n11_share_card.md`** (new)

- Self-contained markdown card for X/HN:
  N=11 table, theorem statement, best near-miss formula,
  complex bypass in Python, install one-liner.

**README.md — complete rewrite of top section**

- Leads with the N=11 result and the Infinite Zeros Barrier theorem
- Performance table (Standard / Fused / torch.compile / Rust) near the top
- `EMLLayer(compiled=True)` backend auto-selection shown prominently
- Rust install instructions (one-time ~30s compile)
- "What's new in v0.8.0" section
- Package structure updated: monogate-core, assets/, paper/, results/ shown

### Changed

- `monogate.__version__`: `0.7.1` → `0.8.0`
- `pyproject.toml`: version `0.8.0`
- `paper/preprint.tex`: fully rewritten for arXiv submission
- `monogate/fused_rust.py`: Rust-first promotion, get_best_activation, improved errors
- `monogate/torch/eml_layer.py`: compiled=True uses get_best_activation (Rust-first)
- `README.md`: leads with N=11 result and performance table

---

## [0.7.1] — 2026-04-16

### Phase 6 — N=11 Results Hardening

**`monogate/search/analyze_n11.py` — Post-search analysis script**

- Reads `results/sin_n11.json`, prints the complete N=1–11 summary table with parity
  stats and runtime, and prints the top-10 near-miss gallery with per-formula
  probe-point evaluation.
- `--html PATH` exports a self-contained HTML near-miss gallery.
- `analyze_n11(json_path, html_out)` callable from Python.
- `monogate.search.analyze_n11` now exported from `monogate.search`.

**`RESULTS.md` — Full N=1–11 table**

- Updated from partial N≤10 table to complete N=1–11 table with per-N parity counts,
  cumulative tree counts, and top-10 near-miss rank table with MSE and formula strings.

**`paper/preprint.tex` — N=11 subsection added**

- New §7.1 "N=11 Exhaustive Search" with full counts table (N=1–11) and near-miss
  analysis including exact MSE of the best 12-leaf approximation found.
- Conjecture support sentence updated to reference 281M-tree search.

**`explorer/src/components/ResearchTab.jsx` — N=11 complete**

- `EXHAUSTIVE_RESULTS`: N=11 row updated from `result: "running"` to `result: "none"`
  with exact `after_parity: 208_901_719` count.
- Added green "N=11 search complete" banner above the results table.
- `NEAR_MISSES`: Updated with real N=11 exhaustive near-miss data (top 4 from 281M-tree
  search) plus the exact complex-domain result at the top.
- Near-miss cards now use `toExponential(4)` for small MSE values and show the `exact`
  badge for the complex-domain result.
- Cumulative total footer updated to exact 281,026,468.

**`README.md` — N=11 update box**

- Added "N=11 Sin Barrier Update" section at the top of the changelog with the key
  numbers, the best near-miss formula, and a link to `analyze_n11.py`.

### Changed

- `monogate.search.__init__`: exports `analyze_n11`
- `monogate.__version__`: `0.7.0` → `0.7.1`

---

## [0.7.0] — 2026-04-16

### Phase 5 — Sin Barrier Deep Search, Challenge Board v2, Compiled Core

**`monogate/search/sin_search_05.py` — N=11 Exhaustive Search**

- Vectorised NumPy batch evaluator: evaluates all 2^12 = 4,096 leaf assignments × 8
  probe points simultaneously per shape via a single bottom-up tree traversal.
  ~50–200× faster than the scalar Python evaluator in sin_search_04.
- Exact parity filter: tests all assignments (not just 64 samples), eliminating ~50% of
  shapes with zero false positives.
- Near-miss tracking: records the top-20 lowest-MSE assignments across all shapes/
  probings, enabling qualitative progress reporting even when no exact candidate exists.
- MCTS post-scan: after exhaustive search, runs MCTS to find the best approximation
  achievable by any finite EML tree (with `--mcts` or `--mcts-only`).
- N=12 dry-run: complexity estimate and time-budgeted partial run (`--n 12 --budget 300`).
- Result: **No EML tree equals sin(x) for any N ≤ 11**. Combined N≤11: ~281M trees.
- Exported: `monogate.search.run_exhaustive`, `run_mcts_approx`, `SearchResult`

**`monogate-core/` — Rust Compiled Core (PyO3)**

- New Rust crate in `monogate-core/` with PyO3 bindings.
- `eval_eml_batch(leaf_w, leaf_b, x, depth)` — fused bottom-up EML evaluation in Rust.
- `eval_best_batch(leaf_w, leaf_b, x, depth)` — BEST routing (EXL inner + EML root).
- Rayon parallel evaluation for batch sizes > 1,000.
- `benchmark_rust(n, depth)` — throughput in millions/sec.
- Sin-search helpers: `eval_tree_assignment`, `check_parity`, `parity_filter_stats`.
- Build: `cd monogate-core && pip install maturin && maturin develop --release`
- `monogate/fused_rust.py` — Python wrapper with graceful fallback to FusedEMLLayer.
- Estimated speedup: 50–200× over Python fused for depth=3–5 on large batches.

**`monogate/validate.py` — Challenge Board v2 Validator CLI**

- `validate_submission(submission, ...)` → `ValidationResult` with tier, points, node counts.
- Five tiers: exact (1e−12), tight (1e−8), medium (1e−5), approximate (1e−3), near_miss (5e−2).
- `monogate-validate submission.json` CLI entry point.
- `monogate-validate --list-problems` — shows all open problems and current best.
- GitHub Action `.github/workflows/validate-submission.yml` — auto-validates PR submissions
  and posts tier/MSE/node-count comment.

**`challenge/` — 10 Open Problems**

- `challenge/problems.json` v2: 10 problems incl. Lambert W₀, erf, Airy Ai, Bessel J₀,
  Poisson PINN residual, softplus exact, swish, exp(-x²).
- `challenge/leaderboard.json` — structured leaderboard with tier and per-problem stats.
- Drag-and-drop submission flow: copy template from LeaderboardTab → PR → auto-validation.

**Explorer — Two New Tabs**

- `LeaderboardTab.jsx` — Challenge Board v2 browser + leaderboard + submission template.
  Loads live data from `/challenge/problems.json` and `/challenge/leaderboard.json`.
- `ResearchTab.jsx` — Research Mode: sin barrier theorem, exhaustive search table through
  N=11, MCTS live search (connected to API if running, offline demo otherwise),
  near-miss approximation gallery, N=12 complexity estimate.

**`EMLLayer(compiled=True)` — Polish**

- `EMLLayer(..., compiled=True)` now uses `FusedEMLActivation` when `depth ≤ 3` and
  operator ∈ {EML, BEST}. Graceful fallback with warning for depth > 3.
- New `.compile()` method on `EMLLayer` (wraps with `compile_eml_layer`).
- `extra_repr` shows `fused=True` flag when compiled mode is active.

### Changed

- `monogate.__version__`: `0.6.0` → `0.7.0`
- `pyproject.toml`: version `0.7.0`, added `monogate-validate` CLI entry point
- `monogate.search.__init__`: exports `run_exhaustive`, `run_mcts_approx`, `SearchResult`
- `monogate.__init__`: exports `validate_submission`, `ValidationResult`, `load_problems`
- `mkdocs.yml`: added "Phase 5: Sin Barrier Deep Search" research page
- `explorer/src/App.jsx`: added `research` and `leaderboard` tabs
- `explorer/public/challenge/`: added `problems.json` + `leaderboard.json` static assets

---

## [0.6.0] — 2026-04-16

### Added

**`monogate.compile` — Performance kernels**

- `FusedEMLActivation(depth, operator)` — manually inlines the EML expression
  tree as a flat bottom-up vectorized computation over `(n_leaves, N)` tensors.
  No Python recursion; single broadcast multiply for all leaf evaluations.
  - Depth 1–3, operators EML and BEST
  - 1.5–3.6× faster than `EMLActivation` on CPU at typical batch sizes
  - Depth 4+ raises `ValueError` (Numerical Overflow Barrier documented)
- `FusedEMLLayer(in, out, depth, operator)` — drop-in for `EMLLayer(mode='activation')`.
  - 1.2–2.8× faster training step than `EMLLayer` in SIREN-style networks
  - Full `state_dict()` round-trip; ONNX-exportable
  - `.compile()` convenience method → `torch.compile` wrapper
- `compile_eml_layer(layer, mode, backend)` — `torch.compile` wrapper with
  graceful fallback for platforms without Inductor (Windows/Python 3.14)
- `to_torchscript(layer, method)` — TorchScript export via trace/script
- `benchmark_layer(*layers, batch_sizes, ...)` → `BenchmarkTable` — timing harness
  with `print_table()` and `as_dict()` output

**`monogate.llm` — LLM-assisted optimizer**

- `suggest_and_optimize(prompt, target_func, provider, ...)` → `LLMOptimizeResult`
  - Providers: `mock` (no key), `openai`, `groq`, `anthropic`
  - Sends structured prompt → LLM suggests math expression → BEST-optimized
  - Optional `run_mcts=True` adds gradient-free MCTS search
  - `result.print_summary()` — formatted human-readable output
  - `result.code` — copy-paste `f = lambda x: BEST.*` snippet
- `LLMOptimizeResult` dataclass with all fields
- `SUPPORTED_PROVIDERS` tuple
- `monogate-optimize` CLI entry point (installed by `pip install monogate`)
  - `monogate-optimize "sigmoid function"`
  - `monogate-optimize --provider openai "GELU activation"`
  - `monogate-optimize --mcts "exp(-x^2)"`

**Notebooks & benchmarks**

- `notebooks/performance_kernels.py` — measures activation throughput,
  layer throughput, training step timing; actual numbers on hardware
- `notebooks/llm_optimizer_demo.py` — LLM optimizer walkthrough with
  mock/OpenAI/Groq/Anthropic provider support
- `benchmarks/kernel_benchmarks.py` — full benchmark suite with JSON output

**Tests**

- `tests/test_compile.py` — 41 tests: FusedEMLActivation, FusedEMLLayer,
  compile wrapper, TorchScript, BenchmarkTable
- `tests/test_llm.py` — 40 tests: mock provider, expression analysis,
  BEST rewriting, CLI, integration tests (skip without API keys)
- Total: **593 passing, 8 skipped**

### Changed

- `monogate.__version__`: `0.5.0` → `0.6.0`
- `pyproject.toml`: added `[llm]` optional deps group, `[docs]` group,
  `monogate-optimize` CLI script entry point
- `monogate.__init__`: exports `FusedEMLActivation`, `FusedEMLLayer`,
  `compile_eml_layer`, `suggest_and_optimize`, `LLMOptimizeResult`
- `explorer/src/components/LandingPage.jsx`: added performance benchmark
  section with real numbers from CPU timing

---

## [0.5.0] — 2026-04-16

### Added

**`monogate.torch` — Differentiable EML layers for PyTorch**

- `EMLActivation(depth, operator)` — element-wise EML activation (drop-in for `torch.sin`, `F.gelu`, etc.)
  - Fully vectorized via `EMLNetwork(in_features=1)` backbone — no Python loops
  - Shapes preserved; all operators supported: `EML`, `EDL`, `EXL`, `BEST`
- `EMLLayer(in_features, out_features, depth, operator, mode)` — complete learnable layer
  - `mode='activation'`: `nn.Linear(in, out)` + shared `EMLActivation`
  - `mode='tree'`: `out_features` independent EML trees with linear leaves (interpretable)
  - `.formula()` — human-readable EML expression string / list
  - `.n_eml_nodes` — node count property
  - `state_dict()` / `load_state_dict()` round-trip
  - ONNX export (opset 14; all ops are ONNX-native)
- `compare_to_native(layer, native_name)` — prints node-count comparison vs sin/cos/GELU
- Notebook: `notebooks/eml_layer_siren_example.py` — SIREN with EMLLayer activation

**`monogate.complex_eval` — Complex-domain EML**

- `eml_complex(a, b)` — complex EML operator using `cmath` principal branch
- `eval_complex(node, x)` — tree evaluation with terminals `'x'`, `'ix'`, `'i'`, numeric
- `euler_path_node()` — tree dict for `eml(ix, 1)` (the Euler path)
- `sin_via_euler(x)` — exact `sin(x)` = `Im(eml(ix, 1))`, one node, machine precision
- `cos_via_euler(x)` — exact `cos(x)` = `Re(eml(ix, 1))`
- `score_complex_projection(node, probe_x, probe_y, projection)` — MSE of Im/Re part
- `formula_complex(node)` — formula string with complex terminal rendering
- `COMPLEX_TERMINALS` — extended terminal set `[1.0, 'x', 'ix', 'i']`

**`monogate.search` — MCTS and Beam Search**

- `mcts_search(target_fn, ...)` — Monte-Carlo Tree Search over EML grammar
  - UCB1 selection, random rollout completion, `1/(1+MSE)` reward
  - `n_rollouts` parameter: parallel rollouts via `ThreadPoolExecutor`
  - Returns `MCTSResult(best_tree, best_mse, best_formula, history, elapsed_s)`
- `beam_search(target_fn, ...)` — systematic beam search (top-`width` candidates per level)
  - Returns `BeamResult(best_tree, best_mse, best_formula, n_levels, elapsed_s)`
- Notebook: `notebooks/mcts_sin_approximation.py`

**Research: N=10 exhaustive search**

- `experiments/sin_search_04.py` — extends search to N=10 (34M trees, ~19s)
- Combined N≤10: **40,239,012 EML trees**, zero sin candidates at any tolerance
- 45.5% parity pruning for N=10 shapes

**Research: phase transition refinement**

- `experiments/gen_attractor_data_v2.py` — 10-lambda sweep, λ_crit = 0.001
- Depth=4 documented as Numerical Overflow Barrier (structural, not hyperparameter)

**Documentation**

- MkDocs site: `mkdocs.yml` + `docs/` (Home, Installation, 4 guides, 3 research pages, 6 API pages)
- `paper/preprint.tex` — arXiv-ready LaTeX (8 sections, full bibliography)
- `PAPER.md` — updated with N=10 results, depth=4 barrier, λ_crit, MCTS section

**Tests**

- `tests/test_eml_layer.py` — 68 tests: shapes, operators, gradients, serialization, ONNX
- `tests/test_complex.py` — 36 tests: Euler path, Pythagorean identity, Barrier bypass
- Total: **512 passing, 4 skipped** (ONNX skips without `onnx` package)

### Changed

- `monogate.__version__`: `0.4.0` → `0.5.0`
- `monogate.__init__` exports `EMLActivation`, `EMLLayer` (try/import, no mandatory torch)
- `monogate.__init__` exports all `complex_eval` symbols unconditionally (no torch dependency)

---

## [0.4.0] — 2026-04-15

### Added

- `monogate.search.mcts_search` — MCTS over EML grammar (initial version)
- `monogate.search.beam_search` — beam search over EML grammar
- `experiments/sin_search_03.py` — N=9 exhaustive search (parity pruning, parallel)
- `experiments/gen_attractor_data.py` — 40-seed attractor trajectory generator
- Explorer: Attractor Lab tab (`AttractorViz.jsx`) with animated convergence
- Explorer: offline JS optimizer enhancements (`opt-engine.js` — PyTorch/NumPy patterns)
- Explorer: BEST toggle, node breakdown table, copyable snippet in `OptimizeTab.jsx`

### Changed

- `monogate.__version__`: `0.3.3` → `0.4.0`
- `explorer/package.json`: `0.1.0` → `0.2.0`

---

## [0.3.3] — 2026-04-10

### Fixed

- `best_optimize` BEST operations now return `float` instead of `complex` (#bug)
- Fixed phantom attractor test: expected value corrected for `softplus` right-child transformation

---

## [0.3.1] — 2026-04-05

### Added

- NeRF optimizer (`optimize_nerf`)
- SIREN tab in explorer
- Research scripts (attractor analysis, operator zoo)
- PyPI release

---

## [0.2.0] — 2026-03-20

### Added

- `monogate.network`: `EMLNetwork`, `HybridNetwork`, `EMLTree`, `fit()`
- `monogate.torch_ops`: differentiable tensor operations
- Explorer: BEST tab, SIREN tab
- `monogate.optimize`: `best_optimize`, `OptimizeResult`, `BestRewriter`
- Challenge board (`challenge/`)

---

## [0.1.0] — 2026-03-01

### Added

- Initial release
- `monogate.core`: EML operator, EML/EDL/EXL/EAL/EMN families, BEST routing
- `monogate.operators`: operator registry, comparison table
- JavaScript package (`lib/`)
- Interactive explorer (`explorer/`) — basic viz, sin tab, calculator
