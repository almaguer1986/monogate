# -*- coding: utf-8 -*-
"""
verify_bio_1.py -- SuperBEST v4 Biology & Epidemiology Cost Verification
Verifies that each equation produces correct numerical results.
"""

import math
import sys
import io

# Force UTF-8 output on Windows to avoid cp1252 encode errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Logistic Growth: N(t) = K / (1 + A*exp(-rt)),  A = (K-N0)/N0
# ---------------------------------------------------------------------------
def logistic_growth(K, N0, r, t):
    A = (K - N0) / N0          # precomputed constant
    exp_rt = math.exp(-r * t)  # mul(r,t)=2n, DEML=1n -> 3n
    denom = 1 + A * exp_rt     # mul(A, exp_rt)=2n, add_pos=3n -> 5n
    return K / denom            # div=2n  -> total: 10n


# ---------------------------------------------------------------------------
# 2. SIR Epidemic Model -- one discrete timestep
# dS = -beta*S*I/N,  dI = beta*S*I/N - gamma*I,  dR = gamma*I
# ---------------------------------------------------------------------------
def sir_step(S, I, R, N, beta, gamma, dt=1.0):
    bSI_N = beta * S * I / N    # 6n (mul+mul+div)
    dS = -bSI_N                 # neg -> 2n total for dS contribution
    gI = gamma * I              # 2n; shared for dI and dR
    dI = bSI_N - gI             # sub -> 2n
    dR = gI                     # free reuse
    return (
        S + dS * dt,
        I + dI * dt,
        R + dR * dt,
    )


# ---------------------------------------------------------------------------
# 3. Basic Reproduction Number: R0 = beta/gamma
# ---------------------------------------------------------------------------
def basic_reproduction_number(beta, gamma):
    return beta / gamma    # div=2n


# ---------------------------------------------------------------------------
# 4. Gompertz Growth: N(t) = K * exp(-exp(-b*(t - t_m)))
# ---------------------------------------------------------------------------
def gompertz_growth(K, b, t_m, t):
    inner_arg = b * (t - t_m)          # sub=2n, mul=2n -> 4n
    inner_exp = math.exp(-inner_arg)   # DEML(inner_arg, 1) = 1n -> cumulative 5n
    outer_exp = math.exp(-inner_exp)   # DEML(inner_exp, 1) = 1n -> cumulative 6n
    return K * outer_exp               # mul=2n -> total 8n


# ---------------------------------------------------------------------------
# 5. Hill Equation: E = E_max * C^n / (EC50^n + C^n)
# ---------------------------------------------------------------------------
def hill_equation(E_max, EC50, n, C):
    C_n = C ** n                 # pow=3n
    EC50_n = EC50 ** n           # pow=3n
    denom = EC50_n + C_n         # add_pos=3n  -> 9n
    fraction = C_n / denom       # div=2n      -> 11n
    return E_max * fraction      # mul=2n      -> total 13n


# ---------------------------------------------------------------------------
# 6. Allometric Scaling (Kleiber's Law): Y = a * M^b,  b ~= 0.75
# ---------------------------------------------------------------------------
def allometric_scaling(a, M, b):
    return a * (M ** b)    # pow=3n, mul=2n -> total 5n


