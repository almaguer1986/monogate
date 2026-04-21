import { useState, useRef, useEffect } from "react";

// ═══════════════════════════════════════════════════════════════════
// BARRIER FUNCTIONS — EML-∞ over ℝ, some resolved over ℂ via T03
// ═══════════════════════════════════════════════════════════════════
const BARRIERS = [
  {
    id: "sin",
    name: "sin(x)",
    symbol: "sin",
    desc: "Periodic oscillation. Infinitely many zeros. T01: no finite real EML tree can equal it.",
    formula: "EML-∞ (ℝ)  ·  EML-1 (ℂ)",
    color: "#EF4444",
    shadows: [
      { id: "sin_n1", name: "N=1 shadow", depth: 1, mse: 0.4932,
        formula: "exp(x) — 1 node, MSE 0.493",
        desc: "1-node real EML tree. Best fit: exp(x). MSE 0.493. No oscillation at depth 1.",
        type: "real" },
      { id: "sin_n3", name: "N=3 shadow", depth: 3, mse: 0.0059,
        formula: "depth-3 composition — MSE 0.006",
        desc: "N=3 singularity: 64 trees. MSE drops 100× vs depth 2. Best real approximation. Still not sin(x).",
        type: "real" },
      { id: "sin_n12", name: "N=12 shadow", depth: 12, mse: 0.0048,
        formula: "1,704,034,304 trees — MSE 0.005",
        desc: "1.7 billion real EML trees exhaustively searched. Zero sin(x) candidates. T01 confirmed computationally.",
        type: "real" },
      { id: "sin_complex", name: "ℂ bypass", depth: "C", mse: 0,
        formula: "sin(x) = Im(eml(ix, 1))",
        desc: "T03 Euler Gateway: sin(x) = Im(eml(ix,1)). Over ℂ, 1 node. MSE = 0. Exact. The barrier dissolves.",
        type: "complex" },
    ],
  },
  {
    id: "cos",
    name: "cos(x)",
    symbol: "cos",
    desc: "Phase-shifted oscillation. Same infinite-depth barrier over ℝ. T03 resolves it over ℂ.",
    formula: "EML-∞ (ℝ)  ·  EML-1 (ℂ)",
    color: "#06B6D4",
    shadows: [
      { id: "cos_n3", name: "N=3 shadow", depth: 3, mse: 0.0063,
        formula: "depth-3 composition — MSE 0.006",
        desc: "N=3 behavior mirrors sin(x). Phase shift doesn't change depth. The barrier is structural, not incidental.",
        type: "real" },
      { id: "cos_n12", name: "N=12 shadow", depth: 12, mse: 0.0051,
        formula: "1,704,034,304 trees — MSE 0.005",
        desc: "Same exhaustive search confirms the barrier for cos(x). No finite real EML tree exists.",
        type: "real" },
      { id: "cos_complex", name: "ℂ bypass", depth: "C", mse: 0,
        formula: "cos(x) = Re(eml(ix, 1))",
        desc: "T03 variant: cos(x) = Re(eml(ix,1)). Same 1 complex node. The Euler Gateway resolves both.",
        type: "complex" },
    ],
  },
  {
    id: "abs_sin",
    name: "|sin(x)|",
    symbol: "|s|",
    desc: "Rectified sine. Non-analytic kinks at every zero. EML-∞ over ℝ and ℂ both. No bypass exists.",
    formula: "EML-∞ (ℝ)  ·  EML-∞ (ℂ)",
    color: "#8B5CF6",
    shadows: [
      { id: "abs_fourier", name: "Fourier shadow", depth: "F", mse: null,
        formula: "4/π · Σ cos(2kx)/(1−4k²)",
        desc: "Infinite Fourier series. Each partial sum is EML-3. Converges to |sin(x)| — but requires infinitely many terms.",
        type: "real" },
      { id: "abs_no_bypass", name: "No ℂ bypass", depth: "C", mse: null,
        formula: "|sin(x)| ∈ EML-∞ (ℂ) also",
        desc: "Non-analytic kinks survive over ℂ. No Euler trick applies. This function is unreachable in both domains.",
        type: "none" },
    ],
  },
];

const ALL_SHADOWS = BARRIERS.flatMap(b =>
  b.shadows.map(s => ({ ...s, barrierId: b.id, barrierName: b.name, barrierColor: b.color }))
);

