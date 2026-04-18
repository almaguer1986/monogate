"""
session61_qft_eml.py — Session 61: Quantum Field Theory & EML Complexity.
"""

import sys
import json
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from monogate.frontiers.qft_eml import (
    ScalarFieldPropagator,
    HarmonicOscillatorPI,
    InstantonAction,
    BetaFunction,
    TQFTPartition,
    FeynmanRules,
    QFT_EML_TAXONOMY,
    analyze_qft_eml,
)

DIVIDER = "=" * 70


def section1_path_integral() -> dict:
    print(DIVIDER)
    print("SECTION 1 — PATH INTEGRAL: EML-1 ATOMS")
    print(DIVIDER)
    print("""
  Z = ∫exp(-S[φ]/ħ)𝒟φ

  Each field configuration φ contributes exp(-S[φ]) = EML-1 atom.
  The path integral is an infinite-dimensional Boltzmann sum.

  UNIFICATION (EML-1 structure appears in):
    Session 57: Z_stat = Σ exp(-βE_i)          (stat mech)
    Session 60: p*(x) ∝ exp(θᵀT(x))            (max entropy)
    Session 61: Z_QFT = ∫exp(-S[φ]/ħ)𝒟φ      (QFT)

  All three are EML-1 structures! The exponential function is the
  universal building block connecting physics and information theory.
""")
    return {
        "eml_depth": 1,
        "note": "Path integral kernel exp(-S[phi]) is EML-1 atom",
        "unification": [
            "stat_mech_Z = sum exp(-beta*E): EML-1",
            "max_entropy p* prop exp(theta*T): EML-1",
            "QFT Z = integral exp(-S/hbar): EML-1",
        ],
    }


def section2_free_propagator() -> dict:
    print(DIVIDER)
    print("SECTION 2 — FREE SCALAR PROPAGATOR: EML-2")
    print(DIVIDER)
    print("""
  G(x,τ;x',τ') = exp(-(x-x')²/(4D·Δτ)) / √(4πD·Δτ)

  Gaussian kernel in position: EML-2 (exp of quadratic = Gaussian)
  Rational in momentum: 1/(k²+m²) — EML-2

  Verify normalization: ∫G(x,τ)dx = 1
""")
    prop = ScalarFieldPropagator(mass=1.0)
    tau_vals = [0.1, 0.5, 1.0, 2.0]
    print("  Δτ     ∫G dx (numerical)  |1-norm|")
    print("  ----   -----------------  --------")
    rows = []
    for tau in tau_vals:
        norm = prop.verify_normalization(tau)
        err = abs(norm - 1.0)
        print(f"  {tau:.1f}    {norm:.8f}       {err:.2e}")
        rows.append({"dtau": tau, "norm": norm, "error": err})

    # Momentum space
    k_vals = [0.0, 0.5, 1.0, 2.0]
    print("\n  k      G̃(k) = 1/(k²+m²)  (m=1)")
    for k in k_vals:
        gk = prop.propagator_momentum(k, 0.0)
        print(f"  {k:.1f}    {gk:.6f}")

    return {
        "normalization_check": rows,
        "all_normalized": all(r["error"] < 0.01 for r in rows),
        "eml_depth": prop.eml_depth_position(),
    }


def section3_harmonic_oscillator() -> dict:
    print(DIVIDER)
    print("SECTION 3 — HARMONIC OSCILLATOR PATH INTEGRAL: EML-2")
    print(DIVIDER)
    print("""
  K_E(x,τ;x',0) = √(mω/(2πsinh(ωτ))) · exp(-mω/(2sinh(ωτ))·((x²+x'²)cosh-2xx'))

  Structure: Gaussian in x,x' → EML-2
  Energy levels: E_n = ħω(n+½) → EML-0 (linear spectrum)
  Partition function: Z = exp(-βħω/2)/(1-exp(-βħω)) → EML-1
""")
    hopi = HarmonicOscillatorPI(mass=1.0, omega=1.0)
    tau_vals = [0.5, 1.0, 2.0]
    x_vals = [0.0, 0.5, 1.0]

    print("  τ=1.0, x'=0: kernel for various x")
    print("  x      K_E(x,1;0,0)")
    for x in x_vals:
        k = hopi.kernel_euclidean(x, 0.0, 1.0)
        print(f"  {x:.1f}    {k:.8f}")

    print("\n  Energy levels E_n = ħω(n+½), ω=1:")
    energies = {n: hopi.nth_energy(n) for n in range(5)}
    for n, e in energies.items():
        print(f"  E_{n} = {e:.4f}")

    beta_vals = [0.5, 1.0, 2.0, 5.0]
    print("\n  Z(β) partition function:")
    parts = {}
    for b in beta_vals:
        z = hopi.partition_function(b)
        parts[f"beta_{b}"] = z
        print(f"  Z(β={b}) = {z:.6f}")

    return {
        "energies": energies,
        "partition_function": parts,
        "kernel_x0_x0_tau1": hopi.kernel_euclidean(0.0, 0.0, 1.0),
        "eml_depth": hopi.eml_depth_kernel(),
    }


