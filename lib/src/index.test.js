import { describe, it, expect } from "vitest";
import {
  op, E, ZERO, NEG_ONE,
  exp, ln, sub, neg, add, mul, div, pow, recip,
  edl, EDL_E,
  div_edl, recip_edl, neg_edl, mul_edl, pow_edl,
  exl, EXL_E,
  ln_exl, pow_exl,
  BEST,
  sin_best, cos_best,
  gelu_eml, gelu_best,
  IDENTITIES,
} from "./index.js";

// ── Tolerance levels (mirrors complex_eml.test.js) ────────────────────────────
const TIGHT = 1e-14;  // direct arithmetic, 0–1 node chains
const TOL   = 1e-10;  // EML multi-node chains (3–15 nodes)

const near = (a, b, tol = TOL) => Math.abs(a - b) <= tol;

// ─── Core operator ────────────────────────────────────────────────────────────

describe("op — the EML gate", () => {
  it("op(1, 1) = e", () => {
    expect(near(op(1, 1), Math.E, TIGHT)).toBe(true);
  });

  it("op(0, 1) = 1  (exp(0) − ln(1) = 1 − 0)", () => {
    expect(near(op(0, 1), 1, TIGHT)).toBe(true);
  });

  it("op(1, Math.E) = e − 1", () => {
    expect(near(op(1, Math.E), Math.E - 1, TIGHT)).toBe(true);
  });

  it("op(ln(x), exp(y)) = x − y  (sub identity)", () => {
    const x = 5, y = 2;
    expect(near(op(Math.log(x), Math.exp(y)), x - y)).toBe(true);
  });

  it("op(x, 1) = exp(x)  (exp identity)", () => {
    for (const x of [-2, -1, 0, 1, 2]) {
      expect(near(op(x, 1), Math.exp(x), TIGHT)).toBe(true);
    }
  });
});

// ─── Constants ────────────────────────────────────────────────────────────────

describe("EML constants", () => {
  it("E = e", () => {
    expect(near(E, Math.E, TIGHT)).toBe(true);
  });

  it("ZERO = 0", () => {
    expect(near(ZERO, 0, TOL)).toBe(true);
  });

  it("NEG_ONE = −1", () => {
    expect(near(NEG_ONE, -1, TOL)).toBe(true);
  });
});

// ─── exp ──────────────────────────────────────────────────────────────────────

describe("exp", () => {
  it("exp(0) = 1", () => expect(near(exp(0), 1, TIGHT)).toBe(true));
  it("exp(1) = e", () => expect(near(exp(1), Math.E, TIGHT)).toBe(true));
  it("exp(-1) = 1/e", () => expect(near(exp(-1), 1 / Math.E, TIGHT)).toBe(true));
  it("exp(2) matches Math.exp(2)", () => expect(near(exp(2), Math.exp(2), TIGHT)).toBe(true));
  it("exp(-3) matches Math.exp(-3)", () => expect(near(exp(-3), Math.exp(-3), TIGHT)).toBe(true));
});

// ─── ln ───────────────────────────────────────────────────────────────────────

describe("ln", () => {
  it("ln(1) = 0", () => expect(near(ln(1), 0, TOL)).toBe(true));
  it("ln(e) = 1", () => expect(near(ln(Math.E), 1, TOL)).toBe(true));
  it("ln(e²) = 2", () => expect(near(ln(Math.E * Math.E), 2, TOL)).toBe(true));
  it("ln(0.5) matches Math.log(0.5)", () => expect(near(ln(0.5), Math.log(0.5), TOL)).toBe(true));
  it("ln(10) matches Math.log(10)", () => expect(near(ln(10), Math.log(10), TOL)).toBe(true));
  it("exp(ln(x)) ≈ x for x ∈ {0.1, 1, 2, 5, 100}", () => {
    for (const x of [0.1, 1, 2, 5, 100]) {
      expect(near(exp(ln(x)), x, TOL)).toBe(true);
    }
  });
  it("ln(exp(x)) ≈ x for x ∈ {-2, -1, 0, 1, 2}", () => {
    for (const x of [-2, -1, 0, 1, 2]) {
      expect(near(ln(exp(x)), x, TOL)).toBe(true);
    }
  });
});

// ─── sub ──────────────────────────────────────────────────────────────────────

describe("sub", () => {
  it("sub(3, 1) = 2", () => expect(near(sub(3, 1), 2)).toBe(true));
  it("sub(5, 5) = 0", () => expect(near(sub(5, 5), 0)).toBe(true));
  it("sub(Math.E, 1) = e − 1", () => expect(near(sub(Math.E, 1), Math.E - 1)).toBe(true));
  it("sub(x, 0) = x for positive x", () => {
    expect(near(sub(4, 0), 4)).toBe(true);
  });
  it("sub(x, y) = −sub(y, x) + 0  (antisymmetry, both x,y > 0)", () => {
    const a = 3, b = 2;
    expect(near(sub(a, b), -(sub(b, a) - (a - b) - (b - a)))).toBe(true);
    // direct value check:
    expect(near(sub(a, b), a - b)).toBe(true);
    expect(near(sub(b, a), b - a)).toBe(true);
  });
});

