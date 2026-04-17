"""
monogate.frontiers.deml_census
==============================
Session 9 — DEML Dual Gate: Physics Census and Barrier Analysis.

The negative-exponent barrier (Sessions 6–8) blocks 14/15 physics laws from
EML representation because every EML-family operator uses ``exp(left_subtree)``
as one component, making decay functions unreachable.

DEML (``deml(x, y) = exp(−x) − ln(y)``) is the natural dual of EML.  Its
defining identity ``deml(x, 1) = exp(−x)`` makes exponential decay a 1-node
native primitive.  Combined with EML in the BEST router you get:

    exp(+x) → 1 node  (EML)
    exp(−x) → 1 node  (DEML)

This module runs the full 15-law physics census for three configurations:

1. EML alone (baseline from Session 6)
2. DEML alone (new — how many laws are *DEML-native*?)
3. EML + DEML combined (how many laws become reachable with both gates?)

Key open question (P2 from CONTEXT.md):
    Does EML + DEML break the barrier for all 15 physics laws?

Usage::

    python -m monogate.frontiers.deml_census
    python -m monogate.frontiers.deml_census --n-simulations 500 --quick
"""

from __future__ import annotations

import argparse
import math
import time
from typing import Callable

__all__ = [
    "run_deml_census",
    "plot_deml_census",
    "DEML_NATIVE_THRESHOLD",
]

DEML_NATIVE_THRESHOLD: float = 1e-6


# ── Internal helpers ──────────────────────────────────────────────────────────

def _census_one(
    op_name: str,
    laws: list[dict],
    n_simulations: int,
    depth: int,
    verbose: bool,
) -> list[dict]:
    """Run MCTS census for one operator on *laws*, returning per-law result dicts."""
    from monogate.search.mcts import mcts_search
    from monogate.frontiers.operator_comparison import _EVAL_FNS

    eval_fn = _EVAL_FNS[op_name]
    results = []

    for law in laws:
        fn = law["fn"]
        lo, hi = law["domain"]
        n_probe = 60
        probe = [lo + (hi - lo) * i / (n_probe - 1) for i in range(n_probe)]

        valid_x = [x for x in probe if _safe(fn, x)]
        if len(valid_x) < 10:
            results.append({"name": law.get("name", "?"), "mse": float("inf"), "native": False})
            continue

        try:
            r = mcts_search(
                target_fn=fn,
                probe_points=valid_x,
                depth=depth,
                n_simulations=n_simulations,
                seed=42,
                eval_tree_fn=eval_fn,
            )
            native = r.best_mse < DEML_NATIVE_THRESHOLD
            results.append({
                "name":     law.get("name", "?"),
                "category": law.get("category", "?"),
                "mse":      r.best_mse,
                "formula":  r.best_formula,
                "native":   native,
                "operator": op_name,
            })
        except Exception as exc:
            results.append({
                "name":     law.get("name", "?"),
                "category": law.get("category", "?"),
                "mse":      float("inf"),
                "formula":  "",
                "native":   False,
                "operator": op_name,
                "error":    str(exc),
            })

        if verbose:
            mse = results[-1]["mse"]
            tag = "NATIVE" if results[-1]["native"] else f"mse={mse:.4f}"
            print(f"  [{op_name}] {law.get('name', '?'):40s} {tag}")

    return results


def _safe(fn: Callable, x: float) -> bool:
    try:
        return math.isfinite(fn(x))
    except Exception:
        return False


# ── Public API ────────────────────────────────────────────────────────────────

