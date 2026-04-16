# Phantom Attractors

## The phenomenon

When training an `EMLTree(depth=3)` to fit the constant target `y = π` using gradient descent (`fit()`), the network converges to an *incorrect* value — **3.169642** — regardless of random seed (at regularization λ=0).

This value is not a known mathematical constant. It is a **phantom attractor**: a stable fixed point of the depth=3 EML loss landscape that traps gradient descent.

## Phase transition

Adding L2 regularization on the leaf parameters (λ > 0) breaks the attractor's hold. Sweep results:

| λ | Converges to attractor | Converges to π | Notes |
|---|----------------------|----------------|-------|
| 0.000 | 100% | 0% | Full attractor |
| 0.001 | ~50% | ~50% | **Phase transition (λ_crit)** |
| 0.005 | ~10% | ~90% | Near-full escape |
| 0.010 | 0% | 100% | Full escape |

**λ_crit ≈ 0.001** (refined measurement with 20 seeds × 10 λ values).

## Depth dependence

| Depth | Behavior |
|-------|---------|
| 1 | Converges, no attractor observed |
| 2 | Attractor at ~2.43, weaker basin |
| 3 | **Strong phantom attractor at 3.1696** |
| 4 | **Diverges unconditionally** (Numerical Overflow Barrier) |

Depth=4 is not a deeper attractor — it overflows float64 immediately. Initial output ≈ 10^13.

## Generating attractor data

```bash
cd python/

# Quick sweep (20 seeds, 10 lambda values, depths=[3,4])
python experiments/gen_attractor_data_v2.py

# Full 100-seed trajectories for depth=3
python experiments/gen_attractor_data_v2.py --full

# Original 40-seed data for the explorer animation
python experiments/gen_attractor_data.py
```

Output: `experiments/attractor_phase_transition.json`

## Escaping the attractor

Three strategies:

1. **Regularization**: set λ ≥ 0.001 in `fit()`
2. **MCTS search**: gradient-free, no attractor (see [MCTS Guide](../guide/mcts.md))
3. **Complex terminals**: use `monogate.complex_eval` for exact sin/cos via Euler path

## Visualizing in the Explorer

The **Attractor Lab** tab at [monogate.dev](https://monogate.dev) animates 40 seeds converging, with a λ toggle to show the phase transition live.

---

## Resolution (2026-04-16) — Numerical Artifact, Not a Constant

**C3 is closed.** The phantom attractor is not a mathematical constant.

### What actually happens at depth 3

A 100-seed sweep across seven training targets (π, e, √2, ln(10), 1.5, 2.0, 3.0) at both depth=2 and depth=3:

| Depth | Result |
|-------|--------|
| 2 | Converges to training target with std ≈ 0 (universal, clean) |
| 3 | Collapses to **−∞** universally, every seed, every target |

There is no stable fixed point at 3.1696. The earlier observation was a **pre-collapse transient** — a value the optimizer passes through at intermediate iteration counts before gradient explosion.

### Mechanism

The EML operator `eml(x, y) = exp(x) − ln(y)` requires `y > 0`. At depth 3, the tree has three nested evaluations. Without input clamping:

1. A leaf parameter drifts slightly negative during gradient descent.
2. `ln(negative)` → NaN, which propagates upward through the tree.
3. The gradient update treats NaN as 0 or −∞, driving parameters toward −∞.
4. The final tree output is −∞.

The value 3.1696 appeared in finite-step experiments because early stopping (before full collapse) captured the transient. The earlier depth=4 result ("overflows immediately to 10^13") was the same artifact at faster timescale.

### Why the MCTS prover is unaffected

`EMLProverV2` searches combinatorially via MCTS — it has no gradient landscape, no attractors, and no log-of-negative issue. The artifact is specific to `EMLTree.fit()` (gradient descent on leaf parameters).

### Escaping the artifact in gradient-based training

If you must use gradient descent on EML trees at depth ≥ 3:

1. **Clamp leaf inputs:** ensure `y > ε` before each `ln()` call.
2. **Use regularization:** λ ≥ 0.001 reduces (but does not eliminate) collapse.
3. **Prefer MCTS:** the EMLProverV2 witness search is gradient-free and correct.

### Reproduction

```bash
cd python/
python -m monogate.frontiers.attractor_identity --n-seeds 100 --universality \
    --output results/attractor_investigation.json
```

Output: `results/attractor_investigation.json`, `results/attractor_investigation_summary.md`

---

## Original Investigation (archived)

### Pre-resolution: what it appeared to be

The value 3.169642 appeared in a 40-seed sweep (`experiments/attractor_phase_transition.json`) at depth=3 with finite iteration counts. It passed mpmath.identify() and PSLQ without a match to classical constants, which led to the tentative "novel constant" classification.

### Phase transition (λ sweep — still valid for the regularized case)

L2 regularization delays (but cannot prevent) collapse at depth=3 without proper input clamping:

| λ | Converges to attractor | Converges to target | Notes |
|---|----------------------|----------------|-------|
| 0.000 | 100% | 0% | Full collapse |
| 0.001 | ~50% | ~50% | Phase transition (λ_crit) |
| 0.005 | ~10% | ~90% | Near-full escape |
| 0.010 | 0% | 100% | Full escape |

The λ_crit phenomenon (C4) remains an interesting property of the regularized loss landscape, distinct from the attractor question.
