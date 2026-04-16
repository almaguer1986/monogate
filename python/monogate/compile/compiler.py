"""
monogate.compile.compiler — torch.compile wrappers and benchmarking.
"""

from __future__ import annotations

import sys
import time
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import torch
import torch.nn as nn
from torch import Tensor

if TYPE_CHECKING:
    from ..torch.eml_layer import EMLLayer

__all__ = ["compile_eml_layer", "to_torchscript", "benchmark_layer", "BenchmarkTable"]


# ── torch.compile wrapper ─────────────────────────────────────────────────────

def compile_eml_layer(
    layer: nn.Module,
    mode: str = "default",
    backend: str | None = None,
    **kwargs,
) -> nn.Module:
    """
    Apply torch.compile to an EMLLayer or FusedEMLLayer.

    On systems with TorchInductor (Linux/Mac): fuses exp + softplus + log into
    a single kernel.  On Windows: falls back to 'eager' backend automatically.

    Args:
        layer:   EMLLayer or FusedEMLLayer to compile.
        mode:    torch.compile mode: 'default', 'reduce-overhead', 'max-autotune'.
        backend: torch.compile backend override.  None → auto-select.
        **kwargs: Forwarded to torch.compile.

    Returns:
        Compiled module (or original module if compilation fails gracefully).

    Example::

        from monogate.torch import EMLLayer
        from monogate.compile import compile_eml_layer

        layer = EMLLayer(256, 256, depth=2)
        fast  = compile_eml_layer(layer, mode="reduce-overhead")
        y = fast(x)

    Notes:
        - Compiled layers cannot be pickled directly; save state_dict() instead.
        - First forward pass triggers compilation (warm-up cost).
        - Compilation is skipped and a warning is issued if torch.compile is
          unavailable (torch < 2.0) or if an unrecoverable error occurs.
    """
    if not hasattr(torch, "compile"):
        warnings.warn(
            "torch.compile requires PyTorch >= 2.0. Returning original layer.",
            stacklevel=2,
        )
        return layer

    compile_kwargs: dict = {"mode": mode, **kwargs}
    if backend is not None:
        compile_kwargs["backend"] = backend

    try:
        compiled = torch.compile(layer, **compile_kwargs)
        return compiled
    except Exception as exc:
        warnings.warn(
            f"torch.compile failed ({exc}). "
            "Retrying with backend='eager'...",
            stacklevel=2,
        )

    try:
        return torch.compile(layer, backend="eager", mode=mode)
    except Exception as exc2:
        warnings.warn(
            f"torch.compile (eager) also failed ({exc2}). "
            "Returning original uncompiled layer.",
            stacklevel=2,
        )
        return layer


# ── TorchScript export ────────────────────────────────────────────────────────

def to_torchscript(
    layer: nn.Module,
    example_input: Tensor | None = None,
    method: str = "trace",
) -> torch.jit.ScriptModule:
    """
    Export an EMLLayer or FusedEMLLayer to TorchScript.

    TorchScript removes Python overhead entirely and is suitable for
    deployment in C++ or mobile environments.

    Args:
        layer:         Module to export.
        example_input: Sample input tensor.  If None, uses randn(1, in_features).
        method:        'trace' (default) or 'script'.  Trace is simpler; script
                       handles data-dependent control flow.

    Returns:
        TorchScript module (torch.jit.ScriptModule).

    Example::

        from monogate.compile import FusedEMLLayer, to_torchscript

        layer  = FusedEMLLayer(64, 64, depth=2)
        script = to_torchscript(layer)
        torch.jit.save(script, "eml_layer.pt")
        loaded = torch.jit.load("eml_layer.pt")
    """
    layer.eval()

    if example_input is None:
        in_f = getattr(layer, "in_features", 8)
        example_input = torch.randn(1, in_f)

    if method == "script":
        return torch.jit.script(layer)
    else:
        with torch.no_grad():
            return torch.jit.trace(layer, example_input)


# ── Benchmark ─────────────────────────────────────────────────────────────────

@dataclass
class _TimingRow:
    name:       str
    batch:      int
    mean_ms:    float
    std_ms:     float
    speedup:    float   # vs first row (baseline)


