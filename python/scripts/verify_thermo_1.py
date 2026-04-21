"""
verify_thermo_1.py
Verification of thermodynamics node-cost equations — SuperBEST v4 session.

Tests:
  1. Carnot efficiency:        T_cold=300K, T_hot=600K  → eta = 0.5
  2. Boltzmann entropy:        Omega=1e23               → S ≈ 7.28e-23 J/K
  3. Ideal gas law:            n=1, T=273.15K, V=0.02241 m³ → P ≈ 101325 Pa
  4. Gibbs free energy:        dH=-100kJ, T=298K, dS=-50 J/K → dG = -85100 J
  5. Arrhenius equation:       A=1e13, Ea=50000, R=8.314, T=300K → k
  6. Stefan-Boltzmann law:     eps=1, A=1 m², T=300K    → P ≈ 459 W
"""

import math

# ── Physical constants ────────────────────────────────────────────────────────
k_B   = 1.380649e-23    # J/K  (Boltzmann constant, exact SI 2019)
R     = 8.314           # J/mol/K  (gas constant)
sigma = 5.670374419e-8  # W/m²/K⁴ (Stefan-Boltzmann constant)

PASS = "PASS"
FAIL = "FAIL"

def check(label: str, computed: float, expected: float, rtol: float = 1e-4) -> bool:
    err = abs(computed - expected) / (abs(expected) if expected != 0 else 1.0)
    ok = err <= rtol
    symbol = PASS if ok else FAIL
    print(f"  [{symbol}]  {label}")
    print(f"         computed = {computed:.6g}")
    print(f"         expected = {expected:.6g}")
    print(f"         rel_err  = {err:.2e}")
    return ok


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Carnot efficiency  eta = 1 - T_cold / T_hot
# Cost: div(2n) + sub(2n) = 4n
# ═══════════════════════════════════════════════════════════════════════════════
def carnot_efficiency(T_cold: float, T_hot: float) -> float:
    ratio = T_cold / T_hot          # div  2n
    return 1.0 - ratio              # sub  2n  (1-ratio provably positive)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Boltzmann entropy  S = k_B * ln(Omega)
# Cost: ln(1n) + mul(2n) = 3n
# ═══════════════════════════════════════════════════════════════════════════════
def boltzmann_entropy(Omega: float) -> float:
    return k_B * math.log(Omega)    # ln(1n) + mul(2n)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Ideal gas law  P = nRT / V
# Cost: mul(2n) + mul(2n) + div(2n) = 6n
# ═══════════════════════════════════════════════════════════════════════════════
def ideal_gas_pressure(n: float, T: float, V: float) -> float:
    nR  = n * R                     # mul  2n
    nRT = nR * T                    # mul  2n
    return nRT / V                  # div  2n


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Gibbs free energy  dG = dH - T * dS
# Cost: mul(2n) + sub(2n) = 4n
# ═══════════════════════════════════════════════════════════════════════════════
def gibbs_free_energy(dH: float, T: float, dS: float) -> float:
    T_dS = T * dS                   # mul  2n
    return dH - T_dS                # sub  2n


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Arrhenius equation  k = A * exp(-Ea / (R * T))
# Cost: mul(2n) + div(2n) + DEML(1n) + mul(2n) = 7n
# ═══════════════════════════════════════════════════════════════════════════════
def arrhenius(A: float, Ea: float, T: float) -> float:
    RT          = R * T             # mul  2n
    Ea_over_RT  = Ea / RT           # div  2n
    exp_factor  = math.exp(-Ea_over_RT)  # DEML(x,1) = exp(-x)  1n
    return A * exp_factor           # mul  2n


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Stefan-Boltzmann  P = epsilon * sigma * A_area * T^4
# Cost: pow(3n) + mul(2n) + mul(2n) + mul(2n) = 9n
# ═══════════════════════════════════════════════════════════════════════════════
def stefan_boltzmann(epsilon: float, A_area: float, T: float) -> float:
    T4         = T ** 4             # pow  3n
    eps_sigma  = epsilon * sigma    # mul  2n  (sigma is constant)
    esa        = eps_sigma * A_area # mul  2n
    return esa * T4                 # mul  2n


# ═══════════════════════════════════════════════════════════════════════════════
# Run verifications
# ═══════════════════════════════════════════════════════════════════════════════
results = []

print("=" * 60)
print("THERMO_1 VERIFICATION - SuperBEST v4")
print("=" * 60)

