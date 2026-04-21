"""
Polynomial node count analysis under SuperBEST v5 costs.
Session: Polynomials_With_Cheap_Add
"""
import json

# SuperBEST v5.1 cost tables
COSTS_POS = {
    "exp": 1, "ln": 1, "recip": 1,
    "div": 2, "neg": 2, "mul": 2, "sub": 2, "add": 2, "sqrt": 2,
    "pow": 1,   # EPL/ELMl for x>0 (X20 resolution)
    "sin": 1, "cos": 1,
}

COSTS_GEN = {
    "exp": 1, "ln": 1, "recip": 1,
    "div": 2, "neg": 2, "mul": 6, "sub": 2, "add": 2, "sqrt": 2,
    "pow": 3,
    "sin": 1, "cos": 1,
}

NAIVE = {
    "exp": 1, "ln": 3, "mul": 13, "div": 15, "add": 11,
    "sub": 5, "neg": 9, "recip": 5, "sqrt": 8, "pow": 15, "sin": 13, "cos": 13,
}

results = {}

print("=" * 70)
print("POLYNOMIAL NODE COUNT ANALYSIS: SuperBEST v5")
print("=" * 70)

# ------------------------------------------------------------------
# 1. General degree-N polynomial (monomial form)
# p(x) = a0 + a1*x + a2*x^2 + ... + aN*x^N
#
# Positive domain (x>0, constants treated as free scalars):
#   k=1: mul(a1,x)=2n + add(to a0)=2n = 4n
#   k>=2: pow(x,k)=1n + mul(ak, x^k)=2n + add=2n = 5n per term
#   Total for degree N>=2: 4 + 5*(N-1) = 5N - 1
#
# General domain (x can be any real):
#   k=1: mul_gen(6) + add(2) = 8n
#   k>=2: pow_gen(3) + mul_gen(6) + add(2) = 11n per term
#   Total for N>=2: 8 + 11*(N-1) = 11N - 3
#
# Naive:
#   k=1: naive_mul(13) + naive_add(11) = 24n
#   k>=2: naive_pow(15) + naive_mul(13) + naive_add(11) = 39n per term
#   Total for N>=2: 24 + 39*(N-1) = 39N - 15
# ------------------------------------------------------------------

def mono_pos(N):
    if N == 0:
        return 0
    if N == 1:
        return 4
    return 4 + 5 * (N - 1)

def mono_gen(N):
    if N == 0:
        return 0
    if N == 1:
        return 8
    return 8 + 11 * (N - 1)

def mono_naive(N):
    if N == 0:
        return 0
    if N == 1:
        return 24
    return 24 + 39 * (N - 1)

print("\n--- 1. General Degree-N Polynomial (monomial form) ---")
for N in [1, 2, 3, 4, 5, 10]:
    p = mono_pos(N)
    g = mono_gen(N)
    nv = mono_naive(N)
    spct = 100 * (1 - p / nv)
    gpct = 100 * (1 - g / nv)
    print(f"  N={N:2d}: pos={p:4d}n  gen={g:4d}n  naive={nv:4d}n  "
          f"savings_pos={spct:.1f}%  savings_gen={gpct:.1f}%")

results["general_monomial_form"] = {
    "description": "p(x) = a_0 + a_1*x + ... + a_N*x^N (monomial basis)",
    "cost_formula_pos": "5N - 1 for N>=2 (pos domain, pow=1n, mul=2n, add=2n)",
    "cost_formula_gen": "11N - 3 for N>=2 (gen domain, pow=3n, mul=6n, add=2n)",
    "cost_formula_naive": "39N - 15 for N>=2",
    "spot_checks": {
        str(N): {"pos": mono_pos(N), "gen": mono_gen(N), "naive": mono_naive(N)}
        for N in [1, 2, 3, 5, 10]
    }
}

# ------------------------------------------------------------------
# 2. Horner Form
# p(x) = ((...((a_N*x + a_{N-1})*x + a_{N-2})*x ... + a_0)
# Per step: one mul + one add; N steps for degree-N polynomial.
# Positive: mul(2n) + add(2n) = 4n per step; total = 4N
# General: mul_gen(6n) + add(2n) = 8n per step; total = 8N
# Naive: mul(13n) + add(11n) = 24n per step; total = 24N
# If monic (a_N=1): save one mul -> pos: 4N-2, gen: 8N-6
# ------------------------------------------------------------------