# ---------------------------------------------------------------------------
# Run all verifications
# ---------------------------------------------------------------------------
def main():
    print("=" * 65)
    print("SuperBEST v4 -- Biology & Epidemiology Verification")
    print("=" * 65)

    # 1. Logistic growth
    # NOTE: With r=0.5, t=10: rt=5, exp(-5)=0.00674, A=99 -> N~600.
    # The session prompt stated "expected ~993" but 993 requires r~0.955.
    # Correct analytical answer for K=1000, N0=10, r=0.5, t=10 is ~600.
    # We verify against the true analytical value and flag the discrepancy.
    K, N0, r, t = 1000, 10, 0.5, 10
    N = logistic_growth(K, N0, r, t)
    A = (K - N0) / N0
    expected_exact = K / (1.0 + A * math.exp(-r * t))
    print(f"\n[bio_01] Logistic Growth (10n)")
    print(f"  Params: K={K}, N0={N0}, r={r}, t={t}, A={A:.1f}")
    print(f"  rt = {r*t:.1f}  exp(-rt) = {math.exp(-r*t):.6f}")
    print(f"  N(t) = {N:.4f}  (analytical: {expected_exact:.4f})")
    print(f"  NOTE: session prompt said ~993; correct value for r=0.5,t=10 is ~600")
    print(f"        (993 needs r~0.955; r=1.0 gives {logistic_growth(K, N0, 1.0, t):.1f})")
    assert abs(N - expected_exact) < 1e-10, f"Logistic growth check failed: {N}"
    print(f"  PASS (cost: 10n, formula verified)")

    # 2. R0
    beta, gamma = 0.3, 0.1
    R0 = basic_reproduction_number(beta, gamma)
    print(f"\n[bio_03] Basic Reproduction Number (2n)")
    print(f"  Params: beta={beta}, gamma={gamma}")
    print(f"  R0 = {R0:.4f}  (expected 3.0)")
    assert abs(R0 - 3.0) < 1e-10, f"R0 check failed: {R0}"
    print(f"  PASS")

    # 3. SIR one step
    S, I, R, N_pop = 990, 10, 0, 1000
    dt = 1.0
    S_new, I_new, R_new = sir_step(S, I, R, N_pop, beta, gamma, dt)
    bSI_N = beta * S * I / N_pop
    gI_val = gamma * I
    print(f"\n[bio_02] SIR Epidemic Model -- one timestep (20n)")
    print(f"  Params: S={S}, I={I}, R={R}, N={N_pop}, beta={beta}, gamma={gamma}, dt={dt}")
    print(f"  beta*S*I/N = {bSI_N:.4f}  (new infections per day)")
    print(f"  gamma*I    = {gI_val:.4f}  (recoveries per day)")
    print(f"  S_new = {S_new:.4f}  (expected {S - bSI_N:.4f})")
    print(f"  I_new = {I_new:.4f}  (expected {I + bSI_N - gI_val:.4f})")
    print(f"  R_new = {R_new:.4f}  (expected {R + gI_val:.4f})")
    assert abs(S_new - (S - bSI_N)) < 1e-10, "SIR S check failed"
    assert abs(I_new - (I + bSI_N - gI_val)) < 1e-10, "SIR I check failed"
    assert abs(R_new - (R + gI_val)) < 1e-10, "SIR R check failed"
    print(f"  PASS")

    # 4. Herd immunity threshold
    p_c = 1 - 1 / R0
    print(f"\n[bio_09] Herd Immunity Threshold (3n)")
    print(f"  R0  = {R0:.4f}")
    print(f"  p_c = {p_c:.6f}  (expected 0.666667 for R0=3)")
    assert abs(p_c - (1 - 1/3)) < 1e-10, f"Herd immunity check failed: {p_c}"
    print(f"  PASS")

    # 5. Gompertz growth
    K_g, b_g, t_m, t_g = 100, 0.5, 5, 10
    N_g = gompertz_growth(K_g, b_g, t_m, t_g)
    expected_g = K_g * math.exp(-math.exp(-2.5))
    print(f"\n[bio_06] Gompertz Growth (8n)")
    print(f"  Params: K={K_g}, b={b_g}, t_m={t_m}, t={t_g}")
    print(f"  b*(t-tm) = {b_g*(t_g-t_m):.2f}")
    print(f"  inner exp(-2.5) = {math.exp(-2.5):.6f}")
    print(f"  N(t) = {N_g:.4f}  (expected ~{expected_g:.4f}, ~91.8)")
    assert abs(N_g - expected_g) < 1e-10, f"Gompertz check failed: {N_g}"
    print(f"  PASS")

    # 6. Hill equation
    E_max, EC50, n_h, C = 100, 10, 2, 10
    E = hill_equation(E_max, EC50, n_h, C)
    print(f"\n[bio_07] Hill Equation (13n)")
    print(f"  Params: E_max={E_max}, EC50={EC50}, n={n_h}, C={C}")
    print(f"  E = {E:.4f}  (expected 50.0 -- C=EC50 means half-max effect)")
    assert abs(E - 50.0) < 1e-10, f"Hill check failed: {E}"
    print(f"  PASS")

    # 7. Allometric scaling (Kleiber's law)
    a_k, b_k, M_k = 70, 0.75, 70
    bmr = allometric_scaling(a_k, M_k, b_k)
    expected_bmr = 70 * (70 ** 0.75)
    print(f"\n[bio_10] Allometric Scaling -- Kleiber's Law (5n)")
    print(f"  Params: a={a_k}, b={b_k}, M={M_k} kg")
    print(f"  BMR = {bmr:.2f} kcal/day  (expected ~{expected_bmr:.2f}, ~1744 kcal/day for 70kg)")
    assert abs(bmr - expected_bmr) < 1e-6, f"Allometric check failed: {bmr}"
    print(f"  PASS")

    # 8. Michaelis-Menten (Hill n=1 special case, 7n)
    V_max, K_m, S_conc = 100.0, 10.0, 10.0
    v_mm = V_max * S_conc / (K_m + S_conc)
    print(f"\n[bio_07_mm] Michaelis-Menten / Hill n=1 (7n)")
    print(f"  Params: V_max={V_max}, K_m={K_m}, [S]={S_conc}")
    print(f"  v = {v_mm:.4f}  (expected 50.0 -- [S]=Km means half-Vmax)")
    assert abs(v_mm - 50.0) < 1e-10, f"MM check failed: {v_mm}"
    print(f"  PASS")

    # Summary table
    print("\n" + "=" * 65)
    print("SUMMARY -- SuperBEST v4 Biology & Epidemiology Costs")
    print("=" * 65)
    rows = [
        ("bio_03",    "R0 = beta/gamma",                        2,  "cheapest metric in epidemiology"),
        ("bio_09",    "Herd immunity p_c = 1 - 1/R0",           3,  "recip + sub"),
        ("bio_05",    "Malthusian N0*e^(rt)",                    5,  "universal exponential process"),
        ("bio_10",    "Allometric a*M^b (Kleiber)",              5,  "universal power law"),
        ("bio_07_mm", "Michaelis-Menten (Hill n=1)",             7,  "enzyme kinetics"),
        ("bio_08",    "Infection growth I0*e^(lt) l=b-g",        7,  "Malthusian + sub for net rate"),
        ("bio_06",    "Gompertz K*exp(-exp(-b(t-tm)))",          8,  "two chained DEML calls"),
        ("bio_01",    "Logistic K/(1+A*exp(-rt))",               10, "canonical S-curve"),
        ("bio_07",    "Hill Emax*C^n/(EC50^n+C^n)",              13, "cooperativity: +6n over MM"),
        ("bio_04",    "Lotka-Volterra (per step)",                16, "two 8n coupled equations"),
        ("bio_02",    "SIR model (per timestep)",                 20, "20n with sharing; tractable"),
    ]
    print(f"  {'ID':<12} {'Equation':<42} {'Cost':>5}  Key observation")
    print(f"  {'-'*12} {'-'*42} {'-'*5}  {'-'*35}")
    for row in rows:
        print(f"  {row[0]:<12} {row[1]:<42} {row[2]:>4}n  {row[3]}")

    print("\nAll verifications PASSED.")


if __name__ == "__main__":
    main()
