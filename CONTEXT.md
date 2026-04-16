# monogate — Complete Project Context
> Single-document briefing for the full state of the project as of **v0.12.0-dev**, April 2026.
> Branch: `phase9-arxiv-live`. Next step: merge → master, cut v0.12.0 PyPI release.
> Update ARXIV_ID_PLACEHOLDER with real ID once published.

---

## 1. Project Overview

**monogate** is a Python and JavaScript library built around a single algebraic discovery:
the binary operator

    eml(x, y) = exp(x) − ln(y),    constant = 1

generates every elementary function as a finite binary tree of identical nodes.
This was proved by Odrzywołek (2026, arXiv:2603.21852).

monogate provides:
- A symbolic computation engine that builds, evaluates, and rewrites EML expression trees.
- **BEST routing**: a hybrid dispatcher (EML/EDL/EXL) that cuts node count 52–74% and
  delivers up to 2.8× wall-clock speedup with zero accuracy loss.
- A PyTorch integration layer (`EMLLayer`) as a drop-in activation for SIREN, NeRF, PINN.
- Rust-accelerated kernels via PyO3 (5.9×) and a fused Python kernel (3.6×).
- An exhaustive symbolic search engine (N≤11, 281M trees).
- A gradient-free MCTS search module that avoids phantom-attractor traps.
- **15 special functions** pre-computed as CBEST/BEST expressions (`monogate.special`).
- **Symbolic regression leaderboard** over 10 Nguyen/Keijzer benchmarks (`monogate.leaderboard`).
- **Physics-Informed EML Networks** for 7 differential equations (`monogate.pinn`).
- **Certified interval arithmetic** through EML trees (`monogate.interval`).
- **SymPy interoperability**: to_sympy, from_sympy, latex_eml (`monogate.sympy_bridge`).
- **Streamlit web demo** — 5 interactive tabs, deployable to Streamlit Cloud (`streamlit_app.py`).

**The central research question** monogate addresses:

> Can sin(x) be expressed exactly as a finite real-valued EML tree?

**Answer**: No. The Infinite Zeros Barrier theorem proves this for all N on structural
grounds. Empirical confirmation: 281,026,468 trees (N≤11), zero candidates. The
complex bypass Im(eml(ix,1)) = sin(x) recovers the function exactly in one node.

**Operator family:**

| Operator | Definition          | Constant | Complete? | Strength                         |
|----------|---------------------|----------|-----------|----------------------------------|
| EML      | exp(x) − ln(y)      | 1        | Yes       | Add, subtract                    |
| EDL      | exp(x) / ln(y)      | e        | Yes       | Div (1 node), mul (7 nodes)      |
| EXL      | exp(x) · ln(y)      | 1        | No        | ln (1 node), pow (3 nodes), stability |
| EAL      | exp(x) + ln(y)      | 1        | No        | —                                |
| EMN      | ln(y) − exp(x)      | −∞       | No        | —                                |

---

## 2. Full File Structure

