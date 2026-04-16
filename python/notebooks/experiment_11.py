# Results (run 2026-04-16, Python 3.14, CPU):
#
# Experiment             nodes EML  nodes BEST  savings  speedup
# ---------------------- ---------  ----------  -------  -------
# sin/cos (exp_09)             245          63    74.0%    2.80x
# poly    (exp_11)              67          31    53.7%    2.08x
# GELU    (exp_10)              17          14    18.0%    0.93x
#
# Linear model:  speedup = 0.0332 * savings_pct + 0.3206  (R2=0.9992)
# Crossover:     ~20.4% node reduction → speedup = 1.0x
#
"""
experiment_11  --  Overhead Crossover: Node Reduction vs Wall-Clock Speedup
===========================================================================
Locates the BEST-routing speedup crossover threshold by benchmarking a
polynomial activation with ~54% node reduction — midway between:
  experiment_09: sin/cos  74% reduction → 2.8× speedup
  experiment_10: GELU     18% reduction → 0.93× speedup

Target activation: poly(x) = x⁴ + x³ + x²
  EML routing:  3×pow_eml(15n) + 2×add_eml(11n) = 67 nodes
  BEST routing: 3×pow_exl( 3n) + 2×add_eml(11n) = 31 nodes
  Savings: 53.7%

pow_eml requires x > 1 (ln(x) must be > 0 for mul_eml).
Benchmark uses values in [1.1, 2.5] — same constraint as experiment_09.

Architecture: same as experiment_10 in spirit
  Scalar batch of 512 activations (= d_hid=64 × batch=8)
  measured ms/batch and us/element

Summary table (all three experiments):
  exp   activation   nodes_eml  nodes_best  savings  speedup
  09    sin          245        63          74%      ~2.8x
  11    poly         67         31          54%      ???x
  10    GELU         17         14          18%      ~0.93x

Linear model: speedup = a * savings_pct + b → crossover at speedup=1.0

Usage
-----
  cd python && python notebooks/experiment_11.py
"""

import math
import random
import sys
import timeit
from typing import Callable

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from monogate import pow_eml, add_eml
    from monogate.core import pow_exl
except ImportError as exc:
    print(f"monogate not installed: {exc}")
    sys.exit(1)


SEP  = "=" * 68
SEP2 = "-" * 52

# ── Node count constants ──────────────────────────────────────────────────────
EML_NODES_POW  = 15
EXL_NODES_POW  =  3
EML_NODES_ADD  = 11
N_POW_TERMS    =  3   # x^4, x^3, x^2
N_ADD_OPS      =  2

EML_TOTAL   = N_POW_TERMS * EML_NODES_POW + N_ADD_OPS * EML_NODES_ADD   # 67
BEST_TOTAL  = N_POW_TERMS * EXL_NODES_POW + N_ADD_OPS * EML_NODES_ADD   # 31
SAVINGS_PCT = round((1 - BEST_TOTAL / EML_TOTAL) * 100, 1)              # 53.7%


# ── Activation functions ──────────────────────────────────────────────────────

def poly_eml(x: float) -> float:
    """x⁴ + x³ + x² — pure EML arithmetic, 67 nodes.  Domain: x > 1."""
    p4 = pow_eml(x, 4)
    p3 = pow_eml(x, 3)
    p2 = pow_eml(x, 2)
    s1 = add_eml(p4, p3)
    return add_eml(s1, p2)


def poly_best(x: float) -> float:
    """x⁴ + x³ + x² — BEST routing, 31 nodes.  Domain: x > 0."""
    p4 = float(pow_exl(x, 4).real)
    p3 = float(pow_exl(x, 3).real)
    p2 = float(pow_exl(x, 2).real)
    s1 = add_eml(p4, p3)
    return add_eml(s1, p2)


def poly_native(x: float) -> float:
    """x⁴ + x³ + x² — native Python arithmetic."""
    return x * x * x * x + x * x * x + x * x


