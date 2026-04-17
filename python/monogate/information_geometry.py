"""
information_geometry.py -- Session 28: Information Geometry via EML Trees.

Key theorem: For any exponential family distribution, the KL divergence equals
the Bregman divergence of the EML log-partition function A(eta).

Exponential family: p(x; eta) = h(x) * exp(eta^T T(x) - A(eta))
Log-partition function: A(eta) = ln(integral h(x) exp(eta^T T(x)) dx)

For Gaussian: A(eta) = -eta^2 / (4*eta1) - ln(-2*eta1) / 2
For Bernoulli: A(eta) = ln(1 + exp(eta))
For Poisson: A(eta) = exp(eta)

EML structure:
  Gaussian A(eta): involves ln and quadratic terms
  Bernoulli A(eta): ln(1 + exp(eta)) = softplus = BEST/DEML composition
  Poisson A(eta): exp(eta) = eml(eta, 1) — 1-node EML

KL divergence = Bregman divergence of A:
  D_KL(p||q) = A(q) - A(p) - <p - q, grad_A(p)>
"""

from __future__ import annotations

import math
from typing import Callable

import numpy as np


# ── Log-partition functions ───────────────────────────────────────────────────

def log_partition_poisson(eta: float) -> float:
    """Log-partition for Poisson: A(eta) = exp(eta).

    EML form: A(eta) = eml(eta, 1) = exp(eta) - ln(1) = exp(eta).
    This is a 1-node EML expression.

    Args:
        eta: Natural parameter (log of mean rate).

    Returns:
        A(eta) = exp(eta).
    """
    return math.exp(eta)


def log_partition_bernoulli(eta: float) -> float:
    """Log-partition for Bernoulli: A(eta) = ln(1 + exp(eta)).

    Also called softplus. EML form:
    A(eta) = eml(ln(1 + exp(eta)), 1) [uses ln and eml composition]

    Connection to DEML:
    ln(1 + exp(eta)) = eta + ln(1 + exp(-eta)) = eta - ln(deml(eta, 1) / exp(eta))

    Args:
        eta: Natural parameter (log-odds).

    Returns:
        A(eta) = ln(1 + exp(eta)).
    """
    if eta > 100:
        return eta
    if eta < -100:
        return 0.0
    return math.log1p(math.exp(eta))


def log_partition_gaussian_1d(eta1: float, eta2: float, eps: float = 1e-10) -> float:
    """Log-partition for univariate Gaussian: A(eta1, eta2) = -eta2^2/(4*eta1) - ln(-2*eta1)/2.

    Natural parameters: eta1 = -1/(2*sigma^2), eta2 = mu/sigma^2.
    Mean: mu = -eta2/(2*eta1), Variance: sigma^2 = -1/(2*eta1).

    EML structure:
    - -eta2^2/(4*eta1): ratio of squares → polynomial EXL
    - ln(-2*eta1)/2: logarithmic term → 3-node EML

    Args:
        eta1: Natural parameter 1 (must be < 0).
        eta2: Natural parameter 2.
        eps:  Numerical floor for stability.

    Returns:
        A(eta1, eta2).
    """
    if eta1 >= 0:
        return float('inf')
    return -eta2 ** 2 / (4.0 * eta1) - 0.5 * math.log(-2.0 * eta1 + eps)


def log_partition_exponential(eta: float) -> float:
    """Log-partition for Exponential distribution: A(eta) = -ln(-eta).

    Natural parameter eta = -lambda (must be < 0).
    EML form: A(eta) = -ln(-eta) = eml(0, -eta) ... [3-node EML for log]

    Args:
        eta: Natural parameter (must be < 0).

    Returns:
        A(eta) = -ln(-eta).
    """
    if eta >= 0:
        return float('inf')
    return -math.log(-eta)


# ── Fisher metric ─────────────────────────────────────────────────────────────

def fisher_metric_poisson(eta: float) -> float:
    """Fisher metric g(eta) = A''(eta) for Poisson.

    A(eta) = exp(eta), A''(eta) = exp(eta).
    So the Fisher metric = exp(eta) = mean rate.

    This is the 1-node EML expression again — exp(eta).
    """
    return math.exp(eta)


def fisher_metric_bernoulli(eta: float) -> float:
    """Fisher metric g(eta) = A''(eta) for Bernoulli.

    A(eta) = ln(1 + exp(eta))
    A'(eta) = sigmoid(eta) = 1/(1+exp(-eta))
    A''(eta) = sigmoid(eta) * (1 - sigmoid(eta)) = p*(1-p)

    The Fisher metric is the variance of the Bernoulli distribution.
    EML connection: sigmoid = DEML-near-native at depth 2.
    """
    if eta > 100:
        return 0.0
    if eta < -100:
        return 0.0
    sig = 1.0 / (1.0 + math.exp(-eta))
    return sig * (1.0 - sig)


def fisher_metric_gaussian_1d(eta1: float, eta2: float) -> np.ndarray:
    """Fisher metric (2x2 matrix) for univariate Gaussian.

    g_ij = partial^2 A / (partial eta_i partial eta_j)

    g_11 = -eta2^2 / (2*eta1^3) + 1 / (2*eta1^2)
    g_12 = g_21 = eta2 / (2*eta1^2)
    g_22 = -1 / (2*eta1)

    Returns:
        2x2 Fisher information matrix.
    """
    if eta1 >= 0:
        raise ValueError("eta1 must be < 0 for Gaussian")
    g11 = -eta2 ** 2 / (2.0 * eta1 ** 3) + 1.0 / (2.0 * eta1 ** 2)
    g12 = eta2 / (2.0 * eta1 ** 2)
    g22 = -1.0 / (2.0 * eta1)
    return np.array([[g11, g12], [g12, g22]])


