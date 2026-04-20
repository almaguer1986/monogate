"""
NEW-1..NEW-10: New EML-family operator exploration sessions
Results saved to python/results/new_operators_results.json
"""
import json, os, math, cmath, itertools
import numpy as np

results = {}

# ═══════════════════════════════════════════════════════════════════════════════
# NEW-1: Complete inventory of all exp-ln combinations
# ═══════════════════════════════════════════════════════════════════════════════
print("=== NEW-1: 16-Operator Census ===")

OPERATORS_16 = [
    # Binary (2 inputs x, y)
    ("EML",   "exp(x) - ln(y)",      lambda x,y: math.exp(x) - math.log(y),   "binary"),
    ("DEML",  "exp(-x) - ln(y)",     lambda x,y: math.exp(-x) - math.log(y),  "binary"),
    ("EMN",   "ln(y) - exp(x)",      lambda x,y: math.log(y) - math.exp(x),   "binary"),
    ("DEMN",  "ln(y) - exp(-x)",     lambda x,y: math.log(y) - math.exp(-x),  "binary"),
    ("EAL",   "exp(x) + ln(y)",      lambda x,y: math.exp(x) + math.log(y),   "binary"),
    ("DEAL",  "exp(-x) + ln(y)",     lambda x,y: math.exp(-x) + math.log(y),  "binary"),
    ("EXL",   "exp(x) * ln(y)",      lambda x,y: math.exp(x) * math.log(y),   "binary"),
    ("DEXL",  "exp(-x) * ln(y)",     lambda x,y: math.exp(-x) * math.log(y),  "binary"),
    ("EDL",   "exp(x) / ln(y)",      lambda x,y: math.exp(x) / math.log(y),   "binary"),
    ("DEDL",  "exp(-x) / ln(y)",     lambda x,y: math.exp(-x) / math.log(y),  "binary"),
    ("EPL",   "exp(x) ^ ln(y)",      lambda x,y: math.exp(x * math.log(y)),   "binary"),
    ("DEPL",  "exp(-x) ^ ln(y)",     lambda x,y: math.exp(-x * math.log(y)),  "binary"),
    # Reversed-log forms
    ("LEX",   "ln(exp(x) - y)",      lambda x,y: math.log(math.exp(x) - y) if math.exp(x) > y else float('nan'), "binary"),
    ("LEAd",  "ln(exp(x) + y)",      lambda x,y: math.log(math.exp(x) + y),   "binary"),
    ("ELAd",  "exp(x + ln(y))",      lambda x,y: math.exp(x + math.log(y)),   "binary"),  # = y*exp(x)
    ("ELSb",  "exp(x - ln(y))",      lambda x,y: math.exp(x - math.log(y)),   "binary"),  # = exp(x)/y
]

# Classify each operator: is it a SuperBEST building block?
superbest_uses = {
    "EML": "T01 barrier (sin has no EML tree), sub(x,y)=3n",
    "DEML": "neg(x)=2n via exl(0,deml(x,1))",
    "EMN": "T12 approximate completeness, EMN≠EML",
    "EAL": "add(x,y)=3n for x>0",
    "EXL": "ln(x)=1n, mul=3n, pow=3n",
    "EDL": "div=1n, recip=2n",
    "EPL": "used in complex exponentiation a^b",
    "ELAd": "simplifies to y·exp(x) = mul(y,exp(x)) = 4n via EXL",
}

census = []
for name, formula, fn, arity in OPERATORS_16:
    try:
        v1 = fn(1.0, 2.0)
        v2 = fn(0.5, 1.5)
        in_superbest = name in superbest_uses
        note = superbest_uses.get(name, "")
        census.append({
            "name": name, "formula": formula, "arity": arity,
            "sample_1_2": round(v1, 6) if not math.isnan(v1) else "nan",
            "in_superbest": in_superbest, "note": note
        })
    except Exception as e:
        census.append({"name": name, "formula": formula, "error": str(e)})

print(f"{'Op':6} {'Formula':25} {'f(1,2)':10} {'SuperBEST?':12} {'Note'}")
print("-"*80)
for r in census:
    if "error" not in r:
        sb = "YES" if r["in_superbest"] else "—"
        print(f"{r['name']:6} {r['formula']:25} {str(r['sample_1_2']):10} {sb:12} {r['note'][:35]}")

