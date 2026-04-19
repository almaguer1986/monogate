"""
S81 — Transcendence Reduction Memo

Map the tan(1) non-membership claim to known transcendence theory.
Which theorems could close the gap?

THE REDUCTION
=============

We want to show: tan(1) ∉ { Im(z)/Re(z) : z ∈ EML({1}, extended) }

Equivalently: no element of EML₁ has argument = 1 (radian).

STEP 1: What kind of number is tan(1)?
  - tan(1) = sin(1)/cos(1)
  - By Hermite-Lindemann: e^(2i) ≠ 1 (since 2i is not zero), so e^(2i) is transcendental.
  - More precisely: Lindemann-Weierstrass says e^α is transcendental for algebraic α ≠ 0.
  - Take α = 2i: algebraic (over ℚ). Then e^(2i) is transcendental.
  - e^(2i) = cos(2) + i·sin(2). Since it's transcendental, at least one of cos(2), sin(2) is transcendental.
  - Actually: Niven's theorem says sin(r°) is rational only for r=0,30,90,150,180,...
  - For r in radians: sin(1) is transcendental (Hermite-Lindemann: sin(1) = Im(e^i), e^i transcendental).
  - Therefore tan(1) = sin(1)/cos(1) is transcendental.

STEP 2: What kind of numbers are in EML₁?
  The EML₁ elements build up via:
    z_{n+1} = exp(z_n) − Log(z_m)
  Starting from 1 ∈ ℝ.

  Real parts: 1, e, exp(e), exp(exp(e)), ..., also e − exp(e), etc.
  Imaginary parts: 0 initially, then −π (first complex value), then
    multiples/combinations involving −π and other terms.

  Key: all imaginary parts of EML₁ elements are in the ℤ-linear span of {π, arctan(r)}
  for various real-part ratios r of previous elements.

STEP 3: Possible proof strategies

  STRATEGY A — Nesterenko's Theorem (1996):
    Nesterenko proved: π, e^π, and Γ(1/4) are algebraically independent over ℚ.
    Extended: for any algebraic α, e^(πα) is transcendental.
    Does this help? arg(z) = 1 requires Im(z)/Re(z) = tan(1), i.e., Im(z) = Re(z)·tan(1).
    We need Im(z) to be a specific transcendental. The question is whether
    the EML₁ imaginary parts can ever produce the value Re(z)·tan(1).

  STRATEGY B — Baker's Theorem on linear forms in logarithms:
    Baker (1966): If α₁,...,αₙ are nonzero algebraic numbers, then
      β₁ log α₁ + ... + βₙ log αₙ ≠ 0
    for algebraic β₁,...,βₙ not all zero.
    Relevance: EML₁ Im-parts are sums involving π (= −i·Log(−1)) and log values.
    The specific value Im(z)=tan(1)·Re(z) would require a transcendental linear combination.
    Baker doesn't directly apply since tan(1) itself is transcendental.

  STRATEGY C — Algebraic independence of {e, π}:
    Schanuel's conjecture (unproved): if z₁,...,zₙ are ℚ-linearly independent,
    then trdeg_ℚ(z₁,...,zₙ, e^z₁,...,e^zₙ) ≥ n.
    Applying to z₁=1, z₂=i: if 1 and i are ℚ-linearly independent (they are),
    then e, e^i are algebraically independent, so {e, cos(1), sin(1)} have trdeg ≥ 2.
    This would mean no algebraic relation between e and tan(1) = sin(1)/cos(1).
    But Schanuel is unproved!

  STRATEGY D — Direct analysis of EML Im-parts:
    Prove by induction that all Im(z) for z ∈ EML₁ lie in the set
      { r · π + Σᵢ aᵢ · arg(zᵢ) : r ∈ ℚ, aᵢ ∈ ℤ, zᵢ computed from exp/log }
    Then show this set doesn't contain ±1.
    This is a structural approach, not requiring Schanuel.

STEP 4: Most promising path
  Strategy D seems most tractable:
  (a) Characterize Im(EML₁) structurally.
  (b) Show 1 is not in this structural set.
  (c) The characterization might reduce to: Im(EML₁) ⊆ ℤ·π + arctan(ℚ(EML₁_reals)).

REDUCTION CHAIN:
  tan(1) ∉ T
  ⟺ no z ∈ EML₁ has arg(z) = ±1
  ⟸ no z ∈ EML₁ has Im(z)/Re(z) = ±tan(1)
  ⟸ Im(EML₁) ⊆ {multiples and combinations of π, not ±Re(z)·tan(1)}
  ⟸ [structural characterization theorem — not yet proved]
"""