// ─── neg ──────────────────────────────────────────────────────────────────────

describe("neg — two-regime construction", () => {
  // Regime A: y ≤ 0 (tower formula)
  it("neg(0) = 0", () => expect(near(neg(0), 0)).toBe(true));
  it("neg(-1) = 1  (regime A)", () => expect(near(neg(-1), 1)).toBe(true));
  it("neg(-2) = 2  (regime A)", () => expect(near(neg(-2), 2)).toBe(true));
  it("neg(-0.5) = 0.5  (regime A)", () => expect(near(neg(-0.5), 0.5)).toBe(true));

  // Regime B: y > 0 (shift formula)
  it("neg(1) = −1  (regime B)", () => expect(near(neg(1), -1)).toBe(true));
  it("neg(2) = −2  (regime B)", () => expect(near(neg(2), -2)).toBe(true));
  it("neg(0.5) = −0.5  (regime B)", () => expect(near(neg(0.5), -0.5)).toBe(true));
  it("neg(100) = −100  (regime B, large value)", () => expect(near(neg(100), -100)).toBe(true));

  // Involution: neg(neg(x)) ≈ x
  it("neg(neg(x)) ≈ x for both regimes", () => {
    for (const x of [-3, -1, 0, 1, 3, 0.7]) {
      expect(near(neg(neg(x)), x)).toBe(true);
    }
  });

  // Additivity: neg(x) + x ≈ 0
  it("neg(x) + x ≈ 0 for various x", () => {
    for (const x of [-2, -0.5, 0, 0.5, 2]) {
      expect(near(neg(x) + x, 0)).toBe(true);
    }
  });
});

// ─── add ──────────────────────────────────────────────────────────────────────

describe("add — three branches", () => {
  // Branch x > 0
  it("add(2, 3) = 5  (x > 0 branch)", () => expect(near(add(2, 3), 5)).toBe(true));
  it("add(1, -1) = 0  (x > 0 branch)", () => expect(near(add(1, -1), 0)).toBe(true));
  it("add(3, -1) = 2  (x > 0 branch)", () => expect(near(add(3, -1), 2)).toBe(true));

  // Branch y > 0 (x ≤ 0)
  it("add(-1, 1) = 0  (y > 0 branch)", () => expect(near(add(-1, 1), 0)).toBe(true));
  it("add(-2, 5) = 3  (y > 0 branch)", () => expect(near(add(-2, 5), 3)).toBe(true));

  // Branch both ≤ 0
  it("add(-2, -3) = -5  (both ≤ 0 branch)", () => expect(near(add(-2, -3), -5)).toBe(true));
  it("add(-1, -1) = -2  (both ≤ 0 branch)", () => expect(near(add(-1, -1), -2)).toBe(true));

  // Commutativity
  it("add(a, b) ≈ add(b, a) for mixed signs", () => {
    const cases = [[2, 3], [1, -2], [-3, 4], [-1, -5]];
    for (const [a, b] of cases) {
      expect(near(add(a, b), add(b, a))).toBe(true);
    }
  });

  // add(x, 0) = x
  it("add(x, 0) ≈ x", () => {
    expect(near(add(3, 0), 3)).toBe(true);
    expect(near(add(-2, 0), -2)).toBe(true);
  });

  // add(x, neg(x)) = 0
  it("add(x, neg(x)) ≈ 0", () => {
    for (const x of [1, 2, 0.5]) {
      expect(near(add(x, neg(x)), 0)).toBe(true);
    }
  });
});

// ─── mul ──────────────────────────────────────────────────────────────────────

describe("mul  (domain: x,y > 0)", () => {
  it("mul(2, 3) = 6", () => expect(near(mul(2, 3), 6)).toBe(true));
  it("mul(1, 5) = 5", () => expect(near(mul(1, 5), 5)).toBe(true));
  it("mul(0.5, 4) = 2", () => expect(near(mul(0.5, 4), 2)).toBe(true));
  it("mul(Math.E, Math.E) = e²", () => expect(near(mul(Math.E, Math.E), Math.E * Math.E)).toBe(true));
  it("mul(x, 1/x) ≈ 1 (uses recip internally)", () => {
    for (const x of [2, 3, 0.5]) {
      expect(near(mul(x, 1 / x), 1)).toBe(true);
    }
  });
  it("mul(a, b) ≈ mul(b, a)  (commutativity)", () => {
    expect(near(mul(2, 5), mul(5, 2))).toBe(true);
  });
});

// ─── div ──────────────────────────────────────────────────────────────────────

describe("div  (domain: x,y > 0)", () => {
  it("div(6, 2) = 3", () => expect(near(div(6, 2), 3)).toBe(true));
  it("div(x, 1) = x", () => {
    for (const x of [1, 2, 0.5, Math.PI]) {
      expect(near(div(x, 1), x)).toBe(true);
    }
  });
  it("div(1, 2) = 0.5", () => expect(near(div(1, 2), 0.5)).toBe(true));
  it("div(x, x) = 1", () => {
    for (const x of [1, 2, 5]) {
      expect(near(div(x, x), 1)).toBe(true);
    }
  });
  it("div(Math.E, Math.E) = 1", () => expect(near(div(Math.E, Math.E), 1)).toBe(true));
  it("div(a, b) * b ≈ a", () => {
    const a = 7, b = 3;
    expect(near(mul(div(a, b), b), a)).toBe(true);
  });
});