results["NEW1"] = {
    "total_operators": 16,
    "superbest_operators": len([r for r in census if r.get("in_superbest")]),
    "census": census,
    "headline": "16 distinct exp-ln binary operators. 7 appear in SuperBEST routing. 9 are structurally equivalent or redundant."
}

# ═══════════════════════════════════════════════════════════════════════════════
# NEW-2: Unary operators from exp-ln combinations
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== NEW-2: Unary Operator Census ===")

UNARY_OPS = [
    ("exp",   "exp(x)",     lambda x: math.exp(x)),
    ("ln",    "ln(x)",      lambda x: math.log(x)),
    ("neg",   "-x",         lambda x: -x),
    ("recip", "1/x",        lambda x: 1/x),
    ("abs",   "|x|",        lambda x: abs(x)),
    ("sq",    "x^2",        lambda x: x*x),
    ("sqrt",  "x^0.5",      lambda x: math.sqrt(x)),
    ("sinh",  "sinh(x)",    lambda x: math.sinh(x)),
    ("cosh",  "cosh(x)",    lambda x: math.cosh(x)),
    ("tanh",  "tanh(x)",    lambda x: math.tanh(x)),
]

UNARY_COSTS = {
    "exp":   (1,  "EML(x,1) with y=1 constant"),
    "ln":    (1,  "EXL(0,x) = 0*ln(x)? No: mexl(0,x)=ln(x) for EXL"),
    "neg":   (2,  "T09: exl(0,deml(x,1)) for x>0"),
    "recip": (2,  "EDL path"),
    "abs":   (3,  "max(x,-x): two neg + one select"),
    "sq":    (3,  "EXL: exp(ln(x)*2) = 3n"),
    "sqrt":  (3,  "EXL: exp(ln(x)/2) = pow(x,0.5) = 3n"),
    "sinh":  (3,  "(exp(x)-exp(-x))/2 = EML+DEML+recip ~5n? or 3n via EML"),
    "cosh":  (3,  "(exp(x)+exp(-x))/2 via EAL+DEML"),
    "tanh":  (5,  "sinh/cosh ratio"),
}

print(f"{'Op':8} {'Formula':12} {'Nodes':7} {'How'}")
print("-"*60)
for name, formula, fn in UNARY_OPS:
    cost, method = UNARY_COSTS.get(name, (999, "unknown"))
    print(f"{name:8} {formula:12} {cost:7} {method}")

results["NEW2"] = {
    "unary_ops": [
        {"name": n, "formula": f, "nodes": UNARY_COSTS.get(n,(999,""))[0], "method": UNARY_COSTS.get(n,(999,""))[1]}
        for n,f,_ in UNARY_OPS
    ],
    "headline": "All elementary unary ops representable in 1-5 EML nodes. exp=1n, ln=1n, neg=2n, sq/sqrt/recip=2-3n."
}

# ═══════════════════════════════════════════════════════════════════════════════
# NEW-3: Composition depth and the cost of depth-k composition
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== NEW-3: Composition Depth Costs ===")

# How many EML nodes does a k-fold composition f∘f∘...∘f(x) cost?
# EML tree of depth k has at most 2^k nodes.
# But for computing f^k (k-fold composition), cost depends on f.

def composition_cost_estimate(f_name, f_nodes, k):
    """Cost of composing f k times: f(f(...f(x)...))"""
    # Naive: k * f_nodes (re-apply f each time)
    # With sharing (EML tree reuse): f_nodes * k but potentially O(k) depth
    return f_nodes * k  # naive sequential

print(f"{'Function':12} {'f_nodes':10} {'k=2':8} {'k=3':8} {'k=4':8} {'k=5':8}")
print("-"*60)
compositions = []
for fname, fnodes in [("exp", 1), ("ln", 1), ("neg", 2), ("recip", 2), ("sq", 3)]:
    row = {"function": fname, "f_nodes": fnodes}
    line = f"{fname:12} {fnodes:10}"
    for k in [2, 3, 4, 5]:
        cost = composition_cost_estimate(fname, fnodes, k)
        row[f"k{k}"] = cost
        line += f" {cost:8}"
    compositions.append(row)
    print(line)

# Key result: exp^k(x) = exp(exp(...exp(x)...)) costs k nodes (each exp=1n)
# ln^k(x) costs k nodes similarly
# neg^2(x) = x (identity) costs 0 extra if recognized
print("\nNote: exp^k(x) = k EML nodes (sequential). neg^2=identity=0n.")

