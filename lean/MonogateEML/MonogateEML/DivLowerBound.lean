-- MonogateEML/DivLowerBound.lean
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Data.Complex.ExponentialBounds

/-!
# Div Lower Bound: SB(div) ≥ 2 (all reals)

No single F16 operator computes division x / y for all real inputs x, y.
Combined with the 1-node construction exp(log(x) − log(y)) = x/y for x,y > 0,
this shows the general-domain cost is ≥ 2.

## Proof strategy

For each of the 16 F16 operators, exhibit a concrete witness pair (x₀, y₀)
where op(x₀, y₀) ≠ x₀ / y₀. All inequalities discharged by `linarith` /
`nlinarith` with `Real.exp_one_gt_d9`, `Real.log_pos`, `Real.exp_pos`.

## No sorries
-/

open Real

private lemma two_lt_e_d : (2 : ℝ) < Real.exp 1 :=
  lt_trans (by norm_num) Real.exp_one_gt_d9

private lemma eneg_lt_one_d : Real.exp (-1) < 1 := by
  have h : Real.exp (-1) * Real.exp 1 = 1 := by
    have := Real.exp_add (-1) 1
    simp only [show (-1:ℝ)+1=0 from by norm_num, Real.exp_zero] at this; linarith
  nlinarith [Real.exp_pos (-1), two_lt_e_d]

private lemma log2_pos_d : (0:ℝ) < Real.log 2 := Real.log_pos (by norm_num)

-- 16 F16 operators (same definitions as MulLowerBound, prefixed D_)
noncomputable def D_F1  (x y : ℝ) : ℝ := Real.exp x - Real.log y
noncomputable def D_F2  (x y : ℝ) : ℝ := Real.exp x - Real.log (-y)
noncomputable def D_F3  (x y : ℝ) : ℝ := Real.exp (-x) - Real.log y
noncomputable def D_F4  (x y : ℝ) : ℝ := Real.exp (-x) - Real.log (-y)
noncomputable def D_F5  (x y : ℝ) : ℝ := Real.exp y - Real.log x
noncomputable def D_F6  (x y : ℝ) : ℝ := Real.exp (-y) - Real.log x
noncomputable def D_F7  (x y : ℝ) : ℝ := Real.exp y - Real.log (-x)
noncomputable def D_F8  (x y : ℝ) : ℝ := Real.exp (-y) - Real.log (-x)
noncomputable def D_F9  (x y : ℝ) : ℝ := x - Real.log y
noncomputable def D_F10 (x y : ℝ) : ℝ := x - Real.log (-y)
noncomputable def D_F11 (x y : ℝ) : ℝ := Real.log (Real.exp x + y)
noncomputable def D_F12 (x y : ℝ) : ℝ := Real.log (Real.exp x - y)
noncomputable def D_F13 (x y : ℝ) : ℝ := Real.exp (x * Real.log y)
noncomputable def D_F14 (x y : ℝ) : ℝ := Real.exp (x + Real.log y)
noncomputable def D_F15 (x y : ℝ) : ℝ := Real.exp (x + Real.log (-y))
noncomputable def D_F16 (x y : ℝ) : ℝ := Real.exp (Real.log x + Real.log y)

-- Witnesses for each operator:

-- F1(1,1) = exp(1) - log(1) = exp(1) ≠ 1/1 = 1
theorem D_F1_ne_div : ¬ (∀ x y : ℝ, D_F1 x y = x / y) := by
  intro h; have := h 1 1; simp [D_F1, Real.log_one] at this; linarith [two_lt_e_d]

-- F2(0,-1) = exp(0) - log(1) = 1 ≠ 0/(-1) = 0
theorem D_F2_ne_div : ¬ (∀ x y : ℝ, D_F2 x y = x / y) := by
  intro h; have := h 0 (-1); simp [D_F2, neg_neg, Real.log_one, Real.exp_zero] at this; linarith

-- F3(1,1) = exp(-1) - log(1) = exp(-1) ≠ 1/1 = 1
theorem D_F3_ne_div : ¬ (∀ x y : ℝ, D_F3 x y = x / y) := by
  intro h; have := h 1 1; simp [D_F3, Real.log_one] at this; linarith [eneg_lt_one_d]

-- F4(0,-1) = exp(0) - log(1) = 1 ≠ 0/(-1) = 0
theorem D_F4_ne_div : ¬ (∀ x y : ℝ, D_F4 x y = x / y) := by
  intro h; have := h 0 (-1); simp [D_F4, neg_neg, Real.log_one, Real.exp_zero] at this; linarith

-- F5(1,1) = exp(1) - log(1) = exp(1) ≠ 1/1 = 1
theorem D_F5_ne_div : ¬ (∀ x y : ℝ, D_F5 x y = x / y) := by
  intro h; have := h 1 1; simp [D_F5, Real.log_one] at this; linarith [two_lt_e_d]

-- F6(1,1) = exp(-1) - log(1) = exp(-1) ≠ 1/1 = 1
theorem D_F6_ne_div : ¬ (∀ x y : ℝ, D_F6 x y = x / y) := by
  intro h; have := h 1 1; simp [D_F6, Real.log_one] at this; linarith [eneg_lt_one_d]

