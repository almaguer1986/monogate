import { useState, useRef, useEffect } from "react";

const eml = (x, y) => {
  if (y <= 0) return Math.exp(Math.min(x, 20));
  return Math.exp(Math.min(x, 20)) - Math.log(y);
};

// ═══════════════════════════════════════════════════════════════════
// CREATIONS — what can be built and in what order
// ═══════════════════════════════════════════════════════════════════
const CREATIONS = [
  // Age 0: The First Light
  { id: "e", name: "e", formula: "eml(1, 1)", recipe: [1, 1], age: 0, depth: 1,
    desc: "Euler's number. The first thing that exists.", value: Math.E,
    physics: "The first constant. The seed of all EML composition.", color: "#06B6D4" },
  // Age 1: Growth
  { id: "e2", name: "e²", formula: "eml(2, 1)", recipe: [2, 1], age: 1, depth: 1,
    desc: "Growth squared. Things can compound now.", value: Math.E ** 2,
    physics: "Compound growth. EML-1 functions now have a second representative.", color: "#06B6D4" },
  { id: "exp", name: "exp(x)", formula: "eml(x, 1)", recipe: ["x", 1], age: 1, depth: 1,
    desc: "The exponential function. Growth itself.", value: null,
    physics: "The exponential function. One EML node. EML-1 stratum is open.", color: "#06B6D4" },
  // Age 2: Measurement
  { id: "e_inv", name: "1/e", formula: "eml(-1, 1)", recipe: [-1, 1], age: 2, depth: 1,
    desc: "The inverse of growth. Decay enters.", value: 1 / Math.E,
    physics: "Decay. The negative exponential. DEML gate in 1 node.", color: "#8B5CF6" },
  { id: "ln", name: "ln(x)", formula: "eml(1, eml(eml(1,x), 1))", recipe: "special", age: 2, depth: 2,
    desc: "The logarithm. Three levels of EML. Measurement is born.", value: null,
    physics: "The logarithm. 4-node minimum. EML-2 stratum is open.", color: "#8B5CF6" },
  { id: "entropy", name: "entropy", formula: "-Σ p·ln(p)", recipe: "derived", age: 2, depth: 2,
    desc: "Shannon entropy. The universe now has thermodynamics.", value: null,
    physics: "Shannon entropy −Σp·ln(p). Logarithmic depth confirmed.", color: "#8B5CF6" },
  // Age 3: Structure
  { id: "add", name: "a + b", formula: "eml(a, eml(1, eml(b, 1)))", recipe: "special", age: 3, depth: 1,
    desc: "Addition. 11 EML nodes. Things can combine.", value: null,
    physics: "Addition. 11 EML nodes. Arithmetic is constructible.", color: "#10B981" },
  { id: "mul", name: "a × b", formula: "exp(ln(a) + ln(b))", recipe: "derived", age: 3, depth: 2,
    desc: "Multiplication. Built from exp and ln. Scaling enters.", value: null,
    physics: "Multiplication. Built from exp(ln(a)+ln(b)). EML-2.", color: "#10B981" },
  { id: "pi_approx", name: "π", formula: "4·Σ(-1)^k/(2k+1)", recipe: "derived", age: 3, depth: 2,
    desc: "Pi emerges from the arithmetic. Circles are possible.", value: Math.PI,
    physics: "π from the Leibniz series. Circles and rotation constructible.", color: "#10B981" },
  // Age 4: Oscillation
  { id: "sin", name: "sin(x)", formula: "Im(eml(ix, 1))", recipe: "complex", age: 4, depth: 3,
    desc: "108 real EML nodes. Or 1 complex node. Oscillation.", value: null,
    physics: "sin(x) arrives. N=3 singularity: MSE drops 1.4M× at depth 3. EML-3 opens.", color: "#EC4899" },
  { id: "fourier", name: "Fourier", formula: "∫f·e^{-2πixξ}dx", recipe: "derived", age: 4, depth: 3,
    desc: "Decompose anything into frequencies. Analysis supreme.", value: null,
    physics: "Fourier transform. EML-3 functions decompose into EML-3 frequency components.", color: "#EC4899" },
  { id: "schrodinger", name: "ψ(x,t)", formula: "iℏ∂ψ/∂t = Ĥψ", recipe: "derived", age: 4, depth: 3,
    desc: "Quantum mechanics. Probability waves. Superposition.", value: null,
    physics: "Schrödinger equation. ψ = Ae^{ikx} is an EML-3 oscillatory function.", color: "#EC4899" },
  // Age 5: The Depths
  { id: "categorify", name: "∞", formula: "categorification", recipe: "transcend", age: 5, depth: "∞",
    desc: "Enrich the finite into the infinite. The universe gains depth beyond measure.", value: null,
    physics: "EML-∞: non-constructible functions. |sin(x)|, |x|, sawtooth. The infinite-node limit.", color: "#FDE68A" },
];

