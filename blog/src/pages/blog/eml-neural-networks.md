---
title: "EML Meets Neural Networks"
subtitle: "What happens when you put a 1-operator symbolic head on a DNN"
date: 2026-04-20
tags: [neural-networks, symbolic-regression, eml, cost-theory]
author: "Arturo R. Almaguer"
---

# EML Meets Neural Networks

_What happens when you put a 1-operator symbolic head on a DNN_

---

The standard story for neural networks and symbolic regression goes like this: first you train a DNN until it fits the data, then you run something like PySR or gplearn over the residuals to find a closed-form approximation. The DNN is a black box. The symbolic part happens after the fact, separately, with no shared structure.

This post explores a different idea. What if the DNN trunk and the symbolic head share the same mathematical vocabulary? Specifically: what if every activation function in the network is itself a cheap EML operator, and the symbolic head tries to distil the whole thing into one small expression?

The answer turns out to depend almost entirely on what the target function is built from.

---

## The Architecture

The hybrid setup is straightforward. A DNN trunk — a few dense layers — extracts features from raw inputs. The final layer feeds into an EML symbolic head: a small tree of operators from the monogate family (eml(x,y) = exp(x) − ln(y) and its cousins). The head tries to compress what the trunk learned into a closed-form expression.

Training has two phases. First, standard backpropagation trains the full network end-to-end. Second, a distillation pass searches for the smallest EML tree that matches the trunk's output on the training distribution.

The SuperBEST v4 cost system assigns each operator a cost in n-units:

| Operator | Cost |
|----------|------|
| exp, ln, recip | 1n each |
| neg, mul, sub, div, sqrt | 2n each |
| pow | 3n |
| add_pos | 3n |
| add_gen | 11n |

The cost of an expression is the sum of its operator costs. The goal of distillation is to find the lowest-cost EML tree that represents the function the DNN learned.

---

## The D=4 Gradient Wall

There is a problem with pure EML trees as the architecture for every layer: they become untrainable past depth 3 or 4.

The issue is exponential gradient growth. Consider a 4-layer EML tree where each layer applies exp(·). The gradient of the output with respect to the first-layer input involves a product of four exp values. For inputs with magnitude greater than ~2, this product explodes. Backpropagation diverges.

DEML fixes this. The operator DEML(x, r) = exp(−x) − ln(r) uses exp(−x) instead of exp(x). The gradient of exp(−x) with respect to x is −exp(−x), which stays in (−1, 0) for all x > 0. The dampening is structural: adding the minus sign in the exponent bounds the gradient magnitude at each layer.

The LEAd operator (= softplus) fixes it in a different way. LEAd(x, r) = ln(exp(x) + r). Its gradient with respect to x is σ(x) = 1/(1 + exp(−x)), the sigmoid function. Sigmoid stays in (0, 1) for all real x. No explosion, no vanishing. This is why LEAd is the recommended activation for EML hybrid networks.

---

## Activation Function Costs: The Headline Number

The headline result from NN-7 is a single equation:

**softplus(x) = ln(1 + exp(x)) = LEAd(x, 1) = 1n**

Softplus is not just EML-friendly — it *is* an EML primitive. When the DNN uses softplus activations throughout, every layer of the network is a 1n EML operation. The symbolic head can, in principle, read the whole network as one big EML expression and compress it.

The full activation shootout:

| Activation | Formula | SuperBEST cost | Gradient | PINN suitable |
|------------|---------|----------------|----------|---------------|
| softplus | ln(1+exp(x)) | **1n** | σ(x) ∈ (0,1) | Yes |
| sigmoid | 1/(1+exp(−x)) | 7n | σ(x)(1−σ(x)) | No |
| tanh | (exp(x)−exp(−x))/(exp(x)+exp(−x)) | 9n | 1−tanh²(x) | No |
| Swish | x·σ(x) | 9n | complex | No |
| ReLU | max(0, x) | N/A | 0 or 1 | No |
| GELU | x·Φ(x) | N/A (erf not in EML) | smooth | No |

ReLU and GELU are not in the EML operator closure. No finite EML tree represents them exactly. Distillation fails by definition when the activations are ReLU.

**The PINN insight.** Physics equations are built from exp and ln. Arrhenius kinetics is A·exp(−Ea/RT). Boltzmann distributions are exp(−E/kT)/Z. Entropy is −Σ p·ln(p). When the activation IS a 1n EML operator, the network layers speak the same mathematical language as the physics. Distillation recovers the physics equation, not just an approximation.

---

## Where EML Wins: Transcendental Targets

EML has a structural advantage on any target built from exp, ln, or trig (via the CEML complex extension).

From the NN-6 SR benchmark analysis across 10 standard functions:

**EML wins (5 functions):**

