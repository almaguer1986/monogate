"""
Session 122 — Evolutionary Biology: Fitness Landscapes, Speciation & Evolutionary Phase Transitions

Wright's adaptive landscape, NK fitness landscapes, punctuated equilibrium, speciation
thresholds, and the population genetics of evolution classified by EML depth.

Key theorem: Additive fitness W = exp(Σ s_i σ_i) is EML-1 (Boltzmann product of
per-locus contributions). NK rugged landscape with K>1 epistasis is EML-∞ (no closed
form, spin glass analog). Speciation threshold = EML-∞ phase transition. Error threshold
ln(W_max)/L is EML-2 (log of fitness ratio). Neutral evolution = EML-0.
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass

EML_INF = float("inf")


@dataclass
class FitnessLandscape:
    """
    Wright's adaptive landscape and NK model.

    EML structure:
    - Additive fitness: W = exp(Σᵢ sᵢ σᵢ): EML-1 (product of Boltzmann factors)
    - Multiplicative fitness: W = Π(1+sᵢ) ≈ exp(Σ sᵢ): EML-1 (small s)
    - NK landscape K=0 (additive): EML-1 (single peak, closed form)
    - NK landscape K=1: EML-2 (pairwise epistasis, correlation landscape)
    - NK landscape K=N-1 (fully epistatic): EML-∞ (random energy model — no formula)
    - Fitness gradient: ∂W/∂σᵢ = sᵢ W: EML-1 (scalar multiple)
    - Mean fitness dW/dt = Var(W)/W (Fisher): EML-2 (variance normalized by mean)
    """

    def additive_fitness(self, selection_coeffs: list[float],
                         alleles: list[int]) -> dict:
        """W = exp(Σ sᵢ σᵢ): additive log-fitness."""
        log_W = sum(s * a for s, a in zip(selection_coeffs, alleles))
        W = math.exp(log_W)
        return {
            "selection_coeffs": selection_coeffs,
            "alleles": alleles,
            "log_W": round(log_W, 4),
            "W": round(W, 4),
            "eml": 1,
            "reason": "W=exp(Σ sᵢσᵢ): product of EML-1 Boltzmann factors = EML-1.",
        }

    def nk_complexity(self, N: int, K: int) -> dict:
        """NK landscape EML depth as function of K."""
        if K == 0:
            eml = 1
            description = "Additive landscape: single global peak, closed form W=exp(Σsᵢ)"
        elif K == 1:
            eml = 2
            description = "Pairwise epistasis: pair correlations, EML-2 structure (quadratic interactions)"
        elif K < N // 2:
            eml = 3
            description = "Moderate epistasis: multiple local peaks, EML-3 (oscillatory fitness surface)"
        else:
            eml = EML_INF
            description = "Fully epistatic (spin glass): no closed form, random energy model = EML-∞"
        return {
            "N": N, "K": K,
            "eml": "∞" if eml == EML_INF else eml,
            "description": description,
        }

    def fishers_fundamental_theorem(self, fitnesses: list[float],
                                    freqs: list[float]) -> dict:
        """dW̄/dt = Var(W)/W̄ — Fisher's fundamental theorem."""
        W_bar = sum(w * p for w, p in zip(fitnesses, freqs))
        var_W = sum(p * (w - W_bar)**2 for w, p in zip(fitnesses, freqs))
        dW_bar_dt = var_W / W_bar
        return {
            "fitnesses": fitnesses,
            "frequencies": freqs,
            "W_bar": round(W_bar, 4),
            "Var_W": round(var_W, 4),
            "dW_bar_dt": round(dW_bar_dt, 4),
            "eml": 2,
            "reason": "dW̄/dt = Var(W)/W̄: variance/mean = EML-2 (ratio of quadratic to linear).",
        }

    def to_dict(self) -> dict:
        return {
            "additive_fitness": [
                self.additive_fitness([0.1, -0.05, 0.2], [1, 0, 1]),
                self.additive_fitness([0.05, 0.05, 0.05, 0.05], [1, 1, 1, 1]),
            ],
            "nk_landscape": [self.nk_complexity(20, K) for K in [0, 1, 5, 10, 19]],
            "fishers_theorem": self.fishers_fundamental_theorem(
                [1.0, 1.1, 0.9], [0.5, 0.3, 0.2]
            ),
            "eml_additive_fitness": 1,
            "eml_nk_K0": 1,
            "eml_nk_K_high": "∞",
        }


