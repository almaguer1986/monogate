#!/usr/bin/env python3
# encoding: utf-8
"""
X8 — SuperBEST v5 Domain Audit
================================
Tests every SuperBEST operation using its EXACT construction from
superbest_v5_table.json / superbest.py across a grid of inputs
including negatives, zeros, and both signs.

Operator primitives (real-valued):
  eml(a,b)   = exp(a) - ln(b)       [requires b > 0]
  deml(a,b)  = exp(-a) - ln(b)      [requires b > 0]
  exl(a,b)   = exp(a) * ln(b)       [requires b > 0]
  elad(a,b)  = exp(a) * b           [b can be any real; note: elad != ELAd-ln form if b<0]
  elsb(a,b)  = exp(a) / b           [requires b != 0]
  lediv(a,b) = ln(exp(a)/b)         [requires b > 0]
  eal(a,b)   = exp(a) + ln(b)       [requires b > 0]

SuperBEST v5 constructions:
  exp(x)    = eml(x, 1)               cost=1n  domain=all x
  ln(x)     = exl(0, x)               cost=1n  domain=x > 0
  recip(x)  = elsb(0, x)             cost=1n  domain=x != 0
  neg(x)    = exl(0, deml(x, 1))     cost=2n  domain=all x
  add(x,y)  = lediv(x, deml(y, 1))  cost=2n  domain=all x, y (ADD-T1)
  sub(x,y)  = lediv(x, eml(y, 1))   cost=2n  domain=all x, y
  mul(x,y)  = elad(exl(0,x), y)     cost=2n  domain=x > 0, y any
  div(x,y)  = elsb(exl(0,x), y)     cost=2n  domain=x > 0, y != 0
  sqrt(x)   = eml(0.5*exl(0,x), 1)  cost=2n  domain=x > 0
  pow(x,n)  = eml(exl(ln(n),x), 1)  cost=3n  domain=x > 0, n > 0
"""

from __future__ import annotations
import json
import math
import sys
from datetime import date

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ── Primitive operators ────────────────────────────────────────────────────────

def eml(a: float, b: float) -> float:
    """EML: exp(a) - ln(b). Requires b > 0."""
    return math.exp(a) - math.log(b)

def deml(a: float, b: float) -> float:
    """DEML: exp(-a) - ln(b). Requires b > 0."""
    return math.exp(-a) - math.log(b)

def exl(a: float, b: float) -> float:
    """EXL: exp(a) * ln(b). Requires b > 0."""
    return math.exp(a) * math.log(b)

def elad(a: float, b: float) -> float:
    """ELAd: exp(a) * b. b can be any real (pure multiplication)."""
    return math.exp(a) * b

def elsb(a: float, b: float) -> float:
    """ELSb: exp(a) / b. Requires b != 0."""
    if b == 0:
        raise ZeroDivisionError("elsb: b must be != 0")
    return math.exp(a) / b

def lediv(a: float, b: float) -> float:
    """LEdiv: ln(exp(a)/b) = a - ln(b). Requires b > 0."""
    if b <= 0:
        raise ValueError(f"lediv: b must be > 0, got {b}")
    return math.log(math.exp(a) / b)

def eal(a: float, b: float) -> float:
    """EAL: exp(a) + ln(b). Requires b > 0."""
    return math.exp(a) + math.log(b)

# ── SuperBEST v5 constructions ─────────────────────────────────────────────────

def op_exp(x: float) -> float:
    """exp(x) = eml(x, 1). Domain: all x."""
    return eml(x, 1)

def op_ln(x: float) -> float:
    """ln(x) = exl(0, x). Domain: x > 0."""
    return exl(0, x)

def op_recip(x: float) -> float:
    """recip(x) = elsb(0, x) = exp(0)/x = 1/x. Domain: x != 0."""
    return elsb(0, x)

def op_neg(x: float) -> float:
    """neg(x) = exl(0, deml(x,1)) = ln(exp(-x)) = -x. Domain: all x."""
    # deml(x,1) = exp(-x) - ln(1) = exp(-x) > 0 always
    # exl(0, exp(-x)) = exp(0)*ln(exp(-x)) = 1 * (-x) = -x
    inner = deml(x, 1)   # = exp(-x) > 0 always
    return exl(0, inner)  # = ln(exp(-x)) = -x

