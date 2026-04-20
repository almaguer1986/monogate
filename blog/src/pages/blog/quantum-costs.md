---
layout: ../../layouts/Base.astro
title: "The SuperBEST Cost of Quantum Mechanics"
description: "Partition functions, time evolution, density matrices, and quantum information geometry measured in matrix EML nodes."
date: 2026-04-20
---

# The SuperBEST Cost of Quantum Mechanics

**Tier: OBSERVATION** (computed, reproduce command below)

Quantum mechanics uses matrix exponentials and matrix logarithms everywhere. This post measures the cost of standard quantum formulas in **matrix EML nodes** — the matrix generalization of EML where exp → expm (matrix exponential) and ln → logm (matrix logarithm).

---

## Matrix EML Operators

The matrix EML family extends scalar EML to square matrices:

| Operator | Formula | Scalar analog |
|---------|---------|--------------|
| meml(A,B) | expm(A) − logm(B) | eml |
| mexl(A,B) | expm(A) · logm(B) | exl |
| mdeml(A,B) | expm(−A) − logm(B) | deml |
| meal(A,B) | expm(A) + logm(B) | eal |

Key constraint: **non-commutativity**. expm(A)·expm(B) ≠ expm(A+B) unless AB = BA. This blocks scalar SuperBEST routing from directly transferring to the matrix case.

---

## Q1: Core Quantum Formula Costs

| Formula | Meaning | Matrix EML nodes |
|---------|---------|-----------------|
| U(t) = exp(−iHt) | Time evolution | **1 node** (meml with 0 offset) |
| Z = Tr(exp(−βH)) | Partition function | **1 node** + Tr |
| ρ(β) = exp(−βH)/Z | Thermal state | 2 nodes |
| S = −Tr(ρ·ln ρ) | von Neumann entropy | **2 mexl nodes** + Tr |
| F = −ln(Z)/β | Free energy | **1 node** + scalar ln |

**Headline**: Time evolution U(t) = exp(−iHt) is a single matrix EML node. This is the quantum analog of T03 (Euler Gateway).

---

## Q2: Non-Commutativity Barrier

Scalar SuperBEST routing for mul(x,y): exp(ln(x) + ln(y)) = x·y.
Matrix analog: expm(logm(A) + logm(B)) ≠ AB in general.

This is a hard barrier — **matrix multiplication cannot be routed through SuperBEST for non-commuting matrices**.

| Operation | Scalar routing | Matrix cost | Why? |
|-----------|---------------|-------------|------|
| AB | 3n via EXL | Full mmul | AB ≠ BA |
| exp(A)·exp(B) | N/A | 2 nodes + mmul | Baker-Campbell-Hausdorff |
| Tr(AB) | 3n + Tr | Tr + mmul | Need full product |

The scalar SuperBEST savings (77% for multiplication) **do not transfer** to non-commuting matrices.

For **commuting matrices** (e.g., diagonal, A = f(H) for same H), SuperBEST routing applies unchanged.

---

## Q3: Precision Verification

Computed at d=2, 3, 4:

| d | Z (partition fn) | S (entropy) | logm error |
|---|-----------------|-------------|-----------|
| 2 | 2.8873 | 0.360188 | 2.3×10⁻¹⁵ |
| 3 | 4.6790 | 0.652474 | 2.1×10⁻¹⁵ |
| 4 | 6.4376 | 0.665785 | 3.9×10⁻¹⁵ |

Matrix logarithm achieves machine precision (∼10⁻¹⁵). Von Neumann entropy computed exactly via mexl.

---

## Q4: Quantum Information Geometry

| Formula | Operations | Matrix EML nodes |
|---------|-----------|-----------------|
| Bures distance | 4 msqrt + 4 mmul + Tr | 12 ops |
| Quantum rel. entropy | 2 mexl + msub + mmul + Tr | 9 ops |
| QFI (SLD) | Sylvester eq + 3 mmul + Tr | 15 ops |
| Matrix sqrt A^{1/2} | 1 mexl + 1 meml | **2 matrix EML ops** |
| Fisher-Rao (classical) | div+pow+mul+add+integral | ~7 scalar nodes |

**Matrix sqrt in 2 matrix EML ops**: A^{1/2} = expm(logm(A)/2) = mexl(logm(A)/2, I) decomposed as 2 matrix operations.

---

## Reproduce

```bash
python python/scripts/research_cal_quantum.py
```

Results in `python/results/cal_quantum_results.json` under keys `Q1`, `Q2`, `Q3`, `Q4`.

---

**Cite:** Almaguer, A.R. (2026). "The SuperBEST Cost of Quantum Mechanics." monogate research blog. https://monogate.org/blog/quantum-costs
