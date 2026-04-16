"""
monogate.llm.optimizer — LLM-assisted EML expression optimizer.

Flow:
  1. Build prompt from user description (or function probe points)
  2. Call LLM API (or mock)
  3. Parse the expression → identify ops
  4. Run best_optimize → BEST node count + rewritten code
  5. Optionally run mcts_search for gradient-free minimal tree
  6. Return LLMOptimizeResult

Supported providers:
    mock      — keyword heuristics, no API key required
    openai    — requires: pip install openai; env OPENAI_API_KEY
    groq      — requires: pip install groq;  env GROQ_API_KEY
    anthropic — requires: pip install anthropic; env ANTHROPIC_API_KEY
"""

from __future__ import annotations

import math
import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Callable

from .prompts import SYSTEM_PROMPT, build_user_message, build_probe_message, mock_response

__all__ = ["suggest_and_optimize", "LLMOptimizeResult", "SUPPORTED_PROVIDERS"]

SUPPORTED_PROVIDERS = ("mock", "openai", "groq", "anthropic")

# Default models per provider — cheap + fast
_DEFAULT_MODELS = {
    "openai":    "gpt-4o-mini",
    "groq":      "llama3-8b-8192",
    "anthropic": "claude-haiku-4-5-20251001",
}


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class LLMOptimizeResult:
    """
    Result from suggest_and_optimize().

    Attributes:
        prompt:          Original user prompt.
        llm_expression:  Expression suggested by the LLM (or mock).
        best_formula:    BEST-routed rewritten expression.
        eml_nodes:       Node count in naive EML form.
        best_nodes:      Node count after BEST routing.
        savings_pct:     Node reduction percentage.
        code:            Copy-paste Python snippet using BEST.* primitives.
        provider:        Provider used ('mock', 'openai', etc.).
        model:           Model ID used.
        elapsed_s:       Wall time for the full call.
        mcts_formula:    Best MCTS tree formula (set by run_mcts=True).
        mcts_mse:        MSE of MCTS formula on probe points.
        ops_found:       List of operations identified in the expression.
    """
    prompt:         str
    llm_expression: str
    best_formula:   str
    eml_nodes:      int
    best_nodes:     int
    savings_pct:    float
    code:           str
    provider:       str
    model:          str
    elapsed_s:      float
    mcts_formula:   str = ""
    mcts_mse:       float = float("inf")
    ops_found:      list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"LLMOptimizeResult(\n"
            f"  prompt      = {self.prompt!r}\n"
            f"  llm_expr    = {self.llm_expression!r}\n"
            f"  best_formula= {self.best_formula!r}\n"
            f"  eml_nodes   = {self.eml_nodes}\n"
            f"  best_nodes  = {self.best_nodes}\n"
            f"  savings_pct = {self.savings_pct:.1f}%\n"
            f"  provider    = {self.provider!r}\n"
            f"  model       = {self.model!r}\n"
            f")"
        )

    def print_summary(self) -> None:
        """Print a human-readable summary to stdout."""
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

        print()
        print("=" * 60)
        print(f"  monogate LLM optimizer  [{self.provider} / {self.model}]")
        print("=" * 60)
        print(f"  Input     : {self.prompt}")
        print(f"  LLM said  : {self.llm_expression}")
        print()
        print(f"  EML nodes : {self.eml_nodes}")
        print(f"  BEST nodes: {self.best_nodes}  ({self.savings_pct:.1f}% savings)")
        print()
        print("  Rewritten code:")
        print(f"    {self.code}")
        if self.mcts_formula:
            print()
            print(f"  MCTS formula: {self.mcts_formula}  (MSE={self.mcts_mse:.4e})")
        print(f"  [{self.elapsed_s:.2f}s]")
        print("=" * 60)
        print()


# ── LLM callers ───────────────────────────────────────────────────────────────

def _call_openai(system: str, user: str, model: str, api_key: str) -> str:
    try:
        from openai import OpenAI  # type: ignore[import]
    except ImportError:
        raise ImportError(
            "pip install openai  (required for provider='openai')"
        ) from None

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        max_tokens=150,
        temperature=0.1,
    )
    return resp.choices[0].message.content.strip()


def _call_groq(system: str, user: str, model: str, api_key: str) -> str:
    try:
        from groq import Groq  # type: ignore[import]
    except ImportError:
        raise ImportError(
            "pip install groq  (required for provider='groq')"
        ) from None

    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        max_tokens=150,
        temperature=0.1,
    )
    return resp.choices[0].message.content.strip()


def _call_anthropic(system: str, user: str, model: str, api_key: str) -> str:
    try:
        import anthropic as ant  # type: ignore[import]
    except ImportError:
        raise ImportError(
            "pip install anthropic  (required for provider='anthropic')"
        ) from None

    client = ant.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=150,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


# ── Expression analysis ────────────────────────────────────────────────────────

