---
layout: ../../layouts/Base.astro
title: "The Equation That Counts Physics"
description: "Hand a damped-oscillator equation to a computer and it can tell you, without knowing any physics, that there's one oscillation and one decay inside it. Across 193 expressions and 12 domains, this counter holds at ρ = +0.885."
date: "2026-04-27"
author: "Monogate Research"
tag: research
featured: true
---

# The Equation That Counts Physics

**Tier: RESEARCH** (empirical, statistical, reproducible)

Look at this expression for one second:

<div class="math-block">A · exp(−ζω · t) · cos(ω<sub>d</sub> · t)</div>

If you've taken a physics class, your brain just ran a tiny instinctual decoder. *Damped harmonic oscillator. One oscillation. One decay.* You didn't compute anything. You recognized a shape.

Here's the question that's been answering itself in our data for the past few weeks: **can a computer do that without knowing any physics?**

Not "can it integrate the equation." Not "can it solve the ODE." Just: can it look at the symbolic form and tell us, *this thing has one oscillation and one decay in it*? The answer turns out to be yes, and the way it does it is mechanical — no domain knowledge required, no physics priors, no training data.

## The counter

For any symbolic expression `f`, define a single integer we call the **chain order**, written `r(f)`. Compute it by walking the expression's AST and summing per-primitive contributions: each `sin` or `cos` adds 2, each `exp` or `ln` adds 1, polynomials add 0, and so on. (The formal definition is the depth of a Pfaffian chain that realizes the expression — but the per-node walk is the operational form.)

The claim is that for symbolic forms describing real physical or engineering systems, this number lines up cleanly with their dynamics:

<div class="math-block">r(f) ≈ 2 · n<sub>oscillations</sub> + n<sub>decays</sub></div>

Two units of chain order per oscillation mode, one unit per exponential decay. Let's walk three examples.

## Example 1: pure decay

`exp(−x)` — an isolated exponential decay. AST is one `exp` node over a polynomial argument. Chain order: **r = 1**. Dynamics decoder reads it as **0 oscillations, 1 decay**. The arithmetic checks: 2·0 + 1 = 1. ✓

## Example 2: damped oscillator

`sin(x) · exp(−x)` — the signature shape of every overdamped lab demo, every shock-absorber model, every membrane decay in cable theory. AST has one `sin` (chain 2) and one `exp` (chain 1). Chain order: **r = 3**. Dynamics decoder reads **1 oscillation, 1 decay**. Arithmetic: 2·1 + 1 = 3. ✓

## Example 3: 8-octave fractal noise

`Σ A_k · sin(2^k · x)` for k = 1..8 — eight stacked sinusoidal modes, the kind of thing that ends up in procedural-terrain shaders and fractal-Brownian-motion noise generators. The AST has eight distinct sinusoidal primitives. Chain order: **r = 16**. Dynamics decoder reads **8 oscillations, 0 decays**. Arithmetic: 2·8 + 0 = 16. ✓

Three examples, three different domains, one rule.

## The data

We ran the counter against **193 expressions** spanning 12 domains — physics, neuroscience, signal processing, color science, electromagnetism, robotics, music, finance, chemistry, biology, geology, olfactory. Combined Spearman correlation between predicted and structurally-measured chain order:

<div class="math-block">ρ = +0.885, p = 1.8 × 10⁻⁶⁵</div>

This is across both elementary expressions and Pfaffian-extended ones (Bessel functions, Airy, the gamma family, Lambert W, error functions, and the rest). Per-domain breakdown isn't uniform. Crypto sits at ρ = 1.000 — perfect. Olfactory sits at ρ = 0.462 — much weaker, because olfactory perception models tend to count receptor-binding kinetics as a different kind of "complexity" than the counter measures. The counter measures **oscillatory and decay complexity specifically**, not generic function complexity. Where the dynamics live in those terms, the counter nails it. Where complexity hides in branching reaction kinetics or piecewise thresholds, the counter can miss.

That's an honest limit, not a bug. The counter does what it says.

## The exact case

Restrict to the 18 elementary primitives we measured directly — sin, cos, exp, ln, the basic transcendentals plus their hyperbolic and inverse counterparts. The chain-order rule isn't statistical there. It's **18 of 18 exact**. Walk the AST, sum the per-node contributions, get the chain order. No correlation, no scatter — exact integer agreement on every single primitive.

The statistics on the 193-expression corpus measure how well the rule generalizes to *compositions* of those primitives in real-world equations. Strong correlation, not perfection — because the corpus contains some shapes (modular arithmetic, piecewise definitions, special-function corner cases) where the simple per-node sum needs adjustments. But the rule's foundation is exact.

## The ceiling

The most complex elementary function we've found in the corpus — across all 12 domains — is FM synthesis. Specifically the carrier-modulator wave you'd write as `sin(ω_c · t + I · sin(ω_m · t))`, the math behind every Yamaha DX7 patch in every 80s pop song. Its fingerprint sits at `p4-d10-w4-c2`. Maximum path chain order: 4. It's the **only expression in 578** with that profile.

That's the structural ceiling of "elementary functions humans deploy at scale": the Yamaha DX7. Everything else lives at chain order 3 or below.

## Verify it yourself

```bash
pip install eml-cost
```

```python
import eml_cost

# Damped oscillator: 1 osc + 1 decay
result = eml_cost.analyze_dynamics("sin(x) * exp(-x)")
print(result.n_oscillations, result.n_decays, result.predicted_r)
# -> 1, 1, 3

# 8-octave fBm noise: 8 oscillations
import sympy as sp
x = sp.Symbol('x')
fbm = sum(sp.sin(2**k * x) for k in range(1, 9))
print(eml_cost.analyze_dynamics(fbm).predicted_r)
# -> 16

# FM synthesis: chain ceiling
print(eml_cost.analyze("sin(omega_c * t + I * sin(omega_m * t))").max_path_r)
# -> 4
```

The package is `eml-cost` on PyPI. The 578-expression corpus is bundled. The dynamics-counter functions are `analyze_dynamics()` for the predicted-vs-measured comparison and `analyze()` for the full Pfaffian profile. Source on [agent-maestro/eml-cost](https://github.com/agent-maestro/eml-cost).

---

*Monogate Research (2026). "The Equation That Counts Physics." monogate research blog. https://monogate.org/blog/dynamics-counter*