- **Nguyen-7** — log(x+1) + log(x²+1): 14n total. PySR needs a Taylor or rational approximation for log. EML computes ln in 1n.
- **Feynman-I.6.20** — exp(−θ²/2)/√(2π): 8n total. DEML routes exp(−θ²/2) in 1n.
- **Korns-12** — 2 − 2.1·cos(9.8x)·sin(1.3y): 12n total. Trig via CEML costs 1n each. PySR needs a 20-40 node Taylor expansion.
- **Strogatz-1** — −sin(x): 3n total. CEML for sin + neg. Minimal.
- **Custom-1** — exp(−x)·sin(2πx): 6n total. DEML for exp(−x) in 1n, CEML for sin in 1n. PySR must approximate both simultaneously.

The pattern is clear: if the target is what physics textbooks call a transcendental function, EML finds a compact closed form. PySR finds an approximation requiring many more nodes.

---

## Where EML Loses: Polynomial Targets

**EML loses (3 functions):**

- **Nguyen-1** — x³ + x² + x: 28n with add_gen (or 12n if x > 0). PySR: ~3-5 nodes.
- **Nguyen-4** — x⁶ + x⁵ + x⁴ + x³ + x² + x: 70n with add_gen. PySR: ~8-12 nodes.
- **Livermore-2** — (x−3)² + (x−3)³: 11n. PySR: ~5-7 nodes.

The structural reason is add_gen. General addition costs 11n in SuperBEST v4 because it requires routing through the full 11-operator sub-expression. Polynomials need many additions. A 6-term polynomial like Nguyen-4 needs 5 additions at 11n each — 55n just for the additions, on top of the 15n for the power terms.

Polynomial SR tools (PySR, gplearn) represent addition and multiplication as 1-node operations. They win on polynomials by design. EML's cost structure penalises addition because exp(x) − ln(y) is the native operation, not x + y.

**The honest score: 5 wins, 3 losses, 2 neutral out of 10 standard benchmarks.**

EML symbolic heads are not general-purpose symbolic regression. They are specialised tools for physics-informed targets built from the exp-ln family.

---

## Expression Distillation: What Actually Works

The NN-8 distillation analysis covers five canonical targets:

| Target | EML cost | Completeness | Prediction |
|--------|----------|-------------|------------|
| Arrhenius A·exp(−Ea/RT) | 7n | Complete | Success |
| sigmoid 1/(1+exp(−x)) | 7n | Complete | Success |
| polynomial x³+x | 14n | Complete | Success (slow) |
| sin(x) | N/A | **Incomplete** | Fails |
| ReLU max(0,x) | N/A | **Incomplete** | Fails |

The completeness theorem explains the failure cases:

**sin(x) fails** because it has infinitely many real zeros (at x = nπ for all integers n). Any EML expression has at most finitely many real zeros — exp(g(x)) = ln(h(x)) produces isolated solutions, not an infinite discrete set. No finite EML tree can equal sin(x) on all of ℝ.

**ReLU fails** because EML expressions are smooth (C-∞, since exp and ln are analytic). ReLU has a non-differentiable kink at x = 0. A smooth function cannot equal a non-smooth one on any open interval.

Compression ratios when distillation succeeds are substantial. A 500-parameter MLP trained to compute Arrhenius kinetics distils to a 5-node EML tree: roughly 100:1 compression. The distilled expression is exact on the training distribution, not an approximation.

---

## Operator Subset Architecture Search

NN-9 evaluated six operator subsets across the five targets above. The key finding:

**{EML, DEML, LEAd} is the sweet spot.**

Expected success rates for this subset:
- Arrhenius: 95%
- sigmoid: 92%
- polynomial x³+x: 55% (add_gen not in subset — approximate only)
- sin(x): 5% (fundamentally incomplete)
- ReLU: 10% (softplus approximation only)

The full F16 set achieves lower rates on most targets despite higher expressivity, because the heterogeneous gradient magnitudes (add_gen contributes 11n worth of gradient signal vs 1n for the exp operators) make training unstable.

The recommendation stands: use {EML, DEML, LEAd} for PINN hybrid architectures. Add CEML only if trig targets are required.

---

## Honest Conclusion

EML symbolic heads are a specialised tool. They work well — sometimes remarkably well — when the target function is built from the same mathematical atoms as the EML operator family: exponentials, logarithms, and their combinations.

They do not work well on polynomials, because the addition operator is expensive in EML's cost structure. They cannot work at all on trigonometric or piecewise functions by completeness theory.

The practical scope is narrower than general symbolic regression but precisely matched to one important domain: physics-informed machine learning. Arrhenius kinetics, Boltzmann distributions, chemical equilibria, log-linear models — these are all native EML territory. For these targets, a DNN with softplus activations and an EML symbolic head can distil the learned function into an exact closed-form expression at ~100:1 compression.

That is a specific, honest, and useful result.

---

_Monogate project — sessions NN-1 through NN-10. Source: [github.com/almagu/monogate](https://github.com/almagu/monogate)._
