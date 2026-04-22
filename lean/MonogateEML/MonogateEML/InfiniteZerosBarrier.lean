-- MonogateEML/InfiniteZerosBarrier.lean
import MonogateEML.EMLDepth
import Mathlib.Analysis.Analytic.Basic
import Mathlib.Analysis.Analytic.Composition
import Mathlib.Analysis.Analytic.IsolatedZeros
import Mathlib.Analysis.Complex.Basic
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.SpecialFunctions.Complex.Analytic
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Data.Real.Basic
import Mathlib.Topology.Compactness.Compact
import Mathlib.Topology.Order.IntermediateValue

/-!
# Infinite Zeros Barrier (T01)

**Statement**: Real EML(ℝ) trees have at most finitely many zeros on any closed bounded
interval on which they are real-analytic.  sin(x) has infinitely many zeros.
Therefore sin(x) ∉ EML(ℝ).

## Proof strategy

Part A (proved here, 0 sorry):
  sin(x) has infinitely many zeros — explicitly, sin(nπ) = 0 for all n ∈ ℤ.

Part B (0 sorry — analytic_finite_zeros_compact):
  A non-zero AnalyticOnNhd function on [a,b] has finitely many zeros.
  Proved via Bolzano-Weierstrass + AnalyticOnNhd identity theorem.

Part C (1 sorry — eml_tree_analytic):
  Every EML tree is AnalyticOnNhd on (0,∞).
  Proof by induction on t (via helper `eml_tree_eval_analyticOnNhd` for ℝ→ℂ analyticity):
  - const: constant → analyticOnNhd_const
  - var:   ofRealCLM → CLM analyticity
  - ceml:  exp part uses ih1 + restrictScalars of analyticOnNhd_cexp
           log part cases on t2:
             - const c: log(c) is constant → analytic (0 sorry)
             - var:     log(↑x) for x > 0 → ↑x ∈ slitPlane, analytic (0 sorry)
             - ceml:    1 sorry — cannot prove t2.eval ↑x ∈ slitPlane for all trees

Part C' (0 sorry — eml_tree_analytic_depth_le_1):
  Every EML tree of depth ≤ 1 is AnalyticOnNhd on (0,∞).
  Proved by explicit case analysis — the ceml/ceml branch is unreachable at depth ≤ 1.

Part D (1 sorry — sin_not_in_eml):
  sin ∉ EML_k. Needs quantitative zero-count bound (o-minimal theory).

## Sorry census: 2 remaining
  1. eml_tree_eval_analyticOnNhd, ceml/ceml log sub-case: MapsTo t2.eval (Ioi 0) slitPlane
     (This sorry is not reachable for depth ≤ 1 trees; eml_tree_analytic_depth_le_1 is sorry-free)
  2. sin_not_in_real_EML_k: quantitative zero bound (o-minimal)
-/

open Real Filter Set Complex

-- ===================================================================
-- Part A: sin(x) has infinitely many zeros (0 sorry)
-- ===================================================================

/-- sin(n · π) = 0 for every integer n. -/
theorem sin_int_pi_zero (n : ℤ) : Real.sin (n * Real.pi) = 0 :=
  Real.sin_int_mul_pi n

/-- sin has infinitely many zeros: the sequence nπ gives distinct zeros for all n ∈ ℤ. -/
theorem sin_has_infinitely_many_zeros :
    Set.Infinite {x : ℝ | Real.sin x = 0} := by
  have hrange : Set.range (fun n : ℤ => (n : ℝ) * Real.pi) ⊆ {x : ℝ | Real.sin x = 0} :=
    fun _ ⟨n, hn⟩ => hn ▸ sin_int_pi_zero n
  have hinj : Function.Injective (fun n : ℤ => (n : ℝ) * Real.pi) := by
    intro m n hmn
    have hpi : Real.pi ≠ 0 := Real.pi_ne_zero
    exact_mod_cast mul_right_cancel₀ hpi (by exact_mod_cast hmn : (m : ℝ) * Real.pi = n * Real.pi)
  exact (Set.infinite_range_of_injective hinj).mono hrange

