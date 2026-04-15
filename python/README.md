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
pip install monogate

# With PyTorch support
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

## Package structure

```
python/
├── pyproject.toml
├── README.md
└── monogate/
    ├── __init__.py      # public API, lazy torch import
    ├── core.py          # pure Python, no dependencies
    ├── torch_ops.py     # differentiable tensor ops (requires torch)
    └── network.py       # EMLTree, EMLNetwork, fit (requires torch)
tests/
├── test_core.py
└── test_torch.py
```