# ── Bregman divergence = KL divergence ───────────────────────────────────────

def bregman_divergence(
    A: Callable[[float], float],
    grad_A: Callable[[float], float],
    eta_p: float,
    eta_q: float,
) -> float:
    """Bregman divergence of A: D_A(p||q) = A(q) - A(p) - (q-p)*grad_A(p).

    For exponential families, this equals KL divergence:
    D_KL(p||q) = D_A(p||q) where A is the log-partition function.

    This is the central theorem of information geometry via EML:
    The KL divergence IS the Bregman divergence of the EML log-partition
    function. Since A is EML-expressible, KL divergence inherits the
    EML tree structure.

    Args:
        A:      Log-partition function eta -> float.
        grad_A: Gradient of A (mean parameter map) eta -> float.
        eta_p:  Natural parameter of distribution p.
        eta_q:  Natural parameter of distribution q.

    Returns:
        D_A(p||q) = A(eta_q) - A(eta_p) - (eta_q - eta_p) * grad_A(eta_p).
    """
    return A(eta_q) - A(eta_p) - (eta_q - eta_p) * grad_A(eta_p)


def kl_divergence_poisson(eta_p: float, eta_q: float) -> float:
    """KL divergence between Poisson(exp(eta_p)) and Poisson(exp(eta_q)).

    KL(P||Q) = mu_p * (eta_p - eta_q) - (exp(eta_p) - exp(eta_q))
             = Bregman divergence of A(eta) = exp(eta).

    EML form: entirely in 1-node EML expressions.
    """
    grad_A = math.exp  # A'(eta) = exp(eta)
    return bregman_divergence(math.exp, grad_A, eta_p, eta_q)


def kl_divergence_bernoulli(eta_p: float, eta_q: float) -> float:
    """KL divergence between Bernoulli(sigmoid(eta_p)) and Bernoulli(sigmoid(eta_q)).

    KL(P||Q) = Bregman divergence of A(eta) = ln(1 + exp(eta)).
    """
    def grad_softplus(eta: float) -> float:
        if eta > 100:
            return 1.0
        if eta < -100:
            return 0.0
        return 1.0 / (1.0 + math.exp(-eta))

    return bregman_divergence(log_partition_bernoulli, grad_softplus, eta_p, eta_q)


def kl_divergence_exponential(eta_p: float, eta_q: float) -> float:
    """KL divergence between Exp(-eta_p) and Exp(-eta_q) distributions.

    A(eta) = -ln(-eta), grad_A(eta) = -1/eta.
    KL = Bregman divergence of -ln(-eta).
    """
    def grad_A(eta: float) -> float:
        return -1.0 / eta

    return bregman_divergence(log_partition_exponential, grad_A, eta_p, eta_q)


# ── Geodesics ─────────────────────────────────────────────────────────────────

def geodesic_exponential_family(
    eta1: float,
    eta2: float,
    distribution: str = "poisson",
    n_steps: int = 50,
) -> list[tuple[float, float]]:
    """Geodesic in the exponential family statistical manifold.

    The e-geodesic (exponential geodesic) is a straight line in
    the natural parameter space:
        eta(t) = (1-t)*eta1 + t*eta2,  t in [0, 1].

    The m-geodesic (mixture geodesic) is a straight line in
    the mean parameter space (expectation parameters).

    We compute the e-geodesic — it's linear in EML natural parameters.

    Args:
        eta1:         Start natural parameter.
        eta2:         End natural parameter.
        distribution: "poisson", "bernoulli", or "exponential".
        n_steps:      Number of steps along geodesic.

    Returns:
        List of (t, A(eta(t))) pairs.
    """
    A_fns = {
        "poisson": log_partition_poisson,
        "bernoulli": log_partition_bernoulli,
        "exponential": log_partition_exponential,
    }
    A = A_fns.get(distribution, log_partition_poisson)

    ts = np.linspace(0, 1, n_steps)
    path = []
    for t in ts:
        eta_t = (1.0 - t) * eta1 + t * eta2
        try:
            a_val = A(eta_t)
            if math.isfinite(a_val):
                path.append((float(t), float(a_val)))
        except Exception:
            pass
    return path


# ── Summary ───────────────────────────────────────────────────────────────────

def eml_information_geometry_summary() -> str:
    """Return a markdown summary of information geometry via EML trees."""
    return """## Information Geometry via EML Trees

| Distribution | Log-partition A(eta) | EML form | Nodes |
|-------------|---------------------|----------|-------|
| Poisson     | exp(eta)            | eml(eta, 1) | 1 |
| Bernoulli   | ln(1 + exp(eta))    | DEML composition | ~3 |
| Gaussian    | -eta2²/(4eta1) - ln(-2eta1)/2 | EXL + EML | ~5 |
| Exponential | -ln(-eta)           | 3-node EML | 3 |

**Key theorem**: For any exponential family distribution,
KL divergence = Bregman divergence of the EML log-partition function A(eta).

Since A is EML-expressible, the KL divergence inherits the EML tree structure.
The Fisher metric g_ij = ∂²A/∂eta_i ∂eta_j is also EML-expressible.

This makes EML the **natural coordinate system** for information geometry:
- Natural parameters = EML arguments
- Log-partition = EML tree
- Fisher metric = second derivative of EML tree
- KL divergence = Bregman divergence of EML tree
"""
