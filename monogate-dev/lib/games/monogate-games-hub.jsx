import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const eml = (x, y) => (y <= 0 ? Math.exp(x) : Math.exp(x) - Math.log(y));

const GAMES = [
  {
    id: "magic-brick", title: "Magic Brick Math", status: "play", category: "experience",
    tagline: "One brick. Infinite creation.",
    desc: "Drag a living brick into glowing zones. Watch one equation generate polar spirals, waveforms, Lorenz attractors, Ulam spirals, orbital curves, and exponential sweeps. Overlap zones for hybrids.",
    color: "#8B5CF6", icon: "◆", phase: "Wonder", teaches: "The EML operator creates varied mathematical structures",
  },
  {
    id: "eml-builder", title: "EML Builder", status: "play", category: "experience",
    tagline: "Snap. Compose. Create.",
    desc: "Connect EML bricks into computation trees. Variable nodes let you plot f(x) live. Three visualization modes. Audio output. Challenge puzzles — build e, e², π with the fewest nodes.",
    color: "#06B6D4", icon: "⧈", phase: "Agency", teaches: "How EML composition works mechanically",
  },
  {
    id: "strata", title: "Strata", status: "play", category: "game",
    tagline: "Walk through the layers of mathematical reality.",
    desc: "Move your brick through five EML strata. 23 census objects from §41 of the EML paper. Hit the EML-4 wall — six independent proofs it doesn't exist. T01, T02, T03 explained in context.",
    color: "#EC4899", icon: "▽", phase: "Discovery", teaches: "The EML depth hierarchy and §41 census",
  },
  {
    id: "shadow", title: "The Barrier", status: "play", category: "experience",
    tagline: "Real vs complex. The same function. Different depths.",
    desc: "sin(x) is EML-∞ over ℝ — T01 proves it. Collect approximation shadows at N=1 through N=12 (1.7 billion trees, zero candidates). Then discover T03: sin(x) = Im(eml(ix,1)). One complex node. Exact. |sin(x)| has no bypass.",
    color: "#FDE68A", icon: "◐", phase: "Mystery", teaches: "T01 barrier and T03 Euler Gateway",
  },
  {
    id: "measure", title: "Measure", status: "play", category: "game",
    tagline: "Integration costs exactly 2.",
    desc: "Transform mathematical objects through depth space. Exponentiate, integrate, Wick rotate, categorify. The depth +3 operation doesn't exist. Discover why through 14 puzzles across 5 chapters.",
    color: "#F59E0B", icon: "∫", phase: "Understanding", teaches: "The signed depth-change group across EML strata",
  },
  {
    id: "closure", title: "Closure", status: "play", category: "game",
    tagline: "You can't escape. Unless...",
    desc: "Trapped inside EML-3. 28 combinations of oscillatory objects — sin, cos, tanh, erf, Fourier series, wave equations. Every result stays at depth 3. EML Closure Theorem: eml(EML-3, EML-3) = EML-3. The only exit: categorification.",
    color: "#EF4444", icon: "⊘", phase: "Insight", teaches: "EML-3 self-closure and the Closure Theorem",
  },
  {
    id: "genesis", title: "Genesis", status: "play", category: "experience",
    tagline: "Build the function library from one equation.",
    desc: "Start with one equation and the constant 1. Compose through five EML depth levels: arithmetic, growth, measurement, oscillation, infinity. Each creation is real EML computation — T02 Universality in action.",
    color: "#10B981", icon: "◉", phase: "Creation", teaches: "T02: EML + constant 1 generates all elementary functions",
  },
  {
    id: "proof", title: "Proof", status: "play", category: "game",
    tagline: "Prove it yourself.",
    desc: "Nine EML theorems decomposed into proof blocks. Arrange them in valid logical order. From exp(x)=eml(x,1) to the Infinite Zeros Barrier to the Pumping Lemma to EML Weierstrass. The actual proofs, step by step.",
    color: "#A78BFA", icon: "∴", phase: "Mastery", teaches: "T01–T07 and the EML proof structure",
  },
  {
    id: "the-gap", title: "1.7 Billion Trees", status: "play", category: "game",
    tagline: "Zero sin(x) candidates. Then: one complex node.",
    desc: "Reveal the N=1 through N=12 exhaustive EML search. Watch 1,704,034,304 trees searched — zero sin(x) candidates. T01 explains why. Then T03 resolves it: sin(x) = Im(eml(ix,1)). One complex node. MSE = 0.",
    color: "#EF4444", icon: "∎", phase: "Victory", teaches: "T01 computational confirmation and T03 complex bypass",
  },
  {
    id: "conveyor-sim", title: "Conveyor Sim", status: "play", category: "experience",
    tagline: "Watch complexity assemble itself.",
    desc: "A conveyor belt of EML computation. Objects enter at depth 0 and transform through each layer — arithmetic, growth, measurement, oscillation. Read EML-2 (logarithmic wear) and EML-3 (oscillatory vibration) together.",
    color: "#F97316", icon: "⇒", phase: "Process", teaches: "EML depth as a production pipeline",
  },
  {
    id: "depth-of-room", title: "Depth of Room", status: "play", category: "experience",
    tagline: "Every space has a depth.",
    desc: "Walk through rooms at different EML depths. Sound, light, and space shift as depth grows. EML-0 is silence. EML-3 is the stratum of sin(x), cos(x), and Fourier series. EML-∞ is the non-constructible.",
    color: "#8B5CF6", icon: "⬡", phase: "Space", teaches: "EML depth as spatial and sonic character",
  },
  {
    id: "monogate-sound", title: "Monogate Sound", status: "play", category: "experience",
    tagline: "Hear the equation.",
    desc: "The EML operator turned into sound. Each depth has a signature timbre — discrete clicks at EML-0, continuous tones at EML-1, oscillating harmonics at EML-3. EML-4 doesn't exist. Listen for the gap.",
    color: "#10B981", icon: "♫", phase: "Sound", teaches: "EML depth as acoustic texture",
  },
  {
    id: "cosmos", title: "The Cosmos", status: "play", category: "experience",
    tagline: "Every mathematical object, at its true depth.",
    desc: "The EML census as a living universe. Objects float at their EML depth — integers at EML-0, exp(x) at EML-1, sin(x) at EML-3, |sin(x)| at EML-∞. Click any object to inspect it. Click two to combine with eml(). EML-3 × EML-3 = EML-3.",
    color: "#A78BFA", icon: "✦", phase: "Overview", teaches: "The EML-k depth hierarchy as a living map",
  },
  {
    id: "phantom-attractor", title: "Phantom Attractor", status: "play", category: "experience",
    tagline: "Why does gradient descent get stuck at 3.1696?",
    desc: "Simulate EML tree training dynamics. Without regularization, 92% of runs collapse to the phantom attractor at 3.1696 — not the target π. Dial up λ past the critical threshold and watch the phantom vanish. Phase transition. Real data from §5.",
    color: "#F97316", icon: "⊕", phase: "Dynamics", teaches: "The phantom attractor phenomenon and λ_crit phase transition",
  },
  {
    id: "identity-theorem", title: "Identity Theorem", status: "play", category: "game",
    tagline: "Step through the proof that eml gives you everything.",
    desc: "Walk through each algebraic step of the EML chain: eml(x,1)=exp(x), eml(1,exp(x))=e−x, eml(e−x,1)=exp(e−x). Each cancellation is a puzzle piece. Prove the neg(x)=−x identity in 4 steps from first principles.",
    color: "#06B6D4", icon: "∴", phase: "Proof", teaches: "The algebraic chain behind the 4-node neg identity",
  },
  {
    id: "negative-exponent", title: "Negative Exponent", status: "play", category: "game",
    tagline: "Which operator can reach exp(−x)?",
    desc: "Only one operator in the EML family reaches exp(−x) exactly in one node. EML fails (wrong sign). EDL fails. EXL only approximates. DEML wins: deml(x,1)=exp(−x)−ln(1)=exp(−x). Discover why each operator either succeeds or gets blocked.",
    color: "#EC4899", icon: "⁻¹", phase: "Discovery", teaches: "Why DEML = exp(−A)−ln(B) is the right operator for negative exponents",
  },
  {
    id: "weierstrass-machine", title: "Weierstrass Machine", status: "play", category: "experience",
    tagline: "Build any continuous function from EML atoms.",
    desc: "The EML Weierstrass theorem in action: for any continuous f on [0.2, 3.0], compose EML atoms to approximate it. Select depth-1, depth-2, or depth-3 atoms and combine them. Watch the approximation converge. T02 Universality made tangible.",
    color: "#10B981", icon: "≈", phase: "Approximation", teaches: "T02: EML + constant 1 approximates any continuous function",
  },
  {
    id: "billion-trees", title: "Search Log", status: "play", category: "experience",
    tagline: "Reveal the search, depth by depth.",
    desc: "The exhaustive EML tree search (§35) made interactive. Click to reveal each depth level: 4 trees at N=1, 16 at N=2, up to 1,704,034,304 at N=12. Watch the best-MSE column stall above 0.1. sin(x) never appears. Real data, real search times.",
    color: "#EF4444", icon: "⏱", phase: "Search", teaches: "How the exhaustive search was conducted and why it found nothing",
  },
  {
    id: "eml-synth", title: "EML Synth", status: "play", category: "experience",
    tagline: "Play the math.",
    desc: "A synthesizer built from EML nodes. Each key triggers oscillators constructed from exp-ln operators. Chord mode, arpeggio, and free play. The sound of one equation.",
    color: "#A78BFA", icon: "♩", phase: "Sound", teaches: "EML as a generative musical instrument",
  },
  {
    id: "fractal-explorer", title: "Fractal Explorer", status: "play", category: "experience",
    tagline: "Eight operators. Eight different universes.",
    desc: "Real-plane escape-time fractals for all 8 EML-family operators: EML, EAL, EMN, EXL, EDL, DEML, POW, LEX. Click to zoom, shift-click to zoom out. The EML operator produces the Devaney exponential family — boundary dimension 1.716. EAL, DEML, and EMN generate entirely different geometry.",
    color: "#e8a020", icon: "◈", phase: "Fractal", teaches: "How operator structure determines fractal geometry",
  },
  {
    id: "eml-synthesizer", title: "EML Synthesizer", status: "play", category: "experience",
    tagline: "Timbre is EML node count.",
    desc: "Fourier synthesis where every harmonic is one complex EML node: Im(eml(i·2πft,1))=sin(2πft). A sine wave costs 1 node. A violin costs 12. Adjust harmonic amplitudes with sliders, watch the waveform and spectrum update live, then play the sound.",
    color: "#5ec47a", icon: "♫", phase: "Harmonics", teaches: "The EML-Fourier identity and how timbre complexity maps to node count",
  },
];

