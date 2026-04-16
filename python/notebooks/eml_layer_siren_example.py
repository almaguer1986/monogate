"""
eml_layer_siren_example.py — EMLLayer as sin activation replacement in SIREN
=============================================================================

Demonstrates:
  1. A minimal SIREN-style network for 1D function approximation
  2. Replacing the sin activation with EMLLayer (mode='activation')
  3. Node count comparison: sin (245 EML nodes) vs EMLLayer (3 nodes at depth=2)
  4. Training comparison: standard sin-SIREN vs EML-SIREN on f(x) = sin(3x)cos(x)
  5. ONNX export validation

Run:
    cd python/
    python notebooks/eml_layer_siren_example.py

Requires: torch >= 2.0
Optional: onnx (for export check)
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from monogate.torch import EMLLayer, EMLActivation, compare_to_native

# ── Target function ───────────────────────────────────────────────────────────
# A mildly complex function that sin-SIREN should handle well

def target_fn(x: Tensor) -> Tensor:
    return torch.sin(3.0 * x) * torch.cos(x)


# ── Model definitions ─────────────────────────────────────────────────────────

class SinSIREN(nn.Module):
    """Standard 3-layer SIREN with sin activation."""
    def __init__(self, width: int = 32) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(1, width),
            nn.Linear(width, width),
            nn.Linear(width, 1),
        )
        self.width = width

    def forward(self, x: Tensor) -> Tensor:
        h = x
        for i, layer in enumerate(self.layers[:-1]):
            h = torch.sin(30.0 * layer(h) if i == 0 else layer(h))
        return self.layers[-1](h)


class EMLSIREN(nn.Module):
    """3-layer SIREN with EMLLayer activation instead of sin."""
    def __init__(self, width: int = 32, depth: int = 2, operator: str = "EML") -> None:
        super().__init__()
        self.eml_layers = nn.ModuleList([
            EMLLayer(1, width, depth=depth, operator=operator),
            EMLLayer(width, width, depth=depth, operator=operator),
        ])
        self.output = nn.Linear(width, 1)
        self.depth    = depth
        self.operator = operator

    def forward(self, x: Tensor) -> Tensor:
        h = x
        for layer in self.eml_layers:
            h = layer(h)
        return self.output(h)

    @property
    def eml_node_count(self) -> int:
        return sum(l.n_eml_nodes for l in self.eml_layers)


# ── Training helper ───────────────────────────────────────────────────────────

def train(
    model: nn.Module,
    x_train: Tensor,
    y_train: Tensor,
    steps: int = 2000,
    lr: float = 1e-3,
) -> list[float]:
    opt    = torch.optim.Adam(model.parameters(), lr=lr)
    losses = []
    for _ in range(steps):
        opt.zero_grad()
        pred = model(x_train)
        loss = F.mse_loss(pred.squeeze(), y_train)
        if not torch.isfinite(loss):
            break
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        losses.append(loss.item())
    return losses


# ── Data ──────────────────────────────────────────────────────────────────────

torch.manual_seed(42)
N_TRAIN = 200
x_train = torch.linspace(-math.pi, math.pi, N_TRAIN).unsqueeze(1)
y_train = target_fn(x_train).squeeze()
x_test  = torch.linspace(-math.pi, math.pi, 500).unsqueeze(1)
y_test  = target_fn(x_test).squeeze()


# ── Section 1: Node count comparison ─────────────────────────────────────────

print("=" * 64)
print("  1. Node count: EMLLayer vs sin activation")
print("=" * 64)
print()

for depth in [1, 2, 3]:
    layer = EMLLayer(32, 32, depth=depth, operator='EML')
    print(f"  EMLLayer depth={depth} : {layer.n_eml_nodes} EML nodes/layer")

print()
print("  Reference: sin(x) in pure EML  =  245 nodes (8-term Taylor)")
print("  Reference: sin(x) BEST-routed  =   63 nodes (8-term Taylor)")
print()

eml_layer = EMLLayer(32, 32, depth=2, operator='EML')
compare_to_native(eml_layer, native_name="sin")

# ── Section 2: Training comparison ───────────────────────────────────────────

print()
print("=" * 64)
print("  2. Training: sin-SIREN vs EML-SIREN")
print(f"     target: f(x) = sin(3x)*cos(x) on [-pi, pi]")
print("=" * 64)
print()

configs = [
    ("sin-SIREN",          lambda: SinSIREN(width=32)),
    ("EML-SIREN (d=2)",    lambda: EMLSIREN(width=32, depth=2, operator="EML")),
    ("EML-SIREN (d=2,BEST)", lambda: EMLSIREN(width=32, depth=2, operator="BEST")),
    ("EML-SIREN (d=3)",    lambda: EMLSIREN(width=32, depth=3, operator="EML")),
]

results = []
for name, factory in configs:
    torch.manual_seed(0)
    model = factory()
    n_params = sum(p.numel() for p in model.parameters())
    n_eml = getattr(model, 'eml_node_count', None)

    t0     = time.perf_counter()
    losses = train(model, x_train, y_train, steps=2000, lr=1e-3)
    elapsed = time.perf_counter() - t0

    with torch.no_grad():
        final_mse = F.mse_loss(model(x_test).squeeze(), y_test).item()

    print(f"  {name:<28}: final_mse={final_mse:.4e}  "
          f"params={n_params:5d}  " +
          (f"eml_nodes={n_eml:3d}  " if n_eml is not None else "             ") +
          f"t={elapsed:.1f}s")
    results.append((name, final_mse, losses))

# ── Section 3: Formula inspection ────────────────────────────────────────────

print()
print("=" * 64)
print("  3. Learned formula (EML-SIREN d=2, first layer, first output)")
print("=" * 64)
print()

torch.manual_seed(0)
eml_model = EMLSIREN(width=4, depth=2)
train(eml_model, x_train, y_train, steps=500)
formula = eml_model.eml_layers[0].formula("x")
print(f"  Activation formula: {formula}")
print()

# ── Section 4: ONNX export ────────────────────────────────────────────────────

print("=" * 64)
print("  4. ONNX export validation")
print("=" * 64)
print()

torch.manual_seed(0)
small_model = EMLSIREN(width=8, depth=2)
dummy_input = torch.randn(1, 1)
onnx_path   = Path(__file__).parent / "eml_siren.onnx"

try:
    torch.onnx.export(
        small_model,
        dummy_input,
        str(onnx_path),
        input_names=["x"],
        output_names=["y"],
        opset_version=14,   # 14 is broadly supported; all ops (exp,log,softplus) are native
        verbose=False,
    )
    size_kb = onnx_path.stat().st_size / 1024
    print(f"  ONNX export: OK  ({size_kb:.1f} KB) -> {onnx_path}")

    try:
        import onnx  # type: ignore
        model_proto = onnx.load(str(onnx_path))
        onnx.checker.check_model(model_proto)
        print("  ONNX checker: PASSED")
    except ImportError:
        print("  (onnx not installed -- skipped checker)")

except Exception as e:
    print(f"  ONNX export failed: {e}")

# ── Section 5: Summary plot ───────────────────────────────────────────────────

try:
    import matplotlib.pyplot as plt  # type: ignore

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle("EMLLayer vs sin activation -- monogate.torch", fontsize=12)

    # Left: convergence curves
    ax = axes[0]
    for name, _, losses in results:
        ax.semilogy(losses, label=name, linewidth=1)
    ax.set_xlabel("Step")
    ax.set_ylabel("MSE (log scale)")
    ax.set_title("Training convergence")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Right: final predictions of best EML model
    ax2 = axes[1]
    torch.manual_seed(0)
    best_model = EMLSIREN(width=32, depth=2, operator="EML")
    train(best_model, x_train, y_train, steps=2000, lr=1e-3)
    with torch.no_grad():
        preds = best_model(x_test).squeeze()

    ax2.plot(x_test.squeeze().numpy(), y_test.numpy(),
             label="target", color="#1e293b", linewidth=2)
    ax2.plot(x_test.squeeze().numpy(), preds.numpy(),
             label="EML-SIREN", color="#10b981", linestyle="--", linewidth=1.5)
    ax2.set_xlabel("x")
    ax2.set_ylabel("f(x)")
    ax2.set_title("sin(3x)cos(x) fit on [-pi, pi]")
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    out_path = Path(__file__).parent / "eml_siren_results.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    print(f"\n  Plot saved -> {out_path}")

except ImportError:
    print("\n  (matplotlib not installed -- skipping plot)")

print()
print("=" * 64)
print("  DONE")
print("=" * 64)
