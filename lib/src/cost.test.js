/**
 * Tests for monogate/cost — Pfaffian cost analysis port.
 *
 * The reference values are taken from the Python `eml-cost` package
 * (v0.6.0+). Every case here was cross-checked against
 * `eml_cost.analyze` + `eml_cost.fingerprint_axes` for byte-identical
 * output. Divergences are documented in the test name.
 */
import { describe, it, expect } from 'vitest';
import {
  parse,
  analyze,
  analyze_batch,
  pfaffian_r,
  max_path_r,
  eml_depth,
  structural_overhead,
  is_pfaffian_not_eml,
  distance,
  compare,
  PFAFFIAN_NOT_EML_R,
} from './cost.js';

// ────────────────────────────────────────────────────────────────────
// Parser
// ────────────────────────────────────────────────────────────────────

describe('parse()', () => {
  it('parses a bare symbol', () => {
    expect(parse('x')).toEqual({ type: 'sym', name: 'x' });
  });

  it('parses an integer literal', () => {
    expect(parse('42')).toEqual({ type: 'num', value: 42 });
  });

  it('parses a float literal', () => {
    expect(parse('3.14')).toEqual({ type: 'num', value: 3.14 });
  });

  it('parses scientific notation with negative exponent', () => {
    expect(parse('1.5e-3')).toEqual({ type: 'num', value: 1.5e-3 });
  });

  it('parses unary minus as neg', () => {
    expect(parse('-x')).toEqual({
      type: 'neg',
      arg: { type: 'sym', name: 'x' },
    });
  });

  it('treats subtraction as add(x, neg(y))', () => {
    const tree = parse('x - y');
    expect(tree.type).toBe('add');
    expect(tree.args).toHaveLength(2);
    expect(tree.args[1].type).toBe('neg');
  });

  it('parses division as mul(a, pow(b, -1))', () => {
    const tree = parse('x/2');
    expect(tree.type).toBe('mul');
    expect(tree.args[0]).toEqual({ type: 'sym', name: 'x' });
    expect(tree.args[1]).toEqual({
      type: 'pow',
      base: { type: 'num', value: 2 },
      exponent: { type: 'num', value: -1 },
    });
  });

  it('parses both ^ and ** as pow', () => {
    const a = parse('x^2');
    const b = parse('x**2');
    expect(a).toEqual(b);
    expect(a.type).toBe('pow');
  });

  it('flattens nested mul', () => {
    const tree = parse('a*b*c');
    expect(tree.type).toBe('mul');
    expect(tree.args).toHaveLength(3);
  });

  it('parses transcendental function calls', () => {
    expect(parse('exp(x)').type).toBe('exp');
    expect(parse('log(x)').type).toBe('log');
    expect(parse('ln(x)').type).toBe('log');  // ln aliases to log
    expect(parse('sin(x)').type).toBe('sin');
  });

  it('parses sqrt as pow(.., 1/2)', () => {
    const tree = parse('sqrt(x)');
    expect(tree.type).toBe('pow');
    expect(tree.exponent.value).toBe(0.5);
  });

  it('parses pi and e as numeric constants', () => {
    expect(parse('pi').value).toBeCloseTo(Math.PI);
    expect(parse('e').value).toBeCloseTo(Math.E);
  });

  it('throws on unknown function name', () => {
    expect(() => parse('foobar(x)')).toThrow(/Unknown function/);
  });

  it('throws on trailing garbage', () => {
    expect(() => parse('x +')).toThrow();
  });

  it('parses Pfaffian-not-EML functions', () => {
    expect(parse('erf(x)').type).toBe('erf');
    expect(parse('gamma(x)').type).toBe('gamma');
    expect(parse('lambertw(x)').type).toBe('lambertw');
  });
});

// ────────────────────────────────────────────────────────────────────
// Python-parity table
// ────────────────────────────────────────────────────────────────────

