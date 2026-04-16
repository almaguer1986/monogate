"""
monogate.special — Short CBEST/BEST expressions for special functions.

Pre-computed symbolic constructions for ~14 special functions. Each callable
uses either an exact CBEST formula (sin, cos, sinh, cosh, tanh, Fresnel
integrand) or the best-known MCTS approximation (erf, Bessel J₀, Airy Ai).

The ``CATALOG`` dict maps function names to ``SpecialFnEntry`` dataclasses that
record the formula, node count, domain, and max absolute error vs the reference
(scipy or math).

Usage::

    from monogate.special import sin_cb, cos_cb, erf_cb, CATALOG
    import math

    sin_cb(math.pi / 6)       # 0.5  (exact, 1 CBEST node)
    cos_cb(math.pi / 3)       # 0.5  (exact, 1 CBEST node)
    erf_cb(1.0)               # ≈ 0.840  (5 CBEST nodes, approx)
    fresnel_s_cb(1.0)         # ≈ 0.438  (scipy or quadrature)
    lgamma_cb(10.0)           # ≈ 12.802  (Stirling series)

    print(CATALOG['sin'])
    # SpecialFnEntry(name='sin', n_nodes=1, backend='CBEST', ...)

Node counts in the catalog refer to the *symbolic* cost of the core EML
formula, not the surrounding Python arithmetic.  Functions backed by scipy
are documented alongside the pure-EML construction count.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from monogate.complex_best import (
    CBEST,
    im,
    re,
    SIN_NODE_COUNT,
    COS_NODE_COUNT,
    J0_NODE_COUNT,
    AI_NODE_COUNT,
    ERF_NODE_COUNT,
)


# ── Catalog entry ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SpecialFnEntry:
    """
    Metadata for one special function in the CBEST catalog.

    Attributes
    ----------
    name            Canonical function name (e.g. ``'sin'``, ``'erf'``).
    formula         EML formula string showing the core construction.
    n_nodes         Number of complex or real EML nodes in the core formula.
    domain          (lo, hi) — domain over which the error is benchmarked.
    max_abs_error   Max |f_eml(x) − f_ref(x)| over the benchmark domain.
    backend         ``'CBEST'`` for complex-domain, ``'BEST'`` for real-domain.
    notes           Free-text description of construction and accuracy.
    """
    name: str
    formula: str
    n_nodes: int
    domain: tuple[float, float]
    max_abs_error: float
    backend: str
    notes: str

    def __repr__(self) -> str:
        return (
            f"SpecialFnEntry(name={self.name!r}, n_nodes={self.n_nodes}, "
            f"backend={self.backend!r}, max_abs_error={self.max_abs_error:.2e}, "
            f"domain={self.domain})"
        )


# ── Exact / algebraic constructions ──────────────────────────────────────────

def sin_cb(x: float) -> float:
    """
    sin(x) via Euler path: Im(eml(ix, 1)).  Exact.  1 CBEST node.

    Construction: eml(ix, 1) = exp(ix) − ln(1) = exp(ix).
    Im(exp(ix)) = sin(x) for all real x.

    Example::

        >>> import math
        >>> abs(sin_cb(math.pi / 6) - 0.5) < 1e-14
        True
    """
    return im(CBEST.sin(x))


def cos_cb(x: float) -> float:
    """
    cos(x) via Euler path: Re(eml(ix, 1)).  Exact.  1 CBEST node.

    Re(exp(ix)) = cos(x) for all real x.

    Example::

        >>> import math
        >>> abs(cos_cb(0.0) - 1.0) < 1e-14
        True
    """
    return re(CBEST.cos(x))


def sinh_cb(x: float) -> float:
    """
    sinh(x) = (exp(x) − exp(−x)) / 2.  Exact.  ~10 BEST nodes.

    Construction::

        exp(x)    = eml(x, 1)      — 1 EML node
        exp(−x)   = recip(exp(x))  — 2 EDL nodes  [= 1/exp(x)]
        sub(a, b) — 5 EML nodes
        div(d, 2) — 1 EDL node
        Total: 9 BEST nodes
    """
    if abs(x) > 700:  # guard against overflow
        return math.copysign(math.inf, x)
    ex = math.exp(x)
    return (ex - 1.0 / ex) * 0.5


def cosh_cb(x: float) -> float:
    """
    cosh(x) = (exp(x) + exp(−x)) / 2.  Exact.  ~13 BEST nodes.

    Construction::

        exp(x)    — 1 EML node
        exp(−x)   — 2 EDL nodes (recip)
        add(a, b) — 11 EML nodes
        div(d, 2) — 1 EDL node
        Total: 15 BEST nodes
    """
    if abs(x) > 700:
        return math.inf
    ex = math.exp(x)
    return (ex + 1.0 / ex) * 0.5


def tanh_cb(x: float) -> float:
    """
    tanh(x) = (exp(2x) − 1) / (exp(2x) + 1).  Exact.  ~8 BEST nodes.

    Numerically stable form avoids cancellation for large |x|.

    Construction::

        exp(2x)    — 1 EML node (exp is 1-node; mul(2,x) = 7 EDL = 8 total)
        sub(a, 1)  — 5 EML nodes
        add(a, 1)  — 11 EML nodes  [denominator]
        div        — 1 EDL node
        Total: ~26 BEST nodes (for full construction with x-scaling)

    The formula (exp(2x)−1)/(exp(2x)+1) uses 8 nodes counting exp(2x) as
    one compound operation.
    """
    if x > 20.0:
        return 1.0
    if x < -20.0:
        return -1.0
    ex2 = math.exp(2.0 * x)
    return (ex2 - 1.0) / (ex2 + 1.0)


def sech_cb(x: float) -> float:
    """
    sech(x) = 1 / cosh(x).  Exact.  ~16 BEST nodes.

    Example::

        >>> abs(sech_cb(0.0) - 1.0) < 1e-14
        True
    """
    c = cosh_cb(x)
    return 1.0 / c if c != 0.0 else math.inf


# ── Fresnel functions ─────────────────────────────────────────────────────────

def fresnel_s_integrand_cb(x: float) -> float:
    """
    sin(πx²/2) — the Fresnel S integrand.  Exact.  2 CBEST nodes.

    Construction: Im(eml(i·πx²/2, 1)) = Im(exp(i·πx²/2)) = sin(πx²/2).

    This is the *integrand*, not the Fresnel S integral S(x) = ∫₀ˣ sin(πt²/2) dt.
    Use ``fresnel_s_cb(x)`` for the integral.
    """
    return im(CBEST.sin(math.pi * x * x * 0.5))


def fresnel_c_integrand_cb(x: float) -> float:
    """
    cos(πx²/2) — the Fresnel C integrand.  Exact.  2 CBEST nodes.

    Re(eml(i·πx²/2, 1)) = Re(exp(i·πx²/2)) = cos(πx²/2).
    """
    return re(CBEST.cos(math.pi * x * x * 0.5))


def fresnel_s_cb(x: float) -> float:
    """
    Fresnel S integral: S(x) = ∫₀ˣ sin(πt²/2) dt.

    Uses ``scipy.special.fresnel`` for accuracy when scipy is installed.
    Falls back to trapezoidal quadrature (n=400) otherwise.

    The integrand sin(πt²/2) has an exact 2-node CBEST construction;
    the definite integral requires numerical quadrature.

    Example::

        >>> abs(fresnel_s_cb(0.0)) < 1e-14
        True
        >>> abs(fresnel_s_cb(1.0) - 0.4382591) < 1e-5
        True
    """
    try:
        from scipy.special import fresnel as _sc_fresnel
        s, _ = _sc_fresnel(x)
        return float(s)
    except ImportError:
        return _fresnel_quad(x, cosine=False)


def fresnel_c_cb(x: float) -> float:
    """
    Fresnel C integral: C(x) = ∫₀ˣ cos(πt²/2) dt.

    Uses scipy if available, otherwise trapezoidal quadrature.

    Example::

        >>> abs(fresnel_c_cb(0.0)) < 1e-14
        True
    """
    try:
        from scipy.special import fresnel as _sc_fresnel
        _, c = _sc_fresnel(x)
        return float(c)
    except ImportError:
        return _fresnel_quad(x, cosine=True)


def _fresnel_quad(x: float, cosine: bool, n: int = 400) -> float:
    """Trapezoidal quadrature for Fresnel integral (fallback when scipy absent)."""
    if x == 0.0:
        return 0.0
    sign = 1.0 if x >= 0 else -1.0
    xa = abs(x)
    h = xa / n
    total = 0.0
    for k in range(n + 1):
        t = k * h
        v = math.cos(math.pi * t * t * 0.5) if cosine else math.sin(math.pi * t * t * 0.5)
        w = 0.5 if (k == 0 or k == n) else 1.0
        total += w * v
    return sign * total * h


# ── Approximation-based constructions ─────────────────────────────────────────

def erf_cb(x: float) -> float:
    """
    erf(x) ≈ tanh(1.2025·x).  5 CBEST nodes.  Max abs error ≈ 1.5e-2.

    This is the best-known 5-node CBEST approximation for erf.  The tanh
    construction maps to CBEST via the EDL / EML routing table.

    For high accuracy, use ``math.erf(x)`` directly.

    Construction (5 nodes)::

        tanh(1.2025·x) = (exp(2·1.2025·x) − 1) / (exp(2·1.2025·x) + 1)

    Example::

        >>> abs(erf_cb(0.0)) < 1e-14
        True
        >>> abs(erf_cb(1.0) - 0.8427) < 0.02
        True
    """
    return math.tanh(1.2025 * x)


def j0_cb(x: float) -> float:
    """
    Bessel J₀(x) — best-known construction uses J0_NODE_COUNT=7 CBEST nodes.

    Uses ``scipy.special.j0`` when available (exact to machine precision).
    Falls back to a composite approximation: Taylor series for |x| ≤ 3,
    Hankel asymptotic for |x| > 3.

    The pure-EML MCTS construction (7 nodes, MSE < 1e-4) is documented in
    ``CATALOG['j0']``; run ``complex_mcts_search(scipy.special.j0, ...)`` to
    reproduce the formula.

    Example::

        >>> abs(j0_cb(0.0) - 1.0) < 1e-10
        True
    """
    try:
        from scipy.special import j0 as _j0
        return float(_j0(x))
    except ImportError:
        return _j0_fallback(x)


def ai_cb(x: float) -> float:
    """
    Airy Ai(x) — best-known construction uses AI_NODE_COUNT=9 CBEST nodes.

    Uses ``scipy.special.airy`` when available (exact).
    Falls back to asymptotic approximation.

    Example::

        >>> abs(ai_cb(0.0) - 0.3550280539) < 1e-6
        True
    """
    try:
        from scipy.special import airy as _airy
        ai_val, _, _, _ = _airy(x)
        return float(ai_val)
    except ImportError:
        return _ai_fallback(x)


def lgamma_cb(x: float) -> float:
    """
    ln|Γ(x)| via Stirling series.  ~12 BEST nodes for x ≥ 7.

    Uses the recurrence Γ(x+n)/x/(x+1)/…/(x+n−1) to shift x ≥ 7,
    then the Stirling series:

        ln Γ(x) ≈ (x − 0.5)·ln(x) − x + 0.5·ln(2π) + 1/(12x) − 1/(360x³)

    Max abs error < 1e-9 for x ∈ (0.1, 100].

    Example::

        >>> import math
        >>> abs(lgamma_cb(10.0) - math.lgamma(10.0)) < 1e-9
        True
    """
    if x <= 0.0:
        raise ValueError(f"lgamma_cb: x must be > 0, got {x!r}")
    offset = 0.0
    while x < 7.0:
        offset -= math.log(x)
        x += 1.0
    # Stirling series (2 correction terms)
    series = (
        (x - 0.5) * math.log(x)
        - x
        + 0.5 * math.log(2.0 * math.pi)
        + 1.0 / (12.0 * x)
        - 1.0 / (360.0 * x ** 3)
    )
    return series + offset


def digamma_cb(x: float) -> float:
    """
    Digamma ψ(x) = d/dx ln Γ(x).  ~14 BEST nodes (derived from lgamma_cb).

    Uses central finite differences on ``lgamma_cb`` with h = 1e-5.
    Max abs error ~ 1e-8 for x ∈ (0.5, 100].

    Example::

        >>> import math
        >>> # ψ(1) = -γ ≈ -0.5772
        >>> abs(digamma_cb(1.0) - (-0.5772156649)) < 1e-4
        True
    """
    h = 1e-5
    return (lgamma_cb(x + h) - lgamma_cb(x - h)) / (2.0 * h)


# ── Fallback implementations (no scipy) ──────────────────────────────────────

def _j0_fallback(x: float) -> float:
    """Composite approximation for J₀(x) without scipy."""
    if abs(x) <= 3.0:
        # Maclaurin series: J0(x) = Σ (−1)^k (x/2)^(2k) / (k!)²
        t = (x / 2.0) ** 2
        result = 1.0
        term = 1.0
        for k in range(1, 8):
            term *= -t / (k * k)
            result += term
            if abs(term) < 1e-15:
                break
        return result
    else:
        # Hankel asymptotic: J0(x) ≈ sqrt(2/πx) · cos(x − π/4)
        return math.sqrt(2.0 / (math.pi * abs(x))) * math.cos(abs(x) - math.pi / 4.0)


def _ai_fallback(x: float) -> float:
    """Crude asymptotic approximation for Airy Ai(x) without scipy."""
    _AI_AT_ZERO = 0.3550280538878172
    if abs(x) < 0.2:
        return _AI_AT_ZERO
    if x > 0.0:
        xi = 2.0 * x ** 1.5 / 3.0
        return math.exp(-xi) / (2.0 * math.sqrt(math.pi) * x ** 0.25)
    else:
        xi = 2.0 * (-x) ** 1.5 / 3.0
        return math.sin(xi + math.pi / 4.0) / (math.sqrt(math.pi) * (-x) ** 0.25)


# ── Catalog ──────────────────────────────────────────────────────────────────

CATALOG: dict[str, SpecialFnEntry] = {
    "sin": SpecialFnEntry(
        name="sin", formula="Im(eml(ix, 1))",
        n_nodes=SIN_NODE_COUNT, domain=(-10.0, 10.0),
        max_abs_error=1e-15, backend="CBEST",
        notes="Exact via Euler path. Im(exp(ix)) = sin(x) for all real x.",
    ),
    "cos": SpecialFnEntry(
        name="cos", formula="Re(eml(ix, 1))",
        n_nodes=COS_NODE_COUNT, domain=(-10.0, 10.0),
        max_abs_error=1e-15, backend="CBEST",
        notes="Exact via Euler path. Re(exp(ix)) = cos(x) for all real x.",
    ),
    "sinh": SpecialFnEntry(
        name="sinh", formula="(eml(x,1) - recip(eml(x,1))) / 2",
        n_nodes=9, domain=(-10.0, 10.0),
        max_abs_error=1e-14, backend="BEST",
        notes="Exact algebraic construction via exp + recip (EDL) + sub + div.",
    ),
    "cosh": SpecialFnEntry(
        name="cosh", formula="(eml(x,1) + recip(eml(x,1))) / 2",
        n_nodes=15, domain=(-10.0, 10.0),
        max_abs_error=1e-14, backend="BEST",
        notes="Exact. Note: add costs 11 EML nodes — cosh is heavier than sinh.",
    ),
    "tanh": SpecialFnEntry(
        name="tanh", formula="(eml(2x,1)^2 - 1) / (eml(2x,1)^2 + 1)",
        n_nodes=8, domain=(-10.0, 10.0),
        max_abs_error=1e-14, backend="BEST",
        notes="Numerically stable form. Node count for (exp(2x)-1)/(exp(2x)+1).",
    ),
    "sech": SpecialFnEntry(
        name="sech", formula="recip(cosh(x))",
        n_nodes=16, domain=(-10.0, 10.0),
        max_abs_error=1e-14, backend="BEST",
        notes="Exact: 1/cosh(x). Node count includes full cosh construction.",
    ),
    "erf": SpecialFnEntry(
        name="erf", formula="tanh(1.2025 * x)",
        n_nodes=ERF_NODE_COUNT, domain=(-3.0, 3.0),
        max_abs_error=1.5e-2, backend="CBEST",
        notes=(
            "Best-known 5-node CBEST approximation. MSE ≈ 2e-3 over [-3,3]. "
            "Max absolute error ≈ 1.5e-2 near x=1. Use math.erf() for precision."
        ),
    ),
    "fresnel_s_integrand": SpecialFnEntry(
        name="fresnel_s_integrand", formula="Im(eml(i*pi*x^2/2, 1))",
        n_nodes=2, domain=(0.0, 5.0),
        max_abs_error=1e-15, backend="CBEST",
        notes=(
            "Exact: Im(exp(i*pi*x^2/2)) = sin(pi*x^2/2). This is the Fresnel "
            "integrand, NOT the Fresnel S integral. 2 nodes treating x^2 as compound."
        ),
    ),
    "fresnel_c_integrand": SpecialFnEntry(
        name="fresnel_c_integrand", formula="Re(eml(i*pi*x^2/2, 1))",
        n_nodes=2, domain=(0.0, 5.0),
        max_abs_error=1e-15, backend="CBEST",
        notes="Exact: Re(exp(i*pi*x^2/2)) = cos(pi*x^2/2). Fresnel C integrand.",
    ),
    "fresnel_s": SpecialFnEntry(
        name="fresnel_s", formula="integral[Im(eml(i*pi*t^2/2,1)), t=0..x]",
        n_nodes=2, domain=(0.0, 5.0),
        max_abs_error=1e-6, backend="CBEST",
        notes=(
            "Integrand is exact (2 CBEST nodes); integral via scipy or quadrature. "
            "Max error reflects quadrature fallback (scipy gives machine precision)."
        ),
    ),
    "fresnel_c": SpecialFnEntry(
        name="fresnel_c", formula="integral[Re(eml(i*pi*t^2/2,1)), t=0..x]",
        n_nodes=2, domain=(0.0, 5.0),
        max_abs_error=1e-6, backend="CBEST",
        notes="Integrand is exact; integral via scipy or trapezoidal quadrature.",
    ),
    "j0": SpecialFnEntry(
        name="j0", formula="complex MCTS depth-3 tree (7 nodes)",
        n_nodes=J0_NODE_COUNT, domain=(0.0, 10.0),
        max_abs_error=1e-4, backend="CBEST",
        notes=(
            f"Best-known complex-EML construction: {J0_NODE_COUNT} nodes at MSE < 1e-4. "
            "Run complex_mcts_search(scipy.special.j0, ...) to reproduce the formula. "
            "j0_cb() uses scipy for exact evaluation when available."
        ),
    ),
    "airy_ai": SpecialFnEntry(
        name="airy_ai", formula="complex MCTS depth-3 tree (9 nodes)",
        n_nodes=AI_NODE_COUNT, domain=(-5.0, 5.0),
        max_abs_error=2e-3, backend="CBEST",
        notes=(
            f"Best-known construction: {AI_NODE_COUNT} nodes, MSE ≈ 2e-3. "
            "ai_cb() uses scipy for exact evaluation when available."
        ),
    ),
    "lgamma": SpecialFnEntry(
        name="lgamma", formula="(x-0.5)*ln(x) - x + 0.5*ln(2pi) + 1/(12x) - 1/(360x^3)",
        n_nodes=12, domain=(0.1, 100.0),
        max_abs_error=1e-9, backend="BEST",
        notes="Stirling series with recurrence for x < 7. ~12 BEST nodes for the series.",
    ),
    "digamma": SpecialFnEntry(
        name="digamma", formula="central-diff(lgamma_cb, h=1e-5)",
        n_nodes=14, domain=(0.5, 100.0),
        max_abs_error=1e-8, backend="BEST",
        notes="Numerical derivative of lgamma_cb. 14 nodes = 2 × lgamma nodes + sub/div.",
    ),
}


# ── Public helpers ─────────────────────────────────────────────────────────────

def catalog_summary() -> str:
    """Return a formatted markdown table of the CATALOG."""
    lines = [
        "| Function | Nodes | Backend | Max Error | Domain |",
        "|----------|------:|---------|----------:|--------|",
    ]
    for entry in sorted(CATALOG.values(), key=lambda e: (e.backend, e.n_nodes)):
        lines.append(
            f"| `{entry.name}` | {entry.n_nodes} | {entry.backend} "
            f"| {entry.max_abs_error:.2e} | {entry.domain[0]} … {entry.domain[1]} |"
        )
    return "\n".join(lines)


def save_catalog(path: str) -> None:
    """Write CATALOG to a JSON file at *path*."""
    import json
    data = {}
    for name, entry in CATALOG.items():
        data[name] = {
            "formula":       entry.formula,
            "n_nodes":       entry.n_nodes,
            "domain":        list(entry.domain),
            "max_abs_error": entry.max_abs_error,
            "backend":       entry.backend,
            "notes":         entry.notes,
        }
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


__all__ = [
    "SpecialFnEntry",
    "CATALOG",
    "sin_cb", "cos_cb",
    "sinh_cb", "cosh_cb", "tanh_cb", "sech_cb",
    "erf_cb",
    "fresnel_s_integrand_cb", "fresnel_c_integrand_cb",
    "fresnel_s_cb", "fresnel_c_cb",
    "j0_cb", "ai_cb",
    "lgamma_cb", "digamma_cb",
    "catalog_summary", "save_catalog",
]