def section4_instantons() -> dict:
    print(DIVIDER)
    print("SECTION 4 — INSTANTONS: EML-INFINITY (ESSENTIAL SINGULARITY)")
    print(DIVIDER)
    print("""
  Double-well potential V(x) = (x²-1)²/4
  Instanton action S_inst = ∫√(2V(x)) dx  (BPS bound)

  Non-perturbative amplitude: A ∝ exp(-S_inst/g)

  As g → 0: exp(-S_inst/g) → 0 FASTER than any power g^n.
  This is an ESSENTIAL SINGULARITY at g=0.
  → EML-inf in coupling constant g.

  CONSEQUENCE: Instantons CANNOT be seen in perturbation theory.
""")
    inst = InstantonAction()
    s_inst = inst.instanton_action()
    print(f"  Instanton action S_inst = {s_inst:.6f}")

    g_vals = [1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
    table = inst.show_essential_singularity(g_vals)
    print("\n  g        exp(-S/g)      g^10           amp < g^10")
    print("  ------   -----------    -----------    ----------")
    for row in table:
        g = row["g"]
        amp = row["instanton_amp"]
        g10 = row["g_to_10"]
        less = row["amp_smaller_than_g10"]
        amp_str = f"{amp:.4e}" if amp > 0 else "0.0000e+00"
        g10_str = f"{g10:.4e}"
        print(f"  {g:.3f}    {amp_str}   {g10_str}   {less}")

    return {
        "instanton_action": s_inst,
        "amplitude_table": table,
        "eml_depth_in_g": inst.eml_depth_in_g(),
        "note": "Essential singularity at g=0: non-perturbative, EML-inf",
    }


def section5_rg_beta() -> dict:
    print(DIVIDER)
    print("SECTION 5 — RENORMALIZATION GROUP β-FUNCTION: EML-1")
    print(DIVIDER)
    print("""
  β(g) = μ·dg/dμ = b₂·g³ + b₃·g⁵ + ...   (φ⁴ theory, 4d)

  b₂ = 3/(16π²) ≈ 0.019 (one-loop)
  β(g) > 0 → coupling grows at high energy (φ⁴ is IR-free / UV-trivial)

  EML depth in g: each g^n is EML-1 (exp(n·log g)) → series is EML-1
""")
    beta = BetaFunction()
    g_vals = [0.1, 0.2, 0.5, 1.0, 2.0]
    print("  g      β(g) one-loop    β(g) two-loop")
    print("  ----   ------------    -------------")
    rows = []
    for g in g_vals:
        b1 = beta.beta(g, order=1)
        b2 = beta.beta(g, order=2)
        print(f"  {g:.1f}    {b1:.8f}    {b2:.8f}")
        rows.append({"g": g, "beta_1loop": b1, "beta_2loop": b2})

    print(f"\n  b₂ = {beta.b2:.6f}")
    print(f"  β(g=0.1) one-loop = {beta.beta(0.1):.6f}")

    # Running coupling
    print("\n  Running coupling g(μ) from g₀=0.1 at μ₀=1:")
    mu_vals = [1.0, 2.0, 5.0, 10.0]
    running = {}
    for mu in mu_vals:
        g_run = beta.running_coupling(0.1, 1.0, mu)
        running[f"mu_{mu}"] = g_run
        print(f"  g(μ={mu}) = {g_run:.6f}")

    return {
        "beta_table": rows,
        "running_coupling": running,
        "eml_depth_in_g": beta.eml_depth_in_g(),
        "fixed_points": beta.fixed_points(),
    }


def section6_tqft() -> dict:
    print(DIVIDER)
    print("SECTION 6 — TQFT PARTITION FUNCTIONS: EML-0")
    print(DIVIDER)
    print("""
  TQFT partition functions are TOPOLOGICAL INVARIANTS:
  - Do not depend on metric → cannot contain continuous geometric data
  - Jones polynomial: Laurent polynomial in q with INTEGER coefficients → EML-0
  - Chern-Simons: involves sin(π·rational) which is algebraic → EML-0/2

  This connects to Session 58 (Algebraic Topology): topological
  invariants are always EML-0.
""")
    tqft = TQFTPartition()
    q_vals = [0.5, 1.0, 1.5, 2.0]
    print("  Jones polynomial of trefoil vs unknot:")
    print("  q       J(trefoil)    J(unknot)=1")
    rows = []
    for q in q_vals:
        j_unknot = tqft.jones_polynomial_unknot(q)
        j_trefoil = tqft.jones_polynomial_trefoil(q)
        print(f"  {q:.1f}    {j_trefoil:.6f}    {j_unknot:.1f}")
        rows.append({"q": q, "jones_trefoil": j_trefoil, "jones_unknot": j_unknot})

    print("\n  Chern-Simons partition function Z(S³, SU(2)):")
    cs_data = []
    for k in [2, 3, 4, 5, 10]:
        cs = tqft.chern_simons_level_k(k)
        print(f"  k={k}: Z = {cs['Z']:.6f}")
        cs_data.append(cs)

    return {
        "jones_table": rows,
        "chern_simons": cs_data,
        "eml_depth": tqft.eml_depth(),
    }


def section7_feynman_rules() -> dict:
    print(DIVIDER)
    print("SECTION 7 — FEYNMAN RULES: EML DEPTHS")
    print(DIVIDER)
    print("""
  Propagator: Δ(k) = 1/(k²-m²) → EML-2 (rational in k)
  Vertex: iλ → EML-0 (coupling constant)
  Loop integral: ∫dk/(k²+m²) = π/m → EML-2 (finite)
  UV-divergent loops: need regularization → EML-inf before renorm
""")
    feyn = FeynmanRules(mass=1.0)
    k_vals = [0.5, 1.5, 2.0, 3.0]
    print("  k      Δ(k) = 1/(k²-1)")
    for k in k_vals:
        delta = feyn.propagator(k)
        print(f"  {k:.1f}    {delta:.6f}")

    loop_num = feyn.one_loop_integral_1d(1.0)
    loop_exact = feyn.one_loop_exact_1d(1.0)
    print(f"\n  1D loop integral ∫dk/(k²+1):")
    print(f"  Numerical: {loop_num:.6f}")
    print(f"  Exact π/1: {loop_exact:.6f}")
    print(f"  Match: {abs(loop_num - loop_exact)/loop_exact < 0.01}")

    return {
        "propagator_at_k2": feyn.propagator(2.0),
        "loop_1d_numerical": loop_num,
        "loop_1d_exact": loop_exact,
        "loop_match": abs(loop_num - loop_exact) / loop_exact < 0.01,
        "eml_propagator": feyn.eml_depth_propagator(),
        "eml_vertex": feyn.eml_depth_vertex(),
        "eml_loop_finite": feyn.eml_depth_loop_finite(),
        "eml_loop_divergent": feyn.eml_depth_loop_divergent(),
    }


def main() -> None:
    print("\n" + DIVIDER)
    print("SESSION 61 — QUANTUM FIELD THEORY & EML COMPLEXITY")
    print(DIVIDER + "\n")

    results: dict = {"session": 61, "title": "Quantum Field Theory EML Complexity"}

    results["section1_path_integral"] = section1_path_integral()
    results["section2_free_propagator"] = section2_free_propagator()
    results["section3_harmonic_oscillator"] = section3_harmonic_oscillator()
    results["section4_instantons"] = section4_instantons()
    results["section5_rg_beta"] = section5_rg_beta()
    results["section6_tqft"] = section6_tqft()
    results["section7_feynman_rules"] = section7_feynman_rules()

    full = analyze_qft_eml()
    results["taxonomy"] = full["taxonomy"]
    results["summary"] = full["summary"]

    print("\n" + DIVIDER)
    print("SUMMARY — EML DEPTHS IN QUANTUM FIELD THEORY")
    print(DIVIDER)
    print("""
  Path integral Z = ∫exp(-S/ħ)𝒟φ:   EML-1  (Boltzmann kernel)
  Free scalar propagator G(x,τ):      EML-2  (Gaussian kernel)
  Harmonic oscillator kernel K_E:     EML-2  (Gaussian in x,x')
  Instanton amplitude exp(-S/g):      EML-∞  (essential singularity at g=0)
  RG β-function β(g):                 EML-1  (power series in coupling)
  TQFT partition function Z_TQFT:     EML-0  (topological invariant)
  Feynman propagator 1/(k²-m²):       EML-2  (rational in momentum)
  UV-divergent loop integrals:        EML-∞  (before regularization)

  KEY INSIGHT:
    The EML hierarchy mirrors the perturbative/non-perturbative divide:
    - Perturbative (Feynman diagrams): EML-0 to EML-2
    - Non-perturbative (instantons):   EML-∞
    - Topological (TQFT):              EML-0
""")

    out_path = Path(__file__).parent.parent / "results" / "session61_qft_eml.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