describe('analyze() — Python eml-cost parity', () => {
  // Each case = [expr, expected_axes_string, expected_pne]
  // Cross-checked against Python eml_cost 0.6.0 + fingerprint_axes
  // on 2026-04-26 NIGHT.
  const CASES = [
    // Polynomial / arithmetic
    ['x', 'p0-d0-w0-c0', false],
    ['x + 1', 'p0-d1-w0-c0', false],
    ['x*y', 'p0-d1-w0-c0', false],
    ['(x+1)*(x-1)', 'p0-d3-w0-c0', false],
    ['x**2 + y**2', 'p0-d2-w0-c0', false],
    ['(x+y)**3', 'p0-d2-w0-c0', false],
    // Transcendental primitives
    ['exp(x)', 'p1-d1-w1-c0', false],
    ['log(x)', 'p1-d1-w1-c0', false],
    ['sin(x)', 'p2-d3-w2-c1', false],
    ['cos(x)', 'p2-d3-w2-c1', false],
    ['tan(x)', 'p1-d4-w1-c1', false],
    ['tanh(x)', 'p1-d1-w1-c0', false],
    ['sinh(x)', 'p2-d1-w2-c0', false],
    ['cosh(x)', 'p2-d1-w2-c0', false],
    // Compositions
    ['exp(exp(x))', 'p2-d2-w2-c0', false],
    ['sin(sin(x))', 'p4-d6-w4-c2', false],
    ['log(sin(x))', 'p3-d4-w3-c1', false],
    ['exp(sin(x))', 'p3-d4-w3-c1', false],
    ['sin(exp(x))', 'p3-d4-w3-c1', false],
    // ML activations + fusion patterns
    ['1/(1+exp(-x))', 'p1-d2-w1-c0', false],
    ['log(1+exp(x))', 'p2-d1-w2-c-1', false],
    ['x*tanh(log(1+exp(x)))', 'p3-d3-w3-c0', false],
    ['x*(1+tanh(x))/2', 'p1-d3-w1-c0', false],
    ['tanh(x/2)/2 + 1/2', 'p1-d5-w1-c0', false],
    // Pfaffian-not-EML
    ['erf(x)', 'p2-d1-w2-c0', true],
    ['gamma(x)', 'p2-d1-w2-c0', true],
    ['besselj(0, x)', 'p3-d1-w3-c0', true],
    ['x*(1+erf(x/sqrt(2)))/2', 'p3-d6-w3-c0', true],   // GELU exact
    // Multivariate
    ['exp(-x**2 - y**2)', 'p1-d4-w1-c0', false],
    ['exp(x*y) + cos(x*y)', 'p3-d5-w2-c1', false],
    ['sin(x)**2 + cos(x)**2', 'p2-d5-w2-c1', false],
    ['a*cos(omega*t)', 'p2-d5-w2-c1', false],
  ];

  for (const [expr, expectedAxes, expectedPne] of CASES) {
    it(`${expr} → ${expectedAxes} (pne=${expectedPne})`, () => {
      const r = analyze(expr);
      expect(r.cost_class).toBe(expectedAxes);
      expect(r.is_pfaffian_not_eml).toBe(expectedPne);
    });
  }
});

// ────────────────────────────────────────────────────────────────────
// Individual metrics
// ────────────────────────────────────────────────────────────────────

describe('pfaffian_r()', () => {
  it('counts distinct chain generators across the tree', () => {
    expect(pfaffian_r(parse('x'))).toBe(0);
    expect(pfaffian_r(parse('exp(x)'))).toBe(1);
    expect(pfaffian_r(parse('exp(x) + exp(y)'))).toBe(2);
  });

  it('dedupes shared sin/cos generator', () => {
    // sin(x) and cos(x) share one chain pair → r=2
    expect(pfaffian_r(parse('sin(x) + cos(x)'))).toBe(2);
    // sin(x) and cos(y) are independent → r=4
    expect(pfaffian_r(parse('sin(x) + cos(y)'))).toBe(4);
  });

  it('skips integer-power chain elements', () => {
    expect(pfaffian_r(parse('x**5'))).toBe(0);
    expect(pfaffian_r(parse('(x+1)**3'))).toBe(0);
  });
});

describe('max_path_r()', () => {
  it('counts chain order along deepest path only', () => {
    // exp(x) + exp(y): pfaffian_r=2 but max_path_r=1
    expect(max_path_r(parse('exp(x) + exp(y)'))).toBe(1);
    expect(pfaffian_r(parse('exp(x) + exp(y)'))).toBe(2);
  });

  it('sin/cos contribute 2 (Euler bypass)', () => {
    expect(max_path_r(parse('sin(x)'))).toBe(2);
    expect(max_path_r(parse('cos(exp(x))'))).toBe(3);
  });
});

describe('eml_depth()', () => {
  it('handles SuperBEST routing depths', () => {
    expect(eml_depth(parse('x'))).toBe(0);
    expect(eml_depth(parse('exp(x)'))).toBe(1);
    expect(eml_depth(parse('sin(x)'))).toBe(3);
    expect(eml_depth(parse('tan(x)'))).toBe(4);
    expect(eml_depth(parse('tanh(x)'))).toBe(1);
  });

  it('applies F-family fusion for sigmoid', () => {
    // 1/(1+exp(-x)) → 1 + emlDepth(x via minus extraction) ; with the
    // mul wrapper from the parser, total = 2.
    expect(eml_depth(parse('1/(1+exp(-x))'))).toBe(2);
  });

  it('applies F-family fusion for softplus / lead', () => {
    // log(1+exp(x)) — fused in eml_depth: 1 + emlDepth(x) = 1.
    expect(eml_depth(parse('log(1+exp(x))'))).toBe(1);
  });
});

