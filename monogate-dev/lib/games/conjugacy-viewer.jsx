// Conjugacy Viewer — side-by-side cobweb diagrams for the EAL and EXL
// self-maps, with exp as the conjugating map.
//
//   f(x) = exp(x) + ln(x)     EAL self-map on (0, ∞)
//   g(y) = exp(y) · ln(y)     EXL self-map on (0, ∞)
//
// Claim (Prop A-1, Lean-formalized in SelfMapConjugacy.lean):
//   exp(f(x)) = g(exp(x))     for all x > 0.
// So orbits of f on (0, ∞) push through exp to orbits of g on (1, ∞),
// step by step. At the fixed points x* ≈ 0.3442 and y* = exp(x*) ≈ 1.4108,
// the multipliers match to 13 decimals: f'(x*) = g'(y*) ≈ 4.316420588709.
//
// Slider: initial x₀. Play: step both orbits in sync and draw cobweb lines.

import { useState, useRef, useEffect } from "react";

const F = (x) => Math.exp(x) + Math.log(x);              // EAL self-map
const G = (y) => Math.exp(y) * Math.log(y);              // EXL self-map

// Panel dimensions (one panel)
const W = 330;
const H = 330;
const PAD = 32;

// Domain for the two panels
const EAL_DOM = { xMin: 0.1, xMax: 3.0, yMin: -1,  yMax: 12 };
const EXL_DOM = { xMin: 0.5, xMax: 4.0, yMin: -1,  yMax: 30 };

const FIXED_X = 0.34416128672196;
const FIXED_Y = Math.exp(FIXED_X); // 1.41080616145986
const MULTIPLIER = 4.316420588709;

function mapX(v, dom) {
  return PAD + ((v - dom.xMin) / (dom.xMax - dom.xMin)) * (W - 2 * PAD);
}
function mapY(v, dom) {
  return H - PAD - ((v - dom.yMin) / (dom.yMax - dom.yMin)) * (H - 2 * PAD);
}

