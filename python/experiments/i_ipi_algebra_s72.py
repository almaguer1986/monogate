"""
S72 — The iπ Algebra Session

Starting from iπ (the first complex value in extended grammar),
systematically compute all one-step eml combinations.

Key values available at this stage (N=5 context):
  - Real values from the closure: 1, e, e-1, exp(e), exp(e-1), 0, e-exp(e), ...
  - First complex value: a - iπ for some real a (from ln of a negative real)

Specific first complex value: eml(x_real, negative_real) = exp(x_real) - ln(neg)
  ln(neg) = ln|neg| + iπ
  so eml(x, neg) = exp(x) - ln|neg| - iπ  = (exp(x) - ln|neg|) - iπ

The FIRST negative real produced is at N=4:
  eml(1, exp(exp(e))) = e - ln(exp(exp(e))) = e - exp(e) ≈ 2.718 - 15.154 ≈ -12.436

So first complex at N=5:
  eml(z, e - exp(e)) where z is any N=4 value
  = exp(z) - ln(e - exp(e))
  = exp(z) - ln(exp(e) - e) - iπ     [since e - exp(e) < 0, ln gives iπ term]

Let c = e - exp(e) ≈ -12.436.
Let c_abs = exp(e) - e ≈ 12.436.

First complex = eml(1, c) = exp(1) - (ln(c_abs) + iπ) = e - ln(exp(e) - e) - iπ

Now: what does eml do to iπ?

Central computations:
  ipi = 0 + iπ  [imaginary unit times pi]

  eml(iπ, 1)  = exp(iπ) - ln(1) = -1 - 0 = -1  [REAL!]
  eml(1, iπ)  = exp(1) - Log(iπ) = e - (ln(π) + iπ/2)  [Log(iπ) = ln(π) + i·arg(iπ) = ln(π) + iπ/2]
  eml(iπ, iπ) = exp(iπ) - Log(iπ) = -1 - ln(π) - iπ/2

Key: exp(iπ) = -1 is the Euler identity — iπ produces -1 under exp!

Can we reach i from these?
  We need Im(result) = 1.
  eml(1, iπ) has Im = -π/2 (not 1)
  eml(iπ, iπ) has Im = -π/2 (not 1)

For Im = 1: need result where Im part = 1.
  From Log: Log(z) has Im = arg(z) ∈ (-π, π].
  arg(z) = 1 radian means z = |z|·e^{i·1}, i.e., z has argument exactly 1 radian.

  Is any constructible z from {1} at argument 1 radian?
  exp(iy) has argument y (for real y). So exp(1·i) = cos(1) + i·sin(1) has Im = sin(1) ≈ 0.841,
  NOT Im = 1.

  For Im = 1: we need a value z = a + i·1. When can eml(x, y) have Im exactly 1?
  Im(eml(x,y)) = Im(exp(x)) - Im(Log(y)) = exp(Re x)·sin(Im x) - arg(y)

  For this to equal 1: exp(Re x)·sin(Im x) - arg(y) = 1.

  The simplest case: Im x = 0 (x real), then Im(exp(x)) = 0.
  So: -arg(y) = 1, meaning arg(y) = -1.
  This means y = |y|·e^{-i·1} for some |y|.

  Do we have any constructible y with arg(y) = -1 exactly?
  arg(y) = -arctan(Im(y)/Re(y)) = -1 means Im(y)/Re(y) = -tan(1) ≈ -1.557.

  The question: is there a constructible y (from {1}) where Im(y)/Re(y) = -tan(1)?
  tan(1) is transcendental (Nesterenko 1996: π and e^π are algebraically independent,
  and tan(1) = sin(1)/cos(1) where sin(1), cos(1) are known transcendentals).

  There's no a priori reason to expect tan(1) to appear in EML({1}).

DIVISION BY π: The question of reaching i = iπ/π explicitly.
  iπ is constructible (at N=5). π is NOT directly constructible.
  π = Im(iπ) — extracting the imaginary part is not an EML operation.
  EML has no separate Re() or Im() operation.
  π would need to be constructed as a COMPLEX VALUE with Im=0 and Re=π.
  But π ≈ 3.14159... — is this in EML({1})?

  The constructible reals from {1} are: {1, e, e-1, exp(e), exp(e-1), ...}
  π is NOT of this form (it's not a combination of e, exp, log starting from 1
  in any known finite way). This is related to: is π in the EML closure of {1}?
"""

import cmath
import math
import json
from pathlib import Path


PI = math.pi


def fmt(z):
    """Format complex number for display."""
    z = complex(z)
    if abs(z.imag) < 1e-9:
        return f"{z.real:.6f}"
    return f"{z.real:.6f} + {z.imag:.6f}i"


def eml(x, y):
    if y == 0 or complex(y) == 0:
        return None
    try:
        return cmath.exp(complex(min(complex(x).real, 600), complex(x).imag)) - cmath.log(complex(y))
    except Exception:
        return None


