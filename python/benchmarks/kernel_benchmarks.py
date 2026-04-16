"""
benchmarks/kernel_benchmarks.py — EML kernel performance comparison.

Measures wall-clock throughput for:
  1. EMLLayer (baseline — recursive Python EMLNetwork)
  2. FusedEMLLayer (flat vectorized tree computation)
  3. FusedEMLLayer + torch.compile (when available)
  4. Native torch.sin (reference ceiling)

Usage:
    cd python/
    python benchmarks/kernel_benchmarks.py
    python benchmarks/kernel_benchmarks.py --depth 1 --batch 64 512 4096
    python benchmarks/kernel_benchmarks.py --save results/kernel_bench.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import warnings
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
from torch import Tensor

from monogate.compile import FusedEMLLayer, compile_eml_layer, benchmark_layer
from monogate.torch import EMLLayer


# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_BATCH_SIZES = (4, 16, 64, 128, 512, 1024, 4096)
IN_FEATURES  = 256
OUT_FEATURES = 256
DEPTH        = 2
N_WARMUP     = 20
N_REPEAT     = 100


# ── Native sin reference ──────────────────────────────────────────────────────

class NativeSin(nn.Module):
    """nn.Module wrapper around torch.sin — the performance ceiling."""
    def __init__(self, in_f: int, out_f: int):
        super().__init__()
        self.linear = nn.Linear(in_f, out_f)
        # Near-identity init so output scale is comparable to EMLLayer
        nn.init.eye_(self.linear.weight[:min(in_f, out_f), :min(in_f, out_f)])

    def forward(self, x: Tensor) -> Tensor:
        return torch.sin(self.linear(x))


# ── Timing helpers ────────────────────────────────────────────────────────────

def _time_layer(
    layer: nn.Module,
    batch: int,
    in_f: int,
    n_warmup: int,
    n_repeat: int,
    device: str = "cpu",
) -> tuple[float, float]:
    """Returns (mean_ms, std_ms)."""
    import statistics

    layer = layer.to(device).eval()
    x = torch.randn(batch, in_f, device=device)

    with torch.no_grad():
        for _ in range(n_warmup):
            layer(x)

    times = []
    with torch.no_grad():
        for _ in range(n_repeat):
            t0 = time.perf_counter()
            layer(x)
            times.append((time.perf_counter() - t0) * 1_000)

    return statistics.mean(times), statistics.stdev(times) if len(times) > 1 else 0.0


# ── Main benchmark ────────────────────────────────────────────────────────────

def run_benchmark(
    batch_sizes: tuple[int, ...] = DEFAULT_BATCH_SIZES,
    in_features: int = IN_FEATURES,
    out_features: int = OUT_FEATURES,
    depth: int = DEPTH,
    operator: str = "EML",
    device: str = "cpu",
    n_warmup: int = N_WARMUP,
    n_repeat: int = N_REPEAT,
) -> dict:
    """
    Run the full kernel benchmark and return a results dict.

    Returns:
        dict with keys: config, layers, batch_sizes, rows
        Each row: {layer, batch, mean_ms, std_ms, speedup_vs_eml, speedup_vs_sin}
    """
    print()
    print("=" * 78)
    print(f"  monogate kernel benchmark")
    print(f"  in={in_features}, out={out_features}, depth={depth}, "
          f"operator={operator!r}, device={device}")
    print(f"  warmup={n_warmup}, repeat={n_repeat}")
    print("=" * 78)

    # ── Build layers ──────────────────────────────────────────────────────
    torch.manual_seed(0)
    # Three-way comparison: EMLLayer (recursive Python) vs compiled=True (fused)
    # vs fused + torch.compile — plus the native sin ceiling.
    eml_op = operator if operator in ("EML", "BEST") else "EML"
    layers: dict[str, nn.Module] = {
        "EMLLayer (recursive)":          EMLLayer(in_features, out_features, depth=depth, operator=operator),
        "EMLLayer(compiled=True)":       EMLLayer(in_features, out_features, depth=depth,
                                                   operator=eml_op, compiled=(depth <= 3)),
        "FusedEMLLayer":                 FusedEMLLayer(in_features, out_features, depth=depth,
                                                        operator=eml_op) if depth <= 3 else None,
        "torch.sin (ceiling)":           NativeSin(in_features, out_features),
    }
    # Remove depth-limited layers that could not be built
    layers = {k: v for k, v in layers.items() if v is not None}

    # Attempt to add fused + torch.compile variant
    if depth <= 3:
        fused_for_compile = FusedEMLLayer(in_features, out_features, depth=depth, operator=eml_op)
        compiled = compile_eml_layer(fused_for_compile)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with torch.no_grad():
                    compiled(torch.randn(4, in_features))
            if compiled is not fused_for_compile:
                layers["FusedEMLLayer + torch.compile"] = compiled
            else:
                print("  [note] torch.compile not available on this platform — skipped")
        except Exception as e:
            print(f"  [note] torch.compile failed ({e}) — skipped")

    # ── Header ────────────────────────────────────────────────────────────
    col_w = 28
    print(f"\n  {'Layer':<{col_w}}  {'Batch':>6}  {'Mean ms':>9}  {'Std ms':>8}  {'vs EML':>8}  {'vs sin':>8}")
    print("  " + "-" * 76)

    # ── Collect baseline timings (EMLLayer at each batch) ─────────────────
    eml_times: dict[int, float] = {}
    sin_times: dict[int, float] = {}

    baseline_layer = layers["EMLLayer (recursive)"]
    sin_layer      = layers["torch.sin (ceiling)"]

    for batch in batch_sizes:
        eml_times[batch], _ = _time_layer(baseline_layer, batch, in_features, n_warmup, n_repeat, device)
        sin_times[batch], _ = _time_layer(sin_layer, batch, in_features, n_warmup, n_repeat, device)

    # ── Full measurement ──────────────────────────────────────────────────
    rows = []
    for name, layer in layers.items():
        for batch in batch_sizes:
            mean_ms, std_ms = _time_layer(layer, batch, in_features, n_warmup, n_repeat, device)

            speedup_eml = eml_times[batch] / mean_ms if mean_ms > 0 else float("inf")
            speedup_sin = sin_times[batch] / mean_ms if mean_ms > 0 else float("inf")

            eml_tag = f"{speedup_eml:.2f}x" if name != "EMLLayer (recursive)" else "1.0x"
            sin_tag = f"{speedup_sin:.2f}x"

            print(f"  {name:<{col_w}}  {batch:>6}  {mean_ms:>9.3f}  {std_ms:>8.3f}  "
                  f"{eml_tag:>8}  {sin_tag:>8}")

            rows.append({
                "layer":          name,
                "batch":          batch,
                "mean_ms":        round(mean_ms, 4),
                "std_ms":         round(std_ms, 4),
                "speedup_vs_eml": round(speedup_eml, 3),
                "speedup_vs_sin": round(speedup_sin, 3),
            })

    print("=" * 78)

    # ── Print summary ─────────────────────────────────────────────────────
    # Summary: three-way comparison at batch=128
    target_batch = 128 if 128 in batch_sizes else batch_sizes[len(batch_sizes) // 2]
    eml_row  = next((r for r in rows if r["layer"] == "EMLLayer (recursive)" and r["batch"] == target_batch), None)
    fused_row    = next((r for r in rows if r["layer"] in ("EMLLayer(compiled=True)", "FusedEMLLayer")
                         and r["batch"] == target_batch), None)
    compile_row  = next((r for r in rows if "torch.compile" in r["layer"] and r["batch"] == target_batch), None)
    sin_row      = next((r for r in rows if r["layer"] == "torch.sin (ceiling)" and r["batch"] == target_batch), None)

    print(f"\n  Three-way comparison at batch={target_batch}:")
    if eml_row:
        print(f"    EMLLayer (recursive)         : {eml_row['mean_ms']:.3f} ms  (1.0× baseline)")
    if fused_row:
        sp = eml_row['mean_ms'] / fused_row['mean_ms'] if eml_row else 1.0
        print(f"    EMLLayer(compiled=True)       : {fused_row['mean_ms']:.3f} ms  ({sp:.1f}× vs baseline)")
    if compile_row:
        sp = eml_row['mean_ms'] / compile_row['mean_ms'] if eml_row else 1.0
        print(f"    FusedEMLLayer + torch.compile : {compile_row['mean_ms']:.3f} ms  ({sp:.1f}× vs baseline)")
    if sin_row:
        ratio = eml_row['mean_ms'] / sin_row['mean_ms'] if eml_row else 0.0
        print(f"    torch.sin (ceiling)           : {sin_row['mean_ms']:.3f} ms  ({ratio:.0f}× EML overhead)")

    print()

    return {
        "config": {
            "in_features": in_features,
            "out_features": out_features,
            "depth": depth,
            "operator": operator,
            "device": device,
        },
        "batch_sizes": list(batch_sizes),
        "layers": list(layers.keys()),
        "rows": rows,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="monogate kernel performance benchmark"
    )
    parser.add_argument("--batch", type=int, nargs="+",
                        default=list(DEFAULT_BATCH_SIZES))
    parser.add_argument("--in-features", type=int, default=IN_FEATURES)
    parser.add_argument("--out-features", type=int, default=OUT_FEATURES)
    parser.add_argument("--depth", type=int, default=DEPTH)
    parser.add_argument("--operator", default="EML", choices=["EML", "BEST"])
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--warmup", type=int, default=N_WARMUP)
    parser.add_argument("--repeat", type=int, default=N_REPEAT)
    parser.add_argument("--save", default=None, help="Save results JSON to path.")
    args = parser.parse_args()

    results = run_benchmark(
        batch_sizes=tuple(args.batch),
        in_features=args.in_features,
        out_features=args.out_features,
        depth=args.depth,
        operator=args.operator,
        device=args.device,
        n_warmup=args.warmup,
        n_repeat=args.repeat,
    )

    if args.save:
        path = Path(args.save)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(results, indent=2))
        print(f"Results saved -> {path}")


if __name__ == "__main__":
    main()
