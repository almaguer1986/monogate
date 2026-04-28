---
layout: ../../layouts/Base.astro
title: "One Operator, All of Applied Mathematics"
description: "The NAND gate of continuous math. A single binary operation eml(x, y) = exp(x) − ln(y) generates every elementary function — and the structural fingerprint of an expression turns out to predict where it came from."
date: "2026-04-27"
author: "Monogate Research"
tag: announcement
featured: true
---

# One Operator, All of Applied Mathematics

**Tier: ANNOUNCEMENT** (overview of public results)

In digital logic, NAND is universal — a single two-input gate composes into every Boolean circuit. AND, OR, NOT, XOR, the entire silicon stack: all of it falls out of NAND wired up enough times. One gate. Every circuit.

Continuous mathematics has the same property, and it's been hiding in plain sight. Define one binary operator:

<div class="math-block">eml(x, y) = exp(x) − ln(y)</div>

Then `exp(x) = eml(x, 1)`. Addition is `eml`-derived. `sin` falls out via Euler. So does every elementary function you've ever seen — every `cos`, `tan`, `sinh`, `log`, polynomial, rational, every composition that doesn't involve a special function. One operator, every formula.

## The 23-operator census

We tested every binary combination of `exp(±x)` with `ln(y)` through arithmetic — every shape `op₁(op₂(x), op₃(y))` you could write down. Sixteen turn out to be **complete** in the formal sense: each one alone generates the elementary closure. Seven are structurally impossible (the wrong sign combination forces undefined branches). Layer-2 extensions like `LEAd(x, y) = ln(exp(x) + y)` round the working set to 23 operators — every entry classified, the closure proved by exhaustion.

The interesting part isn't that the operator works. It's what falls out of measuring real expressions through it.

## The structural fingerprint

Every expression in our corpus gets a four-axis profile:

- **p** — the polynomial degree component
- **d** — the routing depth (the EML tree's height)
- **w** — the weight (a count of multiplicative complexity)
- **c** — the chain order (a Pfaffian-flavored measure of transcendental nesting)

A corpus of **578 expressions** spanning 12 domains — physics, neuroscience, signal processing, color science, finance, chemistry, robotics, music, olfactory, geology, electromagnetism, biology — all profiled. The fingerprint is mechanical: feed an expression through `eml-cost`, get back its four numbers.

## What the fingerprints reveal

The headline cross-domain class is `p2-d5-w2-c1`. **38 expressions** sit there. They include:

- Faraday's EMF: `B · ω · cos(ω · t)` (electromagnetism)
- Hodgkin-Huxley membrane current's oscillatory term (neuroscience)
- HSL → RGB conversion's sinusoidal blend (color science)
- The Shannon sinc filter `sin(πx)/(πx)` (signal processing)

Same fingerprint. Different fields, different equations, different pencils on different blackboards a century apart. Statistical enrichment for the class is **2.43× over the null** at q=1.49×10⁻⁴ across **18 distinct subdomains**.

This isn't "they're all sinusoidal." Plenty of sinusoids in the corpus sit in *other* classes. The four-axis fingerprint is finer-grained than that — it picks out a structural family that the human eye doesn't.

## Why this matters

If you've ever looked at a new equation in an unfamiliar field and felt the strange déjà vu of "I've seen this shape before," there's now a way to make that intuition computable. Expression fingerprints are deterministic. They don't care about variable names, units, or domain conventions. They identify structural cousins across fields without needing a human to spot the analogy.

The flip side is even more concrete: if you're optimizing an expression — a shader, a control loop, a stability-sensitive numerical kernel — the fingerprint tells you which structural family you're in, and the structural family has a known cost. You don't have to discover the optimization. You look it up.

## Verify it yourself

```bash
pip install eml-cost
```

Then:

```python
import eml_cost

# Faraday's EMF
print(eml_cost.analyze("B * omega * cos(omega * t)").cost_class)
# -> p2-d5-w2-c1

# Shannon sinc filter
print(eml_cost.analyze("sin(pi * x) / (pi * x)").cost_class)
# -> p2-d5-w2-c1

# Find every sibling in the corpus
for sib in eml_cost.find_siblings("B * omega * cos(omega * t)"):
    print(f"  {sib.name:40s} {sib.domain}")
```

That last command walks the 578-expression corpus and prints every structural sibling. Different fields, same fingerprint.

The package is on PyPI (`eml-cost`), the source on GitHub at [agent-maestro/eml-cost](https://github.com/agent-maestro/eml-cost), and the foundational paper is on arXiv ([arXiv:2603.21852](https://arxiv.org/abs/2603.21852)). One operator. Every elementary function. Fingerprints that travel across fields.

---

*Monogate Research (2026). "One Operator, All of Applied Mathematics." monogate research blog. https://monogate.org/blog/one-operator*
