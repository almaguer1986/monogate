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