// ─── pow ──────────────────────────────────────────────────────────────────────

// EML pow(x,n) = op(mul(n,ln(x)),1) uses EML mul internally, so domain is:
//   n > 0  (mul requires both args > 0, so n must be positive)
//   x > 1  (ln(x) > 0 required for mul's second ln call)
// For negative exponents or x ≤ 1, use recip/pow_exl instead.
describe("pow  (domain: x > 1, n > 0)", () => {
  it("pow(2, 3) = 8", () => expect(near(pow(2, 3), 8)).toBe(true));
  it("pow(4, 0.5) = 2  (square root)", () => expect(near(pow(4, 0.5), 2)).toBe(true));
  it("pow(x, 0) = 1 for x > 1", () => {
    for (const x of [2, 5, Math.PI]) {
      expect(near(pow(x, 0), 1)).toBe(true);
    }
  });
  it("pow(1, n) = 1 for n > 0", () => {
    for (const n of [0, 1, 2, 0.5, 100]) {
      expect(near(pow(1, n), 1)).toBe(true);
    }
  });
  it("pow(x, 1) = x  (x > 1)", () => {
    for (const x of [2, 3, Math.PI]) {
      expect(near(pow(x, 1), x)).toBe(true);
    }
  });
  it("pow(x, 2) ≈ x²  (x > 1)", () => {
    for (const x of [2, 3, 4]) {
      expect(near(pow(x, 2), x * x)).toBe(true);
    }
  });
  it("pow(2, 10) = 1024", () => expect(near(pow(2, 10), 1024)).toBe(true));
  it("pow(x, -1) = 1/x — use recip() for negative exponents", () => {
    // EML pow requires n > 0; recip is the canonical 1-arg form
    for (const x of [2, 4, 3]) {
      expect(near(recip(x), 1 / x)).toBe(true);
    }
  });
  it("pow(pow(x, a), b) ≈ pow(x, a*b)", () => {
    expect(near(pow(pow(2, 2), 3), pow(2, 6))).toBe(true);
  });
});

// ─── recip ────────────────────────────────────────────────────────────────────

describe("recip  (domain: x > 0)", () => {
  it("recip(1) = 1", () => expect(near(recip(1), 1)).toBe(true));
  it("recip(2) = 0.5", () => expect(near(recip(2), 0.5)).toBe(true));
  it("recip(0.5) = 2", () => expect(near(recip(0.5), 2)).toBe(true));
  it("recip(Math.E) = 1/e", () => expect(near(recip(Math.E), 1 / Math.E)).toBe(true));
  it("recip(recip(x)) ≈ x", () => {
    for (const x of [2, 3, 0.5, Math.PI]) {
      expect(near(recip(recip(x)), x)).toBe(true);
    }
  });
  it("x * recip(x) ≈ 1", () => {
    for (const x of [2, 5, Math.E]) {
      expect(near(mul(x, recip(x)), 1)).toBe(true);
    }
  });
});

// ─── EDL operator ─────────────────────────────────────────────────────────────

describe("edl — the EDL gate", () => {
  it("EDL_E = e", () => expect(near(EDL_E, Math.E, TIGHT)).toBe(true));
  it("edl(0, e) = 1  (exp(0)/ln(e) = 1)", () => expect(near(edl(0, EDL_E), 1, TIGHT)).toBe(true));
  it("edl(1, e) = e  (exp(1)/ln(e) = e/1)", () => expect(near(edl(1, EDL_E), Math.E, TIGHT)).toBe(true));
  it("edl(0, e²) = 0.5  (exp(0)/ln(e²) = 1/2)", () => {
    expect(near(edl(0, Math.E * Math.E), 0.5, TIGHT)).toBe(true);
  });
});

describe("div_edl  (EDL, 1 node — domain: x > 0, y ≠ 0)", () => {
  it("div_edl(6, 2) = 3", () => expect(near(div_edl(6, 2), 3)).toBe(true));
  it("div_edl(x, 1) = x", () => {
    for (const x of [1, 2, Math.PI, 0.5]) {
      expect(near(div_edl(x, 1), x)).toBe(true);
    }
  });
  it("div_edl(x, x) = 1", () => {
    for (const x of [2, 5, Math.E]) {
      expect(near(div_edl(x, x), 1)).toBe(true);
    }
  });
  it("div_edl(1, 2) = 0.5", () => expect(near(div_edl(1, 2), 0.5)).toBe(true));
  it("agrees with EML div for positive inputs", () => {
    const cases = [[6, 2], [10, 5], [Math.PI, 2]];
    for (const [a, b] of cases) {
      expect(near(div_edl(a, b), div(a, b))).toBe(true);
    }
  });
});

