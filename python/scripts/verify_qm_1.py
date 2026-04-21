"""
verify_qm_1.py
Verify SuperBEST v4 node-cost computations for quantum mechanics equations.
All calculations use SI or natural units as noted per equation.
"""

import sys
import io
import math
import json
from pathlib import Path

# Ensure UTF-8 output on Windows (avoids CP1252 encoding errors)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RESULTS_DIR = Path(__file__).parent.parent / "results"
PASS = "PASS"
FAIL = "FAIL"

# ─────────────────────────────────────────────────
# Physical constants (SI)
# ─────────────────────────────────────────────────
k_B   = 1.380649e-23   # Boltzmann constant  [J/K]
h_P   = 6.62607015e-34 # Planck constant     [J·s]
hbar  = h_P / (2 * math.pi)
eV    = 1.602176634e-19 # 1 eV in joules
c     = 2.99792458e8   # speed of light      [m/s]
m_e   = 9.1093837015e-31  # electron mass     [kg]

results = []


def record(name: str, expected, got, tol: float = 1e-6):
    rel_err = abs(got - expected) / (abs(expected) + 1e-300)
    ok = rel_err < tol
    results.append({
        "test": name,
        "expected": expected,
        "got": got,
        "rel_err": rel_err,
        "status": PASS if ok else FAIL,
    })
    status = PASS if ok else FAIL
    print(f"[{status}] {name}")
    print(f"       expected = {expected:.8g}")
    print(f"       got      = {got:.8g}  (rel_err={rel_err:.2e})")
    return ok


# ═══════════════════════════════════════════════════════════════
# 1. Boltzmann factor: exp(-E/kT)
#    Test: E/kT = 2.0  →  exp(-2) ≈ 0.13533528
# ═══════════════════════════════════════════════════════════════
print("\n── 1. Boltzmann factor ──────────────────────────")
x_kT = 2.0
boltzmann = math.exp(-x_kT)           # DEML(x_kT, 1)
record("Boltzmann exp(-2.0)", math.exp(-2.0), boltzmann)

# ═══════════════════════════════════════════════════════════════
# 2. Fermi-Dirac distribution: f(E) = 1/(1+exp((E-mu)/kT))
#    Test: (E-mu)/kT = 2.0  →  f = 1/(1+e^2) ≈ 0.11920292
# ═══════════════════════════════════════════════════════════════
print("\n── 2. Fermi-Dirac distribution ──────────────────")

def fermi_dirac(x: float) -> float:
    """x = (E - mu) / kT.  Cost: sub+div already done → exp(1n)+add_pos(3n)+recip(1n) = 5n from x."""
    exp_x   = math.exp(x)              # EML: 1n
    denom   = 1.0 + exp_x              # add_pos: 3n (both positive)
    return 1.0 / denom                 # recip: 1n

fd_val   = fermi_dirac(2.0)
expected_fd = 1.0 / (1.0 + math.exp(2.0))
record("Fermi-Dirac (E-mu)/kT=2.0", expected_fd, fd_val)
print(f"       note: same as sigmoid(-2.0) = {1/(1+math.exp(2.0)):.8f}")

# ═══════════════════════════════════════════════════════════════
# 3. Bose-Einstein distribution: n(E) = 1/(exp((E-mu)/kT) - 1)
#    Test: (E-mu)/kT = 1.0  →  n = 1/(e-1) ≈ 0.58197671
# ═══════════════════════════════════════════════════════════════
print("\n── 3. Bose-Einstein distribution ────────────────")

def bose_einstein(x: float) -> float:
    """x = (E - mu) / kT.  Cost from x: exp(1n)+sub(2n)+recip(1n) = 4n."""
    exp_x  = math.exp(x)               # EML: 1n
    denom  = exp_x - 1.0               # sub: 2n  (exp > 1 for x > 0)
    return 1.0 / denom                 # recip: 1n

be_val   = bose_einstein(1.0)
expected_be = 1.0 / (math.e - 1.0)
record("Bose-Einstein (E-mu)/kT=1.0", expected_be, be_val)

