"""
performance_kernels.py — EML layer performance: before vs after.
=================================================================

Measures:
  1. EMLLayer vs FusedEMLLayer throughput at multiple batch sizes
  2. SIREN-style network training step benchmark
  3. Activation overhead breakdown (linear pass vs activation)
  4. Optional: torch.compile timing (when available)

Run:
    cd python/
    python notebooks/performance_kernels.py

Requires: torch >= 2.0
"""

from __future__ import annotations

import sys
import time
import math
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from monogate.compile import FusedEMLLayer, FusedEMLActivation, compile_eml_layer, benchmark_layer
from monogate.torch import EMLLayer, EMLActivation


# ── Helpers ───────────────────────────────────────────────────────────────────

def timed(fn, n_warmup=10, n_repeat=50):
    """Time fn() and return (mean_ms, std_ms)."""
    import statistics
    with torch.no_grad():
        for _ in range(n_warmup):
            fn()
    times = []
    with torch.no_grad():
        for _ in range(n_repeat):
            t0 = time.perf_counter()
            fn()
            times.append((time.perf_counter() - t0) * 1000)
    return statistics.mean(times), statistics.stdev(times)


def speedup_label(a_ms: float, b_ms: float) -> str:
    """'3.5x faster' style label: how much faster is b than a."""
    r = a_ms / b_ms
    if r >= 1.0:
        return f"{r:.1f}x faster"
    return f"{1/r:.1f}x slower"


def header(title: str) -> None:
    print()
    print("=" * 64)
    print(f"  {title}")
    print("=" * 64)


# ── Section 1: Activation throughput ─────────────────────────────────────────

header("1. Activation throughput: EMLActivation vs FusedEMLActivation")
print()

for depth in [1, 2, 3]:
    for n in [16, 256, 4096]:
        x    = torch.randn(n)
        std  = EMLActivation(depth=depth)
        fsd  = FusedEMLActivation(depth=depth)
        std_ms, _ = timed(lambda: std(x))
        fsd_ms, _ = timed(lambda: fsd(x))
        label = speedup_label(std_ms, fsd_ms)
        print(f"  depth={depth}  N={n:>5}  EML:{std_ms:.3f}ms  Fused:{fsd_ms:.3f}ms  [{label}]")

print()

# ── Section 2: Layer throughput (realistic SIREN sizes) ───────────────────────

header("2. Layer throughput: EMLLayer vs FusedEMLLayer")
print()
print(f"  {'Config':<28}  {'EMLLayer':>10}  {'FusedEML':>10}  {'Speedup':>10}")
print("  " + "-" * 64)

for in_f, out_f, depth, batch in [
    (1, 64, 2, 16),
    (64, 64, 2, 16),
    (64, 64, 2, 128),
    (64, 64, 2, 1024),
    (256, 256, 2, 128),
    (256, 256, 3, 128),
]:
    x   = torch.randn(batch, in_f)
    eml = EMLLayer(in_f, out_f, depth=depth)
    fsd = FusedEMLLayer(in_f, out_f, depth=depth)
    eml_ms, _ = timed(lambda: eml(x))
    fsd_ms, _ = timed(lambda: fsd(x))
    label = speedup_label(eml_ms, fsd_ms)
    cfg = f"({in_f}->{out_f}, d={depth}, b={batch})"
    print(f"  {cfg:<28}  {eml_ms:>10.3f}  {fsd_ms:>10.3f}  {label:>10}")

print()

# ── Section 3: Training step benchmark ───────────────────────────────────────

header("3. Training step: full backward pass")
print()

class SirenEML(nn.Module):
    def __init__(self, width=64, depth=2):
        super().__init__()
        self.layers = nn.ModuleList([
            EMLLayer(1, width, depth=depth),
            EMLLayer(width, width, depth=depth),
            EMLLayer(width, width, depth=depth),
        ])
        self.out = nn.Linear(width, 1)

    def forward(self, x):
        for l in self.layers:
            x = l(x)
        return self.out(x)


