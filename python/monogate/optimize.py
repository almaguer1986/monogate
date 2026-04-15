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
from dataclasses import dataclass
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

_BEST_SOURCE: dict[str, str] = {
    "exp": "EML", "ln": "EXL", "pow": "EXL", "sqrt": "EXL",
    "mul": "EDL", "div": "EDL", "recip": "EDL", "neg": "EDL",
    "sub": "EML", "add": "EML", "abs": "EML",
    "sin": "EXL", "cos": "EXL",
}


# ── Detection rules ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class _Rule:
    op_name: str        # canonical operation name
    py_pattern: str     # matches library-prefixed calls (math.*, torch.*, np.*)
    expr_pattern: str   # matches bare calls in expression strings (empty = skip)
    replacement: str    # what to substitute the matched prefix with


# Order matters: ln must come before log to avoid partial-match issues in expr mode.
_RULES: tuple[_Rule, ...] = (
    _Rule("sin",  r"(?:math|torch|np|numpy|F)\.sin\s*\(",    r"\bsin\s*\(",    "BEST.sin("),
    _Rule("cos",  r"(?:math|torch|np|numpy|F)\.cos\s*\(",    r"\bcos\s*\(",    "BEST.cos("),
    _Rule("exp",  r"(?:math|torch|np|numpy|F)\.exp\s*\(",    r"\bexp\s*\(",    "BEST.exp("),
    _Rule("ln",   r"(?:math|torch|np|numpy|F)\.log\w*\s*\(", r"\bln\s*\(",     "BEST.ln("),
    _Rule("pow",  r"(?:math|torch|np|numpy)\.pow(?:er)?\s*\(",r"\bpow\s*\(",   "BEST.pow("),
    _Rule("sqrt", r"(?:math|torch|np|numpy)\.sqrt\s*\(",     r"\bsqrt\s*\(",   "BEST.sqrt("),
    _Rule("abs",  r"(?:math|torch|np|numpy)\.fabs\s*\(",     r"",              "abs("),
    _Rule("div",  r"(?:torch\.div|np\.divide)\s*\(",         r"",              "BEST.div("),
    _Rule("mul",  r"(?:torch\.mul|np\.multiply)\s*\(",       r"",              "BEST.mul("),
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
    node_note = (
        f"# {total_best} nodes (BEST)  vs  {total_eml} (pure EML)"
        f"  — {savings_pct}% fewer exp/ln calls"
        if total_eml > total_best
        else f"# {total_best} nodes (BEST mode)"
    )
    py_body = rewritten.strip().replace("\n", "\n    ")
    return (
        "from monogate import BEST\n"
        "import math\n\n"
        "def f(x):\n"
        f"    {node_note}\n"
        f"    return {py_body}\n"
        "    # Note: *, /, +, - operators are standard Python arithmetic.\n"
        "    # For full BEST routing wrap them: BEST.mul(a,b), BEST.div(a,b)\n"
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


def _ast_rewrite(src: str) -> str:
    """
    Parse *src*, apply BestRewriter, return the unparsed result.
    Returns the original source unchanged on any parse/unparse error.
    """
    try:
        tree = ast.parse(src)
        new_tree = BestRewriter().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)
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


def _decorate_function(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Wrap *func* with BEST analysis **at decoration time** (not call time).

    Attributes added to the wrapper:

    ``best_info``
        ``OptimizeResult`` — full node cost breakdown and savings summary.

    ``_best_rewritten_source``
        The function's source after BestRewriter transforms it — every
        ``math.sin``, ``torch.cos``, ``x**n`` etc. replaced with
        ``BEST.sin``, ``BEST.cos``, ``BEST.pow(x,n)`` etc.

    ``_best_original_source``
        The original (unmodified) source string.

    ``_is_best_optimized``
        ``True`` — quick membership test.

    Call behaviour is unchanged: the original function runs unchanged.
    """
    analysis, rewritten_src = _analyze_fn(func)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    wrapper.best_info               = analysis          # type: ignore[attr-defined]
    wrapper._best_rewritten_source  = rewritten_src     # type: ignore[attr-defined]
    wrapper._best_original_source   = analysis.original # type: ignore[attr-defined]
    wrapper._is_best_optimized      = True              # type: ignore[attr-defined]
    wrapper._best_optimize_stub     = True              # type: ignore[attr-defined]
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
    rewritten = _rewrite(source)

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


# Convenience alias
optimize = best_optimize