def run_deml_census(
    n_simulations: int = 5000,
    depth: int = 2,
    verbose: bool = True,
) -> dict:
    """Run the 3-configuration physics census: EML, DEML, and EML+DEML combined.

    Args:
        n_simulations: MCTS simulation budget per law per operator.
        depth:         Tree search depth (2 = shallow/fast, 4 = thorough).
        verbose:       Print per-law progress lines.

    Returns:
        dict with keys:
            ``eml_results``      — list of per-law dicts for EML alone
            ``deml_results``     — list of per-law dicts for DEML alone
            ``combined_results`` — per-law dicts: native if native in EML *or* DEML
            ``n_eml_native``     — int: laws native to EML
            ``n_deml_native``    — int: laws native to DEML
            ``n_combined_native``— int: laws native to EML or DEML
            ``n_total``          — int: total laws
            ``summary_table``    — str: GitHub-Flavored Markdown summary
            ``elapsed_s``        — float: wall-clock seconds
    """
    from monogate.frontiers.law_complexity import FUNCTIONAL_LAWS

    t0 = time.perf_counter()
    laws = FUNCTIONAL_LAWS

    if verbose:
        print("\n" + "=" * 65)
        print("  DEML DUAL GATE — PHYSICS CENSUS (Session 9)")
        print("=" * 65)
        print(f"  Laws: {len(laws)}  |  n_simulations: {n_simulations}  |  depth: {depth}")

    if verbose:
        print("\n[1/2] EML baseline")
        print("-" * 50)
    eml_results = _census_one("EML", laws, n_simulations, depth, verbose)

    if verbose:
        print("\n[2/2] DEML dual gate")
        print("-" * 50)
    deml_results = _census_one("DEML", laws, n_simulations, depth, verbose)

    # Combined: native if native in either operator
    combined_results = []
    for eml_r, deml_r in zip(eml_results, deml_results):
        native_combined = eml_r.get("native", False) or deml_r.get("native", False)
        best_mse = min(eml_r.get("mse", float("inf")), deml_r.get("mse", float("inf")))
        best_op = "EML" if eml_r.get("mse", float("inf")) <= deml_r.get("mse", float("inf")) else "DEML"
        combined_results.append({
            "name":          eml_r.get("name", "?"),
            "category":      eml_r.get("category", "?"),
            "native":        native_combined,
            "best_mse":      best_mse,
            "best_operator": best_op,
            "eml_mse":       eml_r.get("mse", float("inf")),
            "deml_mse":      deml_r.get("mse", float("inf")),
        })

    n_eml      = sum(1 for r in eml_results  if r.get("native"))
    n_deml     = sum(1 for r in deml_results if r.get("native"))
    n_combined = sum(1 for r in combined_results if r.get("native"))
    n_total    = len(laws)
    elapsed    = time.perf_counter() - t0

    summary = _make_summary_table(eml_results, deml_results, combined_results)

    if verbose:
        print("\n" + "=" * 65)
        print(f"  EML native:          {n_eml}/{n_total}")
        print(f"  DEML native:         {n_deml}/{n_total}")
        print(f"  EML+DEML combined:   {n_combined}/{n_total}")
        print(f"  Elapsed: {elapsed:.1f}s")
        print("=" * 65)
        print("\n" + summary)

    return {
        "eml_results":       eml_results,
        "deml_results":      deml_results,
        "combined_results":  combined_results,
        "n_eml_native":      n_eml,
        "n_deml_native":     n_deml,
        "n_combined_native": n_combined,
        "n_total":           n_total,
        "summary_table":     summary,
        "elapsed_s":         elapsed,
    }


def _make_summary_table(
    eml: list[dict],
    deml: list[dict],
    combined: list[dict],
) -> str:
    """Return a Markdown table comparing EML, DEML, and combined results."""
    rows = [
        "| Law | EML MSE | DEML MSE | Combined | Best gate |",
        "|-----|---------|----------|----------|-----------|",
    ]
    for e, d, c in zip(eml, deml, combined):
        name = e.get("name", "?")[:35]
        e_mse = e.get("mse", float("inf"))
        d_mse = d.get("mse", float("inf"))
        e_tag = "NATIVE" if e.get("native") else f"{e_mse:.3f}"
        d_tag = "NATIVE" if d.get("native") else f"{d_mse:.3f}"
        c_tag = "**NATIVE**" if c.get("native") else "blocked"
        best  = c.get("best_operator", "—")
        rows.append(f"| {name} | {e_tag} | {d_tag} | {c_tag} | {best} |")
    return "\n".join(rows)


