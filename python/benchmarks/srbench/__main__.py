"""
Entry point: python -m benchmarks.srbench.runner [--full] [--suite nguyen|keijzer|vlad]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

OUT_JSON = Path(__file__).parent.parent.parent / "results" / "srbench_results.json"
OUT_REPORT = Path(__file__).parent.parent.parent / "results" / "srbench_report.md"
OUT_PLOT = Path(__file__).parent.parent.parent / "results" / "srbench_pareto.png"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SRBench benchmarks")
    parser.add_argument("--full", action="store_true", help="Full run (10k sims)")
    parser.add_argument("--suite", choices=["nguyen", "keijzer", "vlad", "all"],
                        default="nguyen")
    parser.add_argument("--n-sims", type=int, default=3000)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--no-beam", action="store_true")
    args = parser.parse_args()

    from .functions import NGUYEN, KEIJZER, VLADISLAVLEVA, ALL_BENCHMARKS
    from .runner import run_suite
    from .report import generate_report, plot_pareto, save_results_json

    suite_map = {
        "nguyen": NGUYEN,
        "keijzer": KEIJZER,
        "vlad": VLADISLAVLEVA,
        "all": ALL_BENCHMARKS,
    }
    fns = suite_map[args.suite]
    n_sims = 10000 if args.full else args.n_sims

    print(f"Running SRBench: suite={args.suite}, n_sims={n_sims}, depth={args.depth}")
    print(f"  {len(fns)} functions")

    results = run_suite(fns, n_simulations=n_sims, depth=args.depth,
                        use_beam=not args.no_beam)

    save_results_json(results, OUT_JSON)
    table = generate_report(results, out_path=OUT_REPORT)
    print("\n" + table)
    plot_pareto(results, OUT_PLOT)


if __name__ == "__main__":
    main()
