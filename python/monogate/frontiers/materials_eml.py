"""
Session 108 — Materials Science & Condensed Matter: EML in Matter

Band structure, phonons, superconductivity, density functional theory, and
materials phase transitions classified by EML depth.

Key theorem: Band gap is EML-2 (from Schrödinger = EML-3, but gap = rational
in k is EML-2). Phonon dispersion ω(k) is EML-3 (oscillatory in k). BCS
superconducting gap Δ = 2ħω_D·exp(-1/(N(0)V)): EML-1 (exp of rational).
DFT exchange-correlation: EML-2 (LDA) to EML-∞ (exact XC). Mott insulator
transition is EML-∞.
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass, field


EML_INF = float("inf")


@dataclass
class BandStructure:
    """
    Electronic band structure: Bloch's theorem, dispersion relations.

    EML structure:
    - Bloch state: ψ_k(r) = e^{ik·r}·u_k(r): EML-1 per k (exp factor) × periodic u_k
    - Free electron: E(k) = ħ²k²/(2m): EML-2 (quadratic in k = power law)
    - Nearly-free electron: gaps at BZ boundary: E_± = E₀ ± |V_G|: EML-2 (splitting)
    - Band gap: E_g = 2|V_G|: EML-0 (constant given crystal potential)
    - Effective mass: m* = ħ²/(d²E/dk²): EML-2 (inverse curvature = EML-2)
    - Fermi-Dirac: f(E) = 1/(exp((E-E_F)/kT)+1): EML-1 (Fermi function)
    - DOS: g(E) = (V/2π²)(2m/ħ²)^{3/2}·√E: EML-2 (√E = power law)
    """

    def free_electron_dispersion(self, k: float, mass_ratio: float = 1.0) -> dict:
        """E(k) = ħ²k²/(2m*) in eV·Å² units (ħ²/2m = 3.81 eV·Å²)."""
        hbar2_2m = 3.81 * mass_ratio
        E = hbar2_2m * k ** 2
        return {
            "k_invA": k,
            "mass_ratio_m_over_me": mass_ratio,
            "E_eV": round(E, 4),
            "eml": 2,
            "reason": "E(k) = ħ²k²/2m: EML-2 (quadratic in k = power law)",
        }

    def fermi_dirac(self, E: float, E_F: float = 0.0, T_K: float = 300.0) -> dict:
        """f(E) = 1/(exp((E-E_F)/kT) + 1)."""
        kT = 8.617e-5 * T_K
        x = (E - E_F) / kT
        if x > 500:
            f = 0.0
        elif x < -500:
            f = 1.0
        else:
            f = 1.0 / (math.exp(x) + 1)
        return {
            "E_eV": E, "E_F_eV": E_F, "T_K": T_K,
            "f": round(f, 6),
            "eml": 1,
            "reason": "f = 1/(exp((E-E_F)/kT)+1): EML-1 (Fermi function = logistic = EML-1 sigmoid)",
        }

    def density_of_states_3d(self, E: float) -> dict:
        """Free electron DOS: g(E) ~ √E (3D)."""
        if E <= 0:
            return {"E_eV": E, "g_rel": 0.0, "eml": 2}
        g = math.sqrt(E)
        return {
            "E_eV": E,
            "g_relative": round(g, 4),
            "eml": 2,
            "reason": "g(E) ~ √E = E^{1/2}: EML-2 (power law in energy)",
        }

    def to_dict(self) -> dict:
        k_vals = [0.0, 0.5, 1.0, 1.5, 2.0]
        E_vals = [-0.5, -0.1, 0.0, 0.1, 0.5]
        return {
            "free_electron": [self.free_electron_dispersion(k) for k in k_vals],
            "fermi_dirac_300K": [self.fermi_dirac(E) for E in E_vals],
            "fermi_dirac_1000K": [self.fermi_dirac(E, T_K=1000) for E in E_vals],
            "dos_3d": [self.density_of_states_3d(E) for E in [0.1, 0.5, 1.0, 2.0, 4.0]],
            "eml_bloch_state": 1,
            "eml_dispersion": 2,
            "eml_fermi_dirac": 1,
            "eml_dos_3d": 2,
            "band_gap_eml": 2,
        }


@dataclass
class PhononDispersion:
    """
    Lattice vibrations: phonon dispersion ω(k) for 1D diatomic chain.

    EML structure:
    - Monoatomic chain: ω(k) = 2√(K/M)·|sin(ka/2)|: EML-3 (sin of k = oscillatory)
    - Diatomic chain: ω±(k) = √((K/μ) ± √((K/μ)² - 4K²sin²(ka/2)/mM)): EML-3
    - Debye model: ω ~ v_s·k (linear): EML-2 (power law k^1)
    - Einstein model: ω = const: EML-0 (discrete frequency)
    - Thermal energy: U = ∫ħω·n_BE(ω)·g(ω)dω: EML-3 (oscillatory integral)
    - Bose-Einstein: n_BE = 1/(exp(ħω/kT)-1): EML-1 (Boltzmann denom)
    - Debye T³ law: C_v ~ (T/T_D)³ at low T: EML-2 (power law in T)
    """

    def monoatomic_dispersion(self, k: float, K: float = 1.0,
                               M: float = 1.0, a: float = 1.0) -> dict:
        omega = 2 * math.sqrt(K / M) * abs(math.sin(k * a / 2))
        return {
            "k": round(k, 4),
            "omega": round(omega, 6),
            "eml": 3,
            "reason": "ω(k) = 2√(K/M)|sin(ka/2)|: EML-3 (sin function of wavevector k)",
        }

    def bose_einstein_occupation(self, omega: float, T_K: float) -> dict:
        """n_BE = 1/(exp(ħω/kT) - 1). Use ħω/kT directly as dimensionless."""
        x = omega / T_K if T_K > 0 else float("inf")
        if x > 500:
            n = 0.0
        elif x < 0.001:
            n = T_K / omega
        else:
            n = 1.0 / (math.exp(x) - 1)
        return {
            "hbar_omega_over_kT": round(x, 4),
            "n_BE": round(n, 4),
            "eml": 1,
            "reason": "n_BE = 1/(e^{ħω/kT}-1): EML-1 (exp in denominator = Boltzmann form)",
        }

    def debye_heat_capacity(self, T_over_TD: float) -> dict:
        """Debye C_v ~ 12π⁴R/5·(T/T_D)³ at low T."""
        if T_over_TD < 0.1:
            C_v = 12 * math.pi**4 / 5 * T_over_TD**3
            regime = "low-T (Debye T³)"
            eml = 2
        else:
            C_v = 3.0 * (1 - 0.05 / T_over_TD)
            regime = "high-T (Dulong-Petit)"
            eml = 0
        return {
            "T_over_T_D": T_over_TD,
            "C_v_over_R": round(C_v, 4),
            "regime": regime,
            "eml": eml,
            "reason_low": "C_v ~ (T/T_D)³: EML-2 (cubic power law at low T)",
            "reason_high": "C_v = 3R (classical): EML-0 (constant at high T)",
        }

    def to_dict(self) -> dict:
        k_vals = [0.0, 0.25, 0.5, 0.75, 1.0, math.pi]
        return {
            "monoatomic_chain": [self.monoatomic_dispersion(k) for k in k_vals],
            "bose_einstein": [self.bose_einstein_occupation(1.0, T) for T in [0.1, 0.5, 1.0, 2.0, 5.0]],
            "debye_Cv": [self.debye_heat_capacity(t) for t in [0.01, 0.05, 0.1, 0.5, 1.0, 2.0]],
            "eml_phonon": 3,
            "eml_debye_lowT": 2,
            "eml_einstein": 0,
            "eml_BE": 1,
        }


@dataclass
class Superconductivity:
    """
    BCS superconductivity: Cooper pairs, gap equation, Meissner effect.

    EML structure:
    - BCS gap: Δ ≈ 2ħω_D·exp(-1/(N(0)V)): EML-1 (pure exponential of rational)
    - T_c = 1.13·ħω_D·exp(-1/(N(0)V)) / k_B: EML-1
    - Gap/T_c ratio: 2Δ/k_BT_c = 3.528 (universal): EML-0 (universal constant)
    - Condensation energy: E_cond ~ N(0)Δ²/2: EML-2 (gap squared × DOS)
    - London penetration depth: λ_L = √(mc²/(4πne²)): EML-2 (rational power)
    - Ginzburg-Landau: |ψ|² = n_s, F = α|ψ|² + β|ψ|⁴ + ...: EML-2 (GL free energy)
    - Josephson junction: I = I_c·sin(φ): EML-3 (current is sin of phase difference)
    - Vortex lattice (Abrikosov): B field periodic → EML-3 (periodic structure)
    """

    def bcs_gap(self, omega_D: float, N0V: float) -> dict:
        """Δ ≈ 2ħω_D·exp(-1/(N(0)V)) in units where ħω_D = omega_D."""
        Delta = 2 * omega_D * math.exp(-1.0 / N0V)
        T_c = Delta / (2 * 1.764)
        return {
            "omega_D": omega_D,
            "N0V": N0V,
            "Delta": round(Delta, 6),
            "T_c_ratio": round(T_c / omega_D, 6),
            "gap_ratio_2D_kTc": 3.528,
            "eml_gap": 1,
            "eml_gap_ratio": 0,
            "reason": "Δ = 2ħω_D·exp(-1/N(0)V): EML-1 (exponential of rational parameter)",
        }

    def josephson_current(self, phi: float, Ic: float = 1.0) -> dict:
        """DC Josephson: I = Ic·sin(φ)."""
        I = Ic * math.sin(phi)
        return {
            "phi_rad": round(phi, 4),
            "I_over_Ic": round(I, 6),
            "eml": 3,
            "reason": "I = I_c·sin(φ): EML-3 (sine of phase = oscillatory)",
        }

    def gl_free_energy(self, psi: float, alpha: float = -1.0,
                        beta: float = 0.5) -> dict:
        """GL: F(|ψ|²) = α|ψ|² + β|ψ|⁴/2."""
        F = alpha * psi ** 2 + beta * psi ** 4 / 2
        psi_eq = math.sqrt(-alpha / beta) if alpha < 0 and beta > 0 else 0.0
        return {
            "psi": psi,
            "F": round(F, 6),
            "psi_eq": round(psi_eq, 4),
            "eml": 2,
            "reason": "GL: F = α|ψ|² + β|ψ|⁴: EML-2 (polynomial in |ψ|²)",
        }

    def to_dict(self) -> dict:
        return {
            "bcs_gap": [self.bcs_gap(1.0, N0V) for N0V in [0.2, 0.3, 0.5, 1.0]],
            "josephson": [self.josephson_current(phi) for phi in
                          [0, math.pi/6, math.pi/4, math.pi/2, math.pi]],
            "gl_energy": [self.gl_free_energy(psi) for psi in [0.0, 0.5, 1.0, 1.414, 2.0]],
            "eml_BCS_gap": 1,
            "eml_Tc": 1,
            "eml_gap_ratio": 0,
            "eml_josephson": 3,
            "eml_GL": 2,
            "mott_transition": {"eml": EML_INF,
                                "reason": "Mott insulator-metal transition = EML-∞ (strong correlations, no perturbative description)"},
        }


def analyze_materials_eml() -> dict:
    bands = BandStructure()
    phonons = PhononDispersion()
    sc = Superconductivity()
    return {
        "session": 108,
        "title": "Materials Science & Condensed Matter: EML in Matter",
        "key_theorem": {
            "theorem": "EML Materials Depth Theorem",
            "statement": (
                "Free electron dispersion E(k) = ħ²k²/2m is EML-2 (quadratic = power law). "
                "Fermi-Dirac distribution is EML-1 (logistic function = EML-1 sigmoid). "
                "Phonon dispersion ω(k) = 2√(K/M)|sin(ka/2)| is EML-3 (oscillatory in k). "
                "Debye low-T heat capacity C_v ~ (T/T_D)³ is EML-2. "
                "Bose-Einstein occupation n_BE = 1/(e^{ħω/kT}-1) is EML-1. "
                "BCS gap Δ = 2ħω_D·exp(-1/N(0)V) is EML-1 (exponential of rational). "
                "Josephson current I = I_c·sin(φ) is EML-3. "
                "Ginzburg-Landau free energy is EML-2. "
                "Mott insulator transition is EML-∞ (strong correlations)."
            ),
        },
        "band_structure": bands.to_dict(),
        "phonon_dispersion": phonons.to_dict(),
        "superconductivity": sc.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Band gap 2|V_G| (constant); Einstein phonon (fixed frequency); universal BCS ratio 2Δ/kT_c=3.528",
            "EML-1": "Fermi-Dirac f(E); Bose-Einstein n_BE; BCS gap Δ (exp of coupling); T_c (same form as Δ)",
            "EML-2": "Free electron E(k)~k²; DOS ~√E; London penetration depth; GL free energy; Debye T³ law",
            "EML-3": "Phonon dispersion ω(k)~sin(ka); Josephson current I_c·sin(φ); Abrikosov vortex lattice",
            "EML-∞": "Mott insulator transition; heavy fermion systems; high-T_c (d-wave pairing symmetry unknown origin)",
        },
        "rabbit_hole_log": [
            "BCS gap is EML-1 by the same mechanism as Boltzmann: Δ = 2ħω_D·exp(-1/N(0)V). The argument -1/N(0)V of the exponential is negative-rational (a ratio of coupling constant to density of states). This is the exact same EML-1 structure as the Boltzmann weight exp(-E/kT), with 1/N(0)V playing the role of energy/temperature.",
            "Phonon dispersion is EML-3 for the same reason as quantum harmonic oscillator wavefunctions: both involve sin(ka), the projection of circular motion onto a line. The phonon is literally a quantized sin wave in the lattice — EML-3 is the fundamental depth of oscillatory collective modes.",
            "The Josephson junction is EML-3: I = I_c·sin(φ). This is the fundamental quantum interference of superconducting order parameters. The sin(φ) structure means the Josephson junction is in the EML-3 class along with all quantum coherence phenomena.",
            "Mott transition is EML-∞ because it requires resummation of all perturbative orders: no finite EML tree can describe the strongly-correlated electron state. This is the condensed matter analog of QCD confinement (Session 98): strong coupling → EML-∞. Both represent breakdowns of the EML-2 perturbative regime.",
        ],
        "connections": {
            "to_session_57": "Ising = EML-∞ phase transition. Mott transition = EML-∞ same universality class.",
            "to_session_61": "Harmonic oscillator = EML-3. Phonons = quantized oscillators = EML-3. Same mathematics.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_materials_eml(), indent=2, default=str))
