"""
Session 72 — Limits of EML Approximation

EML Weierstrass density, approximation rates for EML-∞ functions (ReLU, step, |x|),
Gibbs phenomenon, and Shannon sampling theorem.

Key theorem: The EML approximation rate for EML-∞ functions on [a,b] is O(N^{-s})
where s is the Hölder exponent — identical to classical approximation theory rates.
"""

from __future__ import annotations
import math
import json
from dataclasses import dataclass, field
from typing import Callable, Optional


EML_INF = float("inf")


@dataclass
class EMLClass:
    depth: float
    label: str
    reason: str

    def __str__(self) -> str:
        d = "∞" if self.depth == EML_INF else str(int(self.depth))
        return f"EML-{d}: {self.label}"


# ---------------------------------------------------------------------------
# EML approximation atoms
# ---------------------------------------------------------------------------

def eml_atom_k1(x: float, omega: float = 1.0, phi: float = 0.0) -> float:
    """EML-1 atom: exp(omega*x + phi)"""
    return math.exp(omega * x + phi)


def eml_atom_k2(x: float, a: float = 1.0, b: float = 1.0) -> float:
    """EML-2 atom: x^a = exp(a*ln(x)) for x > 0"""
    if x <= 0:
        return 0.0
    return math.exp(a * math.log(abs(x)))


def eml_atom_k3_sin(x: float, omega: float = 1.0) -> float:
    """EML-3 atom: sin(omega*x) via EML representation"""
    # sin(x) = Im(exp(ix)) — EML-3
    return math.sin(omega * x)


def eml_atom_k3_gauss(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """EML-3 atom: Gaussian = exp(-((x-mu)/sigma)^2 / 2)"""
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2)


# ---------------------------------------------------------------------------
# Target functions to approximate
# ---------------------------------------------------------------------------

@dataclass
class ApproximationTarget:
    name: str
    eml_depth: float
    holder_exponent: float  # s: f ∈ Hölder-s → rate O(N^{-s})
    fn: Callable[[float], float]
    eml_reason: str

    def evaluate(self, xs: list[float]) -> list[float]:
        return [self.fn(x) for x in xs]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "eml_depth": self.eml_depth if self.eml_depth != EML_INF else "∞",
            "holder_exponent": self.holder_exponent,
            "approximation_rate": f"O(N^{{-{self.holder_exponent}}})",
            "eml_reason": self.eml_reason,
        }


APPROXIMATION_TARGETS = [
    ApproximationTarget(
        "sin(x)", 3, 1.0,
        lambda x: math.sin(x),
        "EML-3: sin(x) = Im(exp(ix)) requires 3 EML gates",
    ),
    ApproximationTarget(
        "exp(-x²)", 3, 1.0,
        lambda x: math.exp(-x * x),
        "EML-3: exp(-(x·ln(e))²) — Gaussian is EML-3 despite being smooth",
    ),
    ApproximationTarget(
        "ReLU = max(x,0)", EML_INF, 0.5,
        lambda x: max(x, 0.0),
        "EML-∞: piecewise linear, not analytic; Hölder-1/2 at x=0 for approximation purposes",
    ),
    ApproximationTarget(
        "Step function 1_{x>0}", EML_INF, 0.0,
        lambda x: 1.0 if x > 0 else 0.0,
        "EML-∞: discontinuous, no EML-finite approximation converges uniformly",
    ),
    ApproximationTarget(
        "|x|", EML_INF, 1.0,
        lambda x: abs(x),
        "EML-∞: |x| = sqrt(x²); not analytic at 0; rate O(N^{-1})",
    ),
    ApproximationTarget(
        "x·sin(1/x) for x≠0", EML_INF, 0.5,
        lambda x: x * math.sin(1 / x) if abs(x) > 1e-10 else 0.0,
        "EML-∞: oscillates infinitely near 0; Hölder-1/2 regularity",
    ),
    ApproximationTarget(
        "Cantor function (devil's staircase)", EML_INF, 0.0,
        lambda x: x,  # placeholder — true Cantor function requires iteration
        "EML-∞: non-differentiable everywhere yet continuous; derivative 0 a.e.",
    ),
]


# ---------------------------------------------------------------------------
# EML-k approximation
# ---------------------------------------------------------------------------

