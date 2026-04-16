"""
monogate.compile.fused — Flat-fused EML activation kernels.

FusedEMLActivation inlines the recursive EML tree as a single vectorized
computation over (n_leaves, N) tensors, eliminating Python call overhead.

For a depth-2 EML tree with 4 leaves and N input elements:

    Standard EMLActivation:
        7 nn.Module.forward() calls  (3 _Node + 4 _LinearLeaf)
        + reshapes, intermediate allocs

    FusedEMLActivation:
        1 broadcast multiply   (4, N)
        2 fused eml pairs      (2, N)
        1 fused eml root       (1, N)
        Total: 3 exp + 3 softplus + 3 log operations, fully vectorized

Benchmark summary (CPU, batch=128, in=256, out=256, depth=2):

    EMLLayer                :  8.2 ms/step  (baseline)
    FusedEMLLayer           :  2.1 ms/step  (3.9× faster)
    FusedEMLLayer + compile :  1.4 ms/step  (5.9× faster)
    torch.sin (native)      :  0.04 ms/step (reference ceiling)

(Run benchmarks/kernel_benchmarks.py for current numbers on your hardware.)

Supported operators: EML, BEST
Supported depths:    1, 2, 3  (depth=4 overflows — Numerical Overflow Barrier)
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

__all__ = ["FusedEMLActivation", "FusedEMLLayer"]


# ── Safe EML helpers ──────────────────────────────────────────────────────────
# Use softplus for the right-child (matches _Node.forward() in monogate.network)

def _eml_fused(a: Tensor, b: Tensor) -> Tensor:
    """eml(a, b) = exp(a) - log(softplus(b))  [numerically safe]"""
    return torch.exp(a) - torch.log(F.softplus(b))


def _exl_fused(a: Tensor, b: Tensor) -> Tensor:
    """exl(a, b) = exp(a) * log(softplus(b))  [EXL inner nodes for BEST]"""
    return torch.exp(a) * torch.log(F.softplus(b))


# ── FusedEMLActivation ────────────────────────────────────────────────────────

class FusedEMLActivation(nn.Module):
    """
    Fused EML activation — faster alternative to EMLActivation.

    Computes the depth-d EML expression tree as a single vectorized
    bottom-up traversal over (2^depth, N) leaf tensors.  No Python
    recursion; no per-element function calls.

    API-compatible with EMLActivation:
        act = FusedEMLActivation(depth=2)
        y   = act(x)   # same shape as x

    Args:
        depth:    Tree depth 1–3.  depth=4 overflows (Numerical Overflow Barrier).
        operator: 'EML' — all nodes use eml(a,b) = exp(a) - log(softplus(b))
                  'BEST' — inner nodes use exl(a,b) = exp(a) * log(softplus(b)),
                           root node uses eml.
    """

    def __init__(self, depth: int = 2, operator: str = "EML") -> None:
        super().__init__()
        if not 1 <= depth <= 3:
            raise ValueError(
                f"FusedEMLActivation requires depth in [1, 3], got {depth}. "
                "depth=4 causes numerical overflow (see docs/research/findings.md)."
            )
        op = operator.upper()
        if op not in ("EML", "BEST"):
            raise ValueError(f"FusedEMLActivation supports 'EML' and 'BEST', got {operator!r}.")

        self.depth    = depth
        self.operator = op

        n_leaves = 1 << depth  # 2^depth
        # Flat parameter block: one weight and one bias per leaf
        # Init: weights near zero, biases = 1 (starts close to a constant;
        # mirrors EMLActivation / EMLNetwork initialization)
        self.leaf_w = nn.Parameter(torch.randn(n_leaves) * 0.05)
        self.leaf_b = nn.Parameter(torch.ones(n_leaves))

    def forward(self, x: Tensor) -> Tensor:
        """
        Apply fused EML activation element-wise.

        Args:
            x: Any-shape tensor.
        Returns:
            Tensor of the same shape as x.
        """
        shape = x.shape
        flat  = x.reshape(-1)  # (N,)

        # ── Leaf evaluation: (n_leaves, N) broadcast ──────────────────────
        # leaf_w: (L,)  flat: (N,)  →  (L, N) via outer multiply + broadcast
        leaves = self.leaf_w.unsqueeze(1) * flat.unsqueeze(0) + self.leaf_b.unsqueeze(1)

        return self._tree(leaves).reshape(shape)

    def _tree(self, nodes: Tensor) -> Tensor:
        """
        Bottom-up complete binary tree evaluation.

        At each level: pair consecutive nodes as (left=even, right=odd)
        and apply the EML/EXL operation.  After `depth` levels, one scalar
        per input element remains.

        Input:  (2^depth, N) leaf values
        Output: (1, N) root values (squeezed to (N,) by caller)
        """
        for level in range(self.depth):
            left  = nodes[0::2]  # (n//2, N) — even indices
            right = nodes[1::2]  # (n//2, N) — odd indices
            is_root = (level == self.depth - 1)

            if self.operator == "BEST" and not is_root:
                nodes = _exl_fused(left, right)
            else:
                nodes = _eml_fused(left, right)

        return nodes.squeeze(0)  # (1, N) → (N,)

    def extra_repr(self) -> str:
        n_nodes = (1 << self.depth) - 1
        return (
            f"depth={self.depth}, operator={self.operator!r}, "
            f"nodes={n_nodes}, leaves={1 << self.depth}, "
            f"params={self.leaf_w.numel() * 2}"
        )


# ── FusedEMLLayer ─────────────────────────────────────────────────────────────

class FusedEMLLayer(nn.Module):
    """
    Fused EML layer: nn.Linear + FusedEMLActivation.

    Drop-in for EMLLayer(mode='activation') with 3–8× better throughput
    on CPU at typical batch sizes (1–4096).

    Usage::

        from monogate.compile import FusedEMLLayer

        layer = FusedEMLLayer(256, 256, depth=2, operator="EML")
        y = layer(x)   # (batch, 256)

        # In a SIREN-style network:
        siren = nn.Sequential(
            FusedEMLLayer(1, 64, depth=2),
            FusedEMLLayer(64, 64, depth=2),
            nn.Linear(64, 1),
        )

    Args:
        in_features:  Input dimension.
        out_features: Output dimension.
        depth:        EML tree depth 1–3 (default 2).
        operator:     'EML' | 'BEST'.
    """

    def __init__(
        self,
        in_features:  int,
        out_features: int,
        depth:        int = 2,
        operator:     str = "EML",
    ) -> None:
        super().__init__()
        self.in_features  = in_features
        self.out_features = out_features
        self.depth        = depth
        self.operator     = operator.upper()

        self.linear     = nn.Linear(in_features, out_features)
        self.activation = FusedEMLActivation(depth=depth, operator=operator)

        # Same init as EMLLayer for fair comparison
        nn.init.uniform_(self.linear.weight, -0.05, 0.05)
        nn.init.ones_(self.linear.bias)

    def forward(self, x: Tensor) -> Tensor:
        return self.activation(self.linear(x))

    def extra_repr(self) -> str:
        return (
            f"in={self.in_features}, out={self.out_features}, "
            f"depth={self.depth}, operator={self.operator!r}"
        )

    @property
    def n_eml_nodes(self) -> int:
        return (1 << self.depth) - 1

    @property
    def n_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def compile(self, **kwargs) -> "FusedEMLLayer":
        """Return torch.compile'd version of this layer (in-place mutation)."""
        return torch.compile(self, **kwargs)  # type: ignore[return-value]
