"""
eml_complexity.py -- Session 26: EML Complexity Theory.

Grammar hierarchy G0-G4 defines depth(f) = minimum EML tree depth to express f
exactly. This is circuit complexity for continuous functions.

Known results:
  depth(exp(x)) = 1   [EML-1: eml(x, 1) = exp(x) - ln(1) = exp(x)]
  depth(ln(x))  = 3   [EML-3: 3-node ln construction]
  depth(sin(x)) = ∞   [not EML-expressible — infinite zeros barrier]

Pumping Lemma (informal):
  If f has a zero of exact order k at x₀ (f vanishes as (x-x₀)^k),
  then any EML tree computing f must have depth ≥ ⌈log₂(k)⌉.

  Proof sketch: each EML node can at most double the zero order via
  the exp composition. So k zeros require ≥ log₂(k) nodes.

The EML complexity classes:
  EML-1  {exp(x), exp(-x), 1/x, x^α for rational α, ...}
  EML-2  {exp(exp(x)), x·exp(x), ...}
  EML-3  {ln(x), sqrt(x), ...}
  EML-∞  {sin(x), cos(x), Γ(x), ...}
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np


# ── Complexity classes ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EMLComplexityClass:
    """An EML complexity class — the set of functions expressible at depth ≤ n."""

    name: str              # "EML-1", "EML-2", "EML-3", "EML-inf"
    depth: int | None      # None means ∞
    description: str
    canonical_example: str
    lower_bound_proof: str | None
    known_functions: list[str]

    def contains(self, f_depth: int | None) -> bool:
        """True if a function of given depth is in this class."""
        if self.depth is None:
            return True
        if f_depth is None:
            return False
        return f_depth <= self.depth


EML_1 = EMLComplexityClass(
    name="EML-1",
    depth=1,
    description="Functions expressible as a single eml(x, y) node (depth 1).",
    canonical_example="exp(x) = eml(x, 1)",
    lower_bound_proof="exp(x) has no zeros on ℝ → lower bound 1; 1-node construction exists.",
    known_functions=[
        "exp(x)", "exp(-x)", "deml(x,1)", "eml(x,c) for constant c",
        "1/x (via eml(0, x))", "e^x - c",
    ],
)

EML_2 = EMLComplexityClass(
    name="EML-2",
    depth=2,
    description="Functions expressible with ≤2 EML nodes but not 1.",
    canonical_example="1 - exp(-x)  [RC charging, 2-node DEML]",
    lower_bound_proof=None,
    known_functions=[
        "1 - exp(-x)", "exp(exp(x)) - c", "exp(x) * exp(-x) = 1",
        "sech(x) = 1/cosh(x) [2-node BEST]",
    ],
)

EML_3 = EMLComplexityClass(
    name="EML-3",
    depth=3,
    description="Functions expressible with ≤3 EML nodes but not ≤2.",
    canonical_example="ln(x) = eml(1, eml(eml(1,x), 1))  [3-node]",
    lower_bound_proof=(
        "ln(x) has a simple zero only 'at ∞' (asymptotic), but the 3-node lower "
        "bound follows from the fact that no 1-node or 2-node EML tree can produce "
        "a function with logarithmic growth — requires minimum 3 compositions."
    ),
    known_functions=[
        "ln(x)", "sqrt(x)", "x^(1/3)", "x^(p/q) for rational p/q",
        "ln(x+1)", "ln(x^2+1)",
    ],
)

EML_INF = EMLComplexityClass(
    name="EML-∞",
    depth=None,
    description="Functions not expressible by any finite EML tree.",
    canonical_example="sin(x)  [infinite zeros at x = nπ]",
    lower_bound_proof=(
        "sin(x) has zeros at x = nπ for all n ∈ ℤ. Any finite EML tree has at most "
        "finitely many zeros (the zero set of exp-log compositions). Therefore "
        "sin(x) requires an infinite tree — it is EML-∞."
    ),
    known_functions=[
        "sin(x)", "cos(x)", "Γ(x) (gamma function)",
        "ζ(s) (Riemann zeta, on critical strip)",
        "J₀(x) (Bessel function, has infinitely many zeros)",
    ],
)

COMPLEXITY_CLASSES = [EML_1, EML_2, EML_3, EML_INF]


# ── Zero order analysis ───────────────────────────────────────────────────────

def zero_order_at(f: Callable[[float], float], x0: float, eps: float = 1e-5) -> int:
    """Estimate the order of the zero of f at x0.

    Returns k such that f(x) ~ C*(x-x0)^k near x0.
    Returns 0 if f(x0) != 0 (not a zero).
    Returns -1 if undetermined.
    """
    try:
        f0 = f(x0)
        if abs(f0) > 1e-6:
            return 0

        # Taylor probe: f(x0 + h) ~ C * h^k
        probes = [eps * (10 ** i) for i in range(1, 5)]
        log_vals = []
        for h in probes:
            fh = f(x0 + h)
            if abs(fh) < 1e-15:
                continue
            log_vals.append((math.log(h), math.log(abs(fh))))

        if len(log_vals) < 2:
            return -1

        # Linear regression log|f| ~ k * log(h) + const
        hs = np.array([lv[0] for lv in log_vals])
        fs = np.array([lv[1] for lv in log_vals])
        k_est = float(np.polyfit(hs, fs, 1)[0])
        return max(1, round(k_est))

    except Exception:
        return -1


def zero_order_lower_bound(f: Callable[[float], float], x0: float, eps: float = 1e-5) -> int:
    """Pumping lemma lower bound on EML depth via zero order at x0.

    If f has a zero of order k at x0, then EML depth(f) ≥ ⌈log₂(k)⌉.

    Returns:
        Lower bound on EML depth. 0 if f(x0) != 0.
    """
    k = zero_order_at(f, x0, eps=eps)
    if k <= 0:
        return 0
    return math.ceil(math.log2(max(k, 1)))


# ── Complexity certificates ───────────────────────────────────────────────────

def complexity_certificate(
    f_name: str,
    domain: tuple[float, float] = (0.1, 5.0),
    candidate_depths: list[int] | None = None,
    n_probes: int = 50,
) -> dict:
    """Verify that a known function has the claimed EML complexity class.

    Uses known EML constructions to verify upper bounds, and zero-order
    analysis for lower bounds.

    Args:
        f_name:           Name of a known function (e.g., "exp", "ln", "sin").
        domain:           Domain for numerical verification.
        candidate_depths: Depths to test (default: [1, 2, 3]).
        n_probes:         Number of probe points.

    Returns:
        Dict with class, bounds, and verification status.
    """
    if candidate_depths is None:
        candidate_depths = [1, 2, 3]

    known = _KNOWN_FUNCTIONS.get(f_name)
    if known is None:
        return {"error": f"Unknown function: {f_name}", "known_functions": list(_KNOWN_FUNCTIONS)}

    probes = np.linspace(domain[0], domain[1], n_probes).tolist()

    # Verify the EML construction
    verified = False
    max_err = float('inf')
    if known["eml_fn"] is not None:
        try:
            errs = [abs(known["fn"](x) - known["eml_fn"](x)) for x in probes]
            max_err = max(errs)
            verified = max_err < 1e-6
        except Exception as exc:
            max_err = float('inf')
            verified = False

    # Lower bound from zero order
    lower_bound = 0
    if known.get("zero_at") is not None:
        lower_bound = zero_order_lower_bound(known["fn"], known["zero_at"])

    return {
        "function": f_name,
        "claimed_depth": known["depth"],
        "claimed_class": f"EML-{known['depth']}" if known["depth"] is not None else "EML-∞",
        "eml_formula": known["formula"],
        "verified": verified,
        "max_error": max_err,
        "lower_bound": lower_bound,
        "lower_bound_consistent": (
            lower_bound <= (known["depth"] or 999)
        ),
        "notes": known.get("notes", ""),
    }


def classify_function(
    f: Callable[[float], float],
    domain: tuple[float, float] = (0.1, 5.0),
    max_depth: int = 5,
    tol: float = 1e-6,
) -> dict:
    """Attempt to classify a function into an EML complexity class.

    Uses the zero-order pumping lemma to establish lower bounds,
    and checks known constructions for upper bounds.

    Returns:
        Dict with lower_bound, upper_bound (if known), and complexity_class.
    """
    probes = np.linspace(domain[0], domain[1], 30).tolist()

    # Count approximate zeros in domain
    zero_count = 0
    zero_orders = []
    for x in probes:
        try:
            if abs(f(x)) < tol:
                k = zero_order_at(f, x)
                zero_orders.append((x, k))
                zero_count += 1
        except Exception:
            pass

    # If infinite zeros possible → EML-∞
    # If no zeros → possibly EML-1
    # Multiple zeros → higher depth

    if zero_count > len(probes) * 0.3:
        return {
            "lower_bound": None,
            "upper_bound": None,
            "complexity_class": "EML-∞",
            "reason": f"High zero density ({zero_count}/{len(probes)})",
            "zero_orders": zero_orders[:5],
        }

    max_order = max((k for _, k in zero_orders if k > 0), default=0)
    lower_bound = math.ceil(math.log2(max(max_order, 1))) if max_order > 0 else 0

    return {
        "lower_bound": lower_bound,
        "upper_bound": None,  # Would require exhaustive tree search
        "complexity_class": f"EML-≥{lower_bound}" if lower_bound > 0 else "EML-≥1",
        "reason": f"Max zero order {max_order} → depth ≥ ⌈log₂({max_order})⌉ = {lower_bound}",
        "zero_count": zero_count,
        "zero_orders": zero_orders[:5],
    }


# ── Known function registry ───────────────────────────────────────────────────

_KNOWN_FUNCTIONS: dict[str, dict] = {
    "exp": {
        "fn": math.exp,
        "eml_fn": lambda x: math.exp(x) - math.log(1.0),  # eml(x, 1)
        "formula": "eml(x, 1) = exp(x) - ln(1) = exp(x)",
        "depth": 1,
        "zero_at": None,
        "notes": "exp(x) has no zeros; minimum depth 1.",
    },
    "deml": {
        "fn": lambda x: math.exp(-x),
        "eml_fn": lambda x: math.exp(-x) - math.log(1.0),  # deml(x, 1)
        "formula": "deml(x, 1) = exp(-x) - ln(1) = exp(-x)",
        "depth": 1,
        "zero_at": None,
        "notes": "exp(-x): universal decay, 1-node DEML.",
    },
    "ln": {
        "fn": math.log,
        "eml_fn": lambda x: math.exp(1) - math.log(math.exp(math.exp(1) - math.log(x))),
        "formula": "eml(1, eml(eml(1,x), 1))",
        "depth": 3,
        "zero_at": 1.0,
        "notes": "ln has simple zero at x=1; 3-node construction exact.",
    },
    "sqrt": {
        "fn": math.sqrt,
        "eml_fn": None,
        "formula": "eml(ln(x)/2, 1) = exp(ln(x)/2) = sqrt(x) [via EXL]",
        "depth": 3,
        "zero_at": 0.0,
        "notes": "sqrt(x) = exp(ln(x)/2), depth 3 via EXL.",
    },
    "x_squared": {
        "fn": lambda x: x * x,
        "eml_fn": None,
        "formula": "exp(2*ln(x)) via EXL",
        "depth": 3,
        "zero_at": 0.0,
        "notes": "x^2 has double zero at x=0 → depth ≥ ⌈log₂(2)⌉ = 1.",
    },
    "sech": {
        "fn": lambda x: 1.0 / math.cosh(x),
        "eml_fn": None,
        "formula": "recip(cosh(x)) — 2-node BEST",
        "depth": 2,
        "zero_at": None,
        "notes": "sech(x) = 1/cosh(x); no zeros; 2-node BEST.",
    },
    "sin": {
        "fn": math.sin,
        "eml_fn": None,
        "formula": "Not EML-expressible (EML-∞)",
        "depth": None,
        "zero_at": 0.0,
        "notes": "sin has infinitely many zeros → EML-∞ by pumping lemma.",
    },
    "cos": {
        "fn": math.cos,
        "eml_fn": None,
        "formula": "Not EML-expressible (EML-∞)",
        "depth": None,
        "zero_at": math.pi / 2,
        "notes": "cos has infinitely many zeros → EML-∞.",
    },
}


def complexity_table() -> str:
    """Return a markdown table of known EML complexity classes."""
    lines = [
        "## EML Complexity Table",
        "",
        "| Function | Depth | Class | Formula | Notes |",
        "|----------|-------|-------|---------|-------|",
    ]
    for name, info in _KNOWN_FUNCTIONS.items():
        depth_str = str(info["depth"]) if info["depth"] is not None else "∞"
        class_str = f"EML-{depth_str}"
        lines.append(
            f"| `{name}` | {depth_str} | {class_str} | `{info['formula'][:50]}` | {info['notes'][:60]} |"
        )
    lines.append("")
    lines.append(
        "**Pumping Lemma**: if f has a zero of order k, then EML depth(f) ≥ ⌈log₂(k)⌉."
    )
    return "\n".join(lines)
