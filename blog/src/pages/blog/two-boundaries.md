---
layout: ../../layouts/Base.astro
title: "Two Boundaries of ELC"
description: "The elementary logarithmic closure is bounded by two structurally independent obstructions. Classical analysis guards one edge; classical algebra guards the other."
date: "2026-04-23"
author: "Monogate Research"
tag: observation
---

# Two Boundaries of ELC

**Tier: OBSERVATION** (classical theorems; new observation is the joint interpretation)

We recognise **two structurally independent obstructions** that eject a function from the Elementary Logarithmic Closure. They come from completely different branches of mathematics.

## Boundary 1: T01 — the Infinite Zeros Barrier (analytic)

A real function with infinitely many zeros on every compact interval has no finite real EML tree. `sin`, `cos`, `tan` sit outside real ELC because any finite composition of exp, log, and arithmetic over ℝ produces a real-analytic function with only finitely many zeros on any compact set. The barrier is **analytic** — it's about the function as an analytic object on the real line.

Oscillation is the dominant witness: on our 315-equation catalog, φ = P(oscillatory ⇔ outside-ELC) = 1.0 with one off-diagonal (the Dirac delta — not a function).

## Boundary 2: Abel-Ruffini — the Solvability Barrier (algebraic)

Eigenvalues of a general symbolic matrix are roots of its characteristic polynomial:

- **n ≤ 4**: closed-form radical expressions (quadratic, Cardano cubic, Ferrari quartic). Inside ELC.
- **n ≥ 5**: **no radical formula** exists. Abel (1824) and Galois (1832) proved this by showing the symmetric group S₅ is not solvable. General quintic eigenvalues lie **outside ELC**.

The barrier is **algebraic** — the obstruction is the structure of a finite group, not analytic behaviour. Entirely independent of oscillation: a generic 5×5 matrix need not have any sin or cos anywhere, yet its eigenvalues are still outside ELC.

## Why both must coexist

Neither subsumes the other. A generic matrix without trig terms still has n ≥ 5 eigenvalues outside ELC — T01 doesn't catch these. Conversely, sin(x) lies outside ELC by T01 regardless of any polynomial structure. The two obstructions fence the elementary closure from different sides.

Algebraic statement:

> **ELC ⊆ (non-oscillatory closure) ∩ (radically-solvable closure)**

Two classical theorems, two centuries apart, constraining the same complexity class from independent directions.

## What this opens up

If two independent obstructions exist, how many more are there? Candidates we haven't placed in the picture:

- **Lindemann-Weierstrass** (transcendence of π, e) — transcendence obstruction
- **Risch elementarity** (elementary antiderivatives) — integration-closure obstruction
- **Picard-Vessiot** (ODEs solvable in elementary functions) — differential-algebraic obstruction

Each is a theorem about closure under a specific operation; each could in principle eject functions from ELC that survive T01 and Abel-Ruffini. Whether they do, and whether they collapse into each other, is an open structural question we're now pursuing.

## Reproduce

Abel-Ruffini eigenvalue costs for n = 2..5 and the classical solvability argument: `exploration/symbolic-math/determinants_and_matrices.py` (DET-4). Oscillation-boundary evidence for T01: `exploration/batch50b/B21_*`.

---

*Monogate Research (2026). "Two Boundaries of ELC." monogate research blog. https://monogate.org/blog/two-boundaries*