function drawPanel(ctx, dom, fn, color, label, orbit, current) {
  ctx.fillStyle = "#08080c";
  ctx.fillRect(0, 0, W, H);

  // Grid
  ctx.strokeStyle = "rgba(255,255,255,0.06)";
  ctx.lineWidth = 1;
  for (let k = Math.ceil(dom.xMin); k <= dom.xMax; k++) {
    const x = mapX(k, dom);
    ctx.beginPath(); ctx.moveTo(x, PAD); ctx.lineTo(x, H - PAD); ctx.stroke();
  }
  const yStep = (dom.yMax - dom.yMin) / 6;
  for (let j = 0; j <= 6; j++) {
    const v = dom.yMin + j * yStep;
    const y = mapY(v, dom);
    ctx.beginPath(); ctx.moveTo(PAD, y); ctx.lineTo(W - PAD, y); ctx.stroke();
  }

  // Axes
  ctx.strokeStyle = "rgba(255,255,255,0.25)";
  ctx.beginPath();
  ctx.moveTo(PAD, H - PAD); ctx.lineTo(W - PAD, H - PAD);
  ctx.moveTo(PAD, PAD);     ctx.lineTo(PAD, H - PAD);
  ctx.stroke();

  // y = x diagonal
  ctx.strokeStyle = "rgba(255,255,255,0.25)";
  ctx.setLineDash([3, 3]);
  ctx.beginPath();
  const xLo = Math.max(dom.xMin, dom.yMin);
  const xHi = Math.min(dom.xMax, dom.yMax);
  ctx.moveTo(mapX(xLo, dom), mapY(xLo, dom));
  ctx.lineTo(mapX(xHi, dom), mapY(xHi, dom));
  ctx.stroke();
  ctx.setLineDash([]);

  // Curve
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.6;
  ctx.beginPath();
  const N = 200;
  let started = false;
  for (let i = 0; i <= N; i++) {
    const x = dom.xMin + (i / N) * (dom.xMax - dom.xMin);
    if (x <= 0) continue;
    const y = fn(x);
    if (!Number.isFinite(y)) continue;
    const px = mapX(x, dom);
    const py = mapY(y, dom);
    if (py < -100 || py > H + 100) { started = false; continue; }
    if (!started) { ctx.moveTo(px, py); started = true; }
    else ctx.lineTo(px, py);
  }
  ctx.stroke();

  // Cobweb up to `current` steps
  if (orbit.length >= 2) {
    ctx.strokeStyle = color + "aa";
    ctx.lineWidth = 1.2;
    const stop = Math.min(current, orbit.length - 1);
    for (let i = 0; i < stop; i++) {
      const x0 = orbit[i];
      const x1 = orbit[i + 1];
      // Vertical: (x0, x0) → (x0, f(x0) = x1)
      ctx.beginPath();
      ctx.moveTo(mapX(x0, dom), mapY(x0, dom));
      ctx.lineTo(mapX(x0, dom), mapY(x1, dom));
      ctx.stroke();
      // Horizontal: (x0, x1) → (x1, x1)
      ctx.beginPath();
      ctx.moveTo(mapX(x0, dom), mapY(x1, dom));
      ctx.lineTo(mapX(x1, dom), mapY(x1, dom));
      ctx.stroke();
    }
  }

  // Current point
  if (orbit.length > 0 && current >= 0) {
    const idx = Math.min(current, orbit.length - 1);
    const x = orbit[idx];
    const px = mapX(x, dom);
    const py = mapY(x, dom);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(px, py, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  // Fixed point marker
  const fp = fn === F ? FIXED_X : FIXED_Y;
  if (fp >= dom.xMin && fp <= dom.xMax) {
    ctx.strokeStyle = "rgba(255,255,255,0.5)";
    ctx.setLineDash([4, 3]);
    const px = mapX(fp, dom);
    ctx.beginPath();
    ctx.moveTo(px, PAD); ctx.lineTo(px, H - PAD);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(255,255,255,0.8)";
    ctx.font = "9px monospace";
    ctx.fillText(`x* = ${fp.toFixed(5)}`, px + 3, PAD + 10);
  }

  // Label
  ctx.fillStyle = color;
  ctx.font = "bold 12px monospace";
  ctx.fillText(label, PAD, 18);
}

export default function ConjugacyViewer() {
  const [x0, setX0] = useState(1.0);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const ealOrbit = useRef([]);
  const exlOrbit = useRef([]);
  const ealCanvas = useRef(null);
  const exlCanvas = useRef(null);
  const [, setTick] = useState(0);       // force rerender on orbit updates

  // Recompute orbits whenever x0 changes
  useEffect(() => {
    const N = 30;
    const ealPath = [x0];
    for (let i = 0; i < N; i++) {
      const x = ealPath[ealPath.length - 1];
      if (x <= 0 || !Number.isFinite(x)) break;
      const nx = F(x);
      if (!Number.isFinite(nx) || Math.abs(nx) > 1e6) break;
      ealPath.push(nx);
    }
    const exlPath = [Math.exp(x0)];
    for (let i = 0; i < N; i++) {
      const y = exlPath[exlPath.length - 1];
      if (y <= 0 || !Number.isFinite(y)) break;
      const ny = G(y);
      if (!Number.isFinite(ny) || Math.abs(ny) > 1e10) break;
      exlPath.push(ny);
    }
    ealOrbit.current = ealPath;
    exlOrbit.current = exlPath;
    setStep(0);
    setTick((t) => t + 1);
  }, [x0]);

  // Animate step progression when playing
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setStep((s) => {
        const maxStep = Math.min(ealOrbit.current.length, exlOrbit.current.length) - 1;
        if (s >= maxStep) {
          setPlaying(false);
          return maxStep;
        }
        return s + 1;
      });
    }, 500);
    return () => clearInterval(id);
  }, [playing]);

  // Redraw on step or x0 change
  useEffect(() => {
    if (ealCanvas.current) {
      const ctx = ealCanvas.current.getContext("2d");
      drawPanel(
        ctx, EAL_DOM, F, "#a18cd1", "f(x) = exp(x) + ln(x)   [EAL]",
        ealOrbit.current, step
      );
    }
    if (exlCanvas.current) {
      const ctx = exlCanvas.current.getContext("2d");
      drawPanel(
        ctx, EXL_DOM, G, "#0fd38d", "g(y) = exp(y) · ln(y)   [EXL]",
        exlOrbit.current, step
      );
    }
  }, [step, x0]);

  const ealSnap = ealOrbit.current[Math.min(step, ealOrbit.current.length - 1)];
  const exlSnap = exlOrbit.current[Math.min(step, exlOrbit.current.length - 1)];
  const match = Number.isFinite(ealSnap) && Number.isFinite(exlSnap)
    ? Math.abs(Math.exp(ealSnap) - exlSnap)
    : null;
  const maxStep = Math.min(ealOrbit.current.length, exlOrbit.current.length) - 1;

  return (
    <div style={S.root}>
      <header style={S.header}>
        <span style={S.brand}>monogate</span>
        <span style={S.subBrand}>conjugacy viewer</span>
        <span style={S.formula}>EAL ↔ EXL via exp · Lean: SelfMapConjugacy.lean</span>
      </header>

      <div style={S.info}>
        For all x &gt; 0, <code>exp(f(x)) = g(exp(x))</code>. Orbits of f on the
        left panel project through <code>y = exp(x)</code> onto orbits of g on
        the right panel, step by step. Fixed points: x* ≈ {FIXED_X.toFixed(5)},
        y* = exp(x*) ≈ {FIXED_Y.toFixed(5)}, multiplier at each ≈ {MULTIPLIER.toFixed(5)}.
      </div>

      <div style={S.panels}>
        <canvas ref={ealCanvas} width={W} height={H} style={S.canvas} />
        <div style={S.arrow}>
          <div style={{ fontSize: 18, color: "#e8e8f0" }}>⟶</div>
          <div style={{ fontSize: 10, color: "rgba(255,255,255,0.5)", marginTop: 4 }}>exp</div>
        </div>
        <canvas ref={exlCanvas} width={W} height={H} style={S.canvas} />
      </div>

      <div style={S.readout}>
        <span>step {step}/{Math.max(0, maxStep)}</span>
        <span>f-orbit: {Number.isFinite(ealSnap) ? ealSnap.toFixed(6) : "—"}</span>
        <span>g-orbit: {Number.isFinite(exlSnap) ? exlSnap.toFixed(6) : "—"}</span>
        <span>|exp(f) − g|: {match === null ? "—" : match < 1e-10 ? match.toExponential(2) : match.toFixed(10)}</span>
      </div>

      <div style={S.controls}>
        <span style={S.label}>x₀ = {x0.toFixed(3)}</span>
        <input
          type="range"
          min={0.1}
          max={2.5}
          step={0.01}
          value={x0}
          onChange={(e) => { setPlaying(false); setX0(parseFloat(e.target.value)); }}
          style={S.slider}
        />
        <div style={S.divider} />
        <button
          onClick={() => setStep(0)}
          style={S.btn}
        >⏮ reset</button>
        <button
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          style={S.btn}
        >◀ back</button>
        <button
          onClick={() => setPlaying((p) => !p)}
          style={{ ...S.btn, color: playing ? "#08080c" : "#a18cd1",
            background: playing ? "#a18cd1" : "transparent",
            borderColor: "#a18cd1", fontWeight: 600 }}
        >{playing ? "⏸ pause" : "▶ play"}</button>
        <button
          onClick={() => setStep((s) => Math.min(maxStep, s + 1))}
          style={S.btn}
        >step ▶</button>
        <div style={S.divider} />
        <button
          onClick={() => { setX0(FIXED_X); setPlaying(false); setStep(0); }}
          style={{ ...S.btn, borderColor: "rgba(255,255,255,0.3)" }}
        >jump to x*</button>
      </div>

      <div style={S.help}>
        The EAL and EXL self-maps have <b>different</b> fixed points (0.344 vs
        1.411) yet share the <b>same</b> multiplier to 13 decimals
        (4.3164206…). That's conjugacy at work: dynamical invariants live on
        conjugacy classes, not individual maps. The cobweb on the left is a
        1-to-1 image of the cobweb on the right under exp — whatever happens
        to the orbit in f-space happens to the orbit in g-space, at the
        matching point.
        <br /><br />
        Lean formalization: <code>eal_exl_conjugacy</code> in{" "}
        <a href="https://github.com/almaguer1986/monogate-lean/blob/master/MonogateEML/SelfMapConjugacy.lean"
           style={{ color: "#4facfe" }} target="_blank" rel="noreferrer">
          SelfMapConjugacy.lean</a>{" "}
        (0 sorries).
      </div>
    </div>
  );
}

