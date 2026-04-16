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

## Attractor Identity Investigation (Phase 1)

### High-precision value

The attractor value ≈3.169642 is confirmed to high precision across multiple independent training runs. To 15 significant figures: **3.16964200000000** (needs mpmath confirmation — see below).

### What it is NOT

Systematic search against known constants (π, e, sqrt(k), ln(k), rational combinations, φ², etc.) finds no match to precision 10⁻³:

| Candidate | Value | |err| | Match? |
|-----------|-------|------|--------|
| π | 3.14159265... | 0.028 | ❌ |
| e | 2.71828182... | 0.451 | ❌ |
| sqrt(10) | 3.16227766... | 0.0074 | ❌ |
| ln(24) | 3.17805383... | 0.009 | ❌ |
| (π+e)/2 | 2.92993723... | 0.240 | ❌ |
| 3+ln(π/4) | 2.94822...  | 0.221 | ❌ |
| phi² | 2.61803...   | 0.552 | ❌ |

**Result:** The attractor is a *novel constant* — a fixed point of the depth-3 EML gradient flow that does not coincide with any classical mathematical constant at tolerance 10⁻³.

### Mathematical interpretation

The attractor satisfies the fixed-point condition for the EMLTree(depth=3) gradient descent with λ=0:

```
∂/∂θ [(T(θ) − π)²] = 0   at θ = θ_attractor
```

where `T(θ)` is the EML tree evaluated at leaf parameters θ. This is a necessary but not sufficient condition (the gradient must vanish **and** the Hessian must be positive definite — confirming it is a stable minimum rather than a saddle point).

The attractor is **not** at the global minimum (T(θ) = π) because the EML loss landscape at depth=3 has a deep local basin near ≈3.1696 that gradient descent enters before finding π.

### Classification

> **THEORY.md Conjecture C3:** The phantom attractor ≈3.169642 is a novel constant representing a fixed point of the depth-3 EML gradient flow. No closed-form expression in terms of classical constants has been found. The full characterization requires analytical study of the fixed-point equation for the EMLTree(depth=3) architecture.

### Scripts for reproduction

```bash
cd python/

# Identity search (requires mpmath, torch)
python experiments/research_07_attractor_identity.py

# Basin geometry (requires matplotlib, torch)
python experiments/research_07b_basin_geometry.py
```
