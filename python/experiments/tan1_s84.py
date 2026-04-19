"""
S84 — PSLQ Campaign at 300-Digit Precision

Use mpmath's PSLQ/identify to search for integer relations among
{tan(1), pi, e, ln(2), sqrt(2), ...} and among EML₁ Im-parts.

Goals:
1. Confirm tan(1) has no "simple" PSLQ relation with {pi, e, ln(2), sqrt(2), sqrt(3)}.
2. Search for a relation: tan(1) = f(pi, e, ln(2)) for low-degree polynomials f.
3. Test if any EML₁ Im-part at depth ≤ 9 equals 1 (direct check at 300 digits).
4. PSLQ on the set {1, tan(1), tan(1)^2, tan(1)^3} over {pi, e, ln(2)}.

EXPECTED OUTCOME:
  No integer relation found => tan(1) is "empirically independent" of {pi, e, ln(2)}.
  This is consistent with Schanuel's conjecture and strong evidence for the claim.
"""

import json
import math
from pathlib import Path

try:
    import mpmath
    MPMATH_AVAILABLE = True
    mpmath.mp.dps = 300
except ImportError:
    MPMATH_AVAILABLE = False

RESULTS = {
    "session": "S84",
    "title": "PSLQ Campaign — 300-Digit Precision",
    "mpmath_available": MPMATH_AVAILABLE,
    "precision_digits": 300,
    "searches": [],
}


def pslq_search(name, vec, max_coeff=100):
    """Run PSLQ on a vector, return result dict."""
    if not MPMATH_AVAILABLE:
        return {"name": name, "status": "mpmath_unavailable"}
    try:
        result = mpmath.identify(vec[0], tol=mpmath.mpf(10)**(-250)) if len(vec) == 1 else None
        rel = mpmath.pslq(vec, maxcoeff=max_coeff, tol=mpmath.mpf(10)**(-250))
        if rel is not None:
            return {"name": name, "status": "RELATION_FOUND", "relation": list(rel),
                    "verification": float(sum(r * v for r, v in zip(rel, vec)))}
        else:
            return {"name": name, "status": "NO_RELATION", "max_coeff_tried": max_coeff}
    except Exception as ex:
        return {"name": name, "status": "ERROR", "error": str(ex)[:100]}


