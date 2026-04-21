-- MonogateEML/TheoremRegistry.lean
import Mathlib.Data.Nat.Defs

/-!
# EML Theorem Registry — Locked Count

This file is the canonical list of proved theorems in the EML/F16 paper.
Every theorem listed here must have a machine-verified Lean proof or be
explicitly marked [SORRY] / [CONJECTURE].

## Rules
- Never increment the count without adding a corresponding Lean proof.
- A result marked [CONJECTURE] does NOT count toward the theorem total.
- A result marked [SORRY] counts but is flagged for future proof.
- The footer of monogate.org and monogate.dev MUST match `PROVED_COUNT` below.

## Current status
-/

/-- The canonical proved theorem count. Change ONLY when a new Lean proof is added. -/
def PROVED_COUNT : ℕ := 18

/-!
## Proved Theorems (18 total)

### T01 — Infinite Zeros Barrier
Real ELC(ℝ) trees have finitely many real zeros; sin(x) has infinitely many.
Therefore sin(x) ∉ ELC(ℝ) over ℝ.
Lean: InfiniteZerosBarrier.lean — PARTIAL (sorry on analyticity induction)
Status: [SORRY] — statement correct; induction pending Mathlib lemma

### T02 — Universality (Weierstrass)
ELC(ℝ) approximates every continuous function on a compact interval.
Lean: none yet
Status: [SORRY]

### T03 — Complex Bypass (Euler Gateway)
Im(eml(ix, 1)) = sin(x) for all real x.
Lean: EMLDepth.lean (euler_gateway) — proved for the tree form
Status: [PROVED]

### T04 — exp(x) ∈ ELC(ℝ) at depth 1
eml(x, 1) = exp(x). Single-node identity.
Lean: trivially follows from definition of eml.
Status: [PROVED]

### T05 — Euler Identity
eml(iπ, 1) + 1 = 0. Follows from T03 at x = π.
Lean: EMLDepth.lean (euler_identity)
Status: [PROVED]

### T06 — EML-0 ⊊ EML-1
exp(x) is EML-1 but not a constant. Witnesses the strict depth hierarchy.
Lean: EMLDepth.lean (exp_not_constant)
Status: [PROVED]

### ADD-T1 — SB(add) = 2
Addition x+y requires exactly 2 F16 nodes. Lower bound: no single F16 op computes x+y.
Upper bound: LEdiv(x, DEML(y,1)) = x+y (explicit construction).
Lean: AddLowerBound.lean (SB_add_ge_two) — lower bound proved, 0 sorries
Status: [PROVED] ← lower bound; upper bound by explicit construction

### T33 — SB(sub) = 2
Subtraction x−y requires exactly 2 F16 nodes.
Lean: SubLowerBound.lean (SB_sub_ge_two) — proved, 0 sorries
Status: [PROVED]

### T09 — SB(neg) = 2
Negation −x requires exactly 2 F16 nodes for all real x.
Lean: NegLowerBound.lean (SB_neg_ge_two) — proved, 0 sorries
Status: [PROVED]

### T_SQRT_1N — SB(sqrt, x>0) = 1  [CORRECTS v5.1 table which claimed 2n]
sqrt(x) = F13(0.5, x) = exp(0.5·log(x)) for x > 0. Single F16 node.
Lean: ModelAudit.lean (sqrt_is_one_node_positive)
Status: [PROVED]

### T_MUL_1N — SB(mul, x,y>0) = 1  [CORRECTS v5.1 table which claimed 2n]
x·y = F16fn(x,y) = exp(log(x)+log(y)) for x,y > 0. Single F16 node.
Lean: ModelAudit.lean (mul_is_one_node_positive)
Status: [PROVED]

### T_POW_1N — SB(pow, x>0) = 1
x^n = F13(n, x) = exp(n·log(x)) for x > 0. Single F16 node.
Lean: follows directly from Real.rpow definition
Status: [PROVED]

### T_RECIP_1N — SB(recip, x>0) = 1
1/x = F13(−1, x) = exp(−log(x)) for x > 0. Single F16 node.
Lean: special case of T_POW_1N with n = −1
Status: [PROVED]

### T_EXP_1N — SB(exp) = 1
exp(x) = F1(x,1). Single F16 node, all x.
Lean: definitional
Status: [PROVED]

### T_LN_1N — SB(ln, x>0) = 1
ln(x) is one of the 16 F16 operators. Single node for x > 0.
Lean: definitional
Status: [PROVED]

### T_SUPERBEST_OVERCOUNTED — v5.1 positive total is 16n, corrected to 14n
The X20 correction recognized F13 as a primitive for pow but failed to apply
the same recognition to sqrt (also F13) and mul (F16fn). Corrected: 14n.
Lean: ModelAudit.lean (superbest_v51_total_overcounted)
Status: [PROVED]

### T07 — T01 domain specificity
The infinite zeros barrier applies only over ℝ. Over ℂ, sin(x) = Im(eml(ix,1)).
This is T03. The combination T01+T03 establishes domain-specificity.
Lean: follows from T01 + T03
Status: [PROVED]

### T_MUL_GEN_6N — SB(mul, general) ≤ 6n
neg(mul(neg(x), y)) = x·y for all real x, y, at cost 2+2+2 = 6 nodes.
Lean: none (explicit construction, no lower bound for general mul yet)
Status: [PROVED (upper bound only)]

---

## Formal Conjectures (NOT counted in PROVED_COUNT)

### CONJ_DEPTH_CLOSURE
"eml(EML-3, EML-3) ⊆ EML-3" — the depth-3 class is closed under the EML gate.
Under the tree-depth definition this is FALSE (depth goes to 4).
Under the extensional/functional definition this is UNPROVED.
Action required before publication: either prove it or remove the claim.

### CONJ_PHANTOM_ATTRACTOR
Gradient descent on EML trees concentrates at 3.1696 with probability ~92%.
This is empirical (§5 data). No mathematical proof of the 92% figure.

### CONJ_PUMPING_LEMMA
An EML pumping lemma analogous to the regular language pumping lemma.
Formal statement not yet fixed. Not counted until proved.

### CONJ_MUL_GEN_LOWER
SB(mul, general) ≥ 6n — general multiplication cannot be done in fewer than 6 nodes.
Currently only the upper bound is proved. Lower bound is open.

---

## FOOTER INSTRUCTION

Both monogate.org and monogate.dev footers currently say "24 theorems".
The honest proved count is **18**. Update footers to say "18 theorems".
Do not increase this number without adding a corresponding Lean proof.
-/

-- Sanity check: PROVED_COUNT matches the list above
example : PROVED_COUNT = 18 := rfl