// depth → y fraction in the lower canvas zone
function depthY(depth, horizonY, h) {
  if (depth === 1)   return horizonY + (h - horizonY) * 0.22;
  if (depth === 3)   return horizonY + (h - horizonY) * 0.46;
  if (depth === 12)  return horizonY + (h - horizonY) * 0.70;
  if (depth === "F") return horizonY + (h - horizonY) * 0.88;
  return horizonY + (h - horizonY) * 0.55;
}

// ═══════════════════════════════════════════════════════════════════
// BARRIER CANVAS
// ═══════════════════════════════════════════════════════════════════
function BarrierCanvas({ barriers, collectedShadows, selectedBarrier, bypassRevealed, pulse }) {
  const ref = useRef(null), t = useRef(0), f = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height;
    t.current = 0;
    const go = () => {
      t.current += 0.012; const time = t.current;
      ctx.fillStyle = "rgba(6,2,14,0.06)"; ctx.fillRect(0, 0, w, h);

      const horizonY = h * 0.38;
      const complexX = w * 0.72; // dividing line: real left, complex right

      // ─── DEPTH ZONE LABELS (left = real EML, right = complex ℂ) ───
      ctx.save();
      ctx.fillStyle = "rgba(100,116,139,0.07)"; ctx.font = "8px monospace"; ctx.textAlign = "left";
      ctx.fillText("EML-1", 6, horizonY + (h - horizonY) * 0.22 + 4);
      ctx.fillText("EML-3", 6, horizonY + (h - horizonY) * 0.46 + 4);
      ctx.fillText("N=12", 6, horizonY + (h - horizonY) * 0.70 + 4);
      ctx.fillText("EML-∞", 6, horizonY + (h - horizonY) * 0.88 + 4);
      ctx.restore();

      // ─── COMPLEX ZONE (right column) ───
      const czGrad = ctx.createLinearGradient(complexX, horizonY, w, h);
      czGrad.addColorStop(0, "rgba(253,230,138,0.015)");
      czGrad.addColorStop(1, "rgba(253,230,138,0.03)");
      ctx.fillStyle = czGrad; ctx.fillRect(complexX, horizonY, w - complexX, h - horizonY);
      ctx.beginPath(); ctx.moveTo(complexX, horizonY); ctx.lineTo(complexX, h);
      ctx.strokeStyle = "rgba(253,230,138,0.06)"; ctx.lineWidth = 0.5;
      ctx.setLineDash([4, 6]); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = "rgba(253,230,138,0.09)"; ctx.font = "8px monospace"; ctx.textAlign = "center";
      ctx.fillText("ℂ", complexX + (w - complexX) / 2, horizonY + 12);

      // ─── HORIZON ───
      for (let i = 0; i < 200; i++) {
        const x = (i / 200) * w;
        const wave = Math.sin(i * 0.08 + time * 0.5) * 2 + Math.sin(i * 0.15 + time * 0.8) * 1;
        ctx.beginPath(); ctx.arc(x, horizonY + wave, 0.5 + Math.sin(time + i * 0.3) * 0.3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(253,230,138,${0.06 + Math.sin(time * 2 + i * 0.1) * 0.03})`; ctx.fill();
      }
      ctx.fillStyle = "rgba(253,230,138,0.05)"; ctx.font = "9px monospace"; ctx.textAlign = "center";
      ctx.fillText("— EML-∞ above · real approximations below · ℂ bypass right —", w / 2, horizonY - 4);

      // ─── COSMIC DUST (above horizon) ───
      for (let i = 0; i < 50; i++) {
        const x = (Math.sin(i * 73.7) * 0.5 + 0.5) * w;
        const y = (Math.sin(i * 31.3 + 0.5) * 0.5 + 0.5) * horizonY;
        const sz = 0.3 + Math.sin(time * 0.4 + i * 2.1) * 0.2;
        ctx.beginPath(); ctx.arc(x, y, sz, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(253,230,138,${0.04 + Math.sin(time * 0.3 + i) * 0.02})`; ctx.fill();
      }

      // ─── BARRIERS — massive, glowing, above horizon ───
      barriers.forEach((b, i) => {
        const bx = (i + 0.5) / barriers.length * (complexX - 20) + 10;
        const breathe = Math.sin(time * 0.4 + i * 1.2) * 5;
        const by = horizonY * 0.38 + breathe;
        const isSelected = selectedBarrier === b.id;
        const shadowsFound = b.shadows.filter(s => collectedShadows.includes(s.id)).length;
        const completeness = shadowsFound / b.shadows.length;

        const r = parseInt(b.color.slice(1, 3), 16);
        const g = parseInt(b.color.slice(3, 5), 16);
        const bv = parseInt(b.color.slice(5, 7), 16);

        // Glow
        const glowSize = 40 + completeness * 25 + (isSelected ? 18 : 0);
        for (let ring = 3; ring >= 0; ring--) {
          const rr = glowSize - ring * 7;
          const grd = ctx.createRadialGradient(bx, by, 0, bx, by, rr);
          grd.addColorStop(0, `rgba(${r},${g},${bv},${(0.025 + completeness * 0.05 + (isSelected ? 0.04 : 0)) * (1 - ring * 0.22)})`);
          grd.addColorStop(1, "rgba(0,0,0,0)");
          ctx.fillStyle = grd; ctx.beginPath(); ctx.arc(bx, by, rr, 0, Math.PI * 2); ctx.fill();
        }

        // Symbol
        const symSize = isSelected ? 28 : 22;
        ctx.fillStyle = `rgba(${r},${g},${bv},${0.22 + completeness * 0.35 + (isSelected ? 0.18 : 0) + Math.sin(time * 1.2 + i) * 0.04})`;
        ctx.font = `bold ${symSize}px monospace`; ctx.textAlign = "center";
        ctx.fillText(b.symbol, bx, by + symSize * 0.35);
        ctx.fillStyle = `rgba(${r},${g},${bv},${0.06 + completeness * 0.1 + (isSelected ? 0.08 : 0)})`;
        ctx.font = "8px monospace";
        ctx.fillText(b.name, bx, by + symSize * 0.35 + 14);
        ctx.fillText("EML-∞", bx, by + symSize * 0.35 + 24);

        // ─── SHADOW BEAMS ───
        b.shadows.forEach((s, si) => {
          const isCollected = collectedShadows.includes(s.id);
          const isComplex = s.type === "complex";
          const isNone = s.type === "none";

          // Target position
          const tx = isComplex
            ? complexX + (w - complexX) * 0.5
            : bx + (si - (b.shadows.length - 1) / 2) * 28;
          const ty = isComplex
            ? horizonY + (h - horizonY) * 0.5
            : depthY(s.depth, horizonY, h);

          if (isCollected) {
            if (isNone) {
              // Blocked beam — dashed red X
              ctx.beginPath(); ctx.moveTo(bx, by + 20); ctx.lineTo(tx, ty);
              ctx.strokeStyle = `rgba(${r},${g},${bv},0.12)`; ctx.lineWidth = 1;
              ctx.setLineDash([3, 5]); ctx.stroke(); ctx.setLineDash([]);
              ctx.fillStyle = `rgba(${r},${g},${bv},0.2)`;
              ctx.font = "bold 12px sans-serif"; ctx.textAlign = "center";
              ctx.fillText("✕", tx, ty);
              ctx.font = "7px monospace";
              ctx.fillStyle = `rgba(${r},${g},${bv},0.25)`;
              ctx.fillText("no bypass", tx, ty + 12);
              return;
            }

            const beamColor = isComplex ? "253,230,138" : `${r},${g},${bv}`;
            const beamAlpha = isComplex ? 0.1 : 0.07;

            // Beam
            const bw2 = 10;
            const bg = ctx.createLinearGradient(bx, by + 18, tx, ty);
            bg.addColorStop(0, `rgba(${beamColor},${beamAlpha})`);
            bg.addColorStop(0.5, `rgba(${beamColor},${beamAlpha * 0.5 + Math.sin(time * 1.5 + si) * 0.02})`);
            bg.addColorStop(1, `rgba(${beamColor},${isComplex ? 0.18 : 0.12})`);
            ctx.beginPath();
            ctx.moveTo(bx - 2, by + 18); ctx.lineTo(tx - bw2 / 2, ty);
            ctx.lineTo(tx + bw2 / 2, ty); ctx.lineTo(bx + 2, by + 18);
            ctx.closePath(); ctx.fillStyle = bg; ctx.fill();

            // Pool
            const poolG = ctx.createRadialGradient(tx, ty, 0, tx, ty, isComplex ? 22 : 16);
            poolG.addColorStop(0, `rgba(${beamColor},${isComplex ? 0.22 : 0.14})`);
            poolG.addColorStop(1, "rgba(0,0,0,0)");
            ctx.fillStyle = poolG; ctx.beginPath(); ctx.arc(tx, ty, isComplex ? 22 : 16, 0, Math.PI * 2); ctx.fill();

            // Orb
            ctx.beginPath(); ctx.arc(tx, ty, 4 + Math.sin(time * 2 + si) * 1.2, 0, Math.PI * 2);
            ctx.fillStyle = isComplex ? `rgba(253,230,138,0.7)` : `rgba(${r},${g},${bv},0.55)`; ctx.fill();

            // Label
            ctx.fillStyle = isComplex ? "rgba(253,230,138,0.5)" : `rgba(${r},${g},${bv},0.4)`;
            ctx.font = "7px monospace"; ctx.textAlign = "center";
            const label = s.mse === 0 ? "MSE=0" : s.mse !== null ? `MSE ${s.mse}` : "∞ terms";
            ctx.fillText(label, tx, ty + 14);
            if (!isComplex) {
              const depthLabel = s.depth === "F" ? "EML-∞" : `N=${s.depth}`;
              ctx.fillText(depthLabel, tx, ty + 22);
            } else {
              ctx.fillText("ℂ exact", tx, ty + 22);
            }
          } else {
            // Uncollected hint
            ctx.beginPath(); ctx.moveTo(bx, by + 18); ctx.lineTo(tx, ty);
            const hintColor = isComplex ? "253,230,138" : `${r},${g},${bv}`;
            ctx.strokeStyle = `rgba(${hintColor},0.025)`; ctx.lineWidth = 0.5;
            ctx.setLineDash([2, 6]); ctx.stroke(); ctx.setLineDash([]);
            ctx.beginPath(); ctx.arc(tx, ty, 2.5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${hintColor},${0.04 + Math.sin(time * 2 + si + i) * 0.02})`; ctx.fill();
          }
        });
      });

      f.current = requestAnimationFrame(go);
    };
    ctx.fillStyle = "#06020E"; ctx.fillRect(0, 0, w, h); go();
    return () => cancelAnimationFrame(f.current);
  }, [barriers, collectedShadows, selectedBarrier, bypassRevealed, pulse]);

  return <canvas ref={ref} width={680} height={380} style={{ width: "100%", height: "100%", display: "block", borderRadius: 12 }} />;
}

// ═══════════════════════════════════════════════════════════════════
// MAIN GAME
// ═══════════════════════════════════════════════════════════════════
export default function Shadow() {
  const [collected, setCollected] = useState([]);
  const [selectedBarrier, setSelectedBarrier] = useState(null);
  const [selectedShadow, setSelectedShadow] = useState(null);
  const [bypassRevealed, setBypassRevealed] = useState(false);
  const [pulse, setPulse] = useState(0);

  useEffect(() => { let fr; const tick = () => { setPulse(p => p + 0.025); fr = requestAnimationFrame(tick); }; tick(); return () => cancelAnimationFrame(fr); }, []);

  const totalShadows = ALL_SHADOWS.length;
  const realShadows = collected.filter(id => {
    const s = ALL_SHADOWS.find(s => s.id === id);
    return s?.type === "real" || s?.type === "none";
  }).length;
  const complexShadows = collected.filter(id => ALL_SHADOWS.find(s => s.id === id)?.type === "complex").length;
  const allCollected = collected.length === totalShadows;

  // Reveal bypass card when first complex shadow collected
  useEffect(() => {
    if (complexShadows > 0 && !bypassRevealed) setBypassRevealed(true);
  }, [complexShadows, bypassRevealed]);

  const collectShadow = (shadowId) => {
    if (collected.includes(shadowId)) return;
    setCollected(prev => [...prev, shadowId]);
    setSelectedShadow(ALL_SHADOWS.find(s => s.id === shadowId));
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)();
      const shadow = ALL_SHADOWS.find(s => s.id === shadowId);
      const isComplex = shadow?.type === "complex";
      const isNone = shadow?.type === "none";
      const freq = isComplex ? 440 : isNone ? 110 : [220, 261.63, 329.63][BARRIERS.findIndex(b => b.id === shadow?.barrierId)] || 220;
      const o = ac.createOscillator();
      o.type = isComplex ? "sine" : "triangle";
      o.frequency.setValueAtTime(freq, ac.currentTime);
      const g = ac.createGain();
      g.gain.setValueAtTime(isComplex ? 0.1 : 0.06, ac.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + (isComplex ? 3 : 1.5));
      o.connect(g); g.connect(ac.destination);
      o.start(); o.stop(ac.currentTime + (isComplex ? 3.5 : 2));
      setTimeout(() => ac.close(), 4000);
    } catch {}
  };

  const activeBarrier = selectedBarrier ? BARRIERS.find(b => b.id === selectedBarrier) : null;

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 740, margin: "0 auto", padding: "0 0 2rem" }}>
      {/* Header */}
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.4rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#FDE68A", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>The Barrier</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          sin(x) is unreachable in real EML. Collect the approximation shadows — then find the complex bypass.
        </p>
      </div>

      {/* Progress */}
      <div style={{
        textAlign: "center", padding: "6px 14px", margin: "6px 0 10px",
        background: allCollected ? "rgba(16,185,129,0.08)" : "rgba(253,230,138,0.05)",
        borderRadius: 8, fontSize: 12, fontWeight: 500,
        color: allCollected ? "#059669" : "#D97706",
      }}>
        {allCollected
          ? "✓ All shadows collected. T01 confirmed. T03 discovered. The barrier is mapped."
          : `${collected.length}/${totalShadows} shadow fragments collected`}
      </div>

      <div className="shadow-grid" style={{ display: "grid", gridTemplateColumns: "1fr 220px", gap: 10 }}>
        {/* BARRIER CANVAS */}
        <div>
          <div style={{ borderRadius: 14, overflow: "hidden", border: "1px solid rgba(253,230,138,0.1)", marginBottom: 10, aspectRatio: "680/380" }}>
            <BarrierCanvas barriers={BARRIERS} collectedShadows={collected} selectedBarrier={selectedBarrier} bypassRevealed={bypassRevealed} pulse={pulse} />
          </div>

          {/* BARRIER SELECTOR */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 4, marginBottom: 10 }}>
            {BARRIERS.map(b => {
              const isActive = selectedBarrier === b.id;
              const found = b.shadows.filter(s => collected.includes(s.id)).length;
              const complete = found === b.shadows.length;
              return (
                <button key={b.id} onClick={() => setSelectedBarrier(isActive ? null : b.id)} style={{
                  padding: "8px 6px", borderRadius: 8, cursor: "pointer", textAlign: "center",
                  background: isActive ? `${b.color}15` : complete ? "rgba(16,185,129,0.06)" : "var(--color-background-secondary, #f8f5ff)",
                  border: isActive ? `2px solid ${b.color}40` : complete ? "1.5px solid rgba(16,185,129,0.15)" : "1.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
                }}>
                  <div style={{ fontSize: 16, color: b.color, fontFamily: "var(--font-mono)", fontWeight: 700, marginBottom: 2 }}>{b.symbol}</div>
                  <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-secondary, #666)", marginBottom: 1 }}>{b.name}</div>
                  <div style={{ fontSize: 8, color: "var(--color-text-secondary, #aaa)", fontFamily: "var(--font-mono)" }}>{b.formula.split("·")[0].trim()}</div>
                  <div style={{ fontSize: 8, color: complete ? "#059669" : b.color, fontFamily: "var(--font-mono)", marginTop: 2 }}>{found}/{b.shadows.length}</div>
                </button>
              );
            })}
          </div>

          {/* SHADOW COLLECTION — for selected barrier */}
          {activeBarrier && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 10, fontWeight: 600, color: activeBarrier.color, textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
                Shadows of {activeBarrier.name}
              </div>
              <div style={{ fontSize: 12, color: "var(--color-text-secondary, #888)", marginBottom: 8, lineHeight: 1.5 }}>
                {activeBarrier.desc}
                <br /><span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: activeBarrier.color }}>{activeBarrier.formula}</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {activeBarrier.shadows.map(s => {
                  const isCollected = collected.includes(s.id);
                  const isComplex = s.type === "complex";
                  const isNone = s.type === "none";
                  const accentColor = isComplex ? "#FDE68A" : isNone ? "#9CA3AF" : activeBarrier.color;
                  return (
                    <button key={s.id} onClick={() => collectShadow(s.id)} style={{
                      padding: "12px 14px", borderRadius: 10, cursor: isCollected ? "default" : "pointer",
                      background: isCollected
                        ? isComplex ? "rgba(253,230,138,0.06)" : `${activeBarrier.color}08`
                        : "var(--color-background-secondary, #f8f5ff)",
                      border: isCollected
                        ? isComplex ? "1.5px solid rgba(253,230,138,0.15)" : `1.5px solid ${activeBarrier.color}20`
                        : "1.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
                      textAlign: "left", transition: "all 0.2s",
                      opacity: isCollected ? 1 : 0.7 + Math.sin(pulse * 3) * 0.15,
                    }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: isCollected ? accentColor : "var(--color-text-primary, #555)" }}>
                          {isCollected ? "✓ " : "◇ "}{s.name}
                        </span>
                        <div style={{ display: "flex", gap: 5, alignItems: "center" }}>
                          {isComplex && (
                            <span style={{ fontSize: 9, padding: "2px 6px", borderRadius: 4, background: "rgba(253,230,138,0.1)", color: "#FDE68A", fontWeight: 600, fontFamily: "var(--font-mono)" }}>
                              ℂ bypass
                            </span>
                          )}
                          {isNone && (
                            <span style={{ fontSize: 9, padding: "2px 6px", borderRadius: 4, background: "rgba(156,163,175,0.1)", color: "#9CA3AF", fontWeight: 600, fontFamily: "var(--font-mono)" }}>
                              no bypass
                            </span>
                          )}
                          {!isComplex && !isNone && s.depth !== "F" && (
                            <span style={{ fontSize: 9, padding: "2px 6px", borderRadius: 4, background: `${activeBarrier.color}10`, color: activeBarrier.color, fontWeight: 600, fontFamily: "var(--font-mono)" }}>
                              N={s.depth}
                            </span>
                          )}
                          {s.mse !== null && s.mse !== undefined && (
                            <span style={{ fontSize: 8, padding: "2px 6px", borderRadius: 4, background: s.mse === 0 ? "rgba(16,185,129,0.1)" : "rgba(0,0,0,0.04)", color: s.mse === 0 ? "#059669" : "var(--color-text-secondary, #999)" }}>
                              {s.mse === 0 ? "exact" : `MSE ${s.mse}`}
                            </span>
                          )}
                        </div>
                      </div>
                      {isCollected ? (
                        <>
                          <div style={{ fontSize: 11, color: "var(--color-text-secondary, #777)", lineHeight: 1.5, marginBottom: 4 }}>{s.desc}</div>
                          <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: accentColor, opacity: 0.7 }}>{s.formula}</div>
                        </>
                      ) : (
                        <div style={{ fontSize: 11, color: "var(--color-text-secondary, #bbb)", fontStyle: "italic" }}>
                          {isComplex ? "Tap to reveal the complex bypass" : "Tap to collect this approximation shadow"}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {!activeBarrier && (
            <div style={{ textAlign: "center", padding: 16, color: "var(--color-text-secondary, #aaa)", fontSize: 12, fontStyle: "italic" }}>
              Select a barrier function above to explore its shadows
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {/* Latest shadow */}
          {selectedShadow && (
            <div style={{
              padding: "10px 12px", borderRadius: 10,
              background: selectedShadow.type === "complex" ? "rgba(253,230,138,0.06)" : `${selectedShadow.barrierColor}08`,
              border: `1px solid ${selectedShadow.type === "complex" ? "rgba(253,230,138,0.15)" : selectedShadow.barrierColor + "18"}`,
              animation: "fadeIn 0.3s ease",
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: selectedShadow.type === "complex" ? "#FDE68A" : selectedShadow.barrierColor, textTransform: "uppercase", letterSpacing: 1, marginBottom: 3 }}>
                {selectedShadow.type === "complex" ? "bypass found" : selectedShadow.type === "none" ? "barrier confirmed" : "shadow collected"}
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary, #1a1a2e)", marginBottom: 2 }}>{selectedShadow.name}</div>
              <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)", marginBottom: 4 }}>from {selectedShadow.barrierName}</div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", lineHeight: 1.5 }}>{selectedShadow.desc}</div>
            </div>
          )}

          {/* Shadow census */}
          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>Shadow census</div>
            <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #1a1a2e)" }}>{collected.length}/{totalShadows}</div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)", marginBottom: 6 }}>fragments collected</div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
              <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "#6B7280" }}>real approx</span>
              <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #aaa)" }}>{realShadows}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "#FDE68A" }}>ℂ bypasses</span>
              <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #aaa)" }}>{complexShadows}</span>
            </div>
          </div>

          {/* T01 CARD */}
          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "rgba(239,68,68,0.04)",
            border: "1px solid rgba(239,68,68,0.12)",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#EF4444", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>T01 — Infinite Zeros Barrier</div>
            <div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", lineHeight: 1.6 }}>
              Any finite real EML tree is real-analytic with finitely many zeros.<br />
              sin(x) has infinitely many zeros.<br />
              Therefore: no finite real EML tree equals sin(x).
            </div>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "#EF4444", opacity: 0.6, marginTop: 6 }}>
              sin(x) ∈ EML-∞(ℝ)
            </div>
          </div>

          {/* T03 CARD — unlocked when complex bypass found */}
          {bypassRevealed ? (
            <div style={{
              padding: "10px 12px", borderRadius: 10,
              background: "rgba(253,230,138,0.05)",
              border: "1px solid rgba(253,230,138,0.15)",
              animation: "fadeIn 0.5s ease",
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: "#FDE68A", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>T03 — Euler Gateway</div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", lineHeight: 1.6 }}>
                Over ℂ, the barrier dissolves.<br />
                1 node. MSE = 0. Exact.
              </div>
              <div style={{ marginTop: 6, padding: "6px 8px", borderRadius: 6, background: "rgba(253,230,138,0.04)" }}>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "#FDE68A" }}>sin(x) = Im(eml(ix, 1))</div>
                <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "#06B6D4", marginTop: 2 }}>cos(x) = Re(eml(ix, 1))</div>
              </div>
              <div style={{ fontSize: 9, color: "var(--color-text-secondary, #999)", marginTop: 6 }}>
                The real-domain barrier is structural — not fundamental. The complex field resolves it.
              </div>
            </div>
          ) : (
            <div style={{
              padding: "10px 12px", borderRadius: 10,
              background: "rgba(253,230,138,0.02)",
              border: "1px dashed rgba(253,230,138,0.08)",
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: "rgba(253,230,138,0.3)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>T03 — locked</div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary, #bbb)", fontStyle: "italic" }}>
                Collect a ℂ bypass shadow to unlock the Euler Gateway theorem.
              </div>
            </div>
          )}

          {/* What you're seeing */}
          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>What you're seeing</div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #666)", lineHeight: 1.7 }}>
              The functions above the horizon are EML-∞ over ℝ — no finite real tree reaches them.
              Below: the best approximation shadows at each search depth. MSE decreases, but never reaches zero.
              The golden zone shows what's possible over ℂ: exact solutions in 1 node.
            </div>
          </div>
        </div>
      </div>

      {/* ALL COLLECTED — final message */}
      {allCollected && (
        <div style={{
          padding: "16px 20px", marginTop: 10, borderRadius: 12,
          background: "rgba(253,230,138,0.04)", border: "1px solid rgba(253,230,138,0.12)",
          textAlign: "center", animation: "fadeIn 0.8s ease",
        }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#FDE68A", marginBottom: 8 }}>
            The barrier is mapped.
          </div>
          <div style={{ fontSize: 13, color: "var(--color-text-secondary, #888)", lineHeight: 1.7, maxWidth: 500, margin: "0 auto" }}>
            {realShadows} real approximation shadows. {complexShadows} complex bypasses. 1 function without any bypass.<br /><br />
            T01 explains why 1.7 billion real trees find nothing. T03 shows the complex field resolves sin(x) and cos(x) exactly. |sin(x)| remains at EML-∞ in both domains — non-analytic kinks survive everywhere.
          </div>
          <div style={{ fontSize: 11, color: "#A78BFA", fontFamily: "var(--font-mono)", marginTop: 10 }}>
            "The barrier over ℝ is not the barrier over ℂ.
            <br />One equation. Two fields. Different depths."
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{
        padding: "0.75rem 1rem", marginTop: 12,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          T01 (§12): Any finite real EML tree is real-analytic with finitely many zeros — sin(x) is excluded. N=12 search (§35): 1,704,034,304 trees confirmed zero sin(x) candidates.
          T03 (§18): sin(x) = Im(eml(ix,1)). Over ℂ, 1 node. The real-domain barrier is structural, not fundamental.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#FDE68A", textDecoration: "none", fontWeight: 500 }}>monogate.dev</a>
        {" · "}
        <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none" }}>arXiv:2603.21852</a>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }
        @media(max-width:600px){.shadow-grid{grid-template-columns:1fr!important;}}
      `}</style>
    </div>
  );
}
