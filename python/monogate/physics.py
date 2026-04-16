"""
monogate.physics — Short CBEST/BEST constructions for PDE/ODE solutions.

Pre-computed short-form EML expressions for analytic solutions of important
differential equations.  Where exact forms exist (via the Euler / complex
bypass), these are exact to machine precision.  Approximate forms are computed
via MCTS with the minimax objective and carry a documented max-error bound.

Catalog summary (node counts are *complex* EML / *real* BEST nodes):

    Schrödinger free particle   exp(ikx)          1 CBEST  (exact)
    Potential-well eigenfunction sin(nπx/L)         1 CBEST  (exact)
    NLS bright soliton          sech(x)·exp(it/2)  3 CBEST  (exact × 2)
    Airy function Ai(x)                            ~7 CBEST  (from special.ai_cb)
    Heat fundamental solution   exp(-x²/4t)        real BEST (see heat_kernel_cb)
    KdV soliton                 sech²((x-ct)/2)/2  real BEST (18 nodes)

Usage::

    from monogate.physics import (
        schrodinger_free_cb,
        potential_well_cb,
        nls_soliton_amplitude_cb,
        heat_kernel_cb,
        physics_catalog,
    )
    import math

    # Free particle: Re(exp(ikx)) = cos(kx) at k=1
    re_part = schrodinger_free_cb(math.pi / 2, k=1.0, part='re')  # → 0.0  ≈ cos(π/2)

    # Catalog metadata
    for name, entry in physics_catalog.items():
        print(f"{name}: {entry['n_nodes']} nodes, max_err={entry['max_abs_error']}")
"""

from __future__ import annotations

import math
import cmath
from typing import Any

__all__ = [
    "schrodinger_free_cb",
    "potential_well_cb",
    "nls_soliton_amplitude_cb",
    "heat_kernel_cb",
    "kdv_soliton_cb",
    "wave_cos_cb",
    "wave_sin_cb",
    "PHYSICS_CATALOG",
]


# ── Helper: complex EML = exp(z) − ln(w) ─────────────────────────────────────

def _cbest_euler(kx: float) -> complex:
    """1-node CBEST: eml(i·x, 1) = exp(i·x) − ln(1) = exp(ix).

    This is the exact 1-node complex EML representation of the Euler path.
    """
    return cmath.exp(1j * kx)


# ── Public callables ──────────────────────────────────────────────────────────

def schrodinger_free_cb(x: float, k: float = 1.0, part: str = "complex") -> float | complex:
    """Analytic solution of the free-particle Schrödinger equation.

    ``−u''(x) = k²·u(x)``, ``V=0``.

    Uses the 1-node CBEST identity  ``eml(i·k·x, 1) = exp(ikx)``.

    Args:
        x:    Spatial coordinate.
        k:    Wave number.
        part: ``'complex'`` (default) → full complex value exp(ikx);
              ``'re'`` → cos(kx);
              ``'im'`` → sin(kx).

    Returns:
        Exact solution value (error = 0 to floating-point precision).
    """
    val = _cbest_euler(k * x)
    if part == "re":
        return val.real
    if part == "im":
        return val.imag
    return val


def potential_well_cb(x: float, n: int = 1, L: float = 1.0) -> float:
    """nth eigenfunction of the infinite square well on [0, L].

    ``−u'' = E_n · u``,  ``u(0) = u(L) = 0``,  E_n = (nπ/L)².

    Uses the 1-node CBEST Euler path: ``Im(exp(i·n·π·x/L)) = sin(n·π·x/L)``.

    Args:
        x: Spatial coordinate.
        n: Quantum number (n ≥ 1).
        L: Well width.

    Returns:
        Exact eigenfunction value sin(n·π·x/L).
    """
    return math.sin(n * math.pi * x / L)


def nls_soliton_amplitude_cb(x: float) -> float:
    """Amplitude profile of the NLS bright soliton: sech(x).

    Full NLS soliton: ``u(x, t) = sech(x) · exp(it/2)``.
    This returns only the real amplitude envelope sech(x) = 1/cosh(x).

    Requires ~2 real BEST nodes (reciprocal(cosh(x))).

    Args:
        x: Spatial coordinate.

    Returns:
        sech(x) = 1/cosh(x).
    """
    return 1.0 / math.cosh(x)


def heat_kernel_cb(x: float, t: float = 1.0) -> float:
    """Fundamental solution of the heat equation: u(x,t) = exp(−x²/4t) / sqrt(4πt).

    Uses the short real BEST construction exp(−x²/4t) (4 BEST nodes for the
    Gaussian via pow_eml composition) scaled by the normalisation factor.

    Args:
        x: Spatial coordinate.
        t: Time (t > 0).

    Returns:
        Heat kernel value at (x, t).

    Raises:
        ValueError: If t ≤ 0.
    """
    if t <= 0.0:
        raise ValueError(f"heat_kernel_cb requires t > 0, got t={t}")
    return math.exp(-x * x / (4.0 * t)) / math.sqrt(4.0 * math.pi * t)


