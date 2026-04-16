"""
monogate.torch.eml_layer — Differentiable EML arithmetic layers for PyTorch.

Two classes:

    EMLActivation  — EML tree as a scalar activation function (element-wise).
                     Drop-in replacement for torch.sin / F.gelu / etc.
                     Shares the same tree parameters across all input positions.

    EMLLayer       — Complete layer combining a linear transform with an EML
                     tree.  Two modes:

                     mode='activation'  (default) — nn.Linear(in, out) → EMLActivation
                         • 2^depth scalar tree parameters (activation)
                         • in * out + out  linear parameters
                         • Recommended for SIREN / NeRF / PINN activation replacement.

                     mode='tree'  — out_features independent EML expression trees,
                         each with linear leaves projecting from in_features.
                         • out_features × (2^depth linear leaves) parameters
                         • Fully interpretable: call layer.formula(feat_names)
                         • Equivalent to out_features stacked EMLNetwork instances.

Operator families:
    'EML'   — eml(a, b) = exp(a) - ln(b)               const=1
    'EDL'   — edl(a, b) = exp(a) / ln(b)  (safe form)  const=e-1
    'EXL'   — exl(a, b) = exp(a) * ln(b)               const=1
    'BEST'  — EXL inner nodes + EML root  (HybridNetwork-style)
              Inner subtrees use EXL for numerical stability;
              the root combines them with EML subtraction.

Serialization:
    Standard torch.save(layer.state_dict()) / load_state_dict() work with
    both modes.  For full reconstruction, save the constructor kwargs alongside:
        torch.save({'kwargs': {...}, 'state': layer.state_dict()}, path)

ONNX export example:
    layer = EMLLayer(8, 16, depth=2, mode='activation')
    dummy = torch.randn(1, 8)
    torch.onnx.export(layer, dummy, 'eml_layer.onnx',
                      input_names=['x'], output_names=['y'],
                      opset_version=17)
    # All ops used (exp, log, mul, sigmoid, softplus) are ONNX-native.

Requires: torch >= 2.0
"""

from __future__ import annotations

import math
from typing import Callable

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from ..torch_ops import op as _eml_op, exl_op as _exl_op, edl_op_safe as _edl_op
from ..network import _Leaf, _LinearLeaf, _Node, _build_tree

__all__ = ["EMLActivation", "EMLLayer"]


# ── Operator registry ─────────────────────────────────────────────────────────

_OP_MAP: dict[str, Callable[[Tensor, Tensor], Tensor]] = {
    "EML": _eml_op,
    "EDL": _edl_op,
    "EXL": _exl_op,
}


def _get_op(operator: str) -> Callable[[Tensor, Tensor], Tensor]:
    op = _OP_MAP.get(operator.upper())
    if op is None and operator.upper() != "BEST":
        raise ValueError(
            f"Unknown operator {operator!r}.  Choose from: "
            f"'EML', 'EDL', 'EXL', 'BEST'."
        )
    return op  # type: ignore[return-value]  # BEST handled separately


# ── EMLActivation ─────────────────────────────────────────────────────────────