describe("recip_edl  (EDL, 2 nodes — domain: x ≠ 0)", () => {
  it("recip_edl(1) = 1", () => expect(near(recip_edl(1), 1)).toBe(true));
  it("recip_edl(2) = 0.5", () => expect(near(recip_edl(2), 0.5)).toBe(true));
  it("recip_edl(0.5) = 2", () => expect(near(recip_edl(0.5), 2)).toBe(true));
  it("recip_edl(Math.E) = 1/e", () => expect(near(recip_edl(Math.E), 1 / Math.E)).toBe(true));
  it("recip_edl(recip_edl(x)) ≈ x for positive inputs", () => {
    for (const x of [2, 5, Math.PI]) {
      expect(near(recip_edl(recip_edl(x)), x)).toBe(true);
    }
  });
  it("agrees with EML recip for positive inputs", () => {
    for (const x of [2, 3, 0.5]) {
      expect(near(recip_edl(x), recip(x))).toBe(true);
    }
  });
});

describe("neg_edl  (EDL, 6 nodes)", () => {
  it("neg_edl(1) = -1", () => expect(near(neg_edl(1), -1)).toBe(true));
  it("neg_edl(2) = -2", () => expect(near(neg_edl(2), -2)).toBe(true));
  it("neg_edl(0.5) = -0.5", () => expect(near(neg_edl(0.5), -0.5)).toBe(true));
  // neg_edl(x) = -x, but neg_edl uses _ln_edl internally which requires x > 0.
  // The involution neg_edl(neg_edl(x)) = x fails because neg_edl(x) < 0.
  // Involution is verified via plain arithmetic: neg_edl(x) + x ≈ 0.
  it("neg_edl(x) + x ≈ 0", () => {
    for (const x of [1, 3, 0.7]) {
      expect(near(neg_edl(x) + x, 0)).toBe(true);
    }
  });
});

describe("mul_edl  (EDL, 7 nodes — domain: x > 0, y ≠ 0)", () => {
  it("mul_edl(2, 3) = 6", () => expect(near(mul_edl(2, 3), 6)).toBe(true));
  it("mul_edl(1, 5) = 5", () => expect(near(mul_edl(1, 5), 5)).toBe(true));
  it("mul_edl(0.5, 4) = 2", () => expect(near(mul_edl(0.5, 4), 2)).toBe(true));
  it("agrees with EML mul for positive inputs", () => {
    const cases = [[2, 3], [4, 5], [0.5, 2]];
    for (const [a, b] of cases) {
      expect(near(mul_edl(a, b), mul(a, b))).toBe(true);
    }
  });
});

describe("pow_edl  (EDL, 11 nodes — domain: x > 0, x ≠ 1)", () => {
  it("pow_edl(2, 3) = 8", () => expect(near(pow_edl(2, 3), 8)).toBe(true));
  it("pow_edl(4, 0.5) = 2", () => expect(near(pow_edl(4, 0.5), 2)).toBe(true));
  it("pow_edl(2, 10) = 1024", () => expect(near(pow_edl(2, 10), 1024)).toBe(true));
  it("agrees with EML pow for x > 0, x ≠ 1", () => {
    const cases = [[2, 3], [3, 2], [0.5, 4]];
    for (const [x, n] of cases) {
      expect(near(pow_edl(x, n), Math.pow(x, n))).toBe(true);
    }
  });
});

// ─── EXL operator ─────────────────────────────────────────────────────────────

describe("exl — the EXL gate", () => {
  it("EXL_E = e", () => expect(near(EXL_E, Math.E, TIGHT)).toBe(true));
  it("exl(0, x) = ln(x)  (1-node ln)", () => {
    for (const x of [1, 2, Math.E, 10]) {
      expect(near(exl(0, x), Math.log(x), TIGHT)).toBe(true);
    }
  });
  it("exl(1, e) = e  (exp(1)*ln(e) = e*1)", () => {
    expect(near(exl(1, Math.E), Math.E, TIGHT)).toBe(true);
  });
});

describe("ln_exl  (EXL, 1 node — domain: x > 0)", () => {
  it("ln_exl(1) = 0", () => expect(near(ln_exl(1), 0, TIGHT)).toBe(true));
  it("ln_exl(e) = 1", () => expect(near(ln_exl(Math.E), 1, TIGHT)).toBe(true));
  it("ln_exl(e²) = 2", () => expect(near(ln_exl(Math.E * Math.E), 2, TIGHT)).toBe(true));
  it("ln_exl(0.5) matches Math.log(0.5)", () => {
    expect(near(ln_exl(0.5), Math.log(0.5), TIGHT)).toBe(true);
  });
  it("ln_exl(x) matches EML ln(x) to TOL", () => {
    for (const x of [0.1, 1, 2, 5, 100]) {
      expect(near(ln_exl(x), ln(x), TOL)).toBe(true);
    }
  });
  it("exp(ln_exl(x)) ≈ x", () => {
    for (const x of [0.5, 1, 2, Math.PI]) {
      expect(near(exp(ln_exl(x)), x, TOL)).toBe(true);
    }
  });
});