const AGES = [
  { id: 0, name: "The First Light", stratum: "EML-0 → 1", color: "#64748B", bg: [8, 6, 14] },
  { id: 1, name: "The Growth Age", stratum: "EML-1", color: "#06B6D4", bg: [8, 14, 24] },
  { id: 2, name: "The Measurement Age", stratum: "EML-2", color: "#8B5CF6", bg: [14, 8, 28] },
  { id: 3, name: "The Age of Structure", stratum: "EML-2 → 3", color: "#10B981", bg: [8, 18, 14] },
  { id: 4, name: "The Oscillation Age", stratum: "EML-3", color: "#EC4899", bg: [20, 8, 18] },
  { id: 5, name: "The Infinite Age", stratum: "EML-∞", color: "#FDE68A", bg: [22, 18, 6] },
];

// ═══════════════════════════════════════════════════════════════════
// UNIVERSE VISUALIZATION
// ═══════════════════════════════════════════════════════════════════
function UniverseCanvas({ created, currentAge, revelation }) {
  const ref = useRef(null), t = useRef(0), f = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height, cx = w / 2, cy = h / 2;
    t.current = 0;
    const age = AGES[Math.min(currentAge, 5)];
    const [bgR, bgG, bgB] = age.bg;

    const has = (id) => created.includes(id);

    const go = () => {
      t.current += 0.016; const time = t.current;

      // Fade to age background
      ctx.fillStyle = `rgba(${bgR},${bgG},${bgB},0.08)`;
      ctx.fillRect(0, 0, w, h);

      // ─── Age 0: Nothing, then a single point ───
      if (created.length === 0) {
        // Pure void with faint equation
        ctx.fillStyle = "rgba(167,139,250,0.02)";
        ctx.font = "11px monospace"; ctx.textAlign = "center";
        ctx.fillText("eml(x, y) = exp(x) − ln(y)", cx, cy);
        f.current = requestAnimationFrame(go); return;
      }

      // Stars (accumulate with creations)
      if (has("e")) {
        const starCount = Math.min(created.length * 15, 120);
        for (let i = 0; i < starCount; i++) {
          const sx = (Math.sin(i * 73.7 + 0.1) * 0.5 + 0.5) * w;
          const sy = (Math.cos(i * 31.3 + 0.2) * 0.5 + 0.5) * h;
          const sz = 0.3 + Math.sin(time * 0.5 + i * 2) * 0.3;
          ctx.beginPath(); ctx.arc(sx, sy, sz, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255,255,255,${0.1 + Math.sin(time + i) * 0.08})`;
          ctx.fill();
        }
      }

      // The First Creation — point of light
      if (has("e") && !has("e2")) {
        const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, 20 + Math.sin(time) * 5);
        glow.addColorStop(0, "rgba(6,182,212,0.4)");
        glow.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(cx, cy, 25, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(cx, cy, 3 + Math.sin(time * 2) * 1, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(6,182,212,0.8)"; ctx.fill();
      }

      // Growth — exponential curves radiating
      if (has("exp")) {
        for (let curve = 0; curve < 6; curve++) {
          const angle = (curve / 6) * Math.PI * 2 + time * 0.05;
          ctx.beginPath();
          for (let i = 0; i < 60; i++) {
            const frac = i / 60;
            const r = frac * Math.min(w, h) * 0.35;
            const wobble = Math.exp(frac * 1.5 - 1) * 3 * Math.sin(time * 0.3 + curve);
            const px = cx + Math.cos(angle + wobble * 0.02) * r;
            const py = cy + Math.sin(angle + wobble * 0.02) * r;
            if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
          }
          ctx.strokeStyle = `rgba(6,182,212,${0.06 + curve * 0.01})`; ctx.lineWidth = 1; ctx.stroke();
        }
      }

      // Measurement — logarithmic spirals
      if (has("ln")) {
        for (let sp = 0; sp < 3; sp++) {
          ctx.beginPath();
          for (let i = 0; i < 150; i++) {
            const frac = i / 150;
            const angle = frac * Math.PI * 5 + sp * (Math.PI * 2 / 3) + time * 0.1;
            const r = 5 + Math.log(1 + frac * 12) * 22;
            if (i === 0) ctx.moveTo(cx + Math.cos(angle) * r, cy + Math.sin(angle) * r);
            else ctx.lineTo(cx + Math.cos(angle) * r, cy + Math.sin(angle) * r);
          }
          ctx.strokeStyle = `rgba(139,92,246,${0.08 + sp * 0.02})`; ctx.lineWidth = 1; ctx.stroke();
        }
      }

      // Entropy — opacity/color variation
      if (has("entropy")) {
        for (let i = 0; i < 30; i++) {
          const px = (Math.sin(i * 41.7) * 0.4 + 0.5) * w;
          const py = (Math.cos(i * 23.1) * 0.4 + 0.5) * h;
          const hue = (time * 10 + i * 30) % 360;
          ctx.beginPath(); ctx.arc(px, py, 2 + Math.sin(time + i * 3) * 1, 0, Math.PI * 2);
          ctx.fillStyle = `hsla(${hue},60%,50%,${0.04 + Math.sin(time * 0.5 + i) * 0.02})`;
          ctx.fill();
        }
      }

      // Pi — circles and orbits
      if (has("pi_approx")) {
        for (let ring = 0; ring < 4; ring++) {
          const r = 30 + ring * 28;
          ctx.beginPath();
          ctx.arc(cx, cy, r + Math.sin(time * 0.3 + ring) * 2, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(16,185,129,${0.05 + ring * 0.015})`; ctx.lineWidth = 0.8; ctx.stroke();
          // Orbiting body
          const angle = time * (0.3 - ring * 0.05) + ring * 1.5;
          ctx.beginPath(); ctx.arc(cx + Math.cos(angle) * r, cy + Math.sin(angle) * r, 2, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(16,185,129,0.3)`; ctx.fill();
        }
      }

      // Oscillation — waves rippling across everything
      if (has("sin")) {
        for (let wave = 0; wave < 5; wave++) {
          ctx.beginPath();
          for (let i = 0; i < 150; i++) {
            const frac = i / 150;
            const x = frac * w;
            const freq = 3 + wave;
            const y = cy + Math.sin(frac * Math.PI * freq + time * (0.8 + wave * 0.2)) * (20 + wave * 8)
              + Math.sin(frac * Math.PI * freq * 1.6 + time * 1.1) * 6;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          }
          ctx.strokeStyle = `rgba(236,72,153,${0.06 + wave * 0.015})`; ctx.lineWidth = 1; ctx.stroke();
        }
      }

      // Fourier — spectrum bars
      if (has("fourier")) {
        for (let i = 0; i < 20; i++) {
          const x = w * 0.1 + (i / 20) * w * 0.8;
          const barH = 8 + Math.abs(Math.sin(i * 1.3 + time * 0.5)) * 15 * (1 + Math.sin(time * 0.3 + i * 0.7) * 0.5);
          ctx.fillStyle = `rgba(236,72,153,${0.04 + Math.sin(time + i) * 0.02})`;
          ctx.fillRect(x - 2, cy + 80 - barH / 2, 4, barH);
        }
      }

      // Quantum — probability cloud
      if (has("schrodinger")) {
        for (let i = 0; i < 40; i++) {
          const angle = (i / 40) * Math.PI * 2 + time * 0.2;
          const r = 50 + Math.sin(time * 0.7 + i * 0.8) * 25;
          const px = cx + Math.cos(angle) * r + Math.sin(i * 7 + time) * 10;
          const py = cy + Math.sin(angle) * r + Math.cos(i * 5 + time) * 10;
          const sz = 1 + Math.random() * 1.5;
          ctx.beginPath(); ctx.arc(px, py, sz, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(236,72,153,${0.06 + Math.random() * 0.04})`; ctx.fill();
        }
      }

      // Infinity — Lorenz + fractals
      if (has("categorify")) {
        const sigma = 10, rho = 28, beta = 8 / 3;
        let lx = Math.sin(time * 0.1) * 2, ly = Math.cos(time * 0.1) * 2, lz = 1;
        ctx.beginPath();
        for (let i = 0; i < 300; i++) {
          const dt = 0.006;
          lx += sigma * (ly - lx) * dt; ly += (lx * (rho - lz) - ly) * dt; lz += (lx * ly - beta * lz) * dt;
          const px = cx + lx * 4, py = cy - lz * 3 + 40;
          if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.strokeStyle = "rgba(253,230,138,0.1)"; ctx.lineWidth = 0.8; ctx.stroke();
        // Distant EML-∞ objects — non-constructible
        ["|sin(x)|", "|x|", "sawtooth"].forEach((label, i) => {
          const a = (i / 3) * Math.PI * 2 + time * 0.02;
          const r = Math.min(w, h) * 0.42;
          ctx.fillStyle = "rgba(253,230,138,0.03)";
          ctx.font = "9px monospace"; ctx.textAlign = "center";
          ctx.fillText(label, cx + Math.cos(a) * r, cy + Math.sin(a) * r);
        });
      }

      // Center label — current value
      if (created.length > 0 && !revelation) {
        const latest = CREATIONS.find(c => c.id === created[created.length - 1]);
        if (latest && latest.value !== null) {
          ctx.fillStyle = `rgba(255,255,255,0.04)`;
          ctx.font = "bold 32px monospace"; ctx.textAlign = "center";
          ctx.fillText(latest.value.toFixed(4), cx, cy + 12);
        }
      }

      // REVELATION HEARTBEAT — all layers pulse in sync
      if (revelation) {
        const beat = Math.sin(time * 1.5) * 0.5 + 0.5; // 0-1 pulse
        const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.min(w, h) * 0.5);
        glow.addColorStop(0, `rgba(253,230,138,${beat * 0.06})`);
        glow.addColorStop(0.5, `rgba(139,92,246,${beat * 0.03})`);
        glow.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = glow; ctx.fillRect(0, 0, w, h);
        // The equation at center
        ctx.fillStyle = `rgba(196,181,253,${0.06 + beat * 0.04})`;
        ctx.font = "bold 16px monospace"; ctx.textAlign = "center";
        ctx.fillText("eml(x, y) = exp(x) − ln(y)", cx, cy);
        ctx.fillStyle = `rgba(253,230,138,${0.04 + beat * 0.03})`;
        ctx.font = "11px monospace";
        ctx.fillText("one equation · one universe", cx, cy + 20);
      }

      f.current = requestAnimationFrame(go);
    };
    ctx.fillStyle = `rgb(${bgR},${bgG},${bgB})`; ctx.fillRect(0, 0, w, h);
    go(); return () => cancelAnimationFrame(f.current);
  }, [created, currentAge, revelation]);

  return <canvas ref={ref} width={680} height={440} style={{ width: "100%", height: "100%", display: "block", borderRadius: 12 }} />;
}

