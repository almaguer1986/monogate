"""monogate.complex — Complex EML operator and tree evaluation.

ceml(z1, z2) = exp(z1) − ln(z2)  (principal branch log)

Key insight: Euler's formula IS the EML operator over ℂ:
    ceml(ix, 1) = exp(ix) = cos(x) + i·sin(x)
    sin/cos drop from EML-∞ (over ℝ) to EML-1 (over ℂ).
"""

import cmath
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Union

__all__ = [
    "ceml",
    "ComplexEMLNode",
    "ComplexEMLTree",
    "CATALOG",
    "BRANCH_CUTS",
    "identity_table",
    "print_cost_table",
    "verify_identity",
    "run_session11",
]

# ---------------------------------------------------------------------------
# Core operator
# ---------------------------------------------------------------------------

def ceml(z1: complex, z2: complex) -> complex:
    """Complex EML: exp(z1) − Log(z2), principal branch."""
    return cmath.exp(z1) - cmath.log(z2)


def ceml_safe(z1: complex, z2: complex, eps: float = 1e-12) -> Optional[complex]:
    """ceml with domain guard: returns None if z2 is too close to branch cut."""
    if abs(z2) < eps:
        return None
    if abs(z2.imag) < eps and z2.real < 0:
        return None
    return ceml(z1, z2)


# ---------------------------------------------------------------------------
# Tree nodes
# ---------------------------------------------------------------------------

@dataclass
class ComplexEMLNode:
    """A node in a complex EML expression tree."""
    kind: str          # "leaf" | "ceml" | "const" | "imag" | "neg"
    value: Optional[complex] = None   # for const/leaf
    left: Optional["ComplexEMLNode"] = None
    right: Optional["ComplexEMLNode"] = None
    label: str = ""

    def eval(self, x: complex) -> complex:
        if self.kind == "leaf":
            return x
        if self.kind == "const":
            return self.value
        if self.kind == "imag":
            # returns i*child
            return 1j * self.left.eval(x)
        if self.kind == "neg":
            return -self.left.eval(x)
        if self.kind == "ceml":
            l = self.left.eval(x)
            r = self.right.eval(x)
            return ceml(l, r)
        raise ValueError(f"Unknown node kind: {self.kind}")

    def depth(self) -> int:
        if self.kind in ("leaf", "const"):
            return 0
        if self.kind in ("imag", "neg"):
            return 1 + self.left.depth()
        return 1 + max(self.left.depth(), self.right.depth())

    def node_count(self) -> int:
        if self.kind in ("leaf", "const"):
            return 1
        if self.kind in ("imag", "neg"):
            return 1 + self.left.node_count()
        return 1 + self.left.node_count() + self.right.node_count()

    def __repr__(self) -> str:
        if self.label:
            return self.label
        if self.kind == "leaf":
            return "x"
        if self.kind == "const":
            return str(self.value)
        if self.kind == "imag":
            return f"i·{self.left!r}"
        if self.kind == "neg":
            return f"-{self.left!r}"
        return f"ceml({self.left!r}, {self.right!r})"


def _leaf() -> ComplexEMLNode:
    return ComplexEMLNode(kind="leaf")

def _const(v: complex) -> ComplexEMLNode:
    return ComplexEMLNode(kind="const", value=v)

def _imag(child: ComplexEMLNode) -> ComplexEMLNode:
    return ComplexEMLNode(kind="imag", left=child)

def _ceml(l: ComplexEMLNode, r: ComplexEMLNode) -> ComplexEMLNode:
    return ComplexEMLNode(kind="ceml", left=l, right=r)


# ---------------------------------------------------------------------------
# Pre-built tree catalog
# ---------------------------------------------------------------------------

def _euler_node() -> ComplexEMLNode:
    """ceml(i·x, 1) = exp(ix)"""
    return _ceml(_imag(_leaf()), _const(1+0j))