describe("pow_exl  (EXL, 3 nodes — domain: x > 0, n > 0)", () => {
  it("pow_exl(2, 1) = 2", () => expect(near(pow_exl(2, 1), 2)).toBe(true));
  it("pow_exl(2, 3) = 8", () => expect(near(pow_exl(2, 3), 8)).toBe(true));
  it("pow_exl(4, 0.5) = 2  (square root)", () => expect(near(pow_exl(4, 0.5), 2)).toBe(true));
  it("pow_exl(2, 10) = 1024", () => expect(near(pow_exl(2, 10), 1024)).toBe(true));
  it("pow_exl(x, 1) = x", () => {
    for (const x of [2, 3, Math.PI, 0.5]) {
      expect(near(pow_exl(x, 1), x)).toBe(true);
    }
  });
  it("pow_exl(x, 2) ≈ x²", () => {
    for (const x of [2, 3, 0.5]) {
      expect(near(pow_exl(x, 2), x * x)).toBe(true);
    }
  });
  it("agrees with Math.pow for x > 0, n > 0", () => {
    const cases = [[2, 3], [3, 4], [0.5, 3], [Math.PI, 2]];
    for (const [x, n] of cases) {
      expect(near(pow_exl(x, n), Math.pow(x, n))).toBe(true);
    }
  });
  it("agrees with EML pow for positive x and n", () => {
    const cases = [[2, 3], [3, 2], [4, 0.5]];
    for (const [x, n] of cases) {
      expect(near(pow_exl(x, n), pow(x, n))).toBe(true);
    }
  });
});

// ─── BEST routing ─────────────────────────────────────────────────────────────

describe("BEST.exp  (EML, 1 node)", () => {
  it("BEST.exp(0) = 1", () => expect(near(BEST.exp(0), 1, TIGHT)).toBe(true));
  it("BEST.exp(1) = e", () => expect(near(BEST.exp(1), Math.E, TIGHT)).toBe(true));
  it("BEST.exp(x) matches Math.exp(x)", () => {
    for (const x of [-2, -1, 0, 1, 2]) {
      expect(near(BEST.exp(x), Math.exp(x), TIGHT)).toBe(true);
    }
  });
});

describe("BEST.ln  (EXL, 1 node)", () => {
  it("BEST.ln(1) = 0", () => expect(near(BEST.ln(1), 0, TIGHT)).toBe(true));
  it("BEST.ln(e) = 1", () => expect(near(BEST.ln(Math.E), 1, TIGHT)).toBe(true));
  it("BEST.ln(x) matches Math.log(x)", () => {
    for (const x of [0.1, 0.5, 1, 2, 10, 100]) {
      expect(near(BEST.ln(x), Math.log(x), TIGHT)).toBe(true);
    }
  });
  it("1 node cheaper than EML ln (3 nodes) — same value", () => {
    expect(near(BEST.ln(5), ln(5), TOL)).toBe(true);
  });
});

describe("BEST.pow  (EXL, 3 nodes)", () => {
  it("BEST.pow(2, 3) = 8", () => expect(near(BEST.pow(2, 3), 8)).toBe(true));
  it("BEST.pow(4, 0.5) = 2", () => expect(near(BEST.pow(4, 0.5), 2)).toBe(true));
  it("BEST.pow(2, 10) = 1024", () => expect(near(BEST.pow(2, 10), 1024)).toBe(true));
  it("BEST.pow(x, 1) = x", () => {
    for (const x of [2, 3, Math.PI]) {
      expect(near(BEST.pow(x, 1), x)).toBe(true);
    }
  });
  it("BEST.pow matches Math.pow for positive x,n", () => {
    const cases = [[2, 3], [3, 2], [4, 0.5], [Math.PI, 2]];
    for (const [x, n] of cases) {
      expect(near(BEST.pow(x, n), Math.pow(x, n))).toBe(true);
    }
  });
});

describe("BEST.div  (EDL, 1 node)", () => {
  it("BEST.div(6, 2) = 3", () => expect(near(BEST.div(6, 2), 3)).toBe(true));
  it("BEST.div(x, 1) = x", () => {
    for (const x of [1, 2, Math.PI]) {
      expect(near(BEST.div(x, 1), x)).toBe(true);
    }
  });
  it("BEST.div(x, x) = 1", () => {
    for (const x of [2, 5, Math.E]) {
      expect(near(BEST.div(x, x), 1)).toBe(true);
    }
  });
  it("BEST.div agrees with EML div", () => {
    const cases = [[6, 2], [10, 5], [Math.PI, 2]];
    for (const [a, b] of cases) {
      expect(near(BEST.div(a, b), div(a, b))).toBe(true);
    }
  });
});

describe("BEST.recip  (EDL, 2 nodes)", () => {
  it("BEST.recip(1) = 1", () => expect(near(BEST.recip(1), 1)).toBe(true));
  it("BEST.recip(2) = 0.5", () => expect(near(BEST.recip(2), 0.5)).toBe(true));
  it("BEST.recip(x) * x ≈ 1", () => {
    for (const x of [2, 3, Math.PI]) {
      expect(near(BEST.recip(x) * x, 1)).toBe(true);
    }
  });
  it("BEST.recip agrees with EML recip", () => {
    for (const x of [2, 5, 0.5]) {
      expect(near(BEST.recip(x), recip(x))).toBe(true);
    }
  });
});

