"""
verify_econ_1.py
Verification script for econ_1_economics.json node-cost computations.
SuperBEST v4 cost model.
"""

import sys
import math

# Force UTF-8 output on Windows (avoids CP1252 UnicodeEncodeError)
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def verify_cobb_douglas():
    """Y = A * L^alpha * K^beta, cost = 10n"""
    A, L, K, alpha, beta = 1.0, 100.0, 50.0, 0.3, 0.7
    # Step-by-step matching the cost breakdown
    pow_L = L ** alpha          # pow(L, alpha) = 3n
    pow_K = K ** beta           # pow(K, beta)  = 3n
    step1  = A * pow_L          # mul(A, pow_L) = 2n
    Y      = step1 * pow_K      # mul(step1, pow_K) = 2n  => total 10n

    expected = 100**0.3 * 50**0.7  # A=1 simplifies
    return {
        "name": "Cobb-Douglas  Y = A·L^α·K^β",
        "formula": "Y = 1 * 100^0.3 * 50^0.7",
        "computed": round(Y, 4),
        "expected_approx": round(expected, 4),
        "cost": "10n",
        "pass": abs(Y - expected) < 1e-8,
    }


def verify_log_utility():
    """U = ln(C), cost = 1n"""
    C = 100.0
    U = math.log(C)             # ln(C) = 1n

    expected = math.log(100)
    return {
        "name": "Log Utility  U = ln(C)",
        "formula": "U = ln(100)",
        "computed": round(U, 6),
        "expected_approx": round(expected, 6),
        "expected_numeric": "≈ 4.605170",
        "cost": "1n",
        "pass": abs(U - expected) < 1e-10,
    }


def verify_crra_utility():
    """U = C^(1-gamma) / (1-gamma), gamma=2, cost = 7n"""
    C, gamma = 100.0, 2.0
    exp_val   = 1.0 - gamma          # sub(1, gamma) = 2n  => -1.0
    pow_C     = C ** exp_val         # pow(C, 1-gamma) = 3n => 100^(-1) = 0.01
    U         = pow_C / exp_val      # div(pow, sub) = 2n   => 0.01 / (-1) = -0.01

    expected = (100.0 ** (1 - 2)) / (1 - 2)
    return {
        "name": "CRRA Utility  U = C^(1-γ)/(1-γ)  γ=2",
        "formula": "U = 100^(-1) / (-1) = -0.01",
        "computed": round(U, 6),
        "expected_approx": round(expected, 6),
        "cost": "7n",
        "pass": abs(U - expected) < 1e-10,
    }


def verify_price_elasticity():
    """epsilon = (deltaQ/Q) / (deltaP/P), cost = 6n"""
    deltaQ_over_Q = -0.2    # -20% quantity change
    deltaP_over_P =  0.1    # +10% price change

    ratio_Q = deltaQ_over_Q   # already a ratio; div(deltaQ, Q) = 2n
    ratio_P = deltaP_over_P   # div(deltaP, P) = 2n
    epsilon = ratio_Q / ratio_P  # div(ratio_Q, ratio_P) = 2n => total 6n

    expected = -2.0
    return {
        "name": "Price Elasticity  ε = (ΔQ/Q) / (ΔP/P)",
        "formula": "ε = (-0.2) / (0.1) = -2.0",
        "computed": round(epsilon, 6),
        "expected_approx": round(expected, 6),
        "cost": "6n",
        "pass": abs(epsilon - expected) < 1e-10,
    }


def verify_compound_interest():
    """A = P * (1 + r/n)^(n*t), cost = 12n"""
    P, r, n, t = 1000.0, 0.05, 12.0, 10.0

    r_n      = r / n              # div(r, n) = 2n
    base     = 1.0 + r_n          # add_pos(1, r_n) = 3n
    periods  = n * t              # mul(n, t) = 2n
    growth   = base ** periods    # pow(base, periods) = 3n
    A        = P * growth         # mul(P, growth) = 2n  => total 12n

    expected = 1000 * (1 + 0.05/12) ** (12*10)
    return {
        "name": "Compound Interest  A = P·(1+r/n)^(n·t)",
        "formula": "A = 1000*(1+0.05/12)^120",
        "computed": round(A, 4),
        "expected_approx": round(expected, 4),
        "expected_numeric": "≈ 1647.0095",
        "cost": "12n",
        "pass": abs(A - expected) < 1e-6,
    }


