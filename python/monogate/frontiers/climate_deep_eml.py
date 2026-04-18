"""
Session 127 — Climate & Earth Systems: Coupled Models & Tipping Point Dynamics

AMOC collapse, ice-albedo feedback, permafrost carbon release, climate sensitivity
distributions, paleoclimate variability, and tipping cascade networks.

Key theorem: Individual climate feedbacks are EML-2 (Planck -4σT³, water vapor
Clausius-Clapeyron = EML-1, ice-albedo = EML-2). Climate sensitivity distribution
P(λ) = fat-tailed log-normal = EML-2. AMOC and ice sheet tipping points are EML-∞
(saddle-node bifurcation). Tipping cascade: if two EML-∞ tipping elements are coupled,
the coupled system has lower tipping threshold — cascade of EML-∞ events.
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass

EML_INF = float("inf")


@dataclass
class ClimateFeeback:
    """
    Climate feedback analysis.

    EML structure:
    - Planck feedback: α_P = -4σT³: EML-2 (cubic in T = power law)
    - Water vapor feedback: amplifies by factor 1/(1-f): EML-1 (geometric series of EML-1 terms)
    - Ice-albedo: Δα ≈ α_ice - α_ocean = EML-0 (constant albedo difference); T_trigger = EML-∞
    - Total feedback parameter: λ = Σαᵢ / α_P: EML-2 (ratio of feedbacks)
    - Climate sensitivity ECS = F₂ₓ/λ: EML-2 (forcing / feedback = EML-2)
    - ECS distribution: log-normal P(λ) → fat tail: EML-2 (log-normal = EML-2)
    """

    sigma_sb: float = 5.67e-8

    def planck_feedback(self, T: float) -> dict:
        """α_P = -4σT³: Planck (blackbody) feedback."""
        alpha_P = -4 * self.sigma_sb * T**3
        return {
            "T_K": T,
            "alpha_P_Wm2K": round(alpha_P, 4),
            "eml": 2,
            "reason": "-4σT³: cubic power law = EML-2.",
        }

    def ecs_estimate(self, F_2x: float = 3.7, lambda_total: float = -1.2) -> dict:
        """ECS = F₂ₓ/|λ|: equilibrium climate sensitivity."""
        ecs = -F_2x / lambda_total
        return {
            "F_2x_Wm2": F_2x,
            "lambda_Wm2K": lambda_total,
            "ECS_K": round(ecs, 2),
            "eml": 2,
            "reason": "ECS=F₂ₓ/|λ|: ratio of forcing to feedback = EML-2.",
        }

    def ecs_lognormal(self, ecs: float, mu: float = 1.1, sigma: float = 0.4) -> dict:
        """Log-normal ECS distribution: P(S) ~ log-normal(μ,σ)."""
        ln_s = math.log(ecs)
        P = (1 / (ecs * sigma * math.sqrt(2 * math.pi))) * math.exp(
            -0.5 * ((ln_s - mu) / sigma) ** 2
        )
        return {
            "ECS": ecs,
            "P_ECS": round(P, 6),
            "eml": 2,
            "reason": "Log-normal: P=exp(-½((ln S-μ)/σ)²)/(Sσ√2π): Gaussian of log = EML-2.",
        }

    def to_dict(self) -> dict:
        return {
            "planck": [self.planck_feedback(T) for T in [255, 275, 288, 310]],
            "ecs_estimate": [self.ecs_estimate(3.7, l) for l in [-0.5, -0.8, -1.2, -2.0]],
            "ecs_distribution": [self.ecs_lognormal(s) for s in [1.0, 2.0, 3.0, 4.5, 6.0]],
            "eml_planck_feedback": 2,
            "eml_ecs": 2,
            "eml_ecs_distribution": 2,
        }


@dataclass
class TippingPoints:
    """
    Climate tipping elements and saddle-node bifurcations.

    EML structure:
    - Saddle-node bifurcation: dx/dt = r + x - x³ = 0: fold at x_c = √(r_c/3): EML-2
    - Before tipping: recovery rate → 0 (critical slowing): |eigenvalue| = EML-2
    - At tipping: eigenvalue = 0: EML-∞ (infinite timescale = phase transition)
    - AMOC: hysteresis = EML-∞ (bistability)
    - Ice sheet: T_tip ~ 1.5°C above pre-industrial: EML-∞ (irreversible collapse)
    - Permafrost: carbon release rate = EML-1 (exponential Q₁₀ factor)
    - Cascade: if element A tips → forces B → cascade probability = EML-∞
    """

    def saddle_node_bifurcation(self, r: float) -> dict:
        """Normal form: dx/dt = r + x - x³. Fixed points where r + x - x³ = 0."""
        r_c = -2.0 / (3 * math.sqrt(3))
        if r > abs(r_c):
            fixed_points = []
            regime = "no stable state — tipped"
            eml = EML_INF
        elif abs(r - r_c) < 0.01:
            fixed_points = [-1 / math.sqrt(3)]
            regime = "at saddle-node bifurcation"
            eml = EML_INF
        else:
            x_stable = 1.0
            fixed_points = [x_stable, -x_stable]
            regime = "bistable"
            eml = 2
        return {
            "r": r,
            "r_critical": round(r_c, 4),
            "fixed_points_approx": [round(x, 3) for x in fixed_points],
            "regime": regime,
            "eml": "∞" if eml == EML_INF else eml,
            "reason": "Saddle-node: fixed point √(r/3): EML-2 (square root). Bifurcation at r_c: EML-∞.",
        }

    def critical_slowing_down(self, delta_r: float, r_c: float = -0.385) -> dict:
        """Recovery rate ~ |r - r_c|^{1/2}: EML-2 (square root vanishes at tipping)."""
        if delta_r <= 0:
            return {"delta_r": delta_r, "recovery_rate": 0.0, "eml": "∞"}
        rate = math.sqrt(abs(delta_r))
        return {
            "delta_r_to_tipping": delta_r,
            "recovery_rate": round(rate, 4),
            "eml": 2,
            "reason": "Recovery rate ~ |Δr|^{1/2}: EML-2 square root diverges (→0) at tipping.",
        }

    def permafrost_q10(self, T_anomaly: float, Q10: float = 2.0) -> dict:
        """Soil respiration Q₁₀: R(T) = R₀·Q₁₀^{T/10}."""
        R = Q10 ** (T_anomaly / 10)
        return {
            "T_anomaly_K": T_anomaly,
            "Q10": Q10,
            "respiration_multiplier": round(R, 4),
            "eml": 1,
            "reason": "R=Q₁₀^{T/10}=exp((T/10)·ln Q₁₀): EML-1 (exponential in temperature).",
        }

    def tipping_cascade(self, n_elements: int, coupling: float) -> dict:
        """Probability cascade propagates to ≥k elements: P~exp(-n/coupling)."""
        P_cascade = 1 - math.exp(-coupling * n_elements)
        return {
            "n_tipping_elements": n_elements,
            "coupling": coupling,
            "P_cascade": round(P_cascade, 4),
            "eml_each_tipping": "∞",
            "eml_cascade_probability": 2,
            "reason": "P=1-exp(-λn): EML-2 (complementary exponential). Each individual tip = EML-∞.",
        }

    def to_dict(self) -> dict:
        return {
            "saddle_node": [self.saddle_node_bifurcation(r) for r in [-0.5, -0.39, -0.385, -0.3, 0.0]],
            "critical_slowing": [self.critical_slowing_down(d) for d in [0.0, 0.01, 0.1, 0.5, 1.0]],
            "permafrost": [self.permafrost_q10(T) for T in [0, 1, 2, 3, 4, 6]],
            "cascade": [self.tipping_cascade(n, 0.3) for n in [1, 3, 5, 9, 15]],
            "eml_stable_state": 2,
            "eml_bifurcation": "∞",
            "eml_permafrost_q10": 1,
            "eml_cascade_prob": 2,
        }


@dataclass
class PaleoclimateVariability:
    """
    Paleoclimate: Dansgaard-Oeschger events, orbital forcing, climate noise.

    EML structure:
    - Orbital (Milankovitch): e, ε, ψ vary with periods 100kyr/41kyr/23kyr: EML-3
      (quasi-periodic = sum of EML-3 trig terms)
    - Milankovitch forcing: F(t) = Σ Aᵢcos(ωᵢt + φᵢ): EML-3 (Fourier = EML-3)
    - Dansgaard-Oeschger events: abrupt ΔTNH ≈ 10-15K in decades: EML-∞ (abrupt)
    - Stochastic resonance: signal enhanced by noise at critical noise level = EML-∞
    - Ice core δ¹⁸O: log(ratio) of isotopes = EML-2
    - Red climate noise: P(f) ~ f^{-β}: EML-2 (power law = EML-2)
    """

    def orbital_forcing(self, t_kyr: float, amplitudes: list[float] = None,
                         periods: list[float] = None) -> dict:
        """Milankovitch forcing: F = Σ Aᵢcos(2πt/Tᵢ)."""
        if amplitudes is None:
            amplitudes = [0.5, 0.3, 0.2]
        if periods is None:
            periods = [100.0, 41.0, 23.0]
        F = sum(A * math.cos(2 * math.pi * t_kyr / T)
                for A, T in zip(amplitudes, periods))
        return {
            "t_kyr": t_kyr,
            "F_forcing": round(F, 4),
            "periods_kyr": periods,
            "eml": 3,
            "reason": "F=ΣAᵢcos(2πt/Tᵢ): Fourier trig sum = EML-3.",
        }

    def climate_noise_spectrum(self, f: float, beta: float = 1.5) -> dict:
        """Red noise P(f) ~ f^{-β}."""
        if f <= 0:
            return {"f": f, "P_f": float("inf"), "eml": 2}
        P = f ** (-beta)
        return {
            "f_per_kyr": f, "beta": beta,
            "P_f": round(P, 6),
            "eml": 2,
            "reason": "P(f)~f^{-β}: power law spectrum = EML-2 (red noise = EML-2).",
        }

    def do_event_eml(self) -> dict:
        """Dansgaard-Oeschger event: abrupt warming = EML-∞."""
        return {
            "event": "Dansgaard-Oeschger",
            "amplitude_K": 15,
            "duration_years": 50,
            "eml_gradual_baseline": 2,
            "eml_abrupt_event": "∞",
            "reason": (
                "DO events: ΔTNH~10-15K in ~50 years — abrupt, non-analytic warming. "
                "= EML-∞ (AMOC reorganization = saddle-node bifurcation = EML-∞ phase transition)."
            ),
        }

    def to_dict(self) -> dict:
        return {
            "orbital_forcing": [self.orbital_forcing(t) for t in [0, 25, 50, 100, 200]],
            "red_noise": [self.climate_noise_spectrum(f) for f in [0.01, 0.1, 1.0, 10.0]],
            "do_events": self.do_event_eml(),
            "eml_orbital_forcing": 3,
            "eml_red_noise": 2,
            "eml_do_events": "∞",
        }


def analyze_climate_deep_eml() -> dict:
    cf = ClimateFeeback()
    tp = TippingPoints()
    pv = PaleoclimateVariability()
    return {
        "session": 127,
        "title": "Climate & Earth Systems: Coupled Models & Tipping Point Dynamics",
        "key_theorem": {
            "theorem": "EML Climate Tipping Theorem",
            "statement": (
                "Planck feedback -4σT³ is EML-2 (cubic power law). "
                "ECS = F₂ₓ/|λ| is EML-2. ECS log-normal distribution is EML-2. "
                "Saddle-node bifurcation fixed points ±√(r/3) are EML-2; bifurcation point is EML-∞. "
                "Critical slowing down recovery rate ~|Δr|^{1/2} is EML-2 (vanishes at tipping). "
                "Permafrost Q₁₀ respiration Q₁₀^{T/10} is EML-1 (exponential). "
                "Orbital (Milankovitch) forcing Σ cos(2πt/T) is EML-3. "
                "Red climate noise P(f)~f^{-β} is EML-2. "
                "Dansgaard-Oeschger events and AMOC collapse are EML-∞ (saddle-node phase transitions)."
            ),
        },
        "climate_feedbacks": cf.to_dict(),
        "tipping_points": tp.to_dict(),
        "paleoclimate": pv.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Albedo difference Δα=const; dimension d=3; latitude λ (constant parameter)",
            "EML-1": "Clausius-Clapeyron exp(-L/RT); permafrost Q₁₀^{T/10}; water vapor feedback geometric series",
            "EML-2": "Planck -4σT³; ECS=F₂ₓ/λ; ECS log-normal; saddle-node fixed points; critical slowing √|Δr|; red noise f^{-β}; CO₂ forcing 5.35 ln(C/C₀)",
            "EML-3": "Orbital forcing Σcos(2πt/T); ENSO oscillation; Milankovitch quasi-periodic signal",
            "EML-∞": "AMOC collapse; ice sheet collapse; permafrost cascade; DO events; saddle-node bifurcation",
        },
        "rabbit_hole_log": [
            "The tipping point is an EML-∞ event by the saddle-node bifurcation theorem: at the critical parameter value r_c, the stable and unstable fixed points collide and annihilate. The system's eigenvalue passes through zero — infinite relaxation time = EML-∞. Critical slowing down (the observable precursor) sees the recovery rate shrink as √|r-r_c| = EML-2 approaching zero. The tipping itself (eigenvalue=0) is EML-∞. This is the same structure as ALL EML-∞ phase transitions: Ising T_c (eigenvalue of transfer matrix → 1), laser threshold (gain = loss), epidemic R₀=1 (SIR Jacobian eigenvalue → 0).",
            "Climate sensitivity has a fat-tailed log-normal distribution because it is a ratio of sums: ECS = F₂ₓ/|λ| where λ = Σλᵢ (sum of feedbacks). When feedback components are uncertain, their sum is Gaussian in log-space (central limit theorem applied to log-normally distributed feedbacks) → log-normal ECS. The fat upper tail (P(ECS>4.5°C) > 0) means the ECS distribution is EML-2 (log-normal) with a tail that never reaches EML-∞ probability — rare but not singular.",
            "Dansgaard-Oeschger events are the paleoclimate analog of phase transitions: in 50 years, ΔTNH~15K — ten times faster than forced anthropogenic warming. The mechanism is AMOC reorganization (EML-∞ saddle-node). The Greenland ice core δ¹⁸O record shows 25 DO events in the last 120 kyr, each a saw-tooth: rapid warming (EML-∞ phase transition), slow cooling (EML-1 exponential return toward baseline). The asymmetric saw-tooth = EML-∞ up + EML-1 down = the same asymmetry as the Asymmetry Theorem (S111): d(exp)=1 < d(inverse)=∞.",
        ],
        "connections": {
            "to_session_107": "S107 covered EBM, CO₂ forcing, tipping overview. S127 adds saddle-node (EML-∞ structure), critical slowing, DO events, paleoclimate.",
            "to_session_57": "Saddle-node bifurcation (EML-∞) = Ising phase transition (EML-∞): both have eigenvalue→0 at criticality.",
            "to_session_111": "DO saw-tooth: EML-∞ up + EML-1 down = EML Asymmetry Theorem applied to climate dynamics.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_climate_deep_eml(), indent=2, default=str))