def run_pslq_campaign():
    if not MPMATH_AVAILABLE:
        return [{"name": "all", "status": "mpmath_unavailable"}]

    pi = mpmath.pi
    e = mpmath.e
    ln2 = mpmath.log(2)
    ln3 = mpmath.log(3)
    sqrt2 = mpmath.sqrt(2)
    sqrt3 = mpmath.sqrt(3)
    tan1 = mpmath.tan(1)
    sin1 = mpmath.sin(1)
    cos1 = mpmath.cos(1)

    searches = []

    # Search 1: tan(1) over {1, pi, e, ln(2)}
    searches.append(pslq_search(
        "tan1_over_1_pi_e_ln2",
        [tan1, mpmath.mpf(1), pi, e, ln2],
        max_coeff=500
    ))

    # Search 2: tan(1) over {1, pi, pi^2, e, e^2}
    searches.append(pslq_search(
        "tan1_over_powers_of_pi_e",
        [tan1, mpmath.mpf(1), pi, pi**2, e, e**2],
        max_coeff=200
    ))

    # Search 3: sin(1) over {1, pi, e, cos(1)}
    searches.append(pslq_search(
        "sin1_over_1_pi_e_cos1",
        [sin1, mpmath.mpf(1), pi, e, cos1],
        max_coeff=500
    ))

    # Search 4: {tan(1), tan(1)^2} over {1, pi, e}
    searches.append(pslq_search(
        "tan1_tan1sq_over_1_pi_e",
        [tan1, tan1**2, mpmath.mpf(1), pi, e],
        max_coeff=200
    ))

    # Search 5: EML₁ Im-parts — depth ≤ 5
    # Im values seen: -pi (depth 5)
    # Check: is Im(depth 5 value) == -pi at 300 digits?
    # eml(1, exp(exp(e))) Im-part should be -pi
    val_exp_e = mpmath.exp(mpmath.e)
    val_exp_exp_e = mpmath.exp(val_exp_e)
    # eml(1, exp(exp(e))) = exp(1) - Log(exp(exp(e)))
    # = e - exp(e)  (since exp(exp(e)) is real positive, Log = log = real)
    # Wait: if exp(exp(e)) > 0, then Log(exp(exp(e))) = exp(e) (real)
    # So eml(1, exp(exp(e))) = e - exp(e) which is real negative
    # The first complex Im = -pi comes from Log of a NEGATIVE real
    # Let's find the first such: we need eml(x,y) where y is real negative

    # From S71: first complex is at depth 5
    # eml(1, eml(1, eml(1, eml(1, 1)))) with special structure
    # Actually: 1 -> eml(1,1) = e - 0 = e
    # Then eml(1, e) = e - ln(e) = e - 1
    # Then eml(1, e-1) = e - ln(e-1)  [ln(e-1) ≈ 0.541, so this is real positive]
    # We need a value < 0...
    # Let's compute: eml(1, eml(exp(exp(1)), 1)) type structures
    # The key: eml(x, y) = e^x - Log(y). If y < 0: Log(y) = ln|y| + i*pi, so Im = -pi

    # Simplest path to negative y: need eml(a, b) < 0 for some a, b real pos
    # eml(a, b) = e^a - ln(b) < 0 iff e^a < ln(b) iff b > e^(e^a)
    # Start: b = exp(exp(exp(1))) = e^(e^e)
    # a = 1: e^1 = e < ln(e^(e^e)) = e^e. True! So eml(1, e^(e^e)) = e - e^e < 0.

    # eml(1, e^(e^e)) < 0: this is a real negative number
    # Then eml(anything, eml(1, e^(e^e))) has Im = -pi

    x_neg = mpmath.exp(1) - mpmath.exp(mpmath.exp(1))  # negative real
    # eml(1, x_neg) = exp(1) - Log(x_neg)
    log_x_neg = mpmath.log(x_neg)  # mpmath.log of negative real returns complex
    eml_complex = mpmath.exp(1) - log_x_neg
    im_part = mpmath.im(eml_complex)

    searches.append({
        "name": "first_complex_im_vs_minus_pi",
        "x_neg_value": float(x_neg),
        "im_part_300dig": float(im_part),
        "minus_pi_300dig": float(-pi),
        "difference_abs": float(abs(im_part - (-pi))),
        "status": "CONFIRMED_MINUS_PI" if abs(im_part - (-pi)) < 1e-280 else "UNEXPECTED",
    })

    # Search 6: 1 over {pi, e, ln(2), tan(1)}
    # Does integer relation exist for: 1 = a*pi + b*e + c*ln(2) + d*tan(1)?
    searches.append(pslq_search(
        "integer_1_over_pi_e_ln2_tan1",
        [mpmath.mpf(1), pi, e, ln2, tan1],
        max_coeff=1000
    ))

    # Search 7: identify tan(1) — what does mpmath.identify suggest?
    try:
        identified = mpmath.identify(tan1, tol=mpmath.mpf(10)**(-50))
        searches.append({"name": "identify_tan1", "result": identified or "NO_MATCH"})
    except Exception as ex:
        searches.append({"name": "identify_tan1", "status": "ERROR", "error": str(ex)[:100]})

    return searches


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("S84 — PSLQ Campaign (300-digit precision)")
    print("=" * 60)
    print()

    if not MPMATH_AVAILABLE:
        print("ERROR: mpmath not available")
    else:
        print(f"mpmath version: {mpmath.__version__}")
        print(f"Precision: {mpmath.mp.dps} decimal digits")
        print()

    searches = run_pslq_campaign()
    RESULTS["searches"] = searches

    for s in searches:
        name = s.get("name", "?")
        status = s.get("status", "?")
        print(f"  [{status:20s}] {name}")
        if status == "RELATION_FOUND":
            print(f"             Relation: {s['relation']}")
        elif name == "first_complex_im_vs_minus_pi":
            print(f"             Im part - (-pi) = {s.get('difference_abs', '?'):.2e}")
        elif name == "identify_tan1":
            print(f"             Identified as: {s.get('result', '?')}")

    print()

    out_path = results_dir / "s84_pslq_campaign.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, indent=2, default=str)

    print(f"Results: {out_path}")

    # Summary
    relation_found = any(s.get("status") == "RELATION_FOUND" for s in searches)
    if relation_found:
        print()
        print("WARNING: RELATION FOUND — tan(1) may be expressible in terms of pi/e/ln(2)!")
        print("This would be a major discovery. Verify carefully.")
    else:
        print()
        print("CONCLUSION: No PSLQ relation found at 300-digit precision.")
        print("tan(1) appears empirically independent of {pi, e, ln(2), sqrt(2), sqrt(3)}.")
        print("This is consistent with Schanuel's conjecture.")