// ═══════════════════════════════════════════════════════════════════
// MAIN GAME
// ═══════════════════════════════════════════════════════════════════
export default function Genesis() {
  const [created, setCreated] = useState([]);
  const [currentAge, setCurrentAge] = useState(0);
  const [selectedCreation, setSelectedCreation] = useState(null);
  const [showRevelation, setShowRevelation] = useState(false);
  const [pulse, setPulse] = useState(0);

  useEffect(() => { let fr; const tick = () => { setPulse(p => p + 0.025); fr = requestAnimationFrame(tick); }; tick(); return () => cancelAnimationFrame(fr); }, []);

  // Available creations = those in current age that aren't created yet
  const available = CREATIONS.filter(c => c.age <= currentAge && !created.includes(c.id));
  const ageCreations = CREATIONS.filter(c => c.age === currentAge);
  const ageComplete = ageCreations.every(c => created.includes(c.id));

  // Auto-advance age when all creations in current age are done
  useEffect(() => {
    if (ageComplete && currentAge < 5) {
      const timer = setTimeout(() => setCurrentAge(a => a + 1), 800);
      return () => clearTimeout(timer);
    }
    if (currentAge === 5 && created.includes("categorify")) {
      const timer = setTimeout(() => setShowRevelation(true), 2000);
      return () => clearTimeout(timer);
    }
  }, [ageComplete, currentAge, created]);

  const create = (id) => {
    if (created.includes(id)) return;
    setCreated(prev => [...prev, id]);
    setSelectedCreation(CREATIONS.find(c => c.id === id));
  };

  const age = AGES[Math.min(currentAge, 5)];
  const totalCreations = CREATIONS.length;
  const progress = created.length / totalCreations;

  // Depth stats
  const depthCounts = { 0: 0, 1: 0, 2: 0, 3: 0, "∞": 0 };
  created.forEach(id => {
    const c = CREATIONS.find(cr => cr.id === id);
    if (c) depthCounts[c.depth] = (depthCounts[c.depth] || 0) + 1;
  });

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 740, margin: "0 auto", padding: "0 0 2rem" }}>
      {/* Header */}
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.4rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: age.color, fontWeight: 500, marginBottom: 3, transition: "color 0.8s" }}>monogate.dev</div>
        <h1 style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>Genesis</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          Build the elementary function library from one equation. Each creation unlocks a new EML depth level.
        </p>
      </div>

      {/* Age indicator */}
      <div className="genesis-ages" style={{
        display: "flex", gap: 3, margin: "8px 0 10px",
      }}>
        {AGES.map((a, i) => {
          const completed = i < currentAge;
          const active = i === currentAge;
          const future = i > currentAge;
          return (
          <div key={a.id} style={{
            flex: 1, padding: "6px 4px", borderRadius: 6, textAlign: "center",
            background: active ? `${a.color}15` : completed ? `${a.color}10` : "var(--color-background-secondary, #f3f4f6)",
            border: active ? `1.5px solid ${a.color}40` : completed ? `1px solid ${a.color}20` : "1px solid transparent",
            boxShadow: completed ? `0 0 8px ${a.color}15` : "none",
            transition: "all 0.5s",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: completed || active ? a.color : "var(--color-text-secondary, #ccc)",
              fontFamily: "var(--font-mono)", transition: "color 0.5s" }}>{completed ? "✓ " : ""}{a.name}</div>
            <div style={{ fontSize: 8, color: completed ? `${a.color}80` : "var(--color-text-secondary, #aaa)", marginTop: 1 }}>{a.stratum}</div>
          </div>
          );
        })}
      </div>

      <div className="genesis-grid" style={{ display: "grid", gridTemplateColumns: "1fr 210px", gap: 10 }}>
        {/* UNIVERSE */}
        <div>
          <div style={{ borderRadius: 14, overflow: "hidden", border: `1px solid ${age.color}20`, marginBottom: 10, position: "relative", transition: "border-color 0.8s", aspectRatio: "680/440" }}>
            <UniverseCanvas created={created} currentAge={currentAge} revelation={showRevelation} />

            {/* Physics unlock message */}
            {selectedCreation && (
              <div style={{
                position: "absolute", bottom: 12, left: 12, right: 12,
                background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)",
                borderRadius: 8, padding: "10px 14px",
                animation: "fadeIn 0.5s ease",
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: selectedCreation.color }}>{selectedCreation.name}</div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.7)", marginTop: 2, fontStyle: "italic" }}>{selectedCreation.physics}</div>
              </div>
            )}

            {/* Void state */}
            {created.length === 0 && (
              <div style={{
                position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
                flexDirection: "column", gap: 12,
              }}>
                <div style={{ fontSize: 14, color: "rgba(167,139,250,0.3)", textAlign: "center", lineHeight: 1.6 }}>
                  The void. One equation. One constant.
                  <br />Create something.
                </div>
              </div>
            )}
          </div>

          {/* CREATION BUTTONS — things you can create right now */}
          <div style={{ fontSize: 10, fontWeight: 600, color: age.color, textTransform: "uppercase", letterSpacing: 1, marginBottom: 6, transition: "color 0.5s" }}>
            {currentAge < 5 ? `${age.name} — what will you create?` : showRevelation ? "Your universe is complete" : "The final act"}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {available.filter(c => c.age === currentAge).map(c => (
              <button key={c.id} onClick={() => create(c.id)} style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "12px 14px", borderRadius: 10, cursor: "pointer",
                background: "var(--color-background-secondary, #f8f5ff)",
                border: `1.5px solid ${c.color}20`,
                textAlign: "left", transition: "all 0.2s",
              }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: c.color }}>{c.name}</div>
                  <div style={{ fontSize: 11, color: "var(--color-text-secondary, #888)", marginTop: 2 }}>{c.desc}</div>
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #aaa)", marginTop: 3 }}>{c.formula}</div>
                </div>
                <div style={{ fontSize: 20, color: c.color, opacity: 0.4 + Math.sin(pulse * 3) * 0.2 }}>+</div>
              </button>
            ))}

            {/* Age transition message */}
            {ageComplete && currentAge < 5 && (
              <div style={{
                textAlign: "center", padding: "10px", borderRadius: 8,
                background: `${age.color}08`, border: `1px solid ${age.color}15`,
                fontSize: 12, color: age.color, fontWeight: 500,
                animation: "fadeIn 0.5s ease",
              }}>
                {age.name} complete. The next age dawns...
              </div>
            )}

            {/* Nothing more to create in this age but age hasn't advanced yet */}
            {available.filter(c => c.age === currentAge).length === 0 && !ageComplete && currentAge < 5 && (
              <div style={{ fontSize: 12, color: "var(--color-text-secondary, #aaa)", fontStyle: "italic", textAlign: "center", padding: 10 }}>
                Complete earlier creations to unlock more...
              </div>
            )}
          </div>

          {/* THE REVELATION */}
          {showRevelation && (
            <div style={{
              marginTop: 14, padding: "20px 24px", borderRadius: 14,
              background: "rgba(253,230,138,0.04)", border: "1px solid rgba(253,230,138,0.15)",
              animation: "fadeIn 1s ease",
            }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: "#FDE68A", textAlign: "center", marginBottom: 10 }}>
                Your universe is one equation.
              </div>
              <div style={{ fontSize: 13, color: "var(--color-text-secondary, #888)", textAlign: "center", lineHeight: 1.7, marginBottom: 12 }}>
                Every elementary function you created — exponential, logarithm, polynomial, oscillatory, infinite — was always just:
              </div>
              <div style={{
                textAlign: "center", padding: "12px 20px", background: "rgba(124,58,237,0.06)",
                border: "1px solid rgba(124,58,237,0.12)", borderRadius: 10,
                fontSize: 18, fontFamily: "var(--font-mono)", color: "#C4B5FD", fontWeight: 500,
              }}>
                eml(eml(eml(eml(...)))) 
              </div>
              <div style={{ fontSize: 12, color: "var(--color-text-secondary, #999)", textAlign: "center", marginTop: 10, fontStyle: "italic", lineHeight: 1.6 }}>
                One function, composed with itself, {created.length} times.
                <br />It created a universe with {Object.entries(depthCounts).filter(([,v]) => v > 0).length} depth levels,
                <br />{created.filter(id => CREATIONS.find(c => c.id === id)?.depth === 2).length} measurements, {created.filter(id => CREATIONS.find(c => c.id === id)?.depth === 3).length} oscillations, and infinity itself.
              </div>
              <div style={{ fontSize: 11, color: "#A78BFA", textAlign: "center", marginTop: 12, fontFamily: "var(--font-mono)" }}>
                "The ladder has five rungs, generated by two primitives,
                <br />and there are exactly three ways to reach the top."
              </div>
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {/* Current age info */}
          <div style={{
            padding: "12px 14px", borderRadius: 10,
            background: `${age.color}06`, border: `1px solid ${age.color}15`,
            transition: "all 0.5s",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: age.color, textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>{age.name}</div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)", fontFamily: "var(--font-mono)" }}>{age.stratum}</div>
          </div>

          {/* Creation log */}
          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>Created</div>
            <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #1a1a2e)" }}>
              {created.length}/{totalCreations}
            </div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)", marginBottom: 8 }}>generations</div>

            {created.map(id => {
              const c = CREATIONS.find(cr => cr.id === id);
              if (!c) return null;
              return (
                <div key={id} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "3px 0", borderBottom: "1px solid var(--color-border-tertiary, rgba(0,0,0,0.03))",
                }}>
                  <span style={{ fontSize: 11, color: c.color, fontWeight: 500 }}>{c.name}</span>
                  <span style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #aaa)" }}>d={String(c.depth)}</span>
                </div>
              );
            })}
          </div>

          {/* Depth census */}
          {created.length > 3 && (
            <div style={{
              padding: "10px 12px", borderRadius: 10,
              background: "var(--color-background-secondary, #faf5ff)",
              border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>Depth census</div>
              {Object.entries(depthCounts).filter(([, v]) => v > 0).map(([depth, count]) => (
                <div key={depth} style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                  <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: depth === "2" ? "#8B5CF6" : "var(--color-text-secondary, #888)" }}>
                    EML-{depth}
                  </span>
                  <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #aaa)" }}>
                    {count} {depth === "2" && created.length > 6 ? `(${Math.round(count / created.length * 100)}%)` : ""}
                  </span>
                </div>
              ))}
              {depthCounts[2] > 2 && created.length > 6 && (
                <div style={{ fontSize: 9, color: "#8B5CF6", fontStyle: "italic", marginTop: 4 }}>
                  Most of your universe lives at depth 2. That's not an accident.
                </div>
              )}
            </div>
          )}

          {/* Latest creation detail */}
          {selectedCreation && (
            <div style={{
              padding: "10px 12px", borderRadius: 10,
              background: `${selectedCreation.color}06`,
              border: `1px solid ${selectedCreation.color}15`,
              animation: "fadeIn 0.3s ease",
            }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: selectedCreation.color, marginBottom: 3 }}>{selectedCreation.name}</div>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #888)", marginBottom: 4 }}>{selectedCreation.formula}</div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", lineHeight: 1.5 }}>{selectedCreation.desc}</div>
              <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #aaa)", marginTop: 4 }}>depth {String(selectedCreation.depth)}</div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: "0.75rem 1rem", marginTop: 12,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          Every function on a scientific calculator — every constant, every operation, every wave — can be built from one equation composed with itself.
          <code style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "#7C3AED", margin: "0 3px" }}>eml(x,y) = exp(x) − ln(y)</code>
          is the NAND gate of continuous mathematics. You just built the elementary function library from it.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#10B981", textDecoration: "none", fontWeight: 500 }}>monogate.dev</a>
        {" · "}
        <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none" }}>arXiv:2603.21852</a>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }
        @media(max-width:640px){
          .genesis-grid{grid-template-columns:1fr!important;}
          .genesis-ages>div{flex:0 0 calc(33% - 4px)!important; min-width:0;}
          .genesis-ages{flex-wrap:wrap!important;}
        }
      `}</style>
    </div>
  );
}
