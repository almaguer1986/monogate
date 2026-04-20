---
layout: ../../layouts/Base.astro
title: "Predicting SuperBEST Cost from Equation Structure"
date: "2026-04-20"
tag: "theorem"
description: "Four structural classes, the cost decomposition theorem (T38), complexity classes O(1)/O(N)/O(N²), and the Linear Ceiling Conjecture (T39): a complete theory of how many EML nodes any standard scientific equation requires."
---

# Predicting SuperBEST Cost from Equation Structure

**Tier: THEOREM** (T34–T39, empirically validated; R²=0.92 on 50 equations, 0-error blind test on 20)

---

The SuperBEST v3 routing table assigns a minimum EML node count to every primitive arithmetic operation. That answers the per-operation question. The harder question is structural: given an arbitrary scientific equation, can you predict its total cost before you build the expression tree?

The answer is yes. This post summarises the complete theory developed across sessions COST-1 through COST-9.

---

## SuperBEST v3 Reference Costs

| Operation | Symbol | Cost |
|-----------|--------|------|
| Exponential e^x | exp | 1n |
| Natural log ln x | ln | 1n |
| Division x/y | div | 1n |
| Negation −x | neg | 2n |
| Reciprocal 1/x | recip | 2n |
| Multiplication x·y | mul | 2n |
| Subtraction x−y | sub | 2n |
| Exponentiation x^n | pow | 3n |
| Addition x+y (pos. domain) | add | 3n |

A 19-node reference equation (SuperBEST v3 standard) costs 19n vs 71n naive — a 74.0% saving.

---

## The Four Structural Classes

Every standard scientific equation falls into one of four structural classes, determined by whether it contains exp, ln, both, or neither.

| Class | Signature | Mean cost | Formula example |
|-------|-----------|-----------|-----------------|
| A — Pure Exponential | exp present, no ln | 5–12n | Arrhenius k=Ae^{−Ea/RT}: 5n |
| B — Rational | no exp, no ln | 1–6n | Ohm V=IR: 2n |
| C — Log-ratio | ln only, no exp | 3–8n | pH = −ln[H⁺]/ln10: 3n |
| D — Mixed | both exp and ln, or multiple exp branches | 8–25n | Boltzmann p_i=e^{−E_i/kT}/Z: 8n |

Class C is the cheapest per equation on average — ln costs only 1n, so log-ratio patterns are highly economical. Class D spans the widest range because it combines both exponential and logarithmic subexpressions; cost depends entirely on how many independent branches exist.

The structural class alone predicts cost to within ±3n for 80% of standard scientific equations (COST-4).

---

## The Cost Decomposition Theorem (T38)

The central result of this sprint is an exact identity:

**Cost(E) = NaiveCost(E) − SharingDiscount(E) − PatternBonus(E)**

where:

- **NaiveCost(E)** sums the SuperBEST unit cost of every primitive operation in E, counted once per occurrence in the expression tree, ignoring any sharing.
- **SharingDiscount(E) ≥ 0** captures two savings: constant folding (any subexpression with all-constant inputs contributes 0 at runtime rather than its naive cost), and shared subexpression elimination (any computed intermediate used at k ≥ 2 sites need only be computed once).
- **PatternBonus(E) ≥ 0** captures compound-pattern recognition: subexpressions that a single F₁₆ operator computes in fewer nodes than their naive decomposition.

This is an equality, not a bound. For any EML-computable expression, the three terms exactly account for all savings.

A key structural lemma underlies the theorem: **No Nesting Penalty**. In the EML framework, composing two operators op₁(op₂(x)) costs exactly c_{op₁} + c_{op₂} — no interface node, no type conversion, no overhead for depth. Nesting depth does not appear in the cost formula.

**Practical consequence**: for single-branch formulas with no shared subexpressions and no constant parameters, SharingDiscount = PatternBonus = 0, so NaiveCost is exact. This was confirmed on all 20 equations in the COST-8 blind test: NaiveCost predicted Cost with zero error for every pure-tree equation.

---

## Pattern Bonus: Top Operators by Impact

The top compound patterns by weighted savings across 50 catalogued equations (COST-7):

