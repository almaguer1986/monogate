import { useState, useRef, useEffect, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════════
// STRATA WORLD DATA
// ═══════════════════════════════════════════════════════════════════
// EML-k census from §41 — 23 functions classified by minimum approximation depth.
// MSE floors are measured results from arXiv:2603.21852.
const STRATA_DATA = [
  { id: 0, name: "Constants", label: "EML-0", y: 0, h: 450, bg: [15, 23, 42], accent: [100, 116, 139], color: "#64748B",
    terrain: "grid", desc: "Constants and closed-form values. Depth 0 — no variable nodes needed.",
    objects: [
      { name: "1", note: "The seed. Starting constant for all constructions.", formula: "the constant", x: 80 },
      { name: "0", note: "ZERO = eml(1, eml(eml(1,1), 1)). Three nodes.", formula: "additive identity", x: 200 },
      { name: "e", note: "eml(1,1) = exp(1) − ln(1) = e. One node.", formula: "2.71828...", x: 340 },
      { name: "ℤ", note: "Integers from iterated EML addition.", formula: "..., -2, -1, 0, 1, 2, ...", x: 480 },
      { name: "ℚ", note: "Rationals from integer division.", formula: "p/q", x: 600 },
    ]},
  { id: 1, name: "Exponential", label: "EML-1", y: 450, h: 450, bg: [12, 27, 42], accent: [6, 182, 212], color: "#06B6D4",
    terrain: "curves", desc: "Functions with MSE floor reaching machine precision at N=1. One EML node suffices.",
    objects: [
      { name: "exp(x)", note: "eml(x,1). One node. MSE → 0 exactly.", formula: "eml(x, 1)", x: 80 },
      { name: "exp(−x)", note: "DEML gate: exp(−x) − ln(1) in 1 node (§19).", formula: "deml(x, 1)", x: 200 },
      { name: "exp(x²)", note: "Gaussian envelope. 2 nodes via DEML.", formula: "exp(x²)", x: 340 },
      { name: "xⁿ", note: "Polynomials. exp(n·ln(x)) — 2-3 nodes.", formula: "exp(n·ln(x))", x: 480 },
      { name: "sinh(x)", note: "EML-1: (exp(x)−exp(−x))/2. Census §41.", formula: "MSE floor: ~0", x: 600 },
      { name: "cosh(x)", note: "EML-1: (exp(x)+exp(−x))/2. Census §41.", formula: "MSE floor: ~0", x: 160 },
      { name: "x²", note: "EML-1 in census (§41). N=3 singularity target.", formula: "MSE floor: ~0", x: 530 },
    ]},
  { id: 2, name: "Logarithmic", label: "EML-2", y: 900, h: 600, bg: [19, 13, 36], accent: [139, 92, 246], color: "#8B5CF6",
    terrain: "spirals", desc: "Functions requiring the logarithm. EML-2 in census §41.",
    objects: [
      { name: "ln(x)", note: "4-node construction (Log Recovery T04). MSE → 0.", formula: "eml(1, eml(eml(1,x), 1))", x: 80 },
      { name: "√x", note: "exp(½·ln(x)). EML-2 via log recovery.", formula: "MSE floor: ~0", x: 200 },
      { name: "1/x", note: "exp(−ln(x)). EML-2.", formula: "MSE floor: ~0", x: 340 },
      { name: "x·ln(x)", note: "EML-2. Basis of Shannon entropy.", formula: "MSE floor: ~0", x: 480 },
      { name: "H(p)", note: "−p·ln(p) Shannon entropy. Mathematical function.", formula: "S = -Σ p·ln(p)", x: 600 },
      { name: "F = −kT ln Z", note: "Helmholtz free energy. Thermodynamics function.", formula: "−kT ln(Z)", x: 120 },
      { name: "S(ρ)", note: "Von Neumann entropy −Tr(ρ·ln ρ). EML-2.", formula: "-Tr(ρ ln ρ)", x: 310 },
    ]},
  { id: 3, name: "Oscillatory", label: "EML-3", y: 1500, h: 500, bg: [26, 13, 24], accent: [236, 72, 153], color: "#EC4899",
    terrain: "waves", desc: "Functions requiring the complex bypass (T03). The N=3 singularity: 1.4M× MSE improvement at depth 3. This stratum seals itself.",
    objects: [
      { name: "sin(x)", note: "T01+T03. Infinite real nodes, 1 complex. MSE: 4.1e-9 at N=3 (1.4M× over N=2).", formula: "Im(eml(ix, 1))", x: 80 },
      { name: "cos(x)", note: "Re(eml(ix,1)). Same barrier as sin. Census §41.", formula: "Re(eml(ix, 1))", x: 200 },
      { name: "tanh(x)", note: "EML-3 in census. MSE floor ~4e-9.", formula: "(e^2x−1)/(e^2x+1)", x: 340 },
      { name: "erf(x)", note: "EML-3 in census §41. MSE floor ~4e-9.", formula: "2/√π ∫₀ˣ e^{-t²}dt", x: 480 },
      { name: "Fourier", note: "Density theorem (§36): EML atoms converge to any smooth function.", formula: "F̂(ξ) = ∫f·e^{-2πixξ}dx", x: 600 },
      { name: "lgamma", note: "log-Gamma. EML-3 in census §41.", formula: "ln(Γ(x))", x: 140 },
      { name: "wave eq", note: "sin/cos solutions. EML-3 because solution space is.", formula: "∂²u/∂t² = c²∇²u", x: 290 },
      { name: "ψ(x,t)", note: "Plane wave e^{ikx}. Complex EML-3.", formula: "iℏ∂ψ/∂t = Ĥψ", x: 440 },
    ]},
  { id: "inf", name: "Non-constructible", label: "EML-∞", y: 2100, h: 600, bg: [26, 20, 8], accent: [253, 230, 138], color: "#FDE68A",
    terrain: "chaos", desc: "Functions with infinite zeros on bounded intervals. No finite real EML tree can approximate them — T01, proved. N=12: 1.7 billion trees searched, zero candidates found.",
    objects: [
      { name: "|sin(x)|", note: "Non-analytic kink. EML-∞ in census §41. MSE floor never drops.", formula: "|sin(x)|", x: 80 },
      { name: "|x|", note: "Non-analytic at 0. Kink prevents finite EML approximation.", formula: "|x|", x: 200 },
      { name: "sign(x)", note: "Discontinuous. EML-∞.", formula: "x/|x|", x: 340 },
      { name: "sawtooth", note: "Discontinuous periodic. EML-∞.", formula: "x − ⌊x⌋", x: 480 },
      { name: "⌊x⌋", note: "Floor function. Discontinuous. EML-∞.", formula: "floor(x)", x: 600 },
      { name: "Heaviside", note: "Step function. Discontinuous. EML-∞.", formula: "H(x)", x: 130 },
      { name: "|sin| over ℝ open", note: "EML Weierstrass proved for smooth f. |sin| open — non-analytic case.", formula: "conjecture", x: 350 },
    ]},
];

const WALL_Y = 2000;
const GAP_PROOFS = [
  "T01 — Infinite Zeros Barrier: any finite real EML tree is real-analytic,\nso it has finitely many zeros. sin(x) has infinitely many. QED.",
  "N=12 exhaustive search: 1,704,034,304 trees. Zero sin(x) candidates found.\nThe barrier is not just structural — it is computational.",
  "EML-k census §41: functions cluster into EML-1/2/3/∞ with measured MSE floors.\nNo function fills the EML-4 slot. The gap is real.",
  "T03 — Euler Gateway: sin(x) = Im(eml(ix,1)). Over ℂ, 1 node.\nOver ℝ, ∞ nodes. The field determines the depth.",
  "EML Pumping Lemma: depth-k trees have at most 2^k zeros.\nsin has ∞ zeros on any interval. Requires infinite k. Proved.",
];

// ═══════════════════════════════════════════════════════════════════
// WORLD RENDERER
// ═══════════════════════════════════════════════════════════════════
function WorldCanvas({ scrollY, brickX, brickWorldY, discovered, wallHits, wallOpen, pulse }) {
  const ref = useRef(null), f = useRef(null), t = useRef(0);

  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d");
    const w = c.width, h = c.height;

    const go = () => {
      t.current += 0.016; const time = t.current;
      ctx.clearRect(0, 0, w, h);

      const viewTop = scrollY;
      const viewBottom = scrollY + h;

      // Render each stratum that's visible
      STRATA_DATA.forEach(stratum => {
        const sTop = stratum.y - viewTop;
        const sBottom = sTop + stratum.h;
        if (sBottom < -50 || sTop > h + 50) return; // Off screen

        const [br, bg, bb] = stratum.bg;
        const [ar, ag, ab] = stratum.accent;

        // Background gradient for this stratum
        const grad = ctx.createLinearGradient(0, Math.max(0, sTop), 0, Math.min(h, sBottom));
        grad.addColorStop(0, `rgb(${br},${bg},${bb})`);
        grad.addColorStop(1, `rgb(${Math.max(0, br - 5)},${Math.max(0, bg - 5)},${Math.max(0, bb - 5)})`);
        ctx.fillStyle = grad;
        ctx.fillRect(0, Math.max(0, sTop), w, Math.min(h, sBottom) - Math.max(0, sTop));

        // Terrain
        if (stratum.terrain === "grid") {
          for (let i = 0; i < 18; i++) for (let j = 0; j < Math.ceil(stratum.h / 40); j++) {
            const x = 20 + i * 38, y = sTop + 20 + j * 40;
            if (y < -5 || y > h + 5) continue;
            ctx.beginPath(); ctx.arc(x, y, 1.2 + Math.sin(time * 0.5 + i * 0.3 + j * 0.5) * 0.3, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${ar},${ag},${ab},${0.15 + Math.sin(time + i + j) * 0.05})`; ctx.fill();
          }
        } else if (stratum.terrain === "curves") {
          for (let curve = 0; curve < 6; curve++) {
            ctx.beginPath();
            for (let i = 0; i < 120; i++) {
              const frac = i / 120;
              const x = frac * w;
              const baseY = sTop + stratum.h * 0.3 + curve * 35;
              const y = baseY - Math.exp(frac * 2 - 0.5) * 6 * Math.sin(time * 0.2 + curve * 0.7);
              if (y < sTop - 10 || y > sBottom + 10) continue;
              if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.strokeStyle = `rgba(${ar},${ag},${ab},${0.08 + curve * 0.02})`; ctx.lineWidth = 1; ctx.stroke();
          }
        } else if (stratum.terrain === "spirals") {
          for (let sp = 0; sp < 3; sp++) {
            const scx = w * (0.25 + sp * 0.25), scy = sTop + stratum.h / 2;
            if (scy < -100 || scy > h + 100) continue;
            ctx.beginPath();
            for (let i = 0; i < 150; i++) {
              const frac = i / 150;
              const angle = frac * Math.PI * 5 + sp * 2 + time * 0.15;
              const radius = 3 + Math.log(1 + frac * 15) * 18;
              const x = scx + Math.cos(angle) * radius, y = scy + Math.sin(angle) * radius;
              if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.strokeStyle = `rgba(${ar},${ag},${ab},0.12)`; ctx.lineWidth = 1; ctx.stroke();
          }
          // Ghost 25.7%
          const ty = sTop + stratum.h / 2;
          if (ty > -30 && ty < h + 30) {
            ctx.fillStyle = `rgba(${ar},${ag},${ab},0.04)`;
            ctx.font = "bold 50px var(--font-mono, monospace)"; ctx.textAlign = "center";
            ctx.fillText("25.7%", w / 2, ty + 15);
          }
        } else if (stratum.terrain === "waves") {
          for (let wave = 0; wave < 5; wave++) {
            ctx.beginPath();
            for (let i = 0; i < 160; i++) {
              const frac = i / 160;
              const x = frac * w;
              const freq = 3 + wave * 1.5;
              const y = sTop + stratum.h * 0.5 + Math.sin(frac * Math.PI * freq + time * (0.8 + wave * 0.3)) * (25 - wave * 3)
                + Math.sin(frac * Math.PI * freq * 1.6 + time) * 8;
              if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.strokeStyle = `rgba(${ar},${ag},${ab},${0.15 - wave * 0.02})`; ctx.lineWidth = 1.5 - wave * 0.2; ctx.stroke();
          }
        } else if (stratum.terrain === "chaos") {
          const sigma = 10, rho = 28, beta = 8 / 3;
          let lx = Math.sin(time * 0.05) * 3, ly = Math.cos(time * 0.05) * 3, lz = 1;
          const ccx = w / 2, ccy = sTop + stratum.h * 0.45;
          if (ccy > -100 && ccy < h + 100) {
            ctx.beginPath();
            for (let i = 0; i < 500; i++) {
              const dt = 0.006;
              lx += sigma * (ly - lx) * dt; ly += (lx * (rho - lz) - ly) * dt; lz += (lx * ly - beta * lz) * dt;
              const x = ccx + lx * 5, y = ccy - lz * 3 + 40;
              if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.strokeStyle = `rgba(${ar},${ag},${ab},0.12)`; ctx.lineWidth = 0.8; ctx.stroke();
          }
        }

        // Stratum label
        const labelY = sTop + 25;
        if (labelY > -20 && labelY < h + 20) {
          ctx.fillStyle = `rgba(${ar},${ag},${ab},0.15)`;
          ctx.font = "bold 14px var(--font-mono, monospace)"; ctx.textAlign = "left";
          ctx.fillText(`${stratum.label} — ${stratum.name}`, 14, labelY);
        }

        // Stratum divider line
        if (sTop > 5 && sTop < h - 5) {
          ctx.beginPath(); ctx.moveTo(0, sTop); ctx.lineTo(w, sTop);
          ctx.strokeStyle = `rgba(${ar},${ag},${ab},0.15)`; ctx.lineWidth = 0.5; ctx.setLineDash([4, 8]); ctx.stroke(); ctx.setLineDash([]);
        }

        // Objects
        stratum.objects.forEach((obj, i) => {
          const oy = sTop + 60 + Math.floor(i / 4) * 60 + (stratum.id === 2 ? 40 : 0);
          if (oy < -30 || oy > h + 30) return;
          const isDisc = discovered.includes(`${stratum.id}:${obj.name}`);
          const ox = obj.x;
          const bobble = Math.sin(time * 1.2 + i * 1.5) * 4;

          // Glow
          if (isDisc) {
            ctx.beginPath(); ctx.arc(ox, oy + bobble, 18, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${ar},${ag},${ab},0.06)`; ctx.fill();
          }
          // Orb
          ctx.beginPath(); ctx.arc(ox, oy + bobble, isDisc ? 10 : 7, 0, Math.PI * 2);
          ctx.fillStyle = isDisc ? `rgba(${ar},${ag},${ab},0.6)` : `rgba(${ar},${ag},${ab},0.15)`;
          ctx.fill();
          ctx.strokeStyle = `rgba(${ar},${ag},${ab},${isDisc ? 0.8 : 0.2})`; ctx.lineWidth = 1; ctx.stroke();
          // Label
          ctx.fillStyle = `rgba(${ar},${ag},${ab},${isDisc ? 0.8 : 0.25})`;
          ctx.font = `${isDisc ? "bold " : ""}11px var(--font-mono, monospace)`; ctx.textAlign = "center";
          ctx.fillText(isDisc ? obj.name : "?", ox, oy + bobble + 24);
        });
      });

      // ─── THE WALL ───
      const wallScreenY = WALL_Y - viewTop;
      if (wallScreenY > -60 && wallScreenY < h + 60) {
        const wallIntensity = Math.min(1, wallHits * 0.15);
        // Wall glow
        const wg = ctx.createLinearGradient(0, wallScreenY - 40, 0, wallScreenY + 40);
        wg.addColorStop(0, "rgba(0,0,0,0)");
        wg.addColorStop(0.5, `rgba(239,68,68,${0.1 + wallIntensity * 0.2 + Math.sin(time * 3) * 0.05})`);
        wg.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = wg; ctx.fillRect(0, wallScreenY - 40, w, 80);
        // Wall line
        ctx.beginPath(); ctx.moveTo(0, wallScreenY); ctx.lineTo(w, wallScreenY);
        ctx.strokeStyle = `rgba(239,68,68,${0.3 + wallIntensity * 0.4 + Math.sin(time * 4) * 0.1})`; ctx.lineWidth = 2 + wallIntensity; ctx.stroke();
        // Fracture lines (more with more hits)
        for (let i = 0; i < Math.min(wallHits * 2, 12); i++) {
          const fx = (i / 12) * w + Math.sin(i * 7) * 30;
          const fy = wallScreenY + Math.sin(time * 2 + i) * (8 + wallHits * 2);
          const fl = 10 + wallHits * 3 + Math.sin(time + i * 3) * 5;
          const fa = Math.random() * Math.PI * 2;
          ctx.beginPath(); ctx.moveTo(fx, fy); ctx.lineTo(fx + Math.cos(fa) * fl, fy + Math.sin(fa) * fl);
          ctx.strokeStyle = `rgba(239,68,68,${0.1 + wallIntensity * 0.2})`; ctx.lineWidth = 1; ctx.stroke();
        }
        // Label
        if (wallHits > 0) {
          ctx.fillStyle = `rgba(239,68,68,${0.3 + wallIntensity * 0.4})`;
          ctx.font = "bold 12px var(--font-mono, monospace)"; ctx.textAlign = "center";
          ctx.fillText(wallOpen ? "The way is open — understanding dissolves the wall" : wallHits > 2 ? "Brute force won't work. Understand the stratum above." : "Something blocks the way...", w / 2, wallScreenY - 12);
        }
      }

      // ─── PLAYER BRICK ───
      const brickScreenY = brickWorldY - viewTop;
      const bs = 18;
      // Glow
      ctx.beginPath(); ctx.arc(brickX, brickScreenY, 28, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(124,58,237,0.1)"; ctx.fill();
      // Body
      ctx.fillStyle = "#7C3AED";
      ctx.beginPath();
      ctx.roundRect(brickX - bs / 2, brickScreenY - bs / 2, bs, bs, 4);
      ctx.fill();
      ctx.strokeStyle = "#A78BFA"; ctx.lineWidth = 1.5; ctx.stroke();
      // Face
      ctx.fillStyle = "#FDE68A";
      ctx.beginPath(); ctx.arc(brickX - 4, brickScreenY - 2, 2.5, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(brickX + 4, brickScreenY - 2, 2.5, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "#1E1B4B";
      ctx.beginPath(); ctx.arc(brickX - 4, brickScreenY - 2.5, 1, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(brickX + 4, brickScreenY - 2.5, 1, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath();
      ctx.moveTo(brickX - 3, brickScreenY + 3);
      ctx.quadraticCurveTo(brickX, brickScreenY + 6, brickX + 3, brickScreenY + 3);
      ctx.strokeStyle = "#FDE68A"; ctx.lineWidth = 1.5; ctx.lineCap = "round"; ctx.stroke();

      f.current = requestAnimationFrame(go);
    };
    go(); return () => cancelAnimationFrame(f.current);
  }, [scrollY, brickX, brickWorldY, discovered, wallHits, wallOpen, pulse]);

  return <canvas ref={ref} width={680} height={500} style={{ width: "100%", height: "100%", display: "block" }} />;
}

// ═══════════════════════════════════════════════════════════════════
// MAIN GAME
// ═══════════════════════════════════════════════════════════════════
export default function Strata() {
  const [brickX, setBrickX] = useState(340);
  const [brickWorldY, setBrickWorldY] = useState(200);
  const [scrollY, setScrollY] = useState(0);
  const [discovered, setDiscovered] = useState([]);
  const [selectedObj, setSelectedObj] = useState(null);
  const [wallHits, setWallHits] = useState(0);
  const [gapProofs, setGapProofs] = useState(0);
  const [pulse, setPulse] = useState(0);
  const [keys, setKeys] = useState({});
  const [touchStart, setTouchStart] = useState(null);
  const [visitedStrata, setVisitedStrata] = useState([0]);
  const [milestone, setMilestone] = useState(null); // temporary message
  const [wallUnderstood, setWallUnderstood] = useState(false); // true when all EML-3 objects found
  const gameRef = useRef(null);
  const milestoneTimer = useRef(null);

  useEffect(() => { let fr; const tick = () => { setPulse(p => p + 0.025); fr = requestAnimationFrame(tick); }; tick(); return () => cancelAnimationFrame(fr); }, []);

  // Check if all EML-3 objects are discovered
  const eml3Objects = STRATA_DATA.find(s => s.id === 3)?.objects || [];
  const eml3Found = eml3Objects.filter(o => discovered.includes(`3:${o.name}`)).length;
  const eml3Complete = eml3Found === eml3Objects.length;

  // When EML-3 is complete, understand the wall
  useEffect(() => {
    if (eml3Complete && !wallUnderstood) {
      setWallUnderstood(true);
      showMilestone("The oscillatory stratum is complete. The wall makes sense now.");
    }
  }, [eml3Complete, wallUnderstood]);

  const showMilestone = (msg) => {
    setMilestone(msg);
    if (milestoneTimer.current) clearTimeout(milestoneTimer.current);
    milestoneTimer.current = setTimeout(() => setMilestone(null), 4000);
  };

  useEffect(() => { let fr; const tick = () => { setPulse(p => p + 0.025); fr = requestAnimationFrame(tick); }; tick(); return () => cancelAnimationFrame(fr); }, []);

  // Keyboard controls
  useEffect(() => {
    const down = (e) => { setKeys(k => ({ ...k, [e.key]: true })); e.preventDefault(); };
    const up = (e) => { setKeys(k => ({ ...k, [e.key]: false })); };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    return () => { window.removeEventListener("keydown", down); window.removeEventListener("keyup", up); };
  }, []);

  // Touch controls
  const handleTouchStart = (e) => {
    const t = e.touches[0];
    const rect = gameRef.current?.getBoundingClientRect();
    if (!rect) return;
    setTouchStart({ x: t.clientX - rect.left, y: t.clientY - rect.top });
  };
  const handleTouchMove = (e) => {
    if (!touchStart) return;
    e.preventDefault();
    const t = e.touches[0];
    const rect = gameRef.current?.getBoundingClientRect();
    if (!rect) return;
    const dx = (t.clientX - rect.left) - touchStart.x;
    const dy = (t.clientY - rect.top) - touchStart.y;
    setTouchStart({ x: t.clientX - rect.left, y: t.clientY - rect.top });
    setBrickX(x => Math.max(20, Math.min(660, x + dx * 0.5)));
    setBrickWorldY(y => {
      let newY = y + dy * 1.5;
      if (newY > WALL_Y - 15 && newY < WALL_Y + 100) {
        if (dy > 0) {
          if (wallUnderstood) return newY; // pass through
          setWallHits(h => h + 1);
          return WALL_Y - 15;
        }
      }
      return Math.max(30, Math.min(wallUnderstood ? 2650 : WALL_Y - 15, newY));
    });
  };
  const handleTouchEnd = () => setTouchStart(null);

  // Movement loop
  useEffect(() => {
    const speed = 3;
    const interval = setInterval(() => {
      let dx = 0, dy = 0;
      if (keys["ArrowLeft"] || keys["a"]) dx -= speed;
      if (keys["ArrowRight"] || keys["d"]) dx += speed;
      if (keys["ArrowUp"] || keys["w"]) dy -= speed;
      if (keys["ArrowDown"] || keys["s"]) dy += speed;
      if (dx === 0 && dy === 0) return;

      setBrickX(x => Math.max(20, Math.min(660, x + dx)));
      setBrickWorldY(y => {
        let newY = y + dy;
        // Wall collision
        if (newY > WALL_Y - 15 && newY < WALL_Y + 100 && dy > 0) {
          if (wallUnderstood) return newY; // understood = pass through
          setWallHits(h => h + 1);
          return WALL_Y - 15;
        }
        return Math.max(30, Math.min(wallUnderstood ? 2650 : WALL_Y - 15, newY));
      });
    }, 16);
    return () => clearInterval(interval);
  }, [keys, wallHits]);

  // Camera follow
  useEffect(() => {
    setScrollY(Math.max(0, brickWorldY - 250));
  }, [brickWorldY]);

  // Object collection — check proximity
  useEffect(() => {
    let nearest = null, nearestDist = Infinity;
    STRATA_DATA.forEach(stratum => {
      stratum.objects.forEach(obj => {
        const objWorldY = stratum.y + 60 + Math.floor(stratum.objects.indexOf(obj) / 4) * 60 + (stratum.id === 2 ? 40 : 0);
        const dist = Math.sqrt((brickX - obj.x) ** 2 + (brickWorldY - objWorldY) ** 2);
        const key = `${stratum.id}:${obj.name}`;
        if (dist < 30) {
          if (!discovered.includes(key)) setDiscovered(prev => [...prev, key]);
          if (dist < nearestDist) {
            nearestDist = dist;
            nearest = { ...obj, stratum: stratum.label, stratumColor: stratum.color, depth: stratum.id };
          }
        }
      });
    });
    if (nearest) setSelectedObj(nearest);
  }, [brickX, brickWorldY, discovered]);

  // Current stratum
  const currentStratum = STRATA_DATA.find(s => brickWorldY >= s.y && brickWorldY < s.y + s.h) || STRATA_DATA[0];
  const totalObj = STRATA_DATA.reduce((s, st) => s + st.objects.length, 0);
  const eml2Disc = discovered.filter(d => d.startsWith("2:")).length;
  const eml2Pct = discovered.length > 0 ? Math.round((eml2Disc / discovered.length) * 100) : 0;

  // Stratum entry milestones
  useEffect(() => {
    const sid = currentStratum.id;
    if (!visitedStrata.includes(sid)) {
      setVisitedStrata(prev => [...prev, sid]);
      const messages = {
        1: "EML-1 — Growth. Things get exponential here.",
        2: "EML-2 — Measurement. Notice how many objects live here...",
        3: "EML-3 — Oscillation. Waves and vibration. Collect everything.",
        "inf": "EML-∞ — The Depths. The unsolved problems of mathematics.",
      };
      if (messages[sid]) showMilestone(messages[sid]);
    }
  }, [currentStratum]);

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 740, margin: "0 auto", padding: "0 0 1rem" }}>
      {/* Header */}
      <div style={{ textAlign: "center", padding: "0.75rem 1rem 0.4rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: currentStratum.color, fontWeight: 500, marginBottom: 2, transition: "color 0.5s" }}>monogate.dev</div>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 2px", color: "var(--color-text-primary, #1a1a2e)" }}>Strata</h1>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #888)", margin: 0 }}>
          {discovered.length === 0
            ? "Move with arrow keys / WASD / touch-drag. Explore downward. Collect the glowing orbs."
            : `${discovered.length}/${totalObj} objects · ${visitedStrata.length}/5 strata explored${wallUnderstood ? " · wall understood" : ""}`
          }
        </p>
      </div>

      {/* MISSION */}
      <div style={{
        textAlign: "center", padding: "5px 12px", margin: "4px 0 8px",
        background: wallUnderstood && discovered.length >= totalObj
          ? "rgba(16,185,129,0.08)" : "rgba(124,58,237,0.05)",
        borderRadius: 8, fontSize: 11, fontWeight: 500,
        color: wallUnderstood && discovered.length >= totalObj
          ? "#059669" : "#7C3AED",
        border: `1px solid ${wallUnderstood && discovered.length >= totalObj ? "rgba(16,185,129,0.12)" : "rgba(124,58,237,0.08)"}`,
      }}>
        {discovered.length >= totalObj
          ? "✓ All strata mapped. Every object found. The depth hierarchy is yours."
          : discovered.length === 0
            ? "Mission: Map all five strata. Find every object. Discover why EML-4 doesn't exist."
            : wallHits > 0 && !wallUnderstood
              ? `Blocked by the wall. Collect all EML-3 objects to understand it. (${eml3Found}/${eml3Objects.length})`
              : wallUnderstood && !visitedStrata.includes("inf")
                ? "The wall is open. EML-∞ awaits below. The unsolved depths."
                : `Keep exploring. ${totalObj - discovered.length} objects remain.`
        }
      </div>

      {/* MILESTONE TOAST */}
      {milestone && (
        <div style={{
          textAlign: "center", padding: "8px 16px", margin: "0 0 8px",
          background: "rgba(253,230,138,0.1)", borderRadius: 8,
          border: "1px solid rgba(253,230,138,0.2)",
          fontSize: 13, fontWeight: 500, color: "#D97706",
          animation: "fadeIn 0.3s ease",
        }}>{milestone}</div>
      )}

      {/* GAME AREA */}
      <div className="strata-main-grid" style={{ display: "grid", gridTemplateColumns: "1fr 200px", gap: 10 }}>
        {/* WORLD */}
        <div ref={gameRef} style={{
          borderRadius: 14, overflow: "hidden", aspectRatio: "680/500",
          border: `1px solid ${currentStratum.color}20`,
          position: "relative",
          outline: "none",
        }} tabIndex={0}
          onTouchStart={handleTouchStart} onTouchMove={handleTouchMove} onTouchEnd={handleTouchEnd}>
          <WorldCanvas scrollY={scrollY} brickX={brickX} brickWorldY={brickWorldY}
            discovered={discovered} wallHits={wallHits} wallOpen={wallUnderstood} pulse={pulse} />

          {/* Current stratum indicator */}
          <div style={{
            position: "absolute", top: 10, left: 10,
            background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)",
            borderRadius: 8, padding: "6px 12px",
            fontSize: 12, fontFamily: "var(--font-mono, monospace)",
            color: currentStratum.color, fontWeight: 600,
          }}>{currentStratum.label} — {currentStratum.name}</div>

          {/* Depth meter */}
          <div style={{
            position: "absolute", top: 10, right: 10,
            background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)",
            borderRadius: 8, padding: "6px 10px",
            fontSize: 10, fontFamily: "var(--font-mono)",
            color: "rgba(255,255,255,0.5)",
          }}>
            depth: {brickWorldY < 450 ? "0" : brickWorldY < 900 ? "1" : brickWorldY < 1500 ? "2" : brickWorldY < 2000 ? "3" : "∞"}
          </div>
        </div>

        {/* SIDE PANEL */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {/* Selected object */}
          {selectedObj && (
            <div style={{
              padding: "10px 12px", borderRadius: 10,
              background: `${selectedObj.stratumColor}08`,
              border: `1px solid ${selectedObj.stratumColor}20`,
              animation: "fadeIn 0.3s ease",
            }}>
              <div style={{ fontSize: 9, color: selectedObj.stratumColor, fontWeight: 600, textTransform: "uppercase", letterSpacing: 1, marginBottom: 3 }}>Discovered!</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--color-text-primary, #1a1a2e)", marginBottom: 2 }}>{selectedObj.name}</div>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: selectedObj.stratumColor, marginBottom: 4 }}>{selectedObj.formula}</div>
              <p style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", margin: 0, lineHeight: 1.5 }}>{selectedObj.note}</p>
              <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #999)", marginTop: 4 }}>
                {selectedObj.stratum} · depth {String(selectedObj.depth)}
              </div>
            </div>
          )}

          {/* Journal */}
          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Journal</div>
            <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #1a1a2e)" }}>{discovered.length}/{totalObj}</div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)", marginBottom: 6 }}>objects found</div>

            {/* Per-stratum counts */}
            {STRATA_DATA.map(s => {
              const count = discovered.filter(d => d.startsWith(`${s.id}:`)).length;
              return (
                <div key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 2 }}>
                  <span style={{ fontSize: 10, color: count > 0 ? s.color : "var(--color-text-secondary, #ccc)", fontFamily: "var(--font-mono)", fontWeight: count > 0 ? 600 : 400 }}>{s.label}</span>
                  <span style={{ fontSize: 10, color: "var(--color-text-secondary, #999)", fontFamily: "var(--font-mono)" }}>{count}/{s.objects.length}</span>
                </div>
              );
            })}

            {/* EML-2 insight */}
            {discovered.length > 8 && eml2Pct > 20 && (
              <div style={{ marginTop: 6, padding: "6px 8px", borderRadius: 6, background: "rgba(139,92,246,0.06)", border: "1px solid rgba(139,92,246,0.1)" }}>
                <div style={{ fontSize: 9, color: "#8B5CF6", fontWeight: 600 }}>Pattern noticed</div>
                <div style={{ fontSize: 10, color: "#7C3AED", marginTop: 2 }}>
                  {eml2Pct}% of your discoveries are EML-2. Why does everything that measures live at depth 2?
                </div>
              </div>
            )}
          </div>

          {/* Wall / Gap info */}
          {wallHits > 0 && (
            <div style={{
              padding: "10px 12px", borderRadius: 10,
              background: "rgba(239,68,68,0.04)",
              border: "1px solid rgba(239,68,68,0.12)",
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: "#EF4444", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>
                {wallUnderstood ? "The EML-4 gap" : "The wall"}
              </div>
              {!wallUnderstood ? (
                <div style={{ fontSize: 11, color: "var(--color-text-secondary, #888)", lineHeight: 1.5 }}>
                  <p style={{ margin: "0 0 6px" }}>Something blocks the way between EML-3 and the depths below.</p>
                  <p style={{ margin: "0 0 6px", color: "#EF4444" }}>Brute force won't work. You need to understand it.</p>
                  <p style={{ margin: 0, fontWeight: 500, color: "#EC4899" }}>
                    Map the oscillatory stratum completely. ({eml3Found}/{eml3Objects.length} objects found)
                  </p>
                  {eml3Found > 0 && eml3Found < eml3Objects.length && (
                    <div style={{ marginTop: 6, height: 4, borderRadius: 2, background: "rgba(236,72,153,0.15)", overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${(eml3Found / eml3Objects.length) * 100}%`, background: "#EC4899", borderRadius: 2, transition: "width 0.3s" }} />
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <div style={{ fontSize: 11, color: "#EF4444", lineHeight: 1.5, marginBottom: 6 }}>
                    The oscillatory stratum is L²-complete. Fourier of Fourier stays Fourier. There is no EML-4 — the wall is a theorem, not a barrier.
                  </div>
                  {GAP_PROOFS.slice(0, gapProofs).map((proof, i) => (
                    <div key={i} style={{
                      fontSize: 9, color: "#EF4444", padding: "5px 7px", marginBottom: 3,
                      background: "rgba(239,68,68,0.04)", borderRadius: 5, lineHeight: 1.5,
                      whiteSpace: "pre-line",
                    }}>
                      <span style={{ fontWeight: 600 }}>Proof {i + 1}:</span> {proof}
                    </div>
                  ))}
                  {gapProofs < GAP_PROOFS.length && (
                    <button onClick={() => setGapProofs(g => g + 1)} style={{
                      padding: "5px 10px", borderRadius: 6, border: "1px solid rgba(239,68,68,0.2)",
                      background: "rgba(239,68,68,0.06)", color: "#EF4444", fontSize: 9, cursor: "pointer", fontWeight: 500,
                    }}>Reveal proof {gapProofs + 1}/4</button>
                  )}
                  {gapProofs >= 4 && (
                    <div style={{ fontSize: 10, color: "#EF4444", fontWeight: 600, marginTop: 4, textAlign: "center" }}>
                      Δd=3 is impossible. EML-4 doesn't exist.
                      <br /><span style={{ fontWeight: 400, fontSize: 9 }}>But EML-∞ is now open. The depths await.</span>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Depth rules discovered */}
          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Depth rules</div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #666)", lineHeight: 1.8, fontFamily: "var(--font-mono)" }}>
              <div style={{ color: discovered.length > 0 ? "#06B6D4" : "var(--color-text-secondary, #ccc)" }}>Δd=1 — step (smooth)</div>
              {discovered.some(d => parseInt(d) >= 2) && <div style={{ color: "#F59E0B" }}>Δd=2 — portal (inversion)</div>}
              {wallUnderstood && <div style={{ color: "#EF4444" }}>Δd=∞ — collapse (categorification)</div>}
              {wallUnderstood && <div style={{ color: "#EF4444", fontWeight: 600 }}>Δd=3 — impossible</div>}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: "0.75rem 1rem", marginTop: 10,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          Every mathematical object has a depth — how many times <code style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "#7C3AED" }}>eml(x,y) = exp(x) − ln(y)</code> composes to express it.
          Move through the strata. Collect objects. Notice patterns. Find the wall. Ask why.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#7C3AED", textDecoration: "none", fontWeight: 500 }}>monogate.dev</a>{" · "}<a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none" }}>arXiv:2603.21852</a>
      </div>

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } } @media(max-width:600px){.strata-main-grid{grid-template-columns:1fr!important;}}`}</style>
    </div>
  );
}
