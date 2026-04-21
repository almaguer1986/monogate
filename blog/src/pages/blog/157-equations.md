---
layout: ../../layouts/Base.astro
title: "214 Equations: The SuperBEST Cost of Science"
description: "A complete catalog of SuperBEST node counts for standard equations across 12+ domains — from 1-node trivialities to 2037-node error correction. Expanded from 157 (Monster Sprint) to 214 (COMP-ALL) to 295+ (domain-2 sessions: FIN, INFO, QM, THERMO, CHEM, BIO, ECON)."
date: "2026-04-20"
tag: "observation"
---

> **Update — 2026-04-20 (COMP-ALL):** This catalog has been expanded from 157 to **214 equations** following nine new measurement sessions (TECH-1 through TECH-5, SPORT-1 through SPORT-2, NAT-1 through NAT-2). New domains added: information retrieval, recommendation systems, GPS navigation, 3D graphics, error correction, sports analytics, and applied physics. The new ceiling is **2037n** (Reed-Solomon syndrome for RS(255,223)), far exceeding the previous ceiling of 47n (Black-Scholes). The new floor remains **2n** (ETA, batting average, any ratio). All new results use SuperBEST v4 (div=2n, recip=1n). See also: [The SuperBEST Cost of Everything](/blog/cost-of-everything).

---

## How expensive is science?

Not in grant money or compute hours — but in operator nodes. Under the SuperBEST v3 routing table, every equation reduces to a tree of EML-family primitives. Each primitive costs between 1 and 11 nodes. The tree depth is the cost of the science.

We measured 295+ standard equations across domains including chemistry, biology, astrophysics, neuroscience, geology, economics, electromagnetism, technology, sports, finance, quantum physics, and epidemiology. The range is stark: Wien's displacement law costs **1 node**. The Black-Scholes call price costs **47 nodes** (83n with full shared DAG). The gap is a factor of 47–83 — not because one equation is physically deeper than the other, but because one contains more irreducible arithmetic. The original catalog of 157 equations (Monster Sprint, seven scientific domains) has been expanded twice: to 214 (COMP-ALL sessions TECH-1 through NAT-2) and then to 295+ (domain-2 expansion: FIN, INFO, QM, THERMO, CHEM, BIO, ECON sessions).

This catalog documents every node count, every cross-domain isomorphism, and the structural rules that determine cost.

---

## SuperBEST v3 Node Costs (Reference)

| Operation | Cost |
|-----------|------|
| exp(x), ln(x), sin(x), cos(x) | 1n each |
| div(x, y) | 1n |
| mul(x, y), sub(x, y) | 2n each |
| neg(x) | 2n |
| recip(x) | **1n** (ELSb, R16-C1) |
| pow(x, p) for any real p | 3n |
| add(x, y) — positive domain | 3n |
| add(x, y) — general domain | 11n |
| Parameters, named constants | 0n (free) |

The key inversion: **transcendentals are cheap (1n); arithmetic is expensive (2-3n)**. The most expensive single operation is `add` in a domain where the sign of both operands is unknown — 11 nodes, eleven times the cost of exp.

---

## Table 1: Domain Statistics

| Domain | Equations | Min (unfolded) | Max (unfolded) | Mean |
|--------|-----------|----------------|----------------|------|
| Chemistry | 31 | 3n | 31n | 13.5n |
| Biology | 31 | 2n | 40n | 13.1n |
| Astrophysics | 22 | 1n | 19n | 8.8n |
| Neuroscience | 17 | 1n | 30n | 12.5n |
| Geology | 23 | 1n | 24n | 8.3n |
| Economics | 19 | 1n | 47n | 10.2n |
| Electromagnetism | 25 | 1n | 14n | 6.2n |

Electromagnetism is the cheapest domain on average — most EM laws are simple power-law or product-of-constants forms. Biology and Chemistry are the most expensive, driven by the MWC allosteric model (40n) and Maxwell-Boltzmann distribution (31n).

---

## Table 2: Top 10 Cheapest Equations (1n floor)

| Rank | Equation | Domain | Nodes (unfolded) | Nodes (folded) |
|------|----------|--------|------------------|----------------|
| 1 | Wien's displacement law λ_max = b/T | Astrophysics | 1n | 1n |
| 1 | Gauss's law Φ = Q/ε₀ | Electromagnetism | 1n | 1n |
| 1 | Curie law χ = C/T | Electromagnetism | 1n | 1n |
| 1 | Distribution coefficient Kd = Cs/Cw | Geology | 1n | 1n |
| 1 | Subduction velocity v = d/t | Geology | 1n | 1n |
| 1 | Perpetuity PV = C/r | Economics | 1n | 1n |
| 1 | ReLU via softplus LEAd(x,1) | Neuroscience | 1n | 1n |
| 8 | Malthus recursion N(t+1) = λN(t) | Biology | 2n | 2n |
| 8 | Hubble's law v = H₀d | Astrophysics | 2n | 2n |
| 8 | Self-capacitance of sphere C = 4πε₀R | Electromagnetism | 2n | 2n |