const FONT = "'IBM Plex Mono', 'SF Mono', 'Fira Code', monospace";
const S = {
  root: {
    background: "#08080c", color: "#e8e8f0", fontFamily: FONT,
    minHeight: "100vh", padding: "20px 24px 80px",
  },
  header: {
    display: "flex", gap: 16, alignItems: "baseline", flexWrap: "wrap",
    marginBottom: 10, paddingBottom: 10,
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  brand: {
    fontSize: 13, fontWeight: 600, letterSpacing: "0.15em",
    textTransform: "uppercase", color: "#4facfe",
  },
  subBrand: { fontSize: 13, color: "rgba(255,255,255,0.3)" },
  formula: { fontSize: 11, color: "rgba(255,255,255,0.45)", marginLeft: "auto" },
  info: {
    fontSize: 12, color: "rgba(255,255,255,0.55)",
    fontFamily: "system-ui, sans-serif", lineHeight: 1.7,
    marginBottom: 18, maxWidth: 780,
  },
  panels: {
    display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap",
    marginBottom: 14,
  },
  canvas: {
    border: "1px solid rgba(255,255,255,0.08)", borderRadius: 6,
    background: "#08080c", maxWidth: "100%",
  },
  arrow: {
    display: "flex", flexDirection: "column", alignItems: "center",
    minWidth: 48,
  },
  readout: {
    display: "flex", gap: 24, fontSize: 11,
    color: "rgba(255,255,255,0.6)", marginBottom: 14, flexWrap: "wrap",
  },
  controls: {
    display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap",
    padding: "10px 0", borderTop: "1px solid rgba(255,255,255,0.06)",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  label: { fontSize: 11, color: "rgba(255,255,255,0.5)" },
  slider: { flex: "0 1 220px", accentColor: "#a18cd1" },
  btn: {
    borderRadius: 4, padding: "5px 11px", fontSize: 11, fontFamily: "inherit",
    cursor: "pointer", border: "1px solid rgba(255,255,255,0.15)",
    background: "transparent", color: "rgba(255,255,255,0.7)",
  },
  divider: { width: 1, height: 20, background: "rgba(255,255,255,0.08)", margin: "0 4px" },

  help: {
    maxWidth: 780, marginTop: 20, lineHeight: 1.75, fontSize: 12,
    color: "rgba(255,255,255,0.55)", fontFamily: "system-ui, sans-serif",
  },
};
