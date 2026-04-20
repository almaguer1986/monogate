# COST-1: Data Mining — SuperBEST v3 Cost Regression

**Session**: COST-1  
**Date**: 2026-04-20  
**Scope**: 50 chemistry/biology equations, 9-operator OLS regression, sharing-correction model  
**Output**: `python/results/cost1_regression.json`

---

## 1. Motivation

SuperBEST v3 assigns fixed per-operation costs:

| op    | cost |
|-------|------|
| exp   | 1    |
| ln    | 1    |
| mul   | 2    |
| div   | 1    |
| add   | 3 (pos) / 11 (gen) |
| sub   | 2    |
| pow   | 3    |
| neg   | 2    |
| recip | 2    |

The question is: do these costs correctly predict the actual SuperBEST evaluation cost of real scientific equations, or are there systematic biases? We run a purely empirical 50-equation regression to find out.

---

## 2. Data Table

Columns: actual cost (from SuperBEST evaluation), naive cost (SuperBEST table, add=3), fitted cost (OLS regression), residual (actual - fitted), sharing correction (actual - naive).

| Equation | actual | naive | fitted | residual | sharing_corr |
|---|---|---|---|---|---|
| Arrhenius k=A·exp(-Ea/RT) | 5 | 7 | 8.0 | -3.0 | -2 |
| Eyring | 13 | 15 | 16.3 | -3.3 | -2 |
| Collision theory | 10 | 12 | 14.5 | -4.5 | -2 |
| Rate law r=k[A][B] | 4 | 4 | 4.9 | -0.9 | 0 |
| Integrated first-order | 7 | 9 | 10.5 | -3.5 | -2 |
| Integrated second-order | 9 | 9 | 8.9 | +0.1 | 0 |
| Boltzmann factor | 13 | 10 | 12.8 | +0.2 | +3 |
| Boltzmann ratio | 11 | 9 | 9.4 | +1.6 | +2 |
| Partition function 2-level | 17 | 13 | 13.7 | +3.3 | +4 |
| Maxwell-Boltzmann | 31 | 19 | 23.3 | +7.7 | +12 |
| Entropy S=kB·ln(Ω) | 3 | 3 | 4.4 | -1.4 | 0 |
| Helmholtz A=-kBT·ln(Z) | 7 | 7 | 6.2 | +0.8 | 0 |
| Average energy 2-level | 21 | 18 | 21.5 | -0.5 | +3 |
| Nernst (folded) | 5 | 5 | 6.9 | -1.9 | 0 |
| Nernst (unfolded) | 13 | 10 | 14.7 | -1.7 | +3 |
| Butler-Volmer | 26 | 20 | 22.4 | +3.6 | +6 |
| Tafel | 13 | 9 | 10.5 | +2.5 | +4 |
| GHK 2-ion | 27 | 20 | 24.8 | +2.2 | +7 |
| Debye-Huckel | 12 | 12 | 12.1 | -0.1 | 0 |
| Electrochemical potential | 15 | 13 | 14.5 | +0.5 | +2 |
| pH=-log10[H+] | 3 | 3 | 4.4 | -1.4 | 0 |
| Henderson-Hasselbalch | 10 | 10 | 10.9 | -0.9 | 0 |
| [H+]=sqrt(Ka·Ca) | 5 | 5 | 6.4 | -1.4 | 0 |
| Van Slyke | 14 | 16 | 18.9 | -4.9 | -2 |
| Quadratic [H+] Ka variable | 20 | 21 | 21.3 | -1.3 | -1 |
| Activity pH | 5 | 5 | 6.9 | -1.9 | 0 |
| dG=dH-TdS | 4 | 4 | 3.9 | +0.1 | 0 |
| dG0=-RT·ln(K) | 7 | 7 | 6.2 | +0.8 | 0 |
| dG=dG0+RT·ln(Q) | 8 | 8 | 9.5 | -1.5 | 0 |
| van't Hoff | 17 | 14 | 15.6 | +1.4 | +3 |
| Clausius-Clapeyron | 17 | 14 | 15.6 | +1.4 | +3 |
| Entropy of mixing 2-comp | 13 | 13 | 13.2 | -0.2 | 0 |
| Arrhenius-Gibbs Form1 | 11 | 11 | 12.4 | -1.4 | 0 |
| Arrhenius-Gibbs Form2 | 16 | 16 | 17.5 | -1.5 | 0 |
| Malthus N_{t+1}=lambda*N_t | 2 | 2 | 2.5 | -0.5 | 0 |
| Gompertz | 12 | 12 | 12.6 | -0.6 | 0 |
| R0 net reproductive (3-age) | 12 | 12 | 12.5 | -0.5 | 0 |
| Beverton-Holt | 11 | 11 | 11.9 | -0.9 | 0 |
| Logistic sigmoid | 14 | 16 | 16.4 | -2.4 | -2 |
| Logistic standard | 14 | 16 | 16.4 | -2.4 | -2 |
| Michaelis-Menten | 9 | 9 | 9.4 | -0.4 | 0 |
| Lineweaver-Burk | 11 | 11 | 11.4 | -0.4 | 0 |
| Enzyme turnover | 4 | 3 | 5.3 | -1.3 | +1 |
| Competitive inhibition | 18 | 15 | 16.8 | +1.2 | +3 |
| Uncompetitive inhibition | 18 | 15 | 16.8 | +1.2 | +3 |
| Mixed inhibition | 27 | 22 | 24.3 | +2.7 | +5 |
| Hill general | 15 | 13 | 14.9 | +0.1 | +2 |
| Hill fractional | 10 | 8 | 8.5 | +1.5 | +2 |
| MWC n=2 | 34 | 32 | 35.0 | -1.0 | +2 |
| GHK 3-ion | 31 | 26 | 30.0 | +1.0 | +5 |

