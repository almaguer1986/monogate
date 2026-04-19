"""
S83 — Gelfond-Schneider Mapping

Can the Gelfond-Schneider theorem be mapped onto the tan(1) claim?

GELFOND-SCHNEIDER THEOREM (1934):
  If α is algebraic and α ≠ 0, 1, and β is algebraic and irrational,
  then α^β is transcendental.

HERMITE-LINDEMANN (special case):
  e^α is transcendental for any nonzero algebraic α.
  (Take α = α, base = e which has α = 1 in ln sense.)

ATTEMPT TO APPLY TO tan(1):

  tan(1) = sin(1)/cos(1) = Im(e^i)/Re(e^i)

  e^i = cos(1) + i·sin(1) is transcendental by Hermite-Lindemann (i is algebraic nonzero).

  e^i is a SINGLE transcendental number (complex).

  Gelfond-Schneider says: if α ∈ algebraic \ {0,1}, β ∈ algebraic \ ℚ, then α^β transcendental.
  Key: α^β = exp(β · ln(α)).

  Can we write e^i = α^β for some algebraic α, β?
    e^i = e^(i·1). Here the "base" is e (transcendental), the "exponent" is i (algebraic).
    So e^i is NOT of the form α^β with algebraic α.

  What about: e^i = (e^(1/n))^(n·i)?
    e^(1/n) is transcendental (Hermite-Lindemann), so base is transcendental.
    Gelfond-Schneider doesn't apply.

WHAT GELFOND-SCHNEIDER DOES GIVE:
  2^√2 is transcendental. (Hilbert's 7th problem!)
  e^π = (-1)^(-i) is transcendental. (Classic corollary)
  i^i = e^(-π/2) is transcendental.

  These involve: algebraic base raised to algebraic irrational power.

THE CRITICAL QUESTION:
  Is tan(1) = α^β for some algebraic α, β?

  Suppose tan(1) = α^β. Then:
    sin(1)/cos(1) = α^β
    sin(1) = α^β · cos(1)

  We need both sin(1) and cos(1) to be algebraically related. But:
    sin(1)² + cos(1)² = 1 (always).
    e^i = cos(1) + i·sin(1) is transcendental (Lindemann).
    cos(1) and sin(1) are NOT both algebraic (if they were, e^i would be algebraic).
    Actually: by Lindemann-Weierstrass, {e^i} is transcendental, and cos(1), sin(1)
    are both transcendental (if one is algebraic, then e^(±i) = algebraic ± i·transcendental
    — contradiction since e^i is transcendental).

  So tan(1) is a ratio of two transcendentals, neither of which is algebraic.
  Gelfond-Schneider has nothing to say about such numbers directly.

THE ALGEBRAIC POWER LENS:
  Even if tan(1) ≠ α^β for algebraic α, β, we can still ask:
  Is tan(1) in the "algebraic closure of the transcendence basis containing e^i"?

  Under Schanuel: 1 and i are ℚ-linearly independent.
  So trdeg_ℚ(1, i, e, e^i) ≥ 2.
  Since 1, i ∈ ℚ(i) (algebraic), we get trdeg_ℚ(e, e^i) ≥ 2.
  I.e., e and e^i are algebraically independent over ℚ.
  This means cos(1) and sin(1) (= Re(e^i), Im(e^i)) — well, they satisfy
  the polynomial x² + y² = 1 together, so they're not algebraically independent.
  But neither is algebraic.

  Under Schanuel: sin(1) and cos(1) have no algebraic relation other than sin²+cos²=1.
  So tan(1) = sin(1)/cos(1) satisfies 1 + tan(1)² = 1/cos(1)², but we can't pin it
  to an algebraic power tower.

CONCLUSION:
  Gelfond-Schneider does NOT directly apply to tan(1) — it handles α^β with algebraic base.
  tan(1) is transcendental by Lindemann (indirect), not by Gelfond-Schneider.

  For our problem (tan(1) ∉ Im(EML₁)/Re(EML₁)), neither Baker nor Gelfond-Schneider
  suffices alone. The path remains: structural characterization of Im(EML₁).

  ONE USEFUL FACT: Under Schanuel, e and e^i are algebraically independent.
  This means: the "transcendence basis" for EML₁ values would need to include
  at least e and e^i = cos(1)+i·sin(1) as independent generators.
  Any element of EML₁ would then be an algebraic function of {e, e^i, further exp/log values}.
  The question: can arg(element) = 1 in this field? Under Schanuel, seemingly no —
  but we can't prove Schanuel.
"""

