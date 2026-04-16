"""
siren_with_monogate.py — SIREN-style coordinate network with EMLLayer activation.

Demonstrates replacing the periodic sin activation in a SIREN network with
EMLLayer(depth=2, compiled=True), showing:

1. Training on a synthetic 2D function (Gaussian sum)
2. Speed comparison: sin-SIREN vs EML-SIREN
3. Final PSNR comparison
4. Visual output (ASCII art heatmap when matplotlib unavailable)

Reference: Sitzmann et al. (2020), "Implicit Neural Representations with
Periodic Activation Functions", NeurIPS 2020.

Run:
    python notebooks/siren_with_monogate.py
    python notebooks/siren_with_monogate.py --plot      # save PNG if matplotlib available
    python notebooks/siren_with_monogate.py --steps 500 # quick smoke test
"""
from __future__ import annotations

import argparse
import math
import time

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

# ── Target function ───────────────────────────────────────────────────────────

def target_fn(xy: Tensor) -> Tensor:
    """
    2D Gaussian mixture: sum of 4 Gaussians at unit-circle positions.
    Maps (N, 2) → (N,).  Output range approximately [0, 1].
    """
    x, y = xy[:, 0:1], xy[:, 1:2]
    centers = [(0.5, 0.0), (-0.5, 0.0), (0.0, 0.5), (0.0, -0.5)]
    result = torch.zeros(xy.shape[0], 1, device=xy.device)
    for cx, cy in centers:
        dx = x - cx
        dy = y - cy
        result = result + torch.exp(-8.0 * (dx**2 + dy**2))
    return result.squeeze(1) / len(centers)


# ── SIREN with sin activation ─────────────────────────────────────────────────

class SirenLayer(nn.Module):
    """Single SIREN layer: Linear → sin(w0 * x)."""

    def __init__(self, in_f: int, out_f: int, w0: float = 30.0, first: bool = False) -> None:
        super().__init__()
        self.linear = nn.Linear(in_f, out_f)
        self.w0 = w0
        c = 1.0 / in_f if first else math.sqrt(6.0 / in_f) / w0
        nn.init.uniform_(self.linear.weight, -c, c)
        nn.init.zeros_(self.linear.bias)

    def forward(self, x: Tensor) -> Tensor:
        return torch.sin(self.w0 * self.linear(x))


class SirenNet(nn.Module):
    """Minimal SIREN: 2 → hidden → hidden → hidden → 1."""

    def __init__(self, hidden: int = 64, n_layers: int = 3, w0: float = 30.0) -> None:
        super().__init__()
        layers: list[nn.Module] = [SirenLayer(2, hidden, w0=w0, first=True)]
        for _ in range(n_layers - 1):
            layers.append(SirenLayer(hidden, hidden, w0=w0))
        self.net = nn.Sequential(*layers)
        self.out = nn.Linear(hidden, 1)
        nn.init.uniform_(self.out.weight, -math.sqrt(6 / hidden) / w0,
                          math.sqrt(6 / hidden) / w0)
        nn.init.zeros_(self.out.bias)

    def forward(self, x: Tensor) -> Tensor:
        return self.out(self.net(x)).squeeze(1)


# ── EML-SIREN ─────────────────────────────────────────────────────────────────

