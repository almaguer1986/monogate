"""
srbench_runner.py — SRBench benchmark runner for EMLRegressor
=============================================================
Runs EMLRegressor on the Nguyen-1..12 and Keijzer-1..15 benchmark suites
and saves results to results/srbench_results.json.

Run from python/:
    python experiments/srbench_runner.py

Results are saved to python/results/srbench_results.json.

References:
  - Nguyen benchmarks: Uy et al. 2011
  - Keijzer benchmarks: Keijzer 2003
  - Vladislavleva benchmarks: Vladislavleva et al. 2009
"""

import sys, math, time, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from monogate.sklearn_wrapper import EMLRegressor

# ── Benchmark problem definitions ─────────────────────────────────────────────

def _unif(lo, hi, n, seed=0):
    return np.random.default_rng(seed).uniform(lo, hi, n)

NGUYEN = {
    "Nguyen-1":  (lambda x: x**3 + x**2 + x,             _unif(-1, 1, 100)),
    "Nguyen-2":  (lambda x: x**4 + x**3 + x**2 + x,       _unif(-1, 1, 100)),
    "Nguyen-3":  (lambda x: x**5 + x**4 + x**3 + x**2 + x, _unif(-1, 1, 100)),
    "Nguyen-4":  (lambda x: x**6 + x**5 + x**4 + x**3 + x**2 + x, _unif(-1, 1, 100)),
    "Nguyen-5":  (lambda x: math.sin(x**2)*math.cos(x) - 1,       None),  # vectorized below
    "Nguyen-6":  (lambda x: math.sin(x) + math.sin(x + x**2),    None),
    "Nguyen-7":  (lambda x: math.log(x + 1) + math.log(x**2 + 1), None),
    "Nguyen-8":  (lambda x: math.sqrt(x),                          _unif(0, 4, 100)),
    "Nguyen-9":  (lambda x: math.sin(x) + math.sin(2*x),          None),
    "Nguyen-10": (lambda x: 2*math.sin(x)*math.cos(x),             None),
    "Nguyen-11": (lambda x: x**x,                                  _unif(0, 1, 100)),
    "Nguyen-12": (lambda x: x**4 - x**3 + x**2/2 - x,             _unif(-1, 1, 100)),
}

KEIJZER = {
    "Keijzer-1":  (lambda x: 0.3 * x * math.sin(2 * math.pi * x),   _unif(-1, 1, 100)),
    "Keijzer-2":  (lambda x: 0.3 * x * math.sin(2 * math.pi * x),   _unif(-2, 2, 100)),
    "Keijzer-3":  (lambda x: 0.3 * x * math.sin(2 * math.pi * x),   _unif(-3, 3, 100)),
    "Keijzer-4":  (lambda x: x**3 * math.exp(-x) * math.cos(x) * math.sin(x) *
                              (math.sin(x)**2 * math.cos(x) - 1),    None),
    "Keijzer-5":  (lambda x: 30 * x * (x - 1) / ((x - 10) * x**2),  None),
    "Keijzer-6":  (lambda x: sum(1.0/i for i in range(1, int(x)+1)) if x >= 1 else 0.0,
                  np.arange(1, 51, dtype=float)),
    "Keijzer-7":  (lambda x: math.log(x),                             _unif(1, 100, 100)),
    "Keijzer-8":  (lambda x: math.sqrt(x),                            _unif(0, 100, 100)),
    "Keijzer-9":  (lambda x: math.log(x + math.sqrt(x**2 + 1)),       _unif(0, 100, 100)),
    "Keijzer-10": (lambda x: x**0.1,                                   _unif(0, 1, 100)),
    "Keijzer-11": (lambda x: x**4 - x**3 + x**2/2 - x,                _unif(-3, 3, 100)),
    "Keijzer-12": (lambda x: x**5 - x**4 + x**3/2 - x,                _unif(-3, 3, 100)),
    "Keijzer-13": (lambda x: 6 * math.sin(x) * math.cos(x),           None),
    "Keijzer-14": (lambda x: 8 / (2 + x**2 + 4),                      _unif(-3, 3, 100)),
    "Keijzer-15": (lambda x: (x**3/5 + x**2/2 - x - x/2),             _unif(-3, 3, 100)),
}


