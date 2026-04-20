import { useState, useRef, useEffect } from "react";

const STRATA = [
  { id: 0, name: "Arithmetic", label: "EML-0", color: "#64748B", start: 0, end: 10, desc: "Discrete. Integer values. Constants." },
  { id: 1, name: "Exponential", label: "EML-1", color: "#06B6D4", start: 10, end: 20, desc: "exp(x), eˣ, xⁿ. Growth without oscillation." },
  { id: 2, name: "Logarithmic", label: "EML-2", color: "#8B5CF6", start: 20, end: 35, desc: "ln(x), √x, entropy. EML requires 4 nodes minimum." },
  { id: 3, name: "Oscillatory", label: "EML-3", color: "#EC4899", start: 35, end: 50, desc: "sin(x), cos(x), Fourier series. N=3 singularity." },
  { id: "wall", name: "The Wall", label: "EML-4 ∅", color: "#EF4444", start: 50, end: 55, desc: "Does not exist." },
  { id: "silence", name: "The Leap", label: "...", color: "#000000", start: 55, end: 58, desc: "" },
  { id: "inf", name: "The Depths", label: "EML-∞", color: "#FDE68A", start: 58, end: 62, desc: "Everything. Irreducible. Infinite." },
];

export default function MonogateSound() {
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [finished, setFinished] = useState(false);
  const acRef = useRef(null);
  const nodesRef = useRef([]);
  const frameRef = useRef(null);
  const startRef = useRef(0);
  const canvasRef = useRef(null);

  const currentStratum = STRATA.find(s => time >= s.start && time < s.end) || STRATA[STRATA.length - 1];
  const progress = Math.min(time / 62, 1);

  const stopAll = () => {
    nodesRef.current.forEach(n => { try { n.stop?.(); n.disconnect?.(); } catch {} });
    nodesRef.current = [];
  };

  const startExperience = () => {
    if (playing) return;
    setPlaying(true);
    setFinished(false);
    setTime(0);

    const ac = new (window.AudioContext || window.webkitAudioContext)();
    acRef.current = ac;
    const now = ac.currentTime;
    startRef.current = now;
    const nodes = [];

    const makeOsc = (type, freq, startT, endT, vol = 0.06) => {
      const o = ac.createOscillator(); o.type = type;
      if (typeof freq === "number") o.frequency.setValueAtTime(freq, now + startT);
      else freq(o.frequency, now + startT);
      const g = ac.createGain();
      g.gain.setValueAtTime(0, now + startT);
      g.gain.linearRampToValueAtTime(vol, now + startT + 0.3);
      g.gain.setValueAtTime(vol, now + endT - 0.3);
      g.gain.linearRampToValueAtTime(0, now + endT);
      o.connect(g); g.connect(ac.destination);
      o.start(now + startT); o.stop(now + endT + 0.1);
      nodes.push(o, g);
    };

    // ─── EML-0: Clicks (0-10s) ───
    for (let i = 0; i < 10; i++) {
      const click = ac.createOscillator(); click.type = "square";
      click.frequency.setValueAtTime(800, now + i);
      const cg = ac.createGain();
      cg.gain.setValueAtTime(0.08, now + i);
      cg.gain.exponentialRampToValueAtTime(0.001, now + i + 0.05);
      click.connect(cg); cg.connect(ac.destination);
      click.start(now + i); click.stop(now + i + 0.06);
      nodes.push(click, cg);
    }

    // ─── EML-1: Exponential rise (10-20s) ───
    makeOsc("sine", (f, t) => {
      f.setValueAtTime(55, t);
      f.exponentialRampToValueAtTime(440, t + 10);
    }, 10, 20, 0.07);
    // Doubling clicks accelerating
    for (let i = 0; i < 20; i++) {
      const t = 10 + (1 - Math.exp(-i * 0.3)) * 9;
      if (t < 20) {
        const cl = ac.createOscillator(); cl.type = "square";
        cl.frequency.setValueAtTime(600, now + t);
        const cg = ac.createGain();
        cg.gain.setValueAtTime(0.04, now + t);
        cg.gain.exponentialRampToValueAtTime(0.001, now + t + 0.03);
        cl.connect(cg); cg.connect(ac.destination);
        cl.start(now + t); cl.stop(now + t + 0.04);
        nodes.push(cl, cg);
      }
    }

    // ─── EML-2: Harmonic spread (20-35s) ───
    [110, 165, 220, 277, 330].forEach((freq, i) => {
      makeOsc(i % 2 === 0 ? "sine" : "triangle", freq, 20 + i * 0.5, 35, 0.04);
    });
    // Reverb-like delayed copies
    [112, 167, 223].forEach((freq, i) => {
      makeOsc("sine", freq, 22 + i, 34, 0.02);
    });

    // ─── EML-3: Oscillation + interference (35-50s) ───
    makeOsc("sine", 220, 35, 50, 0.06);
    makeOsc("sine", 223, 35, 50, 0.05); // Beat frequency 3Hz
    makeOsc("triangle", 330, 36, 50, 0.04);
    makeOsc("sine", 333, 36, 50, 0.03); // Another beat
    makeOsc("sine", 440, 38, 50, 0.03);
    // Heartbeat pulse
    for (let i = 0; i < 12; i++) {
      const t = 40 + i * 0.8;
      if (t < 50) {
        const hb = ac.createOscillator(); hb.type = "sine";
        hb.frequency.setValueAtTime(55, now + t);
        const hg = ac.createGain();
        hg.gain.setValueAtTime(0.08, now + t);
        hg.gain.exponentialRampToValueAtTime(0.001, now + t + 0.3);
        hb.connect(hg); hg.connect(ac.destination);
        hb.start(now + t); hb.stop(now + t + 0.35);
        nodes.push(hb, hg);
      }
    }

    // ─── THE WALL: Dissonant chord (50-55s) ───
    [233, 311, 415, 554].forEach(freq => {
      makeOsc("sawtooth", freq, 50, 55, 0.03);
    });
    // Unresolvable — tritone
    makeOsc("square", 293.66, 50, 55, 0.02); // D4
    makeOsc("square", 415.30, 50, 55, 0.02); // Ab4 — tritone

    // ─── SILENCE (55-58s) — nothing plays ───

    // ─── EML-∞: Everything (58-62s) ───
    [55, 82.5, 110, 146.83, 165, 220, 261.63, 293.66, 330, 392, 440, 523.25].forEach((freq, i) => {
      makeOsc(i % 3 === 0 ? "sine" : i % 3 === 1 ? "triangle" : "square", freq, 58 + i * 0.05, 61.5, 0.025);
    });
    // Final fade to single tone — the click returns
    const finalClick = ac.createOscillator(); finalClick.type = "sine";
    finalClick.frequency.setValueAtTime(440, now + 61);
    finalClick.frequency.exponentialRampToValueAtTime(800, now + 61.5);
    const fg = ac.createGain();
    fg.gain.setValueAtTime(0.06, now + 61);
    fg.gain.exponentialRampToValueAtTime(0.001, now + 62);
    finalClick.connect(fg); fg.connect(ac.destination);
    finalClick.start(now + 61); finalClick.stop(now + 62.5);
    nodes.push(finalClick, fg);

    nodesRef.current = nodes;

    // Timer
    const tick = () => {
      const elapsed = ac.currentTime - startRef.current;
      setTime(elapsed);
      if (elapsed >= 62) {
        setPlaying(false);
        setFinished(true);
        return;
      }
      frameRef.current = requestAnimationFrame(tick);
    };
    tick();
  };

  // Canvas visualization
  useEffect(() => {
    const c = canvasRef.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height;
    let animFrame;
    const draw = () => {
      ctx.fillStyle = "rgba(6,2,14,0.15)";
      ctx.fillRect(0, 0, w, h);

      const cx = w / 2, cy = h / 2;
      const t = performance.now() / 1000;

      if (playing || finished) {
        const stratum = currentStratum;
        const r = parseInt((stratum.color || "#888").slice(1, 3), 16) || 100;
        const g = parseInt((stratum.color || "#888").slice(3, 5), 16) || 100;
        const b = parseInt((stratum.color || "#888").slice(5, 7), 16) || 100;

        if (stratum.id === 0) {
          // Discrete dots
          for (let i = 0; i < 8; i++) {
            const x = cx - 120 + i * 35;
            ctx.beginPath(); ctx.arc(x, cy, 3, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${r},${g},${b},${i < (time % 10) ? 0.6 : 0.1})`; ctx.fill();
          }
        } else if (stratum.id === 1) {
          // Exponential curve
          ctx.beginPath();
          for (let x = 0; x < w; x += 2) {
            const frac = x / w;
            const y = cy + 60 - Math.exp(frac * 3) * 2 * ((time - 10) / 10);
            if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          }
          ctx.strokeStyle = `rgba(${r},${g},${b},0.4)`; ctx.lineWidth = 2; ctx.stroke();
        } else if (stratum.id === 2) {
          // Logarithmic spirals
          for (let sp = 0; sp < 3; sp++) {
            ctx.beginPath();
            for (let i = 0; i < 200; i++) {
              const frac = i / 200;
              const angle = frac * Math.PI * 6 + sp * (Math.PI * 2 / 3) + t * 0.2;
              const radius = 5 + Math.log(1 + frac * 15) * 25;
              if (i === 0) ctx.moveTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
              else ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
            }
            ctx.strokeStyle = `rgba(${r},${g},${b},0.15)`; ctx.lineWidth = 1.5; ctx.stroke();
          }
        } else if (stratum.id === 3) {
          // Interference waves
          for (let wave = 0; wave < 5; wave++) {
            ctx.beginPath();
            for (let x = 0; x < w; x += 2) {
              const frac = x / w;
              const y = cy + Math.sin(frac * Math.PI * (4 + wave) + t * (2 + wave * 0.3)) * (15 + wave * 6)
                + Math.sin(frac * Math.PI * (4 + wave) * 1.03 + t * (2.1 + wave * 0.3)) * (10 + wave * 4);
              if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.strokeStyle = `rgba(${r},${g},${b},${0.12 + wave * 0.04})`; ctx.lineWidth = 1.5; ctx.stroke();
          }
        } else if (stratum.id === "wall") {
          // Jagged red static
          for (let i = 0; i < 60; i++) {
            const x = Math.random() * w, y = Math.random() * h;
            ctx.beginPath(); ctx.arc(x, y, 1 + Math.random() * 2, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(239,68,68,${0.1 + Math.random() * 0.15})`; ctx.fill();
          }
          ctx.fillStyle = "rgba(239,68,68,0.08)"; ctx.font = "bold 24px monospace"; ctx.textAlign = "center";
          ctx.fillText("∅", cx, cy + 8);
        } else if (stratum.id === "silence") {
          // Nothing. Pure black.
        } else if (stratum.id === "inf") {
          // Everything — all previous visuals at once, faintly
          // Dots
          for (let i = 0; i < 8; i++) { ctx.beginPath(); ctx.arc(cx - 120 + i * 35, cy - 50, 2, 0, Math.PI * 2); ctx.fillStyle = "rgba(253,230,138,0.06)"; ctx.fill(); }
          // Curve
          ctx.beginPath(); for (let x = 0; x < w; x += 4) { ctx.lineTo(x, cy + 30 - Math.exp((x / w) * 2) * 3); } ctx.strokeStyle = "rgba(253,230,138,0.06)"; ctx.lineWidth = 1; ctx.stroke();
          // Spiral
          ctx.beginPath(); for (let i = 0; i < 100; i++) { const a = (i / 100) * Math.PI * 4 + t * 0.3; const rad = 5 + Math.log(1 + i * 0.15) * 20; ctx.lineTo(cx + Math.cos(a) * rad, cy + Math.sin(a) * rad); } ctx.strokeStyle = "rgba(253,230,138,0.06)"; ctx.stroke();
          // Waves
          for (let w2 = 0; w2 < 3; w2++) { ctx.beginPath(); for (let x = 0; x < w; x += 3) { ctx.lineTo(x, cy + Math.sin((x / w) * Math.PI * 6 + t * 2 + w2) * 20); } ctx.strokeStyle = "rgba(253,230,138,0.08)"; ctx.stroke(); }
          // Glow
          const grd = ctx.createRadialGradient(cx, cy, 0, cx, cy, 100);
          grd.addColorStop(0, `rgba(253,230,138,${0.06 + Math.sin(t * 2) * 0.03})`);
          grd.addColorStop(1, "rgba(0,0,0,0)");
          ctx.fillStyle = grd; ctx.beginPath(); ctx.arc(cx, cy, 100, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = `rgba(253,230,138,${0.12 + Math.sin(t * 1.5) * 0.05})`; ctx.font = "bold 32px serif"; ctx.textAlign = "center";
          ctx.fillText("∞", cx, cy + 12);
        }
      } else {
        // Idle state
        ctx.fillStyle = "rgba(167,139,250,0.04)"; ctx.font = "12px monospace"; ctx.textAlign = "center";
        ctx.fillText("eml(x, y) = exp(x) − ln(y)", cx, cy);
      }

      animFrame = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(animFrame);
  }, [playing, time, currentStratum, finished]);

  useEffect(() => { return () => { cancelAnimationFrame(frameRef.current); stopAll(); }; }, []);

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 640, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.5rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#A78BFA", fontWeight: 500, marginBottom: 3 }}>monogate.org</div>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>The Sound of Depth</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          60 seconds. Five strata. One equation. Close your eyes and listen.
        </p>
      </div>

      {/* Canvas */}
      <div style={{ borderRadius: 14, overflow: "hidden", border: `1px solid ${currentStratum?.color || "#A78BFA"}20`, marginBottom: 12, position: "relative" }}>
        <canvas ref={canvasRef} width={640} height={280} style={{ width: "100%", height: "100%", display: "block", borderRadius: 12 }} />
        {/* Stratum label */}
        {playing && (
          <div style={{ position: "absolute", top: 12, left: 16, animation: "fadeIn 0.3s ease" }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: currentStratum.color }}>{currentStratum.label}</div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>{currentStratum.name}</div>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", fontStyle: "italic", marginTop: 2 }}>{currentStratum.desc}</div>
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div style={{ height: 6, borderRadius: 3, background: "var(--color-background-secondary, #1a1a2e)", overflow: "hidden", marginBottom: 12, display: "flex" }}>
        {STRATA.map(s => (
          <div key={s.id} style={{
            flex: (s.end - s.start) / 62,
            background: time >= s.start ? s.color : "transparent",
            opacity: time >= s.start && time < s.end ? 1 : time >= s.end ? 0.4 : 0.1,
            transition: "opacity 0.3s",
          }} />
        ))}
      </div>

      {/* Stratum indicators */}
      <div style={{ display: "flex", gap: 3, marginBottom: 16 }}>
        {STRATA.filter(s => s.id !== "silence").map(s => (
          <div key={s.id} style={{
            flex: 1, padding: "4px 2px", borderRadius: 6, textAlign: "center",
            background: (playing || finished) && time >= s.start ? `${s.color}12` : "var(--color-background-secondary, #f3f4f6)",
            border: (playing || finished) && time >= s.start && time < s.end ? `1.5px solid ${s.color}40` : "1px solid transparent",
            transition: "all 0.3s",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: time >= s.start ? s.color : "var(--color-text-secondary, #ccc)", fontFamily: "var(--font-mono)" }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Play button */}
      {!playing && (
        <button onClick={startExperience} style={{
          display: "block", width: "100%", padding: "16px 24px", borderRadius: 12,
          cursor: "pointer", textAlign: "center",
          background: finished ? "rgba(253,230,138,0.06)" : "rgba(167,139,250,0.06)",
          border: `2px solid ${finished ? "rgba(253,230,138,0.2)" : "rgba(167,139,250,0.2)"}`,
        }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: finished ? "#FDE68A" : "#A78BFA" }}>
            {finished ? "Experience again" : "Begin"}
          </div>
          <div style={{ fontSize: 11, color: "var(--color-text-secondary, #888)", marginTop: 2 }}>
            {finished ? "The hierarchy returns to its starting point. One equation." : "60 seconds. Use headphones."}
          </div>
        </button>
      )}

      {/* Finished message */}
      {finished && (
        <div style={{
          marginTop: 12, padding: "16px 20px", borderRadius: 12,
          background: "rgba(253,230,138,0.04)", border: "1px solid rgba(253,230,138,0.1)",
          textAlign: "center", animation: "fadeIn 0.8s ease",
        }}>
          <div style={{ fontSize: 14, color: "var(--color-text-secondary, #888)", lineHeight: 1.7 }}>
            You just heard the structure of mathematics. Counting became growth. Growth became measurement.
            Measurement became oscillation. Oscillation hit the wall. Silence. Then everything at once.
            Then a single tone — the beginning again.
          </div>
          <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "#A78BFA", marginTop: 10 }}>
            eml(x, y) = exp(x) − ln(y)
          </div>
          <div style={{ fontSize: 11, color: "#FDE68A", marginTop: 6, fontStyle: "italic" }}>
            One equation. Five strata. The structure of everything.
          </div>
        </div>
      )}

      <div style={{ textAlign: "center", marginTop: 12, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.org" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none", fontWeight: 500 }}>monogate.org</a>
        {" · "}
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#06B6D4", textDecoration: "none" }}>monogate.dev</a>
      </div>

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }`}</style>
    </div>
  );
}
