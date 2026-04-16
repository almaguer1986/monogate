import { useState, useEffect, useCallback } from "react";
import {
  API_URL, C, PILL, CROSSOVER_PCT, BENCHMARKS,
  analyzeAll, mapPythonResponse,
} from "../opt-engine.js";

// ── Presets ────────────────────────────────────────────────────────────────────

const PRESETS = [
  {
    label: "Minimal SIREN",
    code: `import torch
import torch.nn as nn

class SIREN(nn.Module):
    def __init__(self, in_features=2, hidden=64, out_features=1):
        super().__init__()
        self.linear = nn.Linear(in_features, hidden)
        self.out    = nn.Linear(hidden, out_features)

    def forward(self, x):
        x = torch.sin(30 * self.linear(x))
        return self.out(x)`,
  },
  {
    label: "Deep SIREN",
    code: `import torch
import torch.nn as nn

class DeepSIREN(nn.Module):
    def __init__(self, width=256):
        super().__init__()
        self.layers = nn.ModuleList([
            nn.Linear(2, width),
            nn.Linear(width, width),
            nn.Linear(width, width),
            nn.Linear(width, 1),
        ])

    def forward(self, x):
        x = torch.sin(30 * self.layers[0](x))
        x = torch.sin(30 * self.layers[1](x))
        x = torch.sin(30 * self.layers[2](x))
        return self.layers[3](x)`,
  },
  {
    label: "NeRF + PosEnc",
    code: `import torch
import torch.nn as nn

class NeRFMLP(nn.Module):
    def __init__(self, L=10, hidden=256):
        super().__init__()
        self.L   = L
        in_dim   = 3 + 6 * L
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.out = nn.Linear(hidden, 4)

    def encode(self, x):
        parts = [x]
        for i in range(self.L):
            f = 2 ** i
            parts.append(torch.sin(f * x))
            parts.append(torch.cos(f * x))
        return torch.cat(parts, dim=-1)

    def forward(self, x):
        return self.out(self.net(self.encode(x)))`,
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

function SavingsBadge({ pct }) {
  if (!pct || pct <= 0) return null;
  return (
    <span style={{
      fontSize: 11, padding: "3px 10px", borderRadius: 4, fontWeight: 700,
      background: "rgba(94,196,122,0.10)", border: "1px solid #5ec47a", color: "#5ec47a",
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

// ── Main component ─────────────────────────────────────────────────────────────

export default function NeRFOptimizerTab() {
  const [src,       setSrc]       = useState(PRESETS[0].code);
  const [result,    setResult]    = useState(null);
  const [copied,    setCopied]    = useState(null);  // "rewritten" | "python"
  const [toast,     setToast]     = useState(null);
  const [apiStatus, setApiStatus] = useState("unknown");
  const [apiMode,   setApiMode]   = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

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
            setResult(mapPythonResponse(data));
            setApiMode(true);
            setAnalyzing(false);
            return;
          }
        }
      } catch {
        setApiStatus("unavailable");
      }
    }

    // JS fallback.
    setResult(analyzeAll(src));
    setApiMode(false);
    setAnalyzing(false);
  }, [src, apiStatus]);

  const copy = (key, text, label) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied(null), 2000);
      setToast({ label });
      setTimeout(() => setToast(null), 2000);
    });
  };

  const downloadPy = () => {
    const code = result?.overall?.rewritten ?? "";
    if (!code) return;
    const blob = new Blob([code], { type: "text/x-python" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = "optimized_siren.py";
    a.click();
    URL.revokeObjectURL(url);
  };

  const overall  = result?.overall;
  const savings  = overall && overall.totalEml > 0
    ? Math.round((1 - overall.totalBest / overall.totalEml) * 100) : 0;
  const rewritten = overall?.rewritten ?? "";
  const pySnippet = overall?.pythonSnippet
    ? "# pip install monogate\n" + overall.pythonSnippet
    : rewritten.startsWith("from monogate")
      ? rewritten
      : `from monogate import BEST\n\n${rewritten}`;

  const card = {
    background: C.surface, border: `1px solid ${C.border}`,
    borderRadius: 8, padding: 16, marginBottom: 12,
  };
  const btnBase = {
    padding: "5px 12px", fontSize: 10, borderRadius: 4, cursor: "pointer",
    border: `1px solid ${C.border}`, background: "transparent",
    color: C.muted, fontFamily: "'Space Mono', monospace", letterSpacing: "0.04em",
  };
  const noOps = result && (!overall || overall.matches.length === 0);

  return (
    <div style={{ overflowX: "hidden" }}>

      {/* ── Toast ── */}
      {toast && (
        <div style={{
          position: "fixed", bottom: 24, right: 24, zIndex: 9999,
          padding: "8px 16px", borderRadius: 6,
          background: "#0d0e1c", border: `1px solid ${C.green}`,
          color: C.green, fontSize: 11, fontFamily: "'Space Mono', monospace",
          boxShadow: "0 4px 16px rgba(0,0,0,0.5)", pointerEvents: "none",
        }}>
          ✓ {toast.label}
        </div>
      )}

      {/* ── Header ── */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: C.accent }}>⬡ NeRF / SIREN Optimizer</span>
          {apiStatus === "available" && (
            <span style={{
              fontSize: 8, padding: "1px 6px", borderRadius: 3,
              background: "rgba(94,196,122,0.12)", border: "1px solid #5ec47a",
              color: "#5ec47a", fontWeight: 700, letterSpacing: "0.06em",
            }}>Python API</span>
          )}
          {apiMode && (
            <span style={{
              fontSize: 8, padding: "1px 6px", borderRadius: 3,
              background: "rgba(94,196,122,0.07)", border: "1px solid #3a7a4a",
              color: "#5ec47a", letterSpacing: "0.04em",
            }}>AST rewrite</span>
          )}
          {apiStatus === "unavailable" && (
            <span style={{
              fontSize: 8, padding: "1px 6px", borderRadius: 3,
              background: "rgba(78,81,104,0.15)", border: `1px solid ${C.border}`,
              color: C.muted, letterSpacing: "0.04em",
            }}>JS mode</span>
          )}
        </div>
        <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.7 }}>
          SIREN networks use <code style={{ color: C.text }}>sin(ω₀·Wx+b)</code> as activation.
          sin is the dominant op — BEST routing cuts its node cost from 245n → 63n (74% savings).
          Measured speedup: <span style={{ color: C.green }}>2.8–3.4× on sin-heavy forward passes.</span>
        </div>
      </div>

      {/* ── Presets ── */}
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 10 }}>
        <span style={{
          fontSize: 9, color: C.muted, alignSelf: "center",
          textTransform: "uppercase", letterSpacing: "0.06em", marginRight: 2,
        }}>presets</span>
        {PRESETS.map(p => (
          <button key={p.label} onClick={() => {
            setSrc(p.code);
            setResult(null);
            setApiMode(false);
          }} style={{ ...btnBase, padding: "4px 10px", background: C.tag }}>
            {p.label}
          </button>
        ))}
      </div>

      {/* ── Input ── */}
      <div style={card}>
        <textarea
          value={src}
          onChange={e => setSrc(e.target.value)}
          rows={11}
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
            {analyzing ? "Analyzing…" : "Analyze with BEST →"}
          </button>
        </div>
      </div>

      {/* ── No ops found ── */}
      {noOps && (
        <div style={{ ...card, color: C.muted, fontSize: 11 }}>
          No <code>torch.sin</code> / <code>torch.cos</code> or other recognized math ops found.
          Make sure the code uses <code>torch.*</code>, <code>math.*</code>, or <code>np.*</code> calls.
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
                : <span style={{ fontSize: 11, color: C.muted }}>No savings — expression is EML-optimal</span>
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

          {/* Op table */}
          {overall.matches.length > 0 && (
            <div style={card}>
              <div style={{
                fontSize: 9, color: C.muted, textTransform: "uppercase",
                letterSpacing: "0.06em", marginBottom: 10,
              }}>Detected operations</div>
              <OpTable
                matches={overall.matches}
                totalEml={overall.totalEml}
                totalBest={overall.totalBest}
              />
            </div>
          )}

          {/* Before / After + actions */}
          {savings > 0 && (
            <div style={{ ...card, padding: "14px 16px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                {/* Before */}
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{
                    fontSize: 9, color: C.muted, textTransform: "uppercase",
                    letterSpacing: "0.06em", marginBottom: 6,
                  }}>before</span>
                  <pre style={{
                    margin: 0, padding: "10px 12px", flex: 1,
                    background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6,
                    fontSize: 10, color: C.text, lineHeight: 1.65,
                    fontFamily: "'Space Mono', monospace",
                    whiteSpace: "pre-wrap", wordBreak: "break-word", minHeight: 80,
                  }}>{src.trim()}</pre>
                </div>

                {/* After */}
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <div style={{
                    display: "flex", justifyContent: "space-between",
                    alignItems: "center", marginBottom: 6,
                  }}>
                    <span style={{
                      fontSize: 9, color: C.green, textTransform: "uppercase",
                      letterSpacing: "0.06em",
                    }}>after · monogate BEST</span>
                    <button onClick={() => copy("rewritten", rewritten, "Rewritten code copied")} style={{
                      ...btnBase, padding: "2px 8px", fontSize: 9,
                      border: `1px solid ${copied === "rewritten" ? C.green : C.border}`,
                      color: copied === "rewritten" ? C.green : C.muted,
                      background: copied === "rewritten" ? "rgba(94,196,122,0.08)" : "transparent",
                    }}>
                      {copied === "rewritten" ? "✓ copied" : "⎘ copy"}
                    </button>
                  </div>
                  <pre style={{
                    margin: 0, padding: "10px 12px", flex: 1,
                    background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6,
                    fontSize: 10, color: C.text, lineHeight: 1.65,
                    fontFamily: "'Space Mono', monospace",
                    whiteSpace: "pre-wrap", wordBreak: "break-word", minHeight: 80,
                  }}>{rewritten}</pre>
                </div>
              </div>

              {/* Action buttons */}
              <div style={{ display: "flex", gap: 6, justifyContent: "flex-end", flexWrap: "wrap" }}>
                <button
                  onClick={() => copy("python", pySnippet, "Python snippet copied")}
                  style={{
                    ...btnBase,
                    color: copied === "python" ? C.green : C.accent,
                    border: `1px solid ${copied === "python" ? C.green : C.accent}`,
                    background: copied === "python"
                      ? "rgba(94,196,122,0.08)"
                      : "rgba(232,160,32,0.06)",
                  }}
                >
                  {copied === "python" ? "✓ Copied" : "⎘ Copy as Python"}
                </button>
                <button
                  onClick={downloadPy}
                  style={{
                    ...btnBase,
                    color: C.accent,
                    border: `1px solid ${C.accent}`,
                    background: "rgba(232,160,32,0.06)",
                  }}
                >
                  ↓ Download optimized_siren.py
                </button>
              </div>

              <div style={{ fontSize: 9, color: C.muted, marginTop: 10, lineHeight: 1.6 }}>
                Note: BEST routing applies to the symbolic EML substrate (scalar Python math).
                Native <code style={{ color: C.text }}>torch.sin</code> on tensors is ~9,000× faster —
                use monogate for symbolic analysis, interpretable regression, and expression research.
              </div>
            </div>
          )}
        </>
      )}

      {/* ── Empty state ── */}
      {!result && (
        <div style={{ ...card, color: C.muted, fontSize: 11, lineHeight: 1.9 }}>
          <div style={{ marginBottom: 8, color: C.text, fontSize: 10 }}>SIREN / NeRF context:</div>
          <div>SIREN uses <code>sin(ω₀·Wx+b)</code> as every activation — sin is the dominant op</div>
          <div>BEST replaces each <code>torch.sin</code> with an 8-term EXL Taylor expansion</div>
          <div>Node cost: 245n (pure EML sin) → 63n (BEST) = 74% savings per sin call</div>
          <div>At 74% savings, well above the 20% crossover — speedup expected</div>
          <div style={{
            marginTop: 12, padding: "8px 12px",
            background: C.tag, borderRadius: 6, fontSize: 10, lineHeight: 1.7,
          }}>
            <span style={{ color: C.accent, fontWeight: 700 }}>Measured (experiment_12, SIREN 3-layer):</span>
            <span style={{ color: C.text }}>{" "}2.8–3.4× speedup on sin-heavy forward passes</span>
          </div>
        </div>
      )}

    </div>
  );
}
