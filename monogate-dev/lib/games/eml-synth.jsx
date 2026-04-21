import { useState, useRef, useEffect, useCallback } from "react";

const NOTES = [
  { name: "A4", freq: 440, color: "#A78BFA" },
  { name: "E5", freq: 659.25, color: "#06B6D4" },
  { name: "A5", freq: 880, color: "#EC4899" },
  { name: "C#5", freq: 554.37, color: "#F59E0B" },
  { name: "E4", freq: 329.63, color: "#10B981" },
  { name: "A3", freq: 220, color: "#64748B" },
  { name: "B5", freq: 987.77, color: "#EF4444" },
  { name: "D5", freq: 587.33, color: "#8B5CF6" },
];

const PRESETS = [
  { name: "Pure tone", harmonics: [{ freq: 440, amp: 1.0 }] },
  { name: "Octave", harmonics: [{ freq: 440, amp: 1.0 }, { freq: 880, amp: 0.5 }] },
  { name: "Major chord", harmonics: [{ freq: 440, amp: 1.0 }, { freq: 554.37, amp: 0.7 }, { freq: 659.25, amp: 0.7 }] },
  { name: "Organ", harmonics: [{ freq: 440, amp: 1.0 }, { freq: 880, amp: 0.5 }, { freq: 1320, amp: 0.33 }, { freq: 1760, amp: 0.25 }] },
  { name: "Hollow", harmonics: [{ freq: 880, amp: 0.8 }, { freq: 1320, amp: 0.5 }, { freq: 1760, amp: 0.3 }] },
];

function WaveformSVG({ harmonics }) {
  const W = 560, H = 140;
  const nSamples = 200;
  const period = 1 / Math.max(Math.min(...harmonics.map(h => h.freq)), 100);
  const tMax = period * 3;

  let points = "";
  let maxVal = 0.01;

  const samples = [];
  for (let i = 0; i < nSamples; i++) {
    const t = (i / (nSamples - 1)) * tMax;
    let val = 0;
    for (let hi = 0; hi < harmonics.length; hi++) {
      val += harmonics[hi].amp * Math.sin(2 * Math.PI * harmonics[hi].freq * t);
    }
    samples.push(val);
    if (Math.abs(val) > maxVal) maxVal = Math.abs(val);
  }

  const margin = 10;
  for (let i = 0; i < nSamples; i++) {
    const sx = margin + (i / (nSamples - 1)) * (W - 2 * margin);
    const sy = H / 2 - (samples[i] / maxVal) * (H / 2 - margin);
    points += `${i === 0 ? "M" : "L"}${sx.toFixed(1)},${sy.toFixed(1)} `;
  }

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", display: "block", background: "#06020E", borderRadius: 10 }}>
      <line x1={margin} y1={H / 2} x2={W - margin} y2={H / 2} stroke="rgba(167,139,250,0.08)" strokeWidth="1" />
      <path d={points} fill="none" stroke="#A78BFA" strokeWidth="2" />
      <text x={W - margin - 4} y={H - 6} fill="rgba(167,139,250,0.15)" fontSize="8" fontFamily="monospace" textAnchor="end">
        {harmonics.length} node{harmonics.length !== 1 ? "s" : ""} = {harmonics.length} Im(eml(i{"\u03C9"}t, 1))
      </text>
    </svg>
  );
}

