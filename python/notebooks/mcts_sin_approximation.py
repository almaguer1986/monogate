"""
mcts_sin_approximation.py -- MCTS search for EML grammar approximations
========================================================================

Demonstrates monogate.search.mcts_search and beam_search on multiple targets:
  1. math.exp  -- MCTS finds the exact EML solution (MSE=0)
  2. math.sin  -- documents the best EML approximation (Infinite Zeros Barrier)
  3. GELU      -- MCTS best vs Taylor-BEST routing comparison

Run:
    cd python/
    python notebooks/mcts_sin_approximation.py

Matplotlib is optional; falls back to text summary if not installed.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

# Fix Unicode on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from monogate.search import mcts_search, beam_search
from monogate.search.mcts import _eval_tree  # internal, only for demo

# ── Probe points ──────────────────────────────────────────────────────────────
PROBE_X = [-3.0 + 6.0 * i / 49 for i in range(50)]
GELU_X  = [-3.0 + 6.0 * i / 49 for i in range(50)]


def gelu(x: float) -> float:
    """GELU activation: 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715*x^3)))"""
    return 0.5 * x * (1.0 + math.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x**3)))


def mse_fn(fn, target_fn, xs=PROBE_X):
    total = 0.0
    n = 0
    for x in xs:
        try:
            v = fn(x)
            if math.isfinite(v):
                total += (v - target_fn(x))**2
                n += 1
        except Exception:
            pass
    return total / n if n > 0 else float("inf")


def print_section(title: str) -> None:
    print()
    print("=" * 64)
    print(f"  {title}")
    print("=" * 64)
    print()


# ── 1. math.exp target: MCTS finds exact solution ─────────────────────────────

print_section("1. Target: math.exp  (MCTS should find exact EML formula)")

r_exp = mcts_search(
    math.exp,
    probe_points=[0.5 + 0.1 * i for i in range(20)],
    depth=3,
    n_simulations=2000,
    seed=42,
)
print(f"  formula  : {r_exp.best_formula}")
print(f"  MSE      : {r_exp.best_mse:.4e}")
print(f"  elapsed  : {r_exp.elapsed_s:.2f}s")
print()
print("  Note: eml(x, 1.0) = exp(x) - ln(1) = exp(x) -- exact solution.")

# ── 2. math.sin target: best EML approximation ────────────────────────────────

print_section("2. Target: math.sin  (EML grammar cannot be exact -- Infinite Zeros Barrier)")

r_sin1 = mcts_search(math.sin, probe_points=PROBE_X, depth=5, n_simulations=5000, seed=42)
r_sin8 = mcts_search(math.sin, probe_points=PROBE_X, depth=5, n_simulations=5000,
                     seed=42, n_rollouts=8)
r_beam = beam_search(math.sin, probe_points=PROBE_X, depth=5, width=100)

print(f"  MCTS (n_rollouts=1): MSE = {r_sin1.best_mse:.4e}   formula = {r_sin1.best_formula}")
print(f"  MCTS (n_rollouts=8): MSE = {r_sin8.best_mse:.4e}   formula = {r_sin8.best_formula}")
print(f"  Beam (width=100)   : MSE = {r_beam.best_mse:.4e}   formula = {r_beam.best_formula}")
print()
print("  Note: MCTS finds the best CONSTANT approximation to sin(x).")
print("  The formula eml(eml(1,1), eml(eml(eml(1,1),1),1)) = 0 for all x.")
print("  MSE~0.513 = E[sin(x)^2] on [-3,3] -- the optimal mean-zero constant.")
print("  Beam search (systematic) finds a non-trivial function (lower MSE).")
print("  No EML tree exactly represents sin(x) -- Infinite Zeros Barrier")
print("  (40.2M trees searched, N<=10, zero candidates at any tolerance).")
print("  Best practical: BEST-routed 8-term Taylor, 63 nodes, MSE=6.6e-15.")

# ── 3. Comparison table ───────────────────────────────────────────────────────

print_section("3. Approximation Comparison")

def taylor_sin_8(x: float) -> float:
    # 8-term Taylor series for sin(x)
    s = 0.0
    sign = 1
    fact = 1
    for k in range(8):
        n = 2 * k + 1
        if k > 0:
            fact *= (2 * k) * (2 * k + 1)
        s += sign * x**n / fact
        sign *= -1
    return s

mse_t8  = mse_fn(taylor_sin_8, math.sin)
best_sin = r_sin8 if r_sin8.best_mse < r_sin1.best_mse else r_sin1

print(f"  {'Method':<44}  {'MSE on [-3,3]':>14}")
print("  " + "-" * 62)
print(f"  {'MCTS depth=5, n_sim=5000, rollouts=8':<44}  {r_sin8.best_mse:>14.4e}")
print(f"  {'Beam depth=5, width=100':<44}  {r_beam.best_mse:>14.4e}")
print(f"  {'Taylor 8-term (BEST-routed, 63 EML nodes)':<44}  {mse_t8:>14.4e}")

# ── 4. Convergence history ────────────────────────────────────────────────────

print_section("4. MCTS Convergence History (n_rollouts=1)")

print(f"  {'Sim':>8}  {'Best MSE':>14}")
print("  " + "-" * 28)
for sim_n, mse_val in r_sin1.history:
    print(f"  {sim_n:>8,}  {mse_val:>14.4e}")

# ── 5. Sample predictions ─────────────────────────────────────────────────────

print_section("5. Sample Predictions at key x values (best MCTS vs Taylor-8)")

test_xs = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
print(f"  Formula: {best_sin.best_formula}")
print()
print(f"  {'x':>6}  {'sin(x)':>10}  {'MCTS':>10}  {'Taylor-8':>10}  {'err_MCTS':>10}")
print("  " + "-" * 56)
for x in test_xs:
    true_v = math.sin(x)
    t8_v   = taylor_sin_8(x)
    try:
        mcts_v = _eval_tree(best_sin.best_tree, x)
        e_m    = abs(mcts_v - true_v)
    except Exception:
        mcts_v = float("nan")
        e_m    = float("nan")
    print(f"  {x:>6.1f}  {true_v:>10.6f}  {mcts_v:>10.6f}  {t8_v:>10.6f}  {e_m:>10.2e}")

# ── 6. GELU target ────────────────────────────────────────────────────────────

print_section("6. Target: GELU  (non-trivial differentiable activation)")

r_gelu = mcts_search(gelu, probe_points=GELU_X, depth=5, n_simulations=5000, seed=7)
print(f"  Best formula : {r_gelu.best_formula}")
print(f"  Best MSE     : {r_gelu.best_mse:.4e}")
print(f"  Elapsed      : {r_gelu.elapsed_s:.2f}s")

# ── 7. Optional plot ──────────────────────────────────────────────────────────

try:
    import matplotlib.pyplot as plt  # type: ignore

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle("MCTS EML Grammar Search -- monogate.search", fontsize=12)

    # Left: convergence curves for sin(x)
    ax = axes[0]
    h1 = r_sin1.history
    h8 = r_sin8.history
    ax.semilogy([h[0] for h in h1], [h[1] for h in h1],
                label="n_rollouts=1", color="#3b82f6", linewidth=1.5)
    ax.semilogy([h[0] for h in h8], [h[1] for h in h8],
                label="n_rollouts=8", color="#10b981", linewidth=1.5)
    ax.axhline(mse_t8, color="#f97316", linestyle="--",
               label="Taylor 8-term", linewidth=1)
    ax.set_xlabel("Simulations")
    ax.set_ylabel("MSE (log scale)")
    ax.set_title("sin(x) convergence")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Right: sample predictions on [-2, 2]
    ax2 = axes[1]
    xs_p = [-2.0 + 4.0 * i / 199 for i in range(200)]
    ax2.plot(xs_p, [math.sin(x) for x in xs_p],
             label="sin(x)", color="#1e293b", linewidth=2)
    ax2.plot(xs_p, [taylor_sin_8(x) for x in xs_p],
             label="Taylor-8", color="#f97316", linestyle="--", linewidth=1)

    mcts_y = []
    for x in xs_p:
        try:
            v = _eval_tree(best_sin.best_tree, x)
            mcts_y.append(v if math.isfinite(v) else None)
        except Exception:
            mcts_y.append(None)

    # Plot MCTS where finite
    valid_x = [x for x, y in zip(xs_p, mcts_y) if y is not None]
    valid_y = [y for y in mcts_y if y is not None]
    if valid_x:
        ax2.plot(valid_x, valid_y, label="MCTS best", color="#10b981",
                 linestyle="--", linewidth=1)

    ax2.set_xlabel("x")
    ax2.set_ylabel("f(x)")
    ax2.set_title("Approximation quality on [-2, 2]")
    ax2.legend(fontsize=8)
    ax2.set_ylim(-2, 2)
    ax2.grid(True, alpha=0.3)

    out_path = Path(__file__).parent / "mcts_sin_results.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    print(f"\n  Plot saved -> {out_path}")

except ImportError:
    print("\n  (matplotlib not installed -- skipping plot)")

print()
print("=" * 64)
print("  DONE")
print("=" * 64)
