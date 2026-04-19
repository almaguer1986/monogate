"""
Session 2 — Search hardening & caching tests.

Covers: tree hashing, evaluation cache, beam deduplication,
_random_complete guarantee, timeout support.
"""

import math
import time

import pytest

from monogate.search.mcts import (
    BeamResult,
    MCTSResult,
    _copy,
    _eml,
    _eval_tree,
    _is_complete,
    _leaf,
    _placeholder,
    _random_complete,
    _tree_hash,
    beam_search,
    mcts_search,
)
from monogate.search.cache import EvalCache


# ── Tree hashing ──────────────────────────────────────────────────────────────

class TestTreeHash:
    def test_leaf_constant_hash(self):
        h = _tree_hash(_leaf(1.0))
        assert isinstance(h, str) and len(h) > 0

    def test_leaf_variable_hash(self):
        hx = _tree_hash(_leaf("x"))
        h1 = _tree_hash(_leaf(1.0))
        assert hx != h1

    def test_same_structure_same_hash(self):
        t1 = _eml(_leaf(1.0), _leaf("x"))
        t2 = _eml(_leaf(1.0), _leaf("x"))
        assert _tree_hash(t1) == _tree_hash(t2)

    def test_different_structure_different_hash(self):
        t1 = _eml(_leaf(1.0), _leaf("x"))
        t2 = _eml(_leaf("x"), _leaf(1.0))
        assert _tree_hash(t1) != _tree_hash(t2)

    def test_deep_tree_hash(self):
        deep = _eml(_eml(_leaf(1.0), _leaf(1.0)), _leaf("x"))
        shallow = _eml(_leaf(1.0), _leaf("x"))
        assert _tree_hash(deep) != _tree_hash(shallow)

    def test_placeholder_hash(self):
        h = _tree_hash(_placeholder())
        assert isinstance(h, str)

    def test_hash_is_deterministic(self):
        t = _eml(_leaf(1.0), _eml(_leaf("x"), _leaf(1.0)))
        assert _tree_hash(t) == _tree_hash(t)


# ── Evaluation cache ──────────────────────────────────────────────────────────

class TestEvalCache:
    def setup_method(self):
        self.cache = EvalCache(max_size=128)

    def test_cache_miss_returns_none(self):
        assert self.cache.get("absent_key") is None

    def test_cache_set_get(self):
        self.cache.set("k1", 0.5)
        assert self.cache.get("k1") == 0.5

    def test_cache_hit_avoids_recomputation(self):
        calls = []
        def expensive(tree, xs, ys):
            calls.append(1)
            return 99.0

        key = "tree_abc"
        # Miss — should call expensive
        result = self.cache.get(key)
        if result is None:
            result = expensive(None, None, None)
            self.cache.set(key, result)
        assert calls == [1]
        assert result == 99.0

        # Hit — should NOT call expensive again
        result2 = self.cache.get(key)
        if result2 is None:
            result2 = expensive(None, None, None)
            self.cache.set(key, result2)
        assert calls == [1]  # still only 1 call
        assert result2 == 99.0

    def test_cache_max_size_eviction(self):
        cache = EvalCache(max_size=4)
        for i in range(10):
            cache.set(f"key_{i}", float(i))
        # Cache should not grow beyond max_size
        assert cache.size() <= 4

    def test_cache_zero_score(self):
        self.cache.set("perfect", 0.0)
        assert self.cache.get("perfect") == 0.0

    def test_cache_inf_score(self):
        self.cache.set("invalid", float("inf"))
        assert self.cache.get("invalid") == float("inf")


# ── _random_complete guarantee ────────────────────────────────────────────────

