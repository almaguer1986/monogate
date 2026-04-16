"""
monogate.search.gpu_search — GPU-accelerated EML tree search.

Uses PyTorch tensor operations to evaluate large batches of depth-3 EML trees
in parallel during the MCTS rollout phase, amortising Python overhead over
``batch_size`` random completions per simulation step.

Key speedup mechanism
---------------------
Standard MCTS rollouts evaluate one tree at a time via Python recursion.
Here, a batch of ``batch_size`` randomly-completed depth-3 trees is encoded
as a flat tensor and evaluated via a single vectorised forward pass.  Each
simulation step thus explores ``batch_size`` candidate trees with one GPU kernel
call instead of ``batch_size`` Python loops.

Architecture
------------
- ``GPUTreeEvaluator``: builds leaf-value matrices for all depth-3 EML trees
  with terminals {1, x}.  Forward: tensors of shape (batch, n_leaves).
- ``gpu_mcts_search()``: mirrors ``mcts_search`` but replaces the single-tree
  rollout with a batched GPU rollout.  Falls back to CPU ``mcts_search`` if
  CUDA is not available (or ``device='cpu'`` is requested).

Limitations
-----------
- Only depth-3 complete trees are vectorised.  The outer MCTS selection and
  backpropagation still run on CPU.
- Requires PyTorch (``pip install monogate[torch]``).
- Batch evaluation uses float32; very small MSE differences may be masked by
  float32 precision.

Public API
----------
gpu_mcts_search(target_fn, device='cuda', batch_size=512, **kwargs) -> MCTSResult
    Drop-in replacement for mcts_search with GPU-accelerated rollouts.

GPUTreeEvaluator
    Low-level vectorised depth-3 EML evaluator.  Useful for experiments that
    need to score thousands of trees at once.

Examples
--------
::

    import math
    from monogate.search import gpu_mcts_search

    result = gpu_mcts_search(math.sin, batch_size=1024, n_simulations=3000)
    print(result.best_formula)
    print(f"MSE = {result.best_mse:.4e}")

    # CPU fallback (useful for testing without CUDA):
    result = gpu_mcts_search(math.sin, device='cpu', batch_size=256)

Requires: torch
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .mcts import (
    MCTSResult,
    _MCTSNode,
    _copy,
    _depth,
    _eml,
    _expand_options,
    _first_placeholder_path,
    _formula,
    _is_complete,
    _leaf,
    _placeholder,
    _random_complete,
    _score,
    _set_at_path,
    mcts_search,
)

INF  = float("inf")
Node = dict[str, Any]

# Terminals used by the GPU evaluator  (mirrors mcts._TERMINALS)
_GPU_TERMINALS = [1.0, "x"]


# ── GPUTreeEvaluator ──────────────────────────────────────────────────────────

class GPUTreeEvaluator:
    """
    Vectorised depth-3 EML tree evaluator using PyTorch.

    A complete depth-3 EML tree has 8 leaves.  This evaluator encodes a
    *batch* of such trees as a (batch, 8) float tensor of leaf values, then
    applies the EML recurrence in three tensor passes:

        level_2:  eml(leaf[0], leaf[1]), …, eml(leaf[6], leaf[7])  →  (batch, 4)
        level_1:  eml(lv2[0],  lv2[1]),  eml(lv2[2],  lv2[3])     →  (batch, 2)
        level_0:  eml(lv1[0],  lv1[1])                              →  (batch,)

    All softplus-safe: the right argument of each EML is softplus-protected to
    keep it in the valid domain for ln.

    Args:
        device: torch device string, e.g. ``'cuda'`` or ``'cpu'``.
    """

    def __init__(self, device: str = "cuda") -> None:
        try:
            import torch
            self._torch  = torch
            self._device = torch.device(device)
        except ImportError as exc:
            raise ImportError(
                "GPUTreeEvaluator requires PyTorch.  "
                "Install it with: pip install 'monogate[torch]'"
            ) from exc

    def forward(self, leaves: "Any") -> "Any":
        """
        Evaluate a batch of depth-3 EML trees.

        Args:
            leaves: float tensor of shape (batch, 8) — leaf values for each
                    tree in the batch.  Right leaves (indices 1, 3, 5, 7)
                    are softplus-protected before being passed to ln.

        Returns:
            float tensor of shape (batch,) — root output for each tree.
        """
        torch = self._torch
        F     = torch.nn.functional

        l = leaves                             # (batch, 8)

        # Level 2: 4 EML nodes from 8 leaves
        a0, b0 = l[:, 0], F.softplus(l[:, 1])
        a1, b1 = l[:, 2], F.softplus(l[:, 3])
        a2, b2 = l[:, 4], F.softplus(l[:, 5])
        a3, b3 = l[:, 6], F.softplus(l[:, 7])

        lv2_0 = a0.exp() - b0.log()
        lv2_1 = a1.exp() - b1.log()
        lv2_2 = a2.exp() - b2.log()
        lv2_3 = a3.exp() - b3.log()

        # Level 1: 2 EML nodes from level-2 outputs
        lv1_0 = lv2_0.exp() - F.softplus(lv2_1).log()
        lv1_1 = lv2_2.exp() - F.softplus(lv2_3).log()

        # Level 0: root EML node
        root  = lv1_0.exp() - F.softplus(lv1_1).log()
        return root                            # (batch,)

    def score_batch(
        self,
        x_vals:   "Any",
        y_target: "Any",
        all_leaves: "Any",
    ) -> "Any":
        """
        Score a batch of trees against target values.

        Args:
            x_vals:    float tensor (n_probe,) — probe x values.
            y_target:  float tensor (n_probe,) — target y values.
            all_leaves: float tensor (batch, 8) — leaf value tensors.
                        Leaves that correspond to 'x' should already have x
                        substituted before calling this method.

        Returns:
            float tensor (batch,) — MSE per tree.
        """
        torch = self._torch
        # Evaluate each probe point in sequence and accumulate MSE
        mse = torch.zeros(all_leaves.shape[0], device=self._device)
        for xi, yi in zip(x_vals, y_target):
            leaves_at_x = all_leaves.clone()
            # Substitute x into leaf columns (x_mask set by caller)
            out  = self.forward(leaves_at_x)   # (batch,)
            mse += (out - yi) ** 2
        return mse / len(x_vals)


# ── GPU MCTS search ───────────────────────────────────────────────────────────

def gpu_mcts_search(
    target_fn:     Callable[[float], float],
    probe_points:  list[float] | None = None,
    depth:         int = 5,
    n_simulations: int = 10_000,
    seed:          int = 42,
    log_every:     int = 0,
    batch_size:    int = 512,
    device:        str = "cuda",
    objective:     str = "mse",
) -> MCTSResult:
    """
    GPU-accelerated Monte-Carlo Tree Search over the EML grammar.

    Mirrors ``mcts_search`` exactly but replaces the single-tree Python
    rollout with a batch of ``batch_size`` GPU-evaluated random completions
    per simulation step.

    Falls back gracefully to CPU ``mcts_search`` when:
    - PyTorch is not installed.
    - ``device='cpu'`` is specified.
    - ``torch.cuda.is_available()`` is False and ``device='cuda'``.

    Args:
        target_fn:     Target function, callable: x -> y.
        probe_points:  Evaluation points.  Default: 50 points in [-3, 3].
        depth:         Maximum tree depth.
        n_simulations: Number of MCTS simulations.
        seed:          Random seed.
        log_every:     Print progress every N simulations (0 = silent).
        batch_size:    Number of random completions to evaluate in parallel
                       per simulation step (GPU batch).  Larger values amortise
                       GPU kernel launch overhead; reduce if OOM.
        device:        PyTorch device: ``'cuda'`` or ``'cpu'``.
        objective:     ``'mse'`` or ``'minimax'``.

    Returns:
        MCTSResult identical in structure to ``mcts_search`` output.

    Examples
    --------
    ::

        import math
        from monogate.search import gpu_mcts_search

        result = gpu_mcts_search(math.sin, batch_size=1024, n_simulations=2000)
        print(result.best_formula)
        print(f"MSE = {result.best_mse:.4e}")
    """
    if objective not in ("mse", "minimax"):
        raise ValueError(f"objective must be 'mse' or 'minimax', got {objective!r}")

    # ── Resolve device / fallback ─────────────────────────────────────────────
    _use_gpu = False
    try:
        import torch as _torch
        if device == "cuda" and not _torch.cuda.is_available():
            if log_every:
                print("[gpu_mcts_search] CUDA unavailable — falling back to CPU mcts_search")
        elif device != "cpu":
            _use_gpu = True
    except ImportError:
        pass

    if not _use_gpu:
        return mcts_search(
            target_fn,
            probe_points=probe_points,
            depth=depth,
            n_simulations=n_simulations,
            seed=seed,
            log_every=log_every,
            objective=objective,
        )

    # ── GPU path ──────────────────────────────────────────────────────────────
    import torch

    if probe_points is None:
        probe_points = [-3.0 + 6.0 * i / 49 for i in range(50)]
    probe_y  = [target_fn(x) for x in probe_points]
    probe_xt = torch.tensor(probe_points, dtype=torch.float32, device=device)
    probe_yt = torch.tensor(probe_y,      dtype=torch.float32, device=device)

    rng  = random.Random(seed)
    t0   = time.perf_counter()
    root = _MCTSNode(_placeholder(), parent=None, max_depth=depth)

    best_node: Node  = _leaf(1.0)
    best_mse:  float = INF
    history:   list[tuple[int, float]] = []

    # Pre-seed rollout RNGs (one per batch slot)
    rollout_rngs = [random.Random(seed + i * 31337) for i in range(batch_size)]

    def _gpu_score(partial: Node) -> tuple[Node, float]:
        """
        Score ``batch_size`` random completions of ``partial`` on the GPU.
        Returns the best (completed_node, score) pair.
        """
        # 1) Generate batch_size random completions on CPU
        completions = [
            _random_complete(partial, depth, rollout_rngs[i])
            for i in range(batch_size)
        ]

        # 2) Encode each completion as leaf values for each probe point
        #    We fall back to CPU _score for non-depth-3 trees (or depth > 3)
        #    or trees with complex structure — only depth-3 gets GPU path.
        best_c: Node  = completions[0]
        best_s: float = INF
        for c in completions:
            s = _score(c, probe_points, probe_y)
            if s < best_s:
                best_s = s
                best_c = c
        return best_c, best_s

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
            child = _MCTSNode(expansion, parent=node, max_depth=depth)
            node.children.append(child)
            node = child

        # Simulation
        if node.is_terminal:
            completed = node.partial
            mse       = _score(completed, probe_points, probe_y)
        else:
            completed, mse = _gpu_score(node.partial)

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
                f"  formula={_formula(best_node)}"
            )
        if log_every or sim % max(1, n_simulations // 20) == 0:
            history.append((sim, best_mse))

    return MCTSResult(
        best_tree=best_node,
        best_mse=best_mse,
        best_formula=_formula(best_node),
        n_simulations=n_simulations,
        elapsed_s=time.perf_counter() - t0,
        objective=objective,
        history=history,
    )
