import { useState } from "react";

const C = {
  bg: "#07080f", surface: "#0d0e1c", border: "#191b2e",
  text: "#cdd0e0", muted: "#4e5168", accent: "#e8a020",
  blue: "#6ab0f5", green: "#5ec47a", red: "#e05060", tag: "#1a1c2e",
};

const PILL = {
  EML:       { bg: "rgba(124,111,247,0.14)", border: "#7c6ff7",  color: "#a09cf7" },
  EDL:       { bg: "rgba(45,212,191,0.10)",  border: "#2dd4bf",  color: "#2dd4bf" },
  EXL:       { bg: "rgba(245,158,11,0.12)",  border: "#f59e0b",  color: "#f5b435" },
  "EML+EDL": { bg: "rgba(94,196,122,0.10)",  border: "#5ec47a",  color: "#5ec47a" },
};

// Order matters: longer/more-specific patterns before shorter ones.
const RULES = [
  { id: "sin",     label: "sin",       re: /(?:math|torch|np|numpy|F)\.sin\s*\(/g,        eml: 245, best: 63, op: "EXL",     note: "8-term Taylor via EXL pow (63n vs 245n)",           sub: s => s.replace(/(?:math|torch|np|numpy|F)\.sin/, "BEST.sin") },
  { id: "cos",     label: "cos",       re: /(?:math|torch|np|numpy|F)\.cos\s*\(/g,        eml: 245, best: 63, op: "EXL",     note: "8-term Taylor via EXL pow (63n vs 245n)",           sub: s => s.replace(/(?:math|torch|np|numpy|F)\.cos/, "BEST.cos") },
  { id: "tanh",    label: "tanh",      re: /(?:math|torch|np|numpy|F)\.tanh\s*\(/g,       eml: 45,  best: 25, op: "EML+EDL", note: "mul+exp+sub+add+div via EDL (25n vs 45n)",          sub: s => s.replace(/(?:math|torch|np|numpy|F)\.tanh/, "BEST.tanh") },
  { id: "sigmoid", label: "sigmoid",   re: /(?:torch|F)\.sigmoid\s*\(/g,                 eml: 36,  best: 19, op: "EML+EDL", note: "neg+exp+add+div via EDL (19n vs 36n)",              sub: s => s.replace(/(?:torch|F)\.sigmoid/, "BEST.sigmoid") },
  { id: "gelu",    label: "F.gelu",    re: /F\.gelu\s*\(/g,                              eml: 17,  best: 14, op: "EML+EDL", note: "exp+add+recip_edl = 14n vs 17n (tanh formula)",     sub: s => s.replace(/F\.gelu/, "BEST.gelu") },
  { id: "log",     label: "log / ln",  re: /(?:math|torch|np|numpy|F)\.log\w*\s*\(/g,    eml: 3,   best: 1,  op: "EXL",     note: "EXL ln: 1n vs EML's 3n",                           sub: s => s.replace(/(?:math|torch|np|numpy|F)\.log\w*/, "BEST.ln") },
  { id: "exp",     label: "exp",       re: /(?:math|torch|np|numpy|F)\.exp\s*\(/g,        eml: 1,   best: 1,  op: "EML",     note: "same cost across all operators",                    sub: null },
  { id: "pow_fn",  label: "pow(x,n)",  re: /(?:math|torch|np|numpy)\.pow(?:er)?\s*\(/g,  eml: 15,  best: 3,  op: "EXL",     note: "EXL pow: 3n vs EML's 15n",                         sub: s => s.replace(/(?:math|torch|np|numpy)\.pow(?:er)?/, "BEST.pow") },
  { id: "pow_op",  label: "x ** n",    re: /\*\*\s*[\d.]+/g,                             eml: 15,  best: 3,  op: "EXL",     note: "EXL pow: 3n vs EML's 15n — simple forms rewritten", sub: null },
  { id: "sqrt",    label: "sqrt",      re: /(?:math|torch|np|numpy)\.sqrt\s*\(/g,         eml: 15,  best: 3,  op: "EXL",     note: "pow(x, 0.5) via EXL: 3n",                          sub: s => s.replace(/(?:math|torch|np|numpy)\.sqrt/, "BEST.sqrt") },
  { id: "div_fn",  label: "torch.div", re: /(?:torch\.div|np\.divide)\s*\(/g,            eml: 15,  best: 1,  op: "EDL",     note: "EDL div: 1n vs EML's 15n",                         sub: s => s.replace(/(?:torch\.div|np\.divide)/, "BEST.div") },
  { id: "mul_fn",  label: "torch.mul", re: /(?:torch\.mul|np\.multiply)\s*\(/g,          eml: 13,  best: 7,  op: "EDL",     note: "EDL mul: 7n vs EML's 13n",                         sub: s => s.replace(/(?:torch\.mul|np\.multiply)/, "BEST.mul") },
];

// Measured in experiment_09 (TinyMLP, Python CPU).
const BENCHMARKS = {
  sin:    { speedup: 2.8, label: "sin Taylor (8 terms)" },
  cos:    { speedup: 2.8, label: "cos Taylor (8 terms)" },
  pow_fn: { speedup: 4.8, label: "pow(x, n)" },
  pow_op: { speedup: 4.8, label: "x ** n" },
};

const EXAMPLES = [
  {
    label: "TinyMLP",
    code: `import torch
import torch.nn as nn

class TinyMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(1, 16)
        self.fc2 = nn.Linear(16, 1)

    def forward(self, x):
        x = torch.sin(self.fc1(x)) ** 2
        x = torch.cos(x) * x ** 3
        return self.fc2(x)`,
  },
  {
    label: "sin + cos",
    code: `import torch

def wave(x):
    return torch.sin(x) + torch.cos(x)`,
  },
  {
    label: "FFN block",
    code: `import torch
import torch.nn.functional as F

class FFNBlock(nn.Module):
    def __init__(self, d, hidden):
        super().__init__()
        self.w1 = nn.Linear(d, hidden)
        self.w2 = nn.Linear(hidden, d)

    def forward(self, x):
        return self.w2(F.gelu(self.w1(x)))

    def encode(self, x):
        h = torch.sigmoid(self.w1(x))
        return torch.tanh(h) * x`,
  },
  {
    label: "Taylor term",
    code: `import math

def taylor_sin_term(x, k):
    n = 2 * k + 1
    return math.pow(x, n) / math.factorial(n)`,
  },
  {
    label: "NumPy",
    code: `import numpy as np

y = np.sin(x) + np.cos(x) / np.power(x, 2)`,
  },
];


// ── Source parsing ─────────────────────────────────────────────────────────────

/**
 * Split source into function blocks by `def` boundaries.
 * Returns [{name, body}] sorted by appearance.
 * Simple: uses indentation of the `def` line as the block's base.
 */
function parseFunctions(src) {
  const defRe = /^([ \t]*)def\s+(\w+)\s*\(/gm;
  const positions = [];
  let m;
  while ((m = defRe.exec(src)) !== null) {
    positions.push({ name: m[2], indent: m[1].length, startIdx: m.index });
  }
  if (positions.length === 0) return [];

  return positions.map((pos, i) => {
    // End at the next def at same-or-lesser indent, or end of source.
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


// ── Core analysis ──────────────────────────────────────────────────────────────

function analyzeCode(src) {
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

  // Apply named-function substitutions (sin, cos, log, pow_fn, etc.)
  let rewritten = src;
  for (const rule of RULES) {
    if (!rule.sub) continue;
    rule.re.lastIndex = 0;
    rewritten = rewritten.replace(rule.re, m => rule.sub(m));
  }

  // Rewrite simple `identifier**n` → `BEST.pow(identifier, n)`.
  // Handles: x**2, h**3, self.x**2.  Does NOT handle fn(x)**2 (complex LHS).
  rewritten = rewritten.replace(
    /\b([a-zA-Z_][\w.]*)\s*\*\*\s*([\d.]+)/g,
    "BEST.pow($1, $2)",
  );

  // Prepend import if anything substantive changed.
  const hasGains = matches.some(m => m.best < m.eml);
  if (hasGains && !rewritten.startsWith("from monogate")) {
    rewritten = "from monogate import BEST\n\n" + rewritten;
  }

  return { matches, totalEml, totalBest, rewritten, topBenchmark };
}

function analyzeAll(src) {
  if (!src.trim()) return null;

  const overall  = analyzeCode(src);
  const fnBlocks = parseFunctions(src);

  // Per-function breakdown — skip functions with no recognized ops.
  const functions = fnBlocks
    .map(fn => ({ name: fn.name, result: analyzeCode(fn.body) }))
    .filter(fr => fr.result && fr.result.matches.length > 0);

  return { overall, functions };
}


// ── Small components ───────────────────────────────────────────────────────────

function OpPill({ op }) {
  const s = PILL[op] || PILL.EML;
  return (
    <span style={{
      fontSize: 9, padding: "1px 6px", borderRadius: 3, flexShrink: 0,
      background: s.bg, border: `1px solid ${s.border}`, color: s.color,
      fontWeight: 700, letterSpacing: "0.04em",
    }}>{op}</span>
  );
}

function SavingsBadge({ pct, small = false }) {
  if (!pct || pct <= 0) return null;
  return (
    <span style={{
      fontSize: small ? 9 : 11,
      padding: small ? "1px 6px" : "3px 10px",
      borderRadius: 4, fontWeight: 700,
      background: "rgba(94,196,122,0.10)",
      border: `1px solid #5ec47a`,
      color: "#5ec47a",
    }}>
      {pct}% fewer nodes
    </span>
  );
}

function OpTable({ matches, totalEml, totalBest }) {
  return (
    <div>
      {matches.map(m => {
        const savPct = m.eml > 0 ? Math.round((1 - m.best / m.eml) * 100) : 0;
        return (
          <div key={m.id} style={{
            display: "grid", gridTemplateColumns: "1fr 70px 76px 76px",
            alignItems: "center", gap: 8,
            padding: "6px 0", borderBottom: `1px solid ${C.border}`,
          }}>
            <div>
              <span style={{ fontSize: 11, color: C.text }}>{m.label}</span>
              {m.count > 1 && (
                <span style={{ fontSize: 9, color: C.muted, marginLeft: 6 }}>×{m.count}</span>
              )}
              <div style={{ fontSize: 9, color: C.muted, marginTop: 1 }}>{m.note}</div>
            </div>
            <OpPill op={m.op} />
            <div style={{ textAlign: "right" }}>
              <span style={{ fontSize: 11, color: savPct > 0 ? C.accent : C.muted }}>
                {m.count * m.best}n
              </span>
              <span style={{ fontSize: 9, color: C.muted }}> BEST</span>
            </div>
            <div style={{ textAlign: "right" }}>
              <span style={{
                fontSize: 11, color: C.muted,
                textDecoration: savPct > 0 ? "line-through" : "none",
              }}>
                {m.count * m.eml}n
              </span>
              <span style={{ fontSize: 9, color: C.muted }}> EML</span>
            </div>
          </div>
        );
      })}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 70px 76px 76px",
        alignItems: "center", gap: 8, paddingTop: 8,
      }}>
        <span style={{ fontSize: 10, color: C.muted, textTransform: "uppercase", letterSpacing: "0.06em" }}>
          Total
        </span>
        <span />
        <span style={{ fontSize: 13, fontWeight: 700, color: C.accent, textAlign: "right" }}>
          {totalBest}n
        </span>
        <span style={{ fontSize: 13, color: C.muted, textAlign: "right", textDecoration: "line-through" }}>
          {totalEml}n
        </span>
      </div>
    </div>
  );
}

function CodePane({ code, label, accentColor, copyKey, copiedKey, onCopy }) {
  const isCopied = copiedKey === copyKey;
  return (
    <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6,
      }}>
        <span style={{
          fontSize: 9, color: accentColor || C.muted,
          textTransform: "uppercase", letterSpacing: "0.06em",
        }}>{label}</span>
        {onCopy && (
          <button onClick={onCopy} style={{
            padding: "2px 8px", fontSize: 9, borderRadius: 3, cursor: "pointer",
            border: `1px solid ${isCopied ? C.green : C.border}`,
            background: isCopied ? "rgba(94,196,122,0.08)" : "transparent",
            color: isCopied ? C.green : C.muted,
            fontFamily: "'Space Mono', monospace",
          }}>
            {isCopied ? "✓ copied" : "⎘ copy"}
          </button>
        )}
      </div>
      <pre style={{
        margin: 0, padding: "10px 12px", flex: 1,
        background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6,
        fontSize: 10, color: C.text, lineHeight: 1.65,
        fontFamily: "'Space Mono', monospace",
        whiteSpace: "pre-wrap", wordBreak: "break-word",
        overflowX: "auto", minHeight: 80,
      }}>
        {code}
      </pre>
    </div>
  );
}


// ── Main component ─────────────────────────────────────────────────────────────

export default function OptimizeTab() {
  const [src,         setSrc]         = useState("");
  const [result,      setResult]      = useState(null);
  const [copiedKey,   setCopiedKey]   = useState(null);
  const [expandedFns, setExpandedFns] = useState(new Set());
  const [toast,       setToast]       = useState(null); // { label }

  const runAnalysis = () => {
    const r = analyzeAll(src);
    setResult(r);
    // Default all functions open for the first impression.
    if (r?.functions?.length > 1) {
      setExpandedFns(new Set(r.functions.map(f => f.name)));
    } else {
      setExpandedFns(new Set());
    }
  };

  const copy = (key, text, label) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000);
      setToast({ label });
      setTimeout(() => setToast(null), 2000);
    });
  };

  const overall  = result?.overall;
  const savings  = overall && overall.totalEml > 0
    ? Math.round((1 - overall.totalBest / overall.totalEml) * 100)
    : 0;

  // "Copy Rewritten" — just the rewritten source (with import).
  const rewrittenCode = overall?.rewritten ?? "";

  // "Copy as Python" — adds install comment, ready to paste as a standalone script.
  const pythonSnippet =
    "# pip install monogate\n" +
    (rewrittenCode.startsWith("from monogate")
      ? rewrittenCode
      : `from monogate import BEST\n\n${rewrittenCode}`);

  const card = {
    background: C.surface, border: `1px solid ${C.border}`,
    borderRadius: 8, padding: 16, marginBottom: 12,
  };

  const btnBase = {
    padding: "5px 12px", fontSize: 10, borderRadius: 4, cursor: "pointer",
    border: `1px solid ${C.border}`, background: "transparent",
    color: C.muted, fontFamily: "'Space Mono', monospace", letterSpacing: "0.04em",
  };

  const noOps =
    result &&
    (!overall || overall.matches.length === 0) &&
    result.functions.length === 0;

  const showAccordion = result && result.functions.length > 1;
  const showFlatTable =
    result && !showAccordion && overall && overall.matches.length > 0;

  return (
    <div style={{ overflowX: "hidden" }}>

      {/* ── Toast ── */}
      {toast && (
        <div style={{
          position: "fixed", bottom: 24, right: 24, zIndex: 9999,
          padding: "8px 16px", borderRadius: 6,
          background: "#0d0e1c", border: `1px solid ${C.green}`,
          color: C.green, fontSize: 11, fontFamily: "'Space Mono', monospace",
          boxShadow: "0 4px 16px rgba(0,0,0,0.5)",
          pointerEvents: "none",
          animation: "fadeInUp 0.15s ease",
        }}>
          ✓ {toast.label}
        </div>
      )}

      {/* ── Header ── */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: C.accent, marginBottom: 4 }}>
          ⚙ Optimize My Code
        </div>
        <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.7 }}>
          Paste a Python / NumPy / PyTorch snippet or class definition. Each math op
          is routed to the cheapest operator — EXL for{" "}
          <code style={{ color: C.text }}>pow / ln</code>, EDL for{" "}
          <code style={{ color: C.text }}>div / mul</code>, EML for{" "}
          <code style={{ color: C.text }}>add / sub</code>. Classes with multiple
          methods show a per-function breakdown.
        </div>
      </div>

      {/* ── Examples ── */}
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 10 }}>
        <span style={{
          fontSize: 9, color: C.muted, alignSelf: "center",
          textTransform: "uppercase", letterSpacing: "0.06em", marginRight: 2,
        }}>
          examples
        </span>
        {EXAMPLES.map(ex => (
          <button
            key={ex.label}
            onClick={() => {
              const r = analyzeAll(ex.code);
              setSrc(ex.code);
              setResult(r);
              setExpandedFns(
                r?.functions?.length > 1
                  ? new Set(r.functions.map(f => f.name))
                  : new Set()
              );
            }}
            style={{ ...btnBase, padding: "4px 10px", background: C.tag }}
          >
            {ex.label}
          </button>
        ))}
      </div>

      {/* ── Input ── */}
      <div style={card}>
        <textarea
          value={src}
          onChange={e => setSrc(e.target.value)}
          placeholder={"Paste Python / NumPy / PyTorch code here…\n\nExamples:\n  y = torch.sin(x) ** 2 + torch.cos(x) * x ** 3\n  class MyModel(nn.Module): ..."}
          rows={9}
          style={{
            width: "100%", padding: "10px 14px",
            background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6,
            color: C.text, fontFamily: "'Space Mono', monospace", fontSize: 11,
            outline: "none", resize: "vertical", lineHeight: 1.6,
            boxSizing: "border-box",
          }}
          onFocus={e => { e.target.style.borderColor = C.accent; }}
          onBlur={e  => { e.target.style.borderColor = C.border; }}
          onKeyDown={e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) runAnalysis(); }}
        />
        <div style={{ fontSize: 9, color: C.muted, marginTop: 8, lineHeight: 1.5 }}>
          Supports common PyTorch / NumPy patterns. Complex expressions may need manual wrapping.
        </div>
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          marginTop: 8, flexWrap: "wrap", gap: 6,
        }}>
          <span style={{ fontSize: 9, color: C.muted }}>⌘↵ / Ctrl↵ to analyze</span>
          <button onClick={runAnalysis} style={{
            ...btnBase, padding: "7px 18px", fontSize: 11, fontWeight: 700,
            color: C.accent, border: `1px solid ${C.accent}`,
            background: "rgba(232,160,32,0.08)",
          }}>
            Analyze →
          </button>
        </div>
      </div>

      {/* ── No ops found ── */}
      {noOps && (
        <div style={{ ...card, color: C.muted, fontSize: 11 }}>
          No recognized math operations found. Supported:{" "}
          <code style={{ color: C.text }}>
            math.exp, math.log, math.sin, math.cos, torch.sigmoid, torch.tanh,
            F.gelu, np.power, x**n
          </code>
          , etc.
        </div>
      )}

      {/* ── Results ── */}
      {result && !noOps && (
        <>
          {/* Summary bar */}
          <div style={{
            ...card, padding: "12px 16px",
            display: "flex", justifyContent: "space-between",
            alignItems: "center", flexWrap: "wrap", gap: 8,
          }}>
            <div>
              {savings > 0
                ? <SavingsBadge pct={savings} />
                : <span style={{ fontSize: 11, color: C.muted }}>No node savings — expression is already EML-optimal</span>
              }
            </div>
            {overall?.topBenchmark?.speedup && (
              <span style={{ fontSize: 9, color: C.muted }}>
                ≈ {overall.topBenchmark.speedup}× wall-clock speedup
                <span style={{ opacity: 0.55 }}> (measured, experiment_09)</span>
              </span>
            )}
          </div>

          {/* Per-function accordion — only when 2+ functions have recognized ops */}
          {showAccordion && (
            <div style={{ ...card, padding: "12px 16px" }}>
              <div style={{
                fontSize: 9, color: C.muted, textTransform: "uppercase",
                letterSpacing: "0.06em", marginBottom: 10,
              }}>
                {result.functions.length} functions with recognized operations
              </div>
              {result.functions.map(fn => {
                const fnSav = fn.result.totalEml > 0
                  ? Math.round((1 - fn.result.totalBest / fn.result.totalEml) * 100)
                  : 0;
                const isOpen = expandedFns.has(fn.name);
                const toggle = () => {
                  const next = new Set(expandedFns);
                  if (isOpen) next.delete(fn.name); else next.add(fn.name);
                  setExpandedFns(next);
                };
                return (
                  <div key={fn.name} style={{ marginBottom: 4 }}>
                    {/* Row header */}
                    <div
                      onClick={toggle}
                      style={{
                        display: "flex", justifyContent: "space-between",
                        alignItems: "center", padding: "8px 10px",
                        borderRadius: isOpen ? "5px 5px 0 0" : 5, cursor: "pointer",
                        background: isOpen ? "rgba(232,160,32,0.05)" : C.tag,
                        border: `1px solid ${isOpen ? C.accent : C.border}`,
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <code style={{ fontSize: 10, color: isOpen ? C.accent : C.text }}>
                          {fn.name}()
                        </code>
                        <span style={{ fontSize: 9, color: C.muted }}>
                          {fn.result.matches.length} op{fn.result.matches.length !== 1 ? "s" : ""}
                        </span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <SavingsBadge pct={fnSav} small />
                        <span style={{ fontSize: 9, color: C.muted }}>{isOpen ? "▲" : "▼"}</span>
                      </div>
                    </div>
                    {/* Expanded body */}
                    {isOpen && (
                      <div style={{
                        padding: "10px 12px",
                        background: C.bg,
                        border: `1px solid ${C.accent}`,
                        borderTop: "none",
                        borderRadius: "0 0 5px 5px",
                      }}>
                        <OpTable
                          matches={fn.result.matches}
                          totalEml={fn.result.totalEml}
                          totalBest={fn.result.totalBest}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Flat op table — expression or single function */}
          {showFlatTable && (
            <div style={card}>
              <div style={{
                fontSize: 9, color: C.muted, textTransform: "uppercase",
                letterSpacing: "0.06em", marginBottom: 10,
              }}>
                Detected operations
              </div>
              <OpTable
                matches={overall.matches}
                totalEml={overall.totalEml}
                totalBest={overall.totalBest}
              />
            </div>
          )}

          {/* Side-by-side + copy buttons */}
          {savings > 0 && (
            <div style={{ ...card, padding: "14px 16px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                <CodePane
                  code={src.trim()}
                  label="before"
                />
                <CodePane
                  code={rewrittenCode}
                  label="after · monogate BEST"
                  accentColor={C.green}
                  copyKey="rewritten"
                  copiedKey={copiedKey}
                  onCopy={() => copy("rewritten", rewrittenCode)}
                />
              </div>

              {/* Copy buttons */}
              <div style={{ display: "flex", gap: 6, justifyContent: "flex-end", flexWrap: "wrap" }}>
                <button
                  onClick={() => copy("rewritten", rewrittenCode, "Rewritten code copied")}
                  style={{
                    ...btnBase,
                    color: copiedKey === "rewritten" ? C.green : C.muted,
                    border: `1px solid ${copiedKey === "rewritten" ? C.green : C.border}`,
                    background: copiedKey === "rewritten" ? "rgba(94,196,122,0.08)" : "transparent",
                  }}
                >
                  {copiedKey === "rewritten" ? "✓ Copied" : "⎘ Copy Rewritten"}
                </button>
                <button
                  onClick={() => copy("python", pythonSnippet, "Python snippet copied")}
                  style={{
                    ...btnBase,
                    color: copiedKey === "python" ? C.green : C.accent,
                    border: `1px solid ${copiedKey === "python" ? C.green : C.accent}`,
                    background: copiedKey === "python"
                      ? "rgba(94,196,122,0.08)"
                      : "rgba(232,160,32,0.06)",
                  }}
                >
                  {copiedKey === "python" ? "✓ Copied" : "⎘ Copy as Python"}
                </button>
              </div>

              <div style={{ fontSize: 9, color: C.muted, marginTop: 10, lineHeight: 1.6 }}>
                Structural substitution — verify function signatures match your usage.
                Note: <code style={{ color: C.text }}>fn(x)**n</code> requires manual
                wrapping as <code style={{ color: C.text }}>BEST.pow(fn(x), n)</code>.
                Install: <code style={{ color: C.text }}>pip install monogate</code>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── Empty state ── */}
      {!result && (
        <div style={{ ...card, color: C.muted, fontSize: 11, lineHeight: 1.9 }}>
          <div style={{ marginBottom: 8, color: C.text, fontSize: 10 }}>What this tool does:</div>
          <div>① Scans your code for <code>math.*</code> / <code>np.*</code> / <code>torch.*</code> operations</div>
          <div>② Routes each to the cheapest operator (EXL for pow/ln, EDL for div/mul, EML for add/sub)</div>
          <div>③ Reports node count reduction — directly proportional to exp/ln call savings</div>
          <div>④ For classes with multiple methods, shows per-function savings in a collapsible view</div>
          <div>⑤ Generates a side-by-side diff + ready-to-paste Python snippet</div>
          <div style={{
            marginTop: 12, padding: "8px 12px",
            background: C.tag, borderRadius: 6, fontSize: 10, lineHeight: 1.7,
          }}>
            <span style={{ color: C.accent, fontWeight: 700 }}>Real benchmark (experiment_09):</span>
            <span style={{ color: C.text }}>
              {" "}TinyMLP + sin activation: 39 ms → 14 ms per forward pass (2.8× faster, 74% fewer nodes)
            </span>
          </div>
          <div style={{
            marginTop: 8, padding: "8px 12px",
            background: C.tag, borderRadius: 6, fontSize: 10, lineHeight: 1.7,
          }}>
            <span style={{ color: C.muted, fontWeight: 700 }}>Crossover threshold:</span>
            <span style={{ color: C.text }}>
              {" "}≥21% node savings → wall-clock speedup. Below that, call overhead dominates.
            </span>
          </div>
        </div>
      )}

    </div>
  );
}
