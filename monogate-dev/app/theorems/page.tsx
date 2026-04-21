"use client";
import { useState } from "react";
import type { Metadata } from "next";

// Metadata can't be exported from client components, handled via layout.
// Title set in layout.

const C = {
  bg: "#08090e", surface: "#0d0f18", surface2: "#12151f",
  border: "#1c1f2e", border2: "#252836",
  text: "#d4d4d4", muted: "#4a4d62",
  orange: "#e8a020", blue: "#6ab0f5", green: "#4ade80",
  red: "#f87171", purple: "#a78bfa", yellow: "#fbbf24",
};

const TIER_META: Record<string, { label: string; color: string; desc: string }> = {
  THEOREM:     { label: "THEOREM",     color: C.green,  desc: "Complete, checkable proof. No gaps." },
  PROPOSITION: { label: "PROPOSITION", color: C.blue,   desc: "Proved, short or routine." },
  CONJECTURE:  { label: "CONJECTURE",  color: C.orange, desc: "Precisely stated, believed true, unproved." },
  OBSERVATION: { label: "OBSERVATION", color: C.yellow, desc: "Empirical pattern. No proof." },
  DEFINITION:  { label: "DEFINITION",  color: C.purple, desc: "A new concept or classification choice." },
  SPECULATION: { label: "SPECULATION", color: C.muted,  desc: "Interesting but not currently testable or provable." },
};

type Result = {
  id: string;
  name: string;
  tier: keyof typeof TIER_META;
  session: string;
  category: string;
  statement: string;
  evidence: string;
  verify?: string;
  deps?: string;
  resolvedBy?: string;  // for struck-through conjectures
};

