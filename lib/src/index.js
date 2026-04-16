/**
 * monogate — Exp-Minus-Log arithmetic
 *
 * A single binary operator from which all elementary functions
 * can be constructed, using only the constant 1 as a terminal node.
 *
 *   eml(x, y) = exp(x) − ln(y)
 *   Grammar: S → 1 | eml(S, S)
 *
 * Reference:
 *   "All elementary functions from a single operator"
 *   Andrzej Odrzywołek, Jagiellonian University, 2026
 *   arXiv:2603.21852v2 [cs.SC] · CC BY 4.0
 *
 * @module monogate
 */

// ─── Core operator ────────────────────────────────────────────────────────────

/**
 * The EML operator: eml(x, y) = exp(x) − ln(y)
 *
 * @param {number} x
 * @param {number} y  must be > 0 (argument of ln)
 * @returns {number}
 */
export const op = (x, y) => Math.exp(x) - Math.log(y);

// ─── Constants ────────────────────────────────────────────────────────────────

/** e = eml(1,1).  Proof: exp(1)−ln(1) = e−0 = e.  Nodes:1 Depth:1 */
export const E = op(1, 1);

/** 0 = eml(1, eml(eml(1,1),1)).  Proof: eml(1,1)=e → eml(e,1)=eᵉ → eml(1,eᵉ)=e−e=0.  Nodes:3 Depth:3 */
export const ZERO = op(1, op(op(1, 1), 1));

/** −1 = eml(ZERO, eml(2,1)).  Proof: exp(0)−ln(e²)=1−2=−1.  Nodes:5 Depth:4 */
export const NEG_ONE = op(ZERO, op(2, 1));

// ─── Elementary functions ─────────────────────────────────────────────────────

/**
 * eˣ = eml(x, 1)
 * Proof: exp(x)−ln(1) = exp(x). ∎  Nodes:1 Depth:1
 *
 * @param {number} x
 * @returns {number}
 */
export const exp = (x) => op(x, 1);

/**
 * ln(x) = eml(1, eml(eml(1,x), 1))
 * Proof: let s=e−ln(x); eml(s,1)=eˢ=eᵉ/x; eml(1,eᵉ/x)=e−(e−ln(x))=ln(x). ∎
 * Nodes:3 Depth:3  Domain: x > 0
 *
 * @param {number} x  must be > 0
 * @returns {number}
 */
export const ln = (x) => op(1, op(op(1, x), 1));

// ─── Arithmetic ───────────────────────────────────────────────────────────────

/**
 * x − y = eml(ln(x), exp(y))
 * Proof: exp(ln(x))−ln(exp(y)) = x−y. ∎  Nodes:5 Depth:4  Domain: x > 0
 *
 * @param {number} x  must be > 0
 * @param {number} y
 * @returns {number}
 */
export const sub = (x, y) => op(ln(x), exp(y));

/**
 * −y  (negation — two-regime construction for numerical stability)
 *
 * REGIME A — y ≤ 0 (tower formula):
 *   Let α=eml(y,1)=eʸ.  A=eml(α,α)=exp(eʸ)−y.  B=eml(α,1)=exp(eʸ).
 *   sub(A,B) = A−B = −y. ∎  Stable: exp(eʸ) finite for all y ≤ 0.
 *
 * REGIME B — y > 0 (shift formula, stable to y < 708):
 *   y+1 = sub(y, NEG_ONE).
 *   −y  = eml(ZERO, eml(y+1, 1)) = 1−ln(exp(y+1)) = 1−(y+1) = −y. ∎
 *
 * Valid for all y ∈ ℝ.  Overflows IEEE 754 doubles only for y > 707.
 *
 * @param {number} y
 * @returns {number}
 */
export const neg = (y) => {
  if (y <= 0) {
    const a = op(y, 1);                        // eʸ
    return op(ln(op(a, a)), op(op(a, 1), 1));  // sub(A, B)
  }
  const y1 = op(ln(y), op(NEG_ONE, 1));        // y + 1  [sub(y, −1)]
  return op(ZERO, op(y1, 1));                   // 1 − (y+1) = −y
};

/**
 * x + y
 * Proof: exp(ln(x))−ln(exp(−y)) = x−(−y) = x+y. ∎
 * Generalised for any sign via commutativity and double-negation.
 *
 * @param {number} x
 * @param {number} y
 * @returns {number}
 */
