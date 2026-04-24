"""
SuperBEST Router — Dynamic Per-Operation Operator Selection
Finds the minimum-node operator for each arithmetic primitive in an expression tree.

Author: Monogate Research
Version: v5.3 (2026-04-23) — sqrt positive 2n -> 1n reconciliation

Canonical headlines (library-level; public capcard sync pending user review):
  - Positive domain (10 ops: exp, ln, neg, add, sub, mul, div, recip, pow, sqrt):
        14n / 80.8% savings vs 73n naive
  - General domain (8 ops: exp, ln, mul, div, neg, add, sub, abs):
        16n / 74.2% savings vs 62n naive

v5.2 -> v5.3 change (2026-04-23):
  - sqrt positive: 2n -> 1n
        Reconciles library with UpperBounds.lean theorem `sqrt_one_node_positive'`
        (F13(1/2, x) = exp((1/2)*log(x)) = sqrt(x) for x > 0 — single F16 node).
        v5.2 had retained the older 2-node construction EML(0.5*EXL(0,x), 1);
        the Lean 0-sorry proof establishes the 1-node EPL form as canonical.
  - positive headline: 15n/79.5% -> 14n/80.8%
  - general headline unchanged (sqrt is not part of the 8-op general basket).

v5.1 -> v5.2 changes (2026-04-22):
  - mul positive: 2n -> 1n         (UpperBounds.lean one-node F16 construction)
  - mul general:  6n -> 3n         (Python exact: 3n direct construction via DEML/EXL shell)
  - div general:  2n -> 3n         (DivLowerBound3Full.lean: SB(div, general) >= 3)
  - abs entry:    new  abs=2n      (2-node EPL construction, symmetric in both domains)
  - pow naive:    15 -> 3          (aligns per-op naive sums with CapCard 73n/62n baselines)
  - positive headline: 16n/78.1% -> 15n/79.5%
  - general  headline: 22n/69.9% -> 16n/74.2%

v5.1 retained (unchanged):
  - pow positive: 1n (EPL/ELMl direct: exp(n*ln(x)) = x^n)
  - add = 2n for ALL reals via LEdiv(x, DEML(y,1)) = x + y (ADD-T1)
  - sub = 2n via LEdiv(x, EML(y,1))
  - neg = 2n via EXL(0, DEML(x,1))

References:
  capability_card_public.json  (canonical totals and per-op claims; public sync pending)
  MonogateEML/UpperBounds.lean (1-node positive bounds for exp, mul, pow, recip, sqrt;
                                sqrt_one_node_positive' theorem, line 76, 0 sorries)
  MonogateEML/DivLowerBound3Full.lean (SB(div, general) >= 3)
  ADD_T1_General_Addition_2n.tex
"""
from __future__ import annotations
import re


# ---------------------------------------------------------------------------
# Canonical v5.2 headline constants (agree with capability_card_public.json)
# ---------------------------------------------------------------------------

# v5.3 library-level totals (public capcard sync pending user review):
#   positive, 10 ops: total_nodes = 14, naive_total = 73, savings = 80.8%
# Legacy alias names (V52_*) retained for back-compat imports.
SUPERBEST_V53_POS_TOTAL = 14
SUPERBEST_V53_POS_NAIVE = 73
SUPERBEST_V53_POS_SAVINGS_PCT = 80.8
# Back-compat aliases (callers importing V52_* still resolve to current totals).
SUPERBEST_V52_POS_TOTAL = SUPERBEST_V53_POS_TOTAL
SUPERBEST_V52_POS_NAIVE = SUPERBEST_V53_POS_NAIVE
SUPERBEST_V52_POS_SAVINGS_PCT = SUPERBEST_V53_POS_SAVINGS_PCT

# Recomputed 2026-04-22 for the 8-op general-domain table.
SUPERBEST_V52_GEN_TOTAL = 16
SUPERBEST_V52_GEN_NAIVE = 62
SUPERBEST_V52_GEN_SAVINGS_PCT = 74.2

# Canonical op lists per the CapCard's descriptions.
SUPERBEST_V52_POS_OPS = (
    "exp", "ln", "neg", "add", "sub", "mul", "div", "recip", "pow", "sqrt",
)
SUPERBEST_V52_GEN_OPS = (
    "exp", "ln", "mul", "div", "neg", "add", "sub", "abs",
)


# ---------------------------------------------------------------------------
# Per-op node costs (v5.2)
# ---------------------------------------------------------------------------

# Naive EML-tree costs (no SuperBEST routing). Sums over the canonical op
# lists match the CapCard baselines:
#   sum over SUPERBEST_V52_POS_OPS = 73
#   sum over SUPERBEST_V52_GEN_OPS = 62
NAIVE_COSTS: dict[str, int] = {
    "exp": 1,
    "ln": 3,
    "mul": 13,
    "div": 15,
    "add": 11,
    "sub": 5,
    "neg": 9,
    "recip": 5,
    "sqrt": 8,
    "pow": 3,
    "abs": 5,
    "sin": 13,
    "cos": 13,
}

