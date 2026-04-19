"""
S63 — i-Constructibility: Catalog Entry

STATUS after S61/S62:
- i not found in exhaustive search through N=9 (1429 trees).
- The iπ-first-generation argument is valid: the FIRST complex value from
  a {1}-seeded tree has Im = -π (from ln of a negative real).
- The full iπ-closure induction FAILS: subsequent compositions of that
  complex value produce Im parts that are NOT integer multiples of π.
  (Census shows Im/π values like -0.48, -0.93, -1.59, etc.)
- Therefore, an algebraic proof remains OPEN. We cannot yet prove or disprove.

CATALOG ENTRY: T_i — i-Constructibility (Strict Grammar)
  Tier: CONJECTURE
  Statement: i = sqrt(-1) is not constructible from terminal {1} under
             strict principal-branch EML grammar.
  Evidence: exhaustive search N=1..9 (1429 trees), all leaves=1, no witness.
  Gap: no complete algebraic proof. iπ-closure holds only at first generation.
  Status: OPEN on challenge board.
"""

import json
from pathlib import Path


CATALOG_ENTRY = {
    "id": "T_i_strict",
    "name": "i-Constructibility (Strict Grammar)",
    "tier": "CONJECTURE",
    "session": "S61-S63",
    "category": "Core Algebra",
    "statement": (
        "i = sqrt(-1) is NOT constructible as a finite EML tree from terminal {1} "
        "under strict principal-branch grammar (ln(0) undefined, ln of negative reals "
        "returns complex via principal branch)."
    ),
    "evidence": (
        "Exhaustive enumeration of all full binary EML trees with N=1..9 internal nodes "
        "(1429 trees total), all leaves assigned value 1. No tree evaluates to i. "
        "The loophole (negative y-argument entering ln) first activates at N=5, "
        "producing complex values with Im = -π. Subsequent compositions produce "
        "Im parts that are NOT integer multiples of π (Im/π census: irrational values "
        "like -0.48, -0.93, -1.59 appear). Despite the complex values, Im = 1 never appears."
    ),
    "proof_status": "INCOMPLETE",
    "proof_gap": (
        "Attempted iπ-closure induction: first complex generation has Im = -π (valid). "
        "But exp(a + ib) for general b breaks the integer-π invariant. "
        "A complete proof requires either: (a) a different algebraic invariant, "
        "(b) extending the search to N=11+ with the Rust kernel, "
        "or (c) a transcendence argument about which Im values are reachable."
    ),
    "verify": (
        "python python/experiments/i_constructibility.py  # N=1..7\n"
        "python python/experiments/i_constructibility_s62.py  # N=1..9 census"
    ),
    "challenge_board_status": "OPEN",
    "search_summary": {
        "max_n_searched": 9,
        "total_trees": 1429,
        "complex_outputs": 737,
        "found_i": False,
        "loophole_first_n": 5,
        "note": "N=12 Rust search running in background (started S61)"
    },
    "next_steps": [
        "S66-S69: Lean proof attempt (private repo)",
        "Extend Python search to N=11 using Rust kernel",
        "Explore transcendence argument: what algebraic structure do reachable Im values have?",
    ]
}


def write_theorem_doc():
    doc = f"""# T_i: i-Constructibility (Strict Grammar)

**Tier:** CONJECTURE
**Session:** S61–S63
**Category:** Core Algebra
**Challenge board:** OPEN

## Statement

i = √(−1) is conjectured to be NOT constructible as a finite EML tree from
terminal {{1}} under strict principal-branch grammar.

## Evidence

Exhaustive enumeration of all full binary EML trees with N = 1..9 internal
nodes (1,429 trees total), with all leaves = 1. No tree evaluates to i.

### Loophole analysis (S62)

The naive argument — "all nodes stay real, therefore i unreachable" — has a gap.
When a tree produces a negative real value and routes it to the y-slot of an eml
node, the principal-branch ln introduces a complex value:

    eml(x, y) for y < 0: = exp(x) − (ln|y| + iπ) = (exp(x) − ln|y|) − iπ

This **first-generation loophole** activates at N = 5. The first complex value
produced is ≈ 0.198 − 3.14159i (Im = −π).

However, subsequent compositions of this complex value produce Im parts that
are NOT integer multiples of π. The Im/π census (N ≤ 9) shows irrational values
like −0.48, −0.93, −1.59, confirming the iπ-closure induction fails.

Despite this, Im = 1 (i.e., the imaginary unit i) never appears through N = 9.

## Proof Gap

A complete proof requires showing that Im = 1 is unreachable under arbitrary
depth composition. The first-generation argument is valid; the general inductive
step is not. Possible approaches:

1. **Transcendence/algebraic independence**: the reachable Im values form a
   specific subset of ℝ that provably excludes 1.
2. **Lean 4 formalization** (private repo, S66–S69).
3. **Exhaustive extension**: Rust N = 12 search running (started S61).

## Computational Verification

```
python python/experiments/i_constructibility.py      # N=1..7
python python/experiments/i_constructibility_s62.py  # N=1..9 + census
```

## Dependencies

- Real-analytic function theory
- Principal-branch logarithm definition
- Lindemann–Weierstrass (π transcendental) — for first-generation argument only
"""
    return doc


if __name__ == '__main__':
    # Write catalog entry JSON
    results_dir = Path(__file__).parent.parent / 'results'
    results_dir.mkdir(exist_ok=True)

    catalog_path = results_dir / 's63_i_constructibility_catalog.json'
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(CATALOG_ENTRY, f, indent=2)
    print(f"Catalog entry written: {catalog_path}")

    # Write theorem doc
    docs_dir = Path(__file__).parent.parent.parent / 'docs' / 'theorems'
    docs_dir.mkdir(parents=True, exist_ok=True)
    doc_path = docs_dir / 'i_constructibility.md'
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(write_theorem_doc())
    print(f"Theorem doc written: {doc_path}")

    # Print summary
    print()
    print("=" * 60)
    print("S61-S63 SUMMARY: i-Constructibility")
    print("=" * 60)
    print(f"Tier:    {CATALOG_ENTRY['tier']}")
    print(f"Status:  {CATALOG_ENTRY['challenge_board_status']}")
    print(f"Search:  N=1..9, {CATALOG_ENTRY['search_summary']['total_trees']} trees")
    print(f"Found i: {CATALOG_ENTRY['search_summary']['found_i']}")
    print()
    print("Proof gap identified: ipi-closure holds at first generation only.")
    print("Lean path (S66-S69, private) is the primary route to a complete proof.")
    print("N=12 Rust search running in background.")