class EMLActivation(nn.Module):
    """
    EML tree as a scalar activation function (element-wise, fully vectorized).

    Applies a depth-d EML expression tree to every scalar element of the input.
    Internally wraps ``EMLNetwork(in_features=1, depth)``: the input scalar is
    treated as a 1-D feature, and the tree maps it through learned linear leaves.
    This gives full vectorization — no Python loops, full autograd support.

    The activation has ``2^depth`` leaves, each a ``nn.Linear(1, 1)``.  At init,
    weights are near zero and biases are 1.0, so the activation starts close to a
    constant.  As training proceeds the leaves learn a meaningful transformation.

    Usage::

        act = EMLActivation(depth=2, operator='EML')
        x   = torch.randn(32, 64)
        y   = act(x)               # same shape (32, 64)

        # As a drop-in for sin in SIREN:
        class SIRENLayer(nn.Module):
            def __init__(self, in_f, out_f, depth=2):
                super().__init__()
                self.linear = nn.Linear(in_f, out_f)
                self.act    = EMLActivation(depth=depth)
            def forward(self, x):
                return self.act(self.linear(x))

    Args:
        depth:    Tree depth (1 = single eml node, 2 leaves).
                  depth=d → 2^d - 1 nodes, 2^d leaves.
        operator: 'EML' | 'EDL' | 'EXL' | 'BEST'.
    """

    def __init__(
        self,
        depth:    int = 2,
        operator: str = "EML",
    ) -> None:
        super().__init__()
        if depth < 1:
            raise ValueError("EMLActivation requires depth >= 1")
        self.depth    = depth
        self.operator = operator.upper()

        # Use EMLNetwork(in_features=1) as the vectorized backbone.
        # Each leaf is nn.Linear(1,1); forward maps (N,1) -> (N,).
        if self.operator == "BEST":
            from ..network import HybridNetwork
            self._net = HybridNetwork(in_features=1, depth=depth)
        elif self.operator in _OP_MAP:
            from ..network import EMLNetwork
            self._net = EMLNetwork(
                in_features=1,
                depth=depth,
                op_func=_OP_MAP[self.operator],
            )
        else:
            raise ValueError(
                f"Unknown operator {operator!r}. Choose from: EML, EDL, EXL, BEST."
            )

    def forward(self, x: Tensor) -> Tensor:
        """
        Apply the EML activation element-wise (fully vectorized).

        Args:
            x: Any shape tensor.  The activation is applied to each scalar.
        Returns:
            Tensor of the same shape as x.
        """
        shape  = x.shape
        x_flat = x.reshape(-1, 1)   # (N, 1): treat each scalar as a 1-D feature
        out    = self._net(x_flat)   # (N,)  : EMLNetwork maps 1-D input → scalar
        return out.reshape(shape)

    def extra_repr(self) -> str:
        n_nodes  = (1 << self.depth) - 1
        n_leaves = 1 << self.depth
        return (
            f"depth={self.depth}, operator={self.operator!r}, "
            f"nodes={n_nodes}, leaves={n_leaves}"
        )

    def formula(self, feature_name: str = "x") -> str:
        """Human-readable EML expression with current leaf weights."""
        return self._net.formula([feature_name])


# ── EMLLayer ──────────────────────────────────────────────────────────────────

