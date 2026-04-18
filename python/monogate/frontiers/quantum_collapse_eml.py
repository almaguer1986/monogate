"""
Session 81 — Quantum Randomness: Collapse, Decoherence & Quantum Zeno

Born rule derivation, measurement-induced collapse, decoherence, quantum Zeno effect,
and their EML depth classification.

Key theorem: Decoherence maps EML-3 (quantum superposition) to EML-1 (classical mixture)
via the environment: the pointer basis eigenstates are EML-1 Boltzmann equilibria.
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass, field
from typing import Optional


EML_INF = float("inf")


@dataclass
class DensityMatrix2x2:
    """2×2 density matrix ρ = [[ρ00, ρ01],[ρ10, ρ11]]"""
    rho00: float
    rho11: float
    rho01: complex

    @property
    def rho10(self) -> complex:
        return self.rho01.conjugate()

    def purity(self) -> float:
        return abs(self.rho00 ** 2 + abs(self.rho01) ** 2 * 2 + self.rho11 ** 2)

    def entropy(self) -> float:
        # eigenvalues of 2×2: λ± = ½(1 ± √(1-4det))
        det = self.rho00 * self.rho11 - abs(self.rho01) ** 2
        disc = max(0.0, 1 - 4 * det)
        lam_plus = (1 + math.sqrt(disc)) / 2
        lam_minus = (1 - math.sqrt(disc)) / 2
        S = 0.0
        for lam in [lam_plus, lam_minus]:
            if lam > 1e-15:
                S -= lam * math.log(lam)
        return S

    def off_diagonal_magnitude(self) -> float:
        return abs(self.rho01)

    def eml_classification(self) -> str:
        if abs(self.rho01) > 1e-6:
            return "EML-3 (quantum coherence: off-diagonal = EML-3 amplitude interference)"
        return "EML-1 (classical mixture: diagonal only = Boltzmann probabilities)"


@dataclass
class Decoherence:
    """
    Decoherence: environment destroys off-diagonal elements of density matrix.

    ρ(t) = [[ρ00, ρ01·exp(-Γt)],[ρ01*·exp(-Γt), ρ11]]

    EML depth evolution:
    - t=0: ρ01 ≠ 0 → superposition → EML-3 (quantum interference)
    - t>0: ρ01 → ρ01·exp(-Γt) → off-diagonal decays exponentially (EML-1 decay)
    - t→∞: ρ → diagonal → classical mixture → EML-1 (Boltzmann)

    The EML depth of the state changes: EML-3 → EML-1 via EML-1 envelope.
    This is the EML restatement of the quantum-to-classical transition.
    """
    Gamma: float = 1.0  # decoherence rate

    def evolve(self, rho0: DensityMatrix2x2, t: float) -> DensityMatrix2x2:
        decay = math.exp(-self.Gamma * t)
        return DensityMatrix2x2(rho0.rho00, rho0.rho11, rho0.rho01 * decay)

    def eml_transition(self, rho0: DensityMatrix2x2) -> dict:
        ts = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]
        evolution = []
        for t in ts:
            rho_t = self.evolve(rho0, t)
            evolution.append({
                "t": t,
                "off_diagonal": round(rho_t.off_diagonal_magnitude(), 6),
                "entropy": round(rho_t.entropy(), 6),
                "eml_class": rho_t.eml_classification(),
            })
        return {
            "initial_state": rho0.eml_classification(),
            "decoherence_rate_Gamma": self.Gamma,
            "evolution": evolution,
            "off_diagonal_formula": "|ρ_01(t)| = |ρ_01(0)|·exp(-Γt) [EML-1 decay]",
            "eml_transition": "EML-3 (quantum coherence) → EML-1 (classical mixture) via EML-1 exponential decay",
        }


@dataclass
class QuantumZeno:
    """
    Quantum Zeno effect: frequent measurements freeze quantum evolution.

    For unitary evolution U(t) = exp(-iHt/ħ):
    - Survival probability after one measurement at time t: P(t) = |⟨ψ|U(t)|ψ⟩|² ≈ 1 - t²/τ_Z²
    - After N measurements at intervals τ = T/N: P_total = (1 - T²/N²τ_Z²)^N → 1 as N→∞

    EML depth:
    - P(t) ≈ 1 - t²/τ_Z²: EML-0 (quadratic in t)
    - P_total(N) = (1-T²/(Nτ_Z)²)^N ≈ exp(-T²/(Nτ_Z²)) → 1: EML-1 (exponential)
    - Zeno time τ_Z = ħ/ΔH where ΔH² = ⟨H²⟩-⟨H⟩²: EML-2 (standard deviation of H)

    The Zeno effect replaces EML-3 quantum evolution with EML-1 frozen state.
    """
    tau_Z: float = 1.0  # Zeno time
    T: float = 1.0      # total evolution time

    def survival_single(self, t: float) -> float:
        """P(t) ≈ 1 - (t/τ_Z)² for short t"""
        return max(0.0, 1 - (t / self.tau_Z) ** 2)

    def survival_zeno(self, N: int) -> float:
        """P_total after N measurements in time T"""
        dt = self.T / N
        p_single = self.survival_single(dt)
        return p_single ** N

    def zeno_limit(self) -> dict:
        N_values = [1, 2, 5, 10, 50, 100, 1000]
        return {
            "T": self.T,
            "tau_Z": self.tau_Z,
            "survival_vs_N": [{"N": N, "P_total": round(self.survival_zeno(N), 6)} for N in N_values],
            "limit_N_inf": 1.0,
            "eml_quantum_evolution": "EML-3 (unitary exp(-iHt/ħ) — oscillatory)",
            "eml_zeno_limit": "EML-0 (frozen state: P→1, no evolution)",
            "eml_zeno_time": "EML-2 (τ_Z = ħ/ΔH — inverse of standard deviation of H)",
        }


@dataclass
class PointerBasisEML:
    """
    Decoherence selects a preferred 'pointer basis' — the basis in which the
    density matrix becomes diagonal under environmental interaction.

    EML content:
    - Pointer basis eigenstates |n⟩: EML depends on the Hamiltonian
    - For energy eigenstates: |n⟩ = nth harmonic oscillator state → EML-3
    - Diagonal density matrix: ρ_diag = Σ p_n|n⟩⟨n| where p_n = Boltzmann = EML-1
    - Conclusion: decoherence drives quantum state to EML-1 (thermal Boltzmann mixture)
    """

    @staticmethod
    def thermal_state(beta: float, n_max: int = 10, omega: float = 1.0) -> dict:
        """Thermal density matrix for harmonic oscillator: p_n = (1-e^{-βω})e^{-nβω}"""
        Z = 1.0 / (1 - math.exp(-beta * omega))
        probs = [(1 - math.exp(-beta * omega)) * math.exp(-n * beta * omega) for n in range(n_max)]
        entropy = -sum(p * math.log(p) for p in probs if p > 1e-15)
        return {
            "beta": beta,
            "omega": omega,
            "probabilities": [round(p, 6) for p in probs],
            "partition_Z": round(Z, 6),
            "entropy": round(entropy, 6),
            "eml_depth": 1,
            "reason": "p_n = (1-e^{-βω})·e^{-nβω} = Boltzmann factor = EML-1",
        }


def analyze_quantum_collapse_eml() -> dict:
    rho_pure = DensityMatrix2x2(0.5, 0.5, complex(0.5, 0))
    rho_mixed = DensityMatrix2x2(0.5, 0.5, complex(0, 0))
    dec = Decoherence(Gamma=1.0)
    zeno = QuantumZeno(tau_Z=1.0, T=2.0)
    pointer = PointerBasisEML()
    return {
        "session": 81,
        "title": "Quantum Randomness: Collapse, Decoherence & Quantum Zeno",
        "key_theorem": {
            "theorem": "Decoherence = EML-3 → EML-1 Transition",
            "statement": (
                "Decoherence maps quantum superposition (EML-3: off-diagonal ρ_01 = EML-3 amplitude) "
                "to classical mixture (EML-1: diagonal ρ = Boltzmann distribution). "
                "The off-diagonal decay ρ_01(t) = ρ_01(0)·exp(-Γt) is EML-1. "
                "The pointer basis thermal state is EML-1. "
                "Thus the quantum-to-classical transition is an EML-3 → EML-1 collapse."
            ),
        },
        "density_matrices": {
            "pure_superposition": {"rho01": str(rho_pure.rho01), "eml": rho_pure.eml_classification(), "entropy": round(rho_pure.entropy(), 6)},
            "mixed_classical": {"rho01": str(rho_mixed.rho01), "eml": rho_mixed.eml_classification(), "entropy": round(rho_mixed.entropy(), 6)},
        },
        "decoherence": dec.eml_transition(rho_pure),
        "quantum_zeno": zeno.zeno_limit(),
        "pointer_basis": {
            "thermal_state_beta1": pointer.thermal_state(1.0),
            "thermal_state_beta5": pointer.thermal_state(5.0),
            "eml_pointer": "Pointer basis = energy eigenstates; diagonal thermal ρ = EML-1 (Boltzmann)",
        },
        "eml_depth_summary": {
            "EML-0": "Zeno-frozen state (P→1); discrete measurement outcomes ±1",
            "EML-1": "Classical thermal mixture (Boltzmann); off-diagonal decay exp(-Γt); coherent state",
            "EML-2": "Born rule P=|c|²; decoherence time τ_Z = ħ/ΔH; quantum entropy S=-Trρlogρ",
            "EML-3": "Quantum superposition ρ_01≠0; unitary evolution exp(-iHt); interference fringes",
            "EML-∞": "Individual measurement outcomes (no hidden variable by Bell)",
        },
        "connections": {
            "to_session_70": "Session 70: Born rule EML-2, Bell EML-∞. Session 81: adds decoherence + Zeno dynamics",
            "to_session_57": "Decoherence → Boltzmann = EML-1; same as stat mech equilibration",
            "to_session_64": "Quantum Zeno: measurement as stochastic process → Feynman-Kac style",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_quantum_collapse_eml(), indent=2, default=str))
