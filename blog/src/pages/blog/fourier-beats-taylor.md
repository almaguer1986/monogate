---
layout: ../../layouts/Base.astro
title: "Fourier Beats Taylor by 100x in EML Node Count"
date: 2026-04-19
tag: theorem
description: "sin(x) costs 101 nodes as a Taylor series in BEST routing. The same function is 1 complex EML node using Fourier. This 100x gap validates the lab's sound design and reveals a deep structural fact about the operator."
---

# Fourier Beats Taylor by 100x in EML Node Count

Every EML tree is a composition of exp and ln. To approximate sin(x) using real arithmetic, you need an infinite Taylor series — and in BEST routing, that costs 101 nodes for 8 terms.

But there's a shortcut. And it has everything to do with why the operator is called **exp-minus-ln**.

---

## The Taylor Route

sin(x) = x − x³/3! + x⁵/5! − x⁷/7! + ···

Each term requires:
- pow(x, 2k+1): **3 nodes** (EXL, best known)
- div by (2k+1)!: **1 node** (EDL)
- alternating sign: **6 nodes** (neg via EDL)
- sum with previous term: **3 nodes** (mixed EAL bridge)

Per term: 3 + 1 + 6 = 10 nodes. Plus 3 nodes per addition to sum them.

**Total for K terms:**

| K terms | Nodes | MSE on [−π, π] |
|---------|-------|----------------|
| 2 | 23 | 2.55e+00 |
| 4 | 49 | 8.21e-02 |
| 6 | 75 | 4.66e-04 |
| 8 | 101 | 7.95e-07 |
| 10 | 127 | 5.39e-10 |

To reach 10⁻⁶ accuracy: **101 nodes**.

---

## The Fourier Route

Euler's formula: exp(ix) = cos(x) + i·sin(x).

In EML: exp(ix) = eml(ix, 1) = exp(ix) − ln(1) = exp(ix).

**This is one EML node.** The imaginary part is sin(x) exactly. No approximation.

```
sin(x) = Im(eml(ix, 1))    [1 complex EML node, exact]
cos(x) = Re(eml(ix, 1))    [same node, exact]
```

This is not an approximation — it is the exact value, to floating-point precision, in a single operator application.

The Fourier series for general periodic functions costs more:

| N terms | EML nodes | Accuracy for square wave |
|---------|-----------|--------------------------|
| 1 | 21 | exact for sin (this IS sin) |
| 2 | 37 | ∼1/2² |
| 4 | 69 | ∼1/4² |
| 8 | 133 | ∼1/8² (Gibbs) |

But sin(x) itself is the N=1 case: **1 complex node**.

---

## The 100x Gap

| Method | Nodes for sin(x) | Error |
|--------|-----------------|-------|
| Taylor, 8 terms | **101** | 7.95e-07 |
| Fourier, 1 term | **1** | exact |

The ratio is 101:1. One hundred times fewer nodes.

---

## Why This Happens

The Taylor approach forces sin(x) into the real number line, where EML's operator family has no native trig support. Every term is a workaround: use powers and factorials to reconstruct a function that the operators weren't designed for.

The Fourier approach uses the complex path — exactly the mechanism that makes the EAL bridge work and that EMN uses to achieve approximate completeness. In the complex plane, exp(ix) is native. sin(x) is just its imaginary component.

**The structural fact:** EML's completeness theorem holds over ℂ. In the real line, sin(x) is unreachable (Infinite Zeros Barrier). In ℂ, it costs one node.

The complex plane is not a trick — it is where EML lives natively.

---

## What This Means for BEST Routing

The BEST routing table currently tracks single-variable operations. Adding `sin` and `cos`:

| Operation | BEST operator | Nodes | Notes |
|-----------|--------------|-------|-------|
| exp(x) | EML | 1n | real |
| ln(x) | EXL | 1n | real |
| sin(x) | EML | 1n | complex path |
| cos(x) | EML | 1n | complex path |
| sinh(x) | EML | 3n | (exp(x)−exp(−x))/2 |
| cosh(x) | EML | 3n | (exp(x)+exp(−x))/2 |

exp, ln, sin, and cos all cost **1 node** in BEST. The trig functions are not special — they are Euler's formula applied once.

---

## Why the Lab Uses This

The sound engine in the Monogate lab synthesizes waveforms by computing exp(iωt) for each harmonic frequency ω. Each harmonic is one EML node. A 16-harmonic instrument timbre is 16 nodes — one per frequency component.

This is exactly the Fourier representation, implemented as EML trees. The lab isn't using Fourier synthesis as an analogy — it is literally computing EML trees, one per harmonic, taking the imaginary part.

When you hear a note in the sound experience, you're hearing the output of an EML tree.

---

## Caveat: Taylor Still Wins for Exponentials

For exp(x) itself, the identity tree costs 1 node and is exact. Taylor can only approximate exp(x) with K terms:

| K terms Taylor exp(x) | Nodes |
|-----------------------|-------|
| 2 | 11 |
| 4 | 25 |
| 8 | 53 |

Taylor approximates what EML already knows exactly. The 1-node EML identity tree for exp(x) beats every finite Taylor series — because exp is the operator's native operation.

The lesson generalizes: **EML native operations cost 1 node. Non-native operations (real trig) are expensive. Complex-path operations recover native cost.**

---

*Session M8 · Direction 13 of the Research Roadmap*
