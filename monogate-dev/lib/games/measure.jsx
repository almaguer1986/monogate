import { useState, useRef, useEffect } from "react";

// ═══════════════════════════════════════════════════════════════════
// OPERATIONS — concrete mathematical actions, not abstract moves
// ═══════════════════════════════════════════════════════════════════
const OPERATIONS = [
  { id: "exp", name: "Exponentiate", delta: 1, icon: "eˣ", desc: "Apply exponential. Depth +1.",
    color: "#06B6D4", action: "Growth enters." },
  { id: "log", name: "Take logarithm", delta: 1, icon: "ln", desc: "Apply logarithm. Depth +1.",
    color: "#06B6D4", action: "Measurement enters." },
  { id: "integrate", name: "Integrate", delta: 2, icon: "∫", desc: "Add a measure. ∫dμ + log(Z) = depth +2.",
    color: "#8B5CF6", action: "A measure is added. Depth jumps by 2." },
  { id: "wick", name: "Wick rotate", delta: -2, icon: "⟲", desc: "Remove oscillatory measure. Depth −2.",
    color: "#8B5CF6", action: "The oscillation dissolves. Depth drops by 2." },
  { id: "simplify", name: "Simplify", delta: -1, icon: "→", desc: "Reduce complexity. Depth −1.",
    color: "#64748B", action: "Simplified. One level shallower." },
  { id: "categorify", name: "Categorify", delta: Infinity, icon: "∞", desc: "Enrich to infinite depth. No return.",
    color: "#FDE68A", action: "The structure enriches. Depth → ∞." },
];

// The missing operation
const MISSING_OP = { name: "???", delta: 3, icon: "⚡", desc: "This operation does not exist.", color: "#EF4444" };

// ═══════════════════════════════════════════════════════════════════
// PUZZLES — transform object from one state to another
// ═══════════════════════════════════════════════════════════════════
const PUZZLES = [
  // Chapter 1: Learning the tools
  { id: 1, chapter: "The Basics", name: "First measurement",
    object: "a counting number", start: 0, target: 2,
    story: "You have a plain integer. Transform it into something that can measure.",
    solution: "One integration takes you from depth 0 to depth 2.", par: 1 },
  { id: 2, chapter: "The Basics", name: "Growth",
    object: "a constant", start: 0, target: 1,
    story: "Make it grow. Apply an exponential.",
    solution: "Exponentiate once.", par: 1 },
  { id: 3, chapter: "The Basics", name: "Measure and grow",
    object: "a constant", start: 0, target: 3,
    story: "Reach the oscillatory stratum. You'll need more than one operation.",
    solution: "Integrate (+2) then exponentiate (+1). Or three exponentiations.", par: 2 },
  { id: 4, chapter: "The Basics", name: "Come back down",
    object: "a wave function", start: 3, target: 1,
    story: "The wave is too complex. Simplify it back to growth.",
    solution: "Wick rotate (−2) to drop from 3 to 1.", par: 1 },

  // Chapter 2: The measure theorem
  { id: 5, chapter: "Measure Theory", name: "Radon-Nikodym",
    object: "abstract measure μ", start: 0, target: 2,
    story: "Convert an abstract measure to a density. This is the canonical Δd=2.",
    solution: "Integrate. One operation. +2 exactly.", par: 1 },
  { id: 6, chapter: "Measure Theory", name: "Born rule",
    object: "quantum state |ψ⟩", start: 0, target: 2,
    story: "Collapse a quantum state to a probability. Measurement adds a measure.",
    solution: "Integrate. Quantum measurement = +2.", par: 1 },
  { id: 7, chapter: "Measure Theory", name: "Fisher information",
    object: "model parameters θ", start: 0, target: 2,
    story: "Extract Fisher information from parameters. E_θ[·] adds a measure.",
    solution: "Integrate. Expectation = adding a measure.", par: 1 },
  { id: 8, chapter: "Measure Theory", name: "Double measure",
    object: "a constant", start: 0, target: 2,
    story: "Can you add TWO measures and end up deeper than 2?",
    solution: "∫∫ stays at depth 2 — Fubini/Tonelli. Product measures are self-maps at EML-2. Try it!", par: 2 },

  // Chapter 3: Wick rotation
  { id: 9, chapter: "Oscillation ↔ Measurement", name: "Euclidean QFT",
    object: "oscillatory path integral", start: 3, target: 1,
    story: "Wick-rotate the oscillatory integral to Euclidean space. Remove the phase.",
    solution: "Wick rotation: depth 3 → 1. The complex measure dissolves.", par: 1 },
  { id: 10, chapter: "Oscillation ↔ Measurement", name: "Round trip",
    object: "a counting number", start: 0, target: 0,
    story: "Go up and come back. End where you started.",
    solution: "Integrate (+2) then Wick rotate (−2). Or exponentiate then simplify.", par: 2 },

  // Chapter 4: The wall
  { id: 11, chapter: "The Wall", name: "Reach depth 4",
    object: "a wave equation", start: 3, target: 4,
    story: "You're at depth 3. Can you reach depth 4? Try everything.",
    solution: null, par: -1 },
  { id: 12, chapter: "The Wall", name: "The missing tool",
    object: "a constant", start: 0, target: 3,
    story: "Get to depth 3 in exactly one operation. Look at your toolbox. Is there a +3?",
    solution: null, par: -1, maxMoves: 1 },

  // Chapter 5: Infinity
  { id: 13, chapter: "The Leap", name: "Categorification",
    object: "the Jones polynomial", start: 3, target: Infinity,
    story: "Enrich the Jones polynomial into Khovanov homology. This is a one-way trip.",
    solution: "Categorify. Depth 3 → ∞.", par: 1 },
  { id: 14, chapter: "The Leap", name: "The full journey",
    object: "the number 1", start: 0, target: Infinity,
    story: "Take 1 all the way to infinite depth. The complete journey through mathematics.",
    solution: "Any path that ends with categorification. How you get to 3 first is your choice.", par: 3 },
];

