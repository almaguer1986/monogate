"""
qft_eml.py — EML Complexity in Quantum Field Theory.

Session 61 findings:
  - Path integral Z = ∫exp(-S[φ]/ħ)𝒟φ: EML-1 atoms (infinite-dim Boltzmann)
  - Free scalar propagator: EML-2/3 (Gaussian kernel)
  - Harmonic oscillator path integral: EML-2 (exact Gaussian)
  - Instantons: exp(-S_inst/g) = exp(-1/g) → essential singularity → EML-inf in g
  - Renormalization group β-function: EML-1 in coupling (power series)
  - TQFT partition functions: EML-0 (topological invariants)
  - Feynman rules: propagator EML-2, vertex EML-0, loop can be EML-inf
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

__all__ = [
    "ScalarFieldPropagator",
    "HarmonicOscillatorPI",
    "InstantonAction",
    "BetaFunction",
    "TQFTPartition",
    "FeynmanRules",
    "QFT_EML_TAXONOMY",
    "analyze_qft_eml",
]

# ── EML Taxonomy ─────────────────────────────────────────────────────────────

QFT_EML_TAXONOMY: dict[str, dict] = {
    "path_integral": {
        "formula": "Z = ∫exp(-S[φ]/ħ)𝒟φ",
        "eml_depth": 1,
        "reason": (
            "Each field configuration contributes exp(-S): EML-1 atom. "
            "The path integral is an infinite-dimensional Boltzmann sum. "
            "Same EML-1 structure as stat mech (Session 57) and info theory (Session 60)."
        ),
    },
    "free_scalar_propagator": {
        "formula": "Δ(x,t;x',t') = exp(-(x-x')²/(4D(t-t')))/√(4πD(t-t'))",
        "eml_depth": 2,
        "reason": "Gaussian kernel: exp(-r²/t)/√t. EML-2 in x (Gaussian), EML-2 in t.",
    },
    "harmonic_oscillator_pi": {
        "formula": "⟨x|e^{-Ht}|x'⟩ = (mω/2πsinh(ωt))^{1/2}·exp(-mω·cosh/sinh·stuff)",
        "eml_depth": 2,
        "reason": "Exact Gaussian in x,x'. Involves sinh/cosh (EML-3), but coherent state → EML-2.",
    },
    "instanton": {
        "formula": "A_instanton ∝ exp(-S_inst/g) = exp(-C/g)",
        "eml_depth": "inf",
        "reason": (
            "exp(-1/g) is an essential singularity at g=0. "
            "Non-perturbative: no finite EML tree can represent exp(-1/g). "
            "EML-inf in coupling constant g."
        ),
    },
    "rg_beta_function": {
        "formula": "β(g) = μ·dg/dμ = b·g³ + O(g⁵) for φ⁴",
        "eml_depth": 1,
        "reason": (
            "β(g) is a power series in g. Each g^n is EML-1 (exp(n·log g)). "
            "Perturbative β-function is EML-1 in the coupling."
        ),
    },
    "tqft_partition": {
        "formula": "Z_TQFT = topological invariant (integer or polynomial)",
        "eml_depth": 0,
        "reason": (
            "TQFT partition functions are topological invariants: "
            "integers (Z_CS = knot invariant) or integer polynomials (Jones). "
            "EML-0 (discrete/algebraic)."
        ),
    },
    "feynman_propagator": {
        "formula": "Δ(k) = i/(k²-m²+iε)",
        "eml_depth": 2,
        "reason": "Rational in momentum k: EML-2.",
    },
    "feynman_vertex": {
        "formula": "iλ (coupling constant)",
        "eml_depth": 0,
        "reason": "Constant factor: EML-0.",
    },
    "loop_integral": {
        "formula": "∫d^4k/(k²-m²)^n",
        "eml_depth": "2_or_inf",
        "reason": (
            "UV-finite loops: EML-2 (rational result after regularization). "
            "UV-divergent loops: require renormalization → EML-inf before renorm."
        ),
    },
}


# ── Free Scalar Propagator ────────────────────────────────────────────────────

@dataclass
class ScalarFieldPropagator:
    """
    Free scalar field propagator (Euclidean space / imaginary time).

    For a free scalar field with mass m, the Euclidean propagator is:
      G(x,τ;x',τ') = exp(-(x-x')²/(4D(τ-τ'))) / √(4πD(τ-τ'))
    where D = ħ/(2m).

    In momentum space: G̃(k,ω) = 1/(ω² + k² + m²) — rational EML-2.
    """

    mass: float = 1.0
    hbar: float = 1.0

    @property
    def diffusion_const(self) -> float:
        """D = ħ/(2m)."""
        return self.hbar / (2.0 * self.mass)

    def propagator_position(self, dx: float, dtau: float) -> float:
        """G(Δx, Δτ) = exp(-Δx²/(4D·Δτ)) / √(4πD·Δτ)."""
        if dtau <= 0:
            return 0.0
        D = self.diffusion_const
        exponent = -dx ** 2 / (4.0 * D * dtau)
        # Guard against large negative exponents
        if exponent < -700:
            return 0.0
        norm = math.sqrt(4.0 * math.pi * D * dtau)
        return math.exp(exponent) / norm

    def propagator_momentum(self, k: float, omega: float) -> float:
        """G̃(k,ω) = 1/(ω² + k² + m²) — rational, EML-2."""
        return 1.0 / (omega ** 2 + k ** 2 + self.mass ** 2)

    def verify_normalization(self, dtau: float, n_points: int = 1000) -> float:
        """Verify ∫G(x,τ)dx = 1 numerically."""
        D = self.diffusion_const
        scale = math.sqrt(4.0 * D * dtau)
        x_max = 6.0 * scale
        xs = np.linspace(-x_max, x_max, n_points)
        dx_step = xs[1] - xs[0]
        vals = np.array([self.propagator_position(x, dtau) for x in xs])
        return float(np.sum(vals) * dx_step)

    def eml_depth_position(self) -> int:
        return 2  # Gaussian in position

    def eml_depth_momentum(self) -> int:
        return 2  # Rational in momentum


# ── Harmonic Oscillator Path Integral ────────────────────────────────────────

@dataclass
class HarmonicOscillatorPI:
    """
    Harmonic oscillator path integral (quantum mechanics).

    Exact kernel:
      K(x,T;x',0) = √(mω/(2πisin(ωT))) · exp(imω/(2sin(ωT)) · ((x²+x'²)cos(ωT) - 2xx'))

    Euclidean (T → -iτ):
      K_E(x,τ;x',0) = √(mω/(2πsinh(ωτ))) · exp(-mω/(2sinh(ωτ)) · ((x²+x'²)cosh(ωτ) - 2xx'))
    """

    mass: float = 1.0
    omega: float = 1.0
    hbar: float = 1.0

    def kernel_euclidean(self, x: float, xp: float, tau: float) -> float:
        """Euclidean propagator K_E(x,τ;x',0)."""
        if tau <= 0:
            return 0.0
        mw = self.mass * self.omega
        sinh_wt = math.sinh(self.omega * tau)
        cosh_wt = math.cosh(self.omega * tau)
        if sinh_wt < 1e-15:
            return 0.0
        prefactor = math.sqrt(mw / (2.0 * math.pi * self.hbar * sinh_wt))
        exponent = -mw / (2.0 * self.hbar * sinh_wt) * (
            (x ** 2 + xp ** 2) * cosh_wt - 2.0 * x * xp
        )
        if exponent < -700:
            return 0.0
        return prefactor * math.exp(exponent)

    def ground_state_energy(self) -> float:
        """E_0 = ħω/2 (zero-point energy)."""
        return 0.5 * self.hbar * self.omega

    def nth_energy(self, n: int) -> float:
        """E_n = ħω(n + 1/2)."""
        return self.hbar * self.omega * (n + 0.5)

    def partition_function(self, beta: float) -> float:
        """Z(β) = Σ exp(-βE_n) = exp(-βħω/2)/(1-exp(-βħω))."""
        bw = beta * self.hbar * self.omega
        if bw > 700:
            return math.exp(-bw / 2.0)
        return math.exp(-bw / 2.0) / (1.0 - math.exp(-bw))

    def eml_depth_kernel(self) -> int:
        return 2  # Gaussian in x,x' (involves sinh/cosh but structure is Gaussian)


# ── Instanton Action ─────────────────────────────────────────────────────────

@dataclass
class InstantonAction:
    """
    Instantons in double-well potential V(x) = (x²-1)²/4.

    Instanton: classical solution connecting x=-1 to x=+1.
    Action: S_inst = ∫|dx/dτ|²dτ = 1/3 (for V=(x²-1)²/4, ħ=g=1)

    Non-perturbative amplitude: exp(-S_inst/g) = exp(-1/(3g))
    This is an ESSENTIAL SINGULARITY at g=0 → EML-inf in g.
    """

    def instanton_action(self) -> float:
        """S_inst = 2/3 for V(x) = (x²-1)²/4 (kink integral from -1 to 1)."""
        # ∫_{-1}^{1} √(2V(x)) dx = ∫_{-1}^{1} |x²-1|/√2 · dx...
        # Standard: V=(x^2-a^2)^2/(8a^2), S_inst = 4a^3/3
        # For V=(x^2-1)^2/4: S = ∫_{-1}^{1} (1-x^2)/√2 * √2 dx = ∫(1-x^2)dx = 4/3
        # More carefully via BPS: dτ/dx = 1/√(2V) = 1/|x^2-1|*sqrt(2)...
        # Using numerical integration
        xs = np.linspace(-1.0, 1.0, 10000)
        v_vals = (xs ** 2 - 1.0) ** 2 / 4.0
        integrand = np.sqrt(2.0 * v_vals)
        return float(np.trapezoid(integrand, xs))

    def non_perturbative_amplitude(self, g: float, n_inst: int = 1) -> float:
        """Instanton amplitude: A ∝ exp(-n·S_inst/g)."""
        s = self.instanton_action()
        exponent = -n_inst * s / g
        if exponent < -700:
            return 0.0
        return math.exp(exponent)

    def show_essential_singularity(self, g_vals: Sequence[float]) -> list[dict]:
        """Show exp(-S/g) → 0 faster than any power of g as g→0."""
        s = self.instanton_action()
        results = []
        for g in g_vals:
            amp = self.non_perturbative_amplitude(g)
            # Compare to g^n for n=10
            power10 = g ** 10 if g > 0 else 0.0
            results.append({
                "g": g,
                "instanton_amp": amp,
                "g_to_10": power10,
                "amp_smaller_than_g10": amp < power10 if power10 > 0 else True,
            })
        return results

    def eml_depth_in_g(self) -> str:
        return "inf"  # Essential singularity at g=0


# ── RG Beta Function ─────────────────────────────────────────────────────────

@dataclass
class BetaFunction:
    """
    Renormalization group β-function for φ⁴ theory.

    β(g) = μ·dg/dμ = b₂·g³ + b₃·g⁵ + ...  (perturbative, EML-1 in g)

    For φ⁴ in 4d: b₂ = 3/(16π²) (one-loop)
    Fixed point: β(g*) = 0 → g* = 0 (Gaussian FP, trivial)

    Asymptotic freedom: β(g) < 0 → coupling decreases at high energy (QCD-like)
    """

    b2: float = 3.0 / (16.0 * math.pi ** 2)  # one-loop φ⁴
    b3: float = -17.0 / (3.0 * (16.0 * math.pi ** 2) ** 2)  # two-loop

    def beta(self, g: float, order: int = 1) -> float:
        """β(g) up to specified loop order."""
        result = self.b2 * g ** 3
        if order >= 2:
            result += self.b3 * g ** 5
        return result

    def running_coupling(self, g0: float, mu0: float,
                         mu: float, n_steps: int = 1000) -> float:
        """Integrate RG equation dg/d(log μ) = β(g) from μ₀ to μ."""
        log_mu = math.log(mu / mu0)
        dt = log_mu / n_steps
        g = g0
        for _ in range(n_steps):
            g += self.beta(g) * dt
        return g

    def fixed_points(self) -> list[float]:
        """Find β(g) = 0 solutions (perturbative: g=0 only)."""
        return [0.0]

    def eml_depth_in_g(self) -> int:
        return 1  # Power series in g, each term is EML-1


# ── TQFT Partition Function ───────────────────────────────────────────────────

@dataclass
class TQFTPartition:
    """
    Topological quantum field theory partition functions.

    Z_TQFT is a topological invariant: does not depend on metric.
    Examples:
      - 3d Chern-Simons: Z = surgery formula involving integer framing numbers
      - Jones polynomial: Laurent polynomial in q with integer coefficients
      - Witten invariants: algebraic numbers (roots of unity)

    EML-0: these are discrete/algebraic data.
    """

    def jones_polynomial_unknot(self, q: float) -> float:
        """Jones polynomial of unknot: J(q) = 1. EML-0."""
        return 1.0

    def jones_polynomial_trefoil(self, q: float) -> float:
        """Jones polynomial of trefoil (right-handed): -q^{-4}+q^{-3}+q^{-1}."""
        return -q ** (-4) + q ** (-3) + q ** (-1)

    def chern_simons_level_k(self, k: int, n: int = 2) -> dict:
        """
        SU(2) Chern-Simons partition function on S³ at level k.
        Z = √(2/(k+2)) · sin(π/(k+2)).
        EML-2 (contains sin of rational multiple of π, which is algebraic).
        """
        val = math.sqrt(2.0 / (k + 2)) * math.sin(math.pi / (k + 2))
        return {
            "k": k,
            "n": n,
            "Z": val,
            "eml_note": "sin(π·rational) is algebraic → EML-0 at rational level, EML-2 at generic",
        }

    def linking_number(self, curve1: list[int], curve2: list[int]) -> int:
        """Linking number is an integer: EML-0."""
        # Simplified: return first element as placeholder
        return 0

    def eml_depth(self) -> int:
        return 0  # Topological invariants are EML-0


# ── Feynman Rules ─────────────────────────────────────────────────────────────

@dataclass
class FeynmanRules:
    """
    Feynman rules and their EML depths.

    Propagator: Δ(k) = i/(k²-m²) → EML-2 (rational in k)
    Vertex: iλ → EML-0 (constant)
    Loop integral: ∫d^4k/(2π)^4 · 1/(k²-m²)^n → EML-2 (finite) or EML-inf (divergent)
    """

    mass: float = 1.0
    coupling: float = 0.1

    def propagator(self, k: float) -> complex:
        """Scalar propagator: 1/(k²-m²+iε), return real part for k²≠m²."""
        denom = k ** 2 - self.mass ** 2
        if abs(denom) < 1e-10:
            return float("inf")
        return 1.0 / denom

    def one_loop_integral_1d(self, m: float, scale: float = 100.0,
                              n_steps: int = 10000) -> float:
        """
        Approximate 1D loop integral ∫dk/(k²+m²) = π/m (Euclidean, 1d).
        """
        ks = np.linspace(-scale, scale, n_steps)
        dk = ks[1] - ks[0]
        integrand = 1.0 / (ks ** 2 + m ** 2)
        return float(np.sum(integrand) * dk)

    def one_loop_exact_1d(self, m: float) -> float:
        """Exact: ∫_{-∞}^{∞} dk/(k²+m²) = π/m."""
        return math.pi / m

    def propagator_tensor_product(self, k: float, n: int) -> float:
        """Product of n propagators: (Δ(k))^n — still EML-2 (rational)."""
        denom = k ** 2 - self.mass ** 2
        if abs(denom) < 1e-10:
            return float("inf")
        return 1.0 / (denom ** n)

    def eml_depth_propagator(self) -> int:
        return 2

    def eml_depth_vertex(self) -> int:
        return 0

    def eml_depth_loop_finite(self) -> int:
        return 2

    def eml_depth_loop_divergent(self) -> str:
        return "inf"


# ── Grand Analysis ────────────────────────────────────────────────────────────

def analyze_qft_eml() -> dict:
    """Run full QFT EML analysis."""
    results: dict = {
        "session": 61,
        "title": "Quantum Field Theory EML Complexity",
        "taxonomy": QFT_EML_TAXONOMY,
    }

    prop = ScalarFieldPropagator(mass=1.0)
    hopi = HarmonicOscillatorPI(mass=1.0, omega=1.0)
    inst = InstantonAction()
    beta = BetaFunction()
    tqft = TQFTPartition()
    feyn = FeynmanRules(mass=1.0, coupling=0.1)

    # Propagator
    norm_01 = prop.verify_normalization(dtau=0.1)
    norm_10 = prop.verify_normalization(dtau=1.0)
    results["propagator"] = {
        "normalization_dtau_0.1": norm_01,
        "normalization_dtau_1.0": norm_10,
        "value_dx0_dtau1": prop.propagator_position(0.0, 1.0),
        "momentum_k1_w1": prop.propagator_momentum(1.0, 1.0),
        "eml_depth": prop.eml_depth_position(),
    }

    # Harmonic oscillator
    results["harmonic_oscillator_pi"] = {
        "kernel_x0_x0_tau1": hopi.kernel_euclidean(0.0, 0.0, 1.0),
        "ground_state_energy": hopi.ground_state_energy(),
        "E_1": hopi.nth_energy(1),
        "E_5": hopi.nth_energy(5),
        "partition_beta1": hopi.partition_function(1.0),
        "eml_depth": hopi.eml_depth_kernel(),
    }

    # Instantons
    s_inst = inst.instanton_action()
    g_vals = [0.5, 0.2, 0.1, 0.05, 0.01]
    instanton_data = inst.show_essential_singularity(g_vals)
    results["instantons"] = {
        "action": s_inst,
        "table": instanton_data,
        "eml_depth_in_g": inst.eml_depth_in_g(),
        "note": "exp(-S/g) → 0 faster than any g^n as g→0: essential singularity",
    }

    # Beta function
    g_vals_rg = [0.1, 0.5, 1.0]
    results["rg_beta"] = {
        "beta_g01": beta.beta(0.1),
        "beta_g05": beta.beta(0.5),
        "beta_g10": beta.beta(1.0),
        "running_coupling": {
            f"g0_{g}_mu10": beta.running_coupling(g, 1.0, 10.0) for g in g_vals_rg
        },
        "fixed_points": beta.fixed_points(),
        "eml_depth_in_g": beta.eml_depth_in_g(),
    }

    # TQFT
    results["tqft"] = {
        "jones_unknot": tqft.jones_polynomial_unknot(1.5),
        "jones_trefoil_q15": tqft.jones_polynomial_trefoil(1.5),
        "cs_k2": tqft.chern_simons_level_k(2),
        "cs_k5": tqft.chern_simons_level_k(5),
        "eml_depth": tqft.eml_depth(),
    }

    # Feynman rules
    loop_num = feyn.one_loop_integral_1d(1.0)
    loop_exact = feyn.one_loop_exact_1d(1.0)
    results["feynman_rules"] = {
        "propagator_k2": feyn.propagator(2.0),
        "propagator_k0": feyn.propagator(0.0),
        "loop_1d_numerical": loop_num,
        "loop_1d_exact": loop_exact,
        "loop_match": abs(loop_num - loop_exact) / loop_exact < 0.01,
        "eml_propagator": feyn.eml_depth_propagator(),
        "eml_vertex": feyn.eml_depth_vertex(),
    }

    results["summary"] = {
        "key_insight": (
            "Path integrals are infinite-dimensional EML-1 sums (Boltzmann factors). "
            "Propagators are EML-2 (Gaussian/rational). "
            "Instantons exp(-1/g) are EML-inf (essential singularities). "
            "TQFT invariants are EML-0 (topological = discrete). "
            "The EML hierarchy mirrors the perturbative vs non-perturbative divide in QFT."
        ),
        "eml_depths": {k: v["eml_depth"] for k, v in QFT_EML_TAXONOMY.items()},
    }

    return results