@dataclass
class EMLApproximation:
    """
    Approximate a function on [a, b] using N EML-3 atoms (Gaussians or sinusoids).

    The EML Weierstrass theorem guarantees density. We measure the actual
    approximation error as a function of N and compare to theoretical O(N^{-s}).
    """
    a: float = -math.pi
    b: float = math.pi

    def linspace(self, n: int) -> list[float]:
        return [self.a + (self.b - self.a) * i / (n - 1) for i in range(n)]

    def fourier_approx(self, fn: Callable[[float], float], N: int, x_eval: list[float]) -> list[float]:
        """
        Approximate f using N Fourier terms (EML-3 atoms).
        Coefficients a_k = (1/π)∫f(x)cos(kx)dx, b_k = (1/π)∫f(x)sin(kx)dx.
        """
        # Numerical integration on [a, b]
        pts = 500
        xs = self.linspace(pts)
        dx = (self.b - self.a) / (pts - 1)
        L = (self.b - self.a) / 2
        a0 = sum(fn(x) for x in xs) * dx / (2 * L)
        a_coeffs = [sum(fn(x) * math.cos(k * math.pi * x / L) for x in xs) * dx / L for k in range(1, N + 1)]
        b_coeffs = [sum(fn(x) * math.sin(k * math.pi * x / L) for x in xs) * dx / L for k in range(1, N + 1)]
        result = []
        for x in x_eval:
            val = a0 + sum(a_coeffs[k - 1] * math.cos(k * math.pi * x / L) + b_coeffs[k - 1] * math.sin(k * math.pi * x / L) for k in range(1, N + 1))
            result.append(val)
        return result

    def max_error(self, fn: Callable[[float], float], approx: list[float], xs: list[float]) -> float:
        return max(abs(fn(x) - a) for x, a in zip(xs, approx))

    def approximation_rate(self, target: ApproximationTarget, N_values: list[int]) -> dict:
        """Compute max error for each N to observe convergence rate."""
        xs = self.linspace(30)
        errors = []
        for N in N_values:
            approx = self.fourier_approx(target.fn, N, xs)
            err = self.max_error(target.fn, approx, xs)
            errors.append({"N": N, "max_error": round(err, 6)})
        # Estimate rate from last two points
        if len(errors) >= 2 and errors[-1]["max_error"] > 0 and errors[-2]["max_error"] > 0:
            import math as _m
            e1, e2 = errors[-2]["max_error"], errors[-1]["max_error"]
            N1, N2 = errors[-2]["N"], errors[-1]["N"]
            rate = _m.log(e2 / e1) / _m.log(N2 / N1)
        else:
            rate = float("nan")
        return {
            "target": target.name,
            "eml_depth": target.eml_depth if target.eml_depth != EML_INF else "∞",
            "theoretical_rate": f"O(N^{{{-target.holder_exponent}}})",
            "errors": errors,
            "empirical_rate": round(rate, 3) if not math.isnan(rate) else "n/a",
        }


# ---------------------------------------------------------------------------
# Gibbs phenomenon
# ---------------------------------------------------------------------------

@dataclass
class GibbsPhenomenon:
    """
    Fourier series for step function overshoots by ~9% near the jump.
    This is the EML-3 analog: any EML-k approximation to a step function
    has oscillation near the jump (Gibbs-like behavior).

    EML interpretation: step function is EML-∞; EML-3 (Fourier) approximation
    cannot converge uniformly because of the EML-∞ barrier.
    """

    @staticmethod
    def step_function(x: float) -> float:
        return 1.0 if x > 0 else -1.0

    @staticmethod
    def fourier_step(x: float, N: int) -> float:
        """Partial Fourier sum for step function on [-π, π]."""
        total = 0.0
        for k in range(1, N + 1, 2):  # odd terms only
            total += (4 / (math.pi * k)) * math.sin(k * x)
        return total

    def overshoot_analysis(self, N: int = 50) -> dict:
        """
        Find maximum value of Fourier approximation near x=0+ to measure overshoot.
        True value = 1; Gibbs overshoot ≈ 1.0895...
        """
        xs = [0.001 + 0.001 * i for i in range(200)]
        vals = [self.fourier_step(x, N) for x in xs]
        max_val = max(vals)
        overshoot = max_val - 1.0
        return {
            "N": N,
            "max_value_near_jump": round(max_val, 6),
            "overshoot": round(overshoot, 6),
            "theoretical_overshoot": round(math.pi / 2 - 1, 6),  # ≈ 0.5708 → but Gibbs limit is 1.0895
            "gibbs_constant": round(0.0895, 4),  # ~9% overshoot in limit
            "eml_interpretation": (
                "Step function is EML-∞; any EML-3 (Fourier) approximation cannot converge uniformly. "
                "The Gibbs overshoot persists for all N → EML-∞ barrier at the discontinuity."
            ),
        }

    def convergence_away_from_jump(self, x: float = 1.0, N_values: list[int] = None) -> dict:
        """Away from the jump, Fourier series DOES converge (at the smooth points)."""
        if N_values is None:
            N_values = [5, 10, 20, 50, 100]
        true_val = self.step_function(x)
        errors = [{"N": N, "error": round(abs(self.fourier_step(x, N) - true_val), 6)} for N in N_values]
        return {
            "x": x,
            "true_value": true_val,
            "errors_away_from_jump": errors,
            "comment": "Convergence is pointwise O(1/N) away from jump; uniform convergence fails.",
        }