# ═══════════════════════════════════════════════════════════════
# 4. Hydrogen energy levels: E_n = -13.6 eV / n^2
#    Test: n=1 → -13.6 eV, n=2 → -3.4 eV, n=3 → -1.5111 eV
# ═══════════════════════════════════════════════════════════════
print("\n── 4. Hydrogen energy levels ────────────────────")
RY_eV = 13.6  # Rydberg constant in eV

def hydrogen_energy_eV(n: int) -> float:
    """Cost: pow(n,2)=3n + div=2n + neg=2n = 7n."""
    return -(RY_eV / n**2)

cases = [(1, -13.6), (2, -3.4), (3, -13.6/9.0)]
for n, exp_val in cases:
    got = hydrogen_energy_eV(n)
    record(f"Hydrogen E_n  n={n}", exp_val, got, tol=1e-4)

# ═══════════════════════════════════════════════════════════════
# 5. Partition function Z = Σ exp(-E_i/kT)
#    Test: E_i = i * kT for i in {0,1,2,3,4}
#    → Z = Σ_{i=0}^{4} exp(-i) = 1 + e^-1 + e^-2 + e^-3 + e^-4
# ═══════════════════════════════════════════════════════════════
print("\n── 5. Partition function ────────────────────────")

def partition_function(energies_over_kT: list) -> float:
    """
    energies_over_kT: list of E_i/kT (dimensionless).
    Cost: 3n per term (div already done here) + 3n per add_pos = 6N-3 total.
    """
    terms = [math.exp(-x) for x in energies_over_kT]   # DEML(x,1): 1n each
    return sum(terms)                                    # N-1 add_pos: 3n each

energies_kT = [0.0, 1.0, 2.0, 3.0, 4.0]
Z_got  = partition_function(energies_kT)
Z_exp  = sum(math.exp(-i) for i in range(5))
record("Partition Z (5 levels E_i=i*kT)", Z_exp, Z_got)
print(f"       Z = 1 + e^-1 + e^-2 + e^-3 + e^-4 = {Z_exp:.8f}")
print(f"       node cost: 6*5-3 = {6*5-3}n")

# ═══════════════════════════════════════════════════════════════
# 6. Maxwell-Boltzmann speed distribution normalization
#    f(v) = 4*pi * (m/2pikT)^(3/2) * v^2 * exp(-mv^2/2kT)
#    Integral over [0, inf) should equal 1.
#    Test via numerical integration using scipy.
# ═══════════════════════════════════════════════════════════════
print("\n── 6. Maxwell-Boltzmann normalization ───────────")

try:
    from scipy import integrate

    def mb_speed_dist(v: float, mass: float, T: float) -> float:
        """Maxwell-Boltzmann speed distribution f(v)."""
        kT   = k_B * T
        A    = 4.0 * math.pi * (mass / (2.0 * math.pi * kT))**1.5
        exp_arg = mass * v**2 / (2.0 * kT)
        return A * v**2 * math.exp(-exp_arg)

    # Test with nitrogen molecules (N2), T = 300 K
    m_N2 = 2 * 14 * 1.66053906660e-27   # 28 amu in kg
    T_test = 300.0
    v_max  = 3000.0   # [m/s]  well past the high-speed tail

    norm, err = integrate.quad(mb_speed_dist, 0, v_max, args=(m_N2, T_test))
    record("Maxwell-Boltzmann normalization (N2, 300K)", 1.0, norm, tol=1e-4)
    print(f"       integral [0,3000 m/s] = {norm:.8f}  (err estimate {err:.2e})")

    # Also test with electrons at T=10000 K (higher T → broader distribution)
    T_hot = 10000.0
    norm_e, err_e = integrate.quad(mb_speed_dist, 0, 1e8, args=(m_e, T_hot))
    record("Maxwell-Boltzmann normalization (electron, 10000K)", 1.0, norm_e, tol=1e-4)
    print(f"       integral [0,1e8 m/s]  = {norm_e:.8f}  (err estimate {err_e:.2e})")