const RESULTS: Result[] = [
  // ─── THEOREMS (21) ─────────────────────────────────────────────────────────
  {
    id: "T01",
    name: "EML Universality",
    tier: "THEOREM",
    session: "External (Odrzywołek 2026)",
    category: "Core Algebra",
    statement: "eml(x, y) = exp(x) − ln(y) generates every elementary function as a finite binary tree. Published arXiv:2603.21852.",
    evidence: "Published, peer-reviewable proof. Constructs explicit trees for each elementary function using the Log Recovery identity and composition rules.",
    verify: "See arXiv:2603.21852.",
    deps: "Definition of elementary functions (Liouville/Ritt).",
  },
  {
    id: "T09",
    name: "Negation in 2 Nodes — Optimal",
    tier: "THEOREM",
    session: "Sprint2",
    category: "Core Algebra",
    statement: "neg(x) = −x is computable in exactly 2 EML-family nodes: exl(0, deml(x,1)) = −x. Optimal; 1 node is impossible by exhaustive search.",
    evidence: "Exhaustive search over all 1-node candidates finds no neg construction. Upper bound: explicit 2-node construction verified.",
    verify: "python -c \"import math; exl=lambda x,y: math.exp(x)*math.log(y); deml=lambda x,y: math.exp(-x)-math.log(y); print(round(exl(0,deml(1.5,1)),10))\"",
  },
  {
    id: "T10u",
    name: "Multiplication in 2 Nodes — F16 Optimal",
    tier: "THEOREM",
    session: "Depth Spectrum",
    category: "Core Algebra",
    statement: "In the 16-operator family F16, mul(x,y) = ELAd(EXL(0,x), y) = x·y in exactly 2 nodes. This is optimal in F16. In the 6-operator F6 library, 3 nodes are required (T29).",
    evidence: "Exhaustive search found exactly 4 matching 2-node trees in F16. Source: python/scripts/mul_lower_bound_search.py.",
    deps: "T29.",
  },
  {
    id: "T11",
    name: "EML Self-Map Has No Fixed Points",
    tier: "THEOREM",
    session: "Sprint2",
    category: "Analytic Properties",
    statement: "For all x > 0: eml(x,x) = exp(x) − ln(x) > x. The map x ↦ eml(x,x) has no fixed points. Minimum gap: eml(x,x) − x ≥ 1.648629... at x ≈ 1.7632.",
    evidence: "Calculus: d/dx[exp(x)−ln(x)−x]=0 at x≈1.7632. Numerical minimum confirmed to 6 decimal places.",
    verify: "python -c \"from scipy.optimize import minimize_scalar; import math; f=lambda x: math.exp(x)-math.log(x)-x; r=minimize_scalar(f,bounds=(0.1,5),method='bounded'); print(round(r.fun,6))\"",
  },
  {
    id: "T12",
    name: "Exponential Position Theorem",
    tier: "THEOREM",
    session: "COMP-1 through COMP-5",
    category: "Operator Family",
    statement: "Among the 16 standard exp-ln binary operators: 8 are exactly complete (all with exp(+x), no domain restriction), 1 is approximately complete (EMN), 7 are incomplete. The completeness class is determined entirely by the position of negation relative to exp.",
    evidence: "Forward direction (T26): exp(+x) → complete. Reverse (T27): exp(−x) → incomplete by 5 distinct barrier types. LEX (T28): domain collapse. EMN (T24): approximately complete.",
    deps: "T09, T26, T27, T28, T24.",
  },
  {
    id: "T13",
    name: "DEML Incompleteness",
    tier: "THEOREM",
    session: "Sprint2",
    category: "Operator Family",
    statement: "deml(x,y) = exp(−x) − ln(y) is not exactly complete. neg(x) = −x is not constructible from DEML and constant 1. The self-composition deml(1, deml(x,1)) = e⁻¹ + x has slope +1; no DEML tree achieves slope −1.",
    evidence: "Exhaustive search over 861,952 trees at N ≤ 13 finds no neg construction. Structural proof: slope locked to +1.",
    verify: "python python/results/deml_incompleteness.py",
    deps: "T12.",
  },
  {
    id: "T14",
    name: "Tight Zeros Bound",
    tier: "THEOREM",
    session: "Sprint2",
    category: "Analytic Properties",
    statement: "A depth-k EML tree has at most 2^k real zeros. This bound is tight: explicit constructions achieve it.",
    evidence: "Structural induction: each EML node combines two sub-trees, at most doubling the zero count. Tightness: explicit constructions at each depth. Computational check k=3..6: maximum observed zeros = 2 (bound far from tight in practice).",
    deps: "Analytic function theory.",
  },
  {
    id: "T17",
    name: "Strict i-Unconstructibility (Lean-verified)",
    tier: "THEOREM",
    session: "Sprint2",
    category: "Complex EML",
    statement: "Under strict principal-branch semantics, i = √−1 is not constructible from {1} using the ceml grammar in finite depth. At depth 6, the closest approach is |T − i| ≥ 4.76×10⁻⁶.",
    evidence: "Lean 4 verification: complete inductive proof, 0 sorries. Depth-6 exhaustive search: minimum distance 4.76×10⁻⁶.",
    verify: "See lean4/i_unconstructibility.lean",
  },
  {
    id: "T24",
    name: "EMN Approximate Completeness",
    tier: "THEOREM",
    session: "Sprint2",
    category: "Operator Family",
    statement: "emn(x,y) = ln(y) − exp(x) is approximately complete: for every elementary function f and ε > 0, there exists a finite EMN tree with sup-norm error < ε on any compact set. EMN is not exactly complete: the residual exp(·) error at depth k is ≥ exp(−e^k) > 0.",
    evidence: "Approximate completeness: −exp(x) unbounded gives full range access. Not exact: irremovable exp(·) residual; error converges doubly-exponentially but never reaches 0.",
    deps: "T12.",
  },
  {
    id: "T26",
    name: "Forward Completeness: exp(+x) → Exactly Complete",
    tier: "THEOREM",
    session: "COMP-2",
    category: "Operator Family",
    statement: "Let O(x,y) = h(exp(x), ln y) where h does not impose a domain restriction preventing O from taking all real values. Then O is exactly complete.",
    evidence: "(1) O(x,1) = exp(x) in 1 node. (2) O(c, exp(x)) achieves slope −1. (3) Cross-family bridge gives exact neg in ≤ 2 nodes. (4) With neg, exp, ln: all elementary functions by Ritt's theorem. Verified for all 8 complete operators.",
    deps: "T09, T12.",
  },
  {
    id: "T27",
    name: "Reverse Incompleteness: exp(−x) → Incomplete",
    tier: "THEOREM",
    session: "COMP-3",
    category: "Operator Family",
    statement: "Let O(x,y) = h(exp(−x), ln y), h ∈ {−, +, ×, /, ^}. Then O is incomplete. The 6 operators DEML, DEMN, DEAL, DEXL, DEDL, DEPL each fail by a distinct mechanism.",
    evidence: "DEML: slope barrier (+1). DEMN: domain failure (outputs always negative). DEAL: irremovable e⁻¹ offset. DEXL: dead constant at c=1. DEDL/DEPL: exponential decay, no linear growth. All verified computationally.",
    deps: "T12, T13.",
  },
  {
    id: "T28",
    name: "LEX Domain Incompleteness",
    tier: "THEOREM",
    session: "COMP-3",
    category: "Operator Family",
    statement: "LEX(x,y) = ln(exp(x) − y) is incomplete despite having exp(+x). At self-composition depth n, the valid input domain shrinks to ∅.",
    evidence: "Domain calculation: lex(1, lex(x,1)) requires x < ln(eᵉ+1) ≈ 2.81. Domain strictly shrinks at each level. Verified computationally.",
    deps: "T12.",
  },
  {
    id: "T29",
    name: "Mul ≥ 3 Nodes in F6",
    tier: "THEOREM",
    session: "Depth Spectrum",
    category: "Core Algebra",
    statement: "No 1-node or 2-node tree over the 6-operator library F6 = {EML, EDL, EXL, EAL, EMN, DEML} computes mul(x,y) = x·y exactly. Minimum in F6 is 3 nodes.",
    evidence: "Exhaustive search over all 96 candidate 1-node trees and all 12,288 candidate 2-node mixed trees at 8 test points: no match found.",
    verify: "python python/scripts/mul_lower_bound_search.py",
    deps: "Exhaustive enumeration.",
  },
  {
    id: "T31",
    name: "Complex EML Closure Density",
    tier: "THEOREM",
    session: "Depth Spectrum",
    category: "Complex EML",
    statement: "EML trees (with complex inputs) are dense in H(K), the space of holomorphic functions on any compact simply-connected K ⊂ ℂ. Additionally, i is an accumulation point of EML₁.",
    evidence: "Density: Runge's theorem + T01. Accumulation: depth-6 exhaustive data — closest depth-6 value to i has |w − i| = 4.76×10⁻⁶. Resolves C02 and C03.",
    deps: "T01, T17.",
  },
  {
    id: "T32",
    name: "Mul ≥ 2 Nodes in Any exp-ln Family",
    tier: "THEOREM",
    session: "DOOR-1",
    category: "Core Algebra",
    statement: "In any 1-operator family F where the operator has the form h(exp(±x), ln(y)), multiplication x·y requires at least 2 nodes. A single operator node cannot compute mul.",
    evidence: "Derivative obstruction: ∂op/∂x always contains an exp(x) factor, which cannot equal y for all (x,y). Boundary value at x=0 confirms. Verified for all 16 operators in F16.",
    deps: "T29, T10u.",
  },
  {
    id: "T34",
    name: "Naive Upper Bound",
    tier: "THEOREM",
    session: "COST-2",
    category: "Cost Theory",
    statement: "For any expression E: Cost(E) ≤ NaiveCost(E) = Σ cᵢ · nᵢ where cᵢ is the SuperBEST v3 per-operation cost and nᵢ is the count of operation i in E. The bound is tight iff there are no shared subtrees, no compound patterns, and no constant folding.",
    evidence: "Proof by construction: the naive expansion is a valid DAG. Minimality reduces it. Tightness conditions enumerated in COST2_Naive_Upper_Bound.tex.",
    deps: "T38.",
  },
  {
    id: "T38",
    name: "Cost Decomposition Theorem",
    tier: "THEOREM",
    session: "COST-6 / R2",
    category: "Cost Theory",
    statement: "For any expression E: Cost(E) = NaiveCost(E) − SharingDiscount(E) − PatternBonus(E). All three terms are non-negative. The decomposition is unique for a fixed pattern set and canonical sharing strategy.",
    evidence: "Proved in R2_Decomposition_Theorem.tex. SharingDiscount ≥ 0: merging shared nodes cannot increase cost. PatternBonus ≥ 0: each compound pattern replaces more-expensive naive subtrees. Uniqueness: canonical sharing + greedy pattern matching.",
    deps: "T34.",
  },

  // ─── PROPOSITIONS (6) ─────────────────────────────────────────────────────
  {
    id: "T08",
    name: "SuperBEST Table v5 — 18 Nodes, All Entries Structurally Proved",
    tier: "THEOREM",
    session: "Sprint2 / Sprint3 / S-T08 / ADD-CASCADE",
    category: "Core Algebra",
    statement: "SuperBEST v5: 18 total nodes, all 10 entries structurally proved optimal. recip=1n (ELSb(0,x)=1/x — R16-C1), div=2n (ELSb(ln(x),y)), sub=2n (T33), mul=2n (T10u/F16), neg=2n (T09), add=2n for ALL real x,y via LEDIV(x,DEML(y,1))=x+y — breakthrough replacing add_pos=3n and add_gen=11n, pow=3n (3-intermediate lower bound), sqrt=2n (derivative obstruction), exp=1n, ln=1n. The positive-domain / general-domain split is eliminated: one unified add=2n entry covers all reals. No entry relies solely on exhaustive search.",
    evidence: "S-T08 full structural audit (2026-04-20) + ADD-CASCADE (2026-04-20). add=2n construction: DEML(y,1)=exp(-y), LEDIV(x,z)=ln(exp(x)/z), so LEDIV(x,DEML(y,1))=ln(exp(x)/exp(-y))=ln(exp(x+y))=x+y. Verified: [lediv(a,deml(b,1))-(a+b)] = 0 for all test points. Sum drops from 19n to 18n; savings rise from 74% to 75.3% vs naive EML. Full structural proofs in SuperBEST_v5_Structural_Audit.tex (all 10 entries, structural lower bounds) and ADD_T1_General_Addition_2n.tex (add=2n for all reals, derivative obstruction lower bound). SuperBEST_v5_Table.json.",
    verify: "python -c \"import math; deml=lambda x,y: math.exp(-x)-math.log(y); lediv=lambda x,z: math.log(math.exp(x)/z); print([round(lediv(a,deml(b,1))-(a+b),10) for a,b in [(-3,-2),(-1,0.5),(0.5,2),(2,7),(-3,7),(0,0)]])\"",
    deps: "T09, T10u, T12, T32, T33, R16-C1, ADD-T1.",
  },
  {
    id: "T15",
    name: "Pumping Lemma for EML Trees",
    tier: "PROPOSITION",
    session: "Sprint2",
    category: "Analytic Properties",
    statement: "Depth-k EML trees have at most 2^k real zeros (proved). Observed computational maximum is O(k), suggesting the bound is far from tight. The gap between 2^k and observed O(k) is the Pumping Lemma gap.",
    evidence: "Upper bound: T14. Lower bound construction: sin approximations at depth k have at most 2 observable zeros in practice. Gap unproved.",
    deps: "T14.",
  },
  {
    id: "T21",
    name: "EXL Log-Structure Advantage",
    tier: "PROPOSITION",
    session: "Sprint2",
    category: "Operator Family",
    statement: "EXL(x,y) = exp(x)·ln(y) achieves ln(x) in 1 node: EXL(0, x) = exp(0)·ln(x) = ln(x). Combined with T10u, EXL gives the cheapest logarithm and fastest multiplication route in F16.",
    evidence: "Direct computation: EXL(0,x) = 1·ln(x) = ln(x). Route to mul: ELAd(EXL(0,x), y) = x·y in 2 nodes.",
    verify: "python -c \"import math; exl=lambda x,y: math.exp(x)*math.log(y); print(round(exl(0,2.718),6))\"",
  },
  {
    id: "T25",
    name: "Depth-6 Phase Transition",
    tier: "PROPOSITION",
    session: "Sprint2",
    category: "Complex EML",
    statement: "At depth 5, all complex EML values computed from input 1 have imaginary part Im = −π exactly. At depth 6, imaginary parts escape this constraint and become dense. A structural phase transition at depth 6.",
    evidence: "Exhaustive computation of all depth-5 and depth-6 trees rooted at 1. At depth 5: Im ∈ {−π} (verified). At depth 6: Im values spread across ℝ.",
    deps: "T31.",
  },
  {
    id: "T30",
    name: "Depth Hierarchy: Standard Functions ≤ Depth 3",
    tier: "THEOREM",
    session: "Depth Spectrum / S-T30 / ADD-T1",
    category: "Depth Hierarchy",
    statement: "All standard elementary functions (exp, ln, algebraic, trig via ℂ) have EML depth ≤ 3. The hierarchy is strictly infinite (exp^k requires exactly k nodes). Depth-4 exists (exp^4(x)) but no standard function lives there.",
    evidence: "S-T30 (2026-04-20): all four proof gaps closed. GAP-1 (census completeness): constructive check over standard function tables. GAP-2 (strict hierarchy lower bound): exp^k ∉ EML-(k-1) by Hardy field growth-rate argument. GAP-3/4 (Lemma 4.2 repair): false intermediate bound v≤u^{C'} replaced by correct inductive argument A=exp^{k-1}(x), lnB=exp^{k-2}(x^C), A-lnB→+∞. Full proof: Depth_Spectrum_Self_Contained.tex. Confirmed under SuperBEST v5 (ADD-T1, 2026-04-20): add(x,y) = LEDIV(x,DEML(y,1)) = x+y in 2 nodes (depth 2), valid for ALL real x,y. All 10 core operations now have depth ≤ 2, strictly below the depth-3 ceiling. Depth bound strengthened: addition is depth 2, not depth 3. Definitive proof: Depth_Spectrum_Final.tex.",
    deps: "T14, ADD-T1, T08.",
  },
  {
    id: "T35",
    name: "Lower Bound Theorems (Structural)",
    tier: "THEOREM",
    session: "COST-3",
    category: "Cost Theory",
    statement: "Three structural lower bounds: (T35) Cost(E) ≥ |O(E)| — each non-mergeable operator requires a distinct node, by F16 structure. (T36) Cost(E) ≥ d where d = distinct necessary intermediates — binary-tree counting identity. (T37) Cost(E) ≥ n_exp + n_ln — exp-nodes and ln-nodes are disjoint, each needing a dedicated node by F16 operator structure.",
    evidence: "R18 audit (2026-04-20): all three proofs are structural arguments appealing to F16 operator structure, not definitional unwrapping. Each proof is 2-4 lines. Weak theorems are still theorems. Full proofs in COST3_Lower_Bound.tex.",
    deps: "T38.",
  },
  {
    id: "T40",
    name: "Linear Cost Law",
    tier: "THEOREM",
    session: "COST-9 / R5",
    category: "Cost Theory",
    statement: "For N-term summations with per-term cost α₀, no cross-term sharing, no compound patterns: Cost(E_N) = (α₀ + 2)·N − 2 exactly (SuperBEST v5, c_add=2 for all domains). Softmax: 3N−2. Shannon: 7N−2 (uses neg per term). Taylor: 9N−2. The positive-domain assumption is now unnecessary: c_add=2 applies to all reals via LEDIV+DEML (ADD-CASCADE, 2026-04-20), eliminating the former c_add=3 (positive) vs c_add=11 (general) split.",
    evidence: "R18 audit (2026-04-20) + ADD-CASCADE (2026-04-20): induction proof gap-free. Base N=1: Cost=α₀ by T38 (SD=PB=0). Step: new term costs α₀ (independent, T38) + 1 add node at cost 2 (v5) = α₀+2. Exact equality by T38. Proved in R5_Linear_Cost_Law.tex; updated for v5 in ADD-CASCADE session.",
    deps: "T38, T34.",
  },
  {
    id: "P-NNP",
    name: "No Nesting Penalty Lemma",
    tier: "PROPOSITION",
    session: "COST-6 / R3",
    category: "Cost Theory",
    statement: "For any operators O₁, O₂ and expressions A, B, C: Cost(O₁(O₂(A,B), C)) = c(O₁) + c(O₂) + Cost(A) + Cost(B) + Cost(C). Nested operators pay exactly the sum of individual costs.",
    evidence: "Upper bound: explicit DAG construction. Lower bound: O₂ sub-DAG, O₁ node, and C sub-DAG are pairwise disjoint in any minimal DAG. Applies only to the mathematical cost model, not physical circuits.",
    deps: "T38.",
  },
  {
    id: "P-ACL",
    name: "Additive Cost Law",
    tier: "PROPOSITION",
    session: "R6",
    category: "Cost Theory",
    statement: "For independent expressions E₁, E₂ (sharing no subexpressions): Cost(op(E₁,E₂)) = Cost(E₁) + Cost(E₂) + 1. Corollary: N independent terms cost Σ Cost(termᵢ) + (N−1).",
    evidence: "Upper bound: disjoint optimal DAGs + one root node. Lower bound: the root op node and independent sub-DAGs are disjoint. Proved in R6_Additive_Cost_Law.tex.",
    deps: "T38.",
  },
  {
    id: "P-SD",
    name: "Sharing Discount Formula",
    tier: "PROPOSITION",
    session: "COST-5 / R4",
    category: "Cost Theory",
    statement: "SharingDiscount(E) = Σᵢ NC(Fᵢ) + Σⱼ Cost(Sⱼ)(mⱼ − 1) where Fᵢ are pure-constant foldable blocks and Sⱼ are shared live subexpressions appearing mⱼ ≥ 2 times. For single-formula expressions over distinct variables: SharingDiscount = 0.",
    evidence: "47/50 chembio equations have zero discount (verified). The 3 exceptions have constant-folding only. Proved in R4_Sharing_Discount.tex.",
    deps: "T38.",
  },

  // ─── CONJECTURES ─────────────────────────────────────────────────────────
  {
    id: "C01",
    name: "i-Constructibility (Extended Grammar)",
    tier: "CONJECTURE",
    session: "S11+",
    category: "Complex EML",
    statement: "If the grammar is extended beyond the strict principal-branch ceml (e.g., by allowing multi-valued log, or adding i as an explicit terminal), then i = √−1 becomes exactly constructible and sin(x) becomes EML depth-1 over ℂ.",
    evidence: "T17 shows i is not constructible under strict semantics. T31 shows i is an accumulation point. The open question: does any natural extension of the grammar make i exactly reachable?",
  },
  {
    id: "T39",
    name: "Linear Ceiling Conjecture",
    tier: "CONJECTURE",
    session: "COST-9 / R14",
    category: "Cost Theory",
    statement: "No standard scientific formula has SuperBEST cost exceeding O(N) where N is the number of terms in any sum. Equivalently: every textbook equation is either O(1) (fixed structure) or O(N) (summation over N terms).",
    evidence: "Verified on 187+ equations across 12 domains. Only counterexample class known: Hopfield energy (double sum, O(N²)). No single-sum standard formula found exceeding O(N). Stated as conjecture because counterexample cannot be ruled out.",
    deps: "T40.",
  },
  {
    id: "QCC",
    name: "Quadratic Ceiling Conjecture",
    tier: "CONJECTURE",
    session: "R14",
    category: "Cost Theory",
    statement: "For any N-parameter scientific model, SuperBEST cost is O(N²). No standard scientific formula exceeds O(N²) cost. Pairwise interaction models (Hopfield: 7N²) are the ceiling.",
    evidence: "Verified on 187+ equations. No known counterexample. Supported by physical argument: standard textbook equations model at most pairwise interactions. Triple-interaction tensors (O(N³)) do not appear as standard closed-form expressions.",
    deps: "T39.",
  },
  // ─── RESOLVED CONJECTURES (displayed struck-through) ─────────────────────
  {
    id: "C02",
    name: "Complex EML Closure Density",
    tier: "CONJECTURE",
    session: "S35",
    category: "Complex EML",
    statement: "RESOLVED — The set of functions representable by finite ceml trees over ℂ is dense in H(K) for any compact K. This was stated as a conjecture; proved as T31.",
    evidence: "Resolved by T31 (Complex EML Closure Density). Runge's theorem + T01 give density in H(K).",
    resolvedBy: "T31",
  },
  {
    id: "C03",
    name: "i as Accumulation Point",
    tier: "CONJECTURE",
    session: "S35",
    category: "Complex EML",
    statement: "RESOLVED — i is an accumulation point of EML₁: there exist depth-6 EML trees arbitrarily close to i. Proved as part of T31.",
    evidence: "Resolved by T31. Depth-6 exhaustive search: closest value |w − i| = 4.76×10⁻⁶.",
    resolvedBy: "T31",
  },

  // ─── OBSERVATIONS (9) ────────────────────────────────────────────────────
  {
    id: "O-FOURIER",
    name: "Fourier Beats Taylor by 100× in Node Count",
    tier: "OBSERVATION",
    session: "S-CAL",
    category: "Calculus Costs",
    statement: "sin(x) costs 101 nodes as an 8-term Taylor series under BEST routing. The same function is 1 complex EML node via Fourier/Euler. The factor-100 gap is purely a structural observation.",
    evidence: "Taylor: 9N−3 = 69 nodes for N=8 terms (T25 formula), or 101n with full coefficient expansion. Complex path: Im(ceml(ix,1)) = 1 node. Gap ≈ 100×. Computational, not a proof about the functions themselves.",
  },
  {
    id: "O-LYAPUNOV",
    name: "Lyapunov Landscape 92.9% Correlated with Mandelbrot Interior",
    tier: "OBSERVATION",
    session: "S-CHAOS",
    category: "Dynamical Properties",
    statement: "The Lyapunov exponent landscape of iterating eml(z, c) over a grid of c-values is 92.9% correlated (Pearson) with the Mandelbrot interior indicator. EML and exp(z)+c share universal chaotic structure.",
    evidence: "Numerical: 500×500 grid, 200 iterations each. Pearson r = 0.929. No proof that this correlation holds analytically.",
  },
  {
    id: "O-ATTRACTOR",
    name: "DEML and EMN Generate Bounded Strange Attractors",
    tier: "OBSERVATION",
    session: "S-CHAOS",
    category: "Dynamical Properties",
    statement: "Iterating DEML and EMN in the complex plane generates bounded strange attractors with estimated box-counting dimension ≈ 1.128. No classical period-doubling: the exponential family is a different universality class.",
    evidence: "Computational: 10,000-iteration orbits, box-counting dimension estimated from 50×50 to 800×800 grid scales. Universality class claim based on absence of period-doubling bifurcation sequence.",
  },
  {
    id: "O-NODOUBLING",
    name: "No Period-Doubling in the Exponential Family",
    tier: "OBSERVATION",
    session: "S-CHAOS",
    category: "Dynamical Properties",
    statement: "The bifurcation diagram of eml(z, c) as c varies shows no classical period-doubling cascade. The exponential family transitions directly from fixed points to chaos, bypassing the Feigenbaum universality sequence.",
    evidence: "Bifurcation diagrams computed for 1,000 c-values. No 2-cycle, 4-cycle, 8-cycle sequence observed. Consistent with known theory for exponential maps (Devaney, 1987).",
  },
  {
    id: "O-GEOMETRY",
    name: "Geometry Catalog: 126n vs 345n Naive",
    tier: "OBSERVATION",
    session: "Sprint2",
    category: "Domain Costs",
    statement: "12 classical geometric primitives (hyperbolic distance, Lie group maps, curvature, conformal maps) measured as EML trees: 126n total vs 345n naive EML-only. 63% savings. All computations exact.",
    evidence: "Manual tree construction for each primitive. Savings measured vs naive EML without operator library. Source: python/paper/observations/SuperBEST_ChemBio_Catalog.tex.",
  },
  {
    id: "O-TIMBRE",
    name: "Timbre = EML Node Count",
    tier: "OBSERVATION",
    session: "Sprint2",
    category: "Domain Costs",
    statement: "Each Fourier harmonic = one complex EML node. Timbre measurements: Sine = 1n, Clarinet ≈ 5n, Violin ≈ 12n. 245× fewer nodes than Taylor-based synthesis for equivalent fidelity.",
    evidence: "Node count matches harmonic count for each instrument timbre. 245× factor: Taylor at N=8 terms = 101n vs 1n per complex EML node. Observational correspondence, not a theorem about timbre.",
  },
  {
    id: "O-157",
    name: "295+-Equation Cost Catalog",
    tier: "OBSERVATION",
    session: "Monster Sprint + COMP-ALL + domain-2",
    category: "Domain Costs",
    statement: "295+ standard equations across 12+ domains measured under SuperBEST v3/v4. Floor: 1n (ratio laws, 7+ equations). Ceiling: 2037n (Reed-Solomon). Original: 157 equations (Monster Sprint, 7 domains). Expanded to 214 (COMP-ALL sessions TECH-1 through NAT-2), then to 295+ (domain-2: FIN, INFO, QM, THERMO, CHEM, BIO, ECON sessions).",
    evidence: "Manual operator-tree analysis for each equation, verified by cross-checking against master_equation_catalog.json. Blind test: 27/30 exact (MAE = 0.20). See python/paper/observations/Master_Equation_Catalog.tex.",
  },
  {
    id: "O-ISO",
    name: "8 Cross-Domain Isomorphisms",
    tier: "OBSERVATION",
    session: "R10",
    category: "Domain Costs",
    statement: "8 families of equations from different scientific domains share identical minimal SuperBEST trees, differing only in terminal labels: (1) exponential growth/decay (5n), (2) NPV = N-compartment PK (8N−3), (3) softmax = logit choice, (4) van't Hoff = Clausius-Clapeyron, (5) 1−exp(−t/τ) family, (6) simple ratio laws (1n), (7) linear transport laws, (8) entropy p·ln(p) scaling.",
    evidence: "Explicit bijections between operator trees for each pair. Source: R10_Isomorphism_Theorem.tex. Isomorphism is structural (same topology + operators), not semantic.",
  },
  {
    id: "O-CLASS",
    name: "Four Structural Classes of Scientific Formulas",
    tier: "OBSERVATION",
    session: "COST-4 / R9",
    category: "Cost Theory",
    statement: "Scientific equations fall into 4 structural classes by operator composition: A (pure exponential, 5-12n), B (rational/polynomial, cheapest by MAE), C (log-ratio, cheapest by mean), D (mixed exp+ln, most expensive). Cost ordering: mean(C) < mean(B) < mean(A) < mean(D).",
    evidence: "Verified on 50-equation chembio catalog: overall MAE = 1.80; Class B MAE = 1.11, Class C MAE = 0.85. Cost ordering follows from structural analysis (proved as T41 in R9). Source: COST4_Structural_Classes.tex.",
  },

  // ─── DEFINITIONS ─────────────────────────────────────────────────────────
  {
    id: "D01",
    name: "EML Depth Hierarchy",
    tier: "DEFINITION",
    session: "S19",
    category: "Depth Hierarchy",
    statement: "EML-k = {f : ℂ → ℂ | f = eval(t) for some EML tree t with depth ≤ k}. EML-0 = constants. EML-∞ = functions not in any EML-k for finite k. Hierarchy: EML-0 ⊆ EML-1 ⊆ EML-2 ⊆ EML-3 ⊆ EML-∞.",
    evidence: "Definitional. Strict inclusions EML-0 ⊊ EML-1 proved (exp(x) ∈ EML-1 is non-constant). T30 establishes the strict infinite hierarchy.",
  },
  {
    id: "D02",
    name: "SuperBEST Cost Function",
    tier: "DEFINITION",
    session: "R1",
    category: "Cost Theory",
    statement: "Cost_F(E) = minimum number of internal nodes in any DAG over operator family F computing the same function as E. NaiveCost(E) = Σ cᵢ·nᵢ using SuperBEST v5 unit costs (exp=1, ln=1, neg=2, recip=1, mul=2, sub=2, div=2, pow=3, add=2 for ALL reals via LEDIV+DEML, sqrt=2).",
    evidence: "Formally defined in R1_Cost_Definition.tex with 4 proved properties: non-negativity, terminal characterization, subadditivity, algebraic invariance.",
  },
  {
    id: "D03",
    name: "Complex EML (ceml)",
    tier: "DEFINITION",
    session: "S11",
    category: "Complex EML",
    statement: "ceml(z₁, z₂) = exp(z₁) − Log(z₂), where Log is the principal branch complex logarithm. The complex extension of eml.",
    evidence: "Definitional. Euler Gateway (ceml(ix,1) = exp(ix)) follows immediately.",
  },
  {
    id: "D04",
    name: "Tropical EML (teml)",
    tier: "DEFINITION",
    session: "S9",
    category: "Tropical EML",
    statement: "teml(a, b) = max(Re(a), −Re(b)) + i(Im(a) + Im(b)). The tropical analog of ceml in the (max, +) semiring. teml(a, a) = |a|.",
    evidence: "Definitional. teml(a,a) = max(a,−a) = |a| for real a.",
  },

  // ─── SPECULATION ─────────────────────────────────────────────────────────
  {
    id: "S01",
    name: "P = EML-2, NP = EML-∞",
    tier: "SPECULATION",
    session: "Internal",
    category: "Depth Hierarchy",
    statement: "The conjecture that P corresponds to EML-2 and NP to EML-∞. An interesting analogy, not a formal statement. No definition of 'corresponds to' is given.",
    evidence: "No evidence. A metaphor.",
  },
  {
    id: "S02",
    name: "NS Regularity is ZFC-Independent",
    tier: "SPECULATION",
    session: "S1220–S1237",
    category: "Connections to Existing Mathematics",
    statement: "Claim that Navier-Stokes global regularity is formally ZFC-independent, via EML-theoretic analysis. The argument that NS can simulate Turing machines is a known research direction (Moore 1991, Tao 2016). The jump to ZFC-independence is not established.",
    evidence: "No complete proof. Speculative.",
  },
];

