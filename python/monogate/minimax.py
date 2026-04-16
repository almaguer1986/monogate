"""
monogate.minimax — Minimax (Chebyshev / L∞) EML approximation.

Finds the EML tree with the smallest *maximum* absolute error on a domain,
using MCTS with the ``'minimax'`` objective (already built into mcts_search).

This is a thin wrapper that:
  1. Sets up sensible probe points covering the domain.
  2. Calls ``mcts_search(..., objective='minimax')``.
  3. Returns a :class:`MinimaxResult` with both L∞ and L² metrics.

Usage::

    from monogate.minimax import minimax_eml
    import math

    result = minimax_eml(math.sin, n_nodes=7, domain=(-3.14, 3.14))
    print(result.best_formula)         # EML expression
    print(f"L∞ error: {result.linf:.4e}")
    print(f"L² error: {result.l2:.4e}")

Survey usage (multiple node budgets)::

    from monogate.minimax import minimax_survey
    import math, json

    rows = minimax_survey(math.sin, node_counts=[1, 3, 5, 7, 9, 11],
                          domain=(-3.14, 3.14), n_simulations=2000)
    print(json.dumps(rows, indent=2))
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Callable, Any

from .search.mcts import mcts_search, MCTSResult, _eval_tree, _is_complete, INF

__all__ = [
    "MinimaxResult",
    "minimax_eml",
    "minimax_survey",
]


@dataclass
class MinimaxResult:
    """Result from :func:`minimax_eml`.

    Attributes
    ----------
    best_tree      EML tree dict (can be passed to ``to_sympy``).
    best_formula   Human-readable EML expression string.
    linf           Achieved L∞ (maximum absolute) error on probe points.
    l2             Achieved L² (RMS) error on the same probe points.
    n_nodes        Number of internal (eml) nodes in the tree.
    domain         (lo, hi) domain used for the approximation.
    n_probe        Number of probe points used.
    elapsed_s      Wall-clock time.
    mcts_result    Underlying :class:`MCTSResult` for deeper inspection.
    """

    best_tree:    dict[str, Any]
    best_formula: str
    linf:         float
    l2:           float
    n_nodes:      int
    domain:       tuple[float, float]
    n_probe:      int
    elapsed_s:    float
    mcts_result:  MCTSResult = field(repr=False)

    def __repr__(self) -> str:
        return (
            f"MinimaxResult(formula={self.best_formula!r}, "
            f"L∞={self.linf:.4e}, L²={self.l2:.4e}, "
            f"nodes={self.n_nodes})"
        )


def minimax_eml(
    target_fn:     Callable[[float], float],
    n_nodes:       int = 7,
    domain:        tuple[float, float] = (-3.0, 3.0),
    n_probe:       int = 200,
    n_simulations: int = 5_000,
    seed:          int = 42,
    log_every:     int = 0,
    n_rollouts:    int = 1,
) -> MinimaxResult:
    """Find the EML tree with minimum L∞ error for *target_fn* on *domain*.

    Uses MCTS with the Chebyshev objective (``objective='minimax'``).  Probe
    points are equally spaced on the domain.  The ``n_nodes`` budget controls
    the maximum tree depth: depth ``d`` yields up to ``2^d − 1`` internal nodes,
    so ``n_nodes`` is rounded up to the next ``2^d − 1`` value.

    Args:
        target_fn:     Function to approximate.  Signature: ``(float) -> float``.
        n_nodes:       Maximum number of internal EML nodes.  Converted to depth.
        domain:        ``(lo, hi)`` interval for probe points.
        n_probe:       Number of equally-spaced probe points.
        n_simulations: MCTS simulation budget.
        seed:          Random seed.
        log_every:     Print MCTS progress every N simulations (0 = silent).
        n_rollouts:    Parallel rollouts per simulation (>1 for better exploration).

    Returns:
        :class:`MinimaxResult` with ``linf``, ``l2``, ``best_formula``, etc.

    Example::

        import math
        from monogate.minimax import minimax_eml

        r = minimax_eml(math.exp, n_nodes=5, domain=(0, 2), n_simulations=1000)
        print(r.best_formula, f"L∞={r.linf:.3e}")
    """
    lo, hi = domain
    probe_points = [lo + (hi - lo) * i / (n_probe - 1) for i in range(n_probe)]

    # Convert n_nodes to depth: depth d has at most 2**d - 1 internal nodes
    depth = max(1, math.ceil(math.log2(n_nodes + 1))) if n_nodes >= 1 else 1

    t0 = time.perf_counter()
    mcts_r = mcts_search(
        target_fn=target_fn,
        probe_points=probe_points,
        depth=depth,
        n_simulations=n_simulations,
        seed=seed,
        log_every=log_every,
        n_rollouts=n_rollouts,
        objective="minimax",
    )
    elapsed = time.perf_counter() - t0

    # Recompute L∞ and L² on the probe set
    probe_y = [target_fn(x) for x in probe_points]
    linf, l2_sum = 0.0, 0.0
    try:
        for xi, yi in zip(probe_points, probe_y):
            if _is_complete(mcts_r.best_tree):
                pred = _eval_tree(mcts_r.best_tree, xi)
                err  = abs(pred - yi)
                linf  = max(linf, err)
                l2_sum += err * err
    except (ValueError, OverflowError):
        linf  = INF
        l2_sum = INF
    l2 = math.sqrt(l2_sum / n_probe) if l2_sum < INF else INF

    # Count internal nodes
    def _count_nodes(node: dict) -> int:
        if node["op"] in ("leaf", "?"):
            return 0
        return 1 + _count_nodes(node["left"]) + _count_nodes(node["right"])

    actual_nodes = _count_nodes(mcts_r.best_tree)

    return MinimaxResult(
        best_tree=mcts_r.best_tree,
        best_formula=mcts_r.best_formula,
        linf=linf,
        l2=l2,
        n_nodes=actual_nodes,
        domain=domain,
        n_probe=n_probe,
        elapsed_s=elapsed,
        mcts_result=mcts_r,
    )


def minimax_survey(
    target_fn:     Callable[[float], float],
    node_counts:   list[int] | None = None,
    domain:        tuple[float, float] = (-3.0, 3.0),
    n_probe:       int = 200,
    n_simulations: int = 2_000,
    seed:          int = 42,
) -> list[dict[str, Any]]:
    """Run :func:`minimax_eml` for multiple node budgets and return a summary.

    Args:
        target_fn:     Function to approximate.
        node_counts:   List of ``n_nodes`` values to survey.
                       Default: ``[1, 3, 5, 7, 9, 11]``.
        domain:        ``(lo, hi)`` probe interval.
        n_probe:       Probe point count (shared across all budgets).
        n_simulations: MCTS simulation budget per budget level.
        seed:          Random seed (incremented per run for diversity).

    Returns:
        List of dicts, one per ``n_nodes`` value, suitable for ``json.dumps``.

    Example::

        import math, json
        from monogate.minimax import minimax_survey

        rows = minimax_survey(math.sin, node_counts=[1, 3, 5],
                              domain=(-3.14, 3.14), n_simulations=500)
        print(json.dumps(rows, indent=2))
    """
    if node_counts is None:
        node_counts = [1, 3, 5, 7, 9, 11]

    rows: list[dict[str, Any]] = []
    for i, nc in enumerate(node_counts):
        result = minimax_eml(
            target_fn=target_fn,
            n_nodes=nc,
            domain=domain,
            n_probe=n_probe,
            n_simulations=n_simulations,
            seed=seed + i * 97,
        )
        rows.append({
            "n_nodes":      nc,
            "depth":        max(1, math.ceil(math.log2(nc + 1))) if nc >= 1 else 1,
            "formula":      result.best_formula,
            "linf":         result.linf,
            "l2":           result.l2,
            "elapsed_s":    result.elapsed_s,
        })
    return rows