# ---------------------------------------------------------------------------
# Shannon sampling theorem
# ---------------------------------------------------------------------------

@dataclass
class ShannonSampling:
    """
    Shannon sampling theorem: a band-limited signal f with bandwidth B
    can be perfectly reconstructed from samples at rate ≥ 2B.

    EML analysis:
    - sinc(x) = sin(πx)/(πx): EML-3 (sin = EML-3, but ratio makes it special)
    - Band-limited signal: f(t) = Σ f(n/2B)·sinc(2Bt-n) — sum of EML-3 atoms
    - But: band-limited = analytic (Paley-Wiener) → each value is determined by EML-3 formula
    - In practice: finite bandwidth ↔ EML-3 reconstruction
    - Aliasing (sampling below Nyquist): EML-∞ artifacts (non-analytic folding)
    """

    @staticmethod
    def sinc(x: float) -> float:
        if abs(x) < 1e-12:
            return 1.0
        return math.sin(math.pi * x) / (math.pi * x)

    def reconstruct(self, samples: list[float], t: float, T: float = 1.0) -> float:
        """
        Shannon reconstruction: f(t) = Σ_n f[n] · sinc(t/T - n)
        where T = sampling interval = 1/(2B).
        """
        return sum(s * self.sinc(t / T - n) for n, s in enumerate(samples))

    def sampling_example(self) -> dict:
        """
        Sample sin(2πt) at rate 4 (Nyquist = 2) and reconstruct.
        """
        B = 1.0  # bandwidth
        T = 1 / (2 * B)  # Nyquist interval
        n_samples = 16
        samples = [math.sin(2 * math.pi * k * T) for k in range(n_samples)]

        # Reconstruct at fine grid
        t_fine = [0.05 * i for i in range(20)]
        reconstructed = [self.reconstruct(samples, t, T) for t in t_fine]
        true_values = [math.sin(2 * math.pi * t) for t in t_fine]
        max_error = max(abs(r - tr) for r, tr in zip(reconstructed, true_values))

        return {
            "signal": "sin(2πt)",
            "bandwidth_B": B,
            "nyquist_rate": 2 * B,
            "sampling_interval_T": T,
            "n_samples": n_samples,
            "max_reconstruction_error": round(max_error, 6),
            "eml_depth_sinc": 3,
            "eml_depth_reconstruction": 3,
            "reason": "Band-limited signal = Σ sinc (EML-3) atoms; perfect reconstruction in EML-3",
        }

    def eml_classification(self) -> EMLClass:
        return EMLClass(3, "Shannon reconstruction", "Σ f[n]·sinc(t/T-n) = sum of EML-3 atoms")


# ---------------------------------------------------------------------------
# EML Approximation Rate Theorem
# ---------------------------------------------------------------------------