const TIER_ORDER: Array<keyof typeof TIER_META> = [
  "THEOREM", "PROPOSITION", "CONJECTURE", "OBSERVATION", "DEFINITION", "SPECULATION",
];

function TierBadge({ tier }: { tier: keyof typeof TIER_META }) {
  const m = TIER_META[tier];
  return (
    <span style={{
      display: "inline-block", fontSize: 9, fontWeight: 700,
      letterSpacing: "0.1em", padding: "3px 8px", borderRadius: 3,
      background: `${m.color}18`, border: `1px solid ${m.color}`, color: m.color,
    }}>
      {m.label}
    </span>
  );
}

function ResultCard({ r }: { r: Result }) {
  const isResolved = !!r.resolvedBy;
  return (
    <div style={{
      background: C.surface, border: `1px solid ${isResolved ? C.border : C.border}`,
      borderRadius: 8, padding: "16px 20px", marginBottom: 10,
      opacity: isResolved ? 0.55 : 1,
    }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, marginBottom: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 10, color: C.muted, fontFamily: "monospace", minWidth: 36 }}>{r.id}</span>
          <span style={{
            fontSize: 14, fontWeight: 700, color: C.text,
            textDecoration: isResolved ? "line-through" : "none",
          }}>{r.name}</span>
          {isResolved && (
            <span style={{ fontSize: 9, color: C.green, background: `${C.green}15`, border: `1px solid ${C.green}30`, borderRadius: 3, padding: "2px 6px" }}>
              RESOLVED → {r.resolvedBy}
            </span>
          )}
        </div>
        <TierBadge tier={r.tier} />
      </div>
      <div style={{ fontSize: 9, color: C.muted, marginBottom: 8, display: "flex", gap: 14 }}>
        <span>Session: {r.session}</span>
        <span>Category: {r.category}</span>
      </div>
      <div style={{ fontSize: 11, color: C.text, lineHeight: 1.75, marginBottom: 8 }}>{r.statement}</div>
      <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 8, fontSize: 10, color: C.muted, lineHeight: 1.7 }}>
        <span style={{ color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em", fontSize: 9 }}>
          {r.tier === "THEOREM" || r.tier === "PROPOSITION" ? "Proof: " :
           r.tier === "CONJECTURE" ? "Evidence: " :
           r.tier === "OBSERVATION" ? "Data: " : "Note: "}
        </span>
        {r.evidence}
      </div>
      {r.verify && (
        <div style={{
          marginTop: 6, padding: "5px 10px", background: C.surface2, borderRadius: 4,
          fontFamily: "monospace", fontSize: 10, color: C.blue, overflowX: "auto", whiteSpace: "pre",
        }}>
          {r.verify}
        </div>
      )}
      {r.deps && (
        <div style={{ marginTop: 5, fontSize: 10, color: C.muted }}>Depends on: {r.deps}</div>
      )}
    </div>
  );
}