class EMLSirenLayer(nn.Module):
    """Single EML-SIREN layer: Linear → EMLActivation."""

    def __init__(
        self,
        in_f: int,
        out_f: int,
        depth: int = 2,
        operator: str = "BEST",
        compiled: bool = True,
    ) -> None:
        super().__init__()
        from monogate.torch import EMLLayer
        self.layer = EMLLayer(
            in_f, out_f,
            depth=depth,
            operator=operator,
            mode="activation",
            compiled=compiled,
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.layer(x)


class EMLSirenNet(nn.Module):
    """EML-SIREN: 2 → [EMLSirenLayer] × n_layers → 1."""

    def __init__(
        self,
        hidden: int = 64,
        n_layers: int = 3,
        depth: int = 2,
        operator: str = "BEST",
        compiled: bool = True,
    ) -> None:
        super().__init__()
        layers: list[nn.Module] = [EMLSirenLayer(2, hidden, depth, operator, compiled)]
        for _ in range(n_layers - 1):
            layers.append(EMLSirenLayer(hidden, hidden, depth, operator, compiled))
        self.net = nn.Sequential(*layers)
        self.out = nn.Linear(hidden, 1)

    def forward(self, x: Tensor) -> Tensor:
        return self.out(self.net(x)).squeeze(1)


# ── Training ──────────────────────────────────────────────────────────────────

def make_grid(res: int = 64, device: torch.device | None = None) -> tuple[Tensor, Tensor]:
    """Return (coords, values) over [-1,1]^2 at resolution res×res."""
    lin = torch.linspace(-1.0, 1.0, res)
    yy, xx = torch.meshgrid(lin, lin, indexing="ij")
    coords = torch.stack([xx.reshape(-1), yy.reshape(-1)], dim=1)  # (res^2, 2)
    if device:
        coords = coords.to(device)
    values = target_fn(coords)   # (res^2,)
    return coords, values


def train(
    model: nn.Module,
    steps: int = 1000,
    lr: float = 5e-4,
    res: int = 64,
    device: torch.device | None = None,
) -> tuple[float, float, list[float]]:
    """
    Train model with MSE loss.

    Returns (final_mse, elapsed_sec, loss_history).
    """
    device = device or torch.device("cpu")
    model = model.to(device)
    coords, values = make_grid(res, device)

    opt = torch.optim.Adam(model.parameters(), lr=lr)
    history: list[float] = []
    t0 = time.perf_counter()

    for step in range(steps):
        opt.zero_grad()
        pred = model(coords)
        loss = F.mse_loss(pred, values)
        loss.backward()
        opt.step()
        if step % max(1, steps // 20) == 0:
            history.append(loss.item())

    elapsed = time.perf_counter() - t0

    with torch.no_grad():
        pred = model(coords)
        final_mse = F.mse_loss(pred, values).item()

    return final_mse, elapsed, history


def psnr(mse: float) -> float:
    """PSNR in dB assuming signal range [0, 1]."""
    if mse <= 0:
        return float("inf")
    return -10.0 * math.log10(mse)


# ── ASCII heatmap ─────────────────────────────────────────────────────────────

def ascii_heatmap(values: Tensor, res: int, title: str = "", width: int = 32) -> None:
    """Print a tiny ASCII heatmap for terminal display."""
    step = max(1, res // width)
    grid = values.reshape(res, res)[::step, ::step].detach().cpu()
    vmin, vmax = grid.min().item(), grid.max().item()
    chars = " .:-=+*#@"
    print(f"  {title}  (min={vmin:.3f}, max={vmax:.3f})")
    for row in grid:
        line = ""
        for v in row:
            idx = int((v.item() - vmin) / max(vmax - vmin, 1e-6) * (len(chars) - 1))
            line += chars[max(0, min(len(chars) - 1, idx))]
        print("  " + line)


# ── Main ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SIREN vs EML-SIREN comparison")
    parser.add_argument("--steps", type=int, default=1000, help="Training steps")
    parser.add_argument("--hidden", type=int, default=64,  help="Hidden layer width")
    parser.add_argument("--res",    type=int, default=64,  help="Grid resolution")
    parser.add_argument("--depth",  type=int, default=2,   help="EMLLayer depth")
    parser.add_argument("--plot",   action="store_true",   help="Save PNG plots")
    parser.add_argument("--seed",   type=int, default=42,  help="Random seed")
    args = parser.parse_args(argv)

    torch.manual_seed(args.seed)
    device = torch.device("cpu")

    print("=" * 60)
    print("  SIREN vs EML-SIREN comparison")
    print(f"  steps={args.steps}, hidden={args.hidden}, res={args.res}")
    print("=" * 60)

    # Check Rust status
    try:
        from monogate.fused_rust import RUST_AVAILABLE, _RUST_VERSION
        backend = f"Rust ({_RUST_VERSION})" if RUST_AVAILABLE else "FusedEMLActivation"
    except ImportError:
        RUST_AVAILABLE = False
        backend = "standard"
    print(f"\n  EMLLayer backend: {backend}")

    # ── Train sin-SIREN
    print("\n[1/2] Training sin-SIREN ...")
    torch.manual_seed(args.seed)
    siren = SirenNet(hidden=args.hidden, n_layers=3)
    siren_mse, siren_time, siren_hist = train(
        siren, steps=args.steps, res=args.res, device=device
    )
    print(f"      MSE = {siren_mse:.4e}  |  PSNR = {psnr(siren_mse):.1f} dB"
          f"  |  Time = {siren_time:.2f}s")

    # ── Train EML-SIREN
    print("\n[2/2] Training EML-SIREN (compiled=True) ...")
    torch.manual_seed(args.seed)
    eml_siren = EMLSirenNet(
        hidden=args.hidden, n_layers=3,
        depth=args.depth, operator="BEST", compiled=True,
    )
    eml_mse, eml_time, eml_hist = train(
        eml_siren, steps=args.steps, res=args.res, device=device
    )
    print(f"      MSE = {eml_mse:.4e}  |  PSNR = {psnr(eml_mse):.1f} dB"
          f"  |  Time = {eml_time:.2f}s")

    # ── Summary
    speedup = siren_time / max(eml_time, 1e-6)
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  {'Metric':<20}  {'sin-SIREN':>12}  {'EML-SIREN':>12}")
    print(f"  {'-'*20}  {'-'*12}  {'-'*12}")
    print(f"  {'MSE':<20}  {siren_mse:>12.4e}  {eml_mse:>12.4e}")
    print(f"  {'PSNR (dB)':<20}  {psnr(siren_mse):>12.1f}  {psnr(eml_mse):>12.1f}")
    print(f"  {'Training time (s)':<20}  {siren_time:>12.2f}  {eml_time:>12.2f}")
    print(f"  {'Speedup':<20}  {'1.00x':>12}  {speedup:>11.2f}x")
    print(f"  {'Backend':<20}  {'torch.sin':>12}  {backend[:12]:>12}")
    print()
    print(f"  EML-SIREN is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'} than sin-SIREN")
    print(f"  PSNR difference: {psnr(eml_mse) - psnr(siren_mse):+.1f} dB "
          f"({'better' if eml_mse < siren_mse else 'worse'} quality)")

    # ── ASCII heatmaps
    coords, gt = make_grid(args.res, device)
    print("\n  Ground truth:")
    ascii_heatmap(gt, args.res, "target")

    with torch.no_grad():
        siren_pred = siren(coords)
        eml_pred   = eml_siren(coords)

    print("\n  sin-SIREN prediction:")
    ascii_heatmap(siren_pred, args.res, "sin-SIREN")

    print("\n  EML-SIREN prediction:")
    ascii_heatmap(eml_pred, args.res, "EML-SIREN")

    # ── Optional matplotlib plot
    if args.plot:
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            res = args.res
            fig, axes = plt.subplots(1, 3, figsize=(12, 4))
            for ax, vals, title, mse_val in [
                (axes[0], gt,        "Ground truth",  None),
                (axes[1], siren_pred, f"sin-SIREN\nPSNR={psnr(siren_mse):.1f}dB", siren_mse),
                (axes[2], eml_pred,   f"EML-SIREN ({backend})\nPSNR={psnr(eml_mse):.1f}dB", eml_mse),
            ]:
                img = vals.detach().cpu().numpy().reshape(res, res)
                ax.imshow(img, cmap="viridis", vmin=0, vmax=1)
                ax.set_title(title, fontsize=10)
                ax.axis("off")

            plt.suptitle(
                f"SIREN vs EML-SIREN  |  {args.steps} steps  |  "
                f"EML {speedup:.2f}x faster",
                fontsize=11,
            )
            plt.tight_layout()
            path = "notebooks/siren_comparison.png"
            plt.savefig(path, dpi=120, bbox_inches="tight")
            print(f"\n  Plot saved: {path}")
        except ImportError:
            print("\n  (matplotlib not installed — skipping plot)")

    # ── EMLLayer info
    print("\n  EMLLayer architecture:")
    first_layer = eml_siren.net[0].layer
    print(f"    {first_layer}")
    total_params = sum(p.numel() for p in eml_siren.parameters())
    siren_params = sum(p.numel() for p in siren.parameters())
    print(f"\n  Parameters: EML-SIREN={total_params:,}  sin-SIREN={siren_params:,}")


if __name__ == "__main__":
    main()
