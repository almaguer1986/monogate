"""
quantum.py -- Matrix EML gates for quantum thermodynamics.

Quantum thermodynamics is EML arithmetic on density matrices:
  - Von Neumann entropy:   S(rho) = -Tr(rho ln rho) = Tr(meml(0, rho))
  - Partition function:    Z(beta, H) = Tr(exp(-beta*H)) = Tr(mdeml(beta*H, I))
  - Quantum free energy:   F = -kT ln(Z)
  - Mutual information:    I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)

API:
  meml(A, B)               -- matrix EML: expm(A) - logm(B)
  mdeml(A, B)              -- matrix DEML: expm(-A) - logm(B)
  von_neumann_entropy(rho) -- -Tr(rho ln rho)
  partition_function(H, beta) -- Tr(expm(-beta*H))
  quantum_free_energy(H, beta, kT=1.0) -- -kT * ln(Z)
  quantum_mutual_info(rho_AB, dim_A, dim_B) -- I(A:B)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import scipy.linalg

if TYPE_CHECKING:
    pass

# ── Matrix EML gates ──────────────────────────────────────────────────────────

def meml(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Matrix EML gate: expm(A) - logm(B).

    Requires B to be positive-definite (logm well-defined).
    """
    return scipy.linalg.expm(A) - scipy.linalg.logm(B)


