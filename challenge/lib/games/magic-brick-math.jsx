import { useState, useRef, useEffect, useCallback, useMemo } from "react";

const eml = (x, y) => (y <= 0 ? Math.exp(x) : Math.exp(x) - Math.log(y));
const emlExp = (x) => eml(x, 1);

function deriveParams(bx, by, cw, ch) {
  const nx = (bx / cw) * 2 - 1, ny = (by / ch) * 2 - 1;
  const dist = Math.sqrt(nx * nx + ny * ny);
  const angle = Math.atan2(ny, nx);
  return {
    energy: Math.min(eml(dist * 0.8, 1), 8), scale: 0.5 + (1 - Math.min(dist, 1)) * 1.0,
    freq: Math.max(1, Math.min(eml(Math.abs(nx) * 1.5, 1), 12)),
    depth: Math.min(5, Math.floor(eml(dist * 0.6, 1))),
    arms: Math.max(2, Math.min(7, Math.floor(eml(Math.abs(ny) + 0.3, 1)))),
    hueShift: ((angle + Math.PI) / (2 * Math.PI)) * 360,
    planets: Math.max(3, Math.min(8, Math.floor(eml(Math.abs(nx) * 0.5 + Math.abs(ny) * 0.5, 1)))),
    chaos: 0.5 + dist * 2.5,
    primeCount: Math.max(20, Math.min(80, Math.floor(eml(dist * 0.9, 1) * 10))),
    nx, ny, dist, angle,
    raw: { emlPos: eml(nx, Math.abs(ny) + 0.01), emlEnergy: eml(dist * 0.8, 1) }
  };
}

const ZONES = [
  { id: "galaxy", label: "polar spiral", x: 340, y: 75, color: "#8B5CF6", glow: "139,92,246" },
  { id: "waveform", label: "waveform", x: 538, y: 185, color: "#EC4899", glow: "236,72,153" },
  { id: "chaos", label: "Lorenz attractor", x: 538, y: 330, color: "#EF4444", glow: "239,68,68" },
  { id: "primes", label: "Ulam spiral", x: 340, y: 408, color: "#10B981", glow: "16,185,129" },
  { id: "solar", label: "parametric orbit", x: 142, y: 330, color: "#F59E0B", glow: "245,158,11" },
  { id: "fractal", label: "exponential sweep", x: 142, y: 185, color: "#06B6D4", glow: "6,182,212" },
];
const ZR = 72, ZAR = 65, HEX_CENTER = { x: 340, y: 246 };

const HYBRIDS = [
  { z1: "galaxy", z2: "waveform", id: "singing_galaxy", label: "singing galaxy", color: "#C084FC", glow: "192,132,252" },
  { z1: "galaxy", z2: "fractal", id: "fractal_galaxy", label: "fractal galaxy", color: "#67E8F9", glow: "103,232,249" },
  { z1: "solar", z2: "fractal", id: "fractal_orbit", label: "fractal orbit", color: "#2DD4BF", glow: "45,212,191" },
  { z1: "solar", z2: "primes", id: "prime_orbits", label: "prime orbits", color: "#A3E635", glow: "163,230,53" },
  { z1: "chaos", z2: "waveform", id: "chaos_song", label: "chaos song", color: "#FB923C", glow: "251,146,60" },
  { z1: "chaos", z2: "primes", id: "chaos_primes", label: "chaos primes", color: "#F87171", glow: "248,113,113" },
];

const TRIPLES = [
  { zones: ["galaxy","fractal","waveform"], id: "tri_upper", label: "astral fracture", desc: "singing fractal galaxy", color: "#E879F9", glow: "232,121,249" },
  { zones: ["fractal","solar","primes"], id: "tri_left", label: "prime geometry", desc: "primes on fractal orbits", color: "#34D399", glow: "52,211,153" },
  { zones: ["waveform","chaos","primes"], id: "tri_right", label: "chaos choir", desc: "chaotic primes singing", color: "#FB7185", glow: "251,113,133" },
  { zones: ["galaxy","solar","chaos"], id: "tri_outer", label: "dark matter", desc: "chaotic galaxy with gravity", color: "#FBBF24", glow: "251,191,36" },
];

const UNIFIED = { id: "unified", label: "the monogate", desc: "eml(eml(eml(eml(eml(eml(1,1))))))", color: "#FFFFFF", glow: "255,255,255" };

function getTripleCenter(t) { const pts = t.zones.map(zid => ZONES.find(z => z.id === zid)).filter(Boolean); return { x: pts.reduce((s, p) => s + p.x, 0) / pts.length, y: pts.reduce((s, p) => s + p.y, 0) / pts.length }; }

function detectZone(bx, by) {
  if (Math.sqrt((bx - HEX_CENTER.x) ** 2 + (by - HEX_CENTER.y) ** 2) < 32) return { type: "unified", data: UNIFIED };
  for (const tri of TRIPLES) { const c = getTripleCenter(tri); if (Math.sqrt((bx - c.x) ** 2 + (by - c.y) ** 2) < 38) return { type: "triple", data: tri }; }
  for (const h of HYBRIDS) { const z1 = ZONES.find(z => z.id === h.z1), z2 = ZONES.find(z => z.id === h.z2); if (z1 && z2 && Math.sqrt((bx - (z1.x + z2.x) / 2) ** 2 + (by - (z1.y + z2.y) / 2) ** 2) < 42) return { type: "double", data: h }; }
  for (const z of ZONES) { if (Math.sqrt((bx - z.x) ** 2 + (by - z.y) ** 2) < ZAR) return { type: "single", data: z }; }
  return null;
}

function detectNearest(bx, by) {
  if (Math.sqrt((bx - HEX_CENTER.x) ** 2 + (by - HEX_CENTER.y) ** 2) < 55) return { type: "unified", data: UNIFIED };
  for (const tri of TRIPLES) { const c = getTripleCenter(tri); if (Math.sqrt((bx - c.x) ** 2 + (by - c.y) ** 2) < 55) return { type: "triple", data: tri }; }
  for (const h of HYBRIDS) { const z1 = ZONES.find(z => z.id === h.z1), z2 = ZONES.find(z => z.id === h.z2); if (z1 && z2 && Math.sqrt((bx - (z1.x + z2.x) / 2) ** 2 + (by - (z1.y + z2.y) / 2) ** 2) < 60) return { type: "double", data: h }; }
  let closest = null, cd = Infinity;
  ZONES.forEach(z => { const d = Math.sqrt((bx - z.x) ** 2 + (by - z.y) ** 2); if (d < ZR * 2.5 && d < cd) { closest = z; cd = d; } });
  if (closest) return { type: "single", data: closest };
  return null;
}