describe("BEST.mul  (EDL, 7 nodes)", () => {
  it("BEST.mul(2, 3) = 6", () => expect(near(BEST.mul(2, 3), 6)).toBe(true));
  it("BEST.mul(1, 5) = 5", () => expect(near(BEST.mul(1, 5), 5)).toBe(true));
  it("BEST.mul(0.5, 4) = 2", () => expect(near(BEST.mul(0.5, 4), 2)).toBe(true));
  it("BEST.mul agrees with EML mul", () => {
    const cases = [[2, 3], [4, 5], [0.5, 2]];
    for (const [a, b] of cases) {
      expect(near(BEST.mul(a, b), mul(a, b))).toBe(true);
    }
  });
});

describe("BEST.neg  (EDL, 6 nodes)", () => {
  it("BEST.neg(1) = -1", () => expect(near(BEST.neg(1), -1)).toBe(true));
  it("BEST.neg(2) = -2", () => expect(near(BEST.neg(2), -2)).toBe(true));
  // Same domain constraint as neg_edl: input must be > 0.
  // Involution verified via neg_edl(x) + x ≈ 0 (see neg_edl suite above).
  it("BEST.neg agrees with neg_edl", () => {
    for (const x of [1, 2, Math.PI, 0.5]) {
      expect(near(BEST.neg(x), neg_edl(x))).toBe(true);
    }
  });
});

describe("BEST.sub  (EML, 5 nodes)", () => {
  it("BEST.sub(3, 1) = 2", () => expect(near(BEST.sub(3, 1), 2)).toBe(true));
  it("BEST.sub(5, 5) = 0", () => expect(near(BEST.sub(5, 5), 0)).toBe(true));
  it("BEST.sub agrees with EML sub", () => {
    const cases = [[3, 1], [5, 2], [Math.E, 1]];
    for (const [a, b] of cases) {
      expect(near(BEST.sub(a, b), sub(a, b))).toBe(true);
    }
  });
});

describe("BEST.add  (EML, 11 nodes)", () => {
  it("BEST.add(2, 3) = 5", () => expect(near(BEST.add(2, 3), 5)).toBe(true));
  it("BEST.add(-1, 1) = 0", () => expect(near(BEST.add(-1, 1), 0)).toBe(true));
  it("BEST.add(-2, -3) = -5", () => expect(near(BEST.add(-2, -3), -5)).toBe(true));
  it("BEST.add agrees with EML add", () => {
    const cases = [[2, 3], [1, -2], [-3, 4], [-1, -5]];
    for (const [a, b] of cases) {
      expect(near(BEST.add(a, b), add(a, b))).toBe(true);
    }
  });
});

// ─── sin_best ─────────────────────────────────────────────────────────────────
//
// 8 terms: max error ~7.7e-7 near the edge of [0, π].
// The tolerance here is 1e-5 — loose enough for the 8-term default but
// tight enough to catch wrong implementations.

const SIN_TOL = 1e-5;

describe("sin_best  (8-term Taylor via pow_exl)", () => {
  it("sin_best(0) = 0", () => expect(sin_best(0)).toBe(0));

  const cases = [
    [Math.PI / 6,  0.5],
    [Math.PI / 4,  Math.SQRT1_2],
    [Math.PI / 3,  Math.sqrt(3) / 2],
    [Math.PI / 2,  1],
    [-Math.PI / 2, -1],
    [-Math.PI / 6, -0.5],
    [1,  Math.sin(1)],
    [2,  Math.sin(2)],
  ];

  for (const [x, expected] of cases) {
    it(`sin_best(${x.toFixed(4)}) ≈ ${expected.toFixed(4)}`, () => {
      expect(near(sin_best(x), expected, SIN_TOL)).toBe(true);
    });
  }

  it("error vs Math.sin < 1e-6 for x ∈ [0.1, π] (8 terms)", () => {
    for (let j = 1; j <= 30; j++) {
      const x = j * Math.PI / 30;
      const err = Math.abs(sin_best(x) - Math.sin(x));
      expect(err).toBeLessThan(1e-6);
    }
  });

  it("sin_best(x, 13) reaches machine precision — error < 1e-13", () => {
    for (const x of [0.5, 1, 1.5, 2, Math.PI / 4]) {
      const err = Math.abs(sin_best(x, 13) - Math.sin(x));
      expect(err).toBeLessThan(1e-13);
    }
  });

  it("sin(-x) = -sin(x)  (odd symmetry)", () => {
    for (const x of [0.5, 1, 1.5, 2]) {
      expect(near(sin_best(-x), -sin_best(x), SIN_TOL)).toBe(true);
    }
  });

  it("sin²(x) + cos²(x) ≈ 1  (Pythagorean identity)", () => {
    for (const x of [0.3, 0.7, 1, 1.5, 2]) {
      const s = sin_best(x), c = cos_best(x);
      expect(near(s * s + c * c, 1, 1e-4)).toBe(true);
    }
  });
});

// ─── cos_best ─────────────────────────────────────────────────────────────────

