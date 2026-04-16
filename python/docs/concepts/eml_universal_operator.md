# EML — The Universal Operator

## The central insight

The binary operator:

```
eml(x, y) = exp(x) − ln(y)
```

combined with the constant **1** can generate *every elementary function* as a finite expression tree. This was proved by Odrzywołek (2026) and confirmed exhaustively for all operations at machine precision.

## Why this works

The key observation is that `exp` and `ln` are inverses, so:

- `exp(x)` is directly the output of `eml(x, 1)` because `ln(1) = 0`
- `ln(y)` is reachable via `eml(0, y⁻¹)` via a 2-step construction
- Addition and subtraction follow from combinations of exp/ln

Once you can compute `exp`, `ln`, and the four arithmetic operations, every elementary function follows from calculus identities.

## The construction tree

Every arithmetic primitive has a known EML tree:

| Operation | EML formula | Nodes |
|-----------|-------------|-------|
| `exp(x)` | `eml(x, 1)` | 1 |
| `sub(a, b)` | `eml(ln(a), exp(−b))` | 3 |
| `neg(x)` | `eml(0, exp(x))` | 2 |
| `add(a, b)` | `eml(ln(exp(a)+exp(b)), 1)` | via log-sum-exp |
| `mul(a, b)` | `exp(ln(a) + ln(b))` | 7 |
| `div(a, b)` | `exp(ln(a) − ln(b))` | 5 |
| `pow(a, b)` | `exp(b · ln(a))` | 9 |
| `recip(x)` | `eml(−ln(x), 1)` | 3 |

## Completeness

The formal completeness result means: for any elementary function `f(x)`, there exists a finite integer `N` and an EML tree `T` with `N` internal nodes such that `T(x) = f(x)` for all `x` in the function's domain.

This is not just an approximation theorem — the trees are exact (to floating-point precision).

## The constant

The choice of constant matters. EML uses **1** as its generating constant because:
- `ln(1) = 0`, making `eml(x, 1) = exp(x)` — the most basic useful operation
- Starting from 1, you can build any rational number via the arithmetic identities

Other constants (e.g., `e` for EDL) generate different subsets of elementary arithmetic.

## Python API

```python
from monogate import op, E, ZERO

# op = eml gate
result = op(x=1.0, y=1.0)   # exp(1.0) - ln(1.0) = e - 0 = e ≈ 2.718

# Composed operations
from monogate import exp_eml, ln_eml, add_eml, mul_eml

print(exp_eml(1.0))          # 2.718...   (1 node)
print(ln_eml(math.e))        # 1.0        (2 nodes)
print(add_eml(1.0, 1.0))     # 2.0        (3 nodes)
print(mul_eml(2.0, 3.0))     # 6.0        (7 nodes)
```

## See also

- `monogate.core` — all EML arithmetic primitives
- `THEORY.md` — open conjectures and resolved results
- `paper/preprint.tex` — formal proof (Odrzywołek 2026)