All seven 1-node equations are pure divisions or precomputed constant ratios. They share one structural fact: the only non-trivial operation is a single `div`, and both numerator and denominator are either free constants or live scalar variables — no multiplication needed.

The 1-node floor is the theoretical minimum for any non-trivial formula. Anything cheaper would be a terminal (a constant or a variable), which costs 0n by definition.

---

## Table 3: Top 10 Most Expensive Equations

| Rank | Equation | Domain | Nodes (unfolded) | Nodes (folded) |
|------|----------|--------|------------------|----------------|
| 1 | Black-Scholes call price C | Economics | 47n | 47n |
| 2 | MWC allosteric model (general) | Biology | 40n | 40n |
| 3 | Hodgkin-Huxley total current | Neuroscience | 30n | 30n |
| 4 | Izhikevich V equation (gen. domain) | Neuroscience | 26n | 26n |
| 5 | Maxwell-Boltzmann distribution | Chemistry | 31n | 31n |
| 6 | GHK 3-ion equation | Biology | 31n | 31n |
| 7 | MWC allosteric model (n=2) | Biology | 34n | 34n |
| 8 | Butler-Volmer electrode kinetics | Chemistry | 26n | 26n |
| 9 | Advection-dispersion Gaussian | Geology | 24n | 24n |
| 10 | Black-Scholes d1 formula | Economics | 20n | 20n |

The 47-node Black-Scholes formula includes the full d1 computation (20n), the d2 sub-formula sharing sigma*sqrt(T) (2n more), two normal CDF approximations at 6n each, and the final discounting and combination (13n). Nothing folds: every variable (S, K, r, sigma, T) is live.

The Hodgkin-Huxley equation is expensive for the opposite reason: it contains no transcendentals at the top level, but three separate voltage-gated conductance terms that each require power-law gates (m³, n⁴) and channel-specific reversal potential subtractions. Cost is the sum of three independent rational-polynomial blocks.

---

## Cross-Domain Isomorphisms

The most striking finding of the 295+-equation survey is that many equations from unrelated fields are **structurally identical** — they share the same operator tree and thus the same node cost.

### The 5-Node Exponential Template

`C·exp(−kt)` costs exactly **5 nodes** regardless of what k, C, and t mean:

- Population growth N₀·exp(rt) — Biology
- Radioactive decay N₀·exp(−λt) — Biology, Geology
- Arrhenius rate constant A·exp(−Ea/RT) — Chemistry
- Continuous compounding P·exp(rt) — Economics
- One-compartment pharmacokinetics C₀·exp(−kt) — Biology

All five are the same EML tree: `mul(C, exp(mul(-k, t)))`. The scientific label is semantic metadata. The operator cost is structural.

### The O(N) Linear Scaling Family

When a formula sums N independent terms, cost scales as O(N). Three distinct sciences produce this pattern with the same mechanism:

| Formula | Domain | Scaling law |
|---------|--------|-------------|
| NPV (N cash flows) | Economics | 7N nodes |
| N-compartment pharmacokinetics | Biology | 10N − 3 nodes |
| Seismic travel time (N layers) | Geology | 4N − 3 nodes |
| Softmax denominator (N classes) | Neuroscience | 4N − 3 nodes |

The N-compartment PK and the seismic travel time are exact matches at 4N−3 in their add-dominated structure. The difference between them (PK costs 10N−3, seismic 4N−3) is exactly one extra `exp` plus two extra `mul` nodes per compartment — the exponential decay term each PK compartment requires but each seismic layer does not.

### Softmax = Logit Choice

Neural network softmax (NEURO-2, cost 4N−1 per component with shared denominator) and economic logit choice probability (ECON-3, cost 5N total for N options) share the same tree:

```
exp(x_i) / sum_j(exp(x_j))
```

The 1-node difference per component comes from the `div(Vi, mu)` scaling step in the economic formulation. Structurally, discrete choice econometrics and softmax classification are the same computation with different constants.

### Van't Hoff = Clausius-Clapeyron at 17n

