"""
Session 114 — Optimal Control & Dynamic Programming: EML of Optimization

Bellman equation, HJB PDE, LQR, Kalman filter, and Pontryagin maximum
principle classified by EML depth.

Key theorem: The optimal value function V* is EML-1 (fixed point of a
contraction = ground state). HJB PDE is EML-2 (first-order characteristics).
LQR Riccati solution is EML-2. Kalman filter is EML-1 (minimum variance = ground
state of estimation). Bandit regret lower bound is EML-2. Free energy connects
optimal control to thermodynamics at EML-1.
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass, field


EML_INF = float("inf")


@dataclass
class BellmanEquation:
    """
    Bellman optimality: V*(s) = min_a [c(s,a) + γ·V*(f(s,a))].

    EML structure:
    - V* = fixed point of T[V](s) = min_a [c + γV]: EML-1 (contraction mapping ground state)
    - Contraction factor γ ∈ (0,1): EML-0 (discount rate = constant)
    - Bellman residual ‖TV-V‖: converges as γ^n → EML-1 (geometric convergence)
    - Policy: π*(s) = argmin_a [...]: EML-0 (discrete argmin)
    - Q-function: Q*(s,a) = c(s,a) + γ·Σ P(s'|s,a)·V*(s'): EML-2 (expectation)
    - Temporal difference: δ = r + γV(s') - V(s): EML-2 (prediction error = correction)
    """

    def value_iteration_step(self, V: list[float], rewards: list[float],
                              transitions: list[list[float]], gamma: float = 0.9) -> dict:
        """One step of value iteration: V_new(s) = r(s) + γ·max_s' T(s,s')·V(s')."""
        n = len(V)
        V_new = []
        for s in range(n):
            max_val = rewards[s] + gamma * sum(transitions[s][sp] * V[sp] for sp in range(n))
            V_new.append(round(max_val, 6))
        bellman_residual = max(abs(V_new[s] - V[s]) for s in range(n))
        return {
            "V_old": [round(v, 4) for v in V],
            "V_new": V_new,
            "bellman_residual": round(bellman_residual, 6),
            "gamma": gamma,
            "eml_V_star": 1,
            "reason": "V* = fixed point of Bellman operator T: EML-1 (contraction = ground state)",
        }

    def geometric_convergence(self, gamma: float, n_steps: int) -> dict:
        """Bellman iteration converges geometrically: ‖V_n - V*‖ ≤ γ^n·‖V_0 - V*‖."""
        residuals = [gamma ** k for k in range(n_steps)]
        return {
            "gamma": gamma,
            "n_steps": n_steps,
            "convergence": [round(r, 6) for r in residuals],
            "eml": 1,
            "reason": "Geometric convergence γ^n = exp(n·ln γ): EML-1 per step",
        }

    def free_energy_connection(self, beta_temp: float, V_opt: float) -> dict:
        """
        Soft Bellman: V_soft(s) = -1/β·ln Σ_a exp(-β·Q(s,a)).
        Free energy = EML-1 (log partition function of Boltzmann over actions).
        """
        Z = math.exp(-beta_temp * V_opt)
        F = -math.log(Z) / beta_temp
        return {
            "beta_temperature": beta_temp,
            "V_opt": V_opt,
            "log_partition": round(-beta_temp * V_opt, 4),
            "F_free_energy": round(F, 4),
            "eml": 1,
            "reason": "Soft Bellman = -1/β·ln Z: EML-1 (log partition = free energy = Boltzmann ground state)",
            "connection": "Optimal control IS thermodynamics: V* = free energy, π* = Boltzmann policy",
        }

    def to_dict(self) -> dict:
        V0 = [0.0, 0.0, 1.0, 0.0]
        rewards = [0.0, 0.0, 1.0, 0.0]
        T = [[0.5, 0.5, 0.0, 0.0],
             [0.0, 0.3, 0.7, 0.0],
             [0.0, 0.0, 0.5, 0.5],
             [0.3, 0.0, 0.0, 0.7]]
        steps = [self.value_iteration_step(V0, rewards, T)]
        for _ in range(9):
            V0 = steps[-1]["V_new"]
            steps.append(self.value_iteration_step(V0, rewards, T))
        return {
            "value_iteration": steps[::3],
            "convergence": self.geometric_convergence(0.9, 20),
            "free_energy": self.free_energy_connection(1.0, 2.5),
            "eml_V_star": 1,
            "eml_Q_function": 2,
            "eml_TD_error": 2,
            "eml_policy": 0,
        }


@dataclass
class LQRAndRiccati:
    """
    Linear-Quadratic Regulator (LQR): optimal control of linear systems.

    min Σ x'Qx + u'Ru s.t. x_{t+1} = Ax_t + Bu_t

    EML structure:
    - Riccati equation: P = Q + A'PA - A'PB(R+B'PB)^{-1}B'PA: EML-2 (matrix equation)
    - Optimal gain: K = (R+B'PB)^{-1}B'PA: EML-2 (matrix inversion + multiplication)
    - Closed-loop: u* = -Kx: EML-0 (linear = EML-0 map times state)
    - Lyapunov stability: V(x) = x'Px: EML-2 (quadratic in x = power law)
    - Kalman filter (dual of LQR): optimal estimator = EML-1 (min variance = ground state)
    - DARE (discrete algebraic Riccati): fixed point of Riccati map = EML-2
    """

    def scalar_lqr(self, a: float, b: float, q: float = 1.0, r: float = 1.0) -> dict:
        """Scalar LQR: P satisfies P = q + a²P - a²P²b²/(r+b²P)."""
        P = 1.0
        for _ in range(1000):
            P_new = q + a**2 * P - (a**2 * P**2 * b**2) / (r + b**2 * P)
            if abs(P_new - P) < 1e-10:
                break
            P = P_new
        K = (a * b * P) / (r + b**2 * P) if (r + b**2 * P) > 0 else 0.0
        return {
            "a": a, "b": b, "q": q, "r": r,
            "P_riccati": round(P, 6),
            "K_gain": round(K, 6),
            "closed_loop_a": round(a - b * K, 6),
            "stable": abs(a - b * K) < 1.0,
            "eml_P": 2,
            "eml_K": 2,
            "reason": "Riccati solution P: EML-2 (fixed point of quadratic matrix equation). K = (R+B'PB)^{-1}B'PA: EML-2",
        }

    def kalman_filter_step(self, P: float, A: float, C: float,
                           Q_proc: float, R_obs: float) -> dict:
        """Kalman filter: predict P → APA' + Q, update P → P - PCᵀ(CPC'+R)⁻¹CP."""
        P_pred = A**2 * P + Q_proc
        S = C**2 * P_pred + R_obs
        K_kalman = P_pred * C / S if S > 0 else 0.0
        P_updated = (1 - K_kalman * C) * P_pred
        return {
            "P_prior": round(P, 6),
            "P_predicted": round(P_pred, 6),
            "K_kalman": round(K_kalman, 6),
            "P_updated": round(P_updated, 6),
            "eml": 1,
            "reason": "Kalman filter = min-variance estimator = EML-1 (ground state of estimation under Gaussian noise)",
        }

    def to_dict(self) -> dict:
        return {
            "lqr_examples": [
                self.scalar_lqr(1.1, 1.0),
                self.scalar_lqr(0.9, 0.5),
                self.scalar_lqr(1.5, 2.0),
            ],
            "kalman_steps": [
                self.kalman_filter_step(1.0, 1.0, 1.0, 0.1, 1.0),
                self.kalman_filter_step(0.5, 1.0, 1.0, 0.1, 1.0),
            ],
            "eml_lqr": 2,
            "eml_kalman": 1,
            "lqr_kalman_duality": "LQR (EML-2 control) is dual to Kalman (EML-1 estimation): same Riccati equation",
        }


@dataclass
class PontryaginAndHJB:
    """
    Pontryagin maximum principle and Hamilton-Jacobi-Bellman equation.

    EML structure:
    - Hamiltonian: H(x,p,u) = L(x,u) + p·f(x,u): EML-2 (linear in p = costate)
    - Costate dynamics: ṗ = -∂H/∂x: EML-2 (gradient of EML-2 Hamiltonian)
    - Maximum principle: H(x*,p*,u*) = max_u H: EML-0 (argmax = discrete)
    - HJB PDE: ∂V/∂t + min_u H(x, ∇V, u) = 0: EML-2 (PDE on EML-2 value function)
    - HJB characteristics = Pontryagin trajectories: EML-2 (ODEs)
    - Viscosity solution (non-smooth V): EML-∞ (shocks in value function)
    - Exploration-exploitation (bandit): regret Ω(√T) lower bound: EML-2
    """

    def hjb_linear_quadratic(self, t: float, x: float, a: float = -1.0,
                              q: float = 1.0, r: float = 1.0) -> dict:
        """
        For scalar LQ problem, V(x,t) = x²·P(t)/2 with P satisfying Riccati.
        HJB: ∂V/∂t + ax·∂V/∂x - (∂V/∂x)²/(2r) + qx²/2 = 0.
        """
        P_inf = (a + math.sqrt(a**2 + q/r)) * r
        V = x**2 * P_inf / 2
        dV_dx = x * P_inf
        optimal_u = -dV_dx / r
        return {
            "t": t, "x": x,
            "V_x_t": round(V, 4),
            "dV_dx": round(dV_dx, 4),
            "optimal_u": round(optimal_u, 4),
            "eml_V": 2,
            "eml_HJB": 2,
            "reason": "V(x) = x²P/2: EML-2 (quadratic value function). HJB = first-order PDE on EML-2 function",
        }

    def bandit_regret(self, T: int, K: int = 2) -> dict:
        """UCB1 regret: E[R_T] ≤ √(2KT·ln T) + (1+π²/3)·Σ_i Δ_i."""
        regret_upper = math.sqrt(2 * K * T * math.log(T))
        return {
            "T": T, "K": K,
            "regret_upper_bound": round(regret_upper, 2),
            "sqrt_T_ln_T": round(math.sqrt(T * math.log(T)), 2),
            "eml": 2,
            "reason": "Regret ~ √(T·ln T): EML-2 (square root × log = power law × log)",
        }

    def to_dict(self) -> dict:
        return {
            "hjb_lq": [self.hjb_linear_quadratic(t, x)
                       for t, x in [(0.0, 1.0), (0.5, 2.0), (1.0, -1.0)]],
            "bandit_regret": [self.bandit_regret(T) for T in [100, 1000, 10000, 100000]],
            "eml_pontryagin_H": 2,
            "eml_costate": 2,
            "eml_HJB": 2,
            "eml_viscosity_shock": EML_INF,
            "eml_bandit_regret": 2,
        }


def analyze_optimal_control_eml() -> dict:
    bell = BellmanEquation()
    lqr = LQRAndRiccati()
    pontryagin = PontryaginAndHJB()
    return {
        "session": 114,
        "title": "Optimal Control & Dynamic Programming: EML of Optimization",
        "key_theorem": {
            "theorem": "EML Optimal Control Theorem",
            "statement": (
                "Optimal value function V* is EML-1 (contraction fixed point = ground state). "
                "Discount factor γ is EML-0 (constant). "
                "Bellman residual converges geometrically γ^n: EML-1. "
                "Soft Bellman free energy -1/β·ln Z is EML-1 (Boltzmann ground state). "
                "LQR Riccati solution P is EML-2 (quadratic matrix equation fixed point). "
                "Kalman filter is EML-1 (min-variance = ground state of estimation). "
                "HJB PDE is EML-2 (first-order PDE on quadratic value function). "
                "Bandit regret √(T·ln T) is EML-2. "
                "Viscosity solution shocks are EML-∞."
            ),
        },
        "bellman_equation": bell.to_dict(),
        "lqr_riccati": lqr.to_dict(),
        "pontryagin_hjb": pontryagin.to_dict(),
        "eml_depth_summary": {
            "EML-0": "Discount factor γ; optimal policy argmin (discrete); LQR closed-loop u*=-Kx (linear)",
            "EML-1": "V* (Bellman fixed point); geometric convergence γ^n; soft Bellman free energy; Kalman filter",
            "EML-2": "Riccati solution P; LQR gain K; HJB PDE; TD error; Q-function; bandit regret √(T·ln T)",
            "EML-∞": "HJB viscosity shocks; exact bandit lower bounds with all arms; multi-agent game equilibria (NP-hard)",
        },
        "rabbit_hole_log": [
            "Optimal control IS thermodynamics at EML-1: the soft Bellman equation V_soft = -1/β·ln Σ exp(-β·Q(s,a)) is the free energy of a Boltzmann distribution over actions. β is the inverse temperature of the policy. The optimal deterministic policy (β→∞) is the zero-temperature ground state. Stochastic policies are thermal fluctuations. The EML-1 nature of V* is not accidental — it's the same minimum principle as thermodynamic equilibrium.",
            "Kalman filter = EML-1 by duality: the LQR (EML-2 Riccati) and Kalman filter (EML-1 min-variance) are dual problems via the same Riccati equation. Control (EML-2 design) is dual to estimation (EML-1 ground state). The difference in depth reflects the asymmetry between imposing constraints (EML-2) and satisfying them (EML-1).",
            "Bandit regret is EML-2 (√T·ln T): the exploration-exploitation tradeoff costs exactly O(√T·ln T) regret, which is EML-2. You can't do better than EML-2 efficiency without knowing the environment's EML-class. If the reward function is EML-∞ (adversarial), regret is Ω(√T) — purely EML-2 with no logarithm.",
            "HJB shocks are EML-∞: when the value function is non-smooth (shocks in viscosity solutions), V* cannot be described by any finite EML tree in the vicinity. The optimal policy undergoes a discontinuous switch — an EML-∞ event embedded in an otherwise EML-2 landscape. This is how games with switching strategies produce EML-∞ dynamics despite EML-2 objective functions.",
        ],
        "connections": {
            "to_session_57": "Free energy = -kT ln Z = EML-1. Soft Bellman free energy is the control analog. EML-1 ground state = universal.",
            "to_session_113": "Epidemic R₀ fixed point (EML-1) and Bellman V* (EML-1) have identical structure. Spreading and optimizing both converge to EML-1.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_optimal_control_eml(), indent=2, default=str))
