# monogate · Python

[![PyPI](https://img.shields.io/pypi/v/monogate)](https://pypi.org/project/monogate/)

Pure-Python and PyTorch implementations of **EML arithmetic** — all elementary
functions constructed from a single binary operator:

```
eml(x, y) = exp(x) − ln(y)
```

Based on [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) (Odrzywołek, 2026).

---

## Install

```bash
# Core only (no dependencies)
pip install monogate            # v0.3.0

# With PyTorch support (EMLNetwork, HybridNetwork, fit)
pip install "monogate[torch]"

# Development (pytest + torch)
pip install "monogate[dev]"
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

## Operator family (`monogate.core`)

Beyond EML, the package ships four cousin operators and a hybrid routing system.

### Named operators

```python
from monogate import EML, EDL, EXL, EAL, EMN

# Each Operator wraps its gate function and natural constant
EML.name        # "EML"
EML.constant    # 1.0+0j  (ln(1) = 0 → eml(x,1) = exp(x))
EDL.constant    # e       (ln(e) = 1 → edl(x,e) = exp(x))

# Derived operations via __getattr__ dispatch
EML.pow(2.0, 10.0)   # 1024.0  (15-node formula)
EDL.div(10.0, 2.0)   # 5.0     (1-node formula)
EXL.ln(math.e)       # 1.0     (1-node formula — no dead zone)
EXL.pow(2.0, 8.0)    # 256.0   (3-node formula)

# Summary table
EML.info()   # prints gate, constant, all derived-function node counts
```

| Operator | Gate | Complete? | Cheapest operation |
|----------|------|-----------|-------------------|
| **EML** | `exp(x) − ln(y)` | Yes | sub (5n), add (11n) |
| **EDL** | `exp(x) / ln(y)` | Yes | div (1n), mul (7n) |
| **EXL** | `exp(x) × ln(y)` | No  | ln (1n), pow (3n)  |
| EAL     | `exp(x) + ln(y)` | No  | — |
| EMN     | `ln(y) − exp(x)` | No  | — |

### Operator registry

```python
from monogate import ALL_OPERATORS, COMPLETE_OPERATORS, get_operator, compare_all, markdown_table

ALL_OPERATORS       # [EML, EDL, EXL, EAL, EMN]
COMPLETE_OPERATORS  # [EML, EDL]  — can build all elementary arithmetic

op = get_operator("EXL")      # look up by name
compare_all()                  # print side-by-side comparison table
print(markdown_table())        # GFM table string for docs/wikis
```

### BEST: optimal per-operation routing

`BEST` is a pre-built `HybridOperator` that routes each operation to whichever
base operator costs fewest nodes:

```python
from monogate import BEST, HybridOperator

BEST.pow(2.0, 10.0)   # 1024.0  (EXL, 3 nodes vs EML's 15)
BEST.div(6.0, 2.0)    # 3.0     (EDL, 1 node  vs EML's 15)
BEST.ln(math.e)       # 1.0     (EXL, 1 node  vs EML's 3)
BEST.add(3.0, 4.0)    # 7.0     (EML, 11 nodes — EML only)

# Routing summary + accuracy spot-checks
BEST.info()

# Full benchmark: node counts + accuracy + optional neural regression
BEST.benchmark()
BEST.benchmark(targets=["sin", "cos", "x**3", "poly4"], restarts=3, steps=800)
```

`BEST.benchmark()` prints three tables:

1. **Node counts** — each routed operation vs EML-only baseline with savings
2. **Numerical accuracy** — spot-checks for exp, ln, pow, mul, div, add, sub
3. **Neural regression** — optional; median/min MSE + convergence rate per target

Build a custom routing:

```python
from monogate import HybridOperator, EXL, EDL, EML

fast_pow = HybridOperator({'pow': EXL, 'div': EDL, 'add': EML}, name="FastPow")
fast_pow.pow(3.0, 4.0)   # 81.0  (3 nodes)
fast_pow.info()
```

---

## PyTorch API (`monogate.torch_ops`)

Requires `torch`. All functions accept and return `Tensor` objects and are
fully differentiable through `autograd`.

```python
import torch
from monogate.torch_ops import op, exp_eml, ln_eml, neg_eml, add_eml, mul_eml

x = torch.tensor(2.0, requires_grad=True)
y = torch.tensor(3.0, requires_grad=True)

result = add_eml(x, y)
result.backward()
print(x.grad)   # ≈ 1.0  (d/dx(x+y) = 1)
```

### `neg_eml` — two-regime via `torch.where`

The two-regime negation (tower formula for y ≤ 0, shift formula for y > 0) is
implemented with `torch.where` so that both branches are traced and gradients
flow correctly through the active regime:

```python
# Batch with mixed signs — gradients flow through the correct regime per element
y = torch.tensor([-3., -1., 0., 1., 3.], requires_grad=True)
neg_eml(y).sum().backward()
print(y.grad)   # ≈ [−1, −1, −1, −1, −1]
```

---

## Neural network API (`monogate.network`)

Requires `torch`.

### `EMLTree` — symbolic regression of constants

Learnable EML expression tree with scalar leaf parameters.  Use to discover
EML constructions for mathematical constants.

```python
import math, torch
from monogate.network import EMLTree, fit

model = EMLTree(depth=2)
losses = fit(model, target=torch.tensor(math.pi), steps=3000, lr=5e-3)

print(f"π ≈ {model().item():.6f}")
print(model.formula())   # eml(eml(1.2345, 0.9876), eml(…, …))
```

### `EMLNetwork` — differentiable function approximation

Learnable EML expression tree where every leaf is a `nn.Linear` module.
Approximates arbitrary functions from input features.  When training
converges, `formula()` prints an interpretable expression.

```python
import torch
from monogate.network import EMLNetwork, fit

# Learn y = x² on x ∈ [0.1, 3.0]
x = torch.linspace(0.1, 3.0, 60).unsqueeze(1)
y = x.squeeze() ** 2

model = EMLNetwork(in_features=1, depth=2)
losses = fit(model, x=x, y=y, steps=3000, lr=1e-2)

print(model.formula())   # eml(eml((w·x0+b), …), …)
```

### `HybridNetwork` — EXL inner + EML outer

Composes two different operators in one network: EXL sub-trees for the inner
nodes (3-node pow, 1-node ln, numerically stable at deep random init) and an
EML root node for the final additive step.  Wins 5/7 targets on the operator
zoo leaderboard.

```python
from monogate.network import HybridNetwork, fit
import torch

x = torch.linspace(-3.14, 3.14, 256).unsqueeze(1)
y = torch.sin(x.squeeze())

model = HybridNetwork(in_features=1, depth=3)
losses = fit(model, x=x, y=y, steps=2000, lr=3e-3)
```

Custom inner/outer operators:

```python
from monogate.torch_ops import eal_op
from monogate.network import HybridNetwork, EMLNetwork

# EAL inner nodes + default EML root
model = HybridNetwork(in_features=1, depth=3, inner_op=eal_op)
```

### `fit()` signature

```python
fit(
    model,            # EMLTree or EMLNetwork
    *,
    target=None,      # scalar Tensor or float   (EMLTree only)
    x=None,           # (batch, in_features)     (EMLNetwork only)
    y=None,           # (batch,)                 (EMLNetwork only)
    steps=2000,       # optimisation steps
    lr=1e-2,          # Adam learning rate
    log_every=200,    # print interval (0 = silent)
    loss_threshold=1e-8,  # early-stop threshold
    lam=0.0,          # complexity penalty weight
                      #   EMLTree:    λ · Σ|leaf − 1|
                      #   EMLNetwork: λ · Σ|weight|  (L1 on linear weights)
) -> list[float]      # raw loss values (without penalty)
```

---

## Run tests

```bash
cd python/

# Core tests (no torch required)
pytest tests/test_core.py -v

# All tests (torch required)
pytest tests/ -v
```

---

## PyTorch operator functions

```python
from monogate.torch_ops import (
    op,            # EML gate: exp(x) − ln(y)
    edl_op,        # EDL gate: exp(x) / ln(y)   (raw — avoid y near 1)
    edl_op_safe,   # EDL gate with y+1 shift     (safe for training)
    exl_op,        # EXL gate: exp(x) * ln(y)
    eal_op,        # EAL gate: exp(x) + ln(y)
    EDL_SAFE_CONSTANT,  # e−1 ≈ 1.718   (natural constant for edl_op_safe)
)
```

Pass any of these as `op_func` to `EMLNetwork`:

```python
from monogate.network import EMLNetwork
from monogate.torch_ops import exl_op

model = EMLNetwork(in_features=1, depth=3, op_func=exl_op)
```

## sin(x) via Taylor series

Using BEST routing, sin(x) can be constructed symbolically with dramatically
fewer nodes than all-EML:

| Terms | Nodes (BEST) | Nodes (EML-only) | Saving | max error |
|-------|-------------|-----------------|--------|-----------|
| 4     | 27          | 105             | 74%    | 7.5e-02   |
| 6     | 45          | 175             | 74%    | 4.5e-04   |
| 8     | 63          | 245             | 74%    | 7.7e-07   |
| 10    | 81          | 315             | 74%    | 5.3e-10   |
| 12    | 99          | 385             | 74%    | 1.8e-13   |

Key: `pow_exl` (3 nodes) replaces `pow_eml` (15 nodes); `div_edl` (1 node)
replaces `div_eml` (15 nodes).  The additive steps `sub_eml`/`add_eml` (5/11n)
are irreducible — no cousin operator supports arbitrary a ± b.

See `python/notebooks/sin_best.py` for the full analysis.

---

## Code optimizer (`monogate.optimize`)

`best_optimize` rewrites Python expressions and functions to use BEST-mode
routing, reports per-operation node savings, and annotates decorated functions
with their rewritten source.

### Expression strings

```python
from monogate import best_optimize

r = best_optimize("sin(x)**2 + ln(x+1)")
print(r)
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
r["message"]       # dict-style access also supported
```

### Decorator

```python
from monogate import best_optimize
import math

@best_optimize
def my_func(x):
    return math.sin(x) ** 2 + math.log(x + 1)

my_func.best_info.savings_pct          # e.g. 72
my_func._best_rewritten_source         # "BEST.pow(BEST.sin(x), 2) + ..."
my_func._is_best_optimized             # True
```

`@best_optimize()` (with parentheses) also works.

### `OptimizeResult` fields

| Field | Type | Description |
|-------|------|-------------|
| `ops` | `tuple[OpMatch, …]` | per-operation breakdown |
| `total_best_nodes` | `int` | total nodes under BEST routing |
| `total_eml_nodes` | `int` | total nodes under pure EML |
| `savings_pct` | `int` | integer % reduction |
| `rewritten_code` | `str` | AST-rewritten source using `BEST.*` |
| `python_snippet` | `str` | runnable snippet with imports |
| `message` | `str` | one-line summary |

---

## Package structure

```
python/
├── pyproject.toml
├── README.md
└── monogate/
    ├── __init__.py      # public API, lazy torch import
    ├── core.py          # pure Python: op, EML/EDL/EXL/EAL/EMN, HybridOperator, BEST
    ├── operators.py     # registry: ALL_OPERATORS, compare_all, markdown_table
    ├── optimize.py      # best_optimize(), OptimizeResult, OpMatch, BestRewriter
    ├── torch_ops.py     # differentiable tensor ops (requires torch)
    └── network.py       # EMLTree, EMLNetwork, HybridNetwork, fit (requires torch)
tests/
├── test_core.py
├── test_torch.py
├── test_edl.py          # 154 tests for operator family + HybridOperator + BEST
└── test_optimize.py     # 80 tests for best_optimize, OptimizeResult, BestRewriter
notebooks/
├── operators_study_v2.py   # algebraic derivations for all 5 operators
├── operator_zoo.py         # 5-operator × 7-target leaderboard
├── sin_construction.py     # Taylor sin(x) — 4 sections
├── sin_best.py             # Deeper sin(x) analysis — 20 terms, node Pareto
└── regression_comparison.py
```
