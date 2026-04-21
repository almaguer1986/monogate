-- MonogateEML/UpperBounds.lean
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Analysis.SpecialFunctions.ExpDeriv

/-!
# Upper Bounds: Explicit 1-Node F16 Constructions

Algebraic identity proofs establishing that several SuperBEST operations
can be computed by a SINGLE F16-orbit node.

F16 operator family (selected):
  F1(x,y)  = exp(x) − log(y)
  F13(x,y) = exp(x · log(y))        [EPL — "exponential power law"]
  F14(x,y) = exp(x + log(y))
  F16(x,y) = exp(log(x) + log(y))   [F16fn — the generating operator]

All constructions use only F16-orbit primitives and apply for the stated domain.

## No sorries
-/

open Real

-- ===================================================================
-- 1. exp(x) = F1(x, 1) — for all real x
-- ===================================================================

/-- exp(x) is computable by a single F16 node: F1(x, 1) = exp(x) − log(1) = exp(x). -/
theorem exp_one_node (x : ℝ) : Real.exp x - Real.log 1 = Real.exp x := by
  simp [Real.log_one]

/-- Equivalently stated using the operator form. -/
theorem exp_is_one_node_all_reals (x : ℝ) :
    (fun x y => Real.exp x - Real.log y) x 1 = Real.exp x := by
  simp [Real.log_one]

-- ===================================================================
-- 2. x * y = F16(x, y) for x > 0, y > 0
-- ===================================================================

/-- Multiplication is a single F16 node on the positive domain:
    F16fn(x,y) = exp(log(x) + log(y)) = x · y for x,y > 0. -/
theorem mul_one_node_positive (x y : ℝ) (hx : 0 < x) (hy : 0 < y) :
    Real.exp (Real.log x + Real.log y) = x * y := by
  rw [Real.exp_add, Real.exp_log hx, Real.exp_log hy]

-- ===================================================================
-- 3. x ^ n = F13(n, x) for x > 0, n : ℝ
-- ===================================================================

/-- Real power x^n is a single F16 node via EPL:
    F13(n, x) = exp(n · log(x)) = x^n for x > 0. -/
theorem rpow_one_node_positive (n x : ℝ) (hx : 0 < x) :
    Real.exp (n * Real.log x) = x ^ n := by
  rw [Real.rpow_def_of_pos hx]

-- ===================================================================
-- 4. 1 / x = F13(-1, x) for x > 0
-- ===================================================================

/-- Reciprocal is a single F16 node via EPL with exponent −1:
    F13(−1, x) = exp(−1 · log(x)) = exp(−log(x)) = 1/x for x > 0. -/
theorem recip_one_node_positive (x : ℝ) (hx : 0 < x) :
    Real.exp ((-1) * Real.log x) = 1 / x := by
  rw [rpow_one_node_positive (-1) x hx]
  simp [Real.rpow_neg (le_of_lt hx), Real.rpow_one]

-- ===================================================================
-- 5. sqrt(x) = F13(1/2, x) for x > 0
-- (Reproduced from ModelAudit.lean for completeness; same proof)
-- ===================================================================

/-- Square root is a single F16 node via EPL with exponent 1/2:
    F13(1/2, x) = exp((1/2)·log(x)) = √x for x > 0. -/
theorem sqrt_one_node_positive' (x : ℝ) (hx : 0 < x) :
    Real.exp ((1/2) * Real.log x) = Real.sqrt x := by
  rw [Real.sqrt_eq_rpow, rpow_one_node_positive]

-- ===================================================================
-- 6. exp(x + log(y)) = exp(x) * y  [F14 identity]  for y > 0
-- ===================================================================

/-- F14 identity: exp(x + log(y)) = exp(x) · y for y > 0.
    Useful for computing exp(x) * y with a single F14 node. -/
theorem f14_identity (x y : ℝ) (hy : 0 < y) :
    Real.exp (x + Real.log y) = Real.exp x * y := by
  rw [Real.exp_add, Real.exp_log hy]

-- ===================================================================
-- Summary: SuperBEST positive-domain 1-node operations
-- ===================================================================

/-- All six 1-node positive-domain results, collected. -/
theorem superbest_positive_one_node_ops :
    (∀ x : ℝ, Real.exp x - Real.log 1 = Real.exp x) ∧          -- exp: 1n
    (∀ x y : ℝ, 0 < x → 0 < y →
      Real.exp (Real.log x + Real.log y) = x * y) ∧             -- mul: 1n (x,y>0)
    (∀ n x : ℝ, 0 < x → Real.exp (n * Real.log x) = x ^ n) ∧   -- pow: 1n (x>0)
    (∀ x : ℝ, 0 < x →
      Real.exp ((-1) * Real.log x) = 1 / x) ∧                   -- recip: 1n (x>0)
    (∀ x : ℝ, 0 < x →
      Real.exp ((1/2) * Real.log x) = Real.sqrt x) :=            -- sqrt: 1n (x>0)
  ⟨fun x => by simp [Real.log_one],
   mul_one_node_positive,
   rpow_one_node_positive,
   recip_one_node_positive,
   sqrt_one_node_positive'⟩
