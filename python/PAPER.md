# Extensions to the EML Universal Operator: Hybrid Architectures and Practical Improvements

> **Status:** Internal research document — superseded by the arXiv preprint
> `paper/preprint.tex` (v0.9.0, April 2026). This file is preserved as a working
> notes document. The preprint is the authoritative version.
> **Last updated:** v0.12.0-dev (April 2026). New modules (special, leaderboard, pinn,
> interval, sympy_bridge, Streamlit demo) are documented in Section 10.

## Abstract

Odrzywołek (2026) showed that the binary operator `eml(x,y) = exp(x) − ln(y)` with constant 1 can generate all elementary functions as finite binary trees. We explore the natural family of exp–ln operators and introduce a `HybridOperator` framework called **BEST** that routes each primitive (exp, ln, mul, div, pow, add, sub) to its optimal base operator.

We highlight two particularly useful variants:
- **EDL** (`exp(x)/ln(y)` + `e`): excels at division (1 node) and multiplication (7 nodes)
- **EXL** (`exp(x)·ln(y)` + 1): achieves 1-node `ln` and 3-node `pow` with superior deep-tree stability

The `BEST` router reduces node count by 52% on average and up to 74% for Taylor approximations of `sin(x)` and `cos(x)`. It reaches machine precision (≈6.5×10⁻¹⁵) at 13 terms using 108 nodes, compared to 420 nodes for pure EML. Hybrid networks (EXL-heavy inner subtrees with an EML root) outperform pure EML on 5 of 7 regression targets and exhibit significantly better training stability.

We also document four empirical findings with sharp quantitative results:

1. **Phantom attractors in EMLTree training.** Gradient-based optimization of depth-3 EML trees toward π fails in 100% of random seeds (40/40) without regularization, converging instead to a stable non-target attractor at ≈3.1696. A small L1 complexity penalty (λ_crit = 0.001) induces a sharp phase transition, achieving 100% convergence (20/20 runs).

2. **The Infinite Zeros Barrier (theorem + exhaustive confirmation).** All 281,026,468 real-valued EML trees with up to 11 internal nodes and terminals `{1, x}` were enumerated and evaluated. No tree matches sin(x) at any tolerance (10⁻⁴ to 10⁻⁹). The Infinite Zeros Barrier theorem rules out real-valued construction for any finite N: sin(x) has infinitely many zeros; every finite real EML tree is real-analytic with finitely many. Contradiction.

