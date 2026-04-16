"""
monogate.search — Stochastic search strategies for EML grammar trees.

Public API:
    mcts_search(target_fn, ...) -> MCTSResult
    beam_search(target_fn, ...) -> BeamResult
    gpu_mcts_search(target_fn, device='cuda', batch_size=512, ...) -> MCTSResult

These algorithms find the best *approximation* to a target function using
the EML grammar (eml(a,b) = exp(a) - ln(b)).  They are complementary to the
exhaustive search in experiments/sin_search_*.py:
 - Exhaustive search *proves* no exact tree exists (for small N).
 - Stochastic search finds the *best approximation* (for any N).

Both mcts_search and beam_search support an ``objective`` parameter:
 - ``'mse'`` (default) — minimise mean-squared error.
 - ``'minimax'``       — minimise max absolute error (Chebyshev).

Example::

    import math
    from monogate.search import mcts_search, gpu_mcts_search

    result = mcts_search(math.sin, n_simulations=5000)
    print(result.best_formula)     # eml(eml(x, 1), ...)
    print(f"MSE = {result.best_mse:.4e}")

    # GPU-accelerated (falls back to CPU if CUDA unavailable):
    result = gpu_mcts_search(math.sin, batch_size=1024, n_simulations=2000)

    # Minimax objective:
    result = mcts_search(math.exp, n_simulations=2000, objective='minimax')
"""

from .mcts import mcts_search, beam_search, MCTSResult, BeamResult
from .gpu_search import gpu_mcts_search, GPUTreeEvaluator
from .sin_search_05 import run_exhaustive, run_mcts_approx, SearchResult
from .analyze_n11 import run as analyze_n11

__all__ = [
    "mcts_search", "beam_search", "MCTSResult", "BeamResult",
    "gpu_mcts_search", "GPUTreeEvaluator",
    "run_exhaustive", "run_mcts_approx", "SearchResult",
    "analyze_n11",
]
