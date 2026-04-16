# %% [markdown]
# # Neurosymbolic Theorem Prover — monogate Demo
#
# This notebook demonstrates `monogate.prover`, a neurosymbolic proof engine
# that combines three verification strategies:
#
# | Tier | Method | Confidence |
# |------|--------|-----------|
# | 1 | Numerical (500 probe points) | 0.90 |
# | 2 | Exact (SymPy `simplify`) | 1.00 |
# | 3 | Certified (interval arithmetic) | 0.95 |
# | 4 | EML witness (MCTS + SymPy) | 1.00 |
#
# **The "neurosymbolic" loop:**  MCTS discovers EML structure, SymPy verifies
# algebraically.  If MCTS finds a short EML tree T such that `T(x) ≈ f(x)`,
# and SymPy confirms `simplify(T_sympy - rhs) == 0`, the proof is exact.

# %% [markdown]
# ## Section A — What is a Neurosymbolic Proof?
#
# A **neurosymbolic proof** for `f(x) = g(x)` proceeds in layers:
#
# 1. **Statistical confidence** (numerical check): Can we find even one x
#    where the identity fails? If max|f(x)−g(x)| < 1e-8 over 500 random
#    points, we have strong evidence.
#
# 2. **Formal verification** (SymPy): `sympy.simplify(f_expr - g_expr) == 0`
#    is a computer-verified algebraic proof — no floating-point involved.
#
# 3. **Certified bounds** (interval arithmetic): Evaluate using interval
#    extensions; if the residual interval contains 0 everywhere, the identity
#    holds over the domain.
#
# 4. **EML witness** (MCTS): Find an EML tree T such that
#    `simplify(to_sympy(T) - g_expr) == 0`.  The tree T is a *proof witness*
#    — a constructive EML expression that certifies the LHS.

# %%
import math
from monogate.prover import EMLProver, ProofResult, BenchmarkReport
from monogate.identities import (
    ALL_IDENTITIES, TRIG_IDENTITIES, HYPERBOLIC_IDENTITIES,
    EXPONENTIAL_IDENTITIES, SPECIAL_IDENTITIES, PHYSICS_IDENTITIES,
    EML_IDENTITIES, OPEN_IDENTITIES,
    get_by_difficulty, get_by_category,
)

prover = EMLProver(verbose=True, n_probe=200)
print(f"EMLProver ready. n_probe={prover.n_probe}")

# %% [markdown]
# ## Section B — Prove Simple Identities (Exp / Log)
#
# Start with identities that SymPy can verify algebraically.

# %%
print("=" * 60)
print("B1. exp(x) * exp(-x) == 1")
r = prover.prove("exp(x) * exp(-x) == 1", domain=(-3.0, 3.0))
print(f"  Status:     {r.status}")
print(f"  Method:     {r.verification_method}")
print(f"  Confidence: {r.confidence:.2f}")
print(f"  Residual:   {r.max_residual:.2e}")
print(f"  Time:       {r.elapsed_s:.3f}s")
if r.sympy_simplification:
    print(f"  SymPy got:  {r.sympy_simplification}")
print()

# %%
print("=" * 60)
print("B2. log(exp(x)) == x")
r = prover.prove("log(exp(x)) == x", domain=(-3.0, 3.0))
print(f"  Status: {r.status}  |  residual: {r.max_residual:.2e}")
print(f"  Notes: {r.notes[:2]}")
print()

# %%
print("=" * 60)
print("B3. exp(log(x)) == x  (domain x > 0)")
r = prover.prove("exp(log(x)) == x", domain=(0.1, 5.0))
print(f"  Status: {r.status}  |  residual: {r.max_residual:.2e}")
print()

# %%
print("=" * 60)
print("B4. exp(2*x) == exp(x)**2")
r = prover.prove("exp(2*x) == exp(x)**2", domain=(-2.0, 2.0))
print(f"  Status: {r.status}  |  residual: {r.max_residual:.2e}")
print()

# %% [markdown]
# ## Section C — Trigonometric Identity Gallery
#
# Test all 15+ trigonometric identities with a one-liner loop.

# %%
print("=" * 60)
print("TRIGONOMETRIC IDENTITY GALLERY")
print("=" * 60)

trig_results = []
for ident in TRIG_IDENTITIES:
    r = prover.prove(ident.expression, domain=ident.domain, timeout=10.0)
    trig_results.append(r)
    symbol = "PASS" if r.proved() else "FAIL"
    print(f"  [{symbol}] {ident.name:<40} {r.status}")

n_pass = sum(1 for r in trig_results if r.proved())
print(f"\n  Passed: {n_pass}/{len(trig_results)}")

