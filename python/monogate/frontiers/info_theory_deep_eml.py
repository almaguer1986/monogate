"""
Session 74 — Information Theory: Algorithmic & Geometric Deep Dive

Algorithmic mutual information, MDL, information geometry (Amari's α-connections),
natural gradient descent, and Legendre duality.

Key theorem: The Legendre duality of information geometry is exactly the EML-1/EML-2 duality:
exponential family (EML-1) ↔ mean parameterization (EML-2 via log partition A(θ)).
"""

from __future__ import annotations
import math
import json
from dataclasses import dataclass, field
from typing import Callable


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
# Exponential family (EML-1 atoms)
# ---------------------------------------------------------------------------

@dataclass
class ExponentialFamily:
    """
    p(x;θ) = h(x) · exp(θ·T(x) - A(θ))

    EML-1: each factor exp(θ·T(x) - A(θ)) is a single EML-1 atom.

    Log-partition function: A(θ) = ln(∫h(x)exp(θ·T(x))dx) — EML-2 (ln of integral)
    Mean parameters: η = E_θ[T(X)] = ∂A/∂θ — EML-2 (derivative of EML-2 = EML-2)

    Legendre duality:
    A*(η) = sup_θ {η·θ - A(θ)} — Legendre transform of A
    → A* is EML-2 (Legendre of EML-2 function stays EML-2 for smooth A)
    """
    name: str
    theta_range: tuple[float, float]
    T: Callable[[float], float]       # sufficient statistic
    h: Callable[[float], float]       # base measure
    A: Callable[[float], float]       # log partition function
    dA: Callable[[float], float]      # ∂A/∂θ = mean parameter η
    d2A: Callable[[float], float]     # ∂²A/∂θ² = Fisher information

    def mean_parameter(self, theta: float) -> float:
        return self.dA(theta)

    def fisher_information(self, theta: float) -> float:
        return self.d2A(theta)

    def entropy(self, theta: float) -> float:
        """H = -E[log p] = A(θ) - θ·η(θ) = A(θ) - θ·A'(θ)"""
        return self.A(theta) - theta * self.dA(theta)

    def kl_divergence(self, theta1: float, theta2: float) -> float:
        """D_KL(p_θ1 || p_θ2) = A(θ2) - A(θ1) - (θ2-θ1)·∂A/∂θ|_{θ1}"""
        return self.A(theta2) - self.A(theta1) - (theta2 - theta1) * self.dA(theta1)

    def legendre_dual(self, eta: float, n_search: int = 1000) -> float:
        """A*(η) = sup_θ {η·θ - A(θ)} — compute numerically."""
        lo, hi = self.theta_range
        best = float("-inf")
        for i in range(n_search):
            theta = lo + (hi - lo) * i / (n_search - 1)
            val = eta * theta - self.A(theta)
            if val > best:
                best = val
        return best

    def to_dict(self) -> dict:
        thetas = [self.theta_range[0] + (self.theta_range[1] - self.theta_range[0]) * k / 4 for k in range(5)]
        return {
            "name": self.name,
            "eml_density_depth": 1,
            "eml_log_partition_depth": 2,
            "eml_fisher_info_depth": 2,
            "theta_values": [round(t, 3) for t in thetas],
            "mean_parameters": [round(self.mean_parameter(t), 6) for t in thetas],
            "fisher_information": [round(self.fisher_information(t), 6) for t in thetas],
            "entropy_values": [round(self.entropy(t), 6) for t in thetas],
            "kl_example": round(self.kl_divergence(thetas[1], thetas[3]), 6),
        }


# Canonical exponential families
def gaussian_family(sigma: float = 1.0) -> ExponentialFamily:
    """N(μ, σ²): θ = μ/σ², T(x) = x, A(θ) = θ²σ²/2"""
    return ExponentialFamily(
        name=f"Gaussian N(μ,{sigma}²)",
        theta_range=(-3.0, 3.0),
        T=lambda x: x,
        h=lambda x: math.exp(-x ** 2 / (2 * sigma ** 2)) / math.sqrt(2 * math.pi * sigma ** 2),
        A=lambda t: t ** 2 * sigma ** 2 / 2,
        dA=lambda t: t * sigma ** 2,
        d2A=lambda t: sigma ** 2,
    )


