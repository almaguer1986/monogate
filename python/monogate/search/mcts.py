"""
monogate.search.mcts — MCTS and Beam Search over the EML grammar.

Grammar:  S  ->  1  |  x  |  eml(S, S)
Operator: eml(a, b) = exp(a) - ln(b)

These algorithms find the best *approximation* to a target function
using EML trees.  They escape local optima that trap gradient descent
(the phantom attractor problem documented in research_02_attractors.py).

Public functions
----------------
mcts_search(target_fn, ...) -> MCTSResult
beam_search(target_fn, ...) -> BeamResult

Both return a result object with:
  .best_tree     -- the winning EML tree node dict
  .best_mse      -- mean squared error on probe points
  .best_formula  -- human-readable formula string
  .history       -- list of (simulation, best_mse) checkpoints

Tree representation
-------------------
Each node is a plain dict with one of three shapes:

    {"op": "leaf", "val": 1.0}      -- constant 1
    {"op": "leaf", "val": "x"}      -- input variable
    {"op": "eml",  "left": node, "right": node}
    {"op": "?"}                     -- placeholder (unexpanded)

All tree-building functions return new dicts; existing trees are never
mutated (immutable pattern — see common/coding-style.md).
"""

from __future__ import annotations

import math
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable


# ── Types & constants ─────────────────────────────────────────────────────────

Node = dict[str, Any]
INF  = float("inf")

_TERMINALS: list[Any] = [1.0, "x"]


# ── Tree constructors (pure; never mutate) ────────────────────────────────────

def _leaf(val: Any) -> Node:
    return {"op": "leaf", "val": val}


def _eml(left: Node, right: Node) -> Node:
    return {"op": "eml", "left": left, "right": right}


def _placeholder() -> Node:
    return {"op": "?"}


def _copy(node: Node) -> Node:
    """Deep copy of a tree node."""
    if node["op"] in ("leaf", "?"):
        return dict(node)
    return {"op": "eml", "left": _copy(node["left"]), "right": _copy(node["right"])}


# ── Tree introspection ────────────────────────────────────────────────────────

def _is_complete(node: Node) -> bool:
    if node["op"] == "?":
        return False
    if node["op"] == "leaf":
        return True
    return _is_complete(node["left"]) and _is_complete(node["right"])


def _depth(node: Node) -> int:
    if node["op"] in ("leaf", "?"):
        return 0
    return 1 + max(_depth(node["left"]), _depth(node["right"]))


def _size(node: Node) -> int:
    """Count internal (eml) nodes."""
    if node["op"] in ("leaf", "?"):
        return 0
    return 1 + _size(node["left"]) + _size(node["right"])


def _formula(node: Node) -> str:
    if node["op"] == "leaf":
        return str(node["val"]) if node["val"] != "x" else "x"
    if node["op"] == "?":
        return "?"
    return f"eml({_formula(node['left'])}, {_formula(node['right'])})"


# ── Tree evaluation ────────────────────────────────────────────────────────────

def _eval_tree(node: Node, x: float) -> float:
    """Evaluate a complete EML tree at x.  Raises ValueError on domain errors."""
    op = node["op"]
    if op == "leaf":
        val = node["val"]
        return x if val == "x" else float(val)
    if op == "?":
        raise ValueError("Incomplete tree")
    a = _eval_tree(node["left"],  x)
    b = _eval_tree(node["right"], x)
    if b <= 0.0:
        raise ValueError(f"ln domain error: b={b}")
    return math.exp(a) - math.log(b)


def _score(node: Node, probe_x: list[float], probe_y: list[float]) -> float:
    """MSE against probe points.  Returns INF on any error."""
    if not _is_complete(node):
        return INF
    total = 0.0
    try:
        for xi, yi in zip(probe_x, probe_y):
            diff  = _eval_tree(node, xi) - yi
            total += diff * diff
    except (ValueError, OverflowError, ZeroDivisionError):
        return INF
    if not math.isfinite(total):
        return INF
    return total / len(probe_x)


# ── Placeholder navigation ────────────────────────────────────────────────────

def _first_placeholder_path(node: Node) -> list[str] | None:
    """DFS path to the first '?' node.  Returns None if none found."""
    if node["op"] == "?":
        return []
    if node["op"] == "leaf":
        return None
    lp = _first_placeholder_path(node["left"])
    if lp is not None:
        return ["left"] + lp
    rp = _first_placeholder_path(node["right"])
    if rp is not None:
        return ["right"] + rp
    return None


def _set_at_path(node: Node, path: list[str], replacement: Node) -> Node:
    """Return a new tree with node at path replaced."""
    if not path:
        return replacement
    direction = path[0]
    rest      = path[1:]
    new_node  = _copy(node)
    if direction == "left":
        new_node["left"]  = _set_at_path(new_node["left"],  rest, replacement)
    else:
        new_node["right"] = _set_at_path(new_node["right"], rest, replacement)
    return new_node


