// Bifurcation Viewer — real-slice parameter sweeps for 8 F16 operators.
//
// For each operator op, iterate z_{n+1} = op(z_n, cr + 0i) from z_0 = 0,
// discard a transient, plot the tail. Scan the mouse horizontally to pick a
// cr value; play tones from the tail values at that cr. Multiplicative
// operators (EXL, DEXL) show period-3 / Sharkovskii fingerprints.
//
// Data is computed client-side on mount (~300ms) so the same code powers
// any future extension (EMN, DEXN, …) without bundling precomputed arrays.

import { useState, useRef, useEffect, useCallback } from "react";

// ─── Shared op definitions (same as fractal-studio) ──────────────────────────

function cExp(r, i) {
  const e = Math.exp(r);
  return [e * Math.cos(i), e * Math.sin(i)];
}
function cLn(r, i) {
  const mag = Math.sqrt(r * r + i * i);
  if (mag < 1e-300) return [-700, 0];
  return [Math.log(mag), Math.atan2(i, r)];
}

const OP_FNS = {
  EML:  (zr, zi, cr, ci) => { const [er, ei] = cExp(zr, zi); const [lr, li] = cLn(cr, ci); return [er - lr, ei - li]; },
  DEML: (zr, zi, cr, ci) => { const [er, ei] = cExp(-zr, -zi); const [lr, li] = cLn(cr, ci); return [er - lr, ei - li]; },
  EXL:  (zr, zi, cr, ci) => { const [er, ei] = cExp(zr, zi); const [lr, li] = cLn(cr, ci); return [er * lr - ei * li, er * li + ei * lr]; },
  DEXL: (zr, zi, cr, ci) => { const [er, ei] = cExp(-zr, -zi); const [lr, li] = cLn(cr, ci); return [er * lr - ei * li, er * li + ei * lr]; },
  EDL:  (zr, zi, cr, ci) => { const [er, ei] = cExp(zr, zi); const [lr, li] = cLn(cr, ci); const d = lr * lr + li * li; if (d < 1e-30) return [1e10, 0]; return [(er * lr + ei * li) / d, (ei * lr - er * li) / d]; },
  DEDL: (zr, zi, cr, ci) => { const [er, ei] = cExp(-zr, -zi); const [lr, li] = cLn(cr, ci); const d = lr * lr + li * li; if (d < 1e-30) return [1e10, 0]; return [(er * lr + ei * li) / d, (ei * lr - er * li) / d]; },
  EAL:  (zr, zi, cr, ci) => { const [er, ei] = cExp(zr, zi); const [lr, li] = cLn(cr, ci); return [er + lr, ei + li]; },
  DEAL: (zr, zi, cr, ci) => { const [er, ei] = cExp(-zr, -zi); const [lr, li] = cLn(cr, ci); return [er + lr, ei + li]; },
};

const OP_META = {
  EML:  { label: "EML",  formula: "exp(z) − ln(c)",  color: "#4facfe" },
  DEML: { label: "DEML", formula: "exp(−z) − ln(c)", color: "#f5576c" },
  EXL:  { label: "EXL",  formula: "exp(z) · ln(c)",  color: "#0fd38d", chaotic: true },
  DEXL: { label: "DEXL", formula: "exp(−z) · ln(c)", color: "#7af0c8", chaotic: true, sharkovskii: true },
  EDL:  { label: "EDL",  formula: "exp(z) / ln(c)",  color: "#fccb52" },
  DEDL: { label: "DEDL", formula: "exp(−z) / ln(c)", color: "#e8a020" },
  EAL:  { label: "EAL",  formula: "exp(z) + ln(c)",  color: "#a18cd1" },
  DEAL: { label: "DEAL", formula: "exp(−z) + ln(c)", color: "#c4a7f5" },
};

const N_CR = 400;
const CR_LO = -3.0;
const CR_HI = 3.0;
const WARM = 400;
const TAIL = 40;
const ESCAPE = 1e6;

