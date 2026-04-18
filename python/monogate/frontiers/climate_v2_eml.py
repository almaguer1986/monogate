"""
Session 137 — Climate & Earth Systems Deep II: Feedback, Tipping Points & Paleoclimate

EML operator: eml(x,y) = exp(x) - ln(y)
EML depth hierarchy: 0 (topology) | 1 (equilibria) | 2 (geometry) | 3 (waves) | ∞ (singularities)

Key theorem: Climate equilibria are EML-2; tipping points and irreversible transitions are EML-∞.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# 1. Energy Balance Model & Feedback
# ---------------------------------------------------------------------------

@dataclass
class EnergyBalanceModelV2:
    """Budyko-Sellers energy balance: dT/dt = Q(1-α) - εσT⁴."""

    Q: float = 342.0     # Solar constant / 4 (W/m²)
    epsilon: float = 0.78  # emissivity
    sigma: float = 5.67e-8  # Stefan-Boltzmann
    alpha_ice: float = 0.6   # ice albedo
    alpha_ocean: float = 0.1  # ocean albedo
    C: float = 2e8           # heat capacity (J/m²/K)

    def outgoing_longwave(self, T: float) -> float:
        """OLR = ε σ T⁴. EML-2 (fourth power = exp(4·ln(T)))."""
        return self.epsilon * self.sigma * (T ** 4)

    def incoming_shortwave(self, alpha: float) -> float:
        """ASR = Q(1-α). EML-0 (linear)."""
        return self.Q * (1 - alpha)

    def equilibrium_temperature(self, alpha: float) -> float:
        """T_eq = (Q(1-α)/(εσ))^{1/4}. EML-2."""
        incoming = self.incoming_shortwave(alpha)
        return (incoming / (self.epsilon * self.sigma)) ** 0.25

    def ice_albedo_feedback(self, T: float, T_freeze: float = 263.0) -> float:
        """
        Ice-albedo: α(T) = α_ice if T < T_freeze, else α_ocean.
        The transition is EML-∞ (step function / bifurcation).
        """
        if T < T_freeze:
            return self.alpha_ice
        return self.alpha_ocean

    def climate_sensitivity(self, CO2_doubling: bool = True) -> float:
        """
        ECS: equilibrium climate sensitivity ≈ 3°C per CO2 doubling.
        ΔT = λ * ΔF where ΔF = 3.7 W/m² for 2xCO2. EML-2.
        """
        lambda_feedback = 0.8  # K/(W/m²)
        delta_F = 3.7 if CO2_doubling else 0.0
        return lambda_feedback * delta_F

    def feedback_factor(self, wv_feedback: float = 1.8,
                        cloud_feedback: float = 0.4,
                        lapse_rate: float = -0.6) -> float:
        """
        Total feedback f = Σ feedbacks. Gain factor G = 1/(1-f). EML-2.
        Water vapor WV ≈ +1.8, cloud ≈ +0.4, lapse rate ≈ -0.6 W/m²/K.
        """
        f = (wv_feedback + cloud_feedback + lapse_rate) / 3.2  # normalize by Planck response
        if f >= 1.0:
            return float('inf')  # runaway greenhouse = EML-∞
        return 1.0 / (1.0 - f)

    def analyze(self) -> dict[str, Any]:
        T_ice = self.equilibrium_temperature(self.alpha_ice)
        T_ocean = self.equilibrium_temperature(self.alpha_ocean)
        T_current = self.equilibrium_temperature(0.3)

        albedo_vals = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        T_eq_vals = {a: round(self.equilibrium_temperature(a) - 273.15, 2)
                     for a in albedo_vals}

        ecs = self.climate_sensitivity()
        gain = self.feedback_factor()

        return {
            "model": "EnergyBalanceModelV2",
            "T_ice_eq_C": round(T_ice - 273.15, 2),
            "T_ocean_eq_C": round(T_ocean - 273.15, 2),
            "T_current_eq_C": round(T_current - 273.15, 2),
            "T_eq_vs_albedo_C": T_eq_vals,
            "ECS_degC_per_2xCO2": round(ecs, 2),
            "feedback_gain_factor": round(gain, 3),
            "ice_albedo_transition": "EML-∞ (discontinuous bifurcation at T_freeze)",
            "eml_depth": {
                "OLR_T4": 2,
                "equilibrium_temperature": 2,
                "climate_sensitivity": 2,
                "ice_albedo_feedback": "∞"
            },
            "key_insight": "EBM equilibrium = EML-2 (T^{1/4} formula); ice-albedo bifurcation = EML-∞"
        }


# ---------------------------------------------------------------------------
# 2. Tipping Points
# ---------------------------------------------------------------------------

@dataclass
class ClimateTippingPoints:
    """Lenton et al. (2008): tipping elements — abrupt, potentially irreversible transitions."""

    amoc_threshold: float = 0.5   # AMOC weakening fraction at tipping
    amazon_threshold: float = 0.4  # deforestation fraction

    def cusp_bifurcation(self, x: float, r: float, a: float = 1.0) -> float:
        """
        Normal form of fold bifurcation: dx/dt = r + a*x - x³.
        Equilibrium: x* is a root. At saddle-node bifurcation: EML-∞.
        """
        return r + a * x - x ** 3

    def fold_bifurcation_points(self, a: float = 1.0) -> tuple[float, float]:
        """
        Fold points: r* = ±(2/3√3) * a^{3/2}. EML-2.
        """
        r_crit = (2.0 / (3.0 * math.sqrt(3.0))) * (a ** 1.5)
        return (-r_crit, r_crit)

    def amoc_strength(self, t: float, t_tip: float = 50.0) -> float:
        """
        AMOC collapses at tipping: logistic decay. EML-∞ event.
        Pre-collapse: slow decline (EML-1). Post-collapse: EML-∞ jump.
        """
        slow_decline = math.exp(-0.005 * t)  # EML-1 slow weakening
        collapse_sigmoid = 1.0 / (1 + math.exp(-0.3 * (t - t_tip)))
        return slow_decline * (1 - self.amoc_threshold * collapse_sigmoid)

    def critical_slowing_down(self, r_vals: list[float], r_crit: float) -> list[float]:
        """
        Near tipping: recovery rate ~ |r - r_crit|. EML-2.
        Critical slowing down: recovery → 0 at r_crit.
        """
        return [abs(r - r_crit) for r in r_vals]

    def amazon_dieback(self, deforestation: float) -> float:
        """
        Amazon dieback: if deforestation > threshold, precipitation collapse → EML-∞.
        Below threshold: linear degradation (EML-0).
        """
        if deforestation < self.amazon_threshold:
            return 1.0 - deforestation / self.amazon_threshold * 0.3
        return 0.0  # collapse = EML-∞ irreversible transition

    def analyze(self) -> dict[str, Any]:
        r_vals = [-0.5, -0.3, -0.1, 0.0, 0.1, 0.3, 0.5]
        fold_neg, fold_pos = self.fold_bifurcation_points()
        recovery_rates = self.critical_slowing_down(r_vals, 0.0)

        t_vals = [0, 20, 40, 50, 55, 60, 80]
        amoc = {t: round(self.amoc_strength(t), 4) for t in t_vals}

        defor_vals = [0.1, 0.2, 0.3, 0.39, 0.4, 0.5]
        amazon = {d: round(self.amazon_dieback(d), 4) for d in defor_vals}

        return {
            "model": "ClimateTippingPoints",
            "fold_bifurcation_critical_r": (round(fold_neg, 4), round(fold_pos, 4)),
            "critical_slowing_down": {round(r, 1): round(rec, 4)
                                       for r, rec in zip(r_vals, recovery_rates)},
            "amoc_strength_vs_time": amoc,
            "amazon_dieback_vs_deforestation": amazon,
            "known_tipping_elements": [
                "West Antarctic Ice Sheet: EAIS-∞",
                "Greenland Ice Sheet: EML-∞",
                "AMOC: EML-∞",
                "Amazon dieback: EML-∞",
                "Permafrost carbon: EML-∞"
            ],
            "eml_depth": {
                "fold_bifurcation": 2,
                "critical_slowing_down": 2,
                "tipping_event": "∞",
                "pre_collapse_dynamics": 1
            },
            "key_insight": "All tipping points are EML-∞; pre-tipping critical slowing is EML-2"
        }


# ---------------------------------------------------------------------------
# 3. Milankovitch Cycles & Paleoclimate
# ---------------------------------------------------------------------------

@dataclass
class MilankovitchPaleoclimate:
    """Orbital forcing of ice ages: 23/41/100 kyr cycles."""

    eccentricity_period: float = 100.0  # kyr
    obliquity_period: float = 41.0      # kyr
    precession_period: float = 23.0     # kyr

    def orbital_forcing(self, t: float) -> float:
        """
        Total insolation forcing: sum of orbital cycles.
        F(t) = A1*cos(2πt/T1) + A2*cos(2πt/T2) + A3*cos(2πt/T3).
        EML-3 (sum of cosines).
        """
        A1, A2, A3 = 0.1, 0.4, 0.3  # relative amplitudes
        f = (A1 * math.cos(2 * math.pi * t / self.eccentricity_period) +
             A2 * math.cos(2 * math.pi * t / self.obliquity_period) +
             A3 * math.cos(2 * math.pi * t / self.precession_period))
        return f

    def ice_volume_response(self, t: float) -> float:
        """
        Ice volume responds nonlinearly to forcing (100 kyr problem).
        V(t) ~ integrate orbital_forcing with nonlinear threshold → EML-∞.
        Approximation: fast ablation, slow accumulation (sawtooth).
        """
        forcing = self.orbital_forcing(t)
        return math.tanh(3.0 * forcing)  # nonlinear response

    def carbon_cycle_forcing(self, CO2_ratio: float) -> float:
        """
        Radiative forcing: ΔF = 5.35 * ln(CO2/CO2_0). EML-2.
        """
        if CO2_ratio <= 0:
            return 0.0
        return 5.35 * math.log(CO2_ratio)

    def spectral_power(self, period: float) -> float:
        """
        Power spectrum of orbital forcing at given period. EML-3.
        """
        periods = [self.eccentricity_period, self.obliquity_period, self.precession_period]
        amps = [0.1, 0.4, 0.3]
        power = 0.0
        for T, A in zip(periods, amps):
            bandwidth = 5.0
            power += A ** 2 * math.exp(-((period - T) ** 2) / (2 * bandwidth ** 2))
        return power

    def analyze(self) -> dict[str, Any]:
        t_vals = [0, 10, 23, 41, 50, 82, 100, 123, 164, 200]
        forcing = {t: round(self.orbital_forcing(t), 4) for t in t_vals}
        ice_vol = {t: round(self.ice_volume_response(t), 4) for t in t_vals}

        co2_ratios = [0.5, 0.8, 1.0, 1.5, 2.0, 4.0]
        rf_vals = {r: round(self.carbon_cycle_forcing(r), 4) for r in co2_ratios}

        period_vals = [10, 23, 41, 65, 100, 130]
        spectrum = {p: round(self.spectral_power(p), 4) for p in period_vals}

        return {
            "model": "MilankovitchPaleoclimate",
            "orbital_periods_kyr": {
                "eccentricity": self.eccentricity_period,
                "obliquity": self.obliquity_period,
                "precession": self.precession_period
            },
            "orbital_forcing_vs_t_kyr": forcing,
            "ice_volume_response": ice_vol,
            "co2_radiative_forcing_vs_ratio": rf_vals,
            "power_spectrum": spectrum,
            "eml_depth": {
                "orbital_forcing": 3,
                "carbon_cycle_forcing": 2,
                "ice_volume_response": 3,
                "glacial_termination": "∞"
            },
            "key_insight": (
                "Orbital forcing = EML-3 (sum of cosines). "
                "CO₂ forcing = EML-2 (logarithm). "
                "Glacial terminations (100 kyr problem) = EML-∞ (nonlinear threshold)."
            )
        }


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_climate_v2_eml() -> dict[str, Any]:
    ebm = EnergyBalanceModelV2()
    tipping = ClimateTippingPoints()
    milank = MilankovitchPaleoclimate()

    return {
        "session": 137,
        "title": "Climate & Earth Systems Deep II: Feedback, Tipping Points & Paleoclimate",
        "eml_operator": "eml(x,y) = exp(x) - ln(y)",
        "energy_balance_model": ebm.analyze(),
        "climate_tipping_points": tipping.analyze(),
        "milankovitch_paleoclimate": milank.analyze(),
        "eml_depth_summary": {
            "EML-0": "Albedo fractions, deforestation ratios (pure numbers)",
            "EML-1": "Pre-tipping exponential approach (slow decay toward critical state)",
            "EML-2": "T^{1/4} equilibrium, climate sensitivity, CO₂ forcing ln(C/C₀), fold bifurcation",
            "EML-3": "Milankovitch orbital cycles (EML-3 sum of cosines), ENSO oscillations",
            "EML-∞": "Ice-albedo bifurcation, AMOC collapse, Amazon dieback, glacial terminations"
        },
        "key_theorem": (
            "The EML Climate Depth Theorem: "
            "Climate equilibria are EML-2 (energy balance = T^{1/4}, CO₂ forcing = ln(C/C₀)). "
            "Orbital forcing is EML-3 (sum of three cosines). "
            "All tipping points — ice-albedo feedback, AMOC, Amazon, permafrost — are EML-∞: "
            "they are fold bifurcations where the equilibrium curve becomes non-analytic "
            "and the system jumps irreversibly to a new state."
        ),
        "rabbit_hole_log": [
            "T_eq = (Q(1-α)/εσ)^{1/4}: fourth root = exp(ln/4) = EML-2",
            "CO₂ forcing = 5.35 ln(C/C₀): logarithm = EML-2",
            "Feedback gain G = 1/(1-f): diverges at runaway → EML-∞",
            "Orbital forcing = Σ A_i cos(2πt/T_i): sum of EML-3 terms = EML-3",
            "Tipping points = fold bifurcations = EML-∞ (same as QCD confinement, NS blowup)",
            "CO₂ forcing log structure: same class as Hawking temperature, PMI, Word2Vec"
        ],
        "connections": {
            "S57_stat_mech": "EBM equilibrium = thermodynamic equilibrium (EML-2)",
            "S62_pde": "Energy balance ODE = same class as heat equation (EML-2)",
            "S75_qft": "Tipping points = fold bifurcations = phase transitions (EML-∞)",
            "S127_climate_deep": "Extends EBM from Session 127 with full tipping point analysis"
        }
    }


if __name__ == "__main__":
    import json
    print(json.dumps(analyze_climate_v2_eml(), indent=2, default=str))