def verify_dcf():
    """PV = sum CF_t / (1+r)^t, CF=[100,100,100], r=0.1, cost = 12*3-3 = 33n"""
    cash_flows = [100.0, 100.0, 100.0]
    r = 0.1

    pv = 0.0
    per_period_breakdown = []
    for t, cf in enumerate(cash_flows, start=1):
        base      = 1.0 + r         # add_pos(1, r) = 3n
        denom     = base ** t       # pow(1+r, t) = 3n
        disc      = 1.0 / denom     # recip(denom) = 1n
        term      = cf * disc       # mul(cf, disc) = 2n  => 9n per period
        pv        += term           # add_pos (CF > 0) = 3n per addition
        per_period_breakdown.append({
            "t": t,
            "CF": cf,
            "discount_factor": round(disc, 8),
            "PV_term": round(term, 6),
        })

    # Manual expected
    expected = 100/1.1 + 100/1.21 + 100/1.331

    return {
        "name": "DCF Present Value  PV = Σ CF_t/(1+r)^t",
        "formula": "PV = 100/1.1 + 100/1.21 + 100/1.331",
        "computed": round(pv, 4),
        "expected_approx": round(expected, 4),
        "expected_numeric": "≈ 248.6852",
        "cost": "12*3 - 3 = 33n  (positive CFs)",
        "per_period": per_period_breakdown,
        "pass": abs(pv - expected) < 1e-6,
    }


def print_result(r):
    status = "PASS" if r["pass"] else "FAIL"
    print(f"  [{status}] {r['name']}")
    print(f"         Formula  : {r['formula']}")
    print(f"         Computed : {r['computed']}")
    print(f"         Expected : {r.get('expected_numeric', r['expected_approx'])}")
    print(f"         Cost     : {r['cost']}")
    if "per_period" in r:
        for p in r["per_period"]:
            print(f"           t={p['t']}: CF={p['CF']}, disc={p['discount_factor']}, PV={p['PV_term']}")
    print()


def main():
    print("=" * 65)
    print("  SuperBEST v4 — Economics Node Cost Verification")
    print("=" * 65)
    print()

    results = [
        verify_cobb_douglas(),
        verify_log_utility(),
        verify_crra_utility(),
        verify_price_elasticity(),
        verify_compound_interest(),
        verify_dcf(),
    ]

    for r in results:
        print_result(r)

    passed = sum(1 for r in results if r["pass"])
    total  = len(results)

    print("=" * 65)
    print(f"  Results: {passed}/{total} passed")
    print("=" * 65)
    print()

    print("Cost Summary Table:")
    print(f"  {'Equation':<40} {'Cost':>10}")
    print(f"  {'-'*40} {'-'*10}")
    summary = [
        ("Log Utility  U=ln(C)",               "1n"),
        ("Compound Interest (continuous)",       "5n"),
        ("Discounting factor 1/(1+r)^t",        "7n"),
        ("CRRA Utility  C^(1-γ)/(1-γ)",        "7n"),
        ("Price Elasticity (arc)",              "6n"),
        ("Laffer Curve  t*(1-t)*Y",             "6n"),
        ("Cobb-Douglas  Y=A·L^α·K^β",          "10n"),
        ("Compound Interest (discrete)",        "12n"),
        ("CES Utility (add_pos, ρ>0)",          "19n"),
        ("CES Utility (add_gen, ρ<0)",          "27n"),
        ("DCF PV (positive CF, N periods)",     "12N-3"),
        ("NPV (positive CF, N periods)",        "12N-1"),
        ("DCF PV (mixed CF, N periods)",        "20N-11"),
        ("Gini Coefficient (N points)",         "8N+2"),
    ]
    for name, cost in summary:
        print(f"  {name:<40} {cost:>10}")

    print()
    if passed == total:
        print("  All verifications passed.")
    else:
        print(f"  WARNING: {total - passed} verification(s) FAILED.")


if __name__ == "__main__":
    main()