// Singleton AudioContext — created once on first user gesture, reused thereafter.
let _sharedAC = null;
function getAC() {
  if (!_sharedAC || _sharedAC.state === "closed") {
    _sharedAC = new (window.AudioContext || window.webkitAudioContext)();
  }
  return _sharedAC;
}

function createAmbient(type, params) {
  try {
    const ac = getAC();
    const startNodes = () => {
      const master = ac.createGain();
      master.gain.setValueAtTime(0, ac.currentTime);
      master.gain.linearRampToValueAtTime(0.45, ac.currentTime + 1.2);
      master.connect(ac.destination);
      const nodes = [];
      const addS = (f, v = 0.15) => { const o = ac.createOscillator(); o.type = "sine"; o.frequency.setValueAtTime(f, ac.currentTime); const g = ac.createGain(); g.gain.setValueAtTime(v, ac.currentTime); o.connect(g); g.connect(master); o.start(); nodes.push(o); };
      const addO = (f, t, v = 0.12) => { const o = ac.createOscillator(); o.type = t; o.frequency.setValueAtTime(f, ac.currentTime); const g = ac.createGain(); g.gain.setValueAtTime(v, ac.currentTime); o.connect(g); g.connect(master); o.start(); nodes.push(o); };
      if (type.includes("galaxy") || type.includes("singing") || type.includes("fractal_galaxy") || type === "tri_upper" || type === "tri_outer" || type === "unified") { addS(55); addS(55.5, 0.1); addS(440, 0.06); }
      if (type.includes("waveform") || type.includes("singing") || type.includes("chaos_song") || type === "tri_upper" || type === "tri_right" || type === "unified") { const b = 110 + (params?.freq || 4) * 25; [1, 2, 3].forEach(h => addO(b * h, h === 1 ? "sine" : "triangle", 0.1 / h)); }
      if (type.includes("fractal") || type === "tri_upper" || type === "tri_left" || type === "unified") { addS(880, 0.08); addS(660, 0.06); }
      if (type.includes("solar") || type.includes("orbit") || type === "tri_left" || type === "tri_outer" || type === "unified") { addS(65, 0.15); addS(98, 0.12); }
      if (type.includes("chaos") || type.includes("flutter") || type === "tri_right" || type === "tri_outer" || type === "unified") { addO(110, "sawtooth", 0.08); }
      if (type.includes("primes") || type.includes("count") || type === "tri_left" || type === "tri_right" || type === "unified") { addS(660, 0.07); }
      if (type === "unified") { addS(220, 0.06); addS(330, 0.05); }
      return { master, nodes };
    };

    let handle = null;
    const doStart = () => { handle = startNodes(); };

    if (ac.state === "suspended") {
      ac.resume().then(doStart);
    } else {
      doStart();
    }

    return {
      stop: () => {
        if (!handle) return;
        const { master, nodes } = handle;
        try {
          master.gain.setValueAtTime(master.gain.value, ac.currentTime);
          master.gain.linearRampToValueAtTime(0, ac.currentTime + 0.6);
          setTimeout(() => { nodes.forEach(n => { try { n.stop(); } catch {} }); }, 700);
        } catch {}
      },
    };
  } catch (err) {
    console.warn("Audio error:", err);
    return { stop: () => {} };
  }
}

function EquationLog({ params, mode }) {
  if (!params) return null;
  const { nx, ny, dist, raw } = params;
  const depth = mode === "unified" ? "∞" : TRIPLES.find(t => t.id === mode) ? "3" : HYBRIDS.find(h => h.id === mode) ? "2" : "1";
  const steps = [
    { eq: `brick → (${nx.toFixed(2)}, ${ny.toFixed(2)})`, val: null },
    { eq: `eml(${nx.toFixed(2)}, ${Math.abs(ny + 0.01).toFixed(2)})`, val: raw.emlPos.toFixed(4) },
    { eq: `energy = exp(${(dist * 0.8).toFixed(2)})`, val: raw.emlEnergy.toFixed(3) },
    { eq: `composition depth`, val: depth },
  ];
  return (
    <div style={{ fontFamily: "var(--font-mono,monospace)", fontSize: 10, lineHeight: 2, color: "#C4B5FD", padding: "8px 12px", background: "rgba(15,5,40,0.9)", borderRadius: 8, maxWidth: 300 }}>
      <div style={{ fontSize: 9, color: "#8B5CF6", marginBottom: 2, letterSpacing: 1, textTransform: "uppercase" }}>{mode === "unified" ? "unified eml" : depth === "3" ? "triple eml" : depth === "2" ? "hybrid eml" : "eml chain"}</div>
      {steps.map((s, i) => (<div key={i} style={{ display: "flex", justifyContent: "space-between", gap: 8, borderBottom: i < steps.length - 1 ? "1px solid rgba(139,92,246,0.12)" : "none", paddingBottom: 2 }}><span style={{ color: "#A78BFA" }}>{s.eq}</span>{s.val && <span style={{ color: "#FDE68A", fontWeight: 500 }}>{s.val}</span>}</div>))}
    </div>
  );
}

function kochSegs(ax, ay, bx, by, d) { if (d === 0) return [{ x1: ax, y1: ay, x2: bx, y2: by }]; const dx = bx - ax, dy = by - ay; return [...kochSegs(ax, ay, ax + dx / 3, ay + dy / 3, d - 1), ...kochSegs(ax + dx / 3, ay + dy / 3, (ax + bx) / 2 - dy * Math.sqrt(3) / 6, (ay + by) / 2 + dx * Math.sqrt(3) / 6, d - 1), ...kochSegs((ax + bx) / 2 - dy * Math.sqrt(3) / 6, (ay + by) / 2 + dx * Math.sqrt(3) / 6, ax + dx * 2 / 3, ay + dy * 2 / 3, d - 1), ...kochSegs(ax + dx * 2 / 3, ay + dy * 2 / 3, bx, by, d - 1)]; }
function isPrime(n) { if (n < 2) return false; if (n < 4) return true; if (n % 2 === 0 || n % 3 === 0) return false; for (let i = 5; i * i <= n; i += 6) if (n % i === 0 || n % (i + 2) === 0) return false; return true; }