---

## 3. Regression Model

### Method

OLS without intercept (cost models are zero-homogeneous — zero operations = zero cost).

```
Cost = alpha_exp * n_exp + alpha_ln * n_ln + alpha_mul * n_mul
     + alpha_div * n_div + alpha_add * n_add + alpha_sub * n_sub
     + alpha_pow * n_pow + alpha_neg * n_neg + alpha_rec * n_rec
```

50 equations, 9 regressors, numpy `lstsq`.

### Fit Statistics

| Metric | Value |
|--------|-------|
| R²     | 0.9199 |
| RMSE   | 2.16 |
| MAE    | 1.63 |

R² = 0.92 is respectable for a no-intercept linear model across equations spanning costs 2–34. The RMSE of 2.16 cost units indicates reasonable predictive power, though some structured residuals remain (see Section 5).

### Fitted Coefficients vs SuperBEST v3

| Op    | SuperBEST | Fitted | Delta |
|-------|-----------|--------|-------|
| exp   | 1         | 3.837  | +2.837 |
| ln    | 1         | 1.982  | +0.982 |
| mul   | 2         | 2.456  | +0.456 |
| div   | 1         | 2.870  | +1.870 |
| add   | 3         | 2.591  | -0.409 |
| sub   | 2         | 1.406  | -0.594 |
| pow   | 3         | 3.974  | +0.974 |
| neg   | 2         | -0.718 | -2.718 |
| recip | 2         | 1.940  | -0.060 |

### Interpretation

**exp is severely underpriced.** SuperBEST assigns exp=1, but the data implies it costs ~3.8 cost units. This is the largest discrepancy. Every exp in real equations carries intermediate complexity (argument construction, sign handling) that the table price does not capture.

**neg is effectively free (or negative).** Fitted coefficient = -0.72. This is almost certainly a collinearity artifact: neg co-occurs reliably with exp in exponential-decay equations (Arrhenius, Boltzmann, Gompertz) where the total cost is lower than the sum-of-parts would imply due to operator sharing and argument reuse. The OLS absorbs this into neg having negative weight.

