"""
chaos_taxonomy.py — Full EML-k Chaos Classification.

Session 51 extends Session 48's EML_K_CLASSIFICATION with:
  - Rössler system (EML-2 RHS, smooth)
  - Chua circuit (EML-inf, piecewise-linear nonlinearity)
  - Double pendulum (EML-2 per step, transcendental trig but rational once expanded)
  - Hénon map (EML-2 per step, O(n) horizon)
  - Duffing oscillator (EML-2 per step, polynomial)
  - Lorenz system (EML-2 per step — from Session 47)

Three EML-k chaos classes:
  Class 1 — SMOOTH (EML-2 per step, O(n) horizon): logistic, Chebyshev, Hénon, Lorenz, Rössler, Duffing
  Class 2 — PIECEWISE (EML-inf): tent, doubling, Chua
  Class 3 — MIXED (linear EML-1 + nonanalytic mod): Arnold cat

Key result: EML-k complexity class partitions chaotic systems cleanly.
  Smooth chaos: real-analytic → EML-2 per step
  Piecewise chaos: non-analytic kinks → EML-inf
  The partition aligns with Lyapunov exponent origin:
    Class 1: chaos from exponential sensitivity in smooth flow
    Class 2: chaos from symbol dynamics at kinks
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np

__all__ = [
    "ChaosSystem",
    "RosslerSystem",
    "ChuaCircuit",
    "DoublePendulum",
    "HenonMap",
    "DuffingOscillator",
    "FULL_CHAOS_TAXONOMY",
    "classify_system",
    "taxonomy_table",
]


# ── Base ──────────────────────────────────────────────────────────────────────

@dataclass
class ChaosSystem:
    name: str
    formula: str
    eml_class: str
    eml_depth_step: int | str
    eml_depth_horizon: str
    is_smooth: bool
    lyapunov_positive: bool
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "formula": self.formula,
            "eml_class": self.eml_class,
            "eml_depth_step": self.eml_depth_step,
            "eml_depth_horizon": self.eml_depth_horizon,
            "is_smooth": self.is_smooth,
            "lyapunov_positive": self.lyapunov_positive,
            "notes": self.notes,
        }


# ── Rössler System ────────────────────────────────────────────────────────────

class RosslerSystem:
    """
    dx/dt = -y - z
    dy/dt = x + a*y
    dz/dt = b + z*(x - c)

    RHS is degree-2 polynomial in (x,y,z) → EML-2 per step.
    Runge-Kutta integration adds O(1) depth per step.
    Long-time orbit: EML-2 per step × n_steps = O(n) depth.
    """

    def __init__(self, a: float = 0.2, b: float = 0.2, c: float = 5.7) -> None:
        self.a = a
        self.b = b
        self.c = c

    def rhs(self, state: np.ndarray) -> np.ndarray:
        x, y, z = state
        return np.array([
            -y - z,
            x + self.a * y,
            self.b + z * (x - self.c),
        ])

    def integrate(
        self,
        x0: float = 0.1,
        y0: float = 0.0,
        z0: float = 0.0,
        dt: float = 0.05,
        n_steps: int = 5000,
    ) -> np.ndarray:
        state = np.array([x0, y0, z0])
        traj = np.empty((n_steps + 1, 3))
        traj[0] = state
        for i in range(n_steps):
            k1 = self.rhs(state)
            k2 = self.rhs(state + 0.5 * dt * k1)
            k3 = self.rhs(state + 0.5 * dt * k2)
            k4 = self.rhs(state + dt * k3)
            state = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
            traj[i + 1] = state
        return traj

    def eml_analysis(self) -> dict[str, object]:
        return {
            "name": "rossler",
            "eml_class": "Class 1 — SMOOTH",
            "eml_depth_per_step": 2,
            "eml_depth_horizon_n": "O(n) — RK4 iteration, depth 2 per step",
            "rhs_polynomial_degree": 2,
            "nonlinearity": "z*x — single bilinear term",
            "insight": (
                "Rössler RHS: (-y-z, x+a*y, b+z*(x-c)). "
                "Highest degree term is z*x = product of two state variables. "
                "Product of two EML-1 expressions = EML-2. "
                "Same class as Lorenz (also degree-2 polynomial RHS)."
            ),
        }


# ── Chua Circuit ──────────────────────────────────────────────────────────────

class ChuaCircuit:
    """
    Chua's circuit with piecewise-linear diode characteristic f(x):
      f(x) = m1*x + (m0-m1)/2 * (|x+1| - |x-1|)

    The absolute value |x| is NOT real-analytic → EML-inf.
    This is the same barrier as the tent map.

    State equations:
      dx/dt = alpha * (y - x - f(x))
      dy/dt = x - y + z
      dz/dt = -beta * y
    """

    def __init__(
        self,
        alpha: float = 15.6,
        beta: float = 28.0,
        m0: float = -1.143,
        m1: float = -0.714,
    ) -> None:
        self.alpha = alpha
        self.beta = beta
        self.m0 = m0
        self.m1 = m1

    def f(self, x: float) -> float:
        """Piecewise-linear diode characteristic."""
        return self.m1 * x + 0.5 * (self.m0 - self.m1) * (abs(x + 1.0) - abs(x - 1.0))

    def rhs(self, state: np.ndarray) -> np.ndarray:
        x, y, z = state
        return np.array([
            self.alpha * (y - x - self.f(x)),
            x - y + z,
            -self.beta * y,
        ])

    def integrate(
        self,
        x0: float = 0.1,
        y0: float = 0.0,
        z0: float = 0.0,
        dt: float = 0.01,
        n_steps: int = 10000,
    ) -> np.ndarray:
        state = np.array([x0, y0, z0])
        traj = np.empty((n_steps + 1, 3))
        traj[0] = state
        for i in range(n_steps):
            k1 = self.rhs(state)
            k2 = self.rhs(state + 0.5 * dt * k1)
            k3 = self.rhs(state + 0.5 * dt * k2)
            k4 = self.rhs(state + dt * k3)
            state = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
            traj[i + 1] = state
        return traj

    def eml_analysis(self) -> dict[str, object]:
        return {
            "name": "chua_circuit",
            "eml_class": "Class 2 — PIECEWISE",
            "eml_depth_per_step": "inf",
            "eml_depth_horizon_n": "inf",
            "barrier": "Piecewise-linear diode f(x) = m1*x + (m0-m1)/2*(|x+1| - |x-1|)",
            "insight": (
                "Chua diode uses |x±1| — absolute value is not real-analytic at kinks. "
                "By the Identity Theorem, no finite EML tree can represent f(x). "
                "The chaos mechanism is the kink at x=±1, not smooth sensitivity. "
                "Same EML class as tent map: piecewise-linear chaos."
            ),
        }


# ── Double Pendulum ───────────────────────────────────────────────────────────

class DoublePendulum:
    """
    Double pendulum equations of motion (equal masses and lengths, m=l=1).
    The EOM involves sin(θ1-θ2), cos(θ1-θ2) — transcendental but:
      sin(θ1-θ2) = sin(θ1)cos(θ2) - cos(θ1)sin(θ2)
    which is degree-2 polynomial in (sin,cos) variables.

    In the (q1,q2,p1,p2) Hamiltonian formulation, the RHS is rational in sin/cos.
    Substituting u_i=sin(θ_i), v_i=cos(θ_i) gives rational expressions → EML-2.

    EML analysis:
      sin(θ) is depth 3 (pure tone formula).
      cos(θ) = sin(θ + pi/2) is also depth 3.
      Products like sin(θ1)*cos(θ2) are depth 4 (product of two depth-3 terms).
      Net per-step depth: 4 (one integration step with transcendental trig).
    """

    def __init__(self, g: float = 9.81) -> None:
        self.g = g

    def rhs(self, state: np.ndarray) -> np.ndarray:
        theta1, theta2, omega1, omega2 = state
        delta = theta1 - theta2
        denom = 2.0 - math.cos(2.0 * delta)
        sin_d = math.sin(delta)
        cos_d = math.cos(delta)

        alpha1 = (
            -self.g * (2.0 * math.sin(theta1) + math.sin(theta1 - 2.0 * theta2))
            - 2.0 * sin_d * (omega2**2 + omega1**2 * cos_d)
        ) / denom
        alpha2 = (
            2.0 * sin_d * (
                2.0 * omega1**2 + self.g * math.cos(theta1)
                + omega2**2 * cos_d
            )
        ) / denom
        return np.array([omega1, omega2, alpha1, alpha2])

    def integrate(
        self,
        theta1: float = math.pi / 2,
        theta2: float = math.pi / 3,
        omega1: float = 0.0,
        omega2: float = 0.0,
        dt: float = 0.01,
        n_steps: int = 5000,
    ) -> np.ndarray:
        state = np.array([theta1, theta2, omega1, omega2])
        traj = np.empty((n_steps + 1, 4))
        traj[0] = state
        for i in range(n_steps):
            k1 = self.rhs(state)
            k2 = self.rhs(state + 0.5 * dt * k1)
            k3 = self.rhs(state + 0.5 * dt * k2)
            k4 = self.rhs(state + dt * k3)
            state = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
            traj[i + 1] = state
        return traj

    def eml_analysis(self) -> dict[str, object]:
        return {
            "name": "double_pendulum",
            "eml_class": "Class 1 — SMOOTH (transcendental, but EML-finite)",
            "eml_depth_per_step": 4,
            "eml_depth_horizon_n": "O(n) — per step depth 4 via RK4",
            "why_depth_4": (
                "sin(θ), cos(θ) are depth 3 each. "
                "Product sin(θ1)*cos(θ2) is depth 4. "
                "Quotient adds log/exp: depth 5-6. "
                "But all functions are real-analytic → EML-finite."
            ),
            "insight": (
                "Double pendulum chaos is smooth — the equations of motion "
                "involve sin/cos (depth-3 EML) multiplied together (depth-4). "
                "No kinks or absolute values. Despite wild sensitivity to initial "
                "conditions, the EML class is 1 (smooth), not 2 (piecewise)."
            ),
        }


# ── Hénon Map ─────────────────────────────────────────────────────────────────

class HenonMap:
    """
    (x, y) -> (1 - a*x² + y, b*x)

    Degree-2 polynomial in (x,y). EML-2 per step.
    Closed form at step n: exponentially complex polynomial (no simple form).
    EML-k horizon n: O(n) — degree doubles each step: 2^n degree at step n,
    requiring O(n) EML depth to represent.
    """

    def __init__(self, a: float = 1.4, b: float = 0.3) -> None:
        self.a = a
        self.b = b

    def step(self, x: float, y: float) -> tuple[float, float]:
        return 1.0 - self.a * x * x + y, self.b * x

    def orbit(self, x0: float, y0: float, n: int) -> np.ndarray:
        traj = np.empty((n + 1, 2))
        traj[0] = [x0, y0]
        x, y = x0, y0
        for i in range(n):
            x, y = self.step(x, y)
            traj[i + 1] = [x, y]
        return traj

    def eml_analysis(self) -> dict[str, object]:
        return {
            "name": "henon_map",
            "eml_class": "Class 1 — SMOOTH",
            "eml_depth_per_step": 2,
            "eml_depth_horizon_n": "O(n) — degree-2 map iterated n times, degree grows as 2^n",
            "closed_form": "None (polynomial composition has no simple closed form)",
            "insight": (
                "(x,y) -> (1 - a*x² + y, b*x). Highest degree: x². "
                "Like logistic map: degree-2 per step, EML-2 per step. "
                "No closed form but smooth → Class 1. "
                "Hénon attractor is fractal but the MAP is EML-2."
            ),
        }


# ── Duffing Oscillator ────────────────────────────────────────────────────────

class DuffingOscillator:
    """
    dx/dt = y
    dy/dt = x - x³ - delta*y + gamma*cos(omega*t)

    Polynomial degree-3 in (x,y) → EML-2 per step (x³ = x*x*x = depth-2).
    The external forcing gamma*cos(omega*t) adds 3 more nodes but same depth (parallel).
    """

    def __init__(
        self,
        delta: float = 0.3,
        gamma: float = 0.5,
        omega: float = 1.2,
    ) -> None:
        self.delta = delta
        self.gamma = gamma
        self.omega = omega

    def rhs(self, t: float, state: np.ndarray) -> np.ndarray:
        x, y = state
        return np.array([
            y,
            x - x**3 - self.delta * y + self.gamma * math.cos(self.omega * t),
        ])

    def integrate(
        self,
        x0: float = 0.1,
        y0: float = 0.0,
        t_span: float = 100.0,
        dt: float = 0.05,
    ) -> np.ndarray:
        n_steps = int(t_span / dt)
        state = np.array([x0, y0])
        traj = np.empty((n_steps + 1, 2))
        traj[0] = state
        t = 0.0
        for i in range(n_steps):
            k1 = self.rhs(t, state)
            k2 = self.rhs(t + 0.5*dt, state + 0.5*dt*k1)
            k3 = self.rhs(t + 0.5*dt, state + 0.5*dt*k2)
            k4 = self.rhs(t + dt, state + dt*k3)
            state = state + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)
            t += dt
            traj[i + 1] = state
        return traj

    def eml_analysis(self) -> dict[str, object]:
        return {
            "name": "duffing",
            "eml_class": "Class 1 — SMOOTH",
            "eml_depth_per_step": 2,
            "eml_depth_horizon_n": "O(n)",
            "nonlinearity": "x³ = (x*x)*x — depth 2 via two multiplies",
            "forcing": "gamma*cos(omega*t) — depth 3, parallel to polynomial part",
            "insight": (
                "Duffing: dy/dt = x - x³ - delta*y + gamma*cos(omega*t). "
                "x³ is depth 2 (two multiplies). cos is depth 3. "
                "The RHS has depth 3 overall (max of parallel branches). "
                "Forced oscillator chaos: smooth sensitivity, Class 1."
            ),
        }


# ── Full Taxonomy ─────────────────────────────────────────────────────────────

FULL_CHAOS_TAXONOMY: dict[str, dict[str, object]] = {
    # Class 1 — SMOOTH
    "logistic_r4": {
        "class": 1,
        "formula": "4x(1-x)",
        "eml_per_step": 2,
        "eml_horizon": "O(n)",
        "smooth": True,
        "notes": "Exact closed form sin²(2^n*arcsin(√x)). Sessions 47-48.",
    },
    "chebyshev_T2": {
        "class": 1,
        "formula": "2x²-1 = cos(2*arccos(x))",
        "eml_per_step": 2,
        "eml_horizon": "O(n)",
        "smooth": True,
        "notes": "Conjugate to logistic. Session 48.",
    },
    "lorenz": {
        "class": 1,
        "formula": "sigma*(y-x), x*(rho-z)-y, x*y-beta*z",
        "eml_per_step": 2,
        "eml_horizon": "O(n)",
        "smooth": True,
        "notes": "Degree-2 polynomial RHS. Session 47.",
    },
    "rossler": {
        "class": 1,
        "formula": "-y-z, x+a*y, b+z*(x-c)",
        "eml_per_step": 2,
        "eml_horizon": "O(n)",
        "smooth": True,
        "notes": "Single bilinear term z*x. Session 51.",
    },
    "henon": {
        "class": 1,
        "formula": "(1-a*x²+y, b*x)",
        "eml_per_step": 2,
        "eml_horizon": "O(n)",
        "smooth": True,
        "notes": "Degree-2 map; no closed form. Session 51.",
    },
    "duffing": {
        "class": 1,
        "formula": "(y, x-x³-delta*y+gamma*cos(omega*t))",
        "eml_per_step": 2,
        "eml_horizon": "O(n)",
        "smooth": True,
        "notes": "Polynomial+cos forcing, degree 3. Session 51.",
    },
    "double_pendulum": {
        "class": 1,
        "formula": "trig rational in angles",
        "eml_per_step": 4,
        "eml_horizon": "O(n)",
        "smooth": True,
        "notes": "sin/cos products, depth 4. Session 51.",
    },
    # Class 2 — PIECEWISE
    "tent_map": {
        "class": 2,
        "formula": "1 - |2x-1|",
        "eml_per_step": "inf",
        "eml_horizon": "inf",
        "smooth": False,
        "notes": "|x| at x=0.5 kink. Session 48.",
    },
    "doubling_map": {
        "class": 2,
        "formula": "2x mod 1",
        "eml_per_step": "inf",
        "eml_horizon": "inf",
        "smooth": False,
        "notes": "mod 1 is non-analytic. Session 48.",
    },
    "chua_circuit": {
        "class": 2,
        "formula": "ODE with piecewise-linear diode f(x)",
        "eml_per_step": "inf",
        "eml_horizon": "inf",
        "smooth": False,
        "notes": "|x±1| kinks in diode characteristic. Session 51.",
    },
    # Class 3 — MIXED
    "arnold_cat": {
        "class": 3,
        "formula": "(x+y, x+2y) mod 1",
        "eml_per_step": "1 (linear) + inf (mod)",
        "eml_horizon": "inf",
        "smooth": False,
        "notes": "Linear part EML-1, mod is EML-inf. Session 48.",
    },
}


def classify_system(name: str) -> dict[str, object]:
    """Look up a system in the full taxonomy."""
    if name not in FULL_CHAOS_TAXONOMY:
        return {"error": f"Unknown system: {name}. Known: {list(FULL_CHAOS_TAXONOMY.keys())}"}
    entry = FULL_CHAOS_TAXONOMY[name].copy()
    entry["name"] = name
    entry["eml_class_name"] = {
        1: "Class 1 — SMOOTH (EML-finite)",
        2: "Class 2 — PIECEWISE (EML-inf)",
        3: "Class 3 — MIXED (EML-1 + EML-inf)",
    }.get(entry["class"], "Unknown")
    return entry


def taxonomy_table() -> str:
    """Format the full taxonomy as a readable table."""
    header = f"  {'System':22s}  {'Class':>6}  {'Depth/step':>12}  {'Horizon':>10}  {'Smooth':>7}"
    sep = "  " + "-"*22 + "  " + "-"*6 + "  " + "-"*12 + "  " + "-"*10 + "  " + "-"*7
    rows = [header, sep]
    for name, info in FULL_CHAOS_TAXONOMY.items():
        rows.append(
            f"  {name:22s}  {str(info['class']):>6}  {str(info['eml_per_step']):>12}"
            f"  {str(info['eml_horizon']):>10}  {'Yes' if info['smooth'] else 'No':>7}"
        )
    return "\n".join(rows)