function getLayers(id) {
  if (id === "unified") return ["galaxy", "waveform", "fractal", "solar", "chaos", "primes"];
  const tri = TRIPLES.find(t => t.id === id); if (tri) return tri.zones;
  const hyb = HYBRIDS.find(h => h.id === id); if (hyb) return [hyb.z1, hyb.z2];
  return [id];
}

function ComposedDemo({ params, layers }) {
  const ref = useRef(null), t = useRef(0), f = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c || !params) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height, cx = w / 2, cy = h / 2;
    t.current = 0;
    const has = (l) => layers.includes(l);
    const isU = layers.length === 6;
    const { energy, scale, arms, hueShift, freq, depth, planets, chaos, primeCount } = params;
    const pd = []; if (has("solar")) { for (let i = 0; i < planets; i++) { const fr = (i + 1) / (planets + 1); pd.push({ orbitR: 35 + fr * 140 * scale, speed: eml(1 - fr, 1) * 0.25 * (0.5 + energy * 0.15), size: 3 + Math.sin(i * 2.7) * 2 + (1 - fr) * 3, hue: (hueShift + i * (360 / planets)) % 360, phase: i * 1.1 }); } }
    const pTrails = pd.map(() => []);
    const sigma = 10 * (0.8 + chaos * 0.08), rho = 28 * (0.7 + chaos * 0.12), beta = 8 / 3 * (0.9 + chaos * 0.04);
    let lx = 1, ly = 1, lz = 1; const dt = 0.004, cTrail = [];
    const primes = []; if (has("primes")) { let n = 2; while (primes.length < Math.min(primeCount, 60)) { if (isPrime(n)) primes.push(n); n++; } }
    const pStates = primes.map(p => ({ x: 1 + Math.sin(p) * 0.5, y: 1 + Math.cos(p) * 0.5, z: 1 + Math.sin(p * 1.3) * 0.5 }));
    const bg = isU ? "#020008" : "#06020F";
    ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h);
    if (has("galaxy") || has("solar")) { for (let i = 0; i < 130; i++) { ctx.beginPath(); ctx.arc(Math.random() * w, Math.random() * h, Math.random() * (isU ? 1.5 : 1), 0, Math.PI * 2); ctx.fillStyle = `rgba(255,255,255,${0.08 + Math.random() * 0.3})`; ctx.fill(); } }
    const go = () => {
      t.current += 0.016; const time = t.current;
      ctx.fillStyle = isU ? "rgba(2,0,8,0.04)" : "rgba(6,2,15,0.06)"; ctx.fillRect(0, 0, w, h);
      if (has("chaos") && !has("primes")) {
        for (let s = 0; s < 6; s++) { lx += sigma * (ly - lx) * dt; ly += (lx * (rho - lz) - ly) * dt; lz += (lx * ly - beta * lz) * dt; cTrail.push({ x: cx + lx * 6 * scale, y: cy - lz * 4.5 * scale + 90 }); if (cTrail.length > 2500) cTrail.shift(); }
        for (let i = 1; i < cTrail.length; i++) { const fr = i / cTrail.length; ctx.beginPath(); ctx.moveTo(cTrail[i - 1].x, cTrail[i - 1].y); ctx.lineTo(cTrail[i].x, cTrail[i].y); ctx.strokeStyle = `hsla(${(hueShift + fr * 120 + 60) % 360},70%,55%,${fr * 0.5})`; ctx.lineWidth = 0.4 + fr; ctx.stroke(); }
        if (cTrail.length) { const hd = cTrail[cTrail.length - 1]; const hg = ctx.createRadialGradient(hd.x, hd.y, 0, hd.x, hd.y, 12); hg.addColorStop(0, `hsla(${hueShift + 60},90%,80%,0.4)`); hg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = hg; ctx.beginPath(); ctx.arc(hd.x, hd.y, 12, 0, Math.PI * 2); ctx.fill(); }
      }
      if (has("solar")) {
        const sunR = 12 + Math.sin(time * 2) * 1.5; const sg = ctx.createRadialGradient(cx, cy, 0, cx, cy, sunR * 3); sg.addColorStop(0, `hsla(${hueShift + 30},90%,85%,0.7)`); sg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(cx, cy, sunR * 3, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(cx, cy, sunR, 0, Math.PI * 2); ctx.fillStyle = `hsla(${hueShift + 30},90%,80%,0.85)`; ctx.fill();
        pd.forEach((p, i) => {
          ctx.beginPath(); ctx.ellipse(cx, cy, p.orbitR, p.orbitR * 0.85, 0, 0, Math.PI * 2); ctx.strokeStyle = "rgba(139,92,246,0.06)"; ctx.lineWidth = 0.4; ctx.stroke();
          const angle = time * p.speed + p.phase, px = cx + Math.cos(angle) * p.orbitR, py = cy + Math.sin(angle) * p.orbitR * 0.85;
          pTrails[i].push({ x: px, y: py }); if (pTrails[i].length > 35) pTrails[i].shift();
          if (has("fractal") && pTrails[i].length > 3) { for (let j = 1; j < pTrails[i].length; j += 3) { const a = pTrails[i][j - 1], b = pTrails[i][Math.min(j + 2, pTrails[i].length - 1)]; if (Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2) > 6) { const segs = kochSegs(a.x, a.y, b.x, b.y, 1); segs.forEach((s, si) => { ctx.beginPath(); ctx.moveTo(s.x1, s.y1); ctx.lineTo(s.x2, s.y2); ctx.strokeStyle = `hsla(${(p.hue + si * 20) % 360},70%,60%,${0.1 + (j / pTrails[i].length) * 0.2})`; ctx.lineWidth = 0.4; ctx.stroke(); }); } }
          } else { for (let j = 1; j < pTrails[i].length; j++) { ctx.beginPath(); ctx.arc(pTrails[i][j].x, pTrails[i][j].y, p.size * 0.25, 0, Math.PI * 2); ctx.fillStyle = `hsla(${p.hue},70%,60%,${(j / pTrails[i].length) * 0.25})`; ctx.fill(); } }
          ctx.beginPath(); ctx.arc(px, py, p.size, 0, Math.PI * 2); ctx.fillStyle = `hsla(${p.hue},75%,60%,0.85)`; ctx.fill();
        });
      }
      if (has("galaxy")) {
        const maxP = 500, count = Math.min(maxP, Math.floor(time * 75));
        for (let i = 0; i < count; i++) { const fr = i / maxP, arm = i % arms, aa = (arm / arms) * 2 * Math.PI; let d = emlExp(fr * 2.2) * 13 * scale; const sp = aa + fr * (5 + energy) + time * (0.1 + energy * 0.04); const j = Math.sin(i * 13.7) * 4 + Math.cos(i * 7.3) * 4;
          let px = cx + Math.cos(sp) * d + j, py = cy + Math.sin(sp) * d * 0.55 + j * 0.5;
          if (has("waveform")) { const wd = Math.sin(fr * freq * Math.PI + time * 2) * 12 * scale; px += wd * Math.cos(sp + Math.PI / 2); py += wd * Math.sin(sp + Math.PI / 2) * 0.55; }
          const b = 0.3 + 0.7 * (1 - fr); let sz = 0.7 + (1 - fr) * 2.5; let hu = (hueShift + fr * 80 + arm * (360 / arms)) % 360;
          if (has("waveform")) { const sp2 = Math.sin(fr * freq * Math.PI + time * 4) * 0.3; hu = (hu + sp2 * 40) % 360; sz *= (1 + Math.abs(sp2) * 0.4); }
          ctx.beginPath(); ctx.arc(px, py, sz, 0, Math.PI * 2); ctx.fillStyle = `hsla(${hu},85%,${42 + b * 35}%,${b * 0.85})`; ctx.fill();
        }
        const cp = has("waveform") ? 1 + Math.sin(time * freq * 0.5) * 0.3 : 1;
        const cg = ctx.createRadialGradient(cx, cy, 0, cx, cy, (55 + energy * 8) * cp); cg.addColorStop(0, `hsla(${hueShift},70%,85%,0.3)`); cg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = cg; ctx.beginPath(); ctx.arc(cx, cy, (65 + energy * 10) * cp, 0, Math.PI * 2); ctx.fill();
      }
      if (has("fractal") && !has("solar")) {
        const curD = Math.min(depth, Math.floor(time * 0.55) + 1), r = Math.min(w, h) * 0.28 * scale;
        const verts = []; for (let i = 0; i < 3; i++) { const a = -Math.PI / 2 + (i * 2 * Math.PI) / 3 + time * 0.03 * energy * 0.3; verts.push({ x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r }); }
        let segs = []; for (let i = 0; i < 3; i++) { const n = (i + 1) % 3; segs = segs.concat(kochSegs(verts[i].x, verts[i].y, verts[n].x, verts[n].y, curD)); }
        const total = segs.length, show = Math.min(total, Math.floor(time * 110));
        for (let i = 0; i < show; i++) { const s = segs[i], fr = i / total; ctx.beginPath(); ctx.moveTo(s.x1, s.y1); ctx.lineTo(s.x2, s.y2); ctx.strokeStyle = `hsla(${(hueShift + fr * 140) % 360},75%,55%,${0.4 + Math.sin(time * 2 + fr * 12) * 0.3})`; ctx.lineWidth = Math.max(0.3, 2.2 - curD * 0.35); ctx.stroke(); }
      }
      if (has("waveform") && !has("galaxy")) {
        const cnt = 250, halfW = w * 0.44, amp = scale * 0.8;
        for (let layer = 2; layer >= 0; layer--) { ctx.beginPath(); for (let i = 0; i < cnt; i++) { const fr = i / cnt; const x = cx - halfW + fr * halfW * 2; let y = cy + Math.sin(fr * freq * Math.PI + time * 2 + layer * 0.3) * 50 * energy * 0.5 * amp + Math.sin(fr * freq * 0.7 * Math.PI + time * 1.4 + layer * 0.3) * 25 * energy * 0.3 * amp + Math.sin(fr * 11 + time * 3 + layer) * 12 * amp;
          if (has("chaos") && cTrail.length > 10) { const ci = Math.floor(fr * (cTrail.length - 1)); y += ((cTrail[ci]?.y || cy) - cy) * 0.15; }
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); } ctx.strokeStyle = `hsla(${(hueShift + layer * 40) % 360},85%,65%,${0.15 + (2 - layer) * 0.25})`; ctx.lineWidth = 1 + (2 - layer); ctx.stroke(); }
        for (let i = 0; i < cnt; i += 4) { const fr = i / cnt; const x = cx - halfW + fr * halfW * 2; let y = cy + Math.sin(fr * freq * Math.PI + time * 2) * 50 * energy * 0.5 * amp + Math.sin(fr * freq * 0.7 * Math.PI + time * 1.4) * 25 * energy * 0.3 * amp + Math.sin(fr * 11 + time * 3) * 12 * amp;
          if (has("chaos") && cTrail.length > 10) { const ci = Math.floor(fr * (cTrail.length - 1)); y += ((cTrail[ci]?.y || cy) - cy) * 0.15; }
          ctx.beginPath(); ctx.arc(x, y, 1 + Math.abs(Math.sin(fr * Math.PI)) * 3, 0, Math.PI * 2); ctx.fillStyle = `hsla(${(hueShift + fr * 90) % 360},95%,75%,0.7)`; ctx.fill(); }
      }
      if (has("primes")) {
        const vis = Math.min(primes.length, Math.floor(time * 10));
        primes.slice(0, vis).forEach((p, i) => { let px, py;
          if (has("chaos")) { const st = pStates[i]; st.x += sigma * (st.y - st.x) * dt * 0.5; st.y += (st.x * (rho - st.z) - st.y) * dt * 0.5; st.z += (st.x * st.y - beta * st.z) * dt * 0.5; px = cx + st.x * 5 * scale; py = cy - st.z * 3.5 * scale + 80; }
          else if (has("solar")) { const oR = 25 + Math.sqrt(p) * 10 * scale, sp = eml(1 - i / primes.length, 1) * 0.2 * (0.5 + energy * 0.1); px = cx + Math.cos(time * sp + p * 0.5) * oR; py = cy + Math.sin(time * sp + p * 0.5) * oR * 0.8; }
          else { const a = Math.sqrt(p) * 2.4 + time * energy * 0.08, d2 = Math.sqrt(p) * 8 * scale; px = cx + Math.cos(a) * d2; py = cy + Math.sin(a) * d2; }
          const hu = (hueShift + p * 7) % 360, sz = 2 + (1 / (1 + (p - 2) * 0.01)) * 6;
          ctx.beginPath(); ctx.arc(px, py, sz * 2, 0, Math.PI * 2); ctx.fillStyle = `hsla(${hu},80%,60%,0.06)`; ctx.fill();
          ctx.beginPath(); ctx.arc(px, py, sz, 0, Math.PI * 2); ctx.fillStyle = `hsla(${hu},85%,65%,${0.4 + Math.sin(time * 2 + p * 0.1) * 0.3})`; ctx.fill();
          if (p <= 19) { ctx.fillStyle = `hsla(${hu},70%,85%,0.65)`; ctx.font = "9px monospace"; ctx.textAlign = "center"; ctx.fillText(p.toString(), px, py - sz - 3); }
        });
      }
      if (isU) { const mh = (time * 30) % 360; const ug = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.min(w, h) * 0.48); ug.addColorStop(0, "rgba(0,0,0,0)"); ug.addColorStop(0.7, "rgba(0,0,0,0)"); ug.addColorStop(1, `hsla(${mh},70%,50%,0.08)`); ctx.fillStyle = ug; ctx.fillRect(0, 0, w, h); }
      f.current = requestAnimationFrame(go);
    };
    go(); return () => cancelAnimationFrame(f.current);
  }, [params, layers]);
  return <canvas ref={ref} width={680} height={460} style={{ width: "100%", height: "100%", display: "block" }} />;
}

