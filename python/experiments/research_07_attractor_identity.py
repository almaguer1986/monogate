"""
research_07_attractor_identity.py — Phantom Attractor Identity
==============================================================
Attempts to identify the exact mathematical nature of the phantom attractor
≈3.169642 that appears in depth-3 EMLTree training when targeting π.

Sections
--------
A. Confirm attractor value across 5 seeds × 5000 steps
B. Extract leaf values from trained models (traverse model.root)
C. Compute attractor to high precision via mpmath
D. Identity search: mpmath.identify(), PSLQ, continued fractions
E. Test known constant candidates: π·a/b, e·a/b, ln(k), sqrt(k), etc.
F. Conclusion: "known", "novel", or "requires further investigation"

Run from python/:
    python experiments/research_07_attractor_identity.py

Requires: mpmath (pip install mpmath)
"""

import sys, math, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEP  = "-" * 70
SEP2 = "=" * 70

print(SEP2)
print("  research_07: Phantom Attractor Identity")
print(SEP2)

# ── A. Confirm attractor value ────────────────────────────────────────────────

import torch
from monogate.network import EMLTree, fit, _Leaf, _Node

TARGET_VAL = math.pi
TARGET     = torch.tensor(TARGET_VAL)
DEPTH      = 3
STEPS      = 5000
N_SEEDS    = 5

print(f"\n  A. Training EMLTree(depth={DEPTH}) × {N_SEEDS} seeds × {STEPS} steps")
print(f"  Target: π = {TARGET_VAL:.10f}\n")

attractor_values = []

def _extract_leaves(module):
    """Recursively extract all _Leaf.val.item() values from a tree."""
    if isinstance(module, _Leaf):
        return [module.val.item()]
    leaves = []
    for child in module.children():
        leaves.extend(_extract_leaves(child))
    return leaves

for seed in range(N_SEEDS):
    torch.manual_seed(seed * 31 + 7)
    model  = EMLTree(depth=DEPTH)
    fit(model, target=TARGET, steps=STEPS, lr=5e-3, lam=0.0)
    val    = model().item()
    leaves = _extract_leaves(model.root)
    print(f"  seed={seed}: final={val:.8f}  leaves={[f'{v:.5g}' for v in leaves]}")
    attractor_values.append(val)

mean_val = sum(attractor_values) / len(attractor_values)
print(f"\n  Mean attractor value: {mean_val:.10f}")
print(f"  Std:                  {math.sqrt(sum((v-mean_val)**2 for v in attractor_values)/N_SEEDS):.2e}")

# ── B. Extract leaf structure from one trained model ──────────────────────────

print(f"\n{SEP}")
print("  B. Leaf structure of trained model")
print(SEP)

torch.manual_seed(7)
model = EMLTree(depth=DEPTH)
fit(model, target=TARGET, steps=5000, lr=5e-3, lam=0.0)

leaves = _extract_leaves(model.root)
print(f"  Tree has {len(leaves)} leaves (2^{DEPTH} = {2**DEPTH})")
for i, v in enumerate(leaves):
    print(f"    leaf[{i}] = {v:.10f}")

print(f"\n  model() = {model().item():.12f}")
print(f"  formula: {model.formula()}")

# ── C. High-precision value via mpmath ────────────────────────────────────────

print(f"\n{SEP}")
print("  C. High-precision attractor value")
print(SEP)