def mdeml(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Matrix DEML gate: expm(-A) - logm(B).

    Partition function: Tr(mdeml(beta*H, I)) = Tr(expm(-beta*H)) = Z(beta).
    """
    return scipy.linalg.expm(-A) - scipy.linalg.logm(B)


def mexl(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Matrix EXL gate: expm(A) @ logm(B)  (matrix product)."""
    return scipy.linalg.expm(A) @ scipy.linalg.logm(B)


# ── Quantum thermodynamic quantities ─────────────────────────────────────────

def von_neumann_entropy(rho: np.ndarray, eps: float = 1e-12) -> float:
    """
    Von Neumann entropy: S(rho) = -Tr(rho ln rho).

    Note: S(rho) = Tr(meml(0, rho)) when Tr(rho) = 1 (since expm(0) = I,
    and -Tr(rho ln rho) = -Tr(rho logm(rho)) = Tr(I - rho logm(rho)) - Tr(I)
    ... simplified: this uses the eigenvalue decomposition directly.
    """
    rho = np.asarray(rho, dtype=complex)
    eigenvalues = np.real(np.linalg.eigvalsh(rho))
    eigenvalues = eigenvalues[eigenvalues > eps]
    return float(-np.sum(eigenvalues * np.log(eigenvalues)))


def von_neumann_entropy_meml(rho: np.ndarray) -> float:
    """
    Von Neumann entropy via matrix EML identity.

    meml(0, rho) = I - logm(rho)
    => logm(rho) = I - meml(0, rho)
    => S(rho) = -Tr(rho * logm(rho))
             = -Tr(rho * (I - meml(0, rho)))
             = -Tr(rho) + Tr(rho * meml(0, rho))
             = Tr(rho * meml(0, rho)) - 1   [since Tr(rho)=1]
    """
    n = rho.shape[0]
    Z = np.zeros((n, n), dtype=complex)
    result = meml(Z, rho)  # I - logm(rho)
    return float(np.real(np.trace(rho @ result))) - 1.0


def partition_function(H: np.ndarray, beta: float) -> float:
    """
    Quantum partition function: Z = Tr(expm(-beta*H)).

    EML identity: Z = Tr(mdeml(beta*H, I)).
    This is a 1-node DEML expression in matrix EML arithmetic.
    """
    n = H.shape[0]
    I = np.eye(n, dtype=complex)
    # mdeml(beta*H, I) = expm(-beta*H) - logm(I) = expm(-beta*H) - 0
    return float(np.real(np.trace(mdeml(beta * H, I))))


def quantum_free_energy(H: np.ndarray, beta: float, kT: float | None = None) -> float:
    """
    Quantum free energy: F = -kT * ln(Z) = -kT * ln(Tr(expm(-beta*H))).

    If kT is None, uses kT = 1/beta.
    """
    if kT is None:
        kT = 1.0 / beta if beta != 0 else 1.0
    Z = partition_function(H, beta)
    if Z <= 0:
        return float("nan")
    return float(-kT * math.log(Z))


def thermal_state(H: np.ndarray, beta: float) -> np.ndarray:
    """
    Gibbs thermal state: rho(beta) = expm(-beta*H) / Z.

    The canonical state at inverse temperature beta.
    """
    n = H.shape[0]
    rho_unnorm = scipy.linalg.expm(-beta * np.asarray(H, dtype=complex))
    Z = np.real(np.trace(rho_unnorm))
    return rho_unnorm / Z


def quantum_mutual_info(rho_AB: np.ndarray, dim_A: int, dim_B: int) -> float:
    """
    Quantum mutual information: I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB).

    rho_AB is a density matrix on system AB.
    dim_A and dim_B are dimensions of subsystems A and B.
    """
    assert dim_A * dim_B == rho_AB.shape[0], "dim_A * dim_B must equal rho_AB dimension"
    rho_A = partial_trace(rho_AB, dim_A, dim_B, trace_out="B")
    rho_B = partial_trace(rho_AB, dim_A, dim_B, trace_out="A")
    return von_neumann_entropy(rho_A) + von_neumann_entropy(rho_B) - von_neumann_entropy(rho_AB)


def partial_trace(rho: np.ndarray, dim_A: int, dim_B: int,
                  trace_out: str = "B") -> np.ndarray:
    """
    Partial trace of a bipartite density matrix.

    trace_out="B": return rho_A = Tr_B(rho_AB)
    trace_out="A": return rho_B = Tr_A(rho_AB)
    """
    rho = np.asarray(rho, dtype=complex)
    rho_reshaped = rho.reshape(dim_A, dim_B, dim_A, dim_B)
    if trace_out == "B":
        return np.trace(rho_reshaped, axis1=1, axis2=3)
    else:
        return np.trace(rho_reshaped, axis1=0, axis2=2)


# ── EML identities for quantum systems ───────────────────────────────────────

def eml_identity_check(rho: np.ndarray, eps: float = 1e-8) -> dict:
    """
    Verify the core EML identities for a density matrix rho.

    Returns dict with verification results:
    - von_neumann_via_meml: S(rho) computed via meml vs eigenvalue method
    - partition_via_mdeml: Z(1, H_eff) for effective Hamiltonian
    """
    n = rho.shape[0]
    s_eigen = von_neumann_entropy(rho)
    s_meml = von_neumann_entropy_meml(rho)

    return {
        "entropy_eigenvalue": s_eigen,
        "entropy_meml": s_meml,
        "entropy_match": abs(s_eigen - s_meml) < eps,
        "entropy_error": abs(s_eigen - s_meml),
    }


# ── Standard test systems ─────────────────────────────────────────────────────

def two_level_hamiltonian(omega: float = 1.0) -> np.ndarray:
    """Two-level system Hamiltonian: H = omega/2 * sigma_z."""
    return np.array([[omega / 2, 0], [0, -omega / 2]], dtype=complex)


def harmonic_oscillator_hamiltonian(n_levels: int = 10, omega: float = 1.0) -> np.ndarray:
    """Truncated harmonic oscillator: H = omega * (n + 1/2) * I for n = 0..n_levels-1."""
    return omega * np.diag(np.arange(n_levels) + 0.5).astype(complex)


def maximally_mixed(n: int) -> np.ndarray:
    """Maximally mixed state rho = I/n."""
    return np.eye(n, dtype=complex) / n


def pure_state(psi: np.ndarray) -> np.ndarray:
    """Pure state density matrix: rho = |psi><psi|."""
    psi = np.asarray(psi, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    return np.outer(psi, psi.conj())


def bell_state(which: int = 0) -> np.ndarray:
    """Bell state density matrix (4x4)."""
    bell_states = [
        np.array([1, 0, 0, 1]) / math.sqrt(2),   # |Phi+>
        np.array([1, 0, 0, -1]) / math.sqrt(2),   # |Phi->
        np.array([0, 1, 1, 0]) / math.sqrt(2),    # |Psi+>
        np.array([0, 1, -1, 0]) / math.sqrt(2),   # |Psi->
    ]
    psi = bell_states[which % 4]
    return pure_state(psi)