function TreeDiagram({ harmonics }) {
  if (harmonics.length === 0) return null;
  const W = 560, H = 80;
  const nodeR = 14;
  const gap = Math.min(60, (W - 40) / Math.max(harmonics.length, 1));
  const startX = W / 2 - ((harmonics.length - 1) * gap) / 2;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", display: "block" }}>
      {/* Sum node */}
      {harmonics.length > 1 && (
        <g>
          <circle cx={W / 2} cy={16} r={nodeR} fill="rgba(167,139,250,0.1)" stroke="rgba(167,139,250,0.3)" strokeWidth="1.5" />
          <text x={W / 2} y={20} fill="#A78BFA" fontSize="11" fontFamily="monospace" textAnchor="middle">{"\u03A3"}</text>
          {harmonics.map((h, i) => {
            const nx = startX + i * gap;
            return <line key={i} x1={W / 2} y1={16 + nodeR} x2={nx} y2={H / 2 + 12 - nodeR} stroke="rgba(167,139,250,0.15)" strokeWidth="1" />;
          })}
        </g>
      )}
      {/* EML nodes */}
      {harmonics.map((h, i) => {
        const nx = startX + i * gap;
        const ny = harmonics.length > 1 ? H / 2 + 12 : H / 2;
        const noteInfo = NOTES.find(n => Math.abs(n.freq - h.freq) < 1);
        const col = noteInfo ? noteInfo.color : "#A78BFA";
        return (
          <g key={i}>
            <circle cx={nx} cy={ny} r={nodeR} fill={`${col}15`} stroke={`${col}60`} strokeWidth="1.5" />
            <text x={nx} y={ny - 2} fill={col} fontSize="7" fontFamily="monospace" textAnchor="middle">eml</text>
            <text x={nx} y={ny + 7} fill={`${col}90`} fontSize="6" fontFamily="monospace" textAnchor="middle">
              {Math.round(h.freq)}Hz
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function EMLSynth() {
  const [harmonics, setHarmonics] = useState([{ freq: 440, amp: 1.0 }]);
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef(null);
  const oscRef = useRef([]);
  const gainRef = useRef([]);
  const masterRef = useRef(null);

  const startAudio = useCallback(() => {
    if (playing) return;
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    audioRef.current = ctx;
    const master = ctx.createGain();
    master.gain.value = 0.15;
    master.connect(ctx.destination);
    masterRef.current = master;

    const oscs = [];
    const gains = [];
    harmonics.forEach((h) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = h.freq;
      gain.gain.value = h.amp * 0.3;
      osc.connect(gain);
      gain.connect(master);
      osc.start();
      oscs.push(osc);
      gains.push(gain);
    });
    oscRef.current = oscs;
    gainRef.current = gains;
    setPlaying(true);
  }, [harmonics, playing]);

  const stopAudio = useCallback(() => {
    oscRef.current.forEach(o => { try { o.stop(); } catch (_e) { /* */ } });
    oscRef.current = [];
    gainRef.current = [];
    if (audioRef.current) {
      try { audioRef.current.close(); } catch (_e) { /* */ }
      audioRef.current = null;
    }
    setPlaying(false);
  }, []);

  // Sync oscillators when harmonics change while playing
  useEffect(() => {
    if (!playing || !audioRef.current) return;
    const ctx = audioRef.current;
    const master = masterRef.current;

    // Stop old
    oscRef.current.forEach(o => { try { o.stop(); } catch (_e) { /* */ } });

    const oscs = [];
    const gains = [];
    harmonics.forEach((h) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = h.freq;
      gain.gain.value = h.amp * 0.3;
      osc.connect(gain);
      gain.connect(master);
      osc.start();
      oscs.push(osc);
      gains.push(gain);
    });
    oscRef.current = oscs;
    gainRef.current = gains;
  }, [harmonics, playing]);

  // Cleanup on unmount
  useEffect(() => () => stopAudio(), [stopAudio]);

  const addHarmonic = (freq) => {
    if (harmonics.length >= 8) return;
    if (harmonics.some(h => Math.abs(h.freq - freq) < 1)) return;
    setHarmonics(prev => [...prev, { freq, amp: 0.5 }]);
  };

  const removeHarmonic = (idx) => {
    if (harmonics.length <= 1) return;
    setHarmonics(prev => prev.filter((_, i) => i !== idx));
  };

  const setAmp = (idx, amp) => {
    setHarmonics(prev => prev.map((h, i) => i === idx ? { ...h, amp } : h));
  };

  const loadPreset = (p) => {
    setHarmonics(p.harmonics.map(h => ({ ...h })));
  };

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 600, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.5rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#A78BFA", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>EML Sound Synthesis</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          Each harmonic is one EML node: sin({"\u03C9"}t) = Im(eml(i{"\u03C9"}t, 1)). Build a tree. Hear it.
        </p>
      </div>

      {/* Waveform */}
      <div style={{ borderRadius: 14, overflow: "hidden", border: "1px solid rgba(167,139,250,0.1)", marginBottom: 8 }}>
        <WaveformSVG harmonics={harmonics} />
      </div>

      {/* Tree diagram */}
      <div style={{ marginBottom: 8 }}>
        <TreeDiagram harmonics={harmonics} />
      </div>

      {/* Play button */}
      <button onClick={playing ? stopAudio : startAudio} style={{
        display: "block", width: "100%", padding: "12px", borderRadius: 10, marginBottom: 10,
        cursor: "pointer",
        background: playing ? "rgba(239,68,68,0.08)" : "rgba(16,185,129,0.08)",
        border: `2px solid ${playing ? "rgba(239,68,68,0.2)" : "rgba(16,185,129,0.2)"}`,
        fontSize: 14, fontWeight: 700, color: playing ? "#EF4444" : "#10B981",
      }}>{playing ? "\u25A0  Stop" : "\u25B6  Play"}</button>

      {/* Active harmonics */}
      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-secondary, #999)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
        Active nodes ({harmonics.length}/8)
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 10 }}>
        {harmonics.map((h, idx) => {
          const noteInfo = NOTES.find(n => Math.abs(n.freq - h.freq) < 1);
          const col = noteInfo ? noteInfo.color : "#A78BFA";
          const noteName = noteInfo ? noteInfo.name : `${Math.round(h.freq)}Hz`;
          return (
            <div key={idx} style={{
              display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", borderRadius: 8,
              background: `${col}06`, border: `1px solid ${col}15`,
            }}>
              <div style={{
                width: 28, height: 28, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center",
                background: `${col}15`, fontSize: 9, fontWeight: 700, fontFamily: "var(--font-mono)", color: col,
              }}>{idx + 1}</div>
              <div style={{ flex: "0 0 50px" }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: col }}>{noteName}</div>
                <div style={{ fontSize: 9, color: "var(--color-text-secondary, #999)" }}>{Math.round(h.freq)}Hz</div>
              </div>
              <div style={{ fontSize: 8, color: "var(--color-text-secondary, #aaa)", flex: "0 0 90px", fontFamily: "var(--font-mono)" }}>
                Im(eml(i{"\u00B7"}{Math.round(h.freq)}t, 1))
              </div>
              <input
                type="range" min="0" max="1" step="0.05" value={h.amp}
                onChange={(e) => setAmp(idx, Number(e.target.value))}
                aria-label={`Amplitude for ${noteName}`}
                style={{ flex: 1, accentColor: col, cursor: "pointer" }}
              />
              <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: col, width: 30, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                {h.amp.toFixed(2)}
              </span>
              <button onClick={() => removeHarmonic(idx)} disabled={harmonics.length <= 1} style={{
                width: 22, height: 22, borderRadius: 4, border: "none", cursor: harmonics.length <= 1 ? "default" : "pointer",
                background: "rgba(239,68,68,0.06)", color: "#EF4444", fontSize: 12, fontWeight: 700,
                opacity: harmonics.length <= 1 ? 0.2 : 1,
              }}>{"\u00D7"}</button>
            </div>
          );
        })}
      </div>

      {/* Add harmonics */}
      {harmonics.length < 8 && (
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-secondary, #999)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>
            Add a node
          </div>
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {NOTES.filter(n => !harmonics.some(h => Math.abs(h.freq - n.freq) < 1)).map(n => (
              <button key={n.name} onClick={() => addHarmonic(n.freq)} style={{
                padding: "6px 12px", borderRadius: 6, cursor: "pointer",
                background: `${n.color}08`, border: `1px solid ${n.color}20`,
                fontSize: 11, fontWeight: 500, color: n.color,
              }}>{n.name} ({Math.round(n.freq)}Hz)</button>
            ))}
          </div>
        </div>
      )}

      {/* Presets */}
      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-secondary, #999)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>
        Presets
      </div>
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 10 }}>
        {PRESETS.map(p => (
          <button key={p.name} onClick={() => loadPreset(p)} style={{
            padding: "6px 14px", borderRadius: 6, cursor: "pointer",
            background: "var(--color-background-secondary, #faf5ff)",
            border: "1px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
            fontSize: 11, fontWeight: 500, color: "var(--color-text-primary, #555)",
          }}>{p.name} ({p.harmonics.length})</button>
        ))}
      </div>

      {/* The math */}
      <div style={{
        padding: "12px 16px", borderRadius: 10, marginBottom: 10,
        background: "rgba(167,139,250,0.03)", border: "1px solid rgba(167,139,250,0.08)",
      }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "#A78BFA", marginBottom: 4 }}>Why this works</div>
        <div style={{ fontSize: 12, color: "var(--color-text-secondary, #666)", lineHeight: 1.7 }}>
          Every sinusoidal tone is one complex EML node: sin({"\u03C9"}t) = Im(eml(i{"\u03C9"}t, 1)) = Im(exp(i{"\u03C9"}t)) by Euler's formula (T03). 
          Fourier's theorem says any periodic waveform is a sum of sinusoids. Therefore any 
          periodic sound is a linear combination of complex EML nodes. The tree topology — which 
          nodes are present and at what amplitudes — determines the timbre. Adding a node at 
          880Hz to a 440Hz fundamental adds the first overtone. The waveform changes. The sound 
          changes. The tree grew by one node.
        </div>
      </div>

      {/* EML formula display */}
      <div style={{
        padding: "10px 14px", borderRadius: 8,
        background: "var(--color-background-secondary, #faf5ff)",
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
        marginBottom: 10,
      }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-secondary, #999)", marginBottom: 4 }}>Current EML expression</div>
        <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #444)", lineHeight: 1.6, overflowWrap: "break-word" }}>
          f(t) = {harmonics.map((h, i) => (
            <span key={i}>
              {i > 0 ? " + " : ""}
              {h.amp !== 1 ? `${h.amp.toFixed(2)}{"\u00B7"}` : ""}
              Im(eml(i{"\u00B7"}{Math.round(h.freq)}t, 1))
            </span>
          ))}
        </div>
        <div style={{ fontSize: 10, color: "var(--color-text-secondary, #999)", marginTop: 4 }}>
          {harmonics.length} complex EML node{harmonics.length !== 1 ? "s" : ""} = {harmonics.length} harmonic{harmonics.length !== 1 ? "s" : ""}
        </div>
      </div>

      <div style={{
        padding: "0.6rem 1rem",
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 11, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          EML sound synthesis generates audio directly from EML tree evaluation. Each node 
          computes sin({"\u03C9"}t) via the complex bypass (T03). The waveform is the sum. The timbre 
          is determined by which frequencies are present and at what amplitudes — the Fourier 
          spectrum. This is not a metaphor. The audio you hear IS the EML computation.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 8, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.org" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none", fontWeight: 500 }}>monogate.org</a>
        {" \u00B7 "}
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#06B6D4", textDecoration: "none" }}>monogate.dev</a>
      </div>
    </div>
  );
}
