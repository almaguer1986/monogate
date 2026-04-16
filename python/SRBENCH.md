# SRBench — EMLRegressor Symbolic Regression Leaderboard

> **monogate v0.12.0** · EMLRegressor (MCTS, max_depth=5, n_simulations=2000)
> Last updated: April 2026

---

## Overview

This document reports `EMLRegressor` results on the standard symbolic regression benchmark suites (Nguyen, Keijzer) and provides a comparison with published baselines.

`EMLRegressor` uses MCTS over the EML grammar to find compact, interpretable expression trees. Unlike neural network regressors, every result is a symbolic formula that can be simplified and verified.

---

## Running the Benchmark

```bash
cd python/
python experiments/srbench_runner.py
# Results saved to results/srbench_results.json
```

To update this document after a fresh run:

```bash
python scripts/update_srbench_leaderboard.py
```

---

## Nguyen Benchmarks (Uy et al. 2011)

| Problem | Target | EMLRegressor R² | Exact? |
|---------|--------|----------------|--------|
| Nguyen-1 | x³ + x² + x | — | — |
| Nguyen-2 | x⁴ + x³ + x² + x | — | — |
| Nguyen-3 | x⁵ + … + x | — | — |
| Nguyen-4 | x⁶ + … + x | — | — |
| Nguyen-5 | sin(x²)cos(x) − 1 | — | — |
| Nguyen-6 | sin(x) + sin(x+x²) | — | — |
| Nguyen-7 | ln(x+1) + ln(x²+1) | — | — |
| Nguyen-8 | √x | — | — |
| Nguyen-9 | sin(x) + sin(2x) | — | — |
| Nguyen-10 | 2sin(x)cos(x) | — | — |
| Nguyen-11 | xˣ | — | — |
| Nguyen-12 | x⁴ − x³ + x²/2 − x | — | — |

*Run `python experiments/srbench_runner.py` to populate this table.*

---

## Keijzer Benchmarks (Keijzer 2003)

| Problem | Target | EMLRegressor R² | Notes |
|---------|--------|----------------|-------|
| Keijzer-1 | 0.3x·sin(2πx) | — | — |
| Keijzer-2 | (wider domain) | — | — |
| Keijzer-3 | (widest domain) | — | — |
| Keijzer-6 | Σ(1/i, i=1..x) | — | — |
| Keijzer-7 | log(x) | — | — |
| Keijzer-8 | √x | — | — |
| Keijzer-9 | arcsinh(x) | — | — |
| Keijzer-10 | x^0.1 | — | — |
| Keijzer-11 | x⁴ − x³ + x²/2 − x | — | — |
| Keijzer-12 | x⁵ − x⁴ + x³/2 − x | — | — |
| Keijzer-13 | 6sin(x)cos(x) | — | — |

*Run `python experiments/srbench_runner.py` to populate this table.*

---

## Comparison with Baselines

The following table shows published results from the SRBench paper (La Cava et al. 2021) for reference:

| Method | Avg R² (Nguyen) | Exact recovery rate |
|--------|----------------|---------------------|
| gplearn | ~0.85 | ~40% |
| PySR | ~0.95 | ~70% |
| **EMLRegressor** (n=2000) | *run pending* | *run pending* |
| **EMLRegressor** (n=10000) | *run pending* | *run pending* |

*Note:* EMLRegressor uses a uniquely constrained search space (EML grammar only).
The comparison is informative rather than a strict apples-to-apples competition.

---

## Architecture Notes

`EMLRegressor` internally:
1. Extracts probe points from training data.
2. Builds an interpolant of (x, y) pairs.
3. Runs MCTS with that interpolant as the target function.
4. Returns the best EML tree found.

**Strengths:**
- Produces compact, interpretable formulas
- Guaranteed to return a symbolic expression
- Supports `objective='minimax'` for uniform error bounds
- sklearn-compatible: pipelines, cross-validation, etc.

**Limitations:**
- Univariate only (first feature column used)
- MCTS search quality scales with `n_simulations`
- Very complex targets may need `max_depth=6+` and `n_simulations=10000+`

---

## See Also

- `python/docs/guide/symbolic_regression.md` — user guide
- `python/monogate/sklearn_wrapper.py` — source code
- `python/experiments/srbench_runner.py` — benchmark runner
- `python/results/srbench_results.json` — raw results (after running)