| Pattern | Weighted impact | Frequency (50 eqs) |
|---------|----------------|---------------------|
| EXL (exp-times-log) | 60 | 14/50 |
| EML (exp-mul-log) | 54 | 18/50 |
| EAL (exp-add-log) | 48 | 11/50 |
| DEML (double exp-mul-log) | 44 | 22/50 |

DEML is the single most frequent pattern (22 of 50 equations), appearing wherever softmax, partition functions, or Boltzmann distributions are present. EXL has the highest per-match savings.

---

## Complexity Classes

Classifying equations by how cost scales with a structural parameter N (number of terms in a sum, number of components, etc.) reveals three regimes:

**O(1) — constant cost.** Any equation whose formula has fixed operator structure and no summation. Examples: Arrhenius, Ohm's law, the logistic function, any single closed-form expression. Cost does not depend on N because there is no N.

**O(N) — linear cost.** Equations containing one explicit summation over N terms: Taylor series (9N−3 nodes), Fourier series (linear in number of retained terms), Shannon entropy (linear in number of states), softmax (linear in number of classes), pharmacokinetic multi-compartment models. The general form is Cost = (α₀+3)N − 3, where α₀ is the cost of the per-term expression. Leading coefficients observed in practice range from 4 to 12.

**O(N²) — quadratic cost.** Arises only when the closed-form expression contains a nested double summation. In standard scientific equations this occurs only in Hopfield energy functions and pairwise interaction models. No single-summation textbook formula reaches O(N²).

---

## The Linear Ceiling Conjecture (T39 candidate)

**Conjecture T39**: Every standard scientific equation — meaning a textbook formula with a fixed, finite operator structure — has SuperBEST cost that is at most O(N) in its structural parameter N (number of summands). No standard scientific equation has super-linear cost in its closed-form formula.

Evidence: every equation in the 50-equation COST-1 catalogue and the 20-equation COST-8 blind test falls into O(1) or O(N). The only known O(N²) examples are discrete energy models (Hopfield, Ising) whose closed-form expressions contain explicit double sums — not single-formula continuous equations. The conjecture remains open for equations with more exotic combinatorial structure, but no counterexample has been found.

---

## Empirical Validation

The cost model was validated in two stages:

**Regression (COST-1, n=50 equations).** Linear regression of actual SuperBEST cost on NaiveCost gave R²=0.92. The residual 8% is explained almost entirely by SharingDiscount (constant folding for equations with fixed parameters). PatternBonus accounts for the remaining variance in multi-branch expressions. One finding: exp is empirically underpriced in SuperBEST by approximately 3× relative to its contribution to total equation cost — equations with many exp nodes tend to sit above the regression line.

**Blind test (COST-8, n=20 equations).** Twenty equations not seen in COST-1 were predicted using NaiveCost alone (assuming SharingDiscount=PatternBonus=0). Prediction error: 0 for all 20. This confirms that NaiveCost is a perfect predictor for pure-tree equations over live variables, which is the generic case for textbook formulas with free parameters.

---

## Theorem Summary (T34–T39)

| Label | Statement | Proved in |
|-------|-----------|-----------|
| T34 | Cost(E) ≤ NaiveCost(E) for all EML-computable E | COST-2 |
| T35 | Cost(E) ≥ 1 (trivial lower bound) | COST-3 |
| T36 | Cost(E) ≥ ⌈depth(E)/2⌉ (depth lower bound) | COST-3 |
| T37 | Cost(E) ≥ n_exp + n_ln (operation-type lower bound) | COST-3 |
| T38 | Cost(E) = NaiveCost(E) − SharingDiscount(E) − PatternBonus(E) (exact decomposition) | COST-6 |
| T38-NNP | Cost(op₁(op₂(x))) = c_{op₁} + c_{op₂} (No Nesting Penalty) | COST-6 |
| T39 | Every standard scientific equation has cost O(N) or less (conjecture) | COST-9 |

---

**Cite:** Almaguer, A.R. (2026). "Predicting SuperBEST Cost from Equation Structure." monogate research blog. https://monogate.org/blog/cost-theory
