# %% [markdown]
# # Minimax vs MSE MCTS — Chebyshev-Style EML Approximation
#
# Compares two search objectives for EML tree discovery:
#
# - **MSE** (default): minimise mean-squared error over probe points.
#   Equivalent to L2 approximation — small peaks allowed if average is low.
#
# - **Minimax**: minimise max absolute error over probe points.
#   Equivalent to L∞ / Chebyshev approximation — uniform error bound.
#
# Chebyshev approximation is preferable when you need a *guaranteed worst-case
# error bound* across the entire input range rather than a good average.
#
# Example targets: sin(x), exp(x), x².

# %%
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from monogate.search import mcts_search, beam_search

print("Minimax vs MSE MCTS — Chebyshev EML Approximation")
print("=" * 55)

# %% [markdown]
# ## 1. MCTS — MSE vs Minimax on sin(x)

# %%
print("\n1. MCTS objective comparison on sin(x)  (depth=4, n=2000)")
print("-" * 55)

probe = list(np.linspace(-math.pi, math.pi, 50))

r_mse = mcts_search(
    math.sin, probe_points=probe,
    depth=4, n_simulations=2000, seed=1, objective="mse",
)
r_mm  = mcts_search(
    math.sin, probe_points=probe,
    depth=4, n_simulations=2000, seed=1, objective="minimax",
)

probe_y = [math.sin(x) for x in probe]

def max_abs_err(formula_result, probe_x, probe_y):
    from monogate.search.mcts import _eval_tree, _is_complete
    node = formula_result.best_tree
    if not _is_complete(node):
        return float("inf")
    errs = []
    for xi, yi in zip(probe_x, probe_y):
        try:
            errs.append(abs(_eval_tree(node, xi) - yi))
        except Exception:
            return float("inf")
    return max(errs) if errs else float("inf")

mse_of_mse   = r_mse.best_mse
mse_of_mm    = r_mm.best_mse   # this stores the minimax score (max abs err)
maxerr_of_mse = max_abs_err(r_mse, probe, probe_y)

print(f"\n  MSE-objective   best_mse = {mse_of_mse:.4e}  max_abs_err = {maxerr_of_mse:.4e}")
print(f"  Minimax-obj     best_mse = N/A          max_abs_err = {mse_of_mm:.4e}")
print(f"\n  MSE formula:      {r_mse.best_formula}")
print(f"  Minimax formula:  {r_mm.best_formula}")

# %% [markdown]
# ## 2. Beam search — MSE vs Minimax on exp(x)

# %%
print("\n2. Beam search objective comparison on exp(x)  (depth=4, width=30)")
print("-" * 55)

probe_exp = list(np.linspace(-2, 2, 40))
probe_y_exp = [math.exp(x) for x in probe_exp]

b_mse = beam_search(
    math.exp, probe_points=probe_exp,
    depth=4, width=30, objective="mse",
)
b_mm  = beam_search(
    math.exp, probe_points=probe_exp,
    depth=4, width=30, objective="minimax",
)

maxerr_b_mse = max_abs_err(b_mse, probe_exp, probe_y_exp)
print(f"\n  MSE-objective   best_mse = {b_mse.best_mse:.4e}  max_abs_err = {maxerr_b_mse:.4e}")
print(f"  Minimax-obj     best_val = {b_mm.best_mse:.4e}  (minimax score)")
print(f"\n  MSE formula:      {b_mse.best_formula}")
print(f"  Minimax formula:  {b_mm.best_formula}")

# %% [markdown]
# ## 3. Convergence history comparison

# %%
print("\n3. Generating convergence history plots …")
fig, axes = plt.subplots(1, 2, figsize=(13, 4))

# sin MCTS history
ax = axes[0]
if r_mse.history:
    ax.semilogy([h[0] for h in r_mse.history],
                [h[1] for h in r_mse.history],
                "b-o", ms=3, label="MSE objective")
if r_mm.history:
    ax.semilogy([h[0] for h in r_mm.history],
                [h[1] for h in r_mm.history],
                "r-s", ms=3, label="Minimax objective")
ax.set_title("MCTS on sin(x) — objective convergence")
ax.set_xlabel("Simulation")
ax.set_ylabel("Best objective value")
ax.legend()
ax.grid(True, alpha=0.3)

# exp beam history
ax = axes[1]
if b_mse.history:
    ax.semilogy([h[0] for h in b_mse.history],
                [h[1] for h in b_mse.history],
                "b-o", ms=4, label="MSE objective")
if b_mm.history:
    ax.semilogy([h[0] for h in b_mm.history],
                [h[1] for h in b_mm.history],
                "r-s", ms=4, label="Minimax objective")
ax.set_title("Beam search on exp(x) — objective convergence")
ax.set_xlabel("Level")
ax.set_ylabel("Best objective value")
ax.legend()
ax.grid(True, alpha=0.3)

fig.tight_layout()
out_path = "minimax_vs_mse_convergence.png"
fig.savefig(out_path, dpi=120, bbox_inches="tight")
print(f"  Saved: {out_path}")
plt.close(fig)

# %% [markdown]
# ## 4. Error distribution comparison (sin MCTS)

# %%
print("\n4. Generating error distribution plots …")
from monogate.search.mcts import _eval_tree, _is_complete

x_dense = np.linspace(-math.pi, math.pi, 300)
y_dense = np.sin(x_dense)

def eval_on_grid(result, xs):
    node = result.best_tree
    if not _is_complete(node):
        return np.full(len(xs), float("nan"))
    ys = []
    for xv in xs:
        try:
            ys.append(_eval_tree(node, float(xv)))
        except Exception:
            ys.append(float("nan"))
    return np.array(ys)

y_pred_mse = eval_on_grid(r_mse, x_dense)
y_pred_mm  = eval_on_grid(r_mm,  x_dense)

fig, axes = plt.subplots(1, 2, figsize=(13, 4))

ax = axes[0]
ax.plot(x_dense, y_dense, "k-", lw=2, label="sin(x) exact")
ax.plot(x_dense, y_pred_mse, "b--", lw=1.5, label=f"MSE tree: {r_mse.best_formula[:30]}…")
ax.plot(x_dense, y_pred_mm,  "r-.", lw=1.5, label=f"Minimax tree: {r_mm.best_formula[:30]}…")
ax.set_title("Predictions — MSE vs Minimax")
ax.legend(fontsize=7)
ax.set_xlabel("x")
ax.grid(True, alpha=0.3)

ax = axes[1]
err_mse = np.abs(y_pred_mse - y_dense)
err_mm  = np.abs(y_pred_mm  - y_dense)
ax.plot(x_dense, err_mse, "b-",  lw=1.5, label=f"MSE   max={np.nanmax(err_mse):.3f}")
ax.plot(x_dense, err_mm,  "r--", lw=1.5, label=f"Minimax max={np.nanmax(err_mm):.3f}")
ax.set_title("Absolute error — MSE vs Minimax")
ax.legend(fontsize=8)
ax.set_xlabel("x")
ax.set_ylabel("|error|")
ax.grid(True, alpha=0.3)

fig.tight_layout()
out_path = "minimax_vs_mse_errors.png"
fig.savefig(out_path, dpi=120, bbox_inches="tight")
print(f"  Saved: {out_path}")
plt.close(fig)

print("\nDone.")