def bernoulli_family() -> ExponentialFamily:
    """Bernoulli(p): θ = logit(p), T(x) = x, A(θ) = log(1+exp(θ))"""
    return ExponentialFamily(
        name="Bernoulli(p)",
        theta_range=(-3.0, 3.0),
        T=lambda x: x,
        h=lambda x: 1.0,
        A=lambda t: math.log(1 + math.exp(t)),
        dA=lambda t: math.exp(t) / (1 + math.exp(t)),  # = sigmoid(θ) = p
        d2A=lambda t: math.exp(t) / (1 + math.exp(t)) ** 2,  # = p(1-p)
    )


def exponential_family_dist() -> ExponentialFamily:
    """Exp(λ): θ = -λ, T(x) = x, A(θ) = -log(-θ) for θ < 0"""
    return ExponentialFamily(
        name="Exponential(λ)",
        theta_range=(-5.0, -0.1),
        T=lambda x: x,
        h=lambda x: 1.0,
        A=lambda t: -math.log(-t) if t < 0 else float("inf"),
        dA=lambda t: -1 / t if t < 0 else float("inf"),
        d2A=lambda t: 1 / t ** 2 if t < 0 else float("inf"),
    )


EXPONENTIAL_FAMILIES = [gaussian_family(), bernoulli_family(), exponential_family_dist()]


# ---------------------------------------------------------------------------
# Information geometry: Amari's α-connections
# ---------------------------------------------------------------------------

@dataclass
class AmariAlphaConnection:
    """
    Amari's α-connections on the statistical manifold.

    The Fisher information metric: g_{ij}(θ) = E[∂_i log p · ∂_j log p] — EML-2

    α-connection Γ^{(α)}_{ijk}:
    - α = 0: Levi-Civita (Riemannian connection of Fisher metric) → EML-2
    - α = 1: exponential connection (e-connection) → EML-1
    - α = -1: mixture connection (m-connection) → EML-1

    Duality: (e-connection, Fisher, m-connection) form a Hessian structure.
    The e and m connections are dual: geodesics in one are Pythagorean in the other.
    """
    alpha: float  # α ∈ [-1, 1]

    def connection_coefficient(self, family: ExponentialFamily, theta: float, i: int = 0, j: int = 0, k: int = 0) -> float:
        """
        For 1D exponential family:
        Γ^{(α)}_{111} = A'''(θ) / 2 - (1-α)/2 · A'''(θ)/A''(θ) · A''(θ)
        Simplified: (1+α)/2 · A'''(θ)
        """
        h = 1e-4
        A = family.A
        d3A = (A(theta + 2 * h) - 2 * A(theta + h) + 2 * A(theta - h) - A(theta - 2 * h)) / (2 * h ** 3)
        return (1 + self.alpha) / 2 * d3A

    def geodesic_description(self) -> str:
        if abs(self.alpha - 1) < 0.01:
            return "e-geodesic: mixture of canonical parameters θ → EML-1 structure (exp family)"
        if abs(self.alpha + 1) < 0.01:
            return "m-geodesic: mixture of mean parameters η → EML-2 structure (linear in η)"
        return f"α={self.alpha}: interpolation between e and m connections"

    def eml_classification(self) -> EMLClass:
        if abs(self.alpha) == 1:
            return EMLClass(1, f"α={self.alpha} connection", "e/m connections are linear in exp-family parameters → EML-1")
        return EMLClass(2, f"α={self.alpha} connection", "Levi-Civita of Fisher metric → EML-2")

    def to_dict(self) -> dict:
        fam = gaussian_family()
        thetas = [-1.0, 0.0, 1.0]
        coeffs = [round(self.connection_coefficient(fam, t), 6) for t in thetas]
        return {
            "alpha": self.alpha,
            "geodesic": self.geodesic_description(),
            "eml_class": str(self.eml_classification()),
            "connection_coefficients_gaussian": dict(zip(thetas, coeffs)),
        }