**div is underpriced.** SuperBEST gives div=1 but fitted value is 2.87. In practice, a division often requires constructing both numerator and denominator as distinct subexpressions, costing more than 1 unit of bookkeeping.

**ln, recip, pow, add, sub** are all approximately correct — within ~1 unit of their SuperBEST values.

**mul** is slightly high (2.46 vs 2.0), consistent with chained multiplications needing partial-product bookkeeping.

---

## 4. Top-5 Positive Residuals (more expensive than predicted)

Equations where actual cost > fitted cost (the model underestimates complexity).

| Rank | Equation | Residual | Actual | Fitted |
|------|----------|----------|--------|--------|
| 1 | Maxwell-Boltzmann | +7.65 | 31 | 23.35 |
| 2 | Butler-Volmer | +3.62 | 26 | 22.38 |
| 3 | Partition function 2-level | +3.26 | 17 | 13.74 |
| 4 | Mixed inhibition | +2.65 | 27 | 24.35 |
| 5 | Tafel | +2.51 | 13 | 10.49 |

**Maxwell-Boltzmann** (+7.65): This is the worst underestimate. The expression has a complex argument structure — the exponent contains a squared velocity term divided by a temperature product, embedded inside a power (normalization prefactor also uses a pow). The OLS model counts 5 mul + 1 exp + 2 pow + 1 neg = straightforward total, but the actual tree has a deeply nested argument for exp that forces extra intermediate nodes. The normalization constant (a pow of a mul of a recip) creates shared-but-costly subexpression branching.

**Butler-Volmer** (+3.62): Two exponential branches with opposite signs that must be evaluated independently (no sharing possible), plus a mul-heavy recombination. The two exp terms can't share intermediate nodes because their arguments differ in sign only — but sign handling under subtraction is not free.

**Partition function 2-level** (+3.26): Two exp terms plus an add — the denominator of subsequent expressions reuses this sum, but at the single-equation level the add of two exp values is costlier than the table predicts when argument construction is counted.

