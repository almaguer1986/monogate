"""
Experiment 12: SIREN-style Network (sin-heavy)
==============================================
SIREN (Sitzmann et al., 2020) uses sin activations throughout.  Because sin
has a 74% node reduction under BEST routing, this architecture sits at the
maximum end of the BEST-benefit spectrum.

What this experiment measures
------------------------------
A. Static analysis        — best_optimize_model() node report per layer
B. Per-element benchmark  — sin_eml_taylor vs sin_best_taylor (scalar)
C. Extrapolated estimate  — scale B up to a full forward pass
D. Native baseline        — torch.sin for context (outside EML substrate)
E. Summary                — crossover check + linear-model comparison

Notes
-----
- best_optimize_model is analysis-only (Option A): it reports what BEST would
  change but does NOT replace forward methods.  Both timed models use torch.sin.
- sin_eml_taylor requires x > 1 (pow_eml constraint on the base).
  sin_best_taylor (pow_exl via complex arithmetic) works for all real x.
- EML/BEST arithmetic operates on Python scalars.  Native torch.sin is always
  faster; the substrate is relevant for symbolic regression and interpretable
  EML expression trees, not production inference.

Results (CPU, Windows 11, Python 3.14)
------------------------------------------
A. Static analysis
  layers.0-3.forward: 73% savings each
  ModelOptimizeReport: 73% node savings (280n BEST vs 1032n EML)
  Per SIRENLayer: 1 × sin = 63n BEST vs 245n EML

B. Per-element sin benchmark (x=2.5)
  EML:  45.6 µs/call
  BEST: 13.3 µs/call
  Speedup: 3.43×

C. Extrapolated full-forward (batch=4096, hidden=64, 4 sin layers)
  EML-sin  estimate:  ~47,800 ms
  BEST-sin estimate:  ~13,900 ms
  Speedup:  3.43×  (linear-model pred: 2.76×)

D. Native torch.sin: 5.1 ms/forward  (EML overhead: ~9300×)

E. Summary
  Node savings: 74%  |  EML→BEST speedup: 3.43×
  sin-heavy = maximum BEST benefit; crossover threshold (~20%) well below 74%
"""

import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch
import torch.nn as nn

from monogate import best_optimize_model
from monogate.optimize import benchmark_optimize, sin_best_taylor, sin_eml_taylor


# ── Model definition ──────────────────────────────────────────────────────────