const STATUS_CONFIG = {
  play: { label: "Open", bg: "#059669", dot: true },
  building: { label: "Building", bg: "#D97706", dot: true },
  concept: { label: "Concept", bg: "#6366F1", dot: false },
};

function LiveEml() {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let x = 0, fr;
    const tick = () => { x += 0.008; setVal(eml(Math.sin(x) * 0.5, Math.cos(x) * 0.3 + 1)); fr = requestAnimationFrame(tick); };
    tick(); return () => cancelAnimationFrame(fr);
  }, []);
  return <span style={{ color: "#A78BFA", fontFamily: "var(--font-mono, monospace)", fontSize: 13 }}>{val.toFixed(6)}</span>;
}

function GameCard({ game, index, visible }) {
  const [hovered, setHovered] = useState(false);
  const nav = useNavigate();
  const st = STATUS_CONFIG[game.status];
  const playable = game.status === "play";

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => playable && nav(`/${game.id}`)}
      style={{
        opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(24px)",
        transition: `all 0.5s cubic-bezier(0.16,1,0.3,1) ${index * 0.06}s`,
        background: hovered ? `linear-gradient(135deg, ${game.color}08, transparent)` : "rgba(255,255,255,0.015)",
        border: `1px solid ${hovered ? game.color + "35" : "rgba(255,255,255,0.05)"}`,
        borderRadius: 14, padding: "20px 20px 18px", cursor: playable ? "pointer" : "default",
        position: "relative", overflow: "hidden",
      }}>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: hovered ? 2 : 0, background: game.color, transition: "height 0.3s" }} />
      <div style={{ position: "absolute", top: 12, right: 12, display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontSize: 9, color: "rgba(255,255,255,0.25)", fontStyle: "italic" }}>{game.phase}</span>
        <span style={{ fontSize: 9, fontWeight: 600, letterSpacing: 0.8, textTransform: "uppercase",
          background: st.bg, color: "white", padding: "2px 8px", borderRadius: 99 }}>{st.label}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
        <span style={{ fontSize: 24, color: game.color, lineHeight: 1,
          filter: hovered ? `drop-shadow(0 0 6px ${game.color}50)` : "none", transition: "filter 0.3s" }}>{game.icon}</span>
        <div>
          <h3 style={{ fontSize: 17, fontWeight: 600, color: "#E2E8F0", margin: 0 }}>{game.title}</h3>
          <p style={{ fontSize: 12, color: game.color, margin: "1px 0 0", fontStyle: "italic", opacity: 0.8 }}>{game.tagline}</p>
        </div>
      </div>
      <p style={{ fontSize: 12, color: "rgba(226,232,240,0.5)", margin: "6px 0 0", lineHeight: 1.6 }}>{game.desc}</p>
      <div style={{ marginTop: 10, fontSize: 10, color: "rgba(167,139,250,0.4)", fontFamily: "var(--font-mono, monospace)" }}>
        teaches: {game.teaches}
      </div>
    </div>
  );
}

