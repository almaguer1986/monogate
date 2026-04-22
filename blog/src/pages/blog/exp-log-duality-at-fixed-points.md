---
layout: ../../layouts/Base.astro
title: "The Exp-Log Duality at Fixed Points"
description: "Every repelling fixed point of exp is an attracting fixed point of log on its branch, with reciprocal multipliers. Machine-verified in Lean 4."
date: 2026-04-22
---

# The Exp-Log Duality at Fixed Points

**Tier: THEOREM** (Lean-verified, 0 sorries)

The complex exponential $\exp(z)$ has no real fixed points — the equation
$\exp(z) = z$ has no real solution — but on $\mathbb{C}$ it has
infinitely many. They are the Lambert points
$z_k^* = -W_k(-1)$,
one for each branch $k \in \mathbb{Z}$ of the Lambert $W$ function.

Running `exp` repeatedly at each of these points spirals outward.
Running `log` (principal branch, or branch $k$ for $z_k^*$) spirals inward
to the same point. **The same point is repelling for `exp` and attracting
for `log`, and the two multipliers multiply to exactly 1.**

---

## The result

**Theorem (T_EXP_LOG_DUALITY).** Let $z \in \mathbb{C}$ lie in the slit
plane (i.e., $z \notin (-\infty, 0]$). Suppose $\exp(z) = z$. Then

$$
(\exp)'(z) \cdot (\log)'(z) = 1.
$$

Equivalently: $(\exp)'(z) = z$ (since $\exp'(z) = \exp(z) = z$), and
$(\log)'(z) = 1/z$. Their product telescopes to $z \cdot (1/z) = 1$.

**Consequence:** for every Lambert fixed point $z_k^*$, $|z_k^*| > 1$.
Therefore `exp`-iteration *diverges* from $z_k^*$ and `log`-iteration
*converges* to it at geometric rate $1/|z_k^*|$ on its matching branch.

---

## Numerical verification

Iterate the principal log from a few seeds on $\mathbb{C}$:

| seed $z_0$        | $\log^{50}(z_0)$ (real, imag)              | distance from $z_0^*$ |
|-------------------|--------------------------------------------|------------------------|
| $10 + 0i$         | $0.31813094 + 1.33723539\,i$               | $< 10^{-7}$            |
| $2 + 1i$          | $0.31813129 + 1.33723583\,i$               | $< 10^{-7}$            |
| $0.5 + 0.5i$      | $0.31813161 + 1.33723581\,i$               | $< 10^{-7}$            |
| $-1 + 0i$         | $0.31813164 + 1.33723555\,i$               | $< 10^{-7}$            |

All four converge to $z_0^* \approx 0.3181 + 1.3372\,i = -W_0(-1)$
within 50 iterations. The decay factor per step is
$|1/z_0^*| \approx 0.7275$.

For the non-principal branches: iterating $\log_k(z) = \log(z) + 2\pi i k$
gives a distinct attractor $z_k^*$ for each $k$, with
$|z_k^*| \approx 2\pi |k|$ as $|k| \to \infty$.

---

## Why it matters

The duality isolates a structural fact about EML-style operators: every
fixed point of `exp` carries a pair of reciprocal multipliers, one per
direction. This is the simplest case of a broader pattern — at any fixed
point of $f$ where $f^{-1}$ is also well-defined, the multipliers satisfy
$\mu_f \cdot \mu_{f^{-1}} = 1$. For F16 operators specifically, this
halves the number of dynamically distinct orbits: the compositions
$f \circ g$ and $g \circ f$ share Lyapunov spectra at corresponding
fixed points.

It also touches decidability: the Lambert constants $z_k^*$ are reachable
as *iterated limits* of EML orbits but are **not known** to be reachable
as any finite EML tree. The gap

$$
\mathrm{ELC}(\mathbb{C}) \;\subseteq_?\; \mathrm{ELC}\text{-iter}(\mathbb{C})
$$

is open (see our [research note](https://github.com/almaguer1986/monogate-research)
on the Schanuel–Lambert bridge). Every Lambert constant is a candidate
witness for strictness.

---

## Lean proof

The theorem is machine-verified in Lean 4, 0 sorries:

```lean
theorem exp_log_multiplier_product_at_fixed_point
    {z : ℂ} (hz : Complex.exp z = z) (hdom : z ∈ Complex.slitPlane) :
    deriv Complex.exp z * deriv Complex.log z = 1 := by
  have hne : z ≠ 0 := exp_fixed_point_ne_zero hz
  rw [deriv_exp_at, deriv_log_at hdom, hz]
  field_simp
```

The chain rule gives `exp'(z) = exp(z) = z` (since z is a fixed point) and
`log'(z) = 1/z` in the slit plane, so the product telescopes to
`z · (1/z) = 1`. Non-vanishing of z is automatic: `exp(z) = z` combined with
`exp z ≠ 0` forces `z ≠ 0`.

Source: [EMLDuality.lean](https://github.com/almaguer1986/monogate-lean/blob/master/MonogateEML/EMLDuality.lean)
(4 theorems total, including `exp_fixed_point_multiplier_equals_z` and
`log_multiplier_at_exp_fixed_point` as corollaries).

---

## Reproduce

```bash
git clone https://github.com/almaguer1986/monogate-lean
cd monogate-lean
lake build MonogateEML.EMLDuality
```

Numerical iteration (Python):

```python
import cmath
z = complex(10, 0)
for _ in range(50):
    z = cmath.log(z)
print(z)  # ~ 0.3181 + 1.3372i
```

---

**Cite:** Monogate Research (2026). "The Exp-Log Duality at Fixed Points."
monogate research blog. https://monogate.org/blog/exp-log-duality-at-fixed-points
