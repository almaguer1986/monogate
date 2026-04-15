"""
monogate.network — EML expression trees as differentiable nn.Module objects.

Two model classes share the same recursive tree structure:

    EMLTree     — all leaves are scalar nn.Parameter objects.
                  Use for symbolic regression of constants (e, π, …).

    EMLNetwork  — all leaves are nn.Linear(in_features, 1) modules.
                  Use for function approximation from input features.
                  When training converges, formula(feature_names) prints an
                  interpretable EML expression with the learned linear leaves.

Helper:
    fit()       — training loop (Adam) that works for both model types.

Tree topology
─────────────
Both classes take a `depth` argument that builds a complete binary tree:

    depth=0  → single leaf  (scalar or linear)
    depth=1  → eml(leaf, leaf)                      1 node,  2 leaves
    depth=2  → eml(eml(l,l), eml(l,l))              3 nodes, 4 leaves
    depth=3  → depth-3 tree                          7 nodes, 8 leaves
    depth=d  → 2^d − 1 internal nodes, 2^d leaves

Stability note
──────────────
EML operations can hit domain errors early in training when leaf outputs are
negative (ln of a negative number).  _LinearLeaf is initialised with near-zero
weights and bias=1, so every leaf starts close to the constant 1 — a safe
starting point for both regimes of neg_eml and ln_eml.

Requires: torch
"""

from __future__ import annotations

from typing import Callable

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from .torch_ops import op, exl_op as _exl_op

__all__ = ["EMLTree", "EMLNetwork", "HybridNetwork", "fit"]


# ── Private tree node types ───────────────────────────────────────────────────

class _Leaf(nn.Module):
    """Scalar trainable leaf: a single nn.Parameter."""

    def __init__(self, init: float = 1.0) -> None:
        super().__init__()
        self.val = nn.Parameter(torch.tensor(float(init)))

    def forward(self, _x: Tensor | None = None) -> Tensor:  # noqa: ARG002
        return self.val

    def formula(self, names: list[str] | None = None) -> str:  # noqa: ARG002
        return f"{self.val.item():.5g}"


class _LinearLeaf(nn.Module):
    """
    Linear trainable leaf: nn.Linear(in_features, 1).

    Initialised with near-zero weights and bias=1 so that at the start of
    training every leaf outputs ≈ 1, keeping the EML tree in a numerically
    safe region (ln(1)=0, no domain errors).
    """

    def __init__(self, in_features: int) -> None:
        super().__init__()
        self.linear = nn.Linear(in_features, 1)
        nn.init.uniform_(self.linear.weight, -0.05, 0.05)
        nn.init.ones_(self.linear.bias)

    def forward(self, x: Tensor | None = None) -> Tensor:
        if x is None:
            raise ValueError("_LinearLeaf.forward requires input tensor x")
        return self.linear(x).squeeze(-1)

    def formula(self, names: list[str] | None = None) -> str:
        w = self.linear.weight.data.squeeze(0)   # (in_features,)
        b = self.linear.bias.data.item()
        labels = names if names else [f"x{i}" for i in range(w.shape[0])]
        parts = [f"{w[i].item():.4g}·{labels[i]}" for i in range(w.shape[0])
                 if abs(w[i].item()) > 1e-4]
        if abs(b) > 1e-4:
            parts.append(f"{b:.4g}")
        return "(" + ("+".join(parts) if parts else "0") + ")"


class _Node(nn.Module):
    """Internal tree node: op_func(left, softplus(right))."""

    def __init__(
        self,
        left: nn.Module,
        right: nn.Module,
        op_func: Callable[[Tensor, Tensor], Tensor] | None = None,
    ) -> None:
        super().__init__()
        self.left   = left
        self.right  = right
        self._op    = op_func if op_func is not None else op

    def forward(self, x: Tensor | None = None) -> Tensor:
        lv = self.left(x)
        rv = F.softplus(self.right(x))  # enforce ln domain: rv > 0 throughout training
        return self._op(lv, rv)

    def formula(self, names: list[str] | None = None) -> str:
        return f"eml({self.left.formula(names)}, {self.right.formula(names)})"


def _build_tree(
    depth: int,
    leaf_factory: Callable[[], nn.Module],
    op_func: Callable[[Tensor, Tensor], Tensor] | None = None,
) -> nn.Module:
    """Recursively build a complete binary tree of the given depth."""
    if depth == 0:
        return leaf_factory()
    return _Node(
        _build_tree(depth - 1, leaf_factory, op_func),
        _build_tree(depth - 1, leaf_factory, op_func),
        op_func,
    )


# ── Public model classes ──────────────────────────────────────────────────────

