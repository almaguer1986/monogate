"""
research_07b_basin_geometry.py — Phantom Attractor Basin Geometry
=================================================================
Visualizes the 2D geometry of the loss landscape and attractor basin
for the depth-3 EMLTree trained to approximate π.

Method:
  1. Train 40 models to convergence → identify which are in attractor basin.
  2. Fix 6 of 8 leaves at their attractor values.
  3. Sweep the remaining 2 leaves on a 100×100 grid.
  4. Plot 2D heatmap of loss, mark attractor and π.
  5. Measure gradient magnitude inside each basin.

Run from python/:
    python experiments/research_07b_basin_geometry.py

Requires: matplotlib (pip install matplotlib)
"""

import sys, math, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 70)
print("  research_07b: Phantom Attractor Basin Geometry")
print("=" * 70)

import torch
import torch.nn.functional as F
from monogate.network import EMLTree, fit, _Leaf, _Node

TARGET = torch.tensor(math.pi)
DEPTH  = 3

def _extract_leaves(module):
    """Recursively extract all _Leaf modules from a tree."""
    if isinstance(module, _Leaf):
        return [module]
    leaves = []
    for child in module.children():
        leaves.extend(_extract_leaves(child))
    return leaves


# ── A. Train 40 models and record attractor leaf values ──────────────────────

print("\n  A. Training 40 models to identify representative attractor leaves...")
N_RUNS = 40
attractor_leaves_all = []
pi_leaves_all = []

for seed in range(N_RUNS):
    torch.manual_seed(seed * 17 + 3)
    model = EMLTree(depth=DEPTH)
    fit(model, target=TARGET, steps=3000, lr=5e-3, lam=0.0)
    val = model().item()
    leaves = _extract_leaves(model.root)
    leaf_vals = [lf.val.item() for lf in leaves]

    if abs(val - 3.1696) < 0.01:
        attractor_leaves_all.append(leaf_vals)
    elif abs(val - math.pi) < 0.01:
        pi_leaves_all.append(leaf_vals)

print(f"  Attractor basin: {len(attractor_leaves_all)}/40 runs")
print(f"  Pi basin:        {len(pi_leaves_all)}/40 runs")


# ── B. 2D grid sweep ──────────────────────────────────────────────────────────

print("\n  B. 2D loss landscape sweep (fixing 6 leaves, sweeping 2)...")

def eml_eval(l0, l1, l2, l3, l4, l5, l6, l7):
    """Evaluate depth-3 EMLTree with given leaf values (using softplus on right branches)."""
    def sp(x):
        return math.log(1 + math.exp(x))
    def eml(a, b):
        bsp = sp(b)
        if bsp <= 0:
            return float('nan')
        return math.exp(a) - math.log(bsp)
    try:
        n1 = eml(l0, l1)
        n2 = eml(l2, l3)
        n3 = eml(l4, l5)
        n4 = eml(l6, l7)
        n5 = eml(n1, n2)
        n6 = eml(n3, n4)
        return eml(n5, n6)
    except (ValueError, OverflowError):
        return float('nan')

if attractor_leaves_all:
    fixed = attractor_leaves_all[0][:6]  # Fix first 6 leaves
    print(f"  Fixed leaves: {[f'{v:.4g}' for v in fixed]}")

    GRID_N = 60  # 60x60 grid for speed
    lo, hi = -3.0, 3.0
    xs = [lo + (hi - lo) * i / (GRID_N - 1) for i in range(GRID_N)]

    grid_loss = [[0.0]*GRID_N for _ in range(GRID_N)]
    for i, v6 in enumerate(xs):
        for j, v7 in enumerate(xs):
            pred = eml_eval(fixed[0], fixed[1], fixed[2], fixed[3],
                           fixed[4], fixed[5], v6, v7)
            if math.isfinite(pred):
                grid_loss[i][j] = (pred - math.pi) ** 2
            else:
                grid_loss[i][j] = float('nan')

    # Find attractor location in sweep (min loss point)
    min_loss = float('inf')
    min_i, min_j = 0, 0
    for i in range(GRID_N):
        for j in range(GRID_N):
            v = grid_loss[i][j]
            if math.isfinite(v) and v < min_loss:
                min_loss, min_i, min_j = v, i, j

    print(f"  Grid minimum: loss={min_loss:.6f} at "
          f"(leaf6={xs[min_i]:.3f}, leaf7={xs[min_j]:.3f})")

    # Try to plot
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive
        import matplotlib.pyplot as plt
        import numpy as np

        Z = np.array(grid_loss)
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(
            np.log10(Z + 1e-10).T,
            origin="lower",
            extent=[lo, hi, lo, hi],
            aspect="auto",
            cmap="viridis",
        )
        plt.colorbar(im, ax=ax, label="log₁₀(loss)")
        ax.set_xlabel("leaf[6]")
        ax.set_ylabel("leaf[7]")
        ax.set_title("Depth-3 EMLTree Loss Landscape\n(6 leaves fixed at attractor values)")

        # Mark attractor point
        ax.scatter([xs[min_i]], [xs[min_j]], c="red", s=100, zorder=5,
                   label=f"Attractor min (loss={min_loss:.4f})")
        ax.legend()

        out = "python/paper/figures/basin_geometry_2d.pdf"
        plt.tight_layout()
        plt.savefig(out, dpi=150)
        plt.close()
        print(f"  Saved plot: {out}")

    except ImportError:
        print("  matplotlib not available; skipping plot")
    except Exception as ex:
        print(f"  Plot error: {ex}")

else:
    print("  No attractor runs found — cannot compute basin geometry.")
    print("  Try running with more seeds or fewer steps.")


# ── C. Gradient magnitude inside each basin ───────────────────────────────────

print("\n  C. Gradient magnitude comparison")
print("-" * 50)

for basin_name, basin_runs in [("attractor", attractor_leaves_all), ("pi", pi_leaves_all)]:
    if not basin_runs:
        print(f"  {basin_name}: no runs available")
        continue

    leaf_vals = basin_runs[0]
    model = EMLTree(depth=DEPTH)
    leaf_mods = _extract_leaves(model.root)
    with torch.no_grad():
        for lf, v in zip(leaf_mods, leaf_vals):
            lf.val.data.fill_(v)

    pred = model()
    loss = (pred - TARGET) ** 2
    loss.backward()

    grad_norm = math.sqrt(sum(
        lf.val.grad.item() ** 2 for lf in leaf_mods
        if lf.val.grad is not None
    ))
    print(f"  {basin_name:10s}: pred={pred.item():.6f}  "
          f"loss={loss.item():.6f}  |grad|={grad_norm:.6e}")

print("\n  Basin geometry analysis complete.")