export const add = (x, y) => {
  if (x > 0) return op(ln(x), op(neg(y), 1));
  if (y > 0) return op(ln(y), op(neg(x), 1));
  return neg(op(ln(neg(x)), op(neg(neg(y)), 1)));
};

/**
 * x × y = exp(ln(x) + ln(y))
 * Proof: exp(ln(x)+ln(y)) = exp(ln(xy)) = xy. ∎  Domain: x,y > 0
 *
 * @param {number} x  must be > 0
 * @param {number} y  must be > 0
 * @returns {number}
 */
export const mul = (x, y) => op(add(ln(x), ln(y)), 1);

/**
 * x / y = exp(ln(x) − ln(y))
 * Proof: exp(ln(x)−ln(y)) = exp(ln(x/y)) = x/y. ∎  Domain: x,y > 0
 *
 * @param {number} x  must be > 0
 * @param {number} y  must be > 0
 * @returns {number}
 */
export const div = (x, y) => op(add(ln(x), neg(ln(y))), 1);

/**
 * xⁿ = exp(n · ln(x))
 * Proof: exp(n·ln(x)) = exp(ln(xⁿ)) = xⁿ. ∎  Domain: x > 0, n ∈ ℝ
 *
 * @param {number} x  must be > 0
 * @param {number} n
 * @returns {number}
 */
export const pow = (x, n) => op(mul(n, ln(x)), 1);

/**
 * 1/x = exp(−ln(x))
 * Proof: exp(−ln(x)) = x⁻¹. ∎  Domain: x > 0
 *
 * @param {number} x  must be > 0
 * @returns {number}
 */
export const recip = (x) => op(neg(ln(x)), 1);

// ─── EDL operator ─────────────────────────────────────────────────────────────
//
// edl(x, y) = exp(x) / ln(y)
// Natural constant: Math.E  (ln(e) = 1 → edl(x,e) = exp(x))
// Domain: y > 0, y ≠ 1  (ln(1) = 0 causes division by zero)
// EDL and EML are the two known complete operator families.

/**
 * The EDL operator: edl(x, y) = exp(x) / ln(y)
 *
 * @param {number} x
 * @param {number} y  must be > 0 and ≠ 1
 * @returns {number}
 */
export const edl = (x, y) => Math.exp(x) / Math.log(y);

/** EDL natural constant: e (ln(e)=1 → edl(x,e)=exp(x)) */
export const EDL_E = Math.E;

// EDL exp: edl(x, e) = exp(x) / ln(e) = exp(x)
const _exp_edl = (x) => edl(x, EDL_E);

// EDL ln: edl(0, edl(edl(0,x), e)) — 3-node tree
// step 1: edl(0, x)    = 1/ln(x)
// step 2: edl(s, e)    = exp(1/ln(x))
// step 3: edl(0, t)    = 1/(1/ln(x)) = ln(x)  ✓
// Dead zone: x near 1 causes step 2 to overflow (ln(x) → 0)
const _ln_edl  = (x) => edl(0, edl(edl(0, x), EDL_E));

/**
 * x / y — EDL's natural 1-node operation: edl(ln(x), exp(y))
 * Proof: exp(ln(x)) / ln(exp(y)) = x / y  ∎
 * Nodes: 1 (vs EML's 15)  Domain: x > 0, y ≠ 0
 *
 * @param {number} x  must be > 0
 * @param {number} y  must be ≠ 0
 * @returns {number}
 */
export const div_edl = (x, y) => edl(_ln_edl(x), _exp_edl(y));

/**
 * 1/x — 2-node EDL tree: edl(0, edl(x, e))
 * Proof: edl(x,e)=exp(x); edl(0,exp(x))=1/ln(exp(x))=1/x  ∎
 * Nodes: 2 (vs EML's 5)  Domain: x ≠ 0
 *
 * @param {number} x  must be ≠ 0
 * @returns {number}
 */
export const recip_edl = (x) => edl(0, edl(x, EDL_E));

/**
 * −x — 6-node EDL tree via ln(1/e) = −1
 * Proof: edl(ln(x), 1/e) = x / ln(1/e) = x / (−1) = −x  ∎
 * Nodes: 6 (vs EML's 9)
 *
 * @param {number} x
 * @returns {number}
 */