# ---------------------------------------------------------------------------
# Natural gradient descent
# ---------------------------------------------------------------------------

@dataclass
class NaturalGradient:
    """
    Natural gradient: ∇̃ L(θ) = F(θ)^{-1} · ∇L(θ)

    where F(θ) is the Fisher information matrix (EML-2).

    Standard gradient descent: θ ← θ - η·∇L — ignores metric → slow in curved space.
    Natural gradient: θ ← θ - η·F^{-1}·∇L — uses Fisher metric → invariant under reparameterization.

    EML depth:
    - Fisher F(θ): EML-2 (gradient of gradient of log density)
    - F^{-1}: EML-2 (inverse of EML-2 function)
    - Natural gradient step: EML-2 × EML-2 = EML-2
    - Amari's result: natural gradient = steepest descent in information geometry
    """

    @staticmethod
    def natural_gradient_step(
        theta: float,
        loss_grad: float,
        fisher: float,
        lr: float = 0.1,
    ) -> float:
        """θ_new = θ - lr · F^{-1} · ∇L"""
        if abs(fisher) < 1e-12:
            return theta
        return theta - lr * loss_grad / fisher

    @staticmethod
    def standard_gradient_step(theta: float, loss_grad: float, lr: float = 0.1) -> float:
        """θ_new = θ - lr · ∇L"""
        return theta - lr * loss_grad

    def optimization_comparison(self, family: ExponentialFamily, target_eta: float, n_steps: int = 20) -> dict:
        """
        Optimize to match target mean parameter η* using standard vs natural gradient.
        Loss: L(θ) = (η(θ) - η*)²/2
        """
        theta_ng = family.theta_range[0] + 0.1
        theta_sg = family.theta_range[0] + 0.1
        lr = 0.5
        ng_trajectory = []
        sg_trajectory = []
        for step in range(n_steps):
            eta_ng = family.mean_parameter(theta_ng)
            eta_sg = family.mean_parameter(theta_sg)
            loss_ng = (eta_ng - target_eta) ** 2 / 2
            loss_sg = (eta_sg - target_eta) ** 2 / 2
            ng_trajectory.append({"step": step, "theta": round(theta_ng, 4), "loss": round(loss_ng, 6)})
            sg_trajectory.append({"step": step, "theta": round(theta_sg, 4), "loss": round(loss_sg, 6)})
            # Gradients ∂L/∂θ = (η-η*)·∂η/∂θ = (η-η*)·F(θ)
            grad_ng = (eta_ng - target_eta) * family.fisher_information(theta_ng)
            grad_sg = (eta_sg - target_eta) * family.fisher_information(theta_sg)
            fisher_ng = family.fisher_information(theta_ng)
            theta_ng = self.natural_gradient_step(theta_ng, grad_ng, fisher_ng, lr)
            theta_sg = self.standard_gradient_step(theta_sg, grad_sg, lr)
            theta_ng = max(family.theta_range[0], min(family.theta_range[1], theta_ng))
            theta_sg = max(family.theta_range[0], min(family.theta_range[1], theta_sg))
        return {
            "natural_gradient": ng_trajectory[-5:],
            "standard_gradient": sg_trajectory[-5:],
            "ng_final_loss": ng_trajectory[-1]["loss"],
            "sg_final_loss": sg_trajectory[-1]["loss"],
            "eml_natural_gradient": "EML-2 (Fisher inverse × gradient = EML-2)",
        }


# ---------------------------------------------------------------------------
# Legendre duality theorem
# ---------------------------------------------------------------------------

