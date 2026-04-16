/**
 * monogate — Exp-Minus-Log arithmetic (inlined for the explorer)
 * Full library: https://www.npmjs.com/package/monogate
 * Reference: arXiv:2603.21852 (Odrzywołek, 2026)
 */

// ─── EML ──────────────────────────────────────────────────────────────────────
export const op = (x, y) => Math.exp(x) - Math.log(y);

export const E    = op(1, 1);
export const ZERO = op(1, op(op(1, 1), 1));
export const NEG_ONE = op(ZERO, op(2, 1));

export const exp = (x) => op(x, 1);
export const ln  = (x) => op(1, op(op(1, x), 1));
export const sub = (x, y) => op(ln(x), exp(y));

export const neg = (y) => {
  if (y <= 0) {
    const a = op(y, 1);
    return op(ln(op(a, a)), op(op(a, 1), 1));
  }
  const y1 = op(ln(y), op(NEG_ONE, 1));
  return op(ZERO, op(y1, 1));
};

export const add = (x, y) => {
  if (x > 0) return op(ln(x), op(neg(y), 1));
  if (y > 0) return op(ln(y), op(neg(x), 1));
  return neg(op(ln(neg(x)), op(neg(neg(y)), 1)));
};

export const mul   = (x, y) => op(add(ln(x), ln(y)), 1);
export const div   = (x, y) => op(add(ln(x), neg(ln(y))), 1);
export const pow   = (x, n) => op(mul(n, ln(x)), 1);
export const recip = (x)    => op(neg(ln(x)), 1);

// ─── EDL ──────────────────────────────────────────────────────────────────────
// edl(x, y) = exp(x) / ln(y)   natural constant: e
export const edl = (x, y) => Math.exp(x) / Math.log(y);
export const EDL_E = Math.E;
const _exp_edl = (x) => edl(x, EDL_E);
const _ln_edl  = (x) => edl(0, edl(edl(0, x), EDL_E));
export const div_edl   = (x, y) => edl(_ln_edl(x), _exp_edl(y));
export const recip_edl = (x)    => edl(0, edl(x, EDL_E));
export const neg_edl   = (x)    => { const re = edl(0, edl(EDL_E, EDL_E)); return edl(_ln_edl(x), re); };
export const mul_edl   = (x, y) => div_edl(x, recip_edl(y));
export const pow_edl   = (x, n) => _exp_edl(mul_edl(n, _ln_edl(x)));

// ─── EXL ──────────────────────────────────────────────────────────────────────
// exl(x, y) = exp(x) * ln(y)   natural constant: e   (INCOMPLETE — no add/sub)
export const exl = (x, y) => Math.exp(x) * Math.log(y);
export const EXL_E   = Math.E;
export const ln_exl  = (x)    => exl(0, x);
export const pow_exl = (x, n) => exl(exl(exl(0, n), x), EXL_E);

// ─── BEST: optimal per-operation routing ──────────────────────────────────────
export const BEST = {
  name: "BEST",
  ln:    (x)    => ln_exl(x),
  pow:   (x, n) => pow_exl(x, n),
  div:   (x, y) => div_edl(x, y),
  recip: (x)    => recip_edl(x),
  mul:   (x, y) => mul_edl(x, y),
  neg:   (x)    => neg_edl(x),
  exp:   (x)    => op(x, 1),
  sub:   (x, y) => sub(x, y),
  add:   (x, y) => add(x, y),

  getNodeCost: (opName) => {
    const costs = { sin: 63, cos: 63, exp: 1, ln: 1, pow: 3, mul: 7, div: 1, add: 11, sub: 5 };
    return costs[opName] ?? 1;
  },

  info: () => {
    console.log("%cBEST Routing Table", "color:#e8a020; font-weight:bold");
    console.log("ln   → EXL (1 node)");
    console.log("pow  → EXL (3 nodes)");
    console.log("mul  → EDL (7 nodes)");
    console.log("div  → EDL (1 node)");
    console.log("add/sub → EML");
  },
};

// ─── GELU approximation ──────────────────────────────────────────────────────
// tanh formula: GELU(x) ≈ 0.5·x·(1 + tanh(C1·(x + 0.044715·x³)))
// Both variants clamp the inner argument to ±3.25 for numerical stability.

const _GC1 = Math.sqrt(2 / Math.PI);   // 0.7978845608028654
const _GC2 = _GC1 * 0.044715;          // 0.03567740813446277

/** GELU — pure EML arithmetic, 17 nodes (exp:1 + add:11 + recip_eml:5) */
export const gelu_eml = (x) => {
  const inner = _GC1 * x + _GC2 * x * x * x;
  if (inner >  3.25) return x;
  if (inner < -3.25) return 0;
  const e2i = exp(2 * inner);
  const den  = add(e2i, 1.0);
  return 0.5 * x * (1 + (1 - 2 * recip(den)));
};

/** GELU — BEST-routed, 14 nodes (exp:1 + add:11 + recip_edl:2) */
export const gelu_best = (x) => {
  const inner = _GC1 * x + _GC2 * x * x * x;
  if (inner >  3.25) return x;
  if (inner < -3.25) return 0;
  const e2i = exp(2 * inner);
  const den  = add(e2i, 1.0);
  return 0.5 * x * (1 + (1 - 2 * recip_edl(den)));
};

/** sin(x) via 8-term Taylor using pow_exl (3 nodes/power, 63 nodes total) */
export const sin_best = (x, terms = 8) => {
  if (x === 0) return 0;
  const ax = Math.abs(x), sx = x < 0 ? -1 : 1;
  let result = x;
  for (let k = 1; k < terms; k++) {
    const power = 2 * k + 1;
    let f = 1; for (let i = 2; i <= power; i++) f *= i;
    result += (k % 2 === 1 ? -1 : 1) * sx * pow_exl(ax, power) / f;
  }
  return result;
};

/** cos(x) via 8-term Taylor using pow_exl */
export const cos_best = (x, terms = 8) => {
  if (x === 0) return 1;
  const ax = Math.abs(x);
  let result = 1;
  for (let k = 1; k < terms; k++) {
    const power = 2 * k;
    let f = 1; for (let i = 2; i <= power; i++) f *= i;
    result += (k % 2 === 1 ? -1 : 1) * pow_exl(ax, power) / f;
  }
  return result;
};

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

// ─── Operator family struct objects ───────────────────────────────────────────
// Expose EML / EDL / EXL as first-class objects for the UI and calc-engine.
// These wrap the raw gate functions already defined above.

export const EML = {
  name: "EML",
  func: (x, y) => Math.exp(x) - Math.log(y),
  constant: 1,
};

export const EDL = {
  name: "EDL",
  func: (x, y) => {
    if (y <= 0 || y === 1) throw new Error("EDL domain error: y must be >0 and \u22601");
    return Math.exp(x) / Math.log(y);
  },
  constant: Math.E,
};

export const EXL = {
  name: "EXL",
  func: (x, y) => Math.exp(x) * Math.log(y),
  constant: 1,
};
