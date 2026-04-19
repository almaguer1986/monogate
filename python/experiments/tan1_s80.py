"""
S80 — Precise Formal Statement of the tan(1) Non-Membership Claim

Canonical conjecture formulation, Lean-ready.

THE PRECISE CLAIM
=================

Let EML₁ = EML({1}, extended) ⊆ ℂ be the smallest set satisfying:
  (i)  1 ∈ EML₁
  (ii) If x ∈ EML₁ and y ∈ EML₁ and y ≠ 0, then exp(x) − Log(y) ∈ EML₁

where Log : ℂ∗ → ℂ is the principal-branch logarithm.

Define the argument set:
  ARG(EML₁) = {arg(z) : z ∈ EML₁, Re(z) ≠ 0}  ⊆ (−π, π]

where arg(z) = Im(Log(z)) = arctan(Im(z)/Re(z)) with appropriate sign adjustments.

Define the ratio set:
  T = {Im(z)/Re(z) : z ∈ EML₁, Re(z) ≠ 0, Im(z) ≠ 0}  ⊆ ℝ∗

Note: T = {tan(θ) : θ ∈ ARG(EML₁), θ ≠ 0} (modulo sign/quadrant bookkeeping).

CLAIM C (tan(1) Non-Membership):
  tan(1) ∉ T

EQUIVALENT REFORMULATIONS:
  C1: ∀ z ∈ EML₁, Im(z)/Re(z) ≠ tan(1)   (when Re(z) ≠ 0)
  C2: ∀ z ∈ EML₁, arg(z) ≠ 1              (principal branch, radian)
  C3: ∀ z ∈ EML₁, arg(z) ≠ −1

WHY THIS SUFFICES FOR i-UNCONSTRUCTIBILITY:
  To produce i = 0 + 1·i, we need Im(v) = 1 for some v ∈ EML₁.
  Propagation rule: Im(eml(x,y)) = exp(Re(x))·sin(Im(x)) − arg(y)
  Case x ∈ ℝ: Im(eml(x,y)) = −arg(y). For this to equal 1: arg(y) = −1.
  Case x complex: Im(eml(x,y)) = exp(Re(x))·sin(Im(x)) − arg(y) = 1.
    Subcases analyzed in S86 (branch-cut bounds).
  In all cases, reaching Im = 1 requires arg(y) = −1 (mod available Im-parts),
  which requires some constructible y with tan(arg(y)) = tan(−1) = −tan(1).
  Therefore: C ⟹ i ∉ EML₁.

LEAN-READY STATEMENT:
  theorem tan1_not_in_eml_ratio_set :
      ∀ z : ℂ, z ∈ EML_1 → z.re ≠ 0 →
      z.im / z.re ≠ Real.tan 1 := by sorry
  -- where EML_1 : Set ℂ is defined inductively in ExtendedClosure.lean

DISAMBIGUATION NOTES:
  1. We work in ℂ with principal-branch Log (arg ∈ (−π, π]).
  2. tan(1) ≈ 1.5574077... is transcendental (by Hermite-Lindemann).
  3. The claim is about EXACT equality, not approximation.
  4. We do NOT claim EML₁ ∩ {z : Im(z) = 1} = ∅ directly;
     we claim this via the reduction through arg(y) = −1.
  5. The reduction is complete for the "real x" case (S86 handles the rest).
"""

import math
import json
from pathlib import Path

CANONICAL_CLAIM = {
    "session": "S80",
    "title": "Canonical tan(1) Non-Membership Conjecture",
    "status": "CONJECTURE",
    "definitions": {
        "EML_1": (
            "Smallest subset of C containing 1 and closed under "
            "(x,y) |-> exp(x) - Log(y) for y != 0, "
            "where Log is the principal-branch complex logarithm."
        ),
        "ARG_set": "{ arg(z) : z in EML_1, Re(z) != 0 } ⊆ (-π, π]",
        "T_ratio_set": "{ Im(z)/Re(z) : z in EML_1, Re(z) != 0, Im(z) != 0 }",
    },
    "claim": "tan(1) ∉ T",
    "tan_1_value": math.tan(1),
    "equivalent_forms": {
        "C1": "∀ z ∈ EML₁, Im(z)/Re(z) ≠ tan(1)  [when Re(z)≠0]",
        "C2": "∀ z ∈ EML₁, arg(z) ≠ 1",
        "C3": "1 ∉ ARG(EML₁)",
    },
    "sufficiency": (
        "C ⟹ i ∉ EML₁ via the propagation rule: "
        "Im(eml(x,y)) = exp(Re x)·sin(Im x) − arg(y). "
        "For Im = 1 with real x: arg(y) = −1, requires tan(arg(y)) = −tan(1). "
        "S86 handles the full (x complex) case."
    ),
    "lean_statement": (
        "theorem tan1_not_in_eml_ratio_set :\n"
        "    ∀ z : ℂ, z ∈ EML_1 → z.re ≠ 0 →\n"
        "    z.im / z.re ≠ Real.tan 1 := by sorry"
    ),
    "key_numbers": {
        "tan_1": math.tan(1),
        "neg_tan_1": -math.tan(1),
        "pi": math.pi,
        "target_arg_radians": -1.0,
        "1_over_tan_1": 1.0 / math.tan(1),
    },
    "disambiguation": [
        "Principal-branch Log: arg ∈ (-π, π]",
        "tan(1) ≈ 1.5574077... is transcendental (Hermite-Lindemann)",
        "Claim is exact equality, not approximation",
        "Reduction is complete for real-x case; S86 handles complex-x",
    ],
}


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    out_path = results_dir / "s80_tan1_claim.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(CANONICAL_CLAIM, f, indent=2)

    print("=" * 60)
    print("S80 — Canonical tan(1) Non-Membership Claim")
    print("=" * 60)
    print()
    print(f"tan(1) = {CANONICAL_CLAIM['tan_1_value']:.15f}")
    print()
    print("CLAIM C: tan(1) ∉ { Im(z)/Re(z) : z ∈ EML₁, Re(z)≠0, Im(z)≠0 }")
    print()
    print("Equivalent forms:")
    for k, v in CANONICAL_CLAIM["equivalent_forms"].items():
        print(f"  {k}: {v}")
    print()
    print("Sufficiency for i-unconstructibility:")
    print(f"  {CANONICAL_CLAIM['sufficiency']}")
    print()
    print("Lean statement:")
    print(f"  {CANONICAL_CLAIM['lean_statement']}")
    print()
    print(f"Results: {out_path}")