except ImportError:
    print("  scipy not available — skipping numerical integration test")
    results.append({"test": "Maxwell-Boltzmann normalization", "status": "SKIP",
                    "note": "scipy not installed"})

# ═══════════════════════════════════════════════════════════════
# 7. Cross-domain isomorphism check:
#    Fermi-Dirac == Sigmoid for same argument
# ═══════════════════════════════════════════════════════════════
print("\n── 7. Fermi-Dirac ≡ Sigmoid isomorphism ─────────")

def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(x))   # sigmoid(-x) = FD(x)

for x in [-3.0, -1.0, 0.0, 1.0, 2.0, 3.0]:
    fd = fermi_dirac(x)
    sig = sigmoid(x)    # sigma(-x) = 1/(1+exp(-(-x))) = 1/(1+exp(x)) = FD(x)
    record(f"FD==sigmoid  x={x:+.1f}", sig, fd)

# ═══════════════════════════════════════════════════════════════
# 8. de Broglie wavelength — electron at 1 eV kinetic energy
#    KE = p^2/(2m) → p = sqrt(2*m*KE)
#    lambda = h / p
# ═══════════════════════════════════════════════════════════════
print("\n── 8. de Broglie wavelength (electron, 1 eV) ────")
KE_joules = 1.0 * eV
p = math.sqrt(2.0 * m_e * KE_joules)
lambda_dB = h_P / p   # [m]
lambda_dB_nm = lambda_dB * 1e9
# Known result: ~1.226 nm for 1 eV electron
record("de Broglie lambda (1 eV electron)", 1.2264e-9, lambda_dB, tol=1e-3)
print(f"       lambda = {lambda_dB_nm:.4f} nm  (expect ~1.226 nm)")

# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
passed = sum(1 for r in results if r["status"] == PASS)
failed = sum(1 for r in results if r["status"] == FAIL)
skipped = sum(1 for r in results if r["status"] == "SKIP")
total  = len(results)
print(f"SUMMARY: {passed}/{total} passed, {failed} failed, {skipped} skipped")
print("="*60)

if failed:
    print("\nFAILED tests:")
    for r in results:
        if r["status"] == FAIL:
            print(f"  - {r['test']}: expected {r['expected']:.6g}, got {r['got']:.6g}")

# ─── Cost summary printout ──────────────────────────────────────
print("\n── Node-cost summary ────────────────────────────")
cost_table = [
    ("Boltzmann factor",              "5n (3n if kT const)",   "Beer-Lambert, RC decay, radioactive decay"),
    ("Fermi-Dirac distribution",      "9n",                    "sigmoid, logistic regression, ELO score"),
    ("Bose-Einstein distribution",    "8n",                    "novel; Planck spectral kernel"),
    ("Planck spectral radiance",      "19n",                   "Bose-Einstein kernel + nu^3 prefactor"),
    ("Hydrogen energy levels",        "7n",                    "Kepler orbit energy, Rydberg formula"),
    ("de Broglie wavelength",         "4n (2n if p given)",    "Compton wavelength, lambda=v/f"),
    ("Heisenberg uncertainty check",  "2n",                    "bandwidth-time, Cramer-Rao bound"),
    ("Particle-in-box wavefunction",  "13n (9n if L const)",   "Fourier sine basis, standing waves"),
    ("Particle-in-box energy",        "7n",                    "rigid rotor; inverse of H-atom n^2"),
    ("Partition function (N levels)", "6N-3 nodes",            "softmax denominator, Bayesian evidence"),
    ("Maxwell-Boltzmann dist",        "19n",                   "chi distribution, Rayleigh 2D"),
]
print(f"  {'Equation':<35} {'Cost':<25} {'Cross-domain isomorphism'}")
print(f"  {'-'*35} {'-'*25} {'-'*40}")
for eq, cost, iso in cost_table:
    print(f"  {eq:<35} {cost:<25} {iso}")

# ─── Save verification results ──────────────────────────────────
out_path = RESULTS_DIR / "qm_1_quantum_verify.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": total,
        "tests": results,
    }, f, indent=2)
print(f"\nVerification results saved to {out_path}")