class EMLLayer(nn.Module):
    """
    EML arithmetic layer — differentiable, serializable, ONNX-compatible.

    Two modes:

    **mode='activation'** (recommended for SIREN / NeRF / PINN):

        Applies ``nn.Linear(in_features, out_features)`` followed by a
        shared ``EMLActivation(depth)`` scalar activation.

        Parameter count:
            in_features * out_features + out_features   (linear)
            + 2^depth                                   (activation)

        Example — replace sin activation in SIREN::

            # Before:
            out = torch.sin(30 * nn.Linear(256, 256)(x))
            # After:
            layer = EMLLayer(256, 256, depth=2, mode='activation')
            out   = layer(x)

        One-liner speedup with ``compiled=True``::

            # Automatically selects fastest available backend:
            #   Rust (5.9×) > FusedEMLActivation (3.6×) > standard
            layer = EMLLayer(256, 256, depth=2, compiled=True)
            out   = layer(x)   # same API, no code changes

            # Maximum speed: also apply torch.compile
            fast  = layer.compile()

            # Check which backend is active:
            print(layer)
            # ...backend=rust  (if monogate-core installed)
            # ...backend=fused (Python fallback, still 3.6×)

        **Rust backend (recommended for best performance):**
        Install ``monogate-core`` once (~30 s compile) and all
        ``EMLLayer(compiled=True)`` instances automatically use the
        Rust path for batches ≥ 512 elements::

            cd monogate-core
            pip install maturin && maturin develop --release
            # 5.9× speedup — no code changes needed

    **mode='tree'** (fully interpretable EML trees):

        ``out_features`` independent EML expression trees, each with
        ``in_features``-dimensional linear leaves.  Each tree maps R^in → R.

        Parameter count:
            out_features * 2^depth * (in_features + 1)  (linear leaves)

        Example::

            layer = EMLLayer(4, 8, depth=2, mode='tree')
            out   = layer(x)           # (batch, 8)
            print(layer.formula(["x", "y", "z", "w"]))  # list of 8 formulas

    Args:
        in_features:  Number of input features.
        out_features: Number of output features (scalars).
        depth:        EML tree depth (default 2).
        operator:     'EML' | 'EDL' | 'EXL' | 'BEST' (default 'EML').
        mode:         'activation' | 'tree' (default 'activation').
        init:         Initial value for scalar leaves / linear biases
                      (default 1.0 — numerically safe starting region).
        compiled:     If True and mode='activation' and depth<=3, use
                      ``FusedEMLActivation`` instead of ``EMLActivation``
                      for a 1.5–3.6× CPU speedup.  Falls back gracefully
                      for depth>3 or mode='tree'.  Call ``.compile()`` on
                      the returned layer to also apply ``torch.compile``.
    """

    def __init__(
        self,
        in_features:  int,
        out_features: int,
        depth:        int = 2,
        operator:     str = "EML",
        mode:         str = "activation",
        init:         float = 1.0,
        compiled:     bool = False,
    ) -> None:
        super().__init__()
        if depth < 1:
            raise ValueError("EMLLayer requires depth >= 1")
        mode_ = mode.lower()
        if mode_ not in ("activation", "tree"):
            raise ValueError(f"mode must be 'activation' or 'tree', got {mode!r}")

        self.in_features  = in_features
        self.out_features = out_features
        self.depth        = depth
        self.operator     = operator.upper()
        self.mode         = mode_
        self.compiled     = compiled

        # ── Activation mode: Linear + EMLActivation (or accelerated variant) ─
        if self.mode == "activation":
            self.linear = nn.Linear(in_features, out_features)
            nn.init.uniform_(self.linear.weight, -0.05, 0.05)
            nn.init.ones_(self.linear.bias)

            if compiled and 1 <= depth <= 3 and self.operator in ("EML", "BEST"):
                # Priority: Rust > FusedEMLActivation > standard
                # get_best_activation picks the fastest available backend
                from ..fused_rust import get_best_activation
                self.activation = get_best_activation(depth=depth, operator=operator)
            else:
                if compiled and (depth > 3 or self.operator not in ("EML", "BEST")):
                    import warnings
                    warnings.warn(
                        f"EMLLayer compiled=True is only accelerated for depth<=3 and "
                        f"operator in ('EML','BEST'); got depth={depth}, "
                        f"operator={operator!r}. "
                        "Using standard EMLActivation. "
                        "For Rust acceleration: install monogate-core.",
                        stacklevel=2,
                    )
                self.activation = EMLActivation(depth=depth, operator=operator)

        # ── Tree mode: out_features independent EML trees ─────────────────
        else:
            if self.operator == "BEST":
                trees = [
                    _build_best_network_tree(in_features, depth, init)
                    for _ in range(out_features)
                ]
            else:
                op_fn = _get_op(self.operator)
                trees = [
                    _build_tree(depth,
                                lambda: _LinearLeaf(in_features),  # noqa: B023
                                op_fn)
                    for _ in range(out_features)
                ]
            # Register as a ModuleList so parameters are tracked
            self.trees = nn.ModuleList(trees)

    def forward(self, x: Tensor) -> Tensor:
        """
        Args:
            x: (batch_size, in_features) input tensor.
        Returns:
            (batch_size, out_features) output tensor.
        """
        if self.mode == "activation":
            h = self.linear(x)                  # (batch, out_features)
            # Apply EMLActivation element-wise across the out_features dim
            return self.activation(h)
        else:
            # Tree mode: evaluate each of the out_features trees
            outs = [tree(x) for tree in self.trees]   # list of (batch,)
            return torch.stack(outs, dim=-1)            # (batch, out_features)

    def formula(self, feature_names: list[str] | None = None) -> list[str] | str:
        """
        Human-readable EML formula.

        In tree mode: returns a list of out_features formula strings.
        In activation mode: returns the activation formula string.
        """
        if self.mode == "activation":
            return self.activation.formula()
        return [tree.formula(feature_names) for tree in self.trees]

    def extra_repr(self) -> str:
        n_nodes  = (1 << self.depth) - 1
        n_leaves = 1 << self.depth
        if self.compiled:
            from ..fused_rust import RUST_AVAILABLE
            if RUST_AVAILABLE:
                backend_tag = ", backend=rust"
            else:
                backend_tag = ", backend=fused"
        else:
            backend_tag = ""
        return (
            f"in={self.in_features}, out={self.out_features}, "
            f"depth={self.depth}, operator={self.operator!r}, "
            f"mode={self.mode!r}, nodes/tree={n_nodes}, leaves/tree={n_leaves}"
            f"{backend_tag}"
        )

    @property
    def n_eml_nodes(self) -> int:
        """Total EML internal node count across all trees in this layer."""
        nodes_per_tree = (1 << self.depth) - 1
        if self.mode == "activation":
            return nodes_per_tree
        return nodes_per_tree * self.out_features

    @property
    def n_parameters(self) -> int:
        """Total trainable parameter count."""
        return sum(p.numel() for p in self.parameters())

    def compile(self, **kwargs) -> "nn.Module":
        """
        Return a ``torch.compile``-wrapped version of this layer.

        On Linux/Mac with TorchInductor: fuses exp + softplus + log into a
        single kernel.  On Windows without MSVC: falls back to 'eager' mode
        automatically (still faster due to graph capture overhead reduction).

        Tip: pair with ``compiled=True`` for maximum speedup::

            layer = EMLLayer(256, 256, depth=2, compiled=True).compile()

        Returns:
            torch.compile-wrapped module.  Saves state_dict() for serialization
            (compiled modules cannot be pickled directly).
        """
        from ..compile.compiler import compile_eml_layer
        return compile_eml_layer(self, **kwargs)


