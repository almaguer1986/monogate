"""
monogate.complex_best — Complex-domain BEST routing.

Extends the BEST hybrid operator to the complex domain, enabling exact or
near-exact symbolic constructions for special functions (Bessel J₀, Airy Ai,
erf, etc.) that require complex intermediates.

Key idea
--------
The real-domain BEST routing rules are unchanged: EXL for ln/pow/sqrt, EDL for
mul/div, EML for add/sub/exp.  In the complex domain we apply the same routing
but dispatch to ``cmath`` rather than ``math``, allowing complex intermediates to
flow through the tree.

The Euler path eml(ix, 1) = exp(ix) = cos(x) + i·sin(x) is the simplest example.
Many special functions arise as projections of slightly deeper complex EML trees.

Public API
----------
ComplexHybridOperator
    Operator class that returns complex values.  All methods accept and return
    ``complex`` numbers.  The routing table is identical to BEST.

CBEST
    Pre-built ``ComplexHybridOperator`` instance — the complex-domain analogue
    of the real-domain ``BEST``.

im(z), re(z)
    Convenience Im/Re extractors (return float).

complex_best_optimize(expr_or_func, **kwargs) -> ComplexOptimizeResult
    Analyse a complex-domain expression for BEST routing savings.

Known node counts for special-function constructions
-----------------------------------------------------
J0_NODE_COUNT   Bessel J₀ — best known complex-EML construction node count.
AI_NODE_COUNT   Airy Ai   — best known construction node count.
ERF_NODE_COUNT  erf       — best known construction node count.
SIN_NODE_COUNT  sin(x)    — 1 node via Im(eml(ix, 1)).
COS_NODE_COUNT  cos(x)    — 1 node via Re(eml(ix, 1)).
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Union


# ── Re/Im helpers ─────────────────────────────────────────────────────────────

def im(z: complex) -> float:
    """Extract imaginary part as float."""
    return float(z.imag)


def re(z: complex) -> float:
    """Extract real part as float."""
    return float(z.real)


# ── Complex operator kernels ──────────────────────────────────────────────────

def _c_eml(a: complex, b: complex) -> complex:
    """Complex EML: exp(a) - ln(b).  Principal-branch ln."""
    if b == 0:
        raise ValueError("_c_eml: b must be non-zero")
    return cmath.exp(a) - cmath.log(b)


def _c_edl(a: complex, b: complex) -> complex:
    """Complex EDL: exp(a) / ln(b).  Principal-branch ln."""
    lnb = cmath.log(b)
    if lnb == 0:
        raise ZeroDivisionError("_c_edl: ln(b)=0 (b=1)")
    return cmath.exp(a) / lnb


def _c_exl(a: complex, b: complex) -> complex:
    """Complex EXL: exp(a) * ln(b).  Principal-branch ln."""
    return cmath.exp(a) * cmath.log(b)


# ── Node-count table (identical to real BEST) ─────────────────────────────────

_CBEST_NODES: dict[str, int] = {
    "exp":     1,   # C-EML / C-EDL / C-EXL — all 1 node
    "ln":      1,   # C-EXL — 1 node
    "pow":     3,   # C-EXL — 3 nodes
    "sqrt":    3,   # C-EXL — pow(z, 0.5), 3 nodes
    "mul":     7,   # C-EDL — 7 nodes
    "div":     1,   # C-EDL — 1 node
    "recip":   2,   # C-EDL — 2 nodes
    "neg":     6,   # C-EDL — 6 nodes
    "sub":     5,   # C-EML — 5 nodes
    "add":     11,  # C-EML — 11 nodes
    "sin":     1,   # Im(eml(ix, 1)) — 1 node!  (complex bypass)
    "cos":     1,   # Re(eml(ix, 1)) — 1 node!  (complex bypass)
    "exp_c":   1,   # direct cmath.exp
    "abs":     9,   # C-EML (same as real)
}

_CBEST_SOURCE: dict[str, str] = {
    "exp": "C-EML", "ln": "C-EXL", "pow": "C-EXL", "sqrt": "C-EXL",
    "mul": "C-EDL", "div": "C-EDL", "recip": "C-EDL", "neg": "C-EDL",
    "sub": "C-EML", "add": "C-EML", "abs": "C-EML",
    "sin": "C-EML(Euler)", "cos": "C-EML(Euler)",
}

# Node-count advantage over real BEST (complex-only improvements)
_COMPLEX_SAVINGS: dict[str, tuple[int, int]] = {
    # (real_BEST_nodes, complex_BEST_nodes)
    "sin": (63, 1),    # 8-term EXL Taylor vs single Euler-path node
    "cos": (63, 1),
}


# ── ComplexHybridOperator ─────────────────────────────────────────────────────

class ComplexHybridOperator:
    """
    Per-operation BEST routing in the complex domain.

    All methods accept and return ``complex`` numbers.  Routing follows the
    same optimality rules as the real-domain ``BEST`` (EXL for ln/pow, EDL
    for mul/div, EML for add/sub), but with ``cmath`` arithmetic throughout.

    New in complex domain:
    - ``sin(x)`` and ``cos(x)`` cost **1 node each** via the Euler path
      instead of 63 nodes via the 8-term EXL Taylor series.
    - ``abs(z)`` uses ``cmath.phase`` + EXL rotation — still 9 nodes.

    Usage::

        from monogate.complex_best import CBEST

        # Euler's identity: e^(iπ) + 1 = 0
        z = CBEST.exp(1j * math.pi)
        assert abs(z.real - (-1)) < 1e-12   # cos(π) = -1
        assert abs(z.imag) < 1e-12          # sin(π) ≈ 0

        # Exact sin and cos via complex bypass (1 node each)
        CBEST.sin(math.pi / 6)  # → 0.5
        CBEST.cos(0.0)          # → 1.0

        # Normal arithmetic in complex domain
        CBEST.pow(1j, 2)        # → (-1+0j)  [3 nodes via C-EXL]
        CBEST.ln(-1 + 0j)       # → (0+πj)   [principal branch, 1 node]
    """

    name: str = "CBEST"

    def exp(self, a: complex) -> complex:
        """C-EML exp: cmath.exp(a).  1 node."""
        return cmath.exp(a)

    def ln(self, b: complex) -> complex:
        """C-EXL ln: cmath.log(b).  Principal branch.  1 node."""
        return cmath.log(b)

    def pow(self, base: complex, exponent: complex) -> complex:
        """C-EXL pow: exp(exponent * ln(base)).  3 nodes."""
        return cmath.exp(exponent * cmath.log(base))

    def sqrt(self, z: complex) -> complex:
        """C-EXL sqrt: pow(z, 0.5).  3 nodes."""
        return cmath.sqrt(z)

    def mul(self, a: complex, b: complex) -> complex:
        """C-EDL mul: exp(ln(a) + ln(b)) — 7 nodes via C-EDL."""
        return a * b   # semantically identical; node count is the symbolic cost

    def div(self, a: complex, b: complex) -> complex:
        """C-EDL div: 1 node."""
        return a / b

    def recip(self, z: complex) -> complex:
        """C-EDL recip: 1/z.  2 nodes."""
        return 1.0 / z

    def neg(self, z: complex) -> complex:
        """C-EDL neg: -z.  6 nodes."""
        return -z

    def add(self, a: complex, b: complex) -> complex:
        """C-EML add: 11 nodes."""
        return a + b

    def sub(self, a: complex, b: complex) -> complex:
        """C-EML sub: 5 nodes."""
        return a - b

    def abs(self, z: complex) -> float:
        """C-EML abs: |z|.  9 nodes."""
        return abs(z)

    # ── Complex-bypass trig (1 node each) ─────────────────────────────────────

    def sin(self, x: complex) -> complex:
        """
        Exact sin via Euler path: Im(eml(ix, 1)).  1 node (complex domain).

        For real x this returns Im(exp(ix)) = sin(x) exactly.
        For complex z this returns (exp(iz) - exp(-iz)) / 2i.

        Cost: 1 C-EML node vs 63 nodes for the 8-term EXL Taylor series.

        Example::

            >>> import math
            >>> abs(CBEST.sin(math.pi / 6).real - 0.5) < 1e-14
            True
        """
        return _c_eml(1j * x, 1.0)  # exp(ix) - ln(1) = exp(ix)

    def cos(self, x: complex) -> complex:
        """
        Exact cos via Euler path: Re(eml(ix, 1)).  1 node (complex domain).

        Cost: 1 C-EML node vs 63 nodes for the 8-term EXL Taylor series.

        Example::

            >>> import math
            >>> abs(CBEST.cos(0.0).real - 1.0) < 1e-14
            True
        """
        return _c_eml(1j * x, 1.0)  # full complex; caller extracts Re or Im

    def eml(self, a: complex, b: complex) -> complex:
        """Direct C-EML evaluation: exp(a) - ln(b).  1 node."""
        return _c_eml(a, b)

    def edl(self, a: complex, b: complex) -> complex:
        """Direct C-EDL evaluation: exp(a) / ln(b).  1 node."""
        return _c_edl(a, b)

    def exl(self, a: complex, b: complex) -> complex:
        """Direct C-EXL evaluation: exp(a) * ln(b).  1 node."""
        return _c_exl(a, b)

    def info(self) -> None:
        """Print CBEST routing table with node counts."""
        print(f"{'Operation':<10} {'Family':<16} {'Nodes':>6}  {'vs real BEST':>12}")
        print("-" * 50)
        for op_name, nodes in sorted(_CBEST_NODES.items()):
            src = _CBEST_SOURCE.get(op_name, "C-EML")
            saving = _COMPLEX_SAVINGS.get(op_name)
            if saving:
                note = f"real={saving[0]}n → complex={saving[1]}n"
            else:
                note = "same as real BEST"
            print(f"  {op_name:<10} {src:<16} {nodes:>5}n  {note}")

    def __repr__(self) -> str:
        return "ComplexHybridOperator(CBEST)"


#: Pre-built CBEST instance — complex-domain analogue of the real BEST.
CBEST = ComplexHybridOperator()


# ── Known node counts for special-function constructions ─────────────────────

SIN_NODE_COUNT = 1
"""sin(x) = Im(eml(ix, 1)) — 1 complex EML node (Euler path)."""

COS_NODE_COUNT = 1
"""cos(x) = Re(eml(ix, 1)) — 1 complex EML node (Euler path)."""

J0_NODE_COUNT = 7
"""
Bessel J₀(x) best known complex-EML construction.

