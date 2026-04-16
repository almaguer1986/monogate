"""
Tutorial 03: Complex Bypass — The Sin Barrier and Euler Solution
================================================================
Demonstrates the Infinite Zeros Barrier and the exact 1-node
complex bypass for sin(x) and cos(x).

Run time: < 1 minute
"""

# %% [markdown]
# # Complex Bypass
#
# **The barrier:** No finite real EML tree can represent sin(x) exactly.
# Proof: sin(x) has infinitely many zeros; every real EML tree has finitely many.
#
# **The bypass:** Im(exp(ix)) = sin(x) exactly. One complex EML node suffices.

# %% Show the barrier
import math
from monogate.search import mcts_search

print("=== Real EML approximation of sin(x) ===\n")
print("Searching for best real EML tree (n_simulations=500)...")

result = mcts_search(
    math.sin,
    probe_points=[-3.0 + 6.0 * i / 49 for i in range(50)],
    depth=5,
    n_simulations=500,
    seed=42,
)

print(f"Best formula: {result.best_formula}")
print(f"Best MSE:     {result.best_mse:.4e}")
print()
print("This is an approximation only — it cannot be exact")
print("(Infinite Zeros Barrier: real EML trees have finite zeros)")

# %% The complex bypass
print("\n=== Complex bypass: exact 1-node sin(x) ===\n")

from monogate import sin_via_euler, cos_via_euler
from monogate.special import sin_cb, cos_cb

test_points = [0.0, math.pi/6, math.pi/4, math.pi/3, math.pi/2, math.pi]
print(f"{'x':>8}  {'sin_cb(x)':>12}  {'math.sin(x)':>12}  {'error':>10}")
print(f"{'-'*8}  {'-'*12}  {'-'*12}  {'-'*10}")
max_err = 0.0
for x in test_points:
    ours = sin_cb(x)
    ref  = math.sin(x)
    err  = abs(ours - ref)
    max_err = max(max_err, err)
    print(f"{x:>8.4f}  {ours:>12.10f}  {ref:>12.10f}  {err:>10.2e}")

print(f"\nMax error: {max_err:.2e}  (floating-point rounding only)")

# %% Full catalog
print("\n=== Special functions catalog ===\n")

from monogate.special import CATALOG

print(f"{'Function':<12} {'Backend':<8} {'Nodes':>6} {'Max Error':>12}")
print(f"{'-'*12} {'-'*8} {'-'*6} {'-'*12}")
for name, entry in CATALOG.items():
    err_s = "exact" if entry.max_abs_error == 0.0 else f"{entry.max_abs_error:.0e}"
    print(f"{name:<12} {entry.backend:<8} {entry.n_nodes:>6} {err_s:>12}")

# %% Physics applications
print("\n=== Physics: compact PDE solutions ===\n")

from monogate.physics import schrodinger_free_cb, wave_cos_cb, PHYSICS_CATALOG

print("Free-particle Schrödinger: exp(ikx) = 1 CBEST node")
for x in [0.0, 0.5, 1.0]:
    val = schrodinger_free_cb(x, k=1.0)
    print(f"  x={x:.1f}: |ψ(x)| = {abs(val):.6f}  (should be 1.0 always)")

print(f"\nPhysics catalog: {len(PHYSICS_CATALOG)} equations")

# %% Summary
print("\n Tutorial 03 complete.")
print(" Key results:")
print("   - Real EML: sin(x) unreachable (infinite zeros barrier)")
print("   - CBEST: sin(x) = Im(exp(ix)) = 1 node (exact)")
print("   - 15 special functions cataloged, 5 exact")
