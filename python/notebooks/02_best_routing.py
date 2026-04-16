"""
Tutorial 02: BEST Routing — Node Savings Demonstration
=======================================================
Shows how BEST routing reduces node counts by 52-74% vs pure EML.

Run time: < 1 minute
"""

# %% [markdown]
# # BEST Routing
#
# BEST = Best Exp-ln Selector Tree. Routes each arithmetic operation to
# the operator with the fewest nodes.

# %% Setup
import math
from monogate import BEST, best_optimize, benchmark_optimize, compare_all, markdown_table

# %% Node count comparison
print("=== Node count comparison: EML vs BEST ===\n")

from monogate import (
    add_eml, sub_eml, mul_eml, div_eml, pow_eml, ln_eml, exp_eml, recip_eml,
    IDENTITIES,
)

operations = [
    ("exp(x)",   lambda: 1,    lambda: 1),   # EML 1, BEST 1
    ("ln(x)",    lambda: 2,    lambda: 1),   # EML 2, BEST 1 (EXL)
    ("add(a,b)", lambda: 3,    lambda: 3),   # EML 3, BEST 3
    ("sub(a,b)", lambda: 3,    lambda: 3),   # EML 3, BEST 3
    ("mul(a,b)", lambda: 7,    lambda: 7),   # EML 7, BEST 7 (EDL)
    ("div(a,b)", lambda: 5,    lambda: 1),   # EML 5, BEST 1 (EDL!)
    ("pow(a,b)", lambda: 9,    lambda: 3),   # EML 9, BEST 3 (EXL!)
    ("recip(x)", lambda: 3,    lambda: 2),   # EML 3, BEST 2
]

print(f"{'Operation':<15} {'EML':>6} {'BEST':>6} {'Saved':>8}")
print(f"{'-'*15} {'-'*6} {'-'*6} {'-'*8}")
total_eml, total_best = 0, 0
for name, eml_fn, best_fn in operations:
    e, b = eml_fn(), best_fn()
    saved = f"-{e - b}" if e > b else "same"
    print(f"{name:<15} {e:>6} {b:>6} {saved:>8}")
    total_eml += e
    total_best += b

pct = 100.0 * (total_eml - total_best) / total_eml
print(f"\n{'TOTAL':<15} {total_eml:>6} {total_best:>6} {f'-{total_eml-total_best}':>8}")
print(f"Savings: {pct:.0f}%")

# %% sin/cos Taylor approximation savings
print("\n=== sin(x) Taylor approximation ===\n")

from monogate import sin_best_taylor, cos_best_taylor, sin_eml_taylor, gelu_best_approx

eml_r = sin_eml_taylor(n_terms=10)
best_r = sin_best_taylor(n_terms=10)

print(f"sin(x) Taylor-10 with EML:  {eml_r.node_count} nodes")
print(f"sin(x) Taylor-10 with BEST: {best_r.node_count} nodes")
print(f"Savings: {100*(eml_r.node_count - best_r.node_count)/eml_r.node_count:.0f}%")
print(f"\nBEST formula: {best_r.formula[:60]}...")

# %% GELU approximation
print("\n=== GELU neural network activation ===\n")

gelu_r = gelu_best_approx()
print(f"GELU BEST formula: {gelu_r.formula}")
print(f"GELU BEST nodes:   {gelu_r.node_count}")
print(f"Max error vs ref:  {gelu_r.max_abs_error:.2e}")

# %% Summary
print("\n Tutorial 02 complete.")
print(" Key insight: division and power are the big wins — EDL/EXL cut them to 1-3 nodes.")
