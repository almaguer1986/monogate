// EML Synthesizer — Fourier synthesis as EML nodes (S1)
// Each harmonic = 1 complex EML node: Im(eml(i·2πft, 1)) = sin(2πft)
// Web Audio API synthesis with harmonic amplitude sliders.

import { useState, useRef, useCallback, useEffect } from "react";

const C = {
  bg: "#07080f", surface: "#0d0e1c", border: "#191b2e",
  text: "#cdd0e0", muted: "#4e5168", accent: "#e8a020",
  blue: "#6ab0f5", green: "#5ec47a", red: "#e05060",
  orange: "#f97316", purple: "#a78bfa",
};

// ── Precomputed timbre data (from S2 computational session) ───────────────────

const PRESETS = {
  sine:      { label: "Sine",       nodes: 1,  harmonics: [1.0, 0, 0, 0, 0, 0, 0, 0] },
  clarinet:  { label: "Clarinet",   nodes: 5,  harmonics: [0.5, 0, 0.8, 0, 0.6, 0, 0.3, 0] },
  violin:    { label: "Violin",     nodes: 12, harmonics: [0.9, 0.7, 0.5, 0.4, 0.3, 0.2, 0.15, 0.1] },
  piano:     { label: "Piano A4",   nodes: 12, harmonics: [1.0, 0.6, 0.2, 0.4, 0.1, 0.05, 0.03, 0.02] },
  bell:      { label: "Bell",       nodes: 7,  harmonics: [0.1, 0.0, 0.0, 0.8, 0.0, 0.5, 0.0, 0.0] },
  sawtooth:  { label: "Sawtooth",   nodes: 8,  harmonics: [1.0, 0.5, 0.33, 0.25, 0.2, 0.17, 0.14, 0.125] },
  square:    { label: "Square",     nodes: 4,  harmonics: [1.0, 0, 0.33, 0, 0.2, 0, 0.14, 0] },
};

const N_HARMONICS = 8;
const BASE_FREQ = 440; // A4

// ── Waveform visualization ────────────────────────────────────────────────────

function WaveformCanvas({ harmonics, width = 400, height = 80 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = C.surface;
    ctx.fillRect(0, 0, width, height);

    // draw center line
    ctx.strokeStyle = C.border;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();

    // synthesize one period
    const N = width;
    const points = [];
    for (let i = 0; i < N; i++) {
      const t = i / N;
      let y = 0;
      for (let h = 0; h < N_HARMONICS; h++) {
        y += harmonics[h] * Math.sin(2 * Math.PI * (h + 1) * t);
      }
      points.push(y);
    }
    const maxAmp = Math.max(...points.map(Math.abs), 0.01);
    const scale = (height / 2 - 4) / maxAmp;

    ctx.strokeStyle = C.accent;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i < N; i++) {
      const x = i;
      const y = height / 2 - points[i] * scale;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
  }, [harmonics, width, height]);

  return (
    <canvas ref={canvasRef} width={width} height={height}
      style={{ display: "block", borderRadius: 4, border: `1px solid ${C.border}` }} />
  );
}

// ── Spectrum bar display ──────────────────────────────────────────────────────

function SpectrumBars({ harmonics }) {
  return (
    <div style={{ display: "flex", gap: 4, alignItems: "flex-end", height: 60 }}>
      {harmonics.map((amp, i) => (
        <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
          <div style={{
            width: 20, background: C.blue,
            height: Math.max(2, Math.round(amp * 52)),
            borderRadius: "2px 2px 0 0",
            transition: "height 0.15s",
          }} />
          <div style={{ fontSize: 8, color: C.muted }}>H{i+1}</div>
        </div>
      ))}
    </div>
  );
}

// ── Audio engine ──────────────────────────────────────────────────────────────

function useAudioEngine() {
  const ctxRef = useRef(null);
  const oscRefs = useRef([]);

  function stop() {
    if (!ctxRef.current) return;
    oscRefs.current.forEach(o => { try { o.stop(); o.disconnect(); } catch {} });
    oscRefs.current = [];
  }

  function play(harmonics, duration = 1.5) {
    stop();
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    ctxRef.current = ctx;
    const master = ctx.createGain();
    master.gain.value = 0.4;
    master.connect(ctx.destination);

    harmonics.forEach((amp, i) => {
      if (amp < 0.001) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = BASE_FREQ * (i + 1);
      gain.gain.value = amp;
      osc.connect(gain);
      gain.connect(master);
      osc.start();
      osc.stop(ctx.currentTime + duration);
      oscRefs.current.push(osc);
    });

    // fade out
    master.gain.setTargetAtTime(0, ctx.currentTime + duration - 0.1, 0.05);
  }

  return { play, stop };
}