@dataclass
class LegendreDualityTheorem:
    """
    In information geometry, the Legendre transform connects:
    - θ-parameterization (natural = EML-1): p(x;θ) = h(x)exp(θ·T(x) - A(θ))
    - η-parameterization (mean = EML-2): η = ∂A/∂θ, A*(η) = θ(η)·η - A(θ(η))

    The Legendre duality A(θ) ↔ A*(η) is exactly the EML-1/EML-2 duality:
    - A(θ): EML-2 (log partition function = ln of integral of EML-1)
    - θ(η): inverse of ∂A/∂θ → EML-2
    - A*(η): EML-2 (Legendre of EML-2 = EML-2 for smooth A)

    The duality (e-connection, Fisher, m-connection) is:
    - e-geodesics (EML-1): straight in θ-space
    - m-geodesics (EML-2): straight in η-space
    - Fisher metric (EML-2): the bridge
    """
    statement: str = (
        "EML Legendre Duality Theorem: "
        "The Legendre duality of information geometry is the EML-1/EML-2 duality. "
        "The exponential family density p(x;θ) is EML-1 in θ. "
        "The log-partition function A(θ) is EML-2. "
        "The mean parameterization η = ∂A/∂θ and its inverse A*(η) are EML-2. "
        "The Legendre transform maps EML-2 to EML-2, preserving depth."
    )

    def verify_on_gaussian(self) -> dict:
        """For Gaussian: A(θ) = θ²σ²/2, A*(η) = η²/(2σ²)."""
        sigma = 1.0
        thetas = [-2.0, -1.0, 0.0, 1.0, 2.0]
        results = []
        for theta in thetas:
            A_theta = theta ** 2 * sigma ** 2 / 2
            eta = theta * sigma ** 2  # η = ∂A/∂θ = θσ²
            A_star_eta = eta ** 2 / (2 * sigma ** 2)  # A*(η) = η²/(2σ²)
            legendre_check = eta * theta - A_theta  # should equal A*(η)
            results.append({
                "theta": theta,
                "A_theta": round(A_theta, 4),
                "eta": round(eta, 4),
                "A_star_eta": round(A_star_eta, 4),
                "legendre_check": round(legendre_check, 4),
                "match": abs(A_star_eta - legendre_check) < 1e-10,
            })
        return {
            "family": "Gaussian N(μ,1), θ=μ",
            "A_formula": "A(θ) = θ²/2 [EML-2]",
            "A_star_formula": "A*(η) = η²/2 [EML-2]",
            "verification": results,
            "eml_A": "EML-2",
            "eml_A_star": "EML-2",
            "insight": "Legendre duality maps EML-2 to EML-2 (self-dual for Gaussian)",
        }

    def to_dict(self) -> dict:
        return {
            "theorem": "EML Legendre Duality Theorem",
            "statement": self.statement,
            "gaussian_verification": self.verify_on_gaussian(),
            "duality_table": [
                {"structure": "Density p(x;θ)", "parameterization": "natural θ", "eml_depth": 1},
                {"structure": "Log-partition A(θ)", "parameterization": "θ", "eml_depth": 2},
                {"structure": "Mean parameter η=∂A/∂θ", "parameterization": "θ→η", "eml_depth": 2},
                {"structure": "Dual A*(η)", "parameterization": "η", "eml_depth": 2},
                {"structure": "Fisher metric g_{ij}", "parameterization": "θ", "eml_depth": 2},
                {"structure": "e-geodesic", "parameterization": "θ-space", "eml_depth": 1},
                {"structure": "m-geodesic", "parameterization": "η-space", "eml_depth": 2},
            ],
        }


# ---------------------------------------------------------------------------
# MDL and EML depth as model complexity
# ---------------------------------------------------------------------------

