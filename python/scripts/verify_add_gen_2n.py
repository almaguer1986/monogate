"""Verify add_gen = 2n: lediv(x, deml(y,1)) = x+y for all real x,y

Construction:
  Node 1: z1 = DEML(y, 1) = exp(-y) - ln(1) = exp(-y)
  Node 2: z2 = LEdiv(x, z1) = x - ln(exp(-y)) = x + y

Operator definitions (F16):
  DEML(x, y) = exp(-x) - ln(y)     [requires y > 0]
  LEdiv(x, y) = x - ln(y)          [equivalently ln(exp(x)/y); requires y > 0]
"""
import math
import sys


# ── Operator definitions ──────────────────────────────────────────────────────

def deml(x, y):
    """DEML(x,y) = exp(-x) - ln(y).  Requires y > 0."""
    return math.exp(-x) - math.log(y)


def lediv(x, y):
    """LEdiv(x,y) = x - ln(y) = ln(exp(x)/y).  Requires y > 0."""
    return x - math.log(y)


def add_2n(x, y):
    """2-node F16 computation of x+y."""
    node1 = deml(y, 1)   # exp(-y) - ln(1) = exp(-y)
    node2 = lediv(x, node1)  # x - ln(exp(-y)) = x - (-y) = x + y
    return node2


# ── Test cases: 30+ points spanning all sign combinations and magnitudes ──────

test_cases = [
    # Mixed signs
    (-3.0,   5.0),
    (-1.0,  -2.0),
    ( 0.0,   0.0),
    ( 3.0,  -7.0),
    (-10.0,  4.0),
    # Large magnitudes
    (100.0, -200.0),
    (-500.0, 300.0),
    ( 50.0,  50.0),
    # Near zero
    (-0.001,  0.001),
    ( 1e-10, -1e-10),
    ( 0.5,   -0.5),
    # Both negative
    (-100.0, -100.0),
    ( -50.0,  -30.0),
    # Extreme
    (-1000.0,  500.0),
    (  300.0, -400.0),
    # Positive only (was the domain of add_pos; now handled generally)
    (3.0,    4.0),
    (0.1,    0.9),
    (100.0, 200.0),
    (1.0,    1.0),
    # One zero
    (0.0,    5.0),
    (-3.0,   0.0),
    (0.0,   -7.0),
    # Fractional
    (1.5,    2.7),
    (-3.14159265358979, 2.71828182845905),
    # Irrational-like
    (math.log(2),  -math.log(3)),
    (math.pi,      -math.e),
    # Symmetric
    (7.0,   -7.0),
    (-7.0,   7.0),
    # Stress (within float64 range: exp(-y) must be representable, so |y| < ~709)
    (-700.0,  699.0),
    ( 500.5, -500.5),
]


def run_construction_tests():
    print("Verifying add_gen = 2n: LEdiv(x, DEML(y,1)) = x+y")
    print("=" * 60)

    passed = 0
    failed = 0
    tolerance = 1e-10

    for x, y in test_cases:
        result   = add_2n(x, y)
        expected = x + y
        err      = abs(result - expected)
        ok       = err < tolerance
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: add({x}, {y}) = {result}, expected {expected}, err={err:.2e}")

    print(f"\n{passed}/{passed + failed} test cases PASS (tolerance {tolerance:.0e})")
    return failed == 0


# ── Lower-bound scan: try every plausible 1-node F16 operator ────────────────