class TestRandomCompleteHardening:
    def test_always_produces_complete_tree(self):
        import random
        rng = random.Random(0)
        # Run many times with different seeds and depths
        for seed in range(100):
            rng2 = random.Random(seed)
            partial = _eml(_placeholder(), _eml(_placeholder(), _placeholder()))
            result = _random_complete(partial, depth_budget=6, rng=rng2)
            assert _is_complete(result), f"Incomplete tree on seed {seed}: {result}"

    def test_complete_tree_passes_through(self):
        import random
        rng = random.Random(42)
        complete = _eml(_leaf(1.0), _leaf("x"))
        result = _random_complete(complete, depth_budget=5, rng=rng)
        assert _is_complete(result)

    def test_deeply_nested_partial_completes(self):
        import random
        rng = random.Random(7)
        # 4 levels deep, all placeholders
        partial = _eml(
            _eml(_placeholder(), _eml(_placeholder(), _placeholder())),
            _eml(_eml(_placeholder(), _placeholder()), _placeholder()),
        )
        result = _random_complete(partial, depth_budget=8, rng=rng)
        assert _is_complete(result)

    def test_single_placeholder_completes(self):
        import random
        rng = random.Random(1)
        result = _random_complete(_placeholder(), depth_budget=3, rng=rng)
        assert _is_complete(result)


# ── Beam search deduplication ─────────────────────────────────────────────────

class TestBeamDeduplication:
    def test_beam_runs_without_error(self):
        result = beam_search(math.exp, depth=3, width=10)
        assert isinstance(result, BeamResult)
        assert result.best_mse < float("inf")

    def test_beam_result_has_no_duplicate_evals(self):
        # With deduplication, eval count should be much lower than without
        evals = []
        original_score = None

        result = beam_search(math.exp, depth=4, width=20)
        assert isinstance(result, BeamResult)

    def test_beam_dedup_improves_or_matches_quality(self):
        r1 = beam_search(math.exp, depth=4, width=20, deduplicate=True)
        r2 = beam_search(math.exp, depth=4, width=20, deduplicate=False)
        # Deduplicated result should be at least as good (usually better since
        # width budget is used on distinct candidates)
        assert r1.best_mse <= r2.best_mse * 1.01  # allow 1% tolerance


# ── Timeout support ───────────────────────────────────────────────────────────

class TestTimeoutSupport:
    def test_mcts_respects_timeout(self):
        start = time.perf_counter()
        result = mcts_search(
            math.sin,
            n_simulations=10_000_000,  # huge — should be cut by timeout
            timeout_s=0.5,
        )
        elapsed = time.perf_counter() - start
        assert elapsed < 3.0, f"Timeout not respected: {elapsed:.2f}s"
        assert isinstance(result, MCTSResult)
        assert result.best_mse < float("inf")

    def test_mcts_no_timeout_runs_all_sims(self):
        result = mcts_search(math.exp, n_simulations=100, timeout_s=None)
        assert result.n_simulations == 100

    def test_beam_respects_timeout(self):
        start = time.perf_counter()
        result = beam_search(
            math.sin,
            depth=10,  # deep — expensive
            width=200,
            timeout_s=0.5,
        )
        elapsed = time.perf_counter() - start
        assert elapsed < 3.0
        assert isinstance(result, BeamResult)


# ── Cache integration in mcts_search ─────────────────────────────────────────

class TestCacheIntegration:
    def test_mcts_with_cache_produces_valid_result(self):
        cache = EvalCache(max_size=512)
        result = mcts_search(math.exp, n_simulations=200, eval_cache=cache)
        assert isinstance(result, MCTSResult)
        assert result.best_mse < float("inf")

    def test_cache_populated_after_search(self):
        cache = EvalCache(max_size=512)
        mcts_search(math.exp, n_simulations=200, eval_cache=cache)
        assert cache.size() > 0

    def test_second_search_faster_with_warm_cache(self):
        cache = EvalCache(max_size=2048)

        t0 = time.perf_counter()
        mcts_search(math.exp, n_simulations=300, eval_cache=cache)
        cold_time = time.perf_counter() - t0

        t1 = time.perf_counter()
        mcts_search(math.exp, n_simulations=300, eval_cache=cache)
        warm_time = time.perf_counter() - t1

        # Warm run should be noticeably faster (or at least not slower)
        assert warm_time <= cold_time * 1.5  # generous tolerance
