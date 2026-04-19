"""
S86 — Branch-Cut Bounding Proof

Use the principal-branch arg ∈ (−π, π] constraint to bound
what imaginary parts and argument values are reachable in EML₁.

THE PROPAGATION RULE (exact):
  For z = eml(x, y) = exp(x) − Log(y):
    Re(z) = exp(Re(x))·cos(Im(x)) − Re(Log(y))
          = exp(Re(x))·cos(Im(x)) − ln|y|
    Im(z) = exp(Re(x))·sin(Im(x)) − Im(Log(y))
          = exp(Re(x))·sin(Im(x)) − arg(y)

  where arg(y) = Im(Log(y)) ∈ (−π, π] is the principal argument.

BOUNDING arg(z) FOR z ∈ EML₁:

  arg(z) = arctan(Im(z)/Re(z))  [when Re(z) > 0]
         = π + arctan(Im(z)/Re(z))  [when Re(z) < 0, Im(z) >= 0]
         = −π + arctan(Im(z)/Re(z))  [when Re(z) < 0, Im(z) < 0]

  For arg(z) = 1 (our target):
    Need Im(z)/Re(z) = tan(1) and Re(z) > 0.

  OR: arg(z) = 1 with Re(z) < 0 requires Im(z)/Re(z) = tan(1-π) = tan(1-π) ≈ -8.238.
    Let's check: tan(1 - π) = tan(1-3.14159...) = tan(-2.14159) ≈ -8.238.
    So this case requires Im/Re ≈ -8.238. Also possible to check.

CASE ANALYSIS FOR Im(z) = 1:

CASE 1: x ∈ ℝ (Im(x) = 0)
  Im(z) = exp(Re(x))·sin(0) − arg(y) = −arg(y)
  For Im(z) = 1: arg(y) = −1.
  This requires y ∈ EML₁ with arg(y) = −1.
  arg(y) = −1 iff Im(y)/Re(y) = tan(−1) = −tan(1) and Re(y) > 0
           OR Im(y)/Re(y) = tan(−1 + π) = tan(π−1) ≈ 6.165 and Re(y) < 0.
  So Case 1 reduces to: find y ∈ EML₁ with Im(y)/Re(y) = −tan(1) [Re(y)>0] or ≈6.165 [Re(y)<0].

CASE 2: Im(x) = π (or any Im(x) where sin(Im(x)) ≠ 0)
  Im(z) = exp(Re(x))·sin(Im(x)) − arg(y)
  For Im(z) = 1: arg(y) = exp(Re(x))·sin(Im(x)) − 1.
  This is a REAL equation. If exp(Re(x))·sin(Im(x)) − 1 ∈ (−π, π],
  then we need arg(y) = that value.

CASE 2a: Im(x) = −π (the first non-real value)
  sin(−π) = 0, so Im(z) = −arg(y). Same as Case 1!
  For Im(z) = 1: arg(y) = −1. Again.

CASE 2b: Im(x) = −π/2 (if achievable)
  sin(−π/2) = −1.
  Im(z) = −exp(Re(x)) − arg(y).
  For Im(z) = 1: −exp(Re(x)) − arg(y) = 1 ⟹ arg(y) = −1 − exp(Re(x)).
  But arg(y) ∈ (−π, π], and exp(Re(x)) > 0, so arg(y) < −1 < −π is IMPOSSIBLE
  unless exp(Re(x)) < π − 1 ≈ 2.14.
  I.e., Re(x) < ln(2.14) ≈ 0.76.
  In that case, arg(y) = −1 − exp(Re(x)) ∈ (−1 − e^0.76, −1) ≈ (−3.14, −1).
  For arg(y) ∈ (−π, π]: need arg(y) > −π, so exp(Re(x)) < π − 1.
  This is achievable in principle but requires Im(x) = −π/2 first.
  Is Im(x) = −π/2 achievable in EML₁? From our search: NOT SEEN at depth ≤ 5.

CASE 2c: Im(x) = π/2 (positive, if achievable)
  sin(π/2) = 1.
  Im(z) = exp(Re(x)) − arg(y).
  For Im(z) = 1: arg(y) = exp(Re(x)) − 1.
  Need arg(y) ∈ (−π, π], so exp(Re(x)) − 1 ∈ (−π, π], i.e., exp(Re(x)) ∈ (1−π, π+1).
  Since exp(Re(x)) > 0: need exp(Re(x)) ∈ (0, π+1), i.e., Re(x) < ln(π+1) ≈ 1.42.
  Is Im(x) = π/2 achievable? NOT SEEN at depth ≤ 5.

INDUCTIVE BOUND (key lemma, informal):

  CLAIM: For all z ∈ EML₁, Im(z) ∈ {0} ∪ {values in (−π, 0) ∪ (0, π)
                                        that are arctan-type combinations}.

  More precisely, by induction on depth:
    Depth 0: Im = 0.
    Depth 1: eml(1, 1) = e − 0 = e. Im = 0.
    ...
    Depth d+1: Im(eml(x,y)) = exp(Re(x))·sin(Im(x)) − arg(y).
      If Im(x) = 0: Im(eml) = −arg(y) ∈ (−π, π].
      If Im(x) ≠ 0: sin(Im(x)) factors in. The question is whether sin(Im(x)) ≠ 0.

  KEY OBSERVATION: All Im values seen at depth ≤ 5 lie in (−π, 0) or = 0.
    Specifically: Im ∈ {−π, and negative values close to −2.27, −2.26, etc.}
    These arg values are all in (−π, 0).

  If Im(EML₁) ⊆ (−π, 0] ∪ {0}:
    Then arg(z) ∈ (−π, 0] for all z ∈ EML₁ with Im(z) < 0.
    arg(z) = 1 > 0 would be impossible!
    This would PROVE Claim C!

  But is Im(EML₁) ⊆ (−π, 0]? Let's check:
    Im(eml(x,y)) = exp(Re(x))·sin(Im(x)) − arg(y)
    If Im(x) ∈ (−π, 0) and arg(y) ∈ (−π, 0):
      sin(Im(x)) ∈ (−sin(π), 0) ∪ (sin(0), sin(something)) = (−0,0) ... wait
      sin(θ) for θ ∈ (−π, 0): sin(θ) ∈ (−1, 0)... actually (−1, 0) ∪ {0}.
      So exp(Re(x))·sin(Im(x)) ∈ (−∞, 0).
      And −arg(y) ∈ (0, π] (since arg(y) ∈ (−π, 0)).
      So Im(eml(x,y)) = negative + positive. Sign is AMBIGUOUS.
      Could be positive!

  CONCLUSION: Im(EML₁) ⊆ (−π, 0] is NOT automatically preserved.
  A deeper analysis is needed. S89 will document this as the key open gap.
"""

