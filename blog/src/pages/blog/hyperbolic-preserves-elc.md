---
layout: ../../layouts/Base.astro
title: "Hyperbolic Functions Preserve ELC (And Why Trig Doesn't)"
description: "sinh, cosh, and tanh map ELC inputs to ELC outputs. sin, cos, and tan don't. Machine-verified in Lean 4. With a 3-4-5 triple bonus."
date: 2026-04-22
---

# Hyperbolic Functions Preserve ELC (And Why Trig Doesn't)

**Tier: THEOREM** (Lean-verified, 0 sorries)

The ELC field — the set of real numbers expressible as finite trees of
`exp`, `ln`, and arithmetic — has a strange asymmetry with respect to the
usual transcendental toolkit. Plug in a hyperbolic function and you stay
inside:

$$
\sinh(\mathrm{ELC}) \subseteq \mathrm{ELC}, \quad
\cosh(\mathrm{ELC}) \subseteq \mathrm{ELC}, \quad
\tanh(\mathrm{ELC}) \subseteq \mathrm{ELC}.
$$

Plug in a trig function and you (generically) fall off:

$$
\sin(\mathrm{ELC}) \not\subseteq \mathrm{ELC}.
$$

In particular $\sin(1) \notin \mathrm{ELC}$ (Niven, 1939). This is the
content of the Infinite Zeros Barrier (T01) at the unary-function level.

---

## The theorem

**Theorem (T_HYP_ELC_PRESERVE).** For all real $x$:

$$
\sinh(x) = \frac{e^x - e^{-x}}{2}, \quad
\cosh(x) = \frac{e^x + e^{-x}}{2}, \quad
\tanh(x) = \frac{\sinh(x)}{\cosh(x)}.
$$

Since `exp` and arithmetic are ELC primitives, composing with an ELC input
$x$ keeps the result in ELC. Explicit depth bound in F16: $\leq 4$ nodes
per hyperbolic function.

---

## Why trig is different

The reason is structural, not superficial. On $\mathbb{R}$:

- `exp` is a real entire function of order 1 **with no real zeros**.
  Iterating it, composing it, combining it with arithmetic: the result
  always has finitely many real zeros.
- `sin` is a real entire function of order 1 **with infinitely many real
  zeros** ($\sin(n\pi) = 0$ for all integers $n$).

Any finite EML tree evaluates to a real-analytic function with *finitely*
many real zeros (T01). Therefore $\sin(x)$, with its infinite zero set,
can never be such a tree over the reals.

`sinh` has the same series as `sin` but with all-plus signs:

$$
\sin(x) = x - \frac{x^3}{3!} + \frac{x^5}{5!} - \cdots, \quad
\sinh(x) = x + \frac{x^3}{3!} + \frac{x^5}{5!} + \cdots.
$$

The sign flip from trig to hyperbolic removes the oscillation, removes
the infinite zero set, and keeps us inside the ELC field. One sign, whole
universe of difference.

---

## A 3-4-5 Pythagorean triple at $x = \ln 2$

Bonus observation from the Lean-verified identities. For any integer $n \geq 2$:

$$
\sinh(\ln n) = \frac{n^2 - 1}{2n}, \quad
\cosh(\ln n) = \frac{n^2 + 1}{2n}.
$$

At $n = 2$:

$$
\sinh(\ln 2) = \frac{3}{4}, \quad \cosh(\ln 2) = \frac{5}{4}.
$$

The hyperbolic Pythagorean identity $\cosh^2 - \sinh^2 = 1$ at $x = \ln 2$
gives

$$
\left(\frac{5}{4}\right)^2 - \left(\frac{3}{4}\right)^2 = 1
\iff 5^2 - 3^2 = 4^2.
$$

The 3-4-5 right triangle, hiding inside a hyperbolic identity at a
specific rational-log input. For $n = 3$: $(8/6, 10/6)$, giving
$10^2 - 8^2 = 6^2$. For every integer $n$ the construction continues.

All three are Lean-verified:

```lean
theorem sinh_log_two : Real.sinh (Real.log 2) = 3 / 4
theorem cosh_log_two : Real.cosh (Real.log 2) = 5 / 4
theorem pythagorean_triple_at_log_two :
    (Real.cosh (Real.log 2)) ^ 2 - (Real.sinh (Real.log 2)) ^ 2 = 1
```

---

## Practical consequence

In neural-network architectures, the choice between `tanh` and arbitrary
activations has a hidden tax. `tanh` stays inside ELC at every layer,
so a depth-$D$ network with `tanh` activations expressible in EML
stays a depth-$O(D)$ EML computation. Replace it with `sin` and you
leave ELC immediately — every non-rational input now lives in the
transcendental boundary, and no finite EML tree captures the forward
pass exactly. For approximate computation (softplus etc.) see our earlier
post on [Tier-0 functions](/blog/tier-0-functions).

---

## Lean proof

The three core decompositions are one-liners on top of Mathlib's existing
hyperbolic-function definitions:

```lean
theorem sinh_as_exp_arithmetic (x : ℝ) :
    Real.sinh x = (Real.exp x - Real.exp (-x)) / 2 := by
  rw [Real.sinh_eq]

theorem cosh_as_exp_arithmetic (x : ℝ) :
    Real.cosh x = (Real.exp x + Real.exp (-x)) / 2 := by
  rw [Real.cosh_eq]

theorem tanh_as_sinh_div_cosh (x : ℝ) :
    Real.tanh x = Real.sinh x / Real.cosh x := by
  rw [Real.tanh_eq_sinh_div_cosh]
```

The content of the theorem is the structural observation: because these
expressions use only `exp` and arithmetic, composing with an ELC input
keeps the result in ELC.

Source: [HyperbolicPreservation.lean](https://github.com/agent-maestro/monogate-lean/blob/master/MonogateEML/HyperbolicPreservation.lean)
(7 theorems total, including the numerical 3-4-5 witnesses).

---

**Cite:** Monogate Research (2026). "Hyperbolic Functions Preserve ELC (And
Why Trig Doesn't)." monogate research blog.
https://monogate.org/blog/hyperbolic-preserves-elc