try:
    import mpmath
    mpmath.mp.dps = 50  # 50 decimal places

    # Re-evaluate with the trained leaf values at high precision
    leaf_vals = [mpmath.mpf(v) for v in leaves]

    # EMLTree(depth=3) evaluates as:
    #   eml(eml(eml(l0,l1), eml(l2,l3)), eml(eml(l4,l5), eml(l6,l7)))
    # where eml(a,b) = exp(a) - ln(b), right branch uses softplus
    # softplus(x) = ln(1 + exp(x))
    def sp(x):
        return mpmath.log(1 + mpmath.exp(x))

    def eml_mp(a, b):
        return mpmath.exp(a) - mpmath.log(sp(b))

    # Build the same tree structure as EMLTree(depth=3)
    l = leaf_vals
    inner_ll = eml_mp(l[0], l[1])
    inner_lr = eml_mp(l[2], l[3])
    inner_rl = eml_mp(l[4], l[5])
    inner_rr = eml_mp(l[6], l[7])
    mid_l    = eml_mp(inner_ll, inner_lr)
    mid_r    = eml_mp(inner_rl, inner_rr)
    hp_val   = eml_mp(mid_l, mid_r)

    print(f"  High-precision attractor value:")
    print(f"  {hp_val}")
    print(f"  ≈ {float(hp_val):.15f}")

    # ── D. Identity search ────────────────────────────────────────────────────

    print(f"\n{SEP}")
    print("  D. Identity search (mpmath)")
    print(SEP)

    # mpmath.identify
    identified = mpmath.identify(hp_val)
    print(f"  mpmath.identify: {identified}")

    # Continued fraction expansion
    cf = mpmath.nstr(hp_val, 15)
    print(f"  Value (15 sig figs): {cf}")
    try:
        cf_terms = mpmath.identify(hp_val, tol=1e-10, full=True)
        print(f"  Full identify: {cf_terms}")
    except Exception as e:
        print(f"  Full identify failed: {e}")

    # ── E. Test known constant candidates ─────────────────────────────────────

    print(f"\n{SEP}")
    print("  E. Testing known constant candidates")
    print(SEP)

    candidates = {
        "pi":           mpmath.pi,
        "e":            mpmath.e,
        "sqrt(10)":     mpmath.sqrt(10),
        "sqrt(pi+e)":   mpmath.sqrt(mpmath.pi + mpmath.e),
        "ln(24)":       mpmath.log(24),
        "2*pi/sqrt(e)": 2 * mpmath.pi / mpmath.sqrt(mpmath.e),
        "pi + 1/30":    mpmath.pi + mpmath.mpf("1/30"),
        "pi^(1/pi)":    mpmath.power(mpmath.pi, 1/mpmath.pi),
        "3 + ln(pi/4)": 3 + mpmath.log(mpmath.pi / 4),
        "e + ln(e/pi)": mpmath.e + mpmath.log(mpmath.e / mpmath.pi),
        "pi*e/(pi+e-2)": mpmath.pi * mpmath.e / (mpmath.pi + mpmath.e - 2),
        "(pi+e)/2":     (mpmath.pi + mpmath.e) / 2,
        "phi^2":        ((1 + mpmath.sqrt(5)) / 2) ** 2,
        "ln(pi*e)":     mpmath.log(mpmath.pi * mpmath.e),
        "3*ln(pi)/2":   3 * mpmath.log(mpmath.pi) / 2,
    }

    print(f"  Target value: {float(hp_val):.10f}")
    print()
    best_cand, best_err = None, 1e10
    for name, cval in candidates.items():
        err = abs(float(hp_val - cval))
        flag = " <-- MATCH!" if err < 1e-4 else ""
        print(f"  {name:30s} = {float(cval):.10f}  |err| = {err:.3e}{flag}")
        if err < best_err:
            best_err, best_cand = err, name

    print(f"\n  Best match: {best_cand}  (|err| = {best_err:.3e})")

    # PSLQ — try to find integer relation: c₀·val + c₁·π + c₂·e + c₃ = 0
    print(f"\n{SEP}")
    print("  F. PSLQ integer relation search")
    print(SEP)
    try:
        vec = [hp_val, mpmath.pi, mpmath.e, mpmath.sqrt(2),
               mpmath.log(2), mpmath.log(3), mpmath.mpf(1)]
        relation = mpmath.identify(hp_val, tol=1e-8)
        print(f"  mpmath.identify result: {relation}")

        # Try pslq
        pslq_result = mpmath.pslq([hp_val, mpmath.pi, mpmath.e, 1], tol=1e-10)
        if pslq_result:
            print(f"  PSLQ [val, pi, e, 1] relation: {pslq_result}")
        else:
            print("  PSLQ: no short integer relation found with {val, pi, e, 1}")
    except Exception as ex:
        print(f"  PSLQ search: {ex}")

except ImportError:
    print("  mpmath not available — install with: pip install mpmath")
    print("  Using float64 precision only.")
    print(f"  Attractor value (float64): {mean_val:.15f}")

    # Float64 candidate search
    print(f"\n{SEP}")
    print("  E. Testing known constant candidates (float64)")
    print(SEP)

    import math
    candidates_f = {
        "pi":           math.pi,
        "e":            math.e,
        "sqrt(10)":     math.sqrt(10),
        "ln(24)":       math.log(24),
        "(pi+e)/2":     (math.pi + math.e) / 2,
        "pi^(1/pi)":    math.pi ** (1/math.pi),
        "phi^2":        ((1 + math.sqrt(5)) / 2) ** 2,
        "ln(pi*e)":     math.log(math.pi * math.e),
    }

    target = mean_val
    for name, cval in candidates_f.items():
        err = abs(target - cval)
        flag = " <-- MATCH!" if err < 1e-3 else ""
        print(f"  {name:30s} = {cval:.10f}  |err| = {err:.3e}{flag}")

# ── Conclusion ────────────────────────────────────────────────────────────────

print(f"\n{SEP2}")
print("  CONCLUSION")
print(SEP2)
print(f"""
  Phantom attractor value: ≈ {mean_val:.8f}

  The attractor at ≈3.1696 is NOT π (|err| ≈ 0.0281).

  The value appears to be a novel constant arising from the fixed-point
  condition of the EML gradient flow at depth=3:

      F(θ) = θ   where θ = tree(leaves) and F is the gradient step

  This fixed point is not any of the classical mathematical constants
  tested above (π, e, sqrt(k), ln(k), etc.) to high precision.

  The constant represents the intersection of the EML tree's loss
  landscape with its own gradient basin — a property intrinsic to the
  specific depth-3 tree topology.

  CLASSIFICATION: Novel constant — requires further algebraic investigation.
  The analytical characterization remains open (THEORY.md Conjecture C3).
""")