function computeBifurcation(opKey) {
  const fn = OP_FNS[opKey];
  const diagram = new Array(N_CR);
  for (let i = 0; i < N_CR; i++) {
    const cr = CR_LO + (i / (N_CR - 1)) * (CR_HI - CR_LO);
    let zr = 0, zi = 0;
    let diverged = false;
    for (let k = 0; k < WARM; k++) {
      [zr, zi] = fn(zr, zi, cr, 0);
      if (!Number.isFinite(zr) || !Number.isFinite(zi) ||
          zr * zr + zi * zi > ESCAPE * ESCAPE) { diverged = true; break; }
    }
    if (diverged) { diagram[i] = { cr, tail: [] }; continue; }
    const tail = [];
    for (let k = 0; k < TAIL; k++) {
      [zr, zi] = fn(zr, zi, cr, 0);
      if (!Number.isFinite(zr) || !Number.isFinite(zi) ||
          zr * zr + zi * zi > ESCAPE * ESCAPE) { diverged = true; break; }
      tail.push(zr);
    }
    diagram[i] = { cr, tail: diverged ? [] : tail };
  }
  return diagram;
}

const CANVAS_W = 780;
const CANVAS_H = 420;

export default function BifurcationViewer() {
  const [op, setOp] = useState("DEXL");
  const [diagram, setDiagram] = useState(null);
  const [hoverCr, setHoverCr] = useState(null);
  const [yRange, setYRange] = useState([-3, 3]);
  const [audioOn, setAudioOn] = useState(false);
  const canvasRef = useRef(null);
  const audioCtxRef = useRef(null);
  const masterGainRef = useRef(null);

  // (Re)compute bifurcation when op changes
  useEffect(() => {
    setDiagram(null);
    const id = setTimeout(() => {
      const d = computeBifurcation(op);
      let lo = Infinity, hi = -Infinity;
      for (const { tail } of d) {
        for (const v of tail) {
          if (v < lo) lo = v;
          if (v > hi) hi = v;
        }
      }
      if (!Number.isFinite(lo) || !Number.isFinite(hi) || lo === hi) { lo = -3; hi = 3; }
      const pad = (hi - lo) * 0.05;
      setYRange([lo - pad, hi + pad]);
      setDiagram(d);
    }, 20);
    return () => clearTimeout(id);
  }, [op]);

  // Render canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#08080c";
    ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

    // Axes
    ctx.strokeStyle = "rgba(255,255,255,0.1)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, CANVAS_H / 2); ctx.lineTo(CANVAS_W, CANVAS_H / 2);
    const x0 = ((0 - CR_LO) / (CR_HI - CR_LO)) * CANVAS_W;
    ctx.moveTo(x0, 0); ctx.lineTo(x0, CANVAS_H);
    ctx.stroke();

    if (!diagram) {
      ctx.fillStyle = "rgba(255,255,255,0.3)";
      ctx.font = "12px monospace";
      ctx.fillText("computing bifurcation diagram...", 20, 20);
      return;
    }

    const [yLo, yHi] = yRange;
    const color = OP_META[op].color;
    const dotOpacity = 0.55;
    ctx.fillStyle = color;
    ctx.globalAlpha = dotOpacity;
    for (let i = 0; i < diagram.length; i++) {
      const { cr, tail } = diagram[i];
      const x = ((cr - CR_LO) / (CR_HI - CR_LO)) * CANVAS_W;
      for (const v of tail) {
        if (v < yLo || v > yHi) continue;
        const y = CANVAS_H - ((v - yLo) / (yHi - yLo)) * CANVAS_H;
        ctx.fillRect(x, y, 1.2, 1.2);
      }
    }
    ctx.globalAlpha = 1;

    // Hover cursor
    if (hoverCr !== null) {
      const x = ((hoverCr - CR_LO) / (CR_HI - CR_LO)) * CANVAS_W;
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.6;
      ctx.beginPath();
      ctx.moveTo(x, 0); ctx.lineTo(x, CANVAS_H);
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // Label axis ticks
    ctx.fillStyle = "rgba(255,255,255,0.4)";
    ctx.font = "10px monospace";
    for (let k = -3; k <= 3; k++) {
      const x = ((k - CR_LO) / (CR_HI - CR_LO)) * CANVAS_W;
      ctx.fillText(String(k), x + 3, CANVAS_H / 2 - 4);
    }
    ctx.fillText(yHi.toFixed(2), 6, 14);
    ctx.fillText(yLo.toFixed(2), 6, CANVAS_H - 6);
  }, [diagram, yRange, hoverCr, op]);

  // Audio: play tones from tail values at current hoverCr
  const playTailAt = useCallback((cr) => {
    if (!audioOn || !diagram) return;
    const ctxA = audioCtxRef.current;
    if (!ctxA) return;
    // Find nearest cr index
    const idx = Math.round(((cr - CR_LO) / (CR_HI - CR_LO)) * (N_CR - 1));
    const entry = diagram[Math.max(0, Math.min(N_CR - 1, idx))];
    if (!entry || entry.tail.length === 0) return;
    // Play up to 4 tones
    const now = ctxA.currentTime;
    const master = masterGainRef.current;
    const tones = entry.tail.slice(-4);
    tones.forEach((v, i) => {
      const freq = 220 * Math.pow(2, Math.max(-2, Math.min(2, v / 2)));
      const osc = ctxA.createOscillator();
      const g = ctxA.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      osc.connect(g); g.connect(master);
      const t0 = now + i * 0.05;
      g.gain.setValueAtTime(0, t0);
      g.gain.linearRampToValueAtTime(0.12, t0 + 0.01);
      g.gain.linearRampToValueAtTime(0, t0 + 0.18);
      osc.start(t0); osc.stop(t0 + 0.2);
    });
  }, [audioOn, diagram]);

  function ensureAudio() {
    if (audioCtxRef.current) return;
    const ctxA = new (window.AudioContext || window.webkitAudioContext)();
    const master = ctxA.createGain();
    master.gain.value = 0.22;
    master.connect(ctxA.destination);
    audioCtxRef.current = ctxA;
    masterGainRef.current = master;
  }

  const onCanvasMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * CANVAS_W;
    const cr = CR_LO + (px / CANVAS_W) * (CR_HI - CR_LO);
    setHoverCr(cr);
  };
  const onCanvasLeave = () => setHoverCr(null);
  const onCanvasClick = () => {
    if (!audioOn) { ensureAudio(); setAudioOn(true); }
    if (hoverCr !== null) playTailAt(hoverCr);
  };

  useEffect(() => {
    if (!audioOn || hoverCr === null) return;
    playTailAt(hoverCr);
  }, [hoverCr, audioOn, playTailAt]);

  useEffect(() => () => {
    if (audioCtxRef.current) { try { audioCtxRef.current.close(); } catch {} }
  }, []);

  const meta = OP_META[op];

  return (
    <div style={S.root}>
      <header style={S.header}>
        <span style={S.brand}>monogate</span>
        <span style={S.subBrand}>bifurcation viewer</span>
        <span style={S.formula}>z → {meta.formula}</span>
      </header>

      <div style={S.topBar}>
        {Object.entries(OP_META).map(([key, m]) => (
          <button
            key={key}
            onClick={() => setOp(key)}
            style={{
              ...S.opBtn,
              background: op === key ? m.color : "rgba(255,255,255,0.04)",
              color: op === key ? "#08080c" : "rgba(255,255,255,0.5)",
              border: op === key ? "none" : "1px solid rgba(255,255,255,0.08)",
              fontWeight: op === key ? 600 : 400,
            }}
          >
            {m.label}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <button
          onClick={() => {
            if (!audioOn) { ensureAudio(); setAudioOn(true); }
            else setAudioOn(false);
          }}
          style={{
            ...S.btn,
            background: audioOn ? "rgba(255,255,255,0.12)" : "transparent",
            color: audioOn ? "#e8e8f0" : "rgba(255,255,255,0.4)",
          }}
        >
          audio {audioOn ? "on" : "off"}
        </button>
      </div>

      <div style={S.stageWrap}>
        <canvas
          ref={canvasRef}
          width={CANVAS_W}
          height={CANVAS_H}
          style={S.canvas}
          onMouseMove={onCanvasMove}
          onMouseLeave={onCanvasLeave}
          onClick={onCanvasClick}
        />
        <div style={S.badgeCol}>
          {meta.sharkovskii && (
            <span style={S.sharkBadge}>Sharkovskii · period 3 → all</span>
          )}
          {meta.chaotic && (
            <span style={S.chaoticBadge}>chaotic sweep</span>
          )}
          {!meta.chaotic && !meta.sharkovskii && (
            <span style={S.tameBadge}>period ≤ 2</span>
          )}
        </div>
      </div>

      <div style={S.readout}>
        <span>
          cr = {hoverCr === null ? "—" : hoverCr.toFixed(3)}
        </span>
        <span style={{ color: meta.color }}>{meta.label}</span>
        <span>{diagram ? `${N_CR} cr-samples · ${TAIL}-step tail` : "computing…"}</span>
      </div>

      <div style={S.help}>
        The bifurcation diagram iterates z<sub>n+1</sub> = op(z<sub>n</sub>, c) from z<sub>0</sub> = 0
        for each real c ∈ [−3, 3], discards {WARM} warm-up steps, plots the
        next {TAIL} values of Re(z). Additive and divisive operators collapse
        to period-2 bands. Multiplicative operators (EXL, DEXL) show chaotic
        bands; DEXL contains period 3, implying by Sharkovskii that every
        other period also lives inside the diagram.
        Hover → audio-tail on the current c. Click to retrigger.
      </div>
    </div>
  );
}

const FONT = "'IBM Plex Mono', 'SF Mono', 'Fira Code', monospace";

const S = {
  root: {
    background: "#08080c",
    color: "#e8e8f0",
    fontFamily: FONT,
    minHeight: "100vh",
    padding: "20px 24px 80px",
  },
  header: {
    display: "flex", gap: 16, alignItems: "baseline", flexWrap: "wrap",
    marginBottom: 14, paddingBottom: 10,
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  brand: {
    fontSize: 13, fontWeight: 600, letterSpacing: "0.15em",
    textTransform: "uppercase", color: "#4facfe",
  },
  subBrand: { fontSize: 13, color: "rgba(255,255,255,0.3)" },
  formula: { fontSize: 11, color: "rgba(255,255,255,0.2)", marginLeft: "auto" },

  topBar: {
    display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center",
    marginBottom: 12,
  },
  opBtn: {
    borderRadius: 4, padding: "5px 12px", fontSize: 12,
    fontFamily: "inherit", cursor: "pointer", transition: "all 0.2s",
  },
  btn: {
    borderRadius: 4, padding: "4px 10px", fontSize: 11, fontFamily: "inherit",
    cursor: "pointer", border: "1px solid rgba(255,255,255,0.1)",
    background: "transparent", color: "rgba(255,255,255,0.5)",
  },

  stageWrap: {
    position: "relative",
    maxWidth: CANVAS_W,
    width: "100%",
    aspectRatio: `${CANVAS_W} / ${CANVAS_H}`,
    border: "1px solid rgba(255,255,255,0.06)",
    borderRadius: 6,
    overflow: "hidden",
  },
  canvas: {
    width: "100%", height: "100%", display: "block", cursor: "crosshair",
  },
  badgeCol: {
    position: "absolute", top: 10, right: 10,
    display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-end",
  },
  sharkBadge: {
    background: "#f87171", color: "#08080c",
    fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 3,
    letterSpacing: "0.04em",
  },
  chaoticBadge: {
    background: "rgba(252,203,82,0.22)", color: "#fccb52",
    fontSize: 10, fontWeight: 600, padding: "3px 8px", borderRadius: 3,
    border: "1px solid rgba(252,203,82,0.4)",
  },
  tameBadge: {
    background: "rgba(79,172,254,0.18)", color: "#4facfe",
    fontSize: 10, fontWeight: 600, padding: "3px 8px", borderRadius: 3,
    border: "1px solid rgba(79,172,254,0.35)",
  },
  readout: {
    display: "flex", gap: 18, marginTop: 10,
    color: "rgba(255,255,255,0.5)", fontSize: 11,
  },
  help: {
    maxWidth: 720, marginTop: 20, lineHeight: 1.7, fontSize: 12,
    color: "rgba(255,255,255,0.55)", fontFamily: "system-ui, sans-serif",
  },
};