def _expand_options(node: Node, max_depth: int) -> list[Node]:
    """Return all trees obtained by replacing the first '?' with
    a terminal or an eml(?,?) node (if depth budget allows)."""
    path = _first_placeholder_path(node)
    if path is None:
        return []
    options: list[Node] = []
    for t in _TERMINALS:
        options.append(_set_at_path(node, path, _leaf(t)))
    if _depth(node) + 1 < max_depth:
        options.append(_set_at_path(node, path, _eml(_placeholder(), _placeholder())))
    return options


def _random_complete(partial: Node, depth_budget: int, rng: random.Random) -> Node:
    """Randomly complete all placeholders, respecting depth_budget."""
    node = _copy(partial)
    for _ in range(300):
        path = _first_placeholder_path(node)
        if path is None:
            break
        if _depth(node) >= depth_budget - 1:
            replacement = _leaf(rng.choice(_TERMINALS))
        else:
            replacement = (
                _leaf(rng.choice(_TERMINALS))
                if rng.random() < 0.6
                else _eml(_placeholder(), _placeholder())
            )
        node = _set_at_path(node, path, replacement)
    # Force-fill any remaining placeholders
    for _ in range(200):
        path = _first_placeholder_path(node)
        if path is None:
            break
        node = _set_at_path(node, path, _leaf(rng.choice(_TERMINALS)))
    return node


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class MCTSResult:
    """Result returned by mcts_search()."""
    best_tree:    Node
    best_mse:     float
    best_formula: str
    n_simulations: int
    elapsed_s:    float
    history:      list[tuple[int, float]] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"MCTSResult(mse={self.best_mse:.4e}, "
            f"formula={self.best_formula!r}, "
            f"n_sim={self.n_simulations}, "
            f"elapsed={self.elapsed_s:.2f}s)"
        )


@dataclass
class BeamResult:
    """Result returned by beam_search()."""
    best_tree:    Node
    best_mse:     float
    best_formula: str
    n_levels:     int
    elapsed_s:    float
    history:      list[tuple[int, float]] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"BeamResult(mse={self.best_mse:.4e}, "
            f"formula={self.best_formula!r}, "
            f"n_levels={self.n_levels}, "
            f"elapsed={self.elapsed_s:.2f}s)"
        )


# ── MCTS ──────────────────────────────────────────────────────────────────────