@dataclass
class BenchmarkTable:
    """
    Timing results from benchmark_layer().

    Attributes:
        rows:       List of _TimingRow (one per layer × batch-size combination).
        in_features: Input dimension used.
        out_features: Output dimension used.
        depth:      EML tree depth.
        device:     'cpu' or 'cuda'.
    """
    rows:         list[_TimingRow] = field(default_factory=list)
    in_features:  int = 0
    out_features: int = 0
    depth:        int = 0
    device:       str = "cpu"

    def print_table(self) -> None:
        """Print a formatted benchmark table to stdout."""
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

        print()
        print("=" * 74)
        print(f"  monogate.compile benchmark  "
              f"(in={self.in_features}, out={self.out_features}, "
              f"depth={self.depth}, device={self.device})")
        print("=" * 74)
        print(f"  {'Layer':<32}  {'Batch':>6}  {'Mean ms':>9}  {'Std ms':>8}  {'Speedup':>8}")
        print("  " + "-" * 70)

        for row in self.rows:
            sp = f"{row.speedup:.2f}x" if row.speedup != 1.0 else "baseline"
            print(f"  {row.name:<32}  {row.batch:>6}  {row.mean_ms:>9.3f}  "
                  f"{row.std_ms:>8.3f}  {sp:>8}")

        print("=" * 74)
        print()

    def as_dict(self) -> dict:
        return {
            "rows": [
                {
                    "name": r.name, "batch": r.batch,
                    "mean_ms": round(r.mean_ms, 4),
                    "std_ms": round(r.std_ms, 4),
                    "speedup": round(r.speedup, 3),
                }
                for r in self.rows
            ],
            "in_features": self.in_features,
            "out_features": self.out_features,
            "depth": self.depth,
            "device": self.device,
        }


def benchmark_layer(
    *layers: nn.Module,
    batch_sizes: tuple[int, ...] = (16, 128, 1024),
    n_warmup: int = 10,
    n_repeat: int = 50,
    device: str = "cpu",
    names: list[str] | None = None,
) -> BenchmarkTable:
    """
    Time multiple layers across batch sizes and return a BenchmarkTable.

    Layers are timed in inference mode (torch.no_grad) after warm-up.
    The first layer is used as the baseline for speedup computation.

    Args:
        *layers:     nn.Module instances to benchmark.
        batch_sizes: Batch sizes to test.
        n_warmup:    Number of warm-up forward passes (not timed).
        n_repeat:    Number of timed forward passes per measurement.
        device:      'cpu' or 'cuda'.
        names:       Optional list of display names for each layer.

    Returns:
        BenchmarkTable with timing rows.

    Example::

        from monogate.torch import EMLLayer
        from monogate.compile import FusedEMLLayer, benchmark_layer

        results = benchmark_layer(
            EMLLayer(256, 256, depth=2),
            FusedEMLLayer(256, 256, depth=2),
            batch_sizes=(16, 128, 1024),
        )
        results.print_table()
    """
    if not layers:
        raise ValueError("At least one layer required.")

    import statistics

    # Auto-detect in_features and depth from first layer
    first = layers[0]
    in_f   = getattr(first, "in_features",  8)
    out_f  = getattr(first, "out_features", 8)
    depth  = getattr(first, "depth",        2)

    if names is None:
        names = [type(l).__name__ for l in layers]

    table = BenchmarkTable(
        in_features=in_f, out_features=out_f, depth=depth, device=device
    )

    # baseline: mean_ms of first layer at first batch_size
    baseline_ms: float | None = None

    for name, layer in zip(names, layers):
        layer = layer.to(device)
        layer.eval()

        for batch in batch_sizes:
            x = torch.randn(batch, in_f, device=device)

            # Warm-up
            with torch.no_grad():
                for _ in range(n_warmup):
                    _ = layer(x)

            # Time
            times: list[float] = []
            with torch.no_grad():
                for _ in range(n_repeat):
                    if device == "cuda":
                        torch.cuda.synchronize()
                    t0 = time.perf_counter()
                    _ = layer(x)
                    if device == "cuda":
                        torch.cuda.synchronize()
                    times.append((time.perf_counter() - t0) * 1_000)

            mean_ms = statistics.mean(times)
            std_ms  = statistics.stdev(times) if len(times) > 1 else 0.0

            if baseline_ms is None:
                baseline_ms = mean_ms

            speedup = baseline_ms / mean_ms if mean_ms > 0 else float("inf")

            table.rows.append(_TimingRow(
                name=name, batch=batch,
                mean_ms=mean_ms, std_ms=std_ms, speedup=speedup,
            ))

    return table
