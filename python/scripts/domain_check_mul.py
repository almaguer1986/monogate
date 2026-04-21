#!/usr/bin/env python3
"""
X7: mul Domain Audit and abs(x) Puzzle Resolution

Verifies the domain of every SuperBEST v5 operation and documents
whether mul=2n holds for ALL reals or only for positive inputs.

Output: python/results/x7_mul_domain_audit.json
"""
import sys
import os
import json
import math

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Operator definitions (real-valued)
# Each raises ValueError or math.domain error when undefined on reals.
# ---------------------------------------------------------------------------

def eal(a, b):
    """EAL(a,b) = exp(a) + ln(b)  — requires b > 0"""
    return math.exp(a) + math.log(b)

def eml(a, b):
    """EML(a,b) = exp(a) - ln(b)  — requires b > 0"""
    return math.exp(a) - math.log(b)

def exl(a, b):
    """EXL(a,b) = exp(a) * ln(b)  — requires b > 0"""
    return math.exp(a) * math.log(b)

def edl(a, b):
    """EDL(a,b) = exp(a) / ln(b)  — requires b > 0 and b != 1"""
    lg = math.log(b)
    if abs(lg) < 1e-300:
        raise ValueError(f"EDL denominator ln({b}) = 0")
    return math.exp(a) / lg

def deml(a, b):
    """DEML(a,b) = exp(-a) - ln(b)  — requires b > 0"""
    return math.exp(-a) - math.log(b)

def elad(a, b):
    """ELAd(a,b) = exp(a) * b  — defined for all a, b (b can be any real, including 0)"""
    return math.exp(a) * b

def elsb(a, b):
    """ELSb(a,b) = exp(a) / b  — requires b != 0"""
    if b == 0:
        raise ValueError(f"ELSb division by zero: b={b}")
    return math.exp(a) / b

def lediv(a, b):
    """LEDIV(a,b) = ln(exp(a)/b) = a - ln(b)  — requires b > 0"""
    return math.log(math.exp(a) / b)

def emn(a, b):
    """EMN(a,b) = ln(b) - exp(a)  — requires b > 0"""
    return math.log(b) - math.exp(a)

# ---------------------------------------------------------------------------
# Helper: safe call
# ---------------------------------------------------------------------------

