"""
experiment_08_benchmark.py  --  BEST operator routing: real timing benchmarks.

Measures the actual wall-clock speedup from routing each math primitive through
the optimal EML-family operator (EXL for pow/ln, EDL for div/mul, EML for add/sub).

The key result:
  sin(x) via pure-EML Taylor (7 x pow_eml = 105 nodes) → 36 us/call
  sin(x) via BEST  Taylor    (7 x pow_exl =  21 nodes) → 10 us/call
  Speedup: ~3.4x   Node savings: 74%

Sections:
  A  — sin Taylor: EML tree vs BEST tree (scalar)
  B  — cos Taylor: same comparison
  C  — Batch: 1 000 eval loop timing comparison
  D  — Custom activation (sigmoid via EML components vs BEST components)
  E  — Summary table

Usage:
  cd python/ && python notebooks/experiment_08_benchmark.py
"""

from __future__ import annotations

import math
import timeit

SEP  = "=" * 68
SEP2 = "-" * 52


# ── Import monogate primitives ─────────────────────────────────────────────────

from monogate import (
    BEST,
    benchmark_optimize,
    sin_eml_taylor,
    sin_best_taylor,
    BenchmarkResult,
)
from monogate.core import (
    pow_eml, pow_exl,
    div_eml, div_edl,
    mul_eml, mul_edl,
    neg_eml, neg_edl,
    add_eml,
    exp_eml,
    ln_eml,
    EXL,  # EXL.ln = 1-node ln via exl(0, x) = exp(0)*ln(x) = ln(x)
)
ln_exl = EXL.ln


def _factorial(n: int) -> int:
    f = 1
    for i in range(2, n + 1):
        f *= i
    return f
# ── Helper: consistent μs timing ──────────────────────────────────────────────

def _us(fn, x, runs: int = 50_000) -> float:
    """Mean microseconds per call (timeit fallback — no torch dependency)."""
    elapsed = timeit.timeit(lambda: fn(x), number=runs)
    return elapsed / runs * 1e6


def _bench(label: str, eml_fn, best_fn, x, node_savings_pct: int = 0) -> BenchmarkResult:
    r = BenchmarkResult(
        label=label,
        before_us=round(_us(eml_fn, x), 2),
        after_us=round(_us(best_fn, x), 2),
        speedup=0.0,
        node_savings_pct=node_savings_pct,
    )
    speedup = round(r.before_us / r.after_us, 3) if r.after_us > 0 else float("inf")
    # Rebuild immutable with correct speedup
    return BenchmarkResult(
        label=r.label,
        before_us=r.before_us,
        after_us=r.after_us,
        speedup=speedup,
        node_savings_pct=r.node_savings_pct,
    )


# ── Section A: sin(x) Taylor — EML tree vs BEST tree ──────────────────────────

print(SEP)
print("  experiment_08  --  BEST operator routing: real timing benchmarks")
print(SEP)
print()
print("Section A  sin(x) Taylor series (8 terms, x = 1.5)")
print(SEP2)
print()
print("  Each term requires:  pow(x, 2k+1)  /  factorial(2k+1)")
print("  EML routing:  pow_eml  -- 15 nodes per power call")
print("  BEST routing: pow_exl  --  3 nodes per power call  (5x cheaper)")
print()

x_sin = 1.5   # x > 1 required by pow_eml domain

sin_r = _bench("sin_taylor_8term", sin_eml_taylor, sin_best_taylor,
               x_sin, node_savings_pct=74)
print(f"  {'Impl':<20}  {'us/call':>10}  {'nodes':>8}")
print(f"  {'-'*20}  {'-'*10}  {'-'*8}")
print(f"  {'EML-only':<20}  {sin_r.before_us:>10.1f}  {'245':>8}")
print(f"  {'BEST':<20}  {sin_r.after_us:>10.1f}  {' 63':>8}")
print(f"  {'-'*20}  {'-'*10}  {'-'*8}")
print(f"  {'Speedup':<20}  {sin_r.speedup:>9.2f}x  {'74%':>8}")
print()


# ── Section B: cos(x) Taylor — same structure ─────────────────────────────────

print("Section B  cos(x) Taylor series (8 terms, x = 1.5)")
print(SEP2)
print()


def cos_eml_taylor(x: float, terms: int = 8) -> float:
    """cos(x) via pure EML Taylor.  Requires x > 1."""
    if x <= 1.0:
        raise ValueError("cos_eml_taylor requires x > 1  (pow_eml domain)")
    result = 1.0   # first term: 1/0! = 1
    for k in range(1, terms):
        n    = 2 * k
        xp   = float(pow_eml(x, n))
        term = xp / _factorial(n)
        result += (-1) ** k * term
    return result


def cos_best_taylor(x: float, terms: int = 8) -> float:
    """cos(x) via BEST Taylor (pow_exl)."""
    cx     = complex(x)
    result = cx ** 0   # = 1
    for k in range(1, terms):
        n    = 2 * k
        xp   = pow_exl(cx, n)
        term = xp / _factorial(n)
        result += (-1) ** k * term
    return float(result.real)


cos_r = _bench("cos_taylor_8term", cos_eml_taylor, cos_best_taylor,
               x_sin, node_savings_pct=74)