def bench_batch(fn: Callable, vals: list, runs: int = 50) -> float:
    """Return median ms/batch over 3 blocks."""
    def _run():
        for v in vals: fn(v)
    times = []
    for _ in range(3):
        t = timeit.timeit(_run, number=runs)
        times.append(t / runs * 1000)
    return sorted(times)[1]


# ── Main ──────────────────────────────────────────────────────────────────────

print(SEP)
print("  experiment_11  --  Overhead Crossover: Node Reduction vs Speedup")
print(SEP)
print()

# ── Section A: Verify node counts and accuracy ────────────────────────────────
print("Section A  Node count verification and accuracy")
print(SEP2)
print()
print(f"  poly(x) = x^4 + x^3 + x^2")
print(f"  EML:  {N_POW_TERMS} x pow_eml({EML_NODES_POW}n) + {N_ADD_OPS} x add_eml({EML_NODES_ADD}n) = {EML_TOTAL} nodes")
print(f"  BEST: {N_POW_TERMS} x pow_exl( {EXL_NODES_POW}n) + {N_ADD_OPS} x add_eml({EML_NODES_ADD}n) = {BEST_TOTAL} nodes")
print(f"  Savings: {SAVINGS_PCT}%  (target range 35-55%: {'PASS' if 35 <= SAVINGS_PCT <= 55 else 'FAIL'})")
print()

xs = [1.5, 2.0, 2.5, 3.0, 4.0]
print(f"  {'x':>6}  {'ref':>12}  {'EML':>12}  {'BEST':>12}  {'err_eml':>10}  {'err_best':>10}")
print(f"  {'-'*6}  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*10}  {'-'*10}")
for x in xs:
    ref  = x**4 + x**3 + x**2
    eml  = poly_eml(x)
    best = poly_best(x)
    print(f"  {x:>6.1f}  {ref:>12.6f}  {eml:>12.6f}  {best:>12.6f}  "
          f"{abs(eml-ref):>10.2e}  {abs(best-ref):>10.2e}")
print()

# ── Section B: Scalar batch benchmark ────────────────────────────────────────
D_HID, BATCH = 64, 8
N_ACTIVATIONS = D_HID * BATCH   # 512

print(f"Section B  Scalar batch benchmark  ({BATCH} samples x {D_HID} hidden = {N_ACTIVATIONS} activations)")
print(SEP2)
print()
print(f"  Input domain: x in [1.1, 2.5]  (pow_eml requires x > 1)")
print(f"  Matches FFN hidden-unit structure of experiment_10")
print()

rng = random.Random(42)
vals = [1.1 + rng.random() * 1.4 for _ in range(N_ACTIVATIONS)]

t_native = bench_batch(poly_native, vals, runs=50)
t_eml    = bench_batch(poly_eml,    vals, runs=50)
t_best   = bench_batch(poly_best,   vals, runs=50)

speedup_vs_eml = t_eml / t_best  if t_best  > 0 else float("nan")
overhead_best  = t_best / t_native if t_native > 0 else float("nan")

us_eml    = t_eml    * 1000 / N_ACTIVATIONS
us_best   = t_best   * 1000 / N_ACTIVATIONS
us_native = t_native * 1000 / N_ACTIVATIONS

print(f"  {'Activation':<22}  {'ms/batch':>10}  {'us/elem':>10}  {'gates/elem':>12}")
print(f"  {'-'*22}  {'-'*10}  {'-'*10}  {'-'*12}")
print(f"  {'native math':<22}  {t_native:>10.3f}  {us_native:>10.2f}  {'--':>12}")
print(f"  {'EML-poly':<22}  {t_eml:>10.3f}  {us_eml:>10.2f}  {EML_TOTAL:>12}")
print(f"  {'BEST-poly':<22}  {t_best:>10.3f}  {us_best:>10.2f}  {BEST_TOTAL:>12}")
print(f"  {'-'*22}  {'-'*10}  {'-'*10}  {'-'*12}")
print(f"  Speedup: {speedup_vs_eml:.2f}x   ({SAVINGS_PCT}% fewer gates)")
print(f"  BEST overhead vs native: {overhead_best:.1f}x")
print()

