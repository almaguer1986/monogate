"""
SuperBEST Router — Dynamic Per-Operation Operator Selection
Finds the minimum-node operator for each arithmetic primitive in an expression tree.

Author: Arturo R. Almaguer
Session: FAM-C2 / SuperBEST v5 (ADD-CASCADE 2026-04-20)
Revised: X20 resolution (2026-04-20) — dual-domain table, pow and mul corrected

v5 changes vs v4:
  - add_gen: 11n → 2n for ALL real x, y (LEdiv(x, DEML(y,1)) = x+y)
  - add_pos: 3n → 2n (same construction, no domain restriction needed)
  - add unified entry: single add=2n covers all reals; positive-domain split eliminated
  - sqrt: now a first-class entry at 2n (EML(0.5*EXL(0,x), 1) = sqrt(x))
  - Total: 19n → 18n; savings: ~74% → 75.3% vs naive 73n baseline
  - Reference: SuperBEST_v5_Structural_Audit.tex, ADD_T1_General_Addition_2n.tex

v5.1 changes (X20 resolution + X7/X8 domain audit):
  - pow positive: 3n → 1n (EPL/ELMl = exp(n*ln(x)) = x^n is a direct 1-node F16 op)
  - mul general: NO_F16_TREE → 6n (neg(mul(neg(x), y)) — pay 2n each for neg/mul/neg)
  - Positive-domain total: 16n; savings vs naive 73n: 78.1%
  - General-domain total:  22n; savings vs naive 73n: 69.9%
  - predict_cost() accepts positive_domain=True to switch pow 3n→1n and mul 6n→2n
  - Reference: x20_operator_17.json (F17d paradox), f17_resolution.json
"""
from __future__ import annotations
import math
import re
from typing import Any


# ---------------------------------------------------------------------------
# Operator node costs (EXL-extended, 0 and 1 as free constants)
# ---------------------------------------------------------------------------
SUPERBEST_TABLE: dict[str, dict] = {
    "exp":   {"operator": "EML",                  "nodes": 1, "domain": "all x",
              "construction": "eml(x, 1)"},
    "ln":    {"operator": "EXL",                  "nodes": 1, "domain": "x > 0",
              "construction": "exl(0, x)"},
    "mul":   {"operator": "Mixed(EXL/ELAd)",        "nodes": 2, "domain": "x > 0",
              "construction": "elad(exl(0,x), y)"},
    "div":   {"operator": "Mixed(EXL/ELSb)",       "nodes": 2, "domain": "x, y > 0",
              "construction": "elsb(exl(0,x), y)"},
    "add":   {"operator": "Mixed(DEML/LEdiv)",     "nodes": 2, "domain": "all x, y",
              "construction": "lediv(x, deml(y,1))",
              "note": "2 nodes for ALL reals: LEdiv(x,DEML(y,1))=x-ln(exp(-y))=x+y (ADD-T1)"},
    "sub":   {"operator": "Mixed(EML/LEdiv)",      "nodes": 2, "domain": "all x, y",
              "construction": "lediv(x, eml(y,1))"},
    "sqrt":  {"operator": "Mixed(EXL/EML)",        "nodes": 2, "domain": "x > 0",
              "construction": "eml(0.5*exl(0,x), 1)",
              "note": "2 nodes: EML(0.5*EXL(0,x),1) = exp(0.5*ln(x)) = sqrt(x)"},
    "neg":   {"operator": "Mixed(EXL/DEML)",       "nodes": 2, "domain": "all x",
              "construction": "exl(0, deml(x,1))",
              "construction_pos": "emn(exl(0,x), 1)", "nodes_pos": 2,
              "note": "2 nodes for all x (EXL+DEML); 2 nodes pos-domain (EMN+EXL)"},
    "recip": {"operator": "ELSb",                  "nodes": 1, "domain": "x != 0",
              "construction": "elsb(0, x)"},
    "pow":   {"operator": "EXL",                   "nodes": 3, "domain": "x > 0 (general construction)",
              "construction": "eml(exl(ln(n),x), 1)"},
    "pow_pos": {"operator": "EPL/ELMl",             "nodes": 1, "domain": "x > 0",
                "construction": "epl(n,x) = exp(n*ln(x)) = x^n",
                "note": "X20: EPL = ELMl = exp(x*ln(y)) = y^x is in F16 census. pow(x,n)=EPL(n,x) for x>0 is 1 node."},
    "mul_gen": {"operator": "Mixed(DEML/ELAd/DEML)", "nodes": 6, "domain": "all x, y > 0 possible",
                "construction": "neg(mul(neg(x), y))",
                "note": "General-domain: neg(2n) + mul_pos(2n) + neg(2n) = 6n. Handles signed x via negation."},
    "sin":   {"operator": "EML (complex)",         "nodes": 1, "domain": "all x",
              "construction": "Im(eml(ix, 1))"},
    "cos":   {"operator": "EML (complex)",         "nodes": 1, "domain": "all x",
              "construction": "Re(eml(ix, 1))"},
}

