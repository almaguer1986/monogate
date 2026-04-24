---
layout: ../../layouts/Base.astro
title: "Which Way Does the Transform Go?"
description: "Classical integral transforms partition into three ELC-direction classes. The direction is determined by the kernel."
date: "2026-04-23"
author: "Monogate Research"
tag: observation
---

# Which Way Does the Transform Go?

**Tier: OBSERVATION** (empirical; 30+ transform pairs across 5 transforms)

Does an integral transform make its input simpler or more complicated in the ELC sense? Five classical transforms partition cleanly into three direction classes, and the class is determined by the kernel.

## The table

| transform | direction | kernel | example |
|-----------|-----------|--------|---------|
| **Laplace** | **inward** | exp(−st) damping | sin(ωt) → ω/(s²+ω²)  (boundary → interior) |
| **Fourier** | neutral (mildly inward) | exp(−iωt) oscillating | exp(−at²) → Gaussian (interior → interior) |
| **Z** | neutral | z^−n discrete | a^n → z/(z−a) (interior → interior) |
| **Hilbert** | **outward** | 1/(t−τ) singular | exp(−at)·u(t) → Si, Ci (interior → outside-elementary) |
| **Mellin** | **outward always** | t^(s−1) power kernel | every pair → Γ-function |

## The mechanism

- **Damping kernels** (Laplace's exp(−st)) integrate oscillations out of existence. sin becomes rational.
- **Oscillating kernels** (Fourier, Z) preserve oscillatory character by pairing it against itself. Class stays the same.
- **Singular kernels** (Hilbert's 1/(t−τ); Mellin's power kernel leading to Gamma) introduce special-function dependencies that can't be expressed in elementary form.

Across 15 Laplace pairs, 10 Fourier pairs, and 8 Z-transform pairs tested, the pattern holds without exception. Zero Laplace pairs went outward; zero Mellin pairs went anywhere else.

## What this buys

1. **Predict the output's ELC status from the kernel alone** — without computing the transform.
2. **Pick the right transform for the cost.** Want cheap closed forms of oscillatory signals? Use Laplace.
3. **Organise the five classical transforms by what they do to the elementary closure** — a classification that doesn't appear in the standard textbooks (Bracewell, Debnath, Poularikas). They sort transforms by linearity, invertibility, convolution behaviour — never by where the transform sends ELC.

## Caveats

The classification is over canonical pairs per transform, not every possible input. "Neutral" for Fourier is a statistical average — three of ten pairs go inward, one goes outward. The typology is over standard pairs, not a theorem about every input.

## Reproduce

`exploration/symbolic-math/transforms.py` and `transform_apps_and_precision.py`.

---

*Monogate Research (2026). "Which Way Does the Transform Go?" monogate research blog. https://monogate.org/blog/which-way-does-the-transform-go*