import json
import math
import cmath
from pathlib import Path

GELFOND_ANALYSIS = {
    "session": "S83",
    "title": "Gelfond-Schneider Mapping",
    "theorem": {
        "name": "Gelfond-Schneider 1934",
        "statement": "If a algebraic (not 0,1), b algebraic irrational, then a^b transcendental",
        "classic_examples": {
            "Hilbert_7th": "2^sqrt(2) is transcendental",
            "e_pi": "e^pi = (-1)^(-i) is transcendental",
            "i_i": "i^i = e^(-pi/2) is transcendental",
        },
    },
    "tan1_analysis": {
        "tan1_as_power": "tan(1) != alpha^beta for known algebraic alpha, beta",
        "reason": "tan(1) = sin(1)/cos(1); sin(1) and cos(1) are both transcendental",
        "by_lindemann": "e^i transcendental (Lindemann); e^i = cos(1)+i*sin(1); both parts transcendental",
        "gelfond_inapplicable": "G-S handles algebraic base; tan(1) has transcendental components",
    },
    "schanuel_connection": {
        "under_schanuel": "1 and i are Q-lin-indep => trdeg_Q(e, e^i) >= 2",
        "consequence": "e and e^i = cos(1)+i*sin(1) are algebraically independent",
        "for_tan1": "sin(1) and cos(1) satisfy sin^2+cos^2=1 but otherwise algebraically independent (Schanuel)",
        "conclusion": "tan(1) cannot be algebraically related to EML₁ real-part values (under Schanuel)",
        "caveat": "Schanuel is unproved",
    },
    "key_values": {
        "e_to_i_real": math.cos(1),
        "e_to_i_imag": math.sin(1),
        "tan_1": math.tan(1),
        "i_to_i": math.exp(-math.pi / 2),
        "e_to_pi": math.exp(math.pi),
    },
    "conclusion": (
        "Gelfond-Schneider does not directly constrain tan(1). "
        "tan(1) is transcendental by Lindemann (e^(i) transcendental, not by G-S). "
        "Under Schanuel: e and e^i are algebraically independent, suggesting tan(1) "
        "cannot be in EML₁'s ratio set — but Schanuel is unproved. "
        "Structural path (Strategy D) remains the best hope without Schanuel."
    ),
}


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    out_path = results_dir / "s83_gelfond_analysis.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(GELFOND_ANALYSIS, f, indent=2)

    print("=" * 60)
    print("S83 — Gelfond-Schneider Mapping")
    print("=" * 60)
    print()
    print("Classic G-S examples:")
    for k, v in GELFOND_ANALYSIS["theorem"]["classic_examples"].items():
        print(f"  {k}: {v}")
    print()
    print("tan(1) analysis:")
    print(f"  cos(1) = {math.cos(1):.15f}  [transcendental by Lindemann]")
    print(f"  sin(1) = {math.sin(1):.15f}  [transcendental by Lindemann]")
    print(f"  tan(1) = {math.tan(1):.15f}  [ratio of transcendentals]")
    print(f"  i^i    = {math.exp(-math.pi/2):.15f}  [transcendental by G-S]")
    print()
    print("Schanuel connection:")
    for k, v in GELFOND_ANALYSIS["schanuel_connection"].items():
        print(f"  {k}: {v[:70]}")
    print()
    print(f"Conclusion: {GELFOND_ANALYSIS['conclusion'][:100]}...")
    print(f"Results: {out_path}")
