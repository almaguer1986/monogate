# Monogate Research — Context and Policy Record

## Machine Verification Status (Lean 4, updated 2026-04-21)

**Build status**: `lake build → Build completed successfully` (all files, 0 errors).

### Fully Lean-verified (0 sorries)
| Theorem | Lean file | Lean theorem |
|---------|-----------|--------------|
| SB(neg) ≥ 2 | NegLowerBound.lean | SB_neg_ge_two |
| SB(add) ≥ 2 | AddLowerBound.lean | SB_add_ge_two |
| SB(sub) ≥ 2 | SubLowerBound.lean | SB_sub_ge_two |
| SB(mul, general) ≥ 2 | MulLowerBound.lean | SB_mul_ge_two |
| SB(div, general) ≥ 2 | DivLowerBound.lean | SB_div_ge_two |
| exp = 1n (all x) | UpperBounds.lean | exp_one_node |
| mul = 1n (x,y > 0) | UpperBounds.lean | mul_one_node_positive |
| pow = 1n (x > 0) | UpperBounds.lean | rpow_one_node_positive |
| recip = 1n (x > 0) | UpperBounds.lean | recip_one_node_positive |
| sqrt = 1n (x > 0) | UpperBounds.lean | sqrt_one_node_positive' |
| v5.1 overcounting: 16n → 15n | ModelAudit.lean | superbest_v51_overcounted_by_one |
| Euler Gateway ceml(ix,1) = exp(ix) | EMLDepth.lean | euler_gateway |
| Euler Identity e^{iπ} + 1 = 0 | EMLDepth.lean | euler_identity |
| EML-0 ⊊ EML-1 (exp not constant) | EMLDepth.lean | exp_not_constant |
| sin has infinitely many zeros | InfiniteZerosBarrier.lean | sin_has_infinitely_many_zeros |
| analytic non-zero → finitely many zeros | InfiniteZerosBarrier.lean | analytic_finite_zeros_compact |
| Real.log analytic on (0, ∞) | InfiniteZerosBarrier.lean | real_log_analyticOnNhd_pos |
| Depth ≤ 1 EML trees analytic on (0, ∞) | InfiniteZerosBarrier.lean | eml_tree_analytic_depth_le_1 |
| Depth-1 zeros finite (CEML-T91) | InfiniteZerosBarrier.lean | depth1_finite_zeros_real |
| TheoremRegistry PROVED_COUNT = 24 | TheoremRegistry.lean | (rfl check) |

### Partial / sorry'd (3 genuine open steps)
| Item | Sorry'd step | File | Blocker |
|------|-------------|------|---------|
| sin ∉ EML_k (T01 Part C) | eml_tree_eval_analyticOnNhd ceml/ceml log case | InfiniteZerosBarrier.lean | slit-plane membership for deeply-nested trees |
| sin ∉ EML_k (T01 Part D) | sin_not_in_eml (quantitative zero bound) | InfiniteZerosBarrier.lean | O-minimal theory |
| ELC depth barrier (T48) | sin_not_in_real_EML_k | InfiniteZerosBarrier.lean | depends on T01 Part D |

**eml_tree_analytic obstruction confirmed**: The ceml/ceml slit-plane sorry is mathematically justified — `(ceml (const 0) (const (exp 1))).eval ↑x = 0 ∉ slitPlane` for all x. So `eml_tree_analytic` for ALL trees is false in general. The correct resolution is `eml_tree_analytic_depth_le_1` (proved, 0 sorry) which handles depth ≤ 1 by explicit case analysis where the ceml/ceml branch is unreachable.