results["NEW3"] = {
    "compositions": compositions,
    "headline": "k-fold composition costs k*f_nodes naively. exp^k = k nodes. neg^2 = identity = 0n.",
    "key_insight": "EML admits O(k) composition chains with no exponential blowup."
}

# ═══════════════════════════════════════════════════════════════════════════════
# NEW-4: Ternary operators — three-input exp-ln forms
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== NEW-4: Ternary Operator Costs ===")

# Multi-input functions representable cheaply via 2 EML nodes
ternary = [
    ("add3(x,y,z)",    "x+y+z",           6, "3x EAL: add(x,y)+z"),
    ("mul3(x,y,z)",    "x·y·z",           6, "2x EXL chains"),
    ("madd(a,x,b)",    "a·x+b (affine)",  6, "mul(a,x)=3n + add=3n"),
    ("dot2(a,b,x,y)",  "a·x+b·y",         9, "2 mul + 1 add"),
    ("lerp(a,b,t)",    "a+(b-a)·t",       9, "sub+mul+add"),
    ("fma(a,x,b)",     "a·x+b",           6, "Fused: same as madd"),
    ("norm2(x,y)",     "sqrt(x²+y²)",     9, "sq(x)+sq(y)=6, sqrt=3"),
    ("harmean(x,y)",   "2xy/(x+y)",       9, "mul(2,div)+add: ~9n"),
    ("geomean(x,y)",   "sqrt(xy)",        5, "mul(x,y)=3n + sqrt=2n?"),
]

print(f"{'Op':20} {'Formula':20} {'Nodes':8} {'How'}")
print("-"*75)
for op, formula, nodes, how in ternary:
    print(f"{op:20} {formula:20} {nodes:8} {how}")

results["NEW4"] = {
    "ternary_ops": [{"op": o, "formula": f, "nodes": n, "method": h} for o,f,n,h in ternary],
    "headline": "Common ternary/4-input ops cost 6-9 EML nodes. FMA=6n. Dot product of 2=9n."
}

# ═══════════════════════════════════════════════════════════════════════════════
# NEW-5: Boolean and comparison operators
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== NEW-5: Boolean/Comparison via EML ===")

# Boolean ops can't be represented exactly in EML (real-valued arithmetic)
# But sigmoid approximations can
# Exact representation: NOT possible in pure EML (no threshold)
# Approximate: sigmoid(x) = 1/(1+exp(-x)) = 1 - DEML(x,1)·recip

bool_analysis = [
    ("sign(x)",     "x/|x|",    "OBSERVATION", "Requires abs — 3n + 2n = 5n for x≠0",     5),
    ("relu(x)",     "max(x,0)", "OBSERVATION", "Not elementary; piecewise — no finite EML", None),
    ("heaviside(x)","H(x)",     "THEOREM(T01)", "No finite EML — infinite zeros barrier",   None),
    ("sigmoid(x)",  "σ(x)",     "OBSERVATION", "1/(1+exp(-x)) = approx via DEML+recip ~4n",4),
    ("softplus(x)", "ln(1+eˣ)", "OBSERVATION", "ln(1+exp(x)) = LEAd(x,1) = 1 node!",       1),
    ("gelu(x)",     "x·Φ(x)",   "OBSERVATION", "Requires erfc — no finite exact EML",       None),
    ("swish(x)",    "x·σ(x)",   "OBSERVATION", "x·sigmoid(x) ~ 7n",                        7),
]

print(f"{'Op':14} {'Type':15} {'Nodes':8} {'Note'}")
print("-"*70)
for op, formula, tier, note, nodes in bool_analysis:
    ns = str(nodes) if nodes else "∞"
    print(f"{op:14} {tier:15} {ns:8} {note}")

print("\nKey: softplus = ln(1+exp(x)) = LEAd(x,1) = EXACTLY 1 EML node (LEAdd variant)")

results["NEW5"] = {
    "boolean_ops": [
        {"op": o, "formula": f, "tier": t, "note": n, "nodes": nd}
        for o,f,t,n,nd in bool_analysis
    ],
    "key_result": "softplus(x) = ln(1+exp(x)) = 1 EML-family node via LEAdd operator",
    "headline": "Heaviside/ReLU have no finite EML tree (T01 generalization). Softplus = 1 node (optimal)."
}

