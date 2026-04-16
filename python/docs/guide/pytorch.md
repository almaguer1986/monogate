# PyTorch Integration

monogate provides differentiable EML layers that integrate with PyTorch as drop-in replacements for standard activations or fully learnable expression layers.

## Installation

```bash
pip install "monogate[torch]"
```

Requires `torch >= 2.0`.

---

## EMLActivation

A scalar activation function (element-wise, fully vectorized).

Drop-in replacement for `torch.sin`, `F.gelu`, `F.relu`, etc.

```python
from monogate.torch import EMLActivation
import torch

act = EMLActivation(depth=2, operator="EML")
x   = torch.randn(32, 64)
y   = act(x)               # same shape (32, 64)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `depth` | int | 2 | Tree depth. `depth=d` → 2^d leaves, 2^d−1 internal nodes. |
| `operator` | str | `"EML"` | Operator family: `EML`, `EDL`, `EXL`, or `BEST`. |

### Node count

```python
act = EMLActivation(depth=2)
# nodes = 2^2 - 1 = 3
# leaves = 2^2 = 4
```

---

## EMLLayer

A complete layer combining a linear transform with an EML activation. Two modes:

### mode='activation' (default)

`nn.Linear(in, out)` followed by a shared `EMLActivation`. Recommended for SIREN / NeRF / PINN activation replacement.

```python
from monogate.torch import EMLLayer
import torch

# Replace sin activation in SIREN
layer = EMLLayer(256, 256, depth=2, operator="EML")
x     = torch.randn(8, 256)
y     = layer(x)   # (8, 256)
```

Parameter count:
```
in_features * out_features + out_features  (linear)
+ 2 * 2^depth                              (activation: weight+bias per leaf)
```

### mode='tree'

`out_features` independent EML expression trees, each with `in_features`-dimensional linear leaves. Fully interpretable — call `.formula()` to inspect learned expressions.

```python
layer = EMLLayer(4, 8, depth=2, mode="tree")
out   = layer(x)                                   # (batch, 8)
print(layer.formula(["x", "y", "z", "w"]))         # list of 8 formula strings
```

### Constructor arguments

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `in_features` | int | — | Input dimension |
| `out_features` | int | — | Output dimension |
| `depth` | int | 2 | Tree depth |
| `operator` | str | `"EML"` | `EML` \| `EDL` \| `EXL` \| `BEST` |
| `mode` | str | `"activation"` | `activation` \| `tree` |

---

## SIREN example

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from monogate.torch import EMLLayer

class EMLSIREN(nn.Module):
    def __init__(self, width=32, depth=2):
        super().__init__()
        self.layers = nn.ModuleList([
            EMLLayer(1, width, depth=depth),
            EMLLayer(width, width, depth=depth),
        ])
        self.output = nn.Linear(width, 1)

    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return self.output(x)

# Train on f(x) = sin(3x)*cos(x)
model = EMLSIREN(width=32, depth=2)
opt   = torch.optim.Adam(model.parameters(), lr=1e-3)

x = torch.linspace(-3.14, 3.14, 200).unsqueeze(1)
y = torch.sin(3 * x) * torch.cos(x)

for _ in range(2000):
    opt.zero_grad()
    loss = F.mse_loss(model(x).squeeze(), y.squeeze())
    loss.backward()
    opt.step()
```

---

## Node count comparison

```python
from monogate.torch import EMLLayer, compare_to_native

layer = EMLLayer(32, 32, depth=2)
compare_to_native(layer, native_name="sin")
# EMLLayer nodes : 3
# sin nodes      : 245
# Difference     : 98.8% saved
```

---

## ONNX export

```python
layer = EMLLayer(8, 16, depth=2, mode="activation")
dummy = torch.randn(1, 8)
torch.onnx.export(
    layer, dummy, "eml_layer.onnx",
    input_names=["x"], output_names=["y"],
    opset_version=14,
)
# All ops: exp, log, mul, sigmoid, softplus — all ONNX-native at opset 14.
```

---

## Serialization

```python
# Save
torch.save({
    "kwargs": {"in_features": 256, "out_features": 256, "depth": 2},
    "state":  layer.state_dict(),
}, "eml_layer.pt")

# Reload
ckpt  = torch.load("eml_layer.pt")
layer = EMLLayer(**ckpt["kwargs"])
layer.load_state_dict(ckpt["state"])
```
