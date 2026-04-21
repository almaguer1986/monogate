/**
 * EML Symbolic Regression via gradient descent.
 * Browser-compatible — no Node.js APIs.
 */

// ── Types ───────────────────────────────────────────────────────────────────

export type EMLNode =
  | { type: "eml"; left: EMLNode; right: EMLNode }
  | { type: "weight"; id: number }
  | { type: "x" };

export type TargetKey = "sin" | "cos" | "pi" | "i";

export interface SearchProgress {
  iteration: number;
  bestLoss: number;
}

export interface SearchResult {
  expression: string;
  nodes: number;
  depth: number;
  loss: number;
}

export interface SearchController {
  stop: () => void;
}

// ── Forward pass with reverse-mode AD ───────────────────────────────────────

interface ADVal {
  val: number;
  backward: (g: number) => void;
}

function fwd(
  node: EMLNode,
  weights: number[],
  grads: number[],
  x: number
): ADVal {
  if (node.type === "x") {
    return { val: x, backward: () => {} };
  }
  if (node.type === "weight") {
    const id = node.id;
    return {
      val: weights[id],
      backward: (g: number) => { grads[id] += g; },
    };
  }
  const L = fwd(node.left, weights, grads, x);
  const R = fwd(node.right, weights, grads, x);
  const a = L.val;
  const b = R.val;
  if (!isFinite(a) || !isFinite(b) || b <= 0) {
    return { val: NaN, backward: () => {} };
  }
  const ea = Math.exp(a);
  if (!isFinite(ea)) return { val: NaN, backward: () => {} };
  const val = ea - Math.log(b);
  if (!isFinite(val)) return { val: NaN, backward: () => {} };
  return {
    val,
    backward: (g: number) => {
      L.backward(g * ea);
      R.backward(g * (-1 / b));
    },
  };
}

// ── Loss + gradient accumulation ─────────────────────────────────────────────

function lossAndGrads(
  tree: EMLNode,
  weights: number[],
  grads: number[],
  points: { x: number; y: number }[]
): number {
  grads.fill(0);
  let totalLoss = 0;
  let valid = 0;
  for (const pt of points) {
    const r = fwd(tree, weights, grads, pt.x);
    if (!isFinite(r.val)) continue;
    const err = r.val - pt.y;
    totalLoss += err * err;
    r.backward((2 * err) / points.length);
    valid++;
  }
  return valid > 0 ? totalLoss / points.length : Infinity;
}

// ── Adam optimizer ───────────────────────────────────────────────────────────

function adamStep(
  weights: number[],
  grads: number[],
  m: number[],
  v: number[],
  t: number,
  lr: number
): void {
  const b1 = 0.9, b2 = 0.999, eps = 1e-8;
  for (let i = 0; i < weights.length; i++) {
    m[i] = b1 * m[i] + (1 - b1) * grads[i];
    v[i] = b2 * v[i] + (1 - b2) * grads[i] * grads[i];
    const mh = m[i] / (1 - Math.pow(b1, t));
    const vh = v[i] / (1 - Math.pow(b2, t));
    weights[i] -= (lr * mh) / (Math.sqrt(vh) + eps);
  }
}

// ── Random tree generation ───────────────────────────────────────────────────

let _wid = 0;

function mkLeaf(): EMLNode {
  if (Math.random() < 0.2) return { type: "x" };
  return { type: "weight", id: _wid++ };
}

function mkTree(depth: number): EMLNode {
  if (depth <= 0) return mkLeaf();
  const pLeaf = Math.max(0.05, 0.9 - depth * 0.25);
  if (Math.random() < pLeaf) return mkLeaf();
  return { type: "eml", left: mkTree(depth - 1), right: mkTree(depth - 1) };
}

function freshTree(maxDepth: number): EMLNode {
  _wid = 0;
  // Force root to always be an eml node
  return {
    type: "eml",
    left: mkTree(maxDepth - 1),
    right: mkTree(maxDepth - 1),
  };
}

// ── Tree utilities ───────────────────────────────────────────────────────────

export function countNodes(n: EMLNode): number {
  if (n.type !== "eml") return 1;
  return 1 + countNodes(n.left) + countNodes(n.right);
}

// Match eml-tree.ts convention: leaf = depth 1
export function countDepth(n: EMLNode): number {
  if (n.type !== "eml") return 1;
  return 1 + Math.max(countDepth(n.left), countDepth(n.right));
}

function fmtW(w: number): string {
  if (!isFinite(w)) return "1";
  const rounded = Math.round(w);
  if (Math.abs(w - rounded) < 1e-9) return String(rounded);
  return Number(w.toPrecision(12)).toString();
}

export function treeToExpr(n: EMLNode, weights: number[]): string {
  if (n.type === "x") return "x";
  if (n.type === "weight") return fmtW(weights[n.id]);
  return `eml(${treeToExpr(n.left, weights)}, ${treeToExpr(n.right, weights)})`;
}