# Positive-domain v5.3 costs. Sum over SUPERBEST_V52_POS_OPS = 14n.
SUPERBEST_COSTS_POS: dict[str, int] = {
    "exp": 1,
    "ln": 1,
    "neg": 2,
    "add": 2,
    "sub": 2,
    "mul": 1,   # v5.2: UpperBounds.lean 1-node F16 construction (was 2n in v5.1)
    "div": 2,   # v5.2: DivLowerBound3 2-node positive construction
    "recip": 1,
    "pow": 1,   # v5.1 retained: EPL/ELMl direct
    "sqrt": 1,  # v5.3: UpperBounds.lean sqrt_one_node_positive' — F13(1/2, x) (was 2n)
    "abs": 2,
    "sin": 1,   # via complex EML
    "cos": 1,
}

# General-domain v5.2 costs. Sum over SUPERBEST_V52_GEN_OPS = 16n.
# (pow, sqrt, recip are not part of the canonical 8-op general headline — the
#  entries below are retained for back-compat callers only.)
SUPERBEST_COSTS_GEN: dict[str, int] = {
    "exp": 1,
    "ln": 1,
    "neg": 2,
    "add": 2,
    "sub": 2,
    "mul": 3,   # v5.2: Python exact general-domain 3-node construction (was 6n in v5.1)
    "div": 3,   # v5.2: DivLowerBound3Full.lean SB(div, general) >= 3 (was 2n in v5.1)
    "recip": 1,
    "pow": 3,
    "sqrt": 2,
    "abs": 2,
    "sin": 1,
    "cos": 1,
}

# Legacy unified table (pre-v5.2 callers) — points at positive-domain costs.
SUPERBEST_COSTS_V5: dict[str, int] = dict(SUPERBEST_COSTS_POS)


# ---------------------------------------------------------------------------
# Operator / construction table (display metadata; canonical costs live in the
# dicts above)
# ---------------------------------------------------------------------------