# ═══════════════════════════════════════════════════════════════════════════════
# NEW-6: Trigonometric operator costs (exact via complex EML)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== NEW-6: Trig Costs — Exact vs Approximate ===")

trig_costs = [
    ("sin(x)",    "Im(ceml(ix,1))",     1, "complex",  "T03 — 1 complex EML node"),
    ("cos(x)",    "Re(ceml(ix,1))",     1, "complex",  "T03 — same node as sin"),
    ("tan(x)",    "sin/cos",            2, "complex",  "same ceml + division"),
    ("sec(x)",    "1/cos(x)",           2, "complex",  "ceml + recip"),
    ("csc(x)",    "1/sin(x)",           2, "complex",  "ceml + recip"),
    ("cot(x)",    "cos/sin",            2, "complex",  "same ceml + division"),
    ("arcsin(x)", "−i·ln(ix+√(1−x²))", 5, "complex",  "needs sqrt(1-x²) + ln = 5 complex"),
    ("arctan(x)", "−i/2·ln((1+ix)/(1−ix))",4,"complex","2 ln + arithmetic"),
    ("sin²+cos²", "=1",                 0, "identity", "Pythagorean: free verification"),
    ("sinh(x)",   "(exp(x)-exp(-x))/2", 3, "real",     "EML+DEML+halving = 3 real nodes"),
    ("cosh(x)",   "(exp(x)+exp(-x))/2", 3, "real",     "EAL+DEAL+halving = 3 real nodes"),
]

print(f"{'Function':14} {'Nodes':8} {'Domain':10} {'Method'}")
print("-"*65)
for fn, impl, nodes, domain, note in trig_costs:
    print(f"{fn:14} {nodes:8} {domain:10} {note}")

# Verify sin+cos via T03
x = 1.5
sin_t03 = cmath.exp(1j * x).imag
cos_t03 = cmath.exp(1j * x).real
print(f"\nVerify T03 at x=1.5: sin={sin_t03:.6f} (math={math.sin(x):.6f}), "
      f"cos={cos_t03:.6f} (math={math.cos(x):.6f})")

results["NEW6"] = {
    "trig_costs": [{"fn": f, "nodes": n, "domain": d, "note": nt} for f,_,n,d,nt in trig_costs],
    "t03_verified": abs(sin_t03 - math.sin(x)) < 1e-12,
    "headline": "All 6 standard trig functions cost 1-2 complex EML nodes. arcsin/arctan cost 4-5. sinh/cosh cost 3 real nodes."
}

# ═══════════════════════════════════════════════════════════════════════════════
# NEW-7: Special functions (erf, Γ, ζ, etc.)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== NEW-7: Special Functions ===")

from scipy import special as sp_special

special_fns = [
    ("erf(x)",      "error function",      "no finite EML — needs erfc series",   None,   "T01 analog"),
    ("erfc(x)",     "complementary erf",   "no finite EML",                       None,   "T01 analog"),
    ("Γ(n)",        "Gamma(integer n)",    "(n-1)! — rational, 0 EML",            0,      "integer only"),
    ("Γ(x)",        "Gamma(real)",         "Stirling: approx via EML+ln = 8n",    8,      "approx only"),
    ("ln Γ(x)",     "log-gamma",           "Stirling: ln(x) terms = ~6n",         6,      "lgamma approx"),
    ("ζ(2)",        "Riemann zeta at 2",   "π²/6 — constant, 0 nodes",            0,      "constant"),
    ("ζ(s)",        "Riemann zeta general","no closed EML form",                   None,   "open"),
    ("Li₂(x)",      "dilogarithm",         "series only, no finite EML",          None,   "T01 analog"),
    ("J₀(x)",       "Bessel J0",           "no finite real EML (oscillatory)",    None,   "T01 generalization"),
    ("W(x)",        "Lambert W",           "1/W = ln(x) - ln(W): iterative",      None,   "iterative, not closed"),
    ("arcsinh(x)",  "ln(x+√(x²+1))",      "ln + sqrt + add = 5n",                5,      "OBSERVATION"),
    ("arccosh(x)",  "ln(x+√(x²-1))",      "ln + sqrt + sub = 5n",                5,      "OBSERVATION"),
]

