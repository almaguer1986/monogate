"""
Session 83 — Limits of Approximation Deep: Runge, NTK, Optimal Polynomials

Full characterization of non-EML-approximable functions: Runge phenomenon,
Chebyshev optimal polynomials, neural tangent kernel (NTK) approximation theory,
and the EML-∞ obstruction theorem.

Key theorem: Every continuous function on [a,b] can be ε-approximated by
N EML-3 atoms with N = O(ε^{-1/s}) where s is the Hölder exponent —
but functions in EML-∞ ∩ C^0 require N = Ω(ε^{-1/s}) with no EML-finite shortcut.
"""

from __future__ import annotations
import math, json
from dataclasses import dataclass, field
from typing import Callable


EML_INF = float("inf")


@dataclass
class RungePhenomenon:
    """
    Runge's phenomenon: high-degree polynomial interpolation at equispaced nodes
    diverges near endpoints for functions like f(x) = 1/(1+25x²).

    EML analysis:
    - f(x) = 1/(1+25x²): EML-2 (rational function)
    - Polynomial interpolant P_n(x): EML-2 (polynomial = rational = EML-2)
    - Runge divergence: max|P_n - f| → ∞ near x=±1 even though f is analytic
    - Chebyshev nodes: max error = O(n^{-s}) without Runge → optimal EML-2 approximation
    """
    func: str = "1/(1+25x²)"
    a: float = -1.0
    b: float = 1.0

    def runge_f(self, x: float) -> float:
        return 1.0 / (1 + 25 * x ** 2)

    def chebyshev_nodes(self, n: int) -> list[float]:
        return [math.cos(math.pi * (2 * k - 1) / (2 * n)) for k in range(1, n + 1)]

    def equispaced_nodes(self, n: int) -> list[float]:
        return [self.a + (self.b - self.a) * k / (n - 1) for k in range(n)]

    def lagrange_interpolate(self, nodes: list[float], x: float) -> float:
        n = len(nodes)
        values = [self.runge_f(xi) for xi in nodes]
        result = 0.0
        for i in range(n):
            num = 1.0
            den = 1.0
            for j in range(n):
                if i != j:
                    num *= (x - nodes[j])
                    den *= (nodes[i] - nodes[j])
            if abs(den) > 1e-15:
                result += values[i] * num / den
        return result

    def max_error(self, nodes: list[float], test_pts: int = 100) -> float:
        xs = [self.a + (self.b - self.a) * k / (test_pts - 1) for k in range(test_pts)]
        return max(abs(self.lagrange_interpolate(nodes, x) - self.runge_f(x)) for x in xs)

    def to_dict(self) -> dict:
        report = []
        for n in [5, 10, 15]:
            eq_nodes = self.equispaced_nodes(n)
            cheb_nodes = self.chebyshev_nodes(n)
            report.append({
                "n": n,
                "equispaced_max_error": round(self.max_error(eq_nodes), 4),
                "chebyshev_max_error": round(self.max_error(cheb_nodes), 4),
            })
        return {
            "function": self.func,
            "eml_depth_f": 2,
            "runge_comparison": report,
            "eml_insight": "Runge: equispaced interpolation diverges even for EML-2 functions; Chebyshev nodes converge geometrically",
        }


@dataclass
class ChebyshevApproximation:
    """
    Chebyshev approximation theory: best polynomial approximation to f on [-1,1].

    Jackson's theorem: if f ∈ C^k[-1,1], then best N-term poly approx error = O(N^{-k})
    Bernstein's theorem: if error = O(N^{-α}), then f is analytic in strip of width α/N

    EML version:
    - EML-k functions are analytic in exponentially large strips → geometric convergence
    - EML-∞ functions: rate determined by Hölder exponent only

    Chebyshev expansion: f = Σ a_n T_n(x) where a_n = EML-class of f
    - f ∈ EML-3: |a_n| ~ exp(-cn) (geometric decay) → N terms give exp(-cN) error
    - f ∈ EML-∞ ∩ Hölder-s: |a_n| ~ n^{-s} → N terms give O(N^{-s}) error
    """

    @staticmethod
    def chebyshev_T(n: int, x: float) -> float:
        if abs(x) <= 1:
            return math.cos(n * math.acos(x))
        elif x > 1:
            return math.cosh(n * math.acosh(x))
        else:
            return (-1) ** n * math.cosh(n * math.acosh(-x))

    @staticmethod
    def chebyshev_coefficients(f: Callable[[float], float], n_coefs: int, n_pts: int = 500) -> list[float]:
        xs = [math.cos(math.pi * (k + 0.5) / n_pts) for k in range(n_pts)]
        fs = [f(x) for x in xs]
        coeffs = []
        for n in range(n_coefs):
            c = 2 / n_pts * sum(fk * ChebyshevApproximation.chebyshev_T(n, xk) for fk, xk in zip(fs, xs))
            if n == 0:
                c /= 2
            coeffs.append(c)
        return coeffs

    def decay_rate(self, f_name: str, f: Callable[[float], float], eml_depth: int) -> dict:
        coeffs = self.chebyshev_coefficients(f, 20)
        abs_coeffs = [abs(c) for c in coeffs]
        # Fit geometric vs power law decay
        log_coeffs = [math.log(c) if c > 1e-15 else -35 for c in abs_coeffs[1:10]]
        n_vals = list(range(1, 10))
        # Linear regression on log|a_n| vs n (geometric) and vs log(n) (power law)
        n_avg = sum(n_vals) / len(n_vals)
        log_avg = sum(log_coeffs) / len(log_coeffs)
        geom_slope = sum((n - n_avg) * (l - log_avg) for n, l in zip(n_vals, log_coeffs)) / sum((n - n_avg) ** 2 for n in n_vals)
        return {
            "function": f_name,
            "eml_depth": eml_depth,
            "chebyshev_coefficients": [round(c, 6) for c in abs_coeffs[:8]],
            "geometric_decay_rate": round(geom_slope, 4),
            "convergence_type": "geometric (analytic f)" if geom_slope < -0.5 else "polynomial (non-analytic)",
        }


