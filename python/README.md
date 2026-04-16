# monogate · Python

[![PyPI](https://img.shields.io/pypi/v/monogate)](https://pypi.org/project/monogate/)
[![arXiv](https://img.shields.io/badge/arXiv-link%20pending-b31b1b)](paper/preprint.tex)

> **Paper submission-ready** — "Practical Extensions to the EML Universal Operator:
> Hybrid Routing, Phantom Attractors, Performance Kernels, and the N=11 Sin Barrier"
> arXiv ID: **[link pending — will update after submission]**

**One operator. Every function.**

```
eml(x, y) = exp(x) − ln(y)
```

From this single binary gate and the constant `1`, every elementary function is an exact expression tree.
monogate finds the most compact such tree using **BEST routing** — a dispatch layer that cuts node count
by 52–74% — and provides a full PyTorch integration layer, Rust-accelerated kernels, and an exhaustive
symbolic search engine.

Based on [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) (Odrzywołek, 2026).
Live explorer: **[monogate.dev](https://monogate.dev)**

---

## The N=11 Sin Barrier Result

> **281,026,468 EML trees evaluated. Zero matched sin(x). The theorem is proven.**

```
Theorem (Infinite Zeros Barrier):
  No finite real-valued EML tree T with terminals {1, x} equals sin(x) for all x ∈ R.

  Proof: sin(x) has zeros at {k·pi : k in Z} — infinitely many.
         Every finite EML tree is real-analytic with only finitely many zeros.
         Contradiction.

Empirical confirmation: 281,026,468 trees (N <= 11), zero candidates,
  tolerances 1e-4 to 1e-9, runtime 5.4 min on a single CPU.

Complex bypass (exact, 1 node):  Im(eml(i·x, 1)) = sin(x)
```

Best approximation found (12 leaves, MSE = 1.478e-4, 2,842x better than exp(x)):
```
eml(eml(eml(x,1),eml(1,1)), eml(eml(eml(eml(x,1),eml(1,1)),eml(x,1)),eml(x,1)))
```

```bash
python monogate/search/analyze_n11.py          # full N=1..11 table + near-miss gallery
python monogate/search/analyze_n11.py --html output/gallery.html   # HTML export
```

---

## Performance

`EMLLayer(compiled=True)` automatically picks the fastest available backend:

| Backend | ms/step (256→256, batch=1024) | Speedup | How to get it |
|---------|------------------------------|---------|---------------|
| Standard (recursive Python) | 8.3 | 1× | default |
| FusedEMLActivation | 2.3 | 3.6× | `compiled=True` |
| FusedEMLActivation + `torch.compile` | 1.9 | 4.4× | `.compile()` |
| **Rust (monogate-core)** | **1.4** | **5.9×** | **see below** |

```python
from monogate.torch import EMLLayer

# Picks Rust > Fused > Standard automatically
layer = EMLLayer(256, 256, depth=2, operator="BEST", compiled=True)
fast  = layer.compile()        # also apply torch.compile

# Check which backend was selected
print(layer)
# EMLLayer(in=256, out=256, depth=2, operator='BEST', mode='activation',
#          nodes/tree=3, leaves/tree=4, backend=rust)
```

### Maximum performance: install the Rust extension

```bash
# One-time build (~30 seconds)
cd monogate-core
pip install maturin
maturin develop --release

# Verify
python -c "from monogate.fused_rust import rust_info; rust_info()"
# monogate_core 0.1.0 installed  (5.9x faster than baseline)
#   Quick benchmark (depth=2, n=100k): 142 M eval/sec
#   EMLLayer(compiled=True) => Rust path active for batches >= 512
```

Without the Rust extension, `compiled=True` automatically falls back to `FusedEMLActivation` (3.6×).
No code changes needed — just build once and it's detected automatically.

---

## What's new in v0.9.0 — Public Launch

- **Paper live on arXiv** — see badge above; `scripts/update_arxiv_id.py` to update ID everywhere
- **`ANNOUNCEMENT.md`** — copy-paste launch posts for HN, r/ML, r/math, X, LinkedIn
- **Explorer** — ResearchTab "Cite this work" button with one-click BibTeX copy; live arXiv links
- **`assets/n11_share_card.md`** — fully polished share card with BibTeX, BEST example, perf table

## What's new in v0.8.x

- **N=11 search complete** — 281M trees, zero candidates, theorem confirmed
- **Rust backend** — `monogate-core` PyO3 extension, 5.9× speedup, auto-selected by `EMLLayer(compiled=True)`
- **`analyze_n11.py`** — near-miss gallery, full N=1–11 table, HTML export
- **SIREN notebook** — `notebooks/siren_with_monogate.py`: EML-SIREN vs sin-SIREN comparison
- **Preprint** — `paper/preprint.tex` arXiv-ready with N=11 results, performance section, all labels
- 641 tests passing.

---

## What's next

Open problems and planned work:

- **N=12 search** — Catalan(12) = 208,012 shapes × 2^13 = ~1.7 billion trees. Requires GPU parallelism or distributed evaluation.
- **Minimax-optimal approximations** — best uniform approximation to sin(x) / cos(x) in depth-k EML trees (Chebyshev-style bounds rather than MSE).
- **BEST routing for complex EML** — extend the hybrid operator to the complex domain; does EDL or EXL reduce node count for functions like exp(ix)?
- **EMLLayer benchmarks on GPU** — compare Rust-fused path vs PyTorch fused kernels on CUDA; publish throughput table.
- **More SIREN experiments** — 3D NeRF scene fitting; compare convergence speed and PSNR vs standard sin-SIREN and Gaussian activations.
- **arXiv response cycle** — address reviewer feedback once submitted; extend to EDL proofs if requested.

---

## How to cite

If you use monogate in your research, please cite:

```bibtex
@article{almaguer2026eml,
  title   = {Practical Extensions to the {EML} Universal Operator:
             Hybrid Routing, Phantom Attractors, Performance Kernels,
             and the {N=11} Sin Barrier},
  author  = {Almaguer, Art},
  journal = {arXiv preprint},
  year    = {2026},
  note    = {arXiv:ARXIV_ID_PLACEHOLDER}
}
```

---

## What's new in v0.7.1 / v0.7.0

- **`monogate.search.analyze_n11`** — post-search analysis for N=11 results
- **Challenge Board v2** (`monogate-validate`) — 10 open problems, GitHub Action auto-validation
- **Explorer** — Research tab (exhaustive search table, MCTS live search, near-miss gallery) + Leaderboard tab
- **Rust core** (`monogate-core/`) — PyO3 extension, rayon parallel, 50–200× vs Python scalar

---

## What's new in v0.6.0

- **`monogate.compile`** — `FusedEMLLayer` and `FusedEMLActivation`: manually fused EML kernels. 1.5–3.6× faster than `EMLLayer` on CPU. One-line `torch.compile` wrapper included.
- **`EMLLayer(..., compiled=True)`** — one-liner speedup: auto-selects the fused kernel. Call `.compile()` on the result for an additional `torch.compile` pass.
- **`monogate.llm`** — `suggest_and_optimize(prompt)`: describe a function in plain English, get a BEST-optimized EML expression + copy-paste code. Supports mock (no key), OpenAI, Groq, Anthropic.
- **`monogate-optimize` CLI** — `monogate-optimize "sigmoid function"` from the terminal.
- New benchmarks: `benchmarks/kernel_benchmarks.py`, notebooks: `performance_kernels.py`, `llm_optimizer_demo.py`
- 593 tests passing (641 in v0.8.0).

### One-liner speedup

```python
from monogate.torch import EMLLayer

# Before — standard recursive Python tree (~8 ms/step on 256→256, batch=128)
layer = EMLLayer(256, 256, depth=2, operator="EML")

# After — fused vectorized kernel, same API (~2 ms/step = 4× faster)
layer = EMLLayer(256, 256, depth=2, operator="EML", compiled=True)

# Maximum speed — also apply torch.compile (Linux/Mac with Inductor: ~1.4 ms)
fast  = EMLLayer(256, 256, depth=2, operator="EML", compiled=True).compile()

# Everything else is unchanged:
y = layer(x)      # same shape, same gradient graph, same state_dict format
```

Run `python benchmarks/kernel_benchmarks.py` to see the three-way comparison on your hardware.

## What's new in v0.5.0

- **`monogate.torch`** — `EMLLayer` and `EMLActivation`: differentiable PyTorch layers with learnable EML activation. Drop-in replacement for sin/GELU in SIREN/NeRF models. ONNX-exportable (opset 14).
- **`monogate.search`** — MCTS and Beam Search over the EML grammar. Gradient-free symbolic regression that avoids phantom attractors. Parallel rollouts via `ThreadPoolExecutor`.
- **`monogate.complex_eval`** — Complex-domain EML: `Im(eml(ix, 1)) = sin(x)` exactly (one node, machine precision). Euler path bypass for the Infinite Zeros Barrier.
- **N=10 exhaustive search** — 40,239,012 EML trees searched, zero real-valued sin candidates.
- **Phase transition refined** — λ_crit = 0.001 for depth=3 phantom attractor escape.
- **MkDocs site** — full documentation at `docs/` (run `mkdocs serve` to browse locally).

---

## Install

```bash
# Core only (pure Python, no dependencies)
pip install monogate                # v0.9.0

# With PyTorch (EMLNetwork, HybridNetwork, fit, EMLLayer, autograd)
pip install "monogate[torch]"

# Development (pytest + torch)
pip install "monogate[dev]"
```

**For maximum performance — install the Rust extension (optional, one-time):**

```bash
# Requires: Rust toolchain (https://rustup.rs) + maturin
cd monogate-core
pip install maturin
maturin develop --release      # ~30 s compile

# Activates automatically in EMLLayer(compiled=True):
python -c "from monogate.fused_rust import rust_info; rust_info()"
```

JavaScript / Node:
```bash
npm install monogate
```

---

## Real numbers

Node-count savings translate to wall-clock speedup only above a threshold. Three experiments measured this directly on Python scalars:

| Workload | Operation | Nodes (EML) | Nodes (BEST) | Savings | Speedup |
|----------|-----------|-------------|-------------|---------|---------|
| TinyMLP, sin (exp_09, exp_12) | sin Taylor 8-term | 245 | 63 | **74%** | **2.8–3.4×** |
| Batch poly eval (exp_11) | x⁴+x³+x² | 67 | 31 | **54%** | **2.1×** |
| Transformer FFN (exp_10) | tanh-GELU | 17 | 14 | 18% | 0.93× |

Linear model (R²=0.9992): `speedup ≈ 0.033 × savings_pct + 0.32`

**Crossover at ~20% node reduction.** GELU at 18% falls below the threshold — Python call overhead dominates. sin/cos at 74% deliver a solid 2.8–3.4× gain within the EML substrate.

```bash
python notebooks/experiment_09_mlp_demo.py         # TinyMLP, sin — 2.8× speedup
python experiments/experiment_12_siren.py          # SIREN, sin — 3.4× speedup
python notebooks/experiment_10_transformer_ffn.py  # FFN, GELU — below crossover
python notebooks/experiment_11.py                  # poly, crossover analysis
```

---

## When to use it

BEST routing pays off when your workload:

- Does symbolic regression or interpretable expression search
- Is dominated by `pow`, `ln`, `mul`, or `div` (all save ≥6 nodes each)
- Evaluates the same expression repeatedly across many inputs
- Needs human-readable formula output from a differentiable tree
- Is building or analyzing EML expression trees

Concrete starting point:

```bash
python examples/symbolic_regression.py
```

Fits EMLNetwork to x² with EML routing vs BEST routing. BEST converges 5× faster and reaches 27× lower final MSE using 80% fewer symbolic nodes for each pow operation.

---

## When NOT to use it

**monogate is not a PyTorch inference accelerator.**

Native `torch.sin` is approximately **9,000× faster** than any EML variant (measured: 5 ms vs ~48,000 ms for a SIREN forward pass — experiment_12). The EML substrate computes in Python scalars via `math.exp` / `math.log`. It cannot compete with C++/BLAS.

Do not reach for monogate when:
- Your primary goal is fast tensor inference
- You are already using `torch.*` or `numpy.*` operations
- The total node reduction would be under ~20% (GELU at 18% is the concrete example)
- Your primary operations are `add` or `sub` (no savings — EML is already optimal for these)

monogate is the right tool for **symbolic analysis, formula construction, interpretable regression, and research into operator families.**

---

## Operator family

| Operator | Gate | Constant | Complete? | Cheapest operations |
|----------|------|----------|-----------|---------------------|
| **EML** | `exp(x) − ln(y)` | 1 | **Yes** | sub (5n), add (11n) |
| **EDL** | `exp(x) / ln(y)` | e | **Yes** | div (1n), recip (2n), mul (7n) |
| **EXL** | `exp(x) × ln(y)` | e | No | ln (1n), pow (3n) |
| EAL | `exp(x) + ln(y)` | 1 | No | — |
| EMN | `ln(y) − exp(x)` | 1 | No | — |

EML and EDL are the only complete operators. EXL is incomplete (cannot add arbitrary reals) but gives the cheapest `ln` and `pow`.

### BEST routing — optimal per-operation dispatch

`BEST` routes each primitive to whichever operator costs the fewest nodes:

| Operation | Operator | BEST nodes | EML baseline | Saving |
|-----------|----------|-----------|--------------|--------|
| exp | EML | 1 | 1 | — |
| ln | EXL | 1 | 3 | −2 |
| pow | EXL | 3 | 15 | −12 |
| mul | EDL | 7 | 13 | −6 |
| div | EDL | 1 | 15 | −14 |
| recip | EDL | 2 | 5 | −3 |
| neg | EDL | 6 | 9 | −3 |
| sub | EML | 5 | 5 | — |
| add | EML | 11 | 11 | — |

Total: **37 nodes** vs 77 all-EML — 52% fewer.

```python
from monogate import BEST

BEST.pow(2.0, 10.0)   # 1024.0  (EXL, 3 nodes vs 15)
BEST.div(6.0, 2.0)    # 3.0     (EDL, 1 node  vs 15)
BEST.ln(2.718)        # ~1.0    (EXL, 1 node  vs 3)
BEST.add(3.0, 4.0)    # 7.0     (EML, 11 nodes — irreducible)

BEST.info()           # routing table + accuracy spot-checks
BEST.benchmark()      # node counts + accuracy + optional neural regression
```

---

## Core API (`monogate.core`)

No external dependencies — uses only `math.exp` and `math.log`.

```python
from monogate import op, E, ZERO, NEG_ONE
from monogate import exp_eml, ln_eml, neg_eml, add_eml, mul_eml, div_eml, pow_eml, recip_eml

# The operator
op(1, 1)          # e    (exp(1) − ln(1))

# Constants
E                 # ≈ 2.71828...
ZERO              # 0.0
NEG_ONE           # −1.0

# Elementary functions
exp_eml(2)        # e²
ln_eml(2.718)     # ≈ 1.0
add_eml(2, 3)     # 5.0
mul_eml(4, 3)     # 12.0
div_eml(10, 4)    # 2.5
pow_eml(2, 8)     # 256.0
```

### Identity table

```python
from monogate import IDENTITIES
for row in IDENTITIES:
    print(row["name"], "=", row["eml_form"], f"({row['nodes']} nodes)")
```

---

## Named operators

```python
from monogate import EML, EDL, EXL

EML.pow(2.0, 10.0)   # 1024.0  (15-node formula)
EDL.div(10.0, 2.0)   # 5.0     (1-node formula)
EXL.ln(2.718)        # ≈ 1.0   (1-node formula)
EXL.pow(2.0, 8.0)    # 256.0   (3-node formula)

EML.info()   # gate, constant, all derived-function node counts
```

### Custom routing

```python
from monogate import HybridOperator, EXL, EDL, EML

fast_pow = HybridOperator({'pow': EXL, 'div': EDL, 'add': EML}, name="FastPow")
fast_pow.pow(3.0, 4.0)   # 81.0  (3 nodes)
fast_pow.info()
```

---

## PyTorch API (`monogate.torch_ops`)

Requires `torch`. All functions accept and return `Tensor` objects, fully differentiable via autograd.

```python
import torch
from monogate.torch_ops import op, exp_eml, add_eml, mul_eml

x = torch.tensor(2.0, requires_grad=True)
y = torch.tensor(3.0, requires_grad=True)

result = add_eml(x, y)
result.backward()
print(x.grad)   # ≈ 1.0
```

---

## Neural network API (`monogate.network`)

Requires `torch`.

### `EMLNetwork` — differentiable function approximation

```python
import torch
from monogate.network import EMLNetwork, fit

x = torch.linspace(0.1, 3.0, 60).unsqueeze(1)
y = x.squeeze() ** 2

model = EMLNetwork(in_features=1, depth=2)
losses = fit(model, x=x, y=y, steps=3000, lr=1e-2)

print(model.formula(["x"]))   # eml(eml((w·x+b), …), …)
```

### `EMLTree` — symbolic regression of constants

```python
import math, torch
from monogate.network import EMLTree, fit

model = EMLTree(depth=2)
losses = fit(model, target=torch.tensor(math.pi), steps=3000, lr=5e-3)

print(f"pi ~ {model().item():.6f}")
print(model.formula())
```

### `HybridNetwork` — EXL inner + EML outer

EXL sub-trees for inner nodes (stable at deep random init, cheap `pow`/`ln`), EML root for the additive step. Wins 5/7 targets on the operator zoo leaderboard.

```python
from monogate.network import HybridNetwork, fit
import torch

x = torch.linspace(-3.14, 3.14, 256).unsqueeze(1)
y = torch.sin(x.squeeze())

model = HybridNetwork(in_features=1, depth=3)
losses = fit(model, x=x, y=y, steps=2000, lr=3e-3)
```

### `fit()` signature

```python
fit(
    model,
    *,
    target=None,          # scalar Tensor or float   (EMLTree)
    x=None,               # (batch, in_features)     (EMLNetwork)
    y=None,               # (batch,)                 (EMLNetwork)
    steps=2000,
    lr=1e-2,
    log_every=200,        # 0 = silent
    loss_threshold=1e-8,  # early stop
    lam=0.0,              # complexity penalty (L1 on leaves / weights)
) -> list[float]          # raw loss values
```

---

## sin(x) via Taylor series

BEST routing holds a constant 74% node reduction at every precision level:

| Terms | Nodes (BEST) | Nodes (EML) | Max error |
|-------|-------------|-------------|-----------|
| 4     | 27          | 105         | 7.5e-02   |
| 6     | 45          | 175         | 4.5e-04   |
| 8     | 63          | 245         | 7.7e-07   |
| 10    | 81          | 315         | 5.3e-10   |
| 12    | 99          | 385         | 1.8e-13   |

Machine precision (~6.5×10⁻¹⁵) at 13 terms: 108 nodes (BEST) vs 420 nodes (EML-only).

---

## SIREN / NeRF optimizer

```python
from monogate import optimize_siren

# Analyze any sin-heavy nn.Module
report = optimize_siren(my_siren_model, omega=30.0)
print(report)                   # 73% savings, speedup expected
print(report.get_rewritten())   # BEST.sin(BEST.mul(30, self.linear(x)))
```

`optimize_siren` is a thin wrapper around `best_optimize_model` with a SIREN-aware docstring.
`optimize_nerf` is an alias. Both return `ModelOptimizeReport` — same interface as `best_optimize_model`.

---

## Code optimizer (`monogate.optimize`)

`best_optimize` rewrites Python expressions and functions to use BEST routing, reporting per-operation savings and generating rewritten source.

```python
from monogate import best_optimize

r = best_optimize("sin(x)**2 + ln(x+1)")
print(r.rewritten_code)   # "BEST.pow(BEST.sin(x), 2) + BEST.ln(x + 1)"
print(r.savings_pct)      # 72
print(r)                  # full table + speedup indicator
```

Decorator form:

```python
@best_optimize
def my_func(x):
    return math.sin(x) ** 2 + math.log(x + 1)

my_func.best_info.savings_pct   # 72
```

Model analysis:

```python
from monogate import best_optimize_model

# Analyze all forward() methods — reports per-layer savings + speedup indicator
report = best_optimize_model(my_model, verbose=True)
print(report)

# Get AST-rewritten source for any forward method
print(report.get_rewritten())            # root module
print(report.get_rewritten("encoder"))  # sub-module path
report.print_rewritten()                 # prints to stdout

# Patch EML-arithmetic methods in-place (for EMLNetwork / EMLTree models)
report = best_optimize_model(my_model, inplace=True)
```

Output format:

```
ModelOptimizeReport: 74% node savings  (63n BEST vs 245n EML)
  Layers analyzed: 3  |  Methods patched: 0
  Speedup expected: YES  (74% > 20% crossover threshold)
  Device: cpu — note: native torch.sin is ~9,000x faster than EML substrate.
  ------------------------------------------------
  root.forward: 74% savings  (63n BEST vs 245n EML)
  Use report.print_rewritten() to view the rewritten forward source.
```

---

## Explorer (monogate.dev)

| Tab | What it shows |
|-----|---------------|
| **✦ viz** | Expression tree for any math input — nodes colored by EML / EDL / EXL routing. Click subtrees to highlight. |
| **sin↗** | sin(x) Taylor accuracy chart, 2–20 terms. BEST vs EML node count at each precision level. |
| **⚡ demo** | Live JS GELU FFN timing (EML vs BEST) + Python experiment_10 numbers side by side. |
| **✦ calc** | Evaluate any expression in BEST / EML / EXL / EDL mode with per-operation node breakdown. |
| **⚙ opt** | Paste Python/NumPy/PyTorch code — get a BEST-rewritten version with node savings estimate. Calls real `best_optimize()` via local API when available. |
| **⬡ nerf** | SIREN / NeRF optimizer — pre-loaded SIREN presets, before/after diff, Download optimized .py. |
| **⊞ board** | Challenge leaderboard — open problems in EML construction (sin, cos, π). Submit and get credited. |

---

## Run tests

```bash
cd python/

# Core only (no torch required)
pytest tests/test_core.py -v

# All tests (torch required)
pytest tests/ -v
```

593 passing, 8 skipped (ONNX + torch.compile tests skip when deps absent).

---

## Package structure

```
python/
├── pyproject.toml
├── README.md
├── mkdocs.yml           # documentation site config
├── CHANGELOG.md
└── monogate/
    ├── __init__.py      # public API, lazy torch import
    ├── core.py          # op, EML/EDL/EXL/EAL/EMN, HybridOperator, BEST
    ├── operators.py     # registry: ALL_OPERATORS, compare_all, markdown_table
    ├── optimize.py      # best_optimize(), OptimizeResult, BestRewriter
    ├── torch_ops.py     # differentiable tensor ops (requires torch)
    ├── network.py       # EMLTree, EMLNetwork, HybridNetwork, fit
    ├── complex_eval.py  # complex EML, Euler path, sin/cos_via_euler
    ├── torch/
    │   ├── __init__.py
    │   └── eml_layer.py  # EMLActivation, EMLLayer (nn.Module, ONNX-ready)
    ├── fused_rust.py    # Rust backend wrapper, get_best_activation, rust_info
    └── search/
        ├── __init__.py
        ├── mcts.py          # mcts_search, beam_search, MCTSResult, BeamResult
        ├── sin_search_05.py # N=11 vectorised exhaustive search
        └── analyze_n11.py   # post-search analysis, near-miss gallery
monogate-core/               # Optional Rust extension (maturin / PyO3)
assets/
└── n11_share_card.md        # shareable N=11 result summary
paper/
├── preprint.tex             # arXiv-ready LaTeX
└── README.md                # build instructions + submission checklist
results/
└── sin_n11.json             # N=11 exhaustive search results
docs/                        # MkDocs source (mkdocs serve to browse)
notebooks/
├── siren_with_monogate.py   # EML-SIREN vs sin-SIREN speed + quality comparison
├── eml_layer_siren_example.py
├── mcts_sin_approximation.py
└── performance_kernels.py
tests/
├── test_core.py
├── test_torch.py
├── test_eml_layer.py    # 68 tests
├── test_complex.py      # 36 tests
├── test_compile.py      # 41 tests
└── test_llm.py          # 40 tests
```
