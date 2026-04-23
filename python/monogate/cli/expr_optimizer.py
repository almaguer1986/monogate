"""Expression optimiser — paste a Python-style expression, get the SuperBEST
v5.2 EML decomposition.

Usage:
    python -m monogate.cli.expr_optimizer "exp(x) * y + ln(z)"
    python -m monogate.cli.expr_optimizer "1 / (1 + exp(-x))"

Exits 0 with a markdown-friendly report on stdout + a JSON block at the end
(so the tool is usable from CI or agent pipelines).

Parses via the stdlib `ast` module; no extra dependencies.  Supports:
    + - * / **   (arithmetic)
    exp, log, ln, sqrt, sin, cos, tan, abs   (unary function calls)
    Numeric literals (counted as free if 0 or 1, otherwise built).
    Variable names (inputs; 0n).

Costs follow SuperBEST v5.2:
    exp = ln = recip = pow = sqrt = 1
    mul_pos = div = neg = add = sub = abs = 2
    mul_gen = div_gen = 3
    sin/cos/tan = 1 (complex EML) — boundary.

Writes a compact JSON summary at the end of the report so an agent or
CI runner can pick it up with `python -m monogate.cli.expr_optimizer EXPR | tail -1`.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field


# SuperBEST v5.2 positive-domain op costs
SB = {
    "exp": 1, "ln": 1, "log": 1, "sqrt": 1, "pow": 1, "recip": 1,
    "mul": 2, "div": 2, "add": 2, "sub": 2, "neg": 2, "abs": 2,
    # Trig (boundary)
    "sin": 1, "cos": 1, "tan": 1,
}
# Naive (EML-only) costs from the v5.2 docstring
NV = {
    "exp": 1, "ln": 3, "log": 3, "sqrt": 8, "pow": 3, "recip": 5,
    "mul": 13, "div": 15, "add": 11, "sub": 5, "neg": 9, "abs": 5,
    "sin": 13, "cos": 13, "tan": 13,
}

TRIG_TOKENS = {"sin", "cos", "tan"}
PIECEWISE_TOKENS = {"abs"}


@dataclass
class OpUse:
    counts: dict = field(default_factory=dict)
    free_constants: int = 0
    non_free_constants: int = 0
    variables: set = field(default_factory=set)
    contains_trig: bool = False
    contains_piecewise: bool = False
    children: list["OpUse"] = field(default_factory=list)

    def add_op(self, name: str):
        self.counts[name] = self.counts.get(name, 0) + 1

    def merge(self, other: "OpUse"):
        for k, v in other.counts.items():
            self.counts[k] = self.counts.get(k, 0) + v
        self.free_constants += other.free_constants
        self.non_free_constants += other.non_free_constants
        self.variables |= other.variables
        self.contains_trig |= other.contains_trig
        self.contains_piecewise |= other.contains_piecewise

    def naive_cost(self) -> int:
        return sum(NV.get(op, 2) * n for op, n in self.counts.items())

    def sb_cost(self) -> int:
        return sum(SB.get(op, 2) * n for op, n in self.counts.items())


UNARY = {
    "exp": "exp", "log": "log", "ln": "log", "sqrt": "sqrt",
    "sin": "sin", "cos": "cos", "tan": "tan", "abs": "abs",
}


def walk(node: ast.AST) -> OpUse:
    """Walk a Python AST produced by `ast.parse(..., mode='eval')` and
    collect op counts.  Returns a single flat OpUse."""
    use = OpUse()
    if isinstance(node, ast.Expression):
        return walk(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            v = float(node.value)
            if v in (0.0, 1.0):
                use.free_constants += 1
            else:
                use.non_free_constants += 1
        return use
    if isinstance(node, ast.Name):
        use.variables.add(node.id)
        return use
    if isinstance(node, ast.UnaryOp):
        sub = walk(node.operand)
        use.merge(sub)
        if isinstance(node.op, ast.USub):
            use.add_op("neg")
        return use
    if isinstance(node, ast.BinOp):
        l = walk(node.left); r = walk(node.right)
        use.merge(l); use.merge(r)
        if isinstance(node.op, ast.Add):      use.add_op("add")
        elif isinstance(node.op, ast.Sub):    use.add_op("sub")
        elif isinstance(node.op, ast.Mult):   use.add_op("mul")
        elif isinstance(node.op, ast.Div):    use.add_op("div")
        elif isinstance(node.op, ast.Pow):    use.add_op("pow")
        return use
    if isinstance(node, ast.Call):
        fn = node.func.id if isinstance(node.func, ast.Name) else None
        if fn in UNARY:
            tag = UNARY[fn]
            use.add_op(tag)
            if tag in TRIG_TOKENS:
                use.contains_trig = True
            if tag in PIECEWISE_TOKENS:
                use.contains_piecewise = True
        for a in node.args:
            use.merge(walk(a))
        return use
    # fallthrough: recurse into any child with .body etc
    for child in ast.iter_child_nodes(node):
        use.merge(walk(child))
    return use


# Pattern hints — look at the op-count vector and guess whether a 1-node
# F16 primitive applies.  These are heuristic "paths" not formal rewrites.
def suggest_patterns(use: OpUse) -> list[str]:
    c = use.counts
    suggestions = []
    if c.get("exp", 0) >= 1 and c.get("log", 0) >= 1:
        suggestions.append(
            "exp and log co-occur — check whether the expression is an "
            "F16 hybrid primitive (EML/EAL/EXL/EDL/LEAd/LEdiv/ELAd/ELSb). "
            "If so, cost collapses to a single node."
        )
    if c.get("exp", 0) >= 1 and c.get("add", 0) >= 1:
        suggestions.append(
            "If the expression is exp(x + ln(y)) it folds to ELAd(x, y) = "
            "e^x · y  at 1n (SuperBEST).  Check for this fold."
        )
    if c.get("exp", 0) >= 1 and c.get("sub", 0) >= 1:
        suggestions.append(
            "If the expression is exp(x - ln(y)) it folds to ELSb(x, y) = "
            "e^x / y  at 1n.  Check for this fold."
        )
    if c.get("log", 0) >= 1 and c.get("exp", 0) >= 1 and c.get("add", 0) >= 1:
        suggestions.append(
            "ln(exp(x) + 1) = softplus(x) = LEAd(x, 1) at 1n.  "
            "ln(exp(x) + y) = LEAd(x, y) at 1n."
        )
    if c.get("pow", 0) >= 1:
        suggestions.append(
            "x^k for x > 0 is a 1-node EPL/ELMl primitive.  If the AST "
            "counted x^k as `pow=1`, you're already at the optimum."
        )
    return suggestions


def analyse(expr: str) -> dict:
    tree = ast.parse(expr, mode="eval")
    use = walk(tree)
    elc = (
        "outside_piecewise" if use.contains_piecewise else
        "boundary" if use.contains_trig else
        "inside"
    )
    naive = use.naive_cost()
    sb = use.sb_cost()
    savings_pct = round((1 - sb / naive) * 100, 2) if naive > 0 else 0.0
    return {
        "expression": expr,
        "variables": sorted(use.variables),
        "free_constants": use.free_constants,
        "non_free_constants": use.non_free_constants,
        "op_counts": dict(use.counts),
        "naive_cost": naive,
        "superbest_cost": sb,
        "savings_pct_on_ops": savings_pct,
        "elc_class": elc,
        "suggestions": suggest_patterns(use),
    }


def print_report(report: dict):
    print(f"# Expression optimiser — `{report['expression']}`\n")
    print(f"- ELC class: **{report['elc_class']}**")
    print(f"- Variables: {', '.join(report['variables']) or '(none)'}")
    print(f"- Free constants ({{0, 1}}): {report['free_constants']}")
    print(f"- Non-free constants built from {{0, 1}}: {report['non_free_constants']}  "
          f"(add ~2n per construct step)")
    print()
    print("| Op | Count | SB cost | Naive cost |")
    print("|---|---|---|---|")
    for op, n in sorted(report["op_counts"].items()):
        sb = SB.get(op, 2) * n
        nv = NV.get(op, 2) * n
        print(f"| `{op}` | {n} | {sb}n | {nv}n |")
    print()
    print(f"**Totals**: naive **{report['naive_cost']}n** → "
          f"SuperBEST **{report['superbest_cost']}n** "
          f"(**{report['savings_pct_on_ops']}%** reduction on counted ops).")
    if report["suggestions"]:
        print("\n**Fold suggestions**:")
        for s in report["suggestions"]:
            print(f"- {s}")
    # Machine-readable tail (agents / CI)
    print()
    print(json.dumps({"capcard_expr": report}, ensure_ascii=False, separators=(",", ":")))


def main(argv=None):
    ap = argparse.ArgumentParser(description="SuperBEST EML cost estimator for a mathematical expression")
    ap.add_argument("expr", nargs="?", help="Expression, e.g. \"exp(x) * y + ln(z)\"")
    ap.add_argument("--json", action="store_true", help="Emit only the JSON summary")
    args = ap.parse_args(argv)
    if not args.expr:
        ap.error("give an expression as the first argument, "
                 "e.g. python -m monogate.cli.expr_optimizer \"exp(x) * y\"")
    rep = analyse(args.expr)
    if args.json:
        sys.stdout.write(json.dumps(rep, indent=2, ensure_ascii=False) + "\n")
    else:
        print_report(rep)


if __name__ == "__main__":
    main()