class EMLTree(nn.Module):
    """
    EML expression tree with scalar trainable leaves.

    Optimise toward a constant target (symbolic regression).

        model = EMLTree(depth=2)   # 3 internal nodes, 4 leaves
        fit(model, target=torch.tensor(math.pi))
        print(model.formula())     # eml(eml(1.2, 0.8), eml(…, …))
        print(model().item())      # ≈ 3.14159

    Args:
        depth: depth of the complete binary tree.
               depth=1 → 1 node / 2 leaves.
               depth=d → 2^d − 1 nodes / 2^d leaves.
        init:  initial value for every leaf parameter (default 1.0).
    """

    def __init__(
        self,
        depth: int = 3,
        init: float = 1.0,
        op_func: Callable[[Tensor, Tensor], Tensor] | None = None,
    ) -> None:
        super().__init__()
        self.root = _build_tree(depth, lambda: _Leaf(init), op_func)

    def forward(self) -> Tensor:
        return self.root(None)

    def formula(self) -> str:
        """Human-readable EML expression with current leaf values."""
        return self.root.formula(None)


class EMLNetwork(nn.Module):
    """
    EML expression tree with linear trainable leaves.

    Use for differentiable function approximation from input features.
    Each leaf applies a learned linear projection of the input vector.

        model = EMLNetwork(in_features=1, depth=2)
        fit(model, x=X_train, y=y_train)
        print(model.formula(["x"]))   # eml(eml((1.0·x+0.0), …), …)
        pred = model(X_test)          # (batch,) predictions

    Args:
        in_features: number of input features.
        depth:       depth of the complete binary tree.
                     depth=2 → 3 internal nodes, depth=3 → 7 internal nodes.
    """

    def __init__(
        self,
        in_features: int,
        depth: int = 3,
        op_func: Callable[[Tensor, Tensor], Tensor] | None = None,
    ) -> None:
        super().__init__()
        self.in_features = in_features
        self.root = _build_tree(depth, lambda: _LinearLeaf(in_features), op_func)

    def forward(self, x: Tensor) -> Tensor:
        """
        Args:
            x: (batch_size, in_features) input tensor.
        Returns:
            (batch_size,) output tensor.
        """
        return self.root(x)

    def formula(self, feature_names: list[str] | None = None) -> str:
        """
        Human-readable EML expression with current linear weights.

        Args:
            feature_names: optional list of names for input features.
                           E.g. ["x"] for a 1-D input, ["x", "y"] for 2-D.
                           Defaults to ["x0", "x1", …].
        """
        return self.root.formula(feature_names)


# ── Hybrid model ─────────────────────────────────────────────────────────────

class HybridNetwork(nn.Module):
    """
    EXL inner sub-trees with an EML root — exploiting each operator's strength.

    Problem: EXL is numerically stable in deep trees (98% finite vs EML's 2%)
    and produces the best sin(x) approximation, but it cannot represent
    addition/subtraction (it is incomplete).  EML can represent everything but
    explodes in depth (iterated exp(exp(...)) overflow).

    Solution: use EXL for all inner nodes to get stable sub-expressions, then
    connect them at the root with EML (or another outer operator) to recover
    the additive step.  The root sees two bounded EXL outputs and combines
    them via EML's subtraction-in-log-space.

    Architecture (depth d):
        root           EML node (or outer_op)
        ├── left       complete (d-1)-depth EXL tree
        └── right      complete (d-1)-depth EXL tree

    Args:
        in_features: number of input features.
        depth:       total tree depth (>= 1).  depth=1 => one root node and
                     two leaves; depth=d => 2^d-1 total nodes.
        inner_op:    op_func for all non-root nodes.  Default: exl_op.
        outer_op:    op_func for the root node.  Default: None (EML).
    """

    def __init__(
        self,
        in_features: int,
        depth: int = 3,
        inner_op: Callable[[Tensor, Tensor], Tensor] | None = None,
        outer_op: Callable[[Tensor, Tensor], Tensor] | None = None,
    ) -> None:
        super().__init__()
        if depth < 1:
            raise ValueError("HybridNetwork requires depth >= 1")
        _inner = inner_op if inner_op is not None else _exl_op
        # Build two inner sub-trees
        left  = _build_tree(depth - 1, lambda: _LinearLeaf(in_features), _inner)
        right = _build_tree(depth - 1, lambda: _LinearLeaf(in_features), _inner)
        # Root node uses the outer operator (default EML)
        self.root = _Node(left, right, outer_op)

    def forward(self, x: Tensor) -> Tensor:
        return self.root(x)

    def formula(self, feature_names: list[str] | None = None) -> str:
        return self.root.formula(feature_names)


# ── fit() training helper ─────────────────────────────────────────────────────

