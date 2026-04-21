# -*- coding: utf-8 -*-
"""
verify_fin_2.py
SuperBEST v4 -- Portfolio Theory & Risk Metrics verification
Checks: Sharpe, CAPM, Bond Price, Log Return, CAGR
"""

import math
import sys

# Force UTF-8 output on Windows to avoid CP1252 encode errors
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# 1. Sharpe Ratio
# S = (R_p - R_f) / σ_p
# Cost: sub(2n) + div(2n) = 4n
# ---------------------------------------------------------------------------
def sharpe_ratio(r_p: float, r_f: float, sigma_p: float) -> float:
    excess = r_p - r_f          # sub  2n
    return excess / sigma_p     # div  2n


# ---------------------------------------------------------------------------
# 2. CAPM Expected Return
# E(R_i) = R_f + β_i · (E(R_m) - R_f)
# Cost: sub(2n) + mul(2n) + add_pos(3n) = 7n
# ---------------------------------------------------------------------------
def capm(r_f: float, beta: float, e_rm: float) -> float:
    market_premium = e_rm - r_f             # sub      2n
    beta_term = beta * market_premium       # mul      2n
    return r_f + beta_term                  # add_pos  3n (β > 0 assumed)


# ---------------------------------------------------------------------------
# 3. Bond Price (coupon bond)
# P = Σ C/(1+r)^t  +  F/(1+r)^n
# Cost: 12N + 6  (N=10 → 126n)
# ---------------------------------------------------------------------------
def bond_price(coupon: float, face: float, r: float, n: int) -> float:
    base = 1.0 + r              # add_pos  3n  (paid once, reused)
    coupon_pv = 0.0
    for t in range(1, n + 1):
        # per term: pow(3n) + recip(1n) + mul(2n) = 6n  (add_pos already paid)
        discount = base ** t    # pow  3n
        pv_t = coupon / discount  # div → recip(1n) + mul(2n) = 3n (or div 2n)
        coupon_pv += pv_t       # add_pos  3n (accumulated sum of positives)
    face_pv = face / (base ** n)  # pow(3n) + div(2n) = 5n
    return coupon_pv + face_pv    # add_pos  3n


# ---------------------------------------------------------------------------
# 4. Log Return
# r_t = ln(P_t / P_{t-1})
# Cost: div(2n) + ln(1n) = 3n
# ---------------------------------------------------------------------------
def log_return(p_t: float, p_prev: float) -> float:
    ratio = p_t / p_prev        # div  2n
    return math.log(ratio)      # ln   1n


# ---------------------------------------------------------------------------
# 5. CAGR
# CAGR = (V_f / V_i)^(1/n) - 1
# Cost: div(2n) + recip(1n) + pow(3n) + sub(2n) = 8n
# ---------------------------------------------------------------------------
def cagr(v_f: float, v_i: float, n: float) -> float:
    ratio = v_f / v_i           # div    2n
    exponent = 1.0 / n          # recip  1n
    growth = ratio ** exponent  # pow    3n
    return growth - 1.0         # sub    2n