// ── Target definitions ───────────────────────────────────────────────────────

export const TARGET_META: Record<
  TargetKey,
  { label: string; challengeId: string; realValued: boolean }
> = {
  sin: { label: "sin(x)", challengeId: "sin", realValued: true },
  cos: { label: "cos(x)", challengeId: "cos", realValued: true },
  pi:  { label: "π (constant)", challengeId: "pi",  realValued: true },
  i:   { label: "i (imaginary)", challengeId: "i-strict", realValued: false },
};

const TEST_POINTS: Record<TargetKey, { x: number; y: number }[]> = {
  sin: [
    { x: 0.5,    y: Math.sin(0.5)    },
    { x: 1,      y: Math.sin(1)      },
    { x: -0.5,   y: Math.sin(-0.5)   },
    { x: -1,     y: Math.sin(-1)     },
    { x: 1.5,    y: Math.sin(1.5)    },
    { x: -1.5,   y: Math.sin(-1.5)   },
    { x: 2,      y: Math.sin(2)      },
    { x: -2,     y: Math.sin(-2)     },
    { x: 0.25,   y: Math.sin(0.25)   },
    { x: 0.75,   y: Math.sin(0.75)   },
  ],
  cos: [
    { x: 0.5,    y: Math.cos(0.5)    },
    { x: 1,      y: Math.cos(1)      },
    { x: -0.5,   y: Math.cos(-0.5)   },
    { x: -1,     y: Math.cos(-1)     },
    { x: 1.5,    y: Math.cos(1.5)    },
    { x: -1.5,   y: Math.cos(-1.5)   },
    { x: 2,      y: Math.cos(2)      },
    { x: -2,     y: Math.cos(-2)     },
    { x: 0.25,   y: Math.cos(0.25)   },
    { x: 0.75,   y: Math.cos(0.75)   },
  ],
  pi: [
    { x: 1,   y: Math.PI },
    { x: 2,   y: Math.PI },
    { x: -1,  y: Math.PI },
    { x: 0.5, y: Math.PI },
    { x: -0.5, y: Math.PI },
  ],
  i: [],
};

// ── Main search runner ───────────────────────────────────────────────────────

const MAX_ITER   = 10_000;
const BATCH      = 30;        // iterations per setTimeout tick
const THRESHOLD  = 1e-10;
const RESTART_AT = 500;       // iterations per random tree before restart
const LR         = 0.005;     // Adam learning rate

export function runSearch(
  target: TargetKey,
  maxDepth: number,
  onProgress: (p: SearchProgress) => void,
  onComplete: (r: SearchResult | null) => void
): SearchController {
  let stopped = false;
  let iteration = 0;
  let bestLoss = Infinity;
  let bestTree: EMLNode | null = null;
  let bestWeights: number[] | null = null;

  const points = TEST_POINTS[target];
  if (points.length === 0) {
    onComplete(null);
    return { stop: () => {} };
  }

  let tree: EMLNode;
  let weights: number[];
  let grads: number[];
  let m: number[];
  let v: number[];
  let adamT: number;
  let sinceRestart: number;

  function init() {
    tree = freshTree(maxDepth);
    const nW = Math.max(_wid, 1);
    weights      = Array.from({ length: nW }, () => 1 + Math.random() * 2);
    grads        = new Array(nW).fill(0);
    m            = new Array(nW).fill(0);
    v            = new Array(nW).fill(0);
    adamT        = 0;
    sinceRestart = 0;
  }

  init();

  function step() {
    if (stopped) return;

    for (let b = 0; b < BATCH; b++) {
      if (iteration >= MAX_ITER) {
        onProgress({ iteration, bestLoss });
        onComplete(
          bestTree && bestWeights
            ? {
                expression: treeToExpr(bestTree, bestWeights),
                nodes: countNodes(bestTree),
                depth: countDepth(bestTree),
                loss: bestLoss,
              }
            : null
        );
        return;
      }

      const loss = lossAndGrads(tree, weights, grads, points);

      if (isFinite(loss)) {
        adamT++;
        adamStep(weights, grads, m, v, adamT, LR);

        if (loss < bestLoss) {
          bestLoss    = loss;
          bestTree    = tree;
          bestWeights = [...weights];
        }

        if (loss < THRESHOLD) {
          onProgress({ iteration, bestLoss: loss });
          onComplete({
            expression: treeToExpr(tree, weights),
            nodes: countNodes(tree),
            depth: countDepth(tree),
            loss,
          });
          return;
        }
      }

      iteration++;
      sinceRestart++;

      if (sinceRestart >= RESTART_AT) {
        init();
      }
    }

    onProgress({ iteration, bestLoss });
    setTimeout(step, 0);
  }

  setTimeout(step, 0);
  return { stop: () => { stopped = true; } };
}