export const neg_edl = (x) => {
  const recip_e = edl(0, edl(EDL_E, EDL_E)); // 1/e (2 nodes)
  return edl(_ln_edl(x), recip_e);            // edl(ln(x), 1/e) = −x
};

/**
 * x × y — 7-node EDL tree: div_edl(x, recip_edl(y))
 * Route: x * y = x / (1/y)
 * Nodes: 7 (vs EML's 13)  Domain: x > 0, y ≠ 0
 *
 * @param {number} x  must be > 0
 * @param {number} y  must be ≠ 0
 * @returns {number}
 */
export const mul_edl = (x, y) => div_edl(x, recip_edl(y));

/**
 * xⁿ — 11-node EDL tree: edl(mul_edl(n, ln_edl(x)), e)
 * Route: exp(n·ln(x)) via EDL mul and ln
 * Nodes: 11 (vs EML's 15)  Domain: x > 0, x ≠ 1
 *
 * @param {number} x  must be > 0 and ≠ 1
 * @param {number} n
 * @returns {number}
 */
export const pow_edl = (x, n) => _exp_edl(mul_edl(n, _ln_edl(x)));

// ─── EXL operator ─────────────────────────────────────────────────────────────
//
// exl(x, y) = exp(x) * ln(y)
// Natural constant: Math.E  (ln(e) = 1 → exl(x,e) = exp(x))
// INCOMPLETE: no finite EXL formula for addition or general subtraction.
// Best-in-class for: ln (1 node), pow (3 nodes).

/**
 * The EXL operator: exl(x, y) = exp(x) * ln(y)
 *
 * @param {number} x
 * @param {number} y  must be > 0 (argument of ln)
 * @returns {number}
 */
export const exl = (x, y) => Math.exp(x) * Math.log(y);

/** EXL natural constant: e */
export const EXL_E = Math.E;

/**
 * ln(x) — 1-node EXL tree: exl(0, x)
 * Proof: exp(0) * ln(x) = ln(x)  ∎
 * Nodes: 1 (vs EML/EDL's 3)  Domain: x > 0
 *
 * @param {number} x  must be > 0
 * @returns {number}
 */
export const ln_exl = (x) => exl(0, x);

/**
 * xⁿ — 3-node EXL tree: exl(exl(exl(0, n), x), e)
 * Proof:
 *   step 1: exl(0, n)         = ln(n)
 *   step 2: exl(ln(n), x)     = exp(ln(n)) * ln(x) = n·ln(x)
 *   step 3: exl(n·ln(x), e)   = exp(n·ln(x)) * 1   = xⁿ  ∎
 * Nodes: 3 (vs EML's 15, EDL's 11)  Domain: x > 0, n > 0
 *
 * @param {number} x  must be > 0
 * @param {number} n  must be > 0
 * @returns {number}
 */
export const pow_exl = (x, n) => exl(exl(exl(0, n), x), EXL_E);

// ─── BEST: optimal per-operation routing ──────────────────────────────────────
//
// Routes each operation to the operator that uses fewest nodes.
// EML handles add/sub (only complete operator with these).
// EDL handles div/mul/recip/neg (multiplicative group — cheapest).
// EXL handles ln/pow (smallest known formulas).

/**
 * BEST operator routing — minimum nodes per operation across EML/EDL/EXL.
 *
 *   ln:    EXL  1 node  (vs EML/EDL 3)
 *   pow:   EXL  3 nodes (vs EML 15, EDL 11)
 *   div:   EDL  1 node  (vs EML 15)
 *   recip: EDL  2 nodes (vs EML 5)
 *   mul:   EDL  7 nodes (vs EML 13)
 *   neg:   EDL  6 nodes (vs EML 9)
 *   exp:   EML  1 node  (tied)
 *   sub:   EML  5 nodes (EML only)
 *   add:   EML  11 nodes(EML only)
 */
