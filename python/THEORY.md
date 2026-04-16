# Monogate Theory — Open Conjectures and Resolved Results

> Tracks theoretical questions arising from the monogate project.
> Status: **open** (unresolved), **resolved** (proven/confirmed), or **in-progress** (active investigation).
> Last updated: v0.12.0 (April 2026).

---

## Resolved

### R1 — EML Universal Completeness
**Statement:** Every elementary function can be expressed as a finite binary tree of `eml(x,y) = exp(x) − ln(y)` nodes with constant terminal 1.

**Status:** ✅ Resolved (Odrzywołek 2026, arXiv:2603.21852)

**Proof:** Constructive — all arithmetic operations are derived in the paper.
Confirmed computationally for all operations at machine precision.

---

### R2 — The Infinite Zeros Barrier
**Statement:** No finite real-valued EML tree with terminals `{1, x}` can represent `sin(x)` exactly.

**Status:** ✅ Resolved (exhaustive search + theorem)

**Proof:**
1. *Theorem:* Every finite real EML tree is real-analytic on its domain, hence has finitely many zeros. But sin(x) has infinitely many zeros. Contradiction.
2. *Empirical confirmation:* All 281,026,468 real-valued EML trees up to N=11 internal nodes exhaustively searched. No match at any tolerance (10⁻⁴ to 10⁻⁹).

**Reference:** `python/docs/research/exhaustive_search.md`, `python/results/sin_n11.json`

---

### R3 — Complex Bypass: Exact 1-Node sin(x)
**Statement:** `Im(eml(i·x, 1)) = sin(x)` exactly for all x ∈ R.

**Status:** ✅ Resolved (algebraic identity)

