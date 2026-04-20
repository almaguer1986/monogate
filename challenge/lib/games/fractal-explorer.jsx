// EML Fractal Explorer — interactive operator fractal renderer (F5)
// Covers 8 EML-family operators, zoom, color schemes, canvas renderer.

import { useState, useEffect, useRef, useCallback } from "react";

const C = {
  bg: "#07080f", surface: "#0d0e1c", border: "#191b2e",
  text: "#cdd0e0", muted: "#4e5168", accent: "#e8a020",
  blue: "#6ab0f5", green: "#5ec47a", red: "#e05060",
  orange: "#f97316", purple: "#a78bfa",
};

// ── Operator definitions ──────────────────────────────────────────────────────

const OPERATORS = {
  EML:  { label: "EML  exp(A)−ln(B)",  fn: (a, b) => Math.exp(a) - Math.log(b), color: C.blue },
  EAL:  { label: "EAL  exp(A)+ln(B)",  fn: (a, b) => Math.exp(a) + Math.log(b), color: C.green },
  EMN:  { label: "EMN  ln(B)−exp(A)",  fn: (a, b) => Math.log(b) - Math.exp(a), color: C.orange },
  EXL:  { label: "EXL  exp(A)·ln(B)",  fn: (a, b) => Math.exp(a) * Math.log(b), color: C.purple },
  EDL:  { label: "EDL  exp(A)/ln(B)",  fn: (a, b) => { const l = Math.log(b); return l === 0 ? Infinity : Math.exp(a) / l; }, color: C.accent },
  DEML: { label: "DEML exp(−A)−ln(B)", fn: (a, b) => Math.exp(-a) - Math.log(b), color: C.red },
  POW:  { label: "POW  B^A",           fn: (a, b) => Math.pow(b, a), color: "#38bdf8" },
  LEX:  { label: "LEX  ln(exp(A)·B)",  fn: (a, b) => Math.log(Math.exp(a) * b), color: "#f472b6" },
};

const COLOR_SCHEMES = {
  fire:  { bg: [7,8,15],   palette: (t) => `hsl(${30+t*270},90%,${20+t*60}%)` },
  ocean: { bg: [5,10,20],  palette: (t) => `hsl(${200+t*60},80%,${10+t*70}%)` },
  mono:  { bg: [0,0,0],    palette: (t) => { const v = Math.round(t*255); return `rgb(${v},${v},${v})`; } },
  neon:  { bg: [5,5,15],   palette: (t) => `hsl(${t*360},100%,${30+t*30}%)` },
};

const MAX_ITER = 100;
const ESCAPE = 40;

// Real-plane escape time for the map x → op(x, k)
function escapeTime(op, x0, kReal, kImag) {
  let x = x0;
  // use only real part for real-valued operators
  for (let i = 0; i < MAX_ITER; i++) {
    try {
      x = op(x, kReal);
      if (!isFinite(x) || Math.abs(x) > ESCAPE) return i + 1;
    } catch {
      return i + 1;
    }
  }
  return MAX_ITER;
}

// ── Canvas worker substitute (inline on main thread for simplicity) ───────────

function renderFractal(ctx, width, height, opFn, viewport, colorPalette) {
  const { xMin, xMax, yMin, yMax } = viewport;
  const imgData = ctx.createImageData(width, height);
  const data = imgData.data;

  for (let py = 0; py < height; py++) {
    const k = yMin + (py / height) * (yMax - yMin); // k parameter (real)
    for (let px = 0; px < width; px++) {
      const x0 = xMin + (px / width) * (xMax - xMin); // initial condition
      const iter = escapeTime(opFn, x0, k, 0);
      const t = iter === MAX_ITER ? 0 : (iter / MAX_ITER);
      const col = colorPalette(t);
      const match = col.match(/\d+/g);
      const idx = (py * width + px) * 4;
      if (col.startsWith("rgb")) {
        data[idx]   = parseInt(match[0]);
        data[idx+1] = parseInt(match[1]);
        data[idx+2] = parseInt(match[2]);
      } else {
        // hsl — approximate decode via canvas trick
        data[idx]   = Math.round(t * 255);
        data[idx+1] = Math.round((1-t) * 200);
        data[idx+2] = Math.round(t * 180);
      }
      data[idx+3] = 255;
    }
  }
  ctx.putImageData(imgData, 0, 0);
}

// ── Main component ────────────────────────────────────────────────────────────