```
monogate/                          # repo root  (branch: phase9-arxiv-live)
├── streamlit_app.py               # 5-tab Streamlit demo (Optimizer, Special Fns,
│                                  #   PINN, MCTS Explorer, Phantom Attractor)
├── requirements.txt               # Streamlit Cloud deps (no torch required)
├── CONTEXT.md                     # this file — current project briefing
├── THEORY.md                      # formal theory: definitions, theorems, conjectures
├── Makefile                       # make reproduce-n11, reproduce-all, paper, docker-*
├── Dockerfile                     # clean-room reproduce environment
├── python/                        # Python library (PyPI: monogate)
│   ├── monogate/                  # main package
│   │   ├── __init__.py            # public API re-exports, __version__ = "0.11.0"
│   │   ├── core.py                # op(), E, ZERO, NEG_ONE; all EML/EDL/EXL scalar ops;
│   │   │                          #   _NODE_COSTS table; IDENTITIES dict
│   │   ├── operators.py           # BEST, CBEST operator dispatch objects
│   │   ├── network.py             # EMLTree, EMLNetwork, HybridNetwork, fit()
│   │   ├── optimize.py            # best_optimize(), context_aware_best_optimize();
│   │   │                          #   OptimizeResult, OpMatch, BestRewriter
│   │   ├── torch_ops.py           # PyTorch tensor EML/EXL/EDL ops (softplus-safe)
│   │   ├── fused_rust.py          # get_best_activation(), FusedEMLActivation,
│   │   │                          #   RustFusedLayer, RUST_AVAILABLE, rust_info()
│   │   ├── complex_eval.py        # complex_eml_sin/cos/eval; Im(eml(ix,1))=sin(x)
│   │   ├── complex_best.py        # CBEST class; im(), re() helpers; node counts
│   │   ├── complex_search.py      # MCTS over complex EML grammar
│   │   ├── special.py             # CATALOG + 15 callables (sin_cb, cos_cb, erf_cb,
│   │   │                          #   j0_cb, ai_cb, lgamma_cb, digamma_cb, …)
│   │   ├── leaderboard.py         # PROBLEMS dict; run_leaderboard(),
│   │   │                          #   markdown_leaderboard(); LeaderboardEntry
│   │   ├── pinn.py                # EMLPINN, fit_pinn(), PINNResult; 7 equations:
│   │   │                          #   harmonic, burgers, heat, schrodinger,
│   │   │                          #   kdv_soliton, nls, lotka_volterra
│   │   ├── interval.py            # Interval, eml_interval(), eval_interval(),
│   │   │                          #   bound_expression()
│   │   ├── sympy_bridge.py        # to_sympy, from_sympy, simplify_eml, latex_eml,
│   │   │                          #   verify_identity (optional: pip install monogate[sympy])
│   │   ├── validate.py            # monogate-validate CLI; challenge board validation
│   │   ├── torch/
│   │   │   ├── __init__.py        # exports EMLLayer, EMLActivation
│   │   │   └── eml_layer.py       # EMLLayer (nn.Module); mode='activation'|'tree';
│   │   │                          #   compiled=True; ONNX opset 17; torch.compile
│   │   ├── compile/
│   │   │   ├── __init__.py        # exports FusedEMLLayer, FusedEMLActivation
│   │   │   ├── fused.py           # FusedEMLActivation: vectorised bottom-up kernel
│   │   │   └── compiler.py        # compile_eml_layer(): torch.compile wrapper
│   │   ├── llm/
│   │   │   ├── __init__.py        # exports suggest_and_optimize
│   │   │   ├── optimizer.py       # LLM → BEST expression (mock/openai/groq/anthropic)
│   │   │   ├── prompts.py         # prompt templates
│   │   │   └── cli.py             # monogate-optimize CLI entry point
│   │   └── search/
│   │       ├── __init__.py        # exports mcts_search, beam_search, analyze_n11
│   │       ├── mcts.py            # mcts_search(), beam_search(); MCTSResult;
│   │       │                      #   UCB1 + 1/(1+MSE) reward; immutable tree dicts
│   │       ├── gpu_search.py      # GPU-accelerated search (PyTorch tensor eval)
│   │       ├── analyze_n11.py     # analyze_n11(): N=1–11 table; --html export
│   │       ├── sin_search_03.py   # N=9 exhaustive (parity filter)
│   │       ├── sin_search_04.py   # N=10 exhaustive (ProcessPoolExecutor)
│   │       └── sin_search_05.py   # N=11 exhaustive; vectorised NumPy; 323s
│   ├── tests/                     # 913 passing, 8 skipped, 0 failed
│   │   ├── test_core.py, test_network.py, test_optimize.py, test_search.py
│   │   ├── test_torch.py, test_compile.py, test_complex.py, test_eml_layer.py
│   │   ├── test_llm.py, test_complex_best.py, test_pinn.py
│   │   └── (+ interval, sympy_bridge, special, leaderboard tests)
│   ├── experiments/
│   │   ├── gen_attractor_data.py       # 40 seeds × λ∈{0,0.005}, depth=3, 3000 steps
│   │   ├── gen_attractor_data_v2.py    # 20 seeds × 10 λ values; λ_crit=0.001 sweep
│   │   ├── attractor_phase_transition.json  # raw sweep results (used by Streamlit tab 5)
│   │   ├── attractor_data.json         # 40-seed attractor curves (used by explorer)
│   │   ├── plot_attractor_landscape.py # paper/figures/attractor_landscape.pdf
│   │   ├── experiment_12_siren.py      # EML-SIREN comparison
│   │   └── research_02/03/04.py        # attractor, EDL completeness, tree search studies
│   ├── notebooks/
│   │   ├── eml_layer_siren_example.py
│   │   ├── siren_with_monogate.py      # EMLSirenNet vs SirenNet; PSNR comparison
│   │   ├── mcts_sin_approximation.py
│   │   ├── performance_kernels.py
│   │   ├── llm_optimizer_demo.py
│   │   ├── complex_special_functions.py   # Session 1 notebook
│   │   ├── pinn_eml_demo.py               # Session 4 notebook
│   │   ├── minimax_approximation.py       # Session 2 notebook
│   │   └── attractor_generalization.py    # Session 5: attractor in Taylor/Padé/CF bases
│   ├── scripts/
│   │   ├── update_arxiv_id.py             # post-submission ID update
│   │   ├── update_leaderboard.py          # run leaderboard + save results/leaderboard.json
│   │   ├── prepare_v0.10.py               # v0.10.0 release prep
│   │   ├── reproduce_n11.py               # reproduce N=11 from sin_n11.json cache
│   │   └── release_v0.11.0.py             # v0.11.0 release script
│   ├── paper/
│   │   ├── preprint.tex                   # arXiv-ready LaTeX (authoritative)
│   │   ├── arxiv_submission_notes.md      # abstract ≤250w, categories, checklist
│   │   └── README.md                      # pdflatex build + arXiv upload (5 steps)
│   ├── docs/                              # MkDocs source
│   ├── results/
│   │   ├── sin_n11.json                   # N=11 search output
│   │   └── leaderboard.json               # latest Nguyen/Keijzer leaderboard
│   ├── assets/
│   │   └── n11_share_card.md
│   ├── CHANGELOG.md                       # version history v0.1–v0.12.0-dev
│   ├── PAPER.md                           # internal research notes (updated to v0.12.0-dev)
│   ├── RESULTS.md                         # N=1–11 table + near-miss gallery
│   ├── ANNOUNCEMENT.md                    # launch posts
│   ├── pyproject.toml                     # version="0.11.0"; extras: torch,llm,sympy,streamlit,dev
│   └── mkdocs.yml
├── explorer/                       # React/Vite SPA (monogate.dev, deployed on Vercel)
│   ├── src/App.jsx                  # tab router
│   └── src/components/             # OptimizeTab, AttractorViz, ResearchTab, LeaderboardTab
├── lib/                            # JS/npm package (monogate 0.2.0)
└── monogate-core/                  # Rust/PyO3 extension (5.9× speedup)
    ├── src/lib.rs                  # eval_eml_batch(); rayon parallel
    └── Cargo.toml
```