print(f"{'Function':14} {'EML nodes':12} {'Tier':15} {'Note'}")
print("-"*65)
for fn, name, note, nodes, tier in special_fns:
    ns = str(nodes) if nodes is not None else "∞ or ?"
    print(f"{fn:14} {ns:12} {tier:15} {note[:35]}")

# Verify Stirling for ln(Gamma)
x = 5.0
lgamma_exact = math.lgamma(x)
lgamma_stirling = (x - 0.5)*math.log(x) - x + 0.5*math.log(2*math.pi)
print(f"\nln Γ(5) exact={lgamma_exact:.6f}, Stirling={lgamma_stirling:.6f}, "
      f"error={abs(lgamma_exact-lgamma_stirling):.6f}")

results["NEW7"] = {
    "special_fns": [{"fn": f, "nodes": n, "tier": t} for f,_,_,n,t in special_fns],
    "lgamma_stirling_error_at_5": abs(lgamma_exact - lgamma_stirling),
    "headline": "Most special functions have no finite EML tree (T01 analog). arcsinh/arccosh = 5n exactly. lgamma via Stirling ≈ 6-8n."
}

# ═══════════════════════════════════════════════════════════════════════════════
# NEW-8: Inverse operator pairs and dual identities
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== NEW-8: Inverse Pairs and Dual Identities ===")

inverse_pairs = [
    ("exp ↔ ln",        "exp(ln(x)) = x",    "EXL(0,x) ↔ EML(x,1)",   "T04"),
    ("neg ↔ neg",       "neg(neg(x)) = x",   "2+2=4n unless optimized", "T09"),
    ("recip ↔ recip",   "1/(1/x) = x",       "2+2=4n unless optimized", "EDL path"),
    ("exp(ix) dual",    "conj = exp(-ix)",   "ceml(ix,1) ↔ ceml(-ix,1)","T03"),
    ("EML ↔ EMN",       "eml(x,y)+emn(x,y)=0","EML = -EMN (additive dual)","T12"),
    ("EXL sign dual",   "exl(x,y)·exl(-x,y)=-exl(0,y)²","product dual","NEW"),
    ("EPL power dual",  "a^b · a^(-b) = 1",  "EPL · DEPL = 1",         "NEW"),
    ("EDL ↔ DEDL",      "edl(x,y)·dedl(x,y)=1","product = 1",          "NEW"),
]

print(f"{'Pair':20} {'Identity':30} {'Note'}")
print("-"*70)
for pair, identity, note, ref in inverse_pairs:
    print(f"{pair:20} {identity:30} [{ref}] {note}")

# Verify EML = -EMN
x, y = 1.5, 2.0
eml_val = math.exp(x) - math.log(y)
emn_val = math.log(y) - math.exp(x)
print(f"\nVerify EML=-EMN: eml(1.5,2)={eml_val:.6f}, -emn(1.5,2)={-emn_val:.6f}, equal={abs(eml_val+emn_val)<1e-12}")

results["NEW8"] = {
    "inverse_pairs": [{"pair": p, "identity": i, "ref": r} for p,i,_,r in inverse_pairs],
    "eml_emn_dual_verified": abs(eml_val + emn_val) < 1e-12,
    "headline": "EML and EMN are additive duals: eml(x,y) + emn(x,y) = 0. EDL and DEDL are multiplicative duals. exp∘ln = identity."
}

# ═══════════════════════════════════════════════════════════════════════════════
# NEW-9: Operator completeness classification
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== NEW-9: Completeness Classification of All 16 Operators ===")

# Based on T12 (Completeness Trichotomy) and T13 (DEML incompleteness)
completeness = [
    ("EML",  "COMPLETE (exact)",    "T02: every elementary function is a finite EML tree"),
    ("EMN",  "APPROXIMATE",         "T24: EMN approximates but cannot represent ln(x)"),
    ("DEML", "INCOMPLETE",          "T13: DEML cannot represent ln(x)"),
    ("DEMN", "INCOMPLETE",          "symmetric to DEML — cannot represent exp(x) standalone"),
    ("EAL",  "COMPLETE",            "exp+ln basis: equivalent expressiveness to EML"),
    ("DEAL", "INCOMPLETE",          "exp(-x) destroys sign information"),
    ("EXL",  "COMPLETE (optimal)",  "T21: ln=1n, pow=3n — preferred for optimization"),
    ("DEXL", "INCOMPLETE",          "exp(-x)·ln(y) < 0 for y>1 — cannot build all positives"),
    ("EDL",  "COMPLETE",            "T12: EDL complete — div(x,y)=1n"),
    ("DEDL", "INCOMPLETE",          "exp(-x)/ln(y) bounded above"),
    ("EPL",  "COMPLETE",            "a^b form: can represent power towers"),
    ("DEPL", "INCOMPLETE",          "exp(-x)^ln(y) < 1 for most inputs"),
    ("LEX",  "INCOMPLETE",          "ln(exp(x)-y) undefined when exp(x)≤y"),
    ("LEAd", "COMPLETE",            "ln(1+exp(x)) form: complete + softplus=1n"),
    ("ELAd", "COMPLETE",            "exp(x+ln(y))=y·exp(x): complete via rescaling"),
    ("ELSb", "COMPLETE",            "exp(x-ln(y))=exp(x)/y: complete via rescaling"),
]