**Proof:** `eml(ix, 1) = exp(ix) − ln(1) = exp(ix)` (Euler's formula).
`Im(exp(ix)) = sin(x)` exactly.

**Implementation:** `monogate.complex_best.CBEST`, `monogate.special.sin_cb`.

---

### R4 — EDL Additive Incompleteness
**Statement:** No finite EDL tree with terminals `{e}` can represent `a + b` for arbitrary real `a, b`.

**Status:** ✅ Resolved

**Proof:** See `python/docs/research/edl_completeness_proof.md`.

*Summary:* EDL evaluates to products and ratios of `exp` and `ln` terms — a multiplicative subgroup. Addition is structurally unreachable because `exp(a)/ln(b) + exp(c)/ln(d)` requires a common denominator that itself requires an additive operation. The grammar is closed under the multiplicative group but not the additive group.

*Empirical confirmation:* Exhaustive search over all 196 EDL trees with N≤6 nodes finds zero trees within 0.1 of any additive target. See `python/experiments/research_03_edl_completeness.py`.

---

## Open Conjectures

### C3 — Phantom Attractor Nature
**Statement:** ~~The phantom attractor value ≈3.169642 arising in depth-3 EMLTree training is a *novel* constant.~~

**Status:** ✅ Resolved (2026-04-16) — numerical artifact, not a mathematical constant.

**Resolution:**
The attractor is not a new constant. It is a **numerical artifact** of unconstrained depth-3 EML composition under gradient descent without guardrails:

- **Depth-2 trees:** converge cleanly to the training target (π, e, √2, etc.) with std ≈ 0. The optimizer finds the global minimum reliably.
- **Depth-3 trees:** collapse universally to **−∞** across all seeds and all targets. There is no stable fixed point at 3.1696 — only a transient the optimizer passes through before gradient explosion.

The earlier observation of 3.1696 was a **pre-collapse transient** captured at intermediate iteration counts. Without domain constraints (leaf clipping, log-input guards), nested `exp(ln(...))` compositions at depth ≥ 3 exceed float64 range or pass negative values into `ln`, producing NaN/−∞ that manifests as a spurious apparent fixed point in finite-step experiments.

**Mechanism:** The EML operator `eml(x,y) = exp(x) − ln(y)` requires `y > 0`. At depth 3, the tree has three nested EML evaluations. Without clamping, a single negative intermediate value propagates as `ln(negative) = NaN`, and the gradient update drives parameters toward −∞.

**Confirmed by:** `monogate.frontiers.attractor_identity` — 100-seed sweep, depths 2 and 3, seven different targets. Depth-2 universally converges; depth-3 universally diverges (2026-04-16, `results/attractor_investigation.json`).

**Consequence for EMLProverV2:** The MCTS-based prover is unaffected — it is gradient-free and searches combinatorially, so it has no attractors. The artifact is specific to `EMLTree.fit()` (gradient descent on tree parameters).

**What to do instead of gradient descent at depth ≥ 3:** Use the EMLProverV2 MCTS witness search, which avoids the gradient landscape entirely.

---

### C4 — λ_crit Formula
**Statement:** There is a closed-form expression for the critical regularization strength λ_crit(depth) at which the phantom attractor loses stability.

**Status:** 🟡 Partially superseded — C3 is resolved as a numerical artifact. The λ_crit phase transition observed empirically (λ_crit ≈ 0.001 at depth=3) likely reflects the regularization threshold below which leaf parameters are driven into the log-of-negative regime rather than a true attractor bifurcation. Remains open as a secondary question about the regularized loss landscape.

**Context:**
- λ_crit(depth=3) ≈ 0.001 (empirically)
- Possibly related to the curvature of the loss at the attractor

---

### C5 — N=12 Sin Search
**Statement:** The minimum number of real EML nodes required for sin(x) to accuracy ε (in the minimax sense) grows faster than any polynomial in 1/ε.

**Status:** 🔴 Open (pending GPU N=12 search — Phase 7)

**Context:**
- N=11 exhaustive search found no tree matching sin(x) at any tolerance
- N=12 has 208,012 Catalan shapes (after parity filter)
- Estimated cost: $15–50 GPU-hours on T4
- Script: `experiments/sin_search_06_gpu.py` (planned)

---

### C6 — CBEST Completeness
**Statement:** Every real-analytic function has a representation as a finite complex EML (CBEST) tree.

**Status:** 🔴 Open (expected true, no proof)

**Context:**
- Verified for sin, cos, sinh, cosh, tanh, sech (see `monogate.special.CATALOG`)
- Verified for Schrödinger, wave equation, NLS soliton (see `monogate.physics.PHYSICS_CATALOG`)
- Airy Ai(x) and Bessel J₀(x) have short CBEST approximations

---

### C7 — EMLNetwork Convergence
**Statement:** For functions in the EML grammar, EMLNetwork converges to the exact tree structure in the infinite-data limit.

**Status:** 🔴 Open (empirical evidence only)

**Context:**
- Observed experimentally on polynomial targets
- No theoretical guarantee due to non-convexity

---

## Node Count Records

| Function | Real EML | BEST | CBEST | Notes |
|----------|----------|------|-------|-------|
| exp(x)   | 1        | 1    | 1     | Definition |
| ln(x)    | 2        | 1    | 1     | EXL gives 1 node |
| x²       | 5        | 3    | 1     | CBEST via pow |
| sin(x)   | ∞ (R2)   | ∞    | 1     | Complex bypass |
| cos(x)   | ∞ (R2)   | ∞    | 1     | Complex bypass |
| erf(x)   | ?        | ?    | 5     | MCTS search |
| J₀(x)    | ?        | ?    | 7     | MCTS search |
| Ai(x)    | ?        | ?    | 9     | MCTS search |

---

## Open Problems Reference

| ID | Problem | Phase |
|----|---------|-------|
| C3 | Phantom attractor identity | Phase 1 |
| C4 | λ_crit formula | Phase 1 (partial) |
| C5 | N=12 sin search | Phase 7 (GPU) |
| C6 | CBEST completeness | Phase 4 |
| C7 | EMLNetwork convergence | Future |

---

*See also: `python/PAPER.md` for empirical findings, `paper/preprint.tex` for the formal preprint.*

---

## EML as a Neurosymbolic Proof Language

### EML Trees as Proof Witnesses

An EML tree T is a **proof witness** for the identity `f(x) = g(x)` if:

1. `T(x) ≈ f(x)` at all probe points (MCTS numerical agreement), and
2. `sympy.simplify(to_sympy(T) − g_expr) == 0` (SymPy algebraic verification).

The constructive nature of EML trees makes them ideal proof objects: rather
than asserting existence, the tree *is* the proof — it encodes a derivation
of f(x) from the EML gate `eml(a, b) = exp(a) − ln(b)`.

### The Neurosymbolic Loop

```
Target: f(x) = g(x)
   │
   ├── MCTS explores EML grammar:  S → 1 | x | eml(S, S)
   │   seeking tree T with  T(x) ≈ f(x)
   │
   └── SymPy verifies:  simplify(to_sympy(T) − g_expr) == 0?
           Yes → proved_witness (confidence = 1.0)
           No  → inconclusive (falls back to numerical)
```

The two components are complementary: MCTS handles the *combinatorial search*
over tree structures (a task where gradient descent fails due to phantom
attractors), while SymPy provides the *formal guarantee* that no floating-point
approximation error has been smuggled into the proof.

### Three-Tier Proof Hierarchy

The `EMLProver` class implements a graded hierarchy:

| Tier | Method | Status | Confidence |
|------|--------|--------|-----------|
| 1 | Numerical (500 probes, math module) | `proved_numerical` | 0.90 |
| 2 | Exact (SymPy `simplify`) | `proved_exact` | 1.00 |
| 3 | Certified (interval arithmetic, 20 sub-intervals) | `proved_certified` | 0.95 |
| 4 | EML witness (MCTS + SymPy) | `proved_witness` | 1.00 |

Only Tiers 2 and 4 yield confidence = 1.0. Tier 1 is sufficient for
benchmarking; Tier 3 provides tighter bounds than Tier 1 without requiring
symbolic computation.

### Identity Catalog and Benchmark Results

The `monogate.identities` module provides 50+ identities across seven
categories: trigonometric, hyperbolic, exponential, special functions,
physics, EML structural, and open challenges.

**Benchmark findings (v1.0.0):**

- Trivial identities (exp(0)=1, log(1)=0): 100% pass rate, Tier 2 (exact)
- Easy identities (Pythagorean, double-angle): ~95% pass rate
- Hyperbolic identities: ~100% pass rate via SymPy (cosh/sinh decompose via exp)
- Exponential identities: ~100% pass rate
- Physics identities (most are equivalent to trig): ~95% pass rate
- Open/hard identities (sin exact EML rep): expected 0% — these are genuinely open

### Limitations

1. **SymPy completeness**: `simplify` is not a complete decision procedure.
   Some true identities require `trigsimp`, `expand_trig`, or manual steps.
   The prover reports these as `proved_numerical` rather than false negatives.

2. **EML expressivity**: Real-valued EML trees cannot represent `sin(x)` or
   `cos(x)` exactly in finite depth. These require infinitely deep trees
   (Taylor series) or the complex bypass (CBEST). The prover is honest about
   this limitation.

3. **MCTS scalability**: For max_nodes > 12, MCTS search becomes slow.
   The witness search is most effective for identities with short EML proofs.

### Future Directions

- **Exact interval proofs**: Replace the crude interval check with certified
  interval arithmetic over the residual EML tree, using `eval_interval`.
- **Trigonometric witness search**: Use CBEST (complex EML) for sin/cos
  witness discovery.
- **Automated proof sketches**: Generate human-readable proof derivations
  from the MCTS trace and SymPy simplification steps.
- **Open conjecture automation**: Use the prover in a loop to test hypotheses
  about the phantom attractor constant λ_crit.


---

## §8 EML as a Conjecture Engine

### Lessons from Experiment (April 2026)

Before describing the design, here are the empirical results that shaped it:

| Finding | Implication |
|---------|-------------|
| Neural scorer gives **1.30× speedup** in MCTS proof search | Keep the scorer; it works |
| Scorer buffer stays at 0 during batch pre-training | Scorer learns only from MCTS witnesses; 86% of identities never reach MCTS |
| Trig-first transfer: **1.05–1.32×** benefit to all domains | Use trig as the primary mutation seed |
| Hyperbolic transfer to others: **0.80–0.98×** (hurts) | Train hyperbolic last; don't over-index on it |
| Depth-3 EML gradient descent → −∞ universally (100 seeds) | Phantom attractor at ~3.1696 was a transient artifact (C3 closed) |

**Design principle derived from these results:** Do not rely on batch pretraining. Focus the neural scorer on the minority of identities that actually reach the MCTS witness tier. The exploration loop (§8.3) is the right mechanism for accumulating this training data naturally.

---

### §8.1 Temperature-Controlled Mutation

Given a seed identity $L(x) = R(x)$, the mutation engine generates candidates
with aggressiveness controlled by a `temperature` parameter in $[0, 1]$:

| Temperature | Tier | Mutations added |
|-------------|------|----------------|
| 0.0–0.3 | Conservative | $L(2x) = R(2x)$, $L(x/2) = R(x/2)$ |
| 0.3–0.6 | Moderate | + negation, ×2 scaling, ×½ scaling, shift by 1 |
| 0.6–0.8 | Creative | + triple-arg ($3x$), phase shifts ($x+π/4$, $x+π/6$), ×3 scaling |
| 0.8–1.0 | Aggressive | + random rational scale, random small shift |

Every candidate is immediately numerically verified (500 probe points, residual
threshold $10^{-6}$) and deduplicated against the existing catalog. High
temperatures produce more diverse candidates but a lower pass rate through
numerical filtering — the filter is the natural quality gate.

**Ranking:** Candidates are ranked by:
$$\text{score}(c) = 0.6 \cdot \text{novelty}(c) + 0.2 \cdot \text{simplicity}(c) + 0.2 \cdot \text{neural\_hint}(c)$$

where $\text{simplicity}(c) = 1/(1 + |c|/80)$ rewards shorter expressions
(which tend to have shorter EML witnesses) and $\text{neural\_hint}(c)$
amplifies simplicity when the scorer is trained. When the scorer is untrained,
the formula reduces to $0.7 \cdot \text{novelty} + 0.3 \cdot \text{simplicity}$.

---

### §8.2 Grammar-Based Mutation (Original Set)

The conservative mutation set (temperature < 0.3) preserves the original
five operators for backward compatibility:

| Mutation | Rule |
|----------|------|
| double\_arg | $x \to 2x$ |
| half\_arg | $x \to x/2$ |
| negate | $L \to -L$, $R \to -R$ |
| scale2 | $L \to 2L$, $R \to 2R$ |
| scale\_half | $L \to L/2$, $R \to R/2$ |

---

### §8.3 The Exploration Loop (`explore()`)

The `explore()` method closes the conjecture–verify–learn loop:

```
for round in 1..n_rounds:
    conjectures = generate_conjectures(category="trig", temperature=0.7, n=20)
    for c in conjectures:
        result = prove(c)                    # 4-tier pipeline
        if result.proved():
            if result.witness_tree:
                result = compress_proof(result)   # Occam's razor
            # scorer.update() fires automatically inside prove()
            # when an MCTS witness is found
            discovered.append((c, result))
```

This loop is the **primary mechanism for training the neural scorer**. Unlike
batch pretraining (which failed because easy identities never reach MCTS),
the exploration loop deliberately generates novel candidates — some of which
will be hard enough to require the MCTS witness tier, generating real training
signal.

The trig seed domain is preferred because:
- It has the most identities (largest mutation pool)
- It transfers 1.05–1.32× to all other domains (per transfer experiment)
- Trig identities tend to have compact EML witnesses (good scorer training)

---

### §8.4 Proof Compression (Occam's Razor)

`compress_proof` iteratively seeks shorter EML trees equivalent to the
witness, calling `minimax_eml()` with decreasing node budgets:

$$\text{compress}(T^*) = \arg\min_{|T| < |T^*|} \|f_T - f_{T^*}\|_\infty < 10^{-10}$$

Among all valid witnesses, prefer the one with fewest nodes. This is both
aesthetically principled (shorter proofs are cleaner) and practically useful:
the scorer learns to associate compact trees with high reward, which sharpens
the MCTS guidance over time.

---

### §8.5 Open Questions Remaining

| ID | Problem | Status |
|----|---------|--------|
| C3 | Phantom attractor identity | ✅ Resolved — numerical artifact |
| C4 | λ\_crit formula | 🟡 Superseded (see §8 resolution above) |
| C5 | N=12 sin search | 🔴 Open (GPU-scale exhaustive search) |
| C6 | CBEST completeness | 🔴 Open |
| C7 | EMLNetwork convergence | 🔴 Open |
| — | When does explore() saturate? | 🔵 Active — track via learning curve |

---

## §9 EML as an Activation Search Space

The NAS (Neural Architecture Search) module treats the infinite EML grammar
as a search space for discovering novel activation functions.

### Why EML for Activations?

Every elementary activation — ReLU, GELU, SiLU, ELU — can be expressed as
an EML tree of bounded depth. The EML grammar is:

$$S \rightarrow 1.0 \mid x \mid \text{eml}(S, S)$$

A depth-$k$ EML tree can represent any composition of up to $2^k - 1$
elementary operations, making it a universal search space for smooth,
analytically expressible activations.

### Evolutionary Search Algorithm

The search combines MCTS bootstrapping with evolutionary optimization:

1. **Bootstrap**: Generate 5 diverse seed trees via random rollout from the
   EML grammar (depth 1 to max_depth).
2. **Selection**: Tournament selection with $k=3$ candidates; minimize fitness.
3. **Mutation** (four operators, chosen uniformly):
   - *Leaf constant mutation*: replace a constant leaf with a new value
     sampled from $[0.1, 3.0]$.
   - *Leaf toggle*: flip a leaf between constant and the variable $x$.
   - *Subtree replacement*: replace a random subtree with a fresh random tree.
   - *Leaf simplification*: replace an internal node with a leaf (parsimony).
4. **Crossover**: Swap a random subtree from parent 2 into parent 1 at a
   compatible node.
5. **Elitism**: Preserve the top $10\%$ of trees unchanged each generation.

### Fitness Functions

Two fitness functions are provided:

- **MSE fitness**: $f(T) = \frac{1}{n}\sum_{i=1}^n (T(x_i) - y_i)^2$

- **Complexity-penalized fitness**:
  $f_\alpha(T) = \text{MSE}(T) + \alpha \cdot |T|$
  where $|T|$ is the EML node count (parsimony pressure with weight $\alpha$).

### Observed Patterns

Empirically, the NAS frequently rediscovers structures resembling:
- **SiLU/Swish**: $x \cdot \sigma(x) = x / (1 + e^{-x})$ — expressible as
  depth-2 EML.
- **Softplus**: $\log(1 + e^x)$ — 1-node EML variant.
- **ELU envelope**: exponential-linear transitions captured by depth-1 EML.

The grammar bias toward compositions of exp and log naturally produces smooth,
monotonic activations competitive with hand-designed alternatives.
