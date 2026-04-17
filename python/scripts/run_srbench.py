"""
run_srbench.py -- Session 23: SRBench full run launcher.

Runs monogate MCTS and beam search over all 35 benchmark functions
(Nguyen-12, Keijzer-15, Vladislavleva-8), saves JSON results, and
writes a Markdown report.

Usage:
    cd python/
    python scripts/run_srbench.py                    # quick (500 sims per fn)
    python scripts/run_srbench.py --sims 3000        # full run
    python scripts/run_srbench.py --eml-only         # eml-friendly subset only
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

# Allow running from python/ or repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.srbench.functions import ALL_BENCHMARKS, EML_FRIENDLY
from benchmarks.srbench.runner import run_mcts_benchmark, BenchmarkResult


def run_suite(
    benchmarks: list,
    n_simulations: int = 500,
    depth: int = 4,
    verbose: bool = True,
) -> list[BenchmarkResult]:
    results = []
    n = len(benchmarks)
    for i, fn in enumerate(benchmarks):
        if verbose:
            print(f"[{i+1:2d}/{n}] {fn.name:<20} ({fn.suite}, {fn.difficulty}) ... ", end="", flush=True)
        t0 = time.time()
        result = run_mcts_benchmark(fn, n_simulations=n_simulations, depth=depth)
        elapsed = time.time() - t0
        results.append(result)
        if verbose:
            r2_str = f"R²={result.test_r2:.3f}" if result.test_r2 > -999 else "R²=ERR"
            mse_str = f"MSE={result.best_mse:.2e}" if math.isfinite(result.best_mse) else "MSE=nan"
            print(f"{r2_str}  {mse_str}  {elapsed:.1f}s")
    return results


def classify_result(r: BenchmarkResult) -> str:
    if r.test_r2 >= 0.999:
        return "exact"
    if r.test_r2 >= 0.95:
        return "good"
    if r.test_r2 >= 0.5:
        return "partial"
    return "fail"


def write_json(results: list[BenchmarkResult], path: Path) -> None:
    data = [r.to_dict() for r in results]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Results written to {path}")


def write_report(results: list[BenchmarkResult], path: Path) -> None:
    lines = [
        "# SRBench Full Run — monogate v1.4.0",
        "",
        f"Date: {time.strftime('%Y-%m-%d')}  ·  {len(results)} benchmarks",
        "",
        "## Summary",
        "",
    ]

    by_outcome = {"exact": [], "good": [], "partial": [], "fail": []}
    for r in results:
        by_outcome[classify_result(r)].append(r)

    lines += [
        f"| Outcome | Count | % |",
        f"|---------|-------|---|",
        f"| Exact (R²≥0.999) | {len(by_outcome['exact'])} | {100*len(by_outcome['exact'])/len(results):.0f}% |",
        f"| Good (R²≥0.95)   | {len(by_outcome['good'])} | {100*len(by_outcome['good'])/len(results):.0f}% |",
        f"| Partial (R²≥0.5) | {len(by_outcome['partial'])} | {100*len(by_outcome['partial'])/len(results):.0f}% |",
        f"| Fail (R²<0.5)    | {len(by_outcome['fail'])} | {100*len(by_outcome['fail'])/len(results):.0f}% |",
        "",
    ]

    # Tag breakdown
    eml_friendly = [r for r in results if "eml-friendly" in r.tags]
    non_eml = [r for r in results if "eml-friendly" not in r.tags]
    if eml_friendly:
        eml_good = sum(1 for r in eml_friendly if r.test_r2 >= 0.95)
        non_eml_good = sum(1 for r in non_eml if r.test_r2 >= 0.95)
        lines += [
            "## EML-natural vs Non-EML functions",
            "",
            f"EML-friendly: {eml_good}/{len(eml_friendly)} good (R²≥0.95) = "
            f"{100*eml_good/len(eml_friendly):.0f}%",
            f"Non-EML:      {non_eml_good}/{len(non_eml)} good (R²≥0.95) = "
            f"{100*non_eml_good/max(len(non_eml),1):.0f}%",
            "",
            "**Key hypothesis**: monogate wins disproportionately on EML-friendly",
            "(exp/log-structured) functions. If confirmed, this is the first formal",
            "definition of the 'EML-natural' function class.",
            "",
        ]

    # Full results table
    lines += [
        "## Results by Function",
        "",
        "| Function | Suite | Difficulty | Tags | Test R² | MSE | Nodes | Outcome |",
        "|----------|-------|------------|------|---------|-----|-------|---------|",
    ]
    for r in results:
        tags = ", ".join(r.tags)
        r2_str = f"{r.test_r2:.4f}" if r.test_r2 > -999 else "ERR"
        mse_str = f"{r.best_mse:.2e}" if math.isfinite(r.best_mse) else "nan"
        outcome = classify_result(r)
        lines.append(
            f"| {r.fn_name} | {r.suite} | {r.fn_name} | {tags} "
            f"| {r2_str} | {mse_str} | {r.n_nodes} | {outcome} |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report written to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SRBench full run")
    parser.add_argument("--sims", type=int, default=500,
                        help="MCTS simulations per function (default: 500)")
    parser.add_argument("--depth", type=int, default=4,
                        help="Max search depth (default: 4)")
    parser.add_argument("--eml-only", action="store_true",
                        help="Run only EML-friendly subset")
    parser.add_argument("--out-dir", type=str, default="results",
                        help="Output directory for results")
    args = parser.parse_args()

    benchmarks = EML_FRIENDLY if args.eml_only else ALL_BENCHMARKS
    subset_label = "eml-friendly" if args.eml_only else "full"

    print(f"SRBench Session 23 — monogate v1.4.0")
    print(f"Subset: {subset_label}  ({len(benchmarks)} functions)")
    print(f"MCTS sims per function: {args.sims}")
    print(f"Max depth: {args.depth}")
    print("=" * 60)

    t_start = time.time()
    results = run_suite(benchmarks, n_simulations=args.sims, depth=args.depth)
    t_total = time.time() - t_start

    print(f"\nCompleted {len(results)} benchmarks in {t_total:.1f}s")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tag = f"srbench_{subset_label}_{args.sims}sims"
    write_json(results, out_dir / f"{tag}_results.json")
    write_report(results, out_dir / f"{tag}_report.md")

    # Print summary
    good = sum(1 for r in results if r.test_r2 >= 0.95)
    exact = sum(1 for r in results if r.test_r2 >= 0.999)
    print(f"\n=== SUMMARY ===")
    print(f"Exact (R²≥0.999): {exact}/{len(results)}")
    print(f"Good  (R²≥0.95):  {good}/{len(results)}")
    print(f"Total time: {t_total:.1f}s")


if __name__ == "__main__":
    main()