describe('is_pfaffian_not_eml()', () => {
  it('detects bare PNE primitives', () => {
    expect(is_pfaffian_not_eml(parse('erf(x)'))).toBe(true);
    expect(is_pfaffian_not_eml(parse('gamma(x)'))).toBe(true);
    expect(is_pfaffian_not_eml(parse('besselj(2, x)'))).toBe(true);
  });

  it('propagates through sub-expressions', () => {
    expect(is_pfaffian_not_eml(parse('x + erf(y)'))).toBe(true);
    expect(is_pfaffian_not_eml(parse('exp(gamma(x))'))).toBe(true);
  });

  it('returns false for pure EML expressions', () => {
    expect(is_pfaffian_not_eml(parse('exp(sin(x*y))'))).toBe(false);
    expect(is_pfaffian_not_eml(parse('1/(1+exp(-x))'))).toBe(false);
  });
});

// ────────────────────────────────────────────────────────────────────
// Distance + compare
// ────────────────────────────────────────────────────────────────────

describe('distance()', () => {
  it('is zero for identical profiles', () => {
    const a = analyze('exp(x)');
    expect(distance(a, a)).toBe(0);
  });

  it('is symmetric', () => {
    const a = analyze('sin(x)');
    const b = analyze('exp(x)');
    expect(distance(a, b)).toBeCloseTo(distance(b, a));
  });

  it('respects the triangle inequality', () => {
    const a = analyze('x');
    const b = analyze('exp(x)');
    const c = analyze('sin(exp(x))');
    expect(distance(a, c)).toBeLessThanOrEqual(distance(a, b) + distance(b, c) + 1e-9);
  });

  it('supports custom weights', () => {
    const a = analyze('exp(x)');
    const b = analyze('sin(x)');
    const wide = distance(a, b, { w_r: 100 });
    const default_ = distance(a, b);
    expect(wide).toBeGreaterThan(default_);
  });
});

describe('compare()', () => {
  it('returns per-axis deltas + total distance', () => {
    const a = analyze('exp(x)');
    const b = analyze('sin(x)');
    const c = compare(a, b);
    expect(c.delta_r).toBe(a.max_path_r - b.max_path_r);
    expect(c.delta_d).toBe(a.predicted_depth - b.predicted_depth);
    expect(c.distance).toBeCloseTo(distance(a, b));
  });
});

// ────────────────────────────────────────────────────────────────────
// Batch + tree-input acceptance
// ────────────────────────────────────────────────────────────────────

describe('analyze_batch()', () => {
  it('analyzes a list of expressions', () => {
    const results = analyze_batch(['x', 'exp(x)', 'sin(x)']);
    expect(results).toHaveLength(3);
    expect(results[0].cost_class).toBe('p0-d0-w0-c0');
    expect(results[1].cost_class).toBe('p1-d1-w1-c0');
    expect(results[2].cost_class).toBe('p2-d3-w2-c1');
  });
});

describe('analyze() input forms', () => {
  it('accepts pre-built expression trees', () => {
    const tree = { type: 'exp', arg: { type: 'sym', name: 'x' } };
    expect(analyze(tree).cost_class).toBe('p1-d1-w1-c0');
  });

  it('parses a string and returns the same result', () => {
    const fromStr = analyze('exp(x)');
    const fromTree = analyze({ type: 'exp', arg: { type: 'sym', name: 'x' } });
    expect(fromStr.cost_class).toBe(fromTree.cost_class);
    expect(fromStr.pfaffian_r).toBe(fromTree.pfaffian_r);
  });
});

// ────────────────────────────────────────────────────────────────────
// Registry
// ────────────────────────────────────────────────────────────────────

describe('PFAFFIAN_NOT_EML_R registry', () => {
  it('includes the major PNE families', () => {
    // Bessel
    expect(PFAFFIAN_NOT_EML_R.besselj).toBeGreaterThan(0);
    // erf
    expect(PFAFFIAN_NOT_EML_R.erf).toBe(2);
    // Gamma
    expect(PFAFFIAN_NOT_EML_R.gamma).toBe(2);
    // Lambert W
    expect(PFAFFIAN_NOT_EML_R.lambertw).toBe(2);
    // Airy
    expect(PFAFFIAN_NOT_EML_R.airyai).toBe(3);
  });
});

// ────────────────────────────────────────────────────────────────────
// Backwards-compat: hand-built div trees
// ────────────────────────────────────────────────────────────────────

describe('hand-built div trees (backwards compat)', () => {
  it('handles type:div in metric walks', () => {
    // User builds tree manually with div instead of mul+pow(.,-1)
    const tree = {
      type: 'div',
      args: [
        { type: 'num', value: 1 },
        {
          type: 'add',
          args: [
            { type: 'num', value: 1 },
            { type: 'exp', arg: { type: 'sym', name: 'x' } },
          ],
        },
      ],
    };
    const r = analyze(tree);
    // Sigmoid pattern via div should still match
    expect(r.is_pfaffian_not_eml).toBe(false);
    expect(r.pfaffian_r).toBe(1);
  });
});