@dataclass
class NeuralTangentKernel:
    """
    Neural tangent kernel (NTK) approximation theory.

    Infinite-width neural network with EML-k activations:
    - Training converges to kernel regression with kernel K_NTK
    - K_NTK depends on activation σ: K = E[σ'(u)σ'(v)]
    - For σ = erf (EML-3): K_NTK is EML-3 (product of EML-3 functions)
    - For σ = ReLU (EML-∞): K_NTK involves |⟨u,v⟩|/... — EML-2 (piecewise)

    Approximation in RKHS of K_NTK:
    - EML-3 activation → smooth K_NTK → RKHS = Sobolev space → rate O(N^{-s})
    - EML-∞ activation (ReLU) → K_NTK = EML-2 → RKHS = "rougher" → rate O(N^{-s}) same
    - Key: activation EML depth does NOT change approximation rate; only the target's smoothness matters
    """

    @staticmethod
    def ntk_eml_table() -> list[dict]:
        return [
            {
                "activation": "erf (EML-3)",
                "K_NTK_depth": 3,
                "RKHS_space": "Sobolev H^s for all s",
                "approx_rate": "O(N^{-s}) matching target smoothness",
                "note": "Smooth kernel → faster convergence for smooth targets",
            },
            {
                "activation": "ReLU (EML-∞)",
                "K_NTK_depth": 2,
                "RKHS_space": "Sobolev H^{3/2} (arc-cosine kernel)",
                "approx_rate": "O(N^{-3/2}) for smooth targets",
                "note": "Less smooth kernel → limited rate even for smooth targets",
            },
            {
                "activation": "tanh (EML-3)",
                "K_NTK_depth": 3,
                "RKHS_space": "Sobolev H^s for s depending on depth",
                "approx_rate": "O(N^{-s}) for smooth targets",
                "note": "Similar to erf; EML-3 activations give smoother NTK",
            },
        ]


def analyze_approx_limits_deep_eml() -> dict:
    runge = RungePhenomenon()
    runge_report = runge.to_dict()
    cheb = ChebyshevApproximation()
    decay_report = [
        cheb.decay_rate("sin(πx) [EML-3]", lambda x: math.sin(math.pi * x), 3),
        cheb.decay_rate("|x| [EML-∞]", lambda x: abs(x), EML_INF),
        cheb.decay_rate("exp(-x²) [EML-3]", lambda x: math.exp(-x**2), 3),
        cheb.decay_rate("1/(1+25x²) [EML-2]", lambda x: 1/(1+25*x**2), 2),
    ]
    ntk = NeuralTangentKernel()
    return {
        "session": 83,
        "title": "Limits of Approximation Deep: Runge, NTK, Chebyshev",
        "key_theorem": {
            "theorem": "EML Approximation Obstruction Theorem",
            "statement": (
                "For f ∈ EML-j (j finite), N-term EML-k approximation (k≥j) achieves exact representation for finite N. "
                "For f ∈ EML-∞ ∩ Hölder-s, the best N-term approximation error is Θ(N^{-s}): "
                "no EML-finite shortcut exists; the rate is determined purely by the Hölder smoothness. "
                "EML depth of the approximation atoms does NOT improve beyond the smoothness barrier."
            ),
        },
        "runge_phenomenon": runge_report,
        "chebyshev_decay_rates": decay_report,
        "neural_tangent_kernel": ntk.ntk_eml_table(),
        "eml_depth_summary": {
            "EML-2": "Runge function 1/(1+25x²); polynomial interpolants; Chebyshev polynomials",
            "EML-3": "erf activation NTK; sin(πx) with geometric Chebyshev decay; Shannon sinc",
            "EML-∞": "|x| at 0; ReLU activation; Chebyshev decay is polynomial not geometric",
        },
        "connections": {
            "to_session_72": "Session 72: Gibbs, rate O(N^{-s}). Session 83: adds Runge, Chebyshev decay, NTK.",
            "to_session_56": "ML theory (Session 56): EML-3 activation (erf/tanh) better than EML-∞ (ReLU) for smooth targets",
        },
    }


if __name__ == "__main__":
    print(json.dumps(analyze_approx_limits_deep_eml(), indent=2, default=str))
