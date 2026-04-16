# Research Findings

## Overview

monogate is based on the paper [arXiv:2603.21852](https://arxiv.org/abs/2603.21852) (Odrzywołek, 2026). Key findings:

---

## 1. EML Completeness

**The EML operator and the constant 1 generate all elementary arithmetic.**

`eml(x, y) = exp(x) − ln(y)` with terminal constant `1` can express:

| Function | EML nodes | Construction |
|----------|-----------|-------------|
| e | 1 | `eml(1, 1)` |
| 0 | 3 | `eml(1, eml(eml(1,1), 1))` |
| exp(x) | 1 | `eml(x, 1)` |
| ln(x) | 1 | `eml(1, x)` (note: `eml(1,x) = e - ln(x)`, shifted) |
| x + y | 7 | via `exp(ln(x) + ln(y))` construction |
| x · y | 5 | via `exp(ln(x) + ln(y))` |
| x / y | 3 | `eml(ln(x), y)` |
| x^y | 7 | `exp(y · ln(x))` |
| sin(x) | 245 | 8-term Taylor expansion |
| cos(x) | 245 | 8-term Taylor expansion |

---

## 2. BEST Routing

**52% average node reduction by dispatching each primitive to the cheapest operator family.**

Three operator families:

| Family | Operator | Best for |
|--------|----------|----------|
| EML | `exp(a) − ln(b)` | addition, subtraction |
| EDL | `exp(a) / ln(b)` | division, reciprocal |
| EXL | `exp(a) × ln(b)` | multiplication, powers |

BEST (Balanced Exp-Substitution Tree) routes each sub-expression:

| Function | EML nodes | BEST nodes | Savings |
|----------|-----------|------------|---------|
| sin/cos (Taylor-8) | 245 | 63 | **74%** |
| GELU | 17 | 14 | 18% |
| x⁴ + x³ + x² | 67 | 31 | **54%** |
| Average | — | — | **52%** |

**Crossover**: GELU at 18% falls below the Python call overhead threshold (~20%). BEST is worth using when savings exceed 20%.

---

## 3. Phantom Attractor

**depth=3 EMLTree gradient descent converges to 3.1696, not π.**

When training `EMLTree(depth=3)` with `fit()` to target the constant π:

- At regularization λ=0: **100% of 100 seeds** converge to **3.169642...** (the phantom attractor)
- At λ=0.001 (λ_crit): approximately 50% of seeds escape to π
- At λ=0.005: most seeds converge to π

The phantom attractor at **3.169642** is approximately `e + 1/e ≈ 3.086` but more precisely the fixed point of the depth=3 EML loss landscape.

---

## 4. Depth Limit: Numerical Overflow Barrier

**depth=4 EMLTree diverges unconditionally.**

A depth=4 complete binary EML tree has 15 internal nodes. The initial output (even with leaves at 0) is:

```
eml(eml(eml(0,0), eml(0,0)), eml(eml(0,0), eml(0,0)))
≈ exp(exp(exp(1)−1) − ...) ≈ 1.6 × 10^13
```

Any learning rate causes NaN after the first backward pass. This is a **structural** barrier, not a hyperparameter issue.

**Practical training limit: depth ≤ 3.**

---

## 5. Exhaustive Search: N ≤ 10

**40,239,012 EML trees searched. Zero candidates at any tolerance.**

| N (leaves) | Catalan shapes | Trees (EML) | Cumulative |
|------------|---------------|-------------|------------|
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
| **≤10 total** | | | **40,239,012** |

No tree at any tolerance (1e-4, 1e-6, 1e-9) approximates sin(x) on [-π, π].

Parity pruning: sin is odd, so only trees satisfying `T(-x) = -T(x)` are candidates. This eliminates ~45% of shapes before evaluation.

---

## 6. Infinite Zeros Barrier (Theorem)

**No finite real-valued EML tree can equal sin(x).**

**Theorem.** Let T: ℝ → ℝ be any finite EML expression tree (composition of exp and ln with real constants). Then T ≠ sin on all of ℝ.

**Proof.** T is real-analytic (compositions of analytic functions). A non-zero real-analytic function has only *isolated* zeros — finitely many on any bounded interval. But sin(x) has zeros at x = kπ for all integers k — infinitely many on [0, ∞). Therefore T ≢ sin.

**Corollary.** No exhaustive search over real-valued EML trees (at any depth) can find sin — confirming the N ≤ 10 experimental result and extending it theoretically to all depths.

---

## 7. Complex Bypass

**Im(eml(ix, 1)) = sin(x) exactly — one node, machine precision.**

The Infinite Zeros Barrier applies only to *real-valued* trees. In the complex domain:

```
eml(ix, 1) = exp(ix) − ln(1) = exp(ix) = cos(x) + i·sin(x)
```

One EML node, using the `ix` terminal (imaginary x), gives sin(x) (as the imaginary part) to full floating-point precision at every real x. See [Complex EML](../guide/complex.md) for usage.
