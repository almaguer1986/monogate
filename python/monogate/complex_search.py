"""
monogate.complex_search — Complex-domain MCTS and Beam Search.

Extends the standard EML grammar search to the complex terminal set
{1, x, ix, i}, enabling discovery of EML trees whose Im or Re projection
approximates a target function.

Key identity motivating this module:
    Im(eml(ix, 1)) = sin(x)   — exact, 1 node
    Re(eml(ix, 1)) = cos(x)   — exact, 1 node

Deeper complex trees can approximate Bessel J₀, Airy Ai, erf, and other
functions that require complex intermediates.

Public API
----------
complex_mcts_search(target_fn, projection, **kwargs) -> ComplexMCTSResult
    MCTS over the complex EML grammar; scores by Im(tree) or Re(tree) vs target.

complex_beam_search(target_fn, projection, **kwargs) -> ComplexBeamResult
    Beam Search over the complex grammar.

ComplexMCTSResult
    MCTSResult subclass with extra fields: projection, complex_formula.
ComplexBeamResult
    BeamResult subclass with extra fields: projection, complex_formula.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .complex_eval import (
    COMPLEX_TERMINALS,
    eval_complex,
    formula_complex,
    score_complex_projection,
)
from .search.mcts import (
    MCTSResult,
    BeamResult,
    _MCTSNode,
    _copy,
    _depth,
    _eml,
    _expand_options,
    _first_placeholder_path,
    _is_complete,
    _leaf,
    _placeholder,
    _random_complete,
    _set_at_path,
)

INF = float("inf")
Node = dict[str, Any]


# ── Override _TERMINALS inside the complex grammar ────────────────────────────

_COMPLEX_LEAF_VALS = COMPLEX_TERMINALS  # [1.0, "x", "ix", "i"]


def _c_leaf(val: Any) -> Node:
    return {"op": "leaf", "val": val}


def _c_expand_options(node: Node, max_depth: int) -> list[Node]:
    """Like mcts._expand_options but with COMPLEX_TERMINALS."""
    path = _first_placeholder_path(node)
    if path is None:
        return []
    options: list[Node] = []
    for t in _COMPLEX_LEAF_VALS:
        options.append(_set_at_path(node, path, _c_leaf(t)))
    if _depth(node) + 1 < max_depth:
        options.append(_set_at_path(node, path, _eml(_placeholder(), _placeholder())))
    return options


def _c_random_complete(partial: Node, depth_budget: int, rng: random.Random) -> Node:
    """Randomly complete placeholders using complex terminals."""
    node = _copy(partial)
    for _ in range(300):
        path = _first_placeholder_path(node)
        if path is None:
            break
        if _depth(node) >= depth_budget - 1:
            replacement = _c_leaf(rng.choice(_COMPLEX_LEAF_VALS))
        else:
            replacement = (
                _c_leaf(rng.choice(_COMPLEX_LEAF_VALS))
                if rng.random() < 0.6
                else _eml(_placeholder(), _placeholder())
            )
        node = _set_at_path(node, path, replacement)
    for _ in range(200):
        path = _first_placeholder_path(node)
        if path is None:
            break
        node = _set_at_path(node, path, _c_leaf(rng.choice(_COMPLEX_LEAF_VALS)))
    return node


def _c_score(
    node: Node,
    probe_x: list[float],
    probe_y: list[float],
    projection: str,
) -> float:
    """MSE of Im/Re(tree(x)) against targets.  Returns INF on error."""
    return score_complex_projection(node, probe_x, probe_y, projection)


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class ComplexMCTSResult:
    """Result returned by complex_mcts_search()."""
    best_tree:      Node
    best_mse:       float
    best_formula:   str
    n_simulations:  int
    elapsed_s:      float
    projection:     str                            # 'imag' or 'real'
    complex_formula: str                           # formula_complex rendering
    history:        list[tuple[int, float]] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"ComplexMCTSResult(mse={self.best_mse:.4e}, "
            f"projection={self.projection!r}, "
            f"formula={self.complex_formula!r}, "
            f"elapsed={self.elapsed_s:.2f}s)"
        )


@dataclass
class ComplexBeamResult:
    """Result returned by complex_beam_search()."""
    best_tree:      Node
    best_mse:       float
    best_formula:   str
    n_levels:       int
    elapsed_s:      float
    projection:     str
    complex_formula: str
    history:        list[tuple[int, float]] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"ComplexBeamResult(mse={self.best_mse:.4e}, "
            f"projection={self.projection!r}, "
            f"formula={self.complex_formula!r}, "
            f"n_levels={self.n_levels})"
        )


# ── Complex MCTS ─────────────────────────────────────────────────────────────

class _ComplexMCTSNode:
    """MCTS node for the complex grammar."""

    __slots__ = (
        "partial", "parent", "children", "visits", "total_reward",
        "untried_expansions", "is_terminal",
    )

    def __init__(
        self,
        partial: Node,
        parent: "_ComplexMCTSNode | None",
        max_depth: int,
    ) -> None:
        self.partial = partial
        self.parent  = parent
        self.children: list[_ComplexMCTSNode] = []
        self.visits: int          = 0
        self.total_reward: float  = 0.0
        self.is_terminal: bool    = _is_complete(partial)
        self.untried_expansions: list[Node] = (
            [] if self.is_terminal
            else _c_expand_options(partial, max_depth)
        )

    def ucb1(self) -> float:
        if self.visits == 0:
            return INF
        parent_visits = self.parent.visits if self.parent else self.visits
        exploit = self.total_reward / self.visits
        explore = math.sqrt(2.0) * math.sqrt(math.log(parent_visits) / self.visits)
        return exploit + explore

    def is_fully_expanded(self) -> bool:
        return len(self.untried_expansions) == 0

    def best_child(self) -> "_ComplexMCTSNode":
        return max(self.children, key=lambda c: c.ucb1())


def complex_mcts_search(
    target_fn:     Callable[[float], float],
    probe_points:  list[float] | None = None,
    projection:    str = "imag",
    depth:         int = 5,
    n_simulations: int = 10_000,
    seed:          int = 42,
    log_every:     int = 0,
    n_rollouts:    int = 1,
) -> ComplexMCTSResult:
    """
    MCTS over the complex EML grammar.

    Searches for EML trees with complex terminals {1, x, ix, i} whose
    imaginary (or real) projection minimises MSE against ``target_fn``.

    The simplest discovery is Im(eml(ix, 1)) = sin(x) (1 node, MSE = 0).
    Deeper searches find approximate constructions for Bessel J₀, Airy Ai, erf.

    Args:
        target_fn:     Target function x → y (real-valued).
        probe_points:  Evaluation points.  Default: 50 points in [-3, 3].
        projection:    'imag' (default) or 'real' — which complex part to match.
        depth:         Maximum tree depth.
        n_simulations: Number of MCTS simulations.
        seed:          Random seed.
        log_every:     Print progress every N simulations (0 = silent).
        n_rollouts:    Parallel rollouts per simulation (> 1 improves exploration).

    Returns:
        ComplexMCTSResult with best tree, MSE, formula, and projection info.

    Examples
    --------
    Recover sin(x) exactly in one simulation::

        import math
        from monogate.complex_search import complex_mcts_search

        result = complex_mcts_search(math.sin, n_simulations=100, projection='imag')
        print(result.complex_formula)  # eml(ix, 1.0)
        print(f"MSE = {result.best_mse:.2e}")  # ≈ 0

    Search for Bessel J₀ approximation::

        from scipy.special import j0
        result = complex_mcts_search(j0, depth=4, n_simulations=5000)
        print(result.complex_formula)
    """
    if projection not in ("imag", "real"):
        raise ValueError(f"projection must be 'imag' or 'real', got {projection!r}")

    if probe_points is None:
        probe_points = [-3.0 + 6.0 * i / 49 for i in range(50)]
    probe_y = [target_fn(x) for x in probe_points]

    rng  = random.Random(seed)
    t0   = time.perf_counter()
    root = _ComplexMCTSNode(_placeholder(), parent=None, max_depth=depth)

    best_node: Node  = _c_leaf(1.0)
    best_mse:  float = INF
    history:   list[tuple[int, float]] = []

    rollout_rngs = [random.Random(seed + i * 31337) for i in range(max(n_rollouts, 1))]

    def _rollout(partial: Node, rng_: random.Random) -> tuple[Node, float]:
        completed = _c_random_complete(partial, depth, rng_)
        score     = _c_score(completed, probe_points, probe_y, projection)
        return completed, score

    for sim in range(1, n_simulations + 1):
        # Selection
        node = root
        while node.is_fully_expanded() and node.children and not node.is_terminal:
            node = node.best_child()

        # Expansion
        if not node.is_terminal and node.untried_expansions:
            expansion = node.untried_expansions.pop(
                rng.randrange(len(node.untried_expansions))
            )
            child = _ComplexMCTSNode(expansion, parent=node, max_depth=depth)
            node.children.append(child)
            node = child

        # Simulation
        if node.is_terminal:
            completed = node.partial
            mse       = _c_score(completed, probe_points, probe_y, projection)
        elif n_rollouts <= 1:
            completed = _c_random_complete(node.partial, depth, rng)
            mse       = _c_score(completed, probe_points, probe_y, projection)
        else:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=n_rollouts) as exe:
                futures = [
                    exe.submit(_rollout, node.partial, rollout_rngs[i])
                    for i in range(n_rollouts)
                ]
                results = [f.result() for f in futures]
            completed, mse = min(results, key=lambda r: r[1])

        reward = 1.0 / (1.0 + mse)

        if mse < best_mse:
            best_mse  = mse
            best_node = completed

        # Backpropagation
        n = node
        while n is not None:
            n.visits       += 1
            n.total_reward += reward
            n = n.parent

        if log_every and sim % log_every == 0:
            print(
                f"  sim {sim:>6}/{n_simulations}  best_mse={best_mse:.4e}"
                f"  formula={formula_complex(best_node)}"
            )
        if log_every or sim % max(1, n_simulations // 20) == 0:
            history.append((sim, best_mse))

    return ComplexMCTSResult(
        best_tree       = best_node,
        best_mse        = best_mse,
        best_formula    = formula_complex(best_node),
        n_simulations   = n_simulations,
        elapsed_s       = time.perf_counter() - t0,
        projection      = projection,
        complex_formula = formula_complex(best_node),
        history         = history,
    )


def complex_beam_search(
    target_fn:    Callable[[float], float],
    probe_points: list[float] | None = None,
    projection:   str = "imag",
    depth:        int = 6,
    width:        int = 50,
    log_every:    int = 0,
) -> ComplexBeamResult:
    """
    Beam Search over the complex EML grammar.

    Incrementally builds trees using {1, x, ix, i} as terminals, keeping the
    top-``width`` candidates by Im/Re MSE at each expansion level.

    Args:
        target_fn:    Target function x → y.
        probe_points: Evaluation points. Default: 50 points in [-3, 3].
        projection:   'imag' or 'real'.
        depth:        Maximum tree depth.
        width:        Beam width.
        log_every:    Print per-level progress (0 = silent).

    Returns:
        ComplexBeamResult with best tree, MSE, formula, projection info.

    Examples
    --------
        import math
        from monogate.complex_search import complex_beam_search

        result = complex_beam_search(math.sin, depth=4, width=20)
        print(result.complex_formula)
    """
    if projection not in ("imag", "real"):
        raise ValueError(f"projection must be 'imag' or 'real', got {projection!r}")

    if probe_points is None:
        probe_points = [-3.0 + 6.0 * i / 49 for i in range(50)]
    probe_y = [target_fn(x) for x in probe_points]

    t0         = time.perf_counter()
    best_node: Node  = _c_leaf(1.0)
    best_mse:  float = INF
    history:   list[tuple[int, float]] = []

    beam: list[tuple[float, Node]] = [(INF, _placeholder())]
    level = 0

    while beam:
        level += 1
        candidates: list[tuple[float, Node]] = []

        for _, partial in beam:
            for expanded in _c_expand_options(partial, depth):
                if _is_complete(expanded):
                    mse = _c_score(expanded, probe_points, probe_y, projection)
                    candidates.append((mse, expanded))
                    if mse < best_mse:
                        best_mse  = mse
                        best_node = expanded
                else:
                    candidates.append((INF, expanded))

        if not candidates:
            break

        finite   = sorted([(m, n) for m, n in candidates if m < INF], key=lambda t: t[0])
        infinite = [(m, n) for m, n in candidates if m == INF]
        beam     = (finite + infinite)[:width]
        history.append((level, best_mse))

        if log_every and level % log_every == 0:
            print(
                f"  level {level:2d}: beam={len(beam):4d}  "
                f"best_mse={best_mse:.4e}  "
                f"formula={formula_complex(best_node)}"
            )

        if all(_is_complete(n) for _, n in beam):
            break

    return ComplexBeamResult(
        best_tree       = best_node,
        best_mse        = best_mse,
        best_formula    = formula_complex(best_node),
        n_levels        = level,
        elapsed_s       = time.perf_counter() - t0,
        projection      = projection,
        complex_formula = formula_complex(best_node),
        history         = history,
    )