def _build_dataset(fn, xs_or_none):
    """Build (X, y) arrays for a benchmark problem."""
    if xs_or_none is None:
        xs = np.linspace(-3, 3, 100)
    else:
        xs = np.asarray(xs_or_none, dtype=float)

    ys = []
    good_xs = []
    for x in xs:
        try:
            y = fn(x)
            if math.isfinite(y):
                ys.append(y)
                good_xs.append(x)
        except (ValueError, ZeroDivisionError, OverflowError):
            pass
    return np.array(good_xs).reshape(-1, 1), np.array(ys)


def _r2(y_true, y_pred):
    """Compute R² score, handling NaN predictions."""
    mask = np.isfinite(y_pred)
    if mask.sum() < 2:
        return float("nan")
    yt, yp = y_true[mask], y_pred[mask]
    ss_res = np.sum((yt - yp) ** 2)
    ss_tot = np.sum((yt - yt.mean()) ** 2)
    if ss_tot < 1e-12:
        return 1.0 if ss_res < 1e-12 else 0.0
    return float(1.0 - ss_res / ss_tot)


# ── Runner ────────────────────────────────────────────────────────────────────

def run_srbench(
    problems: dict,
    suite_name: str,
    max_depth: int = 5,
    n_simulations: int = 2000,
    seed: int = 0,
):
    results = []
    print(f"\n  {'Problem':<15} {'R²':>8} {'Formula':<35} {'ms':>6}")
    print(f"  {'-'*15} {'-'*8} {'-'*35} {'-'*6}")

    for name, (fn, xs) in problems.items():
        X, y = _build_dataset(fn, xs)
        if len(y) < 5:
            print(f"  {name:<15} {'SKIP (insufficient data)':>50}")
            continue

        reg = EMLRegressor(
            max_depth=max_depth,
            n_simulations=n_simulations,
            random_state=seed,
        )

        t0 = time.perf_counter()
        try:
            reg.fit(X, y)
            preds  = reg.predict(X)
            r2     = _r2(y, preds)
            formula = reg.get_formula()
            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            results.append({
                "suite":        suite_name,
                "problem":      name,
                "r2":           r2,
                "formula":      formula,
                "n_nodes":      formula.count("eml"),
                "elapsed_ms":   elapsed_ms,
                "n_train":      len(y),
                "best_score":   reg.best_score_,
            })

            formula_short = formula[:33] + ".." if len(formula) > 35 else formula
            r2_s = f"{r2:.4f}" if math.isfinite(r2) else "nan"
            print(f"  {name:<15} {r2_s:>8} {formula_short:<35} {elapsed_ms:>6}")

        except Exception as e:
            print(f"  {name:<15} {'ERROR: ' + str(e)[:50]:>60}")
            results.append({
                "suite": suite_name, "problem": name,
                "r2": float("nan"), "formula": "ERROR",
                "n_nodes": 0, "elapsed_ms": 0, "error": str(e),
            })

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("  SRBench Runner — EMLRegressor")
    print("=" * 70)
    print(f"  max_depth=5, n_simulations=2000, seed=0")

    all_results = []

    print("\n  === Nguyen Benchmarks ===")
    all_results += run_srbench(NGUYEN, "Nguyen", max_depth=5, n_simulations=2000)

    print("\n  === Keijzer Benchmarks ===")
    all_results += run_srbench(KEIJZER, "Keijzer", max_depth=5, n_simulations=2000)

    # Save results
    out_path = "results/srbench_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Results saved to {out_path}")

    # Summary
    valid = [r for r in all_results if math.isfinite(r.get("r2", float("nan")))]
    r2_vals = [r["r2"] for r in valid]
    if r2_vals:
        print(f"\n  Summary:")
        print(f"    Problems run:  {len(all_results)}")
        print(f"    R² ≥ 0.9:      {sum(1 for v in r2_vals if v >= 0.9)}/{len(valid)}")
        print(f"    R² ≥ 0.5:      {sum(1 for v in r2_vals if v >= 0.5)}/{len(valid)}")
        print(f"    Mean R²:       {sum(r2_vals)/len(r2_vals):.4f}")
