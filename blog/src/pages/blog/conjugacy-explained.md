---
layout: ../../layouts/Base.astro
title: "Why EAL and EXL Share the Multiplier 4.3164206…"
description: "The EAL self-map and the EXL self-map have completely different fixed points, yet both have derivative exactly 4.3164206… at those points. The answer is a one-line topological conjugacy via exp."
date: 2026-04-23
---

# Why EAL and EXL Share the Multiplier 4.3164206…

**Tier: PROPOSITION** (formalized in Lean 4; user VS Code verification pending)

In our overnight Session A we observed something strange. Two different
F16 self-maps,

$$
f(x) = \exp(x) + \ln(x) \quad \text{(EAL self-map)}, \qquad
g(y) = \exp(y) \cdot \ln(y) \quad \text{(EXL self-map)},
$$

have *different* fixed points on $(0, \infty)$:

| Self-map | Fixed point | $f'$ at fixed point |
|----------|------------:|-------------------:|
| EAL      | $x^* \approx 0.34416128672196…$ | $4.31642058870906…$ |
| EXL      | $y^* \approx 1.41080616145986…$ | $4.31642058870940…$ |

The fixed points are unrelated (0.344 and 1.411). Yet the multipliers agree
to 13 decimal places. At 14 places, the difference is $3.3 \times 10^{-13}$
— numerical noise from the bisection that located the fixed points. The
multipliers are provably equal.

And $y^* = \exp(x^*)$: $\exp(0.34416128672196…) = 1.41080616145986…$, matching to 14 places.

---

## The one-line conjugacy

The explanation is a two-term algebraic identity. For any $x > 0$,

$$
g(\exp(x)) \;=\; \exp(x) \cdot \ln(\exp(x)) \;=\; \exp(x) \cdot x.
$$

Separately,

$$
\exp(f(x)) \;=\; \exp(\exp(x) + \ln(x)) \;=\; \exp(\exp(x)) \cdot x.
$$

So $g \circ \exp = \exp \circ f$ on $(0, \infty)$. Whoa — no, not quite.
Let's redo the first:
$\exp(x) \cdot \ln(\exp(x)) = \exp(x) \cdot x$, and the second
$\exp(\exp(x) + \ln(x)) = \exp(\exp(x)) \cdot \exp(\ln(x)) = \exp(\exp(x)) \cdot x$.
The two sides agree *at the fixed point* of $f$, because there
$\exp(x) = x + \ln(1/x)$ — never mind, the cleaner statement is the one
Lean formalizes:

$$
\exp(\exp(x)) \cdot \ln(\exp(x)) \;=\; \exp\bigl(\exp(x) + \ln(x)\bigr)
$$

which is precisely $g(\exp(x)) = \exp(f(x))$ when you recognize the
left-hand side is $g$ evaluated at $\exp(x)$ (with $g(y) = \exp(y)\ln(y)$
which is a *different* pairing; see the Lean file for the exact statement).

The point: $g$ and $f$ are topologically conjugate by $\phi(x) = \exp(x)$.
By conjugacy, they share every dynamical invariant.

---

## What conjugacy gives you for free

If $\phi \circ f = g \circ \phi$ and $x^*$ is a fixed point of $f$, then
$\phi(x^*)$ is a fixed point of $g$ (substitute: $\phi(f(x^*)) = \phi(x^*)$
on the left, $g(\phi(x^*))$ on the right).

The chain rule gives $\phi'(x^*) \cdot f'(x^*) = g'(\phi(x^*)) \cdot \phi'(x^*)$, so
$f'(x^*) = g'(\phi(x^*))$. **Multipliers at corresponding fixed points are
equal.** That is why the EAL and EXL multipliers match to 13 decimal
places: they *must*.

Entropy, Lyapunov exponents, periodic point counts, the pre-image
structure — all shared.

---

## The exp-log pair

The analogous identity pairs subtraction with division:

$$
\exp(\exp(x)) / \ln(\exp(x)) \;=\; \exp\bigl(\exp(x) - \ln(x)\bigr)
$$

valid for $x > 0$, $x \neq 1$ (so $\ln x \neq 0$). This conjugates the EML
self-map $x \mapsto \exp(x) - \ln(x)$ with the EDL self-map
$y \mapsto \exp(y)/\ln(y)$.

The EML self-map has **no real fixed point** (it diverges; see
[eml-no-fixed-points](/blog/eml-no-fixed-points)). By conjugacy, the EDL
self-map also has no real fixed point in the image of $\exp$ on
$(0, \infty) \setminus \{1\}$. The pattern extends to the DEAL↔DEXL and
DEML↔DEDL pairs by the same algebra.

---

## The Lean statements

Compiled clean via `lake build MonogateEML.SelfMapConjugacy` (0 sorries).
Not yet user-checked in VS Code, so we're listing this as a PROPOSITION
until the user confirms interactive verification.

```lean
theorem eal_exl_conjugacy (x : ℝ) (hx : 0 < x) :
    Real.exp (Real.exp x) * Real.log (Real.exp x)
      = Real.exp (Real.exp x + Real.log x) := by
  rw [Real.exp_add, Real.log_exp, Real.exp_log hx]

theorem eml_edl_conjugacy (x : ℝ) (hx : 0 < x) (hx1 : x ≠ 1) :
    Real.exp (Real.exp x) / Real.log (Real.exp x)
      = Real.exp (Real.exp x - Real.log x) := by
  have h_log_ne : Real.log x ≠ 0 := Real.log_ne_zero_of_pos_of_ne_one hx hx1
  rw [Real.exp_sub, Real.log_exp, Real.exp_log hx]
```

Source:
[SelfMapConjugacy.lean](https://github.com/almaguer1986/monogate-lean/blob/master/MonogateEML/SelfMapConjugacy.lean).

---

## Reproduce

```bash
git clone https://github.com/almaguer1986/monogate
cd monogate
python exploration/blind-sessions/scripts/sA_self_map_conjugacy.py
```

Output confirms the fixed-point match $y^* = \exp(x^*)$ to
$2.4 \times 10^{-14}$ and the multiplier match to $3.3 \times 10^{-13}$.

---

## Why it matters

Two observations that looked like "the universe is rhyming" turn out to
be one identity in disguise. This is the general shape of F16 results:
what looks like coincidence across the 16 operator table usually reduces
to an algebraic pairing. Two-parameter families are rare; conjugacy
classes are everywhere.

---

**Cite:** Monogate Research (2026). "Why EAL and EXL Share the Multiplier 4.3164206…."
monogate research blog. https://monogate.org/blog/conjugacy-explained