export default function App() {
  const [brickPos, setBrickPos] = useState({ x: 340, y: 230 });
  const [dragging, setDragging] = useState(false);
  const [activeDemo, setActiveDemo] = useState(null);
  const [activeDemoLabel, setActiveDemoLabel] = useState("");
  const [activeDemoColor, setActiveDemoColor] = useState("#FDE68A");
  const [demoParams, setDemoParams] = useState(null);
  const [showWow, setShowWow] = useState(false);
  const [showMath, setShowMath] = useState(false);
  const [pulse, setPulse] = useState(0);
  const [introPhase, setIntroPhase] = useState(0);
  const [nearInfo, setNearInfo] = useState(null);
  const dragRef = useRef(false), offsetRef = useRef({ x: 0, y: 0 }), svgRef = useRef(null), audioRef = useRef(null);
  const activeLayers = useMemo(() => getLayers(activeDemo), [activeDemo]);

  useEffect(() => { setTimeout(() => setIntroPhase(1), 100); setTimeout(() => setIntroPhase(2), 900); }, []);
  useEffect(() => { let fr; const tick = () => { setPulse(p => p + 0.025); fr = requestAnimationFrame(tick); }; tick(); return () => cancelAnimationFrame(fr); }, []);
  useEffect(() => { if (!dragging) { setNearInfo(null); return; } setNearInfo(detectNearest(brickPos.x, brickPos.y)); }, [brickPos, dragging]);
  useEffect(() => {
    const onVisibility = () => { if (document.visibilityState === "hidden" && audioRef.current) { audioRef.current.stop(); audioRef.current = null; } };
    document.addEventListener("visibilitychange", onVisibility);
    return () => { document.removeEventListener("visibilitychange", onVisibility); if (audioRef.current) { audioRef.current.stop(); audioRef.current = null; } };
  }, []);

  const getPos = useCallback((e) => { const touch = e.touches?.length ? e.touches[0] : e.changedTouches?.length ? e.changedTouches[0] : e; const svg = svgRef.current; if (!svg) return { x: 0, y: 0 }; const rect = svg.getBoundingClientRect(); return { x: (touch.clientX - rect.left) * (680 / rect.width), y: (touch.clientY - rect.top) * (460 / rect.height) }; }, []);

  useEffect(() => {
    const move = (e) => { if (!dragRef.current) return; e.preventDefault(); const p = getPos(e); setBrickPos({ x: Math.max(30, Math.min(650, p.x - offsetRef.current.x)), y: Math.max(30, Math.min(430, p.y - offsetRef.current.y)) }); };
    const up = (e) => { if (!dragRef.current) return; dragRef.current = false; setDragging(false); const p = getPos(e); const bx = Math.max(30, Math.min(650, p.x - offsetRef.current.x)), by = Math.max(30, Math.min(430, p.y - offsetRef.current.y));
      const det = detectZone(bx, by); if (det) { const params = deriveParams(bx, by, 680, 460); setDemoParams(params); setActiveDemo(det.data.id); setActiveDemoLabel(det.data.label); setActiveDemoColor(det.data.color || "#FDE68A"); setShowWow(false); setShowMath(false); if (audioRef.current) audioRef.current.stop(); audioRef.current = createAmbient(det.data.id, params); } };
    window.addEventListener("mousemove", move); window.addEventListener("mouseup", up); window.addEventListener("touchmove", move, { passive: false }); window.addEventListener("touchend", up);
    return () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); window.removeEventListener("touchmove", move); window.removeEventListener("touchend", up); };
  }, [getPos]);

  const handleDown = (e) => {
    e.preventDefault();
    // Unlock AudioContext on first gesture — must happen synchronously in event handler
    try { const ac = getAC(); if (ac.state === "suspended") ac.resume(); } catch {}
    dragRef.current = true; setDragging(true); const p = getPos(e); offsetRef.current = { x: p.x - brickPos.x, y: p.y - brickPos.y };
  };
  const handleReset = () => { if (audioRef.current) audioRef.current.stop(); setActiveDemo(null); setDemoParams(null); setShowWow(false); setShowMath(false); setBrickPos({ x: 340, y: 230 }); };

  const liveParams = deriveParams(brickPos.x, brickPos.y, 680, 460);
  let eyeOffX = 0, eyeOffY = 0;
  if (dragging && nearInfo) { let tx, ty; if (nearInfo.type === "unified") { tx = HEX_CENTER.x; ty = HEX_CENTER.y; } else if (nearInfo.type === "triple") { const c = getTripleCenter(nearInfo.data); tx = c.x; ty = c.y; } else if (nearInfo.type === "double") { const z1 = ZONES.find(z => z.id === nearInfo.data.z1), z2 = ZONES.find(z => z.id === nearInfo.data.z2); tx = (z1.x + z2.x) / 2; ty = (z1.y + z2.y) / 2; } else { tx = nearInfo.data.x; ty = nearInfo.data.y; } const d = Math.sqrt((tx - brickPos.x) ** 2 + (ty - brickPos.y) ** 2) || 1; eyeOffX = ((tx - brickPos.x) / d) * 2.5; eyeOffY = ((ty - brickPos.y) / d) * 2; }
  const eyeScale = nearInfo && dragging ? (nearInfo.type === "unified" ? 1.6 : nearInfo.type === "triple" ? 1.45 : nearInfo.type === "double" ? 1.3 : 1.15) : 1;
  const smile = !nearInfo || !dragging ? "M-7 7 Q0 13 7 7" : nearInfo.type === "unified" ? "M-10 4 Q0 20 10 4" : nearInfo.type === "triple" ? "M-9 5 Q0 18 9 5" : "M-8 6 Q0 16 8 6";
  const sc = 1 + Math.sin(pulse * 2) * 0.03;
  const nearGlow = nearInfo ? nearInfo.data.glow || "139,92,246" : "139,92,246";
  const nearColor = nearInfo ? nearInfo.data.color || "#A78BFA" : "#A78BFA";
  const depthLabel = activeDemo === "unified" ? "∞" : TRIPLES.find(t => t.id === activeDemo) ? "3" : HYBRIDS.find(h => h.id === activeDemo) ? "2" : "1";

  return (
    <div style={{ fontFamily: "var(--font-sans,system-ui,sans-serif)", maxWidth: 720, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1.25rem 1rem 0.5rem", opacity: introPhase >= 2 ? 1 : 0, transition: "opacity 0.8s ease 0.3s" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#A78BFA", fontWeight: 500, marginBottom: 4 }}>monogate.dev</div>
        <h1 style={{ fontSize: 28, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary,#1a1a2e)" }}>Magic Brick Math</h1>
        <p style={{ fontSize: 20, fontFamily: "var(--font-mono,monospace)", color: "#7C3AED", fontWeight: 500, margin: "4px 0 0", letterSpacing: 1 }}>eml(x, y) = exp(x) − ln(y)</p>
      </div>

      <div onClick={() => { if (activeDemo && !showWow) { if (audioRef.current) { audioRef.current.stop(); audioRef.current = null; } setShowWow(true); } }}
        style={{ position: "relative", width: "100%", aspectRatio: "680/460", borderRadius: 16, overflow: "hidden", background: activeDemo ? "#06020F" : "var(--color-background-secondary,#f8f5ff)", border: activeDemo ? "none" : "0.5px solid var(--color-border-tertiary,rgba(0,0,0,0.1))", transition: "background 0.5s ease", marginTop: 8, cursor: activeDemo && !showWow ? "pointer" : "default" }}>

        {activeDemo && <ComposedDemo params={demoParams} layers={activeLayers} />}

        {!activeDemo && (
          <svg ref={svgRef} width="100%" height="100%" viewBox="0 0 680 460" style={{ position: "absolute", top: 0, left: 0, touchAction: "none" }}>
            {Array.from({ length: 14 }).map((_, i) => Array.from({ length: 10 }).map((_, j) => (<circle key={`${i}-${j}`} cx={i * 50 + 30} cy={j * 48 + 22} r="0.6" fill="var(--color-border-tertiary,#ccc)" opacity="0.3" />)))}

            {ZONES.map((z) => { const dist = Math.sqrt((brickPos.x - z.x) ** 2 + (brickPos.y - z.y) ** 2); const prox = Math.max(0, 1 - dist / (ZR * 2.5)); const op = dragging ? 0.1 + prox * 0.45 : 0; const isN = nearInfo?.type === "single" && nearInfo.data.id === z.id; const r = ZR + (isN ? 8 + Math.sin(pulse * 4) * 3 : 0);
              return (<g key={z.id}><circle cx={z.x} cy={z.y} r={r * 1.5} fill={`rgba(${z.glow},${op * 0.1})`} /><circle cx={z.x} cy={z.y} r={r} fill={`rgba(${z.glow},${op * 0.18})`} stroke={z.color} strokeWidth={isN ? 1.5 : 0.5} strokeOpacity={op * 0.6} /><text x={z.x} y={z.y + 4} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 12, fontFamily: "var(--font-sans)", fill: z.color, opacity: dragging ? 0.15 + prox * 0.75 : 0, fontWeight: isN ? 600 : 400 }}>{z.label}</text></g>); })}

            {dragging && HYBRIDS.map((h) => { const z1 = ZONES.find(z => z.id === h.z1), z2 = ZONES.find(z => z.id === h.z2); if (!z1 || !z2) return null; const mx = (z1.x + z2.x) / 2, my = (z1.y + z2.y) / 2; const d = Math.sqrt((brickPos.x - mx) ** 2 + (brickPos.y - my) ** 2); const prox = Math.max(0, 1 - d / 80); const isN = nearInfo?.type === "double" && nearInfo.data.id === h.id; if (prox < 0.03) return null;
              return (<g key={h.id}><circle cx={mx} cy={my} r={36 + (isN ? 5 + Math.sin(pulse * 5) * 3 : 0)} fill={`rgba(${h.glow},${prox * 0.25})`} stroke={h.color} strokeWidth={isN ? 1.8 : 0.6} strokeOpacity={prox * 0.7} strokeDasharray={isN ? "none" : "3 3"} />{isN && <text x={mx} y={my + 3} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 9, fontFamily: "var(--font-sans)", fill: h.color, fontWeight: 600 }}>{h.label}</text>}</g>); })}

            {dragging && TRIPLES.map((tri) => { const c = getTripleCenter(tri); const d = Math.sqrt((brickPos.x - c.x) ** 2 + (brickPos.y - c.y) ** 2); const prox = Math.max(0, 1 - d / 65); const isN = nearInfo?.type === "triple" && nearInfo.data.id === tri.id; if (prox < 0.03) return null;
              return (<g key={tri.id}><circle cx={c.x} cy={c.y} r={30 + (isN ? 6 + Math.sin(pulse * 6) * 3 : 0)} fill={`rgba(${tri.glow},${prox * 0.3})`} stroke={tri.color} strokeWidth={isN ? 2 : 0.8} strokeOpacity={prox * 0.8} />{isN && <><text x={c.x} y={c.y - 2} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 9, fontFamily: "var(--font-sans)", fill: tri.color, fontWeight: 600 }}>{tri.label}</text><text x={c.x} y={c.y + 10} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 7, fontFamily: "var(--font-mono)", fill: tri.color, opacity: 0.7 }}>depth 3</text></>}{isN && [0, 1, 2, 3, 4, 5, 6, 7].map(s => <circle key={s} cx={c.x + Math.cos((s / 8) * Math.PI * 2 + pulse * 3.5) * (34 + Math.sin(pulse * 4 + s) * 4)} cy={c.y + Math.sin((s / 8) * Math.PI * 2 + pulse * 3.5) * (34 + Math.sin(pulse * 4 + s) * 4)} r="2" fill={tri.color} opacity={0.4 + Math.sin(pulse * 6 + s) * 0.4} />)}</g>); })}

            {dragging && (() => { const d = Math.sqrt((brickPos.x - HEX_CENTER.x) ** 2 + (brickPos.y - HEX_CENTER.y) ** 2); const prox = Math.max(0, 1 - d / 65); const isN = nearInfo?.type === "unified"; if (prox < 0.02) return null; const mh = (pulse * 15) % 360;
              return (<g><circle cx={HEX_CENTER.x} cy={HEX_CENTER.y} r={28 + (isN ? 8 + Math.sin(pulse * 7) * 4 : 0)} fill={`hsla(${mh},70%,60%,${prox * 0.25})`} stroke={`hsl(${mh},80%,70%)`} strokeWidth={isN ? 2.5 : 1} strokeOpacity={prox * 0.9} />{isN && <><text x={HEX_CENTER.x} y={HEX_CENTER.y - 3} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 10, fontFamily: "var(--font-sans)", fill: "#FDE68A", fontWeight: 700 }}>the monogate</text><text x={HEX_CENTER.x} y={HEX_CENTER.y + 9} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 7, fontFamily: "var(--font-mono)", fill: "#FDE68A", opacity: 0.8 }}>depth ∞</text></>}{isN && [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map(s => <circle key={s} cx={HEX_CENTER.x + Math.cos((s / 12) * Math.PI * 2 + pulse * 4) * (32 + Math.sin(pulse * 5 + s) * 5)} cy={HEX_CENTER.y + Math.sin((s / 12) * Math.PI * 2 + pulse * 4) * (32 + Math.sin(pulse * 5 + s) * 5)} r="2.5" fill={`hsl(${(mh + s * 30) % 360},80%,70%)`} opacity={0.5 + Math.sin(pulse * 7 + s) * 0.4} />)}</g>); })()}

            {!dragging && introPhase >= 2 && ["exp", "ln", "π", "e", "sin", "cos", "√", "∑"].map((sym, i) => { const a = (i / 8) * Math.PI * 2 + pulse * 0.18; const prox = Math.sqrt((340 + Math.cos(a) * 200 - brickPos.x) ** 2 + (230 + Math.sin(a) * 150 - brickPos.y) ** 2); const att = Math.max(0, 1 - prox / 180); return <text key={sym} x={340 + Math.cos(a) * (200 - att * 80)} y={230 + Math.sin(a) * (150 - att * 60)} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 15 + att * 7, fontFamily: "var(--font-mono)", fill: "#A78BFA", opacity: 0.12 + att * 0.5 }}>{sym}</text>; })}

            <g onMouseDown={handleDown} onTouchStart={handleDown} style={{ cursor: dragging ? "grabbing" : "grab", touchAction: "none" }} transform={`translate(${brickPos.x},${brickPos.y + (introPhase === 0 ? -80 : introPhase === 1 ? 8 : 0)}) scale(${sc * (introPhase === 1 ? 1.1 : 1)})`}>
              <circle cx="0" cy="0" r={dragging ? 70 : 55} fill={`rgba(${nearGlow},${dragging ? 0.15 : 0.1})`} style={{ transition: "fill 0.3s" }} />
              <g style={{ transform: dragging ? "scale(1.08,0.94)" : "scale(1)", transformOrigin: "center", transition: "transform 0.15s" }}>
                <rect x="-26" y="-26" width="52" height="52" rx="9" fill="#7C3AED" stroke="#A78BFA" strokeWidth="2" />
                <rect x="-23" y="-23" width="46" height="21" rx="5" fill="#8B5CF6" opacity="0.45" />
                <rect x="-24" y="21" width="48" height="5" rx="2.5" fill="#6D28D9" />
                <circle cx={-9 + eyeOffX} cy={-4 + eyeOffY} r={4.5 * eyeScale} fill="#FDE68A" />
                <circle cx={9 + eyeOffX} cy={-4 + eyeOffY} r={4.5 * eyeScale} fill="#FDE68A" />
                <circle cx={-9 + eyeOffX * 1.3} cy={-5.5 + eyeOffY * 1.2} r="1.8" fill="#1E1B4B" />
                <circle cx={9 + eyeOffX * 1.3} cy={-5.5 + eyeOffY * 1.2} r="1.8" fill="#1E1B4B" />
                <path d={smile} fill="none" stroke="#FDE68A" strokeWidth="2.2" strokeLinecap="round" />
              </g>
              {nearInfo && dragging && [0, 1, 2].map(s => <circle key={s} cx={Math.cos((s / 3) * Math.PI * 2 + pulse * 3) * 35} cy={Math.sin((s / 3) * Math.PI * 2 + pulse * 3) * 35} r={nearInfo.type === "unified" ? 4 : nearInfo.type === "triple" ? 3 : 2} fill={nearColor} opacity={0.5 + Math.sin(pulse * 5 + s) * 0.4} />)}
            </g>

            {!dragging && introPhase >= 2 && <text x={brickPos.x} y={brickPos.y + 50} textAnchor="middle" style={{ fontSize: 12, fill: "var(--color-text-secondary,#999)", fontFamily: "var(--font-sans)" }}>drag me — zones, overlaps, and the center</text>}
          </svg>
        )}

        {!activeDemo && dragging && (
          <div style={{ position: "absolute", left: brickPos.x > 400 ? "12px" : "auto", right: brickPos.x <= 400 ? "12px" : "auto", top: brickPos.y > 300 ? "12px" : "auto", bottom: brickPos.y <= 300 ? "12px" : "auto", zIndex: 15, pointerEvents: "none", fontFamily: "var(--font-mono,monospace)", fontSize: 11, lineHeight: 1.9, color: "#A78BFA", background: "rgba(15,5,40,0.8)", backdropFilter: "blur(4px)", padding: "8px 12px", borderRadius: 10, border: "1px solid rgba(139,92,246,0.2)", minWidth: 210 }}>
            <div style={{ fontSize: 9, color: "#7C3AED", letterSpacing: 1, textTransform: "uppercase", marginBottom: 2 }}>{nearInfo?.type === "unified" ? "unified · depth ∞" : nearInfo?.type === "triple" ? "triple · depth 3" : nearInfo?.type === "double" ? "hybrid · depth 2" : "live · eml"}</div>
            <div style={{ display: "flex", justifyContent: "space-between" }}><span style={{ color: "#8B5CF6" }}>pos</span><span style={{ color: "#C4B5FD" }}>({liveParams.nx.toFixed(2)}, {liveParams.ny.toFixed(2)})</span></div>
            <div style={{ display: "flex", justifyContent: "space-between" }}><span style={{ color: "#8B5CF6" }}>eml(x,y)</span><span style={{ color: "#FDE68A", fontWeight: 500 }}>{liveParams.raw.emlPos.toFixed(4)}</span></div>
            <div style={{ display: "flex", justifyContent: "space-between" }}><span style={{ color: "#8B5CF6" }}>energy</span><span style={{ color: "#FDE68A", fontWeight: 500 }}>{liveParams.raw.emlEnergy.toFixed(3)}</span></div>
            <div style={{ display: "flex", justifyContent: "space-between" }}><span style={{ color: "#8B5CF6" }}>hue</span><span style={{ color: `hsl(${liveParams.hueShift},80%,65%)`, fontWeight: 500 }}>{liveParams.hueShift.toFixed(0)}°</span></div>
            {nearInfo && (<div style={{ borderTop: "1px solid rgba(139,92,246,0.25)", marginTop: 3, paddingTop: 3 }}><div style={{ color: nearColor, fontSize: 10, fontWeight: 600 }}>{nearInfo.data.label}</div>{nearInfo.data.desc && <div style={{ fontSize: 8, color: "#C4B5FD" }}>{nearInfo.data.desc}</div>}</div>)}
          </div>
        )}

        {activeDemo && !showWow && showMath && (<div style={{ position: "absolute", bottom: 50, left: 12, zIndex: 20, pointerEvents: "none" }}><EquationLog params={demoParams} mode={activeDemo} /></div>)}
        {activeDemo && !showWow && (<div style={{ position: "absolute", bottom: 12, right: 12, zIndex: 20, pointerEvents: "auto" }}><button onClick={(e) => { e.stopPropagation(); setShowMath(m => !m); }} style={{ background: showMath ? "rgba(139,92,246,0.4)" : "rgba(15,5,40,0.8)", border: "1px solid rgba(139,92,246,0.5)", color: showMath ? "#FDE68A" : "#A78BFA", borderRadius: 8, padding: "7px 14px", fontSize: 11, fontFamily: "var(--font-mono,monospace)", cursor: "pointer", backdropFilter: "blur(4px)" }}>{showMath ? "✕ hide math" : "{ } behind the magic"}</button></div>)}
        {activeDemo && !showWow && (<div style={{ position: "absolute", top: 12, right: 12, zIndex: 20, pointerEvents: "none", fontSize: 11, color: "rgba(167,139,250,0.4)", fontFamily: "var(--font-sans)" }}>tap anywhere when done</div>)}

        {showWow && (<div onClick={(e) => e.stopPropagation()} style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.65)", zIndex: 10, animation: "fadeIn 0.6s ease" }}>
          <div style={{ fontSize: activeDemo === "unified" ? 30 : 26, fontWeight: 600, color: "#FDE68A", textAlign: "center", lineHeight: 1.3, textShadow: "0 0 50px rgba(253,230,138,0.3)" }}>
            {activeDemo === "unified" ? <>The Monogate<br /><span style={{ fontSize: 18, fontWeight: 400 }}>All six. One brick. One equation.</span></> : depthLabel === "3" ? <>Three layers deep.<br />One brick made this.</> : depthLabel === "2" ? <>Two zones. One brick.<br />A new creation emerged.</> : <>All of this was made with<br />just ONE magic brick!</>}
          </div>
          <div style={{ fontSize: 14, color: activeDemoColor, marginTop: 8, fontWeight: 600 }}>{activeDemoLabel}</div>
          <div style={{ fontSize: 11, color: "#A78BFA", marginTop: 6, fontFamily: "var(--font-mono)", textAlign: "center", lineHeight: 1.9 }}>
            eml({demoParams?.nx.toFixed(2)}, {Math.abs(demoParams?.ny + 0.01).toFixed(2)}) = {demoParams?.raw.emlPos.toFixed(4)}<br />composition depth: {depthLabel}
          </div>
          <button onClick={handleReset} style={{ marginTop: 16, padding: "10px 32px", background: "#7C3AED", color: "white", border: "none", borderRadius: 99, fontSize: 14, fontWeight: 500, cursor: "pointer" }}>Try again ↻</button>
        </div>)}
      </div>

      {!activeDemo && introPhase >= 2 && (<p style={{ textAlign: "center", fontSize: 13, color: "var(--color-text-secondary,#888)", margin: "10px 0 0", lineHeight: 1.6 }}>
        {dragging ? nearInfo ? nearInfo.type === "unified" ? <span style={{ color: "#FDE68A", fontWeight: 600 }}>Release → THE MONOGATE (all six!)</span> : nearInfo.type === "triple" ? <span style={{ color: nearColor, fontWeight: 500 }}>Release → {nearInfo.data.label} (triple!)</span> : nearInfo.type === "double" ? <span style={{ color: nearColor, fontWeight: 500 }}>Release → {nearInfo.data.label} (hybrid)</span> : `Release here → ${nearInfo.data.label}` : "Drag toward a zone — overlap for hybrids, center for everything" : "Grab the brick — zones, overlaps, triples, and the center"}
      </p>)}

      {!activeDemo && (<div style={{ padding: "1rem 1.25rem", marginTop: 14, background: "var(--color-background-secondary,#faf5ff)", borderRadius: 12, border: "0.5px solid var(--color-border-tertiary,rgba(0,0,0,0.06))" }}>
        <div style={{ fontSize: 11, fontWeight: 500, color: "#7C3AED", marginBottom: 6, letterSpacing: 1.5, textTransform: "uppercase" }}>Composition is the point</div>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary,#555)", margin: "0 0 8px", lineHeight: 1.7 }}>
          The EML operator works by feeding itself into itself: <code style={{ background: "var(--color-background-primary,white)", padding: "1px 5px", borderRadius: 4, fontFamily: "var(--font-mono)", fontSize: 12 }}>eml(eml(eml(...)))</code>. Each layer creates something new. Drop in a zone (depth 1), overlap two (depth 2), find triple overlaps (depth 3), or the dead center — the Monogate — all six at once (depth ∞).
        </p>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary,#555)", margin: 0, lineHeight: 1.7 }}>One brick. One equation. Infinite depth.</p>
      </div>)}

      <div style={{ textAlign: "center", marginTop: 14, fontSize: 12, color: "var(--color-text-secondary,#999)" }}>
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#7C3AED", textDecoration: "none", fontWeight: 500 }}>monogate.dev</a>{" · "}<a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none" }}>arXiv:2603.21852</a>
      </div>
      <style>{`@keyframes fadeIn{from{opacity:0}to{opacity:1}}`}</style>
    </div>
  );
}