def horner_pos(N):
    return 4 * N

def horner_gen(N):
    return 8 * N

def horner_naive(N):
    return 24 * N

print("\n--- 2. Horner Form ---")
for N in [1, 2, 3, 4, 5, 10]:
    p = horner_pos(N)
    g = horner_gen(N)
    nv = horner_naive(N)
    spct = 100 * (1 - p / nv)
    print(f"  N={N:2d}: pos={p:4d}n  gen={g:4d}n  naive={nv:4d}n  savings_pos={spct:.1f}%")

results["horner_form"] = {
    "description": "Horner method: (...((a_N*x + a_{N-1})*x + a_{N-2})*x ... + a_0)",
    "cost_formula_pos": "4N (mul=2n + add=2n per step)",
    "cost_formula_gen": "8N (mul_gen=6n + add=2n per step)",
    "cost_formula_naive": "24N",
    "monic_savings": "subtract 2n (pos) or 6n (gen) if leading coeff is 1",
    "spot_checks": {
        str(N): {"pos": horner_pos(N), "gen": horner_gen(N), "naive": horner_naive(N)}
        for N in [1, 2, 3, 5, 10]
    }
}

# ------------------------------------------------------------------
# 3. Taylor series of exp(x): sum_{k=0}^N x^k / k!
#
# k=0: 1 (free constant)
# k=1: x (free, coeff=1)
# Connection k=0 to k=1: add(1, x) = 2n
# k>=2 each: pow(x,k)=1n (pos) + mul(1/k!, x^k)=2n + add=2n = 5n
# Total for N>=2: 2 + 5*(N-1)
# Note: exp(x) itself = 1n. This counts the truncated Taylor approximation.
# ------------------------------------------------------------------

def taylor_exp_pos(N):
    if N == 0:
        return 0
    if N == 1:
        return 2   # add(1, x)
    return 2 + 5 * (N - 1)

def taylor_exp_naive(N):
    if N == 0:
        return 0
    if N == 1:
        return 11
    return 11 + 39 * (N - 1)

print("\n--- 3. Taylor series of exp(x): sum x^k/k! ---")
for N in [2, 3, 4, 5, 10]:
    p = taylor_exp_pos(N)
    nv = taylor_exp_naive(N)
    print(f"  N={N:2d} terms: pos={p:4d}n  naive={nv:4d}n  savings={100*(1-p/nv):.1f}%")
print("  Note: exact exp(x)=1n; Taylor is approximation cost")

results["taylor_exp"] = {
    "description": "Truncated Taylor series: sum_{k=0}^N x^k/k!",
    "exact_function_cost": "1n via EML(x,1)",
    "cost_formula_pos": "2 + 5*(N-1) = 5N-3 for N>=2",
    "spot_checks": {str(N): taylor_exp_pos(N) for N in [2, 3, 5, 10]}
}

# ------------------------------------------------------------------
# 4. Taylor series of ln(1+x): sum_{k=1}^N (-1)^{k+1} x^k/k
#
# k=1: x (free, coeff=1, sign +1)
# k>=2: pow(x,k)=1n + mul(1/k)=2n + sub/add=2n = 5n each
# Total: 5*(N-1) for N>=2
# Note: ln(1+x) itself = 2n (add + ln). Taylor is the polynomial approximation.
# ------------------------------------------------------------------

def taylor_ln_pos(N):
    if N <= 1:
        return 0
    return 5 * (N - 1)

print("\n--- 4. Taylor series of ln(1+x) ---")
for N in [2, 3, 5, 10]:
    p = taylor_ln_pos(N)
    print(f"  N={N:2d} terms: pos={p:4d}n")
print("  Note: ln(1+x) exact = 2n (add+ln). Taylor is approximation cost.")
print("  Alternating signs handled by sub=add=2n in v5.")