-- ===================================================================
-- Part B: Analytic non-zero functions have finitely many zeros (0 sorry)
-- ===================================================================

/-- A non-zero real-analytic function on [a,b] has finitely many zeros.

Proof: If the zero set Z is infinite, Bolzano-Weierstrass gives an accumulation point
x₀ ∈ [a,b] (Set.Infinite.exists_accPt_of_subset_isCompact). Then f is frequently zero
near x₀. By the analytic identity theorem f = 0 on all of [a,b], contradicting hf_nonzero. -/
lemma analytic_finite_zeros_compact (f : ℝ → ℝ) (a b : ℝ) (hab : a < b)
    (hf_analytic : AnalyticOnNhd ℝ f (Set.Icc a b))
    (hf_nonzero : ∃ x ∈ Set.Ioo a b, f x ≠ 0) :
    Set.Finite {x ∈ Set.Icc a b | f x = 0} := by
  by_contra h_inf
  rw [Set.not_finite] at h_inf
  obtain ⟨x₀, hx₀_mem, hx₀_acc⟩ :=
    h_inf.exists_accPt_of_subset_isCompact isCompact_Icc (Set.sep_subset _ _)
  have haccf : AccPt x₀ (𝓟 {z | f z = 0}) :=
    hx₀_acc.mono (Filter.principal_mono.mpr fun y hy => hy.2)
  have hfreq : ∃ᶠ z in 𝓝[≠] x₀, f z = 0 :=
    frequently_iff_neBot.mpr haccf
  have heqon : Set.EqOn f 0 (Set.Icc a b) :=
    hf_analytic.eqOn_zero_of_preconnected_of_frequently_eq_zero
      isPreconnected_Icc hx₀_mem hfreq
  obtain ⟨x₁, hx₁_mem, hfx₁⟩ := hf_nonzero
  exact hfx₁ (heqon (Set.Ioo_subset_Icc_self hx₁_mem))

-- ===================================================================
-- Part C: EML tree functions are real-analytic on (0, ∞)
-- ===================================================================

open EMLTree in
/-- Helper: x ↦ t.eval (↑x : ℂ) is real-analytic (ℝ → ℂ) on (0, ∞).

Induction on t:
- const c: constant function → analyticOnNhd_const
- var:     ofRealCLM ∘ id, a CLM → ContinuousLinearMap.analyticOnNhd
- ceml t1 t2: exp part via ih1 + restrictScalars of analyticOnNhd_cexp (entire).
              log part cases on t2:
                const c → log(c) constant, analytic everywhere
                var     → log(↑x) analytic on (0,∞) since ↑x ∈ slitPlane for x > 0
                ceml    → 1 sorry: need to show t2.eval (↑x) ∈ slitPlane for x ∈ (0,∞) -/