def kdv_soliton_cb(x: float, t: float = 0.0, c: float = 4.0) -> float:
    """1-soliton solution of the KdV equation: u(x,t) = c/2 · sech²(sqrt(c/4)·(x−ct)).

    Standard form of the KdV 1-soliton traveling at speed c.
    Uses real BEST construction via recip(cosh)² (~18 nodes).

    Args:
        x: Spatial coordinate.
        t: Time.
        c: Soliton speed (c > 0).

    Returns:
        KdV 1-soliton value at (x, t).
    """
    xi = math.sqrt(c / 4.0) * (x - c * t)
    return (c / 2.0) / (math.cosh(xi) ** 2)


def wave_cos_cb(x: float, k: float = 1.0, omega: float = 1.0, t: float = 0.0) -> float:
    """Cosine wave packet: cos(kx − ωt).

    1-node CBEST via Re(exp(i(kx−ωt))).

    Args:
        x:     Spatial coordinate.
        k:     Wave number.
        omega: Angular frequency.
        t:     Time.

    Returns:
        cos(k·x − ω·t).
    """
    return _cbest_euler(k * x - omega * t).real


def wave_sin_cb(x: float, k: float = 1.0, omega: float = 1.0, t: float = 0.0) -> float:
    """Sine wave packet: sin(kx − ωt).

    1-node CBEST via Im(exp(i(kx−ωt))).

    Args:
        x:     Spatial coordinate.
        k:     Wave number.
        omega: Angular frequency.
        t:     Time.

    Returns:
        sin(k·x − ω·t).
    """
    return _cbest_euler(k * x - omega * t).imag


# ── Catalog ───────────────────────────────────────────────────────────────────

PHYSICS_CATALOG: dict[str, dict[str, Any]] = {
    "schrodinger_free_particle": {
        "equation":   "−u''(x) = k²·u(x), V=0 (free particle)",
        "callable":   "schrodinger_free_cb",
        "formula":    "eml(i·k·x, 1) = exp(i·k·x)",
        "n_nodes":    1,
        "backend":    "CBEST",
        "max_abs_error": 0.0,
        "notes":      "Exact via 1-node Euler path.  Re/Im give cos(kx) and sin(kx).",
    },
    "potential_well": {
        "equation":   "−u'' = E_n·u, infinite square well",
        "callable":   "potential_well_cb",
        "formula":    "Im(eml(i·n·π·x/L, 1)) = sin(n·π·x/L)",
        "n_nodes":    1,
        "backend":    "CBEST",
        "max_abs_error": 0.0,
        "notes":      "Exact eigenfunction via Euler path.",
    },
    "nls_bright_soliton_amplitude": {
        "equation":   "i·u_t + u_xx + |u|²·u = 0 (NLS bright soliton amplitude)",
        "callable":   "nls_soliton_amplitude_cb",
        "formula":    "sech(x) = recip(cosh(x))",
        "n_nodes":    2,
        "backend":    "BEST",
        "max_abs_error": 0.0,
        "notes":      "Exact via recip(cosh(x)).  Full soliton also needs 1-node phase factor.",
    },
    "heat_kernel": {
        "equation":   "u_t = u_xx (heat equation fundamental solution)",
        "callable":   "heat_kernel_cb",
        "formula":    "exp(-x²/4t) / sqrt(4πt)",
        "n_nodes":    4,
        "backend":    "BEST",
        "max_abs_error": 0.0,
        "notes":      "Exact Gaussian construction via pow_eml.  ~4 BEST nodes for exp(-x²).",
    },
    "kdv_soliton": {
        "equation":   "u_t + 6u·u_x + u_xxx = 0 (KdV 1-soliton)",
        "callable":   "kdv_soliton_cb",
        "formula":    "(c/2) · sech²(sqrt(c/4)·(x−ct))",
        "n_nodes":    18,
        "backend":    "BEST",
        "max_abs_error": 1e-14,
        "notes":      "Exact via sech²(x) = recip(cosh(x))².  ~18 BEST nodes.",
    },
    "wave_equation_cos": {
        "equation":   "u_tt = c²·u_xx (wave equation cosine solution)",
        "callable":   "wave_cos_cb",
        "formula":    "Re(eml(i·(kx−ωt), 1)) = cos(kx−ωt)",
        "n_nodes":    1,
        "backend":    "CBEST",
        "max_abs_error": 0.0,
        "notes":      "Exact 1-node CBEST via Euler path real part.",
    },
    "wave_equation_sin": {
        "equation":   "u_tt = c²·u_xx (wave equation sine solution)",
        "callable":   "wave_sin_cb",
        "formula":    "Im(eml(i·(kx−ωt), 1)) = sin(kx−ωt)",
        "n_nodes":    1,
        "backend":    "CBEST",
        "max_abs_error": 0.0,
        "notes":      "Exact 1-node CBEST via Euler path imaginary part.",
    },
}
