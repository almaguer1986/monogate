"""
grammar_hierarchy.py -- Grammar Complexity Hierarchy for EML operators.

Formalizes the expressivity ladder G0 through G_inf:
  G0: S -> 1 | eml(S,S)                      -- baseline
  G1: S -> x | eml(S,S)                      -- add variable
  G2: S -> 1 | x | eml(S,S) | deml(S,S)     -- add DEML
  G3: S -> 1 | x | eml(S,S) | deml(S,S) | exl(S,S)  -- add EXL
  G4: S -> n in Z | eml(S,S)                 -- integer constants
  G5: S -> r in Q | eml(S,S)                 -- rational constants

Tests each grammar level against 15 physics laws + 9 arithmetic operations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np


# ── Operators ─────────────────────────────────────────────────────────────────

def _eml(x: float, y: float) -> float:
    return math.exp(x) - math.log(y)


def _deml(x: float, y: float) -> float:
    return math.exp(-x) - math.log(y)


def _exl(x: float, y: float) -> float:
    return math.exp(x) * math.log(y)


def _eal(x: float, y: float) -> float:
    return math.exp(x) + math.log(y)


# ── Target function catalog ───────────────────────────────────────────────────

@dataclass(frozen=True)
class TargetFn:
    name: str
    func: Callable[[float], float]
    x_probe: float = 2.0
    category: str = "other"
    expected_grammar: str | None = None


PHYSICS_LAWS: list[TargetFn] = [
    TargetFn("exp(x)",       lambda x: math.exp(x),      2.0, "exponential", "G1"),
    TargetFn("exp(-x)",      lambda x: math.exp(-x),     2.0, "neg_exp",     "G2"),
    TargetFn("ln(x)",        lambda x: math.log(x),      2.0, "log",         "G1"),
    TargetFn("x^2",          lambda x: x**2,              2.0, "power",       "G4"),
    TargetFn("x^3",          lambda x: x**3,              2.0, "power",       "G4"),
    TargetFn("1/x",          lambda x: 1/x,               2.0, "rational",    "G4"),
    TargetFn("sqrt(x)",      lambda x: math.sqrt(x),     2.0, "root",        "G4"),
    TargetFn("x*exp(-x)",    lambda x: x*math.exp(-x),   1.0, "decay",       "G3"),
    TargetFn("exp(-x^2)",    lambda x: math.exp(-x**2),  1.0, "gaussian",    "G3"),
    TargetFn("1/(1+exp(-x))",lambda x: 1/(1+math.exp(-x)),1.0,"sigmoid",     "G2"),
    TargetFn("x*ln(x)",      lambda x: x*math.log(x),    2.0, "mixed",       "G3"),
    TargetFn("exp(x)/x",     lambda x: math.exp(x)/x,    2.0, "mixed",       "G3"),
    TargetFn("ln(x)/x",      lambda x: math.log(x)/x,    2.0, "mixed",       "G3"),
    TargetFn("cosh(x)",      lambda x: math.cosh(x),     1.0, "hyperbolic",  "G4"),
    TargetFn("sinh(x)",      lambda x: math.sinh(x),     1.0, "hyperbolic",  "G4"),
]

ARITHMETIC_OPS: list[TargetFn] = [
    TargetFn("x+1",    lambda x: x+1,        2.0, "arithmetic", "G1"),
    TargetFn("x-1",    lambda x: x-1,        2.0, "arithmetic", "G1"),
    TargetFn("x*2",    lambda x: x*2,        2.0, "arithmetic", "G4"),
    TargetFn("x/2",    lambda x: x/2,        2.0, "arithmetic", "G4"),
    TargetFn("x^2+x",  lambda x: x**2+x,    2.0, "arithmetic", "G4"),
    TargetFn("log2(x)",lambda x: math.log2(x), 2.0, "arithmetic", "G1"),
    TargetFn("exp(2x)",lambda x: math.exp(2*x), 1.0, "arithmetic", "G4"),
    TargetFn("1+1/x",  lambda x: 1+1/x,     2.0, "arithmetic", "G4"),
    TargetFn("x*e",    lambda x: x*math.e,  1.0, "arithmetic", "G4"),
]

ALL_TARGETS: list[TargetFn] = PHYSICS_LAWS + ARITHMETIC_OPS


# ── Grammar definition ────────────────────────────────────────────────────────

@dataclass
class Grammar:
    name: str
    operators: list[Callable]
    op_names: list[str]
    constants: list[float]
    const_desc: str
    has_variable: bool = True
    description: str = ""


def _make_grammars() -> list[Grammar]:
    return [
        Grammar(
            name="G0",
            operators=[_eml],
            op_names=["eml"],
            constants=[1.0],
            const_desc="1",
            has_variable=False,
            description="S -> 1 | eml(S,S)  -- baseline, no variable",
        ),
        Grammar(
            name="G1",
            operators=[_eml],
            op_names=["eml"],
            constants=[1.0],
            const_desc="1,x",
            has_variable=True,
            description="S -> 1 | x | eml(S,S)  -- standard EML",
        ),
        Grammar(
            name="G2",
            operators=[_eml, _deml],
            op_names=["eml", "deml"],
            constants=[1.0],
            const_desc="1,x",
            has_variable=True,
            description="S -> 1 | x | eml(S,S) | deml(S,S)  -- EML + DEML",
        ),
        Grammar(
            name="G3",
            operators=[_eml, _deml, _exl],
            op_names=["eml", "deml", "exl"],
            constants=[1.0],
            const_desc="1,x",
            has_variable=True,
            description="S -> 1 | x | eml | deml | exl  -- EML + DEML + EXL",
        ),
        Grammar(
            name="G3+eal",
            operators=[_eml, _deml, _exl, _eal],
            op_names=["eml", "deml", "exl", "eal"],
            constants=[1.0],
            const_desc="1,x",
            has_variable=True,
            description="S -> 1 | x | eml | deml | exl | eal  -- 4 operators",
        ),
        Grammar(
            name="G4",
            operators=[_eml],
            op_names=["eml"],
            constants=[float(k) for k in range(-3, 4) if k != 0],
            const_desc="Z\\{0}",
            has_variable=True,
            description="S -> n in Z | x | eml(S,S)  -- integer constants",
        ),
    ]


GRAMMARS: list[Grammar] = _make_grammars()


# ── Expressivity test ─────────────────────────────────────────────────────────

def _try_depth1(op: Callable, c1: float, c2: float, x: float, target: float,
                tol: float = 0.01) -> bool:
    """Check if op(c1, c2) or op(x, c) or op(c, x) matches target."""
    combos = [(c1, c2), (x, c1), (c1, x), (x, x)]
    for a, b in combos:
        try:
            val = op(a, b)
            if math.isfinite(val) and abs(val - target) < tol:
                return True
        except (ValueError, ZeroDivisionError, OverflowError):
            pass
    return False


_PROBE_OFFSETS = [0.5, 1.0, 1.5, 2.0, 2.5]


def _leaf_options(grammar: Grammar) -> list:
    """Return all possible symbolic leaf values: constants + 'x' marker."""
    opts = list(grammar.constants)
    if grammar.has_variable:
        opts.append("x")  # sentinel meaning "use x"
    return opts


def _eval_assigned(assignment: list, tree_shape: tuple | str,
                   ops: list[Callable], x: float) -> float | None:
    """
    Evaluate a tree with a specific leaf assignment at x.
    assignment is a flat list of leaf values (constants or 'x' resolved to x).
    """
    counter = [0]

    def _eval(shape):
        if shape == "leaf":
            idx = counter[0]
            counter[0] += 1
            raw = assignment[idx]
            v = x if raw == "x" else raw
            return v
        op_idx, left, right = shape
        op = ops[op_idx]
        a = _eval(left)
        b = _eval(right)
        if a is None or b is None:
            return None
        try:
            v = op(a, b)
            return v if math.isfinite(v) else None
        except Exception:
            return None

    return _eval(tree_shape)


def _count_leaves(shape: tuple | str) -> int:
    if shape == "leaf":
        return 1
    return _count_leaves(shape[1]) + _count_leaves(shape[2])


def _all_shapes(n_ops: int, max_depth: int = 2) -> list[tuple[tuple | str, int]]:
    """Return (shape, depth) pairs for all tree shapes up to max_depth."""
    shapes = [("leaf", 0)]
    for oi in range(n_ops):
        shapes.append(((oi, "leaf", "leaf"), 1))
    if max_depth >= 2:
        for oi in range(n_ops):
            for oj in range(n_ops):
                shapes.append(((oi, (oj, "leaf", "leaf"), "leaf"), 2))
                shapes.append(((oi, "leaf", (oj, "leaf", "leaf")), 2))
    return shapes


def _expressivity_test(
    grammar: Grammar,
    fn: TargetFn,
    tol: float = 0.05,
    max_depth: int = 2,
) -> dict:
    """
    Test symbolic expressivity: is there ONE tree structure + leaf assignment
    (constants or x) that matches fn(x) at ALL probe points?
    """
    import itertools

    base_x = fn.x_probe
    probes = [base_x + off for off in _PROBE_OFFSETS]
    leaf_opts = _leaf_options(grammar)

    for shape, depth in _all_shapes(len(grammar.operators), max_depth):
        n_leaves = _count_leaves(shape)
        # Try all assignments of leaf_opts to each leaf position
        for assignment in itertools.product(leaf_opts, repeat=n_leaves):
            all_match = True
            for x in probes:
                try:
                    target = fn.func(x)
                except Exception:
                    all_match = False
                    break
                if not math.isfinite(target):
                    all_match = False
                    break
                val = _eval_assigned(list(assignment), shape, grammar.operators, x)
                if val is None or abs(val - target) > tol:
                    all_match = False
                    break
            if all_match:
                return {"expressible": True, "min_nodes": depth, "notes": "symbolic_match"}

    return {"expressible": False, "min_nodes": None, "notes": "not_found"}


def coverage_table(grammars: list[Grammar] | None = None, tol: float = 0.001) -> str:
    """Generate a markdown coverage table showing grammar vs target function (depth<=2)."""
    if grammars is None:
        grammars = GRAMMARS

    rows = []
    header = "| Target | Category | " + " | ".join(g.name for g in grammars) + " |"
    separator = "|--------|----------|" + "|".join(["---"] * len(grammars)) + "|"
    rows.append(header)
    rows.append(separator)

    grammar_totals = {g.name: 0 for g in grammars}

    for fn in ALL_TARGETS:
        row_cells = [fn.name, fn.category]
        for g in grammars:
            result = _expressivity_test(g, fn, tol=tol)
            if result["expressible"]:
                cell = f"Y(d{result['min_nodes']})"
                grammar_totals[g.name] += 1
            else:
                cell = "N"
            row_cells.append(cell)
        rows.append("| " + " | ".join(row_cells) + " |")

    rows.append("| **TOTAL** | | " + " | ".join(str(grammar_totals[g.name]) for g in grammars) + " |")
    return "\n".join(rows)


def build_hierarchy(tol: float = 0.001) -> list[dict]:
    """Return ordered list of (grammar_name, coverage_count, covered_fns) at depth<=2."""
    result = []
    for g in GRAMMARS:
        covered = []
        for fn in ALL_TARGETS:
            r = _expressivity_test(g, fn, tol=tol)
            if r["expressible"]:
                covered.append(fn.name)
        result.append({
            "grammar": g.name,
            "description": g.description,
            "coverage": len(covered),
            "total": len(ALL_TARGETS),
            "covered_functions": covered,
        })
    return result


def main() -> None:
    print("Grammar Complexity Hierarchy (depth <= 2, tol=0.001)")
    print("=" * 60)
    print()

    hierarchy = build_hierarchy()
    for entry in hierarchy:
        pct = 100 * entry["coverage"] / entry["total"]
        covered_str = ", ".join(entry["covered_functions"]) if entry["covered_functions"] else "none"
        print(f"{entry['grammar']:8s}  {entry['coverage']:2d}/{entry['total']} ({pct:.0f}%)  |  {entry['description']}")
        print(f"          Covered: {covered_str}")
        print()

    print(coverage_table())


if __name__ == "__main__":
    main()
