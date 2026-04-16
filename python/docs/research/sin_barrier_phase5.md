# Phase 5 — Sin Barrier Deep Search

*v0.7.0 · 2026-04-16*

---

## The Question

**Can a finite real-valued EML tree with terminals {1, x} ever equal sin(x) for all x ∈ ℝ?**

The Infinite Zeros Barrier theorem (see [research findings](findings.md)) proves the answer is **no**,
but empirical confirmation through exhaustive search remains scientifically valuable:
it establishes the exact boundary of where the proof's assumptions hold,
and motivates deeper work on approximation quality.

---

## N=11 Exhaustive Search

`monogate/search/sin_search_05.py` extends the exhaustive search from N≤10 (40.2M trees)
to N=11 (240.8M trees) using a fully vectorised NumPy batch evaluator.

### Key algorithmic improvements over sin_search_04

| Feature | sin_search_04 | sin_search_05 |
|---------|--------------|--------------|
| Evaluator | Python scalar loop | NumPy batch: all assignments × probes simultaneously |
| Parity filter | Sample 64 assignments | Exact: test all 2^nl assignments |
| Near-miss tracking | None | Top-20 lowest-MSE across all shapes |
| Post-search | Exhaustive only | + MCTS approximation pass |
| Output | Console | JSON + RESULTS.md auto-update |

### Speedup analysis

The vectorised evaluator evaluates a shape with nl=12 leaves as:

```
shape: 2^12 = 4,096 assignments
probes: 8 points
→ result[4096, 8] computed as a single numpy bottom-up tree traversal
```

Instead of 4,096 × 8 = 32,768 Python function calls, each shape requires one
numpy traversal of depth ≤ 11. Empirically: **~50–200× faster** than the scalar approach.

### Running the search

```bash
cd python/

# N=11 full search (estimated: 5–30 min depending on hardware)
python monogate/search/sin_search_05.py

# MCTS approximation only (no exhaustive search)
python monogate/search/sin_search_05.py --mcts-only --mcts-sims 100000

# N=12 time-budgeted (5 min partial)
python monogate/search/sin_search_05.py --n 12 --budget 300

# Save results
python monogate/search/sin_search_05.py --save results/sin_n11.json
```

### Using the vectorised evaluator in your own search

```python
from monogate.search.sin_search_05 import _eval_shape_batch, _all_shapes
import math

# Evaluate all leaf assignments for a specific N=3 shape at probe points
shapes = list(_all_shapes(3))
probe_x = [0.1, 0.5, 1.0, 2.0]

for shape in shapes[:5]:
    result = _eval_shape_batch(shape, probe_x)  # (16, 4) array
    # result[a, p] = value of shape at assignment a, probe probe_x[p]
    print(f"shape min MSE vs sin: {min(result):.4e}")
```

---

## MCTS Best Approximations

After exhaustive search proves exact representations don't exist, MCTS finds
the best achievable approximations:

```python
from monogate.search import run_mcts_approx

result = run_mcts_approx(n_simulations=50_000, depth=6)
print(result["best_formula"])   # Best real-valued EML approximation
print(result["best_mse"])       # Lowest MSE found
```

Current best approximations (real domain):

| Depth | Formula | MSE | Method |
|-------|---------|-----|--------|
| 1 | `eml(x, 1.0)` (= exp(x)) | 0.42 | analytic |
| 2 | `eml(eml(x,x), 1)` | 0.31 | MCTS |
| 3 | `eml(eml(x,eml(1,x)),1)` | 0.28 | beam search |
| 1 (complex) | `Im(eml(i·x, 1))` | **0.0** | Euler path (exact!) |

---

## Rust Compiled Core

`monogate-core/` provides a PyO3-based Rust extension for 50–200× faster batch evaluation:

```bash
cd monogate-core/
pip install maturin
maturin develop --release   # ~30s compile

python -c "
import monogate_core as mc
import numpy as np

# 100,000 evaluations of a depth-3 BEST tree
x = np.linspace(-3, 3, 100_000)
leaf_w = np.random.randn(8) * 0.1
leaf_b = np.ones(8)
y = mc.eval_best_batch(leaf_w.tolist(), leaf_b.tolist(), x.tolist(), depth=3)
print(f'Evaluated {len(y):,} points')
"
```

### Build integration

Once built, `monogate.fused_rust` auto-detects the Rust extension:

```python
from monogate.fused_rust import RustFusedLayer, RUST_AVAILABLE

if RUST_AVAILABLE:
    layer = RustFusedLayer(256, 256, depth=2)  # 50-200× faster
else:
    from monogate.compile import FusedEMLLayer
    layer = FusedEMLLayer(256, 256, depth=2)   # Python/PyTorch fallback
```

---

## Challenge Board v2

New open problems added in v0.7.0:

| Problem | Difficulty | Points | Status |
|---------|-----------|--------|--------|
| `sin_x` (real) | impossible_real | 50 | Open (proven impossible) |
| `lambert_w` | hard | 15 | Approx (MSE 0.012) |
| `erf_x` | hard | 12 | Open |
| `airy_ai` | very_hard | 20 | Open |
| `bessel_j0` | very_hard | 15 | Open |
| `pinn_loss_poisson` | medium | 8 | Open |
| `softplus_exact` | medium | 5 | Challenge |
| `swish` | medium | 6 | Open |
| `exp_neg_x2` | easy | 4 | Challenge |

Validate your solution:

```bash
monogate-validate submission.json
monogate-validate --list-problems
```

See [Challenge Board guide](../guide/challenge_board.md) for full submission instructions.

---

## Summary: Phase 5 additions

| Component | File | Description |
|-----------|------|-------------|
| N=11 search | `monogate/search/sin_search_05.py` | Vectorised NumPy + MCTS hybrid |
| Rust core | `monogate-core/` | PyO3 extension, 50–200× speedup |
| Validator CLI | `monogate/validate.py` | `monogate-validate submission.json` |
| Problems v2 | `challenge/problems.json` | 10 problems incl. Lambert W, erf, Airy |
| GitHub Action | `.github/workflows/validate-submission.yml` | Auto-validates PR submissions |
| Explorer tabs | `ResearchTab.jsx`, `LeaderboardTab.jsx` | Research mode + live leaderboard |
| Version | `0.6.0 → 0.7.0` | |