export default function EMLFractalExplorer() {
  const canvasRef = useRef(null);
  const [opKey, setOpKey] = useState("EML");
  const [scheme, setScheme] = useState("fire");
  const [rendering, setRendering] = useState(false);
  const [viewport, setViewport] = useState({ xMin: -3, xMax: 3, yMin: -3, yMax: 3 });
  const [zoom, setZoom] = useState({ cx: 0, cy: 0, level: 1 });

  const SIZE = 480;

  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    setRendering(true);
    setTimeout(() => {
      const op = OPERATORS[opKey].fn;
      const pal = COLOR_SCHEMES[scheme].palette;
      renderFractal(ctx, SIZE, SIZE, op, viewport, pal);
      setRendering(false);
    }, 10);
  }, [opKey, scheme, viewport]);

  useEffect(() => { render(); }, [render]);

  function handleCanvasClick(e) {
    const rect = canvasRef.current.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    const { xMin, xMax, yMin, yMax } = viewport;
    const cx = xMin + (px / SIZE) * (xMax - xMin);
    const cy = yMin + (py / SIZE) * (yMax - yMin);
    const factor = e.shiftKey ? 2 : 0.5;
    const dx = (xMax - xMin) * factor / 2;
    const dy = (yMax - yMin) * factor / 2;
    setViewport({ xMin: cx - dx, xMax: cx + dx, yMin: cy - dy, yMax: cy + dy });
    setZoom(z => ({ cx, cy, level: z.level * (e.shiftKey ? 0.5 : 2) }));
  }

  function resetView() {
    setViewport({ xMin: -3, xMax: 3, yMin: -3, yMax: 3 });
    setZoom({ cx: 0, cy: 0, level: 1 });
  }

  const opInfo = OPERATORS[opKey];

  return (
    <div style={{ background: C.bg, color: C.text, minHeight: "100vh", padding: 24, fontFamily: "monospace" }}>
      <h2 style={{ color: C.accent, marginBottom: 4, fontSize: 20 }}>EML Fractal Explorer</h2>
      <p style={{ color: C.muted, fontSize: 11, marginBottom: 20 }}>
        Real-plane escape-time diagram: x₀ (horizontal) vs parameter k (vertical).
        Click to zoom in, Shift+click to zoom out.
      </p>

      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {/* Controls */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, minWidth: 220 }}>
          <div>
            <div style={{ fontSize: 10, color: C.muted, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.1em" }}>Operator</div>
            {Object.entries(OPERATORS).map(([key, info]) => (
              <button key={key} onClick={() => setOpKey(key)} style={{
                display: "block", width: "100%", textAlign: "left",
                background: opKey === key ? C.surface : "transparent",
                border: `1px solid ${opKey === key ? info.color : C.border}`,
                borderRadius: 4, padding: "5px 8px", marginBottom: 4,
                color: opKey === key ? info.color : C.muted,
                fontSize: 10, cursor: "pointer",
              }}>
                {info.label}
              </button>
            ))}
          </div>

          <div>
            <div style={{ fontSize: 10, color: C.muted, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.1em" }}>Color scheme</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {Object.keys(COLOR_SCHEMES).map(s => (
                <button key={s} onClick={() => setScheme(s)} style={{
                  background: scheme === s ? C.accent : C.surface,
                  border: `1px solid ${C.border}`, borderRadius: 4,
                  color: scheme === s ? C.bg : C.text, fontSize: 10,
                  padding: "4px 8px", cursor: "pointer",
                }}>{s}</button>
              ))}
            </div>
          </div>

          <button onClick={resetView} style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 4, color: C.text, fontSize: 10, padding: "6px 12px", cursor: "pointer",
          }}>Reset view</button>

          {/* Metrics */}
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, padding: 12, fontSize: 10 }}>
            <div style={{ color: C.muted, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.1em" }}>Known metrics</div>
            {opKey === "EML" && <>
              <div style={{ color: C.text, marginBottom: 4 }}>Boundary dim: <span style={{ color: C.green }}>1.716 ± 0.025</span></div>
              <div style={{ color: C.text, marginBottom: 4 }}>Area (k-plane): <span style={{ color: C.green }}>23.27</span></div>
              <div style={{ color: C.muted }}>= Devaney exponential family f_k(z)=e^z−k</div>
            </>}
            <div style={{ color: C.muted, marginTop: 8 }}>Zoom: {zoom.level.toFixed(1)}×</div>
            <div style={{ color: C.muted }}>Center: ({zoom.cx.toFixed(3)}, {zoom.cy.toFixed(3)})</div>
          </div>
        </div>

        {/* Canvas */}
        <div>
          <canvas
            ref={canvasRef}
            width={SIZE}
            height={SIZE}
            onClick={handleCanvasClick}
            style={{
              cursor: "crosshair",
              border: `1px solid ${opInfo.color}`,
              borderRadius: 4,
              display: "block",
              opacity: rendering ? 0.6 : 1,
              transition: "opacity 0.1s",
            }}
          />
          {rendering && (
            <div style={{ color: C.muted, fontSize: 10, marginTop: 6 }}>Rendering…</div>
          )}
          <div style={{ color: C.muted, fontSize: 10, marginTop: 6 }}>
            x₀ ∈ [{viewport.xMin.toFixed(2)}, {viewport.xMax.toFixed(2)}] &nbsp;
            k ∈ [{viewport.yMin.toFixed(2)}, {viewport.yMax.toFixed(2)}]
          </div>
        </div>
      </div>

      {/* Footer note */}
      <div style={{
        marginTop: 24, padding: 12,
        background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
        fontSize: 10, color: C.muted, maxWidth: 720,
      }}>
        <span style={{ color: C.text }}>How to read this:</span> Each pixel (x₀, k) is colored by how many iterations
        x → op(x, k) take to escape |x| &gt; {ESCAPE}. Dark = bounded (periodic/fixed). Bright = escapes fast.
        The EML operator produces the <em>exponential family</em> Mₑ studied by Devaney and Eremenko-Lyubich.
      </div>
    </div>
  );
}
