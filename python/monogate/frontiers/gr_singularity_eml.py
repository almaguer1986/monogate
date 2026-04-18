"""
Session 86 — GR Full Singularity: Penrose-Hawking, Trapped Surfaces & Cauchy Horizon

Complete EML analysis of general relativistic singularities:
- Penrose singularity theorem (1965): trapped surface + energy condition → geodesic incompleteness
- Hawking singularity theorem (1967): cosmological singularity (Big Bang/Crunch)
- Strong Cosmic Censorship: no naked singularities → Cauchy horizon is EML-∞ barrier
- BKL oscillations: chaotic approach to spacelike singularity → EML-∞

Key theorem: A trapped surface is an EML-2 object (its existence is determined by sign
of mean curvature θ = ∇_μ l^μ, an EML-2 functional). Once a trapped surface exists,
the singularity is EML-∞ — it cannot be represented by any EML-finite function.
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass, field
from typing import Callable


EML_INF = float("inf")


@dataclass
class TrappedSurface:
    """
    A trapped surface S is a compact 2-surface where both null expansions θ± < 0.

    θ = ∇_μ l^μ: expansion of null congruence l^μ emanating from S.

    EML structure:
    - θ(S): EML-2 (covariant divergence of null vector = Christoffel + metric = EML-2)
    - θ < 0 condition: EML-0 (sign condition on EML-2 quantity)
    - Apparent horizon (θ = 0): EML-2 boundary condition
    - Event horizon: EML-∞ (teleological: depends on all future evolution)
    """

    def expansion_schwarzschild(self, r: float, M: float) -> dict:
        """
        For Schwarzschild: θ_± = ∓ 2/r (flat) or θ_± = ∓(2/r)·√(1-2M/r).
        Trapped if r < 2M (inside horizon).
        """
        r_s = 2 * M
        is_trapped = r < r_s
        if r > 0 and r != r_s:
            factor = math.sqrt(abs(1 - r_s / r)) if r > r_s else math.sqrt(r_s / r - 1)
            theta_out = 2 / r * factor if r > r_s else -2 / r * factor
            theta_in = -2 / r * (1 if r > r_s else 1)
        else:
            theta_out = theta_in = float("nan")
        return {
            "r": r,
            "M": M,
            "r_s": r_s,
            "is_trapped": is_trapped,
            "theta_outgoing": round(theta_out, 6) if not math.isnan(theta_out) else "undefined",
            "theta_ingoing": round(theta_in, 6) if not math.isnan(theta_in) else "undefined",
            "eml_theta": 2,
            "eml_trapped_condition": 0,
        }

    def to_dict(self) -> dict:
        radii = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        M = 1.0
        return {
            "definition": "Trapped surface: compact 2-surface with θ_± < 0",
            "schwarzschild_expansion": [self.expansion_schwarzschild(r, M) for r in radii],
            "apparent_horizon": "θ = 0 at r = 2M: EML-2 (zero of EML-2 function)",
            "event_horizon": "r = 2M globally: EML-∞ (teleological — requires full spacetime knowledge)",
            "eml_depth_apparent_vs_event": {
                "apparent_horizon": 2,
                "event_horizon": EML_INF,
                "distinction": "Apparent horizon is locally computable (EML-2); event horizon requires knowing all future (EML-∞)",
            },
        }


@dataclass
class PenroseSingularityTheorem:
    """
    Penrose (1965): If (M,g) satisfies the null energy condition R_{μν}l^μl^ν ≥ 0,
    and contains a non-compact Cauchy surface and a trapped surface, then M is geodesically incomplete.

    EML analysis:
    - Raychaudhuri equation: dθ/dλ = -θ²/2 - σ_{μν}σ^{μν} - R_{μν}l^μl^ν ≤ -θ²/2
      (under NEC)
    - This ODE: dθ/dλ ≤ -θ²/2 with θ₀ < 0 → θ → -∞ in finite affine parameter λ* ≤ 2/|θ₀|
    - λ* = 2/|θ₀|: EML-2 (rational in initial expansion)
    - The singularity (θ → -∞): EML-∞
    """

    def raychaudhuri_blowup(self, theta0: float) -> dict:
        """
        dθ/dλ = -θ²/2 → θ(λ) = θ₀/(1 + θ₀λ/2).
        Blows up at λ* = -2/θ₀ (θ₀ < 0).
        """
        if theta0 >= 0:
            return {"error": "Need θ₀ < 0 for trapped surface"}
        lambda_star = -2.0 / theta0
        lambdas = [lambda_star * k / 10 for k in range(1, 10)]
        trajectory = []
        for lam in lambdas:
            denom = 1 + theta0 * lam / 2
            if abs(denom) > 1e-8:
                theta = theta0 / denom
                trajectory.append({
                    "lambda": round(lam, 4),
                    "lambda_over_lambda_star": round(lam / lambda_star, 3),
                    "theta": round(theta, 4),
                })
        return {
            "theta0": theta0,
            "lambda_star": round(lambda_star, 6),
            "lambda_star_formula": "-2/θ₀: EML-2 (rational in θ₀)",
            "trajectory": trajectory,
            "singularity": "θ → -∞ at λ* — EML-∞",
        }

    def energy_conditions(self) -> list[dict]:
        return [
            {
                "name": "Null Energy Condition (NEC)",
                "statement": "R_{μν}l^μl^ν ≥ 0 for all null l^μ",
                "classical_matter": True,
                "quantum_violations": "Casimir effect, Hawking radiation",
                "eml": 2,
                "reason": "R_{μν}l^μl^ν: EML-2 (Riemann tensor = EML-2 of metric)",
            },
            {
                "name": "Strong Energy Condition (SEC)",
                "statement": "R_{μν}v^μv^ν ≥ 0 for all timelike v^μ",
                "classical_matter": True,
                "quantum_violations": "Positive cosmological constant (dark energy)",
                "eml": 2,
                "reason": "Same: EML-2 curvature contraction",
            },
            {
                "name": "Dominant Energy Condition (DEC)",
                "statement": "T_{μν}v^μ w^ν ≥ 0 for future-directed v^μ, w^ν",
                "classical_matter": True,
                "quantum_violations": "Less common than NEC/SEC violations",
                "eml": 2,
                "reason": "T_{μν}: EML-2 stress-energy tensor",
            },
        ]

    def to_dict(self) -> dict:
        return {
            "theorem": "Penrose Singularity Theorem (1965)",
            "hypotheses": ["NEC", "non-compact Cauchy surface", "trapped surface"],
            "conclusion": "Geodesic incompleteness (singularity)",
            "raychaudhuri": self.raychaudhuri_blowup(-1.0),
            "energy_conditions": self.energy_conditions(),
            "eml_blowup": EML_INF,
            "eml_lambda_star": 2,
            "eml_insight": "The singularity time λ* is EML-2 (computable from θ₀); the singularity itself is EML-∞",
        }


@dataclass
class BKLOscillations:
    """
    Belinskii-Khalatnikov-Lifshitz (BKL) conjecture (1970):
    near a spacelike singularity, the spatial metric oscillates chaotically
    between Kasner epochs.

    Kasner metric: ds² = -dt² + t^{2p₁}dx² + t^{2p₂}dy² + t^{2p₃}dz²
    where p₁+p₂+p₃ = 1 and p₁²+p₂²+p₃² = 1.

    EML structure:
    - Kasner exponents (p₁,p₂,p₃): EML-2 (rational curve on unit sphere ∩ unit plane)
    - Kasner metric components t^{2pᵢ}: EML-1 (power of t = exp(2pᵢ·ln t))
    - BKL transition map: pᵢ → p'ᵢ (Kasner transition): EML-2 (rational Möbius map)
    - Chaotic iteration of Möbius map: EML-∞ (same as logistic map chaos)
    """

    def kasner_exponents(self) -> list[dict]:
        """Parametrize Kasner exponents: p₁=u/(1+u+u²), p₂=(u+u²)/(1+u+u²), p₃=-(u²)/(1+u+u²)."""
        results = []
        for u in [0.5, 1.0, 1.5, 2.0, 3.0]:
            p1 = -u / (1 + u + u**2)
            p2 = (1 + u) / (1 + u + u**2)
            p3 = u * (1 + u) / (1 + u + u**2)
            # Verify
            s1 = round(p1 + p2 + p3, 10)
            s2 = round(p1**2 + p2**2 + p3**2, 10)
            results.append({
                "u": u,
                "p1": round(p1, 6),
                "p2": round(p2, 6),
                "p3": round(p3, 6),
                "sum_p": s1,
                "sum_p2": s2,
                "constraints_satisfied": abs(s1 - 1) < 1e-8 and abs(s2 - 1) < 1e-8,
            })
        return results

    def bkl_transition_map(self, u: float) -> dict:
        """
        BKL map: if u > 1, u → u-1; if u < 1, u → 1/u (Gauss map = continued fraction).
        This is ergodic → chaotic → EML-∞.
        """
        trajectory = [u]
        for _ in range(8):
            if u >= 1:
                u = u - 1
            else:
                u = 1 / u if u > 1e-10 else float("inf")
            if u == float("inf") or u > 1000:
                break
            trajectory.append(round(u, 6))
        return {
            "initial_u": trajectory[0],
            "bkl_orbit": trajectory,
            "map": "u → u-1 if u≥1; u → 1/u if u<1 (Gauss/continued fraction map)",
            "eml": EML_INF,
            "reason": "Gauss map = EML-∞: ergodic, mixing, generates continued fractions (generically EML-∞)",
        }

    def to_dict(self) -> dict:
        return {
            "conjecture": "BKL: approach to spacelike singularity = chaotic Kasner oscillations",
            "kasner_solution": "ds² = -dt² + Σ t^{2pᵢ} dx_i² with Σpᵢ=1, Σpᵢ²=1",
            "kasner_eml": 1,
            "kasner_reason": "t^{2p} = exp(2p·ln t): EML-1 (single exp atom)",
            "kasner_exponents": self.kasner_exponents(),
            "bkl_chaos": self.bkl_transition_map(2.7),
            "mixmaster_chaos": (
                "Mixmaster universe: Bianchi IX near singularity = BKL chaos = EML-∞. "
                "This is the GR analog of the logistic map: simple rule, chaotic orbits."
            ),
        }


@dataclass
class StrongCosmicCensorship:
    """
    Strong Cosmic Censorship (Penrose): the maximal Cauchy development of generic
    initial data is inextendible as a Lorentzian manifold.

    EML analysis:
    - Cauchy horizon C^+ of RN/Kerr: where the Cauchy development ends
    - Stability question: is C^+ stable under perturbations?
    - Dafermos-Luk (2017): C^+ in Kerr is unstable — fields blow up in C^0 but C^+ exists
    - EML of Cauchy horizon: the blowup is EML-∞ (non-removable singularity)
    """

    @staticmethod
    def cauchy_horizon_stability() -> dict:
        return {
            "schwarzschild": {
                "Cauchy_horizon": "None (spacelike singularity inside)",
                "SCC_status": "Trivially satisfied",
                "eml": 2,
            },
            "reissner_nordstrom": {
                "Cauchy_horizon": "Exists at r = r_- = M - √(M²-Q²)",
                "r_minus_formula": "M - √(M²-Q²): EML-2 (square root of polynomial)",
                "SCC_status": "Violated in exact RN — fields can pass through C^+",
                "perturbation_blowup": "Generic perturbations blow up at C^+",
                "eml": EML_INF,
                "reason": "C^+ is an EML-∞ barrier for generic perturbations",
            },
            "kerr": {
                "Cauchy_horizon": "r_- = M - √(M²-a²)",
                "Dafermos_Luk_2017": "C^0 extension exists but curvature blows up",
                "SCC_status": "Borderline — topology changes but C^+ survives in L^2",
                "eml": EML_INF,
                "reason": "Curvature blow-up at C^+ is EML-∞ even if C^+ exists as C^0",
            },
        }

    def to_dict(self) -> dict:
        return {
            "conjecture": "SCC: Generic spacetimes have inextendible maximal Cauchy development",
            "motivation": "Physics cannot propagate past a Cauchy horizon — determinism requires SCC",
            "horizon_stability": self.cauchy_horizon_stability(),
            "eml_insight": (
                "The Cauchy horizon C^+ is an EML-∞ barrier in EML terms: "
                "the curvature invariants blow up at C^+ for generic data, "
                "matching the EML Phase Transition Theorem (singularity = EML-∞)."
            ),
        }


def analyze_gr_singularity_eml() -> dict:
    trapped = TrappedSurface()
    penrose = PenroseSingularityTheorem()
    bkl = BKLOscillations()
    scc = StrongCosmicCensorship()
    return {
        "session": 86,
        "title": "GR Full Singularity: Penrose-Hawking, Trapped Surfaces & Cauchy Horizon",
        "key_theorem": {
            "theorem": "Penrose-EML Singularity Classification",
            "statement": (
                "In GR, trapped surfaces are EML-2 (locally computable: θ < 0 from metric derivatives). "
                "Event horizons are EML-∞ (teleological). "
                "The Penrose singularity blowup time λ* = 2/|θ₀| is EML-2; "
                "the singularity itself (λ → λ*) is EML-∞. "
                "BKL chaotic oscillations near spacelike singularities are EML-∞ "
                "(Gauss/continued fraction map = ergodic). "
                "The Cauchy horizon C^+ is an EML-∞ barrier (SCC)."
            ),
        },
        "trapped_surfaces": trapped.to_dict(),
        "penrose_theorem": penrose.to_dict(),
        "bkl_oscillations": bkl.to_dict(),
        "strong_cosmic_censorship": scc.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Topological charges (linking number, Euler characteristic of horizon)",
            "EML-1": "Kasner metric t^{2p} = exp(2p·ln t); Hawking temperature T_H ∝ 1/(8πM) = EML-0 × mass",
            "EML-2": "Trapped surface condition (θ < 0); apparent horizon; Penrose blowup time λ*; RN/Kerr Cauchy horizon radius",
            "EML-3": "Hawking radiation spectrum (Planckian: involves exp and sin via Bose-Einstein)",
            "EML-∞": "Spacetime singularity; BKL chaos; event horizon (teleological); Cauchy horizon curvature blowup",
        },
        "connections": {
            "to_session_77": "Session 77: Penrose singularity intro + Kerr. Session 86: full BKL chaos + SCC + trapped surfaces",
            "to_session_57": "Phase transitions = EML-∞. Session 86: spacetime singularities = EML-∞ — same universality",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_gr_singularity_eml(), indent=2, default=str))