---

## 3. Feature Inventory

### `monogate.core`

| Name | Type | Signature | Description |
|------|------|-----------|-------------|
| `op` | function | `op(x, y) -> float` | `eml(x,y) = exp(x) - ln(y)` with softplus-safe ln |
| `E` | constant | `float = math.e` | EML/EXL neutral constant |
| `ZERO` | constant | `float = 0.0` | |
| `NEG_ONE` | constant | `float = -1.0` | |
| `exp_eml` | function | `exp_eml(x) -> float` | `exp(x)` via EML: `op(x, 1)` |
| `ln_eml` | function | `ln_eml(x) -> float` | `ln(x)` via EML (3 nodes) |
| `sub_eml` | function | `sub_eml(a, b) -> float` | `a - b` via EML (5 nodes) |
| `neg_eml` | function | `neg_eml(x) -> float` | `-x` via EML (9 nodes) |
| `add_eml` | function | `add_eml(a, b) -> float` | `a + b` via EML (11 nodes) |
| `mul_eml` | function | `mul_eml(a, b) -> float` | `a × b` via EML (13 nodes) |
| `div_eml` | function | `div_eml(a, b) -> float` | `a / b` via EML (~15 nodes) |
| `pow_eml` | function | `pow_eml(a, n) -> float` | `a^n` via EML (15 nodes) |
| `recip_eml` | function | `recip_eml(x) -> float` | `1/x` via EML (5 nodes) |
| `_NODE_COSTS` | dict | `{op: {family: int}}` | Per-operation node cost table |
| `IDENTITIES` | dict | `{name: str}` | Human-readable EML identities |

Example: `from monogate.core import op; op(1.0, 1.0)  # → e - 0 = e`

---

### `monogate.network`

| Name | Type | Signature | Description |
|------|------|-----------|-------------|
| `EMLTree` | class | `EMLTree(depth=3)` | Trainable complete binary EML tree; all leaves scalar `nn.Parameter` |
| `EMLNetwork` | class | `EMLNetwork(in_features, depth, op_func=None)` | Vectorised EML network; leaves are `nn.Linear(in,1)` |
| `HybridNetwork` | class | `HybridNetwork(in_features, depth)` | EXL inner nodes + EML root (BEST-style) |
| `fit` | function | `fit(model, target, steps=1000, lr=5e-3, lam=0.0, log_every=100) -> list[float]` | Adam training loop; returns loss history |
| `_Leaf` | class | `_Leaf(value=1.0)` | Scalar leaf node |
| `_LinearLeaf` | class | `_LinearLeaf(in_features)` | Linear projection leaf |
| `_Node` | class | `_Node(left, right, op_fn)` | Internal binary node |
| `_build_tree` | function | `_build_tree(depth, leaf_fn, op_fn) -> nn.Module` | Recursive tree builder |

Example: `tree = EMLTree(depth=3); fit(tree, target=torch.tensor(math.pi), lam=0.001)`

---

### `monogate.optimize`

