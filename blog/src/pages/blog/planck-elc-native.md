---
layout: ../../layouts/Base.astro
title: "Planck Radiation Is ELC-Native (No Trig Needed)"
description: "Six canonical electromagnetic formulas costed in F16 nodes. Planck's radiation law sits entirely inside the exp-log closure — unlike wave equations, which must cross to complex EML for cos. A double-angle identity inflates cost."
date: 2026-04-23
---

# Planck Radiation Is ELC-Native (No Trig Needed)

**Tier: OBSERVATION** (measurement; no new proofs)

Electromagnetic physics is a surprisingly mixed bag when you measure it in
F16 nodes. The wave equation and the Poynting vector are *boundary* formulas
— they live just outside $\mathrm{ELC}(\mathbb{R})$ because they call $\cos$,
and $\cos$ is blocked on the reals by the Infinite Zeros Barrier. You pay for
them by crossing to complex EML: one complex node per $\cos$ invocation via
Euler's formula. Thermal radiation is different. The Planck spectrum
$B(\nu, T)$ uses only $\exp$, multiplication, division, and subtraction. It
is an entirely ELC-native formula.

---

## Six formulas, measured

Using v5.2 positive-domain F16 costs ($\mathrm{mul}=1n$, $\mathrm{exp}=1n$,
$\mathrm{ln}=1n$, $\mathrm{div}=2n$, $\mathrm{sqrt}=1n$ via
$\mathrm{EPL}(0.5,x)$, $\mathrm{sub}=2n$):

| Formula | Nodes | Class |
|---------|------:|:------|
| photon energy $E = hc/\lambda$ | 3 | inside ELC |
| skin depth $\delta = \sqrt{2/(\omega\mu\sigma)}$ | 5 | inside ELC |
| Planck radiation $B(\nu,T) = \dfrac{2h\nu^3/c^2}{\exp(h\nu/kT)-1}$ | 14 | **inside ELC** |
| EM energy density $u = \tfrac{1}{2}\varepsilon_0 E^2 + \tfrac{1}{2\mu_0}B^2$ | 10 | inside ELC |
| damped EM wave $E_0 e^{-\alpha x}\cos(kx-\omega t)$ | 8 | boundary (needs $\cos$) |
| Poynting $S = E_0 B_0 \cos^2(kx-\omega t)/\mu_0$ (cos·cos form) | 10 | boundary |
| Poynting via $\cos^2 = (1+\cos 2\theta)/2$ | 14 | boundary |

(Inside-ELC subtotal: 32 nodes over 4 formulas. Boundary subtotal: 32 nodes
over 3 formulas. Data: `sE_em_costs.json`.)

---

## Planck is the surprise

Planck's law calls $\exp(h\nu/kT)$ on positive arguments and then does
algebra. No trig, no branch cuts, no complex bypass. By the Lean-verified
T_EXP_LOG_DUALITY catalogue rule, any F16 tree with $\exp$ of a
positive-real argument stays in the real component of $\mathrm{ELC}$. The
14-node tree computes $B(\nu,T)$ exactly at every physically meaningful
$(\nu, T)$ — no approximation, no truncation.

What this buys you in practice: if you care about *symbolic stability*
(e.g., automatic differentiation through the Planck kernel, or exact
manipulation of blackbody integrals), Planck is on the easy side of the
$\mathrm{ELC}$ frontier. Wave propagation is on the hard side.

---

## The double-angle identity costs 4 extra nodes

The Poynting vector has two routes. Direct squaring of a single complex-bypass
$\cos$ gives 10 nodes. Using the trigonometric identity
$\cos^2\theta = (1+\cos 2\theta)/2$ to "simplify" gives **14 nodes** — 4 more.

Why? The identity buys you one fewer $\cos$ call but introduces an addition
(2n), a division by 2 (2n), and an extra multiplication for $2\theta$. In
F16-node accounting, algebraic identities that look simpler on paper can be
*more expensive* than direct computation. The lesson applies broadly: prefer
the form with fewer arithmetic glue operations, not the form with fewer
transcendental calls. $\cos$ is 1 node either way (complex bypass). The
arithmetic around it is where cost accumulates.

---

## Why "ELC-native" matters

$\mathrm{ELC}(\mathbb{R})$ is the closure of $\{1, x, +, -, \cdot, /, \exp, \log\}$
under composition. Every formula in that closure admits:

- A finite F16 tree representation.
- Exact symbolic manipulation (no series truncation).
- A depth-bounded proof of equivalence via EQ_D (our bounded-depth F16
  equality decision tool).

Thermal radiation, diffusion decay, skin depth, the photon-energy relation,
relativistic energy-momentum — all of these are ELC-native. Wave propagation,
by contrast, requires either (a) crossing to $\mathrm{ELC}(\mathbb{C})$
where $\cos$ is 1 complex node, or (b) accepting a Taylor approximation,
which is 33+ nodes for a 4-term expansion and drops to 1 complex node only
via Euler.

This is a structural feature of physics measured in F16: the thermal sector
is cheap, the oscillatory sector is complex-only.

---

## Reproduce

```bash
git clone https://github.com/almaguer1986/monogate
cd monogate
python exploration/blind-sessions/scripts/sE_em_costs.py
```

Expected output:

```
[E] EM wave cost catalog

  [boundary]  8 n   damped EM wave ...
  [inside  ] 10 n   EM energy density ...
  [boundary] 10 n   Poynting (cos·cos form)
  [boundary] 14 n   Poynting via cos²=(1+cos(2θ))/2
  [inside  ]  5 n   skin depth
  [inside  ] 14 n   Planck B(ν,T)
  [inside  ]  3 n   photon energy E=hc/λ

  Inside ELC total: 32 n (4 formulas)
  Boundary total  : 32 n (3 formulas)
```

---

**Cite:** Monogate Research (2026). "Planck Radiation Is ELC-Native (No Trig Needed)."
monogate research blog. https://monogate.org/blog/planck-elc-native
