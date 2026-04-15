# Extensions to the EML Universal Operator: Hybrid Architectures and Practical Improvements

## Abstract

Odrzywołek (2026) showed that the binary operator eml(x,y) = exp(x) − ln(y) with constant 1 generates all elementary functions as finite binary trees. We explore the broader family of exp-ln operators and introduce a HybridOperator framework that routes each primitive (exp, ln, mul, div, pow, add, sub) to its optimal base operator.

Among the natural variants, we identify:
- **EDL** (`exp(x)/ln(y)` + e): excels at division and multiplication
- **EXL** (`exp(x)·ln(y)` + 1): achieves 1-node ln and 3-node pow with superior numerical stability

A hybrid router (`BEST`) reduces node count by 52% on average and up to 74% for Taylor approximations of sin(x) and cos(x), reaching machine precision (≈6.5e-15) at 13 terms using 108 nodes versus 420 for pure EML. Gradient-based regression experiments reveal that hybrid networks (EXL inner subtrees + EML root) outperform pure-EML on 5/7 tested targets and exhibit significantly better deep-tree stability.

We release monogate (Python + JavaScript) with full support for EML, EDL, EXL, and the BEST hybrid, including a browser explorer with live BEST mode.

Code: https://github.com/almaguer1986/monogate

---

## 1. Introduction

Odrzywołek (2026) established an unexpected result: the binary operator eml(x,y) = exp(x) − ln(y), paired with the constant 1, is sufficient to express every elementary arithmetic function as a finite binary tree. The result was found by exhaustive search rather than mathematical construction, and no comparable single-primitive system had previously been known for continuous mathematics.

This note reports extensions developed through systematic implementation of the EML framework. We implemented a complete EML arithmetic library in Python and JavaScript, built a gradient-based symbolic regression engine, and investigated the broader family of binary operators of the form f(exp(x), ln(y)). The main practical result is a HybridOperator framework — BEST — that routes each arithmetic primitive to the operator with fewest nodes, reducing tree size by 52–74% over pure EML. We also report several observations from gradient-based EML tree training that bear on the difficulty of the open sin(x) problem.

## 2. The Operator Family

We consider five natural binary operators of the form f(exp(x), ln(y)):

| Operator | Gate | Constant | Complete? | Best operation |
|----------|------|----------|-----------|----------------|
| **EML** | `exp(x) − ln(y)` | 1 | Yes | sub (5n), add (11n) |
| **EDL** | `exp(x) / ln(y)` | e | Yes | div (1n), mul (7n) |
| **EXL** | `exp(x) · ln(y)` | 1 | No  | ln (1n), pow (3n) |
| EAL | `exp(x) + ln(y)` | 1 | No  | — |
| EMN | `ln(y) − exp(x)` | 1 | No  | — |

Within the natural exp-ln family, only EML and EDL appear complete for the full set of elementary arithmetic operations. EXL cannot construct arbitrary addition or subtraction — there is no known finite EXL tree for a + b with general real inputs — making it incomplete in this sense. EAL and EMN similarly fail to close over elementary arithmetic.

EXL is numerically superior for deep trees: unlike EML, whose subtraction can produce catastrophic cancellation when exp(x) ≈ ln(y), EXL involves only multiplication of positive quantities. Random initializations are therefore less likely to produce NaN or overflow during training.

EDL has a singularity at y=1 (ln(1)=0) that makes naive training unstable. A shifted variant edl_safe(x,y) = exp(x) / ln(y+1+ε) avoids the singularity at the cost of shifting the natural constant from e to e−1.

## 3. HybridOperator and BEST

We introduce a thin HybridOperator class that routes each arithmetic primitive to its cheapest known implementation:

| Operation | Operator | Nodes | EML baseline | Saving |
|-----------|----------|-------|--------------|--------|
| exp | EML | 1 | 1 | — |
| ln | EXL | 1 | 3 | −2 |
| pow | EXL | 3 | 15 | −12 |
| mul | EDL | 7 | 13 | −6 |
| div | EDL | 1 | 15 | −14 |
| recip | EDL | 2 | 5 | −3 |
| neg | EDL | 6 | 9 | −3 |
| sub | EML | 5 | 5 | — |
| add | EML | 11 | 11 | — |

