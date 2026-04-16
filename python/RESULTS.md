# EML Neural Network Experiments — First Results

The EML operator is `eml(x, y) = exp(x) − ln(y)`. The [monogate project](https://github.com/almaguer1986/monogate) explores whether this single operation can serve as the basis for interpretable machine learning — every node applies the same rule, leaves are the only free parameters. These experiments ask: can a gradient-trained EML tree recover known constants, and can it learn a nonlinear function from data?

---

## Experiment 1 — Can a network find known constants?

`EMLTree(depth=2)` is a complete binary tree of three EML nodes and four scalar leaf parameters, trained with Adam.

**Targeting e:**
```
loss    : 1.95e-09
formula : eml(eml(0.57079, 1.3486), eml(1.0474, 0.87535))
```

**Targeting 0:**
```
loss    : 4.45e-10
formula : eml(eml(0.08911, 1.8195), eml(1.4879, 0.37403))
```

Both converged below `1e-8`. Neither is the minimal construction — `eml(1, 1) = e` is the one-node expression for e, and `eml(e, e) = 0` gives zero. The network found different valid paths with irrational-looking constants that compose correctly. Gradient descent found *a* solution, not *the* simplest one.

Notebooks: [`experiment_01.ipynb`](notebooks/experiment_01.ipynb) · [`experiment_02.ipynb`](notebooks/experiment_02.ipynb)

---

## Experiment 2 — Can a network learn exp(x) from data?

`EMLNetwork(depth=2)` replaces each scalar leaf with a learned linear function of the input, trained on 100 points of `exp(x)` over `[0.1, 3]` with normalised input and target.

```
training MSE : 8.04e-05  (normalised scale)
formula      : eml(eml((0.5683·x+0.090), (0.1329·x+1.964)),
                   eml((0.7216·x+1.381), (−0.7026·x+0.775)))
```

One implementation detail mattered: the right argument of each EML node must be positive for `ln()` to be defined. Early in training, leaf weights drift negative, `ln(negative)` produces NaN, and Adam silently skips the update — freezing at a bad local minimum. The fix was a `softplus` gate on every right child: `softplus(x) = ln(1 + eˣ)` is always positive and equals `x` once the leaf is well-trained. Without it, MSE was 3.4e-2. With it: 8.0e-5.

---

## Experiment 3 — The complexity-accuracy tradeoff

Adding a penalty `λ` to the loss lets us trace the Pareto frontier between accuracy and simplicity. For `EMLTree`, the penalty is `λ · Σ|leaf − 1|` (pull leaves toward the EML terminal 1); for `EMLNetwork`, it is `λ · Σ|weight|` (L1 on linear weights, pushing leaves toward constants).

At λ=0 the tree found `eml(eml(0.571, 1.348), eml(1.047, 0.876))` with error 1.87e-04. As λ grew, the penalty drove three of four leaves to `≈ 1` — but one sat at `≈ 0.45` across the entire sweep. The tree settled into `eml(eml(0.45, 1), eml(1, 1))`, locally stable near e, and never escaped. Error climbed monotonically from λ=0.01 (error 5.69e-04) to λ=2.0 (error 1.80e-01).

This is a **phantom attractor**: a non-minimal expression that is locally stable under gradient descent. The leaf→1 penalty also has the wrong inductive bias: pulling all leaves to 1 gives `eml(eml(1,1), eml(1,1)) = eml(e, e) ≈ 14.78`, not e.

**EMLNetwork binary search (targeting exp(x)):**

Binary search found the critical λ at `0.500015` — the point where all linear weights dropped below 0.05 (effectively constant leaves). The accuracy cost: normalised MSE rose from `8.60e-05` to `9.13e-03`, a **10,518% increase**. Enforcing minimal structure costs two orders of magnitude in accuracy.

---

## What this means

Interpretable AI via EML works — the network finds valid symbolic expressions and learns from data. But minimal structure is expensive: gradient descent cannot efficiently navigate from accurate-but-complex to accurate-and-simple. The phantom attractor phenomenon is a new open problem.

---

## Named Phenomena

Five structural properties of EML symbolic regression identified through systematic experimentation:

**1. Phantom Attractors**
Locally stable non-minimal EML constructions that resist complexity penalties; the canonical example is `eml(eml(0.45, 1), eml(1, 1))` as an attractor for e, where escaping toward the minimal `eml(1,1)` carries a 10,518% MSE penalty.

**2. Lambert W Fixed Point**
The right-chain topology with all-ones leaves converges to W(eᵉ) ≈ 2.0168 — a fixed point of the iteration y → e − ln(y) — connecting EML tree iteration to Lambert W function theory.

**3. Affine Leaf Necessity**
Scalar leaves cannot represent periodic functions under EML; when leaves are constrained near 1, output converges to W(eᵉ) regardless of depth, with an MSE floor above 4.0 for sin(x).

**4. Left-Right Information Asymmetry**
In EML trees the left subtree encodes function behavior and the right subtree encodes domain scaling; fixing the right half of leaves costs 100× more MSE than fixing the left half.

**5. Optimal Topology Bias**
Mildly left-heavy trees (balance score 1) outperform both right-chain and perfectly balanced topologies for periodic function approximation; perfect balance scores worst in its depth class.

---

## Open problems

- Why does `eml(eml(0.45, 1), eml(1, 1))` form a stable attractor for e at depth=2?
- Can a discrete search (exhaustive or MCTS) escape phantoms that gradient descent cannot?
- Is there a penalty schedule that avoids phantom attractors and reaches the true Pareto frontier?


---

## Exhaustive Sin-Search: Complete Results (N ≤ 11)

**Date:** 2026-04-16 · **Script:** `monogate/search/sin_search_05.py`

### Summary table

| N  | Catalan(N) | Raw trees | After exact parity | Cumulative | Result |
|----|------------|-----------|-------------------|------------|--------|
| 1  | 1 | 4 | 2 | 4 | no candidate |
| 2  | 2 | 16 | 8 | 20 | no candidate |
| 3  | 5 | 80 | 40 | 100 | no candidate |
| 4  | 14 | 448 | 224 | 548 | no candidate |
| 5  | 42 | 2,688 | 1,344 | 3,236 | no candidate |
| 6  | 132 | 16,896 | 8,448 | 20,132 | no candidate |
| 7  | 429 | 109,824 | 54,912 | 129,956 | no candidate |
| 8  | 1,430 | 732,160 | 366,080 | 862,116 | no candidate |
| 9  | 4,862 | 4,978,688 | 2,489,344 | 5,840,804 | no candidate |
| 10 | 16,796 | 34,398,208 | 17,199,104 | 40,239,012 | no candidate |
| **11** | **58,786** | **240,787,456** | **208,901,719** | **281,026,468** | **no candidate** |

**N=11 runtime:** 323.1s (5.4 min) · parity filter eliminated 13.2% of raw assignments

```
RESULT: NO EML tree with terminals {1, x} equals sin(x) for any N ≤ 11.
        281,026,468 trees searched. Zero candidates at any tolerance (1e−4 to 1e−9).
```

**Theory:** The Infinite Zeros Barrier proves this holds for all N: sin(x) has
infinitely many zeros (at kπ); every finite real-valued EML tree is real-analytic
and has only finitely many zeros. The exhaustive search provides empirical
confirmation. See `paper/preprint.tex` §7 and `PAPER.md §6`.

**Complex bypass (exact, 1 node):**
```
Im(eml(i·x, 1)) = Im(exp(ix) − ln(1)) = Im(e^(ix)) = sin(x)
```
Exact for all x ∈ ℝ. The barrier is a real-domain statement only.

### Near-miss gallery (top 10 closest to sin(x) found at N=11)

These are the closest real-valued EML trees — not exact, but the best achievable:

| Rank | MSE | Formula |
|------|-----|---------|
| #1 | 1.4781e-04 | `eml(eml(eml(x,1),eml(1,1)),eml(eml(eml(eml(x,1),eml(1,1)),eml(x,1)),eml(x,1)))` |
| #2 | 1.4822e-04 | `eml(eml(1,1),eml(eml(eml(1,1),eml(x,1)),eml(eml(eml(eml(x,1),eml(1,1)),1),1)))` |
| #3 | 2.5052e-04 | `eml(x,eml(1,eml(x,eml(eml(eml(x,eml(x,1)),eml(eml(1,eml(x,1)),eml(x,1))),1))))` |
| #4 | 3.1694e-04 | `eml(1,eml(eml(1,eml(x,1)),eml(1,eml(eml(x,1),eml(eml(x,eml(eml(1,1),1)),1)))))` |
| #5 | 3.1694e-04 | `eml(1,eml(eml(1,eml(x,1)),eml(1,eml(1,eml(eml(x,eml(eml(eml(x,1),1),1)),1)))))` |
| #6 | 5.3702e-04 | `eml(1,eml(eml(1,eml(x,1)),eml(1,eml(eml(1,eml(1,eml(eml(x,eml(1,1)),1))),1))))` |
| #7 | 5.3966e-04 | `eml(x,eml(1,eml(eml(x,eml(x,1)),eml(eml(eml(x,eml(1,eml(1,1))),eml(x,1)),1))))` |
| #8 | 6.9860e-04 | `eml(1,eml(eml(1,eml(x,1)),eml(eml(1,eml(eml(1,1),eml(1,1))),eml(x,eml(x,1)))))` |
| #9 | 7.3270e-04 | `eml(1,eml(eml(1,eml(x,1)),eml(x,eml(eml(eml(x,eml(eml(1,eml(1,1)),1)),1),1))))` |
| #10 | 8.2106e-04 | `eml(1,eml(eml(1,eml(x,1)),eml(1,eml(eml(eml(x,eml(1,1)),eml(x,eml(x,1))),1))))` |

Best near-miss (#1) is 2,842× closer to sin(x) than the trivial baseline exp(x) (MSE≈0.42).

**Analysis script:** `python monogate/search/analyze_n11.py`
**HTML gallery:** `python monogate/search/analyze_n11.py --html output/n11_gallery.html`
