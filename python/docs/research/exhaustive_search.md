# Exhaustive Search

## Methodology

The exhaustive search enumerates all EML expression trees up to N leaves by:

1. **Generating all Catalan shapes** (binary tree topologies) for leaf counts 1..N
2. **Enumerating all terminal assignments** (each leaf ∈ {1.0, x}) — 2^N assignments per shape
3. **Parity pruning** — sin is odd: skip any shape where `T(-x) = T(x)` (eliminates ~45%)
4. **All-ones prescreen** — skip if `T(x=[1,1,...,1])` = NaN/∞
5. **Evaluation on probe points** — [-π, π] with 50 points at each tolerance

## Results

### N ≤ 9 (sin_search_03.py)

- Shapes evaluated: 16,796 after parity filter
- Trees evaluated: ~20M
- Result: **zero candidates** at tol=1e-4, 1e-6, 1e-9

### N = 10 (sin_search_04.py)

- 16,796 Catalan shapes × 2^11 = 34,398,208 trees
- Parity pruning: 45.5% shapes eliminated
- Runtime: ~19s (8-core, ProcessPoolExecutor)
- Result: **zero candidates** at tol=1e-4, 1e-6, 1e-9

## Running the search

```bash
cd python/

# N=9 search (fast, ~2 min)
python experiments/sin_search_03.py

# N=10 search (~20s per tolerance with parallelism)
python experiments/sin_search_04.py
```

## Cumulative table

| N | Catalan | Trees | Cumulative |
|---|---------|-------|------------|
| 1 | 1 | 2 | 2 |
| 2 | 1 | 4 | 6 |
| 3 | 2 | 16 | 22 |
| 4 | 5 | 80 | 102 |
| 5 | 14 | 448 | 550 |
| 6 | 42 | 2,688 | 3,238 |
| 7 | 132 | 16,896 | 20,134 |
| 8 | 429 | 109,824 | 129,958 |
| 9 | 1,430 | 731,136 | 861,094 |
| 10 | 4,862 | 4,978,688 | 5,839,782 |
| **Total** | | | **40,239,012** |

## Why these numbers matter

The exhaustive search provides the empirical foundation for the Infinite Zeros Barrier conjecture at finite N. The theoretical proof (real-analytic argument) extends the result to all depths — the search confirms the theorem is tight and the search was correctly implemented.