NAIVE_COSTS: dict[str, int] = {
    "exp": 1, "ln": 3, "mul": 13, "div": 15, "add": 11,
    "sub": 5, "neg": 9, "recip": 5, "sqrt": 8, "pow": 15, "sin": 13, "cos": 13,
}

# SuperBEST v5: unified single-tier costs (no positive-domain split)
# All entries proved optimal in SuperBEST_v5_Structural_Audit.tex
SUPERBEST_COSTS_V5: dict[str, int] = {
    "exp": 1, "ln": 1, "recip": 1,
    "div": 2, "neg": 2, "mul": 2, "sub": 2, "add": 2, "sqrt": 2,
    "pow": 3,
    "sin": 1, "cos": 1,  # via complex EML
}

# SuperBEST v5.1 — positive-domain costs (X20 resolution)
# pow corrected to 1n: EPL(n,x) = exp(n*ln(x)) = x^n is a 1-node F16 operator (ELMl)
# mul has NO_F16_TREE for general domain; 2n holds for x > 0
# All positive-domain costs: total = 16n; savings vs naive 73n = 78.1%
SUPERBEST_COSTS_POS: dict[str, int] = {
    "exp": 1, "ln": 1, "recip": 1,
    "div": 2, "neg": 2, "mul": 2, "sub": 2, "add": 2, "sqrt": 2,
    "pow": 1,   # X20: EPL/ELMl direct — 1-node F16 application for x > 0
    "sin": 1, "cos": 1,
}

# SuperBEST v5.1 — general-domain costs (dual-domain table)
# mul = 6n via neg(mul(neg(x), y)): neg(2n) + mul_pos(2n) + neg(2n)
# Total = 22n; savings vs naive 73n = 69.9%
SUPERBEST_COSTS_GEN: dict[str, int] = {
    "exp": 1, "ln": 1, "recip": 1,
    "div": 2, "neg": 2, "mul": 6, "sub": 2, "add": 2, "sqrt": 2,
    "pow": 3,   # general domain: expanded EXL+ELAd+EML construction
    "sin": 1, "cos": 1,
}


def superbest_cost(op: str) -> int:
    """Return the SuperBEST node cost for the given operation (general domain, v5 defaults)."""
    if op in SUPERBEST_TABLE:
        return SUPERBEST_TABLE[op]["nodes"]
    return NAIVE_COSTS.get(op, 99)


def predict_cost(op: str, positive_domain: bool = False) -> int:
    """Return the predicted SuperBEST node cost for an operation.

    When positive_domain=True, uses the corrected positive-domain cost table (v5.1).
    The key difference: pow = 1n for positive domain (EPL/ELMl direct application)
    vs pow = 3n for the expanded general-domain construction.

    mul is absent from the general-domain table (NO single real F16 tree for all reals).
    For mul with positive_domain=False, this function returns the positive-domain cost (2n)
    with a note that it only applies for x > 0.

    Args:
        op: Operation name (exp, ln, mul, div, add, sub, neg, recip, sqrt, pow, sin, cos)
        positive_domain: If True, use positive-domain costs (pow=1n). Default: False (pow=3n).

    Returns:
        Minimum node count for the given operation under the specified domain assumption.
    """
    if positive_domain:
        return SUPERBEST_COSTS_POS.get(op, NAIVE_COSTS.get(op, 99))
    return SUPERBEST_COSTS_GEN.get(op, NAIVE_COSTS.get(op, 99))


def superbest_operator(op: str) -> str:
    """Return the optimal operator name for the given operation."""
    if op in SUPERBEST_TABLE:
        return SUPERBEST_TABLE[op]["operator"]
    return "unknown"


def superbest_construction(op: str) -> str:
    """Return the minimal-node construction for the given operation."""
    if op in SUPERBEST_TABLE:
        return SUPERBEST_TABLE[op]["construction"]
    return "unknown"


def savings_vs_naive(op: str) -> int:
    """Return node savings vs naive single-operator evaluation."""
    return NAIVE_COSTS.get(op, 0) - superbest_cost(op)


