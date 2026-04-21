-- MonogateEML/MulLowerBound.lean
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Data.Complex.ExponentialBounds

/-!
# Mul Lower Bound: SB(mul) ≥ 2 (all reals)

No single F16 operator computes multiplication x * y for all real inputs x, y.
Combined with the 1-node construction F16fn(x,y) = exp(log(x)+log(y)) = x*y for x,y > 0,
this shows the general-domain cost is ≥ 2.

## Proof strategy

For each of the 16 F16 operators, exhibit a concrete witness pair (x₀, y₀)
where op(x₀, y₀) ≠ x₀ * y₀. All inequalities discharged by `linarith` /
`nlinarith` with `Real.exp_one_gt_d9`, `Real.log_pos`, `Real.exp_pos`.

## No sorries
-/

open Real

private lemma two_lt_e : (2 : ℝ) < Real.exp 1 :=
  lt_trans (by norm_num) Real.exp_one_gt_d9

private lemma eneg_lt_one_m : Real.exp (-1) < 1 := by
  have h : Real.exp (-1) * Real.exp 1 = 1 := by
    have := Real.exp_add (-1) 1
    simp only [show (-1:ℝ)+1=0 from by norm_num, Real.exp_zero] at this; linarith
  nlinarith [Real.exp_pos (-1), two_lt_e]

private lemma log2_pos_m : (0:ℝ) < Real.log 2 := Real.log_pos (by norm_num)

-- 16 F16 operators (same definitions as AddLowerBound)
noncomputable def M_F1  (x y : ℝ) : ℝ := Real.exp x - Real.log y
noncomputable def M_F2  (x y : ℝ) : ℝ := Real.exp x - Real.log (-y)
noncomputable def M_F3  (x y : ℝ) : ℝ := Real.exp (-x) - Real.log y
noncomputable def M_F4  (x y : ℝ) : ℝ := Real.exp (-x) - Real.log (-y)
noncomputable def M_F5  (x y : ℝ) : ℝ := Real.exp y - Real.log x
noncomputable def M_F6  (x y : ℝ) : ℝ := Real.exp (-y) - Real.log x
noncomputable def M_F7  (x y : ℝ) : ℝ := Real.exp y - Real.log (-x)
noncomputable def M_F8  (x y : ℝ) : ℝ := Real.exp (-y) - Real.log (-x)
noncomputable def M_F9  (x y : ℝ) : ℝ := x - Real.log y
noncomputable def M_F10 (x y : ℝ) : ℝ := x - Real.log (-y)
noncomputable def M_F11 (x y : ℝ) : ℝ := Real.log (Real.exp x + y)
noncomputable def M_F12 (x y : ℝ) : ℝ := Real.log (Real.exp x - y)
noncomputable def M_F13 (x y : ℝ) : ℝ := Real.exp (x * Real.log y)
noncomputable def M_F14 (x y : ℝ) : ℝ := Real.exp (x + Real.log y)
noncomputable def M_F15 (x y : ℝ) : ℝ := Real.exp (x + Real.log (-y))
noncomputable def M_F16 (x y : ℝ) : ℝ := Real.exp (Real.log x + Real.log y)

-- Witnesses for each operator:

-- F1(1,1) = exp(1) - log(1) = exp(1) ≠ 1*1 = 1
theorem M_F1_ne_mul : ¬ (∀ x y : ℝ, M_F1 x y = x * y) := by
  intro h; have := h 1 1; simp [M_F1, Real.log_one] at this; linarith [two_lt_e]

-- F2(0,-1) = exp(0) - log(1) = 1 ≠ 0*(-1) = 0
theorem M_F2_ne_mul : ¬ (∀ x y : ℝ, M_F2 x y = x * y) := by
  intro h; have := h 0 (-1); simp [M_F2, neg_neg, Real.log_one, Real.exp_zero] at this; linarith

-- F3(1,1) = exp(-1) - log(1) = exp(-1) ≠ 1*1 = 1
theorem M_F3_ne_mul : ¬ (∀ x y : ℝ, M_F3 x y = x * y) := by
  intro h; have := h 1 1; simp [M_F3, Real.log_one] at this; linarith [eneg_lt_one_m]

-- F4(0,-1) = exp(0) - log(1) = 1 ≠ 0*(-1) = 0
theorem M_F4_ne_mul : ¬ (∀ x y : ℝ, M_F4 x y = x * y) := by
  intro h; have := h 0 (-1); simp [M_F4, neg_neg, Real.log_one, Real.exp_zero] at this; linarith

-- F5(1,1) = exp(1) - log(1) = exp(1) ≠ 1*1 = 1
theorem M_F5_ne_mul : ¬ (∀ x y : ℝ, M_F5 x y = x * y) := by
  intro h; have := h 1 1; simp [M_F5, Real.log_one] at this; linarith [two_lt_e]

-- F6(1,1) = exp(-1) - log(1) = exp(-1) ≠ 1*1 = 1
theorem M_F6_ne_mul : ¬ (∀ x y : ℝ, M_F6 x y = x * y) := by
  intro h; have := h 1 1; simp [M_F6, Real.log_one] at this; linarith [eneg_lt_one_m]

-- F7(-1,0) = exp(0) - log(-(-1)) = exp(0) - log(1) = 1 ≠ (-1)*0 = 0
theorem M_F7_ne_mul : ¬ (∀ x y : ℝ, M_F7 x y = x * y) := by
  intro h; have := h (-1) 0; simp [M_F7, Real.exp_zero, neg_neg, Real.log_one] at this; linarith