| Name | Type | Signature | Description |
|------|------|-----------|-------------|
| `best_optimize` | function | `best_optimize(expr_or_func, **kwargs) -> OptimizeResult` | Static BEST analysis of expression/code/callable |
| `context_aware_best_optimize` | function | `context_aware_best_optimize(expr_or_func, dynamic=False, stability_threshold=10, sample_inputs=None, warn=True) -> ContextAwareResult` | BEST analysis + optional AST depth flags + numerical profiling |
| `OptimizeResult` | dataclass | frozen | Fields: original, ops, total_best_nodes, total_eml_nodes, savings_pct, python_snippet, rewritten_code, explanation, message |
| `ContextAwareResult` | dataclass | mutable | Fields: base_result, stability_issues, dynamic_profile, diagnostics |
| `OpMatch` | dataclass | frozen | One detected operation: name, count, best_nodes, eml_nodes, best_op, note; `.savings` property |
| `StabilityWarning` | dataclass | frozen | op, max_depth, count, suggestion |
| `BestRewriter` | class | `ast.NodeTransformer` | Rewrites math calls to `BEST.*` in AST |

Example: `r = best_optimize("sin(x)**2 + exp(-x)"); print(r.savings_pct)  # → 74`

---

### `monogate.torch_ops`

| Name | Type | Description |
|------|------|-------------|
| `op` | function | PyTorch tensor EML: `exp(a) - softplus(b)` |
| `exl_op` | function | PyTorch EXL: `exp(a) * softplus(b)` |
| `edl_op_safe` | function | PyTorch EDL: `exp(a) / (softplus(b) + eps)` |

---

### `monogate.torch.EMLLayer`

```python
EMLLayer(
    in_features: int,
    out_features: int,
    depth: int = 2,
    operator: str = "EML",    # 'EML'|'EDL'|'EXL'|'BEST'
    mode: str = "activation", # 'activation'|'tree'
    init: float = 1.0,
    compiled: bool = False,   # Rust > Fused > Standard auto-select
)
```

- `forward(x: Tensor) -> Tensor`: `(batch, in) → (batch, out)`
- `.formula(feature_names) -> str | list[str]`: human-readable expression
- `.compile(**kwargs) -> nn.Module`: torch.compile wrapper
- `.n_eml_nodes`: total internal node count
- `.n_parameters`: total trainable parameter count
- `extra_repr()`: shows `backend=rust` or `backend=fused` when compiled

Mode `'activation'`: Linear(in,out) → EMLActivation (shared tree). Mode `'tree'`: `out_features` independent EML trees with linear leaves.

Example: `layer = EMLLayer(256, 256, depth=2, operator="BEST", compiled=True)`

---

### `monogate.torch.EMLActivation`

```python
EMLActivation(depth: int = 2, operator: str = "EML")
```

- `forward(x: Tensor) -> Tensor`: element-wise, any shape
- `.formula(feature_name="x") -> str`

Example: `act = EMLActivation(depth=2); y = act(torch.randn(32, 64))`

---

### `monogate.fused_rust`

| Name | Type | Description |
|------|------|-------------|
| `get_best_activation(depth, operator) -> nn.Module` | function | Returns fastest backend: RustFusedLayer > FusedEMLActivation > EMLActivation |
| `RUST_AVAILABLE` | bool | True if monogate-core is installed |
| `rust_info()` | function | Prints version, speedup, batch threshold |
| `FusedEMLActivation` | class | Pure-Python fused kernel; depth 1–3; 3.6× speedup |
| `RustFusedLayer` | class | PyO3 wrapper; calls `eval_eml_batch` from monogate-core |

Example: `act = get_best_activation(depth=2, operator="BEST")  # auto-selects Rust`

---

### `monogate.complex_eval`

| Name | Signature | Description |
|------|-----------|-------------|
| `complex_eml_sin(x)` | `(float) -> float` | `Im(eml(ix, 1)) = sin(x)` exactly |
| `complex_eml_cos(x)` | `(float) -> float` | `Re(eml(ix, 1)) = cos(x)` exactly |
| `complex_eml_eval(tree, x)` | `(node, complex) -> complex` | Evaluate EML tree over complex domain |

Example: `from monogate.complex_eval import complex_eml_sin; complex_eml_sin(1.5708)  # → 1.0`

---

### `monogate.search`

| Name | Signature | Description |
|------|-----------|-------------|
| `mcts_search(target_fn, probe_points=None, depth=5, n_simulations=10_000, seed=42) -> MCTSResult` | function | MCTS over EML grammar; UCB1; reward=1/(1+MSE) |
| `beam_search(target_fn, depth=4, beam_width=50, ...) -> MCTSResult` | function | Beam search over EML grammar |
| `analyze_n11(path=None) -> dict` | function | Load sin_n11.json; print N=1–11 table; near-miss gallery; `--html PATH` export |
| `MCTSResult` | dataclass | best_tree, best_mse, best_formula, history |

Example: `result = mcts_search(math.exp, depth=3, n_simulations=2000)  # finds eml(x,1) exactly`

---

### `monogate.llm`

| Name | Signature | Description |
|------|-----------|-------------|
| `suggest_and_optimize(prompt, backend="mock") -> str` | function | LLM → BEST expression; backends: mock, openai, groq, anthropic |