results["taylor_ln"] = {
    "description": "Truncated Taylor: sum_{k=1}^N (-1)^{k+1} x^k/k",
    "exact_function_cost": "2n (add(x,1)+ln)",
    "cost_formula_pos": "5*(N-1) for N>=2",
    "sign_handling": "add and sub both cost 2n in v5; alternating signs add NO extra cost",
    "spot_checks": {str(N): taylor_ln_pos(N) for N in [2, 3, 5, 10]}
}

# ------------------------------------------------------------------
# 5. Taylor series of sin(x):
# sum_{k=0}^N (-1)^k x^{2k+1}/(2k+1)!
#
# k=0: x (free)
# k=1: -x^3/6: pow(x,3)=1n + mul(1/6)=2n + sub=2n = 5n
# k>=1: same pattern, 5n each
# Total: 5*N for k=0..N-1 extra terms
# ------------------------------------------------------------------

def taylor_sin_pos(N):
    return 5 * N

print("\n--- 5. Taylor series of sin(x) ---")
for N in [1, 2, 3, 5]:
    p = taylor_sin_pos(N)
    print(f"  N={N:2d} (k=0..{N}, i.e. {N+1} terms): pos={p:4d}n")
print("  Note: sin(x) exact = 1n via Im(EML(ix,1)). Taylor is approximation cost.")

results["taylor_sin"] = {
    "description": "Truncated Taylor: sum_{k=0}^N (-1)^k x^{2k+1}/(2k+1)!",
    "exact_function_cost": "1n via Im(EML(ix,1))",
    "cost_formula_pos": "5*N for N extra terms beyond the leading x",
    "spot_checks": {str(N): taylor_sin_pos(N) for N in [1, 2, 3, 5]}
}

# ------------------------------------------------------------------
# 6. Chebyshev Polynomials T_0 through T_5
# Recurrence: T_{n+1}(x) = 2x*T_n(x) - T_{n-1}(x)
# T_0=1 (free), T_1=x (free)
#
# T_2: compute 2x (mul=2n), then mul(2x, T_1=x)=2n, sub(T_0=1)=2n -> 6n
# T_3: mul(2x, T_2)=2n + sub(T_1=x)=2n = 4n extra (reuse 2x) -> cumulative 10n
# T_4: mul(2x, T_3)=2n + sub(T_2)=2n = 4n extra -> 14n
# T_5: mul(2x, T_4)=2n + sub(T_3)=2n = 4n extra -> 18n
# Formula for n>=2: 6 + 4*(n-2) = 4n - 2
# ------------------------------------------------------------------

def chebyshev_cost(n):
    if n <= 1:
        return 0
    return 4 * n - 2

print("\n--- 6. Chebyshev Polynomials T_0 to T_5 ---")
cheb_formulas = {
    0: "1",
    1: "x",
    2: "2x^2 - 1",
    3: "4x^3 - 3x",
    4: "8x^4 - 8x^2 + 1",
    5: "16x^5 - 20x^3 + 5x",
}
for n in range(6):
    c = chebyshev_cost(n)
    print(f"  T_{n}: {c:3d}n  f(x)={cheb_formulas[n]}")
print("  Recurrence formula n>=2: 4n-2 nodes (cumulative, including all T_k, k<=n)")

results["chebyshev"] = {
    "description": "Chebyshev polynomials via recurrence T_{n+1}=2x*T_n - T_{n-1}",
    "recurrence_cost_per_step": "4n (mul(2x,T_n)=2n + sub(T_{n-1})=2n)",
    "first_step_setup": "6n for T_2 (includes computing 2x)",
    "cost_formula_cumulative": "4n-2 for n>=2 (cumulative DAG reusing 2x and all prior T_k)",
    "individual_costs": {f"T{n}": chebyshev_cost(n) for n in range(6)},
    "formulas": {f"T{n}": cheb_formulas[n] for n in range(6)},
}

