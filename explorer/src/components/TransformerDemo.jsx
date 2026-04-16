// explorer/src/components/TransformerDemo.jsx
// Transformer activation benchmark demo.
// Live JS timing: gelu_eml (17n) vs gelu_best (14n) on a 4× FFN block.
// Python FFN numbers hardcoded from experiment_10 (Python 3.14, CPU).

import { useState, useEffect } from "react";
import { gelu_eml, gelu_best } from "../eml.js";

const C = {
  bg: "#07080f", surface: "#0d0e1c", border: "#191b2e",
  text: "#cdd0e0", muted: "#4e5168", accent: "#e8a020",
  blue: "#6ab0f5", green: "#5ec47a", red: "#e05060",
};

// ── Hardcoded results from Python experiment_10 ───────────────────────────────
const EXP10 = {
  native_ms: 1.771,
  eml_ms:    4.736,
  best_ms:   5.115,
  eml_vs_best_speedup: 0.93,
  note: "Python 3.14 · CPU · d=16, 4× hidden=64, batch=8",
  gelu_eml_nodes: 17,
  gelu_best_nodes: 14,
  gelu_savings_pct: 18,
};

// ── Minimal pure-JS FFN matching experiment_10 structure ─────────────────────
// d=16, hidden=64 (4× expansion), batch=8 — identical to Python section C

function makeMat(rows, cols, seed) {
  const m = [], a = 1664525, c = 1013904223, mod = 2 ** 32;
  let s = seed;
  const scale = Math.sqrt(2 / (rows + cols));
  for (let i = 0; i < rows; i++) {
    m.push([]);
    for (let j = 0; j < cols; j++) {
      s = (a * s + c) >>> 0;
      m[i].push(((s / mod) * 2 - 1) * scale);
    }
  }
  return m;
}

function makeInput(d, batch, seed) {
  const m = [], a = 1664525, c = 1013904223, mod = 2 ** 32;
  let s = seed;
  for (let i = 0; i < batch; i++) {
    m.push([]);
    for (let j = 0; j < d; j++) {
      s = (a * s + c) >>> 0;
      m[i].push(((s / mod) * 2 - 1));
    }
  }
  return m;
}

function ffnForward(x, W1, b1, W2, b2, activation) {
  const dIn = x.length, dHid = b1.length, dOut = b2.length;
  const h = [];
  for (let j = 0; j < dHid; j++) {
    let v = b1[j];
    for (let i = 0; i < dIn; i++) v += W1[j][i] * x[i];
    h.push(v);
  }
  const hAct = h.map(activation);
  const out = [];
  for (let k = 0; k < dOut; k++) {
    let v = b2[k];
    for (let j = 0; j < dHid; j++) v += W2[k][j] * hAct[j];
    out.push(v);
  }
  return out;
}

const D = 16, D_HID = 64, BATCH = 8;
const W1 = makeMat(D_HID, D, 42),    b1 = new Array(D_HID).fill(0);
const W2 = makeMat(D, D_HID, 99),    b2 = new Array(D).fill(0);
const INPUTS = makeInput(D, BATCH, 7);