# ── BEST network tree (for tree mode) ─────────────────────────────────────────

def _build_best_network_tree(
    in_features: int, depth: int, init: float
) -> nn.Module:
    """BEST routing for tree mode: EXL inner nodes, EML root."""
    if depth == 1:
        return _build_tree(1, lambda: _LinearLeaf(in_features), _eml_op)
    left  = _build_tree(depth - 1, lambda: _LinearLeaf(in_features), _exl_op)
    right = _build_tree(depth - 1, lambda: _LinearLeaf(in_features), _exl_op)
    return _Node(left, right, _eml_op)


# ── Convenience: node-count comparison ────────────────────────────────────────

def compare_to_native(
    layer: EMLLayer,
    native_name: str = "sin",
) -> None:
    """
    Print a node-count comparison between this EMLLayer and a native activation.

    Reference EML node counts for common activations:
        sin / cos  → 245 nodes (8-term Taylor, pure EML)
        sin / cos  →  63 nodes (8-term Taylor, BEST-routed)
        GELU       →  17 nodes (EML)  /  14 nodes (BEST)
    """
    native_nodes = {
        "sin":  245, "cos":  245,
        "sin_best": 63, "cos_best": 63,
        "gelu": 17,  "gelu_best": 14,
        "relu":  1,   "tanh": None,
    }
    this_nodes = layer.n_eml_nodes
    ref = native_nodes.get(native_name.lower())

    print(f"  EMLLayer nodes : {this_nodes}")
    if ref is not None:
        pct = (ref - this_nodes) / ref * 100
        direction = "saved" if pct > 0 else "added"
        print(f"  {native_name} nodes    : {ref}")
        print(f"  Difference     : {abs(pct):.1f}% {direction}")
    else:
        print(f"  (no reference count for {native_name!r})")
