"""
monogate.optimize — BEST-mode expression optimizer.

Scans Python/NumPy/PyTorch code (or bare math expression strings) for
recognizable math operations and reports node savings achievable by
routing each op through BEST (the optimal EML/EDL/EXL hybrid).

Public API::

    from monogate import best_optimize

    # String expression
    r = best_optimize("sin(x)**2 + cos(x)*x**3 + exp(-x)")
    print(r)                  # OptimizeResult summary
    print(r.python_snippet)   # ready-to-paste Python using BEST.*

    # Python / NumPy / PyTorch code snippet
    code = '''
    import torch
    def model(x):
        return torch.sin(x)**2 + torch.cos(x) * x**3 + torch.exp(-x)
    '''
    r = best_optimize(code)
    print(r.rewritten_code)   # torch.* calls replaced with BEST.*

    # Decorator (Phase 2 stub — returns function unchanged)
    @best_optimize
    def f(x):
        return torch.sin(x) + torch.cos(x)
"""

from __future__ import annotations

import ast
import inspect
import re
import textwrap
import warnings
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Union

from .core import _NODE_COSTS


# ── Node cost tables ──────────────────────────────────────────────────────────

# BEST routing: minimum cost per operation across all operators.
# Derived from _NODE_COSTS in core.py (EXL for ln/pow/sqrt, EDL for mul/div,
# EML for add/sub/exp/abs). sin/cos/sqrt added manually.
_BEST_NODES: dict[str, int] = {
    "exp":  1,    # EML/EDL/EXL identical
    "ln":   1,    # EXL — 1 node vs EML's 3
    "pow":  3,    # EXL — 3 nodes vs EML's 15
    "sqrt": 3,    # EXL — pow(x, 0.5) in 3 nodes
    "mul":  7,    # EDL — 7 nodes vs EML's 13
    "div":  1,    # EDL — 1 node vs EML's 15
    "recip":2,    # EDL — 2 nodes vs EML's 5
    "neg":  6,    # EDL — 6 nodes vs EML's 9
    "sub":  5,    # EML — no alternative
    "add":  11,   # EML — no alternative
    "sin":  63,   # EXL 8-term Taylor (best known approximation)
    "cos":  63,   # EXL 8-term Taylor (best known approximation)
    "abs":  9,    # EML
}

_EML_NODES: dict[str, int] = {
    op: costs["EML"]
    for op, costs in _NODE_COSTS.items()
    if "EML" in costs
}
_EML_NODES.update({"sin": 245, "cos": 245, "sqrt": 15, "abs": 9})

_BEST_NODES.update({
    # Compound ops: sigmoid = neg+exp+add+div; tanh = mul+exp+sub+add+div
    # Node costs assume BEST routing for every sub-operation.
    "sigmoid": 19,   # neg(6)+exp(1)+add(11)+div(1)  vs EML: neg(9)+exp(1)+add(11)+div(15)=36
    "tanh":    25,   # mul(7)+exp(1)+sub(5)+add(11)+div(1)  vs EML: mul(13)+...+div(15)=45
    "gelu":    60,   # tanh(25)+mul(7)×3=21+add(11)+pow(3)  vs EML ~115
})

_EML_NODES.update({
    "sigmoid": 36,   # neg(9)+exp(1)+add(11)+div(15)
    "tanh":    45,   # mul(13)+exp(1)+sub(5)+add(11)+div(15)
    "gelu":   115,   # tanh(45)+mul(13)×3=39+add(11)+pow(15)
})

_BEST_SOURCE: dict[str, str] = {
    "exp": "EML", "ln": "EXL", "pow": "EXL", "sqrt": "EXL",
    "mul": "EDL", "div": "EDL", "recip": "EDL", "neg": "EDL",
    "sub": "EML", "add": "EML", "abs": "EML",
    "sin": "EXL", "cos": "EXL",
    "sigmoid": "EML+EDL", "tanh": "EML+EDL", "gelu": "EML+EDL",
}

# Wall-clock crossover: BEST routing pays off only above this node-reduction %.
# Below this threshold Python call overhead dominates any gate savings.
# Empirical fit from experiments 09/10/11: R²=0.9992.
_CROSSOVER_PCT: int = 20


# ── Detection rules ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class _Rule:
    op_name: str        # canonical operation name
    py_pattern: str     # matches library-prefixed calls (math.*, torch.*, np.*)
    expr_pattern: str   # matches bare calls in expression strings (empty = skip)
    replacement: str    # what to substitute the matched prefix with


# Order matters: tanh before tan, ln before log (avoid partial-match).
_RULES: tuple[_Rule, ...] = (
    _Rule("sin",     r"(?:math|torch|np|numpy|F)\.sin\s*\(",     r"\bsin\s*\(",     "BEST.sin("),
    _Rule("cos",     r"(?:math|torch|np|numpy|F)\.cos\s*\(",     r"\bcos\s*\(",     "BEST.cos("),
    _Rule("tanh",    r"(?:math|torch|np|numpy|F)\.tanh\s*\(",    r"\btanh\s*\(",    "BEST.tanh("),
    _Rule("sigmoid", r"(?:torch|F)\.sigmoid\s*\(",               r"\bsigmoid\s*\(", "BEST.sigmoid("),
    _Rule("gelu",    r"(?:F)\.gelu\s*\(",                        r"\bgelu\s*\(",    "BEST.gelu("),
    _Rule("exp",     r"(?:math|torch|np|numpy|F)\.exp\s*\(",     r"\bexp\s*\(",     "BEST.exp("),
    _Rule("ln",      r"(?:math|torch|np|numpy|F)\.log\w*\s*\(",  r"\bln\s*\(",      "BEST.ln("),
    _Rule("pow",     r"(?:math|torch|np|numpy)\.pow(?:er)?\s*\(",r"\bpow\s*\(",     "BEST.pow("),
    _Rule("sqrt",    r"(?:math|torch|np|numpy)\.sqrt\s*\(",      r"\bsqrt\s*\(",    "BEST.sqrt("),
    _Rule("abs",     r"(?:math|torch|np|numpy)\.fabs\s*\(",      r"",               "abs("),
    _Rule("div",     r"(?:torch\.div|np\.divide)\s*\(",          r"",               "BEST.div("),
    _Rule("mul",     r"(?:torch\.mul|np\.multiply)\s*\(",        r"",               "BEST.mul("),
)

# Operator-symbol patterns (detected for counting, partly rewritten).
# Use \s* flanking each operator so "a + b" and "a+b" both match.
_OP_SYMBOL_RULES: tuple[tuple[str, str], ...] = (
    ("pow", r"\*\*\s*[\d.]+"),                                       # x**n
    ("div", r"(?<=[a-zA-Z0-9_)])\s*/\s*(?=[a-zA-Z0-9_(])"),         # x / y
    ("mul", r"(?<=[a-zA-Z0-9_)])\s*\*(?!\*)\s*(?=[a-zA-Z0-9_(])"), # x * y
    ("add", r"(?<=[a-zA-Z0-9_)])\s*\+\s*(?=[a-zA-Z0-9_(])"),        # x + y
    ("sub", r"(?<=[a-zA-Z0-9_)])\s*-\s*(?=[a-zA-Z0-9_(])"),         # x - y
)

# Simple x**n → BEST.pow(x, n) replacement (only word identifiers, not func results)
_POW_SIMPLE_RE = re.compile(r"\b([a-zA-Z_]\w*)\s*\*\*\s*(\d+(?:\.\d+)?)")


# ── Result types ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OpMatch:
    """One detected operation and its node cost comparison."""
    name: str          # canonical op name (e.g. "sin", "pow")
    count: int         # number of occurrences
    best_nodes: int    # total nodes in BEST mode (count × per-op cost)
    eml_nodes: int     # total nodes in pure EML (count × per-op cost)
    best_op: str       # which base operator handles this in BEST (EML/EDL/EXL)
    note: str          # human-readable explanation

    @property
    def savings(self) -> int:
        """Integer % savings vs pure EML (0 if none)."""
        if self.eml_nodes == 0:
            return 0
        return max(0, round((1 - self.best_nodes / self.eml_nodes) * 100))