The integrated van't Hoff equation and the Clausius-Clapeyron equation share an identical 17-node operator tree. Both express `ln(ratio) = −(ΔH/R)·(1/T₂ − 1/T₁)`. The chemical equilibrium law and the vapor pressure law are structurally one equation with different semantic labels — a fact invisible in the equations' algebraic forms but exact in their operator trees.

### The Entropy Scaling Family

Three equations from three domains compute the same sum-of-p·ln(p) pattern:

| Formula | Domain | Scaling law |
|---------|--------|-------------|
| Entropy of mixing (N components) | Chemistry | 6N − 5 nodes |
| Shannon entropy of spike train (K patterns) | Neuroscience | 6K − 1 nodes |
| Cross-entropy loss (N classes) | Neuroscience / ML | 6N − 1 nodes |

Each term contributes 3n (one `ln` at 1n plus one `mul` at 2n). Each addition step costs 3n. The per-term structure is identical across thermodynamics, information theory, and machine learning loss functions.

---

## What Drives Cost

### Rule 1: add is the bottleneck, not exp

Under SuperBEST v3 routing, `exp` and `ln` cost 1 node each. A single `add` costs 3 nodes in positive domain and 11 nodes in general domain. This inverts intuition: the most expensive equations are not those with transcendentals but those with many additions.

The Hodgkin-Huxley equation (30n) contains only one exp implicitly (in the gate variables) but requires six `add` or `sub` operations at the top level for the three conductance terms. The MWC allosteric model (40n) is expensive because it has four power-law terms and five additions — not because it contains transcendentals.

### Rule 2: Constant folding can save up to 8 nodes per occurrence

The Nernst equation costs 5n with RT/nF folded as a single constant and 13n with all four variables live. The savings of 8n come from eliminating two `mul` nodes (each costs 2n) and merging the associated EXL terminals (each costs 1n at minimum). This is the largest per-occurrence saving observable in a single equation.

### Rule 3: Class D equations escape O(1) upper bounds

Four structural classes organize all equations in the catalog:

- **Class A** — Pure exponential templates (5–12n): one DEML/EML terminal, one or two `mul` nodes
- **Class B** — Rational functions without transcendentals (1–27n): chains of `mul`, `add`, `div`
- **Class C** — Log-ratio formulas (1–17n): one or two EXL terminals followed by `mul` and `add`
- **Class D** — Mixed exponential-rational (6–47n): exp or ln inside rational numerator/denominator

Class D is the only class with no structural ceiling. Black-Scholes (47n), MWC (40n), and Maxwell-Boltzmann (31n) are all Class D, and each could in principle grow further with additional product terms or distribution components.

### Rule 4: Linearized forms are never cheaper

Linearized forms of equations consistently cost more than their algebraic counterparts:

- Hill plot `ln(Y/(1−Y))` vs `ln[L]` costs 16n vs Hill algebraic 15n
- Lineweaver-Burk `1/v` vs `1/[S]` costs 11n vs Michaelis-Menten 9n

Linearization adds at least one EXL node plus an extra subtraction. The historical appeal of linearized forms — graphical analysis before computers — has no computational justification under EML routing.

---

## The Science of Computation

The node counts in this catalog are not performance measurements. They do not depend on hardware, compiler, or numerical precision. They are structural invariants — properties of the equation's algebraic form, independent of any implementation.

What they reveal is that scientific equations vary enormously in representational complexity, and that this variation follows structural rather than disciplinary lines. A transport law from geology, a diffusion law from biology, and Ohm's law from physics all cost the same 4–5 nodes because they are the same equation. A mechanistic receptor model costs four times more than an empirical Hill equation not because the science is four times deeper, but because mechanistic tracking requires four times more distinct operator calls.

The 1-node floor — Wien's law, Curie's law, Gauss's flux law, the perpetuity price — represents equations where a single ratio exhausts all the science. The 47-node ceiling — Black-Scholes, where five live variables combine in two interlocking normal CDF evaluations plus discounting — represents equations where no structural simplification is available without fixing a variable.

Between these extremes, the 293+ other equations of science distribute themselves according to how many irreducible operations their algebraic form requires. That distribution is the cost of science.

---

*Data sources: sessions Chem-1 through Bio-5 (chemistry and biology), ASTRO-1 through ASTRO-3 (astrophysics), NEURO-1 through NEURO-3 (neuroscience), GEO-E1 through GEO-E3 (geology), ECON-1 through ECON-3 (economics), MAG-1 through MAG-3 (electromagnetism). SuperBEST v3 routing table applied analytically. All results exact and reproducible.*

*Full machine-readable catalog: `python/results/master_equation_catalog.json`*

*Related paper: [Master Equation Catalog (LaTeX)](https://monogate.org)*