# ------------------------------------------------------------------
# 7. Legendre Polynomials P_0 through P_4
# Recurrence: (n+1)P_{n+1} = (2n+1)x*P_n - n*P_{n-1}
# P_0=1, P_1=x, P_2=(3x^2-1)/2, P_3=(5x^3-3x)/2, P_4=(35x^4-30x^2+3)/8
#
# Standalone costs (positive domain, using pow for x^k):
# P_0: 0n
# P_1: 0n
# P_2 = (3/2)x^2 - (1/2): pow(x,2)=1n + mul(3/2, x^2)=2n + sub(1/2)=2n = 5n
# P_3 = x*(5x^2-3)/2:
#   pow(x,2)=1n + mul(5,x^2)=2n + sub(3)=2n + mul(x,_)=2n + mul(1/2,_)=2n = 9n
# P_4 = (35x^4-30x^2+3)/8:
#   pow(x,4)=1n + mul(35/8,x^4)=2n + pow(x,2)=1n(shared DAG) + mul(30/8,x^2)=2n + sub=2n + add(3/8)=2n = 10n
# ------------------------------------------------------------------

legendre_costs = [0, 0, 5, 9, 10]
legendre_formulas = [
    "1",
    "x",
    "(3x^2-1)/2",
    "(5x^3-3x)/2",
    "(35x^4-30x^2+3)/8",
]
legendre_breakdowns = [
    "free constant",
    "free input variable",
    "pow(x,2)=1n + mul(3/2,x^2)=2n + sub(1/2)=2n",
    "pow(x,2)=1n + mul(5,x^2)=2n + sub(3)=2n + mul(x)=2n + mul(1/2)=2n",
    "pow(x,4)=1n + mul(35/8,x^4)=2n + pow(x,2)=1n(shared) + mul(30/8,x^2)=2n + sub=2n + add(3/8)=2n",
]

print("\n--- 7. Legendre Polynomials P_0 to P_4 ---")
for n in range(5):
    print(f"  P_{n}: {legendre_costs[n]:3d}n  f(x)={legendre_formulas[n]}")
    print(f"         {legendre_breakdowns[n]}")

results["legendre"] = {
    "description": "Legendre polynomials (standalone, positive domain)",
    "individual_costs": {f"P{n}": legendre_costs[n] for n in range(5)},
    "formulas": {f"P{n}": legendre_formulas[n] for n in range(5)},
    "breakdowns": {f"P{n}": legendre_breakdowns[n] for n in range(5)},
    "note": "pow(x,2) can be shared across terms in P_4 (DAG reuse)",
}

# ------------------------------------------------------------------
# 8. Bernstein Basis Polynomials B_{k,n}(x) = C(n,k) * x^k * (1-x)^{n-k}
#
# For x in (0,1) [positive domain]:
# (1-x): sub(1,x) = 2n
# x^k: pow(x,k) = 1n (pos)
# (1-x)^{n-k}: pow(1-x, n-k) = 1n (pos, since 1-x > 0)
# x^k*(1-x)^{n-k}: mul = 2n
# C(n,k) * (...): mul = 2n (constant coefficient)
# Total: 2 + 1 + 1 + 2 + 2 = 8n
#
# Special cases:
#   k=0: x^0=1 (free); just pow(1-x,n)=1n, skip x^k and its mul -> 2+1+2 = 5n if C(n,0)!=1
#         if C(n,0)=1 (always true): 2+1 = 3n (sub+pow only)
#   k=n: (1-x)^0=1 (free); pow(x,n)=1n, skip (1-x)^0 and its mul -> 2+1+2=5n ...
#         C(n,n)=1 always, so: pow(x,n)=1n + sub(1,x)=... wait, (1-x) not needed if n-k=0
#         Actually if n-k=0: B_{n,n}(x)=x^n: just pow(x,n)=1n (no sub needed!)
# ------------------------------------------------------------------

print("\n--- 8. Bernstein Basis Polynomials ---")
print("  B_{k,n}(x) = C(n,k) * x^k * (1-x)^{n-k}, x in (0,1)")
print("  General (0 < k < n): sub(2n) + pow_xk(1n) + pow_1mx(1n) + mul(2n) + mul_coeff(2n) = 8n")
print("  k=0: sub(2n) + pow_1mx(1n) = 3n  [C(n,0)=1, x^0=1 free, no coeff mul]")
print("  k=n: pow_xn(1n) = 1n  [C(n,n)=1, (1-x)^0=1 free, no sub needed]")
print()
print("  Example B_{2,4}(x) = 6*x^2*(1-x)^2:")
print("    sub(1,x)=2n + pow(x,2)=1n + pow(1-x,2)=1n + mul(x^2,1-x^2)=2n + mul(6,)=2n = 8n")

