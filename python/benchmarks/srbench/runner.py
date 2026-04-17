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


def _eval_formula(formula_fn, X: np.ndarray) -> np.ndarray | None:
    """Evaluate a formula callable over X; return None if it diverges."""
    try:
        y = formula_fn(X)
        if not np.all(np.isfinite(y)):
            return None
        return y
    except Exception:
        return None


def run_mcts_benchmark(
    fn: BenchmarkFn,
    n_simulations: int = 3000,
    depth: int = 4,
    n_train: int = 20,
    n_test: int = 100,
) -> BenchmarkResult:
    """Run monogate MCTS symbolic regression on a benchmark function."""
    from monogate import mcts_search

    X_tr, y_tr = fn.sample(n=n_train, seed=0)
    X_te, y_te = fn.test_sample(n=n_test, seed=42)

    data = list(zip(X_tr.tolist(), y_tr.tolist()))

    t0 = time.time()
    try:
        result = mcts_search(data, n_simulations=n_simulations, max_depth=depth)
        elapsed = time.time() - t0

        best_formula = str(result.formula) if hasattr(result, "formula") else str(result)
        best_mse = float(result.mse) if hasattr(result, "mse") else math.nan

        # Evaluate formula on train and test
        try:
            formula_fn = result.to_callable() if hasattr(result, "to_callable") else None
        except Exception:
            formula_fn = None

        if formula_fn is not None:
            y_pred_tr = _eval_formula(formula_fn, X_tr)
            y_pred_te = _eval_formula(formula_fn, X_te)
            train_r2 = _r2(y_tr, y_pred_tr) if y_pred_tr is not None else -999.0
            test_r2 = _r2(y_te, y_pred_te) if y_pred_te is not None else -999.0
            n_nodes = result.n_nodes if hasattr(result, "n_nodes") else -1
        else:
            train_r2 = test_r2 = -999.0
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
    n_train: int = 20,
    n_test: int = 100,
) -> BenchmarkResult:
    """Run monogate beam search on a benchmark function."""
    from monogate import beam_search

    X_tr, y_tr = fn.sample(n=n_train, seed=0)
    X_te, y_te = fn.test_sample(n=n_test, seed=42)

    data = list(zip(X_tr.tolist(), y_tr.tolist()))

    t0 = time.time()
    try:
        result = beam_search(data, width=width, max_depth=depth)
        elapsed = time.time() - t0

        best_formula = str(result.formula) if hasattr(result, "formula") else str(result)
        best_mse = float(result.mse) if hasattr(result, "mse") else math.nan

        try:
            formula_fn = result.to_callable() if hasattr(result, "to_callable") else None
        except Exception:
            formula_fn = None

        if formula_fn is not None:
            y_pred_tr = _eval_formula(formula_fn, X_tr)
            y_pred_te = _eval_formula(formula_fn, X_te)
            train_r2 = _r2(y_tr, y_pred_tr) if y_pred_tr is not None else -999.0
            test_r2 = _r2(y_te, y_pred_te) if y_pred_te is not None else -999.0
            n_nodes = result.n_nodes if hasattr(result, "n_nodes") else -1
        else:
            train_r2 = test_r2 = -999.0
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
    use_beam: bool = True,
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