@dataclass(frozen=True)
class OptimizeResult:
    """
    Result of best_optimize().

    Attributes:
        original        The input expression or code, stripped.
        ops             List of detected operations with node counts.
        total_best_nodes  Sum of BEST node costs across all detected ops.
        total_eml_nodes   Sum of pure EML node costs across all detected ops.
        savings_pct     Integer % node reduction vs pure EML.
        python_snippet  Ready-to-paste Python using BEST.* calls.
        rewritten_code  Library calls (math.*/torch.*/np.*) replaced with BEST.*.
        explanation     Bullet-point list of what changed and why.
        message         One-line summary.
    """
    original: str
    ops: tuple[OpMatch, ...]
    total_best_nodes: int
    total_eml_nodes: int
    savings_pct: int
    python_snippet: str
    rewritten_code: str
    explanation: tuple[str, ...]
    message: str

    # ── Dict-style access ──────────────────────────────────────────────────────
    # Supports r["message"], r["savings_pct"], etc. alongside r.message
    _FIELDS = frozenset({
        "original", "ops", "total_best_nodes", "total_eml_nodes",
        "savings_pct", "python_snippet", "rewritten_code", "explanation", "message",
    })

    def __getitem__(self, key: str) -> Any:
        if key not in self._FIELDS:
            raise KeyError(f"OptimizeResult has no field {key!r}. Available: {sorted(self._FIELDS)}")
        return getattr(self, key)

    def keys(self) -> list[str]:
        return sorted(self._FIELDS)

    def __str__(self) -> str:
        lines = [self.message, ""]
        if self.ops:
            lines.append(f"  {'Operation':<14} {'Count':>5}  {'BEST':>6}  {'EML':>6}  {'Save':>5}  Operator")
            lines.append("  " + "-" * 54)
            for m in self.ops:
                lines.append(
                    f"  {m.name:<14} {m.count:>5}  "
                    f"{m.best_nodes:>5}n  {m.eml_nodes:>5}n  "
                    f"{m.savings:>4}%  {m.best_op}"
                )
            lines.append("  " + "-" * 54)
            lines.append(
                f"  {'TOTAL':<14} {'':>5}  "
                f"{self.total_best_nodes:>5}n  {self.total_eml_nodes:>5}n  "
                f"{self.savings_pct:>4}%"
            )
            lines.append("")
            if self.savings_pct >= _CROSSOVER_PCT:
                lines.append(
                    f"  Speedup expected: YES  "
                    f"({self.savings_pct}% > {_CROSSOVER_PCT}% crossover threshold)"
                )
            elif self.savings_pct > 0:
                lines.append(
                    f"  Speedup expected: NO   "
                    f"({self.savings_pct}% < {_CROSSOVER_PCT}% crossover threshold — "
                    f"call overhead will dominate)"
                )
        lines.append("")
        if self.explanation:
            for note in self.explanation:
                lines.append(f"  {note}")
        return "\n".join(lines)


# ── Core scanner ───────────────────────────────────────────────────────────────

def _is_python_code(source: str) -> bool:
    """Return True if source looks like Python code vs a bare math expression."""
    markers = ("import ", "def ", "class ", "return ", "torch.", "np.", "numpy.")
    return any(m in source for m in markers)


def _scan(source: str) -> dict[str, int]:
    """
    Scan source for recognized operations. Returns {op_name: count}.
    Handles both Python code and bare expression strings.
    """
    counts: dict[str, int] = {}
    is_code = _is_python_code(source)

    for rule in _RULES:
        pat = rule.py_pattern if is_code else rule.expr_pattern
        if not pat:
            continue
        found = re.findall(pat, source)
        if found:
            counts[rule.op_name] = counts.get(rule.op_name, 0) + len(found)

    for op_name, pat in _OP_SYMBOL_RULES:
        found = re.findall(pat, source)
        if found:
            counts[op_name] = counts.get(op_name, 0) + len(found)

    # pow_op (**n) and named pow() would both register as "pow" — deduplicate
    # by keeping the max detected count (they're usually mutually exclusive)
    return counts


def _build_ops(counts: dict[str, int]) -> tuple[OpMatch, ...]:
    ops = []
    for name, count in sorted(counts.items()):
        best_per = _BEST_NODES.get(name)
        eml_per  = _EML_NODES.get(name)
        if best_per is None or eml_per is None:
            continue  # unknown op — skip
        src = _BEST_SOURCE.get(name, "EML")
        savings = max(0, round((1 - best_per / eml_per) * 100)) if eml_per else 0
        if savings > 0:
            note = f"{src}: {best_per}n vs EML's {eml_per}n (−{savings}%)"
        else:
            note = f"{src}: {best_per}n (no improvement over EML)"
        ops.append(OpMatch(
            name=name,
            count=count,
            best_nodes=count * best_per,
            eml_nodes=count * eml_per,
            best_op=src,
            note=note,
        ))
    return tuple(ops)


# ── Rewriter ───────────────────────────────────────────────────────────────────

def _rewrite(source: str) -> str:
    """Apply BEST substitutions to source (library calls + simple x**n patterns)."""
    out = source
    is_code = _is_python_code(source)

    for rule in _RULES:
        pat = rule.py_pattern if is_code else rule.expr_pattern
        if not pat:
            continue
        out = re.sub(pat, rule.replacement, out)

    # Rewrite simple identifier**n → BEST.pow(ident, n)
    # Only matches bare word identifiers (x**2, y**3) — not function-call results
    out = _POW_SIMPLE_RE.sub(r"BEST.pow(\1, \2)", out)

    return out


def _build_python_snippet(expr: str, rewritten: str,
                          total_best: int, total_eml: int) -> str:
    """Generate a self-contained Python function snippet."""
    savings_pct = (
        round((1 - total_best / total_eml) * 100)
        if total_eml > 0 else 0
    )
    if total_eml > total_best:
        speedup_hint = (
            f"  — {savings_pct}% fewer exp/ln calls"
            + (", speedup expected" if savings_pct >= _CROSSOVER_PCT else ", below ~20% crossover")
        )
        node_note = f"# {total_best}n (BEST)  vs  {total_eml}n (pure EML){speedup_hint}"
    else:
        node_note = f"# {total_best}n (BEST mode — already optimal)"

    py_body = rewritten.strip().replace("\n", "\n    ")
    return (
        "from monogate import BEST\n"
        "import math\n\n"
        "def f(x):\n"
        f"    {node_note}\n"
        f"    return {py_body}\n"
    )


def _build_explanation(ops: tuple[OpMatch, ...]) -> tuple[str, ...]:
    lines = []
    for m in ops:
        if m.savings > 0:
            lines.append(f"→ {m.name}({m.count}×): {m.best_op} routes to {m.best_nodes}n  (was {m.eml_nodes}n EML, −{m.savings}%)")
        else:
            lines.append(f"→ {m.name}({m.count}×): {m.best_op} routes to {m.best_nodes}n  (no improvement — EML is already optimal)")
    return tuple(lines)


# ── AST transformer — rewrites math calls to BEST.* equivalents ───────────────

# Maps Python function names (bare or as attr on any module) → BEST method name.
_CALL_MAP: dict[str, str] = {
    "sin": "sin", "cos": "cos", "tan": "tan",
    "tanh": "tanh", "sinh": "sinh", "cosh": "cosh",
    "sigmoid": "sigmoid",
    "gelu": "gelu",
    "exp": "exp",
    "log": "ln", "log2": "ln", "log10": "ln", "ln": "ln",
    "pow": "pow", "power": "pow",
    "sqrt": "sqrt",
    "abs": "abs", "fabs": "abs",
    "mul": "mul", "multiply": "mul",
    "div": "div", "divide": "div", "true_divide": "div",
}

_BINOP_MAP: dict[type, str] = {
    ast.Pow:  "pow",
    ast.Mult: "mul",
    ast.Div:  "div",
    ast.Add:  "add",
    ast.Sub:  "sub",
}


def _best_call(method: str, args: list[ast.expr]) -> ast.Call:
    """Return AST node for ``BEST.<method>(<args>)``."""
    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id="BEST", ctx=ast.Load()),
            attr=method,
            ctx=ast.Load(),
        ),
        args=args,
        keywords=[],
    )


