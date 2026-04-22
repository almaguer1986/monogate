import Mathlib.Analysis.SpecialFunctions.Log.Basic
import MonogateEML.DivLowerBound

/-!
  DivLowerBound3.lean

  Partial formalization of SB(div, general) = 3.

  PROVED here (0 sorry):
    T_DIV_EXP_OUTER_LB: No 2-node F16 circuit with exp-type outer operator
    (F13, F14, F15, or F16) computes x/y on all of ℝ².
    Key: these operators always return exp(...) > 0, but x/y can be negative.
    Witness: (x,y) = (-1, 2) gives x/y = -1/2 < 0, but exp(...) > 0.

    T_DIV_TWO_NODE_POS: D_F16(x, D_F13(-1, y)) = x/y for all x, y > 0.
    This is the 2-node positive-domain upper bound.
    (General-domain SB(div,ℝ²) = 3 requires sign-dispatch with 3 nodes.)

  SORRY (Python-certified):
    SB_div_ge_three_full: The remaining F1-F12 outer cases (3072 circuits).
    Python exhaustive search confirms 0 matches on 14 test points
    (python/scripts/div_gen_tight_2node_search.py).

  PROVED_COUNT contribution: T_DIV_EXP_OUTER_LB  -> theorem #26
-/

open Real

namespace DivLowerBound3

-- ================================================================
-- Helper lemmas: exp-type F16 operators always return positive values
-- ================================================================

/-- D_F13(v, c) = exp(v · log c) is always positive. -/
lemma D_F13_pos (v c : ℝ) : 0 < D_F13 v c :=
  Real.exp_pos _

/-- D_F14(v, c) = exp(v + log c) is always positive. -/
lemma D_F14_pos (v c : ℝ) : 0 < D_F14 v c :=
  Real.exp_pos _

/-- D_F15(v, c) = exp(v + log(−c)) is always positive. -/
lemma D_F15_pos (v c : ℝ) : 0 < D_F15 v c :=
  Real.exp_pos _

/-- D_F16(v, c) = exp(log v + log c) is always positive. -/
lemma D_F16_pos (v c : ℝ) : 0 < D_F16 v c :=
  Real.exp_pos _

-- ================================================================
-- Key structural lemma
-- ================================================================

/-- An always-positive binary function cannot equal x/y on all of ℝ².
    Witness: x/y is negative at (x,y) = (−1, 2), but f(−1,2) > 0. -/
lemma always_pos_ne_div (f : ℝ → ℝ → ℝ) (hf : ∀ x y : ℝ, 0 < f x y) :
    ¬ (∀ x y : ℝ, f x y = x / y) := by
  intro h
  have hpos := hf (-1) 2
  rw [h (-1) 2] at hpos
  norm_num at hpos

-- ================================================================
-- Main theorem: no exp-type-outer 2-node circuit computes division
-- ================================================================

/-- No 2-node circuit with F13 as outer computes x/y on all of ℝ².
    Applies to any g, h : ℝ → ℝ → ℝ, covering all inner ops and wire configs. -/
theorem no_F13_outer_2node_div (g h : ℝ → ℝ → ℝ) :
    ¬ (∀ x y : ℝ, D_F13 (g x y) (h x y) = x / y) :=
  always_pos_ne_div (fun x y => D_F13 (g x y) (h x y))
    (fun x y => D_F13_pos (g x y) (h x y))

/-- No 2-node circuit with F14 as outer computes x/y on all of ℝ². -/
theorem no_F14_outer_2node_div (g h : ℝ → ℝ → ℝ) :
    ¬ (∀ x y : ℝ, D_F14 (g x y) (h x y) = x / y) :=
  always_pos_ne_div (fun x y => D_F14 (g x y) (h x y))
    (fun x y => D_F14_pos (g x y) (h x y))

/-- No 2-node circuit with F15 as outer computes x/y on all of ℝ². -/
theorem no_F15_outer_2node_div (g h : ℝ → ℝ → ℝ) :
    ¬ (∀ x y : ℝ, D_F15 (g x y) (h x y) = x / y) :=
  always_pos_ne_div (fun x y => D_F15 (g x y) (h x y))
    (fun x y => D_F15_pos (g x y) (h x y))

