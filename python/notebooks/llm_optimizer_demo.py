"""
llm_optimizer_demo.py — LLM-assisted EML expression optimization demo.
=======================================================================

Demonstrates suggest_and_optimize() with the mock provider (no API key needed):

  1. Natural-language inputs for common activation functions
  2. Callable-based identification (pass a Python function)
  3. MCTS search for minimal EML tree (optional)
  4. Code generation for copy-paste BEST routing

Run:
    cd python/
    python notebooks/llm_optimizer_demo.py

For real LLM results:
    OPENAI_API_KEY=sk-... python notebooks/llm_optimizer_demo.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from monogate.llm import suggest_and_optimize


# ── Detect provider ───────────────────────────────────────────────────────────

import os
if os.environ.get("OPENAI_API_KEY"):
    PROVIDER = "openai"
elif os.environ.get("GROQ_API_KEY"):
    PROVIDER = "groq"
elif os.environ.get("ANTHROPIC_API_KEY"):
    PROVIDER = "anthropic"
else:
    PROVIDER = "mock"

print()
print("=" * 64)
print(f"  monogate LLM optimizer demo  [provider={PROVIDER!r}]")
print("=" * 64)
if PROVIDER == "mock":
    print()
    print("  Running in MOCK mode (no API key). Results use keyword")
    print("  heuristics. Set OPENAI_API_KEY for real LLM responses.")
print()


# ── Section 1: Common activation functions ────────────────────────────────────

print("-" * 64)
print("  1. Common activation functions")
print("-" * 64)

prompts = [
    "sigmoid function 1/(1+exp(-x))",
    "GELU activation",
    "Swish / SiLU activation",
    "Softplus smooth ReLU",
    "Gaussian bell curve exp(-x^2/2)",
    "tanh hyperbolic tangent",
]

for prompt in prompts:
    r = suggest_and_optimize(prompt, provider=PROVIDER)
    print(f"\n  [{prompt}]")
    print(f"    LLM  : {r.llm_expression[:70]}")
    print(f"    BEST : {r.best_formula[:70]}")
    print(f"    Nodes: {r.eml_nodes} EML -> {r.best_nodes} BEST  ({r.savings_pct:.0f}% savings)")

print()


# ── Section 2: Callable identification ───────────────────────────────────────

print("-" * 64)
print("  2. Callable identification (pass a Python function)")
print("-" * 64)

callables = [
    ("math.exp",  math.exp),
    ("math.log",  math.log),
    ("softplus",  lambda x: math.log(1 + math.exp(x))),
    ("x^2",       lambda x: x * x),
]

for name, fn in callables:
    r = suggest_and_optimize(target_func=fn, provider=PROVIDER)
    print(f"\n  f(x) = {name}")
    print(f"    LLM  : {r.llm_expression[:70]}")
    print(f"    BEST : {r.best_formula[:70]}")
    print(f"    Nodes: {r.eml_nodes} EML -> {r.best_nodes} BEST")

print()


# ── Section 3: MCTS search ────────────────────────────────────────────────────

print("-" * 64)
print("  3. MCTS search for exact EML tree (gradient-free)")
print("-" * 64)
print()
print("  Running MCTS for target f(x) = exp(x)...")

r = suggest_and_optimize(
    target_func=math.exp,
    provider=PROVIDER,
    run_mcts=True,
    mcts_sims=3000,
)
print(f"  LLM expression : {r.llm_expression}")
print(f"  MCTS found     : {r.mcts_formula}  (MSE={r.mcts_mse:.4e})")
print(f"  Expected       : eml(x, 1.0) = exp(x) - ln(1) = exp(x)  [exact]")

print()
print("  Running MCTS for target f(x) = ln(x)  [x in (0.1, 3.0)]...")

r2 = suggest_and_optimize(
    "natural logarithm ln(x)",
    target_func=math.log,
    provider=PROVIDER,
    run_mcts=True,
    mcts_sims=3000,
)
print(f"  LLM expression : {r2.llm_expression}")
print(f"  MCTS found     : {r2.mcts_formula}  (MSE={r2.mcts_mse:.4e})")

print()


# ── Section 4: Code generation ────────────────────────────────────────────────

print("-" * 64)
print("  4. Generated code snippets")
print("-" * 64)
print()

results_for_code = [
    suggest_and_optimize("sigmoid function", provider=PROVIDER),
    suggest_and_optimize("GELU activation",  provider=PROVIDER),
    suggest_and_optimize("softplus",         provider=PROVIDER),
]

for r in results_for_code:
    print(f"  # {r.prompt}")
    print(f"  {r.code}")
    print()


# ── Section 5: Euler bypass for sin ──────────────────────────────────────────

print("-" * 64)
print("  5. Complex Euler bypass for sin(x)")
print("-" * 64)
print()

from monogate import sin_via_euler, cos_via_euler, euler_path_node
from monogate.complex_eval import formula_complex

node = euler_path_node()
print(f"  Euler path node : {formula_complex(node)}")
print(f"  sin(pi/4) exact : {sin_via_euler(math.pi / 4):.15f}")
print(f"  math.sin(pi/4)  : {math.sin(math.pi / 4):.15f}")
print(f"  difference      : {abs(sin_via_euler(math.pi/4) - math.sin(math.pi/4)):.2e}")
print()
print("  The LLM optimizer can't find a real-valued EML tree for sin(x)")
print("  (Infinite Zeros Barrier). But Im(eml(ix,1)) = sin(x) exactly.")

print()
print("=" * 64)
print("  DONE")
print("=" * 64)
print()
if PROVIDER == "mock":
    print("  To try with a real LLM:")
    print("    export OPENAI_API_KEY=sk-...")
    print("    python notebooks/llm_optimizer_demo.py")
    print()
    print("  CLI usage:")
    print("    python -m monogate.llm.cli 'GELU activation'")
    print("    python -m monogate.llm.cli --provider openai 'sigmoid'")
