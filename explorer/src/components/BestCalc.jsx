import { useState, useEffect, useRef } from "react";
import { evalExpr } from "../calc-engine.js";

// ── Colors (matches App.jsx) ───────────────────────────────────────────────────
const C = {
  bg: "#07080f", surface: "#0d0e1c", border: "#191b2e",
  text: "#cdd0e0", muted: "#4e5168", accent: "#e8a020",
  blue: "#6ab0f5", green: "#5ec47a", red: "#e05060", tag: "#1a1c2e",
};

const PILL = {
  EML:     { bg: "rgba(124,111,247,0.14)", border: "#7c6ff7", color: "#a09cf7" },
  EDL:     { bg: "rgba(45,212,191,0.10)", border: "#2dd4bf", color: "#2dd4bf" },
  EXL:     { bg: "rgba(245,158,11,0.12)", border: "#f59e0b", color: "#f5b435" },
};

// ── Formatters ────────────────────────────────────────────────────────────────
function fmt(v) {
  if (v === null || !isFinite(v)) return "—";
  if (v === 0) return "0";
  const a = Math.abs(v);
  if (a < 0.0001 || a >= 1e7) return v.toExponential(6);
  return parseFloat(v.toPrecision(10)).toString();
}

function fmtErr(e) {
  if (e === null || !isFinite(e)) return "—";
  if (e === 0 || e < 5e-17) return "< 5e−17";
  if (e < 1e-14) return "< 1e−14";
  return e.toExponential(2);
}

// ── Quick-insert buttons ──────────────────────────────────────────────────────
const QUICK = [
  { label: "sin(x)",   ins: "sin(x)" },
  { label: "cos(x)",   ins: "cos(x)" },
  { label: "exp(x)",   ins: "exp(x)" },
  { label: "ln(x)",    ins: "ln(x)"  },
  { label: "x²",       ins: "x^2"   },
  { label: "x³",       ins: "x^3"   },
  { label: "1/x",      ins: "1/x"   },
  { label: "x·ln(x)",  ins: "x*ln(x)" },
];

const PRESETS = [
  { label: "sin(x)+cos(x)",   expr: "sin(x)+cos(x)"   },
  { label: "exp(x)·ln(x+1)",  expr: "exp(x)*ln(x+1)"  },
  { label: "x³+2·x",          expr: "x^3+2*x"          },
  { label: "sin(x)/x",        expr: "sin(x)/x"          },
  { label: "pow(x,4)−x²",     expr: "pow(x,4)-x^2"     },
];

const MODES = [
  { id: "best", label: "✦ BEST" },
  { id: "eml",  label: "EML"   },
  { id: "exl",  label: "EXL"   },
  { id: "edl",  label: "EDL"   },
];

const MODE_DESC = {
  best: "Routes each op to its optimal operator — 71.2% fewer nodes on average (SuperBEST FINAL)",
  eml:  "Pure EML — exp(x)−ln(y) for every node",
  exl:  "EXL only — exp(x)·ln(y) — excels at ln and pow, incomplete for add/sub",
  edl:  "EDL only — exp(x)/ln(y) — excels at div and mul, requires e as constant",
};

// ── Python export helper ──────────────────────────────────────────────────────
function exprToPython(expr, mode) {
  const ns = mode === "best" ? "BEST" : mode === "eml" ? "EML" : mode === "exl" ? "EXL" : "EDL";
  return expr
    .replace(/\bsin\b/g, `${ns}.sin`)
    .replace(/\bcos\b/g, `${ns}.cos`)
    .replace(/\bexp\b/g, `${ns}.exp`)
    .replace(/\bln\b/g,  `${ns}.ln`)
    .replace(/\bpow\b/g, `${ns}.pow`)
    .replace(/\bsqrt\b/g,`${ns}.sqrt`)
    .replace(/\babs\b/g, "abs")
    .replace(/\^/g, "**")
    .replace(/\bpi\b/g, "math.pi");
}

