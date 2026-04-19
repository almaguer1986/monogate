# T_i: i-Constructibility (Strict Grammar)

**Tier:** CONJECTURE
**Session:** S61–S63
**Category:** Core Algebra
**Challenge board:** OPEN

## Statement

i = √(−1) is conjectured to be NOT constructible as a finite EML tree from
terminal {1} under strict principal-branch grammar.

## Evidence

Exhaustive enumeration of all full binary EML trees with N = 1..9 internal
nodes (1,429 trees total), with all leaves = 1. No tree evaluates to i.

### Loophole analysis (S62)

The naive argument — "all nodes stay real, therefore i unreachable" — has a gap.
When a tree produces a negative real value and routes it to the y-slot of an eml
node, the principal-branch ln introduces a complex value:

    eml(x, y) for y < 0: = exp(x) − (ln|y| + iπ) = (exp(x) − ln|y|) − iπ

This **first-generation loophole** activates at N = 5. The first complex value
produced is ≈ 0.198 − 3.14159i (Im = −π).

However, subsequent compositions of this complex value produce Im parts that
are NOT integer multiples of π. The Im/π census (N ≤ 9) shows irrational values
like −0.48, −0.93, −1.59, confirming the iπ-closure induction fails.

Despite this, Im = 1 (i.e., the imaginary unit i) never appears through N = 9.

## Proof Gap

A complete proof requires showing that Im = 1 is unreachable under arbitrary
depth composition. The first-generation argument is valid; the general inductive
step is not. Possible approaches:

1. **Transcendence/algebraic independence**: the reachable Im values form a
   specific subset of ℝ that provably excludes 1.
2. **Lean 4 formalization** (private repo, S66–S69).
3. **Exhaustive extension**: Rust N = 12 search running (started S61).

## Computational Verification

```
python python/experiments/i_constructibility.py      # N=1..7
python python/experiments/i_constructibility_s62.py  # N=1..9 + census
```

## Dependencies

- Real-analytic function theory
- Principal-branch logarithm definition
- Lindemann–Weierstrass (π transcendental) — for first-generation argument only