SUPERBEST_TABLE: dict[str, dict] = {
    "exp": {"operator": "EML", "nodes": 1, "domain": "all x",
            "construction": "eml(x, 1)"},
    "ln":  {"operator": "EXL", "nodes": 1, "domain": "x > 0",
            "construction": "exl(0, x)"},
    "mul": {"operator": "EPL/ELMl", "nodes": 1, "domain": "x, y > 0",
            "construction": "elml(ln x, y) = exp(ln x + ln y) = x*y (UpperBounds)",
            "nodes_gen": 3, "construction_gen": "3-node DEML/EXL shell (Python exact)"},
    "div": {"operator": "Mixed(EXL/ELSb)", "nodes": 2, "domain": "x, y > 0",
            "construction": "elsb(exl(0, x), y)",
            "nodes_gen": 3, "construction_gen": "3-node (DivLowerBound3Full tight)"},
    "add": {"operator": "Mixed(DEML/LEdiv)", "nodes": 2, "domain": "all x, y",
            "construction": "lediv(x, deml(y, 1))",
            "note": "2 nodes for ALL reals via ADD-T1"},
    "sub": {"operator": "Mixed(EML/LEdiv)", "nodes": 2, "domain": "all x, y",
            "construction": "lediv(x, eml(y, 1))"},
    "sqrt": {"operator": "EPL (F13)", "nodes": 1, "domain": "x > 0",
             "construction": "epl(1/2, x) = exp((1/2)*ln(x)) (UpperBounds.lean)"},
    "neg": {"operator": "Mixed(EXL/DEML)", "nodes": 2, "domain": "all x",
            "construction": "exl(0, deml(x, 1))"},
    "recip": {"operator": "ELSb", "nodes": 1, "domain": "x != 0",
              "construction": "elsb(0, x)"},
    "pow": {"operator": "EPL/ELMl", "nodes": 1, "domain": "x > 0",
            "construction": "epl(n, x) = exp(n*ln(x)) = x^n",
            "nodes_gen": 3, "construction_gen": "eml(exl(ln(n), x), 1)"},
    "abs": {"operator": "2-node EPL", "nodes": 2, "domain": "all x",
            "construction": "sqrt(x^2) via 2-node EPL construction"},
    "sin": {"operator": "EML (complex)", "nodes": 1, "domain": "all x",
            "construction": "Im(eml(i*x, 1))"},
    "cos": {"operator": "EML (complex)", "nodes": 1, "domain": "all x",
            "construction": "Re(eml(i*x, 1))"},
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def superbest_cost(op: str, positive_domain: bool = True) -> int:
    """Return the SuperBEST node cost for an operation under the chosen domain."""
    table = SUPERBEST_COSTS_POS if positive_domain else SUPERBEST_COSTS_GEN
    return table.get(op, NAIVE_COSTS.get(op, 99))


def predict_cost(op: str, positive_domain: bool = False) -> int:
    """Return the predicted v5.2 SuperBEST node cost.

    Args:
        op: Operation name.
        positive_domain: If True, use positive-domain costs. Default: False (general).

    Returns:
        Minimum node count under the selected domain.
    """
    return superbest_cost(op, positive_domain=positive_domain)


def superbest_operator(op: str) -> str:
    if op in SUPERBEST_TABLE:
        return SUPERBEST_TABLE[op]["operator"]
    return "unknown"


def superbest_construction(op: str, positive_domain: bool = True) -> str:
    entry = SUPERBEST_TABLE.get(op)
    if entry is None:
        return "unknown"
    if not positive_domain and "construction_gen" in entry:
        return entry["construction_gen"]
    return entry["construction"]


def savings_vs_naive(op: str, positive_domain: bool = True) -> int:
    return NAIVE_COSTS.get(op, 0) - superbest_cost(op, positive_domain=positive_domain)


def route_expression(ops: list[str], positive_domain: bool = False) -> dict:
    """Route a list of arithmetic operations using v5.2 SuperBEST costs.

    Args:
        ops: List of operation names, e.g. ["mul", "add", "exp"].
        positive_domain: If True, use positive-domain costs.

    Returns:
        dict mapping op -> routing info, plus a "__totals__" entry.
    """
    result: dict = {}
    total_superbest = 0
    total_naive = 0
    for op in ops:
        sb = predict_cost(op, positive_domain=positive_domain)
        naive = NAIVE_COSTS.get(op, 99)
        total_superbest += sb
        total_naive += naive
        result[op] = {
            "operator": superbest_operator(op),
            "nodes": sb,
            "naive_nodes": naive,
            "savings": naive - sb,
            "construction": superbest_construction(op, positive_domain=positive_domain),
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
    """Annotate a Python expression with SuperBEST operator choices (demo only)."""
    annotations = []
    if re.search(r"\*(?!\*)", expr):
        annotations.append(f"mul -> {superbest_construction('mul')} (1n pos)")
    if "+" in expr:
        annotations.append(f"add -> {superbest_construction('add')} (2n, all reals)")
    if "-" in expr and "exp" not in expr:
        annotations.append(f"sub -> {superbest_construction('sub')} (2n)")
    if "exp(" in expr or "math.exp" in expr:
        annotations.append(f"exp -> {superbest_construction('exp')} (1n)")
    if "log(" in expr or "math.log" in expr:
        annotations.append(f"ln -> {superbest_construction('ln')} (1n)")
    if "/" in expr:
        annotations.append(f"div -> {superbest_construction('div')} (2n)")
    return expr + "  # SuperBEST: " + "; ".join(annotations)


def superbest_summary(positive_domain: bool = False) -> str:
    """Return a human-readable v5.2 routing table summary.

    Args:
        positive_domain: If True, show the 10-op positive table (14n / 80.8%).
                         If False (default), show the 8-op general table (16n / 74.2%).
    """
    if positive_domain:
        domain_label = "Positive-Domain (x > 0)"
        costs = SUPERBEST_COSTS_POS
        ops = SUPERBEST_V52_POS_OPS
        total_sb = SUPERBEST_V52_POS_TOTAL
        total_naive = SUPERBEST_V52_POS_NAIVE
        savings_pct = SUPERBEST_V52_POS_SAVINGS_PCT
    else:
        domain_label = "General-Domain (all reals)"
        costs = SUPERBEST_COSTS_GEN
        ops = SUPERBEST_V52_GEN_OPS
        total_sb = SUPERBEST_V52_GEN_TOTAL
        total_naive = SUPERBEST_V52_GEN_NAIVE
        savings_pct = SUPERBEST_V52_GEN_SAVINGS_PCT

    headline = f"{total_sb}n / {savings_pct}% savings"
    lines = [
        f"SuperBEST v5.2 Routing Table - {domain_label}",
        f"Headline: {headline} vs naive {total_naive}n baseline ({len(ops)} ops)",
        "Key v5.2: mul_pos=1 (UpperBounds), mul_gen=3, div_gen=3 (DivLowerBound3Full), add=2 all reals (ADD-T1)",
        "=" * 72,
        f"  {'Op':8} {'Nodes':6} {'Naive':6} {'Savings':8} {'Construction':40}",
        "-" * 72,
    ]

    computed_sb = 0
    computed_naive = 0
    for op in ops:
        sb = costs.get(op, 99)
        naive = NAIVE_COSTS.get(op, 0)
        computed_sb += sb
        computed_naive += naive
        constr = superbest_construction(op, positive_domain=positive_domain)
        savings_n = naive - sb
        lines.append(f"  {op:8} {sb:6} {naive:6} {savings_n:+8d} {constr:40}")

    lines.append("-" * 72)
    lines.append(f"  {'TOTAL':8} {computed_sb:6} {computed_naive:6} {computed_naive - computed_sb:+8d}")
    lines.append(
        f"  Savings: {(1 - computed_sb / max(computed_naive, 1)) * 100:.1f}% "
        f"vs naive {computed_naive}n baseline"
    )

    if computed_sb != total_sb or computed_naive != total_naive:
        lines.append(
            f"  WARNING: per-op sum ({computed_sb}n / {computed_naive}n) disagrees with "
            f"declared v5.2 headline ({total_sb}n / {total_naive}n). "
            "Fix the per-op entries or the headline constants."
        )

    return "\n".join(lines)