class SIRENLayer(nn.Module):
    def __init__(self, in_features: int, out_features: int, omega: float = 30.0):
        super().__init__()
        self.omega = omega
        self.linear = nn.Linear(in_features, out_features)
        nn.init.uniform_(self.linear.weight, -1 / in_features, 1 / in_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.sin(self.omega * self.linear(x))


class SIREN(nn.Module):
    def __init__(
        self,
        in_features: int = 2,
        hidden: int = 64,
        out_features: int = 1,
        num_layers: int = 5,
    ):
        super().__init__()
        layers: list[nn.Module] = [SIRENLayer(in_features, hidden)]
        for _ in range(num_layers - 2):
            layers.append(SIRENLayer(hidden, hidden))
        layers.append(nn.Linear(hidden, out_features))
        self.layers = nn.ModuleList(layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for layer in self.layers[:-1]:
            x = layer(x)
        return self.layers[-1](x)


# ── Native benchmark helper ───────────────────────────────────────────────────

def benchmark_native(
    model: nn.Module,
    batch_size: int = 4096,
    iters: int = 200,
) -> float:
    """Return wall-clock ms per forward pass (native torch.sin)."""
    x = torch.randn(batch_size, 2)
    for _ in range(20):          # warmup
        _ = model(x)
    t0 = time.perf_counter()
    for _ in range(iters):
        _ = model(x)
    return (time.perf_counter() - t0) / iters * 1_000


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SEP = "-" * 58

    print("=" * 58)
    print("  Experiment 12: SIREN-style Network (sin-heavy)")
    print("=" * 58)

    BATCH    = 4096
    HIDDEN   = 64
    N_LAYERS = 5                         # total; last is Linear (no sin)
    SIN_LAYERS = N_LAYERS - 1            # 4 hidden SIRENLayers

    model = SIREN(
        in_features=2,
        hidden=HIDDEN,
        out_features=1,
        num_layers=N_LAYERS,
    )

    # ── A. Static node analysis ───────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  A. Static node analysis (best_optimize_model)")
    print(SEP)

    report = best_optimize_model(model, verbose=True)
    print()
    print(report)

    sin_best_n = 63
    sin_eml_n  = 245
    print(
        f"  Per SIRENLayer.forward:  1 × sin = {sin_best_n}n BEST "
        f"vs {sin_eml_n}n EML"
    )
    print(
        f"  All {SIN_LAYERS} sin layers:         "
        f"{SIN_LAYERS} × {sin_best_n}n = {SIN_LAYERS * sin_best_n}n BEST "
        f"vs {SIN_LAYERS * sin_eml_n}n EML  (74% savings)"
    )

    # ── B. Per-element sin benchmark ──────────────────────────────────────────
    print(f"\n{SEP}")
    print("  B. Per-element sin benchmark  (EML vs BEST, scalar)")
    print(SEP)
    print("  sin_eml_taylor : pow_eml (15n/power)  — requires x > 1")
    print("  sin_best_taylor: pow_exl ( 3n/power)  — all real x")
    print()

    # x = 2.5: safely > 1, representative of the |omega * h| range.
    X_SCALAR = 2.5
    r_sin = benchmark_optimize(
        sin_eml_taylor,
        sin_best_taylor,
        X_SCALAR,
        label=f"sin 8-term Taylor  (x={X_SCALAR})",
        node_savings_pct=74,
    )
    print(r_sin)

    # ── C. Extrapolated full-forward estimate ─────────────────────────────────
    print(f"\n{SEP}")
    print("  C. Extrapolated full-forward pass")
    print(SEP)

    total_sin = BATCH * HIDDEN * SIN_LAYERS     # scalar sin calls per forward
    ms_eml    = r_sin.before_us * total_sin / 1_000
    ms_best   = r_sin.after_us  * total_sin / 1_000
    speedup   = ms_eml / ms_best if ms_best > 0 else float("inf")

    print(f"  Batch={BATCH}  hidden={HIDDEN}  sin layers={SIN_LAYERS}")
    print(f"  Scalar sin calls per forward:  {total_sin:,}")
    print(f"  EML-sin  estimate:  {ms_eml:,.0f} ms")
    print(f"  BEST-sin estimate:  {ms_best:,.0f} ms")
    print(f"  Speedup:            {speedup:.2f}×")

    # Linear model from experiments 09/11:  speedup ≈ 0.033 × pct + 0.32
    predicted = 0.033 * 74 + 0.32
    print(f"  Linear-model pred:  {predicted:.2f}×  (0.033×74+0.32, R²=0.9992)")

    # ── D. Native torch.sin baseline ─────────────────────────────────────────
    print(f"\n{SEP}")
    print("  D. Native torch.sin baseline  (outside EML substrate)")
    print(SEP)

    ms_native = benchmark_native(model, batch_size=BATCH, iters=200)
    overhead  = ms_eml / ms_native if ms_native > 0 else float("inf")

    print(f"  native torch.sin:          {ms_native:.2f} ms/forward")
    print(f"  EML substrate overhead:    {overhead:.0f}× vs native")
    print()
    print("  EML/BEST arithmetic uses Python scalars; native torch.sin uses")
    print("  C++/BLAS.  The EML substrate is not a drop-in replacement for")
    print("  production inference — it is a symbolic arithmetic layer for")
    print("  interpretable expression trees and differentiable EML programs.")

    # ── E. Summary ────────────────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  E. Summary")
    print(SEP)
    print(f"  Architecture:         SIREN  ({N_LAYERS} layers, hidden={HIDDEN})")
    print(f"  Activation:           torch.sin  (all hidden layers)")
    print(f"  Node savings:         74%  (sin: {sin_best_n}n BEST vs {sin_eml_n}n EML)")
    print(f"  EML→BEST speedup:     {speedup:.2f}×  (within EML arithmetic)")
    print(f"  Linear-model pred:    {predicted:.2f}×")
    print(f"  Crossover threshold:  ~20%  →  74% well above threshold ✓")
    print(f"  Pattern:              sin-heavy = maximum BEST benefit")
    print()
