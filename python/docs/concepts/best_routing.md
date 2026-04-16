# BEST Routing — Hybrid Operator Architecture

## The problem with single operators

EML is complete — it can express every elementary function — but some operations are expensive:

| Operation | EML nodes | EDL nodes | EXL nodes |
|-----------|-----------|-----------|-----------|
| `div(a,b)` | 5 | **1** | 5 |
| `ln(x)` | 2 | 2 | **1** |
| `pow(a,b)` | 9 | 9 | **3** |
| `add(a,b)` | 3 | ❌ cannot | **3** |

No single operator is optimal for all operations. The **BEST** router picks the optimal operator per primitive.

## BEST = Best Exp-ln Selector Tree

```python
from monogate import BEST

# BEST automatically routes each operation to its cheapest implementation
result = BEST.mul(6.0, 7.0)   # EDL path: 7 nodes
result = BEST.ln(math.e)      # EXL path: 1 node
result = BEST.add(3.0, 4.0)   # EML path: 3 nodes
```

## Operator family

| Operator | Formula | Constant | Strength |
|----------|---------|----------|---------|
| **EML** | `exp(x) − ln(y)` | 1 | Addition, subtraction |
| **EDL** | `exp(x) / ln(y)` | e | Division (1 node!), multiplication |
| **EXL** | `exp(x) · ln(y)` | 1 | ln (1 node), pow (3 nodes), stability |
| **EMN** | `exp(x) − ln(-y)` | −1 | Negative domain |
| **EAL** | `exp(x) + ln(y)` | 1 | Specialized sums |

## Node savings

BEST routing achieves:

- **52% average** node savings across all standard operations
- **74% savings** for sin/cos Taylor approximations
- Machine precision (≈6.5×10⁻¹⁵) at 13 terms using **108 nodes** vs 420 for pure EML

## Python API

```python
from monogate import best_optimize, BEST

# Optimize a specific computation
result = best_optimize("sin_taylor_10")
print(result.formula)       # BEST tree formula
print(result.node_count)    # node count
print(result.savings_pct)   # % savings vs EML

# Compare all operators on a single operation
from monogate import compare_all
table = compare_all("mul")
print(table)
```

## How routing works

`HybridOperator` wraps multiple operators and dispatches each arithmetic primitive to the one with the smallest known node count:

```python
from monogate import HybridOperator, EML, EDL, EXL

BEST = HybridOperator(
    add=EML, sub=EML, neg=EML,
    mul=EDL, div=EDL,
    pow=EXL, ln=EXL,
    exp=EML,
)
```

The routing table is fixed at construction time — there is no runtime search.

## See also

- `monogate.core.BEST` — the default hybrid operator
- `monogate.optimize.best_optimize()` — optimize compound expressions
- `PAPER.md` Section 3 — node count tables and comparison
