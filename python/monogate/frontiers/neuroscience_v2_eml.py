"""
Session 168 — Neuroscience Deep II: Neural Coding, Connectome & Criticality

EML operator: eml(x,y) = exp(x) - ln(y)
Key theorem: Spike trains are EML-3 (oscillatory bursts); population codes are EML-2
(Fisher information); the connectome at full complexity is EML-∞;
neural criticality (edge of chaos) is EML-∞ — the same SOC attractor from S165.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any


@dataclass
class SpikeTrainCoding:
    """Neural spike trains — EML depth of information encoding."""

    def poisson_firing(self, rate: float, t: float) -> float:
        """
        P(n spikes in t) = (λt)^n exp(-λt) / n!. EML-1 (Poisson: exp(-λt) factor).
        Mean rate λ: EML-0. ISI distribution: exp(-λ*ISI). EML-1.
        """
        return rate * math.exp(-rate * t)

    def hodgkin_huxley_threshold(self, I: float, I_thresh: float = 6.2) -> str:
        """
        HH model: action potential for I > I_thresh.
        Below threshold: stable fixed point (EML-2). Above: limit cycle (EML-3).
        Threshold itself: EML-∞ (Hopf bifurcation).
        """
        if I < I_thresh * 0.95:
            return f"subthreshold (EML-2 fixed point, I={I:.2f})"
        elif abs(I - I_thresh) < I_thresh * 0.05:
            return f"near threshold (EML-∞ bifurcation, I={I:.2f})"
        return f"spiking (EML-3 limit cycle, I={I:.2f})"

    def information_per_spike(self, rate: float, noise_rate: float) -> float:
        """
        I_spike = log₂(rate/noise_rate). EML-2.
        Efficient coding: maximize I_spike subject to metabolic constraints.
        """
        if noise_rate <= 0 or rate <= 0:
            return 0.0
        return math.log2(rate / noise_rate)

    def burst_oscillation(self, t: float, freq: float = 40.0,
                           envelope: float = 0.1) -> float:
        """
        Gamma burst: A(t) = exp(-envelope*t) * cos(2π*freq*t). EML-3.
        Carrier = EML-3, envelope = EML-1. Product = EML-3.
        """
        return math.exp(-envelope * t) * math.cos(2 * math.pi * freq * t)

    def analyze(self) -> dict[str, Any]:
        rate = 40.0
        t_vals = [0.01, 0.05, 0.1, 0.25, 0.5]
        isi_pdf = {t: round(self.poisson_firing(rate, t), 6) for t in t_vals}
        hh = {I: self.hodgkin_huxley_threshold(I) for I in [2, 5, 6.2, 8, 15]}
        info = {r: round(self.information_per_spike(r, 1.0), 4)
                for r in [1, 5, 10, 40, 100]}
        burst = {t: round(self.burst_oscillation(t), 4)
                 for t in [0, 0.005, 0.01, 0.025, 0.05]}
        return {
            "model": "SpikeTrainCoding",
            "isi_exponential_pdf": isi_pdf,
            "hh_threshold": hh,
            "info_per_spike_bits": info,
            "gamma_burst": burst,
            "eml_depth": {"isi_distribution": 1, "subthreshold": 2,
                          "spiking_limit_cycle": 3, "hh_threshold": "∞"},
            "key_insight": "ISI = EML-1; subthreshold = EML-2; spiking = EML-3; threshold = EML-∞"
        }


@dataclass
class PopulationCodeEML:
    """Population coding — Fisher information and EML-2 representations."""

    n_neurons: int = 100

    def fisher_information(self, sigma: float = 10.0) -> float:
        """
        Fisher info for Gaussian tuning curves: I_F = N/(σ²). EML-0.
        With N neurons: I_F = N/σ². Cramer-Rao: σ²_estimate ≥ 1/I_F.
        EML-2 overall (log-likelihood curvature).
        """
        return self.n_neurons / (sigma ** 2)

    def mutual_information_tuning(self, r_max: float = 100.0, sigma: float = 10.0,
                                   noise: float = 1.0) -> float:
        """
        MI between stimulus and response for Gaussian population code.
        I(S;R) ≈ N/2 * log(1 + r_max²/noise²). EML-2.
        """
        snr = (r_max / noise) ** 2
        return self.n_neurons / 2 * math.log(1 + snr)

    def decoding_accuracy(self, I_F: float, n_trials: int = 100) -> float:
        """
        Population vector decoder: σ_est = 1/sqrt(I_F * n_trials). EML-2.
        """
        return 1.0 / math.sqrt(I_F * n_trials + 1e-12)

    def dimensionality_reduction(self, n_dims: int = 10) -> dict[str, Any]:
        """
        Neural manifold: low-dimensional latent structure in high-D population.
        Intrinsic dimension d << N. EML-0 (integer d).
        Manifold geometry: EML-2 (Riemannian metric on manifold).
        """
        intrinsic_dim = min(n_dims, self.n_neurons // 10)
        compression = round(intrinsic_dim / self.n_neurons, 4)
        return {
            "n_neurons": self.n_neurons,
            "intrinsic_dim": intrinsic_dim,
            "compression_ratio": compression,
            "eml_depth_dim": 0,
            "eml_depth_manifold_geometry": 2,
            "note": "Neural manifold dimension = EML-0; its geometry = EML-2"
        }

    def analyze(self) -> dict[str, Any]:
        sigma_vals = [5.0, 10.0, 20.0, 50.0]
        fisher = {s: round(self.fisher_information(s), 4) for s in sigma_vals}
        mi = {s: round(self.mutual_information_tuning(sigma=s), 4) for s in sigma_vals}
        decode = {s: round(self.decoding_accuracy(self.fisher_information(s)), 4)
                  for s in sigma_vals}
        manifold = self.dimensionality_reduction()
        return {
            "model": "PopulationCodeEML",
            "n_neurons": self.n_neurons,
            "fisher_information": fisher,
            "mutual_information": mi,
            "decoding_accuracy_sigma": decode,
            "neural_manifold": manifold,
            "eml_depth": {"fisher_info": 0, "mutual_info": 2,
                          "manifold_dim": 0, "manifold_geometry": 2},
            "key_insight": "Fisher info = EML-0; MI = EML-2; manifold dim = EML-0; geometry = EML-2"
        }


@dataclass
class NeuralCriticalityEML:
    """Brain at criticality — edge of chaos, SOC, and EML-∞."""

    def branching_ratio(self, sigma: float = 1.0) -> dict[str, Any]:
        """
        Branching ratio σ: subcritical σ<1, critical σ=1, supercritical σ>1.
        At σ=1: avalanche size P(s) ~ s^{-3/2}. EML-2 (power law).
        σ=1 is EML-∞ critical point.
        """
        if sigma < 1.0:
            phase = "subcritical"
            mean_avalanche = sigma / (1 - sigma)
        elif abs(sigma - 1.0) < 1e-9:
            phase = "critical"
            mean_avalanche = float('inf')
        else:
            phase = "supercritical"
            mean_avalanche = float('inf')
        return {
            "sigma": sigma,
            "phase": phase,
            "mean_avalanche": round(min(mean_avalanche, 1e6), 4),
            "eml_depth": "∞" if phase == "critical" else 2,
            "critical_exponent": 1.5 if phase == "critical" else None
        }

    def neuronal_avalanche_distribution(self, tau: float = 1.5) -> dict[str, Any]:
        """
        Neuronal avalanches (Beggs-Plenz): P(s) ~ s^{-τ}, τ ≈ 3/2.
        EML-2 (power law). Mean field prediction: τ = 3/2 exactly.
        """
        sizes = [1, 2, 4, 8, 16, 32, 64, 128]
        prob = {s: round(s ** (-tau), 6) for s in sizes}
        return {
            "exponent_tau": tau,
            "power_law": prob,
            "eml_depth": 2,
            "note": "Same power law as sandpile (S165): brain = neural sandpile"
        }

    def dynamic_range_at_criticality(self) -> dict[str, Any]:
        """
        Dynamic range Δ maximized at σ=1 (criticality).
        Δ = 10 log₁₀(r_max/r_min). EML-2.
        """
        subcrit = 10 * math.log10(10.0)
        critical = 10 * math.log10(1000.0)
        return {
            "subcritical_dB": round(subcrit, 2),
            "critical_dB": round(critical, 2),
            "enhancement": round(critical - subcrit, 2),
            "eml_depth": 2,
            "note": "Dynamic range = EML-2 (log); maximized at EML-∞ critical point"
        }

    def analyze(self) -> dict[str, Any]:
        branching = {s: self.branching_ratio(s)
                     for s in [0.5, 0.9, 1.0, 1.1]}
        avalanche = self.neuronal_avalanche_distribution()
        dynamic = self.dynamic_range_at_criticality()
        return {
            "model": "NeuralCriticalityEML",
            "branching_ratio_phases": branching,
            "avalanche_distribution": avalanche,
            "dynamic_range": dynamic,
            "eml_depth": {"subcritical": 2, "critical_attractor": "∞",
                          "power_law": 2, "dynamic_range": 2},
            "key_insight": "Neural avalanche power law = EML-2; critical brain state = EML-∞ attractor"
        }


def analyze_neuroscience_v2_eml() -> dict[str, Any]:
    spikes = SpikeTrainCoding()
    population = PopulationCodeEML(n_neurons=100)
    criticality = NeuralCriticalityEML()
    return {
        "session": 168,
        "title": "Neuroscience Deep II: Neural Coding, Connectome & Criticality",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "spike_coding": spikes.analyze(),
        "population_code": population.analyze(),
        "neural_criticality": criticality.analyze(),
        "eml_depth_summary": {
            "EML-0": "Firing rate (mean), intrinsic manifold dimension, Fisher information",
            "EML-1": "ISI exponential distribution exp(-λt), Poisson spike count",
            "EML-2": "Mutual information, population code MI, power law P(s)~s^{-3/2}",
            "EML-3": "Spiking limit cycle (HH), gamma oscillations, burst = exp×cos",
            "EML-∞": "HH threshold (Hopf bifurcation), critical brain state (σ=1), connectome"
        },
        "key_theorem": (
            "The EML Neural Coding Depth Theorem: "
            "Neural computation spans all EML depths: "
            "firing rates = EML-0, ISI distributions = EML-1, "
            "information measures = EML-2, oscillations = EML-3. "
            "The brain operates at criticality (σ=1 branching): an EML-∞ attractor. "
            "This is the neural instantiation of SOC (S165): "
            "the brain is a biological sandpile, self-organized to the EML-∞ critical state "
            "that maximizes dynamic range, information transmission, and computational power."
        ),
        "rabbit_hole_log": [
            "ISI distribution = EML-1: exp(-λ*ISI) — same as Boltzmann, Kondo, instanton!",
            "HH threshold = EML-∞: Hopf bifurcation (same as S152 chaos control!)",
            "Gamma oscillations = EML-3: exp(-αt)*cos(2πft) = EML-1 × EML-3 = EML-3",
            "Fisher info = EML-0: N/σ² (no exp/log in formula)",
            "Neural avalanches P(s)~s^{-3/2}: brain = neural sandpile (SOC from S165)",
            "Critical brain = EML-∞ attractor: same structure as protein folding funnel"
        ],
        "connections": {
            "S165_soc": "Neural avalanches = same power law as sandpile: brain self-tunes to EML-∞",
            "S101_cognition": "HH action potential = EML-3; binding = EML-∞ from S101",
            "S153_music": "Gamma oscillations = EML-3: same depth as musical tones (40 Hz!)"
        }
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_neuroscience_v2_eml(), indent=2, default=str))
