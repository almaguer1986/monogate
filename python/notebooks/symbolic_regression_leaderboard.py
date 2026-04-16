# %% [markdown]
# # monogate Symbolic Regression Leaderboard
#
# Standardized benchmark over Nguyen/Keijzer symbolic regression problems.
# Scored by shortest EML expression achieving MSE < threshold.
#
# Problems:
# - Nguyen-1 through Nguyen-8: classic polynomial and trig benchmarks
# - Keijzer-6: harmonic series sum(1/i)
# - Keijzer-11: x*ln(x)
#
# Run as a script or open in Jupyter / VS Code with Python extension.

# %%
import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from monogate.leaderboard import (
    PROBLEMS,
    BenchmarkProblem,
    run_leaderboard,
    markdown_leaderboard,
    save_leaderboard,
    load_leaderboard,
)

print("monogate Symbolic Regression Leaderboard")
print("=" * 50)
print(f"Registered problems: {len(PROBLEMS)}")
print()
print(f"  {'Problem':<14}  {'Domain':>16}  {'Threshold':>10}  Reference formula")
print("  " + "-" * 65)
for name, prob in PROBLEMS.items():
    print(
        f"  {name:<14}  [{prob.domain[0]:>6.2f}, {prob.domain[1]:>6.2f}]"
        f"  {prob.mse_threshold:>10.1e}  {prob.reference_formula or '—'}"
    )

# %% [markdown]
# ## Run the leaderboard (fast mode: beam search, n_sim=200)
#
# For a full run: increase n_simulations to 2000+ and add 'mcts' to methods.

# %%
print()
print("Running leaderboard (fast mode: beam, n_sim=200) ...")
print()

entries = run_leaderboard(
    problems=list(PROBLEMS.keys()),
    n_simulations=200,
    depth=5,
    methods=["beam"],
    seed=42,
)

solved = sum(1 for e in entries if e.solved)
print(f"Solved: {solved}/{len(entries)}")
print()
print(markdown_leaderboard(entries))

# %% [markdown]
# ## Save results

# %%
results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(results_dir, exist_ok=True)
json_path = os.path.join(results_dir, "leaderboard.json")
save_leaderboard(entries, json_path)
print(f"\nSaved: {json_path}")

# %% [markdown]
# ## Visualize: MSE distribution

# %%
print()
problems_sorted = sorted(entries, key=lambda e: e.best_mse)
names = [e.problem for e in problems_sorted]
mses = [e.best_mse for e in problems_sorted]
colors = ["steelblue" if e.solved else "crimson" for e in problems_sorted]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(names, [math.log10(max(m, 1e-16)) for m in mses], color=colors)
ax.axhline(0, color="black", linewidth=0.8, linestyle=":")

# Draw threshold lines
for i, e in enumerate(problems_sorted):
    thresh = PROBLEMS[e.problem].mse_threshold
    ax.plot([i - 0.4, i + 0.4], [math.log10(thresh), math.log10(thresh)],
            color="darkorange", linewidth=1.5)

ax.set_xticks(range(len(names)))
ax.set_xticklabels(names, rotation=45, ha="right")
ax.set_ylabel("log₁₀(MSE)")
ax.set_title("Leaderboard: MSE per problem (beam search, n_sim=200)\nBlue = solved, Red = not solved, Orange line = threshold")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("leaderboard_gallery.png", dpi=120)
plt.close()
print("Saved: leaderboard_gallery.png")

# %% [markdown]
# ## Node counts

# %%
print()
print("Node counts (EML nodes in best expression found):")
print(f"  {'Problem':<14}  {'Nodes':>6}  {'MSE':>10}  {'Solved':>6}  Formula (truncated)")
print("  " + "-" * 75)
for e in sorted(entries, key=lambda e: (not e.solved, e.n_nodes)):
    tick = "✓" if e.solved else "✗"
    print(f"  {e.problem:<14}  {e.n_nodes:>6}  {e.best_mse:>10.3e}  {tick:>6}  {e.formula[:35]}")

# %% [markdown]
# ## Summary
#
# | Method | Problems tried | Solved | Avg nodes |
# |--------|---------------|--------|-----------|
# | beam   | N             | M      | ~k        |
#
# Results are saved to `results/leaderboard.json` and can be loaded with
# `from monogate.leaderboard import load_leaderboard`.

# %%
avg_nodes = sum(e.n_nodes for e in entries) / max(len(entries), 1)
print()
print("Summary")
print(f"  Method: beam | n_sim=200 | depth=5")
print(f"  Solved: {solved}/{len(entries)}  ({100*solved//len(entries) if entries else 0}%)")
print(f"  Avg EML nodes: {avg_nodes:.1f}")
print()
print("Leaderboard complete.")
