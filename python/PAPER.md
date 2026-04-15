# Extensions to the EML Universal Operator: Hybrid Architectures and Practical Improvements

## Abstract

Odrzywołek (2026) showed that the binary operator `eml(x,y) = exp(x) − ln(y)` with constant 1 can generate all elementary functions as finite binary trees. We explore the natural family of exp–ln operators and introduce a `HybridOperator` framework called **BEST** that routes each primitive (exp, ln, mul, div, pow, add, sub) to its optimal base operator.

We highlight two particularly useful variants:
- **EDL** (`exp(x)/ln(y)` + `e`): excels at division (1 node) and multiplication (7 nodes)
- **EXL** (`exp(x)·ln(y)` + 1): achieves 1-node `ln` and 3-node `pow` with superior deep-tree stability

The `BEST` router reduces node count by 52% on average and up to 74% for Taylor approximations of `sin(x)` and `cos(x)`. It reaches machine precision (≈6.5×10⁻¹⁵) at 13 terms using 108 nodes, compared to 420 nodes for pure EML. Hybrid networks (EXL-heavy inner subtrees with an EML root) also outperform pure EML on 5 of 7 regression targets and exhibit significantly better training stability.

We release **monogate** (Python + JavaScript) with full support for EML, EDL, EXL, and the `BEST` hybrid, including a browser explorer with live BEST mode, an interactive code optimizer tab, and a `best_optimize()` Python API for annotating and rewriting functions.

**Code:** https://github.com/almaguer1986/monogate

---

## 1. Introduction

Odrzywołek (2026) established that the single binary operator `eml(x,y) = exp(x) − ln(y)`, together with the constant 1, is sufficient to express every elementary function as a finite binary tree of identical nodes. The result was discovered through exhaustive search rather than analytical construction.

This note reports practical extensions developed while building a full EML library. We implemented complete Python and JavaScript packages (`monogate`), added PyTorch autograd support for differentiable trees, and systematically explored the family of binary operators of the form `f(exp(x), ln(y))`. The main contribution is a thin `HybridOperator` class (`BEST`) that dispatches each arithmetic primitive to its most efficient known implementation. We also document several observations from gradient-based training of EML trees that relate to the open problem of exact `sin(x)` construction.

## 2. The Operator Family

We examined five natural variants of the form `f(exp(x), ln(y))`:

| Operator | Definition                  | Constant | Complete? | Strength                          |
|----------|-----------------------------|----------|-----------|-----------------------------------|
| **EML**  | `exp(x) − ln(y)`            | 1        | Yes       | Addition, subtraction             |
| **EDL**  | `exp(x) / ln(y)`            | e        | Yes       | Division, multiplication          |
| **EXL**  | `exp(x) · ln(y)`            | 1        | No        | `ln` (1 node), `pow` (3 nodes), stability |
| EAL      | `exp(x) + ln(y)`            | 1        | No        | —                                 |
| EMN      | `ln(y) − exp(x)`            | −∞       | No        | —                                 |

Only EML and EDL appear complete for the full set of elementary operations within this family. EXL, while unable to express general addition or subtraction, offers excellent numerical behavior in deep trees because it avoids the catastrophic cancellation that can occur with EML's subtraction.

## 3. HybridOperator and BEST

The `HybridOperator` class routes each primitive to its optimal base operator:

| Operation | Routed to | Nodes (BEST) | EML baseline | Saving |
|-----------|-----------|--------------|--------------|--------|
| `exp`     | EML       | 1            | 1            | 0      |
| `ln`      | EXL       | 1            | 3            | −2     |
| `pow`     | EXL       | 3            | 15           | −12    |
| `mul`     | EDL       | 7            | 13           | −6     |
| `div`     | EDL       | 1            | ~15          | −14    |
| `recip`   | EDL       | 2            | 5            | −3     |
| `neg`     | EDL       | 6            | 9            | −3     |
| `sub`     | EML       | 5            | 5            | 0      |
| `add`     | EML       | 11           | 11           | 0      |

Overall: 37 nodes vs 77 for pure EML (52% reduction). For Taylor series of `sin(x)` and `cos(x)`, savings reach 74% because each term benefits heavily from cheap `pow` and `div`.

**Taylor sin(x) node counts:**

| Terms | BEST nodes | EML-only nodes | Max error     |
|-------|------------|----------------|---------------|
| 8     | 63         | 245            | 7.7×10⁻⁷     |
| 13    | 108        | 420            | 6.5×10⁻¹⁵    |

## 4. Experimental Results

The operator family was implemented in Python (`pip install monogate`) and JavaScript (`npm install monogate`), with 314 and 109 passing tests respectively. The Python version includes differentiable trees via PyTorch autograd and a `best_optimize()` utility that rewrites arbitrary Python expressions and decorated functions to use BEST-mode routing, reporting per-operation node savings and generating AST-rewritten source snippets.

Hybrid networks (EXL-heavy inner structure with EML root) outperformed pure EML on 5 of 7 regression targets (including `sin(x)` and `cos(x)`) and showed markedly better deep-tree stability. Pure EML networks frequently encounter NaN during training due to negative arguments to `ln`; EXL avoids this issue naturally.

Gradient-based searches also revealed a rugged optimization landscape containing many locally optimal but non-minimal constructions ("phantom attractors").

## 5. Conclusion and Open Problems

The `BEST` hybrid shows that intelligently combining variants of EML can produce substantially more efficient and stable trees than any single operator. The released `monogate` library makes these techniques immediately usable in both Python and the browser.

**Open problems:**
- Is there a finite EML tree using only terminal `{1}` that evaluates exactly to `sin(x)`?
- Can discrete search methods (MCTS, exhaustive enumeration) reliably escape phantom attractors?
- Is EDL fully complete over the elementary functions, or only the multiplicative group?

## References

Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852v2 [cs.SC].

monogate repository: https://github.com/almaguer1986/monogate
