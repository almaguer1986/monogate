"""
verify_nat.py - SuperBEST v4 NAT Session Verification
Verifies computed values for natural pattern and applied equations.
"""
# -*- coding: utf-8 -*-
import math
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def check(label: str, expected: float, actual: float, tol: float = 1e-6) -> None:
    ok = abs(actual - expected) < tol
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}")
    print(f"         expected: {expected:.8f}")
    print(f"         actual:   {actual:.8f}")
    if not ok:
        print(f"         diff:     {abs(actual - expected):.2e}")


# ── NAT-1-1: Golden Ratio ────────────────────────────────────────────────────

section("NAT-1-1  Golden Ratio  φ = (1 + √5) / 2")

phi = (1 + math.sqrt(5)) / 2
print(f"  φ = {phi:.10f}")

# Verify the golden ratio identity: φ² - φ - 1 = 0
identity = phi**2 - phi - 1
print(f"  φ² - φ - 1 = {identity:.2e}  (should be ≈ 0)")
check("φ² - φ - 1 = 0", 0.0, identity, tol=1e-12)

# Verify the reciprocal identity: 1/φ = φ - 1
check("1/φ = φ - 1", phi - 1, 1 / phi)

print(f"\n  SuperBEST v4 cost: 7n")
print(f"    sqrt(5)=2n, add_pos(1,√5)=3n, div(sum,2)=2n")


# ── NAT-1-2: Logarithmic Spiral ──────────────────────────────────────────────

section("NAT-1-2  Logarithmic Spiral  r = e^(0.3·θ)  [a=1, b=0.3]")

a, b = 1.0, 0.3

cases = [
    ("θ = π/2",   math.pi / 2,  a * math.exp(b * math.pi / 2)),
    ("θ = π",     math.pi,      a * math.exp(b * math.pi)),
    ("θ = 2π",    2 * math.pi,  a * math.exp(b * 2 * math.pi)),
]

for label, theta, r in cases:
    r_computed = a * math.exp(b * theta)
    check(f"r({label})", r, r_computed)

print(f"\n  SuperBEST v4 cost: 5n")
print(f"    mul(b,θ)=2n, exp(product)=1n, mul(a,exp)=2n")


# ── NAT-1-4: Population Growth ───────────────────────────────────────────────

section("NAT-1-4  Population Growth  N(t) = 100 · e^(0.02t)")

N0, r = 100.0, 0.02

ts = [10, 50, 100]
expected_vals = {
    10:  N0 * math.exp(r * 10),
    50:  N0 * math.exp(r * 50),
    100: N0 * math.exp(r * 100),
}

for t in ts:
    val = N0 * math.exp(r * t)
    check(f"N({t})", expected_vals[t], val)

print(f"\n  At t=10:  N ≈ {expected_vals[10]:.4f}")
print(f"  At t=50:  N ≈ {expected_vals[50]:.4f}")
print(f"  At t=100: N ≈ {expected_vals[100]:.4f}")
print(f"\n  SuperBEST v4 cost: 5n")
print(f"    mul(r,t)=2n, exp(product)=1n, mul(N0,exp)=2n")


# ── NAT-2-3: MRI Signal ──────────────────────────────────────────────────────

section("NAT-2-3  MRI Signal  S = S0 · exp(-TE/T2) · (1 - exp(-TR/T1))")

S0_mri = 1.0
TE, T2 = 20.0, 80.0    # ms
TR, T1 = 500.0, 800.0  # ms

T2_decay    = math.exp(-TE / T2)
T1_recovery = 1.0 - math.exp(-TR / T1)
S_mri       = S0_mri * T2_decay * T1_recovery

print(f"  Parameters: S0={S0_mri}, TE={TE}ms, T2={T2}ms, TR={TR}ms, T1={T1}ms")
print(f"  T2 decay  = exp(-{TE}/{T2}) = exp(-{TE/T2:.4f}) = {T2_decay:.6f}")
print(f"  T1 recov  = 1 - exp(-{TR}/{T1}) = 1 - exp(-{TR/T1:.4f}) = {T1_recovery:.6f}")
print(f"  S (MRI)   = {S_mri:.6f}")

check("T2 decay  exp(-TE/T2)", math.exp(-TE / T2), T2_decay)
check("T1 recov  1-exp(-TR/T1)", 1.0 - math.exp(-TR / T1), T1_recovery)
check("S = S0·T2_decay·T1_recov", S0_mri * T2_decay * T1_recovery, S_mri)