results["bernstein"] = {
    "description": "Bernstein basis polynomial B_{k,n}(x) = C(n,k)*x^k*(1-x)^{n-k}",
    "domain": "x in (0,1) for positive-domain pow",
    "cost_general_0ltkltn": 8,
    "cost_k_eq_0": 3,
    "cost_k_eq_n": 1,
    "breakdown_general": {
        "sub(1,x)": 2, "pow(x,k)": 1, "pow(1-x,n-k)": 1,
        "mul_product": 2, "mul_coeff": 2, "total": 8
    }
}

# ------------------------------------------------------------------
# 9. log-sum-exp: ln(exp(x) + exp(y))
# exp(x): 1n
# exp(y): 1n
# add(exp(x),exp(y)): 2n  <-- ADD-T1: all reals, uniform 2n!
# ln(sum): 1n
# Total: 5n
#
# N-argument: ln(sum_{i=1}^N exp(x_i))
# N exps: N*1n; N-1 adds: (N-1)*2n; 1 ln: 1n
# Total: N + 2(N-1) + 1 = 3N - 1
# ------------------------------------------------------------------

print("\n--- 9. log-sum-exp ---")
def lse_cost(N):
    return N + 2*(N-1) + 1

print("  2-arg ln(exp(x)+exp(y)):")
print("    exp(x)=1n + exp(y)=1n + add(2n, ALL REALS via ADD-T1) + ln(1n) = 5n")
print("    depth: 3 (ln->add->exp)")
print()
for N in [2, 3, 5, 10]:
    c = lse_cost(N)
    print(f"  N={N:2d}: {c:3d}n  (formula 3N-1={3*N-1})")

results["log_sum_exp"] = {
    "two_arg": {
        "formula": "ln(exp(x) + exp(y))",
        "cost": 5,
        "breakdown": {"exp_x": 1, "exp_y": 1, "add": 2, "ln": 1},
        "depth": 3,
        "key_insight": "ADD-T1 drops add cost from 11n to 2n for all real inputs; depth 3 not depth 5+",
    },
    "N_arg": {
        "formula": "ln(sum_{i=1}^N exp(x_i))",
        "cost_formula": "3N - 1",
        "spot_checks": {str(N): lse_cost(N) for N in [2, 3, 5, 10]}
    }
}

# ------------------------------------------------------------------
# 10. Softmax
# sigma_i(x) = exp(x_i) / sum_j exp(x_j)
# N-class softmax:
#   exp_numerators: N*1n
#   denom = sum_j exp(x_j): N exps shared + N-1 adds = N + 2(N-1) = 3N-2
#   but exps are shared with numerators -> denominator ADDS only: (N-1)*2n extra
#   N divs: N*2n
# Total: N(exp) + (N-1)*2n(adds for denom) + N*2n(divs) = N + 2N-2 + 2N = 5N - 2
# ------------------------------------------------------------------

def softmax_cost(N):
    exp_terms = N * 1         # exp for each class (shared numerator+denom)
    denom_adds = (N - 1) * 2  # N-1 additions to sum the exps
    div_terms = N * 2         # divide each exp by sum
    return exp_terms + denom_adds + div_terms

print("\n--- 10. Softmax ---")
print("  sigma_i = exp(x_i) / sum_j exp(x_j)")
print("  Components: N exp (shared) + (N-1) adds for sum + N divs")
for N in [2, 3, 5, 10]:
    c = softmax_cost(N)
    print(f"  N={N:2d}: {c:3d}n  (formula 5N-2={5*N-2})")

results["softmax"] = {
    "formula": "sigma_i(x) = exp(x_i) / sum_j exp(x_j)",
    "cost_formula": "5N - 2 (shared exps, N-1 adds, N divs)",
    "breakdown": {
        "exp_terms": "N*1n (shared with numerators)",
        "sum_additions": "(N-1)*2n",
        "divisions": "N*2n"
    },
    "spot_checks": {str(N): softmax_cost(N) for N in [2, 3, 5, 10]}
}

# ------------------------------------------------------------------
# 11. Depth Analysis
# ------------------------------------------------------------------

