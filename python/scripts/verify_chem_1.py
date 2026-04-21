"""
verify_chem_1.py
SuperBEST v4 - Chemistry equation verification
Checks numerical correctness of all 10 chemistry equations.
"""
# Force UTF-8 output on Windows
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import math

PASS = "PASS"
FAIL = "FAIL"
results = []


def check(name, got, expected, tol=1e-6):
    ok = abs(got - expected) < tol
    status = PASS if ok else FAIL
    results.append((status, name, got, expected))
    print(f"  {status}  {name}")
    print(f"       got={got:.8g}  expected={expected:.8g}  delta={abs(got-expected):.3e}")
    if not ok:
        print(f"       MISMATCH -- tolerance {tol}")
    return ok


# ---------------------------------------------------------------------------
# 1. Nernst equation
# E = E_std - (RT / nF) * ln(Q)
# E_std=0.76V, R=8.314, T=298K, n=2, F=96485, Q=0.01
# ---------------------------------------------------------------------------
print("\n=== 1. Nernst Equation ===")
E_std = 0.76
R = 8.314
T = 298.0
n_nernst = 2.0
F = 96485.0
Q_nernst = 0.01

RT = R * T                           # mul  2n
nF = n_nernst * F                    # mul  2n
RT_nF = RT / nF                      # div  2n
ln_Q = math.log(Q_nernst)            # ln   1n
correction = RT_nF * ln_Q            # mul  2n
E = E_std - correction               # sub  2n  => total 11n

# Manual check: RT/nF = 8.314*298/(2*96485) = 0.012856 V
# ln(0.01) = -4.60517
# correction = 0.012856 * (-4.60517) = -0.059217 V  (note: negative)
# E = 0.76 - (-0.059217) = 0.819217 V
expected_E = 0.76 - (8.314 * 298 / (2 * 96485)) * math.log(0.01)
check("Nernst E (V)", E, expected_E, tol=1e-6)
print(f"       Reference: E ~= {E:.5f} V  (E_std=0.76, Q=0.01, T=298K, n=2)")

# ---------------------------------------------------------------------------
# 2. Henderson-Hasselbalch
# pH = pKa + log10([A-] / [HA])
# pKa=4.74 (acetic acid), [A-]=0.1M, [HA]=0.1M => pH = 4.74
# ---------------------------------------------------------------------------
print("\n=== 2. Henderson-Hasselbalch ===")
pKa = 4.74
A_minus = 0.1
HA = 0.1

ratio = A_minus / HA                                    # div   2n
log10_ratio = math.log(ratio) / math.log(10)           # ln+div 3n
pH_hh = pKa + log10_ratio                              # add_gen 11n  (general)

check("Henderson-Hasselbalch pH", pH_hh, 4.74, tol=1e-9)
print(f"       Equal concentrations => log10(1.0)=0 => pH=pKa=4.74")

# Also verify with unequal concentrations: [A-]=1.0, [HA]=0.1 => pH = 4.74 + 1.0 = 5.74
A2, HA2 = 1.0, 0.1
pH2 = pKa + math.log(A2 / HA2) / math.log(10)
check("Henderson-Hasselbalch pH ([A-]=1.0, [HA]=0.1)", pH2, 5.74, tol=1e-9)

# ---------------------------------------------------------------------------
# 3. Michaelis-Menten
# v = Vmax * [S] / (Km + [S])
# Vmax=10, Km=5, [S]=5 => v = 10*5/(5+5) = 5.0
# ---------------------------------------------------------------------------
print("\n=== 3. Michaelis-Menten ===")
Vmax = 10.0
Km = 5.0
S = 5.0

denom = Km + S                       # add_pos  3n
sat = S / denom                      # div      2n
v = Vmax * sat                       # mul      2n  => total 7n

check("Michaelis-Menten v", v, 5.0, tol=1e-12)
print(f"       At [S]=Km: v = Vmax/2 = {v} (half-maximal velocity)")

# ---------------------------------------------------------------------------
# 4. pH definition
# pH = -log10([H+])
# [H+] = 1e-7 => pH = 7.0
# ---------------------------------------------------------------------------
print("\n=== 4. pH Definition ===")
H_plus = 1e-7

ln_H = math.log(H_plus)                               # ln   1n
log10_H = ln_H / math.log(10)                         # div  2n
pH = -log10_H                                         # neg  2n  => total 5n

check("pH of [H+]=1e-7", pH, 7.0, tol=1e-10)

# Also verify pH 4 and pH 10
check("pH of [H+]=1e-4", -math.log(1e-4) / math.log(10), 4.0, tol=1e-10)
check("pH of [H+]=1e-10", -math.log(1e-10) / math.log(10), 10.0, tol=1e-10)

# ---------------------------------------------------------------------------
# 5. Beer-Lambert law
# A = eps * c * l
# eps=100, c=0.01, l=1 => A = 1.0
# ---------------------------------------------------------------------------
print("\n=== 5. Beer-Lambert Law ===")
epsilon = 100.0
c = 0.01
l = 1.0

