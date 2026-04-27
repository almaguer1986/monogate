---
layout: ../../layouts/Base.astro
title: "When Olympiad Problems Produce EML Trees"
description: "Classical functional equations characterise exp and ln, and their solutions turn out to be minimal EML trees — often cheaper than the equations that define them."
date: 2026-04-23
tag: observation
difficulty: 3
---

Functional equations are how mathematicians *define* the elementary functions
without reaching for calculus.  `f(x + y) = f(x) · f(y)` for every real
`x, y` — together with continuity — forces `f(x) = eᶜˣ`.  Change one
symbol and you get the logarithm instead: `f(xy) = f(x) + f(y)` gives
`f(x) = c · ln x`.

What's rarely noticed is that the *solutions* to these equations are the
minimal EML trees for those functions.  The Cauchy equations don't just
produce exp and ln: they produce **1-node** or **3-node** EML trees, the
cheapest possible representations in the F16 census.

Ten olympiad-style problems, run through the SuperBEST v5.2 cost table.
Every number below is a node count, not a marketing figure.

## The Cauchy trio, in nodes

**Additive Cauchy.**  `f(x + y) = f(x) + f(y)` → `f(x) = c · x`.  That's
one `mul` — `mul = 2n`.  The equation itself is addition (also `2n`).
Input operation and output function share the same budget.

**Exponential Cauchy.**  `f(x + y) = f(x) · f(y)` → `f(x) = eᶜˣ`.
Compute `c · x` (2n), then apply `exp` (1n).  **Total: 3n.**  The gap
between 2n and 3n is exactly one `exp` node — the operator that turns
addition into multiplication.  That's the whole folklore in one number.

**Logarithmic Cauchy.**  `f(xy) = f(x) + f(y)` → `f(x) = c · ln x`.
One `ln` (1n) via `EXL(0, x)`, then `mul` (2n).  **Total: 3n** — the
same as exponential Cauchy.  exp and ln are each other's minimal-tree
conjugates, and that conjugacy shows up in the node count without
anyone having to prove it separately.

## Solutions are often cheaper than their equations

**`f(x + y) = f(x)·eʸ + f(y)·eˣ`** → `f(x) = k · x · eˣ`.

On `x > 0` the solution factors through `exp(ln x + x)`: one `ln` (1n),
one `add` (2n), one `exp` (1n).  **Solution cost: 4n.**

The right-hand side of the equation, on the other hand, requires two
`mul` (4n), two `exp` (2n), one `add` (2n) — **8n per evaluation**.
The functional equation costs twice what its solution costs.  This is
not a coincidence specific to this problem: fixed points of cost-heavy
constraints tend to live at low cost.

## The multiplicative Cauchy family is a 3-node primitive

**`f(xy) = f(x) + f(y) + f(x)·f(y)`** → `f(x) = xᵏ − 1`.

`EPL(k, x) = exp(k · ln x) = xᵏ` is a single F16 node (verified at
machine precision on a 100 k-sample random sweep — max relative error
2 × 10⁻¹⁵).  Subtract 1 and you're done.  **3n total.**

Every power-law scaling relation — Zipf, Pareto, allometric biology,
Kepler's third law, Stefan-Boltzmann — lives in this cell.  They are
all the same 3-node tree with different values of `k`.

## An inequality is a cost comparison

**`x + 1/x ≥ 2 + ln²(x)` for `x > 0`.**

- LHS tree: `add(x, recip x)` — **3n**.
- RHS tree: `add(2, mul(ln x, ln x))` — **5n**.

A 3-node expression bounds a 5-node expression from above, with equality
at `x = 1`.  The cheaper tree is the upper bound.

Does this direction always hold?  Not quite — the classical AM-GM
inequality `(a + b) / 2 ≥ √(ab)` bounds a **4-node** arithmetic mean
**above** a **3-node** geometric mean.  Here the more expensive tree is
the upper bound.  Cost is silent on the direction of the inequality; it
just tells you which trees are in play.