const CHAPTERS = [...new Set(PUZZLES.map(p => p.chapter))];

// Stratum visual data
const STRATA_VIS = [
  { d: 0, label: "Arithmetic", color: "#64748B", bg: "rgba(100,116,139,0.06)" },
  { d: 1, label: "Growth", color: "#06B6D4", bg: "rgba(6,182,212,0.06)" },
  { d: 2, label: "Measurement", color: "#8B5CF6", bg: "rgba(139,92,246,0.06)" },
  { d: 3, label: "Oscillation", color: "#EC4899", bg: "rgba(236,72,153,0.06)" },
  { d: Infinity, label: "The Depths", color: "#FDE68A", bg: "rgba(253,230,138,0.06)" },
];

// ═══════════════════════════════════════════════════════════════════
// OBJECT DISPLAY — visual representation that changes with depth
// ═══════════════════════════════════════════════════════════════════
function ObjectVis({ depth, pulse }) {
  const stratum = STRATA_VIS.find(s => s.d === depth) || STRATA_VIS[0];
  const t = pulse;

  // Different visual per depth
  const renderShape = () => {
    if (depth === 0) {
      return <div style={{ fontSize: 42, fontFamily: "var(--font-mono)", color: stratum.color, opacity: 0.8, fontWeight: 700 }}>1</div>;
    } else if (depth === 1) {
      return (
        <svg width="80" height="60" viewBox="0 0 80 60">
          <path d={`M0 55 ${Array.from({ length: 40 }, (_, i) => `L${i * 2} ${55 - Math.exp(i * 0.08) * 2}`).join(" ")}`}
            fill="none" stroke={stratum.color} strokeWidth="2" opacity="0.6" />
        </svg>
      );
    } else if (depth === 2) {
      return (
        <svg width="80" height="60" viewBox="0 0 80 60">
          {[0, 1, 2].map(sp => (
            <path key={sp} d={`M40 30 ${Array.from({ length: 60 }, (_, i) => {
              const frac = i / 60;
              const angle = frac * Math.PI * 4 + sp * (Math.PI * 2 / 3) + t * 0.3;
              const r = 3 + Math.log(1 + frac * 10) * 10;
              return `L${40 + Math.cos(angle) * r} ${30 + Math.sin(angle) * r}`;
            }).join(" ")}`} fill="none" stroke={stratum.color} strokeWidth="1.5" opacity="0.4" />
          ))}
        </svg>
      );
    } else if (depth === 3) {
      return (
        <svg width="80" height="60" viewBox="0 0 80 60">
          {[0, 1, 2].map(w => (
            <path key={w} d={`M0 ${30 + w * 5} ${Array.from({ length: 40 }, (_, i) =>
              `L${i * 2} ${30 + w * 5 + Math.sin(i * 0.4 + t * 2 + w) * (10 - w * 2)}`
            ).join(" ")}`} fill="none" stroke={stratum.color} strokeWidth="1.5" opacity={0.5 - w * 0.1} />
          ))}
        </svg>
      );
    } else {
      return (
        <div style={{ fontSize: 36, color: stratum.color, opacity: 0.6 + Math.sin(t * 2) * 0.2, fontWeight: 700 }}>∞</div>
      );
    }
  };

  return (
    <div style={{
      width: "100%", aspectRatio: "4/3", borderRadius: 12,
      background: stratum.bg, border: `1.5px solid ${stratum.color}20`,
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      gap: 6, transition: "all 0.5s ease",
    }}>
      {renderShape()}
      <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: stratum.color, fontWeight: 600 }}>
        EML-{depth === Infinity ? "∞" : depth}
      </div>
      <div style={{ fontSize: 9, color: "var(--color-text-secondary, #999)" }}>{stratum.label}</div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// MAIN GAME