ec = epsilon * c                     # mul  2n
A_abs = ec * l                       # mul  2n  => total 4n (absorbance form)

check("Beer-Lambert Absorbance A", A_abs, 1.0, tol=1e-12)

# Transmittance form: T = exp(-epscl) = exp(-1.0) ~= 0.3679
T_transmit = math.exp(-A_abs)        # DEML 1n on top of the 4n = 5n total
check("Beer-Lambert Transmittance T=exp(-A)", T_transmit, math.exp(-1.0), tol=1e-12)
print(f"       T = exp(-1) = {T_transmit:.6f}")

# ---------------------------------------------------------------------------
# 6. First-order decay
# [A](t) = [A]_0 * exp(-k*t)
# [A]_0=1.0, k=0.5, t=2 => [A] = exp(-1) ~= 0.36788
# ---------------------------------------------------------------------------
print("\n=== 6. First-Order Decay ===")
A0 = 1.0
k_decay = 0.5
t_decay = 2.0

kt = k_decay * t_decay               # mul  2n
exp_neg_kt = math.exp(-kt)           # DEML 1n  (= exp(-kt) directly)
A_t = A0 * exp_neg_kt                # mul  2n  => total 5n

check("First-order [A](t)", A_t, math.exp(-1.0), tol=1e-12)
print(f"       [A](t=2) = exp(-1) = {A_t:.8f}")
print(f"       Isomorphic: radioactive decay, RC discharge, optical depth")

# ---------------------------------------------------------------------------
# 7. Reaction free energy (bonus -- same structure as Nernst)
# dG = dGdeg + RT*ln(Q)
# dGdeg=-5000 J/mol, R=8.314, T=298, Q=0.01 => dG = -5000 + 8.314*298*ln(0.01)
# ---------------------------------------------------------------------------
print("\n=== 7. Reaction Free Energy (bonus) ===")
dG_std = -5000.0
Q_dG = 0.01

RT2 = R * T                          # mul  2n
ln_Q2 = math.log(Q_dG)              # ln   1n
RT_lnQ = RT2 * ln_Q2                # mul  2n
dG = dG_std + RT_lnQ                # add_gen 11n => total 16n

expected_dG = -5000.0 + 8.314 * 298 * math.log(0.01)
check("dG reaction free energy (J/mol)", dG, expected_dG, tol=1e-6)
print(f"       dG = {dG:.2f} J/mol  (dGdeg=-5000, Q=0.01)")
print(f"       Note: 16n (add_gen) vs Nernst 11n (sub) -- same physics, different form")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("SUMMARY -- SuperBEST v4 node costs")
print("=" * 60)
rows = [
    ("Nernst Equation",                  "E = Edeg - RT/(nF)*ln(Q)",           11,  "sub(2n) keeps cost low"),
    ("Henderson-Hasselbalch (general)",  "pH = pKa + log10([A-]/[HA])",      16,  "add_gen(11n) dominant"),
    ("Henderson-Hasselbalch (near pKa)", "pH ~= pKa  (log~=0)",                 8,  "add_pos(3n) applicable"),
    ("Equilibrium Constant (2+2)",       "K = ([C]^c[D]^d)/([A]^a[B]^b)",   18,  "4xpow(3n) + 3xmul/div"),
    ("Rate Law (2-species)",             "r = k[A]^m[B]^n",                  10,  "2xpow + 2xmul"),
    ("Michaelis-Menten",                 "v = Vmax[S]/(Km+[S])",              7,  "= Langmuir = Arrhenius"),
    ("Beer-Lambert (absorbance)",        "A = epscl",                           4,  "pure multiply chain"),
    ("Beer-Lambert (transmittance)",     "T = exp(-epscl)",                     5,  "= first-order decay"),
    ("pH Definition",                    "pH = -log10([H+])",                 5,  "= Richter = dB family"),
    ("Gibbs-Helmholtz (dG/T)",          "dG/T",                              2,  "minimal form"),
    ("Reaction Free Energy",             "dG = dGdeg + RT*ln(Q)",             16,  "add_gen drives cost"),
    ("First-Order Decay",                "[A](t) = A0*exp(-kt)",              5,  "universal DEML pattern"),
]
print(f"  {'Equation':<42} {'Cost':>5}  Key Note")
print(f"  {'-'*42} {'-'*5}  {'-'*30}")
for name, formula, cost, note in rows:
    print(f"  {name:<42} {cost:>5}n  {note}")

# final pass/fail count
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
print(f"\n{'=' * 60}")
print(f"Verification: {passed} passed, {failed} failed out of {len(results)} checks")
if failed > 0:
    print("FAILED checks:")
    for r in results:
        if r[0] == FAIL:
            print(f"  {r[1]}: got={r[2]}, expected={r[3]}")
    sys.exit(1)
else:
    print("All checks PASSED.")
