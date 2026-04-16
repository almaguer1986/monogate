"""
monogate.fused_rust — Optional Rust-accelerated EML evaluator.

When ``monogate-core`` is installed, provides the fastest available EML
evaluation path: 5.9x speedup over recursive Python at depth-2 on CPU.

Priority order when ``EMLLayer(compiled=True)`` is used:
  1. **Rust** (``monogate-core``) — if installed and batch >= RUST_BATCH_THRESHOLD
  2. **FusedEMLActivation** — pure PyTorch, 3.6x over baseline
  3. **EMLActivation** — standard recursive Python (always available)

Install the Rust extension (one-time, ~30 s compile):

    cd monogate-core
    pip install maturin
    maturin develop --release

Verify:

    python -c "from monogate.fused_rust import rust_info; rust_info()"

Exports
-------
RUST_AVAILABLE : bool
    True when monogate_core is importable.

RustFusedLayer : nn.Module | None
    Drop-in replacement for FusedEMLActivation using Rust kernels for large
    batches, PyTorch fallback for small batches or non-CPU devices.
    None when monogate_core is not installed.

rust_info() -> None
    Print a human-readable status summary.

Example
-------
    from monogate.fused_rust import RustFusedLayer, RUST_AVAILABLE
    import torch

    if RUST_AVAILABLE:
        act = RustFusedLayer(depth=2, operator="EML")
        y   = act(torch.linspace(-1, 1, 10_000))   # uses Rust path
        print(f"Throughput: {act.throughput_mps():.0f} M eval/sec")
    else:
        print("Rust not installed — using FusedEMLActivation (3.6x baseline).")
        print("Install: cd monogate-core && pip install maturin && maturin develop --release")
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import torch
import torch.nn as nn
from torch import Tensor

if TYPE_CHECKING:
    import numpy as np

# ── Optional Rust import ──────────────────────────────────────────────────────

_RUST_IMPORT_ERROR: str | None = None

try:
    import monogate_core as _core  # type: ignore[import]
    RUST_AVAILABLE: bool = True
    _RUST_VERSION: str = getattr(_core, "__version__", "unknown")
except ImportError as _e:
    RUST_AVAILABLE = False
    _RUST_VERSION = "not installed"
    _RUST_IMPORT_ERROR = str(_e)
    _core = None  # type: ignore[assignment]

# ── Batch-size threshold for switching to Rust ────────────────────────────────

#: Elements below this threshold use the PyTorch path (avoids numpy roundtrip).
RUST_BATCH_THRESHOLD: int = 512


# ── RustFusedLayer ────────────────────────────────────────────────────────────

def _make_rust_fused_layer():
    """Return the RustFusedLayer class (defined lazily to avoid import errors)."""

    class RustFusedLayer(nn.Module):
        """
        Fused EML activation backed by the ``monogate_core`` Rust extension.

        Provides the fastest available EML evaluation path:

        * **Rust path**: for CPU tensors with ``numel() >= rust_threshold``
          and ``requires_grad=False``.  Calls rayon-parallel Rust kernel
          via PyO3.  No autograd through Rust — inference/evaluation only.
        * **PyTorch fallback**: for training, small tensors, or GPU tensors.
          Shares the same ``leaf_w`` / ``leaf_b`` parameters.

        API is identical to ``FusedEMLActivation``.

        Parameters
        ----------
        depth : int
            EML tree depth 1–3.  depth=4 raises ValueError (Numerical
            Overflow Barrier).
        operator : str
            ``"EML"`` or ``"BEST"``.
        rust_threshold : int
            Minimum ``numel()`` to engage the Rust path.
            Default: ``RUST_BATCH_THRESHOLD`` (512).
        """

        def __init__(
            self,
            depth: int = 2,
            operator: str = "EML",
            rust_threshold: int = RUST_BATCH_THRESHOLD,
        ) -> None:
            super().__init__()

            if not 1 <= depth <= 3:
                raise ValueError(
                    f"RustFusedLayer depth must be 1–3, got {depth}.\n"
                    "  depth=4+ causes Numerical Overflow Barrier.\n"
                    "  For depth>3, use EMLLayer without compiled=True."
                )
            op = operator.upper()
            if op not in ("EML", "BEST"):
                raise ValueError(
                    f"RustFusedLayer supports operator='EML' or 'BEST', "
                    f"got {operator!r}.\n"
                    "  For EDL/EXL, use EMLLayer(operator='EDL') without compiled=True."
                )

            self.depth = depth
            self.operator = op
            self.rust_threshold = rust_threshold

            n_leaves = 1 << depth
            self.leaf_w = nn.Parameter(torch.randn(n_leaves) * 0.05)
            self.leaf_b = nn.Parameter(torch.ones(n_leaves))

            self._py_fallback: nn.Module | None = None

        def _get_fallback(self) -> nn.Module:
            """Return (and cache) the Python FusedEMLActivation fallback."""
            if self._py_fallback is None:
                from monogate.compile.fused import FusedEMLActivation
                fallback = FusedEMLActivation(depth=self.depth, operator=self.operator)
                fallback.leaf_w = self.leaf_w   # shared — same Parameter objects
                fallback.leaf_b = self.leaf_b
                self._py_fallback = fallback
            return self._py_fallback

        def forward(self, x: Tensor) -> Tensor:
            """
            Apply the fused EML activation.

            Routes to Rust for large CPU inference tensors; falls back to
            ``FusedEMLActivation`` for training, small batches, or GPU.
            """
            import numpy as np

            n = x.numel()
            use_rust = (
                RUST_AVAILABLE
                and n >= self.rust_threshold
                and not x.requires_grad
                and x.device.type == "cpu"
            )

            if use_rust:
                shape = x.shape
                flat_np: np.ndarray = x.detach().reshape(-1).to(torch.float64).numpy()
                w_np: np.ndarray = self.leaf_w.detach().to(torch.float64).numpy()
                b_np: np.ndarray = self.leaf_b.detach().to(torch.float64).numpy()

                out_np: np.ndarray = _core.eval_eml_batch(
                    w_np.tolist(), b_np.tolist(), flat_np.tolist(),
                    depth=self.depth,
                )
                return torch.tensor(out_np, dtype=x.dtype).reshape(shape)

            return self._get_fallback()(x)

        def throughput_mps(self, n: int = 1_000_000, depth: int | None = None) -> float:
            """
            Rust kernel throughput in millions of evaluations per second.

            Returns 0.0 if Rust is unavailable.
            """
            if not RUST_AVAILABLE:
                return 0.0
            d = depth if depth is not None else self.depth
            return float(_core.benchmark_rust(n=n, depth=d))

        def extra_repr(self) -> str:
            n_nodes = (1 << self.depth) - 1
            backend = f"rust_v{_RUST_VERSION}" if RUST_AVAILABLE else "rust_unavailable"
            return (
                f"depth={self.depth}, operator={self.operator!r}, "
                f"nodes={n_nodes}, leaves={1 << self.depth}, "
                f"backend={backend}, threshold={self.rust_threshold}"
            )

    return RustFusedLayer


if RUST_AVAILABLE:
    RustFusedLayer = _make_rust_fused_layer()
else:
    RustFusedLayer = None  # type: ignore[assignment,misc]


# ── Public helpers ────────────────────────────────────────────────────────────

def rust_info() -> None:
    """Print a human-readable Rust extension status and benchmark."""
    if RUST_AVAILABLE:
        try:
            mps = _core.benchmark_rust(n=100_000, depth=2)
        except Exception:
            mps = float("nan")
        threshold = getattr(_core, "PARALLEL_THRESHOLD", RUST_BATCH_THRESHOLD)
        print(f"monogate_core {_RUST_VERSION} installed  (5.9x faster than baseline)")
        print(f"  Quick benchmark (depth=2, n=100k): {mps:.0f} M eval/sec")
        print(f"  Rayon parallel threshold:           {threshold} elements")
        print(f"  EMLLayer(compiled=True) => Rust path active for batches >= {threshold}")
    else:
        print("monogate_core NOT installed  (Rust 5.9x speedup unavailable)")
        print()
        print("  Current best without Rust: FusedEMLActivation (3.6x over baseline)")
        print()
        print("  To install (one-time ~30 s compile):")
        print("    cd monogate-core")
        print("    pip install maturin")
        print("    maturin develop --release")
        print()
        if _RUST_IMPORT_ERROR:
            print(f"  Import error was: {_RUST_IMPORT_ERROR}")


def get_best_activation(depth: int = 2, operator: str = "EML") -> nn.Module:
    """
    Return the fastest available EML activation for the given depth/operator.

    Priority: RustFusedLayer > FusedEMLActivation > EMLActivation.

    This is the function used internally by EMLLayer(compiled=True).
    """
    if RUST_AVAILABLE and 1 <= depth <= 3 and operator.upper() in ("EML", "BEST"):
        return _make_rust_fused_layer()(depth=depth, operator=operator)

    if 1 <= depth <= 3 and operator.upper() in ("EML", "BEST"):
        from monogate.compile.fused import FusedEMLActivation
        return FusedEMLActivation(depth=depth, operator=operator)

    # Fallback: standard (supports all depths and operators)
    from monogate.torch.eml_layer import EMLActivation
    return EMLActivation(depth=depth, operator=operator)
