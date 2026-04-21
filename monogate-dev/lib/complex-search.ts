/**
 * complex-search.ts — Exhaustive EML tree search over ℂ.
 *
 * Enumerates all EML trees up to a user-chosen max node count,
 * evaluates each one with the single terminal {1} under strict
 * principal-branch ln, and finds the closest match to a target.
 *
 * Tree grammar: S → 1 | eml(S, S)
 * Operator:     eml(x, y) = exp(x) − ln(y)
 * Terminal:     leaf evaluates to Complex(1, 0)
 *
 * Catalan counts by internal node count:
 *   0→1  1→1  2→2  3→5  4→14  5→42  6→132  7→429
 *   8→1430  9→4862  10→16796  11→58786  12→208012
 *   Total (0 through 12): 290 512 trees
 */

// ── Complex type ──────────────────────────────────────────────────────────────

export class C {
  constructor(readonly re: number, readonly im = 0) {}

  exp(): C {
    const r = Math.exp(this.re);
    if (!isFinite(r)) throw new RangeError("exp overflow");
    return new C(r * Math.cos(this.im), r * Math.sin(this.im));
  }

  ln(): C {
    const abs = Math.hypot(this.re, this.im);
    if (abs < 1e-300) throw new RangeError("ln(0)");
    const re = Math.log(abs);
    const im = Math.atan2(this.im, this.re);
    if (!isFinite(re) || !isFinite(im)) throw new RangeError("ln overflow");
    return new C(re, im);
  }

  sub(b: C): C {
    return new C(this.re - b.re, this.im - b.im);
  }

  dist(b: C): number {
    return Math.hypot(this.re - b.re, this.im - b.im);
  }

  fmt(): string {
    const EPS = 1e-10;
    const reZ = Math.abs(this.re) < EPS;
    const imZ = Math.abs(this.im) < EPS;
    const fv = (v: number) => parseFloat(v.toPrecision(8)).toString();

    if (reZ && imZ) return "0";
    if (imZ) return fv(this.re);
    if (reZ) {
      if (Math.abs(this.im - 1) < EPS) return "i";
      if (Math.abs(this.im + 1) < EPS) return "−i";
      return `${fv(this.im)}i`;
    }
    const sign = this.im < 0 ? "−" : "+";
    const absIm = Math.abs(this.im);
    const imStr = Math.abs(absIm - 1) < EPS ? "i" : `${fv(absIm)}i`;
    return `${fv(this.re)}${sign}${imStr}`;
  }
}

// ── Tree type ─────────────────────────────────────────────────────────────────

export type Tree = null | { l: Tree; r: Tree };

// ── Tree evaluation ───────────────────────────────────────────────────────────

const LEAF = new C(1);

function evalTree(t: Tree): C {
  if (t === null) return LEAF;
  const lv = evalTree(t.l);
  const rv = evalTree(t.r);
  // eml(x, y) = exp(x) − ln(y)
  return lv.exp().sub(rv.ln());
}

// ── Tree expression formatter ─────────────────────────────────────────────────

export function fmtTree(t: Tree): string {
  if (t === null) return "1";
  return `eml(${fmtTree(t.l)},${fmtTree(t.r)})`;
}

// ── Catalan tree enumeration (memoized) ───────────────────────────────────────

const _memo = new Map<number, Tree[]>();

export function treesN(n: number): Tree[] {
  if (_memo.has(n)) return _memo.get(n)!;
  if (n === 0) {
    _memo.set(0, [null]);
    return [null];
  }
  const result: Tree[] = [];
  for (let i = 0; i < n; i++) {
    for (const l of treesN(i)) {
      for (const r of treesN(n - 1 - i)) {
        result.push({ l, r });
      }
    }
  }
  _memo.set(n, result);
  return result;
}

// Precompute cumulative tree counts for progress display
export function totalTrees(maxNodes: number): number {
  let count = 0;
  for (let n = 0; n <= maxNodes; n++) count += treesN(n).length;
  return count;
}