_OP_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("exp",  re.compile(r"\bmath\.exp\b|\bexp\b")),
    ("log",  re.compile(r"\bmath\.log\b|\blog\b|\bln\b")),
    ("sqrt", re.compile(r"\bmath\.sqrt\b|\bsqrt\b")),
    ("pow",  re.compile(r"\bmath\.pow\b|\*\*")),
    ("div",  re.compile(r"/")),
    ("mul",  re.compile(r"(?<![/*])\*(?!\*)")),
    ("sin",  re.compile(r"\bmath\.sin\b|\bsin\b")),
    ("cos",  re.compile(r"\bmath\.cos\b|\bcos\b")),
    ("tanh", re.compile(r"\bmath\.tanh\b|\btanh\b")),
]

# Rough BEST node counts per operation
_BEST_NODES: dict[str, int] = {
    "exp": 1, "log": 1, "ln": 1,
    "sqrt": 3, "pow": 3, "mul": 7, "div": 1,
    "sin": 63, "cos": 63, "tanh": 14,
    "add": 11, "sub": 5,
}
_EML_NODES: dict[str, int] = {
    "exp": 1, "log": 3, "ln": 3,
    "sqrt": 7, "pow": 15, "mul": 13, "div": 15,
    "sin": 245, "cos": 245, "tanh": 17,
    "add": 11, "sub": 5,
}


def _analyze_expression(expr: str) -> tuple[list[str], int, int, float]:
    """
    Identify operations in expr, estimate EML and BEST node counts.

    Returns:
        (ops_found, eml_nodes, best_nodes, savings_pct)
    """
    ops: list[str] = []
    for name, pattern in _OP_PATTERNS:
        if pattern.search(expr):
            ops.append(name)

    # Count occurrences for a rough total
    eml_total  = sum(_EML_NODES.get(op,  5) for op in ops)
    best_total = sum(_BEST_NODES.get(op, 3) for op in ops)

    # Add sub-expression overhead (add/sub from composition)
    n_ops = len(ops)
    if n_ops > 1:
        eml_total  += (n_ops - 1) * 5   # each composition adds ~5 EML nodes
        best_total += (n_ops - 1) * 5

    # Ensure best <= eml
    best_total = min(best_total, eml_total)

    savings = (eml_total - best_total) / max(eml_total, 1) * 100.0
    return ops, eml_total, best_total, savings


def _rewrite_to_best(expr: str) -> str:
    """
    Rewrite a math.* expression to use BEST.* routing.

    This is a simple regex-based rewrite (not a full AST pass).
    """
    e = expr
    e = re.sub(r"\bmath\.exp\b",  "BEST.exp",  e)
    e = re.sub(r"\bmath\.log\b",  "BEST.log",  e)
    e = re.sub(r"\bmath\.sqrt\b", "BEST.sqrt", e)
    e = re.sub(r"\bmath\.pow\b",  "BEST.pow",  e)
    e = re.sub(r"\bmath\.tanh\b", "BEST.tanh", e)
    e = re.sub(r"\bmath\.sin\b",  "BEST.sin",  e)
    e = re.sub(r"\bmath\.cos\b",  "BEST.cos",  e)
    e = re.sub(r"\bmath\.sinh\b", "BEST.sinh", e)
    e = re.sub(r"\bmath\.cosh\b", "BEST.cosh", e)
    return e


# ── Probe-based function identification ──────────────────────────────────────

def _probe_function(
    target_func: Callable[[float], float],
    n: int = 8,
) -> tuple[list[float], list[float]]:
    """Sample target_func at n points in a safe domain."""
    xs = [0.1 + 2.8 * i / (n - 1) for i in range(n)]
    ys: list[float] = []
    for x in xs:
        try:
            y = float(target_func(x))
            if not math.isfinite(y):
                raise ValueError
        except Exception:
            y = 0.0
        ys.append(y)
    return xs, ys


# ── Main entry point ──────────────────────────────────────────────────────────