class _MCTSNode:
    """Node in the MCTS search tree (wraps a partial EML grammar node)."""

    __slots__ = (
        "partial", "parent", "children", "visits", "total_reward",
        "untried_expansions", "is_terminal",
    )

    def __init__(self, partial: Node, parent: "_MCTSNode | None", max_depth: int) -> None:
        self.partial            = partial
        self.parent             = parent
        self.children: list[_MCTSNode] = []
        self.visits: int        = 0
        self.total_reward: float = 0.0
        self.is_terminal: bool  = _is_complete(partial)
        self.untried_expansions: list[Node] = (
            [] if self.is_terminal else _expand_options(partial, max_depth)
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

    def best_child(self) -> "_MCTSNode":
        return max(self.children, key=lambda c: c.ucb1())


def mcts_search(
    target_fn:     Callable[[float], float],
    probe_points:  list[float] | None = None,
    depth:         int = 5,
    n_simulations: int = 10_000,
    seed:          int = 42,
    log_every:     int = 0,
    n_rollouts:    int = 1,
) -> MCTSResult:
    """Monte-Carlo Tree Search over the EML grammar.

    Finds the EML tree that minimises MSE against ``target_fn`` on
    ``probe_points``.  Unlike gradient descent, MCTS does not get trapped
    in phantom attractors.

    Args:
        target_fn:     Target function, callable: x -> y.
        probe_points:  Evaluation points.  Default: 50 points in [-3, 3].
        depth:         Maximum tree depth (internal node budget).
        n_simulations: Number of MCTS simulations.
        seed:          Random seed for reproducibility.
        log_every:     Print progress every this many simulations (0 = silent).
        n_rollouts:    Number of parallel rollouts per simulation node.  Each
                       rollout uses an independent random completion; the best
                       score among the batch is used for backpropagation.
                       Values > 1 improve exploration at the cost of speed.
                       Uses ThreadPoolExecutor when n_rollouts > 1.

    Returns:
        MCTSResult with best_tree, best_mse, best_formula, history.

    Example::

        import math
        from monogate.search import mcts_search

        result = mcts_search(math.sin, n_simulations=5000)
        print(result.best_formula)
        print(f"MSE = {result.best_mse:.4e}")

        # Parallel rollouts — more thorough per simulation:
        result = mcts_search(math.sin, n_simulations=2000, n_rollouts=8)
    """
    if probe_points is None:
        probe_points = [-3.0 + 6.0 * i / 49 for i in range(50)]
    probe_y = [target_fn(x) for x in probe_points]

    rng  = random.Random(seed)
    t0   = time.perf_counter()
    root = _MCTSNode(_placeholder(), parent=None, max_depth=depth)

    best_node:    Node  = _leaf(1.0)
    best_mse:     float = INF
    history:      list[tuple[int, float]] = []

    # Pre-seed independent RNGs for rollout workers (avoids GIL contention
    # on the shared rng while still being reproducible).
    rollout_rngs = [random.Random(seed + i * 31337) for i in range(max(n_rollouts, 1))]

    def _do_rollout(partial: Node, rng_: random.Random) -> tuple[Node, float]:
        completed = _random_complete(partial, depth, rng_)
        return completed, _score(completed, probe_points, probe_y)

    for sim in range(1, n_simulations + 1):
        # ── Selection ──────────────────────────────────────────────────────
        node = root
        while node.is_fully_expanded() and node.children and not node.is_terminal:
            node = node.best_child()

        # ── Expansion ──────────────────────────────────────────────────────
        if not node.is_terminal and node.untried_expansions:
            expansion = node.untried_expansions.pop(
                rng.randrange(len(node.untried_expansions))
            )
            child = _MCTSNode(expansion, parent=node, max_depth=depth)
            node.children.append(child)
            node = child

        # ── Simulation (rollout, possibly parallel) ────────────────────────
        if node.is_terminal:
            completed = node.partial
            mse       = _score(completed, probe_points, probe_y)
        elif n_rollouts <= 1:
            completed = _random_complete(node.partial, depth, rng)
            mse       = _score(completed, probe_points, probe_y)
        else:
            # Parallel rollouts: run n_rollouts random completions, pick best.
            with ThreadPoolExecutor(max_workers=n_rollouts) as exe:
                futures = [
                    exe.submit(_do_rollout, node.partial, rollout_rngs[i])
                    for i in range(n_rollouts)
                ]
                results = [f.result() for f in futures]
            completed, mse = min(results, key=lambda r: r[1])

        reward = 1.0 / (1.0 + mse)  # bounded in (0, 1]

        if mse < best_mse:
            best_mse  = mse
            best_node = completed

        # ── Backpropagation ────────────────────────────────────────────────
        n = node
        while n is not None:
            n.visits       += 1
            n.total_reward += reward
            n = n.parent

        # ── Logging ───────────────────────────────────────────────────────
        if log_every and sim % log_every == 0:
            print(f"  sim {sim:>6}/{n_simulations}  best_mse={best_mse:.4e}"
                  f"  formula={_formula(best_node)}")
        if log_every or sim % max(1, n_simulations // 20) == 0:
            history.append((sim, best_mse))

    return MCTSResult(
        best_tree=best_node,
        best_mse=best_mse,
        best_formula=_formula(best_node),
        n_simulations=n_simulations,
        elapsed_s=time.perf_counter() - t0,
        history=history,
    )


# ── Beam Search ───────────────────────────────────────────────────────────────

def beam_search(
    target_fn:    Callable[[float], float],
    probe_points: list[float] | None = None,
    depth:        int = 6,
    width:        int = 50,
    log_every:    int = 0,
) -> BeamResult:
    """Beam Search over the EML grammar.

    Incrementally builds trees left-to-right, keeping the top-``width``
    partial trees at each level.  More systematic than MCTS but memory-
    intensive for large widths.

    Args:
        target_fn:    Target function, callable: x -> y.
        probe_points: Evaluation points.  Default: 50 points in [-3, 3].
        depth:        Maximum tree depth.
        width:        Beam width (number of candidates to keep per level).
        log_every:    Print per-level progress (0 = silent).

    Returns:
        BeamResult with best_tree, best_mse, best_formula, history.

    Example::

        import math
        from monogate.search import beam_search

        result = beam_search(math.sin, depth=5, width=30)
        print(result.best_formula)
    """
    if probe_points is None:
        probe_points = [-3.0 + 6.0 * i / 49 for i in range(50)]
    probe_y = [target_fn(x) for x in probe_points]

    t0         = time.perf_counter()
    best_node: Node  = _leaf(1.0)
    best_mse:  float = INF
    history:   list[tuple[int, float]] = []

    # Each entry: (mse_or_INF, partial_node)
    beam: list[tuple[float, Node]] = [(INF, _placeholder())]
    level = 0

    while beam:
        level     += 1
        candidates: list[tuple[float, Node]] = []

        for _, partial in beam:
            for expanded in _expand_options(partial, depth):
                if _is_complete(expanded):
                    mse = _score(expanded, probe_points, probe_y)
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
            print(f"  level {level:2d}: beam={len(beam):4d}  best_mse={best_mse:.4e}")

        if all(_is_complete(n) for _, n in beam):
            break

    return BeamResult(
        best_tree=best_node,
        best_mse=best_mse,
        best_formula=_formula(best_node),
        n_levels=level,
        elapsed_s=time.perf_counter() - t0,
        history=history,
    )