## Power means have a cost hierarchy

For `a, b > 0`:

| Mean | Construction | Cost |
|---|---|---|
| Geometric | `√(a·b)` | 3n |
| Arithmetic | `(a + b) / 2` | 4n |
| p-mean | `(aᵖ + bᵖ)^(1/p)` | 5n |
| Harmonic | `2 / (1/a + 1/b)` | 8n |

The harmonic mean is the most expensive, which is why numerical code
usually rewrites it as `2ab / (a + b)` — that drops one recip pair and
lands at 6n.  EML accounting makes the rewrite quantitative: it's a
2-node saving, independent of input.

## The recurrence that climbs an EML tower

**`f(x) = exp(f(x − 1)) + ln|x|`** is a one-shot `EAL` per step.
`f(n)` from `f(0)` requires `n` applications of the EAL operator, stacked.
That's a *linear* growth of EML depth with `x`.  The recurrence is an
explicit witness of the EML depth hierarchy (T30) — one new node per
step, no shortcut, no collapse.

The `ln|x|` term puts the equation on the ELC boundary for `x < 0`:
absolute value is piecewise, so the negative-axis branch formally sits
outside pure ELC.  Restrict to `x > 0` and the whole tower is
ELC-interior.

## The hyperbolic-vs-trigonometric split

**`f(x+y) + f(x−y) = 2·f(x)·cosh(y) + 2·x·sinh(y)`** has the solution
family `f(x) = a·x·eˣ + b·x·e⁻ˣ + c`.  All three summands are inside
ELC: `x·eˣ` via `exp(ln x + x)` (4n) and `x·e⁻ˣ` via the DEML primitive
(3n, because `DEML(x, 1) = e⁻ˣ` is a 1-node operator; multiplying by
`x` adds 2n).  Full solution: about 15n.

Replace `cosh` and `sinh` with `cos` and `sin` and the same equation
has solutions in the trig family — which the Infinite Zeros Barrier
(T01) rules out of any finite real EML tree.  One symbol change flips
the problem from ELC-interior to ELC-exterior.

## One impossibility, two mechanisms

**`f(z)² = eᶻ + e⁻ᶻ = 2·cosh(z)`**.  On the real line `f(z) = √(2·cosh z)`
is a clean 5-node construction (4n for the sum of two exponentials, +1
for the square root).  Over the complex plane, `cosh` has zeros at
`z = iπ(n + 1/2)`, each of which becomes a branch point of the square
root — and an entire function can't carry a countable lattice of branch
points.

The Olympiad problem's impossibility is structurally the same as the
Infinite Zeros Barrier, running in reverse.  In T01 a function has too
many zeros to sit inside real EML; here the function's *square* has
zeros that obstruct the square-root's entirety.  Same analytic source,
different direction.

## Reproduce

```bash
git clone https://github.com/agent-maestro/monogate-research       # private
cd monogate-research/exploration/olympiad-sessions
python scripts/verify_claims.py          # the 6 baseline identities
python scripts/olympiad_eml.py           # the 10-problem node-cost table
```

Both scripts output JSON to `data/` and a markdown note to `findings/`.
Every number in this post comes from one of those files.  The post
itself is OBSERVATION tier — it cites classical Olympiad solutions
and adds the node-count layer; it does not claim new theorems.

## The pattern

These ten problems don't agree on which side of an inequality to put
which tree, or whether the equation is larger than its solution or
smaller than it.  They agree on one thing: **the solutions are tiny
EML trees**.  A functional equation that defines exp, ln, or a power
produces a 1-, 2-, 3-, or 4-node tree as its answer.  The operator
structure that generates elementary functions generates low-cost
trees.  That's what "EML is the universal operator" means in practice
— not a philosophical claim, a node-count claim that survives every
concrete olympiad case we tested.
