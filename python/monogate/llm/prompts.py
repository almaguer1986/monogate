"""
monogate.llm.prompts — Prompt templates for LLM expression generation.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are a mathematical expression compiler for the monogate EML optimizer.

Given a description of a mathematical function, output a single Python
expression using ONLY these primitives:

  math.exp(x)   math.log(x)   math.sqrt(x)
  +  -  *  /  **
  numeric constants (e.g., 0.5, 3.14159)
  the variable x

Rules:
- Output ONE Python expression only. No imports, no assignments, no comments.
- Do not use math.sin, math.cos, math.tan, math.tanh, math.erf directly —
  express them via exp and log if needed.
- For unknown or non-elementary functions, give your best exp/log approximation.
- If the function is a composition, express it fully.

Examples:
  "sigmoid"           -> math.exp(x) / (1 + math.exp(x))
  "ReLU"              -> x * (x > 0)   # special: not exp/log
  "exp(-x^2)"         -> math.exp(-x**2)
  "1/x"               -> 1 / x
  "ln(1 + exp(x))"    -> math.log(1 + math.exp(x))
  "x * exp(-x)"       -> x * math.exp(-x)
"""

USER_TEMPLATE = "Express this function as a Python expression: {prompt}"

PROBE_SYSTEM = """\
You are a mathematical function identifier.

Given sample (x, y) pairs, identify the mathematical function and express it
as a Python expression using only: math.exp, math.log, math.sqrt, +, -, *, /,
**, numeric constants, and the variable x.

Output ONE Python expression. No explanation.
"""

PROBE_USER_TEMPLATE = """\
The function produces these (x, y) values:
{samples}

Express the function as: f(x) = ?"""


def build_user_message(prompt: str) -> str:
    return USER_TEMPLATE.format(prompt=prompt)


def build_probe_message(xs: list[float], ys: list[float], n: int = 8) -> str:
    samples = "\n".join(
        f"  f({xs[i]:.3f}) = {ys[i]:.6f}"
        for i in range(min(n, len(xs)))
    )
    return PROBE_USER_TEMPLATE.format(samples=samples)


# ── Mock responses ─────────────────────────────────────────────────────────────
# Fallback when no API key is configured.  Keyword-matched heuristics.

_MOCK_MAP: list[tuple[list[str], str]] = [
    (["sigmoid", "logistic", "1/(1+exp"],
     "math.exp(x) / (1.0 + math.exp(x))"),

    (["gelu", "gaussian error", "gaussian linear"],
     "0.5 * x * (1.0 + math.tanh(0.7978845608 * (x + 0.044715 * x**3)))"),

    (["swish", "silu"],
     "x * math.exp(x) / (1.0 + math.exp(x))"),

    (["softplus", "smooth relu", "smooth rectified"],
     "math.log(1.0 + math.exp(x))"),

    (["relu", "rectified linear"],
     "x * (1 if x > 0 else 0)"),

    (["exp", "exponential", "e^x", "exp(x)"],
     "math.exp(x)"),

    (["log", "ln", "natural log", "logarithm"],
     "math.log(x)"),

    (["sin", "sine"],
     "math.exp(1j * x).imag"),  # not directly expressible in real EML

    (["gaussian", "normal", "bell curve", "exp(-x"],
     "math.exp(-x**2 / 2.0)"),

    (["cauchy", "lorentzian", "1/(1+x"],
     "1.0 / (1.0 + x**2)"),

    (["mish"],
     "x * math.tanh(math.log(1.0 + math.exp(x)))"),

    (["elu", "exponential linear"],
     "x if x > 0 else (math.exp(x) - 1.0)"),

    (["arctan", "atan", "inverse tangent"],
     "x / (1.0 + x**2)"),   # Padé approximation

    (["tanh", "hyperbolic tangent"],
     "(math.exp(x) - math.exp(-x)) / (math.exp(x) + math.exp(-x))"),

    (["cosh", "hyperbolic cosine"],
     "(math.exp(x) + math.exp(-x)) / 2.0"),

    (["sinh", "hyperbolic sine"],
     "(math.exp(x) - math.exp(-x)) / 2.0"),

    (["erf", "error function"],
     "1.0 - math.exp(-x**2 * (0.278393 + x**2 * 0.230389))"),  # approx
]


def mock_response(prompt: str) -> str:
    """
    Return a heuristic expression for common functions without calling an LLM.

    Matches prompt against keyword lists and returns the corresponding
    Python expression.  Falls back to exp(x) when no match is found.
    """
    lower = prompt.lower()
    for keywords, expr in _MOCK_MAP:
        if any(kw in lower for kw in keywords):
            return expr
    # Generic fallback: treat as exp-family
    return "math.exp(x)"
