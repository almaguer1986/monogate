## Chapter: i-Constructibility (S61-S89)

### Summary

The question: can i = √(−1) be constructed from the single terminal value 1
under the EML operator eml(x,y) = exp(x) − Log(y)?

### Results

**T19 — Strict-Grammar i-Barrier** (THEOREM, S70, Lean S74)

Under strict principal-branch grammar (ln: ℝ⁺ → ℝ only), all EML values are real.
Proof: 3-line induction. Lean verified, 0 sorries.

**T_i — Extended-Grammar i-Conjecture** (CONJECTURE, S61-S89)

Under extended principal-branch grammar (Log: ℂ∗ → ℂ), i appears to be unconstructible.

Evidence:
- 50,907 values computed at depth ≤ 5: no i found.
- PSLQ at 300 digits: no relation tan(1) ∈ {π, e, ln(2)}.
- The tan(1) obstruction: Im(z) = 1 requires some y ∈ EML₁ with arg(y) = −1.
- This reduces to: does EML₁ contain an element with Im/Re = −tan(1)?
- By the propagation rule, this is self-similar — reducing to the same question at each depth.

### The tan(1) Obstruction

The critical insight from S73-S86:

    Im(eml(x,y)) = exp(Re(x))·sin(Im(x)) − arg(y)

For Im(z) = 1 with x real: arg(y) = −1.
arg(y) = −1 requires Im(y)/Re(y) = −tan(1).
tan(1) ≈ 1.5574 is transcendental (Hermite-Lindemann).

This reduction is SELF-SIMILAR: proving tan(1) ∉ Im(EML₁)/Re(EML₁) reduces to itself.

### Proof Gap

No existing theorem directly proves the gap. What would close it:
- **Schanuel's conjecture** (unproved): would show e and e^i algebraically independent,
  implying tan(1) unreachable from the EML₁ tower.
- **Structural bound**: if Im(EML₁) ⊆ (−π, 0] could be proved, then Im = 1 > 0 is
  immediately impossible. But Im CAN become positive if we find y with arg(y) < 0.

### Status

| Claim | Status | Evidence |
|-------|--------|----------|
| T19: strict → i not constructible | THEOREM | Lean 0 sorries |
| T_i: extended → i not constructible | CONJECTURE | 50K values, PSLQ 300 dig |
| Claim C: tan(1) ∉ ratio set | CONJECTURE | Same as T_i |
| Im(EML₁) ⊆ (−π,0]: structural bound | OPEN | True at depth ≤ 5 |
| Proof via Schanuel | CONDITIONAL | Would close gap |

### Private Lean Sorry Census (after S89)

| File | Sorries |
|------|---------|
| StrictBarrier.lean | 0 |
| ExtendedClosure.lean | 5 |
| EMLDepth.lean | 2 |
| GrandSynthesis.lean | 2 |
| Millennium.lean | 6 |
| TropicalSemiring.lean | 1 |
| **Total** | **16** |