def plot_deml_census(results: dict) -> "Any":
    """Return a 3-panel matplotlib Figure comparing EML, DEML, and combined.

    Panel 1 (left):  Bar chart of native law counts per configuration.
    Panel 2 (center): Per-law MSE heatmap (EML vs DEML).
    Panel 3 (right):  Pie chart of EML-only / DEML-only / both / blocked.

    Args:
        results: dict returned by :func:`run_deml_census`.

    Returns:
        matplotlib Figure (not shown; caller must call plt.show() or savefig).
    """
    import matplotlib.pyplot as plt
    import numpy as np

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("DEML Dual Gate — Physics Census (Session 9)", fontsize=13)

    # Panel 1: native counts
    ax = axes[0]
    configs = ["EML", "DEML", "EML+DEML"]
    counts  = [results["n_eml_native"], results["n_deml_native"], results["n_combined_native"]]
    colors  = ["#4C72B0", "#DD8452", "#55A868"]
    bars    = ax.bar(configs, counts, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_ylim(0, results["n_total"] + 1)
    ax.set_ylabel("Laws native / 15")
    ax.set_title("Native law counts")
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, count + 0.1, str(count),
                ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.axhline(results["n_total"], color="gray", linestyle="--", linewidth=0.8, label="total (15)")
    ax.legend(fontsize=8)

    # Panel 2: per-law MSE comparison heatmap
    ax = axes[1]
    names    = [r.get("name", "?")[:20] for r in results["eml_results"]]
    eml_mse  = [min(r.get("mse", 10.0), 10.0) for r in results["eml_results"]]
    deml_mse = [min(r.get("mse", 10.0), 10.0) for r in results["deml_results"]]
    x        = np.arange(len(names))
    width    = 0.4
    ax.barh(x + width / 2, eml_mse,  width, label="EML",  color="#4C72B0", alpha=0.8)
    ax.barh(x - width / 2, deml_mse, width, label="DEML", color="#DD8452", alpha=0.8)
    ax.set_yticks(x)
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel("MSE (capped at 10)")
    ax.set_title("Per-law MSE: EML vs DEML")
    ax.axvline(DEML_NATIVE_THRESHOLD, color="green", linestyle="--", linewidth=0.8,
               label=f"native threshold ({DEML_NATIVE_THRESHOLD:.0e})")
    ax.legend(fontsize=7)

    # Panel 3: breakdown pie
    ax = axes[2]
    eml_only  = sum(1 for e, d in zip(results["eml_results"], results["deml_results"])
                    if e.get("native") and not d.get("native"))
    deml_only = sum(1 for e, d in zip(results["eml_results"], results["deml_results"])
                    if not e.get("native") and d.get("native"))
    both      = sum(1 for e, d in zip(results["eml_results"], results["deml_results"])
                    if e.get("native") and d.get("native"))
    blocked   = results["n_total"] - results["n_combined_native"]
    pie_vals  = [eml_only, deml_only, both, blocked]
    pie_lbls  = ["EML only", "DEML only", "Both", "Blocked"]
    pie_cols  = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
    non_zero  = [(v, l, c) for v, l, c in zip(pie_vals, pie_lbls, pie_cols) if v > 0]
    if non_zero:
        vals, lbls, cols = zip(*non_zero)
        ax.pie(vals, labels=lbls, colors=cols, autopct="%d", startangle=90,
               textprops={"fontsize": 9})
    ax.set_title("Law breakdown")

    fig.tight_layout()
    return fig


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cli() -> None:
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="DEML dual gate census")
    parser.add_argument("--n-simulations", type=int, default=5000)
    parser.add_argument("--depth",         type=int, default=2)
    parser.add_argument("--quick",         action="store_true",
                        help="Run with n_simulations=300 and depth=2 for a fast smoke test")
    parser.add_argument("--full",          action="store_true",
                        help="Run with n_simulations=10000 for overnight quality")
    parser.add_argument("--plot",          action="store_true",
                        help="Show matplotlib figure after census")
    parser.add_argument("--output",        type=str, default="results/deml_census_full.json",
                        help="Path to write JSON results (default: results/deml_census_full.json)")
    args = parser.parse_args()

    if args.quick:
        n_sim = 300
    elif args.full:
        n_sim = 10000
    else:
        n_sim = args.n_simulations

    results = run_deml_census(n_simulations=n_sim, depth=args.depth, verbose=True)

    # Serialise results (convert inf/nan to string for JSON)
    def _serialise(obj):
        if isinstance(obj, float):
            if obj == float("inf"):
                return "inf"
            if obj != obj:  # NaN
                return "nan"
        return obj

    def _clean(d):
        if isinstance(d, dict):
            return {k: _clean(v) for k, v in d.items()}
        if isinstance(d, list):
            return [_clean(v) for v in d]
        return _serialise(d)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Build JSON-safe copy (exclude non-serialisable keys)
    json_results = {k: _clean(v) for k, v in results.items() if k != "summary_table"}
    json_results["summary_table"] = results["summary_table"]
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(json_results, fh, indent=2)
    print(f"\n  Results saved: {out_path}")

    if args.plot:
        fig = plot_deml_census(results)
        plot_path = out_path.with_suffix(".png")
        fig.savefig(str(plot_path), dpi=150, bbox_inches="tight")
        print(f"  Plot saved:    {plot_path}")
        try:
            import matplotlib.pyplot as plt
            plt.show()
        except Exception:
            pass


if __name__ == "__main__":
    _cli()