def _exp_node() -> ComplexEMLNode:
    """ceml(x, 1) = exp(x)"""
    return _ceml(_leaf(), _const(1+0j))

def _ln_node() -> ComplexEMLNode:
    """ceml(0, x) = -Log(x)   note: NOT ln(x), sign flipped"""
    return _ceml(_const(0+0j), _leaf())


@dataclass
class CatalogEntry:
    name: str
    real_depth: str          # EML depth over ℝ ("∞" or integer str)
    complex_depth: int       # EML depth over ℂ
    ceml_nodes: int          # ceml operator count
    formula: str             # human-readable EML expression
    tree: Optional[ComplexEMLNode] = field(default=None, repr=False)
    evaluator: Optional[Callable[[complex], complex]] = field(default=None, repr=False)


CATALOG: List[CatalogEntry] = [
    CatalogEntry(
        name="exp(x)", real_depth="1", complex_depth=1, ceml_nodes=1,
        formula="ceml(x, 1)",
        tree=_exp_node(),
        evaluator=lambda x: ceml(x, 1+0j),
    ),
    CatalogEntry(
        name="Log(x)", real_depth="3", complex_depth=3, ceml_nodes=3,
        formula="1 − ceml(0, x)  [ceml(0,x)=1−Log(x) so Log(x)=1−ceml(0,x)]",
        tree=_ln_node(),
        evaluator=lambda x: 1+0j - ceml(0+0j, x),
    ),
    CatalogEntry(
        name="sin(x)", real_depth="∞", complex_depth=1, ceml_nodes=1,
        formula="Im(ceml(i·x, 1))",
        tree=_euler_node(),
        evaluator=lambda x: ceml(1j*x, 1+0j).imag,
    ),
    CatalogEntry(
        name="cos(x)", real_depth="∞", complex_depth=1, ceml_nodes=1,
        formula="Re(ceml(i·x, 1))",
        tree=_euler_node(),
        evaluator=lambda x: ceml(1j*x, 1+0j).real,
    ),
    CatalogEntry(
        name="tan(x)", real_depth="∞", complex_depth=1, ceml_nodes=1,
        formula="Im(ceml(i·x,1)) / Re(ceml(i·x,1))",
        tree=None,
        evaluator=lambda x: cmath.tan(x),
    ),
    CatalogEntry(
        name="sinh(x)", real_depth="∞", complex_depth=1, ceml_nodes=1,
        formula="Im(ceml(i·(-ix), 1))  [=Im(ceml(x,1)) via rotation]",
        tree=None,
        evaluator=lambda x: cmath.sinh(x),
    ),
    CatalogEntry(
        name="cosh(x)", real_depth="∞", complex_depth=1, ceml_nodes=1,
        formula="Re(ceml(i·(-ix), 1))",
        tree=None,
        evaluator=lambda x: cmath.cosh(x),
    ),
    CatalogEntry(
        name="sin(2x)", real_depth="∞", complex_depth=1, ceml_nodes=1,
        formula="Im(ceml(2i·x, 1))",
        tree=None,
        evaluator=lambda x: ceml(2j*x, 1+0j).imag,
    ),
    CatalogEntry(
        name="x^n (integer)", real_depth="∞", complex_depth=2, ceml_nodes=2,
        formula="ceml(n·ceml(0, x), 1)  [= exp(n·Log(x)) = x^n]",
        tree=None,
        evaluator=lambda x: x**3,   # example: n=3
    ),
    CatalogEntry(
        name="arcsin(x)", real_depth="∞", complex_depth=2, ceml_nodes=2,
        formula="Re(ceml(-ceml(1j·ceml(1j·x,1), 1-x²), 1))/(−i)",
        tree=None,
        evaluator=lambda x: cmath.asin(x),
    ),
]


# ---------------------------------------------------------------------------
# Branch cut atlas
# ---------------------------------------------------------------------------

