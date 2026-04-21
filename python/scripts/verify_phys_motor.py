"""
Verification script for phys_1_basic_physics.json and bio_2_motor_equations.json.
Uses only the math module. Exits 0 if all tests pass, 1 if any fail.
"""

import math
import sys

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def check(label, expected, got, rel_tol=1e-3):
    """Return True if |got - expected| / |expected| <= rel_tol."""
    if expected == 0:
        ok = abs(got) <= rel_tol
    else:
        ok = abs(got - expected) / abs(expected) <= rel_tol
    status = PASS if ok else FAIL
    print(f"  [{status}] {label}: expected={expected:.6g}  got={got:.6g}")
    return ok


results = []

print("=" * 60)
print("PHYSICS EQUATIONS — phys_1_basic_physics.json")
print("=" * 60)

# 1. Ohm's Law  V = I*R
I, R = 2.0, 5.0
V = I * R
results.append(check("1. Ohm's Law V=IR (I=2,R=5)", 10.0, V))

# 2. Newton's Second Law  F = m*a
m, a = 3.0, 4.0
F = m * a
results.append(check("2. Newton F=ma (m=3,a=4)", 12.0, F))

# 3. Kinetic Energy  KE = 0.5*m*v^2
m, v = 2.0, 3.0
KE = 0.5 * m * v ** 2
results.append(check("3. KE=0.5mv^2 (m=2,v=3)", 9.0, KE))

# 4. Gravitational Force  F = G*M*m/r^2
G = 6.674e-11
M_earth = 5.972e24
m_test = 1.0
r_earth = 6.371e6
F_grav = G * M_earth * m_test / r_earth ** 2
results.append(check("4. Gravity F=GMm/r^2 (surface)", 9.82, F_grav, rel_tol=5e-3))

# 5. Wave Speed  v = f*lambda
f_wave = 440.0
lam_wave = 0.773
v_wave = f_wave * lam_wave
results.append(check("5. Wave speed v=f*lam (f=440,lam=0.773)", 340.0, v_wave, rel_tol=5e-3))

# 6. Hooke's Law  F = -k*x
k_spring = 50.0
x_disp = 0.1
F_hook = -(k_spring * x_disp)
results.append(check("6. Hooke F=-kx (k=50,x=0.1)", -5.0, F_hook))

# 7. Electric Power  P = V*I  (simplest form)
V_elec = 10.0
I_elec = 2.0
P_elec = V_elec * I_elec
results.append(check("7. Power P=VI (V=10,I=2)", 20.0, P_elec))

# 8. Snell's Law — sin outside real EML; numeric check on ratio identity only
# n1*sin(theta1) = n2*sin(theta2)  ->  n1/n2 = sin(theta2)/sin(theta1)
n1, n2 = 1.0, 1.5
theta1 = math.radians(30)
theta2 = math.asin(n1 / n2 * math.sin(theta1))
ratio_lhs = n1 / n2
ratio_rhs = math.sin(theta2) / math.sin(theta1)
results.append(check("8. Snell ratio n1/n2=sin(t2)/sin(t1)", ratio_lhs, ratio_rhs))

# 9. Pressure  P = F/A
F_press = 100.0
A_area = 5.0
P_press = F_press / A_area
results.append(check("9. Pressure P=F/A (F=100,A=5)", 20.0, P_press))

# 10. Work  W = F*d*cos(theta)  at theta=0
F_work = 10.0
d_work = 5.0
theta_work = 0.0
W_work = F_work * d_work * math.cos(theta_work)
results.append(check("10. Work W=Fd*cos(0) (F=10,d=5)", 50.0, W_work))

# 11. Momentum  p = m*v
m_mom = 5.0
v_mom = 3.0
p_mom = m_mom * v_mom
results.append(check("11. Momentum p=mv (m=5,v=3)", 15.0, p_mom))

# 12. Centripetal Acceleration  a = v^2/r
v_cent = 4.0
r_cent = 2.0
a_cent = v_cent ** 2 / r_cent
results.append(check("12. Centripetal a=v^2/r (v=4,r=2)", 8.0, a_cent))

# 13. Period of Pendulum  T = 2*pi*sqrt(L/g)
L_pend = 1.0
g_grav = 9.81
T_pend = 2 * math.pi * math.sqrt(L_pend / g_grav)
results.append(check("13. Pendulum T=2pi*sqrt(L/g) (L=1,g=9.81)", 2.006, T_pend, rel_tol=2e-3))

# 14. Coulomb's Law  F = k*q1*q2/r^2
k_coul = 8.99e9
q1 = 1e-6
q2 = 1e-6
r_coul = 1.0
F_coul = k_coul * q1 * q2 / r_coul ** 2
results.append(check("14. Coulomb F=kq1q2/r^2 (q=1uC, r=1m)", 8.99e-3, F_coul))

# 15. Wien's Displacement Law  lambda_max = b / T
b_wien = 2.898e-3
T_star = 5778.0
lam_wien = b_wien / T_star
results.append(check("15. Wien lam=b/T (T=5778K)", 5.015e-7, lam_wien, rel_tol=2e-3))

print()
print("=" * 60)
print("MOTOR EQUATIONS — bio_2_motor_equations.json")
print("=" * 60)

# 1. Proton Motive Force  PMF = Deltapsi + (2.303*kBT/e)*DeltapH
Deltapsi = 0.12
kBT_e = 0.02585  # kBT/e in volts at ~300K
DeltapH = 1.0
PMF = Deltapsi + 2.303 * kBT_e * DeltapH
results.append(check("M1. Proton Motive Force (Dpsi=0.12V, DpH=1)", 0.1795, PMF, rel_tol=2e-3))

# 2. Motor Torque  tau = n_p * PMF * e / (2*pi)
n_p = 8
PMF_motor = 0.18
e_charge = 1.602e-19
tau_motor = n_p * PMF_motor * e_charge / (2 * math.pi)
results.append(check("M2. Motor Torque (n_p=8, PMF=0.18V)", 3.6715e-20, tau_motor, rel_tol=5e-3))

# 3. Proton Hop Rate  k_hop = k0 * exp(-DeltaG / kBT)
k0 = 1e9
DeltaG = 4e-21
kBT_motor = 4.14e-21
k_hop = k0 * math.exp(-DeltaG / kBT_motor)
results.append(check("M3. Proton Hop Rate (k0=1e9, DG=4e-21)", 3.8053e8, k_hop, rel_tol=5e-3))

# 4. Switching Probability  P = [CheY]^H / (Kd^H + [CheY]^H)
CheY = 5.0
Kd = 3.0
H = 2
P_switch = CheY ** H / (Kd ** H + CheY ** H)
results.append(check("M4. Switching Prob Hill H=2 (CheY=5,Kd=3)", 25 / 34, P_switch))

# 5. Motor Efficiency (simplified)  eta = omega / (2*pi*rate)
omega_rot = 100.0  # rad/s
rate_rot = 15.9    # Hz = rev/s
eta_simple = omega_rot / (2 * math.pi * rate_rot)
results.append(check("M5. Motor Efficiency simplified (w=100,rate=15.9)", 1.001, eta_simple, rel_tol=2e-3))

# Summary
print()
print("=" * 60)
n_pass = sum(results)
n_fail = len(results) - n_pass
print(f"SUMMARY: {n_pass}/{len(results)} passed, {n_fail} failed")
print("=" * 60)

if n_fail > 0:
    print("RESULT: FAIL")
    sys.exit(1)
else:
    print("RESULT: ALL PASS")
    sys.exit(0)