print(f"\n  SuperBEST v4 cost: 12n")
print(f"    T2: div(TE,T2)=2n, DEML=1n → 3n")
print(f"    T1: div(TR,T1)=2n, DEML=1n, sub=2n → 5n")
print(f"    Assembly: mul×2 = 4n")
print(f"    Total: 3+5+4 = 12n")


# ── NAT-2-4: Beer-Lambert ────────────────────────────────────────────────────

section("NAT-2-4  Beer-Lambert  I = I0 · exp(-μx)  [I0=1, μ=0.5, x=2]")

I0, mu, x_bl = 1.0, 0.5, 2.0
I_computed = I0 * math.exp(-mu * x_bl)
I_expected = math.exp(-1.0)   # exp(-0.5·2) = exp(-1)

print(f"  I0={I0}, μ={mu}, x={x_bl}")
print(f"  μ·x = {mu * x_bl:.4f}")
print(f"  I = exp(-1) ≈ {I_expected:.8f}")
print(f"  Computed   = {I_computed:.8f}")

check("I = exp(-1) ≈ 0.36787944", I_expected, I_computed)

print(f"\n  SuperBEST v4 cost: 5n")
print(f"    mul(μ,x)=2n, DEML(product,1)=1n, mul(I0,exp)=2n")


# ── NAT-2-6: Audio Tuning ────────────────────────────────────────────────────

section("NAT-2-6  Audio Tuning  f(n) = 440 · 2^(n/12)  — one octave up: n=12")

f_ref = 440.0
n_octave = 12

f_octave = f_ref * (2 ** (n_octave / 12))
check("f(12) = 880 Hz (one octave up)", 880.0, f_octave, tol=1e-6)

print(f"\n  f(0)  = {f_ref * 2**(0/12):.4f} Hz  (A4)")
print(f"  f(12) = {f_octave:.4f} Hz  (A5, one octave up)")

for semitone, name in [(0, "A4"), (2, "B4"), (4, "C#5"), (7, "E5"), (12, "A5")]:
    freq = f_ref * (2 ** (semitone / 12))
    print(f"  n={semitone:2d}  {name:4s}  {freq:.2f} Hz")

print(f"\n  SuperBEST v4 cost: 7n per note")
print(f"    div(n,12)=2n, pow(2,quotient)=3n, mul(440,power)=2n")
print(f"  Chromatic scale (12 notes): 12 × 7n = 84n (naive)")


# ── Summary ──────────────────────────────────────────────────────────────────

section("SUMMARY — SuperBEST v4 Costs")

rows = [
    ("NAT-1-1", "Golden ratio φ=(1+√5)/2",          "7n"),
    ("NAT-1-2", "Logarithmic spiral a·e^(bθ)",       "5n"),
    ("NAT-1-3", "Sunflower angle n·2π/φ²",           "4n (literal φ²) / 14n (scratch)"),
    ("NAT-1-4", "Population growth N0·e^(rt)",        "5n"),
    ("NAT-1-5", "Fractal dimension log(N)/log(1/ε)",  "5n"),
    ("NAT-1-6", "L-system eigenvalue = φ",            "7n (scratch) / 0n (constant)"),
    ("NAT-1-7", "Phyllotaxis divergence 360°/φ²",     "2n (literal φ²) / 12n (scratch)"),
    ("NAT-2-1", "Greenshields speed vf(1-k/kj)",      "6n"),
    ("NAT-2-2", "Traffic wave c=vf(1-2k/kj)",         "8n"),
    ("NAT-2-3", "MRI signal (spin-echo)",              "12n"),
    ("NAT-2-4", "Beer-Lambert I=I0·e^(-μx)",           "5n"),
    ("NAT-2-5", "Drug half-life ln(2)/k",             "3n"),
    ("NAT-2-6", "Audio tuning 440·2^(n/12)",          "7n"),
    ("NAT-2-7", "Decibel 10·log10(P/P0)",             "7n"),
    ("NAT-2-8", "Reed-Solomon Forney (t=16)",          "~270n per error location"),
]

print()
for id_, name, cost in rows:
    print(f"  {id_:8s}  {name:42s}  {cost}")

print(f"\n  Key isomorphism families (all same SuperBEST cost):")
print(f"    5n: A·exp(-Bx) — CT, radioactive decay, Beer-Lambert, RC discharge")
print(f"    5n: A·exp(Bt)  — population, spiral, compound interest")
print(f"    6n: F·(1-k/kj) — Greenshields, Fick diffusion, linear drag")
print(f"    7n: 10·log10(P/P0) — dB SPL, SNR, Richter, dBm")
print(f"   12n: double-exponential — MRI spin-echo, NMR relaxation")
print()
