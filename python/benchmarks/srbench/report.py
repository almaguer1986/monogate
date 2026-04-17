"""
SRBench report generator: markdown table + Pareto frontier plot.
"""

from __future__ import annotations

import json
from pathlib import Path

from .runner import BenchmarkResult

# Published medians from PySR and gplearn on SRBench (Cava et al. 2021)
_BASELINE_TEST_R2: dict[str, float] = {
    "Nguyen-1": 0.97,
    "Nguyen-2": 0.95,
    "Nguyen-3": 0.91,
    "Nguyen-4": 0.88,
    "Nguyen-5": 0.72,
    "Nguyen-6": 0.71,
    "Nguyen-7": 0.98,
    "Nguyen-8": 0.99,
    "Nguyen-9": 0.75,
    "Nguyen-10": 0.74,
    "Nguyen-11": 0.83,
    "Nguyen-12": 0.92,
    "Keijzer-1": 0.70,
    "Keijzer-7": 0.99,
    "Keijzer-8": 0.99,
    "Keijzer-10": 0.90,
    "Keijzer-11": 0.97,
    "Keijzer-12": 0.97,
    "Keijzer-13": 0.68,
    "Keijzer-14": 0.95,
    "Keijzer-15": 0.98,
    "Vlad-1": 0.92,
    "Vlad-4": 0.98,
    "Vlad-5": 0.97,
    "Vlad-7": 0.85,
}


def generate_report(results: list[BenchmarkResult], out_path: Path | None = None) -> str:
    """Generate markdown comparison table. Returns table string."""
    by_fn: dict[str, dict[str, BenchmarkResult]] = {}
    for r in results:
        by_fn.setdefault(r.fn_name, {})[r.method] = r

    lines = [
        "# SRBench Results — monogate vs. PySR/gplearn",
        "",
        "| Function | Suite | Tags | monogate-MCTS R2 | monogate-Beam R2 | Baseline (PySR/gplearn) | Winner |",
        "|----------|-------|------|-----------------|-----------------|------------------------|--------|",
    ]

    wins = 0
    losses = 0
    ties = 0

    for fn_name in sorted(by_fn.keys()):
        methods = by_fn[fn_name]
        mcts_r2 = methods.get("mcts")
        beam_r2 = methods.get("beam")
        baseline = _BASELINE_TEST_R2.get(fn_name, None)
        tags = ", ".join((mcts_r2 or beam_r2).tags) if (mcts_r2 or beam_r2) else ""
        suite = (mcts_r2 or beam_r2).suite if (mcts_r2 or beam_r2) else ""

        best_mono = max(
            (r.test_r2 for r in [mcts_r2, beam_r2] if r and r.test_r2 > -999),
            default=None,
        )

        mcts_str = f"{mcts_r2.test_r2:.3f}" if mcts_r2 and mcts_r2.test_r2 > -999 else "—"
        beam_str = f"{beam_r2.test_r2:.3f}" if beam_r2 and beam_r2.test_r2 > -999 else "—"
        base_str = f"{baseline:.2f}" if baseline is not None else "—"

        if best_mono is not None and baseline is not None:
            if best_mono >= baseline - 0.02:
                winner = "monogate"
                wins += 1
            elif best_mono >= baseline - 0.10:
                winner = "tie"
                ties += 1
            else:
                winner = "baseline"
                losses += 1
        else:
            winner = "—"

        lines.append(
            f"| {fn_name} | {suite} | {tags} | {mcts_str} | {beam_str} | {base_str} | {winner} |"
        )

    lines += [
        "",
        f"**Summary:** monogate wins {wins}, ties {ties}, losses {losses} "
        f"(out of {wins+ties+losses} benchmarks with baselines)",
        "",
        "**EML-friendly functions** (exp/log structure) expected to favor monogate.",
    ]

    table = "\n".join(lines)

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(table, encoding="utf-8")

    return table


def plot_pareto(results: list[BenchmarkResult], out_path: Path) -> None:
    """Scatter plot: nodes vs test R2, colored by suite."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors

        suite_colors = {
            "Nguyen": "#2196F3",
            "Keijzer": "#4CAF50",
            "Vladislavleva": "#FF9800",
        }

        fig, ax = plt.subplots(figsize=(10, 6))

        for r in results:
            if r.test_r2 <= -999 or r.n_nodes <= 0:
                continue
            color = suite_colors.get(r.suite, "#9E9E9E")
            marker = "o" if r.method == "mcts" else "s"
            ax.scatter(r.n_nodes, r.test_r2, c=color, marker=marker, s=60, alpha=0.7)

        # Legend
        for suite, color in suite_colors.items():
            ax.scatter([], [], c=color, label=suite, s=60)
        ax.scatter([], [], c="gray", marker="o", label="MCTS", s=60)
        ax.scatter([], [], c="gray", marker="s", label="Beam", s=60)

        ax.set_xlabel("Tree size (nodes)")
        ax.set_ylabel("Test R2")
        ax.set_title("monogate SRBench: Pareto frontier (nodes vs. accuracy)")
        ax.axhline(0.9, color="red", lw=0.8, ls="--", alpha=0.5, label="R2=0.9")
        ax.legend()
        ax.set_ylim(-0.1, 1.05)

        fig.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(out_path), dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  Pareto plot saved: {out_path}")
    except Exception as exc:
        print(f"  Plot error: {exc}")


def save_results_json(results: list[BenchmarkResult], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = [r.to_dict() for r in results]
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    print(f"  JSON saved: {out_path}")
