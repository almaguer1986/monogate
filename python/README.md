# monogate · Python

[![PyPI](https://img.shields.io/pypi/v/monogate)](https://pypi.org/project/monogate/)

**monogate** implements EML arithmetic — a formal system where every elementary function is a finite binary tree of identical gates — and routes each operation to the cheapest known operator family, cutting node counts by 20–74% and delivering measurable wall-clock speedup for pow/ln-heavy workloads.

```
eml(x, y) = exp(x) − ln(y)       ← the one gate
```

From this operator and the constant `1`, every elementary arithmetic function is constructible as an exact expression tree. No approximation. No Taylor series for the core identities.

Based on [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) (Odrzywołek, 2026).
Live explorer: **[monogate.dev](https://monogate.dev)**

---

## Install

```bash
# Core only (pure Python, no dependencies)
pip install monogate                # v0.3.0

# With PyTorch (EMLNetwork, HybridNetwork, fit, autograd)
pip install "monogate[torch]"

# Development (pytest + torch)
pip install "monogate[dev]"
```

JavaScript / Node:
```bash
npm install monogate
```

---

## Real Speedups

Node-count savings translate to wall-clock speedup only above a threshold. Three experiments measured this directly:

| Workload | Activation | Nodes (EML) | Nodes (BEST) | Savings | Speedup |
|----------|-----------|-------------|-------------|---------|---------|
| TinyMLP, sin (exp_09) | sin(x) 8-term Taylor | 245 | 63 | **74%** | **2.8–3.1×** |
| Batch poly eval (exp_11) | x⁴+x³+x² | 67 | 31 | **54%** | **2.1×** |
| Transformer FFN (exp_10) | tanh-GELU | 17 | 14 | 18% | 0.93× |

Linear model fit (R²=0.9992): `speedup ≈ 0.033 × savings_pct + 0.32`

**Crossover at ~20% node reduction.** Functions with ≥21% BEST savings yield wall-clock gains; below that, Python call overhead dominates.

```bash
# Reproduce
python notebooks/experiment_09_mlp_demo.py    # TinyMLP, sin
python notebooks/experiment_10_transformer_ffn.py  # FFN, GELU
python notebooks/experiment_11.py             # poly, crossover analysis
```

---

## Operator family

EML is not the only complete operator of this form. Five variants have been characterised:

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

Total: **37 nodes** vs 77 all-EML — 52% fewer. The add/sub steps stay EML because no other operator currently supports arbitrary a ± b.

```python
from monogate import BEST

BEST.pow(2.0, 10.0)   # 1024.0  (EXL, 3 nodes vs 15)
BEST.div(6.0, 2.0)    # 3.0     (EDL, 1 node  vs 15)
BEST.ln(math.e)       # 1.0     (EXL, 1 node  vs 3)
BEST.add(3.0, 4.0)    # 7.0     (EML, 11 nodes — irreducible)

BEST.info()           # routing table + accuracy spot-checks
BEST.benchmark()      # node counts + accuracy + optional neural regression
```

---

## When to use BEST

Use BEST routing when your workload:

- Contains activations with ≥21% node savings (sin, cos, polynomial expressions)
- Is dominated by `pow`, `ln`, `mul`, or `div` (all save ≥6 nodes each)
- Builds deep expression trees where overhead amortises across many nodes
- Is doing symbolic regression where formula interpretability matters
- Evaluates the same expression repeatedly (savings compound across calls)

Do not expect wall-clock gains from BEST when:
- Your primary operation is `add` or `sub` (no savings — EML-only)
- The total node reduction is under ~20% (GELU at 18% is a concrete example)
- You are already using native `torch` or `numpy` primitives (440× faster than any EML variant)

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
ln_eml(math.e)    # 1.0
neg_eml(5)        # −5.0
add_eml(2, 3)     # 5.0  (all sign combinations supported)
mul_eml(4, 3)     # 12.0
div_eml(10, 4)    # 2.5
pow_eml(2, 8)     # 256.0
recip_eml(4)      # 0.25
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
from monogate import EML, EDL, EXL, EAL, EMN

EML.pow(2.0, 10.0)   # 1024.0  (15-node formula)
EDL.div(10.0, 2.0)   # 5.0     (1-node formula)
EXL.ln(math.e)       # 1.0     (1-node formula — no dead zone)
EXL.pow(2.0, 8.0)    # 256.0   (3-node formula)

EML.info()   # gate, constant, all derived-function node counts
```

### Operator registry

```python
from monogate import ALL_OPERATORS, COMPLETE_OPERATORS, get_operator, compare_all, markdown_table

ALL_OPERATORS       # [EML, EDL, EXL, EAL, EMN]
COMPLETE_OPERATORS  # [EML, EDL]

op = get_operator("EXL")
compare_all()
print(markdown_table())
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

Requires `torch`. All functions accept and return `Tensor` objects, fully differentiable via `autograd`.

```python
import torch
from monogate.torch_ops import op, exp_eml, ln_eml, neg_eml, add_eml, mul_eml

x = torch.tensor(2.0, requires_grad=True)
y = torch.tensor(3.0, requires_grad=True)

result = add_eml(x, y)
result.backward()
print(x.grad)   # ≈ 1.0
```

Available gate functions:

```python
from monogate.torch_ops import (
    op,              # EML: exp(x) − ln(y)
    edl_op,          # EDL: exp(x) / ln(y)    (raw — avoid y near 1)
    edl_op_safe,     # EDL: exp(x) / ln(y+1)  (safe for training)
    exl_op,          # EXL: exp(x) * ln(y)
    eal_op,          # EAL: exp(x) + ln(y)
    EDL_SAFE_CONSTANT,  # e−1 ≈ 1.718
)
```

---

## Neural network API (`monogate.network`)

Requires `torch`.

### `EMLTree` — symbolic regression of constants

```python
import math, torch
from monogate.network import EMLTree, fit

model = EMLTree(depth=2)
losses = fit(model, target=torch.tensor(math.pi), steps=3000, lr=5e-3)

print(f"π ≈ {model().item():.6f}")
print(model.formula())
```

### `EMLNetwork` — differentiable function approximation

```python
import torch
from monogate.network import EMLNetwork, fit

x = torch.linspace(0.1, 3.0, 60).unsqueeze(1)
y = x.squeeze() ** 2

model = EMLNetwork(in_features=1, depth=2)
losses = fit(model, x=x, y=y, steps=3000, lr=1e-2)

print(model.formula())
```

### `HybridNetwork` — EXL inner + EML outer

EXL sub-trees for inner nodes (stable at deep random init, cheap `pow`/`ln`), EML root for the final additive step. Wins 5/7 targets on the operator zoo leaderboard.

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

## Code optimizer (`monogate.optimize`)

`best_optimize` rewrites Python expressions and functions to use BEST routing, reporting per-operation savings and generating rewritten source.

```python
from monogate import best_optimize

r = best_optimize("sin(x)**2 + ln(x+1)")
# ┌─────────────────────────────────────────────────────────────────┐
# │  sin(x)**2 + ln(x+1)  →  BEST-mode optimisation report         │
# ├──────────┬───────┬────────────┬──────────┬──────────────────────┤
# │  op      │ count │ BEST nodes │ EML nodes│ best_op              │
# ├──────────┼───────┼────────────┼──────────┼──────────────────────┤
# │  sin     │   1   │       63   │      245 │ BEST (EXL+EDL)       │
# │  pow     │   1   │        3   │       15 │ EXL                  │
# │  ln      │   1   │        1   │        3 │ EXL                  │
# │  add     │   1   │       11   │       11 │ EML                  │
# ├──────────┼───────┼────────────┼──────────┼──────────────────────┤
# │  TOTAL   │   4   │       78   │      274 │ −72%                 │
# └──────────┴───────┴────────────┴──────────┴──────────────────────┘

r.rewritten_code   # "BEST.pow(BEST.sin(x), 2) + BEST.ln(x + 1)"
r.savings_pct      # 72
```

Decorator form:

```python
@best_optimize
def my_func(x):
    return math.sin(x) ** 2 + math.log(x + 1)

my_func.best_info.savings_pct   # 72
my_func._best_rewritten_source  # "BEST.pow(BEST.sin(x), 2) + ..."
```

---

## Explorer (monogate.dev)

| Tab | Description |
|-----|-------------|
| **✦ viz** | Expression tree for any math input, nodes colored by EML / EDL / EXL routing. Click subtrees to highlight. |
| **sin↗** | sin(x) Taylor accuracy chart, 2–20 terms. BEST vs EML node count at each precision level. |
| **⚡ demo** | Live JS GELU FFN timing (EML vs BEST) + Python experiment_10 numbers side by side. |
| **Calc** | Evaluate any expression in BEST / EML / EXL / EDL mode with per-operation node breakdown. |
| **Opt** | Paste Python/NumPy/PyTorch code and get a BEST-rewritten version with node savings estimate. |
| **Board** | Challenge leaderboard — open problems in EML construction (sin, cos, π). Submit a construction, get credited. |

---

## Run tests

```bash
cd python/

# Core only (no torch required)
pytest tests/test_core.py -v

# All tests (torch required)
pytest tests/ -v
```

406 passing. 2 pre-existing failures in `test_torch.py` (EMLTree/EMLNetwork parameter assertions, unrelated to core or BEST).

---

## Package structure

```
python/
├── pyproject.toml
├── README.md
└── monogate/
    ├── __init__.py      # public API, lazy torch import
    ├── core.py          # op, EML/EDL/EXL/EAL/EMN, HybridOperator, BEST
    ├── operators.py     # registry: ALL_OPERATORS, compare_all, markdown_table
    ├── optimize.py      # best_optimize(), OptimizeResult, BestRewriter
    ├── torch_ops.py     # differentiable tensor ops (requires torch)
    └── network.py       # EMLTree, EMLNetwork, HybridNetwork, fit
tests/
├── test_core.py
├── test_torch.py
├── test_edl.py          # 154 tests — operator family, HybridOperator, BEST
└── test_optimize.py     # 80 tests — best_optimize, OptimizeResult, BestRewriter
notebooks/
├── experiment_09_mlp_demo.py     # TinyMLP + sin: 2.8× speedup
├── experiment_10_transformer_ffn.py  # FFN + GELU: below crossover
├── experiment_11.py              # poly benchmark, linear fit, crossover
├── sin_best.py                   # 20-term sin(x) analysis, node Pareto
├── operator_zoo.py               # 5-operator × 7-target leaderboard
└── operators_study_v2.py         # algebraic derivations for all 5 operators
```
