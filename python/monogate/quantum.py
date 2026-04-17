"""
quantum.py -- Matrix EML gates for quantum thermodynamics and entropy family.

Quantum thermodynamics is EML arithmetic on density matrices:
  - Von Neumann entropy:   S(rho) = -Tr(rho ln rho) = Tr(meml(0, rho))
  - Partition function:    Z(beta, H) = Tr(exp(-beta*H)) = Tr(mdeml(beta*H, I))
  - Quantum free energy:   F = -kT ln(Z)
  - Mutual information:    I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)

Session 24 — Quantum Entropy Family (all quantum entropies as matrix EML):
  - renyi_entropy(rho, alpha)           S_alpha = (1/(1-a))*ln(Tr(rho^a))
  - tsallis_entropy(rho, alpha)         S^T_a = (Tr(rho^a)-1)/(1-a)
  - matrix_power_eml(rho, alpha)        rho^alpha = expm(alpha*logm(rho))
  - quantum_relative_entropy(rho, sig)  S(rho||sig) = Tr(rho*(ln rho - ln sig))
  - quantum_conditional_entropy(rho_AB) H(A|B) = S(AB) - S(B)
  - lindblad_dissipator(rho, jumps)     D[rho] for open system evolution
  - sandwiched_renyi_divergence(rho,sig,a) Wilde-Winter-Yang divergence
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


# ── Session 24: Quantum Entropy Family ───────────────────────────────────────
#
# All quantum entropies are traces of matrix EML compositions.
# Theorem: S_alpha(rho) = (1/(1-alpha)) * ln(Tr(matrix_power_eml(rho, alpha)))
#          for any alpha != 1. The von Neumann entropy is the alpha -> 1 limit.

def matrix_power_eml(rho: np.ndarray, alpha: float) -> np.ndarray:
    """rho^alpha = expm(alpha * logm(rho)) — matrix EML power.

    This is the fundamental building block of the quantum entropy family.
    For alpha=1 returns rho. For alpha=0 returns I (identity).

    EML form: expm(alpha * logm(rho)) = meml(alpha*logm(rho), I) + I
    (approximately; exact via expm)
    """
    if abs(alpha - 1.0) < 1e-12:
        return rho.copy()
    if abs(alpha) < 1e-12:
        return np.eye(rho.shape[0], dtype=complex)
    logm_rho = scipy.linalg.logm(rho)
    return scipy.linalg.expm(alpha * logm_rho)


def renyi_entropy(rho: np.ndarray, alpha: float, eps: float = 1e-12) -> float:
    """Rényi entropy S_alpha(rho) = (1/(1-alpha)) * ln(Tr(rho^alpha)).

    EML structure: Tr(rho^alpha) = Tr(matrix_power_eml(rho, alpha))
    = Tr(expm(alpha * logm(rho))) — composition of matrix EML operations.

    Special cases:
        alpha -> 0:   S_0 = ln(rank(rho))  [Hartley entropy]
        alpha -> 1:   S_1 = von Neumann entropy (limit)
        alpha -> inf: S_inf = -ln(lambda_max)  [min entropy]

    Args:
        rho:   Density matrix (Hermitian, positive semidefinite, trace 1).
        alpha: Order parameter (alpha > 0, alpha != 1).
        eps:   Eigenvalue floor for numerical stability.

    Returns:
        S_alpha(rho).
    """
    if abs(alpha - 1.0) < 1e-6:
        return von_neumann_entropy(rho, eps=eps)

    eigenvalues = np.linalg.eigvalsh(rho).real
    eigenvalues = np.clip(eigenvalues, eps, None)
    eigenvalues /= eigenvalues.sum()  # renormalize after clipping

    if alpha == 0.0:
        return float(np.log(np.sum(eigenvalues > eps * 10)))

    trace_rho_alpha = float(np.sum(eigenvalues ** alpha))
    if trace_rho_alpha <= 0:
        return 0.0
    return float(np.log(trace_rho_alpha) / (1.0 - alpha))


def tsallis_entropy(rho: np.ndarray, alpha: float, eps: float = 1e-12) -> float:
    """Tsallis entropy S_alpha^T(rho) = (Tr(rho^alpha) - 1) / (1 - alpha).

    The Tsallis entropy is a deformation of the von Neumann entropy.
    In the alpha -> 1 limit it recovers S_VN.

    EML structure: numerator = Tr(matrix_power_eml(rho, alpha)) - 1
    = Tr(expm(alpha*logm(rho))) - 1 — this is the scalar EML form eml(x,1)-1
    applied to the matrix trace, making it a natural generalization of the
    DEML/EML scalar family to the matrix setting.

    Args:
        rho:   Density matrix.
        alpha: Order parameter (alpha > 0, alpha != 1).
        eps:   Eigenvalue floor.

    Returns:
        S_alpha^T(rho).
    """
    if abs(alpha - 1.0) < 1e-6:
        return von_neumann_entropy(rho, eps=eps)

    eigenvalues = np.linalg.eigvalsh(rho).real
    eigenvalues = np.clip(eigenvalues, eps, None)
    eigenvalues /= eigenvalues.sum()

    trace_rho_alpha = float(np.sum(eigenvalues ** alpha))
    return (trace_rho_alpha - 1.0) / (1.0 - alpha)


def quantum_relative_entropy(
    rho: np.ndarray,
    sigma: np.ndarray,
    eps: float = 1e-12,
) -> float:
    """Quantum relative entropy (KL divergence) S(rho || sigma).

    S(rho||sigma) = Tr(rho * (logm(rho) - logm(sigma)))
                 = Tr(rho * meml(logm(rho), sigma))  (matrix EML form)

    This is the Bregman divergence of the von Neumann entropy functional,
    connecting quantum information theory to information geometry.

    Args:
        rho:   First density matrix (the 'p' in KL divergence).
        sigma: Second density matrix (the 'q').
        eps:   Eigenvalue floor for logm stability.

    Returns:
        S(rho||sigma) >= 0, with equality iff rho == sigma.
    """
    def _safe_logm(M: np.ndarray) -> np.ndarray:
        evals, evecs = np.linalg.eigh(M)
        evals = np.clip(evals.real, eps, None)
        return (evecs * np.log(evals)) @ evecs.conj().T

    log_rho = _safe_logm(rho)
    log_sigma = _safe_logm(sigma)
    diff = log_rho - log_sigma  # meml(logm(rho), sigma) core
    result = np.real(np.trace(rho @ diff))
    return max(0.0, float(result))


def quantum_conditional_entropy(
    rho_AB: np.ndarray,
    dim_A: int,
    dim_B: int,
) -> float:
    """Quantum conditional entropy H(A|B) = S(rho_AB) - S(rho_B).

    The conditional entropy can be negative for entangled states —
    this is a fundamental feature of quantum information theory
    with no classical analog.

    Args:
        rho_AB: Joint density matrix of system AB.
        dim_A:  Hilbert space dimension of system A.
        dim_B:  Hilbert space dimension of system B.

    Returns:
        H(A|B) = S(rho_AB) - S(rho_B).  May be negative.
    """
    s_ab = von_neumann_entropy(rho_AB)
    rho_B = partial_trace(rho_AB, dim_A, dim_B, trace_out="A")
    s_b = von_neumann_entropy(rho_B)
    return s_ab - s_b


def lindblad_dissipator(
    rho: np.ndarray,
    jump_ops: list[np.ndarray],
) -> np.ndarray:
    """Lindblad dissipator D[rho] = sum_k (L_k rho L_k† - ½{L_k†L_k, rho}).

    The Lindblad master equation describes open quantum system evolution:
        d rho/dt = -i[H, rho] + D[rho]

    The steady state of D[rho] = 0 involves logm(rho) implicitly,
    connecting to the matrix EML / meml structure.

    Args:
        rho:       Density matrix.
        jump_ops:  List of Lindblad jump operators L_k.

    Returns:
        D[rho] (same shape as rho).
    """
    n = rho.shape[0]
    result = np.zeros((n, n), dtype=complex)
    for L in jump_ops:
        Ld = L.conj().T
        LdL = Ld @ L
        result += L @ rho @ Ld - 0.5 * (LdL @ rho + rho @ LdL)
    return result


def sandwiched_renyi_divergence(
    rho: np.ndarray,
    sigma: np.ndarray,
    alpha: float,
    eps: float = 1e-12,
) -> float:
    """Sandwiched Rényi divergence D_alpha(rho || sigma).

    D_alpha(rho||sigma) = (1/(alpha-1)) * ln(Tr((sigma^{(1-alpha)/2alpha}
                           * rho * sigma^{(1-alpha)/2alpha})^alpha))

    This is the operationally meaningful Rényi divergence in quantum
    information theory (Wilde-Winter-Yang, 2014). The 'sandwich' is
    precisely a matrix EML composition.

    Args:
        rho:   First density matrix.
        sigma: Second density matrix.
        alpha: Order parameter (alpha > 1/2, alpha != 1).
        eps:   Eigenvalue floor.

    Returns:
        D_alpha(rho || sigma).
    """
    if abs(alpha - 1.0) < 1e-6:
        return quantum_relative_entropy(rho, sigma, eps=eps)

    exp_coeff = (1.0 - alpha) / (2.0 * alpha)
    sigma_pow = matrix_power_eml(sigma + eps * np.eye(sigma.shape[0]), exp_coeff)
    M = sigma_pow @ rho @ sigma_pow
    M_alpha = matrix_power_eml(M + eps * np.eye(M.shape[0]), alpha)
    trace_val = float(np.real(np.trace(M_alpha)))
    if trace_val <= 0:
        return 0.0
    return float(np.log(trace_val) / (alpha - 1.0))
