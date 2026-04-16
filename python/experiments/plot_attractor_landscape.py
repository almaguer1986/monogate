"""
experiments/plot_attractor_landscape.py

Generate Figure: 2D MSE loss slice for a depth-3 EMLTree, with phantom
attractor and pi basin marked, and L1-penalised contours overlaid.

# Approximate 2D slice — exact attractor location depends on full 8D
# optimization dynamics. This visualization illustrates basin geometry.

Run from python/:
    python experiments/plot_attractor_landscape.py

Output: paper/figures/attractor_landscape.pdf  (+ .png for preview)
"""
from __future__ import annotations

import math
import sys
import warnings
from pathlib import Path

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    from matplotlib.colors import LogNorm
    from matplotlib.lines import Line2D
except ImportError:
    sys.exit(
        "matplotlib is required: pip install matplotlib"
    )


# ── EMLTree forward pass (pure NumPy, no torch dependency) ────────────────────

def _softplus(x: np.ndarray) -> np.ndarray:
    """Numerically stable softplus: ln(1 + exp(x))."""
    return np.where(x > 20, x, np.log1p(np.exp(np.clip(x, -500, 20))))


def eml(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """eml(a, b) = exp(a) - softplus(b)  [safe log approximation]."""
    return np.exp(np.clip(a, -30, 30)) - _softplus(b)


def depth3_eml_tree(w: np.ndarray) -> np.ndarray:
    """
    Evaluate a fixed-topology depth-3 complete binary EML tree.

    Leaf order (left-to-right, bottom-up): w[0..7]

    Internal nodes::

        n0 = eml(w0, w1)    n1 = eml(w2, w3)
        n2 = eml(w4, w5)    n3 = eml(w6, w7)
        n4 = eml(n0, n1)    n5 = eml(n2, n3)
        root = eml(n4, n5)

    ``w`` shape: ``(..., 8)`` — last dim is leaf index.
    Returns scalar array of shape ``(...)``.
    """
    w0, w1, w2, w3, w4, w5, w6, w7 = [w[..., i] for i in range(8)]
    n0 = eml(w0, w1)
    n1 = eml(w2, w3)
    n2 = eml(w4, w5)
    n3 = eml(w6, w7)
    n4 = eml(n0, n1)
    n5 = eml(n2, n3)
    return eml(n4, n5)


# ── Grid setup ────────────────────────────────────────────────────────────────

TARGET  = math.pi
GRID_N  = 400                                        # resolution per axis
DPI     = 150                                        # output DPI (increase for camera-ready)
W1_RANGE = np.linspace(-1.5, 4.0, GRID_N)           # varied leaf w0
W2_RANGE = np.linspace(-1.5, 4.0, GRID_N)           # varied leaf w1
W1_GRID, W2_GRID = np.meshgrid(W1_RANGE, W2_RANGE)  # (GRID_N, GRID_N)

# Fixed leaves: all other 6 leaves held at 1.0
base_leaves = np.ones(8)
FIXED = np.broadcast_to(base_leaves, (GRID_N, GRID_N, 8)).copy()
FIXED[..., 0] = W1_GRID
FIXED[..., 1] = W2_GRID

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    pred = depth3_eml_tree(FIXED)   # (GRID_N, GRID_N)

mse_raw = (pred - TARGET) ** 2
mse     = np.clip(mse_raw, 1e-12, None)    # avoid log(0)


# ── L1-penalised combined losses ──────────────────────────────────────────────

def penalised_loss(
    mse_grid: np.ndarray,
    w1: np.ndarray,
    w2: np.ndarray,
    lam: float,
) -> np.ndarray:
    """
    MSE + lambda * sum_i |w_i - 1|.

    The two varied leaves contribute |w1-1| + |w2-1|; the 6 fixed leaves
    at 1.0 contribute 0.
    """
    return mse_grid + lam * (np.abs(w1 - 1) + np.abs(w2 - 1))


loss_0   = penalised_loss(mse, W1_GRID, W2_GRID, lam=0.0)
loss_001 = penalised_loss(mse, W1_GRID, W2_GRID, lam=0.001)
loss_005 = penalised_loss(mse, W1_GRID, W2_GRID, lam=0.005)


# ── Locate attractor and pi basin in this 2D slice ───────────────────────────
# Note: these are 2D-slice minima. The true 8D attractor sits at
# approximately pred ≈ 3.1696; the exact coordinates depend on the full
# 8-dimensional gradient dynamics observed experimentally.

# Phantom attractor: global MSE minimum on the grid.
attractor_idx = np.unravel_index(np.argmin(mse), mse.shape)
a_w2  = float(W2_RANGE[attractor_idx[0]])
a_w1  = float(W1_RANGE[attractor_idx[1]])
a_val = float(pred[attractor_idx])

# Pi basin: point whose predicted value is closest to pi.
pi_dist = np.abs(pred - math.pi)
pi_idx  = np.unravel_index(np.argmin(pi_dist), pi_dist.shape)
p_w2 = float(W2_RANGE[pi_idx[0]])
p_w1 = float(W1_RANGE[pi_idx[1]])


# ── Plot ──────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(7, 5.6), dpi=DPI)

# Heatmap: log-scale MSE
im = ax.pcolormesh(
    W1_RANGE, W2_RANGE, mse,
    norm=LogNorm(vmin=1e-3, vmax=float(mse.max())),
    cmap="inferno",
    shading="auto",
    rasterized=True,
)
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cbar.set_label(r"MSE loss $(\hat{T}(x) - \pi)^2$", fontsize=10)
cbar.ax.yaxis.set_minor_locator(mticker.NullLocator())

# Contour lines for penalised losses
CONTOUR_LEVELS = 8
ax.contour(W1_RANGE, W2_RANGE, loss_0,
           levels=CONTOUR_LEVELS, colors="white",
           linewidths=0.7, linestyles="solid",  alpha=0.55)
ax.contour(W1_RANGE, W2_RANGE, loss_001,
           levels=CONTOUR_LEVELS, colors="cyan",
           linewidths=0.8, linestyles="dashed", alpha=0.65)
ax.contour(W1_RANGE, W2_RANGE, loss_005,
           levels=CONTOUR_LEVELS, colors="lime",
           linewidths=0.9, linestyles="dotted", alpha=0.75)

# Markers
ax.plot(a_w1, a_w2, marker="x", color="orange", ms=12, mew=2.5,
        zorder=5, label=rf"Phantom attractor ($\approx{a_val:.4f}$)")
ax.plot(p_w1, p_w2, marker="*", color="#00ff88", ms=14, mew=1.5,
        zorder=5, label=rf"$\pi$ basin ($\approx{math.pi:.4f}$)")

# Legend for contour lines
legend_lines = [
    Line2D([0], [0], color="white", lw=1.2, ls="solid",  label=r"$\lambda=0$ (MSE only)"),
    Line2D([0], [0], color="cyan",  lw=1.2, ls="dashed", label=r"$\lambda=0.001$"),
    Line2D([0], [0], color="lime",  lw=1.2, ls="dotted", label=r"$\lambda=0.005$"),
]
leg1 = ax.legend(handles=legend_lines, loc="upper left",
                 fontsize=8.5, framealpha=0.75, title="L1 penalty")
ax.add_artist(leg1)
ax.legend(loc="lower right", fontsize=8.5, framealpha=0.75)

ax.set_xlabel(r"Leaf $w_1$", fontsize=11)
ax.set_ylabel(r"Leaf $w_2$", fontsize=11)
ax.set_title(
    r"MSE loss surface — depth-3 EMLTree, 2D slice $(w_1, w_2)$"
    "\n"
    r"(remaining 6 leaves fixed at $1.0$, target $= \pi$)",
    fontsize=10,
)
ax.set_xlim(W1_RANGE[0], W1_RANGE[-1])
ax.set_ylim(W2_RANGE[0], W2_RANGE[-1])

plt.tight_layout()

# ── Save ──────────────────────────────────────────────────────────────────────

out_dir = Path(__file__).parent.parent / "paper" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)

saved: list[Path] = []
for ext in ("pdf", "png"):
    p = out_dir / f"attractor_landscape.{ext}"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    saved.append(p)

plt.close(fig)

print("attractor_landscape: figure generation complete.")
print(f"  Approximate 2D-slice attractor value : {a_val:.6f}  (full-8D experimental: ~3.1696)")
print(f"  Grid minimum at (w1={a_w1:.3f}, w2={a_w2:.3f})")
for p in saved:
    print(f"  Saved: {p}")
