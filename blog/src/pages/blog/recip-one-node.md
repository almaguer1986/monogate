---
layout: ../../layouts/Base.astro
title: "recip(x) Is 1 Node — ELSb Closes the Gap"
description: "ELSb(0, x) = exp(0 − ln(x)) = 1/x. One node. SuperBEST v4: 18 nodes total, 75.3% savings. The reciprocal was never a division problem."
date: "2026-04-20"
tag: theorem
---

# recip(x) Is 1 Node — ELSb Closes the Gap

**Result: R16-C1** · Tag: THEOREM

---

## The Finding

The reciprocal function $1/x$ is computable in exactly **one node** over the
16-operator family $\mathcal{F}_{16}$, using the operator
$\operatorname{ELSb}(a, b) = \exp(a - \ln b) = e^a / b$:

$$\operatorname{ELSb}(0,\, x) = \exp(0 - \ln x) = \exp(-\ln x) = \frac{1}{x}$$

That is all. Set the first argument to $0$, the second argument to $x$, and
$e^0 / x = 1/x$ exactly.

The previous best was 2 nodes — a construction via EDL that first converted $x$
to $e^x$ and then divided through a logarithm. R16-C1 saves that intermediate
step entirely.

---

## Why It Was Missed

The natural operator family for reciprocals was **EDL**: $\operatorname{EDL}(a,b) = e^a / \ln b$.

To compute $1/x$ via EDL, you need the denominator to equal $\ln b = x$, which
means $b = e^x$. That requires an inner node to produce $e^x$. Two nodes total.

The ELSb operator was studied for **division**: $\operatorname{ELSb}(\ln x, y) = e^{\ln x}/y = x/y$
(a 2-node construction needing an inner $\ln x$ node). Division was the headline
use case. Nobody checked what happened when the first argument is the constant $0$
instead of $\ln x$.

$\operatorname{ELSb}(0, x) = e^0/x = 1/x$.

One node. The operator already knew how to do reciprocal. We just had to ask.

This follows the same structural pattern as the earlier reductions:

| Result | Operator | Key move | Savings |
|--------|---------|---------|---------|
| T10u: mul $3\to2$ | ELAd | $\operatorname{ELAd}(\ln x, y) = xy$ | 1 node |
| T33: sub $3\to2$ | LEdiv | $\operatorname{LEdiv}(x, e^y) = x-y$ | 1 node |
| R16-C1: recip $2\to1$ | ELSb | $\operatorname{ELSb}(0, x) = 1/x$ | 1 node |

In each case: take an operator in $\mathcal{F}_{16} \setminus \mathcal{F}_6$
that accepts one argument directly (no $\exp$ or $\ln$ wrapper), set the free
argument to a constant, and the formula collapses to the target function.

---

## SuperBEST v4: 18 Nodes, 75.3% Savings

The updated table:

| Operation | v3 (F16) | v4 (F16) | Operator |
|-----------|---------|---------|----------|
| exp(x) | 1 | 1 | EML(x,1) |
| ln(x) | 1 | 1 | EXL(0,x) |
| neg(x) | 2 | 2 | EXL(0, DEML(x,1)) |
| **recip(x)** | **2** | **1** | **ELSb(0,x)** |
| mul(x,y) | 2 | 2 | ELAd(EXL(0,x),y) |
| sub(x,y) | 2 | 2 | LEdiv(x, EML(y,1)) |
| add(x,y) | 3 | 3 | EAL(EXL(0,x), EXL(0,y)) |
| pow(x,n) | 3 | 3 | EML(EXL(0,x)·n, 1) |
| **Total** | **19** | **18** | |

Savings: $1 - 18/73 = 55/73 \approx \mathbf{75.3\%}$ vs naive EML.

The naive-EML baseline is fixed at 73 nodes. Every node we remove is a
permanent reduction in the compression floor.

Note: **recip in $\mathcal{F}_6$ still requires 2 nodes**. ELSb is not in the
six-operator library. Every $\mathcal{F}_6$ operator applies $\ln$ to its
second argument, so $x$ cannot appear directly in the denominator without
an intermediate $e^x$ conversion step.

---

## Ripple: Which Downstream Results Update

Most results are unaffected. The reason: in practice, standalone $\recip(x)$
as an explicit unary operation is rare. Most formulas use **division** ($x/y$),
which was already 1 node via EDL, not 2.

The affected cases are formulas where $1/x$ appears as a true unary reciprocal:

**Geometry catalog — Gaussian curvature:**
The entry `K(z = ln r) — 7 nodes — mul+recip+neg` drops to **6 nodes**.
The recip sub-tree was contributing 2n; it now contributes 1n.

**SuperBEST table itself:**
19n $\to$ 18n. This is the primary update.

**Unaffected:**
- Taylor series: coefficients $1/n!$ are constants (folded to 0 nodes). No recip node.
- Partition function $Z = \mathrm{Tr}[e^{-\beta H}]$: no recip.
- Density matrix $\rho = e^{-\beta H}/Z$: the $1/Z$ is a division by a scalar matrix — handled by EDL, already 1 node.
- Free energy $F = -\ln Z / \beta$: no recip.
- 157-equation catalog: the few equations using explicit $1/x$ drop 1 node each; the catalog total decreases by an estimated $\leq 5$ nodes across all 157 equations.

---

## Connection to the Structural Audit

R16-C1 sits on the T08 $\to$ THEOREM path of the structural audit.
The audit identified that the SuperBEST table should be verified by
exhaustive search over $\mathcal{F}_{16}$, not just $\mathcal{F}_6$.
T10u, T33, and R16-C1 are the three results found during that systematic
re-check.

The search principle:

> For every operator $\mathrm{op} \in \mathcal{F}_{16} \setminus \mathcal{F}_6$,
> enumerate all constant-argument specializations from $\{0, 1\}$.
> Many simplify to known functions.

This is a finite search (16 operators $\times$ 4 terminal pairs = 64 candidates
for 1-node trees). R16-C1 fell out of that enumeration.

---

## Formal Reference

Theorem paper: `D:/monogate/python/paper/theorems/recip_One_Node.tex`

Result identifier: **R16-C1** (Census item 16, Construction 1)

Proof: construction by explicit formula + lower bound by non-constancy argument.
No exhaustive search required for the lower bound — it follows immediately that
no constant equals $1/x$ for all $x > 0$.

---

> Almaguer, A.R. (2026). "R16-C1: recip(x) Is 1 Node — ELSb Closes the Gap."
> monogate research blog. Session: 1-Node Integration.
> https://monogate.org/blog/recip-one-node
