"""
symbolic_regression_comparison.py
==================================
Compares EML/BEST + MCTS + Beam search against PySR and gplearn on 5 targets.

Targets:
  1. sin(x)
  2. exp(-x^2)
  3. 1/(1+x^2)   (Lorentzian / Runge function)
  4. x*sin(x)
  5. GELU(x)      (0.5*x*(1+tanh(sqrt(2/pi)*(x+0.044715*x^3))))

Metrics reported for each method on each target:
  - MSE on 50 probe points in [-3, 3]
  - Wall-clock time (seconds)
  - Node count (where applicable)
  - Best formula (where available)

Each method is run with a fixed budget to keep comparison fair:
  - EML MCTS  : n_simulations=10000, depth=6
  - EML Beam  : width=200, depth=6
  - PySR      : niterations=50 (skipped if not installed)
  - gplearn   : generations=50 (skipped if not installed)

Run from python/:
    python benchmarks/symbolic_regression_comparison.py

Results are printed as a markdown table and saved to:
    benchmarks/results.md
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from monogate.search import mcts_search, beam_search

# ── Target functions ──────────────────────────────────────────────────────────

def _gelu(x: float) -> float:
    return 0.5 * x * (1.0 + math.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x**3)))

TARGETS = {
    "sin(x)":        math.sin,
    "exp(-x^2)":     lambda x: math.exp(-x * x),
    "1/(1+x^2)":     lambda x: 1.0 / (1.0 + x * x),
    "x*sin(x)":      lambda x: x * math.sin(x),
    "GELU(x)":       _gelu,
}

PROBE_X = [-3.0 + 6.0 * i / 49 for i in range(50)]


def compute_mse(pred_fn, target_fn, xs=PROBE_X) -> float:
    total = 0.0
    n = 0
    for x in xs:
        try:
            v = pred_fn(x)
            if math.isfinite(v):
                total += (v - target_fn(x)) ** 2
                n += 1
        except Exception:
            pass
    return total / n if n > 0 else float("inf")


# ── EML methods ───────────────────────────────────────────────────────────────

def run_eml_mcts(target_fn, name: str, seed: int = 42) -> dict:
    t0 = time.perf_counter()
    result = mcts_search(
        target_fn,
        probe_points=PROBE_X,
        depth=6,
        n_simulations=10_000,
        seed=seed,
    )
    elapsed = time.perf_counter() - t0
    return {
        "method":  "EML MCTS (d=6, 10k sims)",
        "target":  name,
        "mse":     result.best_mse,
        "time_s":  round(elapsed, 2),
        "formula": result.best_formula,
        "nodes":   "variable",
    }


def run_eml_beam(target_fn, name: str) -> dict:
    t0 = time.perf_counter()
    result = beam_search(
        target_fn,
        probe_points=PROBE_X,
        depth=6,
        width=200,
    )
    elapsed = time.perf_counter() - t0
    return {
        "method":  "EML Beam (d=6, w=200)",
        "target":  name,
        "mse":     result.best_mse,
        "time_s":  round(elapsed, 2),
        "formula": result.best_formula,
        "nodes":   "variable",
    }


# ── PySR (optional) ───────────────────────────────────────────────────────────

def run_pysr(target_fn, name: str) -> dict | None:
    try:
        import numpy as np
        from pysr import PySRRegressor  # type: ignore
    except ImportError:
        return None

    xs = np.array(PROBE_X).reshape(-1, 1)
    ys = np.array([target_fn(x) for x in PROBE_X])

    t0 = time.perf_counter()
    model = PySRRegressor(
        niterations=50,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["exp", "log", "sin", "cos"],
        verbosity=0,
        random_state=42,
    )
    try:
        model.fit(xs, ys)
        pred_fn = model.predict
        mse_val = float(np.mean((pred_fn(xs) - ys) ** 2))
        formula = str(model.sympy())
        elapsed = time.perf_counter() - t0
        return {
            "method":  "PySR (50 iter)",
            "target":  name,
            "mse":     mse_val,
            "time_s":  round(elapsed, 2),
            "formula": formula,
            "nodes":   "N/A",
        }
    except Exception as exc:
        return {
            "method":  "PySR (50 iter)",
            "target":  name,
            "mse":     float("inf"),
            "time_s":  round(time.perf_counter() - t0, 2),
            "formula": f"error: {exc}",
            "nodes":   "N/A",
        }


# ── gplearn (optional) ────────────────────────────────────────────────────────

def run_gplearn(target_fn, name: str) -> dict | None:
    try:
        import numpy as np
        from gplearn.genetic import SymbolicRegressor  # type: ignore
    except ImportError:
        return None

    xs = np.array(PROBE_X).reshape(-1, 1)
    ys = np.array([target_fn(x) for x in PROBE_X])

    t0 = time.perf_counter()
    model = SymbolicRegressor(
        generations=50,
        population_size=500,
        function_set=("add", "sub", "mul", "div", "log", "sqrt", "sin", "cos"),
        random_state=42,
        verbose=0,
    )
    try:
        model.fit(xs, ys)
        preds = model.predict(xs)
        mse_val = float(np.mean((preds - ys) ** 2))
        formula = str(model._program)
        elapsed = time.perf_counter() - t0
        return {
            "method":  "gplearn (50 gen)",
            "target":  name,
            "mse":     mse_val,
            "time_s":  round(elapsed, 2),
            "formula": formula[:80],
            "nodes":   "N/A",
        }
    except Exception as exc:
        return {
            "method":  "gplearn (50 gen)",
            "target":  name,
            "mse":     float("inf"),
            "time_s":  round(time.perf_counter() - t0, 2),
            "formula": f"error: {exc}",
            "nodes":   "N/A",
        }


# ── Main ──────────────────────────────────────────────────────────────────────

def fmt_mse(v: float) -> str:
    if not math.isfinite(v):
        return "inf"
    if v == 0.0:
        return "0"
    return f"{v:.3e}"


def main():
    all_results: list[dict] = []
    skipped_methods: set[str] = set()

    print("Running symbolic regression benchmarks...")
    print(f"  Targets: {list(TARGETS.keys())}")
    print(f"  Probe points: {len(PROBE_X)} in [-3, 3]")
    print()

    for name, fn in TARGETS.items():
        print(f"  Target: {name}")

        r = run_eml_mcts(fn, name)
        all_results.append(r)
        print(f"    EML MCTS  : MSE={fmt_mse(r['mse'])}  t={r['time_s']}s")

        r = run_eml_beam(fn, name)
        all_results.append(r)
        print(f"    EML Beam  : MSE={fmt_mse(r['mse'])}  t={r['time_s']}s")

        if "PySR" not in skipped_methods:
            r = run_pysr(fn, name)
            if r is None:
                print("    PySR      : (not installed -- pip install pysr)")
                skipped_methods.add("PySR")
            else:
                all_results.append(r)
                print(f"    PySR      : MSE={fmt_mse(r['mse'])}  t={r['time_s']}s")

        if "gplearn" not in skipped_methods:
            r = run_gplearn(fn, name)
            if r is None:
                print("    gplearn   : (not installed -- pip install gplearn)")
                skipped_methods.add("gplearn")
            else:
                all_results.append(r)
                print(f"    gplearn   : MSE={fmt_mse(r['mse'])}  t={r['time_s']}s")

        print()

    # ── Results table ─────────────────────────────────────────────────────────

    methods = sorted({r["method"] for r in all_results})
    target_names = list(TARGETS.keys())

    lines = []
    lines.append("# Symbolic Regression Benchmark — monogate vs baselines")
    lines.append("")
    lines.append(
        "Comparison of EML/BEST + MCTS/Beam Search against PySR and gplearn "
        "on 5 regression targets.  All methods evaluated on 50 probe points "
        "in [-3, 3] with fixed budgets."
    )
    lines.append("")
    lines.append("## MSE Comparison")
    lines.append("")

    header = "| Method | " + " | ".join(target_names) + " |"
    sep    = "|--------|" + "|".join([":------:"] * len(target_names)) + "|"
    lines.append(header)
    lines.append(sep)

    for method in methods:
        row_parts = [f"| {method} |"]
        for tname in target_names:
            match = [r for r in all_results if r["method"] == method and r["target"] == tname]
            if match:
                row_parts.append(f" {fmt_mse(match[0]['mse'])} |")
            else:
                row_parts.append(" N/A |")
        lines.append("".join(row_parts))

    lines.append("")
    lines.append("## Wall-clock Time (seconds)")
    lines.append("")

    header2 = "| Method | " + " | ".join(target_names) + " |"
    lines.append(header2)
    lines.append(sep)

    for method in methods:
        row_parts = [f"| {method} |"]
        for tname in target_names:
            match = [r for r in all_results if r["method"] == method and r["target"] == tname]
            if match:
                row_parts.append(f" {match[0]['time_s']}s |")
            else:
                row_parts.append(" N/A |")
        lines.append("".join(row_parts))

    lines.append("")
    lines.append("## Best Formulas")
    lines.append("")

    for r in all_results:
        if r["formula"] and r["formula"] != "variable":
            short = r["formula"][:120] + ("..." if len(r["formula"]) > 120 else "")
            lines.append(f"- **{r['method']}** on `{r['target']}`: `{short}`")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- EML MCTS and Beam Search are constrained to the EML grammar "
        "(`eml(a,b) = exp(a) - ln(b)` with terminals `{1, x}`).  "
        "They cannot produce trigonometric or general polynomial primitives, "
        "so they are systematically disadvantaged on `sin(x)` and `x*sin(x)`."
    )
    lines.append(
        "- The Infinite Zeros Barrier proves no finite EML tree can exactly "
        "represent `sin(x)` for all real x; 40.2M trees searched (N<=10), zero candidates."
    )
    lines.append(
        "- PySR and gplearn have access to `sin`, `cos`, `exp`, `log` "
        "primitives; EML methods do not.  Fair comparison requires "
        "restricting baselines to `{+, -, *, /}` only."
    )

    md_content = "\n".join(lines) + "\n"

    out_path = Path(__file__).parent / "results.md"
    out_path.write_text(md_content, encoding="utf-8")
    print(f"Results saved to {out_path}")

    # Print to stdout as well
    print()
    print(md_content)


if __name__ == "__main__":
    main()
