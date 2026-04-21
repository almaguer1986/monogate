# -*- coding: utf-8 -*-
"""
verify_fin_1.py
---------------
Verify Black-Scholes and Greeks at the reference test point:
  S=100, K=100, r=0.05, sigma=0.2, T=1.0 (at-the-money call)

Expected (from fin_1_black_scholes.json):
  d1 ~ 0.350, d2 ~ 0.150, C ~ 10.45
  Delta ~ 0.637, Gamma ~ 0.019, Vega ~ 37.5, Theta ~ -6.41, Rho ~ 53.2

Two implementations are run side-by-side:
  1. "Exact" -- uses scipy.stats.norm for true N(d) and N'(d)
  2. "EML approx" -- uses sigmoid(1.702d) for N(d), same N'(d) formula

The EML node costs from SuperBEST v4 are printed alongside each result.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import math
from scipy.stats import norm

# ---------------------------------------------------------------------------
# Test parameters
# ---------------------------------------------------------------------------
S     = 100.0   # spot price
K     = 100.0   # strike price
r     = 0.05    # risk-free rate
sigma = 0.20    # volatility
T     = 1.0     # time to expiry (years)

# ---------------------------------------------------------------------------
# SuperBEST v4 operator costs (for reference / audit)
# ---------------------------------------------------------------------------
COST = {
    "exp":     1,
    "ln":      1,
    "recip":   1,
    "neg":     2,
    "mul":     2,
    "sub":     2,
    "div":     2,
    "sqrt":    2,
    "pow":     3,
    "add_pos": 3,
    "add_gen": 11,
    "DEML":    1,   # DEML(x,1) = exp(-x)
}

SIGMOID_N_COST = 9   # mul(1.702,d)=2 + neg=2 + exp=1 + add_pos=3 + recip=1
N_PRIME_COST   = 8   # pow(d1,2)=3 + div(d1²,2)=2 + DEML=1 + div(,sqrt2pi)=2

# ---------------------------------------------------------------------------
# Helper: sigmoid approximation of N(d)
# ---------------------------------------------------------------------------
def sigmoid_N(d: float) -> float:
    """N(d) ≈ sigmoid(1.702·d) = 1/(1+exp(-1.702·d))"""
    return 1.0 / (1.0 + math.exp(-1.702 * d))

# ---------------------------------------------------------------------------
# Core shared subexpressions
# ---------------------------------------------------------------------------
sqrt_T      = math.sqrt(T)                          # sqrt(T) = 2n
sigma_sqrtT = sigma * sqrt_T                        # mul = 2n
ln_SK       = math.log(S / K)                       # div(S,K)=2n + ln=1n = 3n
sigma2_half = (sigma ** 2) / 2.0                    # pow=3n + div=2n = 5n
numerator   = ln_SK + (r + sigma2_half) * T         # add_pos(r,σ²/2)=3n + mul=2n + add[ln+product]=3n = 8n
d1          = numerator / sigma_sqrtT               # div=2n  → d1 total 19n
d2          = d1 - sigma_sqrtT                      # sub=2n  → d2 marginal 2n
e_neg_rT    = math.exp(-r * T)                      # mul(r,T)=2n + DEML=1n = 3n (e^-rT alone)
Ke_rT       = K * e_neg_rT                          # mul=2n  → Ke^(-rT) total 5n
sqrt_2pi    = math.sqrt(2.0 * math.pi)              # constant ≈ 2.5066

# N'(d1) — exact Gaussian PDF, costs 8n given d1
def N_prime(d: float) -> float:
    """exp(-d²/2) / sqrt(2π)  — 8n given d (DEML key: pow=3+div=2+DEML=1+div_by_const=2)"""
    return math.exp(-(d * d) / 2.0) / sqrt_2pi

# ---------------------------------------------------------------------------
# Exact Black-Scholes (using scipy normal CDF)
# ---------------------------------------------------------------------------
def bs_exact(S, K, r, sigma, T):
    Nd1  = norm.cdf(d1)
    Nd2  = norm.cdf(d2)
    Nnd1 = norm.cdf(-d1)
    Nnd2 = norm.cdf(-d2)
    Npd1 = N_prime(d1)

    C     = S * Nd1 - Ke_rT * Nd2
    P     = Ke_rT * Nnd2 - S * Nnd1
    Delta = Nd1
    Gamma = Npd1 / (S * sigma_sqrtT)
    Vega  = S * Npd1 * sqrt_T
    Theta = (-(S * Npd1 * sigma) / (2.0 * sqrt_T)) - (r * Ke_rT * Nd2)
    Rho   = K * T * e_neg_rT * Nd2

    return dict(d1=d1, d2=d2, C=C, P=P, Delta=Delta,
                Gamma=Gamma, Vega=Vega, Theta=Theta, Rho=Rho)

# ---------------------------------------------------------------------------
# EML-approximated Black-Scholes (sigmoid for N(d))
# ---------------------------------------------------------------------------
def bs_eml_approx(S, K, r, sigma, T):
    Nd1  = sigmoid_N(d1)
    Nd2  = sigmoid_N(d2)
    Nnd1 = sigmoid_N(-d1)
    Nnd2 = sigmoid_N(-d2)
    Npd1 = N_prime(d1)

    C     = S * Nd1 - Ke_rT * Nd2
    P     = Ke_rT * Nnd2 - S * Nnd1
    Delta = Nd1
    Gamma = Npd1 / (S * sigma_sqrtT)
    Vega  = S * Npd1 * sqrt_T
    Theta = (-(S * Npd1 * sigma) / (2.0 * sqrt_T)) - (r * Ke_rT * Nd2)
    Rho   = K * T * e_neg_rT * Nd2

    return dict(d1=d1, d2=d2, C=C, P=P, Delta=Delta,
                Gamma=Gamma, Vega=Vega, Theta=Theta, Rho=Rho)

# ---------------------------------------------------------------------------
# Expected reference values and SuperBEST v4 costs
# ---------------------------------------------------------------------------
EXPECTED = {
    "d1":    (0.350,  "19n standalone"),
    "d2":    (0.150,  "2n marginal / 21n standalone"),
    "C":     (10.45,  "50n standalone"),
    "P":     (5.57,   "54n standalone (put-call parity check)"),
    "Delta": (0.637,  "9n given d1 / 28n standalone"),
    "Gamma": (0.019,  "14n given d1,sqrtT / 33n standalone"),
    "Vega":  (37.5,   "12n given d1,sqrtT / 31n standalone"),
    "Theta": (-6.41,  "29n given shared / 58n standalone"),
    "Rho":   (53.2,   "6n given e^(-rT),N(d2) / 35n standalone"),
}

# ---------------------------------------------------------------------------
# Run and print
# ---------------------------------------------------------------------------
def fmt_check(key, actual, expected_val, tol_pct=2.0):
    """Return PASS/WARN based on % deviation."""
    if expected_val == 0:
        ok = abs(actual) < 0.01
    else:
        pct = abs(actual - expected_val) / abs(expected_val) * 100.0
        ok = pct < tol_pct
    return "PASS" if ok else f"WARN (diff={actual-expected_val:+.4f})"

def main():
    exact  = bs_exact(S, K, r, sigma, T)
    approx = bs_eml_approx(S, K, r, sigma, T)

    print("=" * 72)
    print("  Black-Scholes Verification — SuperBEST v4 Cost Audit")
    print(f"  S={S}, K={K}, r={r}, sigma={sigma}, T={T}")
    print("=" * 72)

    print(f"\n{'Metric':<10}  {'Exact':>10}  {'EML-Approx':>12}  {'Expected':>10}  {'Cost (n)':>20}  Status")
    print("-" * 90)

    keys_ordered = ["d1", "d2", "C", "P", "Delta", "Gamma", "Vega", "Theta", "Rho"]

    for key in keys_ordered:
        exp_val, cost_note = EXPECTED[key]
        ex  = exact[key]
        ap  = approx[key]
        status = fmt_check(key, ex, exp_val)
        print(f"{key:<10}  {ex:>10.4f}  {ap:>12.4f}  {exp_val:>10.4f}  {cost_note:>20}  {status}")

    print("-" * 90)

    # Subexpression audit
    print("\n--- Shared subexpressions ---")
    print(f"  sqrt(T)       = {sqrt_T:.6f}   [2n]")
    print(f"  sigma·√T      = {sigma_sqrtT:.6f}   [4n cumulative / 2n marginal]")
    print(f"  exp(-rT)      = {e_neg_rT:.6f}   [3n: mul(r,T)+DEML]")
    print(f"  K·exp(-rT)    = {Ke_rT:.6f}   [5n: +mul(K,exp)]")
    print(f"  N'(d1)        = {N_prime(d1):.6f}   [8n given d1]")

    # EML boundary reminder
    print("\n--- EML Boundary Note ---")
    print("  N(d) = normal CDF uses erf, which is NOT in the EML closure.")
    print("  erf has infinitely many complex zeros (same obstruction as sin).")
    print("  All costs above use sigmoid(1.702d) ≈ N(d) with max error < 0.009.")
    print("  'EML-approximable but not EML-exact.'")

    # Sigmoid approximation error check
    print("\n--- Sigmoid approximation error at test point ---")
    nd1_exact  = norm.cdf(d1)
    nd1_approx = sigmoid_N(d1)
    nd2_exact  = norm.cdf(d2)
    nd2_approx = sigmoid_N(d2)
    print(f"  N(d1): exact={nd1_exact:.6f}  sigmoid={nd1_approx:.6f}  err={nd1_approx-nd1_exact:+.6f}")
    print(f"  N(d2): exact={nd2_exact:.6f}  sigmoid={nd2_approx:.6f}  err={nd2_approx-nd2_exact:+.6f}")

    # Put-call parity check
    C_ex = exact["C"]
    P_ex = exact["P"]
    parity_lhs = C_ex - P_ex
    parity_rhs = S - Ke_rT
    print(f"\n--- Put-Call Parity: C - P = S - K·e^(-rT) ---")
    print(f"  C - P = {parity_lhs:.6f}")
    print(f"  S - K·e^(-rT) = {parity_rhs:.6f}")
    print(f"  Difference: {abs(parity_lhs - parity_rhs):.2e}  {'PASS' if abs(parity_lhs - parity_rhs) < 1e-8 else 'FAIL'}")

    # Full DAG cost summary
    print("\n--- SuperBEST v4 Full DAG Cost (all outputs shared) ---")
    dag = {
        "d1":             19,
        "d2 (+marginal)":  2,
        "N(d1)":           9,
        "N(d2)":           9,
        "Ke^(-rT)":        5,
        "N'(d1)":          8,
        "Call C":          6,
        "Delta (=N(d1))":  0,
        "Gamma":           6,
        "Vega":            4,
        "Theta":          11,
        "Rho":             4,
    }
    total = 0
    for k, v in dag.items():
        print(f"  {k:<28} +{v:>3}n")
        total += v
    print(f"  {'TOTAL':.<28} {total:>4}n")
    print(f"\n  (vs 329n if all computed independently: d1=19,d2=21,C=50,P=54,Delta=28,Gamma=33,Vega=31,Theta=58,Rho=35)")

    print("\n" + "=" * 72)
    print("  All checks complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()
