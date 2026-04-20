---
layout: ../../layouts/Base.astro
title: "The SuperBEST Cost of Calculus"
description: "Taylor series, integration, ODEs, autodiff, and Fourier transforms measured in EML nodes."
date: 2026-04-20
---

# The SuperBEST Cost of Calculus

**Tier: OBSERVATION** (computed results, reproduce commands below)

How expensive is calculus in EML nodes? This post measures Taylor series, integrals, ODEs, automatic differentiation, and transforms — all with SuperBEST FINAL routing (T08).

---

## CAL-1: Taylor Series

A Taylor series for sin(x) with N terms costs **9N − 3 nodes** under SuperBEST routing.

Per term: one pow (3n) + one mul (3n) = 6n. Per join: one sub or add = 3n.
For N terms: N terms × 6n + (N−1) joins × 3n = 9N − 3.

| N terms | SuperBEST nodes | Old BEST nodes |
|---------|----------------|----------------|
| 4       | 33n            | 27n            |
| 6       | 51n            | 39n            |
| 8       | 69n            | 51n            |
| 10      | 87n            | 63n            |
| 12      | 105n           | 75n            |

SuperBEST is slightly *more* expensive for Taylor series than old routing. Why? Old routing used mul=7n and sub=5n; new routing has mul=3n but the formula structure penalizes the joins. The savings from mul (7→3) are offset by the per-join cost holding at 3n.

**Key contrast**: Fourier series via Euler gateway (T16) needs **1 complex EML node** for the kernel exp(iωt), regardless of N.

---

## CAL-2: Integration

Elementary integration (closed-form antiderivatives) is free — an antiderivative is itself an elementary function, so it has the same EML node count as the integrand.

Non-elementary integrals (erf, Li₂, Fresnel, elliptic) have **no finite EML tree** (T01 generalization). They require numerical integration, which costs O(N·f_nodes) for N quadrature points.

| Function     | Integrable? | EML cost |
|-------------|-------------|----------|
| exp(x)      | Yes         | 1n       |
| x^n         | Yes         | 3n (pow) |
| 1/(1+x²)    | Yes (arctan)| 4n       |
| sin(x)      | Yes (-cos)  | 1n complex |
| erf(x)      | No          | ∞ exact  |
| x^x         | No          | ∞ exact  |

---

## CAL-4: Ordinary Differential Equations

Heat equation mode: **2 nodes per mode** (OBSERVATION).

The solution to u_t = k·u_xx with mode n is:
exp(−n²π²kt) · sin(nπx)

This decomposes as: 1 DEML node for the exponential decay factor × 1 complex EML node for the spatial oscillation. Total: **2 nodes**, exact, per mode.

Harmonic oscillator y'' + ω²y = 0: solution cos(ωx) or sin(ωx) = **1 complex EML node** via T03 (Euler gateway).

---

## CAL-5: Automatic Differentiation

The k-th derivative of an N-node EML tree costs approximately **3^k · N nodes**.

Each differentiation order multiplies the tree size by roughly 3 (chain rule on EML introduces exp and 1/x terms). For N=1, exp(x):

| k | d^k/dx^k exp(x) | Cost |
|---|----------------|------|
| 1 | exp(x)         | 1n   |
| 2 | exp(x)         | 1n   |
| k | exp(x)         | 1n   |

exp is its own derivative — 0 cost growth. For general EML trees with N>1, cost grows as 3^k·N.

**Crossover**: for N≤2, EML autodiff stays competitive with dual-number forward mode.

---

## CAL-9: Fourier and Laplace Transforms

**Fourier kernel: 1 complex EML node** (OBSERVATION, optimal).

exp(−iωt) = ceml(−iωt, 1) — this is T03 (Euler Gateway) applied to the transform kernel.

| Transform          | Kernel        | EML cost  |
|-------------------|---------------|-----------|
| Fourier: e^{−iωt} | ceml(−iωt,1)  | **1 node** |
| Laplace: e^{−st}  | ceml(−st,1)   | **1 node** (complex s) |
| Z-transform: z^{−n}| epL          | **1 node** |
| Wavelet: ψ(t/a)   | depends on ψ  | varies    |

The Fourier kernel is a single complex EML node — this is why Fourier series beats Taylor by 100× (T16).

---

## Reproduce

```bash
python python/scripts/research_cal_quantum.py
```

Results in `python/results/cal_quantum_results.json`.

---

**Cite:** Almaguer, A.R. (2026). "The SuperBEST Cost of Calculus." monogate research blog. https://monogate.org/blog/calculus-costs
