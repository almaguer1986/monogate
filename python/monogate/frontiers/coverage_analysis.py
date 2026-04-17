"""
monogate.frontiers.coverage_analysis
=====================================
Session 10 — DEML Physics Census: barrier classification and coverage analysis.

Classifies WHY each physics law is blocked under a given operator configuration
and generates coverage tables and heatmap figures.

Usage::

    python -m monogate.frontiers.coverage_analysis
    python -m monogate.frontiers.coverage_analysis --census-file results/deml_census_full.json
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable

__all__ = [
    "classify_barrier",
    "coverage_table",
    "plot_coverage_heatmap",
    "BARRIER_TYPES",
]

# ── Barrier taxonomy ──────────────────────────────────────────────────────────

BARRIER_TYPES: dict[str, str] = {
    "native":          "Native (≤1 node)",
    "neg_exp_simple":  "Negative-exponent, simple arg   — DEML fixes",
    "neg_exp_nested":  "Negative-exponent, nested arg   — needs EXL composition",
    "power_law":       "Pure power law                  — EXL native",
    "rational":        "Rational / reciprocal            — EDL native",
    "composite_decay": "Composite decay (exp·power)     — needs EXL+DEML",
    "other":           "Other / unclassified",
}

# ── Per-law barrier classification ───────────────────────────────────────────

def classify_barrier(law: dict, eml_native: bool, deml_native: bool) -> str:
    """Return the barrier type string for a single law given census results.

    Args:
        law:        Entry from FUNCTIONAL_LAWS (must have "fn" and "name" keys).
        eml_native: Whether EML achieved MSE < threshold for this law.
        deml_native: Whether DEML achieved MSE < threshold for this law.

    Returns:
        One of the keys in :data:`BARRIER_TYPES`.
    """
    if eml_native or deml_native:
        return "native"

    name = law.get("name", "").lower()
    fn   = law.get("fn")

    # Probe the function to infer structure
    if fn is None:
        return "other"

    # Check if output is always positive (power/rational laws)
    try:
        xs = [0.5, 1.0, 1.5, 2.0, 2.5]
        vals = [fn(x) for x in xs if _safe(fn, x)]
        if not vals:
            return "other"
        all_positive = all(v > 0 for v in vals)
        monotone_dec = vals == sorted(vals, reverse=True)
        monotone_inc = vals == sorted(vals)
    except Exception:
        return "other"

    # Gaussian / Maxwell-Boltzmann: exp(-x²) pattern
    if "gaussian" in name or "maxwell" in name:
        return "neg_exp_nested"

    # Arrhenius: exp(-1/x) — simple negated argument, DEML can handle with pre-composition
    if "arrhenius" in name:
        return "neg_exp_simple"

    # RC discharge: 1 - exp(-x) — DEML handles exp(-x) part
    if "rc" in name or "discharge" in name:
        return "neg_exp_simple"

    # Planck, Fermi-Dirac: 1/(exp(x) ± 1) — EML handles exp(x), denominator is the issue
    if "planck" in name or "fermi" in name or "bose" in name:
        return "neg_exp_simple"

    # Pure power laws (always positive, monotone, no oscillation)
    if "kepler" in name or "stefan" in name or "kinetic" in name:
        return "power_law"

    # Reciprocal / rational laws
    if "wien" in name or "gravity" in name or "newton" in name:
        return "rational"

    # Lorentz: composite involving sqrt(1-x²)
    if "lorentz" in name:
        return "composite_decay"

    # Entropy: -x·ln(x) — involves product
    if "entropy" in name:
        return "neg_exp_simple"

    # Fallback: check if monotone decreasing (likely decay law)
    if monotone_dec and all_positive:
        return "neg_exp_simple"

    return "other"


def _safe(fn: Callable, x: float) -> bool:
    try:
        v = fn(x)
        return math.isfinite(v)
    except Exception:
        return False


# ── Coverage table ─────────────────────────────────────────────────────────────

def coverage_table(
    laws: list[dict],
    eml_results: list[dict],
    deml_results: list[dict],
    combined_results: list[dict],
) -> str:
    """Return a Markdown coverage table with barrier classification column.

    Args:
        laws:             FUNCTIONAL_LAWS list.
        eml_results:      Per-law dicts from run_deml_census (EML config).
        deml_results:     Per-law dicts from run_deml_census (DEML config).
        combined_results: Per-law dicts for combined EML+DEML.

    Returns:
        GitHub-Flavored Markdown table string.
    """
    header = (
        "| # | Law | Category | EML | DEML | Combined | Barrier type |\n"
        "|---|-----|----------|-----|------|----------|--------------|\n"
    )
    rows = []
    for i, (law, er, dr, cr) in enumerate(
        zip(laws, eml_results, deml_results, combined_results), 1
    ):
        name     = law.get("name", "?")
        cat      = law.get("category", "?")
        e_tag    = "✓" if er.get("native") else f"{er.get('mse', 9.99):.3f}"
        d_tag    = "✓" if dr.get("native") else f"{dr.get('mse', 9.99):.3f}"
        c_tag    = "**✓**" if cr.get("native") else "✗"
        barrier  = classify_barrier(law, er.get("native", False), dr.get("native", False))
        b_short  = BARRIER_TYPES.get(barrier, barrier).split("—")[0].strip()
        rows.append(f"| {i} | {name} | {cat} | {e_tag} | {d_tag} | {c_tag} | {b_short} |")

    n_eml  = sum(1 for r in eml_results  if r.get("native"))
    n_deml = sum(1 for r in deml_results if r.get("native"))
    n_comb = sum(1 for r in combined_results if r.get("native"))
    n_tot  = len(laws)

    summary = (
        f"\n**Coverage: EML {n_eml}/{n_tot} | DEML {n_deml}/{n_tot} | "
        f"EML+DEML {n_comb}/{n_tot}**"
    )
    return header + "\n".join(rows) + "\n" + summary


# ── Heatmap visualisation ─────────────────────────────────────────────────────

def plot_coverage_heatmap(
    laws: list[dict],
    eml_results: list[dict],
    deml_results: list[dict],
    combined_results: list[dict],
) -> "Any":
    """Return a 15×3 coverage heatmap Figure (EML / DEML / combined).

    Green = native (MSE < threshold), red = blocked, orange = partial.
    """
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np

    n = len(laws)
    grid = np.zeros((n, 3))  # columns: EML, DEML, combined

    for i, (er, dr, cr) in enumerate(zip(eml_results, deml_results, combined_results)):
        e_mse = er.get("mse", 10.0)
        d_mse = dr.get("mse", 10.0)
        grid[i, 0] = _mse_to_score(e_mse)
        grid[i, 1] = _mse_to_score(d_mse)
        grid[i, 2] = _mse_to_score(min(e_mse, d_mse))

    names = [law.get("name", "?")[:30] for law in laws]
    cols  = ["EML", "DEML", "EML+DEML"]

    cmap  = mcolors.LinearSegmentedColormap.from_list(
        "coverage", ["#C44E52", "#f0a500", "#55A868"], N=256
    )

    fig, ax = plt.subplots(figsize=(7, 9))
    im = ax.imshow(grid, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(3))
    ax.set_xticklabels(cols, fontsize=11, fontweight="bold")
    ax.set_yticks(range(n))
    ax.set_yticklabels(names, fontsize=8)
    ax.set_title("Physics Law Coverage Heatmap\n(green = native, red = blocked)", fontsize=11)

    for i in range(n):
        for j in range(3):
            val = grid[i, j]
            label = "✓" if val > 0.9 else (f"{val:.1f}" if val > 0.1 else "✗")
            ax.text(j, i, label, ha="center", va="center",
                    fontsize=9, color="white" if val < 0.7 else "black")

    plt.colorbar(im, ax=ax, label="Coverage score (1=native, 0=blocked)")
    fig.tight_layout()
    return fig


def _mse_to_score(mse: float) -> float:
    """Convert MSE to a [0,1] coverage score. 1=native, 0=blocked."""
    if not math.isfinite(mse) or mse >= 1.0:
        return 0.0
    if mse < 1e-6:
        return 1.0
    return max(0.0, 1.0 - math.log10(mse) / -6.0)  # log scale 1e-6→1, 1→0


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cli() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Coverage analysis for DEML census")
    parser.add_argument("--census-file", type=str, default=None,
                        help="Path to deml_census_full.json (runs census if absent)")
    parser.add_argument("--plot", action="store_true", help="Show coverage heatmap")
    parser.add_argument("--save-plot", type=str, default=None,
                        help="Save heatmap to this path")
    args = parser.parse_args()

    from monogate.frontiers.law_complexity import FUNCTIONAL_LAWS

    if args.census_file and Path(args.census_file).exists():
        with open(args.census_file, encoding="utf-8") as fh:
            data = json.load(fh)
        eml_r  = data["eml_results"]
        deml_r = data["deml_results"]
        comb_r = data["combined_results"]
    else:
        print("No census file found — running quick census (n=500)…")
        from monogate.frontiers.deml_census import run_deml_census
        results = run_deml_census(n_simulations=500, depth=2, verbose=True)
        eml_r   = results["eml_results"]
        deml_r  = results["deml_results"]
        comb_r  = results["combined_results"]

    table = coverage_table(FUNCTIONAL_LAWS, eml_r, deml_r, comb_r)
    print("\n" + table)

    if args.plot or args.save_plot:
        fig = plot_coverage_heatmap(FUNCTIONAL_LAWS, eml_r, deml_r, comb_r)
        if args.save_plot:
            fig.savefig(args.save_plot, dpi=150, bbox_inches="tight")
            print(f"Saved: {args.save_plot}")
        if args.plot:
            import matplotlib.pyplot as plt
            plt.show()


if __name__ == "__main__":
    _cli()