// ── Main component ────────────────────────────────────────────────────────────

// SuperBEST node costs for reference
const SB_COS = 63;  // sin/cos via EXL 8-term Taylor
const EML_COS = 245;

export default function EMLSynthesizer() {
  const [harmonics, setHarmonics] = useState([...PRESETS.sine.harmonics]);
  const [preset, setPreset] = useState("sine");
  const [playing, setPlaying] = useState(false);
  const [autoBest, setAutoBest] = useState(false);
  const audio = useAudioEngine();

  function applyPreset(key) {
    setPreset(key);
    setHarmonics([...PRESETS[key].harmonics]);
  }

  function setHarmonic(i, val) {
    setHarmonics(prev => {
      const next = [...prev];
      next[i] = val;
      return next;
    });
    setPreset("custom");
  }

  function handlePlay() {
    setPlaying(true);
    audio.play(harmonics);
    setTimeout(() => setPlaying(false), 1600);
  }

  const activeNodes = harmonics.filter(a => a > 0.001).length;
  // Auto-BEST insight: each harmonic = 1 complex EML node (not SB_COS nodes)
  // because Im(eml(i·2πft, 1)) uses the COMPLEX EML identity directly.
  const bestNodes = activeNodes;   // 1 complex EML node per harmonic
  const naiveNodes = activeNodes * EML_COS;  // naive: 245n per sin

  return (
    <div style={{ background: C.bg, color: C.text, minHeight: "100vh", padding: 24, fontFamily: "monospace" }}>
      {/* Header row with Auto-BEST toggle */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h2 style={{ color: C.accent, margin: 0, fontSize: 20 }}>EML Synthesizer</h2>
          <p style={{ color: C.muted, fontSize: 11, margin: "4px 0 0" }}>
            Each harmonic = 1 complex EML node: Im(eml(i·2πft, 1)) = sin(2πft).
            Timbre complexity = number of active EML nodes.
          </p>
        </div>
        {/* Auto-BEST toggle */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          background: autoBest ? "rgba(94,196,122,0.08)" : C.surface,
          border: `1px solid ${autoBest ? "rgba(94,196,122,0.3)" : C.border}`,
          borderRadius: 8, padding: "10px 14px",
        }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: autoBest ? C.green : C.muted }}>
              Auto-BEST
            </div>
            <div style={{ fontSize: 8, color: C.muted }}>
              {autoBest
                ? `${bestNodes}n · complex EML Euler route`
                : `${activeNodes * SB_COS}n · naive sin/cos`}
            </div>
          </div>
          <button
            onClick={() => setAutoBest(v => !v)}
            style={{
              width: 40, height: 22, borderRadius: 11, position: "relative",
              background: autoBest ? C.green : C.border,
              border: "none", cursor: "pointer", transition: "background 0.2s",
              flexShrink: 0,
            }}
          >
            <div style={{
              position: "absolute", top: 3, left: autoBest ? 21 : 3,
              width: 16, height: 16, borderRadius: "50%",
              background: autoBest ? C.bg : C.muted,
              transition: "left 0.2s",
            }} />
          </button>
        </div>
      </div>

      {/* Auto-BEST explanation panel */}
      {autoBest && (
        <div style={{
          background: "rgba(94,196,122,0.06)", border: "1px solid rgba(94,196,122,0.2)",
          borderRadius: 8, padding: "12px 16px", marginBottom: 16,
          display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12,
        }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.green }}>{bestNodes}n</div>
            <div style={{ fontSize: 9, color: C.muted }}>SuperBEST nodes</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.muted }}>{naiveNodes}n</div>
            <div style={{ fontSize: 9, color: C.muted }}>Naive (245n/harmonic)</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: C.accent }}>
              {naiveNodes > 0 ? Math.round((1 - bestNodes / naiveNodes) * 100) : 0}%
            </div>
            <div style={{ fontSize: 9, color: C.muted }}>Savings</div>
          </div>
          <div style={{ gridColumn: "1/-1", fontSize: 9, color: C.muted, marginTop: 4, lineHeight: 1.7 }}>
            Identity: <span style={{ color: C.green, fontFamily: "monospace" }}>
              Im(eml(i·2πft, 1)) = sin(2πft)
            </span> — each harmonic is exactly 1 complex EML node via the Euler formula.
            Sound is identical in both modes. The representation changes, not the math.
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {/* Presets */}
        <div style={{ minWidth: 180 }}>
          <div style={{ fontSize: 10, color: C.muted, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.1em" }}>Presets</div>
          {Object.entries(PRESETS).map(([key, p]) => (
            <button key={key} onClick={() => applyPreset(key)} style={{
              display: "flex", justifyContent: "space-between", width: "100%",
              background: preset === key ? C.surface : "transparent",
              border: `1px solid ${preset === key ? C.accent : C.border}`,
              borderRadius: 4, padding: "6px 10px", marginBottom: 4,
              color: preset === key ? C.accent : C.muted, fontSize: 10, cursor: "pointer",
            }}>
              <span>{p.label}</span>
              {autoBest
                ? <span style={{ color: C.green }}>{p.nodes}n <span style={{ color: C.muted, fontSize: 8 }}>BEST</span></span>
                : <span style={{ color: C.muted }}>{p.nodes * SB_COS}n</span>
              }
            </button>
          ))}
        </div>

        {/* Main panel */}
        <div style={{ flex: 1, minWidth: 300 }}>
          {/* Waveform */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 10, color: C.muted, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.1em" }}>Waveform</div>
            <WaveformCanvas harmonics={harmonics} width={400} height={80} />
          </div>

          {/* Spectrum */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 10, color: C.muted, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.1em" }}>Spectrum</div>
            <SpectrumBars harmonics={harmonics} />
          </div>

          {/* Harmonic sliders */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 10, color: C.muted, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.1em" }}>Harmonic Amplitudes</div>
            {harmonics.map((amp, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                <div style={{ width: 40, fontSize: 10, color: C.muted, flexShrink: 0 }}>
                  H{i+1} <span style={{ color: C.text }}>{(BASE_FREQ * (i+1))}Hz</span>
                </div>
                <input type="range" min={0} max={1} step={0.01} value={amp}
                  onChange={e => setHarmonic(i, parseFloat(e.target.value))}
                  style={{ flex: 1, accentColor: C.blue }}
                />
                <div style={{ width: 34, textAlign: "right", fontSize: 10, color: amp > 0.01 ? C.blue : C.muted }}>
                  {amp.toFixed(2)}
                </div>
              </div>
            ))}
          </div>

          {/* Play + node count */}
          <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
            <button onClick={handlePlay} disabled={playing} style={{
              background: playing ? C.surface : C.accent,
              border: "none", borderRadius: 6, color: playing ? C.muted : C.bg,
              fontSize: 13, fontWeight: 700, padding: "10px 24px", cursor: playing ? "not-allowed" : "pointer",
            }}>
              {playing ? "Playing…" : "▶ Play"}
            </button>
            <div style={{ background: C.surface, border: `1px solid ${autoBest ? "rgba(94,196,122,0.3)" : C.border}`, borderRadius: 6, padding: "8px 16px" }}>
              <span style={{ color: C.muted, fontSize: 10 }}>{autoBest ? "SuperBEST nodes: " : "EML nodes: "}</span>
              <span style={{ color: autoBest ? C.green : C.green, fontSize: 16, fontWeight: 700 }}>
                {autoBest ? bestNodes : activeNodes}
              </span>
              {autoBest && <span style={{ color: C.muted, fontSize: 9, marginLeft: 4 }}>/ {naiveNodes}n naive</span>}
            </div>
            <div style={{ fontSize: 9, color: C.muted }}>
              {autoBest
                ? `Euler: Im(eml(i·2πft, 1)) per harmonic`
                : `Base: ${BASE_FREQ} Hz (A4)`}
            </div>
          </div>
        </div>
      </div>

      {/* Theory note */}
      <div style={{
        marginTop: 24, padding: 12,
        background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
        fontSize: 10, color: C.muted, maxWidth: 720,
      }}>
        <span style={{ color: C.text }}>EML-Fourier identity:</span>&nbsp;
        Im(eml(i·2πft, 1)) = Im(exp(i·2πft) − ln(1)) = Im(e^(i·2πft)) = sin(2πft).
        Each partial = one complex EML node. Timbre complexity = EML node count.
        Instrument data from S2 computational session (F1–F4, S1–S4).
      </div>
    </div>
  );
}
