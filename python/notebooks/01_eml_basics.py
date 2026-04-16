"""
Tutorial 01: EML Basics — Tree Building and Core Operations
===========================================================
This notebook demonstrates the fundamental EML operator and how to
build expression trees from the single binary gate eml(x, y) = exp(x) - ln(y).

Run time: < 1 minute (no GPU required)

Requirements: pip install monogate
"""

# %% [markdown]
# # EML Basics
#
# The **EML operator** is defined as:
# ```
# eml(x, y) = exp(x) − ln(y)
# ```
# From this single operation and the constant 1, every elementary function
# can be constructed as a finite binary tree.

# %% Core operations
import math
from monogate import op, exp_eml, ln_eml, add_eml, mul_eml, div_eml, pow_eml

# The raw EML gate
print(f"eml(0, 1)       = {op(0, 1.0):.6f}")   # exp(0) - ln(1) = 1 - 0 = 1
print(f"eml(1, 1)       = {op(1, 1.0):.6f}")   # exp(1) - 0 = e ≈ 2.718

# exp(x) = eml(x, 1)
print(f"\nexp(2)          = {exp_eml(2.0):.6f}")
print(f"math.exp(2)     = {math.exp(2.0):.6f}")

# ln(y) = 1 - eml(0, y) — note: uses 2 nodes
print(f"\nln(e)           = {ln_eml(math.e):.6f}")
print(f"math.log(e)     = {math.log(math.e):.6f}")

# %% Arithmetic
print("\n--- Arithmetic via EML trees ---")

a, b = 3.0, 4.0
print(f"add({a}, {b})    = {add_eml(a, b):.6f}   (ref: {a + b})")
print(f"mul({a}, {b})    = {mul_eml(a, b):.6f}   (ref: {a * b})")
print(f"div({a}, {b})    = {div_eml(a, b):.6f}   (ref: {a / b})")
print(f"pow({a}, {b})    = {pow_eml(a, b):.6f}   (ref: {a ** b})")

# %% [markdown]
# ## Node counts
#
# Different operators have different costs (internal node counts):
#
# | Operation | EML nodes |
# |-----------|-----------|
# | exp(x)    | 1         |
# | ln(y)     | 2         |
# | add(a,b)  | 3         |
# | sub(a,b)  | 3         |
# | mul(a,b)  | 7         |
# | div(a,b)  | 5         |
# | pow(a,b)  | 9         |

# %% BEST routing (optimal node counts)
from monogate import BEST, best_optimize, benchmark_optimize

print("\n--- BEST routing ---")
print(f"BEST.div(3, 4)  = {BEST.div(3.0, 4.0):.6f}   (1 node via EDL)")
print(f"BEST.ln(e)      = {BEST.ln(math.e):.6f}   (1 node via EXL)")

# Benchmark: which operator wins for each operation?
table = benchmark_optimize("mul")
print(f"\nbenchmark_optimize('mul'):")
print(f"  winner = {table.winner}")
print(f"  savings vs EML = {table.savings_pct:.0f}%")

# %% [markdown]
# ## IDENTITIES
#
# All supported EML identities are stored in the `IDENTITIES` dictionary:

# %% Show identities
from monogate import IDENTITIES

print("\n--- EML Identity Library ---")
for name, identity in list(IDENTITIES.items())[:8]:
    print(f"  {name}")

print(f"\n  Total: {len(IDENTITIES)} identities")

# %% [markdown]
# ## Summary
#
# - `eml(x, y) = exp(x) − ln(y)` is the universal operator
# - All arithmetic is built from this one gate
# - BEST routing picks the optimal operator for each operation
# - 52% average node savings over pure EML

print("\n Tutorial 01 complete.")