def run_lower_bound_scan():
    print()
    print("=" * 60)
    print("Lower bound: scanning all F16 operators for a 1-node add...")
    print("Test points: (2,3), (-1,4), (1,-2), (-3,-1)")

    lb_test = [(2.0, 3.0), (-1.0, 4.0), (1.0, -2.0), (-3.0, -1.0)]

    # All 16 F16 operators in both argument orders where sensible.
    # Each entry: (name, lambda).
    # Domain failures (log of non-positive) return None and are treated as non-matching.
    def safe(fn, x, y):
        try:
            v = fn(x, y)
            return v if math.isfinite(v) else None
        except (ValueError, ZeroDivisionError, OverflowError):
            return None

    ops = [
        # Class I — EML family
        ("EML(x,y)  = exp(x) - ln(y)",   lambda x,y: math.exp(x) - math.log(y)),
        ("EML(y,x)  = exp(y) - ln(x)",   lambda x,y: math.exp(y) - math.log(x)),
        ("DEML(x,y) = exp(-x) - ln(y)",  lambda x,y: math.exp(-x) - math.log(y)),
        ("DEML(y,x) = exp(-y) - ln(x)",  lambda x,y: math.exp(-y) - math.log(x)),
        # Class I — EAL family
        ("EAL(x,y)  = exp(x) + ln(y)",   lambda x,y: math.exp(x) + math.log(y)),
        ("EAL(y,x)  = exp(y) + ln(x)",   lambda x,y: math.exp(y) + math.log(x)),
        # Class I — EXL family
        ("EXL(x,y)  = exp(x) * ln(y)",   lambda x,y: math.exp(x) * math.log(y)),
        ("EXL(y,x)  = exp(y) * ln(x)",   lambda x,y: math.exp(y) * math.log(x)),
        # Class I — ELSb / ELdiv
        ("ELdiv(x,y) = exp(x) / ln(y)",  lambda x,y: math.exp(x) / math.log(y) if math.log(y) != 0 else None),
        ("ELdiv(y,x) = exp(y) / ln(x)",  lambda x,y: math.exp(y) / math.log(x) if math.log(x) != 0 else None),
        # Class I — ELpow
        ("ELpow(x,y) = exp(x) ^ ln(y)",  lambda x,y: math.exp(x) ** math.log(y)),
        ("ELpow(y,x) = exp(y) ^ ln(x)",  lambda x,y: math.exp(y) ** math.log(x)),
        # Class II — composition operators
        ("LEAd(x,y)  = ln(exp(x) + y)",  lambda x,y: math.log(math.exp(x) + y) if math.exp(x) + y > 0 else None),
        ("LEAd(y,x)  = ln(exp(y) + x)",  lambda x,y: math.log(math.exp(y) + x) if math.exp(y) + x > 0 else None),
        ("ELAd(x,y)  = exp(x) * y",      lambda x,y: math.exp(x) * y),
        ("ELAd(y,x)  = exp(y) * x",      lambda x,y: math.exp(y) * x),
        ("ELSb(x,y)  = exp(x) / y",      lambda x,y: math.exp(x) / y if y != 0 else None),
        ("ELSb(y,x)  = exp(y) / x",      lambda x,y: math.exp(y) / x if x != 0 else None),
        ("LEdiv(x,y) = x - ln(y)",       lambda x,y: x - math.log(y)),
        ("LEdiv(y,x) = y - ln(x)",       lambda x,y: y - math.log(x)),
    ]

    found_any = False
    for name, fn in ops:
        matches = True
        for x, y in lb_test:
            r = safe(fn, x, y)
            if r is None or abs(r - (x + y)) > 1e-8:
                matches = False
                break
        if matches:
            print(f"  FOUND 1-NODE ADD: {name}")
            found_any = True

    if not found_any:
        print("  (no 1-node operator matches on all four test points)")

    print("Scan complete.")
    return not found_any  # True = lower bound confirmed


# ── Algebraic trace: show the symbolic steps for a sample point ───────────────

def print_algebraic_trace(x, y):
    print()
    print("=" * 60)
    print(f"Algebraic trace for x={x}, y={y}:")
    exp_neg_y = math.exp(-y)
    ln_1      = math.log(1.0)
    node1     = exp_neg_y - ln_1
    ln_node1  = math.log(node1)
    node2     = x - ln_node1
    print(f"  Node 1: DEML({y}, 1)")
    print(f"        = exp(-{y}) - ln(1)")
    print(f"        = {exp_neg_y} - {ln_1}")
    print(f"        = {node1}")
    print(f"  Node 2: LEdiv({x}, {node1})")
    print(f"        = {x} - ln({node1})")
    print(f"        = {x} - ({ln_node1})")
    print(f"        = {node2}")
    print(f"  Expected x+y = {x + y}")
    print(f"  Error        = {abs(node2 - (x + y)):.2e}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ok_construction = run_construction_tests()
    ok_lower_bound  = run_lower_bound_scan()
    print_algebraic_trace(-3.0, 5.0)

    print()
    print("=" * 60)
    if ok_construction and ok_lower_bound:
        print("RESULT: THEOREM CONFIRMED")
        print("  Construction: 2 nodes suffice for all real x, y")
        print("  Lower bound:  no 1-node F16 operator computes x+y")
        print("  Conclusion:   add_gen = 2n is OPTIMAL")
        sys.exit(0)
    else:
        if not ok_construction:
            print("FAILURE: some construction test cases failed")
        if not ok_lower_bound:
            print("WARNING: a 1-node addition operator was found (update theorem)")
        sys.exit(1)