CLI: `monogate-optimize "sigmoid function"` — prints BEST EML expression + node count.

---

### `monogate.special`

15 pre-computed CBEST/BEST expressions. `CATALOG` dict maps name → `SpecialFnEntry`.

| Function | Nodes | Backend | Max error | Notes |
|----------|-------|---------|-----------|-------|
| sin, cos | 1 | CBEST | 1e-15 | Exact — Im/Re(eml(ix,1)) |
| sinh, cosh | 9, 15 | BEST | 1e-14 | Exact algebraic |
| tanh, sech | 8, 16 | BEST | 1e-14 | Exact algebraic |
| erf | 5 | CBEST | 1.5e-2 | tanh(1.2025x) approximation |
| Fresnel S/C integrand | 2 | CBEST | 1e-15 | Im/Re(eml(i·πx²/2, 1)) |
| Fresnel S/C | 2 | CBEST | 1e-6 | Quadrature of integrand |
| Bessel J₀ | 7 | CBEST | 1e-4 | Complex MCTS depth-3 |
| Airy Ai | 9 | CBEST | 2e-3 | Complex MCTS depth-3 |
| lgamma | 12 | BEST | 1e-9 | Stirling series |
| digamma | 14 | BEST | 1e-8 | Central differences of lgamma |

Callables: `sin_cb, cos_cb, sinh_cb, cosh_cb, tanh_cb, sech_cb, erf_cb, fresnel_s_cb, fresnel_c_cb, fresnel_s_integrand_cb, fresnel_c_integrand_cb, j0_cb, ai_cb, lgamma_cb, digamma_cb`

---

### `monogate.leaderboard`

| Name | Description |
|------|-------------|
| `PROBLEMS` | dict of 10 `BenchmarkProblem` (Nguyen/Keijzer suite) |
| `run_leaderboard(...)` | Run MCTS + beam search; return `list[LeaderboardEntry]` |
| `print_leaderboard(entries)` | Console table |
| `markdown_leaderboard(entries) -> str` | Markdown table string |
| `save_leaderboard / load_leaderboard` | JSON persistence |

Results saved to `results/leaderboard.json`. GitHub Actions auto-refreshes daily.

---

### `monogate.pinn`

```python
EMLPINN(equation, backbone_depth, omega, nu, k, c, alpha, beta, lam_physics)
fit_pinn(model, x_data, y_data, x_phys, steps, lam_physics, log_every) -> PINNResult
```

Equations: `harmonic`, `burgers`, `heat`, `schrodinger`, `kdv_soliton`, `nls`, `lotka_volterra`.

`PINNResult` fields: `data_loss`, `physics_loss`, `formula`, `elapsed_s`, `history`.

Key result: Schrödinger free-particle solution `exp(ikx)` = 1 CBEST node.

---

### `monogate.interval`

```python
Interval(lo, hi)                        # frozen dataclass; .width, .midpoint, .contains()
eml_interval(a, b) -> Interval          # tight certified bounds
eval_interval(tree, x_interval)         # propagate through full EML tree
bound_expression(expr_str, x_lo, x_hi) # parse formula string → certified bounds
```

---

### `monogate.sympy_bridge` *(optional: `pip install monogate[sympy]`)*

```python
to_sympy(tree)          # EML tree dict → SymPy expression
from_sympy(expr)        # SymPy → EML tree (exp/log only, best-effort)
simplify_eml(tree)      # to_sympy + sympy.simplify()
latex_eml(tree)         # LaTeX string via sympy.latex()
verify_identity(t1, t2) # symbolic equality check
```

---

## 4. Research Results

### N=1–11 Exhaustive Search

Complete enumeration of EML trees with terminals {1, x}, using exact parity filter (sin is odd).

| N  | Catalan | Assignments | Raw trees       | After parity    | Cumulative      | Result |
|----|---------|-------------|-----------------|-----------------|-----------------|--------|
| 1  | 1       | 4           | 4               | 2               | 4               | 0      |
| 2  | 2       | 8           | 16              | 8               | 20              | 0      |
| 3  | 5       | 16          | 80              | 40              | 100             | 0      |
| 4  | 14      | 32          | 448             | 224             | 548             | 0      |
| 5  | 42      | 64          | 2,688           | 1,344           | 3,236           | 0      |
| 6  | 132     | 128         | 16,896          | 8,448           | 20,132          | 0      |
| 7  | 429     | 256         | 109,824         | 54,912          | 129,956         | 0      |
| 8  | 1,430   | 512         | 732,160         | 366,080         | 862,116         | 0      |
| 9  | 4,862   | 1,024       | 4,978,688       | 2,489,344       | 5,840,804       | 0      |
| 10 | 16,796  | 2,048       | 34,398,208      | 17,199,104      | 40,239,012      | 0      |
| **11** | **58,786** | **4,096** | **240,787,456** | **208,901,719** | **281,026,468** | **0** |