@dataclass
class EMLApproximationRateTheorem:
    """
    Theorem: For f in Hölder-s([a,b]) and any EML-k approximation scheme:
    - If f ∈ EML-j for j ≤ k: finite N suffices to represent f exactly (EML depth exact)
    - If f ∈ EML-∞: best N-term EML-k approximation achieves O(N^{-s}) error
      matching the classical Jackson/Bernstein approximation theory rates

    This means EML approximation theory is not better or worse than classical
    polynomial/Fourier approximation theory — it has the same fundamental limits
    set by the smoothness of the target function.
    """
    statement: str = (
        "For f ∈ Hölder-s([a,b]) ∩ EML-∞, the best N-term EML-3 approximation "
        "(using exp, sin, Gaussian atoms) achieves max error O(N^{-s}), "
        "the same rate as N-term Fourier/polynomial approximation."
    )
    proof_sketch: str = (
        "Upper bound: EML-3 atoms include Fourier atoms sin(kx), cos(kx) = EML-3. "
        "Classical Fourier N-term approx achieves O(N^{-s}) for Hölder-s → "
        "so does EML-3 (contains Fourier as a subset). "
        "Lower bound: Jackson's theorem gives the optimal rate as O(N^{-s}); "
        "EML cannot do better because adding EML depth cannot improve the "
        "fundamental smoothness constraint."
    )
    examples: list[dict] = field(default_factory=lambda: [
        {"function": "sin(x)", "holder_s": 1.0, "eml_depth": 3, "rate": "exact (N=1 EML-3 atom)"},
        {"function": "ReLU", "holder_s": 0.5, "eml_depth": "∞", "rate": "O(N^{-1/2}) at the kink"},
        {"function": "Step function", "holder_s": 0.0, "eml_depth": "∞", "rate": "O(1) — no uniform convergence"},
        {"|x|": "|x|", "holder_s": 1.0, "eml_depth": "∞", "rate": "O(N^{-1})"},
        {"function": "Gaussian exp(-x²)", "holder_s": 1.0, "eml_depth": 3, "rate": "exact (N=1 EML-3 atom)"},
    ])

    def to_dict(self) -> dict:
        return {
            "theorem": "EML Approximation Rate Theorem",
            "statement": self.statement,
            "proof_sketch": self.proof_sketch,
            "examples": self.examples,
        }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_eml_limits() -> dict:
    """Run full Session 72 analysis."""

    # 1. Approximation targets classification
    targets_report = [t.to_dict() for t in APPROXIMATION_TARGETS]

    # 2. Convergence rates
    approx = EMLApproximation(a=-math.pi, b=math.pi)
    N_values = [2, 5, 10, 20, 50]
    rates = []
    for target in APPROXIMATION_TARGETS[:4]:  # skip slow ones
        rate = approx.approximation_rate(target, N_values)
        rates.append(rate)

    # 3. Gibbs phenomenon
    gibbs = GibbsPhenomenon()
    gibbs_report = {
        "overshoot_N50": gibbs.overshoot_analysis(50),
        "overshoot_N200": gibbs.overshoot_analysis(200),
        "convergence_away": gibbs.convergence_away_from_jump(1.0, [5, 20, 100]),
    }

    # 4. Shannon sampling
    shannon = ShannonSampling()
    shannon_report = shannon.sampling_example()
    shannon_eml = shannon.eml_classification()

    # 5. Theorem
    theorem = EMLApproximationRateTheorem()

    # 6. EML depth constraints on approximability
    approximability = {
        "EML_k_exactly_representable": [
            {"class": "EML-1", "examples": ["exp(ax+b)", "e^x", "e^{2x}"]},
            {"class": "EML-2", "examples": ["ln(x)", "x^a = exp(a·ln x)", "log-polynomials"]},
            {"class": "EML-3", "examples": ["sin(x)", "cos(x)", "erf(x)", "Gaussian", "arctan(x)"]},
        ],
        "EML_inf_requires_infinite_atoms": [
            {"function": "ReLU", "why": "Non-analytic at 0; EML-3 Fourier requires ∞ terms"},
            {"function": "Step function", "why": "Discontinuous; Gibbs oscillation persists"},
            {"|x|": "|x|", "why": "Non-differentiable at 0; rate O(N^{-1})"},
            {"function": "Cantor function", "why": "Singular; derivative 0 a.e."},
            {"function": "Weierstrass W(x)=Σaⁿcos(bⁿπx)", "why": "Continuous but nowhere differentiable"},
        ],
    }

    return {
        "session": 72,
        "title": "Limits of EML Approximation",
        "key_theorem": theorem.to_dict(),
        "approximation_targets": targets_report,
        "convergence_rates": rates,
        "gibbs_phenomenon": gibbs_report,
        "shannon_sampling": {
            **shannon_report,
            "eml_class": str(shannon_eml),
        },
        "approximability": approximability,
        "eml_depth_summary": {
            "Exact representation": "EML-k functions are exactly EML-k (no approximation needed)",
            "EML-3 approximation": "Dense in C[a,b] by Weierstrass theorem (Session 40)",
            "Rate for smooth functions": "O(N^{-s}) = same as Fourier/polynomial (Jackson theorem)",
            "Gibbs barrier": "Discontinuous EML-∞ functions: Gibbs oscillation never disappears",
            "Lower bound": "Cannot exceed Hölder smoothness rate regardless of EML depth of atoms",
        },
        "connections": {
            "to_session_40": "EML Weierstrass theorem: EML-3 atoms are dense in C[a,b]",
            "to_session_37": "EML-Fourier: Fourier atoms are EML-3; same approximation theory applies",
            "to_session_69": "Chaitin Ω and random sequences are EML-∞; their digit functions cannot be O(N^{-s})-approximated for any s > 0",
            "to_deep_learning": "Neural networks with ReLU activations (EML-∞) vs EML-3 activations (smooth): same approximation theory limits",
        },
    }


if __name__ == "__main__":
    result = analyze_eml_limits()
    print(json.dumps(result, indent=2, default=str))
