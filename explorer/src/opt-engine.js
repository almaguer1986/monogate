/**
 * opt-engine.js — shared analysis engine for OptimizeTab and NeRFOptimizerTab.
 *
 * Pure functions and constants only — no React.
 */

export const API_URL = "https://monogate-api.fly.dev";

export const C = {
  bg: "#07080f", surface: "#0d0e1c", border: "#191b2e",
  text: "#cdd0e0", muted: "#4e5168", accent: "#e8a020",
  blue: "#6ab0f5", green: "#5ec47a", red: "#e05060", tag: "#1a1c2e",
};

export const PILL = {
  EML:       { bg: "rgba(124,111,247,0.14)", border: "#7c6ff7",  color: "#a09cf7" },
  EDL:       { bg: "rgba(45,212,191,0.10)",  border: "#2dd4bf",  color: "#2dd4bf" },
  EXL:       { bg: "rgba(245,158,11,0.12)",  border: "#f59e0b",  color: "#f5b435" },
  "EML+EDL": { bg: "rgba(94,196,122,0.10)",  border: "#5ec47a",  color: "#5ec47a" },
};

// Order matters: longer/more-specific patterns before shorter ones.
export const RULES = [
  { id: "sin",     label: "sin",       re: /(?:math|torch|np|numpy|F)\.sin\s*\(/g,        eml: 245, best: 63, op: "EXL",     note: "8-term Taylor via EXL pow (63n vs 245n)",           sub: s => s.replace(/(?:math|torch|np|numpy|F)\.sin/, "BEST.sin") },
  { id: "cos",     label: "cos",       re: /(?:math|torch|np|numpy|F)\.cos\s*\(/g,        eml: 245, best: 63, op: "EXL",     note: "8-term Taylor via EXL pow (63n vs 245n)",           sub: s => s.replace(/(?:math|torch|np|numpy|F)\.cos/, "BEST.cos") },
  { id: "tanh",    label: "tanh",      re: /(?:math|torch|np|numpy|F)\.tanh\s*\(/g,       eml: 45,  best: 25, op: "EML+EDL", note: "mul+exp+sub+add+div via EDL (25n vs 45n)",          sub: s => s.replace(/(?:math|torch|np|numpy|F)\.tanh/, "BEST.tanh") },
  { id: "sigmoid", label: "sigmoid",   re: /(?:torch|F)\.sigmoid\s*\(/g,                  eml: 36,  best: 19, op: "EML+EDL", note: "neg+exp+add+div via EDL (19n vs 36n)",              sub: s => s.replace(/(?:torch|F)\.sigmoid/, "BEST.sigmoid") },
  { id: "gelu",    label: "F.gelu",    re: /F\.gelu\s*\(/g,                               eml: 17,  best: 14, op: "EML+EDL", note: "exp+add+recip_edl = 14n vs 17n (tanh formula)",     sub: s => s.replace(/F\.gelu/, "BEST.gelu") },
  { id: "log",     label: "log / ln",  re: /(?:math|torch|np|numpy|F)\.log\w*\s*\(/g,     eml: 3,   best: 1,  op: "EXL",     note: "EXL ln: 1n vs EML's 3n",                           sub: s => s.replace(/(?:math|torch|np|numpy|F)\.log\w*/, "BEST.ln") },
  { id: "exp",     label: "exp",       re: /(?:math|torch|np|numpy|F)\.exp\s*\(/g,         eml: 1,   best: 1,  op: "EML",     note: "same cost across all operators",                    sub: null },
  { id: "pow_fn",  label: "pow(x,n)",  re: /(?:math|torch|np|numpy)\.pow(?:er)?\s*\(/g,   eml: 15,  best: 3,  op: "EXL",     note: "EXL pow: 3n vs EML's 15n",                         sub: s => s.replace(/(?:math|torch|np|numpy)\.pow(?:er)?/, "BEST.pow") },
  { id: "pow_op",  label: "x ** n",    re: /\*\*\s*[\d.]+/g,                              eml: 15,  best: 3,  op: "EXL",     note: "EXL pow: 3n vs EML's 15n — simple forms rewritten", sub: null },
  { id: "sqrt",    label: "sqrt",      re: /(?:math|torch|np|numpy)\.sqrt\s*\(/g,          eml: 15,  best: 3,  op: "EXL",     note: "pow(x, 0.5) via EXL: 3n",                          sub: s => s.replace(/(?:math|torch|np|numpy)\.sqrt/, "BEST.sqrt") },
  { id: "div_fn",  label: "torch.div", re: /(?:torch\.div|np\.divide)\s*\(/g,             eml: 15,  best: 1,  op: "EDL",     note: "EDL div: 1n vs EML's 15n",                         sub: s => s.replace(/(?:torch\.div|np\.divide)/, "BEST.div") },
  { id: "mul_fn",  label: "torch.mul", re: /(?:torch\.mul|np\.multiply)\s*\(/g,           eml: 13,  best: 7,  op: "EDL",     note: "EDL mul: 7n vs EML's 13n",                         sub: s => s.replace(/(?:torch\.mul|np\.multiply)/, "BEST.mul") },
];

// Node-reduction threshold below which Python call overhead dominates speedup.
// Matches _CROSSOVER_PCT in python/monogate/optimize.py.
export const CROSSOVER_PCT = 20;

// Measured in experiment_09 (TinyMLP, Python CPU).
export const BENCHMARKS = {
  sin:    { speedup: 2.8, label: "sin Taylor (8 terms)" },
  cos:    { speedup: 2.8, label: "cos Taylor (8 terms)" },
  pow_fn: { speedup: 4.8, label: "pow(x, n)" },
  pow_op: { speedup: 4.8, label: "x ** n" },
};

/**
 * Split source into function blocks by `def` boundaries.
 * Returns [{name, body}] sorted by appearance.
 */
export function parseFunctions(src) {
  const defRe = /^([ \t]*)def\s+(\w+)\s*\(/gm;
  const positions = [];
  let m;
  while ((m = defRe.exec(src)) !== null) {
    positions.push({ name: m[2], indent: m[1].length, startIdx: m.index });
  }
  if (positions.length === 0) return [];

  return positions.map((pos, i) => {
    let endIdx = src.length;
    for (let j = i + 1; j < positions.length; j++) {
      if (positions[j].indent <= pos.indent) {
        endIdx = positions[j].startIdx;
        break;
      }
    }
    return { name: pos.name, body: src.slice(pos.startIdx, endIdx).trimEnd() };
  });
}

export function analyzeCode(src) {
  if (!src.trim()) return null;

  const matches = [];
  let totalEml = 0, totalBest = 0;
  let topBenchmark = null, topSavingsPct = 0;

  for (const rule of RULES) {
    rule.re.lastIndex = 0;
    const found = src.match(rule.re);
    const count = found ? found.length : 0;
    if (count > 0) {
      matches.push({ ...rule, count });
      totalEml  += count * rule.eml;
      totalBest += count * rule.best;
      const savPct = rule.eml > 0 ? Math.round((1 - rule.best / rule.eml) * 100) : 0;
      if (savPct > topSavingsPct && BENCHMARKS[rule.id]) {
        topSavingsPct = savPct;
        topBenchmark  = BENCHMARKS[rule.id];
      }
    }
  }

  if (matches.length === 0) {
    return { matches: [], totalEml: 0, totalBest: 0, rewritten: src, topBenchmark: null };
  }

  let rewritten = src;
  for (const rule of RULES) {
    if (!rule.sub) continue;
    rule.re.lastIndex = 0;
    rewritten = rewritten.replace(rule.re, m => rule.sub(m));
  }

  // Rewrite simple `identifier**n` → `BEST.pow(identifier, n)`.
  rewritten = rewritten.replace(
    /\b([a-zA-Z_][\w.]*)\s*\*\*\s*([\d.]+)/g,
    "BEST.pow($1, $2)",
  );

  const hasGains = matches.some(m => m.best < m.eml);
  if (hasGains && !rewritten.startsWith("from monogate")) {
    rewritten = "from monogate import BEST\n\n" + rewritten;
  }

  return { matches, totalEml, totalBest, rewritten, topBenchmark };
}

export function analyzeAll(src) {
  if (!src.trim()) return null;

  const overall  = analyzeCode(src);
  const fnBlocks = parseFunctions(src);

  const functions = fnBlocks
    .map(fn => ({ name: fn.name, result: analyzeCode(fn.body) }))
    .filter(fr => fr.result && fr.result.matches.length > 0);

  return { overall, functions };
}

/** Map a Python API response to the same shape analyzeAll() returns. */
export function mapPythonResponse(apiResp) {
  const matches = apiResp.ops.map(op => ({
    id:    op.name,
    label: op.name,
    count: op.count,
    eml:   op.eml_nodes / op.count,
    best:  op.best_nodes / op.count,
    op:    op.best_op,
    note:  op.note,
  }));

  const benchmarkMap = {
    sin: { speedup: 2.8, label: "sin Taylor (8 terms)" },
    cos: { speedup: 2.8, label: "cos Taylor (8 terms)" },
    pow: { speedup: 4.8, label: "pow(x, n)" },
  };
  let topBenchmark = null;
  for (const op of apiResp.ops) {
    if (benchmarkMap[op.name] && op.best_nodes < op.eml_nodes) {
      topBenchmark = benchmarkMap[op.name];
      break;
    }
  }

  return {
    overall: {
      matches,
      totalEml:      apiResp.total_eml_nodes,
      totalBest:     apiResp.total_best_nodes,
      rewritten:     apiResp.rewritten_code,
      topBenchmark,
      pythonSnippet: apiResp.python_snippet,
    },
    functions: [],
  };
}