def route_expression(ops: list[str], positive_domain: bool = False) -> dict:
    """
    Given a list of arithmetic operations in an expression,
    return the SuperBEST routing and total node count.

    Args:
        ops: List of operation names, e.g., ["mul", "add", "exp"]
        positive_domain: If True, use positive-domain costs (pow=1n via EPL/ELMl).
                         Default: False uses general-domain costs (pow=3n).

    Returns:
        Dictionary with per-op routing and totals.
    """
    result: dict = {}
    total_superbest = 0
    total_naive = 0
    for op in ops:
        sb = predict_cost(op, positive_domain=positive_domain)
        naive = NAIVE_COSTS.get(op, 99)
        total_superbest += sb
        total_naive += naive
        construction = superbest_construction(op)
        if positive_domain and op == "pow":
            construction = SUPERBEST_TABLE.get("pow_pos", {}).get("construction", construction)
        result[op] = {
            "operator": superbest_operator(op),
            "nodes": sb,
            "naive_nodes": naive,
            "savings": naive - sb,
            "construction": construction,
            "domain": "positive" if positive_domain else "general",
        }
    result["__totals__"] = {
        "superbest_nodes": total_superbest,
        "naive_nodes": total_naive,
        "total_savings": total_naive - total_superbest,
        "savings_pct": round((1 - total_superbest / max(total_naive, 1)) * 100, 1),
        "domain_assumption": "positive (x > 0)" if positive_domain else "general (all reals)",
    }
    return result


def rewrite_python_expr(expr: str) -> str:
    """
    Naive regex-based rewriter: annotates Python expressions with SuperBEST operators.
    Not a full compiler — purely for demonstration of routing decisions.

    Args:
        expr: Python expression string, e.g., "x * y + math.exp(z)"

    Returns:
        Annotated string showing SuperBEST operator choices.
    """
    annotations = []
    if re.search(r"\*(?!\*)", expr):
        annotations.append(f"mul → {superbest_construction('mul')} (2n)")
    if "+" in expr:
        annotations.append(f"add → {superbest_construction('add')} (2n, all reals)")
    if "-" in expr and "exp" not in expr:
        annotations.append(f"sub → {superbest_construction('sub')} (2n)")
    if "exp(" in expr or "math.exp" in expr:
        annotations.append(f"exp → {superbest_construction('exp')} (1n)")
    if "log(" in expr or "math.log" in expr:
        annotations.append(f"ln → {superbest_construction('ln')} (1n)")
    if "/" in expr:
        annotations.append(f"div → {superbest_construction('div')} (2n)")
    return expr + "  # SuperBEST: " + "; ".join(annotations)


def superbest_summary(positive_domain: bool = False) -> str:
    """Return a human-readable summary of the SuperBEST v5.1 routing table.

    Args:
        positive_domain: If True, show positive-domain costs (pow=1n). Default: False.
    """
    domain_label = "Positive-Domain (x > 0)" if positive_domain else "General-Domain (all reals)"
    costs = SUPERBEST_COSTS_POS if positive_domain else SUPERBEST_COSTS_GEN
    headline = "16n / 78.1% savings" if positive_domain else "22n / 69.9% savings"
    lines = [
        f"SuperBEST v5.1 Routing Table — {domain_label}",
        f"Headline: {headline} vs naive 73n baseline",
        "Key results: add=2n ALL reals (ADD-T1); pow=1n positive (EPL/ELMl); mul=6n general",
        "=" * 72,
    ]
    lines.append(f"  {'Op':8} {'Nodes':6} {'Naive':6} {'Savings':8} {'Construction':40}")
    lines.append("-" * 72)
    total_sb = total_naive = 0
    ops_v5 = ["exp", "ln", "recip", "div", "neg", "mul", "sub", "add", "sqrt", "pow"]
    for op in ops_v5:
        sb = costs.get(op, 99)
        naive = NAIVE_COSTS.get(op, 0)
        total_sb += sb
        total_naive += naive
        if positive_domain and op == "pow":
            constr = SUPERBEST_TABLE.get("pow_pos", {}).get("construction", "epl(n,x)")
        else:
            constr = superbest_construction(op)
        savings_n = naive - sb
        lines.append(f"  {op:8} {sb:6} {naive:6} {savings_n:+8d} {constr:40}")
    lines.append("-" * 72)
    pct = (1 - total_sb / max(total_naive, 1)) * 100
    lines.append(f"  {'TOTAL':8} {total_sb:6} {total_naive:6} {total_naive-total_sb:+8d}")
    lines.append(f"  Savings: {pct:.1f}% vs naive {total_naive}n baseline")
    lines.append("  Key v5 result: add=2n for ALL reals via LEdiv(x,DEML(y,1))=x+y (ADD-T1)")
    if positive_domain:
        lines.append("  Key v5.1 result: pow=1n positive domain via EPL(n,x)=exp(n*ln(x))=x^n (X20)")
    return "\n".join(lines)