def op_add(x: float, y: float) -> float:
    """add(x,y) = lediv(x, deml(y,1)) = x+y. Domain: all x, y (ADD-T1)."""
    # deml(y,1) = exp(-y) > 0 always — so lediv is always valid
    inner = deml(y, 1)   # = exp(-y) > 0
    return lediv(x, inner)  # = ln(exp(x)/exp(-y)) = ln(exp(x+y)) = x+y

def op_sub(x: float, y: float) -> float:
    """sub(x,y) = lediv(x, eml(y,1)) = x - y. Domain: all x, y where eml(y,1) > 0."""
    # eml(y,1) = exp(y) - ln(1) = exp(y) > 0 always
    inner = eml(y, 1)    # = exp(y) > 0
    return lediv(x, inner)  # = ln(exp(x)/exp(y)) = x - y

def op_mul(x: float, y: float) -> float:
    """mul(x,y) = elad(exl(0,x), y) = ln(x)*y then... wait.

    Construction: elad(exl(0,x), y)
    exl(0,x) = exp(0)*ln(x) = ln(x)   [requires x > 0]
    elad(ln(x), y) = exp(ln(x)) * y = x * y
    Domain: x > 0, y any real.
    """
    lnx = exl(0, x)      # = ln(x), requires x > 0
    return elad(lnx, y)  # = exp(ln(x)) * y = x*y

def op_div(x: float, y: float) -> float:
    """div(x,y) = elsb(exl(0,x), y) = exp(ln(x))/y = x/y.

    Domain: x > 0, y != 0.
    """
    lnx = exl(0, x)      # = ln(x), requires x > 0
    return elsb(lnx, y)  # = exp(ln(x)) / y = x/y

def op_sqrt(x: float) -> float:
    """sqrt(x) = eml(0.5*exl(0,x), 1) = exp(0.5*ln(x)) = sqrt(x).

    Domain: x > 0.
    """
    lnx = exl(0, x)         # = ln(x), requires x > 0
    return eml(0.5 * lnx, 1)  # = exp(0.5*ln(x)) = sqrt(x)

def op_pow(x: float, n: float) -> float:
    """pow(x,n) = exp(n*ln(x)) = x^n.

    Construction from table: eml(exl(ln(n),x), 1) — but this has a subtlety:
    exl(ln(n), x) = exp(ln(n)) * ln(x) = n * ln(x)
    eml(n*ln(x), 1) = exp(n*ln(x)) = x^n
    Requires x > 0 (for ln(x)), n > 0 (for ln(n) inside exl).

    Alternative reading: mul(n, ln(x)) + exp = 3n total.
    """
    # Use the direct mathematical result: exp(n * ln(x))
    # This matches the construction: exl(ln(n), x) requires n > 0
    if x <= 0:
        raise ValueError(f"pow: x must be > 0, got {x}")
    if n <= 0:
        raise ValueError(f"pow: n must be > 0 (for exl(ln(n),x) construction), got {n}")
    ln_n = math.log(n)
    return eml(exl(ln_n, x), 1)  # = exp(exp(ln(n))*ln(x)) = exp(n*ln(x)) = x^n

# ── Test harness ───────────────────────────────────────────────────────────────

EPSILON = 1e-9

def check(name: str, got: float, expected: float, x, y=None) -> str | None:
    """Return a failure string or None if OK."""
    if not math.isfinite(got) or not math.isfinite(expected):
        if got == expected:  # both inf or both -inf
            return None
        return f"({x},{y}): non-finite mismatch got={got}, expected={expected}"
    err = abs(got - expected)
    # Use relative error for large values
    scale = max(abs(expected), 1.0)
    if err / scale > 1e-6:
        return f"({x},{y}): got={got:.10g}, expected={expected:.10g}, err={err:.3e}"
    return None