print("\n--- 11. Depth Analysis ---")
depth_findings = {
    "depth_1_functions": [
        {"expr": "exp(x)", "cost": 1, "op": "EML(x,1)"},
        {"expr": "ln(x)", "cost": 1, "op": "EXL(0,x)"},
        {"expr": "1/x", "cost": 1, "op": "ELSb(0,x)"},
        {"expr": "sin(x)", "cost": 1, "op": "Im(EML(ix,1))"},
        {"expr": "cos(x)", "cost": 1, "op": "Re(EML(ix,1))"},
        {"expr": "x^n (x>0)", "cost": 1, "op": "EPL(n,x)"},
    ],
    "depth_2_polynomials": [
        {"expr": "x^2 + c", "cost": 3, "ops": "pow(1n)+sub/add(2n)", "note": "monic, simple offset"},
        {"expr": "x^2 - c", "cost": 3, "ops": "pow(1n)+sub(2n)", "note": "same"},
        {"expr": "x^2 + x", "cost": 3, "ops": "pow(1n)+add(x,pow)(2n)", "note": "monic linear+quadratic"},
        {"expr": "x^2 - x", "cost": 3, "ops": "pow(1n)+sub(2n)", "note": "same structure"},
        {"expr": "x^n (x>0)", "cost": 1, "ops": "pow=1n", "note": "trivially depth 1"},
    ],
    "depth_3_minimum_for": [
        "Any degree-2 polynomial ax^2+bx+c with a,b,c all nonzero and a!=1",
        "Any degree-3+ polynomial in general (3 nested mul/add/sub operations minimum)",
        "Horner evaluation of any degree-3+ polynomial",
        "log-sum-exp: ln(exp(x)+exp(y)) is exactly depth 3",
    ],
    "key_finding": (
        "Cheap add (2n, ADD-T1) REDUCES NODE COUNT but does NOT drop polynomial depth below 3 "
        "for N>=3 or for general degree-2 with nonzero coefficients. "
        "Simple monic quadratics (x^2+c, x^2+x) do sit at depth 2 with 3n total. "
        "No standard polynomial basis function (Chebyshev, Legendre, Bernstein) falls below depth 3 under v5."
    ),
    "add_depth_impact": (
        "In v4, add_gen=11n required a depth-5+ subtree. "
        "In v5, add=2n always; depth of add is 2 (two nested ops). "
        "So any expression containing add now has its addition subtree at depth 2 instead of 5+. "
        "log-sum-exp: was depth 5-7 effectively (through the 11-node add_gen tree); now depth 3."
    )
}

print(f"  Depth-2 polynomials found: {len(depth_findings['depth_2_polynomials'])}")
for p in depth_findings["depth_2_polynomials"]:
    print(f"    {p['expr']}: {p['cost']}n, depth 2 -- {p['note']}")
print()
print(f"  Key finding: {depth_findings['key_finding'][:100]}...")

results["depth_analysis"] = depth_findings

# ------------------------------------------------------------------
# 12. New identities natural under v5 (cheap add enables)
# ------------------------------------------------------------------