N=11 runtime: **323 seconds** (~5.4 min) on a single CPU using vectorised NumPy batch evaluator.
Tolerances checked: 1e-4, 1e-6, 1e-9. Zero candidates at all three.

### Top-10 Near-Miss Gallery (from sin_n11.json)

| Rank | MSE | Leaves | Method | Formula (abbreviated) |
|------|-----|--------|--------|----------------------|
| 1 | 1.4781e-04 | 12 | exhaustive | eml(eml(eml(x,1),eml(1,1)), eml(eml(eml(eml(x,1),eml(1,1)),eml(x,1)),eml(x,1))) |
| 2 | 1.4822e-04 | 12 | exhaustive | eml(eml(1,1),eml(eml(eml(1,1),eml(x,1)),eml(eml(eml(eml(x,1),eml(1,1)),1),1))) |
| 3 | 2.5052e-04 | 12 | exhaustive | eml(x,eml(1,eml(x,eml(eml(eml(x,eml(x,1)),eml(eml(1,eml(x,1)),eml(x,1))),1)))) |
| 4 | 3.1694e-04 | 12 | exhaustive | eml(1,eml(eml(1,eml(x,1)),eml(1,eml(eml(x,1),eml(eml(x,eml(eml(1,1),1)),1))))) |
| 5 | 2.80e-01   | 4  | beam       | eml(eml(x,eml(1,x)),1) |
| 6 | 3.10e-01   | 3  | MCTS       | eml(eml(x,x), 1) |
| — | 0.0        | 1  | exact      | Im(eml(i·x, 1)) [complex domain] |

Best real-domain result is **2,842× closer** to sin(x) than the trivial baseline `eml(x,1) = exp(x)` (MSE~0.42).

### Phantom Attractor Results

- Target: pi (depth-3 EMLTree, Adam, lr=5e-3, 3000 steps, 40 seeds)
- lambda=0: **0/40** reach pi; all converge to attractor **~3.169642** (MSE~9e-4)
- lambda=0.001: **20/20** reach pi (lambda_crit confirmed)
- lambda=0.005: **40/40** reach pi (MSE < 1e-8)
- Attractor identity: unknown — not pi, e, any known simple closed form, or small rational.
- Depth-4: untrainable; overflow to NaN/inf before step 1000 in all seeds.

### The Infinite Zeros Barrier

**Theorem:** No finite real-valued EML tree T with terminals {1, x} satisfies T(x) = sin(x) for all x in R.

**Proof sketch:** Every finite EML tree is real-analytic. A non-zero real-analytic function on R has only finitely many zeros. sin(x) has zeros at {k*pi : k in Z} — infinitely many. Contradiction.

**Corollary:** The result extends to cos(x), Bessel J0(x), Airy Ai(x), and any real-analytic function with infinitely many real zeros.

### Complex Bypass

    Im(eml(ix, 1)) = Im(exp(ix) - ln(1)) = Im(e^(ix)) = sin(x)

One node. Machine precision. The barrier is real-domain only.

```python
import cmath
def sin_eml(x): return cmath.exp(1j * x).imag
# or: from monogate.complex_eval import complex_eml_sin
```

---

## 5. Benchmarks

### EMLLayer Performance (depth=2, 256→256, batch=1024, CPU)

| Backend | ms/step | Speedup | Activation |
|---------|---------|---------|------------|
| Standard (recursive Python) | 8.3 | 1x | default |
| FusedEMLActivation | 2.3 | **3.6x** | `compiled=True` (no Rust) |
| FusedEMLActivation + torch.compile | 1.9 | **4.4x** | `.compile()` |
| **Rust (monogate-core)** | **1.4** | **5.9x** | `compiled=True` + monogate-core |
| torch.sin (native ceiling) | 0.04 | **205x** faster than EML baseline | fundamental limit |

The 205x gap to `torch.sin` is a fundamental Python overhead ceiling, not addressable without a C/CUDA rewrite of the full tree evaluation.

### BEST Routing Wall-Clock (Python scalars, CPU)

| Workload | Savings | Speedup |
|----------|---------|---------|
| sin/cos Taylor (TinyMLP) | 74% | **2.8x** |
| Polynomial x^4+x^3+x^2 | 54% | **2.1x** |
| GELU (Transformer FFN) | 18% | 0.93x |

Linear fit (R^2=0.9992): `speedup ~= 0.033 * savings_pct + 0.32`

**Crossover threshold**: ~20% node savings. Below this, Python call overhead dominates.

### SIREN Comparison (notebooks/siren_with_monogate.py)