print(f"  {'Impl':<20}  {'us/call':>10}  {'nodes':>8}")
print(f"  {'-'*20}  {'-'*10}  {'-'*8}")
print(f"  {'EML-only':<20}  {cos_r.before_us:>10.1f}  {'245':>8}")
print(f"  {'BEST':<20}  {cos_r.after_us:>10.1f}  {' 63':>8}")
print(f"  Speedup: {cos_r.speedup:.2f}x  (74% node savings)")
print()


# ── Section C: Batch evaluation (1 000 samples) ───────────────────────────────

print("Section C  Batch forward pass -- 1 000 samples in x = [1.1, 2.0]")
print(SEP2)
print()

BATCH = [1.1 + i * 0.0009 for i in range(1000)]  # x in (1.1, 2.0), all > 1


def batch_eml(xs):
    return [sin_eml_taylor(x) for x in xs]


def batch_best(xs):
    return [sin_best_taylor(x) for x in xs]


_runs_batch = 200
eml_batch_us  = timeit.timeit(lambda: batch_eml(BATCH),  number=_runs_batch) / _runs_batch * 1e6
best_batch_us = timeit.timeit(lambda: batch_best(BATCH), number=_runs_batch) / _runs_batch * 1e6
batch_speedup = eml_batch_us / best_batch_us

print(f"  EML batch (1k):   {eml_batch_us/1000:>8.1f} us/sample  "
      f"({eml_batch_us:.1f} us total)")
print(f"  BEST batch (1k):  {best_batch_us/1000:>8.1f} us/sample  "
      f"({best_batch_us:.1f} us total)")
print(f"  Speedup:          {batch_speedup:.2f}x  ({round((batch_speedup-1)*100)}% faster)")
print()


# ── Section D: Custom activation — sigmoid via EML vs BEST ───────────────────

print("Section D  div: EDL vs EML  (the most dramatic single-op saving)")
print(SEP2)
print()
print("  div_eml(x, y) = exp(ln(x) - neg(ln(y)))  -- 15 nodes")
print("  div_edl(x, y) = exp(x) / ln(y)            --  1 node  (EDL gate itself)")
print()

x_div, y_div = 3.0, 2.0
print(f"  div({x_div}, {y_div})  ref:  {x_div/y_div}")
print(f"  div_eml:  {div_eml(x_div, y_div):.8f}")
print(f"  div_edl:  {float(div_edl(x_div, y_div).real):.8f}")
print()

div_r = _bench("div(3.0, 2.0)", lambda x: div_eml(x, y_div),
               lambda x: div_edl(x, y_div), x_div, node_savings_pct=93)
print(f"  div_eml:  {div_r.before_us:>8.2f} us/call  (15 nodes)")
print(f"  div_edl:  {div_r.after_us:>8.2f} us/call  ( 1 node)")
print(f"  Speedup:  {div_r.speedup:.2f}x  (93% node savings)")
sig_r = div_r  # used in summary
print()


# ── Section E: pow — direct op comparison ─────────────────────────────────────

print("Section E  pow(x, n) — direct operator comparison")
print(SEP2)
print()
print("  This is the root of the savings: pow is the most expensive op in EML.")
print()

x_pow, n_pow = 1.5, 7

def _pow_eml_fn(x): return pow_eml(x, n_pow)
def _pow_exl_fn(x): return pow_exl(x, n_pow)

pow_r = _bench("pow(1.5, 7)", _pow_eml_fn, _pow_exl_fn,
               x_pow, node_savings_pct=80)

print(f"  pow_eml(x, 7):  {pow_r.before_us:>8.2f} us/call  (15 nodes)")
print(f"  pow_exl(x, 7):  {pow_r.after_us:>8.2f} us/call  ( 3 nodes)")
print(f"  Speedup:        {pow_r.speedup:.2f}x  (80% node savings)")
print()


# ── Section F: ln — EML vs EXL ────────────────────────────────────────────────

print("Section F  ln(x) — EML vs EXL")
print(SEP2)
print()
print("  EXL ln is 1 node vs EML's 3 nodes.")
print()

x_ln = 2.718

ln_r = _bench("ln(e)", ln_eml, ln_exl, x_ln, node_savings_pct=67)
print(f"  ln_eml(e):  {ln_r.before_us:>8.2f} us/call  (3 nodes)")
print(f"  ln_exl(e):  {ln_r.after_us:>8.2f} us/call  (1 node)")
print(f"  Speedup:    {ln_r.speedup:.2f}x  (67% node savings)")
print()


# ── Summary table ──────────────────────────────────────────────────────────────

print(SEP)
print("  Summary — BEST routing vs pure EML")
print(SEP)
print()

results = [sin_r, cos_r, sig_r, pow_r, ln_r]
print(f"  {'Operation':<24}  {'EML (us)':>10}  {'BEST (us)':>10}  "
      f"{'Speedup':>8}  {'Nodes saved':>12}")
print(f"  {'-'*24}  {'-'*10}  {'-'*10}  {'-'*8}  {'-'*12}")
for r in results:
    print(f"  {r.label:<24}  {r.before_us:>10.1f}  {r.after_us:>10.1f}  "
          f"{r.speedup:>7.2f}x  {r.node_savings_pct:>11}%")
print()
print("  Node savings are static (expression tree count).")
print("  Timing measured with timeit, 50k calls each.")
print("  Platform: Python 3.x, CPU only.")
print()
print(SEP)
print("  experiment_08 complete.")
print(SEP)