new_identities = {
    "log_sum_exp_symmetry": {
        "identity": "ln(exp(x) + exp(y)) = x + ln(1 + exp(y-x)) [for x>=y]",
        "v5_cost_direct": 5,
        "v5_cost_stable": 8,
        "note": "Direct form now competitive; stable form costs 8n due to extra sub+add",
        "verdict": "Direct form preferred under v5 due to cheap add",
    },
    "polynomial_via_log_ratio": {
        "identity": "x^a * (1-x)^b = exp(a*ln(x) + b*ln(1-x)) [Beta distribution kernel]",
        "cost_breakdown": {
            "ln_x": 1, "mul_a": 2, "ln_1mx": 3, "mul_b": 2, "add": 2, "exp": 1
        },
        "total": 11,
        "comment": "ln(1-x) = ln+sub = 2+2=... actually sub(1,x)=2n then ln=1n = 3n total",
        "note": "This EML representation avoids two separate pow operations at cost 11n vs 8n Bernstein",
    },
    "sum_of_exponentials": {
        "identity": "sum_{k=1}^N a_k * exp(b_k * x)",
        "v5_cost": "N*(1+2+2) - 2 = 5N-2 (exp+mul_b+mul_a per term, N-1 adds)",
        "note": "Mixtures of exponentials are now cheap to sum; equal cost to softmax-style sums",
    },
    "chebyshev_via_trig": {
        "identity": "T_n(cos(theta)) = cos(n*theta) -- exact 1n if cos and n*theta available",
        "v5_cost_via_trig": "1n for cos (EML-based) + mul(n,theta)=2n = 3n for any n",
        "v5_cost_via_recurrence": f"4n-2 for T_n",
        "verdict": "Trigonometric route beats recurrence for n>=2: 3n vs 4n-2",
        "note": "For n=2: trig=3n vs recurrence=6n; for n=5: trig=3n vs recurrence=18n. Massive win.",
    },
    "sigmoid": {
        "identity": "sigma(x) = 1/(1+exp(-x)) = recip(1+exp(-x))",
        "breakdown": {
            "neg_x": 2, "exp_negx": 1, "add_1": 2, "recip": 1
        },
        "total": 6,
        "note": "add(1, exp(-x))=2n via ADD-T1; total 6n. Alternative: 1-recip(1+exp(x))=same cost.",
    },
    "softplus": {
        "identity": "softplus(x) = ln(1 + exp(x))",
        "breakdown": {"exp_x": 1, "add_1": 2, "ln": 1},
        "total": 4,
        "note": "add=2n (ADD-T1); 4n total. Before v5: add_pos=3n -> 5n, add_gen=11n -> 13n.",
        "depth": 3,
    },
    "gelu_approx": {
        "identity": "GELU(x) approx x * sigmoid(1.702*x)",
        "cost": "mul(1.702,x)=2n + sigmoid(6n) + mul(x,sigma)=2n = 10n",
        "note": "Sigmoid was the expensive part; with cheap add, sigmoid=6n total",
    }
}

print("\n--- 12. New/Natural Identities Under v5 ---")
for k, v in new_identities.items():
    cost = v.get("total", v.get("v5_cost", "see details"))
    print(f"  {k}: {cost}")

results["new_identities"] = new_identities

# ------------------------------------------------------------------
# Summary table
# ------------------------------------------------------------------

summary = {
    "session": "Polynomials_With_Cheap_Add",
    "date": "2026-04-20",
    "superbest_version": "v5.1",
    "key_breakthrough": "add=2n for ALL real x,y (ADD-T1). Old: 3n (pos) / 11n (gen).",
    "main_findings": [
        "Horner form costs 4N (pos) vs 5N-1 for monomial; saves ~20% for same degree",
        "No standard polynomial of degree N>=3 falls below depth 3 under v5 costs",
        "Simple monic quadratics (x^2+c, x^2+x) achieve depth 2 at 3n total",
        "Chebyshev T_n: 4n-2 cumulative nodes, but trig route cos(n*arccos(x)) costs only 3n for any n",
        "log-sum-exp ln(exp(x)+exp(y)): 5n total, depth 3 (add=2n is the key reduction)",
        "softplus ln(1+exp(x)): 4n (add=2n makes this exceptionally cheap)",
        "sigmoid 1/(1+exp(-x)): 6n",
        "Bernstein B_{k,n}: 8n general, 3n for boundary cases k=0 (expt coeff) or k=n",
        "Alternating-sign Taylor series (sin, ln(1+x)): add and sub IDENTICAL cost (2n each); no penalty",
        "N-arg log-sum-exp: 3N-1 nodes; N-class softmax: 5N-2 nodes",
    ],
    "depth_below_3_answer": (
        "ANSWER: No standard polynomial of degree >=2 with more than 2 terms falls below depth 3. "
        "Degree-1: depth 1 (free). Degree-2 monic with ONE extra term (x^2+c or x^2+x): depth 2, 3n. "
        "The cheap add DOES reduce depth of the addition subtree from 5+ (v4 add_gen) to 2 (v5). "
        "But the mul chain in polynomial evaluation always adds more depth."
    )
}

results["summary"] = summary

with open("D:/monogate/python/results/polynomial_node_counts.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
for finding in summary["main_findings"]:
    print(f"  * {finding}")
print()
print("DEPTH QUESTION:", summary["depth_below_3_answer"])
print()
print("Results saved to: D:/monogate/python/results/polynomial_node_counts.json")