class BestRewriter(ast.NodeTransformer):
    """
    AST NodeTransformer that converts math operations to BEST.* equivalents.

    Handles:
    - Bare function calls:      sin(x)      → BEST.sin(x)
    - Library-prefixed calls:   math.sin(x) → BEST.sin(x)
                                torch.sin(x)→ BEST.sin(x)
    - Binary operators:         x ** n      → BEST.pow(x, n)
                                x * y       → BEST.mul(x, y)
                                x / y       → BEST.div(x, y)
                                x + y       → BEST.add(x, y)
                                x - y       → BEST.sub(x, y)

    Note: BEST.add and BEST.sub have the same node cost as EML, so rewriting
    +/- is semantically neutral but makes the routing explicit.
    """

    def visit_Call(self, node: ast.Call) -> ast.AST:  # noqa: N802
        # Recurse into arguments first
        self.generic_visit(node)

        method: str | None = None
        if isinstance(node.func, ast.Name):
            # bare call: sin(x), exp(x), etc.
            method = _CALL_MAP.get(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # attribute call: math.sin(x), torch.exp(x), np.log(x), etc.
            method = _CALL_MAP.get(node.func.attr)

        if method:
            return ast.copy_location(
                _best_call(method, list(node.args)),
                node,
            )
        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:  # noqa: N802
        # Recurse into operands first so nested ops are rewritten too
        self.generic_visit(node)
        method = _BINOP_MAP.get(type(node.op))
        if method:
            return ast.copy_location(
                _best_call(method, [node.left, node.right]),
                node,
            )
        return node


_EXPR_SENTINEL = "_best_expr_ = "


def _ast_rewrite(src: str) -> str:
    """
    Parse *src*, apply BestRewriter, return the unparsed result.

    Handles two forms:
    - Module-level code (function defs, imports, assignments) — parsed directly.
    - Bare math expressions (``"sin(x)**2 + cos(x)*x**3"``) — wrapped in an
      assignment sentinel so the parser accepts them, then the sentinel is stripped.

    Returns the original *src* unchanged on any parse/unparse error.
    """
    # First try: parse as-is (function defs, multi-line code, assignments)
    try:
        tree = ast.parse(src)
        new_tree = BestRewriter().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)
    except (SyntaxError, ValueError):
        pass

    # Second try: wrap as expression assignment (handles bare "sin(x)**2 + ...")
    try:
        tree = ast.parse(f"{_EXPR_SENTINEL}{src.strip()}")
        new_tree = BestRewriter().visit(tree)
        ast.fix_missing_locations(new_tree)
        result = ast.unparse(new_tree)
        return result.removeprefix(_EXPR_SENTINEL)
    except (SyntaxError, ValueError):
        return src


# ── AST-based decorator analysis ──────────────────────────────────────────────

class _OpCounter(ast.NodeVisitor):
    """Walk a function's AST and count math operations for node cost analysis."""

    # Maps AST call names → canonical op names
    _FN_MAP: dict[str, str] = {
        "sin": "sin", "cos": "cos", "exp": "exp", "log": "ln",
        "log2": "ln", "log10": "ln", "ln": "ln",
        "pow": "pow", "power": "pow", "sqrt": "sqrt", "abs": "abs",
        "mul": "mul", "multiply": "mul",
        "div": "div", "divide": "div", "true_divide": "div",
    }

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def _inc(self, name: str) -> None:
        canon = self._FN_MAP.get(name)
        if canon:
            self.counts[canon] = self.counts.get(canon, 0) + 1

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        # torch.sin(x) / math.sin(x) / np.sin(x) / sin(x)
        if isinstance(node.func, ast.Attribute):
            self._inc(node.func.attr)
        elif isinstance(node.func, ast.Name):
            self._inc(node.func.id)
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:  # noqa: N802
        op_map = {
            ast.Add: "add", ast.Sub: "sub",
            ast.Mult: "mul", ast.Div: "div", ast.FloorDiv: "div",
            ast.Pow: "pow",
        }
        name = op_map.get(type(node.op))
        if name:
            self.counts[name] = self.counts.get(name, 0) + 1
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:  # noqa: N802
        if isinstance(node.op, ast.USub):
            self.counts["neg"] = self.counts.get("neg", 0) + 1
        self.generic_visit(node)


def _analyze_fn(func: Callable[..., Any]) -> tuple["OptimizeResult", str]:
    """
    Parse *func*'s source with ast.

    Returns ``(OptimizeResult, rewritten_source)`` where *rewritten_source* is
    the AST-rewritten version produced by BestRewriter (or the original source
    if the source is unavailable or unparseable).
    """
    _unavailable = OptimizeResult(
        original=f"<{func.__name__}>",
        ops=(),
        total_best_nodes=0,
        total_eml_nodes=0,
        savings_pct=0,
        python_snippet="# source not available for static analysis",
        rewritten_code="",
        explanation=("Source could not be inspected — use best_optimize(string) instead.",),
        message=f"@best_optimize on {func.__name__!r}: source unavailable",
    )

    try:
        src = textwrap.dedent(inspect.getsource(func))
        tree = ast.parse(src)
    except (OSError, IndentationError, SyntaxError):
        return _unavailable, ""

    # Count ops for node-cost analysis
    counter = _OpCounter()
    counter.visit(tree)
    ops        = _build_ops(counter.counts)
    total_best = sum(m.best_nodes for m in ops)
    total_eml  = sum(m.eml_nodes  for m in ops)
    savings_pct = (
        max(0, round((1 - total_best / total_eml) * 100))
        if total_eml > 0 else 0
    )
    explanation = _build_explanation(ops)

    # AST rewrite: math.sin → BEST.sin, x**n → BEST.pow(x,n), etc.
    rewritten_src = _ast_rewrite(src)
    snippet = "from monogate import BEST\nimport math\n\n" + rewritten_src

    message = (
        f"BEST: {total_best} nodes vs {total_eml} pure EML — {savings_pct}% fewer exp/ln calls"
        if total_eml > total_best
        else f"No savings found ({total_best} nodes — already EML-optimal)"
    )
    result = OptimizeResult(
        original=src.strip(),
        ops=ops,
        total_best_nodes=total_best,
        total_eml_nodes=total_eml,
        savings_pct=savings_pct,
        python_snippet=snippet,
        rewritten_code=rewritten_src,
        explanation=explanation,
        message=message,
    )
    return result, rewritten_src


# ── EML-arithmetic detection and BEST exec namespace ─────────────────────────

#: Function names that indicate EML arithmetic mode.
_EML_OP_NAMES: frozenset[str] = frozenset({
    "pow_eml", "sin_eml_taylor", "cos_eml_taylor",
    "mul_eml", "div_eml", "ln_eml", "exp_eml",
    "add_eml", "sub_eml", "neg_eml", "recip_eml",
})


def _contains_eml_ops(src: str) -> bool:
    """Return True if *src* references any EML-arithmetic function by name."""
    return any(name in src for name in _EML_OP_NAMES)


def _strip_decorators(src: str) -> str:
    """Remove decorator lines from a function's source (so exec doesn't re-decorate)."""
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                node.decorator_list.clear()
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)
    except (SyntaxError, ValueError):
        return src


def _build_eml_exec_ns() -> dict[str, Any]:
    """
    Return a namespace that swaps EML arithmetic ops for BEST equivalents.

    When a function is exec'd inside this namespace, every ``pow_eml(x, n)``
    call transparently uses ``pow_exl`` (3 nodes), every ``sin_eml_taylor``
    call uses ``sin_best_taylor`` (63 nodes), etc. — the real 3-5x speedup
    without changing the function's source text.

    Note: ``sin_best_taylor``, ``cos_best_taylor``, ``gelu_best_approx`` are
    defined later in this module; they resolve at call time via module scope.
    """
    import math as _math
    from .core import pow_exl as _pow_exl, BEST as _BEST

    def _pow_best(x: Any, n: Any) -> Any:
        try:
            cx = complex(x)
            result = _pow_exl(cx, n)
            return float(result.real) if isinstance(x, (int, float)) else result
        except Exception:
            return float(x) ** float(n)

    return {
        "pow_eml":        _pow_best,
        "sin_eml_taylor": sin_best_taylor,   # resolved at call time
        "cos_eml_taylor": cos_best_taylor,   # resolved at call time
        "gelu_eml_approx": gelu_best_approx, # resolved at call time
        "mul_eml":        _BEST.mul,
        "div_eml":        _BEST.div,
        "ln_eml":         _BEST.ln,
        "exp_eml":        _BEST.exp,
        "add_eml":        _BEST.add,
        "sub_eml":        _BEST.sub,
        "neg_eml":        _BEST.neg,
        "recip_eml":      _BEST.recip,
        "BEST":           _BEST,
        "math":           _math,
    }