# ── Section C: Three-experiment summary and linear model ─────────────────────
print("Section C  All three experiments: node savings vs wall-clock speedup")
print(SEP2)
print()

# Anchor values from other experiments (reported medians)
EXP_09_SAVINGS = 74.0
EXP_09_SPEEDUP = 2.8
EXP_10_SAVINGS = 18.0
EXP_10_SPEEDUP = 0.93

rows = [
    ("sin/cos (exp_09)", 245, 63,         EXP_09_SAVINGS, EXP_09_SPEEDUP),
    ("poly    (exp_11)", EML_TOTAL, BEST_TOTAL, SAVINGS_PCT, speedup_vs_eml),
    ("GELU    (exp_10)", 17,  14,         EXP_10_SAVINGS, EXP_10_SPEEDUP),
]

print(f"  {'Experiment':<22}  {'nodes EML':>10}  {'nodes BEST':>11}  {'savings':>8}  {'speedup':>8}")
print(f"  {'-'*22}  {'-'*10}  {'-'*11}  {'-'*8}  {'-'*8}")
for name, n_eml, n_best, sv, sp in rows:
    print(f"  {name:<22}  {n_eml:>10}  {n_best:>11}  "
          f"{sv:>7.1f}%  {sp:>7.2f}x")
print()

# ── Section D: Linear model fit ───────────────────────────────────────────────
print("Section D  Linear model: speedup = a * savings_pct + b")
print(SEP2)
print()

xs_ = [r[3] for r in rows]
ys_ = [r[4] for r in rows]
n_  = len(xs_)

sum_x  = sum(xs_)
sum_y  = sum(ys_)
sum_xy = sum(x*y for x, y in zip(xs_, ys_))
sum_xx = sum(x*x for x in xs_)
denom  = n_ * sum_xx - sum_x ** 2

a = (n_ * sum_xy - sum_x * sum_y) / denom if abs(denom) > 1e-12 else float("nan")
b = (sum_y - a * sum_x) / n_

crossover = (1.0 - b) / a if abs(a) > 1e-12 else float("nan")

ss_res = sum((y - (a*x + b))**2 for x, y in zip(xs_, ys_))
ss_tot = sum((y - sum_y/n_)**2 for y in ys_)
r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")

print(f"  speedup = {a:.4f} x savings_pct + {b:.4f}")
print(f"  R2 = {r2:.4f}")
print()
print(f"  Predicted speedup at each savings level:")
for sv in [18, 30, 40, 50, 60, 74]:
    pred = a * sv + b
    print(f"    savings={sv}%  -> speedup={pred:.2f}x")
print()
print(f"  Crossover (speedup = 1.0x): {crossover:.1f}% node reduction")
print()
print(f"  Interpretation: BEST routing yields a wall-clock speedup when")
print(f"  node savings exceed approximately {crossover:.0f}% of the EML count.")
print()
print(SEP)
print("  experiment_11 complete.")
print(SEP)

# ─────────────────────────────────────────────────────────────────────────────
# Interpretation (one paragraph)
#
# We benchmarked poly(x) = x^4 + x^3 + x^2 as an activation that sits midway
# between GELU (18% savings, ~0.93x speedup) and sin/cos (74% savings, ~2.8x
# speedup) in the node-reduction spectrum.  With BEST routing reducing node
# count by 53.7% (67 -> 31 gates), we measure the actual wall-clock speedup
# and combine it with the two anchor data points to fit a linear model:
#   speedup = a * savings_pct + b.
# The model yields a crossover at approximately N% node reduction — below that
# threshold, Python function-call overhead dominates and BEST routing actually
# slows things down; above it, the gate-count savings translate to real speedup.
# This converts the previously qualitative "savings must exceed overhead" rule
# from the paper into a concrete, experiment-backed number that practitioners
# can use to decide whether to apply BEST routing to a given function.
# ─────────────────────────────────────────────────────────────────────────────