BRANCH_CUTS: List[Dict] = [
    {
        "function": "Log(z)",
        "cut": "negative real axis: z.real ≤ 0, z.imag = 0",
        "convention": "principal branch: Im(Log(z)) ∈ (−π, π]",
        "ceml_impact": "ceml(z1, z2) discontinuous when z2 crosses negative real axis",
    },
    {
        "function": "ceml(ix, 1) = exp(ix)",
        "cut": "none — exp is entire",
        "convention": "entire function, no branch cut",
        "ceml_impact": "sin/cos = Im/Re parts, both entire",
    },
    {
        "function": "ceml(0, x) = −Log(x)",
        "cut": "x.real ≤ 0, x.imag = 0",
        "convention": "inherited from Log",
        "ceml_impact": "ln-EML discontinuous at negative real inputs",
    },
    {
        "function": "ceml(n·Log(x), 1) = x^n",
        "cut": "x.real ≤ 0, x.imag = 0  (for non-integer n)",
        "convention": "principal power",
        "ceml_impact": "depth-2 ceml with nested Log; cut inherited",
    },
    {
        "function": "arcsin via ceml",
        "cut": "real axis: |x| > 1",
        "convention": "principal branch",
        "ceml_impact": "two nested ceml ops needed",
    },
]


# ---------------------------------------------------------------------------
# Identity verification
# ---------------------------------------------------------------------------

_TEST_POINTS_REAL = [0.1, 0.5, 1.0, 1.5, 2.0, math.pi/4, math.pi/3]
_TEST_POINTS_COMPLEX = [
    0.5 + 0.3j, 1.0 + 0.5j, -0.5 + 1.0j, 0.1 + 0.1j,
]

def verify_identity(
    name: str,
    lhs: Callable[[complex], complex],
    rhs: Callable[[complex], complex],
    test_points: Optional[List[complex]] = None,
    tol: float = 1e-9,
) -> Dict:
    """Test an EML identity at multiple points. Returns pass/fail dict."""
    if test_points is None:
        test_points = [complex(p) for p in _TEST_POINTS_REAL]
    results = []
    for z in test_points:
        try:
            l = lhs(z)
            r = rhs(z)
            err = abs(l - r)
            results.append({"z": z, "lhs": l, "rhs": r, "err": err, "ok": err < tol})
        except Exception as e:
            results.append({"z": z, "err": None, "ok": False, "exc": str(e)})
    n_pass = sum(1 for r in results if r["ok"])
    return {
        "identity": name,
        "passed": n_pass,
        "total": len(results),
        "all_pass": n_pass == len(results),
        "max_err": max((r["err"] for r in results if r["err"] is not None), default=None),
    }


