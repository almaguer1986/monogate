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

// ─── Identity table ───────────────────────────────────────────────────────────

/** Complexity table: each identity ranked by EML tree node count and depth. */
export const IDENTITIES = [
  { name: "eˣ",  emlForm: "eml(x,1)",                          nodes: 1,  depth: 1, status: "verified" },
  { name: "ln x",emlForm: "eml(1,eml(eml(1,x),1))",            nodes: 3,  depth: 3, status: "verified" },
  { name: "e",   emlForm: "eml(1,1)",                           nodes: 1,  depth: 1, status: "verified" },
  { name: "0",   emlForm: "eml(1,eml(eml(1,1),1))",            nodes: 3,  depth: 3, status: "verified" },
  { name: "x−y", emlForm: "eml(ln(x),exp(y))",                 nodes: 5,  depth: 4, status: "verified" },
  { name: "−y",  emlForm: "two-regime (see source)",            nodes: 9,  depth: 5, status: "proven"   },
  { name: "x+y", emlForm: "eml(ln(x),eml(neg(y),1))",          nodes: 11, depth: 6, status: "proven"   },
  { name: "x×y", emlForm: "eml(add(ln(x),ln(y)),1)",           nodes: 13, depth: 7, status: "proven"   },
  { name: "x/y", emlForm: "eml(add(ln(x),neg(ln(y))),1)",      nodes: 15, depth: 8, status: "proven"   },
  { name: "xⁿ",  emlForm: "eml(mul(n,ln(x)),1)",               nodes: 15, depth: 8, status: "proven"   },
  { name: "1/x", emlForm: "eml(neg(ln(x)),1)",                 nodes: 5,  depth: 4, status: "verified"  },
];

export default { op, exp, ln, E, ZERO, NEG_ONE, sub, neg, add, mul, div, pow, recip, IDENTITIES };
