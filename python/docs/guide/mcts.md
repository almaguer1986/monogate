# MCTS Search

monogate includes a gradient-free symbolic regression engine over the EML grammar. Unlike gradient descent, it does not get trapped in the phantom attractor.

## Setup

```bash
pip install monogate   # no extra dependencies needed
```

---

## MCTS Search

Monte-Carlo Tree Search over the EML grammar `S → 1 | x | eml(S, S)`.

```python
import math
from monogate.search import mcts_search

result = mcts_search(math.exp, n_simulations=5000, depth=5)
print(result.best_formula)   # eml(x, 1.0)   — exact: exp(x) - ln(1) = exp(x)
print(f"MSE = {result.best_mse:.2e}")   # 0.00e+00
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_fn` | — | Callable `x -> y` |
| `probe_points` | 50 pts in [-3, 3] | Evaluation points |
| `depth` | 5 | Max tree depth |
| `n_simulations` | 10000 | MCTS rollout count |
| `seed` | 42 | RNG seed |
| `log_every` | 0 | Print progress every N simulations |
| `n_rollouts` | 1 | Parallel rollouts per node (>1 improves exploration) |

### Result fields

```python
result.best_formula    # str: human-readable EML expression
result.best_mse        # float: MSE on probe points
result.best_tree       # dict: raw tree node
result.n_simulations   # int
result.elapsed_s       # float: wall time
result.history         # list[(sim, best_mse)]: convergence checkpoints
```

---

## Beam Search

More systematic than MCTS — keeps top-`width` partial trees at each depth level.

```python
from monogate.search import beam_search

result = beam_search(math.sin, depth=6, width=100)
print(result.best_formula)
print(f"MSE = {result.best_mse:.4e}")
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_fn` | — | Callable `x -> y` |
| `probe_points` | 50 pts in [-3, 3] | Evaluation points |
| `depth` | 6 | Max tree depth |
| `width` | 50 | Beam width |
| `log_every` | 0 | Print per-level progress |

---

## Parallel rollouts

```python
# n_rollouts=8: run 8 random completions per simulation, keep best
result = mcts_search(math.sin, n_simulations=2000, n_rollouts=8)
```

Uses `ThreadPoolExecutor` internally. Each rollout gets an independent pre-seeded RNG so results are reproducible.

---

## Why MCTS avoids the phantom attractor

Gradient descent on depth-3 EMLTree converges to the phantom attractor (~3.1696) 100% of the time when targeting π. MCTS explores the full grammar space without gradients:

- **UCB1 selection** balances exploitation vs exploration
- **Random rollout** completes partial trees without gradient signal
- **Reward** = `1 / (1 + MSE)` — bounded in (0, 1], gradient-free

MCTS found `eml(x, 1)` (= exp(x)) exactly for the `math.exp` target with MSE = 0.

!!! note "Infinite Zeros Barrier"
    MCTS also cannot find a real-valued EML tree equaling sin(x). The best it can do is the zero constant (MSE ≈ 0.513 = E[sin²(x)]). This is expected — see the [Research Findings](../research/findings.md) page. Use `monogate.complex_eval` for the exact Euler-path construction.

---

## Custom probe points

```python
import math
from monogate.search import mcts_search

# Probe only positive reals (e.g., for ln target)
probe = [0.1 + 3.0 * i / 49 for i in range(50)]
result = mcts_search(math.log, probe_points=probe, depth=5, n_simulations=3000)
print(result.best_formula)
```
