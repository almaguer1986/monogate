"""
S76 — Catalog Writeup: T19 + T_i

Writes two catalog entries:
  1. T19: Strict-Grammar i-Barrier (THEOREM, proved)
  2. T_i: Extended-Grammar i-Conjecture (CONJECTURE, open — strengthened evidence)
And updates docs/theorems/i_unconstructibility.md
"""

import json
from pathlib import Path

T19_ENTRY = {
    "id": "T19",
    "name": "Strict-Grammar i-Barrier",
    "tier": "THEOREM",
    "session": "S70",
    "lean_session": "S74",
    "category": "Core Algebra",
    "statement": (
        "Under the strict principal-branch EML grammar "
        "(eml(x,y) defined only when y > 0, terminal {1}), "
        "every well-defined tree evaluation is a real number. "
        "In particular, i = √(−1) is not constructible."
    ),
    "proof": {
        "length": "3 lines",
        "type": "Induction on depth",
        "line_1": "Leaves evaluate to 1 ∈ ℝ⁺.",
        "line_2": "x ∈ ℝ, y > 0 ⟹ eml(x,y) = exp(x) − ln(y) ∈ ℝ.",
        "line_3": "Induction on depth: all values real. i ∉ ℝ. ∎",
    },
    "proof_status": "COMPLETE",
    "lean_status": "PROVED (0 sorries) — StrictBarrier.lean",
    "sorry_count": 0,
    "corollaries": [
        "EML({1}, strict) ⊆ ℝ.",
        "No complex value is constructible under strict grammar.",
        "Contrast: extended grammar's loophole activates at N=5 (Im = −π).",
    ],
    "challenge_board": "CLOSED (proved)",
}

T_I_ENTRY = {
    "id": "T_i",
    "name": "Extended-Grammar i-Conjecture",
    "tier": "CONJECTURE",
    "session": "S61-S76",
    "lean_session": "S75 (framework only)",
    "category": "Core Algebra",
    "statement": (
        "i = √(−1) is NOT constructible from terminal {1} "
        "under extended principal-branch EML grammar "
        "(eml(x,y) = exp(x) − Log(y) via principal branch, all ℂ∗ inputs allowed)."
    ),
    "evidence": {
        "computational": "N=1..9 exhaustive search: 1429 trees, no i found.",
        "structural": (
            "Propagation rule: Im(eml(x,y)) = exp(Re x)·sin(Im x) − arg(y). "
            "For Im = 1 via Log route: need arg(y) = -1, i.e. Im(y)/Re(y) = -tan(1). "
            "tan(1) ≈ 1.5574 is transcendental; no constructible y known to satisfy this."
        ),
        "loophole": "First complex at N=5: Im = −π. Subsequent Im values: arctan-type, never 1.",
        "euler": "exp(iπ) = -1 and Log(-1) = iπ form a closed loop that never exits to Im = 1.",
    },
    "proof_gap": (
        "Complete proof requires: "
        "(a) Show Im = 1 is not achievable via the exp route: "
        "    exp(Re x)·sin(Im x) = 1 for no constructible x. "
        "(b) Show Im = 1 is not achievable via the Log route: "
        "    arg(y) = -1 for no constructible y — requires tan(1) ∉ EML-reachable. "
        "Both require transcendence theory (Nesterenko, Gelfond-Schneider type arguments)."
    ),
    "proof_status": "INCOMPLETE",
    "lean_status": "FRAMEWORK (ExtendedClosure.lean, 3 sorries)",
    "challenge_board": "OPEN",
    "next_steps": [
        "Transcendence argument: show tan(1) not in EML-closure of real parts.",
        "Extend Lean to full conjecture (post S97 after Im-part bounds).",
        "Extend search to N=12 (Rust kernel).",
    ],
}

