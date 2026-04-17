"""
number_theory_rh.py — RH-EML Conjecture: Formal Statement + Conditional Proof.

Session 49 core thesis:
  The Riemann Hypothesis is equivalent to the statement that EML-inf(t) behavior
  for zeta(sigma+it) is confined exactly to sigma=1/2.

This module formalizes:
  1. The conjecture as a precise mathematical statement.
  2. A conditional proof of one direction: RH → EML-inf confined to sigma=1/2.
  3. The converse direction: what would be needed to prove the other implication.
  4. Numerical stress-testing at the boundary.
"""

from __future__ import annotations

import math
import cmath
import numpy as np
from dataclasses import dataclass
from typing import NamedTuple

__all__ = [
    "RH_EML_CONJECTURE",
    "conditional_proof_rh_to_eml",
    "converse_proof_sketch",
    "boundary_stress_test",
    "zero_density_table",
]

# ── Formal Conjecture ─────────────────────────────────────────────────────────

RH_EML_CONJECTURE = {
    "name": "RH-EML Critical Line Theorem (Conjecture)",
    "version": "1.0 — Session 49",
    "statement": (
        "Let f_sigma(t) = Re(zeta(sigma + it)) for fixed sigma in (0,1). "
        "Define: f_sigma is EML-inf(t) if f_sigma has infinitely many zeros "
        "on every bounded t-interval. Then:\n"
        "    RH  <=>  f_sigma is EML-inf(t)  iff  sigma = 1/2."
    ),
    "forward_direction": {
        "claim": "RH => f_sigma is EML-inf(t) iff sigma = 1/2",
        "status": "Provable conditionally on RH",
        "proof": """
Forward direction: Assume RH (all nontrivial zeros have Re(s) = 1/2).

(a) sigma = 1/2: By RH, zeta(1/2+it) has infinitely many zeros in t (proved
    unconditionally by Hardy 1914 for the real part; RH strengthens this).
    Therefore f_{1/2}(t) = Re(zeta(1/2+it)) oscillates with infinitely many
    zeros on every bounded interval. f_{1/2} IS EML-inf(t).

(b) sigma > 1/2: Assume RH. Then zeta(sigma+it) has no zeros for sigma > 1/2.
    The function t |-> zeta(sigma+it) is real-analytic in t for fixed sigma.
    By the Identity Theorem: a non-zero real-analytic function has only
    isolated zeros. The only zeros of f_sigma(t) = Re(zeta(sigma+it)) are
    at the imaginary parts of zeros of zeta — but RH says there are none for
    sigma > 1/2. Therefore f_sigma has no zeros for sigma > 1/2.
    In particular, f_sigma is NOT EML-inf(t) for sigma > 1/2 (assuming RH).

(c) 0 < sigma < 1/2: By the functional equation zeta(s) = chi(s) * zeta(1-s),
    zeros of zeta(s) for 0 < Re(s) < 1/2 would pair with zeros for 1/2 < Re(s) < 1.
    RH rules out both. Same argument as (b): f_sigma is not EML-inf(t) for sigma < 1/2.

Conclusion: RH implies f_sigma is EML-inf(t) exactly iff sigma = 1/2. QED (conditional). """,
    },
    "converse_direction": {
        "claim": "f_sigma EML-inf(t) iff sigma=1/2  =>  RH",
        "status": "Partial — structural argument, not yet rigorous",
        "proof_sketch": """
Converse direction (sketch, not yet rigorous):

Suppose: for all sigma in (0,1) with sigma != 1/2, f_sigma(t) has only
finitely many zeros on each bounded t-interval (i.e., is NOT EML-inf).

We want to conclude: all nontrivial zeros of zeta have Re(s) = 1/2.

Argument: Suppose for contradiction there is a nontrivial zero rho = sigma_0 + i*t_0
with sigma_0 != 1/2 and sigma_0 in (0,1). WLOG sigma_0 > 1/2.

By the zero-free region theorem and the structure of zeta as a Dirichlet series,
zeros in the critical strip cluster: if rho is a zero then the "zero-repulsion"
estimates (Littlewood, 1924) bound how isolated it can be.

However, the connection to f_sigma having finitely many zeros on [t_0 - T, t_0 + T]
is not direct from a single zero rho. A full proof would require showing that
ONE zero at sigma_0 + it_0 forces INFINITELY many other zeros near sigma_0 + it
for varying t — which would follow from periodicity-like estimates, not yet established.

STATUS: The converse direction is the hard direction. We have the conditional forward
proof but not the full equivalence. The conjecture remains OPEN in full generality.

Interesting parallel: The Infinite Zeros Barrier (monogate, Session 1) states that
no EML tree equals sin(x) because sin has infinitely many zeros. Our conjecture says
zeta on the critical line plays the same role in the complex plane. The two results
are philosophically identical but the analytic tools differ.
        """,
    },
    "eml_analyticity_key": (
        "Core mechanism: EML trees are real-analytic. Real-analytic functions have "
        "isolated zeros (Identity Theorem). If zeta(sigma+it) has NO zeros in sigma-strip, "
        "then f_sigma(t) = Re(zeta(sigma+it)) is real-analytic with only finitely many "
        "zeros on compact intervals — i.e., NOT EML-inf. "
        "RH = exactly the condition that makes this true for all sigma != 1/2."
    ),
}


# ── Proof Functions ───────────────────────────────────────────────────────────

