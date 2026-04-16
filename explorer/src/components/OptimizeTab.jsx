import { useState, useEffect, useCallback } from "react";
import {
  API_URL, C, PILL, RULES, CROSSOVER_PCT, BENCHMARKS,
  analyzeAll, mapPythonResponse,
} from "../opt-engine.js";

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

function SavingsBar({ pct }) {
  if (!pct || pct <= 0) return null;
  const color = pct >= 70 ? C.green : pct >= 40 ? C.accent : C.blue;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
      <div style={{ flex: 1, height: 3, borderRadius: 2, background: C.border, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 2, transition: "width 0.4s" }} />
      </div>
      <span style={{ fontSize: 9, color, minWidth: 28, textAlign: "right", fontWeight: 700 }}>
        -{pct}%
      </span>
    </div>
  );
}

function OpTable({ matches, totalEml, totalBest }) {
  return (
    <div>
      {/* Header */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 60px 62px 62px 80px",
        gap: 8, padding: "4px 0 8px", borderBottom: `1px solid ${C.border}`,
        fontSize: 8, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em",
      }}>
        <span>Operation</span>
        <span style={{ textAlign: "center" }}>Family</span>
        <span style={{ textAlign: "right" }}>BEST</span>
        <span style={{ textAlign: "right" }}>EML</span>
        <span style={{ textAlign: "right" }}>Saving</span>
      </div>
      {matches.map(m => {
        const savPct = m.eml > 0 ? Math.round((1 - m.best / m.eml) * 100) : 0;
        return (
          <div key={m.id} style={{
            display: "grid", gridTemplateColumns: "1fr 60px 62px 62px 80px",
            alignItems: "center", gap: 8,
            padding: "7px 0", borderBottom: `1px solid ${C.border}`,
          }}>
            <div>
              <span style={{ fontSize: 11, color: C.text }}>{m.label}</span>
              {m.count > 1 && (
                <span style={{ fontSize: 9, color: C.muted, marginLeft: 6 }}>×{m.count}</span>
              )}
              <div style={{ fontSize: 9, color: C.muted, marginTop: 1 }}>{m.note}</div>
            </div>
            <div style={{ display: "flex", justifyContent: "center" }}>
              <OpPill op={m.op} />
            </div>
            <div style={{ textAlign: "right" }}>
              <span style={{ fontSize: 11, color: savPct > 0 ? C.accent : C.muted }}>
                {m.count * m.best}n
              </span>
            </div>
            <div style={{ textAlign: "right" }}>
              <span style={{
                fontSize: 11, color: C.muted,
                textDecoration: savPct > 0 ? "line-through" : "none",
              }}>
                {m.count * m.eml}n
              </span>
            </div>
            <div>
              <SavingsBar pct={savPct} />
            </div>
          </div>
        );
      })}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 60px 62px 62px 80px",
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
        <div>
          {totalEml > 0 && (
            <SavingsBar pct={Math.round((1 - totalBest / totalEml) * 100)} />
          )}
        </div>
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
  const [apiStatus,   setApiStatus]   = useState("unknown"); // 'unknown'|'available'|'unavailable'
  const [apiMode,     setApiMode]     = useState(false);     // true when result came from Python
  const [analyzing,   setAnalyzing]   = useState(false);

  // Probe the Python API once on mount.
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(1500) })
      .then(r => r.ok ? "available" : "unavailable")
      .catch(() => "unavailable")
      .then(s => { if (!cancelled) setApiStatus(s); });
    return () => { cancelled = true; };
  }, []);

  const runAnalysis = useCallback(async () => {
    if (!src.trim()) return;
    setAnalyzing(true);

    // Try Python API first when available.
    if (apiStatus === "available") {
      try {
        const resp = await fetch(`${API_URL}/optimize`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source: src }),
          signal: AbortSignal.timeout(5000),
        });
        if (resp.ok) {
          const data = await resp.json();
          if (!data.error) {
            const r = mapPythonResponse(data, src);
            setResult(r);
            setApiMode(true);
            setExpandedFns(r.functions.length > 1
              ? new Set(r.functions.map(f => f.name)) : new Set());
            setAnalyzing(false);
            return;
          }
        }
      } catch {
        // fall through to JS analysis
        setApiStatus("unavailable");
      }
    }

    // JS fallback.
    const r = analyzeAll(src);
    setResult(r);
    setApiMode(false);
    if (r?.functions?.length > 1) {
      setExpandedFns(new Set(r.functions.map(f => f.name)));
    } else {
      setExpandedFns(new Set());
    }
    setAnalyzing(false);
  }, [src, apiStatus]);

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

  // "Copy as Python" — prefer the rich snippet from the Python API when available.
  const pythonSnippet = overall?.pythonSnippet
    ? "# pip install monogate\n" + overall.pythonSnippet
    : "# pip install monogate\n" +
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
        <div style={{
          display: "flex", alignItems: "center", gap: 8, marginBottom: 4,
        }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: C.accent }}>
            ⚙ Optimize My Code
          </span>
          {/* API status badge */}
          {apiStatus === "available" && (
            <span style={{
              fontSize: 8, padding: "1px 6px", borderRadius: 3,
              background: "rgba(94,196,122,0.12)", border: "1px solid #5ec47a",
              color: "#5ec47a", fontWeight: 700, letterSpacing: "0.06em",
            }}>
              Python API
            </span>
          )}
          {apiMode && (
            <span style={{
              fontSize: 8, padding: "1px 6px", borderRadius: 3,
              background: "rgba(94,196,122,0.07)", border: "1px solid #3a7a4a",
              color: "#5ec47a", letterSpacing: "0.04em",
            }}>
              AST rewrite
            </span>
          )}
          {apiStatus === "unavailable" && (
            <span style={{
              fontSize: 8, padding: "1px 6px", borderRadius: 3,
              background: "rgba(78,81,104,0.15)", border: `1px solid ${C.border}`,
              color: C.muted, letterSpacing: "0.04em",
            }}>
              JS mode
            </span>
          )}
        </div>
        <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.7 }}>
          Paste a Python / NumPy / PyTorch snippet or class definition. Each math op
          is routed to the cheapest operator — EXL for{" "}
          <code style={{ color: C.text }}>pow / ln</code>, EDL for{" "}
          <code style={{ color: C.text }}>div / mul</code>, EML for{" "}
          <code style={{ color: C.text }}>add / sub</code>.{" "}
          {apiStatus === "available"
            ? <span style={{ color: C.green }}>Using real Python best_optimize() via local API.</span>
            : <span>Start <code style={{ color: C.text }}>python api/main.py</code> for Python backend.</span>
          }
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
              setSrc(ex.code);
              // Always re-analyze with current API state when loading an example
              const r = analyzeAll(ex.code);
              setResult(r);
              setApiMode(false);
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
          disabled={analyzing}
        />
        <div style={{ fontSize: 9, color: C.muted, marginTop: 8, lineHeight: 1.5 }}>
          Supports common PyTorch / NumPy patterns. Complex expressions may need manual wrapping.
        </div>
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          marginTop: 8, flexWrap: "wrap", gap: 6,
        }}>
          <span style={{ fontSize: 9, color: C.muted }}>⌘↵ / Ctrl↵ to analyze</span>
          <button onClick={runAnalysis} disabled={analyzing} style={{
            ...btnBase, padding: "7px 18px", fontSize: 11, fontWeight: 700,
            color: analyzing ? C.muted : C.accent,
            border: `1px solid ${analyzing ? C.border : C.accent}`,
            background: analyzing ? "transparent" : "rgba(232,160,32,0.08)",
            cursor: analyzing ? "not-allowed" : "pointer",
          }}>
            {analyzing ? "Analyzing…" : "Analyze →"}
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
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {savings > 0
                ? <SavingsBadge pct={savings} />
                : <span style={{ fontSize: 11, color: C.muted }}>No node savings — expression is already EML-optimal</span>
              }
              {savings > 0 && (
                <span style={{ fontSize: 9, color: savings >= CROSSOVER_PCT ? C.green : C.muted }}>
                  Speedup expected: {savings >= CROSSOVER_PCT ? "YES" : "NO"}
                  {" — "}{savings}% {savings >= CROSSOVER_PCT ? ">" : "<"} {CROSSOVER_PCT}% crossover threshold
                </span>
              )}
            </div>
            {overall?.topBenchmark?.speedup && savings >= CROSSOVER_PCT && (
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
                  onCopy={() => copy("rewritten", rewrittenCode, "Rewritten code copied")}
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
              {" "}≥{CROSSOVER_PCT}% node savings → wall-clock speedup. Below that, call overhead dominates.
            </span>
          </div>
        </div>
      )}

    </div>
  );
}