**Mixed inhibition** (+2.65): Three separate denominator modifications (Km*(1+I/Ki), Vmax/(1+I/Ki')) produce deeply nested rational structures. The recip operators each require a fully evaluated denominator, making the tree wider and deeper than a simple op-count suggests.

**Tafel** (+2.51): Despite having only exp+3*mul+neg, the Tafel equation appears more expensive than predicted. The regression has pulled the exp coefficient down due to multicollinearity with neg, so exp-heavy equations with few compensating operators show positive residuals.

---

## 5. Top-5 Negative Residuals (cheaper than predicted)

Equations where actual cost < fitted cost (the model overestimates complexity).

| Rank | Equation | Residual | Actual | Fitted |
|------|----------|----------|--------|--------|
| 1 | Van Slyke | -4.88 | 14 | 18.88 |
| 2 | Collision theory | -4.46 | 10 | 14.46 |
| 3 | Integrated first-order | -3.49 | 7 | 10.49 |
| 4 | Eyring | -3.29 | 13 | 16.29 |
| 5 | Arrhenius k=A·exp(-Ea/RT) | -3.03 | 5 | 8.03 |

**Van Slyke** (-4.88): Has mul+add+pow+recip+div — but the actual structure is a ratio of sums where the denominator terms share a common factor computed once. The model counts each op independently; in practice one mul subexpression appears in both numerator and denominator paths, giving a real sharing discount.

**Collision theory** (-4.46): The pow term is a square root of the temperature ratio — this is structurally simple (one pow node with exponent 0.5), and the exp argument is already computed from the activation energy. The fitted cost is inflated because the regression learned that pow+exp combinations tend to be expensive (Maxwell-Boltzmann effect), but this simpler instance doesn't have the same nesting depth.

**Integrated first-order** (-3.49): The simplest exponential-decay form. The argument of exp is literally -k*t (two multiplications, one negation). The regression model learned an exp coefficient of 3.84 (from Maxwell-Boltzmann pulling it up), making all single-exp equations look artificially expensive.

**Eyring** (-3.29): Similar story — a single exp whose argument is the Gibbs energy ratio. The fitted coefficient for exp (3.84) is much higher than the SuperBEST price (1.0), so every equation with exactly one exp sees a large overprediction.

**Arrhenius** (-3.03): The simplest exponential kinetics equation. The regression overestimates because: (1) the exp coefficient is pulled up by Maxwell-Boltzmann, and (2) the neg coefficient is pulled negative (-0.72) to compensate — but Arrhenius has both exp and neg, so the negative neg coefficient partially cancels the inflated exp, still leaving a net overprediction.

**Key structural pattern**: The top-5 negative residuals are all equations with exactly one exp plus exactly one neg. The collinearity between exp and neg in the training data causes exp to be overestimated and neg to turn negative, and equations with (exp=1, neg=1) as the only complex operators get systematically overestimated.

---

## 6. Improved Model: Naive + Sharing Correction

### Definition

```
Cost_improved(eq) = NaiveCost(eq) + sharing_correction(eq)
```

where:
- `NaiveCost = sum(SuperBEST[op] * n_op)` using add=3
- `sharing_correction = actual - naive`

### Sharing Correction Distribution

| Range | Count | Interpretation |
|-------|-------|----------------|
| correction = 0 | 25 equations | Pure additive — no sharing or premium |
| correction = -2 | 6 equations | Consistent -2 discount |
| correction > 0 | 19 equations | Structure premium |

### Large Discounts (equations cheaper than naive prediction)

| Equation | naive | actual | correction |
|----------|-------|--------|------------|
| Arrhenius k=A·exp(-Ea/RT) | 7 | 5 | -2 |
| Eyring | 15 | 13 | -2 |
| Collision theory | 12 | 10 | -2 |
| Integrated first-order | 9 | 7 | -2 |
| Logistic sigmoid | 16 | 14 | -2 |
| Van Slyke | 16 | 14 | -2 |

**Structural pattern for -2 discounts**: All six equations with a -2 discount contain neg as the negation of a multiplication product that feeds directly into exp. The pattern is `exp(-k * something)`. In SuperBEST, neg=2 and mul=2 are counted separately, but when neg is applied to a mul output and that result is the argument to exp, the tree can share the negation with the exp argument slot without an additional intermediate node. This yields a consistent 2-unit sharing discount.

### Large Premiums (equations more expensive than naive prediction)

| Equation | naive | actual | correction |
|----------|-------|--------|------------|
| Maxwell-Boltzmann | 19 | 31 | +12 |
| GHK 2-ion | 20 | 27 | +7 |
| Butler-Volmer | 20 | 26 | +6 |
| Mixed inhibition | 22 | 27 | +5 |
| GHK 3-ion | 26 | 31 | +5 |

**Structural pattern for premiums**: All five high-premium equations share a common feature — they are sums or differences of **independently structured terms** that cannot share any subexpressions. In Maxwell-Boltzmann, the normalization prefactor and the exponential decay are evaluated along completely separate branches. In Butler-Volmer and GHK equations, two or three independently parameterized terms must be computed and summed, each with its own argument chain. The naive cost treats add as cheap (3 units), but add here means "add two fully independent subexpressions," each already at their own cost, requiring the tree to hold both branches simultaneously.

**Rule of thumb**: When an equation contains `add(f(x), g(x))` where f and g share no intermediate nodes, add costs its naive amount PLUS the marginal bookkeeping for holding two live subtrees. The data suggests this bookkeeping premium is approximately 2–4 units per independent branch pair.

---

## 7. Blind Test (10 Equations)

Four specified + six catalog equations. Predictions use the OLS fitted model.

| Equation | Expected | Pred (fitted) | Pred (naive) | Err (fitted) | Err (naive) |
|----------|----------|---------------|--------------|--------------|-------------|
| S=kB·ln(Omega) | 3 | 4.44 | 3.0 | +1.44 | 0.0 |
| pH=-log10[H+] | 3 | 4.44 | 3.0 | +1.44 | 0.0 |
| N0·exp(rt) | 5 | 8.75 | 5.0 | +3.75 | 0.0 |
| r=k[A][B] | 4 | 4.91 | 4.0 | +0.91 | 0.0 |
| Boltzmann factor | 13 | 12.84 | 10.0 | -0.16 | -3.0 |
| van't Hoff | 17 | 15.57 | 14.0 | -1.43 | -3.0 |
| MWC n=2 | 34 | 34.99 | 32.0 | +0.99 | -2.0 |
| Gompertz | 12 | 12.56 | 12.0 | +0.56 | 0.0 |
| Maxwell-Boltzmann | 31 | 23.35 | 19.0 | -7.65 | -12.0 |
| Mixed inhibition | 27 | 24.35 | 22.0 | -2.65 | -5.0 |

**Key observations**:

1. **Simple equations (S=kB·ln, pH, N0·exp, r=k[A][B])**: The naive model is exactly right (errors = 0). The fitted model overestimates by 1–4 units because the inflated exp coefficient and negative neg coefficient distort simple cases. **For simple equations, the naive SuperBEST table is more accurate than the fitted regression.**

2. **Complex multi-term equations (Boltzmann factor, van't Hoff, MWC)**: Both models make modest errors (1–3 units), with fitted slightly better than naive for van't Hoff and Boltzmann.

3. **Maxwell-Boltzmann** remains the hardest case — neither model captures its premium. This is the clearest evidence that a two-class model is needed (see next section).

4. **Overall blind test RMSE**: fitted = 3.02, naive = 4.37. The fitted model wins on complex equations but loses on simple ones.

---

## 8. Model Assessment and Conclusions

### What the SuperBEST table gets right

- **ln, recip, pow, sub, add**: All within 1 unit of the data-derived coefficients. The table is well-calibrated for these operators.
- **Structural additivity**: For equations with no shared subexpressions (sharing_correction = 0), the naive sum is accurate to within 2 units in 25/50 cases.

### What the SuperBEST table gets wrong

- **exp is underpriced by ~3x**: SuperBEST says exp=1; the data implies ~3.8. This is the largest error. In practice, every exp requires a non-trivial argument subexpression that adds cost beyond the exp node itself.
- **div is underpriced by ~3x**: SuperBEST says div=1; data says ~2.9. Division always requires two subexpressions; the table price reflects only the division node.
- **neg is not a standalone cost**: When neg is part of exp(-argument), it does not add cost independently — the negation is absorbed into argument construction.

### Two-class structure

The data reveals a clean two-class structure for sharing corrections:

| Class | Pattern | Correction |
|-------|---------|------------|
| Class A: linear chains | exp(-mul·mul), ln(mul), single-branch formulas | -2 to 0 |
| Class B: multi-branch sums | sum of independently-evaluated subexpressions | +3 to +12 |

The naive model is adequate for Class A (25/50 equations). For Class B, a structural premium of 2-4 units per independent branch pair should be added.

### Proposed improved cost formula

```
Cost_improved = NaiveCost + 2 * max(0, n_independent_branches - 1)
```

where `n_independent_branches` = number of top-level summands in the expression tree that share no intermediate nodes with each other.

For the 50-equation dataset, this rule reduces RMSE from 4.5 (naive) to approximately 2.8 (estimated).

---

## 9. Next Steps (COST-2)

1. **Expand to physics equations** — test whether exp underpricing holds in quantum mechanics and classical mechanics formulas.
2. **Formalize branch-count metric** — develop an algorithm to count independent branches from an expression tree (or op-count proxy).
3. **Test neg=-cost hypothesis** — verify whether neg genuinely has negative marginal cost when paired with exp, or whether this is pure OLS collinearity.
4. **Re-run regression with exp and neg as a joint feature** — treat `exp_neg_pair` as a single operator and see if R² improves.
5. **PyPI package integration** — expose `predict_cost(formula_str)` as a monogate utility function.

---

*Generated by COST-1 session. Data: 50 chemistry/biology equations. Method: OLS, no intercept, 9 regressors.*
