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
**Statement:** The phantom attractor value ≈3.169642 arising in depth-3 EMLTree training is a *novel* constant — not expressible as a simple rational combination of classical constants (π, e, sqrt(k), ln(k), etc.).

**Status:** 🔵 In progress (Phase 1 investigation)

**Context:**
- Attractor value: **3.169642** (from 40-seed sweep, `experiments/attractor_phase_transition.json`)
- Phase transition at λ_crit ≈ 0.001
- Depth dependence: depth=2 has attractor ≈2.43; depth=3 has attractor ≈3.1696
- The value is NOT π (|err| ≈ 0.028)

**Investigation:** `experiments/research_07_attractor_identity.py` — runs PSLQ and mpmath.identify() against the high-precision value. Basin geometry in `experiments/research_07b_basin_geometry.py`.

**Current evidence:** No known mathematical constant within 10⁻³ of 3.169642. mpmath.identify() does not return a short closed form. Tentative classification: *novel fixed-point constant of the depth-3 EML gradient flow.*

**What would resolve it:**
- An analytical expression for the fixed-point condition `∂L/∂θ = 0` at depth=3
- Or a PSLQ relation: `n₀·val + n₁·π + n₂·e + n₃ = 0` with small integers

---

### C4 — λ_crit Formula
**Statement:** There is a closed-form expression for the critical regularization strength λ_crit(depth) at which the phantom attractor loses stability.

**Status:** 🔴 Open

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