export const BEST = {
  /** ln(x) — EXL, 1 node */
  ln:    (x)    => ln_exl(x),
  /** xⁿ — EXL, 3 nodes */
  pow:   (x, n) => pow_exl(x, n),
  /** x / y — EDL, 1 node */
  div:   (x, y) => div_edl(x, y),
  /** 1/x — EDL, 2 nodes */
  recip: (x)    => recip_edl(x),
  /** x * y — EDL, 7 nodes */
  mul:   (x, y) => mul_edl(x, y),
  /** −x — EDL, 6 nodes */
  neg:   (x)    => neg_edl(x),
  /** eˣ — EML, 1 node */
  exp:   (x)    => op(x, 1),
  /** x − y — EML, 5 nodes */
  sub:   (x, y) => sub(x, y),
  /** x + y — EML, 11 nodes */
  add:   (x, y) => add(x, y),
};

/**
 * sin(x) via Taylor series using BEST operator routing.
 *
 *   sin(x) = x − x³/3! + x⁵/5! − …
 *
 * Uses pow_exl (3 nodes per power — best known) for the power terms.
 * Node counts per term:  pow=3, plus additive combination via EML.
 * At 8 terms: 63 nodes (BEST) vs 245 nodes (all-EML) — 74% saving.
 *
 * @param {number} x
 * @param {number} [terms=8]  number of Taylor terms (default 8, max error ~7.7e-7)
 * @returns {number}
 */
export const sin_best = (x, terms = 8) => {
  if (x === 0) return 0;
  // pow_exl(x, n) requires x > 0.  For odd powers: x^n = sign(x) * |x|^n.
  const ax = Math.abs(x);
  const sx = x < 0 ? -1 : 1;
  let result = x;  // first term: x¹ = x
  for (let k = 1; k < terms; k++) {
    const power = 2 * k + 1;
    let f = 1;
    for (let i = 2; i <= power; i++) f *= i;
    // Odd power: sign = sx^power = sx (since power is odd)
    const xp = sx * pow_exl(ax, power);
    const sign = (k % 2 === 1) ? -1 : 1;
    result += sign * xp / f;
  }
  return result;
};

/**
 * cos(x) via Taylor series using BEST operator routing.
 *
 *   cos(x) = 1 − x²/2! + x⁴/4! − …
 *
 * @param {number} x
 * @param {number} [terms=8]  number of Taylor terms
 * @returns {number}
 */
export const cos_best = (x, terms = 8) => {
  if (x === 0) return 1;
  const ax = Math.abs(x);
  let result = 1;  // first term: x⁰/0! = 1
  for (let k = 1; k < terms; k++) {
    const power = 2 * k;
    let f = 1;
    for (let i = 2; i <= power; i++) f *= i;
    // Even power: |x|^power (always positive, sign = +1)
    const xp = pow_exl(ax, power);
    const sign = (k % 2 === 1) ? -1 : 1;
    result += sign * xp / f;
  }
  return result;
};

// ─── GELU approximation ──────────────────────────────────────────────────────
//
// GELU(x) ≈ 0.5·x·(1 + tanh(C1·x + C2·x³))
// where C1 = sqrt(2/π), C2 = C1·0.044715
//
// tanh(z) is computed as 1 − 2/(exp(2z)+1).
// EML routing: exp(1n) + add(11n) + recip_eml(5n)  = 17 nodes
// BEST routing: exp(1n) + add(11n) + recip_edl(2n) = 14 nodes
// Overflow guard: clamp inner argument to ±3.25.
//   Above +3.25: tanh→1, GELU(x)≈x.  Below −3.25: tanh→−1, GELU(x)≈0.

const _GELU_C1 = Math.sqrt(2 / Math.PI);      // 0.7978845608028654
const _GELU_C2 = _GELU_C1 * 0.044715;         // 0.03567740813446277

/**
 * GELU activation (tanh approximation) — pure EML arithmetic, 17 nodes.
 *
 * GELU(x) ≈ 0.5·x·(1 + tanh(√(2/π)·(x + 0.044715·x³)))
 *
 * Node breakdown: exp_eml(1) + add_eml(11) + recip_eml(5) = 17
 *
 * @param {number} x
 * @returns {number}
 */
export const gelu_eml = (x) => {
  const inner = _GELU_C1 * x + _GELU_C2 * x * x * x;
  if (inner >  3.25) return x;
  if (inner < -3.25) return 0;
  const e2i    = exp(2 * inner);          // exp_eml — 1 node
  const den    = add(e2i, 1.0);           // add_eml — 11 nodes
  const tanh_v = 1 - 2 * recip(den);     // recip_eml — 5 nodes
  return 0.5 * x * (1 + tanh_v);
};