# %% [markdown]
# ### C1 — Pythagorean Identity (deep-dive)

# %%
r = prover.prove("sin(x)**2 + cos(x)**2 == 1", domain=(-math.pi, math.pi))
print(f"sin²(x) + cos²(x) = 1")
print(f"  Status:     {r.status}")
print(f"  Confidence: {r.confidence}")
print(f"  SymPy:      {r.sympy_simplification}")
if r.latex_proof:
    print("\nLaTeX proof:")
    print(r.latex_proof)

# %% [markdown]
# ## Section D — Hyperbolic Identities

# %%
print("=" * 60)
print("HYPERBOLIC IDENTITY GALLERY")
print("=" * 60)

hyp_results = []
for ident in HYPERBOLIC_IDENTITIES:
    r = prover.prove(ident.expression, domain=ident.domain, timeout=10.0)
    hyp_results.append(r)
    symbol = "PASS" if r.proved() else "FAIL"
    print(f"  [{symbol}] {ident.name:<40} {r.status}")

n_pass = sum(1 for r in hyp_results if r.proved())
print(f"\n  Passed: {n_pass}/{len(hyp_results)}")

# %%
# Deep-dive: cosh²(x) - sinh²(x) = 1
print("\nDeep-dive: Hyperbolic Pythagorean identity")
r = prover.prove("cosh(x)**2 - sinh(x)**2 == 1", domain=(-3.0, 3.0))
print(f"  Status:    {r.status}")
print(f"  SymPy:     {r.sympy_simplification}")

# %% [markdown]
# ## Section E — Physics Identities from PHYSICS_CATALOG

# %%
print("=" * 60)
print("PHYSICS IDENTITY GALLERY")
print("=" * 60)

phys_results = []
for ident in PHYSICS_IDENTITIES:
    r = prover.prove(ident.expression, domain=ident.domain, timeout=10.0)
    phys_results.append(r)
    symbol = "PASS" if r.proved() else "FAIL"
    print(f"  [{symbol}] {ident.name:<45} {r.status}")
    if ident.notes:
        print(f"       Note: {ident.notes}")

n_pass = sum(1 for r in phys_results if r.proved())
print(f"\n  Passed: {n_pass}/{len(phys_results)}")

# %%
# Schrodinger unitarity: |exp(ix)|² = cos²(x) + sin²(x) = 1
print("\nPhysics deep-dive: Schrodinger unitarity")
r = prover.prove("cos(x)**2 + sin(x)**2 == 1", domain=(-math.pi, math.pi))
print(f"  |exp(ix)|² = 1?  Status: {r.status}")
print(f"  Physical meaning: quantum probability conservation")

# %% [markdown]
# ## Section F — Failed Proofs and Why (Hard Cases)
#
# Some identities cannot be proved automatically. Understanding failure modes
# is as important as understanding successes.

# %%
print("=" * 60)
print("CHALLENGING / FAILING CASES")
print("=" * 60)

hard_cases = [
    ("False identity: sin(x) == 2", "sin(x) == 2", (-math.pi, math.pi)),
    ("False identity: exp(x) == exp(x) + 1", "exp(x) == exp(x) + 1", (-1.0, 1.0)),
    ("Open: sin(x) exact EML rep", "sin(x) == sin(x)", (-math.pi, math.pi)),
    ("Deep: Stirling approx", "lgamma(x + 1) == x*log(x) - x + 0.5*log(2*3.141592653589793*x)", (5.0, 20.0)),
]

for label, expr, dom in hard_cases:
    r = prover.prove(expr, domain=dom, n_simulations=200, timeout=5.0)
    print(f"\n  {label}")
    print(f"  Expression: {expr[:60]}")
    print(f"  Status:     {r.status}  (confidence: {r.confidence:.2f})")
    print(f"  Residual:   {r.max_residual:.2e}")
    if r.notes:
        print(f"  Notes:      {r.notes[0]}")

# %% [markdown]
# ### Why do proofs fail?
#
# 1. **False identities** (e.g. `sin(x) == 2`): High residual immediately
#    detected numerically.
# 2. **SymPy limitations**: Some true identities have complicated symbolic
#    forms that `simplify` cannot reduce. Use `trigsimp`, `expand_trig`, etc.
# 3. **MCTS depth limit**: For identities requiring deep EML trees (> 10 nodes),
#    the witness search may not converge in reasonable time.
# 4. **Domain issues**: Some identities only hold on restricted domains.

# %% [markdown]
# ## Section G — Batch Benchmark Run (20 easy identities)

# %%
easy_identities = get_by_difficulty("easy")[:20]
print(f"Running benchmark on {len(easy_identities)} easy identities...")
print("=" * 60)

