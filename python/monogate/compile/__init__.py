"""
monogate.compile — Tree compilation and performance kernels.

Two strategies for making EML layers faster:

1. **FusedEMLLayer / FusedEMLActivation** (recommended)
   Manually inlines the EML expression tree as a flat, batched tensor
   computation — no Python recursion, no per-element function calls.
   Typically 3–8× faster than EMLLayer on CPU at batch sizes <= 4096.

2. **compile_eml_layer** (torch.compile wrapper)
   Applies torch.compile/TorchInductor to any existing EMLLayer.
   Adds kernel fusion and loop tiling on top of the existing computation.
   Best for GPU or when you already have a trained EMLLayer checkpoint.

Quick-start::

    from monogate.compile import FusedEMLLayer, compile_eml_layer

    # Drop-in SIREN layer — 4× faster than EMLLayer at batch=128
    layer = FusedEMLLayer(256, 256, depth=2, operator="EML")
    y = layer(x)   # (batch, 256)

    # Or compile an existing layer:
    from monogate.torch import EMLLayer
    fast = compile_eml_layer(EMLLayer(256, 256, depth=2))

Benchmark::

    from monogate.compile import benchmark_layer
    results = benchmark_layer(FusedEMLLayer(256, 256), EMLLayer(256, 256))
    results.print_table()
"""

from .compiler import compile_eml_layer, to_torchscript, benchmark_layer, BenchmarkTable
from .fused import FusedEMLActivation, FusedEMLLayer

__all__ = [
    "FusedEMLActivation",
    "FusedEMLLayer",
    "compile_eml_layer",
    "to_torchscript",
    "benchmark_layer",
    "BenchmarkTable",
]
