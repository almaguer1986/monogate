# Physics-Informed EML Networks (PINN)

`EMLPINN` combines a differentiable EML expression tree with a physics residual
loss, so the learned model simultaneously fits observed data **and** satisfies
a differential equation.  Because the backbone is an EML tree, the learned
solution is an interpretable symbolic expression — not a black-box network.

---

## Quick start

```python
import math
import torch
from monogate import EMLPINN, fit_pinn

# Harmonic oscillator:  u'' + ω²·u = 0  (exact solution: sin(ωx))
omega = 2.0
model = EMLPINN(equation="harmonic", omega=omega, backbone_depth=3)

x_data = torch.linspace(0, math.pi, 50).unsqueeze(1)
y_data = torch.sin(omega * x_data.squeeze(1))
x_phys = torch.linspace(0, math.pi, 100).unsqueeze(1)

result = fit_pinn(model, x_data, y_data, x_phys, steps=2000, log_every=400)

print(result.formula)         # symbolic EML expression for the solution
print(f"data  loss = {result.data_loss:.4e}")
print(f"phys  loss = {result.physics_loss:.4e}")
print(f"elapsed    = {result.elapsed_s:.2f}s")
```

---

## Supported equations

| `equation` | PDE/ODE | Parameters |
|------------|---------|------------|
| `'harmonic'` | u''(x) + ω²·u(x) = 0 | `omega: float` (default 1.0) |
| `'burgers'`  | u(x)·u'(x) − ν·u''(x) = 0 | `nu: float` (default 0.01) |
| `'heat'`     | u''(x) = 0 (steady 1D Laplace) | — |

All equations are formulated for **1-D input** `x` with tensor shape `(batch, 1)`.

---

## EMLPINN constructor

```python
EMLPINN(
    equation="harmonic",     # see table above
    backbone_depth=3,        # EMLNetwork depth (depth=d → 2^d-1 internal nodes)
    omega=1.0,               # harmonic oscillator frequency
    nu=0.01,                 # Burgers viscosity coefficient
    lam_physics=1.0,         # physics loss weight (can be overridden in fit_pinn)
    in_features=1,           # input dimension (default 1 for 1-D problems)
)
```

The backbone is an `EMLNetwork(in_features, depth)` — the same architecture
used for general EML function approximation in `monogate.network`.

---

## fit_pinn()

```python
result = fit_pinn(
    model,          # EMLPINN instance
    x_data,         # (N, 1) observed input tensor
    y_data,         # (N,)   observed target tensor
    x_phys,         # (M, 1) collocation points for physics residual
    steps=2000,
    lr=1e-2,
    log_every=200,
    loss_threshold=1e-6,
    max_grad_norm=1.0,
    lam=0.0,        # optional L1 weight regularisation on backbone
    lam_physics=None,   # overrides model.lam_physics if set
)
```

**Returns** `PINNResult`:

| Field | Type | Description |
|-------|------|-------------|
| `data_loss` | `float` | Final data MSE |
| `physics_loss` | `float` | Final physics residual MSE |
| `formula` | `str` | Human-readable EML formula |
| `elapsed_s` | `float` | Training time in seconds |
| `history` | `list[tuple[int,float,float]]` | `(step, data_loss, phys_loss)` checkpoints |

---

## Accessing the symbolic formula

At any point during or after training:

```python
print(model.formula(["x"]))
# eml(eml((0.8231·x+0.1044), (−0.2189·x+1.7821)),
#      eml((0.1093·x+1.2344), (−0.9871·x+0.0227)))
```

The formula uses the linear weights learned by each leaf's `nn.Linear(1, 1)`.
As training progresses and weights sharpen, the formula becomes more
interpretable.

---

## Example: Steady Burgers equation

The steady 1-D Burgers equation `u·u' = ν·u''` has the exact travelling-wave
solution `u(x) = −ν·tanh(x / 2ν)`:

```python
import numpy as np
import torch
from monogate import EMLPINN, fit_pinn

nu = 0.05

def exact(x_np):
    return -nu * np.tanh(x_np / (2 * nu))

x_np = np.linspace(-2, 2, 60)
x_data = torch.tensor(x_np, dtype=torch.float32).unsqueeze(1)
y_data = torch.tensor(exact(x_np), dtype=torch.float32)
x_phys = torch.linspace(-2, 2, 120).unsqueeze(1)

model = EMLPINN(equation="burgers", nu=nu, backbone_depth=3, lam_physics=2.0)
result = fit_pinn(model, x_data, y_data, x_phys, steps=2000, lr=5e-3)

print(f"data_loss  = {result.data_loss:.4e}")
print(f"phys_loss  = {result.physics_loss:.4e}")
print(result.formula)
```

---

## Training tips

**`backbone_depth`**: Controls the expressiveness of the EML solution
approximator. `depth=2` (3 nodes) is fast to train; `depth=3` (7 nodes) gives
a richer symbolic expression.  `depth=4` is rarely needed for 1-D problems.

**`lam_physics`**: Higher values enforce the equation more strictly but may
hurt data fit when data is noisy.  Start with `lam_physics=1.0` and increase
if the physics loss stays high after convergence.

**`x_phys`**: Use more collocation points than data points (typically 2–3×).
Spread them uniformly across the domain of interest.  The physics loss is
computed at these points without requiring labels.

**`lr`**: The EML backbone can be sensitive to large learning rates in early
training (softplus instabilities).  `lr=5e-3` is a good starting point.

---

## Residual inspection

You can inspect the raw residual tensor at any collocation set:

```python
x_test = torch.linspace(0, math.pi, 200).unsqueeze(1)
with torch.no_grad():
    # Approximate: disable autograd for inspection (no create_graph needed)
    model.backbone.eval()
    r = model.residual(x_test)
    print(f"max residual: {r.abs().max().item():.4e}")
    print(f"mean residual: {r.abs().mean().item():.4e}")
```

---

## See also

- `notebooks/pinn_eml_demo.py` — full runnable experiments (harmonic + Burgers)
- `monogate.network` — `EMLNetwork` backbone documentation
- `docs/guide/complex.md` — complex BEST routing for special functions
- `tests/test_pinn.py` — 27 tests covering all equations and edge cases