report = prover.benchmark(
    catalog=easy_identities,
    n_simulations=500,
    timeout=15.0,
)

print(report.summary())

# %%
# JSON export
import json
data = report.to_json()
print(f"\nJSON export:")
print(f"  n_total:      {data['n_total']}")
print(f"  n_proved:     {data['n_proved']}")
print(f"  success_rate: {data['success_rate']:.1%}")
print(f"  mean_time:    {data['mean_elapsed_s']:.3f}s")

# %%
# Also run trivial identities for a 100% expected pass-rate
trivials = get_by_difficulty("trivial")
print(f"\nRunning {len(trivials)} trivial identities...")
trivial_report = prover.benchmark(catalog=trivials, n_simulations=100, timeout=5.0)
print(f"  Pass rate: {trivial_report.success_rate:.1%}")

# %% [markdown]
# ## Section H — Export a Proof to LaTeX

# %%
print("=" * 60)
print("LATEX PROOF EXPORT")
print("=" * 60)

r = prover.prove("exp(x) * exp(-x) == 1", domain=(-3.0, 3.0))

print(f"Identity: exp(x) * exp(-x) == 1")
print(f"Status:   {r.status}")
print()
print("LaTeX proof:")
print("-" * 40)
if r.latex_proof:
    print(r.latex_proof)
else:
    print("(No LaTeX proof generated)")
print("-" * 40)

# %%
# Save LaTeX proof to file
import os

output_dir = os.path.join(os.path.dirname(__file__), "..", "paper")
os.makedirs(output_dir, exist_ok=True)
proof_path = os.path.join(output_dir, "exp_inv_proof.tex")

with open(proof_path, "w", encoding="utf-8") as f:
    f.write(r"\documentclass{article}" + "\n")
    f.write(r"\usepackage{amsmath, amsthm}" + "\n")
    f.write(r"\newtheorem{theorem}{Theorem}" + "\n")
    f.write(r"\begin{document}" + "\n\n")
    f.write(r"\begin{theorem}" + "\n")
    f.write(r"$e^x \cdot e^{-x} = 1$" + "\n")
    f.write(r"\end{theorem}" + "\n")
    f.write((r.latex_proof or "") + "\n")
    f.write(r"\end{document}" + "\n")

print(f"LaTeX saved to: {proof_path}")

# %% [markdown]
# ## Section I — EML Structural Identities

# %%
print("=" * 60)
print("EML STRUCTURAL IDENTITIES")
print("=" * 60)

for ident in EML_IDENTITIES:
    r = prover.prove(ident.expression, domain=ident.domain, timeout=5.0)
    symbol = "PASS" if r.proved() else "FAIL"
    print(f"  [{symbol}] {ident.name:<40} {r.status}")
    if ident.notes:
        print(f"       {ident.notes}")

# %% [markdown]
# ## Section J — Full Catalog Summary

# %%
print("=" * 60)
print("FULL IDENTITY CATALOG SUMMARY")
print("=" * 60)
print(f"  Total identities: {len(ALL_IDENTITIES)}")
print()

for category in ["trigonometric", "hyperbolic", "exponential", "special", "physics", "eml", "open"]:
    items = get_by_category(category)
    print(f"  {category:<20}: {len(items):3d} identities")

print()
for diff in ["trivial", "easy", "medium", "hard", "open"]:
    items = get_by_difficulty(diff)
    print(f"  difficulty={diff:<8}: {len(items):3d} identities")

# %% [markdown]
# ## Appendix — Proof Hierarchy Diagram
#
# ```
# Identity f(x) = g(x)
#      │
#      ├─ Tier 1: Numerical ─────────────── max|f-g| < 1e-8 → proved_numerical (conf=0.9)
#      │          (500 points, math module)
#      │
#      ├─ Tier 2: SymPy Exact ──────────── simplify(f-g)==0 → proved_exact (conf=1.0)
#      │          (no floating point)
#      │
#      ├─ Tier 3: Interval Certified ───── |f-g| < 1e-6 on sub-intervals → proved_certified (0.95)
#      │          (20 sub-intervals)
#      │
#      └─ Tier 4: EML Witness ──────────── MCTS finds T ≈ f; simplify(T-g)==0 → proved_witness (1.0)
#                 (MCTS + SymPy bridge)
# ```
#
# The neurosymbolic loop closes when:
# 1. MCTS explores the EML expression space (neural/stochastic search)
# 2. SymPy verifies the discovered expression algebraically (symbolic reasoning)
#
# This is the core innovation of monogate: **EML trees as proof witnesses**.