-- F8(-1,0) = exp(-0) - log(-(-1)) = 1 - log(1) = 1 ≠ 0
theorem M_F8_ne_mul : ¬ (∀ x y : ℝ, M_F8 x y = x * y) := by
  intro h; have := h (-1) 0
  simp [M_F8, neg_zero, Real.exp_zero, neg_neg, Real.log_one] at this; linarith

-- F9(1,2) = 1 - log(2) ≠ 1*2 = 2 (since log(2) > 0 implies 1-log(2) < 1 < 2)
theorem M_F9_ne_mul : ¬ (∀ x y : ℝ, M_F9 x y = x * y) := by
  intro h; have := h 1 2; simp [M_F9] at this
  -- this : 1 - log 2 = 2, so log 2 = -1. But log 2 > 0.
  linarith [log2_pos_m]

-- F10(1,-1) = 1 - log(-(-1)) = 1 - log(1) = 1 ≠ 1*(-1) = -1
theorem M_F10_ne_mul : ¬ (∀ x y : ℝ, M_F10 x y = x * y) := by
  intro h; have := h 1 (-1); simp [M_F10, neg_neg, Real.log_one] at this; linarith

-- F11(0,1) = log(exp(0)+1) = log(2) ≠ 0*1 = 0 (log(2) > 0)
theorem M_F11_ne_mul : ¬ (∀ x y : ℝ, M_F11 x y = x * y) := by
  intro h; have h01 := h 0 1; simp [M_F11, Real.exp_zero] at h01
  -- h01 : log 2 = 0. But log 2 > 0.
  linarith [log2_pos_m]

-- F12(0,-1) = log(exp(0) - (-1)) = log(2) ≠ 0*(-1) = 0
theorem M_F12_ne_mul : ¬ (∀ x y : ℝ, M_F12 x y = x * y) := by
  intro h; have h0 := h 0 (-1); simp [M_F12, Real.exp_zero] at h0
  linarith [log2_pos_m]

-- F13(0,1) = exp(0 * log(1)) = exp(0) = 1 ≠ 0*1 = 0
theorem M_F13_ne_mul : ¬ (∀ x y : ℝ, M_F13 x y = x * y) := by
  intro h; have := h 0 1; simp [M_F13, Real.log_one, Real.exp_zero] at this; linarith

-- F14(0,1) = exp(0 + log(1)) = exp(0) = 1 ≠ 0*1 = 0
theorem M_F14_ne_mul : ¬ (∀ x y : ℝ, M_F14 x y = x * y) := by
  intro h; have := h 0 1; simp [M_F14, Real.log_one, Real.exp_zero] at this; linarith

-- F15(0,-1) = exp(0 + log(-(-1))) = exp(0 + log(1)) = exp(0) = 1 ≠ 0*(-1) = 0
theorem M_F15_ne_mul : ¬ (∀ x y : ℝ, M_F15 x y = x * y) := by
  intro h; have := h 0 (-1); simp [M_F15, neg_neg, Real.log_one, Real.exp_zero] at this; linarith

-- F16fn(0,1): exp(log(0) + log(1)) = exp(0+0) = exp(0) = 1 ≠ 0*1 = 0
-- (Real.log 0 = 0 and Real.log 1 = 0 by Mathlib convention)
theorem M_F16_ne_mul : ¬ (∀ x y : ℝ, M_F16 x y = x * y) := by
  intro h; have := h 0 1
  simp [M_F16, Real.log_zero, Real.log_one, Real.exp_zero] at this

def m_f16_ops : List (ℝ → ℝ → ℝ) :=
  [M_F1, M_F2, M_F3, M_F4, M_F5, M_F6, M_F7, M_F8,
   M_F9, M_F10, M_F11, M_F12, M_F13, M_F14, M_F15, M_F16]

theorem no_f16_computes_mul :
    ∀ op ∈ m_f16_ops, ¬ (∀ x y : ℝ, op x y = x * y) := by
  intro op hmem
  simp only [m_f16_ops, List.mem_cons, List.mem_nil_iff, or_false] at hmem
  rcases hmem with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl |
                   rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
  · exact M_F1_ne_mul
  · exact M_F2_ne_mul
  · exact M_F3_ne_mul
  · exact M_F4_ne_mul
  · exact M_F5_ne_mul
  · exact M_F6_ne_mul
  · exact M_F7_ne_mul
  · exact M_F8_ne_mul
  · exact M_F9_ne_mul
  · exact M_F10_ne_mul
  · exact M_F11_ne_mul
  · exact M_F12_ne_mul
  · exact M_F13_ne_mul
  · exact M_F14_ne_mul
  · exact M_F15_ne_mul
  · exact M_F16_ne_mul

def mul_one_node_computable (f : ℝ → ℝ → ℝ) : Prop :=
  ∃ op ∈ m_f16_ops, ∀ x y : ℝ, f x y = op x y

/-- **Main result**: SB(mul) ≥ 2 — multiplication cannot be computed by a single F16 node
    for all real inputs. -/
theorem SB_mul_ge_two : ¬ mul_one_node_computable (· * ·) := by
  intro ⟨op, hmem, heq⟩
  exact no_f16_computes_mul op hmem (fun x y => (heq x y).symm)