CATALOG_DOC = """# i-Constructibility: Complete Record

## T19 — Strict-Grammar i-Barrier

**Tier:** THEOREM (proved)
**Session:** S70 | **Lean:** S74 (0 sorries)
**Challenge board:** CLOSED

### Statement

Under strict principal-branch EML grammar (ln defined only on ℝ⁺, terminal {1}),
every well-defined tree evaluation is a real number. In particular:

> **i = √(−1) is not constructible under strict grammar.**

### Proof (3 lines)

1. Leaves evaluate to 1 ∈ ℝ⁺.
2. If x ∈ ℝ and y ∈ ℝ⁺, then eml(x,y) = exp(x) − ln(y) ∈ ℝ.
3. By induction on depth, all well-defined evaluations are real. Since i ∉ ℝ, i is not constructible. ∎

### Lean Proof

File: `lean/EML/StrictBarrier.lean`

Key insight: the strict grammar's domain restriction types `StrictTree.eval` as
`StrictTree → Option ℝ`. The theorem is type-level: values are ℝ by construction.

---

## T_i — Extended-Grammar i-Conjecture

**Tier:** CONJECTURE (open)
**Session:** S61–S76 | **Lean:** S75 (framework, 3 sorries)
**Challenge board:** OPEN

### Statement

> **i = √(−1) is conjectured to be not constructible from {1} under extended principal-branch EML grammar.**

### Evidence

- **Exhaustive search:** N=1..9 (1429 trees). No witness found.
- **Structural:** Im(eml(x,y)) = exp(Re x)·sin(Im x) − arg(y).
  For Im = 1 via Log: need arg(y) = −1, requiring tan(1) ∈ ratio of constructible parts.
- **Loophole analysis:** First complex at N=5 with Im = −π. The iπ-loop
  (exp(iπ) = −1 ↔ Log(−1) = iπ) cycles back to Im = −π without ever reaching Im = 1.
- **Im census (N≤9):** Values seen: −π, −π/2, arctan-type irrationals. Never 1.

### Proof Gap

Complete proof requires transcendence: show tan(1) is not in the set
{Im(z)/Re(z) : z ∈ EML({1}, extended)}.

### Grammar Comparison

| Grammar | ln domain | i constructible? | Proof |
|---------|-----------|-----------------|-------|
| Strict | ℝ⁺ only | **NO** (T19) | 3-line induction |
| Extended | ℂ∗ (principal branch) | **Conjectured NO** | Open |
| Complex | ℂ∗ (complex leaves) | YES: eml(iπ, 1) = exp(iπ) = −1, then... | EML-1 if leaves allowed |

---

## History

- **S61:** Initial setup, N=1..7 search, loophole identified.
- **S62:** N=1..9 census, iπ-closure fails (Im/π is irrational in general).
- **S63:** Catalog entry (CONJECTURE tier).
- **S64-S65:** Infinite Zeros Barrier (separate theorem, N=12 confirmed).
- **S66-S69:** Lean battlefield (strict theorem outlined, framework built).
- **S70:** T19 proved (3-line proof).
- **S71:** Extended closure computed (N=1..7).
- **S72:** iπ algebra traced (exp(iπ)=−1, Log(iπ)=ln(π)+iπ/2).
- **S73:** Formal closure proof attempt (tan(1) obstruction identified).
- **S74:** Lean proof of T19 (complete, 0 sorries).
- **S75:** Lean framework for extended conjecture (3 sorries).
- **S76:** This writeup.
"""


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    docs_dir = Path("D:/monogate/docs/theorems")
    results_dir.mkdir(exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Write catalog JSONs
    t19_path = results_dir / "s76_T19_catalog.json"
    with open(t19_path, "w", encoding="utf-8") as f:
        json.dump(T19_ENTRY, f, indent=2)

    ti_path = results_dir / "s76_Ti_catalog.json"
    with open(ti_path, "w", encoding="utf-8") as f:
        json.dump(T_I_ENTRY, f, indent=2)

    # Write catalog doc
    doc_path = docs_dir / "i_unconstructibility.md"
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(CATALOG_DOC)

    print("=" * 60)
    print("S76 — Catalog Writeup: T19 + T_i")
    print("=" * 60)
    print()
    print(f"T19: {T19_ENTRY['tier']} | {T19_ENTRY['challenge_board']} | sorry: {T19_ENTRY['sorry_count']}")
    print(f"T_i: {T_I_ENTRY['tier']} | {T_I_ENTRY['challenge_board']}")
    print()
    print(f"Catalog JSON: {t19_path}")
    print(f"Catalog JSON: {ti_path}")
    print(f"Theorem doc:  {doc_path}")
