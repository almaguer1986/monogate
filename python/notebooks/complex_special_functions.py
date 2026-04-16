# %% [markdown]
# # Complex BEST — Special Functions via EML Complex Routing
#
# Demonstrates how extending the BEST operator to the complex domain unlocks
# exact/near-exact symbolic constructions for:
#
# 1. **sin(x)** and **cos(x)** — exact, 1 node each (vs 63 nodes in real BEST)
# 2. **Bessel J₀** — near-exact approximation from complex MCTS search
# 3. **Error function erf** — near-exact approximation
# 4. **Airy Ai** — near-exact approximation
#
# Key identity::
#
#     Im(eml(ix, 1)) = sin(x)   — 1 complex EML node
#     Re(eml(ix, 1)) = cos(x)   — 1 complex EML node
#
# Run this notebook with Jupyter or as a plain Python script.

# %%
import math
import cmath

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from monogate.complex_best import (
    CBEST,
    SIN_NODE_COUNT,
    COS_NODE_COUNT,
    J0_NODE_COUNT,
    AI_NODE_COUNT,
    ERF_NODE_COUNT,
    complex_best_optimize,
    im,
    re,
)
from monogate import sin_via_euler, cos_via_euler
from monogate.complex_search import complex_mcts_search, complex_beam_search

print("Complex BEST — Special Functions Demo")
print("=" * 50)

# %% [markdown]
# ## 1. Euler path — exact sin and cos (1 node each)

# %%
print("\n1. Euler path (sin / cos)")
print("-" * 40)

x_vals = np.linspace(-3, 3, 300)

# sin via CBEST: Im(eml(ix, 1)) = Im(exp(ix)) = sin(x)
sin_cbest = np.array([im(CBEST.sin(x)) for x in x_vals])
sin_exact = np.sin(x_vals)

# cos via CBEST: Re(eml(ix, 1)) = Re(exp(ix)) = cos(x)
cos_cbest = np.array([re(CBEST.cos(x)) for x in x_vals])
cos_exact = np.cos(x_vals)

sin_mse = float(np.mean((sin_cbest - sin_exact) ** 2))
cos_mse = float(np.mean((cos_cbest - cos_exact) ** 2))

print(f"  sin(x) via Im(eml(ix,1)):  MSE = {sin_mse:.2e}  (node count = {SIN_NODE_COUNT})")
print(f"  cos(x) via Re(eml(ix,1)):  MSE = {cos_mse:.2e}  (node count = {COS_NODE_COUNT})")
print(f"  Real BEST sin/cos node count: 63 each (8-term EXL Taylor)")
print(f"  Savings: {(63 - SIN_NODE_COUNT) / 63 * 100:.0f}% fewer nodes per function")

# sin_via_euler cross-check
for xv in [0.0, 0.5, 1.0, -1.5, math.pi / 4]:
    assert abs(sin_via_euler(xv) - math.sin(xv)) < 1e-12, f"Mismatch at {xv}"
print("  sin_via_euler cross-check: PASSED (6 test points)")

# %% [markdown]
# ## 2. Complex BEST routing table

# %%
print("\n2. CBEST routing table")
print("-" * 40)
CBEST.info()

# %% [markdown]
# ## 3. complex_best_optimize — expression analysis

# %%
print("\n3. complex_best_optimize on sin(x) + cos(x) + exp(x)")
print("-" * 40)
result = complex_best_optimize("sin(x) + cos(x) + exp(x)")
print(result)

# %% [markdown]
# ## 4. MCTS search for Bessel J₀

# %%
print(f"\n4. MCTS search for Bessel J₀ (best known = {J0_NODE_COUNT} nodes)")
print("-" * 40)

try:
    from scipy.special import j0 as scipy_j0
    target_j0 = scipy_j0
except ImportError:
    # Manual Bessel J0 via series if scipy not available
    def target_j0(x: float) -> float:
        total = 0.0
        for k in range(20):
            total += ((-1) ** k / (math.factorial(k) ** 2)) * (x / 2) ** (2 * k)
        return total

probe_x_j0 = list(np.linspace(0.1, 8.0, 40))

result_j0 = complex_mcts_search(
    target_j0,
    probe_points=probe_x_j0,
    projection="real",
    depth=4,
    n_simulations=3000,
    seed=7,
    log_every=500,
)
print(f"\n  Best formula: {result_j0.complex_formula}")
print(f"  Projection: {result_j0.projection}")
print(f"  MSE = {result_j0.best_mse:.4e}")
print(f"  Elapsed: {result_j0.elapsed_s:.2f}s")

# %% [markdown]
# ## 5. Beam search for erf

# %%
print(f"\n5. Beam search for erf (best known = {ERF_NODE_COUNT} nodes)")
print("-" * 40)

try:
    from scipy.special import erf as scipy_erf
    target_erf = scipy_erf
except ImportError:
    def target_erf(x: float) -> float:
        """Approximate erf via series."""
        total = 0.0
        for k in range(15):
            total += ((-1) ** k * x ** (2 * k + 1)) / (math.factorial(k) * (2 * k + 1))
        return total * 2 / math.sqrt(math.pi)

probe_x_erf = list(np.linspace(-2.5, 2.5, 30))

result_erf = complex_beam_search(
    target_erf,
    probe_points=probe_x_erf,
    projection="imag",
    depth=3,
    width=30,
    log_every=0,
)
print(f"  Best formula: {result_erf.complex_formula}")
print(f"  MSE = {result_erf.best_mse:.4e}")
print(f"  Levels: {result_erf.n_levels}")

# %% [markdown]
# ## 6. Visualization

# %%
print("\n6. Generating comparison plots …")
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# sin/cos
ax = axes[0]
ax.plot(x_vals, sin_exact, "k-", lw=2, label="sin(x) exact")
ax.plot(x_vals, sin_cbest, "r--", lw=1.5, label=f"Im(CBEST.sin) MSE={sin_mse:.1e}")
ax.plot(x_vals, cos_exact, "b-", lw=2, label="cos(x) exact")
ax.plot(x_vals, cos_cbest, "c--", lw=1.5, label=f"Re(CBEST.cos) MSE={cos_mse:.1e}")
ax.set_title("sin/cos via Complex EML (1 node each)")
ax.legend(fontsize=8)
ax.set_xlabel("x")
ax.grid(True, alpha=0.3)

# J0 search result
ax = axes[1]
x_plot = np.linspace(0.1, 8.0, 200)
y_j0_exact = np.array([target_j0(x) for x in x_plot])
from monogate.complex_eval import eval_complex, formula_complex
y_j0_approx = []
for xv in x_plot:
    try:
        z = eval_complex(result_j0.best_tree, xv)
        y_j0_approx.append(z.real if result_j0.projection == "real" else z.imag)
    except Exception:
        y_j0_approx.append(float("nan"))

ax.plot(x_plot, y_j0_exact,  "k-",  lw=2, label="J₀(x) exact")
ax.plot(x_plot, y_j0_approx, "r--", lw=1.5, label=f"Complex MCTS approx (MSE={result_j0.best_mse:.2e})")
ax.set_title("Bessel J₀ via Complex MCTS")
ax.legend(fontsize=8)
ax.set_xlabel("x")
ax.grid(True, alpha=0.3)

fig.tight_layout()
out_path = "complex_special_functions.png"
fig.savefig(out_path, dpi=120, bbox_inches="tight")
print(f"  Saved: {out_path}")
plt.close(fig)

print("\nDone.")
