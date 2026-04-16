// explorer/src/components/AttractorViz.jsx
// Phantom Attractor Lab — animated visualization of EMLTree(depth=3) training
// trajectories for fitting pi.  Data pre-computed in gen_attractor_data.py.

import { useState, useEffect, useRef, useCallback } from "react";

const C = {
  bg: "#07080f", surface: "#0d0e1c", border: "#191b2e",
  text: "#cdd0e0", muted: "#4e5168", accent: "#e8a020",
  blue: "#6ab0f5", green: "#5ec47a", red: "#e05060",
  orange: "#f97316", purple: "#a78bfa",
};

// Color per destiny
const DESTINY_COLOR = {
  pi:        C.green,
  attractor: C.orange,
  diverged:  C.muted,
};

const PI_VAL = 3.14159265;
const ATTRACTOR_VAL = 3.169642;

// Clamp a value to a displayable range
function clamp(v, lo, hi) {
  if (v === null || v === undefined || !isFinite(v)) return null;
  return Math.max(lo, Math.min(hi, v));
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatBadge({ label, value, color }) {
  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`,
      borderRadius: 6, padding: "10px 14px", textAlign: "center", flex: 1,
    }}>
      <div style={{ fontSize: 22, fontWeight: 700, color, letterSpacing: "-0.02em" }}>
        {value}
      </div>
      <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase",
        letterSpacing: "0.10em", marginTop: 3 }}>
        {label}
      </div>
    </div>
  );
}

function LegendDot({ color, label }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10, color: C.muted }}>
      <div style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
      {label}
    </div>
  );
}

// ── Canvas renderer ───────────────────────────────────────────────────────────

function LossCanvas({ runs, frame, width, height }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !runs.length) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;

    // Canvas physical size
    canvas.width  = width  * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, width, height);

    // Background
    ctx.fillStyle = C.bg;
    ctx.fillRect(0, 0, width, height);

    const pad = { top: 20, right: 16, bottom: 36, left: 52 };
    const plotW = width  - pad.left - pad.right;
    const plotH = height - pad.top  - pad.bottom;

    const nPts  = runs[0].loss.length;
    const steps = (nPts - 1) * 20;   // record_every=20

    // Y axis: log scale loss 1e-10 to 1e2
    const yMin = -10, yMax = 2;   // log10 range
    const toY = (loss) => {
      if (loss === null || loss <= 0) return pad.top + plotH;
      const l = Math.max(yMin, Math.min(yMax, Math.log10(loss)));
      return pad.top + plotH - ((l - yMin) / (yMax - yMin)) * plotH;
    };
    const toX = (i) => pad.left + (i / (nPts - 1)) * plotW;

    // Grid lines
    ctx.strokeStyle = C.border;
    ctx.lineWidth   = 0.5;
    for (let exp = yMin; exp <= yMax; exp += 2) {
      const y = pad.top + plotH - ((exp - yMin) / (yMax - yMin)) * plotH;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + plotW, y);
      ctx.stroke();
    }

    // X-axis gridlines at every 600 steps
    for (let s = 0; s <= steps; s += 600) {
      const x = pad.left + (s / steps) * plotW;
      ctx.beginPath();
      ctx.moveTo(x, pad.top);
      ctx.lineTo(x, pad.top + plotH);
      ctx.stroke();
    }

    // Axis labels
    ctx.fillStyle  = C.muted;
    ctx.font       = `9px 'Space Mono', monospace`;
    ctx.textAlign  = "right";
    ctx.textBaseline = "middle";
    for (let exp = yMin; exp <= yMax; exp += 2) {
      const y = pad.top + plotH - ((exp - yMin) / (yMax - yMin)) * plotH;
      ctx.fillText(`1e${exp}`, pad.left - 4, y);
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let s = 0; s <= steps; s += 600) {
      const x = pad.left + (s / steps) * plotW;
      ctx.fillText(String(s), x, pad.top + plotH + 4);
    }

    // Y axis label
    ctx.save();
    ctx.translate(10, pad.top + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillText("loss (log)", 0, 0);
    ctx.restore();

    // X axis label
    ctx.textAlign    = "center";
    ctx.textBaseline = "bottom";
    ctx.fillText("step", pad.left + plotW / 2, height - 2);

    // Draw each run's trajectory up to frame
    const endFrame = Math.min(frame, nPts - 1);
    for (const run of runs) {
      ctx.strokeStyle = DESTINY_COLOR[run.destiny] ?? C.muted;
      ctx.globalAlpha = run.destiny === "diverged" ? 0.12 : 0.45;
      ctx.lineWidth   = run.destiny === "diverged" ? 0.5 : 1.2;
      ctx.beginPath();
      let started = false;
      for (let i = 0; i <= endFrame; i++) {
        const y = toY(run.loss[i]);
        const x = toX(i);
        if (!started) { ctx.moveTo(x, y); started = true; }
        else           { ctx.lineTo(x, y); }
      }
      ctx.stroke();
    }
    ctx.globalAlpha = 1;

    // Current frame marker
    if (endFrame > 0 && endFrame < nPts - 1) {
      const xMark = toX(endFrame);
      ctx.strokeStyle = C.accent;
      ctx.lineWidth   = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(xMark, pad.top);
      ctx.lineTo(xMark, pad.top + plotH);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Border
    ctx.strokeStyle = C.border;
    ctx.lineWidth   = 1;
    ctx.strokeRect(pad.left, pad.top, plotW, plotH);

  }, [runs, frame, width, height]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width, height, display: "block", borderRadius: 4 }}
    />
  );
}

function ValueCanvas({ runs, frame, width, height }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !runs.length) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;

    canvas.width  = width  * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = C.bg;
    ctx.fillRect(0, 0, width, height);

    const pad   = { top: 20, right: 16, bottom: 36, left: 52 };
    const plotW = width  - pad.left - pad.right;
    const plotH = height - pad.top  - pad.bottom;

    const nPts  = runs[0].value.length;
    const steps = (nPts - 1) * 20;

    // Y range: [2.5, 4.5] — shows π and attractor clearly
    const yLo = 2.5, yHi = 4.5;
    const toY = (v) => {
      const vc = clamp(v, yLo, yHi);
      if (vc === null) return pad.top + plotH;
      return pad.top + plotH - ((vc - yLo) / (yHi - yLo)) * plotH;
    };
    const toX = (i) => pad.left + (i / (nPts - 1)) * plotW;

    // Grid
    ctx.strokeStyle = C.border;
    ctx.lineWidth   = 0.5;
    for (let v = 2.5; v <= 4.5; v += 0.5) {
      const y = toY(v);
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + plotW, y);
      ctx.stroke();
    }

    // Reference lines: π and attractor
    const piY  = toY(PI_VAL);
    const attY = toY(ATTRACTOR_VAL);

    ctx.strokeStyle = C.green;
    ctx.lineWidth   = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(pad.left, piY);
    ctx.lineTo(pad.left + plotW, piY);
    ctx.stroke();

    ctx.strokeStyle = C.orange;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(pad.left, attY);
    ctx.lineTo(pad.left + plotW, attY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Labels for reference lines
    ctx.font = `8px 'Space Mono', monospace`;
    ctx.textAlign = "left";
    ctx.textBaseline = "bottom";
    ctx.fillStyle = C.green;
    ctx.fillText("\u03c0", pad.left + plotW + 2, piY + 1);
    ctx.fillStyle = C.orange;
    ctx.fillText("att", pad.left + plotW + 2, attY + 1);

    // Y axis labels
    ctx.fillStyle  = C.muted;
    ctx.textAlign  = "right";
    ctx.textBaseline = "middle";
    for (let v = 2.5; v <= 4.5; v += 0.5) {
      ctx.fillText(v.toFixed(1), pad.left - 4, toY(v));
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let s = 0; s <= steps; s += 600) {
      const x = pad.left + (s / steps) * plotW;
      ctx.fillText(String(s), x, pad.top + plotH + 4);
    }

    // Y axis label
    ctx.save();
    ctx.translate(10, pad.top + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillStyle = C.muted;
    ctx.textBaseline = "middle";
    ctx.fillText("tree value", 0, 0);
    ctx.restore();

    // Draw trajectories
    const endFrame = Math.min(frame, nPts - 1);
    for (const run of runs) {
      ctx.strokeStyle = DESTINY_COLOR[run.destiny] ?? C.muted;
      ctx.globalAlpha = run.destiny === "diverged" ? 0.10 : 0.45;
      ctx.lineWidth   = run.destiny === "diverged" ? 0.5 : 1.2;
      ctx.beginPath();
      let started = false;
      for (let i = 0; i <= endFrame; i++) {
        const v = run.value[i];
        if (v === null || v === undefined || !isFinite(v) || Math.abs(v) > 100) continue;
        const x = toX(i);
        const y = toY(v);
        if (!started) { ctx.moveTo(x, y); started = true; }
        else           { ctx.lineTo(x, y); }
      }
      ctx.stroke();
    }
    ctx.globalAlpha = 1;

    // Frame marker
    if (endFrame > 0 && endFrame < nPts - 1) {
      const xMark = toX(endFrame);
      ctx.strokeStyle = C.accent;
      ctx.lineWidth   = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(xMark, pad.top);
      ctx.lineTo(xMark, pad.top + plotH);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Border
    ctx.strokeStyle = C.border;
    ctx.lineWidth   = 1;
    ctx.strokeRect(pad.left, pad.top, plotW, plotH);

  }, [runs, frame, width, height]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width, height, display: "block", borderRadius: 4 }}
    />
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function AttractorViz() {
  const [data,       setData]       = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState(null);
  const [lam,        setLam]        = useState(0.0);    // active lambda
  const [frame,      setFrame]      = useState(0);
  const [playing,    setPlaying]    = useState(false);
  const [speed,      setSpeed]      = useState(2);      // frames per tick
  const rafRef = useRef(null);
  const lastTickRef = useRef(0);

  // Load data once
  useEffect(() => {
    fetch("/attractor_data.json")
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  const nFrames = data ? data.meta.n_points : 1;

  // Animation loop
  const tick = useCallback((ts) => {
    if (ts - lastTickRef.current < 30) {   // ~33 fps max
      rafRef.current = requestAnimationFrame(tick);
      return;
    }
    lastTickRef.current = ts;
    setFrame(prev => {
      const next = prev + speed;
      if (next >= nFrames - 1) {
        setPlaying(false);
        return nFrames - 1;
      }
      return next;
    });
    rafRef.current = requestAnimationFrame(tick);
  }, [speed, nFrames]);

  useEffect(() => {
    if (playing) {
      rafRef.current = requestAnimationFrame(tick);
    } else {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    }
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [playing, tick]);

  const handlePlay = () => {
    if (frame >= nFrames - 1) setFrame(0);
    setPlaying(p => !p);
  };

  const handleReset = () => {
    setPlaying(false);
    setFrame(0);
  };

  // Filter runs for current lambda
  const runs = data
    ? data.runs.filter(r => r.lam === lam)
    : [];

  const nPi  = runs.filter(r => r.destiny === "pi").length;
  const nAtt = runs.filter(r => r.destiny === "attractor").length;
  const nDiv = runs.filter(r => r.destiny === "diverged").length;
  const stepLabel = data
    ? Math.min(frame, nFrames - 1) * data.meta.record_every
    : 0;

  const canvasW = 340;
  const canvasH = 200;

  if (loading) {
    return (
      <div style={{ color: C.muted, fontSize: 11, padding: 40 }}>
        Loading attractor data…
      </div>
    );
  }
  if (error) {
    return (
      <div style={{ color: C.red, fontSize: 11, padding: 40 }}>
        Error loading data: {error}
      </div>
    );
  }

  return (
    <div style={{ fontFamily: "'Space Mono', monospace", color: C.text }}>

      {/* Title */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: C.accent, marginBottom: 6 }}>
          Attractor Lab
        </div>
        <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.7, maxWidth: 600 }}>
          EMLTree(depth=3) fitting target π.  40 random seeds, Adam optimizer.
          At <strong style={{ color: C.text }}>λ=0</strong> all seeds collapse to the phantom attractor ~3.1696.
          A tiny penalty <strong style={{ color: C.text }}>λ=0.005</strong> breaks the trap — all seeds reach π.
        </div>
      </div>

      {/* Controls */}
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`,
        borderRadius: 8, padding: "12px 16px", marginBottom: 16,
        display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center",
      }}>

        {/* Lambda toggle */}
        <div style={{ display: "flex", gap: 0, borderRadius: 5, overflow: "hidden",
          border: `1px solid ${C.border}` }}>
          {[0.0, 0.005].map(l => (
            <button key={l}
              onClick={() => { setLam(l); setFrame(0); setPlaying(false); }}
              style={{
                padding: "6px 14px", fontSize: 10, border: "none",
                background: lam === l ? "rgba(232,160,32,0.18)" : "transparent",
                color: lam === l ? C.accent : C.muted,
                fontFamily: "'Space Mono', monospace", cursor: "pointer",
                fontWeight: lam === l ? 700 : 400,
                borderRight: l === 0.0 ? `1px solid ${C.border}` : "none",
              }}>
              λ = {l.toFixed(3)}
            </button>
          ))}
        </div>

        {/* Play / Pause */}
        <button onClick={handlePlay} style={{
          padding: "6px 16px", fontSize: 10, borderRadius: 5,
          background: playing ? "rgba(94,196,122,0.12)" : "rgba(232,160,32,0.12)",
          border: `1px solid ${playing ? C.green : C.accent}`,
          color: playing ? C.green : C.accent,
          fontFamily: "'Space Mono', monospace", cursor: "pointer", fontWeight: 700,
        }}>
          {playing ? "⏸ Pause" : frame >= nFrames - 1 ? "↺ Replay" : "▶ Play"}
        </button>

        {/* Reset */}
        <button onClick={handleReset} style={{
          padding: "6px 12px", fontSize: 10, borderRadius: 5,
          background: "transparent", border: `1px solid ${C.border}`,
          color: C.muted, fontFamily: "'Space Mono', monospace", cursor: "pointer",
        }}>
          Reset
        </button>

        {/* Speed */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 10, color: C.muted }}>
          <span>Speed</span>
          <input type="range" min={1} max={8} value={speed}
            onChange={e => setSpeed(Number(e.target.value))}
            style={{ width: 70 }} />
          <span style={{ color: C.text, minWidth: 12 }}>{speed}×</span>
        </div>

        {/* Frame scrubber */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 10, color: C.muted, flex: 1, minWidth: 120 }}>
          <span style={{ whiteSpace: "nowrap" }}>step {stepLabel}</span>
          <input type="range" min={0} max={nFrames - 1} value={frame}
            onChange={e => { setPlaying(false); setFrame(Number(e.target.value)); }}
            style={{ flex: 1 }} />
          <span>{(data?.meta.steps ?? 0)}</span>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
        <StatBadge
          label={lam === 0.0 ? "reach \u03c0 (none)" : "reach \u03c0"}
          value={`${nPi}/40`}
          color={nPi > 20 ? C.green : C.red}
        />
        <StatBadge
          label="phantom attractor"
          value={`${nAtt}/40`}
          color={nAtt > 20 ? C.orange : C.muted}
        />
        <StatBadge
          label="diverged"
          value={`${nDiv}/40`}
          color={nDiv > 0 ? C.muted : C.green}
        />
      </div>

      {/* Plots */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.10em",
            textTransform: "uppercase", marginBottom: 6 }}>
            Loss
          </div>
          <LossCanvas runs={runs} frame={frame} width={canvasW} height={canvasH} />
        </div>
        <div>
          <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.10em",
            textTransform: "uppercase", marginBottom: 6 }}>
            Formula Value
          </div>
          <ValueCanvas runs={runs} frame={frame} width={canvasW} height={canvasH} />
        </div>
      </div>

      {/* Legend */}
      <div style={{
        display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 16,
        padding: "8px 12px",
        background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
      }}>
        <LegendDot color={C.green}  label={`pi (target ${PI_VAL.toFixed(5)})`} />
        <LegendDot color={C.orange} label={`phantom attractor (${ATTRACTOR_VAL.toFixed(5)})`} />
        <LegendDot color={C.muted}  label="diverged" />
      </div>

      {/* Explanation card */}
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`,
        borderRadius: 8, padding: "14px 16px",
        fontSize: 10, color: C.muted, lineHeight: 1.8,
      }}>
        <div style={{ fontWeight: 700, color: C.text, marginBottom: 8, fontSize: 11 }}>
          What is the phantom attractor?
        </div>
        <p style={{ margin: "0 0 8px" }}>
          The EML grammar generates many "simple" constants as low-complexity trees —
          for example, <span style={{ color: C.accent }}>eml(1,1) = e</span>,{" "}
          <span style={{ color: C.accent }}>eml(eml(1,1),1) = e^e - 0 ≈ 15.15</span>.
          Near {ATTRACTOR_VAL.toFixed(4)}, the loss surface has a shallow bowl that
          traps gradient descent.
        </p>
        <p style={{ margin: 0 }}>
          Adding a complexity penalty <span style={{ color: C.accent }}>λ·Σ|leaf − 1|</span>{" "}
          tilts the landscape: the penalty is near-zero at π (leaves stay close to 1
          in the optimal construction) but large at the phantom attractor.  A tiny
          λ=0.005 is enough to flip convergence from 0% → 100% to π.
        </p>
      </div>

      {/* Footer citation */}
      <div style={{ marginTop: 16, fontSize: 9, color: C.muted }}>
        Data: EMLTree(depth=3), 40 seeds, 3000 steps, Adam lr=5×10⁻³ ·
        Odrzywołek, A. (2026) · arXiv:2603.21852
      </div>
    </div>
  );
}