// ── Targets ───────────────────────────────────────────────────────────────────

export type TargetKey = "i" | "pi" | "neg_i_pi" | "e" | "zero" | "sqrt2";

export interface Target {
  label: string;
  value: C;
  known: string | null;   // known node count, or null if open
}

export const TARGETS: Record<TargetKey, Target> = {
  i:        { label: "i",   value: new C(0, 1),           known: null },
  pi:       { label: "π",   value: new C(Math.PI),        known: null },
  neg_i_pi: { label: "−iπ", value: new C(0, -Math.PI),   known: "11 nodes" },
  e:        { label: "e",   value: new C(Math.E),          known: "1 node" },
  zero:     { label: "0",   value: new C(0),               known: "3 nodes" },
  sqrt2:    { label: "√2",  value: new C(Math.SQRT2),      known: null },
};

// ── Search result types ───────────────────────────────────────────────────────

export interface EvalRow {
  nodes: number;
  expr: string;
  value: string;
  dist: number;
}

export interface SearchProgress {
  evaluated: number;
  total: number;
  errors: number;
  elapsed: number;       // ms
  bestDist: number;
  bestExpr: string;
  bestValue: string;
  bestNodes: number;
  feed: EvalRow[];       // last N evaluations
  found: boolean;        // dist < FOUND_THRESHOLD
}

export interface SearchController {
  stop: () => void;
}

// ── Search runner ─────────────────────────────────────────────────────────────

const BATCH         = 300;
const FOUND_THRESH  = 1e-8;
const FEED_MAX      = 8;

export function runExhaustive(
  targetKey: TargetKey,
  maxNodes: number,
  onProgress: (p: SearchProgress) => void,
  onDone: (p: SearchProgress) => void,
): SearchController {
  const target = TARGETS[targetKey];
  const total  = totalTrees(maxNodes);
  const start  = Date.now();

  let stopped   = false;
  let evaluated = 0;
  let errors    = 0;
  let bestDist  = Infinity;
  let bestExpr  = "";
  let bestValue = "";
  let bestNodes = 0;
  let found     = false;
  const feed: EvalRow[] = [];

  // Flatten all trees into an iterator-style sequence:
  // We'll process node count 0, 1, …, maxNodes in order.
  // State is tracked across async ticks via a generator.
  let nodeCount = 0;
  let treeList  = treesN(0);
  let treeIdx   = 0;

  function buildProgress(): SearchProgress {
    return {
      evaluated, total, errors, elapsed: Date.now() - start,
      bestDist, bestExpr, bestValue, bestNodes,
      feed: [...feed],
      found,
    };
  }

  function step() {
    if (stopped) return;

    let count = 0;

    while (count < BATCH) {
      // Advance to next node count level if exhausted
      while (treeIdx >= treeList.length) {
        nodeCount++;
        if (nodeCount > maxNodes) {
          // Done — all trees exhausted
          onDone(buildProgress());
          return;
        }
        treeList = treesN(nodeCount);
        treeIdx  = 0;
      }

      const tree = treeList[treeIdx++];
      count++;
      evaluated++;

      try {
        const val  = evalTree(tree);
        const dist = val.dist(target.value);
        const expr = fmtTree(tree);
        const row: EvalRow = { nodes: nodeCount, expr, value: val.fmt(), dist };

        feed.push(row);
        if (feed.length > FEED_MAX) feed.shift();

        if (dist < bestDist) {
          bestDist  = dist;
          bestExpr  = expr;
          bestValue = val.fmt();
          bestNodes = nodeCount;
        }

        if (dist < FOUND_THRESH) {
          found = true;
          onDone(buildProgress());
          return;
        }
      } catch {
        errors++;
      }
    }

    onProgress(buildProgress());
    setTimeout(step, 0);
  }

  setTimeout(step, 0);
  return { stop: () => { stopped = true; } };
}