// ═══════════════════════════════════════════════════════════════════
export default function MeasureGame() {
  const [currentPuzzle, setCurrentPuzzle] = useState(0);
  const [depth, setDepth] = useState(PUZZLES[0].start);
  const [history, setHistory] = useState([]);
  const [solved, setSolved] = useState([]);
  const [impossible, setImpossible] = useState([]);
  const [lastAction, setLastAction] = useState(null);
  const [showForbidden, setShowForbidden] = useState(false);
  const [pulse, setPulse] = useState(0);

  useEffect(() => { let fr; const tick = () => { setPulse(p => p + 0.025); fr = requestAnimationFrame(tick); }; tick(); return () => cancelAnimationFrame(fr); }, []);

  const puzzle = PUZZLES[currentPuzzle];
  const isImpossible = puzzle.par === -1;
  const isSolved = depth === puzzle.target && history.length > 0 && !isImpossible;

  useEffect(() => {
    if (isSolved && !solved.includes(puzzle.id)) setSolved(prev => [...prev, puzzle.id]);
  }, [isSolved, puzzle.id, solved]);

  const applyOp = (op) => {
    if (isSolved) return;
    if (puzzle.maxMoves && history.length >= puzzle.maxMoves) {
      if (isImpossible && !impossible.includes(puzzle.id)) setImpossible(prev => [...prev, puzzle.id]);
      return;
    }

    let newDepth = depth;
    if (op.delta === Infinity) {
      newDepth = Infinity;
    } else {
      if (depth === Infinity) return;
      newDepth = depth + op.delta;
    }

    if (newDepth < 0) { setLastAction("Can't go below depth 0."); return; }
    if (newDepth === 4) {
      setShowForbidden(true);
      setLastAction("EML-4 does not exist. Six proofs confirm it.");
      setTimeout(() => setShowForbidden(false), 2500);
      if (isImpossible && !impossible.includes(puzzle.id)) setImpossible(prev => [...prev, puzzle.id]);
      return;
    }
    if (newDepth > 4 && newDepth !== Infinity) return;

    setHistory(prev => [...prev, { from: depth, to: newDepth, op: op.name }]);
    setLastAction(op.action);
    setDepth(newDepth);

    // Play tone
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)();
      const freq = [130, 165, 220, 330, 440][Math.min(newDepth === Infinity ? 4 : newDepth, 4)];
      const o = ac.createOscillator(); o.type = op.delta > 0 ? "sine" : "triangle";
      o.frequency.setValueAtTime(freq, ac.currentTime);
      const g = ac.createGain(); g.gain.setValueAtTime(0.06, ac.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.8);
      o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime + 1);
      setTimeout(() => ac.close(), 1200);
    } catch {}
  };

  const reset = () => { setDepth(puzzle.start); setHistory([]); setLastAction(null); setShowForbidden(false); };
  const loadPuzzle = (idx) => { setCurrentPuzzle(idx); setDepth(PUZZLES[idx].start); setHistory([]); setLastAction(null); setShowForbidden(false); };

  const stars = isSolved ? (history.length <= puzzle.par ? 3 : history.length <= puzzle.par + 1 ? 2 : 1) : 0;
  const totalSolvable = PUZZLES.filter(p => p.par !== -1).length;
  const stratum = STRATA_VIS.find(s => s.d === depth) || STRATA_VIS[0];

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 740, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.4rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#F59E0B", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>Measure</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          Transform mathematical objects. Each operation changes their depth. Some operations don't exist.
        </p>
      </div>

      {/* Progress */}
      <div style={{
        textAlign: "center", padding: "6px 14px", margin: "6px 0 10px",
        background: solved.length >= totalSolvable ? "rgba(16,185,129,0.08)" : "rgba(245,158,11,0.05)",
        borderRadius: 8, fontSize: 12, fontWeight: 500,
        color: solved.length >= totalSolvable ? "#059669" : "#D97706",
      }}>
        {solved.length}/{totalSolvable} puzzles · {impossible.length} impossible discovered
      </div>

      <div className="measure-grid" style={{ display: "grid", gridTemplateColumns: "1fr 200px", gap: 10 }}>
        <div>
          {/* Puzzle card */}
          <div style={{
            padding: "14px 16px", borderRadius: 12, marginBottom: 10,
            background: isSolved ? "rgba(16,185,129,0.06)" : showForbidden ? "rgba(239,68,68,0.06)" : "var(--color-background-secondary, #faf5ff)",
            border: `1.5px solid ${isSolved ? "rgba(16,185,129,0.2)" : showForbidden ? "rgba(239,68,68,0.2)" : "var(--color-border-tertiary, rgba(0,0,0,0.06))"}`,
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: isImpossible ? "#EF4444" : "#D97706", textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>{puzzle.chapter}</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-text-primary, #1a1a2e)", marginBottom: 4 }}>{puzzle.name}</div>
            <div style={{ fontSize: 12, color: "var(--color-text-secondary, #777)", lineHeight: 1.5, marginBottom: 8 }}>{puzzle.story}</div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", fontWeight: 600, color: stratum.color }}>
                {puzzle.object}
              </span>
              <span style={{ fontSize: 20, color: "var(--color-text-secondary, #ccc)" }}>→</span>
              <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", fontWeight: 600,
                color: STRATA_VIS.find(s => s.d === puzzle.target)?.color || "#888" }}>
                EML-{puzzle.target === Infinity ? "∞" : puzzle.target === 4 ? "4?" : puzzle.target}
              </span>
              {isSolved && <span style={{ fontSize: 13, marginLeft: "auto" }}>{"★".repeat(stars)}{"☆".repeat(3 - stars)}</span>}
            </div>
          </div>

          {/* Object display + depth path */}
          <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 10, marginBottom: 10 }}>
            <ObjectVis depth={depth} pulse={pulse} />
            {/* Move history */}
            <div style={{
              padding: "10px 12px", borderRadius: 10,
              background: "var(--color-background-secondary, #faf5ff)",
              border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
              minHeight: 90, maxHeight: 150, overflowY: "auto",
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: "var(--color-text-secondary, #999)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>
                {history.length === 0 ? "No operations applied yet" : `${history.length} operation${history.length !== 1 ? "s" : ""}`}
              </div>
              {history.map((h, i) => (
                <div key={i} style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #666)", lineHeight: 1.6 }}>
                  <span style={{ color: STRATA_VIS.find(s => s.d === h.from)?.color || "#888" }}>{h.from === Infinity ? "∞" : h.from}</span>
                  <span style={{ color: "var(--color-text-secondary, #ccc)" }}> →{h.op}→ </span>
                  <span style={{ color: STRATA_VIS.find(s => s.d === h.to)?.color || "#888" }}>{h.to === Infinity ? "∞" : h.to}</span>
                </div>
              ))}
              {lastAction && (
                <div style={{ fontSize: 10, color: showForbidden ? "#EF4444" : stratum.color, marginTop: 4, fontStyle: "italic" }}>
                  {lastAction}
                </div>
              )}
            </div>
          </div>

          {/* FORBIDDEN */}
          {showForbidden && (
            <div style={{
              textAlign: "center", padding: "10px 16px", marginBottom: 10,
              background: "rgba(239,68,68,0.06)", border: "1.5px solid rgba(239,68,68,0.2)",
              borderRadius: 10, animation: "fadeIn 0.2s ease",
            }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#EF4444" }}>⚡ IMPOSSIBLE</div>
              <div style={{ fontSize: 11, color: "#EF4444", marginTop: 2 }}>{lastAction}</div>
            </div>
          )}

          {/* OPERATION BUTTONS — the toolbox */}
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-secondary, #888)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
            Your toolbox
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6, marginBottom: 8 }}>
            {OPERATIONS.map(op => {
              const disabled = isSolved || (depth === Infinity && op.delta !== Infinity) || (depth + op.delta < 0 && op.delta !== Infinity);
              return (
                <button key={op.id} onClick={() => !disabled && applyOp(op)}
                  style={{
                    padding: "12px 8px", borderRadius: 10, cursor: disabled ? "not-allowed" : "pointer",
                    background: disabled ? "var(--color-background-secondary, #f0f0f0)" : `${op.color}06`,
                    border: `1.5px solid ${disabled ? "var(--color-border-tertiary, #ddd)" : `${op.color}20`}`,
                    opacity: disabled ? 0.35 : 1, textAlign: "center", transition: "all 0.15s",
                  }}>
                  <div style={{ fontSize: 22, color: op.color, marginBottom: 2, lineHeight: 1 }}>{op.icon}</div>
                  <div style={{ fontSize: 10, fontWeight: 600, color: op.color }}>{op.name}</div>
                  <div style={{ fontSize: 8, color: "var(--color-text-secondary, #aaa)", marginTop: 2 }}>
                    depth {op.delta === Infinity ? "→ ∞" : op.delta > 0 ? `+${op.delta}` : op.delta}
                  </div>
                </button>
              );
            })}
          </div>
          {/* The missing slot */}
          <div style={{
            padding: "8px", borderRadius: 8, textAlign: "center",
            background: "rgba(239,68,68,0.02)", border: "1.5px dashed rgba(239,68,68,0.12)",
          }}>
            <div style={{ fontSize: 10, color: "#EF4444", opacity: 0.4 }}>⚡ depth +3 — this tool does not exist</div>
          </div>

          <button onClick={reset} style={{
            marginTop: 8, padding: "8px 16px", borderRadius: 8, border: "1.5px solid var(--color-border-tertiary, #ddd)",
            background: "var(--color-background-primary, white)", color: "var(--color-text-secondary, #666)",
            fontSize: 11, cursor: "pointer", width: "100%",
          }}>Reset puzzle</button>

          {/* Success */}
          {isSolved && (
            <div style={{
              marginTop: 8, padding: "12px 16px", borderRadius: 10,
              background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.15)",
              textAlign: "center", animation: "fadeIn 0.5s ease",
            }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#059669" }}>
                Transformed! {"★".repeat(stars)}{"☆".repeat(3 - stars)} ({history.length} operation{history.length !== 1 ? "s" : ""})
              </div>
              <div style={{ fontSize: 10, color: "var(--color-text-secondary, #aaa)", marginTop: 2 }}>
                {stars === 3 ? "Perfect — minimum operations!" : stars === 2 ? "Good — one extra operation." : `Par is ${puzzle.par}. Can you do it in fewer?`}
              </div>
              {puzzle.solution && <div style={{ fontSize: 11, color: "var(--color-text-secondary, #888)", marginTop: 4 }}>{puzzle.solution}</div>}
            </div>
          )}
          {impossible.includes(puzzle.id) && (
            <div style={{
              marginTop: 8, padding: "12px 16px", borderRadius: 10,
              background: "rgba(239,68,68,0.04)", border: "1px solid rgba(239,68,68,0.12)",
              textAlign: "center", animation: "fadeIn 0.5s ease",
            }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#EF4444" }}>This transformation is impossible.</div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary, #888)", marginTop: 4, lineHeight: 1.6 }}>
                {puzzle.target === 4
                  ? "EML-4 does not exist. The oscillatory stratum seals itself. Six independent proofs."
                  : "No single operation changes depth by 3. The toolbox has a permanent gap."}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT — puzzle selector */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>Chapters</div>
            {CHAPTERS.map(ch => (
              <div key={ch} style={{ marginBottom: 6 }}>
                <div style={{ fontSize: 9, fontWeight: 600, color: ch === "The Wall" ? "#EF4444" : ch === "The Leap" ? "#FDE68A" : "var(--color-text-secondary, #999)", marginBottom: 3 }}>{ch}</div>
                {PUZZLES.filter(p => p.chapter === ch).map(p => {
                  const idx = PUZZLES.indexOf(p);
                  const s = solved.includes(p.id); const imp = impossible.includes(p.id); const act = idx === currentPuzzle;
                  return (
                    <button key={p.id} onClick={() => loadPuzzle(idx)} style={{
                      display: "block", width: "100%", padding: "4px 8px", marginBottom: 2, borderRadius: 6,
                      textAlign: "left", cursor: "pointer",
                      background: act ? "rgba(245,158,11,0.08)" : "transparent",
                      border: act ? "1px solid rgba(245,158,11,0.2)" : "1px solid transparent",
                    }}>
                      <span style={{ fontSize: 10, color: s ? "#059669" : imp ? "#EF4444" : "var(--color-text-primary, #555)", fontWeight: act ? 600 : 400 }}>
                        {s ? "✓ " : imp ? "✕ " : ""}{p.name}
                      </span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Insight panel */}
          {(solved.length + impossible.length) >= 5 && (
            <div style={{
              padding: "10px 12px", borderRadius: 10,
              background: "rgba(245,158,11,0.04)", border: "1px solid rgba(245,158,11,0.1)",
              animation: "fadeIn 0.5s ease",
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: "#F59E0B", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>What you've discovered</div>
              <div style={{ fontSize: 10, color: "var(--color-text-secondary, #666)", lineHeight: 1.8 }}>
                {solved.length >= 1 && <div>• Integration = depth +2 (always)</div>}
                {solved.length >= 3 && <div>• ∫dμ (+1) + log Z (+1) = +2 exactly</div>}
                {impossible.length >= 1 && <div style={{ color: "#EF4444" }}>• Depth +3 does not exist</div>}
                {impossible.length >= 2 && <div style={{ color: "#EF4444" }}>• EML-4 does not exist</div>}
                {solved.some(id => id >= 9) && <div>• Wick rotation = depth −2</div>}
                {solved.some(id => id >= 13) && <div style={{ color: "#FDE68A" }}>• Categorification = the only path to ∞</div>}
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{
        padding: "0.75rem 1rem", marginTop: 12,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          Every mathematical operation changes depth by a fixed amount. Integration always costs +2. Wick rotation always recovers −2.
          There is no operation that costs +3 — that tool is permanently missing from every mathematician's toolbox.
          That's not a design choice. It's a theorem.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#F59E0B", textDecoration: "none", fontWeight: 500 }}>monogate.dev</a>
        {" · "}
        <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none" }}>arXiv:2603.21852</a>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }
        @media(max-width:600px){.measure-grid{grid-template-columns:1fr!important;}}
      `}</style>
    </div>
  );
}