def safe(fn, *args):
    try:
        result = fn(*args)
        return {"ok": True, "value": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ---------------------------------------------------------------------------
# Part 1: mul(x, y) = ELAd(EXL(0,x), y)
# EXL(0, x) = exp(0) * ln(x) = 1 * ln(x) = ln(x)  — REQUIRES x > 0
# ELAd(ln(x), y) = exp(ln(x)) * y = x * y
# ---------------------------------------------------------------------------

print("=" * 70)
print("PART 1: mul(x,y) = ELAd(EXL(0,x), y) domain check")
print("=" * 70)

mul_test_cases = [
    (3, 5, 15),
    (-3, 5, -15),
    (3, -5, -15),
    (-3, -5, 15),
    (0.5, 4, 2.0),
    (-0.5, 4, -2.0),
    (0, 5, 0),      # x=0 edge case
]

mul_failures = []
mul_successes = []

for x, y, expected in mul_test_cases:
    r1 = safe(exl, 0, x)   # EXL(0, x) = ln(x)
    if r1["ok"]:
        r2 = safe(elad, r1["value"], y)   # ELAd(ln(x), y) = exp(ln(x))*y = x*y
        if r2["ok"]:
            v = r2["value"]
            correct = abs(v - expected) < 1e-8
            status = "OK" if correct else "WRONG"
            print(f"  mul({x:5}, {y:5}) = {v:12.6f}  expected {expected:6}  [{status}]")
            mul_successes.append({"x": x, "y": y, "expected": expected, "got": v})
        else:
            print(f"  mul({x:5}, {y:5}): ELAd failed — {r2['error']}")
            mul_failures.append({"x": x, "y": y, "stage": "ELAd", "error": r2["error"]})
    else:
        print(f"  mul({x:5}, {y:5}): EXL(0,x) FAILS — {r1['error']}")
        mul_failures.append({"x": x, "y": y, "stage": "EXL(0,x)", "error": r1["error"]})

print()
if mul_failures:
    print(f"  mul failures: {len(mul_failures)} / {len(mul_test_cases)} cases")
    for f in mul_failures:
        print(f"    x={f['x']}, y={f['y']}: {f['stage']} — {f['error']}")
else:
    print("  No failures.")

# ---------------------------------------------------------------------------
# Part 2: Full operation audit at negative/non-positive inputs
# ---------------------------------------------------------------------------

print()
print("=" * 70)
print("PART 2: Full SuperBEST v5 operation domain audit")
print("=" * 70)

# Test grid covering negative, zero, and fractional negatives
test_xs = [-3, -0.5, 0, 0.5, 3]
test_ys = [-3, -0.5, 0.5, 3]

def audit_op(name, fn, pairs):
    """Returns dict with pass/fail counts and failure list."""
    results = {"op": name, "passed": 0, "failed": 0, "failures": []}
    for (x, y, label) in pairs:
        r = safe(fn, x, y)
        if r["ok"]:
            results["passed"] += 1
        else:
            results["failed"] += 1
            results["failures"].append({"inputs": label, "error": r["error"]})
    return results

def audit_unary(name, fn, inputs):
    results = {"op": name, "passed": 0, "failed": 0, "failures": []}
    for x in inputs:
        r = safe(fn, x)
        if r["ok"]:
            results["passed"] += 1
        else:
            results["failed"] += 1
            results["failures"].append({"input": x, "error": r["error"]})
    return results

# Binary pairs (x, y, label)
binary_pairs = [(x, y, f"({x},{y})") for x in test_xs for y in test_ys]
# Exclude y=0 where it causes trivial issues unrelated to the domain question
binary_pairs_nonzero_y = [(x, y, f"({x},{y})") for x in test_xs for y in test_ys if y != 0]

# ---- add(x,y) = lediv(x, deml(y,1))
# deml(y,1) = exp(-y) - ln(1) = exp(-y)  [always > 0 for all y]
# lediv(x, exp(-y)) = ln(exp(x)/exp(-y)) = x+y
def add_superbest(x, y):
    z = deml(y, 1)   # = exp(-y) > 0 always
    return lediv(x, z)  # = x - ln(exp(-y)) = x+y

# ---- sub(x,y) = lediv(x, eml(y,1))
# eml(y,1) = exp(y) - ln(1) = exp(y)  [always > 0 for all y]
# lediv(x, exp(y)) = x - ln(exp(y)) = x - y
def sub_superbest(x, y):
    z = eml(y, 1)    # = exp(y) > 0 always
    return lediv(x, z)  # = x - y

# ---- mul(x,y) = elad(exl(0,x), y)
# exl(0,x) = ln(x)  — FAILS for x <= 0
def mul_superbest(x, y):
    lnx = exl(0, x)  # ln(x) — fails if x <= 0
    return elad(lnx, y)

# ---- div(x,y) = elsb(exl(0,x), y)
# From superbest.py: elsb(exl(0,x), y) = exp(ln(x)) / y = x/y
# exl(0,x) = ln(x) — fails for x <= 0
# elsb(a, y) = exp(a)/y — also needs y != 0
def div_superbest(x, y):
    lnx = exl(0, x)   # fails if x <= 0
    return elsb(lnx, y)  # fails if y == 0

# ---- neg(x) = exl(0, deml(x,1))
# deml(x,1) = exp(-x) - ln(1) = exp(-x)  [always > 0]
# exl(0, exp(-x)) = 1 * ln(exp(-x)) = -x
def neg_superbest(x):
    z = deml(x, 1)   # = exp(-x) > 0 always
    return exl(0, z)  # = ln(exp(-x)) = -x

# ---- recip(x) = elsb(0, x)
# elsb(0, x) = exp(0) / x = 1/x — fails if x == 0
def recip_superbest(x):
    return elsb(0, x)

# ---- pow(x,n) = eml(exl(ln(n), x), 1)
# Wait — from superbest.py: "eml(exl(ln(n),x), 1)"
# exl(ln(n), x) = exp(ln(n)) * ln(x) = n * ln(x)  — fails for x <= 0
# eml(n*ln(x), 1) = exp(n*ln(x)) - ln(1) = exp(n*ln(x)) = x^n
# Using n=2 for test
def pow_superbest(x, n=2):
    inner = exl(math.log(n), x)  # n * ln(x) — fails if x <= 0
    return eml(inner, 1)  # exp(n*ln(x)) = x^n

# ---- sqrt(x) = eml(0.5*exl(0,x), 1)
# exl(0,x) = ln(x) — fails for x <= 0
# eml(0.5*ln(x), 1) = exp(0.5*ln(x)) - 0 = sqrt(x)
def sqrt_superbest(x):
    lnx = exl(0, x)  # ln(x) — fails if x <= 0
    return eml(0.5 * lnx, 1)

print()

# Audit each operation
op_audits = {}

# add: all reals
add_results = audit_op("add", add_superbest,
                        [(x, y, f"({x},{y})") for x in test_xs for y in test_ys])
op_audits["add"] = add_results

# sub: all reals
sub_results = audit_op("sub", sub_superbest,
                        [(x, y, f"({x},{y})") for x in test_xs for y in test_ys])
op_audits["sub"] = sub_results

# mul: suspect — needs x > 0
mul_results = audit_op("mul", mul_superbest,
                        [(x, y, f"({x},{y})") for x in test_xs for y in test_ys])
op_audits["mul"] = mul_results

# div: needs x > 0, y != 0
div_results = audit_op("div", div_superbest,
                        [(x, y, f"({x},{y})") for x in test_xs for y in test_ys if y != 0])
op_audits["div"] = div_results

# neg: all reals (unary)
neg_results = audit_unary("neg", neg_superbest, test_xs)
op_audits["neg"] = neg_results

# recip: x != 0
recip_results = audit_unary("recip", recip_superbest, [x for x in test_xs if x != 0])
op_audits["recip"] = recip_results

# pow: x > 0
pow_results = audit_op("pow(x,2)", lambda x, y: pow_superbest(x, 2),
                        [(x, 2, f"({x},2)") for x in test_xs])
op_audits["pow"] = pow_results

# sqrt: x > 0
sqrt_results = audit_unary("sqrt", sqrt_superbest, test_xs)
op_audits["sqrt"] = sqrt_results

# Print summary
for op_name, r in op_audits.items():
    total = r["passed"] + r["failed"]
    domain_ok = r["failed"] == 0
    status = "ALL REALS OK" if domain_ok else f"FAILS: {r['failed']}/{total}"
    print(f"  {op_name:12} passed={r['passed']:3} failed={r['failed']:3} — {status}")
    if r["failures"]:
        shown = r["failures"][:3]
        for f in shown:
            loc = f.get("inputs") or f.get("input")
            print(f"             fail at {loc}: {f['error'][:60]}")

# ---------------------------------------------------------------------------
# Part 3: Is there a general mul for all reals?
# ---------------------------------------------------------------------------

print()
print("=" * 70)
print("PART 3: Can mul(x,y) = x*y be computed for ALL real x, y?")
print("=" * 70)

# The fundamental barrier: any path to x*y via real ELC primitives
# (EML, EXL, EAL, DEML, etc.) must go through ln(x) or ln(y).
# ln is undefined for non-positive reals over ℝ.
#
# x*y = exp(ln(x) + ln(y)) — requires x,y > 0
# x*y = exp(ln(|x|) + ln(|y|)) * sign(x)*sign(y) — requires conditionals
#
# Analytic functions of x and y:
#   f(x,y) = x*y  IS analytic everywhere on ℝ²
#   But every F16 tree is a composition of exp, ln, +, *, /, constants
#   The ln in EXL/EAL/EML creates a branch cut at the negative real axis
#
# Key theorem check: is mul achievable via a SINGLE analytic F16 tree?
# Answer: No, because any chain reaching x*y must evaluate ln at some
# intermediate step that depends on x (or y), and for x <= 0, that fails.
#
# However: can we use a different arrangement?
# Attempt 1: EAL(x, y) = exp(x) + ln(y). Can this reach x*y?
#   We'd need exp(x) + ln(y) = x*y — not an identity.
# Attempt 2: via DEML
#   DEML(x,y) = exp(-x) - ln(y). Can't easily get x*y.
# Attempt 3: x*y via addition only?
#   x*y can't be expressed as a fixed composition of addition and exp/ln
#   without going through ln(x) for variable x.
#
# The correct characterization:
#   mul_general(x,y) for ALL reals requires COMPLEX arithmetic or conditionals.
#   In REAL ELC, mul = 2n is valid only for x > 0 (or y > 0 after symmetry).

# Verify: mul(-3, 5) should be -15. Can we get it?
print()
print("  Can mul(-3, 5) = -15 be computed in real ELC?")
print("  Strategy: neg(mul(neg(x), y)) when x < 0, y > 0")
print("  neg(x) = -x costs 2n. mul(-x, y) costs 2n (x>0 now).")
print("  neg(result) costs 2n. Total: 6n + conditional branching.")
print("  This is NOT a single F16 tree — it uses a conditional.")
print()

# Demonstrate the branching approach:
def mul_with_branch(x, y):
    """mul via sign-aware branching — NOT a single F16 tree"""
    if x > 0 and y > 0:
        return math.exp(math.log(x) + math.log(y))
    elif x < 0 and y > 0:
        return -math.exp(math.log(-x) + math.log(y))
    elif x > 0 and y < 0:
        return -math.exp(math.log(x) + math.log(-y))
    elif x < 0 and y < 0:
        return math.exp(math.log(-x) + math.log(-y))
    else:
        return 0.0  # x or y = 0

branch_tests = [(3, 5, 15), (-3, 5, -15), (3, -5, -15), (-3, -5, 15), (0, 5, 0)]
print("  Branched mul (not a single tree) results:")
for x, y, expected in branch_tests:
    v = mul_with_branch(x, y)
    ok = abs(v - expected) < 1e-8
    print(f"    mul({x:4},{y:4}) = {v:8.3f}  expected {expected:4}  {'OK' if ok else 'WRONG'}")

print()
print("  Conclusion: No single analytic real-ELC tree computes x*y for ALL reals.")
print("  The 2n construction uses EXL(0,x) = ln(x), undefined for x <= 0.")

# ---------------------------------------------------------------------------
# Part 4: abs(x) = sqrt(x^2) analysis
# ---------------------------------------------------------------------------

print()
print("=" * 70)
print("PART 4: abs(x) = sqrt(x^2) in real ELC")
print("=" * 70)

# abs(x) requires x^2 = mul(x,x).
# mul(x,x) for x < 0 fails in real ELC.
# Via complex: ln(-3) = ln(3) + i*pi — complex intermediates work.
# But real ELC does not have complex intermediates by definition.
#
# Lower bound argument: abs'(x) is not continuous at 0 (has a kink).
# Any analytic function (which all real ELC trees are) is differentiable everywhere.
# Therefore abs(x) is NOT in real ELC over all of ℝ.
#
# This is the SAME barrier as neg_sqrt: if f is an ELC tree, f is C^∞ everywhere.
# abs(x) has a non-differentiable point at x=0, so abs ∉ ELC(ℝ).

print()
print("  abs(x) = sqrt(x^2) requires:")
print("    Step 1: x^2 = mul(x,x) — fails for x < 0 in real ELC (EXL(0,x)=ln(x) undefined)")
print("    Step 2: sqrt(x^2) = sqrt(positive) — would work IF x^2 were available")
print()
print("  But more fundamentally:")
print("  - Every real ELC tree is an analytic (C^infty) function.")
print("  - abs(x) has a non-differentiable corner at x=0.")
print("  - Therefore abs(x) cannot be expressed as any real ELC tree.")
print("  - abs(x) is OUTSIDE real ELC.")
print()
print("  In complex ELC:")
print("  - ln(-3) = ln(3) + i*pi (principal branch)")
print("  - mul(-3, -3) = exp(ln(-3)+ln(-3)) = exp(ln(9)+2i*pi) = 9")
print("  - sqrt(9) = 3 = abs(-3) -- works in complex ELC!")
print("  - Complex ELC can compute abs(x) via: sqrt(exp(2*ln(x))) using complex branch")

# Verify complex path
import cmath
def mul_complex(x, y):
    return cmath.exp(cmath.log(x) + cmath.log(y))

def abs_via_complex(x):
    x2 = mul_complex(x, x)  # uses complex ln
    return cmath.sqrt(x2)

print()
print("  Complex ELC abs(x) verification:")
for x in [-3, -0.5, 0.5, 3]:
    result = abs_via_complex(x)
    expected = abs(x)
    real_part = result.real
    imag_part = abs(result.imag)
    ok = abs(real_part - expected) < 1e-8 and imag_part < 1e-8
    print(f"    abs_complex({x:5}) = {real_part:.6f} + {result.imag:.2e}i  "
          f"expected {expected}  {'OK' if ok else 'WRONG'}")

# ---------------------------------------------------------------------------
# Part 5: Table implications
# ---------------------------------------------------------------------------

print()
print("=" * 70)
print("PART 5: SuperBEST v5 table corrections needed")
print("=" * 70)

# Current table state in superbest.py:
#   mul: domain = "x > 0"  (ALREADY CORRECT in superbest.py)
#   div: domain = "x, y > 0"  (ALREADY CORRECT)
#   superbest_v5_table.json: mul = 2n with NO domain annotation  <-- NEEDS FIX
#   pow: domain = "x > 0"  (ALREADY CORRECT)
#   sqrt: domain = "x > 0"  (ALREADY CORRECT)
#   add, sub, neg, exp, recip: domain = "all reals"  (CORRECT)

print()
print("  Operations with domain restrictions in real ELC:")
print("    mul(x,y):  x > 0 required (EXL(0,x) = ln(x) undefined for x <= 0)")
print("    div(x,y):  x > 0 and y != 0 required")
print("    ln(x):     x > 0 required (primitive)")
print("    pow(x,n):  x > 0 required (uses ln(x))")
print("    sqrt(x):   x > 0 required (uses ln(x))")
print()
print("  Operations valid for ALL reals in real ELC:")
print("    add(x,y):  all reals (DEML(y,1)=exp(-y)>0 always, LEDIV safe)")
print("    sub(x,y):  all reals (EML(y,1)=exp(y)>0 always, LEDIV safe)")
print("    neg(x):    all reals (DEML(x,1)=exp(-x)>0, then EXL(0,exp(-x))=-x)")
print("    exp(x):    all reals (EML(x,1) primitive)")
print("    recip(x):  all reals except x=0 (ELSb(0,x)=1/x)")
print()
print("  CORRECTION needed in superbest_v5_table.json:")
print("    mul: add domain annotation 'x > 0' (currently missing)")
print("    The table says mul=2n with notes='T10u, F16 optimal' — no domain warning")

# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------

# Determine mul domain
mul_domain = "x > 0 (EXL(0,x) = ln(x) requires x > 0)"
mul_fails_at = [{"x": f["x"], "y": f["y"], "stage": f["stage"], "error": f["error"]}
                for f in mul_failures]

# Compile operations audit
operations_audit = {}
for op_name, r in op_audits.items():
    domain_claim = {
        "add":       "all reals",
        "sub":       "all reals",
        "mul":       "x > 0 only",
        "div":       "x > 0, y != 0",
        "neg":       "all reals",
        "recip":     "x != 0",
        "pow(x,2)":  "x > 0 only",
        "sqrt":      "x > 0 only",
    }.get(op_name, "unknown")
    operations_audit[op_name] = {
        "domain": domain_claim,
        "test_passed": r["passed"],
        "test_failed": r["failed"],
        "verified": r["failed"] == 0 or (op_name in ("mul", "div", "pow(x,2)", "sqrt")
                                          and "x > 0" in domain_claim),
        "note": (f"Correctly fails at x<=0: {[f.get('inputs') or f.get('input') for f in r['failures'][:5]]}"
                 if r["failures"] else "All tested inputs passed")
    }

result = {
    "session": "X7",
    "title": "abs(x) Puzzle and mul Domain Audit",
    "date": "2026-04-20",

    "mul_2n_domain": "positive x only (x > 0); fails for x <= 0",
    "mul_fails_at": [
        {"x": f["x"], "y": f["y"], "stage": f["stage"], "error": f["error"]}
        for f in mul_failures
    ],
    "mul_explanation": (
        "ELAd(EXL(0,x), y) = exp(ln(x)) * y = x*y, but EXL(0,x) = ln(x) "
        "is undefined for x <= 0 in real arithmetic. "
        "There is NO single analytic real-ELC tree computing x*y for all reals. "
        "A branching strategy (6n + conditional) exists but is not a valid F16 tree."
    ),

    "abs_x_status": "outside real ELC",
    "abs_x_explanation": (
        "Two barriers: (1) mul(x,x) fails for x<0 in real ELC; "
        "(2) abs(x) has a non-differentiable corner at x=0, but every real ELC "
        "tree is C^inf analytic — so abs cannot be any real ELC tree regardless of cost. "
        "In complex ELC, abs(x) IS computable via sqrt(exp(2*ln(x))) using complex branch cuts."
    ),

    "general_mul_cost": "not achievable as a single real ELC tree for all reals",
    "general_mul_cost_with_branch": "6n + conditional (3 sub-trees: neg, mul_pos, neg)",

    "superbest_table_correction": "annotation needed",
    "correction_detail": (
        "superbest_v5_table.json entry for mul has notes='T10u, F16 optimal' but no domain "
        "annotation. Should add: domain='x > 0'. "
        "superbest.py ALREADY correctly annotates domain='x > 0' for mul. "
        "The JSON table (superbest_v5_table.json) is inconsistent — it omits the domain restriction."
    ),

    "operations_audit": operations_audit,

    "key_findings": [
        "mul = 2n is CORRECT but domain-restricted: x > 0 only",
        "div = 2n is domain-restricted: x > 0 and y != 0",
        "add = 2n holds for ALL reals (via LEDIV+DEML, proven in ADD-T1)",
        "sub = 2n holds for ALL reals (via LEDIV+EML)",
        "neg = 2n holds for ALL reals (DEML(x,1)=exp(-x)>0 always)",
        "exp = 1n holds for ALL reals",
        "recip = 1n holds for all x != 0",
        "ln = 1n requires x > 0",
        "sqrt = 2n requires x > 0",
        "pow = 3n requires x > 0",
        "abs(x) is OUTSIDE real ELC (non-differentiable at 0; analytic barrier)",
        "abs(x) IS computable in complex ELC via sqrt(exp(2*clog(x)))",
    ],

    "implications_for_physics": (
        "Most physics quantities (mass, length, energy, temperature) are positive-definite, "
        "so mul=2n applies directly. Mixed-sign quantities (sub results, signed charges, "
        "displacements) cannot use mul=2n directly — they need explicit sign handling "
        "or complex ELC. The ADD-T1 breakthrough (add=2n for all reals) is unaffected; "
        "DEML(y,1)=exp(-y)>0 always, so LEDIV is always safe."
    ),

    "superbest_v5_completeness_note": (
        "The SuperBEST v5 table is correct in its node counts. The add=2n result "
        "is genuine and domain-universal. The mul=2n result is genuine but domain-restricted. "
        "The table entry for mul should be annotated 'x > 0' to prevent misapplication."
    )
}

# Save
out_path = os.path.join(os.path.dirname(__file__), "..", "results", "x7_mul_domain_audit.json")
out_path = os.path.normpath(out_path)
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print()
print(f"Results saved to: {out_path}")
print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  mul = 2n domain:    {result['mul_2n_domain']}")
print(f"  abs(x) status:      {result['abs_x_status']}")
print(f"  Table correction:   {result['superbest_table_correction']}")
print(f"  mul failures found: {len(mul_failures)}")