Target: 2D Gaussian mixture, [-1,1]^2, 1000 steps, hidden=64, depth=2.
EMLSirenNet (BEST, compiled=True) vs SirenNet (sin, SIREN init).
Results: EML-SIREN converges; PSNR and training speed not yet competitive with tuned sin-SIREN (sin-SIREN has purpose-built frequency scaling). Ongoing work.

### Taylor Series Node Counts

| Terms | BEST nodes | EML-only nodes | Max error |
|-------|------------|----------------|-----------|
| 8 | 63 | 245 | 7.7e-7 |
| 13 | 108 | 420 | 6.5e-15 |

---

## 6. Version History

### v0.5.0
- `monogate.torch`: EMLLayer, EMLActivation — differentiable PyTorch layers, ONNX opset 14
- `monogate.search`: MCTS and Beam Search over EML grammar
- `monogate.complex_eval`: Im(eml(ix,1))=sin(x), complex_eml_sin/cos
- N=10 exhaustive search: 40,239,012 trees, zero candidates
- Phase transition refined: lambda_crit = 0.001 for depth=3

### v0.6.0
- `monogate.compile`: FusedEMLLayer, FusedEMLActivation (1.5–3.6x CPU speedup)
- `EMLLayer(compiled=True)`: one-liner fused activation
- `monogate.llm`: suggest_and_optimize(); monogate-optimize CLI
- New benchmarks: kernel_benchmarks.py; notebooks: performance_kernels.py, llm_optimizer_demo.py
- 593 passing tests

### v0.7.0 (Phase 5)
- Challenge Board v2 (monogate-validate): 10 open problems, GitHub Action auto-validation
- Explorer Research tab: exhaustive search table, MCTS live search, near-miss gallery
- Explorer Leaderboard tab
- Rust core (monogate-core/): PyO3 extension, rayon parallel, 50–200x vs Python scalar

### v0.7.1 (Phase 6 — N=11 Results Hardening)
- `monogate/search/analyze_n11.py`: N=1–11 table, near-miss gallery, HTML export
- `RESULTS.md`: full N=1–11 table + top-10 near-miss gallery
- `paper/preprint.tex`: N=11 subsection added
- `ResearchTab.jsx`: N=11 marked complete, green banner, real near-miss data
- Version: 0.7.0 → 0.7.1

### v0.8.0 (Phase 7 — arXiv Prep)
- Preprint fully rewritten: 5-contribution abstract, performance section §8, all labels
- `monogate/fused_rust.py`: `get_best_activation()`, Rust-first priority chain
- `EMLLayer(compiled=True)`: now calls `get_best_activation()`; `extra_repr()` shows backend
- `notebooks/siren_with_monogate.py`: EML-SIREN vs sin-SIREN comparison
- `assets/n11_share_card.md`: shareable summary
- README rewritten: leads with N=11, performance table, Rust install
- 641 tests passing

### v0.8.1 (Phase 8 — arXiv Submission Polish)
- `arxiv_submission_notes.md`: abstract ≤250w, categories, post-submission checklist
- `paper/README.md`: exact 5-step arXiv upload + Docker option + full checklist
- Explorer: ResearchTab paper banner; LeaderboardTab arXiv reference banner
- README: "Now on arXiv" notice placeholder, BibTeX, What's next section
- ANNOUNCEMENT.md: launch posts for HN, r/ML, r/math, X, LinkedIn

### v0.9.0 (Phase 9 — Public Launch)
- `scripts/update_arxiv_id.py`: one-command post-submission ID update (dry-run, backups)
- ANNOUNCEMENT.md fully polished
- ResearchTab: live arXiv URL logic; "Cite this work" BibTeX dropdown
- assets/n11_share_card.md: BibTeX block, BEST example, performance table

### v0.10.0 (Session 1 — Special Functions Library)
- `monogate.special`: 15 pre-computed CBEST/BEST expressions; CATALOG dict; SpecialFnEntry
- `monogate.complex_best`: CBEST class, im/re helpers, node-count constants
- `monogate.complex_search`: MCTS over complex EML grammar
- Key identity: `fresnel_s_integrand(x) = Im(eml(i·πx²/2, 1))` — 2 nodes, exact
- New notebook: `complex_special_functions.py`

### v0.11.0 (Sessions 2 + 4 + 5 — Research Extensions)
- **Session 2:** `monogate.leaderboard` — 10 Nguyen/Keijzer problems; GitHub Actions daily refresh; `update_leaderboard.py` script; `LEADERBOARD.md`
- **Session 4:** `monogate.pinn` extended — Schrödinger, KdV, NLS, Lotka-Volterra; key result: free-particle solution = 1 CBEST node
- **Session 5:** `monogate.interval` — certified interval arithmetic; `monogate.sympy_bridge` — SymPy interop (`[sympy]` extra); `attractor_generalization.py` notebook confirms phantom attractor is EML-specific
- 913 tests passing, 0 failed

