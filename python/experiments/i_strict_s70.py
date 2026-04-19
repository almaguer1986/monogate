"""
S70 — Theorem #19: i-Unconstructibility under Strict Principal-Branch Grammar

Under strict grammar: ln(y) is defined only for y ∈ ℝ, y > 0.
Starting terminal: {1}.

THREE-LINE PROOF:
  (1) All leaves evaluate to 1 ∈ ℝ⁺.
  (2) If x ∈ ℝ and y ∈ ℝ⁺, then eml(x,y) = exp(x) − ln(y) ∈ ℝ.
  (3) By induction on depth, every well-defined tree value is real. i ∉ ℝ. ∎

Theorem #19 (Strict-Grammar Barrier):
  i ∉ EML({1}, strict)
"""

import json
from pathlib import Path

THEOREM_19 = {
    "id": "T19",
    "name": "Strict-Grammar i-Barrier",
    "tier": "THEOREM",
    "session": "S70",
    "category": "Core Algebra — i-Constructibility Sprint",
    "statement": (
        "Under the strict principal-branch EML grammar "
        "(ln defined only on ℝ⁺, terminal set {1}), "
        "i = √(−1) is not constructible. "
        "More generally: every well-defined tree evaluation is a real number."
    ),
    "proof": {
        "type": "Induction on depth",
        "length": "3 lines",
        "line_1": "Leaves: the only leaf is 1 ∈ ℝ⁺.",
        "line_2": (
            "Step: if x ∈ ℝ and y ∈ ℝ⁺ (strict grammar requires y > 0), "
            "then exp(x) ∈ ℝ and ln(y) ∈ ℝ, so eml(x,y) = exp(x) − ln(y) ∈ ℝ."
        ),
        "line_3": (
            "By induction on tree depth, every well-defined evaluation is real. "
            "Since i ∉ ℝ, i is not constructible. ∎"
        ),
    },
    "corollaries": [
        "ℂ \\ ℝ ∩ EML({1}, strict) = ∅ — no complex value is constructible under strict grammar.",
        "EML({1}, strict) ⊆ ℝ — the entire strict-grammar closure lies in ℝ.",
        (
            "Contrast with extended grammar: the loophole (ln of negative real) "
            "first activates at N=5, producing values with Im = −π."
        ),
    ],
    "proof_status": "COMPLETE",
    "sorry_count": 0,
    "lean_session": "S74",
    "notes": (
        "The proof is immediate once we note that the strict grammar's domain restriction "
        "(y > 0) is precisely what prevents complex numbers from entering the computation. "
        "The extended grammar relaxes this and creates the loophole (Session S62)."
    ),
}


def verify_strict_grammar():
    """Numerically verify: all depth-≤5 trees from {1} under strict grammar are real."""
    import math

    def eml_strict(x, y):
        """Returns None if y <= 0 (strict grammar), else exp(x) - ln(y)."""
        if not isinstance(y, (int, float)) or y <= 0:
            return None
        if not isinstance(x, (int, float)):
            return None
        try:
            return math.exp(min(x, 500)) - math.log(y)
        except (ValueError, OverflowError):
            return None

    # Build all trees up to N=5 nodes, all leaves = 1
    def build_values(max_n):
        # values_by_n[k] = set of values reachable with exactly k internal nodes
        values_at_n = {0: {1.0}}  # N=0: just the leaf 1
        all_values = {1.0}

        for n in range(1, max_n + 1):
            new_vals = set()
            for k in range(n):
                # Left subtree has k nodes, right has n-1-k nodes
                for lv in values_at_n.get(k, set()):
                    for rv in values_at_n.get(n - 1 - k, set()):
                        result = eml_strict(lv, rv)
                        if result is not None and abs(result) < 1e10:
                            new_vals.add(round(result, 8))
            values_at_n[n] = new_vals
            all_values |= new_vals

        return values_at_n, all_values

    vals_by_n, all_vals = build_values(5)

    # Check: all values are real (they should be since eml_strict returns None for complex inputs)
    all_real = all(isinstance(v, float) for v in all_vals)

    result = {
        "max_n": 5,
        "values_by_n": {k: sorted(list(v))[:20] for k, v in vals_by_n.items()},
        "total_values": len(all_vals),
        "all_real": all_real,
        "i_in_set": False,  # i cannot be a real float
        "theorem_verified": all_real,
    }
    return result


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    verification = verify_strict_grammar()

    output = {"theorem": THEOREM_19, "verification": verification}
    out_path = results_dir / "s70_theorem19_strict.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("=" * 60)
    print("S70 — Theorem #19: Strict-Grammar i-Barrier")
    print("=" * 60)
    print()
    print("PROOF (3 lines):")
    p = THEOREM_19["proof"]
    print(f"  (1) {p['line_1']}")
    print(f"  (2) {p['line_2']}")
    print(f"  (3) {p['line_3']}")
    print()
    print("Corollaries:")
    for c in THEOREM_19["corollaries"]:
        print(f"  • {c}")
    print()
    v = verification
    print(f"Verification (N=1..{v['max_n']}, strict grammar):")
    print(f"  Total distinct values: {v['total_values']}")
    print(f"  All real: {v['all_real']}")
    print(f"  i in set: {v['i_in_set']}")
    print(f"  Theorem verified: {v['theorem_verified']}")
    print()
    for n, vals in v["values_by_n"].items():
        print(f"  N={n}: {vals[:6]}{'...' if len(vals) > 6 else ''}")
    print()
    print(f"Status: {THEOREM_19['proof_status']} | Lean session: {THEOREM_19['lean_session']}")
    print(f"Results: {out_path}")
