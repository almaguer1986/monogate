"""
monogate.llm.cli — Command-line interface for the LLM optimizer.

Usage:
    python -m monogate.llm.cli "sigmoid function"
    python -m monogate.llm.cli --provider openai "GELU activation"
    python -m monogate.llm.cli --provider groq --mcts "1/(1+x^2)"
    python -m monogate.llm.cli --list-providers
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="monogate-optimize",
        description=(
            "Ask an LLM to express a function, then optimize it with BEST routing.\n"
            "No API key required with --provider mock (default)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  monogate-optimize "sigmoid function"
  monogate-optimize --provider openai "GELU activation"
  monogate-optimize --provider groq --mcts "1/(1+x^2) Cauchy kernel"
  monogate-optimize --provider anthropic --model claude-haiku-4-5-20251001 "swish activation"

environment variables:
  OPENAI_API_KEY      — required for --provider openai
  GROQ_API_KEY        — required for --provider groq
  ANTHROPIC_API_KEY   — required for --provider anthropic
        """,
    )

    parser.add_argument(
        "prompt", nargs="?", default=None,
        help="Natural-language description of the function to optimize.",
    )
    parser.add_argument(
        "--provider", "-p", default="mock",
        choices=["mock", "openai", "groq", "anthropic"],
        help="LLM provider (default: mock — no API key required).",
    )
    parser.add_argument(
        "--model", "-m", default=None,
        help="Model ID override (e.g. gpt-4o, llama3-70b-8192).",
    )
    parser.add_argument(
        "--api-key", "-k", default=None,
        help="API key (overrides environment variable).",
    )
    parser.add_argument(
        "--mcts", action="store_true",
        help="Also run MCTS search and show best EML formula found.",
    )
    parser.add_argument(
        "--mcts-sims", type=int, default=2000,
        help="Number of MCTS simulations (default: 2000).",
    )
    parser.add_argument(
        "--list-providers", action="store_true",
        help="List supported providers and exit.",
    )

    args = parser.parse_args(argv)

    if args.list_providers:
        print("Supported providers:")
        print("  mock      — no API key (keyword heuristics)")
        print("  openai    — pip install openai;   env OPENAI_API_KEY")
        print("  groq      — pip install groq;     env GROQ_API_KEY")
        print("  anthropic — pip install anthropic; env ANTHROPIC_API_KEY")
        return 0

    if args.prompt is None:
        parser.print_help()
        print("\nerror: prompt is required (or use --list-providers)")
        return 1

    from .optimizer import suggest_and_optimize

    try:
        result = suggest_and_optimize(
            args.prompt,
            provider=args.provider,
            api_key=args.api_key,
            model=args.model,
            run_mcts=args.mcts,
            mcts_sims=args.mcts_sims,
        )
        result.print_summary()
        return 0

    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ImportError as e:
        print(f"dependency missing: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