@dataclass
class MDLandEML:
    """
    Minimum Description Length (MDL) principle:
    Best model = shortest total description of data + model.

    Connection to EML:
    - EML depth k ↔ description length O(k · log n) bits for n parameters
    - EML-1 model: exp family → O(log n) bits for parameters
    - EML-2 model: log-linear → O(2 log n) bits
    - EML-∞ model: EML-∞ hypothesis class → incompressible → K(x) ≈ n bits

    Formal connection:
    - For smooth EML-k functions: MDL code length = O(k · log(1/ε)) to ε-accuracy
    - For EML-∞ targets: no finite MDL code achieves ε accuracy → K(x) = MDL in limit
    """

    @staticmethod
    def mdl_comparison() -> dict:
        return {
            "principle": "MDL: best model minimizes code_length(data|model) + code_length(model)",
            "eml_analogy": {
                "EML-0": "Constant model: 0 parameter bits; describes only constant functions",
                "EML-1": "Exponential model: O(log n) bits for θ; describes exp family",
                "EML-2": "Log-polynomial: O(2 log n) bits; describes algebraic/log-linear models",
                "EML-3": "Fourier/erf: O(3 log n) bits; describes oscillatory/Gaussian models",
                "EML-∞": "Non-analytic: requires K(x) bits; MDL cannot compress",
            },
            "key_insight": (
                "EML depth is a computable proxy for Kolmogorov complexity: "
                "EML-k ≈ K(x) = O(k·polylog) for k < ∞; "
                "EML-∞ ↔ K(x) = Θ(n) (incompressible)."
            ),
        }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_info_theory_deep_eml() -> dict:
    """Run full Session 74 analysis."""

    # 1. Exponential families
    families_report = [f.to_dict() for f in EXPONENTIAL_FAMILIES]

    # 2. Alpha-connections
    alphas = [-1.0, -0.5, 0.0, 0.5, 1.0]
    connections_report = [AmariAlphaConnection(alpha=a).to_dict() for a in alphas]

    # 3. Natural gradient
    ng = NaturalGradient()
    ng_report = ng.optimization_comparison(bernoulli_family(), target_eta=0.7, n_steps=15)

    # 4. Legendre duality theorem
    legendre = LegendreDualityTheorem()
    legendre_report = legendre.to_dict()

    # 5. MDL
    mdl_report = MDLandEML.mdl_comparison()

    # 6. Information geometry EML depth summary
    info_geo_eml = {
        "statistical_manifold": "Riemannian manifold with Fisher metric (EML-2)",
        "tangent_vectors": "Score functions ∂_i log p — EML-2 (derivative of log density)",
        "e_geodesics": "Straight lines in θ-space = EML-1 interpolations",
        "m_geodesics": "Straight lines in η-space = EML-2 interpolations",
        "divergence_Bregman": "B_A(θ||θ') = A(θ') - A(θ) - (θ'-θ)·∂A/∂θ — EML-2",
        "pythagorean_theorem": "B_A(θ||θ') = B_A(θ||θ_proj) + B_A(θ_proj||θ') — EML-2",
    }

    return {
        "session": 74,
        "title": "Information Theory: Algorithmic & Geometric Deep Dive",
        "key_theorem": legendre_report,
        "exponential_families": families_report,
        "amari_connections": connections_report,
        "natural_gradient": ng_report,
        "mdl_eml_connection": mdl_report,
        "information_geometry_eml": info_geo_eml,
        "eml_depth_summary": {
            "EML-1": "Exponential family density p(x;θ) = h(x)exp(θT(x)-A(θ)); e-geodesics in θ-space",
            "EML-2": "Log-partition A(θ), Fisher information F(θ), mean parameters η, Legendre dual A*(η), KL divergence, m-geodesics in η-space",
            "EML-3": "Entropy of Gaussian = H = ½ln(2πeσ²) — involves π → EML-3",
            "EML-∞": "Kolmogorov complexity K(x); incompressible sources; generic non-parametric models",
        },
        "connections": {
            "to_session_60": "Session 60: Shannon entropy EML-2, max-entropy=EML-1. Session 74 extends to geometry.",
            "to_session_63": "Fisher metric on stat manifold = Riemannian geometry (EML-2 curvature) — connects to Session 63 GR",
            "to_session_69": "MDL depth ↔ EML depth ↔ Kolmogorov complexity K(x) (Session 69)",
            "to_session_57": "Boltzmann/Gibbs distribution = exponential family = EML-1 (stat mech connection)",
        },
    }


if __name__ == "__main__":
    result = analyze_info_theory_deep_eml()
    print(json.dumps(result, indent=2, default=str))