Total: 37 nodes versus 77 for all-EML — a 52% reduction. Addition and subtraction remain on EML because no other operator in the family supports arbitrary a ± b; this makes EML structurally irreplaceable even in a hybrid system.

### Taylor sin(x)

For polynomial expressions, savings are larger because pow and div dominate. Applied to the Taylor series sin(x) = x − x³/6 + x⁵/120 − …:

| Terms | BEST nodes | EML-only nodes | Saving | Max error |
|-------|------------|----------------|--------|-----------|
| 4  | 27  | 105 | 74% | 7.5e-02 |
| 6  | 45  | 175 | 74% | 4.5e-04 |
| 8  | 63  | 245 | 74% | 7.7e-07 |
| 10 | 81  | 315 | 74% | 5.3e-10 |
| 12 | 99  | 385 | 74% | 1.8e-13 |
| 13 | 108 | 420 | 74% | 6.5e-15 |

The 74% saving is consistent across all term counts because each term contains exactly one pow and one div, and these are the operations where BEST gains most.

## 4. Experimental Results

**Library.** We implemented EML, EDL, EXL, EAL, and EMN in Python and JavaScript with full test coverage (109 JavaScript tests, 299 Python tests). The Python implementation includes differentiable EML trees via PyTorch autograd. All experiments ran on CPU in float32 (float64 for analytical verification).

**Gradient-based regression.** We trained EMLNetwork (affine leaves, softplus gating on right arguments) on seven regression targets: sin(x), cos(x), exp(x), x², x³, a degree-4 polynomial, and a mixed exponential-polynomial. HybridNetwork (EXL inner nodes, EML root) outperformed pure-EML on 5 of 7 targets by median MSE across 5 restarts, with the largest gains on sin(x) and cos(x) where EML suffered from training instability.

**Stability.** Pure EML networks fail frequently on deep trees: right-argument leaves drift negative early in training, log(negative) produces NaN, and Adam freezes at a bad basin. Softplus gating (ln(1+eˣ)) on right children fixes this for EMLNetwork. EXL networks do not require this fix because the product exp(x)·ln(y) is well-behaved for positive y.

**Observations from gradient search.** Training EMLTree on scalar targets revealed several behaviors worth noting. Gradient descent consistently found non-minimal constructions: targeting e produced eml(eml(0.45, 1), eml(1, 1)) rather than the one-node eml(1,1). These locally stable non-minimal solutions persisted across all restarts and resisted complexity penalties (λ from 0.01 to 2.0); enforcing minimality via leaf-pull-to-1 penalty cost 10,518% MSE. The right-chain topology with all-ones leaves converges to W(eᵉ) ≈ 2.0168 — the fixed point of y → e − ln(y) — connecting EML iteration to Lambert W theory. Strong leaf constraints drive right-chain outputs to this constant regardless of depth, confirming that affine leaves (not scalar terminals) are necessary for periodic function approximation under this topology class.

## 5. Conclusion and Open Problems

The BEST hybrid achieves substantially more efficient trees than any single operator in the exp-ln family, with a 52% average node reduction and 74% for Taylor polynomial patterns. HybridNetwork outperforms pure-EML on most regression targets. The practical library (monogate) ships with full support for EML, EDL, EXL, and BEST, with a browser explorer at monogate.dev.

**Open problems:**

- Does any finite EML tree with terminal {1} evaluate to sin(x) exactly? Right-chain topologies are ruled out by the affine leaf necessity result; other topology classes remain open.
- Can locally-stable non-minimal solutions (phantom attractors) be escaped by discrete search (MCTS, exhaustive enumeration)? Infrastructure for this is available at monogate.dev/search.
- Is there an analytical explanation for why right-chain EML iteration converges to W(eᵉ) rather than another fixed point?
- Is EDL complete over the full elementary function set, or only over the multiplicative group?

## References

Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852v2 [cs.SC].

monogate — community implementation and extensions. https://github.com/almaguer1986/monogate

npm: https://npmjs.com/package/monogate · PyPI: https://pypi.org/project/monogate
