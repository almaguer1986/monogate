"""
Session 128 — Materials Science Deep: Many-Body Systems, Superconductivity & Topological Phases

Hubbard model, BCS gap equation, Bogoliubov transformation, topological band theory,
Chern numbers, quantum Hall effect, and topological insulators classified by EML depth.

Key theorem: Hubbard model Hamiltonian is EML-2 (bilinear + quadratic hopping terms).
BCS gap Δ=2ħωD·exp(-1/N₀V) is EML-1 (exponential of inverse coupling = Boltzmann-like).
Bogoliubov transformation is EML-2 (rotation in Nambu space). Chern number C = EML-0
(topological integer invariant). Quantum Hall conductance σ_xy = Ce²/h is EML-0 × EML-0.
Topological surface states are EML-3 (Dirac cone = linear dispersion with spin-orbit).
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass

EML_INF = float("inf")


@dataclass
class ManyBodySystems:
    """
    Hubbard model and strongly correlated electrons.

    EML structure:
    - Hopping term: -t·Σ c†_i c_j: EML-2 (bilinear in fermionic operators)
    - On-site repulsion: U·Σ n_↑ n_↓: EML-2 (quadratic in density operators)
    - Half-filled U≫t: Mott insulator (charge gap Δ~U): EML-0 (gap = integer × U)
    - U≪t: metallic band (Fermi energy = EML-2 via √ of hopping bandwidth)
    - Mott transition at U_c/t ~ 6: EML-∞ (metal-insulator phase transition)
    - Heisenberg exchange: J = 4t²/U: EML-2 (quadratic in t / linear in U)
    - Néel temperature T_N ~ J/k_B: EML-2 (exchange energy scale)
    """

    def hubbard_bandwidth(self, t: float, d: int = 3) -> dict:
        """Half-bandwidth W = 2d·t (d-dimensional hypercubic lattice)."""
        W = 2 * d * t
        return {
            "t_hopping": t,
            "dimension": d,
            "half_bandwidth_W": W,
            "eml": 2,
            "reason": "W=2dt: linear in t (EML-2 for band energy via √(t) at band edges).",
        }

    def heisenberg_exchange(self, t: float, U: float) -> dict:
        """J = 4t²/U: superexchange coupling."""
        J = 4 * t**2 / U
        return {
            "t": t, "U": U,
            "J": round(J, 6),
            "eml": 2,
            "reason": "J=4t²/U: quadratic in t, linear in 1/U = EML-2.",
        }

    def mott_transition(self, U_over_t: float, U_c_over_t: float = 6.0) -> dict:
        """Mott metal-insulator transition at U_c/t ≈ 6."""
        if U_over_t < U_c_over_t:
            phase = "metallic (Fermi liquid)"
            eml = 2
        elif abs(U_over_t - U_c_over_t) < 0.5:
            phase = "Mott transition (quantum critical)"
            eml = EML_INF
        else:
            phase = "Mott insulator (charge gap ~ U)"
            eml = 0
        return {
            "U_over_t": U_over_t,
            "U_c_over_t": U_c_over_t,
            "phase": phase,
            "eml": "∞" if eml == EML_INF else eml,
        }

    def to_dict(self) -> dict:
        return {
            "bandwidth": [self.hubbard_bandwidth(t) for t in [0.1, 0.5, 1.0]],
            "exchange": [self.heisenberg_exchange(t, U) for t, U in [(0.5, 4.0), (1.0, 8.0)]],
            "mott_transition": [self.mott_transition(U_t) for U_t in [2, 4, 5.5, 6.0, 7, 10]],
            "eml_hopping": 2,
            "eml_exchange": 2,
            "eml_mott": "∞",
        }


@dataclass
class Superconductivity:
    """
    BCS theory and Bogoliubov transformation.

    EML structure:
    - BCS gap equation: 1 = N₀V·∫dξ/√(ξ²+Δ²)·tanh(√(ξ²+Δ²)/2kT): EML-3
    - Gap solution at T=0: Δ = 2ħωD·exp(-1/N₀V): EML-1 (Boltzmann-like essential singularity)
    - Tc: kT_c = 1.13·ħωD·exp(-1/N₀V): EML-1 (same Boltzmann structure)
    - Coherence length: ξ₀ = ħv_F/πΔ: EML-2 (ratio of energy scales)
    - London penetration depth: λ_L = √(m/μ₀ne²): EML-2 (square root = EML-2)
    - Bogoliubov quasiparticle: E_k = √(ξ_k²+Δ²): EML-2 (Pythagorean energy)
    - Josephson: I = I_c·sin(φ): EML-3 (same as materials session)
    """

    def bcs_gap(self, N0_V: float, omega_D: float = 1.0) -> dict:
        """Δ = 2ħωD·exp(-1/N₀V): BCS gap (essential singularity in coupling)."""
        Delta = 2 * omega_D * math.exp(-1.0 / N0_V)
        return {
            "N0_V_dimensionless": N0_V,
            "omega_D": omega_D,
            "Delta": round(Delta, 6),
            "eml": 1,
            "reason": "Δ=2ħωD·exp(-1/N₀V): exponential of inverse coupling = EML-1 (essential singularity → Boltzmann).",
        }

    def bogoliubov_energy(self, xi: float, Delta: float) -> dict:
        """E_k = √(ξ_k² + Δ²): Bogoliubov quasiparticle energy."""
        E = math.sqrt(xi**2 + Delta**2)
        return {
            "xi_kinetic": xi,
            "Delta_gap": Delta,
            "E_quasiparticle": round(E, 4),
            "eml": 2,
            "reason": "E=√(ξ²+Δ²): Pythagorean = EML-2 (square root of sum of squares).",
        }

    def coherence_length(self, v_F: float, Delta: float) -> dict:
        """ξ₀ = ħv_F/πΔ: BCS coherence length."""
        xi_0 = v_F / (math.pi * Delta)
        return {
            "v_F": v_F, "Delta": Delta,
            "xi_0": round(xi_0, 4),
            "eml": 2,
            "reason": "ξ₀=ħv_F/πΔ: ratio of velocities and energies = EML-2.",
        }

    def to_dict(self) -> dict:
        return {
            "bcs_gap": [self.bcs_gap(N0V) for N0V in [0.1, 0.2, 0.3, 0.5]],
            "bogoliubov": [self.bogoliubov_energy(xi, 0.1) for xi in [-0.5, -0.1, 0.0, 0.1, 0.5]],
            "coherence_length": [self.coherence_length(vF, Delta)
                                  for vF, Delta in [(1.0, 0.1), (2.0, 0.05)]],
            "eml_bcs_gap": 1,
            "eml_bogoliubov_energy": 2,
            "eml_josephson": 3,
        }


@dataclass
class TopologicalPhases:
    """
    Topological band theory and quantum Hall effect.

    EML structure:
    - Chern number: C = (1/2π)∫∫BZ F_{xy} dk_x dk_y: EML-0 (integer topological invariant)
    - Berry curvature: F = ∇_k × A = Im⟨∂_ky u|∂_kx u⟩ - (kx↔ky): EML-3 (gradient of phase)
    - Hall conductance σ_xy = Ce²/h: EML-0 (integer × constants)
    - Topological surface states: E = ±v_F|k| (Dirac cone): EML-2 (linear dispersion = EML-2)
    - Spin-orbit coupling: H_SOC = α·(k × σ)·ẑ: EML-3 (cross product of k and Pauli = EML-3)
    - Topological protection: gap Δ_surface = 0 (gapless): EML-0 (zero = EML-0)
    - Bulk-boundary correspondence: EML-0 (topological = discrete counting)
    """

    def chern_number_eml(self) -> dict:
        """Chern number C is a topological integer invariant."""
        return {
            "C": "integer ∈ ℤ",
            "eml": 0,
            "reason": "Chern number = integer topological invariant (same as Euler characteristic, S58) = EML-0.",
            "examples": {
                "trivial_insulator": "C=0",
                "QAH": "C=±1",
                "IQHE_LL_n": "C=n",
            },
        }

    def dirac_cone_dispersion(self, kx: float, ky: float,
                               v_F: float = 1.0) -> dict:
        """E = ±v_F|k|: Dirac cone surface states."""
        k_mag = math.sqrt(kx**2 + ky**2)
        E_plus = v_F * k_mag
        E_minus = -v_F * k_mag
        return {
            "kx": kx, "ky": ky,
            "k_magnitude": round(k_mag, 4),
            "E_plus": round(E_plus, 4),
            "E_minus": round(E_minus, 4),
            "eml": 2,
            "reason": "E=±v_F√(kx²+ky²): square root of sum of squares = EML-2 (Pythagorean momentum).",
        }

    def quantum_hall_conductance(self, C: int) -> dict:
        """σ_xy = C·e²/h."""
        sigma_SI = C * (1.602e-19)**2 / (6.626e-34)
        return {
            "C_chern": C,
            "sigma_xy_SI": round(sigma_SI, 2),
            "sigma_xy_units": "e²/h",
            "eml": 0,
            "reason": "σ_xy=Ce²/h: integer × fundamental constants = EML-0 (topological quantization).",
        }

    def z2_topological_invariant(self) -> dict:
        """Z₂ invariant ν for time-reversal invariant topological insulators."""
        return {
            "invariant": "Z₂ ν ∈ {0,1}",
            "eml": 0,
            "reason": "Z₂ ∈ {0,1}: binary topological invariant = EML-0.",
            "examples": {
                "trivial_insulator": "ν=0",
                "topological_insulator": "ν=1 (e.g. Bi₂Se₃)",
            },
            "bulk_boundary": "ν=1 → odd number of Dirac cones on surface (gapless = topologically protected)",
        }

    def to_dict(self) -> dict:
        k_pts = [(0, 0), (0.5, 0), (0.3, 0.4), (0, 1.0)]
        return {
            "chern_number": self.chern_number_eml(),
            "dirac_cone": [self.dirac_cone_dispersion(kx, ky) for kx, ky in k_pts],
            "hall_conductance": [self.quantum_hall_conductance(C) for C in [0, 1, 2, -1]],
            "z2_invariant": self.z2_topological_invariant(),
            "eml_chern_number": 0,
            "eml_z2": 0,
            "eml_dirac_cone": 2,
            "eml_berry_curvature": 3,
            "eml_spin_orbit": 3,
            "eml_hall_conductance": 0,
        }


def analyze_materials_deep_eml() -> dict:
    mb = ManyBodySystems()
    sc = Superconductivity()
    tp = TopologicalPhases()
    return {
        "session": 128,
        "title": "Materials Science Deep: Many-Body Systems, Superconductivity & Topological Phases",
        "key_theorem": {
            "theorem": "EML Topology-Dynamics Theorem for Materials",
            "statement": (
                "Chern number C is EML-0 (topological integer). "
                "Hall conductance σ_xy=Ce²/h is EML-0. "
                "Z₂ topological invariant is EML-0. "
                "BCS gap Δ=2ħωD·exp(-1/N₀V) is EML-1 (Boltzmann-like essential singularity). "
                "Bogoliubov energy E_k=√(ξ_k²+Δ²) is EML-2. "
                "Dirac cone E=v_F|k| is EML-2. "
                "Berry curvature F=Im⟨∂_ky u|∂_kx u⟩ is EML-3. "
                "Mott metal-insulator transition is EML-∞. "
                "All topological invariants are EML-0 (integers)."
            ),
        },
        "many_body": mb.to_dict(),
        "superconductivity": sc.to_dict(),
        "topological_phases": tp.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Chern number C; Z₂ invariant; Hall conductance Ce²/h; bulk-boundary correspondence; Mott gap integer",
            "EML-1": "BCS gap exp(-1/N₀V); T_c exp(-1/N₀V); Cooper pair condensate amplitude",
            "EML-2": "Bogoliubov E=√(ξ²+Δ²); Dirac cone |k|; Heisenberg J=4t²/U; London penetration √(m/μ₀ne²)",
            "EML-3": "Berry curvature (gradient of Bloch phase); spin-orbit coupling k×σ; Josephson sin(φ)",
            "EML-∞": "Mott metal-insulator transition (U/t~6); superconductor-normal phase boundary; Anderson localization",
        },
        "rabbit_hole_log": [
            "The EML depth of topological phases is EML-0: ALL topological invariants (Chern number C, Z₂ invariant ν, winding number, TKNN integer) are integers. This is the deepest manifestation of the EML-0 = topology principle (S58): algebraic topology invariants are EML-0 (integers, S58), Chern-Weil map collapses EML-2 curvature to EML-0 integers (S58), and topological materials are engineered systems where this EML-0 structure is physically observable as quantized Hall conductance σ_xy = Ce²/h. Topology protects properties — integers are the most robust numbers.",
            "The BCS gap Δ=2ħωD·exp(-1/N₀V) is EML-1: an essential singularity at N₀V=0 (no BCS gap for infinitesimally weak attractive interaction in 1D). This is the SAME exponential structure as the Boltzmann factor exp(-E/kT), the Planck black hole temperature 1/8πM, and the cosmological inflation potential Λ⁴exp(-φ/f). EML-1 is the universal depth of all ground states — BCS superconductivity rediscovers the same Boltzmann ground state structure that thermodynamics, quantum field theory, and cosmology all use.",
            "The Dirac cone E=v_F|k| is EML-2 (square root = EML-2), but the topological protection of the Dirac cone is EML-0 (the Z₂ invariant ν=1 guarantees gapless surface states). This is the deepest EML structure of topological insulators: the surface states are EML-2 in their dynamics but EML-0 in their topological protection. You cannot gap out a topologically protected Dirac cone without a phase transition (EML-∞) — the topological invariant prevents it.",
        ],
        "connections": {
            "to_session_108": "S108 covered BCS/phonons/Mott overview. S128 adds Hubbard model (EML-2), Bogoliubov transformation (EML-2), topological phases (EML-0 Chern numbers).",
            "to_session_58": "Chern numbers (EML-0) = topological invariants (S58). Same EML-0 collapse via Chern-Weil map.",
            "to_session_57": "Mott transition (EML-∞) = statistical mechanics phase transition (EML-∞). Same universality class.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_materials_deep_eml(), indent=2, default=str))
