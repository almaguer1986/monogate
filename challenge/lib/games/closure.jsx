import { useState, useRef, useEffect } from "react";
// N=3 Singularity (§37): at depth 2, best MSE for sin ≈ 5.9e-3.
// At depth 3, best MSE ≈ 4.1e-9. That is 1.4 million times better.
// All objects are mathematical functions from the EML-k census §41.
const OBJECTS = [
  { id: "sin", name: "sin(x)", desc: "EML-3 in census. MSE 4.1e-9 at N=3.", color: "#F472B6", category: "EML-3", formula: "Im(eml(ix, 1))", detail: "1 complex EML node. Infinite real EML nodes (T01). The N=3 singularity target: MSE 5.9e-3 at depth 2 → 4.1e-9 at depth 3 = 1.4M× jump." },
  { id: "cos", name: "cos(x)", desc: "EML-3 in census. Same barrier as sin.", color: "#E879F9", category: "EML-3", formula: "Re(eml(ix, 1))", detail: "Re(eml(ix,1)). 1 complex node. Proved impossible over ℝ with finite nodes (T01)." },
  { id: "tanh", name: "tanh(x)", desc: "EML-3. MSE floor ~4e-9.", color: "#A78BFA", category: "EML-3", formula: "(e^2x−1)/(e^2x+1)", detail: "EML-3 in census §41. Depth-3 functions compose to depth-3 functions — closure holds." },
  { id: "erf", name: "erf(x)", desc: "EML-3. Census §41.", color: "#FBBF24", category: "EML-3", formula: "2/√π ∫₀ˣ e^{-t²}dt", detail: "EML-3 in census §41. Error function. Maclaurin series basis confirmed EML-3." },
  { id: "fourier", name: "Fourier series", desc: "Sum of EML-3 atoms.", color: "#34D399", category: "EML-3", formula: "Σ aₙsin(nωt)+bₙcos(nωt)", detail: "Each term is one EML-3 atom. EML Fourier density theorem (§36): converges to any smooth function." },
  { id: "lgamma", name: "lgamma(x)", desc: "EML-3. Census §41.", color: "#60A5FA", category: "EML-3", formula: "ln(Γ(x))", detail: "Log-Gamma function. EML-3 in census §41 with measured MSE floor." },
  { id: "wave", name: "wave eq", desc: "EML-3 solution space.", color: "#F97316", category: "EML-3", formula: "∂²u/∂t² = c²∇²u", detail: "Solutions are sin/cos — EML-3. The equation's solution space is depth-3." },
  { id: "onsager", name: "Onsager sol.", desc: "Exact 2D Ising. Elliptic.", color: "#FDE68A", category: "EML-3", formula: "exact 2D Ising", detail: "Onsager's exact solution uses elliptic integrals — EML-3 structure. Combines with other EML-3 functions and stays at depth 3." },
  { id: "schrod", name: "ψ = Ae^{ikx}", desc: "Plane wave. EML-3.", color: "#2DD4BF", category: "EML-3", formula: "exp(ikx)", detail: "Complex exponential plane wave. EML-3 by the complex bypass (T03). Composition with other EML-3 functions stays EML-3." },
  { id: "lfunc", name: "L-function", desc: "EML-3 on critical line.", color: "#FB7185", category: "EML-3", formula: "L(s, χ)", detail: "Euler product of EML-3 factors. Analytic structure on the critical line is EML-3. Number theory meets analysis." },
];
const COMBOS = [
  { a: "sin", b: "cos", result: "sin²(x)+cos²(x)=1", depth: 3, flavor: "Pythagorean identity. Both EML-3, result is a constant — but the function stays depth 3." },
  { a: "sin", b: "fourier", result: "F̂(sin) = δ-peaks at ±1", depth: 3, flavor: "Fourier of sin gives delta spikes. EML-3 in, EML-3 out. The stratum seals itself." },
  { a: "sin", b: "tanh", result: "sin(tanh(x)) — smooth oscillation", depth: 3, flavor: "Composition of EML-3 functions. Census §41 confirms depth stays 3." },
  { a: "sin", b: "erf", result: "sin(erf(x))", depth: 3, flavor: "Both EML-3 in census. Composition is EML-3. The room doesn't care which functions you pick." },
  { a: "sin", b: "wave", result: "Standing wave: sin(kx)·sin(ωt)", depth: 3, flavor: "Product of EML-3 functions. Wave equation solutions. Still depth 3." },
  { a: "cos", b: "fourier", result: "F̂(cos) = δ-peaks at ±1", depth: 3, flavor: "Same as sin — Fourier of cos gives delta peaks. Depth 3." },
  { a: "cos", b: "onsager", result: "Elliptic integral structure", depth: 3, flavor: "Onsager's exact solution involves cos-based elliptic integrals. Still EML-3." },
  { a: "tanh", b: "erf", result: "tanh(erf(x)) — S-curve", depth: 3, flavor: "Both EML-3 in census §41. Depth-3 functions compose to depth-3 functions — proved." },
  { a: "tanh", b: "fourier", result: "Fourier series of tanh", depth: 3, flavor: "EML Fourier density theorem: any EML-3 function has a depth-3 Fourier expansion." },
  { a: "erf", b: "lgamma", result: "erf(lgamma(x))", depth: 3, flavor: "Both EML-3 in census. Composition confirmed EML-3." },
  { a: "fourier", b: "fourier", result: "F̂(F̂(f)) = f(−x)", depth: 3, flavor: "Fourier involution. Apply Fourier twice: you get back the original (reflected). EML-3." },
  { a: "fourier", b: "wave", result: "Modal decomposition", depth: 3, flavor: "Fourier decomposition of wave equation solutions. EML-3 analyzing EML-3." },
  { a: "fourier", b: "schrod", result: "Momentum space ψ̂(k)", depth: 3, flavor: "Fourier of plane wave. Position ↔ momentum. Both EML-3 representations." },
  { a: "fourier", b: "lfunc", result: "Analytic continuation of L", depth: 3, flavor: "Fourier theory on groups underlies L-functions. Both EML-3." },
  { a: "wave", b: "schrod", result: "Quantum wave packet", depth: 3, flavor: "Wave equation + Schrödinger: both governed by sin/cos solutions. EML-3." },
  { a: "wave", b: "onsager", result: "2D wave + Ising", depth: 3, flavor: "Different physical models, same EML-3 solution structure." },
  { a: "lfunc", b: "schrod", result: "Random matrix / quantum chaos", depth: 3, flavor: "GUE statistics. Zeros of L-functions distribute like eigenvalues of quantum operators. Both EML-3." },
  { a: "lfunc", b: "onsager", result: "Elliptic curve L-function", depth: 3, flavor: "L-functions of elliptic curves involve Onsager-type integrals. EML-3." },
  { a: "sin", b: "lgamma", result: "Reflection formula: sin(πx)·Γ(x)·Γ(1-x) = π", depth: 3, flavor: "The reflection formula for Gamma. EML-3 functions combining. Still depth 3." },
  { a: "lgamma", b: "fourier", result: "Stirling series via Fourier", depth: 3, flavor: "Stirling's approximation has a Fourier series form. EML-3." },
];
function RoomCanvas({ attempts, escaped, pulse }) {
  const ref = useRef(null), t = useRef(0), f = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height;
    t.current = 0;
    const go = () => {
      t.current += 0.015; const time = t.current;
      ctx.fillStyle = escaped ? "rgba(22,8,2,0.04)" : "rgba(8,2,14,0.04)";
      ctx.fillRect(0, 0, w, h);
      const shake = Math.min(attempts * 0.15, 4);
      const ox = Math.sin(time * 8) * shake, oy = Math.cos(time * 7) * shake;
      if (escaped) {
        const grd = ctx.createRadialGradient(w/2, h/2, 0, w/2, h/2, Math.min(w,h) * 0.5);
        grd.addColorStop(0, `rgba(253,230,138,${0.03 + Math.sin(time) * 0.015})`);
        grd.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = grd; ctx.fillRect(0, 0, w, h);
        ctx.fillStyle = `rgba(253,230,138,${0.15 + Math.sin(time * 1.5) * 0.05})`;
        ctx.font = "bold 48px serif"; ctx.textAlign = "center";
        ctx.fillText("∞", w/2, h/2 + 18);
        ctx.fillStyle = `rgba(253,230,138,${0.06 + Math.sin(time * 2) * 0.02})`;
        ctx.font = "11px monospace";
        ctx.fillText("categorification", w/2, h/2 + 40);
        f.current = requestAnimationFrame(go); return;
      }
      const wc = 3 + attempts * 0.4, wa = 3 + attempts * 0.6;
      [[20, true, "#EC4899"], [h-20, true, "#EC4899"], [20, false, "#A78BFA"], [w-20, false, "#A78BFA"]].forEach(([pos, horiz, col]) => {
        ctx.beginPath();
        for (let i = 0; i < (horiz ? w : h); i += 2) {
          const wave = pos + Math.sin(i * 0.02 * wc + time * (1.7 + Math.random() * 0.5)) * wa + (horiz ? oy : ox);
          if (i === 0) { if (horiz) ctx.moveTo(i + ox, wave); else ctx.moveTo(wave, i + oy); }
          else { if (horiz) ctx.lineTo(i + ox, wave); else ctx.lineTo(wave, i + oy); }
        }
        ctx.strokeStyle = `${col}${Math.min(255, Math.floor(40 + attempts * 4)).toString(16).padStart(2,"0")}`;
        ctx.lineWidth = 1.5; ctx.stroke();
      });
      for (let i = Math.max(0, attempts - 6); i < attempts; i++) {
        const age = (attempts - i) * 0.15 + time * 0.5, r = age * 40, alpha = Math.max(0, 0.08 - age * 0.01);
        ctx.beginPath(); ctx.arc(w/2, h/2, r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(236,72,153,${alpha})`; ctx.lineWidth = 0.5; ctx.stroke();
      }
      ctx.fillStyle = `rgba(236,72,153,${0.06 + Math.sin(time * 2) * 0.02})`;
      ctx.font = "bold 64px serif"; ctx.textAlign = "center";
      ctx.fillText("3", w/2 + ox, h/2 + 22 + oy);
      OBJECTS.forEach((obj, i) => {
        const angle = (i / OBJECTS.length) * Math.PI * 2 + time * 0.08;
        const r = 80 + Math.sin(time * 0.3 + i * 2) * 15;
        const px = w/2 + Math.cos(angle) * r + ox, py = h/2 + Math.sin(angle) * r * 0.6 + oy;
        ctx.beginPath(); ctx.arc(px, py, 8, 0, Math.PI * 2);
        const pr = parseInt(obj.color.slice(1,3),16), pg = parseInt(obj.color.slice(3,5),16), pb = parseInt(obj.color.slice(5,7),16);
        ctx.fillStyle = `rgba(${pr},${pg},${pb},${0.06 + Math.sin(time + i) * 0.02})`; ctx.fill();
        ctx.fillStyle = `rgba(${pr},${pg},${pb},${0.12 + Math.sin(time * 1.5 + i) * 0.04})`;
        ctx.font = "7px monospace"; ctx.textAlign = "center";
        ctx.fillText(obj.name.split(" ")[0], px, py + 16);
      });
      if (attempts >= 8) { ctx.fillStyle = `rgba(239,68,68,${0.04 + Math.sin(time * 3) * 0.02})`; ctx.font = "9px monospace"; ctx.textAlign = "center"; ctx.fillText("EML-4 does not exist", w/2, h - 35); }
      if (attempts >= 15) { ctx.fillStyle = `rgba(253,230,138,${0.04 + Math.sin(time * 2) * 0.02})`; ctx.font = "9px monospace"; ctx.fillText("the only escape is up", w/2, 35); }
      if (attempts >= 20) { ctx.fillStyle = `rgba(253,230,138,${0.06 + Math.sin(time * 1.5) * 0.03})`; ctx.font = "10px monospace"; ctx.fillText("categorify", w/2, h/2 + 50); }
      f.current = requestAnimationFrame(go);
    };
    ctx.fillStyle = "#08020E"; ctx.fillRect(0, 0, w, h); go();
    return () => cancelAnimationFrame(f.current);
  }, [attempts, escaped, pulse]);
  return <canvas ref={ref} width={680} height={400} style={{ width: "100%", height: "100%", display: "block", borderRadius: 12 }} />;
}
export default function Closure() {
  const [selected, setSelected] = useState([]);
  const [lastCombo, setLastCombo] = useState(null);
  const [attempts, setAttempts] = useState(0);
  const [escaped, setEscaped] = useState(false);
  const [showGodel, setShowGodel] = useState(false);
  const [pulse, setPulse] = useState(0);
  useEffect(() => { let fr; const tick = () => { setPulse(p => p + 0.025); fr = requestAnimationFrame(tick); }; tick(); return () => cancelAnimationFrame(fr); }, []);
  const selectObject = (id) => {
    if (escaped) return;
    if (selected.includes(id)) { setSelected(selected.filter(s => s !== id)); return; }
    if (selected.length === 0) { setSelected([id]); return; }
    const a = selected[0], b = id;
    const combo = COMBOS.find(c => (c.a === a && c.b === b) || (c.a === b && c.b === a));
    const n = attempts + 1; setAttempts(n);
    setLastCombo(combo || { a, b, result: "EML-3 + EML-3", depth: 3, flavor: "Every combination stays. Every single one. The room is sealed by theorem, not by walls." });
    setSelected([]);
    try { const ac = new (window.AudioContext || window.webkitAudioContext)(); const o = ac.createOscillator(); o.type = "triangle"; o.frequency.setValueAtTime(220 + Math.random() * 220, ac.currentTime); o.frequency.setValueAtTime(220 + Math.random() * 220, ac.currentTime + 0.15); const g = ac.createGain(); g.gain.setValueAtTime(0.05, ac.currentTime); g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.8); o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime + 1); setTimeout(() => ac.close(), 1200); } catch {}
    if (n >= 15 && !showGodel) setShowGodel(true);
  };
  const categorify = () => {
    if (attempts < 22 || escaped) return; setEscaped(true);
    try { const ac = new (window.AudioContext || window.webkitAudioContext)(); [261.63, 329.63, 392, 523.25].forEach((freq, i) => { const o = ac.createOscillator(); o.type = i === 0 ? "sine" : "triangle"; o.frequency.setValueAtTime(freq, ac.currentTime + i * 0.3); const g = ac.createGain(); g.gain.setValueAtTime(0.05, ac.currentTime + i * 0.3); g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 4); o.connect(g); g.connect(ac.destination); o.start(ac.currentTime + i * 0.3); o.stop(ac.currentTime + 5); }); setTimeout(() => ac.close(), 6000); } catch {}
  };
  const reset = () => { setSelected([]); setLastCombo(null); setAttempts(0); setEscaped(false); setShowGodel(false); };
  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 740, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.4rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#EC4899", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>Closure</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>Every elementary function that oscillates or flows lives at EML depth 3. Try to escape. You can't.</p>
      </div>
      <div className="closure-grid" style={{ display: "grid", gridTemplateColumns: "1fr 210px", gap: 10 }}>
        <div>
          <div style={{ borderRadius: 14, overflow: "hidden", border: `1px solid ${escaped ? "rgba(253,230,138,0.15)" : "rgba(236,72,153,0.12)"}`, marginBottom: 10, position: "relative", aspectRatio: "680/400" }}>
            <RoomCanvas attempts={attempts} escaped={escaped} pulse={pulse} />
            {lastCombo && !escaped && (<div style={{ position: "absolute", bottom: 12, left: 12, right: 12, background: "rgba(0,0,0,0.75)", backdropFilter: "blur(4px)", borderRadius: 8, padding: "10px 14px", animation: "fadeIn 0.3s ease" }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#EC4899" }}>{lastCombo.result} → depth {lastCombo.depth}</div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.6)", marginTop: 3, fontStyle: "italic" }}>{lastCombo.flavor}</div>
            </div>)}
          </div>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-secondary, #888)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>{escaped ? "You escaped. But the room is still there. It always will be." : "Select two objects to combine. Everything stays at depth 3."}</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 5 }}>
            {OBJECTS.map(obj => (<button key={obj.id} onClick={() => selectObject(obj.id)} style={{ padding: "8px 10px", borderRadius: 8, border: "none", cursor: escaped ? "default" : "pointer", textAlign: "left", transition: "all 0.15s", background: selected.includes(obj.id) ? `${obj.color}15` : "var(--color-background-secondary, #f8f5ff)", border: selected.includes(obj.id) ? `2px solid ${obj.color}` : "1.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))", opacity: escaped ? 0.4 : 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: obj.color }}>{obj.name}</span>
                <span style={{ fontSize: 8, padding: "1px 5px", borderRadius: 3, background: `${obj.color}10`, color: obj.color }}>{obj.category}</span>
              </div>
              <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)", marginTop: 2 }}>{obj.desc}</div>
            </button>))}
          </div>
          {attempts >= 22 && !escaped && (<button onClick={categorify} style={{ display: "block", width: "100%", marginTop: 10, padding: "14px 20px", borderRadius: 12, border: "none", cursor: "pointer", textAlign: "center", background: "rgba(253,230,138,0.06)", border: "2px solid rgba(253,230,138,0.2)", animation: "fadeIn 0.5s ease" }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: "#FDE68A" }}>Categorify</div>
            <div style={{ fontSize: 11, color: "rgba(253,230,138,0.6)", marginTop: 2 }}>Enrich beyond finite description. Leave the room. Become EML-∞.</div>
          </button>)}
          {escaped && (<div style={{ marginTop: 10, padding: "20px 24px", borderRadius: 14, background: "rgba(253,230,138,0.04)", border: "1.5px solid rgba(253,230,138,0.12)", textAlign: "center", animation: "fadeIn 1s ease" }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: "#FDE68A", marginBottom: 8 }}>You left the room.</div>
            <div style={{ fontSize: 13, color: "var(--color-text-secondary, #888)", lineHeight: 1.7, marginBottom: 12 }}>sin, cos, tanh, erf, lgamma — all still in there. Every EML-3 function. The room is sealed by theorem, not by walls. The EML Pumping Lemma bounds the zeros. The N=12 exhaustive search confirms it: 1,704,034,304 trees searched, zero real escape candidates found.</div>
            <div style={{ fontSize: 13, color: "var(--color-text-secondary, #888)", lineHeight: 1.7, marginBottom: 12 }}>You escaped through categorification — the discontinuous leap to EML-∞. No gradient path leads here. No additional EML depth accumulates into a new stratum. The jump from finite to infinite is not a step. EML-4 does not exist as an intermediate floor.</div>
            <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "#A78BFA", lineHeight: 1.6 }}>EML Closure Theorem: eml(EML-3, EML-3) ⊆ EML-3.<br />The stratum is algebraically closed under composition.<br />Six independent proofs confirm EML-4 gap.<br />The only exit is categorification: ∞ nodes.</div>
          </div>)}
          <button onClick={reset} style={{ marginTop: 8, padding: "8px 16px", borderRadius: 8, width: "100%", border: "1.5px solid var(--color-border-tertiary, #ddd)", background: "var(--color-background-primary, white)", color: "var(--color-text-secondary, #666)", fontSize: 11, cursor: "pointer" }}>Reset — enter the room again</button>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ padding: "10px 12px", borderRadius: 10, background: "var(--color-background-secondary, #faf5ff)", border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))" }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#EC4899", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Combinations tried</div>
            <div style={{ fontSize: 28, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #1a1a2e)" }}>{attempts}</div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)" }}>all returned depth 3</div>
            {attempts > 0 && attempts < 22 && (<div style={{ marginTop: 6, height: 4, borderRadius: 2, background: "rgba(236,72,153,0.1)", overflow: "hidden" }}><div style={{ height: "100%", width: `${Math.min(100, (attempts / 22) * 100)}%`, background: "#EC4899", borderRadius: 2, transition: "width 0.3s" }} /></div>)}
          </div>
          {selected.length === 1 && (() => { const obj = OBJECTS.find(o => o.id === selected[0]); return obj ? (<div style={{ padding: "10px 12px", borderRadius: 10, background: `${obj.color}06`, border: `1px solid ${obj.color}15`, animation: "fadeIn 0.2s ease" }}><div style={{ fontSize: 13, fontWeight: 600, color: obj.color, marginBottom: 3 }}>{obj.name}</div><div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #aaa)", marginBottom: 4 }}>{obj.formula}</div><div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", lineHeight: 1.5 }}>{obj.detail}</div></div>) : null; })()}
          {attempts >= 5 && (<div style={{ padding: "8px 10px", borderRadius: 8, background: "rgba(236,72,153,0.04)", border: "1px solid rgba(236,72,153,0.08)", fontSize: 10, color: "#EC4899", lineHeight: 1.6 }}>eml(EML-3, EML-3) = EML-3. The stratum is algebraically closed.</div>)}
          {attempts >= 10 && (<div style={{ padding: "8px 10px", borderRadius: 8, background: "rgba(239,68,68,0.04)", border: "1px solid rgba(239,68,68,0.08)", fontSize: 10, color: "#EF4444", lineHeight: 1.6 }}>EML-4 does not exist. Six proofs. There is no depth between 3 and ∞. The door isn't locked. There IS no door.</div>)}
          {showGodel && (<div style={{ padding: "8px 10px", borderRadius: 8, background: "rgba(253,230,138,0.04)", border: "1px solid rgba(253,230,138,0.1)", fontSize: 10, color: "#FDE68A", lineHeight: 1.6, animation: "fadeIn 0.5s ease" }}>N=3 Singularity (§37): at depth 2, best MSE for sin ≈ 5.9×10⁻³. At depth 3, best MSE ≈ 4.1×10⁻⁹. That is 1.4 million times better. Depth 3 is not just deeper — it is a phase transition.</div>)}
          <div style={{ padding: "8px 10px", borderRadius: 8, background: "var(--color-background-secondary, #faf5ff)", border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))" }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Who's in here with you</div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #666)", lineHeight: 1.8 }}>
              <div>sin(x), cos(x), tanh(x)</div><div>erf(x), lgamma(x)</div><div>Fourier series</div><div>wave equation, Onsager solution</div><div>ψ = Ae^{ikx}, L-functions</div>
              <div style={{ color: "#EC4899", fontWeight: 500, marginTop: 4 }}>All EML-3. All closed under eml().</div>
              <div style={{ color: "#FDE68A", marginTop: 2 }}>EML-4 does not exist. Six proofs.</div>
            </div>
          </div>
        </div>
      </div>
      <div style={{ padding: "0.75rem 1rem", marginTop: 12, background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10, border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))" }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>EML-3 is the deepest finite stratum. The N=3 Singularity (§37) shows a 1.4-million-fold MSE improvement at depth 3 — not gradual, a phase transition. The EML Closure Theorem (§41) proves the stratum is algebraically sealed: no EML composition of depth-3 functions can exceed depth 3. EML-4 is a proved gap, not a conjecture. The only exit is categorification — EML-∞, the infinite-node limit.</p>
      </div>
      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#EC4899", textDecoration: "none", fontWeight: 500 }}>monogate.dev</a>{" · "}<a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none" }}>arXiv:2603.21852</a>
      </div>
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }
        @media(max-width:600px){.closure-grid{grid-template-columns:1fr!important;}}
      `}</style>
    </div>
  );
}