@dataclass
class SpeciationDynamics:
    """
    Speciation: the EML phase transition of evolution.

    EML structure:
    - Gene flow m between populations: if m > m_c → single species (EML-1 shared pool)
    - m < m_c → reproductive isolation → speciation = EML-∞ phase transition
    - Critical migration rate m_c ~ s (selection coefficient): EML-0
    - Dobzhansky-Muller incompatibilities: k loci → P(incompatible) = 1-exp(-k²/2): EML-2
    - Time to speciation: T_spec ~ 1/s · ln(N) = EML-2 (log of population size)
    - Adaptive radiation: burst of speciation = EML-∞ (Cambrian explosion analog)
    - Neutral speciation (drift): T_fix = 4N for neutral allele = EML-0 scaling
    """

    def dobzhansky_muller(self, k: int) -> dict:
        """P(incompatible) = 1 - exp(-k²/2): probability of reproductive isolation."""
        p_incompat = 1 - math.exp(-k**2 / 2)
        return {
            "k_incompatibility_loci": k,
            "P_incompatible": round(p_incompat, 4),
            "eml": 2,
            "reason": "P=1-exp(-k²/2): exp of quadratic = EML-2 (Gaussian complement).",
        }

    def time_to_speciation(self, s: float, N: int) -> dict:
        """T_spec ~ ln(N)/s: time scales as log of population."""
        if s <= 0:
            return {"s": s, "N": N, "T_spec": float("inf"), "eml": "∞"}
        T = math.log(N) / s
        return {
            "s": s, "N": N,
            "T_spec_generations": round(T, 1),
            "eml": 2,
            "reason": "T~ln(N)/s: logarithm of population size = EML-2.",
        }

    def gene_flow_threshold(self, m: float, s: float, n_loci: int = 10) -> dict:
        """m vs s determines single species vs speciation."""
        m_c = s / n_loci
        if m > m_c:
            regime = "gene flow dominates → single species"
            eml = 1
        elif abs(m - m_c) < m_c * 0.05:
            regime = "critical: speciation threshold"
            eml = EML_INF
        else:
            regime = "selection dominates → reproductive isolation → speciation"
            eml = EML_INF
        return {
            "m": m, "s": s,
            "m_critical": round(m_c, 4),
            "regime": regime,
            "eml": "∞" if eml == EML_INF else eml,
        }

    def to_dict(self) -> dict:
        return {
            "dobzhansky_muller": [self.dobzhansky_muller(k) for k in [1, 2, 3, 5, 10]],
            "time_to_speciation": [self.time_to_speciation(s, N)
                                    for s, N in [(0.01, 1000), (0.1, 10000), (0.001, 1000000)]],
            "gene_flow": [self.gene_flow_threshold(m, 0.01) for m in [0.001, 0.005, 0.01, 0.05]],
            "eml_DM_incompatibility": 2,
            "eml_speciation_time": 2,
            "eml_speciation_threshold": "∞",
        }


@dataclass
class PunctuatedEquilibrium:
    """
    Punctuated equilibrium (Gould & Eldredge): evolution proceeds by long
    stasis punctuated by rapid bursts.

    EML structure:
    - Stasis: fitness ≈ constant over long periods = EML-0
    - Background change: neutral drift W~1, slow morphological change = EML-0
    - Punctuation: rapid adaptive radiation = EML-∞ (phase transition in fitness landscape)
    - Stochastic tunneling: crossing fitness valleys by drift = EML-1 (exponential in valley depth)
    - Cambrian explosion: EML-∞ burst (ecological opportunity + developmental toolkit unlock)
    - Mass extinction: EML-∞ phase transition (diversity collapse)
    - Recovery: EML-1 (exponential rebound from survivors)
    """

    def stochastic_tunneling(self, valley_depth: float, N: int) -> dict:
        """P(tunnel) ~ exp(-N·valley_depth): tunneling probability."""
        log_P = -N * valley_depth
        P = math.exp(max(log_P, -700))
        return {
            "valley_depth": valley_depth,
            "N_population": N,
            "P_tunnel": round(P, 8),
            "eml": 1,
            "reason": "P~exp(-N·d): exponential in valley depth × population = EML-1.",
        }

    def radiation_burst(self, t: float, t_burst: float = 10.0,
                        r: float = 0.5, K: float = 100.0) -> dict:
        """Post-extinction radiation: N(t) = K/(1+exp(-r(t-t_burst))) (logistic)."""
        N = K / (1 + math.exp(-r * (t - t_burst)))
        return {
            "t_My": t,
            "t_burst_My": t_burst,
            "N_species": round(N, 2),
            "eml": 2,
            "reason": "Logistic N=K/(1+exp(-r(t-t_b))): sigmoid = EML-2 (rational of EML-1).",
        }

    def to_dict(self) -> dict:
        return {
            "stochastic_tunneling": [
                self.stochastic_tunneling(d, N)
                for d, N in [(0.01, 100), (0.1, 100), (0.01, 1000)]
            ],
            "radiation_burst": [self.radiation_burst(t) for t in range(0, 30, 3)],
            "eml_stasis": 0,
            "eml_tunneling": 1,
            "eml_punctuation": "∞",
            "eml_radiation": 2,
            "eml_mass_extinction": "∞",
        }