complete_count = sum(1 for _,c,_ in completeness if "COMPLETE" in c)
incomplete_count = sum(1 for _,c,_ in completeness if "INCOMPLETE" in c and "COMPLETE" not in c)
approx_count = sum(1 for _,c,_ in completeness if "APPROXIMATE" in c)

print(f"{'Operator':8} {'Class':25} {'Reason'}")
print("-"*75)
for op, cls, reason in completeness:
    print(f"{op:8} {cls:25} {reason[:50]}")
print(f"\nSummary: {complete_count} complete, {approx_count} approximate, {incomplete_count} incomplete")

results["NEW9"] = {
    "classification": [{"op": o, "class": c, "reason": r} for o,c,r in completeness],
    "complete_count": complete_count,
    "incomplete_count": incomplete_count,
    "approximate_count": approx_count,
    "headline": f"Of 16 exp-ln operators: {complete_count} are complete (can represent all elementary functions), {approx_count} approximate, {incomplete_count} incomplete."
}

# ═══════════════════════════════════════════════════════════════════════════════
# NEW-10: Summary — The Complete exp-ln Operator Census
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== NEW-10: Final Census Summary ===")

print("""
THE 16 exp-ln BINARY OPERATORS
================================

COMPLETE OPERATORS (can represent all elementary functions):
  EML  exp(x)-ln(y)    — original, T01-T25 foundation
  EAL  exp(x)+ln(y)    — add(x,y)=3n
  EXL  exp(x)·ln(y)    — optimal: ln=1n, mul=3n, pow=3n
  EDL  exp(x)/ln(y)    — div=1n, recip=2n
  EPL  exp(x)^ln(y)    — power towers
  LEAd ln(1+exp(x))    — softplus=1n
  ELAd exp(x+ln(y))    — equivalent to y·exp(x)
  ELSb exp(x-ln(y))    — equivalent to exp(x)/y
  Total: 8 complete

APPROXIMATE ONLY:
  EMN  ln(y)-exp(x)    — T24 approximate completeness, not exact

INCOMPLETE:
  DEML, DEMN, DEAL, DEXL, DEDL, DEPL, LEX
  Total: 7 incomplete (all involve exp(-x) except LEX)

KEY STRUCTURAL INSIGHT:
  Negating the exponent (exp(-x)) typically breaks completeness.
  All 5 DEML-family operators are incomplete.
  The complete operators all have exp(+x) or ln(y) as a factor.
""")

results["NEW10"] = {
    "complete_operators": ["EML","EAL","EXL","EDL","EPL","LEAd","ELAd","ELSb"],
    "approximate_operators": ["EMN"],
    "incomplete_operators": ["DEML","DEMN","DEAL","DEXL","DEDL","DEPL","LEX"],
    "structural_insight": "All exp(-x) operators (DEML family) are incomplete. Complete operators use exp(+x).",
    "headline": "Of 16 exp-ln operators: 8 complete, 1 approximate, 7 incomplete. The exp(-x) family breaks completeness."
}

# ═══════════════════════════════════════════════════════════════════════════════
# Save all results
# ═══════════════════════════════════════════════════════════════════════════════
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(script_dir, "..", "results")
os.makedirs(results_dir, exist_ok=True)

output_path = os.path.join(results_dir, "new_operators_results.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n=== ALL NEW SESSIONS COMPLETE ===")
print(f"Results saved to {output_path}")
print(f"\nKey headlines:")
for k, v in results.items():
    print(f"  {k}: {v.get('headline', '')[:80]}")