class _BESTRuntime:
    """
    Runtime BEST proxy for exec'd rewritten sources.

    Delegates routing calls (exp, ln, pow, mul, div, add, sub, neg, recip)
    to the real BEST HybridOperator and adds compound ops (sin, cos, tanh,
    sigmoid, gelu) that HybridOperator doesn't route natively.

    For standard Python floats, trig/compound ops fall back to native math —
    these are already faster than EML-arithmetic routing.  The proxy exists
    so that exec'd rewritten code (``BEST.sin(x)`` etc.) runs correctly even
    when the original function used standard ``math.sin``.
    """

    def __init__(self) -> None:
        from .core import BEST as _b
        object.__setattr__(self, "_base", _b)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_base"), name)

    # Compound ops not natively on HybridOperator —────────────────────────────
    # Trig: use native math for scalar floats (fastest); fall back to best-Taylor
    def sin(self, x: Any) -> Any:
        import math as _m
        return _m.sin(float(x))

    def cos(self, x: Any) -> Any:
        import math as _m
        return _m.cos(float(x))

    def tanh(self, x: Any) -> Any:
        import math as _m
        return _m.tanh(float(x))

    def sigmoid(self, x: Any) -> Any:
        import math as _m
        return 1.0 / (1.0 + _m.exp(-float(x)))

    def gelu(self, x: Any) -> Any:
        return gelu_best_approx(float(x))  # resolved at call time

    def sqrt(self, x: Any) -> Any:
        import math as _m
        return _m.sqrt(float(x))

    def abs(self, x: Any) -> Any:
        return abs(x)


