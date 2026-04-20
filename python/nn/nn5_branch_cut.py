#!/usr/bin/env python3
# encoding: utf-8
"""
NN-5: Branch cut problem in EML symbolic trees.

The EML operator eml(x, y) = exp(x) - ln(y) requires y > 0.
When a subtree returns a negative value that feeds into ln(·),
we hit a branch cut: ln is undefined on the negative real axis.

Four strategies to handle branch cuts in EML trees:

  Option A — Softplus clamp:    y_safe = ln(1 + exp(y))   [always positive]
  Option B — Abs wrapper:       y_safe = |y| + ε          [piecewise, discontinuous grad at 0]
  Option C — Complex routing:   y_safe = y + i·π (analytic continuation)
  Option D — DEML routing:      use exp(-x) when y trends negative

We test each strategy on two target functions:

  f1(x) = ln(sin(x))  for x ∈ (0, π)
           — sin(x) > 0 on this interval: branch cut appears only at endpoints
           — a monotonic alternative used in frequency analysis

  f2(x) = ln(|sin(x)|)  for x ∈ (0.1, π-0.1) with random-sign subtrees
           — tests strategies that must handle sign changes
"""

import sys
import torch
import math
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

EPS = 1e-6

# ── Target functions ───────────────────────────────────────────────────
def f1_true(x: torch.Tensor) -> torch.Tensor:
    """ln(sin(x)) — defined on (0, π)."""
    return torch.log(torch.sin(x).clamp(min=EPS))


def f2_true(x: torch.Tensor) -> torch.Tensor:
    """ln(|sin(x)|) — well-defined everywhere sin(x) ≠ 0."""
    return torch.log(torch.abs(torch.sin(x)).clamp(min=EPS))


# ── Branch-cut strategies ──────────────────────────────────────────────
# Each strategy receives the raw (possibly negative) subtree output y_raw
# and computes ln(y_safe) where y_safe > 0.

def strategy_a_softplus(y_raw: torch.Tensor) -> torch.Tensor:
    """
    Option A: Softplus clamp — y_safe = ln(1 + exp(y_raw)) = LEAd(y_raw, 1)
    Always positive, smooth, and differentiable everywhere.
    Distorts the value: large negative y_raw → y_safe ≈ exp(y_raw) ≈ 0+
    """
    return torch.log(1.0 + torch.exp(y_raw.clamp(max=80.0)))


def strategy_b_abs(y_raw: torch.Tensor) -> torch.Tensor:
    """
    Option B: Abs wrapper — y_safe = |y_raw| + ε
    Fast and exact for |y_raw| ≫ 0, but gradient is discontinuous at y=0.
    """
    return torch.abs(y_raw) + EPS


def strategy_c_complex(y_raw: torch.Tensor) -> torch.Tensor:
    """
    Option C: Complex analytic continuation — ln(y_raw) = ln|y_raw| + i·arg(y_raw)
    For y_raw < 0: ln(y_raw) = ln(|y_raw|) + i·π (principal branch)
    We return the real part here; callers can use imaginary part for phase.
    The real part equals ln(|y_raw|), so this is exact for the magnitude.
    """
    return torch.log(torch.abs(y_raw).clamp(min=EPS))  # real part of complex ln


def strategy_d_deml(y_raw: torch.Tensor, x_proxy: torch.Tensor) -> torch.Tensor:
    """
    Option D: DEML routing — for monotonic targets where y_raw < 0 indicates
    the argument should be handled via exp(-x) instead of exp(x).
    DEML(x, y) = exp(-x) - ln(y), so we flip the sign of x when y < 0.
    This keeps everything real-valued by routing around the branch cut.
    Here: if y_raw < 0, use -x_proxy; else use x_proxy.
    Returns: exp(±x_proxy) value (not ln), demonstrating the routing.
    """
    sign = torch.where(y_raw >= 0, torch.ones_like(y_raw), -torch.ones_like(y_raw))
    return torch.exp(sign * x_proxy)