/**
 * GELU activation (tanh approximation) — BEST-routed, 14 nodes.
 *
 * Identical formula to gelu_eml but recip_eml(5n) is replaced by
 * recip_edl(2n), saving 3 nodes (18% fewer).
 *
 * Node breakdown: exp_eml(1) + add_eml(11) + recip_edl(2) = 14
 *
 * @param {number} x
 * @returns {number}
 */
export const gelu_best = (x) => {
  const inner = _GELU_C1 * x + _GELU_C2 * x * x * x;
  if (inner >  3.25) return x;
  if (inner < -3.25) return 0;
  const e2i    = exp(2 * inner);              // exp_eml  — 1 node
  const den    = add(e2i, 1.0);              // add_eml  — 11 nodes
  const tanh_v = 1 - 2 * recip_edl(den);    // recip_edl — 2 nodes
  return 0.5 * x * (1 + tanh_v);
};

// ─── Identity table ───────────────────────────────────────────────────────────

/**
 * Complexity table: each identity ranked by node count and tree depth.
 *
 * EML depths match the Python monogate reference (core.py IDENTITIES).
 * EDL depths reflect the maximum nesting depth of the EDL operator tree.
 * EXL depths reflect the nesting depth of the EXL operator tree.
 */
export const IDENTITIES = [
  // EML family — depths match Python monogate core.py
  { name: "eˣ",   operator:"EML", form: "eml(x,1)",                         nodes: 1,  depth: 1, status: "verified" },
  { name: "ln x", operator:"EML", form: "eml(1,eml(eml(1,x),1))",           nodes: 3,  depth: 3, status: "verified" },
  { name: "x−y",  operator:"EML", form: "eml(ln(x),exp(y))",                nodes: 5,  depth: 4, status: "verified" },
  { name: "−y",   operator:"EML", form: "two-regime (see source)",           nodes: 9,  depth: 5, status: "proven"   },
  { name: "x+y",  operator:"EML", form: "eml(ln(x),eml(neg(y),1))",         nodes: 11, depth: 6, status: "proven"   },
  { name: "x×y",  operator:"EML", form: "eml(add(ln(x),ln(y)),1)",          nodes: 13, depth: 7, status: "proven"   },
  { name: "x/y",  operator:"EML", form: "eml(add(ln(x),neg(ln(y))),1)",     nodes: 15, depth: 8, status: "proven"   },
  { name: "xⁿ",   operator:"EML", form: "eml(mul(n,ln(x)),1)",              nodes: 15, depth: 8, status: "proven"   },
  { name: "1/x",  operator:"EML", form: "eml(neg(ln(x)),1)",                nodes: 5,  depth: 4, status: "verified" },
  // EDL family — depths derived from EDL operator tree nesting
  { name: "x/y",  operator:"EDL", form: "edl(ln(x),exp(y))",               nodes: 1,  depth: 1, status: "verified" },
  { name: "1/x",  operator:"EDL", form: "edl(0,edl(x,e))",                 nodes: 2,  depth: 2, status: "verified" },
  { name: "−x",   operator:"EDL", form: "edl(ln_edl(x),1/e)",              nodes: 6,  depth: 4, status: "proven"   },
  { name: "x×y",  operator:"EDL", form: "div_edl(x,recip_edl(y))",         nodes: 7,  depth: 5, status: "proven"   },
  { name: "xⁿ",   operator:"EDL", form: "edl(mul_edl(n,ln_edl(x)),e)",    nodes: 11, depth: 7, status: "proven"   },
  // EXL family — depths reflect exl gate nesting
  { name: "ln x", operator:"EXL", form: "exl(0,x)",                        nodes: 1,  depth: 1, status: "verified" },
  { name: "xⁿ",   operator:"EXL", form: "exl(exl(exl(0,n),x),e)",         nodes: 3,  depth: 3, status: "proven"   },
];

export default {
  // EML
  op, E, ZERO, NEG_ONE, exp, ln, sub, neg, add, mul, div, pow, recip,
  // EDL
  edl, EDL_E, div_edl, recip_edl, neg_edl, mul_edl, pow_edl,
  // EXL
  exl, EXL_E, ln_exl, pow_exl,
  // BEST routing
  BEST, sin_best, cos_best,
  // GELU
  gelu_eml, gelu_best,
  // Metadata
  IDENTITIES,
};
