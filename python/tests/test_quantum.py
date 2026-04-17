"""Tests for quantum EML module."""

from __future__ import annotations

import math
import numpy as np
import pytest

from monogate.quantum import (
    meml,
    mdeml,
    von_neumann_entropy,
    von_neumann_entropy_meml,
    partition_function,
    quantum_free_energy,
    thermal_state,
    quantum_mutual_info,
    eml_identity_check,
    two_level_hamiltonian,
    harmonic_oscillator_hamiltonian,
    maximally_mixed,
    pure_state,
    bell_state,
    partial_trace,
)


class TestMatrixGates:
    def test_meml_identity_matrix(self):
        """meml(0, I) = expm(0) - logm(I) = I - 0 = I."""
        n = 3
        A = np.zeros((n, n))
        B = np.eye(n)
        result = meml(A, B)
        np.testing.assert_allclose(result, np.eye(n), atol=1e-10)

    def test_mdeml_recovers_boltzmann(self):
        """mdeml(beta*H, I) = expm(-beta*H) for positive beta, any H."""
        import scipy.linalg
        H = two_level_hamiltonian(omega=1.0)
        beta = 0.5
        expected = scipy.linalg.expm(-beta * H)
        n = H.shape[0]
        result = mdeml(beta * H, np.eye(n))
        np.testing.assert_allclose(result, expected, atol=1e-10)

    def test_meml_scalar_consistency(self):
        """meml([[x]], [[y]]) = [[exp(x) - log(y)]] (scalar case)."""
        x, y = 1.5, 2.0
        A = np.array([[x]])
        B = np.array([[y]])
        result = meml(A, B)
        expected = math.exp(x) - math.log(y)
        assert abs(result[0, 0] - expected) < 1e-10


class TestVonNeumannEntropy:
    def test_pure_state_zero_entropy(self):
        """Pure state |0> has S = 0."""
        rho = pure_state(np.array([1.0, 0.0]))
        s = von_neumann_entropy(rho)
        assert abs(s) < 1e-10

    def test_maximally_mixed_2d_entropy(self):
        """Maximally mixed 2-qubit state has S = ln(2)."""
        rho = maximally_mixed(2)
        s = von_neumann_entropy(rho)
        assert abs(s - math.log(2)) < 1e-10

    def test_maximally_mixed_nd_entropy(self):
        """rho = I/n has S = ln(n)."""
        for n in [2, 3, 4]:
            rho = maximally_mixed(n)
            s = von_neumann_entropy(rho)
            assert abs(s - math.log(n)) < 1e-8, f"n={n}: S={s}, expected {math.log(n)}"

    def test_entropy_via_meml_matches_eigenvalue(self):
        """S(rho) via meml gate matches eigenvalue method."""
        rho = maximally_mixed(2)
        s_eigen = von_neumann_entropy(rho)
        check = eml_identity_check(rho)
        assert check["entropy_match"], f"mismatch: {check['entropy_error']}"
        assert abs(check["entropy_eigenvalue"] - s_eigen) < 1e-10

    def test_entropy_bell_state_is_zero(self):
        """Bell states are pure, so entropy = 0."""
        for k in range(4):
            rho = bell_state(k)
            s = von_neumann_entropy(rho)
            assert abs(s) < 1e-8, f"Bell state {k}: S={s}"


class TestPartitionFunction:
    def test_two_level_partition(self):
        """Z = Tr(expm(-beta*H)) for two-level system."""
        H = two_level_hamiltonian(omega=1.0)
        beta = 1.0
        Z_expected = 2 * math.cosh(0.5)
        Z_meml = partition_function(H, beta)
        assert abs(Z_meml - Z_expected) < 1e-8

    def test_partition_function_positive(self):
        """Partition function is always positive."""
        H = two_level_hamiltonian()
        for beta in [0.1, 0.5, 1.0, 2.0, 5.0]:
            Z = partition_function(H, beta)
            assert Z > 0, f"Z={Z} at beta={beta}"

    def test_partition_function_high_temp_limit(self):
        """At beta -> 0: Z -> n (number of states)."""
        H = two_level_hamiltonian()
        Z = partition_function(H, beta=1e-6)
        assert abs(Z - 2.0) < 1e-3

    def test_harmonic_oscillator_partition(self):
        """Z for truncated harmonic oscillator converges."""
        H = harmonic_oscillator_hamiltonian(n_levels=20, omega=1.0)
        Z = partition_function(H, beta=1.0)
        # Exact: Z = sum_{n=0}^{inf} exp(-beta*(n+0.5)) = exp(-0.5) / (1 - exp(-1))
        Z_exact = math.exp(-0.5) / (1 - math.exp(-1.0))
        assert abs(Z - Z_exact) / Z_exact < 0.01  # < 1% error at 20 levels


class TestFreeEnergy:
    def test_free_energy_two_level(self):
        """F = -kT * ln(2*cosh(beta/2)) for spin-1/2."""
        H = two_level_hamiltonian(omega=1.0)
        beta = 1.0
        kT = 1.0 / beta
        F = quantum_free_energy(H, beta, kT=kT)
        F_expected = -kT * math.log(2 * math.cosh(0.5))
        assert abs(F - F_expected) < 1e-8

    def test_free_energy_consistency(self):
        """F = E - T*S at thermal equilibrium."""
        H = two_level_hamiltonian(omega=2.0)
        beta = 0.5
        kT = 1.0 / beta
        rho = thermal_state(H, beta)

        # Energy E = Tr(H * rho)
        E = float(np.real(np.trace(H @ rho)))
        # Entropy
        S = von_neumann_entropy(rho)
        F_thermodynamic = E - kT * S

        F_direct = quantum_free_energy(H, beta, kT=kT)
        assert abs(F_direct - F_thermodynamic) < 1e-8


class TestMutualInformation:
    def test_product_state_zero_mutual_info(self):
        """Product state rho_A x rho_B has I(A:B) = 0."""
        rho_A = maximally_mixed(2)
        rho_B = maximally_mixed(2)
        rho_AB = np.kron(rho_A, rho_B)
        I = quantum_mutual_info(rho_AB, 2, 2)
        assert abs(I) < 1e-8

    def test_bell_state_mutual_info(self):
        """Bell state has I(A:B) = 2*ln(2) (maximal for 2 qubits)."""
        rho_AB = bell_state(0)  # |Phi+>
        I = quantum_mutual_info(rho_AB, 2, 2)
        assert abs(I - 2 * math.log(2)) < 1e-8


class TestThermalState:
    def test_thermal_state_is_density_matrix(self):
        """rho(beta) is trace-1, positive semi-definite."""
        H = two_level_hamiltonian()
        rho = thermal_state(H, beta=1.0)
        assert abs(np.real(np.trace(rho)) - 1.0) < 1e-10
        eigenvalues = np.real(np.linalg.eigvalsh(rho))
        assert np.all(eigenvalues >= -1e-10)

    def test_high_temp_is_maximally_mixed(self):
        """At beta -> 0, thermal state -> I/n."""
        H = two_level_hamiltonian()
        rho = thermal_state(H, beta=1e-6)
        expected = maximally_mixed(2)
        np.testing.assert_allclose(rho, expected, atol=1e-3)

    def test_low_temp_is_ground_state(self):
        """At beta -> inf, thermal state -> ground state projector."""
        H = two_level_hamiltonian(omega=1.0)
        rho = thermal_state(H, beta=100.0)
        # Ground state is |1> (eigenvalue -0.5)
        eigenvalues = np.real(np.linalg.eigvalsh(rho))
        assert eigenvalues.max() > 0.99  # one eigenvalue near 1 (ground state)
