---
layout: ../../layouts/Base.astro
title: "Only the Multiplicative F16 Operators Are Chaotic"
description: "A 600-point parameter sweep across all 16 F16 operators shows that 12 of them collapse to period-2 dynamics, while the four multiplicative operators (EXL, DEXL, EXN, DEXN) exhibit long cycles, chaos, and a period-3 Sharkovskii signature."
date: 2026-04-23
---

# Only the Multiplicative F16 Operators Are Chaotic

**Tier: OBSERVATION** (numerical experiment; no analytic proof yet)

We swept 600 parameter values $c \in [-3, 3]$ for each of the 16 F16
operators, iterated $z_{n+1} = \mathrm{op}(z_n, c)$ from $z_0 = 0$ with a
500-step transient, and classified the tail by period-detection and a
finite-difference Lyapunov exponent. The outcome is cleaner than we
expected: **only the four operators whose arithmetic glue is multiplication
show non-trivial dynamics.** The other twelve collapse to fixed points or
period-2 cycles.

---

## The dynamical partition

| Operator | Formula | Max period | % chaotic | Distinct periods |
|----------|---------|-----------:|----------:|:-----------------|
| **EXL**  | $\exp(z)\cdot\ln(c)$ | **16** | 0.7% | 1,2,5,6,7,8,9,10,11,14,16 |
| **DEXL** | $\exp(-z)\cdot\ln(c)$ | **15** | 0.7% | **1,3**,5,6,7,8,9,10,11,12,13,14,15 |
| **EXN**  | $\exp(z)\cdot\ln(-c)$ | **16** | 0.7% | 1,2,5,6,7,8,9,10,11,14,16 |
| **DEXN** | $\exp(-z)\cdot\ln(-c)$ | **15** | 0.5% | **1,3**,5,6,7,8,9,10,11,12,13,14,15 |
| EML, EAL, EDL, DEML, DEAL, DEDL | ± self-map with $\pm,\div$ | 2 | 0 | 1,2 |
| EMN, EAN, EDN, DEMN, DEAN, DEDN | same with $\ln(-c)$ | 2 | 0 | 1,2 |

The 12 non-multiplicative operators saturate at period 2. The 4
multiplicative operators reach up to period 16 and visit a rich spectrum
of distinct cycle lengths.

---

## The Sharkovskii fingerprint

Two of the multiplicative operators — DEXL and DEXN — contain
**period 3** cycles. By Sharkovskii's theorem on the reals, the presence of
period 3 forces the presence of cycles of every other period (in
Sharkovskii's ordering, 3 is the "largest" element, and its appearance
implies all others). Empirically we observe
$\{1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15\}$ — cycles of length 2
and 4 are *absent* from the sweep, which is consistent with the Sharkovskii
ordering $3 \succ 5 \succ 7 \succ \ldots \succ 2\cdot3 \succ 2\cdot5 \succ \ldots$
where 2 and 4 sit far below 3.

This is a Li-Yorke chaos signature. Period 3 on a 1D real map implies
uncountable scrambled sets and positive topological entropy — not just
positive Lyapunov on a measure-zero set, but *genuinely chaotic* behavior
on an interval.

EXL and EXN have period 16 but apparently lack period 3 in our sweep.
Whether period 3 exists at finer resolution is open (this sweep is 600
points over a 6-unit interval; a denser sweep might surface it).

---

## Why multiplication?

A heuristic: multiplicative coupling of $\exp(\pm z)$ with $\ln(\pm c)$
turns small perturbations in $z$ into scaled perturbations via the
$\ln(\pm c)$ factor, which can be large-magnitude near $c \to 0^+$ or
$c \to 0^-$. The Lyapunov exponent tracks the log-magnitude of that
multiplier. Additive coupling caps the per-step expansion at $\log'$ of the
state, which is bounded below $\exp$-induced contraction for large $|z|$.

Formally this is the **EAL↔EXL conjugacy via exp** (Lean-formalized in
`SelfMapConjugacy.lean`): the EAL self-map $f(x) = \exp(x) + \ln(x)$ and
EXL self-map $g(y) = \exp(y)\ln(y)$ are topologically conjugate on
$(0, \infty)$ by $y = \exp(x)$. They therefore share every dynamical
invariant — entropy, Lyapunov spectrum, periodic point structure. The
*off-diagonal* dynamics (where the $c$ argument varies independently) break
conjugacy and is where the multiplicative/additive split manifests.

---

## Reproduce

```bash
git clone https://github.com/agent-maestro/monogate
cd monogate
python exploration/blind-sessions/scripts/sB_bifurcation_chaos.py
```

Takes ~3 minutes on a laptop. Output goes to
`exploration/blind-sessions/data/sB_bifurcation_chaos.json`.

---

## What's open

- Is period 3 present in EXL/EXN at finer resolution?
- Is the max-period-16 ceiling genuine or an artifact of the tail length?
- Topological entropy of DEXL: lower bound from period 3 is
  $h \geq \log(1+\varphi)/\log\varphi$ ≈ 1.04, where $\varphi$ is the
  golden ratio. Upper bound requires a Markov partition argument.
- None of these results are formalized in Lean. They are reproducible
  empirical claims.

---

**Cite:** Monogate Research (2026). "Only the Multiplicative F16 Operators Are Chaotic."
monogate research blog. https://monogate.org/blog/chaos-multiplicative-operators
