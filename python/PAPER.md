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

### 4.1 GELU activation

The GELU activation function (Hendrycks & Gimpel, 2016) used in GPT/BERT can be expressed via the tanh approximation `0.5·x·(1 + tanh(√(2/π)·(x + 0.044715·x³)))`. In EML arithmetic this requires `exp` (1 node) + `add` (11 nodes) + `recip` (5 nodes) = **17 nodes**. BEST routing replaces `recip_eml` with `recip_edl` (2 nodes), reducing to **14 nodes** — an 18% saving with identical accuracy (max error < 1.4×10⁻¹²).

### 4.2 Wall-clock impact: savings must exceed call overhead

Node-count reductions translate to wall-clock speedup only when the saving is large enough to amortise Python function-call overhead. We measured two regimes:

**experiment_09 — TinyMLP with sin activation** (2-layer MLP, input 1 → hidden 16 → output 1, batch 64):

| Configuration     | ms / forward | Speedup |
|-------------------|-------------|---------|
| EML-sin (245 nodes) | 39.3      | 1×      |
| BEST-sin (63 nodes) | 14.1      | **2.8×** |
| torch.sin (native)  | 0.09      | 440×    |

The 74% node reduction in `sin` yields a **2.8× end-to-end speedup** in EML-arithmetic mode.

**experiment_10 — Transformer FFN with GELU** (4× FFN block, d=16, hidden=64, batch 8, Python 3.14 CPU):

| Configuration   | ms / forward | Relative speedup |
|-----------------|-------------|-----------------|
| native math     | 1.771       | —               |
| EML-GELU (17n)  | 4.736       | 1× (baseline)   |
| BEST-GELU (14n) | 5.115       | ~0.93×          |

The 18% node reduction in GELU is insufficient to overcome Python call overhead at typical batch sizes.

**experiment_11 — Polynomial activation x⁴+x³+x²** (scalar batch of 512, Python 3.14 CPU):

| Configuration    | ms / batch | us / elem | Speedup |
|------------------|-----------|-----------|---------|
| EML-poly (67n)   | 10.22     | 19.96     | 1×      |
| BEST-poly (31n)  | 4.93      | 9.62      | **2.08×** |

The 53.7% node reduction in the polynomial activation yields a **2.08× speedup**, confirming that the crossover lies between GELU (18%) and sin (74%). Fitting a linear model through all three data points (R²=0.9992):

> **speedup ≈ 0.033 × savings_pct + 0.32**

Linear interpolation suggests the crossover occurs at approximately **20% node reduction**. Below that threshold, Python function-call overhead dominates and BEST routing is marginally slower; above it, gate savings translate to measurable wall-clock gains. The full three-experiment comparison is shown below:

| Experiment | Nodes EML | Nodes BEST | Savings | Speedup |
|-----------|-----------|-----------|---------|---------|
| sin/cos (exp_09) | 245 | 63 | 74% | 2.8× |
| poly (exp_11) | 67 | 31 | 54% | 2.1× |
| GELU (exp_10) | 17 | 14 | 18% | 0.93× |

Activations with node reductions above ~20% (sin, cos, polynomial expressions heavy in `pow`) benefit substantially from BEST routing; those below the threshold (GELU with 18% reduction) do not, at typical Python batch sizes.

## 5. Phantom Attractors and Training Dynamics

### 5.1 Characterization

Gradient-based training of `EMLTree` with Adam exhibits a rugged loss landscape dominated by a small number of stable non-target local optima. We term these *phantom attractors*: configurations where the tree converges to a semantically wrong but highly stable constant.

In systematic experiments fitting `EMLTree(depth=3)` to π across 40 random seeds (`experiments/research_02_attractors.py`), without a complexity penalty **100% of runs (40/40) converge to the same wrong value** — approximately 3.1696 — with a final loss of ~9×10⁻⁴. Not a single run reaches π (loss < 10⁻⁴) despite 3000 Adam steps.

The dominant attractor at ≈3.1696 is not a simple EML constant — it is a depth-3 tree configuration that approximates π to 1.4% error and sits at the center of an unusually wide gradient basin. The gradient signal from MSE loss cannot distinguish this basin from the true target basin, because any random initialization falls within the attractor's catchment area.

These attractors are not arbitrary — they correspond to efficient expressions in the EML grammar:

- **`e` ≈ 2.718**: `E = op(1,1)` requires only 1 node — the identity of EML
- **`1.0`**: the terminal constant, zero cost
- **`2.0`** and **`3.0`**: constructible in 3–5 nodes via standard EML identities
- **≈3.1696**: the dominant attractor for π targets — a depth-3 configuration that no known EML simplification reduces further

The gradient signal from MSE loss is insufficient to distinguish these attractors from the true target when the tree's random initialization falls in their catchment region.

### 5.2 Escape Strategies

Three approaches reliably reduce attractor entrapment:

**Complexity penalty (`lam > 0`).** Adding an L1 penalty on the distance of leaf parameters from 1.0 discourages the tree from settling in non-identity positions. Measured result: `lam=0` → 0/20 converge; `lam=0.005` → **20/20 converge**. The effect is dramatic and immediate — even a tiny penalty of 0.005 completely eliminates the dominant attractor basin for depth-3 π fitting. This is the single most effective and cheapest escape strategy.

```python
losses = fit(model, target=torch.tensor(math.pi), steps=3000, lr=5e-3, lam=0.01)
```

**Ensemble probing.** Running K short (250-step) exploratory fits from different seeds and selecting the lowest-loss probe before refining substantially improves the probability of escaping attractors. Measured result: K=3 probes already achieves 8/8 success rate (100%), adding only ~0.9 s/run overhead. This strategy works even without `lam` because different seeds may initialize outside the dominant attractor basin.