**New this session (Session 6)**: 3 new sorry-free theorems + 1 sorry eliminated:
- `real_log_analyticOnNhd_pos`: Real.log analytic on (0,∞) via Complex.log composition
- `eml_tree_analytic_depth_le_1`: depth ≤ 1 trees analytic on (0,∞), sorry-free, 6-case analysis
- `depth1_finite_zeros_real` (CEML-T91): depth-1 finite zeros, now proved (was sorry'd in EMLDepth.lean)
- `sin_not_in_real_EML_k` moved from EMLDepth.lean → InfiniteZerosBarrier.lean (no circular import)
- Sorry count: 4 → 3

### Python-certified (not yet Lean)
| Result | Method | File |
|--------|--------|------|
| SB(mul, general) = 3 | Exhaustive 4112-circuit search | mul_gen_tight_2node_search.py |
| SB(div, general) = 3 | Exhaustive 4112-circuit search | div_gen_tight_2node_search.py |

### Not yet formalized
- T02 (Universality / Weierstrass) — pending
- T30 (Depth Spectrum) — pending
- Cost Theory theorems (T34–T40) — pending

**Source**: `lean/MonogateEML/MonogateEML/` · **TheoremRegistry**: `TheoremRegistry.lean`

---

## Project

EML operator: `eml(x,y) = exp(x) − ln(y)`. Single binary gate from which all arithmetic operations derive.

## Operator Sets

### F16 (16-element orbit)
The group orbit of EML under G₁₆ ≅ (ℤ/2)⁴ — sign changes and reciprocal on both arguments and result, across all four arithmetic operations. This is the canonical primitive set.

### 23-operator extended set
F16 (16) + EEM, EED, EES, EEA (4) + LLA, LLS, LLD (3) = 23 operators total. Proved closed by CONJ_NO_OP_24 (now Theorem). No 24th operator survives the PGC+AIT filter.

## SuperBEST Core Table — v5.2 (canonical, F16-ground-truth)

| Metric | Value |
|--------|-------|
| Operators | 10 arithmetic primitives |
| Total (positive domain) | **15n** |
| Savings vs naive | **79.5%** |
| Total (general domain) | 22n / 69.9% |

**sqrt = 1n** via EPL(0.5, x). This result is locked and correct.

Key entries: add=1n, sub=2n, mul=2n, div=2n, exp=1n, ln=1n, sqrt=1n, abs=2n, neg=2n, pow=3n.

## Two-Layer Accounting Policy

**Effective immediately for all Monogate research outputs.**

### Layer 1 — F16 ground-truth
- All formal theorems, SuperBEST core table (15n/79.5%), circuit-complexity lower bounds
- The 7 extended operators (EEM, EED, EES, LLA, LLS, LLD, EEA) are **not** counted as 1n
- Label: "F16 node count" or implied by context

### Layer 2 — 23-op extended
- Library design, implementation guides, ML/physics papers, efficiency comparisons
- Each of the 7 extended operators counts as 1n (true only if atomically implemented)
- Label: **always** include "23-op count" or "extended-primitive count"

**No mixing**: a single table never lists both F16 and 23-op counts without explicit labels.

## Operator Primitiveness Classification

| Op | F16 best (genuine) | 23-op | F16 saving | Category |
|----|-------------------|-------|------------|----------|
| EEM | 3n (add+exp) | 1n | 1n genuine | A: algebraic shortcut |
| EED | 3n (sub+exp) | 1n | 1n genuine | A: algebraic shortcut |
| EES | 1n for EES(x,0); 4n general | 1n | 3n genuine (special case) | B: F16 sign-variant (constant arg) |
| LLA | 3n (mul+ln) | 1n | 1n genuine | A: algebraic shortcut |
| LLS | 3n (div+ln) | 1n | 1n genuine | A: algebraic shortcut |
| LLD | 4n (no shortcut) | 1n | 0n | C: notation-only |
| EEA | 4n (no shortcut) | 1n | 0n | C: notation-only |

### EES exceptional case
EES(x,0) = eˣ−1 is achievable as **1 F16 node**: EML_neg(a,e) = exp(−a)−1.
For general EES(x,y): F16 cost is 4n; calling it 1n saves 3n notationally.

## Key F16 Sign-Variant Facts (Category B — genuine F16 savings)

- **EML_neg(a,e)** = exp(−a) − ln(e) = exp(−a) − 1: single F16 node. Used for Mayer f-function and eˣ−1.
- **EML(x, 1/e)** = exp(x) − ln(1/e) = exp(x) + 1: single F16 node. Used for softplus first stage.

## Corrected Node Counts — Selected High-Impact Expressions

All counts are **F16 ground-truth (Layer 1)**:

| Expression | Naive | F16 best | Category | Notes |
|-----------|-------|----------|----------|-------|
| Softplus ln(1+eˣ) | 4n | **2n** | B genuine | EML(x,1/e)[1n] + ln[1n] |
| Mayer f: e^{−βu}−1 | 6n | **3n** | B genuine | mul[2n] + EML_neg(·,e)[1n] |
| Boltzmann ratio e^{−β(Ej−Ei)} | 10n | **6n** | A genuine | sub+mul+neg+exp; saves 4n |
| QRE term λ·ln(λ/μ) | 6n | **5n** | A genuine | div+ln+mul; saves 1n |
| Partition fn pair (EEA) | 10n | **10n** | C notation | EEA has no F16 shortcut |
| LSE (EEA) | 5n | **5n** | C notation | EEA has no F16 shortcut |
| Kraus √(1−e^{−γt}) | 6n | **4n** | B genuine | mul+EML-variant+EPL |
| Quantum rel. entropy (full) | 10n | **8n** | mixed | LLS route: 5n+mul; 2n saved |

## ELC Field ε(ℝ)

Smallest subfield of ℝ closed under exp and ln. Countable. Contains all algebraically computable exp-ln expressions over ℚ.

**tan(1) ∉ ε(ℝ)**: proved via Hermite–Lindemann–Weierstrass (algebraically isolated limit, AIL). SuperBEST(tan) = ∞.

**Three-tier ELC complement**:
- Tier 0: non-analytic functions (|x| = 2n in F16 on ℝ*, excluded at x=0)
- Tier 1: analytic but ∞-zero (sin, cos, tan — infinite ELC obstruction)
- Tier 2: AIL — algebraically isolated (functions whose ELC approximation requires unbounded depth)

## Resolved Conjectures

| ID | Statement | Resolution |
|----|-----------|------------|
| CONJ_NO_OP_24 | Taxonomy closed at exactly 23 operators | Theorem — proved |
| CONJ_MUL_GEN_TIGHT | SB(mul, general) = 3 | Python-certified (exhaustive 4112-circuit search) + 3-node witness; Lean target: MulLowerBound3.lean |
| CONJ_DIV_GEN_TIGHT | SB(div, general) = 3 | Python-certified (exhaustive 4112-circuit search) + 3-node witness; Lean target: DivLowerBound3.lean |

## Open Conjectures

| ID | Statement | Status |
|----|-----------|--------|
| EDB-ANALYTIC | eml_tree_analytic ceml/ceml log sorry | Partially proved — ceml/ceml slit-plane step remains |
| CONJ_BOUNDARY_DECIDABLE | SC + EDB ⟹ ELC-membership decidable | Conditional; EDB missing zero-count bound |
| CONJ_TRIG_DEPTH_TOWER | Tower s₀=1, s₁=sin(1), s₂=sin(sin(1)),… algebraically independent over ε(ℝ) | Open; L1 unconditional, L2 needs GAIL, L3/L4 needs SC |
| GAIL | If α ∉ ε(ℝ), then sin(α) ∉ ε(ℝ) | Open unconditionally; follows from Schanuel |

## File Index — Exploration Papers

All files in `python/paper/exploration/`:

| File | Content |
|------|---------|
| Operator_Primitiveness_Audit.tex | Definitive F16 decomposition of all 7 extended operators |
| 23op_Layer_Status_Decision.tex | Formal decision paper; five-criterion comparison; two-layer policy |
| F16_Only_High_Impact_Audit.tex | Corrected node counts using F16 only; three savings categories |
| SuperBEST_v7_Full_23_Audit.tex | Extended 23-op catalog (labeled as Layer 2) |
| SuperBEST_v8_Quantum_Physics_Integration.tex | Quantum/physics extended table (Layer 2, labeled) |
| Quantum_Costs_Final_23.tex | Quantum operator costs (23-op layer; F16 corrections in F16_Only audit) |
| SpecialFunctions_Physics_Final_Audit.tex | erf, Bessel, Airy, lgamma, Boltzmann, Mayer f |
| Trig_Depth_Tower_Investigation.tex | Four-level conjecture hierarchy for sin-tower |
| Boundary_Decidability_Schanuel_Link.tex | SC+EDB⟹CBD; converse partial SC |
| ELC_Boundary_Layer.tex | Three-tier theorem; shell functions; 18 classification examples |
| Tan1_Persistence_Final_Proof.tex | tan(1) ∉ ε(ℝ); AIL proof; 7 bypass attempts closed |
| Taxonomy_Closure_Conjecture.tex | 100-operator enumeration; CONJ_NO_OP_24 proved |
| CONJ_MUL_GEN_TIGHT_Resolution.tex | SB(mul,general)=3; exhaustive search + 3-node witness + Lean plan |
| EDB_Full_Construction.tex | EDB construction: B+(n)=n proved; general EDB partial; eml_tree_analytic sorry plan |
| Conjecture_Prioritization_Post_MUL.tex | Ranked open conjectures post-MUL; EDB-ANALYTIC is #1 |
| Conjecture_Prioritization_Post_23_Verified.tex | Post-sprint re-ranking (17 verified); eml_tree_analytic ceml/ceml sorry isolated |
| sin_not_in_eml_Initial_Mapping.tex | What is provable about sin∉EML without o-minimal theory; depth-0/1 proved, depth-2 conditional, depth≥3 open |
| Prioritization_Post_Verification_Sprint.tex | Re-ranked open items after 24 verified theorems; sin_not_in_eml_depth0 as new #1 |

All files in `python/paper/theorems/`:

| File | Content |
|------|---------|
| CONJ_MUL_GEN_TIGHT_Final.tex | SB(mul,general)=3 lock-in; lower bound cert + 3-node witness |
| CONJ_DIV_GEN_TIGHT_Final.tex | SB(div,general)=3 lock-in; lower bound cert + 3-node witness |
| InfiniteZerosBarrier_Status.tex | Verification status: 3 new theorems proved, sorry count 4→3, obstruction in eml_tree_analytic documented |

## Version History

- **v5.2**: sqrt=1n confirmed; 15n/79.5% locked (positive domain)
- **v6**: First 23-op catalog (LLS, EEA added)
- **v7**: Full 23-op audit (SuperBEST_v7_Full_23_Audit.tex)
- **v8**: Quantum/physics integration (SuperBEST_v8_Quantum_Physics_Integration.tex)
- **v8.1**: Primitiveness audit; two-layer policy; corrected F16 counts (this update)