private lemma eml_tree_eval_analyticOnNhd (t : EMLTree) :
    AnalyticOnNhd ℝ (fun x : ℝ => t.eval (↑x : ℂ)) (Set.Ioi 0) := by
  induction t with
  | const c =>
    simp only [EMLTree.eval]
    exact analyticOnNhd_const
  | var =>
    simp only [EMLTree.eval]
    have heq : (fun x : ℝ => (↑x : ℂ)) = Complex.ofRealCLM := by
      ext x; simp [Complex.ofRealCLM_apply]
    rw [heq]
    exact Complex.ofRealCLM.analyticOnNhd _
  | ceml t1 t2 ih1 ih2 =>
    simp only [EMLTree.eval]
    apply AnalyticOnNhd.sub
    · -- exp(t1.eval ↑x): Complex.exp is ℂ-analytic (entire) → ℝ-analytic via restrictScalars
      have hcexp : AnalyticOnNhd ℝ (Complex.exp : ℂ → ℂ) Set.univ :=
        analyticOnNhd_cexp.restrictScalars
      exact hcexp.comp ih1 (Set.mapsTo_univ _ _)
    · -- log(t2.eval ↑x): case split on t2 to resolve slit-plane membership
      -- Shared: Complex.log is ℝ-analytic on slitPlane (via restrictScalars of ℂ-analyticity)
      have hclog : AnalyticOnNhd ℝ (Complex.log : ℂ → ℂ) Complex.slitPlane :=
        fun z hz => (analyticAt_clog hz).restrictScalars
      cases t2 with
      | const c =>
        -- log(c) is constant (independent of x) → analytic trivially
        simp only [EMLTree.eval]
        exact analyticOnNhd_const
      | var =>
        -- log(↑x): for x ∈ (0,∞), (↑x : ℂ).re = x > 0, so ↑x ∈ slitPlane
        simp only [EMLTree.eval]
        have hmaps : Set.MapsTo (fun x : ℝ => (↑x : ℂ)) (Set.Ioi 0) Complex.slitPlane :=
          fun x hx => Complex.ofReal_mem_slitPlane.mpr (Set.mem_Ioi.mp hx)
        have hofr : AnalyticOnNhd ℝ (fun x : ℝ => (↑x : ℂ)) (Set.Ioi 0) := by
          have heq : (fun x : ℝ => (↑x : ℂ)) = Complex.ofRealCLM := by
            ext x; simp [Complex.ofRealCLM_apply]
          rw [heq]; exact Complex.ofRealCLM.analyticOnNhd _
        exact hclog.comp hofr hmaps
      | ceml t1' t2' _ih1' _ih2' =>
        -- For nested ceml trees, we need t2'.eval ↑x in slitPlane — genuine gap
        -- The function t2 = ceml t1' t2' produces complex values that may not
        -- land in the slit plane for all x > 0. A full proof requires tracking
        -- that every subtree's log argument avoids ℝ≤0 ∪ {0}, which is not
        -- derivable from the induction hypothesis alone without extra structure.
        have hmaps : Set.MapsTo (fun x : ℝ => (EMLTree.ceml t1' t2').eval (↑x : ℂ))
            (Set.Ioi 0) Complex.slitPlane := by
          sorry
        exact hclog.comp ih2 hmaps

open EMLTree in
/-- Every real EML tree function is real-analytic on (0, ∞).

Derived from `eml_tree_eval_analyticOnNhd` (ℝ→ℂ analyticity of t.eval ∘ (↑·))
by composing with Complex.reCLM (continuous ℝ-linear map ℂ →L[ℝ] ℝ).

Note: 1 sorry remains in the ceml/ceml log sub-case of the helper lemma. -/
lemma eml_tree_analytic (t : EMLTree) :
    AnalyticOnNhd ℝ t.evalReal (Set.Ioi 0) := by
  have hcomplex := eml_tree_eval_analyticOnNhd t
  have heq : t.evalReal = Complex.reCLM ∘ (fun x : ℝ => t.eval (↑x : ℂ)) := by
    ext x; simp [EMLTree.evalReal, Complex.reCLM]
  rw [heq]
  exact (Complex.reCLM.analyticOnNhd Set.univ).comp hcomplex (Set.mapsTo_univ _ _)

-- ===================================================================
-- Part C': Depth ≤ 1 EML trees are analytic — sorry-free (0 sorry)
-- ===================================================================

/-- Real.log is real-analytic on (0, ∞).