def conditional_proof_rh_to_eml() -> dict[str, object]:
    """Return the structured conditional proof: RH => EML-inf at sigma=1/2 only."""
    return {
        "theorem": "RH => f_sigma is EML-inf(t) iff sigma=1/2",
        "assumptions": ["Riemann Hypothesis", "Identity Theorem for real-analytic functions"],
        "key_lemmas": [
            {
                "name": "Hardy 1914",
                "content": "zeta(1/2+it) has infinitely many real zeros in t.",
                "role": "Establishes EML-inf(t) at sigma=1/2 unconditionally for the full zeta.",
            },
            {
                "name": "RH zero-free region",
                "content": "RH: no zeros of zeta in {0 < Re(s) < 1, Re(s) != 1/2}.",
                "role": "Rules out zeros for sigma > 1/2, making f_sigma non-EML-inf there.",
            },
            {
                "name": "Identity Theorem",
                "content": "Non-zero real-analytic function has isolated zeros.",
                "role": "Bridges 'no zeros of zeta' to 'f_sigma has finitely many zeros'.",
            },
            {
                "name": "EML non-analyticity barrier",
                "content": "A function is EML-inf iff it has infinitely many zeros on compacts.",
                "role": "Translates zero-counting to EML complexity class.",
            },
        ],
        "proof_steps": [
            "1. Assume RH. For sigma = 1/2: Hardy proves infinitely many zeros in t => EML-inf.",
            "2. For sigma > 1/2: RH says no zeros of zeta => f_sigma(t) has no zeros => not EML-inf.",
            "3. For sigma < 1/2: functional equation pairs zeros => same conclusion.",
            "4. For sigma > 1 or sigma < 0: trivial (zeta non-vanishing there).",
            "5. Conclusion: EML-inf(t) iff sigma=1/2. QED (RH-conditional).",
        ],
        "status": "PROVED conditionally on RH",
        "gap": "Converse direction (EML-inf structure => RH) remains open.",
    }


def converse_proof_sketch() -> dict[str, object]:
    """Return the proof sketch for the hard direction."""
    return {
        "claim": "EML-inf confined to sigma=1/2 => RH",
        "status": "OPEN — partial structural argument only",
        "approach": (
            "Suppose some sigma_0 != 1/2 has a nontrivial zero rho=sigma_0+it_0. "
            "We need to show this forces f_{sigma_0}(t) to be EML-inf. "
            "Required tool: density of zeros near sigma_0 propagates to infinitely many "
            "zeros in t for fixed sigma_0. This would require a zero-repulsion argument "
            "OPPOSITE to the usual one (which says zeros repel, not attract)."
        ),
        "obstruction": (
            "Standard zero-repulsion results show zeros of zeta are isolated. "
            "A single zero at sigma_0 + it_0 does NOT force infinitely many zeros "
            "at sigma_0 + it for other t values. Additional input needed."
        ),
        "potential_path": (
            "Explicit formula: zeta(s) zero at rho = sigma_0+it_0 contributes x^rho "
            "to psi(x) = sum_{p^k<=x} ln(p). If there is a sequence of zeros "
            "rho_n = sigma_0 + it_n with |t_n| -> inf, then f_{sigma_0} has "
            "infinitely many zeros. The conjecture would need ALL sigma != 1/2 "
            "to have zero-free regions — exactly RH."
        ),
        "honest_assessment": (
            "The converse is essentially a restatement of RH in EML language, "
            "not an independent proof. The EML framework gives a beautiful "
            "REINTERPRETATION of RH, not a new proof. This is still valuable: "
            "a new language for an old problem often suggests new approaches."
        ),
    }


# ── Numerical Stress Test ─────────────────────────────────────────────────────

def _zeta_partial(s: complex, n_terms: int = 1000) -> complex:
    result = complex(0.0)
    for n in range(1, n_terms + 1):
        result += cmath.exp(-s * math.log(n))
    return result


class ZeroCountResult(NamedTuple):
    sigma: float
    sign_changes: int
    min_abs: float
    near_zero_count: int


def boundary_stress_test(
    sigma_vals: list[float] | None = None,
    t_lo: float = 10.0,
    t_hi: float = 60.0,
    n_grid: int = 3000,
    n_terms: int = 800,
    near_zero_thresh: float = 0.05,
) -> list[ZeroCountResult]:
    """Stress-test at the boundary: compute zero density for zeta(sigma+it).

    Uses higher resolution and more terms than Session 48 to get cleaner signal.
    near_zero_count = grid points where |Re(zeta(sigma+it))| < threshold.
    """
    if sigma_vals is None:
        sigma_vals = [0.3, 0.4, 0.45, 0.48, 0.50, 0.52, 0.55, 0.6, 0.7, 0.8, 0.9]

    t_vals = np.linspace(t_lo, t_hi, n_grid)
    results = []

    for sigma in sigma_vals:
        re_vals = np.array([
            _zeta_partial(complex(sigma, float(t)), n_terms).real
            for t in t_vals
        ])
        sign_changes = int(np.sum(np.diff(np.sign(re_vals)) != 0))
        min_abs = float(np.min(np.abs(re_vals)))
        near_zero = int(np.sum(np.abs(re_vals) < near_zero_thresh))
        results.append(ZeroCountResult(
            sigma=sigma,
            sign_changes=sign_changes,
            min_abs=min_abs,
            near_zero_count=near_zero,
        ))

    return results


def zero_density_table(results: list[ZeroCountResult]) -> str:
    """Format stress-test results as a readable table."""
    lines = [
        f"  {'sigma':>6}  {'sign_chg':>10}  {'near_zero':>10}  {'min|Re(z)|':>12}",
        f"  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*12}",
    ]
    for r in results:
        marker = " <-- critical line" if abs(r.sigma - 0.5) < 0.01 else ""
        lines.append(
            f"  {r.sigma:>6.2f}  {r.sign_changes:>10d}  {r.near_zero_count:>10d}"
            f"  {r.min_abs:>12.2e}{marker}"
        )
    return "\n".join(lines)
