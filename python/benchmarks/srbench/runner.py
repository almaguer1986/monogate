"""
SRBench runner: evaluate monogate MCTS and beam search on benchmark functions.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

from .functions import BenchmarkFn


@dataclass
class BenchmarkResult:
    fn_name: str
    suite: str
    best_formula: str
    train_r2: float
    test_r2: float
    best_mse: float
    n_nodes: int
    elapsed_s: float
    method: str
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "fn": self.fn_name,
            "suite": self.suite,
            "method": self.method,
            "formula": self.best_formula,
            "train_r2": round(self.train_r2, 4),
            "test_r2": round(self.test_r2, 4),
            "best_mse": self.best_mse,
            "n_nodes": self.n_nodes,
            "elapsed_s": round(self.elapsed_s, 2),
            "tags": self.tags,
        }


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot < 1e-15:
        return 1.0 if ss_res < 1e-15 else 0.0
    return float(1.0 - ss_res / ss_tot)


def _eval_tree(best_tree, X: np.ndarray) -> np.ndarray | None:
    """Evaluate an EML tree node over an array X."""
    from monogate.search.mcts import _eval_tree as _mcts_eval
    try:
        y = np.array([_mcts_eval(best_tree, x) for x in X], dtype=float)
        if not np.all(np.isfinite(y)):
            return None
        return y
    except Exception:
        return None


def _make_probe_points(fn: BenchmarkFn, n: int = 50, seed: int = 0) -> list[float]:
    rng = np.random.default_rng(seed)
    pts = rng.uniform(fn.domain[0] + 1e-6, fn.domain[1], size=n)
    return pts.tolist()


def run_mcts_benchmark(
    fn: BenchmarkFn,
    n_simulations: int = 3000,
    depth: int = 4,
    n_test: int = 100,
) -> BenchmarkResult:
    """Run monogate MCTS symbolic regression on a benchmark function."""
    from monogate.search.mcts import mcts_search

    probe_pts = _make_probe_points(fn, n=50, seed=0)
    X_te, y_te = fn.test_sample(n=n_test, seed=42)

    t0 = time.time()
    try:
        result = mcts_search(
            target_fn=fn.func,
            probe_points=probe_pts,
            depth=depth,
            n_simulations=n_simulations,
            seed=42,
        )
        elapsed = time.time() - t0

        best_formula = result.best_formula
        best_mse = float(result.best_mse) if math.isfinite(result.best_mse) else math.nan

        y_pred_te = _eval_tree(result.best_tree, X_te)
        y_pred_tr = _eval_tree(result.best_tree, np.array(probe_pts))
        y_tr = fn.func(np.array(probe_pts))

        train_r2 = _r2(y_tr, y_pred_tr) if y_pred_tr is not None else -999.0
        test_r2 = _r2(y_te, y_pred_te) if y_pred_te is not None else -999.0
        n_nodes = -1

    except Exception as exc:
        elapsed = time.time() - t0
        return BenchmarkResult(
            fn_name=fn.name,
            suite=fn.suite,
            best_formula=f"ERROR: {exc}",
            train_r2=-999.0,
            test_r2=-999.0,
            best_mse=math.nan,
            n_nodes=-1,
            elapsed_s=elapsed,
            method="mcts",
            tags=fn.tags,
        )

    return BenchmarkResult(
        fn_name=fn.name,
        suite=fn.suite,
        best_formula=best_formula,
        train_r2=train_r2,
        test_r2=test_r2,
        best_mse=best_mse,
        n_nodes=n_nodes,
        elapsed_s=elapsed,
        method="mcts",
        tags=fn.tags,
    )


def run_beam_benchmark(
    fn: BenchmarkFn,
    width: int = 50,
    depth: int = 4,
    n_test: int = 100,
) -> BenchmarkResult:
    """Run monogate beam search on a benchmark function."""
    from monogate.search.mcts import beam_search

    probe_pts = _make_probe_points(fn, n=50, seed=0)
    X_te, y_te = fn.test_sample(n=n_test, seed=42)

    t0 = time.time()
    try:
        result = beam_search(
            target_fn=fn.func,
            probe_points=probe_pts,
            depth=depth,
            width=width,
        )
        elapsed = time.time() - t0

        best_formula = result.best_formula
        best_mse = float(result.best_mse) if math.isfinite(result.best_mse) else math.nan

        y_pred_te = _eval_tree(result.best_tree, X_te)
        y_pred_tr = _eval_tree(result.best_tree, np.array(probe_pts))
        y_tr = fn.func(np.array(probe_pts))

        train_r2 = _r2(y_tr, y_pred_tr) if y_pred_tr is not None else -999.0
        test_r2 = _r2(y_te, y_pred_te) if y_pred_te is not None else -999.0
        n_nodes = -1

    except Exception as exc:
        elapsed = time.time() - t0
        return BenchmarkResult(
            fn_name=fn.name,
            suite=fn.suite,
            best_formula=f"ERROR: {exc}",
            train_r2=-999.0,
            test_r2=-999.0,
            best_mse=math.nan,
            n_nodes=-1,
            elapsed_s=elapsed,
            method="beam",
            tags=fn.tags,
        )

    return BenchmarkResult(
        fn_name=fn.name,
        suite=fn.suite,
        best_formula=best_formula,
        train_r2=train_r2,
        test_r2=test_r2,
        best_mse=best_mse,
        n_nodes=n_nodes,
        elapsed_s=elapsed,
        method="beam",
        tags=fn.tags,
    )


def run_suite(
    fns: list[BenchmarkFn],
    n_simulations: int = 3000,
    width: int = 50,
    depth: int = 4,
    use_beam: bool = False,
) -> list[BenchmarkResult]:
    """Run MCTS (and optionally beam) on a list of benchmark functions."""
    results = []
    for fn in fns:
        print(f"  {fn.name} ({fn.suite})...")
        mcts_res = run_mcts_benchmark(fn, n_simulations=n_simulations, depth=depth)
        results.append(mcts_res)
        print(f"    MCTS: R2_test={mcts_res.test_r2:.3f}  formula={mcts_res.best_formula[:60]}")

        if use_beam:
            beam_res = run_beam_benchmark(fn, width=width, depth=depth)
            results.append(beam_res)
            print(f"    Beam: R2_test={beam_res.test_r2:.3f}  formula={beam_res.best_formula[:60]}")

    return results
