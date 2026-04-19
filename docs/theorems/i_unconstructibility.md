# i-Constructibility: Complete Record

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