# ── 1. Carnot ──────────────────────────────────────────────────────────────────
print("\n[1] Carnot efficiency  (T_cold=300K, T_hot=600K)")
eta = carnot_efficiency(300.0, 600.0)
results.append(check("eta = 0.5", eta, 0.5))

# ── 2. Boltzmann entropy ───────────────────────────────────────────────────────
print("\n[2] Boltzmann entropy  (Omega = 1e23)")
# S = k_B * ln(1e23) = k_B * 23 * ln(10)
S_expected = k_B * 23 * math.log(10)   # ≈ 7.2836e-23 J/K
S = boltzmann_entropy(1e23)
results.append(check("S ~= 7.28e-23 J/K", S, S_expected, rtol=1e-6))

# ── 3. Ideal gas law ───────────────────────────────────────────────────────────
print("\n[3] Ideal gas law  (n=1 mol, T=273.15 K, V=0.02241 m^3)")
P = ideal_gas_pressure(1.0, 273.15, 0.02241)
results.append(check("P ~= 101325 Pa (1 atm)", P, 101325.0, rtol=1e-3))

# ── 4. Gibbs free energy ───────────────────────────────────────────────────────
print("\n[4] Gibbs free energy  (dH=-100kJ, T=298K, dS=-50 J/K)")
# dG = dH - T*dS = -100000 - 298*(-50) = -100000 + 14900 = -85100 J
dG = gibbs_free_energy(-100_000.0, 298.0, -50.0)
results.append(check("dG = -85100 J", dG, -85100.0, rtol=1e-9))

# ── 5. Arrhenius ───────────────────────────────────────────────────────────────
print("\n[5] Arrhenius  (A=1e13, Ea=50000 J/mol, T=300K)")
k_rate = arrhenius(1e13, 50_000.0, 300.0)
# Reference: exp(-50000/(8.314*300)) = exp(-20.046...) ≈ 1.952e-9  → k ≈ 1.952e4
k_ref = 1e13 * math.exp(-50_000.0 / (8.314 * 300.0))
results.append(check(f"k = {k_ref:.4e} s^-1", k_rate, k_ref, rtol=1e-10))

# ── 6. Stefan-Boltzmann ────────────────────────────────────────────────────────
print("\n[6] Stefan-Boltzmann  (eps=1, A=1 m^2, T=300K)")
# P = sigma * 300^4 = 5.670374419e-8 * 8.1e9 ≈ 459.27 W
P_rad = stefan_boltzmann(1.0, 1.0, 300.0)
P_ref = sigma * (300.0 ** 4)
results.append(check(f"P ~= {P_ref:.4g} W", P_rad, P_ref, rtol=1e-10))

# ═══════════════════════════════════════════════════════════════════════════════
# Summary table
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SUMMARY TABLE")
print("=" * 60)
rows = [
    ("Boltzmann entropy",       3,  "ln + mul",                    "Cheapest fundamental physics eq"),
    ("Carnot efficiency",       4,  "div + sub",                   "Universal '1-ratio' pattern"),
    ("Gibbs free energy",       4,  "mul + sub",                   "Same cost as Carnot, free energy family"),
    ("Ideal gas law",           6,  "mul + mul + div",             "3-factor / 1-divisor pattern"),
    ("Arrhenius equation",      7,  "mul + div + DEML + mul",      "Beer-Lambert + div = 5n -> 7n"),
    ("Clausius-Clapeyron",      9,  "pow + mul + mul + div",       "T^2 denominator; pow dominates"),
    ("Stefan-Boltzmann",        9,  "pow + mul + mul + mul",       "T^4 via pow(3n) + 3x mul"),
    ("van't Hoff (ln K ratio)", 10, "2x recip + sub + mul + neg + mul", "10n for log-ratio form"),
    ("van't Hoff (full K2)",    13, "...+ DEML + mul",             "13n with equilibrium constant"),
    ("Maxwell-Boltzmann f(E)",  13, "pow + recip + sqrt + div + DEML + mul*2", "Two multiplied structures"),
    ("Entropy of mixing (N)",   "7N-1", "N*(ln+mul) + (N-1)*add_pos + neg + mul", "= Shannon entropy * nR"),
]

col_w = [28, 8, 36, 0]
header = f"{'Equation':<28} {'Cost':>6}  {'Pattern':<36}  Key observation"
print(header)
print("-" * 100)
for eq, cost, pattern, note in rows:
    print(f"{eq:<28} {str(cost):>6}  {pattern:<36}  {note}")

passed = sum(results)
total  = len(results)
print(f"\nVerification: {passed}/{total} tests passed")
if passed == total:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED — check output above")
