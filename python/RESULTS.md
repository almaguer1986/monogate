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

## Open problems

- Why does `eml(eml(0.45, 1), eml(1, 1))` form a stable attractor for e at depth=2?
- Can a discrete search (exhaustive or MCTS) escape phantoms that gradient descent cannot?
- Is there a penalty schedule that avoids phantom attractors and reaches the true Pareto frontier?