-- F7(-1,0) = exp(0) - log(1) = 1 ≠ (-1)/0 = 0 (div by 0 = 0 in Lean)
theorem D_F7_ne_div : ¬ (∀ x y : ℝ, D_F7 x y = x / y) := by
  intro h; have := h (-1) 0
  simp [D_F7, Real.exp_zero, neg_neg, Real.log_one] at this; linarith

-- F8(-1,0) = exp(0) - log(1) = 1 ≠ (-1)/0 = 0
theorem D_F8_ne_div : ¬ (∀ x y : ℝ, D_F8 x y = x / y) := by
  intro h; have := h (-1) 0
  simp [D_F8, neg_zero, Real.exp_zero, neg_neg, Real.log_one] at this; linarith

-- F9(1,2) = 1 - log(2) ≠ 1/2 = 0.5 (since 1 - log(2) < 1 < 1.5 … actually need both sides)
-- Use witness (0,2): 0 - log(2) = -log(2) ≠ 0/2 = 0, and log(2) > 0
theorem D_F9_ne_div : ¬ (∀ x y : ℝ, D_F9 x y = x / y) := by
  intro h; have := h 0 2; simp [D_F9] at this
  linarith [log2_pos_d]

-- F10(0,-2) = 0 - log(2) = -log(2) ≠ 0/(-2) = 0
theorem D_F10_ne_div : ¬ (∀ x y : ℝ, D_F10 x y = x / y) := by
  intro h; have := h 0 (-2)
  simp [D_F10, show -(-2:ℝ) = 2 from by norm_num] at this
  linarith [log2_pos_d]

-- F11(0,1) = log(exp(0)+1) = log(2) ≠ 0/1 = 0
theorem D_F11_ne_div : ¬ (∀ x y : ℝ, D_F11 x y = x / y) := by
  intro h; have h01 := h 0 1; simp [D_F11, Real.exp_zero] at h01
  linarith [log2_pos_d]

-- F12(0,-1) = log(exp(0) - (-1)) = log(2) ≠ 0/(-1) = 0
theorem D_F12_ne_div : ¬ (∀ x y : ℝ, D_F12 x y = x / y) := by
  intro h; have h0 := h 0 (-1); simp [D_F12, Real.exp_zero] at h0
  linarith [log2_pos_d]

-- F13(0,1) = exp(0 * log(1)) = exp(0) = 1 ≠ 0/1 = 0
theorem D_F13_ne_div : ¬ (∀ x y : ℝ, D_F13 x y = x / y) := by
  intro h; have := h 0 1; simp [D_F13, Real.log_one, Real.exp_zero] at this; linarith

-- F14(0,1) = exp(0 + log(1)) = exp(0) = 1 ≠ 0/1 = 0
theorem D_F14_ne_div : ¬ (∀ x y : ℝ, D_F14 x y = x / y) := by
  intro h; have := h 0 1; simp [D_F14, Real.log_one, Real.exp_zero] at this; linarith

-- F15(0,-1) = exp(0 + log(1)) = 1 ≠ 0/(-1) = 0
theorem D_F15_ne_div : ¬ (∀ x y : ℝ, D_F15 x y = x / y) := by
  intro h; have := h 0 (-1); simp [D_F15, neg_neg, Real.log_one, Real.exp_zero] at this; linarith

-- F16fn(0,1): exp(log(0) + log(1)) = exp(0) = 1 ≠ 0/1 = 0
theorem D_F16_ne_div : ¬ (∀ x y : ℝ, D_F16 x y = x / y) := by
  intro h; have := h 0 1
  simp [D_F16, Real.log_zero, Real.log_one, Real.exp_zero] at this

def d_f16_ops : List (ℝ → ℝ → ℝ) :=
  [D_F1, D_F2, D_F3, D_F4, D_F5, D_F6, D_F7, D_F8,
   D_F9, D_F10, D_F11, D_F12, D_F13, D_F14, D_F15, D_F16]

theorem no_f16_computes_div :
    ∀ op ∈ d_f16_ops, ¬ (∀ x y : ℝ, op x y = x / y) := by
  intro op hmem
  simp only [d_f16_ops, List.mem_cons, List.mem_nil_iff, or_false] at hmem
  rcases hmem with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl |
                   rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
  · exact D_F1_ne_div
  · exact D_F2_ne_div
  · exact D_F3_ne_div
  · exact D_F4_ne_div
  · exact D_F5_ne_div
  · exact D_F6_ne_div
  · exact D_F7_ne_div
  · exact D_F8_ne_div
  · exact D_F9_ne_div
  · exact D_F10_ne_div
  · exact D_F11_ne_div
  · exact D_F12_ne_div
  · exact D_F13_ne_div
  · exact D_F14_ne_div
  · exact D_F15_ne_div
  · exact D_F16_ne_div

def div_one_node_computable (f : ℝ → ℝ → ℝ) : Prop :=
  ∃ op ∈ d_f16_ops, ∀ x y : ℝ, f x y = op x y

/-- **Main result**: SB(div) ≥ 2 — division cannot be computed by a single F16 node
    for all real inputs. -/
theorem SB_div_ge_two : ¬ div_one_node_computable (· / ·) := by
  intro ⟨op, hmem, heq⟩
  exact no_f16_computes_div op hmem (fun x y => (heq x y).symm)