Proof: Real.log x = (Complex.log ↑x).re on all of ℝ (by Complex.log_ofReal_re).
Complex.log is ℂ-analytic on slitPlane; for x > 0, ↑x ∈ slitPlane.
Composing: reCLM ∘ Complex.log ∘ ofRealCLM is analytic on (0,∞), and equals Real.log. -/
private lemma real_log_analyticOnNhd_pos : AnalyticOnNhd ℝ Real.log (Set.Ioi 0) := by
  have hclog : AnalyticOnNhd ℝ (Complex.log : ℂ → ℂ) Complex.slitPlane :=
    fun z hz => (analyticAt_clog hz).restrictScalars
  have hofr : AnalyticOnNhd ℝ (fun x : ℝ => (↑x : ℂ)) (Set.Ioi 0) := by
    have heq : (fun x : ℝ => (↑x : ℂ)) = Complex.ofRealCLM := by
      ext x; simp [Complex.ofRealCLM_apply]
    rw [heq]; exact Complex.ofRealCLM.analyticOnNhd _
  have hmaps : Set.MapsTo (fun x : ℝ => (↑x : ℂ)) (Set.Ioi 0) Complex.slitPlane :=
    fun x hx => Complex.ofReal_mem_slitPlane.mpr (Set.mem_Ioi.mp hx)
  have hcomp : AnalyticOnNhd ℝ (fun x : ℝ => Complex.log (↑x : ℂ)) (Set.Ioi 0) :=
    hclog.comp hofr hmaps
  have hre : AnalyticOnNhd ℝ (fun x : ℝ => (Complex.log (↑x : ℂ)).re) (Set.Ioi 0) :=
    (Complex.reCLM.analyticOnNhd Set.univ).comp hcomp (Set.mapsTo_univ _ _)
  have heq : (fun x : ℝ => (Complex.log (↑x : ℂ)).re) = Real.log := by
    ext x; exact Complex.log_ofReal_re x
  rwa [heq] at hre

/-- Every real EML tree of depth ≤ 1 is real-analytic on (0, ∞). (0 sorry)

Proof by explicit case analysis. For depth ≤ 1, t2 in any ceml node has depth 0
(const or var only), so the ceml/ceml sorry in `eml_tree_analytic` is never reached. -/
private lemma eml_tree_analytic_depth_le_1 (t : EMLTree) (ht : t.depth ≤ 1) :
    AnalyticOnNhd ℝ t.evalReal (Set.Ioi 0) := by
  have hlog := real_log_analyticOnNhd_pos
  have hrexp : AnalyticOnNhd ℝ Real.exp (Set.Ioi 0) := fun x _ => Real.analyticAt_exp
  cases t with
  | const c =>
    simp only [EMLTree.evalReal, EMLTree.eval]
    exact analyticOnNhd_const
  | var =>
    simp only [EMLTree.evalReal, EMLTree.eval, Complex.ofReal_re]
    exact analyticOnNhd_id.mono (Set.subset_univ _)
  | ceml t1 t2 =>
    -- Both t1 and t2 must have depth 0 (const or var)
    have ht1 : t1.depth = 0 := by simp only [EMLTree.depth] at ht; omega
    have ht2 : t2.depth = 0 := by simp only [EMLTree.depth] at ht; omega
    cases t2 with
    | ceml t1' t2' =>
      simp only [EMLTree.depth] at ht2
    | const c2 =>
      cases t1 with
      | ceml t1' t2' =>
        simp only [EMLTree.depth] at ht1
      | const c1 =>
        -- evalReal x = (exp c1).re - (log c2).re  (constant)
        have heq : (EMLTree.ceml (EMLTree.const c1) (EMLTree.const c2)).evalReal =
                   fun _ : ℝ => (Complex.exp c1).re - (Complex.log c2).re := by
          ext x; simp [EMLTree.evalReal, EMLTree.eval, Complex.sub_re]
        rw [heq]; exact analyticOnNhd_const
      | var =>
        -- evalReal x = exp x - (log c2).re
        have heq : (EMLTree.ceml EMLTree.var (EMLTree.const c2)).evalReal =
                   fun x : ℝ => Real.exp x - (Complex.log c2).re := by
          ext x; simp [EMLTree.evalReal, EMLTree.eval, Complex.sub_re, Complex.exp_ofReal_re]
        rw [heq]; exact hrexp.sub analyticOnNhd_const
    | var =>
      cases t1 with
      | ceml t1' t2' =>
        simp only [EMLTree.depth] at ht1
      | const c1 =>
        -- evalReal x = (exp c1).re - log x
        have heq : (EMLTree.ceml (EMLTree.const c1) EMLTree.var).evalReal =
                   fun x : ℝ => (Complex.exp c1).re - Real.log x := by
          ext x; simp [EMLTree.evalReal, EMLTree.eval, Complex.sub_re, Complex.log_ofReal_re]
        rw [heq]; exact analyticOnNhd_const.sub hlog
      | var =>
        -- evalReal x = exp x - log x
        have heq : (EMLTree.ceml EMLTree.var EMLTree.var).evalReal =
                   fun x : ℝ => Real.exp x - Real.log x := by
          ext x; simp [EMLTree.evalReal, EMLTree.eval, Complex.sub_re,
                       Complex.exp_ofReal_re, Complex.log_ofReal_re]
        rw [heq]; exact hrexp.sub hlog