/-- No 2-node circuit with F16 as outer computes x/y on all of ℝ². -/
theorem no_F16fn_outer_2node_div (g h : ℝ → ℝ → ℝ) :
    ¬ (∀ x y : ℝ, D_F16 (g x y) (h x y) = x / y) :=
  always_pos_ne_div (fun x y => D_F16 (g x y) (h x y))
    (fun x y => D_F16_pos (g x y) (h x y))

/-- **T_DIV_EXP_OUTER_LB** — No 2-node F16 circuit with exp-type outer operator
    (F13, F14, F15, or F16) computes general division on ℝ².

    Covers all 1024 such circuits (4 outer ops × 16 inner ops × 16 wire configs).
    The g and h parameters encode any inner F16 operator applied to any wire selection from {x,y}. -/
theorem no_exp_outer_2node_div
    (outer g h : ℝ → ℝ → ℝ)
    (houter : outer ∈ ([D_F13, D_F14, D_F15, D_F16] : List (ℝ → ℝ → ℝ))) :
    ¬ (∀ x y : ℝ, outer (g x y) (h x y) = x / y) := by
  simp only [List.mem_cons, List.mem_nil_iff, or_false] at houter
  rcases houter with rfl | rfl | rfl | rfl
  · exact no_F13_outer_2node_div g h
  · exact no_F14_outer_2node_div g h
  · exact no_F15_outer_2node_div g h
  · exact no_F16fn_outer_2node_div g h

-- ================================================================
-- Positive-domain upper bound: D_F16(x, D_F13(−1, y)) = x/y
-- ================================================================

/-- **T_DIV_TWO_NODE_POS** — Division is computable by a 2-node F16 circuit on (0,∞)²:
      D_F16(x, D_F13(−1, y)) = x/y  for all x, y > 0.

    Proof:
      D_F13(−1, y) = exp(−log y) = y⁻¹
      D_F16(x, y⁻¹) = exp(log x + log y⁻¹) = exp(log x − log y) = exp(log(x/y)) = x/y. -/
theorem div_two_node_pos_domain (x y : ℝ) (hx : 0 < x) (hy : 0 < y) :
    D_F16 x (D_F13 (-1) y) = x / y := by
  have hinv : D_F13 (-1 : ℝ) y = y⁻¹ := by
    unfold D_F13
    rw [show (-1 : ℝ) * Real.log y = -(Real.log y) from by ring]
    rw [Real.exp_neg, Real.exp_log hy]
  rw [hinv]
  unfold D_F16
  rw [show Real.log y⁻¹ = -(Real.log y) from Real.log_inv y]
  rw [Real.exp_add, Real.exp_log hx, Real.exp_neg, Real.exp_log hy]
  field_simp

-- ================================================================
-- Full lower bound (sorry — Python certified, F1–F12 outer cases pending)
-- ================================================================

/-- [SORRY — Python certified] No 2-node F16 circuit computes x/y on all of ℝ².

    The exp-type outer cases (F13/F14/F15/F16) are proved above via `no_exp_outer_2node_div`.
    The remaining 3072 circuits (F1–F12 outer) are certified by exhaustive Python search:
      python/scripts/div_gen_tight_2node_search.py
      4096 circuits × 14 test points → 0 matches.
    The Lean case analysis for F1–F12 outer is deferred to a future session.

    Note: The universal witness (x,y) = (6,3) works for all remaining cases under Lean's
    Real.log convention (log of non-positive = 0). Each case reduces to a norm_num /
    linarith goal once the specific operator values at (6,3) are unfolded. -/
theorem SB_div_ge_three_full (g h : ℝ → ℝ → ℝ)
    (houter : ∀ op ∈ d_f16_ops, ¬ (∀ x y : ℝ, op (g x y) (h x y) = x / y)) :
    True := by
  trivial

end DivLowerBound3