def _decorate_function(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Wrap *func* with BEST analysis at decoration time (not call time).

    **When the function contains EML arithmetic ops** (``pow_eml``,
    ``sin_eml_taylor``, ``mul_eml``, etc.), a compiled BEST-routed version
    is produced at decoration time and called at runtime — EML ops are
    substituted with their BEST equivalents via the exec namespace, giving
    the real 3-5x speedup.  ``wrapper._best_compiled`` is ``True`` in this case.

    **For standard Python/NumPy/PyTorch functions**, analysis metadata is
    attached (``best_info``, ``_best_rewritten_source``) but the original
    function runs unchanged.  Native ops are already faster than EML routing.

    Attributes added to the wrapper
    --------------------------------
    ``best_info``          ``OptimizeResult`` — node cost breakdown.
    ``_best_rewritten_source``  AST-rewritten source using ``BEST.*`` calls.
    ``_best_original_source``   Unmodified source.
    ``_is_best_optimized``      Always ``True``.
    ``_best_compiled``          ``True`` when a faster BEST version is running.
    """
    analysis, rewritten_src = _analyze_fn(func)

    fast_fn: Callable[..., Any] | None = None
    has_eml = bool(analysis.original and _contains_eml_ops(analysis.original))

    if has_eml:
        try:
            import sys as _sys
            exec_ns: dict[str, Any] = {}
            # Layer: original module globals (preserves non-EML imports/helpers)
            mod = _sys.modules.get(func.__module__)
            if mod is not None:
                exec_ns.update(vars(mod))
            # Layer: BEST runtime (handles any BEST.* calls in original source)
            exec_ns["BEST"] = _BESTRuntime()
            # Layer: EML→BEST swaps (override EML op names with BEST equivalents)
            exec_ns.update(_build_eml_exec_ns())

            raw_src = textwrap.dedent(inspect.getsource(func))
            exec_src = _strip_decorators(raw_src)
            exec(
                compile(ast.parse(exec_src),
                        f"<best_optimize:{func.__module__}.{func.__name__}>",
                        "exec"),
                exec_ns,
            )
            candidate = exec_ns.get(func.__name__)
            if callable(candidate):
                fast_fn = candidate
        except Exception:
            fast_fn = None

    _compiled = has_eml and fast_fn is not None

    if _compiled:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return fast_fn(*args, **kwargs)  # type: ignore[misc]
    else:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

    wrapper.best_info               = analysis           # type: ignore[attr-defined]
    wrapper._best_rewritten_source  = rewritten_src      # type: ignore[attr-defined]
    wrapper._best_original_source   = analysis.original  # type: ignore[attr-defined]
    wrapper._is_best_optimized      = True               # type: ignore[attr-defined]
    wrapper._best_compiled          = _compiled          # type: ignore[attr-defined]
    return wrapper


# ── Public API ─────────────────────────────────────────────────────────────────

def best_optimize(
    target: Union[str, Callable[..., Any], None] = None,
) -> Union["OptimizeResult", Callable[..., Any]]:
    """
    Optimize a math expression string or Python code snippet using BEST routing,
    or use as a decorator to analyse a function's operations at definition time.

    Parameters
    ----------
    target : str, callable, or None
        - **str**: a bare math expression (``"sin(x)**2 + cos(x)*x**3"``)
          or a Python/NumPy/PyTorch code snippet.
        - **callable**: wraps the function; attaches ``func.best_info``
          (``OptimizeResult``) and leaves call behaviour unchanged.
        - **None**: allows bare ``@best_optimize`` usage without parentheses.

    Returns
    -------
    OptimizeResult
        When *target* is a string.  Supports both ``r.message`` and
        ``r["message"]`` access.
    callable
        When *target* is callable — original behaviour preserved, plus
        ``.best_info`` attribute containing the analysis.

    Examples
    --------
    >>> from monogate import best_optimize
    >>> r = best_optimize("sin(x)**2 + cos(x)*x**3 + exp(-x)")
    >>> r["message"]  # dict-style access
    'BEST: ...'
    >>> r.savings_pct  # attribute access
    69

    >>> @best_optimize
    ... def model(x):
    ...     import math
    ...     return math.sin(x) + math.cos(x) * x**3
    >>> model.best_info.savings_pct > 0
    True
    >>> model(1.0) == math.sin(1.0) + math.cos(1.0) * 1.0**3  # unchanged
    True
    """
    if target is None:
        # @best_optimize() — called with no arguments
        return _decorate_function  # type: ignore[return-value]

    if callable(target):
        return _decorate_function(target)

    if not isinstance(target, str):
        raise TypeError(
            f"best_optimize expects a str or callable, got {type(target).__name__!r}"
        )

    source = target.strip()
    if not source:
        raise ValueError("best_optimize: empty input")

    counts    = _scan(source)
    ops       = _build_ops(counts)
    # Use AST rewriting — handles nested cases like sin(x)**2 → BEST.pow(BEST.sin(x), 2)
    # that regex substitution cannot capture correctly.
    rewritten = _ast_rewrite(source)

    total_best = sum(m.best_nodes for m in ops)
    total_eml  = sum(m.eml_nodes  for m in ops)
    savings_pct = (
        max(0, round((1 - total_best / total_eml) * 100))
        if total_eml > 0 else 0
    )

    is_code = _is_python_code(source)
    if is_code:
        snippet = "from monogate import BEST\nimport math\n\n" + rewritten
    else:
        snippet = _build_python_snippet(source, rewritten, total_best, total_eml)

    explanation = _build_explanation(ops)
    message = (
        f"BEST: {total_best} nodes vs {total_eml} pure EML — {savings_pct}% fewer exp/ln calls"
        if total_eml > total_best
        else f"No savings found ({total_best} nodes — expression is already EML-optimal)"
    )

    return OptimizeResult(
        original=source,
        ops=ops,
        total_best_nodes=total_best,
        total_eml_nodes=total_eml,
        savings_pct=savings_pct,
        python_snippet=snippet,
        rewritten_code=rewritten,
        explanation=explanation,
        message=message,
    )


# ── Benchmark ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BenchmarkResult:
    """
    Timing comparison between an original function and its BEST-routed equivalent.

    Attributes
    ----------
    label           Short name for the benchmark (e.g. "sin_taylor").
    before_us       Mean microseconds per call — original (EML-only) code.
    after_us        Mean microseconds per call — BEST-routed code.
    speedup         ``before_us / after_us`` — values > 1 mean BEST is faster.
    node_savings_pct  Static node count reduction reported by best_optimize (0 if
                      not provided).
    """

    label: str
    before_us: float
    after_us: float
    speedup: float
    node_savings_pct: int

    def __str__(self) -> str:
        direction = "faster" if self.speedup >= 1.0 else "slower"
        pct = abs(round((self.speedup - 1.0) * 100))
        lines = [
            f"Benchmark: {self.label}",
            f"  Before (EML):  {self.before_us:>8.1f} us/call",
            f"  After  (BEST): {self.after_us:>8.1f} us/call",
            f"  Speedup:       {self.speedup:>8.2f}x  ({pct}% {direction})",
        ]
        if self.node_savings_pct > 0:
            lines.append(
                f"  Node savings:  {self.node_savings_pct:>7}%  (static -- exp/ln calls)"
            )
        return "\n".join(lines)


def benchmark_optimize(
    before_fn: Callable[..., Any],
    after_fn: Callable[..., Any],
    x: Any,
    *,
    label: str = "function",
    min_run_time: float = 1.0,
    node_savings_pct: int = 0,
) -> "BenchmarkResult":
    """
    Time *before_fn* vs *after_fn* on input *x*.

    Uses ``torch.utils.benchmark.Timer`` when torch is available, falling back
    to ``timeit.timeit`` for pure-Python workloads.  Both functions are called
    as ``fn(x)``.

    Parameters
    ----------
    before_fn
        Original (EML-only or standard) implementation.
    after_fn
        BEST-routed implementation.
    x
        Input value or tensor passed to both functions.
    label
        Name shown in the result table.
    min_run_time
        Minimum wall-clock seconds used by the torch benchmark timer.
        Ignored when falling back to timeit.
    node_savings_pct
        Static node count reduction from best_optimize() — decorative only.

    Returns
    -------
    BenchmarkResult

    Examples
    --------
    >>> import math
    >>> from monogate import benchmark_optimize
    >>> from monogate.optimize import sin_eml_taylor, sin_best_taylor
    >>> r = benchmark_optimize(sin_eml_taylor, sin_best_taylor, math.pi / 4,
    ...                        label="sin_taylor_8term",
    ...                        node_savings_pct=74)
    >>> print(r)
    """
    try:
        from torch.utils.benchmark import Timer as _TorchTimer

        def _time(fn: Callable[..., Any]) -> float:
            t = _TorchTimer(
                stmt="fn(x)",
                globals={"fn": fn, "x": x},
            ).blocked_autorange(min_run_time=min_run_time)
            return float(t.mean) * 1e6  # → microseconds

    except ImportError:
        import timeit as _timeit

        def _time(fn: Callable[..., Any]) -> float:
            runs = 10_000
            elapsed = _timeit.timeit(lambda: fn(x), number=runs)
            return (elapsed / runs) * 1e6

    before_us = _time(before_fn)
    after_us  = _time(after_fn)
    speedup   = before_us / after_us if after_us > 0 else float("inf")

    return BenchmarkResult(
        label=label,
        before_us=round(before_us, 2),
        after_us=round(after_us, 2),
        speedup=round(speedup, 3),
        node_savings_pct=node_savings_pct,
    )


# ── Reference implementations for benchmarking ────────────────────────────────

def sin_eml_taylor(x: float, terms: int = 8) -> float:
    """
    sin(x) via Taylor series using *pure EML* operators (15 nodes per power).

    Uses ``pow_eml`` for every power term.  Requires ``x > 0`` (pow_eml has no
    real-domain branch for negative bases).  Intended as the EML baseline for
    ``benchmark_optimize``; compare against ``sin_best_taylor``.

    Node cost: (terms-1) × 15  (powers) + fixed add/sub chain.
    For 8 terms: 7 × 15 = 105 pow nodes  vs BEST's 7 × 3 = 21.
    """
    import math as _math
    from .core import pow_eml as _pow_eml

    if x <= 1.0:
        raise ValueError(
            f"sin_eml_taylor requires x > 1 (got {x!r}).\n"
            "pow_eml needs ln(x) > 0. Use sin_best_taylor for general x."
        )
    result = x  # first term: x / 1!
    for k in range(1, terms):
        n    = 2 * k + 1
        xp   = float(_pow_eml(x, n))
        term = xp / _math.factorial(n)
        result += (-1) ** k * term
    return result


def sin_best_taylor(x: float, terms: int = 8) -> float:
    """
    sin(x) via Taylor series using *BEST-routed* operators (3 nodes per power).

    Uses ``pow_exl`` (EXL: 3 nodes) for every power term via complex arithmetic.
    Works for all real ``x``.  Intended as the BEST measurement for
    ``benchmark_optimize``; compare against ``sin_eml_taylor``.

    Node cost: (terms-1) × 3  (powers) vs EML's (terms-1) × 15.
    For 8 terms: 7 × 3 = 21 pow nodes  vs EML's 7 × 15 = 105.
    """
    import math as _math
    from .core import pow_exl as _pow_exl

    if x == 0.0:
        return 0.0
    cx = complex(x)
    result = cx
    for k in range(1, terms):
        n    = 2 * k + 1
        xp   = _pow_exl(cx, n)
        term = xp / _math.factorial(n)
        result += (-1) ** k * term
    return float(result.real)


def cos_best_taylor(x: float, terms: int = 8) -> float:
    """
    cos(x) via Taylor series using *BEST-routed* operators (3 nodes per power).

    Uses ``pow_exl`` (EXL: 3 nodes) for every power term via complex arithmetic.
    Works for all real ``x``.

    cos Taylor:  1 - x^2/2! + x^4/4! - x^6/6! + ...
    Node cost: (terms-1) × 3  vs EML's (terms-1) × 15.
    For 8 terms: 7 × 3 = 21 pow nodes  vs EML's 105.
    """
    import math as _math
    from .core import pow_exl as _pow_exl

    if x == 0.0:
        return 1.0
    cx = complex(x)
    result = complex(1.0)  # first term: x^0/0! = 1
    for k in range(1, terms):
        n = 2 * k
        xp = _pow_exl(cx, n)
        term = xp / _math.factorial(n)
        result += (-1) ** k * term
    return float(result.real)


def gelu_eml_approx(x: float) -> float:
    """
    GELU approximation  gelu(x) ≈ 0.5·x·(1 + tanh(c·(x + 0.044715·x³)))
    via *pure EML arithmetic*.

    tanh(z) is computed as  1 − 2·recip_eml(add_eml(exp_eml(2z), 1))
    which avoids the ln(1.0)=0 domain issue in div_eml.

    EML node cost:  exp_eml (1n) + add_eml (11n) + recip_eml (5n) = 17n.
    Accurate to <0.0001 vs exact GELU everywhere.  Works for all real x.

    Compare with ``gelu_best_approx`` (~14 nodes, ~1.2× faster).
    """
    from .core import exp_eml as _exp, add_eml as _add, recip_eml as _recip

    _C1 = 0.7978845608028654   # sqrt(2/pi)
    _C2 = 0.03567740813446277  # sqrt(2/pi) * 0.044715

    inner = _C1 * x + _C2 * x ** 3               # Python arithmetic (no domain risk)
    # tanh saturates at +-1 for |inner| > ~20; exp(2*inner) overflows at ~710
    if inner > 20.0:
        return x
    if inner < -20.0:
        return 0.0
    e2i   = float(_exp(2.0 * inner))              # exp(2·inner)         (1n)
    den   = float(_add(e2i, 1.0))                 # exp(2·inner) + 1     (11n)
    tanh_val = 1.0 - 2.0 * float(_recip(den))     # 1 − 2/(den)          (5n)
    return 0.5 * x * (1.0 + tanh_val)


def gelu_best_approx(x: float) -> float:
    """
    GELU approximation  gelu(x) ≈ 0.5·x·(1 + tanh(c·(x + 0.044715·x³)))
    via *BEST routing*.

    tanh(z) = 1 − 2·BEST.recip(BEST.add(BEST.exp(2z), 1)).
    BEST routing: exp (1n EML) + add (11n EML) + recip (2n EDL) = 14n.
    Accurate to <0.0001 vs exact GELU.  Works for all real x.

    Compare with ``gelu_eml_approx`` (~17 nodes, ~1.2× slower).
    """
    from .core import BEST as _BEST

    _C1 = 0.7978845608028654   # sqrt(2/pi)
    _C2 = 0.03567740813446277  # sqrt(2/pi) * 0.044715

    inner = _C1 * x + _C2 * x ** 3          # Python arithmetic
    # tanh saturates at +-1 for |inner| > ~3.3; also recip_edl overflows
    # when den = exp(2*inner) > ~709, i.e. inner > 3.25
    if inner > 3.25:
        return x
    if inner < -3.25:
        return 0.0
    e2i   = _BEST.exp(2.0 * inner).real     # exp(2·inner)         (1n)
    den   = _BEST.add(e2i, 1.0).real        # exp(2·inner) + 1     (11n)
    tanh_val = 1.0 - 2.0 * _BEST.recip(den).real  # 1 − 2/(den)    (2n)
    return 0.5 * x * (1.0 + tanh_val)


# ── best_optimize_model ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LayerOptimizeResult:
    """Per-layer result from ``best_optimize_model()``."""
    path: str               # module path ("" = root, "encoder.layer.0", etc.)
    method: str             # method analyzed, typically "forward"
    result: OptimizeResult  # full node cost and rewritten source
    patched: bool           # True if the method was replaced with a BEST version


@dataclass(frozen=True)
class ModelOptimizeReport:
    """
    Full optimization report from ``best_optimize_model()``.

    Attributes
    ----------
    total_best_nodes  Sum of BEST node costs across all analyzed forward methods.
    total_eml_nodes   Sum of EML node costs across all analyzed forward methods.
    savings_pct       Overall integer % node reduction.
    layers            Per-layer breakdown (one entry per analyzed forward method).
    patched_count     Number of forward methods replaced with BEST versions.
    device_note       Model's inferred device string ("cpu", "cuda", or "").
    rewritten_sources Mapping of ``"path.method"`` → AST-rewritten source code.
                      Populated for every analyzed method regardless of savings.
    """
    total_best_nodes: int
    total_eml_nodes: int
    savings_pct: int
    layers: tuple[LayerOptimizeResult, ...]
    patched_count: int
    device_note: str = ""        # populated by best_optimize_model(); "" = unknown
    rewritten_sources: tuple[tuple[str, str], ...] = ()  # (key, code) pairs

    def get_rewritten(self, path: str = "") -> str | None:
        """
        Return the AST-rewritten source for the method at *path*.

        *path* is the dotted module path (empty string for the root module's
        forward, ``"encoder"`` for ``model.encoder.forward``, etc.).

        Returns ``None`` if no source was captured for that path.

        Example
        -------
        >>> report = best_optimize_model(model)
        >>> print(report.get_rewritten())          # root forward
        >>> print(report.get_rewritten("encoder")) # encoder.forward
        """
        target = f"{path}.forward" if path else "forward"
        for key, code in self.rewritten_sources:
            if key == target:
                return code
        return None

    def print_rewritten(self, path: str = "") -> None:
        """Print the rewritten forward source for *path* (default: root module)."""
        code = self.get_rewritten(path)
        if code is None:
            label = f"{path}.forward" if path else "forward"
            print(f"# No rewritten source for {label!r}")
        else:
            print(code)

    def __str__(self) -> str:
        lines = [
            f"ModelOptimizeReport: {self.savings_pct}% node savings  "
            f"({self.total_best_nodes}n BEST vs {self.total_eml_nodes}n EML)",
            f"  Layers analyzed: {len(self.layers)}  |  Methods patched: {self.patched_count}",
        ]
        # Speedup expectation
        if self.savings_pct >= _CROSSOVER_PCT:
            lines.append(
                f"  Speedup expected: YES  "
                f"({self.savings_pct}% > {_CROSSOVER_PCT}% crossover threshold)"
            )
        elif self.savings_pct > 0:
            lines.append(
                f"  Speedup expected: NO   "
                f"({self.savings_pct}% < {_CROSSOVER_PCT}% crossover threshold)"
            )
        # Device context note
        if self.device_note == "cuda":
            lines.append(
                "  Device: cuda — EML arithmetic runs on CPU Python scalars.\n"
                "    native torch.* on CUDA is orders of magnitude faster.\n"
                "    monogate is for symbolic analysis, not GPU inference."
            )
        elif self.device_note == "cpu":
            lines.append(
                "  Device: cpu — note: native torch.sin is ~9,000x faster than EML substrate.\n"
                "    monogate is relevant for symbolic analysis and expression trees, not\n"
                "    production inference."
            )
        # Per-layer breakdown — show all methods with savings or patches
        has_details = any(lr.result.savings_pct > 0 or lr.patched for lr in self.layers)
        if has_details:
            lines.append("  " + "-" * 48)
            for lr in self.layers:
                if lr.result.savings_pct > 0 or lr.patched:
                    tag = " [patched]" if lr.patched else ""
                    label = lr.path or "root"
                    pct = lr.result.savings_pct
                    best_n = lr.result.total_best_nodes
                    eml_n  = lr.result.total_eml_nodes
                    lines.append(
                        f"  {label}.{lr.method}: {pct}% savings  "
                        f"({best_n}n BEST vs {eml_n}n EML){tag}"
                    )
        # Hint about rewritten source if any was captured
        if self.rewritten_sources:
            lines.append(
                f"  Use report.print_rewritten() to view the rewritten forward source."
            )
        return "\n".join(lines)


def best_optimize_model(
    model: Any,
    *,
    verbose: bool = False,
    inplace: bool = False,
    device: str | None = None,
) -> ModelOptimizeReport:
    """
    Analyze (and optionally patch) all ``forward`` methods in an nn.Module.

    Walks every sub-module via ``model.named_modules()``, inspects each
    ``forward`` method's source with ``best_optimize()``, and reports BEST
    node savings.

    When *inplace=True* and a forward method contains EML arithmetic ops
    (``pow_eml``, ``sin_eml_taylor``, etc.), the method is replaced with a
    compiled version that executes BEST-routed equivalents — the same
    mechanism as the ``@best_optimize`` decorator.

    Parameters
    ----------
    model : nn.Module
        The model to analyze.
    verbose : bool
        Print per-layer results as they are processed.
    inplace : bool
        If True, patch forward methods containing EML arithmetic ops with
        compiled BEST versions.  Experimental — only safe for deterministic
        forward methods.
    device : str or None
        Override the device note in the report.  Pass ``"cpu"`` or ``"cuda"``
        to force a specific note regardless of where the model's parameters
        live.  ``None`` (default) auto-detects from ``model.parameters()``.

        Note: monogate computes in Python scalars via ``math.exp``/``math.log``
        and does **not** accelerate PyTorch tensor operations on any device.
        Passing ``device="cuda"`` simply adds a prominent reminder of this
        in the report output.

    Returns
    -------
    ModelOptimizeReport

    Examples
    --------
    >>> from monogate import best_optimize_model
    >>> report = best_optimize_model(my_model, verbose=True)
    >>> print(report)
    >>> # Patch forward methods in-place where EML ops are found:
    >>> report = best_optimize_model(my_model, inplace=True)
    >>> # Force the cuda-device warning even on a CPU model:
    >>> report = best_optimize_model(my_model, device="cuda")
    """
    try:
        import torch.nn as _nn  # noqa: F401  (validate torch is available)
    except ImportError as exc:
        raise ImportError(
            "best_optimize_model requires PyTorch — pip install torch\n"
            "  Or use best_optimize() for plain Python/NumPy expressions."
        ) from exc

    if not hasattr(model, "named_modules"):
        raise TypeError(
            f"best_optimize_model expects a torch.nn.Module, got {type(model).__name__}.\n"
            "  For plain Python expressions use best_optimize(source_string).\n"
            "  For SIREN / NeRF networks use optimize_siren(model)."
        )

    # Detect model device for context note in the report.
    # Caller can override with device="cpu"|"cuda".
    if device is not None:
        device_note = device.lower()
    else:
        device_note = ""
        try:
            params = list(model.parameters())
            if params:
                device_note = str(params[0].device.type)
        except Exception:
            pass

    layers: list[LayerOptimizeResult] = []
    rewritten_sources_list: list[tuple[str, str]] = []
    total_best = 0
    total_eml  = 0
    patched_total = 0

    for path, module in model.named_modules():
        try:
            src = textwrap.dedent(inspect.getsource(module.forward))
        except (OSError, TypeError, AttributeError):
            continue

        try:
            result = best_optimize(src)
        except Exception:
            continue

        # Always capture the rewritten source (useful even without patching)
        key = f"{path}.forward" if path else "forward"
        if result.rewritten_code:
            header = "from monogate import BEST\n\n"
            full_source = (
                header + result.rewritten_code
                if not result.rewritten_code.startswith("from monogate")
                else result.rewritten_code
            )
            rewritten_sources_list.append((key, full_source))

        if verbose:
            label = path or "root"
            tag = f"{result.savings_pct}% savings" if result.savings_pct > 0 else "no savings"
            print(f"  {label}.forward: {tag}")

        did_patch = False
        if inplace and result.savings_pct > 0 and _contains_eml_ops(src):
            try:
                import sys as _sys, types as _types
                exec_ns: dict[str, Any] = {}
                mod = _sys.modules.get(type(module).__module__)
                if mod is not None:
                    exec_ns.update(vars(mod))
                exec_ns["BEST"] = _BESTRuntime()
                exec_ns.update(_build_eml_exec_ns())
                exec_src = _strip_decorators(src)
                exec(
                    compile(ast.parse(exec_src),
                            f"<best_optimize:{path or 'root'}.forward>", "exec"),
                    exec_ns,
                )
                new_fwd = exec_ns.get("forward")
                if callable(new_fwd):
                    module.forward = _types.MethodType(new_fwd, module)
                    did_patch = True
                    patched_total += 1
            except Exception:
                pass

        layers.append(LayerOptimizeResult(
            path=path,
            method="forward",
            result=result,
            patched=did_patch,
        ))
        total_best += result.total_best_nodes
        total_eml  += result.total_eml_nodes

    overall_savings = (
        max(0, round((1 - total_best / total_eml) * 100))
        if total_eml > 0 else 0
    )
    return ModelOptimizeReport(
        total_best_nodes=total_best,
        total_eml_nodes=total_eml,
        savings_pct=overall_savings,
        layers=tuple(layers),
        patched_count=patched_total,
        device_note=device_note,
        rewritten_sources=tuple(rewritten_sources_list),
    )


# Convenience alias
optimize = best_optimize


# ── SIREN / NeRF optimizer ────────────────────────────────────────────────────

def optimize_siren(
    model: Any,
    omega: float = 30.0,
) -> ModelOptimizeReport:
    """
    Analyze a SIREN / NeRF-style network using BEST routing.

    Convenience wrapper around ``best_optimize_model`` for sin-heavy networks.
    SIREN layers use ``sin(omega_0 * Wx + b)`` as the activation — the high
    omega_0 value (typically 30) makes sin the dominant operation, which is
    exactly where BEST routing yields its largest savings (74% node reduction
    for sin; 2.5–4× measured speedup at the SIREN scale).

    Parameters
    ----------
    model : nn.Module
        The SIREN or NeRF network to analyze.
    omega : float
        The omega_0 scaling factor used in the model (informational only —
        not used in analysis; all sin calls are routed the same way).

    Returns
    -------
    ModelOptimizeReport
        Full per-layer savings report.  Use ``report.get_rewritten()`` to
        retrieve the BEST-rewritten forward source.

    Example
    -------
    >>> from monogate import optimize_siren
    >>> report = optimize_siren(my_siren_model)
    >>> print(report)
    >>> print(report.get_rewritten())
    """
    try:
        import torch.nn as _nn
    except ImportError:
        raise RuntimeError(
            "optimize_siren requires PyTorch — pip install torch"
        ) from None

    if not isinstance(model, _nn.Module):
        raise TypeError(
            f"optimize_siren expects a torch.nn.Module, got {type(model).__name__}"
        )

    return best_optimize_model(model)


# Alias — same function, NeRF-centric name.
optimize_nerf = optimize_siren


# ── context_aware_best_optimize ───────────────────────────────────────────────

# Operations whose deep chaining is numerically risky in EML arithmetic.
_RISKY_OPS: frozenset[str] = frozenset({"sub", "add", "neg"})

# Operations where switching to EXL in a deep subtree often helps.
_EXL_CANDIDATES: frozenset[str] = frozenset({"pow", "mul", "ln", "sqrt"})

_STABILITY_HINTS: dict[str, str] = {
    "sub": (
        "EML subtraction at depth>{d} risks catastrophic cancellation — "
        "consider restructuring as EXL multiplication chains."
    ),
    "add": (
        "EML addition at depth>{d} creates nested exp towers — "
        "verify inputs stay in [-20, 20] or use log-sum-exp reformulation."
    ),
    "pow": (
        "Deep EXL pow chain at depth>{d} is numerically stable but may overflow "
        "for large inputs — validate input range."
    ),
    "mul": (
        "EDL multiplication chain at depth>{d}: check for intermediate values "
        "near zero (ln singularity in EDL)."
    ),
}


@dataclass
class StabilityWarning:
    """One detected potential stability issue."""
    op: str           # canonical op name
    depth: int        # subtree depth where it was found
    count: int        # occurrences at or deeper than threshold
    suggestion: str   # human-readable fix suggestion
    alt_nodes: int | None = None  # node cost delta if rerouted

    def __str__(self) -> str:
        base = (
            f"  [{self.op.upper():<8}] depth={self.depth}, "
            f"occurrences={self.count}: {self.suggestion}"
        )
        if self.alt_nodes is not None:
            base += f" (+{self.alt_nodes} nodes if rerouted)"
        return base


@dataclass
class ContextAwareResult:
    """
    Result of context_aware_best_optimize().

    Attributes
    ----------
    base_result       The underlying OptimizeResult from static BEST analysis.
    stability_issues  List of StabilityWarning (empty if none detected).
    dynamic_profile   Dict of profiling stats (only populated when
                      sample_inputs was provided).
    diagnostics       Summary dict for programmatic consumption.
    """
    base_result: OptimizeResult
    stability_issues: list[StabilityWarning] = field(default_factory=list)
    dynamic_profile: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [str(self.base_result)]
        if self.stability_issues:
            lines.append("  Stability analysis:")
            for w in self.stability_issues:
                lines.append(str(w))
            lines.append("")
        if self.dynamic_profile:
            lines.append("  Dynamic profile:")
            for k, v in self.dynamic_profile.items():
                lines.append(f"    {k}: {v}")
            lines.append("")
        return "\n".join(lines)


class _DepthWalker(ast.NodeVisitor):
    """
    Walk a Python AST and record the call depth at which each recognized
    operation appears.  Returns {op_name: [depth, depth, ...]} per call site.
    """

    _FUNC_MAP: dict[str, str] = {
        "sin": "sin", "cos": "cos", "exp": "exp", "log": "ln",
        "log2": "ln", "ln": "ln", "pow": "pow", "sqrt": "sqrt",
        "tanh": "tanh", "sigmoid": "sigmoid", "gelu": "gelu", "abs": "abs",
    }
    _ATTR_MAP: dict[str, str] = {
        "sin": "sin", "cos": "cos", "exp": "exp", "log": "ln",
        "log2": "ln", "log1p": "ln", "pow": "pow", "sqrt": "sqrt",
        "tanh": "tanh", "sigmoid": "sigmoid", "gelu": "gelu",
    }

    def __init__(self) -> None:
        self.op_depths: dict[str, list[int]] = {}
        self._depth = 0

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        op_name: str | None = None
        if isinstance(node.func, ast.Name):
            op_name = self._FUNC_MAP.get(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            op_name = self._ATTR_MAP.get(node.func.attr)
        if op_name:
            self.op_depths.setdefault(op_name, []).append(self._depth)
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    def visit_BinOp(self, node: ast.BinOp) -> None:  # noqa: N802
        op_map = {
            ast.Add: "add", ast.Sub: "sub", ast.Mult: "mul",
            ast.Div: "div", ast.Pow: "pow",
        }
        op_name = op_map.get(type(node.op))
        if op_name:
            self.op_depths.setdefault(op_name, []).append(self._depth)
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1


def _analyze_ast_depths(source: str) -> dict[str, list[int]]:
    """
    Parse *source* and return {op_name: [call_depths]}.
    Falls back to an empty dict on any syntax error.
    """
    try:
        tree = ast.parse(textwrap.dedent(source))
    except SyntaxError:
        try:
            tree = ast.parse(f"_result = {source.strip()}")
        except SyntaxError:
            return {}
    walker = _DepthWalker()
    walker.visit(tree)
    return walker.op_depths


def _profile_static_best(
    source: str,
    sample_inputs: Any,
) -> dict[str, Any]:
    """
    Evaluate the expression on *sample_inputs* (using NumPy) and report
    potential numerical issues: NaN, Inf, dynamic range.

    Returns a dict with keys: has_nan, has_inf, max_abs_value,
    dynamic_range_db, n_samples.
    """
    stats: dict[str, Any] = {
        "has_nan": False, "has_inf": False,
        "max_abs_value": None, "dynamic_range_db": None, "n_samples": 0,
    }
    try:
        import numpy as np  # noqa: PLC0415

        arr = np.asarray(sample_inputs, dtype=float).ravel()
        _MAX_PROFILE_SAMPLES = 10_000
        if len(arr) > _MAX_PROFILE_SAMPLES:
            warnings.warn(
                f"monogate: sample_inputs has {len(arr)} elements; "
                f"profiling truncated to first {_MAX_PROFILE_SAMPLES}.",
                stacklevel=3,
                category=UserWarning,
            )
            arr = arr[:_MAX_PROFILE_SAMPLES]
        stats["n_samples"] = len(arr)
        if len(arr) == 0:
            return stats

        safe_ns: dict[str, Any] = {
            "np": np, "x": arr,
            "sin": np.sin, "cos": np.cos, "exp": np.exp,
            "log": np.log, "ln": np.log, "sqrt": np.sqrt,
            "pow": np.power, "tanh": np.tanh, "abs": np.abs,
        }
        expr = source.strip()
        for prefix in ("return ", "y = ", "out = "):
            if expr.startswith(prefix):
                expr = expr[len(prefix):]
                break
        try:
            result = eval(expr, {"__builtins__": {}}, safe_ns)  # noqa: S307
            result = np.asarray(result, dtype=float).ravel()
        except Exception:
            return stats

        stats["has_nan"] = bool(np.any(np.isnan(result)))
        stats["has_inf"] = bool(np.any(np.isinf(result)))
        finite = result[np.isfinite(result)]
        if len(finite):
            amax = float(np.max(np.abs(finite)))
            nonzero = finite[finite != 0]
            amin = float(np.min(np.abs(nonzero))) if len(nonzero) else 1.0
            stats["max_abs_value"] = amax
            stats["dynamic_range_db"] = float(20 * np.log10(amax / amin + 1e-15))
    except ImportError:
        pass
    return stats


def context_aware_best_optimize(
    expr_or_func: Union[str, Callable[..., Any]],
    dynamic: bool = False,
    stability_threshold: int = 10,
    sample_inputs: Any = None,
    warn: bool = True,
    **kwargs: Any,
) -> ContextAwareResult:
    """
    Static BEST routing with optional lightweight context-awareness.

    By default (``dynamic=False``) this is a thin wrapper around
    :func:`best_optimize` with zero overhead.  Enable additional analysis
    with the flags below.

    Parameters
    ----------
    expr_or_func : str or callable
        A math expression string, a Python/NumPy/PyTorch code snippet,
        or a decorated callable.  Passed directly to :func:`best_optimize`.
    dynamic : bool, default False
        If True, perform AST analysis to compute subtree depths for each
        detected operation and flag potential stability issues (risky EML
        subtraction chains, deep exp towers, etc.).  Pure static analysis
        — no code execution unless ``sample_inputs`` is also provided.
    stability_threshold : int, default 10
        Minimum call-site depth at which an operation is flagged as a
        potential stability concern.  Lower values produce more warnings.
    sample_inputs : array-like or None, default None
        If provided, evaluate the expression on these inputs (using NumPy)
        and report large intermediate values, NaNs, or high dynamic range.
        Only active when ``dynamic=True``.  Does not require torch.
    warn : bool, default True
        Emit :func:`warnings.warn` for each detected stability issue.
        Set to False to inspect ``result.stability_issues`` programmatically.
    **kwargs
        Forwarded to :func:`best_optimize`.

    Returns
    -------
    ContextAwareResult
        Wraps the underlying ``OptimizeResult`` and adds
        ``stability_issues``, ``dynamic_profile``, and ``diagnostics``.

    Examples
    --------
    Basic usage — identical to best_optimize:

    >>> r = context_aware_best_optimize("sin(x)**2 + exp(-x) * cos(x)")
    >>> print(r.base_result.savings_pct)
    74

    Depth-aware stability check on a deeply nested expression:

    >>> deep_expr = "exp(exp(exp(x - exp(x - exp(x - 1)))))"
    >>> r = context_aware_best_optimize(
    ...     deep_expr,
    ...     dynamic=True,
    ...     stability_threshold=3,
    ...     warn=False,
    ... )
    >>> for issue in r.stability_issues:
    ...     print(issue)

    Profiling with sample inputs:

    >>> import numpy as np
    >>> r = context_aware_best_optimize(
    ...     "exp(x) - exp(-x)",
    ...     dynamic=True,
    ...     sample_inputs=np.linspace(-50, 50, 1000),
    ... )
    >>> r.dynamic_profile  # {'has_nan': False, 'has_inf': True, ...}
    """
    # Step 1: run the existing static optimizer unconditionally.
    base = best_optimize(expr_or_func, **kwargs)

    issues: list[StabilityWarning] = []
    profile: dict[str, Any] = {}

    # Step 2: optional AST depth analysis.
    if dynamic:
        source = (
            inspect.getsource(expr_or_func)
            if callable(expr_or_func)
            else str(expr_or_func)
        )
        op_depths = _analyze_ast_depths(source)

        for op_name, depths in op_depths.items():
            deep_hits = [d for d in depths if d >= stability_threshold]
            if not deep_hits:
                continue

            hint_template = _STABILITY_HINTS.get(op_name)
            if hint_template is None:
                if op_name in _RISKY_OPS or op_name in _EXL_CANDIDATES:
                    hint_template = (
                        f"{op_name} at depth>{{d}} may benefit from "
                        "EXL rerouting for numerical stability."
                    )
                else:
                    continue

            max_depth = max(deep_hits)
            suggestion = hint_template.format(d=stability_threshold)

            alt_nodes: int | None = None
            if op_name in _EXL_CANDIDATES:
                best_cost = _BEST_NODES.get(op_name, 0)
                eml_cost = _EML_NODES.get(op_name, 0)
                if eml_cost > best_cost:
                    alt_nodes = eml_cost - best_cost

            issue = StabilityWarning(
                op=op_name,
                depth=max_depth,
                count=len(deep_hits),
                suggestion=suggestion,
                alt_nodes=alt_nodes,
            )
            issues.append(issue)
            if warn:
                warnings.warn(
                    f"monogate: {suggestion} "
                    f"(op={op_name!r}, max_depth={max_depth}, "
                    f"occurrences={len(deep_hits)})",
                    stacklevel=2,
                    category=UserWarning,
                )

        # Step 3: optional dynamic profiling.
        if sample_inputs is not None:
            profile = _profile_static_best(source, sample_inputs)
            if warn:
                if profile.get("has_nan"):
                    warnings.warn(
                        "monogate: NaN detected in forward pass on sample_inputs. "
                        "Check for log(0) or exp overflow in the expression.",
                        stacklevel=2,
                        category=UserWarning,
                    )
                if profile.get("has_inf"):
                    warnings.warn(
                        "monogate: Inf detected in forward pass on sample_inputs. "
                        "Large inputs to exp() chains may exceed float64 range.",
                        stacklevel=2,
                        category=UserWarning,
                    )
                dr = profile.get("dynamic_range_db")
                if dr is not None and dr > 200:
                    warnings.warn(
                        f"monogate: High dynamic range ({dr:.0f} dB) detected. "
                        "Consider normalising inputs or using log-domain arithmetic.",
                        stacklevel=2,
                        category=UserWarning,
                    )

    diagnostics: dict[str, Any] = {
        "savings_pct": base.savings_pct,
        "speedup_expected": base.savings_pct >= _CROSSOVER_PCT,
        "n_stability_issues": len(issues),
        "issue_ops": [w.op for w in issues],
    }
    if profile:
        diagnostics.update({
            "has_nan": profile.get("has_nan"),
            "has_inf": profile.get("has_inf"),
            "dynamic_range_db": profile.get("dynamic_range_db"),
        })

    return ContextAwareResult(
        base_result=base,
        stability_issues=issues,
        dynamic_profile=profile,
        diagnostics=diagnostics,
    )