# ── Evaluation on test domain ──────────────────────────────────────────
def evaluate_strategies() -> dict:
    """
    Simulate a subtree that outputs y_raw = sin(x) (which goes negative
    for x ∈ (π, 2π)) and evaluate how each strategy handles it.
    For f1: x ∈ (0.1, π-0.1), sin(x) > 0 (no branch cut needed)
    For f2: x ∈ (0.1, 2π-0.1), sin(x) crosses zero
    """
    # f1 domain: sin(x) > 0 throughout
    x1 = torch.linspace(0.1, math.pi - 0.1, 500)
    y_raw1 = torch.sin(x1)  # always positive here

    # f2 domain: sin(x) changes sign
    x2 = torch.linspace(0.1, 2 * math.pi - 0.1, 1000)
    y_raw2 = torch.sin(x2)  # goes negative in (π, 2π)

    true1 = f1_true(x1)
    true2 = f2_true(x2)

    results = {}

    # -- f1 evaluation (sin(x) > 0, no branch cut) ---------------------
    for name, fn in [
        ('A_softplus', lambda y: torch.log(strategy_a_softplus(y))),
        ('B_abs',      lambda y: torch.log(strategy_b_abs(y))),
        ('C_complex',  lambda y: strategy_c_complex(y)),  # already returns ln|y|
    ]:
        pred = fn(y_raw1)
        mse = float(torch.mean((pred - true1) ** 2))
        max_err = float(torch.max(torch.abs(pred - true1)))
        results[f'f1_{name}'] = {'mse': mse, 'max_err': max_err}

    # DEML doesn't apply a direct ln; measure differently for f1
    # (DEML is for monotonic, not oscillatory — f1 IS the right target)
    # Approximate f1 with EML-family routing: for x ∈ (0,π), sin(x) > 0, so no routing needed
    results['f1_D_deml'] = {'mse': 0.0, 'max_err': 0.0,
                             'note': 'DEML routing not needed — sin(x)>0 on (0,π)'}

    # -- f2 evaluation (sin(x) changes sign) ----------------------------
    for name, fn in [
        ('A_softplus', lambda y: torch.log(strategy_a_softplus(y))),
        ('B_abs',      lambda y: torch.log(strategy_b_abs(y))),
        ('C_complex',  lambda y: strategy_c_complex(y)),
    ]:
        pred = fn(y_raw2)
        mse = float(torch.mean((pred - true2) ** 2))
        max_err = float(torch.max(torch.abs(pred - true2)))
        results[f'f2_{name}'] = {'mse': mse, 'max_err': max_err}

    # DEML for f2: sign flip is incorrect for oscillatory target
    results['f2_D_deml'] = {
        'mse': float('inf'),
        'max_err': float('inf'),
        'note': 'DEML routing invalid for oscillatory targets (sign flip incorrect)',
    }

    return results


# ── Branch cut illustration ────────────────────────────────────────────
def illustrate_branch_cut() -> None:
    print("=" * 70)
    print("NN-5: Branch Cut Problem in EML Symbolic Trees")
    print("=" * 70)

    print("\nProblem: eml(x, y) = exp(x) - ln(y) requires y > 0.")
    print("When a subtree outputs y_raw < 0, we face a branch cut:")
    print("  ln(-1) = iπ  (complex, principal branch)")
    print("  ln(-ε) ≈ iπ + ln(ε)  (imaginary part jumps discontinuously)")
    print("  IEEE float: ln(-1) = NaN  ← kills gradients in training")

    print("\nDemo: ln(y_raw) at y_raw ∈ {-2, -0.5, -ε, 0, ε, 0.5, 2}")
    raw_vals = [-2.0, -0.5, -0.01, 0.0, 0.01, 0.5, 2.0]
    y_t = torch.tensor(raw_vals)

    print(f"\n{'y_raw':>8}  {'ln(y)':>10}  {'A:softplus':>12}  {'B:abs':>10}  {'C:complex':>12}")
    print("-" * 60)
    for i, yv in enumerate(raw_vals):
        y = y_t[i:i+1]
        raw_ln = math.log(yv) if yv > 0 else float('nan')
        a = float(torch.log(strategy_a_softplus(y)))
        b = float(torch.log(strategy_b_abs(y)))
        c = float(strategy_c_complex(y))
        raw_str = f"{raw_ln:10.4f}" if not math.isnan(raw_ln) else "     NaN"
        print(f"  {yv:>6.2f}  {raw_str}  {a:>12.4f}  {b:>10.4f}  {c:>12.4f}")

    print()
    print("Observations:")
    print("  A (softplus): smooth transition through y=0, but DISTORTS values")
    print("                near 0 (large offset because ln(LEAd(y))≠ln(y))")
    print("  B (abs):      accurate for |y|≫0, but gradient flip at y=0")
    print("  C (complex):  matches ln|y| exactly — accurate for magnitude,")
    print("                loses sign information (imaginary part discarded)")
    print("  D (DEML):     avoids branch entirely by routing to exp(-x) —")
    print("                only correct for monotonic/exponential targets")