def fit(
    model: EMLTree | EMLNetwork,
    *,
    target: Tensor | float | None = None,
    x: Tensor | None = None,
    y: Tensor | None = None,
    steps: int = 2000,
    lr: float = 1e-2,
    log_every: int = 200,
    loss_threshold: float = 1e-8,
    max_grad_norm: float = 1.0,
    lam: float = 0.0,
) -> list[float]:
    """
    Train an EMLTree or EMLNetwork with Adam.

    For EMLTree  — supply ``target`` (scalar):
        Minimises (model() − target)² + lam · Σ|leaf − 1|.

    For EMLNetwork — supply ``x`` and ``y``:
        Minimises MSE(model(x), y) + lam · Σ|weight|.

    Args:
        model:           EMLTree or EMLNetwork instance.
        target:          Scalar target for EMLTree training.
        x:               Input tensor (batch, in_features) for EMLNetwork.
        y:               Target tensor (batch,) for EMLNetwork.
        steps:           Number of Adam optimisation steps.
        lr:              Adam learning rate.
        log_every:       Print loss every this many steps (0 = silent).
        loss_threshold:  Stop early if *raw* loss drops below this value.
        max_grad_norm:   Gradient clipping threshold (default 1.0).
        lam:             Complexity penalty weight (default 0 = no penalty).
                         EMLTree: penalises Σ|leaf − 1| (pull leaves toward 1).
                         EMLNetwork: penalises Σ|weight| (L1 on linear weights,
                         pushing leaves toward constant functions).

    Returns:
        List of *raw* loss values (without penalty) recorded at each valid step.
    """
    if isinstance(model, EMLTree):
        if target is None:
            raise ValueError("EMLTree training requires `target`")
        target_t = (
            target if isinstance(target, Tensor)
            else torch.tensor(float(target))
        )
        return _fit_constant(model, target_t, steps, lr, log_every,
                             loss_threshold, max_grad_norm, lam)

    if isinstance(model, EMLNetwork):
        if x is None or y is None:
            raise ValueError("EMLNetwork training requires `x` and `y`")
        return _fit_function(model, x, y, steps, lr, log_every,
                             loss_threshold, max_grad_norm, lam)

    raise TypeError(f"fit: unsupported model type {type(model)!r}")


def _fit_constant(
    model: EMLTree,
    target: Tensor,
    steps: int,
    lr: float,
    log_every: int,
    threshold: float,
    max_grad_norm: float,
    lam: float = 0.0,
) -> list[float]:
    opt    = torch.optim.Adam(model.parameters(), lr=lr)
    losses: list[float] = []

    for step in range(1, steps + 1):
        opt.zero_grad()
        try:
            pred     = model()
            raw_loss = (pred - target) ** 2
        except (ValueError, RuntimeError):
            if log_every and step % log_every == 0:
                print(f"step {step:>6} | domain error")
            continue

        if not torch.isfinite(raw_loss):
            if log_every and step % log_every == 0:
                print(f"step {step:>6} | non-finite loss")
            continue

        loss = raw_loss
        if lam > 0:
            penalty = sum((p - 1.0).abs().sum() for p in model.parameters())
            loss    = raw_loss + lam * penalty

        loss.backward()
        if max_grad_norm > 0:
            nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
        opt.step()

        raw_val = raw_loss.item()
        losses.append(raw_val)

        if log_every and step % log_every == 0:
            print(f"step {step:>6} | loss = {raw_val:.4e} | value = {pred.item():.8f}")

        if raw_val < threshold:
            if log_every:
                print(f"Converged at step {step} — loss = {raw_val:.4e}")
            break

    return losses


def _fit_function(
    model: EMLNetwork,
    x: Tensor,
    y: Tensor,
    steps: int,
    lr: float,
    log_every: int,
    threshold: float,
    max_grad_norm: float,
    lam: float = 0.0,
) -> list[float]:
    opt    = torch.optim.Adam(model.parameters(), lr=lr)
    losses: list[float] = []

    for step in range(1, steps + 1):
        opt.zero_grad()
        try:
            pred     = model(x)
            raw_loss = F.mse_loss(pred, y)
        except (ValueError, RuntimeError):
            if log_every and step % log_every == 0:
                print(f"step {step:>6} | domain error")
            continue

        if not torch.isfinite(raw_loss):
            if log_every and step % log_every == 0:
                print(f"step {step:>6} | non-finite loss")
            continue

        loss = raw_loss
        if lam > 0:
            penalty = sum(
                p.abs().sum()
                for name, p in model.named_parameters()
                if "weight" in name
            )
            loss = raw_loss + lam * penalty

        loss.backward()
        if max_grad_norm > 0:
            nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
        opt.step()

        raw_val = raw_loss.item()
        losses.append(raw_val)

        if log_every and step % log_every == 0:
            print(f"step {step:>6} | mse = {raw_val:.4e}")

        if raw_val < threshold:
            if log_every:
                print(f"Converged at step {step} — mse = {raw_val:.4e}")
            break

    return losses
