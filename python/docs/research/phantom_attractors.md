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
