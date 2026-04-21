/**
 * Server-side EML expression validation.
 * Uses monogate for evaluation, eml-tree for node counting.
 * Runs test cases appropriate to each challenge.
 */

import {
  op, exp, ln, neg, add, sub, mul, div, pow, recip,
} from "monogate";

import {
  exp_t, ln_t, neg_t, add_t, sub_t, mul_t, div_t, pow_t, recip_t, sqrt_t,
  mkVar, mkLit, E_t, ZERO_t, NEG_ONE_t,
  countNodes, countDepth, type TreeNode,
} from "./eml-tree";

export interface ValidationResult {
  valid: boolean;
  nodes: number | null;
  depth: number | null;
  eml_calls: number | null;
  error: string | null;
}

// ─── Expression syntax allowlist ──────────────────────────────────────────────

const ALLOWED_RE = /^[emlxadivosubnegpwrctq\d\s.,()e\-+/*]+$/i;

const OPEN_CHALLENGE_WORDS = ["sin", "cos", "tan", "pi", "atan"];

// ─── Safe evaluation context (real-valued) ────────────────────────────────────

type RealContext = Record<string, unknown>;

function makeRealContext(xValue: number): RealContext {
  return {
    eml: op, exp, ln, neg, add, sub, mul, div, pow, recip,
    sqrt: (x: number) => Math.pow(x, 0.5),
    x: xValue,
    e: Math.E,
  };
}

function makeTreeContext(xVar: TreeNode): RealContext {
  const ctx: RealContext = {
    eml: (a: unknown, b: unknown) => ({ tag: "eml", left: a, right: b } as TreeNode),
    exp: exp_t, ln: ln_t, neg: neg_t, add: add_t, sub: sub_t,
    mul: mul_t, div: div_t, pow: pow_t, recip: recip_t, sqrt: sqrt_t,
    x: xVar, e: E_t,
  };
  return ctx;
}

function evalExpr(expression: string, context: RealContext): unknown {
  const keys = Object.keys(context);
  const vals = Object.values(context);
  // Shadow dangerous globals
  const shadowKeys = ["Math", "global", "globalThis", "process", "require", "eval", "Function"];
  const shadowVals = shadowKeys.map(() => undefined);
  const fn = new Function(
    ...shadowKeys, ...keys,
    `"use strict"; return (${expression});`
  );
  return fn(...shadowVals, ...vals);
}

// ─── Test cases per challenge ─────────────────────────────────────────────────

interface TestCase {
  x?: number;
  expected: number;
  tol: number;
  label: string;
}

const TEST_CASES: Record<string, TestCase[]> = {
  sin: [
    { x: 0,               expected: 0,              tol: 1e-10, label: "sin(0) = 0" },
    { x: Math.PI / 6,     expected: 0.5,            tol: 1e-10, label: "sin(π/6) = 0.5" },
    { x: Math.PI / 4,     expected: Math.SQRT2 / 2, tol: 1e-10, label: "sin(π/4) = √2/2" },
    { x: Math.PI / 2,     expected: 1,              tol: 1e-10, label: "sin(π/2) = 1" },
    { x: Math.PI,         expected: 0,              tol: 1e-9,  label: "sin(π) ≈ 0" },
    { x: -Math.PI / 6,    expected: -0.5,           tol: 1e-10, label: "sin(−π/6) = −0.5" },
  ],
  cos: [
    { x: 0,               expected: 1,              tol: 1e-10, label: "cos(0) = 1" },
    { x: Math.PI / 3,     expected: 0.5,            tol: 1e-10, label: "cos(π/3) = 0.5" },
    { x: Math.PI / 2,     expected: 0,              tol: 1e-9,  label: "cos(π/2) ≈ 0" },
    { x: Math.PI,         expected: -1,             tol: 1e-10, label: "cos(π) = −1" },
    { x: -Math.PI / 3,    expected: 0.5,            tol: 1e-10, label: "cos(−π/3) = 0.5" },
  ],
  pi: [
    { expected: Math.PI,  tol: 1e-10, label: "value = π" },
  ],
  "i-strict": [
    // Complex validation — structural check only in Stage 2
  ],
};

// ─── Main validation function ─────────────────────────────────────────────────

export async function validateExpression(
  challengeId: string,
  expression: string
): Promise<ValidationResult> {
  const clean = expression.trim();

  // 1. Syntax check
  if (!ALLOWED_RE.test(clean)) {
    return { valid: false, nodes: null, depth: null, eml_calls: null,
      error: "Expression contains disallowed characters. Only EML functions and numeric literals are permitted." };
  }

  // 2. Check for open-challenge words being used as shortcuts
  for (const word of OPEN_CHALLENGE_WORDS) {
    if (new RegExp(`\\b${word}\\b`).test(clean.toLowerCase())) {
      return { valid: false, nodes: null, depth: null, eml_calls: null,
        error: `"${word}" is not an EML primitive. Build from eml, exp, ln, neg, add, sub, mul, div, pow, recip.` };
    }
  }

  // 3. Build the tree for node/depth count
  let nodes: number | null = null;
  let depth: number | null = null;
  let eml_calls: number | null = null;

  try {
    const xVar = mkVar("x");
    const treeCtx = makeTreeContext(xVar);
    const tree = evalExpr(clean, treeCtx);
    if (!tree || typeof tree !== "object" || !("tag" in (tree as object))) {
      throw new Error("Expression did not produce a valid tree node");
    }
    nodes = countNodes(tree as TreeNode);
    depth = countDepth(tree as TreeNode);
    eml_calls = Math.floor(nodes / 2);
  } catch (err) {
    return { valid: false, nodes: null, depth: null, eml_calls: null,
      error: `Tree construction failed: ${(err as Error).message}` };
  }

  // 4. i-strict: structural validation only (complex eval in Stage 3+)
  if (challengeId === "i-strict") {
    return { valid: true, nodes, depth, eml_calls,
      error: "Note: complex numeric validation not yet implemented. Structural check passed." };
  }

  // 5. Numeric test cases
  const cases = TEST_CASES[challengeId] ?? [];
  if (cases.length === 0) {
    return { valid: true, nodes, depth, eml_calls, error: null };
  }

  for (const tc of cases) {
    try {
      const xVal = tc.x ?? 0;
      const ctx = makeRealContext(xVal);
      const result = evalExpr(clean, ctx);
      if (typeof result !== "number" || !isFinite(result)) {
        return { valid: false, nodes, depth, eml_calls,
          error: `At x=${xVal}: expression returned ${result} (expected ${tc.expected}). Must return a finite real number.` };
      }
      const err = Math.abs(result - tc.expected);
      if (err > tc.tol) {
        return { valid: false, nodes, depth, eml_calls,
          error: `Failed: ${tc.label}. Got ${result.toFixed(10)}, expected ${tc.expected.toFixed(10)}, error ${err.toExponential(3)} > ${tc.tol}.` };
      }
    } catch (err) {
      return { valid: false, nodes, depth, eml_calls,
        error: `Runtime error at test case "${tc.label}": ${(err as Error).message}` };
    }
  }

  return { valid: true, nodes, depth, eml_calls, error: null };
}