export default function Hub() {
  const [visible, setVisible] = useState(false);
  const [tab, setTab] = useState("all");
  useEffect(() => { setTimeout(() => setVisible(true), 150); }, []);

  const displayedGames = tab === "all" ? GAMES : GAMES.filter(g => g.category === tab);
  const expCount = GAMES.filter(g => g.category === "experience").length;
  const gameCount = GAMES.filter(g => g.category === "game").length;

  return (
    <div style={{ minHeight: "100vh", background: "#08060E", color: "#E2E8F0",
      fontFamily: "var(--font-sans, system-ui, sans-serif)", position: "relative", overflow: "hidden" }}>

      <div style={{ position: "absolute", inset: 0,
        backgroundImage: "radial-gradient(circle at 1px 1px, rgba(139,92,246,0.03) 1px, transparent 0)",
        backgroundSize: "48px 48px", pointerEvents: "none" }} />
      <div style={{ position: "absolute", top: -200, left: "50%", transform: "translateX(-50%)",
        width: 600, height: 400, background: "radial-gradient(ellipse, rgba(124,58,237,0.06) 0%, transparent 70%)",
        pointerEvents: "none" }} />

      <div style={{ maxWidth: 760, margin: "0 auto", padding: "0 20px", position: "relative" }}>

        {/* HEADER */}
        <header style={{
          textAlign: "center", padding: "50px 0 30px",
          opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(-16px)",
          transition: "all 0.7s cubic-bezier(0.16,1,0.3,1)",
        }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 10, marginBottom: 18 }}>
            <div style={{ width: 34, height: 34, borderRadius: 8,
              background: "linear-gradient(135deg, #7C3AED, #A78BFA)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 17, fontWeight: 700, color: "white",
              boxShadow: "0 0 20px rgba(124,58,237,0.25)" }}>M</div>
            <span style={{ fontSize: 15, fontWeight: 500, color: "#A78BFA",
              letterSpacing: 2, textTransform: "uppercase", fontFamily: "var(--font-mono, monospace)" }}>monogate.dev</span>
          </div>

          <h1 style={{ fontSize: 44, fontWeight: 700, margin: "0 0 24px", color: "#F1F5F9", letterSpacing: -1, lineHeight: 1.1 }}>
            monogate lab
          </h1>

          <div style={{ maxWidth: 560, marginLeft: "auto", marginRight: "auto", marginBottom: 28, textAlign: "left" }}>
            <p style={{ fontSize: 14, color: "rgba(226,232,240,0.6)", lineHeight: 1.8, margin: "0 0 14px" }}>
              One binary operator generates every function on a scientific calculator.{" "}
              <span style={{ fontFamily: "var(--font-mono, monospace)", color: "#C4B5FD" }}>eml(x,y) = exp(x) − ln(y)</span>
              {" "}— the NAND gate for continuous mathematics. 28 proved theorems. A complete census of elementary functions by EML depth.
            </p>
            <p style={{ fontSize: 14, color: "rgba(226,232,240,0.45)", lineHeight: 1.8, margin: "0 0 14px" }}>
              T01: sin(x) is unreachable in real EML — provably, structurally. 1,704,034,304 trees searched. Zero candidates.
              T03: over ℂ, sin(x) = Im(eml(ix,1)). One node. Exact. The barrier was real-domain only.
              The N=3 singularity: MSE drops 1.4 million times at depth 3.{" "}
              <em style={{ color: "rgba(167,139,250,0.7)" }}>The hierarchy is not a metaphor.</em>
            </p>
            <p style={{ fontSize: 14, color: "rgba(226,232,240,0.35)", lineHeight: 1.8, margin: 0 }}>
              Twenty-one experiences and games. From dragging a brick to 1.7 billion trees to fractal universes. The math is grounded. And it all starts with one equation.
            </p>
          </div>

          <div style={{ display: "inline-block", padding: "10px 24px", background: "rgba(124,58,237,0.06)",
            border: "1px solid rgba(124,58,237,0.15)", borderRadius: 10, marginBottom: 10 }}>
            <span style={{ fontSize: 22, fontFamily: "var(--font-mono, monospace)", color: "#C4B5FD", fontWeight: 500, letterSpacing: 1 }}>
              eml(x, y) = exp(x) − ln(y)
            </span>
          </div>

          <div style={{ fontSize: 11, color: "rgba(167,139,250,0.35)", fontFamily: "var(--font-mono, monospace)" }}>
            live → <LiveEml />
          </div>
        </header>

        {/* STATS */}
        <div style={{ display: "flex", justifyContent: "center", gap: 28, marginBottom: 32,
          opacity: visible ? 1 : 0, transition: "opacity 0.7s ease 0.2s" }}>
          {[
            { n: "1", l: "equation" },
            { n: String(expCount), l: "experiences" },
            { n: String(gameCount), l: "games" },
            { n: "T01–T28", l: "proved" },
            { n: "23", l: "census objects" },
            { n: "∞", l: "depth" },
          ].map(s => (
            <div key={s.l} style={{ textAlign: "center" }}>
              <div style={{ fontSize: s.n.length > 4 ? 16 : 24, fontWeight: 700, color: "#A78BFA", fontFamily: "var(--font-mono, monospace)" }}>{s.n}</div>
              <div style={{ fontSize: 10, color: "rgba(226,232,240,0.3)", textTransform: "uppercase", letterSpacing: 1.5 }}>{s.l}</div>
            </div>
          ))}
        </div>

        {/* THE ARC */}
        <div style={{
          display: "flex", justifyContent: "center", gap: 4, marginBottom: 28, flexWrap: "wrap",
          opacity: visible ? 1 : 0, transition: "opacity 0.7s ease 0.3s",
        }}>
          {GAMES.map((g, i) => (
            <div key={g.id} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div style={{
                width: 8, height: 8, borderRadius: "50%",
                background: g.status === "play" ? g.color : `${g.color}40`,
                boxShadow: g.status === "play" ? `0 0 6px ${g.color}40` : "none",
              }} />
              <span style={{ fontSize: 9, color: g.status === "play" ? g.color : "rgba(255,255,255,0.2)",
                fontFamily: "var(--font-mono, monospace)", fontWeight: g.status === "play" ? 500 : 400 }}>{g.phase}</span>
              {i < GAMES.length - 1 && <span style={{ color: "rgba(255,255,255,0.1)", fontSize: 10, margin: "0 2px" }}>→</span>}
            </div>
          ))}
        </div>

        {/* CATEGORY TABS */}
        <div style={{ display: "flex", gap: 3, marginBottom: 20, borderBottom: "1px solid rgba(255,255,255,0.04)", paddingBottom: 12,
          opacity: visible ? 1 : 0, transition: "opacity 0.7s ease 0.35s" }}>
          {[
            { id: "all",        label: "All",         count: GAMES.length },
            { id: "experience", label: "Experiences", count: expCount },
            { id: "game",       label: "Games",       count: gameCount },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              padding: "7px 16px", borderRadius: 8, border: "none", cursor: "pointer",
              background: tab === t.id ? "rgba(124,58,237,0.18)" : "transparent",
              color: tab === t.id ? "#C4B5FD" : "rgba(226,232,240,0.3)",
              fontSize: 12, fontWeight: tab === t.id ? 600 : 400, transition: "all 0.2s",
              outline: tab === t.id ? "1px solid rgba(124,58,237,0.3)" : "none",
            }}>
              {t.label} <span style={{ opacity: 0.5, fontSize: 10, marginLeft: 3 }}>{t.count}</span>
            </button>
          ))}
        </div>

        {/* CARD LIST */}
        <section style={{ marginBottom: 28 }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 2, textTransform: "uppercase",
            color: "#059669", marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#059669",
              boxShadow: "0 0 8px rgba(5,150,105,0.4)", animation: "pulse 2s ease infinite" }} />
            {tab === "all" ? `All ${GAMES.length} — play now` : tab === "experience" ? `${expCount} experiences — open-ended` : `${gameCount} games — win conditions`}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {displayedGames.map((g, i) => <GameCard key={g.id} game={g} index={i} visible={visible} />)}
          </div>
        </section>

        {/* EML DEPTH HIERARCHY — live census */}
        <section style={{
          padding: "24px", background: "rgba(253,230,138,0.02)",
          border: "1px solid rgba(253,230,138,0.08)", borderRadius: 14, marginBottom: 20,
          textAlign: "center",
        }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 2, textTransform: "uppercase",
            color: "#FDE68A", marginBottom: 12 }}>EML-k Depth Hierarchy — §41 Census</div>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 12, flexWrap: "wrap", marginBottom: 14 }}>
            {[
              { label: "EML-0", example: "integers", color: "#64748B" },
              { label: "EML-1", example: "exp(x)", color: "#06B6D4" },
              { label: "EML-2", example: "ln(x)", color: "#8B5CF6" },
              { label: "EML-3", example: "sin(x)", color: "#EC4899" },
              { label: "EML-∞", example: "|sin(x)|", color: "#FDE68A" },
            ].map((item, i) => (
              <div key={i} style={{
                padding: "8px 14px", borderRadius: 8,
                background: `rgba(${[100, 6, 139, 236, 253][i]},${[116, 182, 92, 72, 230][i]},${[139, 212, 246, 153, 138][i]},0.06)`,
                border: `1px solid rgba(${[100, 6, 139, 236, 253][i]},${[116, 182, 92, 72, 230][i]},${[139, 212, 246, 153, 138][i]},0.15)`,
                textAlign: "center",
              }}>
                <div style={{ fontSize: 11, fontFamily: "var(--font-mono, monospace)", color: ["#64748B", "#06B6D4", "#8B5CF6", "#EC4899", "#FDE68A"][i], fontWeight: 600 }}>{item.label}</div>
                <div style={{ fontSize: 10, color: "rgba(226,232,240,0.4)", marginTop: 2 }}>{item.example}</div>
              </div>
            ))}
          </div>
          <div style={{ fontSize: 12, fontFamily: "var(--font-mono, monospace)", color: "rgba(6,182,212,0.6)", marginBottom: 6 }}>
            eml(x, y) = exp(x) − ln(y)  ·  eml ∈ EML-3
          </div>
          <div style={{ fontSize: 12, color: "rgba(226,232,240,0.4)", maxWidth: 500, margin: "0 auto", lineHeight: 1.6 }}>
            EML combines an EML-1 operation (exp) and an EML-2 operation (ln). The result sits at EML-3 — the deepest finite stratum.
            EML-3 is closed: eml(EML-3, EML-3) = EML-3. The N=3 singularity (§37) shows MSE drops 1.4 million times at depth 3.
          </div>
        </section>

        {/* KEY RESULTS */}
        <section style={{
          padding: "20px 24px", background: "rgba(16,185,129,0.02)",
          border: "1px solid rgba(16,185,129,0.08)", borderRadius: 14, marginBottom: 20,
        }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 2, textTransform: "uppercase",
            color: "#059669", marginBottom: 12 }}>Key Results</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
            {[
              { n: "T01–T28", l: "proved results" },
              { n: "23", l: "EML-k census objects" },
              { n: "1.7B", l: "trees searched" },
              { n: "0", l: "sin(x) candidates" },
              { n: "1", l: "complex bypass node" },
              { n: "1.4M×", l: "N=3 MSE improvement" },
            ].map(s => (
              <div key={s.l} style={{ textAlign: "center" }}>
                <div style={{ fontSize: s.n.length > 4 ? 16 : 22, fontWeight: 700, color: "#059669", fontFamily: "var(--font-mono)" }}>{s.n}</div>
                <div style={{ fontSize: 9, color: "rgba(226,232,240,0.3)", textTransform: "uppercase", letterSpacing: 1 }}>{s.l}</div>
              </div>
            ))}
          </div>
          <div style={{ textAlign: "center", marginTop: 12, fontSize: 11, color: "rgba(226,232,240,0.25)" }}>
            T01: Infinite Zeros Barrier · T02: EML Universality · T03: Euler Gateway · §35: N=12 search · §37: N=3 singularity · §41: EML-k census
          </div>
        </section>

        {/* THE STORY */}
        <section style={{
          padding: "28px 24px", background: "rgba(124,58,237,0.03)",
          border: "1px solid rgba(124,58,237,0.08)", borderRadius: 14, marginBottom: 28,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: "#C4B5FD", margin: "0 0 12px" }}>The results</h2>
          <p style={{ fontSize: 13, color: "rgba(226,232,240,0.5)", margin: "0 0 10px", lineHeight: 1.7 }}>
            T01 — Infinite Zeros Barrier: any finite real EML tree is real-analytic with finitely many zeros. sin(x) has infinitely many zeros. Therefore no finite real EML tree equals sin(x). Computationally confirmed: §35 searched 1,704,034,304 trees to depth N=12. Zero sin(x) candidates.
          </p>
          <p style={{ fontSize: 13, color: "rgba(226,232,240,0.5)", margin: "0 0 10px", lineHeight: 1.7 }}>
            T03 — Euler Gateway: sin(x) = Im(eml(ix, 1)). Over ℂ, one node, MSE = 0. Exact. The real-domain barrier is structural — not fundamental. The complex field dissolves it.
          </p>
          <p style={{ fontSize: 13, color: "rgba(226,232,240,0.5)", margin: 0, lineHeight: 1.7 }}>
            §41 EML-k census: 23 elementary functions classified by minimum EML approximation depth. N=3 singularity (§37): at depth 3, MSE drops 1.4 million times compared to depth 2. The hierarchy is real and measurable.
          </p>
        </section>

        {/* FOOTER */}
        <footer style={{ textAlign: "center", padding: "16px 0 36px", borderTop: "1px solid rgba(255,255,255,0.03)" }}>
          <div style={{ fontSize: 18, fontFamily: "var(--font-mono, monospace)", color: "rgba(167,139,250,0.2)", marginBottom: 10 }}>
            eml(1, 1) = {eml(1, 1).toFixed(6)}
          </div>
          <div style={{ fontSize: 12, color: "rgba(226,232,240,0.25)", lineHeight: 2 }}>
            <a href="https://monogate.dev" style={{ color: "#A78BFA", textDecoration: "none" }}>monogate.dev</a>
            {" · "}
            <a href="https://arxiv.org/abs/2603.21852" style={{ color: "rgba(167,139,250,0.5)", textDecoration: "none" }}>arXiv:2603.21852</a>
            {" · "}
            <a href="https://www.npmjs.com/package/monogate" style={{ color: "rgba(167,139,250,0.5)", textDecoration: "none" }}>npm</a>
            {" · "}
            <a href="https://github.com/almaguer1986/monogate" style={{ color: "rgba(167,139,250,0.5)", textDecoration: "none" }}>github</a>
          </div>
        </footer>
      </div>

      <style>{`
        @keyframes pulse { 0%,100% { opacity:1; transform:scale(1) } 50% { opacity:0.5; transform:scale(1.3) } }
      `}</style>
    </div>
  );
}