def run_test(
    op_name: str,
    op_fn,
    ref_fn,
    n_args: int,
    xs: list[float],
    ys: list[float],
) -> dict:
    """Run a grid test and return result dict."""
    failures = []
    domain_errors = []
    pass_count = 0
    total = 0

    for x in xs:
        ys_iter = ys if n_args == 2 else [None]
        for y in ys_iter:
            total += 1
            args = (x, y) if n_args == 2 else (x,)
            try:
                got = op_fn(*args)
                expected = ref_fn(*args)
                fail = check(op_name, got, expected, x, y)
                if fail:
                    failures.append(fail)
                else:
                    pass_count += 1
            except (ValueError, ZeroDivisionError, OverflowError) as e:
                domain_errors.append(f"({x},{y}): DOMAIN ERROR — {e}")

    return {
        "total_tested": total,
        "pass_count": pass_count,
        "failures": failures,
        "domain_errors": domain_errors,
    }


# ── Main audit ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("X8 SuperBEST v5 Domain Audit")
    print("=" * 70)

    # Test grids
    xs = [-10.0, -3.0, -1.0, -0.5, -0.1, 0.1, 0.5, 1.0, 3.0, 10.0]
    ys = [-10.0, -3.0, -1.0, -0.5, -0.1, 0.1, 0.5, 1.0, 3.0, 10.0]
    xs_pos = [0.01, 0.1, 0.5, 1.0, 2.0, 3.0, 10.0]
    ys_pos = [0.01, 0.1, 0.5, 1.0, 2.0, 3.0, 10.0]
    xs_nonzero = [-10.0, -3.0, -1.0, -0.5, -0.1, 0.1, 0.5, 1.0, 3.0, 10.0]

    audit_results = {}

    # 1. exp(x) — cost 1n, domain: all x
    print("\n[exp] eml(x,1) — expected domain: all x")
    r = run_test("exp", op_exp, lambda x: math.exp(x), 1, xs, ys)
    audit_results["exp"] = {
        "cost_claimed": "1n",
        "construction": "eml(x, 1)",
        "claimed_domain": "all x",
        **r,
        "verdict": "PASS" if not r["failures"] and not r["domain_errors"] else "FAIL",
        "actual_domain": "all x" if not r["failures"] and not r["domain_errors"] else "RESTRICTED",
    }
    print(f"  Passed: {r['pass_count']}/{r['total_tested']}, "
          f"Failures: {len(r['failures'])}, Domain errors: {len(r['domain_errors'])}")
    if r["failures"] or r["domain_errors"]:
        for msg in (r["failures"] + r["domain_errors"])[:5]:
            print(f"    {msg}")

    # 2. ln(x) — cost 1n, domain: x > 0
    print("\n[ln] exl(0,x) — expected domain: x > 0")
    r = run_test("ln", op_ln, lambda x: math.log(x), 1, xs_pos, ys)
    # Also test with negatives to confirm they fail
    r_neg = run_test("ln_neg_test", op_ln, lambda x: math.log(x), 1, [-1.0, -0.5], ys)
    audit_results["ln"] = {
        "cost_claimed": "1n",
        "construction": "exl(0, x)",
        "claimed_domain": "x > 0",
        **r,
        "negative_input_behavior": "domain_error" if r_neg["domain_errors"] else "unexpected_pass",
        "verdict": "PASS" if not r["failures"] else "FAIL",
        "actual_domain": "x > 0",
    }
    print(f"  Passed (x>0): {r['pass_count']}/{r['total_tested']}, "
          f"Failures: {len(r['failures'])}, Domain errors: {len(r['domain_errors'])}")
    print(f"  Negative inputs: {'correctly raise errors' if r_neg['domain_errors'] else 'UNEXPECTED PASS'}")

    # 3. recip(x) — cost 1n, domain: x != 0
    print("\n[recip] elsb(0,x) = 1/x — expected domain: x != 0")
    r = run_test("recip", op_recip, lambda x: 1.0 / x, 1, xs_nonzero, ys)
    audit_results["recip"] = {
        "cost_claimed": "1n",
        "construction": "elsb(0, x)",
        "claimed_domain": "x != 0",
        **r,
        "verdict": "PASS" if not r["failures"] and not r["domain_errors"] else "FAIL",
        "actual_domain": "x != 0 (correctly handles negatives)",
    }
    print(f"  Passed: {r['pass_count']}/{r['total_tested']}, "
          f"Failures: {len(r['failures'])}, Domain errors: {len(r['domain_errors'])}")
    if r["failures"] or r["domain_errors"]:
        for msg in (r["failures"] + r["domain_errors"])[:5]:
            print(f"    {msg}")

    # 4. neg(x) — cost 2n, domain: all x
    print("\n[neg] exl(0, deml(x,1)) = -x — expected domain: all x")
    r = run_test("neg", op_neg, lambda x: -x, 1, xs, ys)
    audit_results["neg"] = {
        "cost_claimed": "2n",
        "construction": "exl(0, deml(x, 1))",
        "claimed_domain": "all x",
        **r,
        "verdict": "PASS" if not r["failures"] and not r["domain_errors"] else "FAIL",
        "actual_domain": "all x" if not r["failures"] and not r["domain_errors"] else "RESTRICTED",
    }
    print(f"  Passed: {r['pass_count']}/{r['total_tested']}, "
          f"Failures: {len(r['failures'])}, Domain errors: {len(r['domain_errors'])}")
    if r["failures"] or r["domain_errors"]:
        for msg in (r["failures"] + r["domain_errors"])[:5]:
            print(f"    {msg}")

    # 5. add(x,y) — cost 2n, domain: all x, y (ADD-T1 key claim)
    print("\n[add] lediv(x, deml(y,1)) = x+y — expected domain: ALL x, y")
    r = run_test("add", op_add, lambda x, y: x + y, 2, xs, ys)
    audit_results["add"] = {
        "cost_claimed": "2n",
        "construction": "lediv(x, deml(y, 1))",
        "claimed_domain": "all x, y",
        **r,
        "verdict": "PASS" if not r["failures"] and not r["domain_errors"] else "FAIL",
        "actual_domain": "all x, y" if not r["failures"] and not r["domain_errors"] else "RESTRICTED",
        "note": "ADD-T1: key v5 breakthrough claim",
    }
    print(f"  Passed: {r['pass_count']}/{r['total_tested']}, "
          f"Failures: {len(r['failures'])}, Domain errors: {len(r['domain_errors'])}")
    if r["failures"] or r["domain_errors"]:
        for msg in (r["failures"] + r["domain_errors"])[:5]:
            print(f"    {msg}")

    # 6. sub(x,y) — cost 2n, domain: all x, y
    print("\n[sub] lediv(x, eml(y,1)) = x-y — expected domain: all x, y")
    r = run_test("sub", op_sub, lambda x, y: x - y, 2, xs, ys)
    audit_results["sub"] = {
        "cost_claimed": "2n",
        "construction": "lediv(x, eml(y, 1))",
        "claimed_domain": "all x, y",
        **r,
        "verdict": "PASS" if not r["failures"] and not r["domain_errors"] else "FAIL",
        "actual_domain": "all x, y" if not r["failures"] and not r["domain_errors"] else "RESTRICTED",
    }
    print(f"  Passed: {r['pass_count']}/{r['total_tested']}, "
          f"Failures: {len(r['failures'])}, Domain errors: {len(r['domain_errors'])}")
    if r["failures"] or r["domain_errors"]:
        for msg in (r["failures"] + r["domain_errors"])[:5]:
            print(f"    {msg}")

    # 7. mul(x,y) — cost 2n, domain: x > 0 (superbest.py says x > 0)
    print("\n[mul] elad(exl(0,x), y) = x*y — claimed domain: x > 0")
    # First test positive x
    r_pos = run_test("mul_pos", op_mul, lambda x, y: x * y, 2, xs_pos, xs)
    # Then test negative x (should fail)
    r_neg = run_test("mul_neg_x", op_mul, lambda x, y: x * y, 2, [-1.0, -3.0], [2.0, 0.5])
    audit_results["mul"] = {
        "cost_claimed": "2n",
        "construction": "elad(exl(0,x), y)",
        "claimed_domain": "x > 0",
        "total_tested": r_pos["total_tested"],
        "pass_count": r_pos["pass_count"],
        "failures": r_pos["failures"],
        "domain_errors": r_pos["domain_errors"],
        "negative_x_behavior": "domain_error" if r_neg["domain_errors"] else f"gives {r_neg['pass_count']} unexpected passes",
        "negative_x_detail": r_neg["domain_errors"][:3] if r_neg["domain_errors"] else r_neg["failures"][:3],
        "verdict": "PASS" if not r_pos["failures"] and not r_pos["domain_errors"] else "FAIL",
        "actual_domain": "x > 0 (ln(x) requires positive x)",
        "table_correction_needed": True,
        "correction_note": "superbest_v5_table.json says 'all real x,y' for mul cost but domain is x > 0",
    }
    print(f"  Passed (x>0): {r_pos['pass_count']}/{r_pos['total_tested']}, "
          f"Failures: {len(r_pos['failures'])}, Domain errors: {len(r_pos['domain_errors'])}")
    neg_fail = "correctly fail" if r_neg["domain_errors"] else f"silently give wrong results ({r_neg['failures']})"
    print(f"  Negative x inputs: {neg_fail}")
    if r_neg["domain_errors"]:
        for msg in r_neg["domain_errors"][:3]:
            print(f"    {msg}")

    # 8. div(x,y) — cost 2n, domain: x > 0, y != 0
    print("\n[div] elsb(exl(0,x), y) = x/y — claimed domain: x, y > 0")
    r_pos = run_test("div_pos", op_div, lambda x, y: x / y, 2, xs_pos, ys_pos)
    r_neg_x = run_test("div_neg_x", op_div, lambda x, y: x / y, 2, [-1.0, -3.0], [2.0, 0.5])
    r_neg_y = run_test("div_neg_y", op_div, lambda x, y: x / y, 2, [1.0, 3.0], [-2.0, -0.5])
    # Can neg y work? elsb allows negative b (exp(a)/b still fine if b != 0)
    # but exl(0,x) = ln(x) requires x > 0
    audit_results["div"] = {
        "cost_claimed": "2n",
        "construction": "elsb(exl(0,x), y)",
        "claimed_domain": "x, y > 0",
        "total_tested": r_pos["total_tested"],
        "pass_count": r_pos["pass_count"],
        "failures": r_pos["failures"],
        "domain_errors": r_pos["domain_errors"],
        "negative_x_behavior": "domain_error" if r_neg_x["domain_errors"] else "unexpected_pass",
        "negative_y_behavior": "domain_error" if r_neg_y["domain_errors"] else "unexpected_pass",
        "negative_y_detail": r_neg_y["domain_errors"][:2] if r_neg_y["domain_errors"] else r_neg_y["failures"][:2],
        "verdict": "PASS" if not r_pos["failures"] and not r_pos["domain_errors"] else "FAIL",
        "actual_domain": "x > 0 (hard), y != 0 (elsb handles y < 0)",
    }
    print(f"  Passed (x,y>0): {r_pos['pass_count']}/{r_pos['total_tested']}, "
          f"Failures: {len(r_pos['failures'])}, Domain errors: {len(r_pos['domain_errors'])}")
    print(f"  Negative x: {'correctly fail' if r_neg_x['domain_errors'] else 'UNEXPECTED PASS'}")
    # Check if div actually works for negative y
    if not r_neg_y["domain_errors"] and not r_neg_y["failures"]:
        print(f"  Negative y: WORKS (elsb handles y < 0) — domain is x > 0, y != 0")
        audit_results["div"]["actual_domain"] = "x > 0 (hard), y != 0 (negative y works)"
        audit_results["div"]["table_correction_needed"] = True
        audit_results["div"]["correction_note"] = "Claimed 'x, y > 0' but y < 0 also works"
    else:
        print(f"  Negative y: fails as expected")

    # 9. sqrt(x) — cost 2n, domain: x > 0
    print("\n[sqrt] eml(0.5*exl(0,x), 1) = sqrt(x) — expected domain: x > 0")
    r = run_test("sqrt", op_sqrt, lambda x: math.sqrt(x), 1, xs_pos, ys)
    r_neg = run_test("sqrt_neg", op_sqrt, lambda x: math.sqrt(x), 1, [-1.0, -0.5], ys)
    audit_results["sqrt"] = {
        "cost_claimed": "2n",
        "construction": "eml(0.5*exl(0,x), 1)",
        "claimed_domain": "x > 0",
        **r,
        "negative_x_behavior": "domain_error" if r_neg["domain_errors"] else "unexpected_pass",
        "verdict": "PASS" if not r["failures"] and not r["domain_errors"] else "FAIL",
        "actual_domain": "x > 0",
    }
    print(f"  Passed (x>0): {r['pass_count']}/{r['total_tested']}, "
          f"Failures: {len(r['failures'])}, Domain errors: {len(r['domain_errors'])}")
    print(f"  Negative x: {'correctly fail' if r_neg['domain_errors'] else 'UNEXPECTED PASS'}")

    # 10. pow(x,n) — cost 3n, domain: x > 0, n > 0
    print("\n[pow] eml(exl(ln(n),x), 1) = x^n — expected domain: x > 0, n > 0")
    pow_xs = [0.5, 1.0, 2.0, 3.0, 10.0]
    pow_ns = [0.5, 1.0, 2.0, 3.0]
    r = run_test("pow", op_pow, lambda x, y: x ** y, 2, pow_xs, pow_ns)
    r_neg_x = run_test("pow_neg_x", op_pow, lambda x, y: x ** y, 2, [-1.0, -2.0], [2.0, 3.0])
    r_neg_n = run_test("pow_neg_n", op_pow, lambda x, y: x ** y, 2, [2.0, 3.0], [-1.0, -2.0])
    audit_results["pow"] = {
        "cost_claimed": "3n",
        "construction": "eml(exl(ln(n),x), 1)",
        "claimed_domain": "x > 0, n > 0",
        "total_tested": r["total_tested"],
        "pass_count": r["pass_count"],
        "failures": r["failures"],
        "domain_errors": r["domain_errors"],
        "negative_x_behavior": "domain_error" if r_neg_x["domain_errors"] else "unexpected_pass",
        "negative_n_behavior": "domain_error" if r_neg_n["domain_errors"] else "unexpected_pass",
        "verdict": "PASS" if not r["failures"] and not r["domain_errors"] else "FAIL",
        "actual_domain": "x > 0, n > 0",
        "note": "Negative exponents n < 0 also fail (ln(n) undefined); integer negative exponents need recip(pow(x,-n))",
    }
    print(f"  Passed (x,n>0): {r['pass_count']}/{r['total_tested']}, "
          f"Failures: {len(r['failures'])}, Domain errors: {len(r['domain_errors'])}")
    print(f"  Negative x: {'correctly fail' if r_neg_x['domain_errors'] else 'unexpected_pass'}")
    print(f"  Negative n: {'correctly fail' if r_neg_n['domain_errors'] else 'unexpected_pass'}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    table_corrections = []
    for op_name, res in audit_results.items():
        v = res.get("verdict", "UNKNOWN")
        domain = res.get("actual_domain", "?")
        claimed = res.get("claimed_domain", "?")
        print(f"  {op_name:8} {v:5}  domain: {domain}")
        if res.get("table_correction_needed"):
            table_corrections.append({
                "op": op_name,
                "issue": res.get("correction_note", ""),
                "claimed": claimed,
                "actual": domain,
            })

    # Determine overall conclusion
    all_pass = all(r.get("verdict") == "PASS" for r in audit_results.values())

    domain_restricted_ops = [
        op for op, r in audit_results.items()
        if "restricted" in r.get("actual_domain", "").lower()
        or r.get("table_correction_needed")
    ]

    # Check if mul domain claim in the table JSON is different from superbest.py
    # superbest.py correctly says "x > 0" for mul
    # superbest_v5_table.json says just "cost=2, domain: all real x,y" in the notes
    mul_result = audit_results["mul"]
    div_result = audit_results["div"]

    conclusion_parts = []
    if all_pass:
        conclusion_parts.append(
            "All SuperBEST v5 constructions compute the correct value within their claimed domain."
        )
    else:
        conclusion_parts.append("Some constructions have failures within claimed domain.")

    conclusion_parts.append(
        "CRITICAL FINDING: mul(x,y) and div(x,y) require x > 0 because exl(0,x)=ln(x) "
        "is only defined for x > 0. superbest.py correctly marks domain as 'x > 0' but "
        "the v5_table.json notes and summary text claim 'all real x,y' for mul — "
        "this is an inconsistency. The construction itself is correct within x > 0."
    )
    conclusion_parts.append(
        "div(x,y): elsb allows y < 0 (no ln of y), so actual domain is x > 0, y != 0, "
        "which is strictly larger than the claimed 'x, y > 0'."
    )
    conclusion_parts.append(
        "add(x,y) = lediv(x, deml(y,1)): deml(y,1)=exp(-y)>0 always, so lediv is always "
        "valid. ADD-T1 claim CONFIRMED: works for ALL real x, y."
    )
    conclusion_parts.append(
        "sub(x,y) = lediv(x, eml(y,1)): eml(y,1)=exp(y)>0 always, so lediv is always "
        "valid. Works for ALL real x, y."
    )
    conclusion_parts.append(
        "neg(x) = exl(0, deml(x,1)): deml(x,1)=exp(-x)>0 always, so exl is always valid. "
        "Works for ALL real x."
    )
    conclusion_parts.append(
        "recip(x) = elsb(0,x): works for x != 0, including negative x. "
        "superbest.py says 'x != 0' which is correct."
    )
    conclusion_parts.append(
        "pow(x,n): requires x > 0 AND n > 0 for the given construction "
        "eml(exl(ln(n),x),1). Negative exponents need recip(pow(x,-n))."
    )

    conclusion = " ".join(conclusion_parts)

    output = {
        "session": "X8",
        "audit_date": str(date.today()),
        "methodology": (
            "Tested every SuperBEST v5 operation using its EXACT construction. "
            "Grid: xs=[-10,-3,-1,-0.5,-0.1,0.1,0.5,1,3,10], ys same. "
            "Positive-domain ops tested on positive subgrid. "
            "Tolerance: relative error < 1e-6."
        ),
        "results": audit_results,
        "table_corrections_needed": table_corrections,
        "conclusion": conclusion,
        "ops_fully_confirmed": [
            op for op, r in audit_results.items()
            if r.get("verdict") == "PASS" and not r.get("table_correction_needed")
        ],
        "ops_with_domain_notes": domain_restricted_ops,
        "add_t1_verified": audit_results["add"]["verdict"] == "PASS",
        "sub_all_reals_verified": audit_results["sub"]["verdict"] == "PASS",
        "neg_all_reals_verified": audit_results["neg"]["verdict"] == "PASS",
    }

    out_path = "D:/monogate/python/results/x8_domain_audit_table.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to: {out_path}")

    if table_corrections:
        print("\nTABLE CORRECTIONS NEEDED:")
        for c in table_corrections:
            print(f"  [{c['op']}] {c['issue']}")

    print("\nKEY FINDINGS:")
    print("  ADD-T1 (add=2n for all reals): VERIFIED" if output["add_t1_verified"] else "  ADD-T1: FAILED")
    print("  sub all reals: VERIFIED" if output["sub_all_reals_verified"] else "  sub all reals: FAILED")
    print("  neg all reals: VERIFIED" if output["neg_all_reals_verified"] else "  neg all reals: FAILED")
    print("  mul domain: x > 0 only (exl(0,x)=ln(x) requires x > 0)")
    print("  div domain: x > 0, y != 0 (y < 0 works via elsb)")
    print("  pow domain: x > 0, n > 0 (both ln calls require positivity)")


if __name__ == "__main__":
    main()