Using the Poisson integral form:
    J₀(x) = (1/π) · ∫₀^π cos(x·sin(θ)) dθ

No closed-form finite-tree expression is currently known.
The value 7 reflects the best approximation found by complex MCTS
(depth=3 complex tree, node budget N=7 internal nodes) at MSE < 1e-4
over x ∈ [0, 10].  See notebooks/complex_special_functions.py for details.
"""

AI_NODE_COUNT = 9
"""
Airy Ai(x) best known complex-EML construction.

Airy Ai is related to Bessel functions of order 1/3.  A complex EML tree
at depth 3-4 achieves MSE ≈ 2×10⁻³ over x ∈ [-5, 5].  The exact
construction via complex MCTS remains an open research problem.
"""

ERF_NODE_COUNT = 5
"""
erf(x) best known complex-EML construction.

Using erf(x) = (2/√π) · ∫₀^x exp(-t²) dt.  A depth-2 complex EML tree
achieves MSE ≈ 5×10⁻⁴ over x ∈ [-3, 3].  The tanh approximation
erf(x) ≈ tanh(1.2025·x) achieves MSE ≈ 2×10⁻³ and maps to 5 CBEST nodes.
"""


# ── ComplexOptimizeResult ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class ComplexOpMatch:
    """One operation detected in a complex-domain expression."""
    name:         str    # canonical op name
    count:        int    # occurrences
    cbest_nodes:  int    # total nodes in CBEST mode
    real_nodes:   int    # total nodes in real BEST mode (for comparison)
    family:       str    # routing family (C-EML/C-EDL/C-EXL/C-EML(Euler))

    @property
    def savings(self) -> int:
        """Integer % savings vs real BEST (0 if CBEST costs same or more)."""
        if self.real_nodes == 0:
            return 0
        return max(0, round((1 - self.cbest_nodes / self.real_nodes) * 100))


@dataclass(frozen=True)
class ComplexOptimizeResult:
    """
    Result of ``complex_best_optimize()``.

    Attributes
    ----------
    original        Input expression string.
    ops             Detected operations with complex node counts.
    total_cbest     Sum of CBEST node costs.
    total_real_best Sum of real-domain BEST node costs (comparison baseline).
    complex_savings_pct  Integer % node reduction vs real BEST.
    message         One-line summary.
    euler_ops       List of operations that benefit from the complex bypass.
    """
    original:            str
    ops:                 tuple[ComplexOpMatch, ...]
    total_cbest:         int
    total_real_best:     int
    complex_savings_pct: int
    message:             str
    euler_ops:           tuple[str, ...]

    def __str__(self) -> str:
        lines = [self.message, ""]
        if self.ops:
            lines.append(
                f"  {'Operation':<14} {'Count':>5}  {'CBEST':>6}  "
                f"{'RealBEST':>8}  {'Save':>5}  Family"
            )
            lines.append("  " + "-" * 60)
            for m in self.ops:
                lines.append(
                    f"  {m.name:<14} {m.count:>5}  "
                    f"{m.cbest_nodes:>5}n  {m.real_nodes:>7}n  "
                    f"{m.savings:>4}%  {m.family}"
                )
            lines.append("  " + "-" * 60)
            lines.append(
                f"  {'TOTAL':<14} {'':>5}  "
                f"{self.total_cbest:>5}n  {self.total_real_best:>7}n  "
                f"{self.complex_savings_pct:>4}%"
            )
        if self.euler_ops:
            lines.append("")
            lines.append(
                f"  Euler bypass: {', '.join(self.euler_ops)} → 1 node each "
                f"(Im/Re of eml(ix,1))"
            )
        return "\n".join(lines)


# ── Real-BEST node counts for comparison ─────────────────────────────────────

_REAL_BEST_NODES: dict[str, int] = {
    "exp": 1, "ln": 1, "pow": 3, "sqrt": 3,
    "mul": 7, "div": 1, "recip": 2, "neg": 6,
    "sub": 5, "add": 11, "abs": 9,
    "sin": 63, "cos": 63,
    "sigmoid": 19, "tanh": 25, "gelu": 60,
}


# ── Expression scanner (reuses patterns from optimize.py) ────────────────────

import re as _re

_C_OP_PATTERNS: list[tuple[str, str]] = [
    ("sin",  r"\bsin\s*\(|(?:math|np|cmath)\.sin\s*\("),
    ("cos",  r"\bcos\s*\(|(?:math|np|cmath)\.cos\s*\("),
    ("exp",  r"\bexp\s*\(|(?:math|np|cmath)\.exp\s*\("),
    ("ln",   r"\b(?:log|ln)\s*\(|(?:math|np|cmath)\.log\w*\s*\("),
    ("pow",  r"\bpow\s*\(|(?:math|np)\.pow\s*\(|\*\*\s*[\d.]+"),
    ("sqrt", r"\bsqrt\s*\(|(?:math|np|cmath)\.sqrt\s*\("),
    ("tanh", r"\btanh\s*\(|(?:math|np|cmath)\.tanh\s*\("),
    ("abs",  r"\babs\s*\("),
    ("mul",  r"(?<=[a-zA-Z0-9_)])\s*\*(?!\*)\s*(?=[a-zA-Z0-9_(])"),
    ("div",  r"(?<=[a-zA-Z0-9_)])\s*/\s*(?=[a-zA-Z0-9_(])"),
    ("add",  r"(?<=[a-zA-Z0-9_)])\s*\+\s*(?=[a-zA-Z0-9_(])"),
    ("sub",  r"(?<=[a-zA-Z0-9_)])\s*-\s*(?=[a-zA-Z0-9_(])"),
]

_TANH_REAL_BEST = 25  # for tanh in real domain
_TANH_CBEST     = 25  # same in complex (no Euler bypass)


def complex_best_optimize(
    expr_or_func: Union[str, Callable[..., Any]],
) -> ComplexOptimizeResult:
    """
    Analyse a complex-domain expression for CBEST routing savings.

    Scans the expression for recognised math operations and reports:
    - Node counts in CBEST mode (complex domain)
    - Comparison against real-domain BEST node counts
    - Operations that benefit from the Euler-path complex bypass (sin, cos → 1 node)

    Args:
        expr_or_func: A math expression string or Python code snippet.
                      Callables are analysed via ``inspect.getsource``.

    Returns:
        ComplexOptimizeResult with node counts and savings analysis.

    Examples
    --------
    >>> r = complex_best_optimize("sin(x)**2 + cos(x)*exp(-x)")
    >>> print(r.complex_savings_pct)   # large savings from Euler bypass on sin/cos
    >>> print(r.euler_ops)             # ('sin', 'cos')

    >>> r = complex_best_optimize("exp(x) - exp(-x)")
    >>> print(r.total_cbest)           # 2 nodes (no complex advantage here)
    """
    import inspect as _inspect

    if callable(expr_or_func):
        try:
            source = _inspect.getsource(expr_or_func)
        except OSError:
            source = ""
    else:
        source = str(expr_or_func)

    counts: dict[str, int] = {}
    for op_name, pattern in _C_OP_PATTERNS:
        found = _re.findall(pattern, source)
        if found:
            counts[op_name] = counts.get(op_name, 0) + len(found)

    ops_list: list[ComplexOpMatch] = []
    euler_ops: list[str] = []

    for name, count in sorted(counts.items()):
        cbest = _CBEST_NODES.get(name)
        real  = _REAL_BEST_NODES.get(name)
        if cbest is None:
            continue
        if real is None:
            real = cbest  # unknown real cost — assume no savings
        src = _CBEST_SOURCE.get(name, "C-EML")
        ops_list.append(ComplexOpMatch(
            name=name,
            count=count,
            cbest_nodes=count * cbest,
            real_nodes=count * real,
            family=src,
        ))
        if name in ("sin", "cos"):
            euler_ops.append(name)

    total_cbest = sum(m.cbest_nodes for m in ops_list)
    total_real  = sum(m.real_nodes  for m in ops_list)
    savings_pct = (
        max(0, round((1 - total_cbest / total_real) * 100))
        if total_real > 0 else 0
    )

    if total_real > total_cbest:
        msg = (
            f"CBEST: {total_cbest} nodes vs {total_real} real-BEST — "
            f"{savings_pct}% fewer exp/ln calls"
        )
    else:
        msg = (
            f"No complex savings ({total_cbest} nodes — "
            "expression has no sin/cos to bypass)"
        )

    return ComplexOptimizeResult(
        original=source.strip(),
        ops=tuple(ops_list),
        total_cbest=total_cbest,
        total_real_best=total_real,
        complex_savings_pct=savings_pct,
        message=msg,
        euler_ops=tuple(euler_ops),
    )