def suggest_and_optimize(
    prompt: str | None = None,
    *,
    target_func: Callable[[float], float] | None = None,
    provider: str = "mock",
    api_key: str | None = None,
    model: str | None = None,
    run_mcts: bool = False,
    mcts_sims: int = 2000,
    mcts_depth: int = 5,
) -> LLMOptimizeResult:
    """
    Ask an LLM to express a function, then optimize it with BEST routing.

    Either describe the function in words (``prompt``) or pass a Python
    callable (``target_func``).  If both are given, ``prompt`` is used for
    the LLM query and ``target_func`` provides probe points for MCTS.

    Args:
        prompt:      Natural-language description. e.g. "the sigmoid function".
                     Optional if target_func is provided.
        target_func: Python callable: x -> y.  Used to generate probe points
                     for the MCTS stage (if run_mcts=True) and to build an
                     auto-description when prompt is None.
        provider:    'mock' | 'openai' | 'groq' | 'anthropic'.
                     'mock' requires no API key and uses keyword heuristics.
        api_key:     API key for the chosen provider.  If None, reads from
                     env: OPENAI_API_KEY / GROQ_API_KEY / ANTHROPIC_API_KEY.
        model:       Override the default model for the provider.
        run_mcts:    If True, also run MCTS search (gradient-free) and
                     include the best EML tree formula in the result.
        mcts_sims:   Number of MCTS simulations (ignored unless run_mcts=True).
        mcts_depth:  Max EML tree depth for MCTS (ignored unless run_mcts=True).

    Returns:
        LLMOptimizeResult with LLM expression, BEST formula, node counts,
        savings %, executable code, and optional MCTS result.

    Example::

        from monogate.llm import suggest_and_optimize
        import math

        # Quick test — no API key needed
        r = suggest_and_optimize("sigmoid function")
        r.print_summary()

        # With OpenAI:
        r = suggest_and_optimize(
            "GELU activation",
            provider="openai",
            # api_key auto-read from OPENAI_API_KEY env var
        )

        # Pass a callable:
        r = suggest_and_optimize(target_func=math.log, run_mcts=True)
    """
    t0 = time.perf_counter()

    # ── Resolve prompt ─────────────────────────────────────────────────────
    if prompt is None and target_func is None:
        raise ValueError("Provide either prompt or target_func (or both).")

    if prompt is None and target_func is not None:
        # Auto-describe from function name
        fname = getattr(target_func, "__name__", "unknown")
        prompt = f"the {fname} function"

    assert prompt is not None  # mypy

    # ── Resolve provider + model ──────────────────────────────────────────
    prov = provider.lower()
    if prov not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unknown provider {provider!r}. "
            f"Choose from: {', '.join(SUPPORTED_PROVIDERS)}"
        )
    resolved_model = model or _DEFAULT_MODELS.get(prov, "mock")

    # ── Resolve API key ────────────────────────────────────────────────────
    if prov != "mock" and api_key is None:
        env_keys = {
            "openai":    "OPENAI_API_KEY",
            "groq":      "GROQ_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        env_var = env_keys.get(prov, "")
        api_key = os.environ.get(env_var)
        if not api_key:
            raise ValueError(
                f"No API key for provider={provider!r}. "
                f"Set env var {env_var} or pass api_key=..."
            )

    # ── Build LLM user message ────────────────────────────────────────────
    if target_func is not None and prov != "mock":
        xs, ys = _probe_function(target_func)
        user_msg = build_probe_message(xs, ys)
    else:
        user_msg = build_user_message(prompt)

    # ── Call LLM / mock ────────────────────────────────────────────────────
    if prov == "mock":
        llm_expr = mock_response(prompt)
    elif prov == "openai":
        llm_expr = _call_openai(SYSTEM_PROMPT, user_msg, resolved_model, api_key)  # type: ignore[arg-type]
    elif prov == "groq":
        llm_expr = _call_groq(SYSTEM_PROMPT, user_msg, resolved_model, api_key)    # type: ignore[arg-type]
    elif prov == "anthropic":
        llm_expr = _call_anthropic(SYSTEM_PROMPT, user_msg, resolved_model, api_key)  # type: ignore[arg-type]
    else:
        llm_expr = mock_response(prompt)

    # Strip code fences / extra whitespace from LLM response
    llm_expr = llm_expr.strip().strip("`").strip()
    if llm_expr.startswith("python"):
        llm_expr = llm_expr[6:].strip()

    # ── Analyze expression ─────────────────────────────────────────────────
    ops, eml_nodes, best_nodes, savings_pct = _analyze_expression(llm_expr)
    best_formula = _rewrite_to_best(llm_expr)
    code = f"f = lambda x: {best_formula}"

    # ── Optional MCTS search ──────────────────────────────────────────────
    mcts_formula = ""
    mcts_mse     = float("inf")

    if run_mcts:
        try:
            from ..search import mcts_search

            probe_fn = target_func
            if probe_fn is None:
                # Try to evaluate the expression as a function
                def probe_fn(x: float) -> float:  # type: ignore[misc]
                    import math as _m  # noqa: F401  (used by eval)
                    return float(eval(llm_expr, {"math": _m, "x": x}))  # noqa: S307

            result = mcts_search(
                probe_fn,
                depth=mcts_depth,
                n_simulations=mcts_sims,
                seed=42,
            )
            mcts_formula = result.best_formula
            mcts_mse     = result.best_mse
        except Exception:
            pass  # MCTS is best-effort

    elapsed = time.perf_counter() - t0

    return LLMOptimizeResult(
        prompt=prompt,
        llm_expression=llm_expr,
        best_formula=best_formula,
        eml_nodes=eml_nodes,
        best_nodes=best_nodes,
        savings_pct=savings_pct,
        code=code,
        provider=prov,
        model=resolved_model,
        elapsed_s=elapsed,
        mcts_formula=mcts_formula,
        mcts_mse=mcts_mse,
        ops_found=ops,
    )
