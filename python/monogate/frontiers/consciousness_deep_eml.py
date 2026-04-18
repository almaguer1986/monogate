"""
Session 121 — Consciousness & Cognitive Science: EML Models of Attention, Insight & Qualia

Deep EML dissection of cognitive architecture: global workspace, integrated information,
predictive coding, attention as Bayesian inference, and the hard problem of qualia.

Key theorem: Global Workspace broadcast is EML-1 (winner-take-all softmax = Boltzmann
over workspace slots). Predictive coding free energy minimization is EML-2. Integrated
Information Φ is EML-2 (mutual information across a partition). Insight (aha moment)
is an EML-∞→EML-3 transition — non-analytic restructuring of the representational field.
Qualia themselves remain EML-∞: the explanatory gap is a genuine EML-∞ barrier.
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass

EML_INF = float("inf")


@dataclass
class GlobalWorkspace:
    """
    Global Workspace Theory (Baars/Dehaene): consciousness = broadcast from
    a bottleneck workspace to specialized processors.

    EML structure:
    - Competition: each processor i has activation a_i; broadcast winner = argmax a_i
    - Softmax broadcast: P(i wins) = exp(a_i/T) / Σ_j exp(a_j/T): EML-1 (Boltzmann)
    - Ignition threshold: when max_a > θ → broadcast = EML-∞ (step function at θ)
    - Reverberation after ignition: oscillatory maintenance ~ cos(ωt)exp(-t/τ): EML-3
    - Access consciousness: information in workspace = EML-1
    - Phenomenal consciousness: quality of content = EML-∞ (hard problem)
    """

    temperature: float = 1.0
    n_processors: int = 6

    def broadcast_probability(self, activations: list[float]) -> dict:
        """Softmax competition for workspace access."""
        exp_a = [math.exp(a / self.temperature) for a in activations]
        Z = sum(exp_a)
        probs = [e / Z for e in exp_a]
        winner = activations.index(max(activations))
        entropy = -sum(p * math.log(p + 1e-12) for p in probs)
        return {
            "activations": activations,
            "broadcast_probs": [round(p, 4) for p in probs],
            "winner": winner,
            "competition_entropy_nats": round(entropy, 4),
            "eml": 1,
            "reason": "Workspace competition = softmax Boltzmann over processor activations: EML-1.",
        }

    def ignition_threshold(self, activation: float, theta: float = 2.0) -> dict:
        """Step-function ignition: consciousness = 0 below θ, 1 above."""
        conscious = activation >= theta
        return {
            "activation": activation,
            "theta": theta,
            "conscious": conscious,
            "eml_subthreshold": 0,
            "eml_suprathreshold": 1,
            "eml_threshold_itself": EML_INF,
            "reason": "Ignition threshold step function at θ: discontinuity = EML-∞ transition.",
        }

    def reverberation(self, t: float, omega: float = 40.0, tau: float = 200.0) -> dict:
        """Post-ignition reverberation: A·exp(-t/τ)·cos(ωt) (gamma oscillation)."""
        omega_rad = omega * 2 * math.pi / 1000.0
        signal = math.exp(-t / tau) * math.cos(omega_rad * t)
        return {
            "t_ms": t,
            "omega_Hz": omega,
            "tau_ms": tau,
            "signal": round(signal, 6),
            "eml": 3,
            "reason": "exp(-t/τ)·cos(ωt): EML-1 decay × EML-3 oscillation = EML-3 (gamma reverberation).",
        }

    def to_dict(self) -> dict:
        test_acts = [[2.0, 1.0, 0.5, 0.3, 0.1, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]
        return {
            "broadcast": [self.broadcast_probability(a) for a in test_acts],
            "ignition": [self.ignition_threshold(a) for a in [0.5, 1.5, 2.0, 2.5, 3.0]],
            "reverberation": [self.reverberation(t) for t in [0, 10, 25, 50, 100, 200]],
            "eml_competition": 1,
            "eml_ignition_threshold": "∞",
            "eml_reverberation": 3,
            "eml_access_consciousness": 1,
            "eml_phenomenal_consciousness": "∞",
        }


@dataclass
class PredictiveCoding:
    """
    Predictive coding (Rao & Ballard / Friston): brain minimizes free energy
    F = E_q[ln q(s) - ln p(o,s)] (variational free energy = EML-2).

    EML structure:
    - Prediction error: ε = o - μ (observation - prediction): EML-0 (linear)
    - Precision-weighted error: ξ = Π·ε where Π = 1/σ²: EML-2 (inverse variance)
    - Free energy: F = ½ε²/σ² + ½ln(2πσ²): EML-2 (quadratic + log)
    - Belief update: μ ← μ + κ·ξ: EML-0 (gradient descent on F)
    - Precision hierarchy: Π at each level = EML-2 (meta-learning)
    - Active inference: action to minimize F → sensorimotor EML-2
    - Consciousness = minimizing surprise = minimizing ln p(o) = EML-2
    """

    def free_energy(self, obs: float, pred: float, sigma: float = 1.0) -> dict:
        """Variational free energy F = ½(o-μ)²/σ² + ½ln(2πσ²)."""
        epsilon = obs - pred
        F = 0.5 * epsilon**2 / sigma**2 + 0.5 * math.log(2 * math.pi * sigma**2)
        return {
            "obs": obs, "pred": pred, "sigma": sigma,
            "prediction_error": round(epsilon, 4),
            "free_energy": round(F, 4),
            "eml": 2,
            "reason": "F = ½ε²/σ² + ½ln(2πσ²): quadratic + log = EML-2 (Gaussian variational free energy).",
        }

    def precision_weighting(self, epsilon: float, sigma: float) -> dict:
        """Precision Π = 1/σ²; weighted error ξ = Π·ε."""
        Pi = 1.0 / sigma**2
        xi = Pi * epsilon
        return {
            "epsilon": epsilon, "sigma": sigma,
            "precision_Pi": round(Pi, 4),
            "weighted_error_xi": round(xi, 4),
            "eml": 2,
            "reason": "Precision Π=1/σ²: inverse variance = EML-2; ξ=Π·ε = EML-2.",
        }

    def surprise(self, obs: float, pred: float, sigma: float = 1.0) -> dict:
        """Surprise = -ln p(o) ≈ F (variational upper bound)."""
        surprise = 0.5 * ((obs - pred) / sigma)**2 + 0.5 * math.log(2 * math.pi * sigma**2)
        return {
            "obs": obs, "pred": pred,
            "surprise_nats": round(surprise, 4),
            "eml": 2,
            "reason": "Surprise = -ln p(o) ≈ F: EML-2 (Gaussian log-likelihood = quadratic + log).",
        }

    def to_dict(self) -> dict:
        scenarios = [(1.0, 0.5, 0.3), (2.0, 1.8, 0.5), (0.0, 1.0, 1.0)]
        return {
            "free_energy": [self.free_energy(o, p, s) for o, p, s in scenarios],
            "precision": [self.precision_weighting(e, s) for e, s in [(0.5, 0.3), (1.0, 1.0), (2.0, 0.1)]],
            "surprise": [self.surprise(o, p) for o, p in [(1.0, 0.5), (0.0, 1.0), (3.0, 3.0)]],
            "eml_free_energy": 2,
            "eml_precision": 2,
            "eml_surprise": 2,
            "eml_active_inference": 2,
        }


@dataclass
class IntegratedInformation:
    """
    Integrated Information Theory (Tononi Φ): consciousness = integrated information
    above a partition into parts.

    EML structure:
    - Φ = min over all bipartitions of MI(X; Y) restricted to the partition: EML-2
    - MI(X;Y) = H(X) + H(Y) - H(X,Y): EML-2 (Shannon entropy differences)
    - High-Φ systems: fully connected recurrent networks (EML-∞ in general)
    - Φ = 0: feedforward systems (no integration): EML-0
    - Φ → ∞ as system is fully integrated: EML-∞ (theoretical maximum)
    - Practical Φ for simple systems: EML-2
    """

    def mutual_information(self, p_xy: list[list[float]]) -> dict:
        """MI(X;Y) = Σ p(x,y) ln(p(x,y)/(p(x)p(y)))."""
        p_x = [sum(row) for row in p_xy]
        p_y = [sum(p_xy[i][j] for i in range(len(p_xy))) for j in range(len(p_xy[0]))]
        mi = 0.0
        for i, row in enumerate(p_xy):
            for j, p in enumerate(row):
                if p > 0 and p_x[i] > 0 and p_y[j] > 0:
                    mi += p * math.log(p / (p_x[i] * p_y[j]))
        return {
            "p_xy": p_xy,
            "MI_nats": round(mi, 4),
            "eml": 2,
            "reason": "MI = Σ p(x,y) log(p(x,y)/p(x)p(y)): product of probs inside log = EML-2.",
        }

    def phi_simple(self, phi_value: float) -> dict:
        """Return EML depth classification for a given Φ value."""
        if phi_value == 0.0:
            eml = 0
            regime = "feedforward — no integration"
        elif phi_value < float("inf"):
            eml = 2
            regime = "partially integrated — EML-2 information structure"
        else:
            eml = EML_INF
            regime = "maximally integrated — EML-∞ (theoretical)"
        return {
            "Phi": phi_value,
            "eml": "∞" if eml == EML_INF else eml,
            "regime": regime,
        }

    def to_dict(self) -> dict:
        p_ind = [[0.25, 0.25], [0.25, 0.25]]
        p_corr = [[0.4, 0.1], [0.1, 0.4]]
        return {
            "mutual_information": [
                self.mutual_information(p_ind),
                self.mutual_information(p_corr),
            ],
            "phi_regimes": [self.phi_simple(p) for p in [0.0, 0.5, 1.0, 2.0]],
            "eml_MI": 2,
            "eml_phi_partial": 2,
            "eml_phi_max": "∞",
            "eml_feedforward": 0,
        }


@dataclass
class InsightAndQualia:
    """
    Insight (aha moment) and qualia: the hardest EML problems in cognitive science.

    EML structure:
    - Insight = EML-∞ → EML-3 restructuring: problem rep jumps non-analytically
    - Impasse before insight: search in wrong EML-2 subspace
    - Resolution: EML-∞ discontinuous jump to EML-3 solution manifold
    - Qualia (redness, pain): EML-∞ — no EML-finite description of subjective experience
    - Explanatory gap: EML-∞ barrier between neural (EML-3) and phenomenal (EML-∞)
    - Zombies (Chalmers): physically identical (EML-3) but no qualia (EML-∞ absent)
    """

    def insight_dynamics(self, t: float, impasse_depth: float = 2.0) -> dict:
        """Impasse: EML-2 search. Insight: EML-∞ transition. Post-insight: EML-3."""
        if t < 0:
            phase = "pre-impasse"
            eml = 2
            progress = math.log(1 + abs(t))
        elif t == 0:
            phase = "insight (aha)"
            eml = EML_INF
            progress = float("inf")
        else:
            phase = "post-insight"
            eml = 3
            progress = math.cos(t / 10.0) * math.exp(-t / 100.0) + impasse_depth
        return {
            "t": t,
            "phase": phase,
            "progress_proxy": round(progress, 4) if progress < 1e9 else "→∞",
            "eml": "∞" if eml == EML_INF else eml,
        }

    def explanatory_gap(self) -> dict:
        """The hard problem: EML-∞ barrier between physical and phenomenal."""
        return {
            "physical_description_eml": 3,
            "phenomenal_experience_eml": "∞",
            "gap": "EML-∞ barrier",
            "reason": (
                "Physical (neural) description = EML-3 (gamma oscillations, NCC). "
                "Qualia = EML-∞: no EML-finite formula maps neural firing patterns to subjective redness. "
                "The explanatory gap IS the EML-∞ barrier — no finite composition of exp/ln crosses it."
            ),
            "chalmers_zombie": "EML-3 without EML-∞ supplement — physically complete, phenomenally absent",
            "panpsychism_eml": "Attempts to reduce EML-∞ to EML-3 by distributing qualia — fails by EML-∞ Gap",
        }

    def to_dict(self) -> dict:
        return {
            "insight_dynamics": [self.insight_dynamics(t) for t in [-5, -1, 0, 1, 5, 20]],
            "explanatory_gap": self.explanatory_gap(),
            "eml_impasse": 2,
            "eml_insight": "∞",
            "eml_post_insight": 3,
            "eml_qualia": "∞",
        }


def analyze_consciousness_deep_eml() -> dict:
    gw = GlobalWorkspace()
    pc = PredictiveCoding()
    ii = IntegratedInformation()
    iq = InsightAndQualia()
    return {
        "session": 121,
        "title": "Consciousness & Cognitive Science: EML Models of Attention, Insight & Qualia",
        "key_theorem": {
            "theorem": "EML Consciousness Stratification Theorem",
            "statement": (
                "Global Workspace broadcast competition is EML-1 (Boltzmann softmax). "
                "Predictive coding free energy F = ½ε²/σ² + ½ln(2πσ²) is EML-2. "
                "Integrated Information Φ = MI across bipartition is EML-2. "
                "Ignition threshold is EML-∞ (step-function discontinuity). "
                "Gamma reverberation is EML-3. "
                "Insight is an EML-∞→EML-3 transition (impasse→aha→solution). "
                "Qualia are EML-∞: the explanatory gap is a genuine EML-∞ barrier — "
                "no EML-finite formula maps neural activity to subjective experience."
            ),
        },
        "global_workspace": gw.to_dict(),
        "predictive_coding": pc.to_dict(),
        "integrated_information": ii.to_dict(),
        "insight_and_qualia": iq.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Prediction error ε=o-μ (linear); working memory count 7±2; feedforward Φ=0",
            "EML-1": "Workspace broadcast softmax; access consciousness; post-ignition amplitude",
            "EML-2": "Free energy F=½ε²/σ²+½ln(2πσ²); precision Π=1/σ²; integrated information Φ; surprise",
            "EML-3": "Gamma reverberation exp(-t/τ)·cos(ωt); post-insight representational structure",
            "EML-∞": "Ignition threshold; insight (aha); qualia; explanatory gap; hard problem of consciousness",
        },
        "rabbit_hole_log": [
            "The Global Workspace is an EML-1 machine: the competition among processors for workspace access is exactly a Boltzmann distribution at temperature T (attention temperature). High-temperature attention (T→∞) = uniform broadcast (democratic); low T → winner-take-all (focused). The transformer's softmax attention (S119) and the brain's workspace competition (S121) are the SAME EML-1 mechanism — evolution and engineering converged on the same Boltzmann ground state.",
            "Predictive coding is EML-2: the variational free energy F = ½ε²/σ² + ½ln(2πσ²) is identical to the negative log-likelihood of a Gaussian — EML-2 by the same argument as all Gaussian statistics (heat kernel S62, BSM option price S64, Fisher information S60). Friston's free energy principle unifies attention, perception, and action under one EML-2 functional — the same functional that appears in thermodynamics (Helmholtz F=-kT ln Z, EML-2) and information theory (rate-distortion R(D), EML-2).",
            "Insight is EML-∞→EML-3: during impasse the system searches in an EML-2 subspace (the wrong problem representation), hits an EML-∞ barrier (dead end = local minimum), and then undergoes a non-analytic restructuring to a new EML-3 representational frame (the aha moment). This is the cognitive analog of the phase transition: Ising T_c (S57), epidemic R₀=1 (S113), neural criticality σ=1 (S118). Restructuring = phase transition in the representational field.",
            "The explanatory gap (Chalmers 1995) is the EML-∞ barrier: we can give EML-3 descriptions of neural correlates of consciousness (NCC: gamma oscillations, S101/S118), but no EML-finite formula maps these to the subjective quality of experience (qualia). The gap is not a gap in our knowledge but a structural EML-∞ barrier — the same barrier that separates computable from uncomputable (S109). Qualia are EML-∞ in the same sense that Gödel sentences are EML-∞: they exist but cannot be reached by any finite EML tree.",
        ],
        "connections": {
            "to_session_119": "Transformer softmax (EML-1) = Global Workspace broadcast (EML-1): same Boltzmann mechanism.",
            "to_session_118": "Neural criticality σ=1 (EML-∞) = ignition threshold (EML-∞): same phase transition.",
            "to_session_109": "Qualia EML-∞ ↔ Gödel sentence EML-∞: both are real but EML-unreachable by finite composition.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_consciousness_deep_eml(), indent=2, default=str))