class SirenFused(nn.Module):
    def __init__(self, width=64, depth=2):
        super().__init__()
        self.layers = nn.ModuleList([
            FusedEMLLayer(1, width, depth=depth),
            FusedEMLLayer(width, width, depth=depth),
            FusedEMLLayer(width, width, depth=depth),
        ])
        self.out = nn.Linear(width, 1)

    def forward(self, x):
        for l in self.layers:
            x = l(x)
        return self.out(x)


class SirenNative(nn.Module):
    def __init__(self, width=64):
        super().__init__()
        self.l1 = nn.Linear(1, width)
        self.l2 = nn.Linear(width, width)
        self.l3 = nn.Linear(width, width)
        self.out = nn.Linear(width, 1)

    def forward(self, x):
        x = torch.sin(30.0 * self.l1(x))
        x = torch.sin(self.l2(x))
        x = torch.sin(self.l3(x))
        return self.out(x)


def training_step_ms(model, x, y, n_warmup=5, n_repeat=20):
    """Measure one full training step (forward + backward + optimizer)."""
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    import statistics

    def step():
        opt.zero_grad()
        loss = F.mse_loss(model(x).squeeze(), y)
        loss.backward()
        opt.step()

    for _ in range(n_warmup):
        step()

    times = []
    for _ in range(n_repeat):
        t0 = time.perf_counter()
        step()
        times.append((time.perf_counter() - t0) * 1000)
    return statistics.mean(times), statistics.stdev(times)


torch.manual_seed(42)
x_siren = torch.linspace(-math.pi, math.pi, 256).unsqueeze(1)
y_siren = torch.sin(3.0 * x_siren).squeeze()

models = [
    ("SIN-SIREN (native)",    SirenNative(width=64)),
    ("EML-SIREN (baseline)",  SirenEML(width=64, depth=2)),
    ("Fused-SIREN",           SirenFused(width=64, depth=2)),
]

print(f"  {'Model':<28}  {'ms/step':>9}  {'vs EML':>8}")
print("  " + "-" * 50)

eml_ms = None
for name, model in models:
    mean_ms, std_ms = training_step_ms(model, x_siren, y_siren)
    if "EML-SIREN" in name and "baseline" in name:
        eml_ms = mean_ms
    vs_eml = ""
    if eml_ms and name != "EML-SIREN (baseline)":
        ratio = eml_ms / mean_ms
        vs_eml = f"{ratio:.1f}x" if ratio >= 1 else f"1/{1/ratio:.1f}x"
    print(f"  {name:<28}  {mean_ms:>9.2f}  {vs_eml:>8}")

print()

# ── Section 4: Node count vs throughput summary ───────────────────────────────

header("4. Node count vs performance summary")
print()
print("  EMLLayer depth=2:")
print(f"    EML nodes (activation): {(1 << 2) - 1}")
print(f"    EML nodes (vs sin):     245 nodes in Taylor-8 = 82x more complex")
print()
print("  FusedEMLLayer advantage:")
print("    - No Python recursion overhead")
print("    - All leaf evaluations in single (4,N) broadcast")
print("    - Better memory locality")
print()

# ── Section 5: Optional torch.compile timing ─────────────────────────────────

header("5. torch.compile timing (if available)")
print()

fused = FusedEMLLayer(64, 64, depth=2)
x_c   = torch.randn(128, 64)

try:
    import warnings
    compiled = compile_eml_layer(fused)
    # Test if compilation actually works
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with torch.no_grad():
            compiled(x_c)

    fsd_ms, _ = timed(lambda: fused(x_c))
    cmp_ms, _ = timed(lambda: compiled(x_c))
    label = speedup_label(fsd_ms, cmp_ms)
    print(f"  FusedEMLLayer:         {fsd_ms:.3f} ms")
    print(f"  FusedEMLLayer+compile: {cmp_ms:.3f} ms  [{label}]")
except Exception as e:
    print(f"  torch.compile not available on this platform ({e})")
    print("  (Linux/Mac with PyTorch >= 2.0 required for full Inductor support)")

print()
print("=" * 64)
print("  DONE")
print("=" * 64)
print()
print("  To run the full benchmark suite:")
print("    python benchmarks/kernel_benchmarks.py")
print()