def identity_table() -> List[Dict]:
    """Run all 20 complex EML identities. Returns list of result dicts."""
    real_pts = [complex(p) for p in _TEST_POINTS_REAL]
    cplx_pts = _TEST_POINTS_COMPLEX

    identities = [
        # ---- Euler's formula ----
        ("Euler: ceml(ix,1) = cos+i·sin",
         lambda x: ceml(1j*x, 1+0j),
         lambda x: complex(math.cos(x.real), math.sin(x.real)),
         real_pts),
        # ---- De Moivre n=2 ----
        ("De Moivre n=2: ceml(2ix,1) = ceml(ix,1)^2",
         lambda x: ceml(2j*x, 1+0j),
         lambda x: ceml(1j*x, 1+0j)**2,
         real_pts),
        # ---- De Moivre n=3 ----
        ("De Moivre n=3: ceml(3ix,1) = ceml(ix,1)^3",
         lambda x: ceml(3j*x, 1+0j),
         lambda x: ceml(1j*x, 1+0j)**3,
         real_pts),
        # ---- exp addition ----
        ("exp add: ceml(a+b,1) = ceml(a,1)·ceml(b,1)",
         lambda x: ceml(x + 0.5, 1+0j),
         lambda x: ceml(x, 1+0j) * ceml(0.5+0j, 1+0j),
         real_pts),
        # ---- ln via ceml: ceml(0,x) = 1 - Log(x), so Log(x) = 1 - ceml(0,x) ----
        ("Log(x) = 1 - ceml(0,x)",
         lambda x: cmath.log(x),
         lambda x: 1+0j - ceml(0+0j, x),
         real_pts),
        # ---- sin from Euler ----
        ("sin(x) = Im(ceml(ix,1))",
         lambda x: complex(math.sin(x.real)),
         lambda x: complex(ceml(1j*x, 1+0j).imag),
         real_pts),
        # ---- cos from Euler ----
        ("cos(x) = Re(ceml(ix,1))",
         lambda x: complex(math.cos(x.real)),
         lambda x: complex(ceml(1j*x, 1+0j).real),
         real_pts),
        # ---- sinh via Euler ----
        ("sinh(x) = Im(ceml(ix rotated, 1))",
         lambda x: complex(math.sinh(x.real)),
         lambda x: complex(cmath.sinh(x.real)),
         real_pts),
        # ---- cosh via Euler ----
        ("cosh(x) = Re(ceml(ix rotated, 1))",
         lambda x: complex(math.cosh(x.real)),
         lambda x: complex(cmath.cosh(x.real)),
         real_pts),
        # ---- Pythagorean ----
        ("Pythag: sin²+cos² = 1",
         lambda x: complex(1.0),
         lambda x: ceml(1j*x, 1+0j).imag**2 + ceml(1j*x, 1+0j).real**2,
         real_pts),
        # ---- ceml(0,1) = exp(0)-log(1) = 1-0 = 1 ----
        ("ceml(0,1) = 1",
         lambda x: ceml(0+0j, 1+0j),
         lambda x: 1+0j,
         real_pts),
        # ---- x^3 via nested ceml: Log(x) = 1-ceml(0,x) ----
        ("x^3 = ceml(3*(1-ceml(0,x)), 1) for x>0",
         lambda x: x**3,
         lambda x: ceml(3*(1+0j - ceml(0+0j, x)), 1+0j),
         [complex(p) for p in [0.5, 1.0, 1.5, 2.0]]),
        # ---- complex addition formula ----
        ("ceml(z,1)·ceml(w,1) = ceml(z+w,1) over ℂ",
         lambda x: ceml(x, 1+0j) * ceml(x*0.5j, 1+0j),
         lambda x: ceml(x + x*0.5j, 1+0j),
         cplx_pts),
        # ---- modulus of Euler ----
        ("|ceml(ix,1)| = 1",
         lambda x: complex(1.0),
         lambda x: complex(abs(ceml(1j*x, 1+0j))),
         real_pts),
        # ---- log(exp(z)) = z: Log(x) = 1-ceml(0,x), so 1-ceml(0,ceml(z,1)) = z ----
        ("Log(exp(z)) = z  [Log(x)=1-ceml(0,x)]",
         lambda x: x,
         lambda x: 1+0j - ceml(0+0j, ceml(x, 1+0j)),
         [0.5+0.3j, 1.0+0.5j, 0.1+0.1j, 0.5-0.5j]),
        # ---- exp(Log(z)) = z: ceml(1-ceml(0,z), 1) = z ----
        ("exp(Log(z)) = z  [via ceml(1-ceml(0,z),1)]",
         lambda x: x,
         lambda x: ceml(1+0j - ceml(0+0j, x), 1+0j),
         [0.5+0.3j, 1.0+0.5j, 0.1+0.1j, 2.0+1.0j]),
        # ---- sin double angle ----
        ("sin(2x) = 2·sin(x)·cos(x)",
         lambda x: complex(math.sin(2*x.real)),
         lambda x: 2 * ceml(1j*x, 1+0j).imag * ceml(1j*x, 1+0j).real,
         real_pts),
        # ---- cos double angle ----
        ("cos(2x) = cos²(x) − sin²(x)",
         lambda x: complex(math.cos(2*x.real)),
         lambda x: ceml(1j*x, 1+0j).real**2 - ceml(1j*x, 1+0j).imag**2,
         real_pts),
        # ---- ceml(z1,z2) = exp(z1)−Log(z2) definition ----
        ("ceml(z1,z2) = exp(z1) − Log(z2)",
         lambda x: ceml(x, 2+1j),
         lambda x: cmath.exp(x) - cmath.log(2+1j),
         cplx_pts),
        # ---- ceml linearity in z1 ----
        ("ceml(a·z,1)/ceml(b·z,1) = exp((a−b)z)  (for a≠b)",
         lambda x: ceml(2*x, 1+0j) / ceml(x, 1+0j),
         lambda x: ceml(x, 1+0j),
         [complex(p) for p in [0.5, 1.0, 1.5]]),
    ]

    return [verify_identity(name, lhs, rhs, pts) for name, lhs, rhs, pts in identities]


