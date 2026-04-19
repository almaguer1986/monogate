"""
S67 — Lean Proof: expTree_evalReal + depth_k_unbounded_along_real (HasVar)

Deliverables written to D:/monogate-research/lean/EML/EMLDepth.lean:
  - expTree_evalReal lemma (proved, no sorry)
  - var_evalReal lemma (proved, no sorry)
  - const_evalReal lemma (proved, no sorry)
  - EMLTree.HasVar predicate (defined)
  - no_var_evalReal_const lemma (1 sorry for x-independence subgoal)
  - depth_k_unbounded_along_real reformulated with HasVar (base case proved,
    inductive step 1 sorry — requires Im-part bound, scheduled S97)

Key mathematical content:
  The original depth_k_unbounded_along_real was FALSE as stated:
  counterexample: ceml(const 0, const(-1)).evalReal = Re(1 - iπ) = 1 = constant.
  Fix: add HasVar predicate. Trees with no variable leaf produce constant evalReal.
"""

import json
from pathlib import Path

S67_RESULTS = {
    "session": "S67",
    "title": "Lean: expTree_evalReal + depth_k_unbounded reformulation",
    "lean_file": "D:/monogate-research/lean/EML/EMLDepth.lean",
    "new_lemmas": [
        {
            "name": "expTree_evalReal",
            "statement": "∀ x : ℝ, expTree.evalReal x = Real.exp x",
            "status": "PROVED",
            "sorry_count": 0,
            "proof_method": "simp [expTree, EMLTree.evalReal, EMLTree.eval, Complex.log_one, Complex.exp_ofReal_re]",
        },
        {
            "name": "var_evalReal",
            "statement": "∀ x : ℝ, EMLTree.var.evalReal x = x",
            "status": "PROVED",
            "sorry_count": 0,
            "proof_method": "simp [EMLTree.evalReal, EMLTree.eval]",
        },
        {
            "name": "const_evalReal",
            "statement": "∀ (c : ℂ) (x : ℝ), (const c).evalReal x = c.re",
            "status": "PROVED",
            "sorry_count": 0,
            "proof_method": "simp [EMLTree.evalReal, EMLTree.eval]",
        },
        {
            "name": "EMLTree.HasVar",
            "statement": "Predicate: tree contains at least one .var leaf",
            "status": "DEFINED",
            "sorry_count": 0,
        },
        {
            "name": "no_var_evalReal_const",
            "statement": "¬HasVar t → ∃ c, ∀ x, t.evalReal x = c",
            "status": "PARTIAL",
            "sorry_count": 1,
            "sorry_note": "ceml inductive case: x-independence of eval for no-var trees",
        },
        {
            "name": "depth_k_unbounded_along_real",
            "statement": "HasVar t → 1 ≤ depth → Tendsto evalReal atTop atTop ∨ atBot",
            "status": "PARTIAL",
            "sorry_count": 1,
            "sorry_note": "General inductive step. Base case (expTree) proved. Im-part bound needed for ceml case.",
            "counterexample_to_original": "ceml(const 0, const(-1)).evalReal = 1 (constant) but depth=1",
        },
    ],
    "sorry_count_change": {"before": 2, "after": 2, "note": "Same count but CORRECTLY STATED now; original lemma was false"},
    "key_insight": (
        "depth_k_unbounded_along_real required HasVar predicate. "
        "Without it, ceml(const 0, const(-1)) is a depth-1 counterexample with constant evalReal=1. "
        "This is mathematically important: the barrier against sin is really about trees "
        "that FUNCTIONALLY depend on x, not just have high depth."
    ),
}


def run_counterexample_check():
    """Verify the ceml(const 0, const(-1)) counterexample computationally."""
    import cmath
    import math

    results = []
    for x in [0.0, 1.0, 2.0, 5.0, 10.0, 100.0]:
        # ceml(const 0, const(-1)).evalReal x = Re(exp(0) - log(-1))
        val = cmath.exp(0) - cmath.log(-1)
        evalReal = val.real
        results.append({
            "x": x,
            "evalReal": evalReal,
            "expected_constant": 1.0,
            "is_constant": abs(evalReal - 1.0) < 1e-10,
        })

    # Verify expTree.evalReal = Real.exp
    exp_check = []
    for x in [0.0, 0.5, 1.0, 2.0]:
        # expTree = ceml(var, const 1): Re(exp(x) - log(1)) = exp(x)
        val = cmath.exp(complex(x, 0)) - cmath.log(1)
        evalReal = val.real
        expected = math.exp(x)
        exp_check.append({
            "x": x,
            "evalReal": evalReal,
            "expected": expected,
            "match": abs(evalReal - expected) < 1e-10,
        })

    return {"counterexample": results, "expTree_check": exp_check}


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    checks = run_counterexample_check()
    S67_RESULTS["computational_checks"] = checks

    out_path = results_dir / "s67_lean_proof.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(S67_RESULTS, f, indent=2)

    print("=" * 60)
    print("S67 — Lean: expTree_evalReal + depth_k_unbounded (HasVar)")
    print("=" * 60)
    print()
    print("New lemmas:")
    for lemma in S67_RESULTS["new_lemmas"]:
        status = lemma["status"]
        sorry = lemma["sorry_count"]
        print(f"  [{status}] {lemma['name']}  (sorry: {sorry})")

    print()
    print("KEY INSIGHT:")
    print("  Original depth_k_unbounded_along_real was FALSE.")
    print("  ceml(const 0, const(-1)) has depth=1 but evalReal=1 (constant).")
    print("  Fix: add HasVar predicate — only trees with variable leaves can be unbounded.")
    print()
    print("Computational verification:")
    ce = checks["counterexample"]
    print(f"  ceml(const 0, const(-1)).evalReal: {ce[0]['evalReal']:.6f} (x=0), "
          f"{ce[-1]['evalReal']:.6f} (x=100) — constant confirmed")
    et = checks["expTree_check"]
    print(f"  expTree.evalReal(1.0) = {et[2]['evalReal']:.6f}, exp(1) = {et[2]['expected']:.6f} — match: {et[2]['match']}")
    print()
    print(f"Results: {out_path}")
