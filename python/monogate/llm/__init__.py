"""
monogate.llm — LLM-assisted EML expression optimizer.

Given a natural-language description (or a Python callable), an LLM suggests
a math expression, which is then run through BEST optimization + MCTS to find
the most compact EML representation.

Quick-start (no API key required — uses mock mode)::

    from monogate.llm import suggest_and_optimize

    # Describe in words:
    result = suggest_and_optimize("the sigmoid function")
    print(result.best_formula)   # BEST-routed EML expression
    print(result.code)           # copy-paste Python snippet

    # Pass a callable:
    import math
    result = suggest_and_optimize(target_func=math.exp)
    print(result.eml_nodes, "->", result.best_nodes, "nodes")

Production usage (set env var, then run)::

    export OPENAI_API_KEY="sk-..."
    python -m monogate.llm.cli "GELU activation"

    # or in Python:
    result = suggest_and_optimize("GELU activation", provider="openai")

Supported providers:  mock | openai | groq | anthropic
"""

from .optimizer import suggest_and_optimize, LLMOptimizeResult, SUPPORTED_PROVIDERS

__all__ = ["suggest_and_optimize", "LLMOptimizeResult", "SUPPORTED_PROVIDERS"]