import json
import math
from pathlib import Path

TRANSCENDENCE_MAP = {
    "session": "S81",
    "title": "Transcendence Reduction Memo",
    "tan1_is_transcendental": {
        "fact": "tan(1) is transcendental",
        "proof_sketch": "Hermite-Lindemann: e^i is transcendental (i is algebraic nonzero). "
                        "e^i = cos(1) + i·sin(1). Both cos(1) and sin(1) transcendental. "
                        "tan(1) = sin(1)/cos(1), ratio of transcendentals. "
                        "(Niven: only rational sin values at rational radian multiples of 2π are ±1,±1/2,0)",
        "value": math.tan(1),
    },
    "strategies": {
        "A_Nesterenko": {
            "theorem": "π, e^π, Γ(1/4) are algebraically independent (Nesterenko 1996)",
            "applicability": "INDIRECT — doesn't directly constrain arg of EML₁ elements",
            "gap": "Need to relate EML₁ imaginary parts to π-multiples; not obvious",
        },
        "B_Baker": {
            "theorem": "Linear forms in logarithms of algebraic numbers are nonzero (Baker 1966)",
            "applicability": "INDIRECT — EML₁ Im-parts may not be log of algebraics",
            "gap": "tan(1) is transcendental so Baker doesn't directly bound it",
        },
        "C_Schanuel": {
            "theorem": "Schanuel's conjecture (unproved): trdeg of {z_i, e^{z_i}} ≥ n for ℚ-lin-indep z_i",
            "applicability": "DIRECT if proved — would show e and tan(1) algebraically independent",
            "gap": "Unproved conjecture! Cannot use as axiom",
        },
        "D_Structural": {
            "theorem": "Characterize Im(EML₁) as closed under specific operations",
            "applicability": "MOST TRACTABLE — no transcendence theory needed if successful",
            "hypothesis": "Im(EML₁) ⊆ ℤ·π + sum of arg values of constructible elements",
            "gap": "Requires inductive characterization of Im-parts; S86 is needed for bounds",
        },
    },
    "recommended_path": "D_Structural",
    "reduction_chain": [
        "tan(1) ∉ T",
        "⟺ ∀ z ∈ EML₁, arg(z) ≠ ±1",
        "⟸ Im(EML₁) ⊆ ℤ·π (or some restricted set not containing ±Re(z)·tan(1))",
        "⟸ Structural induction on EML₁ depth [requires S86 branch-cut analysis]",
    ],
    "key_numbers": {
        "tan_1": math.tan(1),
        "sin_1": math.sin(1),
        "cos_1": math.cos(1),
        "pi": math.pi,
        "pi_approx_tan_1_ratio": math.pi / math.tan(1),
    },
    "literature": {
        "Hermite_1873": "e is transcendental",
        "Lindemann_1882": "π is transcendental; e^α transcendental for algebraic α≠0",
        "Baker_1966": "Linear forms in logarithms (lower bounds)",
        "Nesterenko_1996": "π, e^π, Γ(1/4) algebraically independent",
        "Niven_1956": "Rational values of trig functions at rational multiples of π",
        "Schanuel_1960s": "Conjecture on transcendence degree of exp field extensions",
    },
    "open_question": (
        "Does Strategy D close the gap? "
        "I.e., can we prove Im(EML₁) ⊆ ℤ·π purely structurally? "
        "If yes: i-unconstructibility follows without Schanuel."
    ),
}


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    out_path = results_dir / "s81_transcendence_map.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(TRANSCENDENCE_MAP, f, indent=2)

    print("=" * 60)
    print("S81 — Transcendence Reduction Memo")
    print("=" * 60)
    print()
    print(f"tan(1) = {TRANSCENDENCE_MAP['tan1_is_transcendental']['value']:.15f}")
    print(f"sin(1) = {TRANSCENDENCE_MAP['key_numbers']['sin_1']:.15f}")
    print(f"cos(1) = {TRANSCENDENCE_MAP['key_numbers']['cos_1']:.15f}")
    print()
    print("Strategies:")
    for k, v in TRANSCENDENCE_MAP["strategies"].items():
        print(f"  {k}: {v['applicability'][:60]}")
    print()
    print(f"Recommended: {TRANSCENDENCE_MAP['recommended_path']}")
    print()
    print("Reduction chain:")
    for step in TRANSCENDENCE_MAP["reduction_chain"]:
        print(f"  {step}")
    print()
    print(f"Open question: {TRANSCENDENCE_MAP['open_question'][:80]}...")
    print(f"Results: {out_path}")