```python
probes = []
for seed in range(5):
    torch.manual_seed(seed)
    m = EMLTree(depth=3)
    ls = fit(m, target=target, steps=250, lr=5e-3, log_every=0)
    probes.append((ls[-1], m))
_, best = min(probes, key=lambda x: x[0])
losses = fit(best, target=target, steps=3000, lr=1e-3, log_every=0)
```

**Temperature scheduling.** Starting with a higher learning rate (or wider random initialization) and annealing forces the tree to explore broader regions before settling. This is less robust than ensemble probing in practice but is cheap to combine with it.

### 5.3 Implications for Exact `sin(x)` Construction

The phantom attractor problem bears directly on the open question of whether a finite EML tree from terminal `{1}` can represent `sin(x)` exactly. Gradient-based search with `EMLNetwork` targeting `sin` consistently identifies good Taylor approximations but never produces candidate constructions with period-correct behavior beyond what the Taylor expansion provides.

Two structural observations:

1. **`sin(x)` is transcendental.** No finite expression built from algebraic operations (including the `exp`/`ln` in EML gates) can produce the exact sine function. The question is therefore not "is there an algebraic formula" but rather "does the limit of nested EML trees converge to `sin`" — and whether an *infinite* but finitely-representable construction exists.

2. **Phantom attractors confound search.** For any finite target evaluation (e.g. `sin(π/4) = √2/2`), the EML landscape contains many nearby non-`sin` attractors that match the target at specific probe points. Exhaustive construction via gradient descent is therefore unreliable for exact `sin` search.

The current best practical path remains the BEST-routed Taylor series: 63 nodes for 8-term (7.7×10⁻⁷ max error), 108 nodes for 13-term (machine precision). These are not exact but are computable and compact.

---

## 6. Exact `sin(x)` from Terminal `{1}` — Open Problem Analysis

### 6.1 Theoretical Constraints

The problem asks: does there exist a finite binary tree where every leaf is the constant `1`, every internal node computes `eml(left, right) = exp(left) − ln(right)`, and the resulting tree evaluates to exactly `sin(x)` for all real `x`?

**Known constraints:**

- The Lindemann–Weierstrass theorem implies `sin(x)` is transcendental over the field of algebraic numbers. Any finite EML tree with algebraic leaf constants would produce an elementary function in the sense of Liouville, but not necessarily `sin`. The question is whether EML transcends Liouville elementarity.

- The EML grammar `S → 1 | eml(S, S)` is equivalent to compositions of `exp`, `ln`, `−`, and `+` (via `eml(x,y) = exp(x) − ln(y)`, `eml(exp(a), exp(b)) = a − b`, etc.). This is exactly the set of Liouville elementary functions of constant depth.

- `sin(x)` can be expressed via the Euler identity `sin(x) = (e^{ix} − e^{−ix})/(2i)`, which requires complex arithmetic. Under the extended-reals convention used by `pow_exl` (which returns complex intermediate values), partial sin constructions are reachable.

**Current status:** No finite EML tree from terminal `{1}` that equals `sin(x)` everywhere is known. The challenge leaderboard ([monogate.dev/board](https://monogate.dev)) tracks the best known constructions.

### 6.2 Known Constructions

The best known approximation in the EML substrate is the BEST-routed Taylor series:

```
sin(x) ≈ x − x³/6 + x⁵/120 − x⁷/5040 + ...
```

Using BEST routing (EXL for pow, EML for add/sub), each Taylor term costs:
- `x^(2k+1) / (2k+1)!` → 3 nodes for pow + 1 for div + 5 for sub = 9 nodes/term
- 8-term expansion: 63 nodes total, max error 7.7×10⁻⁷

A closed-form alternative via complex EXL arithmetic:

```
sin(x) ≈ Im(exl(ix, 1)) for small x  [not globally correct]
```

This works locally but fails for |x| > π/2 due to branch cuts.

### 6.3 Search Directions

Promising avenues for future work:

1. **Exhaustive depth enumeration.** Trees of depth ≤ 5 from terminal `{1}` can be enumerated (~2^31 candidates). Evaluating each against `sin(0.5), sin(1.0), sin(1.5)` and checking periodicity would rule out all small constructions definitively or find one.

2. **Symmetry reduction.** `sin(x)` is odd: any candidate tree must satisfy `T(−x) = −T(x)`. Trees with symmetric left/right sub-expressions can be filtered by parity at negligible cost.

3. **MCTS with EML grammar.** Monte Carlo tree search can explore the grammar tree with rollout evaluation against multiple sin test points, avoiding gradient-descent attractor issues entirely.

4. **Complex EML grammar.** Admitting `i` as a terminal extends the grammar while remaining within the EML formalism. The Euler identity becomes directly expressible, and `sin(x)` can be extracted from the imaginary part of a 3-node EXL construction. Whether this satisfies the "terminal `{1}`" constraint depends on whether `i` can itself be constructed finitely in EML arithmetic.

---

## 7. Conclusion and Open Problems

The `BEST` hybrid demonstrates that intelligently combining variants of EML can produce substantially more efficient and stable trees than any single operator. The released `monogate` library makes these techniques immediately usable in both Python and the browser.

**Open problems:**
- Is there a finite EML tree using only terminal `{1}` that evaluates exactly to `sin(x)`?
- Can discrete search methods (MCTS, exhaustive enumeration) reliably escape phantom attractors?
- Is EDL fully complete over the elementary functions, or only the multiplicative group?

## References

Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852v2 [cs.SC].

monogate repository: https://github.com/almaguer1986/monogate