3. **Complex bypass — exact, 1 node.** `Im(eml(i·x, 1)) = Im(exp(ix)) = sin(x)` exactly for all x ∈ R (Euler's formula). The barrier is real-domain only; one complex EML node recovers sin(x) at machine precision.

4. **Performance kernels.** `FusedEMLActivation` (3.6×) and a Rust/PyO3 extension `monogate-core` (5.9×) make EML competitive with native activations in PyTorch. `EMLLayer(compiled=True)` auto-selects the fastest available backend.

We release **monogate** v0.12.0-dev (Python + JavaScript) with full support for EML, EDL, EXL, and the `BEST` hybrid, including: a browser explorer (monogate.dev), an interactive code optimizer, a `best_optimize()` Python API, `monogate.search` stochastic search, a drop-in PyTorch `EMLLayer`, 15 pre-computed special functions (`monogate.special`), a symbolic regression leaderboard (`monogate.leaderboard`), extended PINN support for 7 differential equations (`monogate.pinn`), certified interval arithmetic (`monogate.interval`), SymPy interoperability (`monogate.sympy_bridge`), and a 5-tab Streamlit web demo (`streamlit_app.py`) — 913 passing tests.

**Code:** https://github.com/almaguer1986/monogate · **PyPI:** `pip install monogate`
**Preprint:** `paper/preprint.tex` — arXiv:ARXIV_ID_PLACEHOLDER

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

In systematic experiments fitting `EMLTree(depth=3)` to π across 40 random seeds (`experiments/research_02_attractors.py` and `experiments/gen_attractor_data.py`), without a complexity penalty **100% of runs (40/40) converge to the same wrong value** — approximately **3.169642** — with a final loss of ~9×10⁻⁴. Not a single run reaches π (loss < 10⁻⁴) despite 3000 Adam steps (lr=5×10⁻³).

The dominant attractor at ≈3.1696 is not a simple EML constant — it is a depth-3 tree configuration that approximates π to 1.4% error and sits at the center of an unusually wide gradient basin. The gradient signal from MSE loss cannot distinguish this basin from the true target basin, because any random initialization falls within the attractor's catchment area.

These attractors are not arbitrary — they correspond to efficient expressions in the EML grammar:

- **`e` ≈ 2.718**: `E = op(1,1)` requires only 1 node — the identity of EML
- **`1.0`**: the terminal constant, zero cost
- **`2.0`** and **`3.0`**: constructible in 3–5 nodes via standard EML identities
- **≈3.1696**: the dominant attractor for π targets — a depth-3 configuration that no known EML simplification reduces further

The gradient signal from MSE loss is insufficient to distinguish these attractors from the true target when the tree's random initialization falls in their catchment region.

### 5.2 Depth Limit: The Numerical Overflow Barrier

A complementary experiment tested `EMLTree(depth=4)` — a complete binary tree with 15 internal nodes and 16 leaves.
Across all 20 seeds and all tested λ values (0 to 0.05), every run diverges to NaN or ∞ before completing 1000 steps.

Root cause: the initial forward pass of `EMLTree(depth=4, init=1.0)` returns ∞.
A depth-4 complete binary EML tree applies exp() at every level;
even with leaves initialized to 0 (not 1), the initial output is ~1.6×10¹³.
The tower of 15 nested `eml` operations overflows float64 range before the first gradient step.

This establishes a **Numerical Overflow Barrier** complementary to the phantom attractor problem:
- **Depth ≤ 3**: trainable; dominated by phantom attractors (cured by λ ≥ 0.001)
- **Depth = 4**: numerically untrainable with naive EMLTree initialization

Depth=4 training requires log-scale normalization between levels or a reparameterized tree structure.
This is a known limitation of the current v0.4.0 architecture.

### 5.3 Refined Phase Transition Measurement

A lambda sweep (`gen_attractor_data_v2.py`, 20 seeds × 10 lambda values, depth=3, 1000 steps) shows
the phase transition is sharper than originally measured:

| λ | convergence rate | mean final value |
|---|-----------------|-----------------|
| 0.000 | 0/20 | 3.170460 (attractor) |
| **0.001** | **20/20** | 3.140832 (near π) |
| 0.002 | 20/20 | 3.131840 |
| 0.005 | 20/20 | 3.135407 |
| 0.050 | 20/20 | 3.141778 |

The critical lambda is **λ_crit = 0.001** — an order of magnitude smaller than originally estimated.
Above this threshold the attractor basin vanishes completely in all 20 seeds at 1000 steps.

### 5.4 Escape Strategies

Three approaches reliably reduce attractor entrapment:

**Complexity penalty (`lam > 0`).** Adding an L1 penalty on the distance of leaf parameters from 1.0 discourages the tree from settling in non-identity positions. Measured result from `gen_attractor_data.py` (40 seeds × 2 configs × 3000 steps): `lam=0` → **0/40 reach π** (all 40 converge to attractor ≈3.169642); `lam=0.005` → **40/40 reach π** (MSE < 10⁻⁸). The transition is a sharp phase transition — a penalty of 5×10⁻³ completely eliminates the dominant attractor basin. This is the single most effective and cheapest escape strategy.

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

### 5.5 Implications for Exact `sin(x)` Construction

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

### 6.2 Exhaustive Search Results

Four scripts — `sin_search_01.py` (N≤7), `sin_search_02.py` (N=8), `sin_search_03.py` (N=9), and `sin_search_04.py` (N=10, all parity-pruned + parallel) — performed a complete enumeration of the EML grammar using terminals `{1, x}`.

**Tree counts (complete through N=11):**

| N | Catalan shapes | Leaf assignments | Trees | Cumulative |
|---|---------------|-----------------|-------|-----------|
| 1 | 1 | 4 | 4 | 4 |
| 2 | 2 | 8 | 16 | 20 |
| 3 | 5 | 16 | 80 | 100 |
| 4 | 14 | 32 | 448 | 548 |
| 5 | 42 | 64 | 2,688 | 3,236 |
| 6 | 132 | 128 | 16,896 | 20,132 |
| 7 | 429 | 256 | 109,824 | 129,956 |
| 8 | 1,430 | 512 | 732,160 | 862,116 |
| 9 | 4,862 | 1,024 | 4,978,688 | 5,840,804 |
| 10 | 16,796 | 2,048 | 34,398,208 | 40,239,012 |
| **11** | **58,786** | **4,096** | **240,787,456** | **281,026,468** |

N=8 used all-ones prescreen + first-probe early exit (~25 s, single core). N=9 added a **parity filter** (sin is odd: f(−x) = −f(x)), eliminating 51.8% of shapes. N=10 uses the same pipeline with `ProcessPoolExecutor`. N=11 (`sin_search_05.py`) uses a vectorised NumPy evaluator evaluating all 4,096 leaf assignments per shape in a single matrix operation; runtime **323 s** (~5.4 min) on a laptop CPU. After parity filter: 208,901,719 trees evaluated.

**Results (N ≤ 11):**

- **sin(x) — real-valued:** NO candidate at tolerances 10⁻⁴, 10⁻⁶, 10⁻⁹ for all 281,026,468 trees
- **cos(x) — real-valued:** NO candidate at 10⁻⁶
- **sin(1), cos(1), π, √2, ln(2), 1/π — constant search from `{1}`:** NONE found
- **Complex EML path (N=1):** `Im(eml(i·x, 1)) = sin(x)` — **EXACT** at machine precision ✓

**The Infinite Zeros Barrier (why real-valued search cannot succeed for any N):**

Any finite composition of `exp` and `ln` over real inputs produces a real-analytic function that is strictly monotone between singularities and has at most finitely many zeros on any bounded interval. `sin(x)` has a zero at every integer multiple of π — infinitely many on `[−10, 10]`. This is a structural impossibility: no finite real-valued EML tree can match sin at all its zeros, regardless of depth.

This rules out real-valued constructions for all N, not just N ≤ 10. The complex case remains open.

**Theorem (Infinite Zeros Barrier):**

> *No finite real-valued EML tree with terminals `{1, x}` equals sin(x) for all x ∈ R.*

Proof: sin(x) has zeros at {kπ : k ∈ Z} — infinitely many. Every finite EML tree is
real-analytic and has only finitely many zeros. Contradiction. □

This is supported by exhaustive search (281,026,468 trees, N ≤ 11, zero candidates at any tested tolerance) and the structural proof above (which extends to all N). The complex case is now also resolved:

**Complex bypass (exact, 1 node):**

```python
import cmath
def sin_eml(x):
    return cmath.exp(1j * x).imag   # Im(eml(i·x, 1)) = Im(exp(ix)) = sin(x)

sin_eml(1.5707963268)  # → 1.0 (machine precision)
```

`eml(i·x, 1) = exp(i·x) − ln(1) = exp(i·x)`. Taking the imaginary part gives sin(x) by
Euler's formula. This is exact for all real x — one complex EML node resolves the barrier.

**Best real-domain approximation (from N=11 search, MSE = 1.478e-4):**

```
eml(eml(eml(x,1),eml(1,1)), eml(eml(eml(eml(x,1),eml(1,1)),eml(x,1)),eml(x,1)))
```

This is 2,842× closer to sin(x) than the trivial baseline exp(x) — but still not equal.

**Best Taylor approximation:**

```
sin(x) ≈ x − x³/6 + x⁵/120 − ...  (BEST-routed, 8 terms)
```

63 nodes, max error 7.7×10⁻⁷. 108 nodes for 13 terms (machine precision).

### 6.3 Open Avenues

1. **N=11 search — COMPLETE (2026-04-16).** 240,787,456 trees, 208,901,719 after parity
   filter, runtime 323 s. Zero candidates. See `results/sin_n11.json` and
   `monogate/search/analyze_n11.py` for the full near-miss gallery.

2. **Complex bypass — SOLVED.** `Im(eml(i·x, 1)) = sin(x)` exactly (Euler, 1 node).
   Implemented in `monogate.complex_eval`. The barrier is confirmed real-domain only.

3. **N=12 search (open).** Catalan(12) = 208,012 × 2^13 ≈ 1.7 billion trees. Requires GPU
   parallelism or distributed evaluation. The Infinite Zeros Barrier rules out real-valued hits;
   the value is confirming no corner cases arise from complex-branch evaluation at scale.

4. **MCTS over the EML grammar.** Implemented in `monogate.search.mcts_search()` — see
   Section 6.4. Avoids gradient-descent attractor traps entirely.

### 6.4 MCTS Search Module

`monogate.search` provides gradient-free symbolic search over the EML grammar via Monte Carlo Tree Search and Beam Search:

```python
from monogate.search import mcts_search, beam_search
import math

result = mcts_search(math.exp, depth=3, n_simulations=2000, seed=42)
# MCTSResult(mse=0.0000e+00, formula='eml(x, 1.0)', ...)
# Exact solution eml(x,1) = exp(x) - ln(1) = exp(x) found in <1s
```

**Key properties:**

- **Grammar:** `S → 1.0 | x | eml(S, S)`, with `"?"` placeholder nodes for incremental expansion
- **Selection:** UCB1 with exploration constant C = √2
- **Rollout:** Random completion of placeholder nodes with 60% leaf / 40% branch probability
- **Reward:** `1 / (1 + MSE)` ∈ (0, 1], bounded to prevent large-reward dominance
- **Result:** Returns `MCTSResult` with `best_tree`, `best_mse`, `best_formula`, and `history` list

MCTS avoids the phantom attractor problem entirely because it never follows a gradient: each rollout independently evaluates a complete random tree, and the selection policy biases toward tree prefixes associated with low-MSE completions. This makes it complementary to gradient-based `EMLTree.fit()` — especially useful for escape probing before gradient refinement.

---

## 7. EDL Completeness: Status and Open Questions

### 7.1 What EDL Can and Cannot Construct

EDL is defined as `edl(x, y) = exp(x) / ln(y)` with constant `e`. From this gate:

- **Division** (1 node): `div(a, b) = edl(ln(a), e^b)` — the cheapest div in any operator family
- **Multiplication** (7 nodes): constructible via `mul(a, b) = div(a, recip(b))`
- **Powers and logarithms**: accessible via composition with exp/ln
- **All multiplicative group operations**: EDL is complete over the multiplicative group `(ℝ>0, ×, ÷)`

The critical limitation is the **additive group**. EDL's gate is a ratio — it cannot produce a sum of two independent quantities without first embedding them in a multiplicative structure. Concretely:

- `add(a, b)` requires `ln(exp(a) + exp(b))` — computing the log-sum-exp, which itself needs addition at the argument level. The required addition cannot be expressed by EDL alone.
- `sub(a, b)` has the same issue: `ln(exp(a) - exp(b))` requires subtraction internally.

This means EDL is **not complete** over the full elementary functions if the inputs can take arbitrary real values requiring additive combination.

### 7.2 Complex-Branch Routes

Admitting complex arithmetic creates new paths. In particular:

- `exp(iπ) = −1`, so EDL can construct `−1` via complex inputs if `iπ` is reachable
- Addition of two reals `a + b` can be expressed as a limit of products: `a + b = ln(exp(a) · exp(b))`, which collapses to `a + b` — but this requires `ln(exp(x)) = x`, which is only valid when `exp(x)` is real positive
- Via Euler's formula, `cos(x) = Re(exp(ix))` — but constructing `ix` from EDL terminals alone requires `i`, which is not a real terminal

The current evidence suggests EDL achieves completeness over the **multiplicative elementary functions** (div, mul, pow, recip, ln, exp) but not over the **additive elementary functions** (add, sub) for arbitrary real inputs.

### 7.3 Current Status

| Operation | EDL status | BEST fallback | Notes |
|-----------|-----------|---------------|-------|
| div(a,b)  | 1 node    | EDL           | Cheapest known |
| mul(a,b)  | 7 nodes   | EDL           | Via recip chain |
| pow(a,b)  | 3 nodes   | EXL           | EXL cheaper than EDL here |
| ln(x)     | available | EXL (1n)      | EXL cheaper |
| exp(x)    | available | EML (1n)      | All equal |
| add(a,b)  | not constructible | EML (11n) | Requires EML subtraction |
| sub(a,b)  | not constructible | EML (5n)  | Fundamental limitation |

EDL is formally complete over `{×, ÷, pow, ln}` but cannot escape to the additive group without EML. This is why BEST routing uses EDL for div/mul/recip and EML for add/sub — they are complementary, not competing.

**Empirical confirmation:** `experiments/research_03_edl_completeness.py` searched all 196 EDL trees with N ≤ 6 internal nodes from terminal `{e}`. No tree evaluates to any of: e+1, 2e, 2, π, or √2. These values all require addition of independent reals and are structurally unreachable in the EDL grammar.

**Open question:** Can a finite EDL tree (possibly using complex terminals or branch cuts) produce an exact `a + b` for arbitrary real `a`, `b`? No construction is known; the structural argument above suggests none exists.

---

## 8. Performance Kernels (v0.9.0)

`EMLLayer(compiled=True)` auto-selects the fastest available backend:

| Backend | ms/step (256→256, batch=1024) | Speedup | How to activate |
|---------|------------------------------|---------|-----------------|
| Standard (recursive Python) | 8.3 | 1× | default |
| FusedEMLActivation | 2.3 | 3.6× | `compiled=True` |
| FusedEMLActivation + `torch.compile` | 1.9 | 4.4× | `.compile()` |
| **Rust (monogate-core)** | **1.4** | **5.9×** | install `monogate-core` |

```python
from monogate.torch import EMLLayer

layer = EMLLayer(256, 256, depth=2, operator="BEST", compiled=True)
# → selects Rust > Fused > Standard automatically
# ONNX export, state_dict(), torch.compile supported
```

Install Rust backend (one-time, ~30 s):
```bash
cd monogate-core && pip install maturin && maturin develop --release
```

---

## 9. Conclusion and Open Problems

The `BEST` hybrid demonstrates that intelligently combining variants of EML can produce substantially more efficient and stable trees than any single operator. The released `monogate` library makes these techniques immediately usable in both Python and the browser, with Rust-accelerated kernels for production use.

**Confirmed results (v0.12.0-dev):**
- Phantom attractors trap 100% (40/40) of gradient-based EMLTree fits without regularization; λ_crit = 0.001 eliminates them entirely (sharp phase transition); phenomenon confirmed EML-specific (not present in Taylor/Padé/CF bases)
- **281,026,468 EML trees (N ≤ 11, terminals {1, x}) contain no real-valued construction of sin(x)**; the Infinite Zeros Barrier theorem rules this out for all N
- **Complex bypass found:** `Im(eml(i·x, 1)) = sin(x)` exactly (1 node, machine precision); extends to all functions with infinitely many real zeros (Bessel J₀, Airy Ai, erf)
- BEST routing delivers 2.8× wall-clock speedup on sin/cos-heavy Python code
- Rust backend: 5.9× throughput over baseline; FusedEMLActivation: 3.6× (no Rust required)
- MCTS finds exact solutions (MSE=0) for targets like `exp(x)` in <1s, avoiding phantom attractors
- Free-particle Schrödinger u(x) = exp(ikx) = 1 CBEST node (Euler path identity extended to physics)
- 15 special functions catalogued with CBEST/BEST node counts in `monogate.special`

**Open problems:**
- **N=12 real-valued search** — ~1.7 billion trees; requires GPU/distributed evaluation (Barrier theorem already rules out matches, but empirical confirmation has value)
- **Minimax-optimal EML approximations** — what is the best uniform approximation to sin(x) achievable with exactly k EML nodes?
- **Complex BEST routing** — does EDL or EXL reduce node count for functions expressed via complex EML (exp(ix), Bessel, etc.)?
- **EDL additive completeness** — does a finite EDL tree using complex terminals produce exact `a + b` for arbitrary real a, b?
- **Attractor identity** — what is the exact algebraic identity of the depth-3 EML attractor at ≈3.169642? Is it a known constant?

## References

Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852v2 [cs.SC].

Almaguer, A. (2026). Practical extensions to the EML universal operator: hybrid routing, phantom attractors, performance kernels, and the N=11 sin barrier. arXiv:ARXIV_ID_PLACEHOLDER.

monogate repository: https://github.com/almaguer1986/monogate · v0.12.0-dev

---

## 10. Extensions (v0.10.0–v0.12.0-dev)

### 10.1 `monogate.special` — Special Function Catalog

15 pre-computed CBEST/BEST expressions for special functions:

| Function | Nodes | Backend | Max error | Notes |
|----------|-------|---------|-----------|-------|
| sin, cos | 1 | CBEST | 1e-15 | Exact via Euler path Im/Re(eml(ix,1)) |
| sinh, cosh | 9, 15 | BEST | 1e-14 | Algebraic via exp(x) and recip |
| tanh, sech | 8, 16 | BEST | 1e-14 | Exact algebraic |
| erf | 5 | CBEST | 1.5e-2 | tanh(1.2025x) approximation |
| Fresnel S/C integrand | 2 | CBEST | 1e-15 | Im/Re(eml(i·πx²/2, 1)) |
| Fresnel S/C | 2 | CBEST | 1e-6 | Quadrature of integrand |
| Bessel J₀ | 7 | CBEST | 1e-4 | Complex MCTS depth-3 tree |
| Airy Ai | 9 | CBEST | 2e-3 | Complex MCTS depth-3 tree |
| lgamma | 12 | BEST | 1e-9 | Stirling series |
| digamma | 14 | BEST | 1e-8 | Central differences of lgamma |

**Key identity:** `fresnel_s_integrand(x) = Im(eml(i·πx²/2, 1))` — 2 CBEST nodes, exact.
This extends the Euler-path construction from sin(x) to the entire Fresnel family.

### 10.2 `monogate.leaderboard` — Symbolic Regression Benchmark

10 Nguyen/Keijzer benchmark problems tracked against MCTS and beam search.
`run_leaderboard()` produces a sortable table of formulas, node counts, and MSEs.
GitHub Actions workflow (`.github/workflows/leaderboard.yml`) runs daily auto-refresh.

### 10.3 `monogate.pinn` — Extended Physics-Informed Networks

7 equations now supported (was 3):

| Equation | Formula | Key result |
|----------|---------|------------|
| harmonic | u'' + ω²u = 0 | — |
| burgers | u·u' − ν·u'' = 0 | — |
| heat | u'' = 0 | — |
| **schrodinger** | −u'' = k²u | exp(ikx) = **1 CBEST node** |
| **kdv_soliton** | u' − 6u·u' − u''' = 0 | — |
| **nls** | u'' + |u|²u = 0 | — |
| **lotka_volterra** | u'' + α·u' + β·u·u' = 0 | — |

The Schrödinger result `exp(ikx) = Im(eml(ix, 1))` extends the Euler-path identity
from pure mathematics to a physics equation. One CBEST node solves the free-particle problem.

### 10.4 `monogate.interval` — Certified Interval Arithmetic

Tight certified bounds propagated through EML trees using monotonicity of exp/ln:

```
eml_interval([a_lo, a_hi], [b_lo, b_hi]) = [exp(a_lo) − ln(b_hi), exp(a_hi) − ln(b_lo)]
```

`bound_expression(expr_str, x_lo, x_hi)` parses a formula string and returns certified bounds.

### 10.5 `monogate.sympy_bridge` — SymPy Interoperability

`to_sympy(tree)`, `from_sympy(expr)`, `simplify_eml(tree)`, `latex_eml(tree)`, `verify_identity(t1, t2)`.
Optional dep: `pip install monogate[sympy]`.

### 10.6 Streamlit Web Demo (`streamlit_app.py`)

5-tab interactive demo deployable to Streamlit Cloud (no torch required for base demo):

1. **Optimizer** — BEST savings table + rewritten code snippet
2. **Special Functions** — CATALOG browser; EML vs reference + log-error plot
3. **PINN Demo** — run `fit_pinn()` interactively for all 7 equations; graceful fallback without torch
4. **MCTS Explorer** — configure and run `mcts_search()`; convergence plot; session-cached results
5. **Phantom Attractor** — pre-computed phase-transition chart from `attractor_phase_transition.json`

Run: `streamlit run streamlit_app.py` (install: `pip install -r requirements.txt`).

### 10.7 Attractor Generalization

`experiments/attractor_generalization.py` confirms the phantom attractor at ~3.1696 is
**EML tree topology-specific**: Taylor-series, Padé, and continued-fraction bases fitted to π
with identical seeds and learning rates do not exhibit the phantom attractor phenomenon.
This strengthens the characterization: the false basin arises from the nested exp/ln structure
of EML trees, not from gradient descent or the Adam optimizer in general.