-- ===================================================================
-- Part C'': Depth-1 finite zeros (0 sorry — depends on C')
-- ===================================================================

/-- CEML-T91: A non-zero real depth-≤-1 EML tree has finitely many zeros
in any bounded positive interval. (0 sorry)

Uses eml_tree_analytic_depth_le_1 + analytic_finite_zeros_compact. -/
lemma depth1_finite_zeros_real (t : EMLTree) (ht : t.depth ≤ 1) (a b : ℝ) (hab : a < b)
    (hpos : a > 0)
    (hne : ∃ x ∈ Set.Ioo a b, t.evalReal x ≠ 0) :
    Set.Finite {x ∈ Set.Icc a b | t.evalReal x = 0} := by
  have hIcc_pos : Set.Icc a b ⊆ Set.Ioi 0 :=
    fun x hx => lt_of_lt_of_le hpos hx.1
  have hanal : AnalyticOnNhd ℝ t.evalReal (Set.Icc a b) :=
    (eml_tree_analytic_depth_le_1 t ht).mono hIcc_pos
  exact analytic_finite_zeros_compact t.evalReal a b hab hanal hne

-- ===================================================================
-- Part D: sin ∉ EML_k (1 sorry — genuine mathematical challenge)
-- ===================================================================

open EMLTree in
/-- T01 (Infinite Zeros Barrier): sin is not representable by any finite EML tree.

Sorry: quantitative zero-count bound needed — EML-k trees have ≤ B(k) zeros on ℝ.
This requires o-minimal structure theory (ℝ_exp is o-minimal). -/
theorem sin_not_in_eml (k : ℕ) :
    ∀ t : EMLTree, t.depth ≤ k →
      ¬ (∀ x : ℝ, t.evalReal x = Real.sin x) := by
  sorry

-- ===================================================================
-- CEML-T48: sin(x) ∉ EML-k(ℝ) for any finite k (1 sorry)
-- ===================================================================

/-- CEML-T48: sin(x) ∉ EML-k(ℝ) for any finite k.
    Moved from EMLDepth.lean (avoids circular import).
    Sorry: finite zeros induction (needs o-minimal structure theory). -/
theorem sin_not_in_real_EML_k (k : ℕ) :
    (fun x : ℂ => ↑(Real.sin x.re) : ℂ → ℂ) ∉ EML_k k := by
  sorry  -- Full proof strategy:
         -- 1. Every depth-k real ceml tree has finitely many zeros in any bounded interval
         --    (depth1_finite_zeros_real + induction)
         -- 2. sin(nπ) = 0 for all n ∈ ℤ — infinitely many zeros
         -- 3. Contradiction

-- ===================================================================
-- Verified: sin(x) has zeros at all integer multiples of π
-- ===================================================================

example : Real.sin 0 = 0 := Real.sin_zero
example : Real.sin Real.pi = 0 := Real.sin_pi
example : Real.sin (2 * Real.pi) = 0 := by
  rw [show (2 : ℝ) * Real.pi = Real.pi + Real.pi from by ring]
  rw [Real.sin_add, Real.sin_pi, Real.cos_pi]; ring
example : Real.sin (3 * Real.pi) = 0 := by
  have := sin_int_pi_zero 3; push_cast at this; exact this