import json
import math
import cmath
from pathlib import Path

TAN1 = math.tan(1)
PI = math.pi


def analyze_branch_cut_bounds():
    """Compute bounds from principal-branch constraints."""
    results = {}

    # Case 1: Im(x) = 0
    results["case1_real_x"] = {
        "description": "x real: Im(eml(x,y)) = -arg(y)",
        "for_im_z_equals_1": "Need arg(y) = -1",
        "arg_y_minus1_means": "Im(y)/Re(y) = -tan(1) (if Re(y) > 0) or Im(y)/Re(y) = tan(pi-1) (if Re(y) < 0)",
        "tan_neg1": math.tan(-1),
        "tan_pi_minus_1": math.tan(PI - 1),
        "conclusion": "Reduces to: does EML₁ contain element with arg = -1?",
    }

    # Case 2: Im(x) = -pi (first complex case)
    results["case2_im_x_minus_pi"] = {
        "description": "Im(x) = -pi: sin(-pi) = 0, so Im(eml) = -arg(y)",
        "same_as_case1": True,
        "conclusion": "Also reduces to arg(y) = -1",
    }

    # Case 3: Im(x) = -pi/2 (hypothetical)
    results["case3_im_x_minus_pi_half"] = {
        "description": "If Im(x) = -pi/2: Im(eml) = -exp(Re(x)) - arg(y)",
        "for_im_z_equals_1": "Need arg(y) = -1 - exp(Re(x))",
        "feasibility": "Only if exp(Re(x)) < pi - 1 ≈ 2.14, i.e., Re(x) < 0.76",
        "seen_in_eml1": False,
        "pi_minus_1": PI - 1,
        "ln_pi_minus_1": math.log(PI - 1),
    }

    # Key bound analysis
    results["principal_branch_bound"] = {
        "arg_range": "arg(z) = Im(Log(z)) in (-pi, pi]",
        "bound_on_im_eml": "|Im(eml(x,y))| = |exp(Re(x))*sin(Im(x)) - arg(y)|",
        "upper_bound": "exp(Re(x)) + pi (triangle inequality)",
        "observation": "If Im(x) in (-pi, 0) and arg(y) in (-pi, 0): Im(eml) could be positive or negative",
        "critical_gap": "Im(EML₁) ⊆ (-pi, 0] is NOT automatically preserved by the operator",
    }

    # Check: observed Im values at depth <= 5
    # From S85: args seen are all around -2.27 (which is in (-pi, 0))
    arg_seen_approx = -2.271520
    results["empirical_bound"] = {
        "max_im_seen_depth_5": 0.0,  # all Im values are 0 or negative
        "min_arg_seen_depth_5": arg_seen_approx,
        "min_arg_over_pi": arg_seen_approx / PI,
        "arg_equals_1_seen": False,
        "arg_equals_neg1_seen": False,
        "observation": "All arg values seen at depth <= 5 are negative, confirming Im(EML₁) subset (−pi, 0] at depth <= 5",
    }

    # Recursive analysis: can Im become positive?
    results["positive_im_analysis"] = {
        "formula": "Im(eml(x,y)) = exp(Re(x))*sin(Im(x)) - arg(y)",
        "for_positive_im": "Need exp(Re(x))*sin(Im(x)) > arg(y)",
        "if_arg_y_negative": "arg(y) < 0, so -arg(y) > 0. Even with sin(Im(x)) = 0: Im(eml) = -arg(y) > 0",
        "example": "x = 0, y with arg(y) = -1: Im(eml(0,y)) = 0 - (-1) = 1",
        "key_insight": "Im CAN become 1 via -arg(y) = 1, i.e., arg(y) = -1!",
        "conclusion": (
            "The positivity gap IS reachable — IF there exists y ∈ EML₁ with arg(y) = -1. "
            "This is exactly Claim C. The branch-cut bound does NOT rule it out automatically; "
            "it REDUCES the problem to: find (or rule out) y ∈ EML₁ with arg(y) = -1."
        ),
    }

    return results


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("S86 — Branch-Cut Bounding Proof")
    print("=" * 60)
    print()
    print(f"tan(1) = {TAN1:.15f}")
    print(f"tan(-1) = {math.tan(-1):.15f}")
    print(f"tan(pi-1) = {math.tan(PI-1):.15f}")
    print()

    analysis = analyze_branch_cut_bounds()

    print("PROPAGATION RULE: Im(eml(x,y)) = exp(Re(x))*sin(Im(x)) - arg(y)")
    print()
    print("Case analysis for Im(z) = 1:")
    print()
    for case, data in analysis.items():
        if case.startswith("case"):
            print(f"  {case}: {data['description'][:70]}")
            if "conclusion" in data:
                print(f"    => {data['conclusion'][:80]}")
    print()

    bp = analysis["principal_branch_bound"]
    print(f"Principal branch bound:")
    print(f"  {bp['critical_gap']}")
    print()

    pi_analysis = analysis["positive_im_analysis"]
    print("KEY FINDING:")
    print(f"  {pi_analysis['key_insight']}")
    print(f"  {pi_analysis['conclusion'][:120]}")
    print()

    BRANCH_RESULT = {
        "session": "S86",
        "title": "Branch-Cut Bounding Proof",
        "propagation_rule": "Im(eml(x,y)) = exp(Re(x))*sin(Im(x)) - arg(y)",
        "analysis": analysis,
        "main_finding": (
            "The branch-cut bound REDUCES Claim C to itself: "
            "Im(z) = 1 is achievable iff some y ∈ EML₁ has arg(y) = -1. "
            "arg(y) = -1 iff Im(y)/Re(y) = -tan(1). "
            "So the question is self-similar (fractal): does any EML₁ element have ratio -tan(1)? "
            "This IS Claim C, just shifted. The reduction is circular but necessary — "
            "it shows the claim is self-consistent and highlights the transcendence gap."
        ),
        "key_values": {
            "tan_1": TAN1,
            "tan_neg_1": math.tan(-1),
            "tan_pi_minus_1": math.tan(PI - 1),
            "pi": PI,
        },
        "next_step": "S87: Lean formalization of the reduction structure",
    }

    out_path = results_dir / "s86_branch_cut.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(BRANCH_RESULT, f, indent=2)

    print(f"Results: {out_path}")
