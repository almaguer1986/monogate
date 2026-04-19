"""Session 24 — Gamma Function in Complex EML.

Analyzes the EML depth of Γ(z).

Key results:
- Exact Γ(z): EML-∞ (integral/infinite product, no finite ceml tree)
- Stirling approximation: EML-2 over ℂ
- Log-Gamma via Stirling: EML-2
- Integer factorials n! = Γ(n+1): EML-∞ exactly, but approximated at EML-2
"""

import cmath
import math
from typing import Dict, List

__all__ = ["run_session24"]


GAMMA_CLASSIFICATION = {
    "Gamma(z) exact": {
        "depth": "∞",
        "definitions": [
            "Integral: Γ(z) = ∫_0^∞ t^{z-1} e^{-t} dt — integral of EML-finite integrand",
            "Product: Γ(z) = lim_{n→∞} n! n^z / (z(z+1)···(z+n)) — infinite product",
            "Recurrence: Γ(z+1) = z·Γ(z) — recursive, not finite",
        ],
        "reason": "No finite composition of exp and Log reproduces Γ",
    },
    "Stirling approx ln(Γ(z))": {
        "depth": 2,
        "formula": "(z-1/2)*ln(z) - z + (1/2)*ln(2π) + 1/(12z) + ...",
        "ceml": "Leading term (z-1/2)*Log(z) - z + const is EML-2",
        "reason": "Log(z) = 1-ceml(0,z) at depth 1; multiply by (z-1/2) and add -z+const → depth 2",
    },
    "n! (exact)": {
        "depth": "∞",
        "reason": "n! = Γ(n+1); same as Γ",
    },
    "log(n!) via Stirling": {
        "depth": 2,
        "formula": "n*ln(n) - n + 0.5*ln(2πn)",
        "ceml": "(1-ceml(0,n))*n - n + 0.5*(1-ceml(0,2*pi*n)) ... arithmetic on ceml(0,·)",
        "reason": "Two Log evaluations = two depth-1 ceml ops; total depth 2",
    },
}


def stirling_log_gamma(z: complex, terms: int = 5) -> complex:
    """Stirling's approximation: ln(Γ(z)) ≈ (z-1/2)*ln(z) - z + (1/2)*ln(2π) + Σ B_{2k}/(2k(2k-1)z^{2k-1})"""
    # Bernoulli coefficients for first few terms
    bernoulli = [1/12, -1/360, 1/1260, -1/1680, 1/1188]
    result = ((z - 0.5) * cmath.log(z) - z + 0.5 * cmath.log(2 * math.pi))
    for k, b in enumerate(bernoulli[:terms], 1):
        result += b / z**(2*k - 1)
    return result


def verify_stirling() -> List[Dict]:
    results = []
    for z_real in [5, 10, 20, 50, 100]:
        z = complex(z_real)
        stirling_val = stirling_log_gamma(z).real
        exact_val = math.lgamma(z_real)
        err = abs(stirling_val - exact_val)
        results.append({
            "z": z_real,
            "stirling": stirling_val,
            "exact_lgamma": exact_val,
            "err": err,
            "relative_err": err / abs(exact_val) if exact_val != 0 else None,
            "ok": err < 0.01 * abs(exact_val),
        })
    return results


def stirling_as_ceml() -> Dict:
    """Express Stirling's leading terms in ceml arithmetic form."""
    # ln(Γ(n)) ≈ (n-0.5)*Log(n) - n + 0.5*Log(2π)
    # Log(n) = 1 - ceml(0, n)
    # So: (n-0.5)*(1-ceml(0,n)) - n + 0.5*(1-ceml(0,2π))
    # = (n-0.5) - (n-0.5)*ceml(0,n) - n + 0.5 - 0.5*ceml(0,2π)
    # = -0.5*ceml(0,n) - 0.5*ceml(0,2π) + [constant terms]
    # = arithmetic combination of two depth-1 ceml nodes → depth 2
    return {
        "formula": "ln(Gamma(n)) approx (n-0.5)*(1-ceml(0,n)) - n + 0.5*(1-ceml(0,2*pi))",
        "ceml_nodes": 2,
        "depth": 2,
        "note": "Two independent ceml(0,·) applications; combined arithmetically",
        "verification": {
            "n=10": {
                "ceml_form": (10-0.5)*(1-cmath.log(10).real) - 10 + 0.5*(1-math.log(2*math.pi)),
                "exact_lgamma": math.lgamma(10),
            }
        },
    }


def gamma_integer_values() -> List[Dict]:
    """n! = Γ(n+1) for small n — exact (not EML-finite, but verifiable)."""
    results = []
    for n in range(1, 10):
        exact = math.factorial(n)
        gamma_val = math.gamma(n + 1)
        results.append({
            "n": n,
            "n_factorial": exact,
            "gamma_n+1": gamma_val,
            "match": abs(exact - gamma_val) < 0.5,
        })
    return results


def run_session24() -> Dict:
    stirling = verify_stirling()
    stirling_ok = all(r["ok"] for r in stirling)
    ceml_form = stirling_as_ceml()
    integers = gamma_integer_values()

    # Verify ceml form for n=10
    n = 10
    ceml_val = (n-0.5)*(1-math.log(n)) - n + 0.5*(1-math.log(2*math.pi))
    exact_lgamma_10 = math.lgamma(10)
    ceml_form["verification"]["n=10"]["err"] = abs(ceml_val - exact_lgamma_10)

    theorems = [
        "CEML-T23: Γ(z) exact is EML-∞ (integral/product definition, not finite ceml)",
        "CEML-T24: ln(Γ(z)) Stirling approximation is EML-2 (two Log evaluations)",
        "CEML-T25: Stirling's formula ceml form: 2 nodes, each depth 1",
        "CEML-T26: n! is EML-∞ exactly; EML-2 via Stirling for large n",
    ]

    return {
        "session": 24,
        "title": "Gamma Function in Complex EML",
        "classification": GAMMA_CLASSIFICATION,
        "stirling_verification": stirling,
        "stirling_all_ok": stirling_ok,
        "stirling_as_ceml": ceml_form,
        "gamma_integers": integers,
        "theorems": theorems,
        "key_finding": (
            "Γ(z) is EML-∞ (requires infinite processes). "
            "Stirling's approximation reduces to EML-2 (two Log applications). "
            "The lesson: asymptotic/approximate forms often have finite EML depth while exact forms do not."
        ),
        "status": "PASS" if stirling_ok else "PARTIAL",
    }