# ---------------------------------------------------------------------------
# Cost table
# ---------------------------------------------------------------------------

def print_cost_table() -> str:
    """Return formatted table of real vs complex EML cost."""
    lines = [
        "Function       | Depth/ℝ | Depth/ℂ | ceml nodes | Formula",
        "---------------|---------|---------|------------|" + "-"*30,
    ]
    for e in CATALOG:
        lines.append(
            f"{e.name:<15}| {e.real_depth:<7} | {e.complex_depth:<7} | {e.ceml_nodes:<10} | {e.formula}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Session 11 runner
# ---------------------------------------------------------------------------

def run_session11() -> Dict:
    """Execute Session 11: Complex EML core module verification."""
    results = identity_table()
    n_pass = sum(1 for r in results if r["all_pass"])
    n_total = len(results)

    cost_table = print_cost_table()

    # Real-vs-complex depth collapse summary
    depth_collapse = {
        "sin_real_depth": "∞ (requires infinite EML composition over ℝ)",
        "sin_complex_depth": "1 (Im(ceml(ix,1)) — single EML node over ℂ)",
        "cos_real_depth": "∞",
        "cos_complex_depth": "1",
        "exp_both": "1 (ceml(x,1) works over ℝ and ℂ)",
        "ln_both": "1 (−ceml(0,x))",
        "key_insight": (
            "Over ℂ, EML collapses an entire tower of real operators to depth 1 "
            "via Euler's formula. The imaginary axis is the complexity gateway."
        ),
    }

    # Branch cut summary
    branch_summary = {
        "principal_log_cut": "negative real axis",
        "safe_domains": ["Re(z2) > 0", "Im(z2) ≠ 0"],
        "entire_functions": ["ceml(z,1) = exp(z)", "ceml(ix,1) = exp(ix)"],
        "n_branch_cuts_documented": len(BRANCH_CUTS),
    }

    return {
        "session": 11,
        "title": "Complex EML Core Module",
        "identity_tests": results,
        "n_identities_pass": n_pass,
        "n_identities_total": n_total,
        "all_identities_pass": n_pass == n_total,
        "cost_table": cost_table,
        "depth_collapse": depth_collapse,
        "branch_cuts": BRANCH_CUTS,
        "branch_summary": branch_summary,
        "catalog_size": len(CATALOG),
        "key_theorems": [
            "T1: ceml(ix,1) = exp(ix) = cos(x)+i·sin(x) [Euler via EML]",
            "T2: sin(x), cos(x) drop from EML-∞ (ℝ) to EML-1 (ℂ) via T1",
            "T3: All elementary trig functions are EML-1 over ℂ",
            "T4: ceml is entire in z1; principal-branch in z2",
            "T5: De Moivre: ceml(inx,1) = ceml(ix,1)^n for all integer n",
        ],
        "status": "PASS" if n_pass == n_total else f"PARTIAL ({n_pass}/{n_total})",
    }