# ---------------------------------------------------------------------------
# Run verifications
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("SuperBEST v4 — Finance Session 2: Verification")
    print("=" * 60)

    # --- Sharpe ---
    r_p, r_f, sigma = 0.12, 0.03, 0.15
    s = sharpe_ratio(r_p, r_f, sigma)
    expected_s = (r_p - r_f) / sigma  # = 0.60
    status = "PASS" if abs(s - 0.60) < 1e-10 else "FAIL"
    print(f"\n[fin2_01] Sharpe Ratio  ({status})")
    print(f"  Input:    R_p={r_p}, R_f={r_f}, sigma={sigma}")
    print(f"  Result:   {s:.6f}")
    print(f"  Expected: 0.600000")
    print(f"  Cost:     4n")

    # --- CAPM ---
    r_f_c, beta, e_rm = 0.03, 1.2, 0.10
    e_r = capm(r_f_c, beta, e_rm)
    expected_er = 0.03 + 1.2 * 0.07  # = 0.114
    status = "PASS" if abs(e_r - expected_er) < 1e-10 else "FAIL"
    print(f"\n[fin2_02] CAPM Expected Return  ({status})")
    print(f"  Input:    R_f={r_f_c}, β={beta}, E(R_m)={e_rm}")
    print(f"  Result:   {e_r:.6f}")
    print(f"  Expected: {expected_er:.6f}")
    print(f"  Cost:     7n  (β > 0 path)")

    # --- Bond Price ---
    coupon, face_val, r_bond, n_periods = 50.0, 1000.0, 0.05, 10
    p = bond_price(coupon, face_val, r_bond, n_periods)
    # At par: coupon rate = yield → price = face value = 1000
    status = "PASS" if abs(p - 1000.0) < 1e-6 else "FAIL"
    print(f"\n[fin2_06] Bond Price (N=10)  ({status})")
    print(f"  Input:    C={coupon}, F={face_val}, r={r_bond}, N={n_periods}")
    print(f"  Result:   {p:.6f}")
    print(f"  Expected: ~1000.000000  (at-par: coupon rate = yield)")
    print(f"  Cost:     12×{n_periods} + 6 = {12 * n_periods + 6}n")

    # --- Log Return ---
    p_t, p_prev = 105.0, 100.0
    lr = log_return(p_t, p_prev)
    expected_lr = math.log(1.05)
    status = "PASS" if abs(lr - expected_lr) < 1e-10 else "FAIL"
    print(f"\n[fin2_08] Log Return  ({status})")
    print(f"  Input:    P_t={p_t}, P_{{t-1}}={p_prev}")
    print(f"  Result:   {lr:.8f}")
    print(f"  Expected: {expected_lr:.8f}  (ln(1.05))")
    print(f"  Cost:     3n")

    # --- CAGR ---
    v_f, v_i, n_years = 200.0, 100.0, 10.0
    c = cagr(v_f, v_i, n_years)
    expected_c = 2.0 ** 0.1 - 1  # ≈ 0.071773
    status = "PASS" if abs(c - expected_c) < 1e-10 else "FAIL"
    print(f"\n[fin2_09] CAGR  ({status})")
    print(f"  Input:    V_f={v_f}, V_i={v_i}, n={n_years}")
    print(f"  Result:   {c:.8f}")
    print(f"  Expected: {expected_c:.8f}  (2^0.1 - 1)")
    print(f"  Cost:     8n")

    # --- Summary Table ---
    print("\n" + "=" * 60)
    print("SUMMARY — SuperBEST v4 node costs")
    print("=" * 60)
    rows = [
        ("fin2_01", "Sharpe Ratio",                  "4n",       "given σ_p precomputed"),
        ("fin2_02", "CAPM Expected Return",           "7n",       "β > 0; 15n if β < 0"),
        ("fin2_03", "Portfolio Variance (2-asset)",   "40n",      "34n if ρ ≥ 0 guaranteed"),
        ("fin2_04", "Value at Risk (Normal)",         "4n",       "z_α constant; erfinv outside EML"),
        ("fin2_05", "Kelly Criterion",                "5n",       "simplified μ/σ² form"),
        ("fin2_06", "Bond Price (N coupons)",         "12N+6n",   "126n at N=10"),
        ("fin2_07", "Modified Duration",              "14N+6n",   "P precomputed"),
        ("fin2_08", "Log Return",                     "3n",       "most EML-efficient return measure"),
        ("fin2_09", "CAGR",                           "8n",       "geometric mean kernel"),
        ("fin2_10", "Sortino Ratio",                  "4n",       "given σ_d; σ_d requires conditional"),
    ]
    print(f"  {'ID':<10} {'Equation':<35} {'Cost':<12} Key Insight")
    print(f"  {'-'*10} {'-'*35} {'-'*12} {'-'*35}")
    for row in rows:
        print(f"  {row[0]:<10} {row[1]:<35} {row[2]:<12} {row[3]}")

    print("\n  EML BOUNDARY CASES:")
    print("  - erfinv (VaR z_α):     outside EML; inject as constant")
    print("  - min(r,0) (Sortino σ_d): conditional; needs smooth approx or preprocessing")

    print("\n  CROSS-DOMAIN MOTIFS:")
    print("  - 3n  ln(ratio):          log return = pharmacokinetic decay = entropy term")
    print("  - 9n  discount term:      bond PV coupon = population decay model")
    print("  - 6n  pow(ratio, 1/n):    CAGR = fractal dimension = biological geometric mean")
    print()


if __name__ == "__main__":
    main()