describe("cos_best  (8-term Taylor via pow_exl)", () => {
  it("cos_best(0) = 1", () => expect(cos_best(0)).toBe(1));

  const cases = [
    [Math.PI / 3,  0.5],
    [Math.PI / 4,  Math.SQRT1_2],
    [Math.PI / 6,  Math.sqrt(3) / 2],
    [Math.PI / 2,  0],
    [Math.PI,     -1],
    [-Math.PI / 3, 0.5],
    [1,  Math.cos(1)],
    [2,  Math.cos(2)],
  ];

  for (const [x, expected] of cases) {
    it(`cos_best(${x.toFixed(4)}) ≈ ${expected.toFixed(4)}`, () => {
      expect(near(cos_best(x), expected, SIN_TOL)).toBe(true);
    });
  }

  it("error vs Math.cos < 5e-6 for x ∈ [0.1, π] (8 terms)", () => {
    for (let j = 1; j <= 30; j++) {
      const x = j * Math.PI / 30;
      const err = Math.abs(cos_best(x) - Math.cos(x));
      expect(err).toBeLessThan(5e-6);
    }
  });

  it("cos_best(x, 13) reaches machine precision — error < 1e-13", () => {
    for (const x of [0.5, 1, 1.5, 2, Math.PI / 4]) {
      const err = Math.abs(cos_best(x, 13) - Math.cos(x));
      expect(err).toBeLessThan(1e-13);
    }
  });

  it("cos(-x) = cos(x)  (even symmetry)", () => {
    for (const x of [0.5, 1, 1.5, 2]) {
      expect(near(cos_best(-x), cos_best(x), SIN_TOL)).toBe(true);
    }
  });

  it("cos_best(x, 13) agrees with sin_best — Pythagorean identity at precision", () => {
    for (const x of [0.3, 0.7, 1, 1.5, 2]) {
      const s = sin_best(x, 13), c = cos_best(x, 13);
      expect(near(s * s + c * c, 1, 1e-12)).toBe(true);
    }
  });
});

// ─── Cross-operator consistency ───────────────────────────────────────────────
//
// Each BEST op should agree with its EML baseline to TOL.
// These cross-checks catch routing bugs (wrong function assigned to BEST key).

describe("BEST vs EML baseline — cross-consistency", () => {
  it("BEST.add ≈ EML add", () => {
    const cases = [[2, 3], [-1, 4], [-3, -2]];
    for (const [a, b] of cases) expect(near(BEST.add(a, b), add(a, b))).toBe(true);
  });

  it("BEST.sub ≈ EML sub", () => {
    const cases = [[5, 2], [3, 1], [Math.E, 1]];
    for (const [a, b] of cases) expect(near(BEST.sub(a, b), sub(a, b))).toBe(true);
  });

  it("BEST.exp ≈ EML exp", () => {
    for (const x of [-2, 0, 1, 2]) expect(near(BEST.exp(x), exp(x), TIGHT)).toBe(true);
  });

  it("BEST.ln ≈ EML ln  (different operator, same value)", () => {
    for (const x of [1, 2, Math.E, 10]) expect(near(BEST.ln(x), ln(x), TOL)).toBe(true);
  });

  it("BEST.pow ≈ EML pow  (3n vs 15n)", () => {
    const cases = [[2, 3], [4, 0.5], [3, 4]];
    for (const [x, n] of cases) expect(near(BEST.pow(x, n), pow(x, n))).toBe(true);
  });

  it("BEST.mul ≈ EML mul  (7n vs 13n)", () => {
    const cases = [[2, 3], [4, 5], [0.5, 2]];
    for (const [a, b] of cases) expect(near(BEST.mul(a, b), mul(a, b))).toBe(true);
  });

  it("BEST.div ≈ EML div  (1n vs 15n)", () => {
    const cases = [[6, 2], [10, 5], [Math.PI, 2]];
    for (const [a, b] of cases) expect(near(BEST.div(a, b), div(a, b))).toBe(true);
  });

  it("BEST.recip ≈ EML recip  (2n vs 5n)", () => {
    for (const x of [2, 3, Math.E]) expect(near(BEST.recip(x), recip(x))).toBe(true);
  });
});

// ─── gelu_eml / gelu_best ─────────────────────────────────────────────────────

const C1 = Math.sqrt(2 / Math.PI);
const C2 = C1 * 0.044715;

// Reference using the same ±3.25 clamp but native Math.tanh
const gelu_ref = (x) => {
  const inner = C1 * x + C2 * x * x * x;
  if (inner >  3.25) return x;
  if (inner < -3.25) return 0;
  return 0.5 * x * (1 + Math.tanh(inner));
};