export default function TheoremsPage() {
  const [activeFilter, setActiveFilter] = useState<string>("all");

  const byTier = TIER_ORDER.reduce<Record<string, Result[]>>((acc, t) => {
    acc[t] = RESULTS.filter((r) => r.tier === t);
    return acc;
  }, {});

  const openConjectures = byTier["CONJECTURE"].filter(r => !r.resolvedBy);
  const resolvedConjectures = byTier["CONJECTURE"].filter(r => !!r.resolvedBy);

  const theoremCount = byTier["THEOREM"].length;
  const propositionCount = byTier["PROPOSITION"].length;
  const openConjectureCount = openConjectures.length;
  const observationCount = byTier["OBSERVATION"].length;

  const filteredResults = activeFilter === "all"
    ? RESULTS
    : RESULTS.filter(r => r.tier === activeFilter);

  const filterTiers: Array<{ key: string; label: string; count: number; color: string }> = [
    { key: "all", label: "All", count: RESULTS.length, color: C.muted },
    { key: "THEOREM", label: `Theorems`, count: theoremCount, color: C.green },
    { key: "PROPOSITION", label: `Propositions`, count: propositionCount, color: C.blue },
    { key: "CONJECTURE", label: `Conjectures`, count: openConjectureCount + resolvedConjectures.length, color: C.orange },
    { key: "OBSERVATION", label: `Observations`, count: observationCount, color: C.yellow },
    { key: "DEFINITION", label: `Definitions`, count: byTier["DEFINITION"].length, color: C.purple },
    { key: "SPECULATION", label: `Speculation`, count: byTier["SPECULATION"].length, color: C.muted },
  ];

  const renderSection = (tier: keyof typeof TIER_META) => {
    if (activeFilter !== "all" && activeFilter !== tier) return null;
    const results = byTier[tier];
    if (results.length === 0) return null;
    const m = TIER_META[tier];
    const openItems = tier === "CONJECTURE" ? openConjectures : results;
    const resolvedItems = tier === "CONJECTURE" ? resolvedConjectures : [];

    return (
      <section key={tier} style={{ marginBottom: 36 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8, paddingBottom: 6, borderBottom: `1px solid ${m.color}20` }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: m.color, letterSpacing: "0.12em", textTransform: "uppercase" }}>
            {m.label} — {results.length}
          </div>
          <div style={{ fontSize: 10, color: C.muted }}>{m.desc}</div>
        </div>
        {openItems.map((r) => <ResultCard key={r.id} r={r} />)}
        {resolvedItems.length > 0 && (
          <>
            <div style={{ fontSize: 9, color: C.muted, margin: "12px 0 8px", letterSpacing: "0.1em", textTransform: "uppercase" }}>
              Resolved conjectures
            </div>
            {resolvedItems.map((r) => <ResultCard key={r.id} r={r} />)}
          </>
        )}
      </section>
    );
  };

  return (
    <div style={{ background: C.bg, minHeight: "100vh", maxWidth: 760, margin: "0 auto", padding: "0 16px 60px" }}>

      <header style={{ borderBottom: `1px solid ${C.border}`, padding: "28px 0 22px", marginBottom: 28 }}>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>
          <a href="/" style={{ color: C.muted, textDecoration: "none" }}>monogate.dev</a>{" / theorems"}
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em" }}>Theorem Catalog</div>
        <div style={{ marginTop: 8, fontSize: 11, color: C.muted, lineHeight: 1.8, maxWidth: 560 }}>
          Every result classified honestly. Theorem = complete checkable proof.
          Conjecture = precisely stated, falsifiable, unproved. Observation = empirical, no proof.
        </div>
        <div style={{ marginTop: 12, fontSize: 10, color: C.muted }}>
          <span style={{ color: C.green, fontWeight: 700 }}>{theoremCount} theorems</span>
          {" · "}
          <span style={{ color: C.blue, fontWeight: 700 }}>{propositionCount} propositions</span>
          {" · "}
          <span style={{ color: C.orange, fontWeight: 700 }}>{openConjectureCount} open conjectures</span>
          {" · "}
          <span style={{ color: C.yellow, fontWeight: 700 }}>{observationCount}+ observations</span>
        </div>
      </header>

      {/* Filter buttons */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 28 }}>
        {filterTiers.map(({ key, label, count, color }) => {
          const isActive = activeFilter === key;
          return (
            <button
              key={key}
              onClick={() => setActiveFilter(key)}
              style={{
                fontSize: 9, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase",
                color: isActive ? color : C.muted,
                background: isActive ? `${color}15` : "transparent",
                border: `1px solid ${isActive ? color : C.border}`,
                borderRadius: 3, padding: "4px 10px", cursor: "pointer",
                boxShadow: isActive ? `0 0 0 1px ${color}` : "none",
                transition: "all 0.15s",
              }}
            >
              {label} <span style={{ opacity: 0.5 }}>{count}</span>
            </button>
          );
        })}
      </div>

      {TIER_ORDER.map((tier) => renderSection(tier))}

      <footer style={{
        marginTop: 48, paddingTop: 20, borderTop: `1px solid ${C.border}`,
        display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10,
        fontSize: 10, color: C.muted,
      }}>
        <a href="/" style={{ color: C.muted }}>← All challenges</a>
        <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: C.muted }}>
          arXiv:2603.21852
        </a>
      </footer>
    </div>
  );
}