def run_ipi_algebra():
    ipi = complex(0, PI)

    # Base values available (from N=1..5 analysis)
    base_reals = [1.0, math.e, math.e - 1, math.exp(math.e), math.exp(math.e - 1),
                  math.e - math.exp(math.e), 0.0]
    base_reals = [x for x in base_reals if x != 0]  # exclude 0 from y-slot

    results = []

    # One-step eml with ipi as one argument
    cases = [
        ("eml(ipi, 1)", eml(ipi, 1.0)),
        ("eml(1, ipi)", eml(1.0, ipi)),
        ("eml(ipi, ipi)", eml(ipi, ipi)),
        ("eml(ipi, e)", eml(ipi, math.e)),
        ("eml(e, ipi)", eml(math.e, ipi)),
        ("eml(ipi, -1)", eml(ipi, -1.0)),  # -1 = exp(ipi), this might be constructible
        ("eml(-1, ipi)", eml(-1.0, ipi)),
    ]

    for name, val in cases:
        if val is None:
            continue
        arg_z = cmath.phase(val)
        results.append({
            "expr": name,
            "value": fmt(val),
            "Re": round(val.real, 6),
            "Im": round(val.imag, 6),
            "Im_over_pi": round(val.imag / PI, 6),
            "arg_rad": round(arg_z, 6),
            "magnitude": round(abs(val), 6),
            "is_real": abs(val.imag) < 1e-9,
            "Im_is_1": abs(val.imag - 1.0) < 1e-6,
        })

    # Euler identity: exp(ipi) = -1
    euler_check = {
        "exp_ipi": fmt(cmath.exp(ipi)),
        "equals_neg1": abs(cmath.exp(ipi) + 1) < 1e-10,
    }

    # Log(ipi) analysis
    log_ipi = cmath.log(ipi)
    log_analysis = {
        "Log(ipi)": fmt(log_ipi),
        "magnitude_ipi": abs(ipi),
        "Re_Log_ipi": round(log_ipi.real, 6),
        "Im_Log_ipi": round(log_ipi.imag, 6),
        "Im_over_pi": round(log_ipi.imag / PI, 6),
        "note": "Log(ipi) = ln(pi) + i*pi/2 since arg(ipi) = pi/2",
    }

    # Can we reach i via division? i = ipi / pi
    # But pi is not a separate constructible value — it only appears as Im(ipi)
    # EML has no Im() extraction. We can't divide ipi by pi directly.
    pi_constructibility = {
        "question": "Is pi = Re(0 + i*pi) constructible as a REAL value from {1}?",
        "pi_value": PI,
        "closest_constructible_reals": sorted([
            abs(x - PI) for x in [1.0, math.e, math.e - 1, math.exp(math.e - 1),
                                   math.log(math.e), math.log(2)]
        ])[:3],
        "min_distance_to_pi": min(abs(x - PI) for x in [
            1.0, math.e, math.e - 1, math.exp(math.e - 1)
        ]),
        "conclusion": (
            "pi is NOT known to be EML-constructible from {1}. "
            "Even if it were, there's no EML division operation. "
            "The question i = ipi/pi is ill-posed within the EML grammar."
        ),
    }

    # Im=1 reachability analysis
    im1_analysis = {
        "question": "Can Im(z) = 1 for any constructible z?",
        "from_exp": {
            "route": "Im(exp(x)) = exp(Re x) * sin(Im x) = 1",
            "requirement": "exp(Re x) * sin(Im x) = 1",
            "example": "if Im x = pi/6, then sin(pi/6) = 0.5, need exp(Re x) = 2, i.e. Re x = ln(2)",
            "issue": "ln(2) is not known to be EML-constructible from {1}",
        },
        "from_log": {
            "route": "Im(Log(y)) = arg(y) = 1 requires y at argument exactly 1 radian",
            "requirement": "arg(y) = -1 for eml(real, y) to have Im = 1",
            "condition": "Im(y)/Re(y) = -tan(1) ≈ -1.5574",
            "issue": "tan(1) is transcendental; no constructible y is known to have this ratio",
        },
        "conclusion": "Im = 1 appears unreachable; proof requires transcendence argument",
    }

    return {
        "ipi_value": fmt(ipi),
        "euler_identity": euler_check,
        "log_ipi": log_analysis,
        "one_step_from_ipi": results,
        "pi_constructibility": pi_constructibility,
        "im1_analysis": im1_analysis,
    }


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    data = run_ipi_algebra()

    out_path = results_dir / "s72_ipi_algebra.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("=" * 60)
    print("S72 — iπ Algebra: one-step closure from iπ")
    print("=" * 60)
    print()
    print(f"Euler identity: exp(iπ) = {data['euler_identity']['exp_ipi']}  "
          f"[= -1: {data['euler_identity']['equals_neg1']}]")
    print(f"Log(iπ) = {data['log_ipi']['Log(ipi)']}")
    print()
    print("One-step eml combinations:")
    for r in data["one_step_from_ipi"]:
        flag = "  ← Im=1!" if r["Im_is_1"] else ""
        print(f"  {r['expr']:20s} = {r['value']:30s}  Im/pi={r['Im_over_pi']:8.4f}{flag}")
    print()
    print("Can we reach i directly?")
    print(f"  {data['pi_constructibility']['conclusion']}")
    print()
    print("Im=1 reachability:")
    print(f"  Via exp: {data['im1_analysis']['from_exp']['issue']}")
    print(f"  Via Log: {data['im1_analysis']['from_log']['issue']}")
    print(f"  Conclusion: {data['im1_analysis']['conclusion']}")
    print()
    print(f"Results: {out_path}")