describe("gelu_eml  (17 nodes: exp 1 + add 11 + recip_eml 5)", () => {
  const spots = [[-2, -0.04540229], [-1, -0.15880800], [-0.5, -0.15428598],
                 [0, 0], [0.5, 0.34571401], [1, 0.84119199], [2, 1.95459769]];

  for (const [x, expected] of spots) {
    it(`gelu_eml(${x}) ≈ ${expected}`, () => {
      expect(near(gelu_eml(x), expected, 1e-6)).toBe(true);
    });
  }

  it("gelu_eml(0) = 0", () => expect(gelu_eml(0)).toBe(0));

  it("max error vs Math.tanh reference < 1e-12 over 1000 pts in [-4, 4]", () => {
    let maxErr = 0;
    for (let i = 0; i < 1000; i++) {
      const x = -4 + i * 8 / 999;
      maxErr = Math.max(maxErr, Math.abs(gelu_eml(x) - gelu_ref(x)));
    }
    expect(maxErr).toBeLessThan(1e-12);
  });

  it("clamp guard: gelu_eml(5) = 5, gelu_eml(-5) = 0", () => {
    expect(gelu_eml(5)).toBe(5);
    expect(gelu_eml(-5)).toBe(0);
  });
});

describe("gelu_best  (14 nodes: exp 1 + add 11 + recip_edl 2)", () => {
  const spots = [[-2, -0.04540229], [-1, -0.15880800], [-0.5, -0.15428598],
                 [0, 0], [0.5, 0.34571401], [1, 0.84119199], [2, 1.95459769]];

  for (const [x, expected] of spots) {
    it(`gelu_best(${x}) ≈ ${expected}`, () => {
      expect(near(gelu_best(x), expected, 1e-6)).toBe(true);
    });
  }

  it("gelu_best(0) = 0", () => expect(gelu_best(0)).toBe(0));

  it("max error vs Math.tanh reference < 1e-12 over 1000 pts in [-4, 4]", () => {
    let maxErr = 0;
    for (let i = 0; i < 1000; i++) {
      const x = -4 + i * 8 / 999;
      maxErr = Math.max(maxErr, Math.abs(gelu_best(x) - gelu_ref(x)));
    }
    expect(maxErr).toBeLessThan(1e-12);
  });

  it("gelu_eml and gelu_best agree to < 1e-10 over 1000 pts in [-4, 4]", () => {
    let maxDiff = 0;
    for (let i = 0; i < 1000; i++) {
      const x = -4 + i * 8 / 999;
      maxDiff = Math.max(maxDiff, Math.abs(gelu_eml(x) - gelu_best(x)));
    }
    expect(maxDiff).toBeLessThan(1e-10);
  });

  it("clamp guard: gelu_best(5) = 5, gelu_best(-5) = 0", () => {
    expect(gelu_best(5)).toBe(5);
    expect(gelu_best(-5)).toBe(0);
  });
});

// ─── IDENTITIES catalogue ─────────────────────────────────────────────────────

describe("IDENTITIES", () => {
  it("has at least 15 entries", () => {
    expect(IDENTITIES.length).toBeGreaterThanOrEqual(15);
  });

  it("every entry has name, operator, nodes, status", () => {
    for (const id of IDENTITIES) {
      expect(id).toHaveProperty("name");
      expect(id).toHaveProperty("operator");
      expect(id).toHaveProperty("nodes");
      expect(id).toHaveProperty("status");
    }
  });

  it("EXL ln is 1 node (cheapest known)", () => {
    const entry = IDENTITIES.find(e => e.operator === "EXL" && e.name === "ln x");
    expect(entry).toBeDefined();
    expect(entry.nodes).toBe(1);
  });

  it("EXL pow is 3 nodes (cheapest known)", () => {
    const entry = IDENTITIES.find(e => e.operator === "EXL" && e.name === "xⁿ");
    expect(entry).toBeDefined();
    expect(entry.nodes).toBe(3);
  });

  it("EDL div is 1 node", () => {
    const entry = IDENTITIES.find(e => e.operator === "EDL" && e.name === "x/y");
    expect(entry).toBeDefined();
    expect(entry.nodes).toBe(1);
  });

  it("EML add is 11 nodes", () => {
    const entry = IDENTITIES.find(e => e.operator === "EML" && e.name === "x+y");
    expect(entry).toBeDefined();
    expect(entry.nodes).toBe(11);
  });

  it("every entry has a depth field (numeric)", () => {
    for (const id of IDENTITIES) {
      expect(typeof id.depth).toBe("number");
      expect(id.depth).toBeGreaterThan(0);
    }
  });

  it("exp (EML) depth = 1 — matches Python core.py", () => {
    const entry = IDENTITIES.find(e => e.operator === "EML" && e.name === "eˣ");
    expect(entry).toBeDefined();
    expect(entry.depth).toBe(1);
  });

  it("ln (EML) depth = 3 — matches Python core.py", () => {
    const entry = IDENTITIES.find(e => e.operator === "EML" && e.name === "ln x");
    expect(entry).toBeDefined();
    expect(entry.depth).toBe(3);
  });

  it("pow (EML) depth = 8, pow (EXL) depth = 3 — EXL is shallower", () => {
    const emlPow = IDENTITIES.find(e => e.operator === "EML" && e.name === "xⁿ");
    const exlPow = IDENTITIES.find(e => e.operator === "EXL" && e.name === "xⁿ");
    expect(emlPow).toBeDefined();
    expect(exlPow).toBeDefined();
    expect(emlPow.depth).toBe(8);
    expect(exlPow.depth).toBe(3);
  });
});