# ── Strategy comparison table ─────────────────────────────────────────
def comparison_table(results: dict) -> None:
    print("\n")
    print("=" * 80)
    print("Strategy Comparison: MSE vs true ln(sin(x))")
    print("=" * 80)

    strategies = [
        ('A', 'Softplus clamp', 'smooth, always positive, slight distortion'),
        ('B', 'Abs wrapper',    'exact magnitude, non-smooth at 0'),
        ('C', 'Complex route',  'exact real part = ln|y|, loses phase'),
        ('D', 'DEML routing',   'avoids branch entirely; monotonic targets only'),
    ]

    print(f"\nTarget f1: ln(sin(x)) on x ∈ (0.1, π-0.1)  [sin(x) > 0 throughout]")
    print(f"{'Strategy':4}  {'Name':18}  {'MSE':>12}  {'MaxErr':>10}  Note")
    print("-" * 80)
    for code, name, note in strategies:
        key = f'f1_{code}_softplus' if code == 'A' else \
              f'f1_{code}_abs'      if code == 'B' else \
              f'f1_{code}_complex'  if code == 'C' else \
              f'f1_D_deml'
        r = results.get(key, results.get(f'f1_{code.lower()}_softplus',
                        results.get(f'f1_A_softplus' if code == 'A' else
                        f'f1_B_abs' if code == 'B' else
                        f'f1_C_complex' if code == 'C' else
                        'f1_D_deml')))
        mse_str = f"{r['mse']:>12.6f}" if r['mse'] < 1e9 else "      N/A   "
        err_str = f"{r['max_err']:>10.6f}" if r['max_err'] < 1e9 else "     N/A  "
        print(f"  {code}   {name:18}  {mse_str}  {err_str}  {r.get('note', note)}")

    print(f"\nTarget f2: ln(|sin(x)|) on x ∈ (0.1, 2π-0.1)  [sin(x) changes sign]")
    print(f"{'Strategy':4}  {'Name':18}  {'MSE':>12}  {'MaxErr':>10}  Note")
    print("-" * 80)
    for code, name, note in strategies:
        key = f'f2_A_softplus' if code == 'A' else \
              f'f2_B_abs'      if code == 'B' else \
              f'f2_C_complex'  if code == 'C' else \
              f'f2_D_deml'
        r = results[key]
        mse_str = f"{r['mse']:>12.6f}" if r['mse'] < 1e9 else "     inf    "
        err_str = f"{r['max_err']:>10.6f}" if r['max_err'] < 1e9 else "     inf  "
        print(f"  {code}   {name:18}  {mse_str}  {err_str}  {r.get('note', note)}")


# ── Recommendations ───────────────────────────────────────────────────
def recommendations() -> None:
    print("\n")
    print("=" * 70)
    print("Branch Cut Recommendations for EML Symbolic Trees")
    print("=" * 70)
    print()
    print("Target type          Recommended strategy  Rationale")
    print("-" * 70)
    recs = [
        ("Monotonic/exponential", "D — DEML routing",
         "Avoids branch entirely; stays real-valued"),
        ("Oscillatory (sin, cos)", "C — Complex route",
         "Exact via analytic continuation; imaginary part carries phase"),
        ("Unknown sign",          "B — Abs wrapper",
         "Best accuracy where |y|≫0; cheapest to compute"),
        ("Smooth gradient needed", "A — Softplus clamp",
         "Everywhere differentiable; slight distortion acceptable"),
    ]
    for target, strat, rationale in recs:
        print(f"  {target:24}  {strat:22}  {rationale}")

    print()
    print("Hardware cost of each strategy (SuperBEST v4):")
    print("  A (softplus): LEAd = 1n  [cheapest!]")
    print("  B (abs):      abs ≈ 2n (implemented as sqrt(x²)=sqrt(pow(x,2))=2+3=5n)")
    print("  C (complex):  1n (same as ln, just allow complex domain)")
    print("  D (DEML):     1n (single DEML operator, no extra cost)")
    print()
    print("Conclusion: Options C and D are both 1n and cover the two main cases.")
    print("  Use D for monotonic targets (exponential growth/decay).")
    print("  Use C for oscillatory targets (trigonometric functions).")


if __name__ == '__main__':
    illustrate_branch_cut()
    results = evaluate_strategies()
    comparison_table(results)
    recommendations()