function makePySnippet(expr, mode, totalNodes, emlNodes) {
  const pyExpr = exprToPython(expr, mode);
  const modeUp = mode.toUpperCase();
  const nodeNote = emlNodes && mode === "best" && totalNodes < emlNodes
    ? `# ${totalNodes} nodes BEST  (vs ${emlNodes} pure EML — ${Math.round((1 - totalNodes / emlNodes) * 100)}% fewer exp/ln calls)`
    : `# ${totalNodes} nodes (${modeUp} mode)`;
  return [
    `from monogate import ${mode === "best" ? "BEST" : mode === "eml" ? "EML" : mode === "exl" ? "EXL" : "EDL"}`,
    "import math",
    "",
    "def f(x):",
    `    ${nodeNote}`,
    `    return ${pyExpr}`,
  ].join("\n");
}

function makeEmbedSnippet(expr, mode) {
  const p = new URLSearchParams();
  p.set("expr", expr);
  if (mode !== "best") p.set("mode", mode);
  const src = `${window.location.origin}${window.location.pathname}?${p.toString()}`;
  return `<iframe\n  src="${src}"\n  width="780"\n  height="620"\n  frameborder="0"\n  style="background:#07080f;border-radius:8px;border:1px solid #191b2e;"\n></iframe>`;
}

