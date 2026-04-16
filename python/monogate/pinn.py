"""
monogate.pinn — Physics-Informed EML Networks (PINN).

Wraps an EMLNetwork backbone with a physics residual loss so that the
learned symbolic expression satisfies a differential equation, not just
the observed data.  The interpretable EML formula doubles as both the
fitted model and a symbolic candidate for the exact solution.

Supported equations
-------------------
harmonic  u''(x) + ω²·u(x) = 0        (simple harmonic oscillator ODE)
burgers   u·u'(x) − ν·u''(x) = 0      (steady-state 1-D Burgers equation)
heat      u''(x) = 0                   (steady 1-D heat / Laplace equation)

Public API
----------
EMLPINN(equation, backbone_depth, omega, nu, alpha, lam_physics)
    nn.Module whose forward pass evaluates the backbone EMLNetwork and
    whose ``residual(x_phys)`` method returns the PDE/ODE residual tensor.

fit_pinn(model, x_data, y_data, x_phys, **kwargs) -> PINNResult
    Training loop (Adam) that minimises data_loss + lam_physics * physics_loss.

PINNResult
    Dataclass with data_loss, physics_loss, history, formula, elapsed_s.

Examples
--------
Harmonic oscillator — train on 50 noisy samples, enforce ODE::

    import math, torch
    from monogate.pinn import EMLPINN, fit_pinn

    omega = 2.0
    model = EMLPINN(equation='harmonic', omega=omega, backbone_depth=2)

    x_data = torch.linspace(0, 2 * math.pi, 50).unsqueeze(1)
    y_data = torch.sin(omega * x_data.squeeze(1))
    x_phys = torch.linspace(0, 2 * math.pi, 100).unsqueeze(1)

    result = fit_pinn(model, x_data, y_data, x_phys, steps=1000, log_every=200)
    print(result.formula)
    print(f"data={result.data_loss:.4f}  phys={result.physics_loss:.4f}")

Requires: torch
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from .network import EMLNetwork

__all__ = ["EMLPINN", "PINNResult", "fit_pinn"]

_SUPPORTED_EQUATIONS = ("harmonic", "burgers", "heat")


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class PINNResult:
    """Result returned by fit_pinn()."""

    data_loss:    float
    physics_loss: float
    formula:      str
    elapsed_s:    float
    history:      list[tuple[int, float, float]] = field(default_factory=list)
    # history entries: (step, data_loss_at_step, physics_loss_at_step)

    def __repr__(self) -> str:
        return (
            f"PINNResult(data_loss={self.data_loss:.4e}, "
            f"physics_loss={self.physics_loss:.4e}, "
            f"elapsed={self.elapsed_s:.2f}s)"
        )


# ── EMLPINN model ─────────────────────────────────────────────────────────────

class EMLPINN(nn.Module):
    """
    Physics-Informed EML Network.

    Wraps an EMLNetwork backbone so that its predictions satisfy a given
    ODE/PDE constraint.  The physics loss is a mean-squared residual term
    added on top of the usual data MSE loss during ``fit_pinn()``.

    Args:
        equation:       Differential equation to enforce.  One of:
                        ``'harmonic'``  — u''(x) + ω²·u(x) = 0
                        ``'burgers'``   — u·u'(x) − ν·u''(x) = 0
                        ``'heat'``      — u''(x) = 0
        backbone_depth: Depth of the EMLNetwork binary tree (default 3).
                        depth=d → 2^d−1 internal nodes, 2^d linear leaves.
        omega:          Angular frequency for ``'harmonic'`` (default 1.0).
        nu:             Viscosity coefficient for ``'burgers'`` (default 0.01).
        lam_physics:    Weight on the physics residual loss (default 1.0).
                        Higher values enforce the equation more strictly but
                        may hurt data fit if the data is inconsistent.
        in_features:    Input dimension (default 1 for 1-D problems).

    Note:
        All equations are formulated for 1-D input (the spatial/temporal
        coordinate ``x``).  Input tensors must have shape ``(batch, 1)``.
    """

    def __init__(
        self,
        equation:       str   = "harmonic",
        backbone_depth: int   = 3,
        omega:          float = 1.0,
        nu:             float = 0.01,
        lam_physics:    float = 1.0,
        in_features:    int   = 1,
    ) -> None:
        super().__init__()
        if equation not in _SUPPORTED_EQUATIONS:
            raise ValueError(
                f"equation must be one of {_SUPPORTED_EQUATIONS!r}, got {equation!r}"
            )
        self.equation    = equation
        self.omega       = omega
        self.nu          = nu
        self.lam_physics = lam_physics
        self.backbone    = EMLNetwork(in_features=in_features, depth=backbone_depth)

    def forward(self, x: Tensor) -> Tensor:
        """
        Evaluate the backbone EMLNetwork.

        Args:
            x: (batch, in_features) input tensor.

        Returns:
            (batch,) predictions.
        """
        return self.backbone(x)

    def residual(self, x_phys: Tensor) -> Tensor:
        """
        Compute the PDE/ODE residual at collocation points.

        Derivatives are computed via ``torch.autograd.grad`` with
        ``create_graph=True`` so they remain part of the computation graph
        for backprop through the physics loss.

        Args:
            x_phys: (batch, 1) collocation points, will be detached and
                    given requires_grad=True internally.

        Returns:
            (batch,) residual tensor (should be driven toward zero).
        """
        x = x_phys.detach().requires_grad_(True)   # (batch, 1)
        u = self.backbone(x)                         # (batch,)

        ones_u = torch.ones_like(u)
        u_x_full, = torch.autograd.grad(
            u, x,
            grad_outputs=ones_u,
            create_graph=True,
            retain_graph=True,
        )
        u_x = u_x_full[:, 0]                        # (batch,)

        ones_ux = torch.ones_like(u_x)
        u_xx_full, = torch.autograd.grad(
            u_x, x,
            grad_outputs=ones_ux,
            create_graph=True,
            retain_graph=True,
        )
        u_xx = u_xx_full[:, 0]                      # (batch,)

        if self.equation == "harmonic":
            return u_xx + self.omega ** 2 * u

        if self.equation == "burgers":
            return u * u_x - self.nu * u_xx

        # heat: steady-state u'' = 0
        return u_xx

    def formula(self, feature_names: list[str] | None = None) -> str:
        """Human-readable EML expression for the backbone."""
        return self.backbone.formula(feature_names)


# ── fit_pinn() ────────────────────────────────────────────────────────────────

def fit_pinn(
    model:            EMLPINN,
    x_data:           Tensor,
    y_data:           Tensor,
    x_phys:           Tensor,
    *,
    steps:            int   = 2000,
    lr:               float = 1e-2,
    log_every:        int   = 200,
    loss_threshold:   float = 1e-6,
    max_grad_norm:    float = 1.0,
    lam:              float = 0.0,
    lam_physics:      float | None = None,
) -> PINNResult:
    """
    Train an EMLPINN with a combined data + physics loss.

    Total loss::

        L = MSE(model(x_data), y_data)
            + λ_physics · mean(residual(x_phys)²)
            + lam · Σ|weight|

    The physics residual drives the EML expression toward satisfying the
    chosen ODE/PDE at all collocation points ``x_phys``, even between the
    data points.  This typically yields smoother, more generalizable
    symbolic expressions than pure data fitting.

    Args:
        model:          EMLPINN instance.
        x_data:         (N, 1) observed input tensor.
        y_data:         (N,) observed target tensor.
        x_phys:         (M, 1) collocation points for physics residual.
                        Can overlap with or be denser than x_data.
        steps:          Number of Adam optimisation steps.
        lr:             Adam learning rate.
        log_every:      Print progress every N steps (0 = silent).
        loss_threshold: Stop early if total loss drops below this value.
        max_grad_norm:  Gradient clipping threshold.
        lam:            L1 weight regularisation on backbone linear weights.
        lam_physics:    Physics loss weight.  Overrides ``model.lam_physics``
                        if provided, otherwise uses ``model.lam_physics``.

    Returns:
        PINNResult with final data_loss, physics_loss, history, formula,
        and elapsed_s.

    Examples
    --------
    Steady Burgers, 40 data points, 200 collocation points::

        import torch
        from monogate.pinn import EMLPINN, fit_pinn

        model = EMLPINN(equation='burgers', nu=0.05, backbone_depth=2)
        x_d = torch.linspace(-1, 1, 40).unsqueeze(1)
        y_d = torch.tanh(x_d.squeeze(1) / (2 * 0.05))
        x_p = torch.linspace(-1, 1, 200).unsqueeze(1)
        result = fit_pinn(model, x_d, y_d, x_p, steps=500, log_every=0)
        print(result.formula)
    """
    if not isinstance(model, EMLPINN):
        raise TypeError(f"fit_pinn: model must be EMLPINN, got {type(model)!r}")

    lam_w = lam_physics if lam_physics is not None else model.lam_physics

    opt    = torch.optim.Adam(model.parameters(), lr=lr)
    t0     = time.perf_counter()
    history: list[tuple[int, float, float]] = []

    final_data_loss:  float = float("inf")
    final_phys_loss:  float = float("inf")

    for step in range(1, steps + 1):
        opt.zero_grad()

        # ── Data loss ─────────────────────────────────────────────────────
        try:
            pred     = model(x_data)
            data_loss_t = F.mse_loss(pred, y_data)
        except (ValueError, RuntimeError):
            if log_every and step % log_every == 0:
                print(f"step {step:>6} | data domain error")
            continue

        if not torch.isfinite(data_loss_t):
            if log_every and step % log_every == 0:
                print(f"step {step:>6} | non-finite data loss")
            continue

        # ── Physics loss ──────────────────────────────────────────────────
        try:
            res       = model.residual(x_phys)
            phys_loss_t = (res ** 2).mean()
        except (ValueError, RuntimeError):
            if log_every and step % log_every == 0:
                print(f"step {step:>6} | physics domain error")
            phys_loss_t = torch.zeros(1)

        if not torch.isfinite(phys_loss_t):
            phys_loss_t = torch.zeros(1)

        # ── Combined loss ─────────────────────────────────────────────────
        total_loss = data_loss_t + lam_w * phys_loss_t

        if lam > 0:
            l1_penalty = sum(
                p.abs().sum()
                for name, p in model.named_parameters()
                if "weight" in name
            )
            total_loss = total_loss + lam * l1_penalty

        total_loss.backward()
        if max_grad_norm > 0:
            nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
        opt.step()

        d_val = data_loss_t.item()
        p_val = phys_loss_t.item()
        final_data_loss = d_val
        final_phys_loss = p_val

        if log_every and step % log_every == 0:
            print(
                f"step {step:>6} | data={d_val:.4e}  phys={p_val:.4e}"
                f"  total={total_loss.item():.4e}"
            )
            history.append((step, d_val, p_val))
        elif step % max(1, steps // 20) == 0:
            history.append((step, d_val, p_val))

        if total_loss.item() < loss_threshold:
            if log_every:
                print(f"Converged at step {step} — total={total_loss.item():.4e}")
            break

    return PINNResult(
        data_loss    = final_data_loss,
        physics_loss = final_phys_loss,
        formula      = model.formula(["x"]),
        elapsed_s    = time.perf_counter() - t0,
        history      = history,
    )
