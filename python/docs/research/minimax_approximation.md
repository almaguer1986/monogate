# Minimax EML Approximation

> Module: `monogate.minimax`
> API: `minimax_eml()`, `minimax_survey()`

---

## What is minimax approximation?

Minimax (or Chebyshev) approximation finds the function in a given class that minimises the *maximum* pointwise error on a domain:

```
min_{T ∈ EML_k}  max_{x ∈ [a,b]}  |T(x) − f(x)|
```

where `EML_k` is the set of EML trees with at most `k` internal nodes.

This is also called the **L∞ approximation** or **uniform approximation**, in contrast to the L² (RMS/MSE) approximation that minimises the average squared error.

### When to prefer minimax

- **Worst-case guarantees.** For hardware implementations, you need a bound on the maximum error, not just the average.
- **Safety-critical applications.** Medical or aerospace computations where a single large error is unacceptable.
- **Equioscillation property.** The Chebyshev alternation theorem says the optimal uniform approximation has exactly `k+2` equioscillation points — a useful diagnostic.

---

## Implementation

`monogate.minimax` uses MCTS with the `'minimax'` objective (already built into `monogate.search.mcts`):

```python
from monogate.minimax import minimax_eml
import math

result = minimax_eml(
    target_fn=math.sin,
    n_nodes=7,
    domain=(-math.pi, math.pi),
    n_simulations=5000,
)
print(result.best_formula)
print(f"L∞ error: {result.linf:.4e}")
print(f"L² error: {result.l2:.4e}")
```

The MCTS reward function is:

```python
reward = 1.0 / (1.0 + max_abs_error)
```

Trees with smaller maximum error get higher reward and are explored more aggressively.

---

## Survey: sin(x) on [−π, π]

The `minimax_survey()` function runs the search at multiple node budgets:

```python
from monogate.minimax import minimax_survey
import math, json

rows = minimax_survey(
    math.sin,
    node_counts=[1, 3, 5, 7, 9, 11],
    domain=(-math.pi, math.pi),
    n_simulations=2000,
)
print(json.dumps(rows, indent=2))
```

Typical output (actual values depend on MCTS luck and simulation budget):

| Nodes | Depth | L∞ error | Notes |
|-------|-------|----------|-------|
| 1     | 1     | ~1.0     | Constant approximation |
| 3     | 2     | ~0.3     | Rough shape |
| 5     | 3     | ~0.1     | Recognizable sine |
| 7     | 3     | ~0.05    | Good approximation |
| 9     | 4     | ~0.02    | Fine-grained |
| 11    | 4     | ~0.01    | Near machine precision region |

*Note:* For sin(x), real EML trees can only approximate (never exact) due to the
Infinite Zeros Barrier. The exact 1-node form uses the complex bypass:
`Im(eml(ix, 1)) = sin(x)`.

---

## Comparison with MSE

The same MCTS infrastructure can be used with `objective='mse'` (default) or `objective='minimax'`. Key differences:

| Property | MSE | Minimax |
|----------|-----|---------|
| Objective | avg(err²) | max(|err|) |
| Sensitive to outliers | Yes | Naturally handles outliers |
| Error distribution | Concentrated regions may be worse | More uniform |
| Typical use | Regression, ML | Hardware tables, safety |

---

## API Reference

### `minimax_eml(target_fn, n_nodes, domain, ...)`

```python
from monogate.minimax import minimax_eml, MinimaxResult
```

Returns a `MinimaxResult` with:
- `best_tree` — EML tree dict (usable with `to_sympy()`)
- `best_formula` — human-readable string
- `linf` — achieved L∞ error
- `l2` — achieved L² (RMS) error
- `n_nodes` — actual node count in found tree
- `domain` — search domain
- `elapsed_s` — wall-clock time
- `mcts_result` — underlying `MCTSResult` for full history

### `minimax_survey(target_fn, node_counts, ...)`

Runs `minimax_eml` for each node count and returns a list of dicts, suitable for `json.dumps()`.

---

## Implementation notes

- `n_nodes` is converted to depth: `depth = ceil(log2(n_nodes + 1))`
- Probe points are equally spaced on the domain (`n_probe=200` default)
- The MCTS objective is `1 / (1 + max_abs_error)` — higher reward for smaller max error
- The MCTS `best_mse` field stores the minimax objective value (confusingly named, but consistent with the `MCTSResult` schema)