### v0.12.0-dev (Session 3 — Streamlit Web Demo, current)
- `streamlit_app.py`: 5-tab Streamlit demo (Optimizer, Special Functions, PINN, MCTS Explorer, Phantom Attractor)
- `requirements.txt`: Streamlit Cloud deps (no torch required)
- `[streamlit]` optional dep group in `pyproject.toml`
- Streamlit Cloud badge + "Run locally" block in README
- **Status:** all 5 sessions done; ready to merge → master + cut v0.12.0 PyPI release

---

## 7. Open Problems

### Six Open Research Problems (from README "What's next")

1. **N=12 search** — Catalan(12)=208,012 shapes x 2^13 ~= 1.7 billion trees. Requires GPU parallelism or distributed evaluation. Barrier theorem already rules out real-valued matches; empirical value is extending coverage and finding better near-misses.

2. **Minimax-optimal EML approximations** — What is the best uniform approximation to sin(x) achievable with exactly k EML nodes? (Chebyshev-style bounds rather than MSE.)

3. **Complex BEST routing** — Does EDL or EXL reduce node count for functions expressed via complex EML (exp(ix), Bessel, Airy)? No systematic survey exists.

4. **EDL additive completeness** — Does a finite EDL tree using complex terminals produce exact `a + b` for arbitrary real a, b? Structural argument suggests no; formal proof missing.

5. **GPU-accelerated search** — PyTorch tensor evaluation across all leaf assignments in parallel; would make N=13+ viable.

6. **arXiv response cycle** — Address reviewer feedback post-submission; potentially extend to EDL proofs.

### Ten Challenge Board Problems (monogate.dev/board)

| Problem | Difficulty | Points | Status |
|---------|-----------|--------|--------|
| sin(x) | impossible_real | 50 | open — exact: Im(eml(ix,1)) in complex |
| cos(x) | impossible_real | 30 | open — real-domain barrier applies |
| Lambert W0(x) | hard | 15 | open — near_miss: MSE~0.012 at 3 nodes |
| erf(x) | hard | 12 | open |
| Airy Ai(x) | very_hard | 20 | open — Barrier corollary applies |
| Bessel J0(x) | very_hard | 15 | open — Barrier corollary applies |
| exp(-x^2) | easy | 4 | challenge |
| softplus(x) exact | medium | 5 | challenge |
| swish(x) | medium | 6 | open |

Leaderboard submissions via JSON: `{"problem_id": "sin_x", "formula": "...", "submitter": "handle", "notes": ""}`.

---

## 8. Paper Status

**Title:**
> Practical Extensions to the EML Universal Operator: Hybrid Routing, Phantom Attractors, Performance Kernels, and the N=11 Sin Barrier

**Author:** Art Almaguer (almaguer1986@gmail.com)

**arXiv ID:** ARXIV_ID_PLACEHOLDER *(run `python scripts/update_arxiv_id.py <id>` after submission)*

**Status:** Submission-ready as of v0.9.0 (April 2026). LaTeX compiles clean (zero errors, zero undefined references). All checklist items in `paper/README.md` satisfied except figure placeholder for `fig:attractor` (replace `\fbox{...}` with `\includegraphics{figures/attractor_landscape}` after running `plot_attractor_landscape.py`).

**Five Contributions:**

1. **BEST hybrid routing** — per-primitive dispatch to EML/EDL/EXL; 52% average and 74% sin/cos node savings; 2.8x wall-clock speedup; zero accuracy loss.

2. **Phantom attractors** — depth-3 EMLTree fits to pi fail 40/40 without regularisation (attractor ~3.1696); lambda_crit=0.001 induces sharp phase transition to 40/40 convergence.

3. **Infinite Zeros Barrier + N=11 search** — structural theorem rules out real-valued sin(x) for all N; confirmed by 281,026,468-tree exhaustive search (N<=11, 323s); complex bypass Im(eml(ix,1))=sin(x) exact in one node.

4. **Performance kernels** — FusedEMLActivation (3.6x), monogate-core Rust (5.9x), EMLLayer(compiled=True) auto-selects fastest backend; torch.compile support.

5. **PyTorch integration** — EMLLayer drop-in nn.Module for SIREN/NeRF/PINN; ONNX opset 17; state_dict() serialisation; two modes (activation/tree).

**BibTeX:**

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

**arXiv categories:** cs.SC (primary), cs.LG, math.NA

**MSC classes:** 68W30 (symbolic computation), 65D15 (functional approximation)

**Source:** `paper/preprint.tex` — build with `pdflatex preprint.tex` (twice for cross-refs). All packages standard TeX Live 2022+; no custom .sty files.

---

*Generated for monogate v0.12.0-dev — April 2026*
*Branch: `phase9-arxiv-live` — next: merge → master, cut v0.12.0 PyPI release*
*Update ARXIV_ID_PLACEHOLDER throughout by running: `python scripts/update_arxiv_id.py <id>`*