// ── OperatorPill ──────────────────────────────────────────────────────────────
function OpPill({ op }) {
  const s = PILL[op] || PILL.EML;
  return (
    <span style={{
      fontSize: 9, padding: "1px 6px", borderRadius: 3,
      background: s.bg, border: `1px solid ${s.border}`, color: s.color,
      fontWeight: 700, letterSpacing: "0.04em",
    }}>{op}</span>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function BestCalc() {
  // ── Read URL params on first mount ──────────────────────────────────────────
  const initParams = () => {
    const p = new URLSearchParams(window.location.search);
    return {
      expr: p.get("expr") ? decodeURIComponent(p.get("expr")) : "x^3 + sin(x)",
      mode: ["best","eml","exl","edl"].includes(p.get("mode")) ? p.get("mode") : "best",
    };
  };
  const init = initParams();

  const [expr,      setExpr]      = useState(init.expr);
  const [xVal,      setXVal]      = useState(1.0);
  const [mode,      setMode]      = useState(init.mode);
  const [result,    setResult]    = useState(null);
  const [evalError, setEvalError] = useState(null);
  const [showTree,  setShowTree]  = useState(true);
  const [live,       setLive]      = useState(false);
  const [copied,     setCopied]    = useState(false);
  const [copiedPy,   setCopiedPy]  = useState(false);
  const [copiedEmbed,setCopiedEmbed] = useState(false);
  const [showExport, setShowExport] = useState(false);
  const inputRef = useRef(null);

  // ── Sync expr+mode to URL (no navigation) ──────────────────────────────────
  useEffect(() => {
    const p = new URLSearchParams();
    p.set("expr", expr);
    if (mode !== "best") p.set("mode", mode);
    const qs = p.toString();
    history.replaceState(null, "", qs ? "?" + qs : window.location.pathname);
  }, [expr, mode]);

  // ── Debounced evaluation ────────────────────────────────────────────────────
  useEffect(() => {
    setLive(true);
    const t = setTimeout(() => {
      if (!expr.trim()) { setResult(null); setEvalError(null); setLive(false); return; }
      const r = evalExpr(expr, xVal, mode);
      if (!r) { setResult(null); setEvalError(null); }
      else if (r.error) { setEvalError(r.error); setResult(null); }
      else               { setResult(r);          setEvalError(null); }
      setLive(false);
    }, 150);
    return () => clearTimeout(t);
  }, [expr, xVal, mode]);

  const hasX     = /\bx\b/.test(expr);
  const savings  = result && result.emlNodes && mode === "best"
    ? Math.round((1 - result.totalNodes / result.emlNodes) * 100)
    : 0;
  const maxNodes = result ? Math.max(...result.nodeLog.map(e => e.nodes), 1) : 1;

  // ── Helpers ─────────────────────────────────────────────────────────────────
  // Quick buttons always replace — avoids "xsin(x)" concatenation bugs
  const handleInsert = (text) => {
    setExpr(text);
    inputRef.current?.focus();
  };

  // ── Styles ──────────────────────────────────────────────────────────────────
  const card = {
    background: C.surface, border: `1px solid ${C.border}`,
    borderRadius: 8, padding: 16, marginBottom: 12,
  };

  const btnBase = {
    padding: "5px 12px", fontSize: 10, borderRadius: 4, border: `1px solid ${C.border}`,
    background: "transparent", color: C.muted, cursor: "pointer",
    fontFamily: "'Space Mono', monospace", letterSpacing: "0.04em",
    transition: "border-color 0.15s, color 0.15s",
  };

  const btnActive = { ...btnBase,
    background: "rgba(232,160,32,0.10)", border: `1px solid ${C.accent}`,
    color: C.accent,
  };

  const quickBtn = {
    ...btnBase, padding: "4px 10px", fontSize: 10,
    background: C.tag,
  };

  // Unique operators used — shown in collapsed breakdown header
  const usedOps = result
    ? [...new Set(result.nodeLog.map(e => e.op))]
    : [];

  return (
    <div style={{ overflowX: "hidden" }}>
      {/* Title + powered-by badge + copy link */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
        gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: C.accent }}>✦ BEST Calc</span>
          <span style={{ fontSize: 9, color: C.muted }}>
            powered by BEST hybrid — routes each op to its optimal base operator
          </span>
        </div>
        <button
          onClick={() => {
            navigator.clipboard.writeText(window.location.href).then(() => {
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            });
          }}
          style={{ ...btnBase, padding: "4px 10px", fontSize: 9,
            color: copied ? C.green : C.muted,
            borderColor: copied ? C.green : C.border,
            background: copied ? "rgba(94,196,122,0.08)" : "transparent",
            flexShrink: 0,
          }}>
          {copied ? "✓ copied" : "⎘ share"}
        </button>
      </div>

      {/* How to use */}
      <div style={{ fontSize: 10, color: C.muted, marginBottom: 12, lineHeight: 1.7 }}>
        Tap a function to load it · drag x to change the input · switch modes to compare node counts.
        To combine, type in the box: <code style={{ color: C.accent }}>sin(x)+cos(x)</code>
      </div>

      {/* Mode selector */}
      <div style={{ ...card, padding: "12px 16px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {MODES.map(m => (
              <button key={m.id}
                onClick={() => setMode(m.id)}
                style={m.id === "best"
                  ? (mode === "best"
                    ? { ...btnActive, fontWeight: 700, fontSize: 11 }
                    : { ...btnBase, color: C.accent, borderColor: "rgba(232,160,32,0.4)", fontSize: 11 })
                  : (mode === m.id ? btnActive : btnBase)
                }>
                {m.label}
              </button>
            ))}
          </div>
          <span style={{ fontSize: 10, color: C.muted }}>
            {MODE_DESC[mode]}
          </span>
        </div>
      </div>

      {/* Input + quick buttons */}
      <div style={card}>
        <input
          ref={inputRef}
          type="text"
          value={expr}
          onChange={e => setExpr(e.target.value)}
          onKeyDown={e => e.key === "Enter" && inputRef.current?.blur()}
          placeholder="e.g. sin(x) + ln(x+1)"
          style={{
            width: "100%", padding: "10px 14px", marginBottom: 10,
            background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6,
            color: C.text, fontFamily: "'Space Mono', monospace", fontSize: 13,
            outline: "none",
          }}
          onFocus={e => { e.target.style.borderColor = C.accent; }}
          onBlur={e  => { e.target.style.borderColor = C.border; }}
        />

        {/* Quick-insert */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 8, maxWidth: "100%" }}>
          {QUICK.map(q => (
            <button key={q.label} onClick={() => handleInsert(q.ins)} style={quickBtn}>
              {q.label}
            </button>
          ))}
        </div>

        {/* Preset expressions */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, alignItems: "center" }}>
          <span style={{ fontSize: 9, color: C.muted, marginRight: 2, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            presets
          </span>
          {PRESETS.map(p => (
            <button key={p.label} onClick={() => setExpr(p.expr)}
              style={{ ...quickBtn, background: "transparent", color: C.muted,
                border: `1px solid ${C.border}` }}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* x slider */}
      {hasX && (
        <div style={{ ...card, padding: "10px 16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 11, color: C.muted, minWidth: 14 }}>x</span>
            <input
              type="range"
              min={-6.28} max={6.28} step={0.01}
              value={xVal}
              onChange={e => setXVal(parseFloat(e.target.value))}
              style={{ flex: 1 }}
            />
            <span style={{
              fontSize: 12, color: C.accent, fontFamily: "'Space Mono', monospace",
              minWidth: 54, textAlign: "right", flexShrink: 0,
            }}>{xVal.toFixed(3)}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between",
            fontSize: 9, color: C.muted, marginTop: 3 }}>
            <span>−2π</span><span>0</span><span>+2π</span>
          </div>
        </div>
      )}

      {/* Result */}
      <div style={card}>
        {/* Live indicator row */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 6, minHeight: 14 }}>
          {live && (
            <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 9, color: C.green }}>
              <span style={{
                width: 6, height: 6, borderRadius: "50%",
                background: C.green, display: "inline-block",
                boxShadow: `0 0 4px ${C.green}`,
              }} />
              live
            </span>
          )}
        </div>

        {evalError ? (
          <div style={{ color: C.red, fontSize: 12 }}>⚠ {evalError}</div>
        ) : result ? (
          <>
            {/* Large number */}
            <div style={{ fontSize: 28, fontWeight: 700, color: C.text,
              letterSpacing: "-0.02em", marginBottom: 4, wordBreak: "break-all" }}>
              {fmt(result.value)}
            </div>

            {/* Error vs Math.* */}
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 14 }}>
              vs Math.* &nbsp;error = {fmtErr(result.absError)}
            </div>

            {/* Node count + badge */}
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 5 }}>
                <span style={{ fontSize: 22, fontWeight: 700, color: C.accent }}>
                  {result.totalNodes}
                </span>
                <span style={{ fontSize: 11, color: C.muted }}>nodes</span>
              </div>

              {mode === "best" && result.emlNodes && savings > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{
                    fontSize: 10, padding: "3px 9px", borderRadius: 4,
                    background: "rgba(94,196,122,0.10)", border: `1px solid ${C.green}`,
                    color: C.green, fontWeight: 700,
                  }}>
                    ✦ {savings}% fewer nodes than pure EML
                  </span>
                  <span style={{ fontSize: 9, color: C.muted, paddingLeft: 2 }}>
                    ≈ {savings}% fewer exp/ln calls on CPU
                  </span>
                </div>
              )}

              {mode === "eml" && result.totalNodes > 0 && (
                <span style={{
                  fontSize: 10, padding: "3px 9px", borderRadius: 4,
                  background: "rgba(106,176,245,0.08)", border: `1px solid ${C.blue}`,
                  color: C.blue,
                }}>
                  pure EML baseline
                </span>
              )}
            </div>
          </>
        ) : (
          <div style={{ color: C.muted, fontSize: 12 }}>
            Type an expression above to evaluate
          </div>
        )}
      </div>

      {/* Node breakdown (expandable) */}
      {result && result.nodeLog.length > 0 && (
        <div style={card}>
          <button
            onClick={() => setShowTree(v => !v)}
            style={{ ...btnBase, padding: "4px 10px", fontSize: 10,
              background: "transparent", display: "flex", alignItems: "center", gap: 6,
              flexWrap: "wrap" }}>
            <span style={{ fontSize: 8 }}>{showTree ? "▼" : "▶"}</span>
            <span>Node breakdown</span>
            <span style={{ color: C.muted }}>({result.nodeLog.length} op{result.nodeLog.length > 1 ? "s" : ""})</span>
            {!showTree && usedOps.map(op => <OpPill key={op} op={op} />)}
          </button>

          {showTree && (
            <div style={{ marginTop: 12 }}>
              {result.nodeLog.map((entry, i) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "1fr 52px 32px 80px",
                  alignItems: "center", gap: 6,
                  padding: "5px 0",
                  borderBottom: i < result.nodeLog.length - 1
                    ? `1px solid ${C.border}` : "none",
                }}>
                  <span style={{ fontSize: 11, color: C.text, fontFamily: "'Space Mono', monospace" }}>
                    {entry.fn}
                  </span>
                  <OpPill op={entry.op} />
                  <span style={{ fontSize: 11, color: C.accent, textAlign: "right" }}>
                    {entry.nodes}n
                  </span>
                  <div style={{ height: 4, background: C.border, borderRadius: 2, overflow: "hidden" }}>
                    <div style={{
                      width: `${(entry.nodes / maxNodes) * 100}%`,
                      height: "100%", borderRadius: 2,
                      background: PILL[entry.op]?.border || C.accent,
                      transition: "width 0.3s",
                    }} />
                  </div>
                </div>
              ))}

              {/* Total row */}
              <div style={{
                display: "grid", gridTemplateColumns: "1fr 52px 32px 80px",
                alignItems: "center", gap: 6, paddingTop: 8, marginTop: 4,
                borderTop: `1px solid ${C.border}`,
              }}>
                <span style={{ fontSize: 10, color: C.muted, textTransform: "uppercase",
                  letterSpacing: "0.06em" }}>Total</span>
                <span />
                <span style={{ fontSize: 12, fontWeight: 700, color: C.accent, textAlign: "right" }}>
                  {result.totalNodes}n
                </span>
                {mode === "best" && result.emlNodes && savings > 0 && (
                  <span style={{ fontSize: 9, color: C.green }}>
                    EML baseline: {result.emlNodes}n
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Export row */}
      {result && !evalError && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            <span style={{ fontSize: 9, color: C.muted, textTransform: "uppercase",
              letterSpacing: "0.06em" }}>
              export
            </span>
            <button
              onClick={() => {
                const py = makePySnippet(expr, mode, result.totalNodes, result.emlNodes);
                navigator.clipboard.writeText(py).then(() => {
                  setCopiedPy(true);
                  setTimeout(() => setCopiedPy(false), 2000);
                });
              }}
              style={{ ...btnBase, padding: "3px 9px", fontSize: 9,
                color: copiedPy ? C.green : C.muted,
                borderColor: copiedPy ? C.green : C.border,
                background: copiedPy ? "rgba(94,196,122,0.08)" : "transparent" }}>
              {copiedPy ? "✓ copied" : "⎘ python"}
            </button>
            <button
              onClick={() => setShowExport(v => !v)}
              style={{ ...btnBase, padding: "3px 9px", fontSize: 9,
                color: showExport ? C.accent : C.muted,
                borderColor: showExport ? C.accent : C.border }}>
              {"</>"} embed
            </button>
          </div>

          {showExport && (
            <div style={{
              marginTop: 8, background: C.surface,
              border: `1px solid ${C.border}`, borderRadius: 6, overflow: "hidden",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between",
                alignItems: "center", padding: "8px 12px",
                borderBottom: `1px solid ${C.border}` }}>
                <span style={{ fontSize: 9, color: C.muted, textTransform: "uppercase",
                  letterSpacing: "0.06em" }}>
                  iframe embed code
                </span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(makeEmbedSnippet(expr, mode)).then(() => {
                      setCopiedEmbed(true);
                      setTimeout(() => setCopiedEmbed(false), 2000);
                    });
                  }}
                  style={{ ...btnBase, padding: "2px 8px", fontSize: 9,
                    color: copiedEmbed ? C.green : C.muted,
                    borderColor: copiedEmbed ? C.green : C.border,
                    background: copiedEmbed ? "rgba(94,196,122,0.08)" : "transparent" }}>
                  {copiedEmbed ? "✓ copied" : "⎘ copy"}
                </button>
              </div>
              <pre style={{
                margin: 0, padding: "10px 12px",
                fontFamily: "'Space Mono', monospace", fontSize: 10,
                color: C.blue, lineHeight: 1.7, overflowX: "auto",
                whiteSpace: "pre-wrap", wordBreak: "break-all",
              }}>
                {makeEmbedSnippet(expr, mode)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Supported functions hint */}
      <div style={{ fontSize: 9, color: C.muted, marginTop: 4, lineHeight: 1.8 }}>
        Functions: sin, cos, exp, ln, pow(x,n), sqrt, abs &nbsp;·&nbsp;
        Operators: + − * / ^ &nbsp;·&nbsp;
        Constants: pi, e &nbsp;·&nbsp;
        Variable: x (use slider)
      </div>

      {/* sin(x) challenge showcase */}
      <div style={{ marginTop: 20, borderTop: `1px solid ${C.border}`, paddingTop: 16 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: C.text, marginBottom: 4 }}>
          Open Challenge: exact sin(x) from terminal {"{1}"}
        </div>
        <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.7, marginBottom: 12 }}>
          No finite EML tree using only the constant 1 is known to compute sin(x) exactly.
          Below are the best Taylor constructions using BEST hybrid routing.
          Right-chain topologies are ruled out. Other topology classes remain open.
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 8, marginBottom: 12 }}>
          {[
            { terms: 4,  bestN: 27,  emlN: 105, err: "7.5e-2",  label: "rough" },
            { terms: 8,  bestN: 63,  emlN: 245, err: "7.7e-7",  label: "good"  },
            { terms: 13, bestN: 108, emlN: 420, err: "6.5e-15", label: "machine ε" },
          ].map(row => (
            <div key={row.terms} style={{
              background: C.surface, border: `1px solid ${C.border}`,
              borderRadius: 6, padding: "10px 12px",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 10, color: C.text }}>{row.terms} terms</span>
                <span style={{ fontSize: 9, color: C.muted, fontStyle: "italic" }}>{row.label}</span>
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginBottom: 4 }}>
                <span style={{ fontSize: 16, fontWeight: 700, color: C.accent }}>{row.bestN}</span>
                <span style={{ fontSize: 9, color: C.muted }}>nodes (BEST)</span>
              </div>
              <div style={{ fontSize: 9, color: C.muted, marginBottom: 6 }}>
                vs {row.emlN} pure EML &nbsp;
                <span style={{ color: C.green }}>
                  −{Math.round((1 - row.bestN / row.emlN) * 100)}%
                </span>
              </div>
              <div style={{ fontSize: 9, color: C.muted }}>
                max error: <span style={{ color: parseFloat(row.err) < 1e-10 ? C.green : C.muted }}>{row.err}</span>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button
            onClick={() => { setExpr("sin(x)"); setMode("best"); }}
            style={{ ...btnBase, padding: "5px 12px", fontSize: 10,
              color: C.accent, borderColor: "rgba(232,160,32,0.4)" }}>
            ▶ try sin(x) in BEST
          </button>
          <button
            onClick={() => { setExpr("sin(x)"); setMode("eml"); }}
            style={{ ...btnBase, padding: "5px 12px", fontSize: 10 }}>
            ▶ try sin(x) in EML
          </button>
          <a
            href="https://github.com/agent-maestro/monogate/issues"
            target="_blank" rel="noreferrer"
            style={{ ...btnBase, padding: "5px 12px", fontSize: 10,
              textDecoration: "none", display: "inline-flex", alignItems: "center" }}>
            submit a construction ↗
          </a>
        </div>
      </div>
    </div>
  );
}
