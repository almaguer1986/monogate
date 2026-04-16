"""
monogate.leaderboard — Symbolic regression benchmark over Nguyen/Keijzer problems.

Runs MCTS and/or beam search on a standard suite of symbolic regression targets,
scores results by EML node count, and produces a leaderboard table.

Public API
----------
PROBLEMS : dict[str, BenchmarkProblem]   — all registered problems
run_leaderboard(...)  -> list[LeaderboardEntry]
print_leaderboard(entries)
markdown_leaderboard(entries) -> str
save_leaderboard(entries, path)
load_leaderboard(path) -> list[LeaderboardEntry]
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np


# ── Data types ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BenchmarkProblem:
    """A single symbolic regression benchmark problem."""

    name: str
    target_fn: Callable[[float], float]
    domain: tuple[float, float]
    mse_threshold: float
    reference_formula: str | None = None  # known closed form, or None


@dataclass(frozen=True)
class LeaderboardEntry:
    """Result of running one search method on one problem."""

    problem: str
    formula: str
    n_nodes: int
    best_mse: float
    solved: bool        # best_mse < threshold
    method: str         # 'mcts' | 'beam' | 'manual'
    elapsed_s: float


# ── Problem definitions ───────────────────────────────────────────────────────

def _safe(fn: Callable[[float], float]) -> Callable[[float], float]:
    """Wrap fn to return NaN on domain errors (log of negative, etc.)."""
    def wrapper(x: float) -> float:
        try:
            v = fn(x)
            return v if math.isfinite(v) else float("nan")
        except (ValueError, ZeroDivisionError, OverflowError):
            return float("nan")
    return wrapper


PROBLEMS: dict[str, BenchmarkProblem] = {
    "nguyen-1": BenchmarkProblem(
        name="nguyen-1",
        target_fn=_safe(lambda x: x**3 + x**2 + x),
        domain=(-1.0, 1.0),
        mse_threshold=1e-4,
        reference_formula="x^3 + x^2 + x",
    ),
    "nguyen-2": BenchmarkProblem(
        name="nguyen-2",
        target_fn=_safe(lambda x: x**4 + x**3 + x**2 + x),
        domain=(-1.0, 1.0),
        mse_threshold=1e-4,
        reference_formula="x^4 + x^3 + x^2 + x",
    ),
    "nguyen-3": BenchmarkProblem(
        name="nguyen-3",
        target_fn=_safe(lambda x: x**5 + x**4 + x**3 + x**2 + x),
        domain=(-1.0, 1.0),
        mse_threshold=1e-4,
        reference_formula="x^5 + x^4 + x^3 + x^2 + x",
    ),
    "nguyen-4": BenchmarkProblem(
        name="nguyen-4",
        target_fn=_safe(lambda x: x**6 + x**5 + x**4 + x**3 + x**2 + x),
        domain=(-1.0, 1.0),
        mse_threshold=1e-4,
        reference_formula="x^6 + x^5 + ... + x",
    ),
    "nguyen-5": BenchmarkProblem(
        name="nguyen-5",
        target_fn=_safe(lambda x: math.sin(x**2) * math.cos(x) - 1.0),
        domain=(0.0, math.pi),
        mse_threshold=1e-3,
        reference_formula="sin(x^2)*cos(x) - 1",
    ),
    "nguyen-6": BenchmarkProblem(
        name="nguyen-6",
        target_fn=_safe(lambda x: math.sin(x) + math.sin(x + x**2)),
        domain=(-1.0, 1.0),
        mse_threshold=1e-3,
        reference_formula="sin(x) + sin(x + x^2)",
    ),
    "nguyen-7": BenchmarkProblem(
        name="nguyen-7",
        target_fn=_safe(lambda x: math.log(x + 1.0) + math.log(x**2 + 1.0)),
        domain=(0.0, 2.0),
        mse_threshold=1e-4,
        reference_formula="ln(x+1) + ln(x^2+1)",
    ),
    "nguyen-8": BenchmarkProblem(
        name="nguyen-8",
        target_fn=_safe(lambda x: math.sqrt(x)),
        domain=(0.0, 4.0),
        mse_threshold=1e-4,
        reference_formula="sqrt(x)",
    ),
    "keijzer-6": BenchmarkProblem(
        name="keijzer-6",
        target_fn=_safe(lambda x: sum(1.0 / i for i in range(1, max(1, int(x)) + 1))),
        domain=(1.0, 50.0),
        mse_threshold=1e-2,
        reference_formula="sum(1/i, i=1..floor(x))",
    ),
    "keijzer-11": BenchmarkProblem(
        name="keijzer-11",
        target_fn=_safe(lambda x: x * math.log(x)),
        domain=(1.0, 10.0),
        mse_threshold=1e-3,
        reference_formula="x * ln(x)",
    ),
}


# ── Node count helper ─────────────────────────────────────────────────────────


def _count_nodes(tree: dict) -> int:
    """Count internal eml nodes in a tree dict (leaves count as 0)."""
    if tree.get("op") == "eml":
        return 1 + _count_nodes(tree["left"]) + _count_nodes(tree["right"])
    return 0


# ── Probe point generator ─────────────────────────────────────────────────────


def _probe_points(problem: BenchmarkProblem, n: int = 40) -> list[float]:
    lo, hi = problem.domain
    eps = (hi - lo) * 0.01
    return np.linspace(lo + eps, hi - eps, n).tolist()


# ── Core runner ───────────────────────────────────────────────────────────────


def _run_one(
    problem: BenchmarkProblem,
    method: str,
    n_simulations: int,
    depth: int,
    seed: int,
) -> LeaderboardEntry:
    from monogate.search.mcts import mcts_search, beam_search

    pts = _probe_points(problem)
    t0 = time.perf_counter()

    if method == "mcts":
        result = mcts_search(
            target_fn=problem.target_fn,
            probe_points=pts,
            depth=depth,
            n_simulations=n_simulations,
            seed=seed,
        )
        formula = result.best_formula
        mse = result.best_mse
        tree = result.best_tree
    elif method == "beam":
        # beam_search uses 'width' (beam width) rather than n_simulations;
        # map n_simulations → width so callers use a uniform interface.
        result = beam_search(
            target_fn=problem.target_fn,
            probe_points=pts,
            depth=depth,
            width=n_simulations,
        )
        formula = result.best_formula
        mse = result.best_mse
        tree = result.best_tree
    else:
        raise ValueError(f"Unknown method: {method!r}. Use 'mcts' or 'beam'.")

    elapsed = time.perf_counter() - t0
    n_nodes = _count_nodes(tree)

    return LeaderboardEntry(
        problem=problem.name,
        formula=formula,
        n_nodes=n_nodes,
        best_mse=mse,
        solved=mse < problem.mse_threshold,
        method=method,
        elapsed_s=elapsed,
    )


# ── Public API ────────────────────────────────────────────────────────────────


def run_leaderboard(
    problems: list[str] | None = None,
    n_simulations: int = 2000,
    depth: int = 5,
    methods: list[str] | None = None,
    save_path: str | None = None,
    seed: int = 42,
) -> list[LeaderboardEntry]:
    """Run the symbolic regression benchmark.

    Args:
        problems:      Problem names to run (None = all registered problems).
        n_simulations: MCTS/beam simulations per problem.
        depth:         Maximum EML tree depth.
        methods:       Search methods to use (default: ['mcts', 'beam']).
        save_path:     If given, save results as JSON to this path.
        seed:          Random seed for reproducibility.

    Returns:
        List of LeaderboardEntry — one per (problem, method) pair.
    """
    if methods is None:
        methods = ["mcts", "beam"]

    problem_names = problems if problems is not None else list(PROBLEMS.keys())
    entries: list[LeaderboardEntry] = []

    for name in problem_names:
        if name not in PROBLEMS:
            raise ValueError(f"Unknown problem: {name!r}. Available: {list(PROBLEMS)}")
        prob = PROBLEMS[name]
        for method in methods:
            entry = _run_one(prob, method, n_simulations, depth, seed)
            entries.append(entry)

    if save_path:
        save_leaderboard(entries, save_path)

    return entries


def print_leaderboard(entries: list[LeaderboardEntry]) -> None:
    """Print a leaderboard table to stdout."""
    print(markdown_leaderboard(entries))


def markdown_leaderboard(entries: list[LeaderboardEntry]) -> str:
    """Return the leaderboard as a GitHub-flavoured Markdown table."""
    header = (
        "| Problem | Method | Nodes | MSE | Solved | Formula | Time (s) |\n"
        "|---------|--------|------:|----:|:------:|---------|--------:|"
    )
    rows = []
    for e in entries:
        solved = "✓" if e.solved else "✗"
        rows.append(
            f"| {e.problem} | {e.method} | {e.n_nodes} "
            f"| {e.best_mse:.3e} | {solved} "
            f"| `{e.formula[:40]}` | {e.elapsed_s:.1f} |"
        )
    return header + "\n" + "\n".join(rows)


def save_leaderboard(entries: list[LeaderboardEntry], path: str) -> None:
    """Save leaderboard entries to a JSON file."""
    data = [
        {
            "problem": e.problem,
            "formula": e.formula,
            "n_nodes": e.n_nodes,
            "best_mse": e.best_mse,
            "solved": e.solved,
            "method": e.method,
            "elapsed_s": e.elapsed_s,
        }
        for e in entries
    ]
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def load_leaderboard(path: str) -> list[LeaderboardEntry]:
    """Load leaderboard entries from a JSON file."""
    with open(path) as fh:
        data = json.load(fh)
    return [
        LeaderboardEntry(
            problem=d["problem"],
            formula=d["formula"],
            n_nodes=d["n_nodes"],
            best_mse=d["best_mse"],
            solved=d["solved"],
            method=d["method"],
            elapsed_s=d["elapsed_s"],
        )
        for d in data
    ]