def analyze_evolution_deep_eml() -> dict:
    fl = FitnessLandscape()
    sp = SpeciationDynamics()
    pe = PunctuatedEquilibrium()
    return {
        "session": 122,
        "title": "Evolutionary Biology: Fitness Landscapes, Speciation & Evolutionary Phase Transitions",
        "key_theorem": {
            "theorem": "EML Evolution Phase Transition Theorem",
            "statement": (
                "Additive fitness W=exp(Σsᵢσᵢ) is EML-1 (Boltzmann product). "
                "Fisher's fundamental theorem dW̄/dt=Var(W)/W̄ is EML-2 (variance/mean). "
                "NK landscape with K=0 is EML-1; K→N-1 is EML-∞ (spin glass). "
                "Dobzhansky-Muller incompatibility P=1-exp(-k²/2) is EML-2. "
                "Time to speciation T~ln(N)/s is EML-2. "
                "Speciation threshold m=m_c is EML-∞ (phase transition). "
                "Stochastic tunneling P~exp(-N·d) is EML-1. "
                "Adaptive radiation follows logistic EML-2 growth. "
                "Punctuated equilibrium: stasis=EML-0, tunneling=EML-1, burst=EML-∞."
            ),
        },
        "fitness_landscape": fl.to_dict(),
        "speciation_dynamics": sp.to_dict(),
        "punctuated_equilibrium": pe.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Neutral evolution (drift); stasis; morphological conservation; fixation time 4N",
            "EML-1": "Additive fitness exp(Σsᵢσᵢ); stochastic tunneling exp(-Nd); post-extinction rebound",
            "EML-2": "Fisher's theorem Var(W)/W̄; DM incompatibility 1-exp(-k²/2); speciation time ln(N)/s; logistic radiation",
            "EML-3": "Moderate epistasis (K~N/2): oscillatory fitness surface with multiple peaks",
            "EML-∞": "NK K=N-1 (spin glass); speciation threshold m=m_c; Cambrian explosion; mass extinction",
        },
        "rabbit_hole_log": [
            "The NK landscape is the evolutionary analog of the Ising model. K=0 (additive) = non-interacting spins = EML-1. K=N-1 (fully epistatic) = random energy model = spin glass = EML-∞. The spin glass phase transition at K_c is the evolutionary analog of Ising T_c (S57) — above K_c, the fitness landscape has exponentially many local optima, no gradient to follow, and evolution stalls. Evolution itself is an EML-∞ problem in the fully epistatic regime.",
            "Speciation is an EML-∞ phase transition: below the critical migration rate m_c~s, gene flow prevents divergence (single species = EML-1 shared gene pool). Above m_c, allele frequencies diverge, reproductive isolation builds up via Dobzhansky-Muller incompatibilities (EML-2), and speciation occurs. The speciation threshold m=m_c is the same EML-∞ structure as R₀=1 (S113), laser threshold (S116), and neural criticality σ=1 (S118). Phase transitions are evolution's mechanism for generating biological diversity.",
            "Fisher's Fundamental Theorem is EML-2: dW̄/dt = Var(W)/W̄. This is a ratio of variance (EML-2 quadratic) to mean (EML-1), giving EML-2. The theorem says mean fitness increases at the rate of additive genetic variance — the engine of evolution is EML-2. This connects to the Fisher information (S60): Fisher information I(θ) = E[(∂ ln p/∂θ)²] = 1/σ² (also EML-2). The same Fisher who proved the fundamental theorem derived the Fisher information — both are EML-2 by the same variance-over-mean structure.",
        ],
        "connections": {
            "to_session_57": "NK spin glass (EML-∞) = Ising spin glass below T_c. Same EML-∞ frustrated landscape.",
            "to_session_113": "Speciation threshold m=m_c = epidemic threshold R₀=1: same EML-∞ phase transition structure.",
            "to_session_60": "Fisher's theorem Var(W)/W̄ = EML-2, same depth as Fisher information I(θ)=1/σ².",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_evolution_deep_eml(), indent=2, default=str))