// ── Component ─────────────────────────────────────────────────────────────────
export default function TransformerDemo() {
  const [bench, setBench] = useState(null);

  useEffect(() => {
    const RUNS = 100;

    // Warm up
    for (let i = 0; i < 5; i++) {
      for (const x of INPUTS) ffnForward(x, W1, b1, W2, b2, gelu_eml);
      for (const x of INPUTS) ffnForward(x, W1, b1, W2, b2, gelu_best);
    }

    const t0 = performance.now();
    for (let r = 0; r < RUNS; r++)
      for (const x of INPUTS) ffnForward(x, W1, b1, W2, b2, gelu_eml);
    const ms_eml = (performance.now() - t0) / RUNS;

    const t1 = performance.now();
    for (let r = 0; r < RUNS; r++)
      for (const x of INPUTS) ffnForward(x, W1, b1, W2, b2, gelu_best);
    const ms_best = (performance.now() - t1) / RUNS;

    setBench({ ms_eml, ms_best, speedup: ms_eml / ms_best });
  }, []);

  return (
    <div style={{ color: C.text }}>
      {/* Header */}
      <div style={{ fontSize: 10, color: C.muted, marginBottom: 16, lineHeight: 1.8 }}>
        GELU activation benchmarked in a Transformer FFN (d=16, hidden=64, batch=8).
        Live JS uses <span style={{ color: C.accent }}>gelu_best</span> (14n) vs{" "}
        <span style={{ color: C.muted }}>gelu_eml</span> (17n) — 18% fewer nodes.
        Python numbers from <span style={{ color: C.accent }}>experiment_10</span>.
      </div>

      {/* Architecture diagram */}
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8,
        padding: "12px 20px", marginBottom: 16, display: "flex", alignItems: "center",
        gap: 10, flexWrap: "wrap",
      }}>
        <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em" }}>FFN block:</div>
        {["Input x", "Linear (d→4d)", "GELU", "Linear (4d→d)", "Output"].map((label, i, arr) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{
              background: i === 2 ? "rgba(232,160,32,0.12)" : "rgba(255,255,255,0.04)",
              border: `1px solid ${i === 2 ? C.accent : C.border}`,
              borderRadius: 5, padding: "5px 10px", fontSize: 10,
              color: i === 2 ? C.accent : C.text,
            }}>
              {label}
              {i === 2 && <div style={{ fontSize: 8, color: C.muted, marginTop: 2 }}>← 17n EML / 14n BEST</div>}
            </div>
            {i < arr.length - 1 && <span style={{ color: C.muted, fontSize: 14 }}>→</span>}
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>

        {/* ── Live JS timing ── */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
          <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
            Live JS benchmark — GELU activation
          </div>
          <div style={{ fontSize: 8, color: C.muted, marginBottom: 10 }}>
            {RUNS_DISPLAY} forward passes · d={D}, hidden={D_HID}, batch={BATCH} · this browser
          </div>

          {bench ? (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 12 }}>
                {[
                  { label: "EML (17n)",  ms: bench.ms_eml,  col: C.muted  },
                  { label: "BEST (14n)", ms: bench.ms_best, col: C.accent },
                ].map(({ label, ms, col }) => (
                  <div key={label} style={{ background: C.bg, borderRadius: 6, padding: "10px 12px" }}>
                    <div style={{ fontSize: 9, color: C.muted, marginBottom: 4 }}>{label}</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: col }}>{ms.toFixed(2)}</div>
                    <div style={{ fontSize: 8, color: C.muted }}>ms/forward</div>
                  </div>
                ))}
              </div>

              <div style={{
                background: bench.speedup >= 1
                  ? "rgba(94,196,122,0.08)" : "rgba(106,176,245,0.08)",
                border: `1px solid ${bench.speedup >= 1
                  ? "rgba(94,196,122,0.25)" : "rgba(106,176,245,0.2)"}`,
                borderRadius: 6, padding: "8px 12px", fontSize: 11, marginBottom: 10,
              }}>
                <span style={{ color: bench.speedup >= 1 ? C.green : C.blue }}>
                  {bench.speedup.toFixed(2)}× {bench.speedup >= 1 ? "faster" : "slower"}
                </span>
                <span style={{ color: C.muted, fontSize: 9, marginLeft: 8 }}>
                  (18% fewer nodes → {bench.speedup.toFixed(2)}× wall-clock)
                </span>
              </div>

              {bench.speedup < 1.05 && (
                <div style={{ fontSize: 9, color: C.blue, lineHeight: 1.6 }}>
                  Note: 18% node reduction is below JS call-overhead threshold —
                  V8 JIT amortises the savings. Compare Python result at right.
                </div>
              )}

              {/* Node bars */}
              <div style={{ marginTop: 10 }}>
                {[{ label: "EML",  n: 17, col: C.muted + "88" }, { label: "BEST", n: 14, col: C.accent }].map(({ label, n, col }) => (
                  <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                    <div style={{ fontSize: 9, color: C.muted, width: 40 }}>{label}</div>
                    <div style={{ height: 8, borderRadius: 3, width: `${Math.round(n * 7)}px`, background: col }} />
                    <div style={{ fontSize: 9, color: C.muted }}>{n}n</div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div style={{ fontSize: 10, color: C.muted }}>Running benchmark…</div>
          )}
        </div>

        {/* ── Python (CPU) column ── */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14 }}>
          <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
            Python (CPU) — experiment_10
          </div>
          <div style={{ fontSize: 8, color: C.muted, marginBottom: 12 }}>
            {EXP10.note}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6, marginBottom: 12 }}>
            {[
              { label: "native math", ms: EXP10.native_ms, col: C.blue,   sub: "Math.tanh" },
              { label: "EML-GELU",    ms: EXP10.eml_ms,    col: C.muted,  sub: "17n" },
              { label: "BEST-GELU",   ms: EXP10.best_ms,   col: C.accent, sub: "14n" },
            ].map(({ label, ms, col, sub }) => (
              <div key={label} style={{ background: C.bg, borderRadius: 6, padding: "8px 10px" }}>
                <div style={{ fontSize: 8, color: C.muted, marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: 15, fontWeight: 700, color: col }}>{ms.toFixed(3)}</div>
                <div style={{ fontSize: 8, color: C.muted }}>ms/fwd · {sub}</div>
              </div>
            ))}
          </div>

          <div style={{
            background: "rgba(106,176,245,0.08)", border: "1px solid rgba(106,176,245,0.2)",
            borderRadius: 6, padding: "8px 12px", fontSize: 10, color: C.blue, marginBottom: 12,
          }}>
            18% node reduction → {EXP10.eml_vs_best_speedup}× (Python) — below call-overhead threshold
          </div>

          {/* GELU node cost breakdown */}
          <div style={{ fontSize: 9, color: C.muted, marginBottom: 6 }}>GELU node cost breakdown:</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 4, fontSize: 9 }}>
            {[
              { op: "exp",   eml: 1,  best: 1,  via: "EML" },
              { op: "add",   eml: 11, best: 11, via: "EML" },
              { op: "recip", eml: 5,  best: 2,  via: "EDL" },
            ].map(({ op, eml, best, via }) => (
              <div key={op} style={{ background: C.bg, borderRadius: 4, padding: "5px 8px", border: `1px solid ${C.border}` }}>
                <div style={{ color: C.text }}>{op}</div>
                <div style={{ color: C.accent }}>{best}n <span style={{ fontSize: 7, color: C.muted }}>BEST</span></div>
                <div style={{ color: C.muted }}>{eml}n <span style={{ fontSize: 7 }}>EML</span></div>
                <div style={{ fontSize: 7, color: via === "EDL" ? "#2dd4bf" : "#7c6ff7", marginTop: 2 }}>{via}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 8, fontSize: 9, color: C.muted }}>
            Total: <span style={{ color: C.accent }}>14n</span> BEST vs{" "}
            <span style={{ color: C.muted }}>17n</span> EML — 18% saving
          </div>
        </div>
      </div>

      {/* Key insight */}
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8,
        padding: "14px 18px",
      }}>
        <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
          Key insight: savings must exceed call overhead
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div style={{ fontSize: 10, color: C.text, lineHeight: 1.8 }}>
            GELU saves <span style={{ color: C.muted }}>18%</span> of nodes —
            below the ~20% crossover. In Python, call overhead swamps the saving; speedup ≈ 1×.
            V8 JIT can make JS results differ.
            <br /><br />
            <span style={{ color: C.green }}>sin/cos</span> save <span style={{ color: C.green }}>74%</span> →{" "}
            <span style={{ color: C.green }}>2.8× speedup</span> (Python).
            Polynomial activations at ~54% savings land at ~2.1×.
          </div>
          <div>
            {[
              { fn: "GELU",    pct: 18, py: "~1×",   col: C.muted  },
              { fn: "sin/cos", pct: 74, py: "2.8×",  col: C.green  },
              { fn: "div",     pct: 93, py: "—",      col: C.accent },
              { fn: "pow",     pct: 80, py: "4.77×", col: C.accent },
            ].map(({ fn, pct, py, col }) => (
              <div key={fn} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                <div style={{ width: 48, fontSize: 10, color: C.text }}>{fn}</div>
                <div style={{
                  height: 10, borderRadius: 3,
                  width: `${Math.round(pct * 1.3)}px`,
                  background: col + "88", border: `1px solid ${col}44`,
                }} />
                <div style={{ fontSize: 9, color: C.muted }}>{pct}% nodes</div>
                <div style={{ fontSize: 9, color: col, marginLeft: "auto" }}>{py} (Py)</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// constant referenced in JSX string interpolation
const RUNS_DISPLAY = "100";
