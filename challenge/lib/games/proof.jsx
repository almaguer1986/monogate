import { useState, useEffect } from "react";

// ═══════════════════════════════════════════════════════════════════
// THEOREMS — each decomposed into proof blocks
// ═══════════════════════════════════════════════════════════════════
const THEOREMS = [
  {
    id: "exp", name: "exp(x) = eml(x, 1)", difficulty: 1, color: "#06B6D4",
    statement: "The exponential function is a single EML call.",
    blocks: [
      { id: "def", text: "eml(x, y) = exp(x) − ln(y)", type: "definition", order: 0 },
      { id: "sub", text: "Substitute y = 1", type: "step", order: 1 },
      { id: "ln1", text: "ln(1) = 0", type: "fact", order: 2 },
      { id: "result", text: "eml(x, 1) = exp(x) − 0 = exp(x)", type: "conclusion", order: 3 },
    ],
  },
  {
    id: "e", name: "e = eml(1, 1)", difficulty: 1, color: "#10B981",
    statement: "Euler's number is eml applied to its own constant.",
    blocks: [
      { id: "exp_id", text: "exp(x) = eml(x, 1) [from Theorem 1]", type: "reference", order: 0 },
      { id: "sub_x", text: "Substitute x = 1", type: "step", order: 1 },
      { id: "exp1", text: "exp(1) = e ≈ 2.71828", type: "fact", order: 2 },
      { id: "result", text: "eml(1, 1) = exp(1) = e", type: "conclusion", order: 3 },
    ],
  },
  {
    id: "ln", name: "ln(x) = eml(1, eml(eml(1,x), 1))", difficulty: 2, color: "#8B5CF6",
    statement: "The logarithm requires three levels of EML nesting.",
    blocks: [
      { id: "inner", text: "eml(1, x) = exp(1) − ln(x) = e − ln(x)", type: "step", order: 0 },
      { id: "middle", text: "eml(e − ln(x), 1) = exp(e − ln(x))", type: "step", order: 1 },
      { id: "simplify", text: "exp(e − ln(x)) = exp(e) · exp(−ln(x)) = exp(e)/x", type: "step", order: 2 },
      { id: "outer", text: "eml(1, exp(e)/x) = e − ln(exp(e)/x)", type: "step", order: 3 },
      { id: "expand", text: "e − ln(exp(e)) + ln(x) = e − e + ln(x)", type: "step", order: 4 },
      { id: "result", text: "= ln(x) ∎", type: "conclusion", order: 5 },
    ],
  },
  {
    id: "barrier", name: "Infinite Zeros Barrier", difficulty: 3, color: "#EF4444",
    statement: "No finite real EML tree can equal sin(x). Proven on structural grounds.",
    blocks: [
      { id: "premise", text: "Assume: ∃ finite real EML tree T with T(x) = sin(x) ∀x", type: "assumption", order: 0 },
      { id: "analytic", text: "Every finite EML tree is a composition of exp and ln", type: "fact", order: 1 },
      { id: "finite_zeros", text: "Real-analytic functions have finitely many zeros on any bounded interval (unless identically 0)", type: "fact", order: 2 },
      { id: "sin_zeros", text: "sin(x) has infinitely many zeros: x = nπ for all n ∈ ℤ", type: "fact", order: 3 },
      { id: "contradiction", text: "T(x) is real-analytic with finitely many zeros, but sin(x) has infinitely many → contradiction", type: "step", order: 4 },
      { id: "result", text: "No finite real EML tree equals sin(x) ∎", type: "conclusion", order: 5 },
    ],
  },
  {
    id: "bypass", name: "Complex Bypass: sin(x) = Im(eml(ix, 1))", difficulty: 2, color: "#EC4899",
    statement: "One complex EML node recovers sin(x) exactly. The barrier is real-domain only.",
    blocks: [
      { id: "euler", text: "Euler's formula: exp(ix) = cos(x) + i·sin(x)", type: "fact", order: 0 },
      { id: "eml_ix", text: "eml(ix, 1) = exp(ix) − ln(1) = exp(ix)", type: "step", order: 1 },
      { id: "expand", text: "exp(ix) = cos(x) + i·sin(x)", type: "step", order: 2 },
      { id: "im", text: "Im(exp(ix)) = sin(x)", type: "step", order: 3 },
      { id: "result", text: "Im(eml(ix, 1)) = sin(x) exactly, for all x ∈ ℝ ∎", type: "conclusion", order: 4 },
    ],
  },
  {
    id: "closure", name: "EML-3 Self-Closure", difficulty: 3, color: "#F59E0B",
    statement: "eml(EML-3, EML-3) = EML-3. The oscillatory stratum cannot escape itself.",
    blocks: [
      { id: "def3", text: "EML-3 = the stratum of oscillatory functions (sin, cos, Fourier, etc.)", type: "definition", order: 0 },
      { id: "fourier_closed", text: "The Fourier algebra is closed: F(F(f)) = f(−x) ∈ EML-3", type: "fact", order: 1 },
      { id: "product", text: "Product of oscillatory functions is oscillatory: sin·cos = ½sin(2x) ∈ EML-3", type: "fact", order: 2 },
      { id: "eml_compose", text: "eml(f, g) = exp(f) − ln(g). For f,g ∈ EML-3: exp(oscillatory) involves oscillatory modes", type: "step", order: 3 },
      { id: "ring", text: "EML-3 forms a ring under composition. No finite combination leaves depth 3.", type: "step", order: 4 },
      { id: "result", text: "eml(EML-3, EML-3) = EML-3. The stratum is closed. ∎", type: "conclusion", order: 5 },
    ],
  },
  {
    id: "identity", name: "EML Identity Theorem", difficulty: 2, color: "#F97316",
    statement: "A 4-node EML tree computes f(x) = x. The identity function is EML-constructible.",
    blocks: [
      { id: "setup", text: "Goal: construct EML tree T such that T(x) = x for all x > 0.", type: "definition", order: 0 },
      { id: "ln_ref", text: "Theorem 3: ln(x) = eml(1, eml(eml(1,x), 1)) — three nested EML nodes.", type: "reference", order: 1 },
      { id: "wrap", text: "Wrap with one more eml node: eml(ln(x), 1) = exp(ln(x)) − ln(1).", type: "step", order: 2 },
      { id: "ln1", text: "ln(1) = 0, so eml(ln(x), 1) = exp(ln(x)) − 0 = exp(ln(x)).", type: "fact", order: 3 },
      { id: "inverse", text: "exp and ln are inverse functions: exp(ln(x)) = x for all x > 0.", type: "fact", order: 4 },
      { id: "result", text: "A 4-node EML tree computes the identity: eml(ln(x), 1) = x. ∎", type: "conclusion", order: 5 },
    ],
  },
  {
    id: "pumping", name: "EML Pumping Lemma", difficulty: 3, color: "#DC2626",
    statement: "Every depth-k real EML tree has at most 2^k zeros on any bounded interval.",
    blocks: [
      { id: "base", text: "Base case k=1: eml(x, c) = exp(x) − c. exp is strictly monotone → at most 1 zero. 1 ≤ 2¹. ✓", type: "step", order: 0 },
      { id: "hyp", text: "Inductive hypothesis: every depth-(k−1) EML tree has at most 2^(k−1) zeros on [a,b].", type: "assumption", order: 1 },
      { id: "compose", text: "depth-k tree: T = eml(f, g) = exp(f) − g. T(x) = 0 iff exp(f(x)) = g(x).", type: "step", order: 2 },
      { id: "analytic", text: "Both exp(f) and g are real-analytic (finite compositions of exp and ln).", type: "fact", order: 3 },
      { id: "rolle", text: "By Rolle's theorem: zeros(exp(f) − g) ≤ zeros(f′) + zeros(g′) + 1 ≤ 2·2^(k−1) = 2^k.", type: "step", order: 4 },
      { id: "result", text: "Every depth-k EML tree has at most 2^k zeros on [a, b]. sin(x) has infinitely many → EML-∞. ∎", type: "conclusion", order: 5 },
    ],
  },
  {
    id: "weierstrass", name: "EML Weierstrass Theorem", difficulty: 3, color: "#14B8A6",
    statement: "The linear span of EML trees is dense in C[a,b] under the uniform norm.",
    blocks: [
      { id: "classical", text: "Classical Weierstrass: polynomials are dense in C[a,b] under the uniform norm.", type: "fact", order: 0 },
      { id: "monomial", text: "Every monomial xⁿ = exp(n·ln(x)) — an EML-2 composition (for x > 0).", type: "step", order: 1 },
      { id: "linear_span", text: "Linear combinations of EML trees form a vector space closed under addition and scalar multiplication.", type: "fact", order: 2 },
      { id: "poly_in_span", text: "All polynomials Σ aₙxⁿ lie in the EML linear span (finite sums of EML-2 monomials).", type: "step", order: 3 },
      { id: "density", text: "EML span ⊇ polynomials. Polynomials are dense in C[a,b]. Therefore EML span is dense.", type: "step", order: 4 },
      { id: "result", text: "The EML linear span is dense in C[a,b]. Any continuous function is approximable by EML trees. ∎", type: "conclusion", order: 5 },
    ],
  },
];

const TYPE_COLORS = {
  definition: "#64748B",
  fact: "#06B6D4",
  step: "#8B5CF6",
  assumption: "#F59E0B",
  reference: "#10B981",
  conclusion: "#FDE68A",
};

const TYPE_LABELS = {
  definition: "DEF",
  fact: "FACT",
  step: "STEP",
  assumption: "ASSUME",
  reference: "REF",
  conclusion: "∎ QED",
};

// ═══════════════════════════════════════════════════════════════════
// MAIN GAME
// ═══════════════════════════════════════════════════════════════════
export default function Proof() {
  const [selectedTheorem, setSelectedTheorem] = useState(0);
  const [arrangements, setArrangements] = useState({}); // theoremId -> [blockId order]
  const [dragBlock, setDragBlock] = useState(null);
  const [dragOver, setDragOver] = useState(null);
  const [proven, setProven] = useState([]);
  const [showHint, setShowHint] = useState(false);
  const [pulse, setPulse] = useState(0);

  useEffect(() => { let fr; const tick = () => { setPulse(p => p + 0.025); fr = requestAnimationFrame(tick); }; tick(); return () => cancelAnimationFrame(fr); }, []);

  const theorem = THEOREMS[selectedTheorem];

  // Get current arrangement for this theorem (shuffled on first access)
  const getArrangement = () => {
    if (arrangements[theorem.id]) return arrangements[theorem.id];
    // Shuffle blocks
    const shuffled = [...theorem.blocks].sort(() => Math.random() - 0.5).map(b => b.id);
    setArrangements(prev => ({ ...prev, [theorem.id]: shuffled }));
    return shuffled;
  };

  const currentOrder = getArrangement();
  const correctOrder = theorem.blocks.map(b => b.id);

  // Check if current arrangement is correct
  const isCorrect = currentOrder.length === correctOrder.length &&
    currentOrder.every((id, i) => id === correctOrder[i]);

  // Mark as proven when correct
  useEffect(() => {
    if (isCorrect && !proven.includes(theorem.id)) {
      setProven(prev => [...prev, theorem.id]);
    }
  }, [isCorrect, theorem.id, proven]);

  // Drag and drop to reorder
  const handleDragStart = (blockId) => setDragBlock(blockId);
  const handleDragEnter = (blockId) => setDragOver(blockId);

  const handleDrop = (targetId) => {
    if (!dragBlock || dragBlock === targetId) { setDragBlock(null); setDragOver(null); return; }
    const order = [...currentOrder];
    const fromIdx = order.indexOf(dragBlock);
    const toIdx = order.indexOf(targetId);
    order.splice(fromIdx, 1);
    order.splice(toIdx, 0, dragBlock);
    setArrangements(prev => ({ ...prev, [theorem.id]: order }));
    setDragBlock(null);
    setDragOver(null);
  };

  // Click-to-swap (mobile friendly alternative)
  const [swapFirst, setSwapFirst] = useState(null);
  const handleBlockClick = (blockId) => {
    if (isCorrect) return;
    if (!swapFirst) {
      setSwapFirst(blockId);
    } else {
      if (swapFirst === blockId) { setSwapFirst(null); return; }
      const order = [...currentOrder];
      const i = order.indexOf(swapFirst);
      const j = order.indexOf(blockId);
      [order[i], order[j]] = [order[j], order[i]];
      setArrangements(prev => ({ ...prev, [theorem.id]: order }));
      setSwapFirst(null);
    }
  };

  const resetTheorem = () => {
    const shuffled = [...theorem.blocks].sort(() => Math.random() - 0.5).map(b => b.id);
    setArrangements(prev => ({ ...prev, [theorem.id]: shuffled }));
    setSwapFirst(null);
    setShowHint(false);
  };

  // How many blocks are in the correct position?
  const correctCount = currentOrder.filter((id, i) => id === correctOrder[i]).length;
  const totalBlocks = theorem.blocks.length;

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 740, margin: "0 auto", padding: "0 0 2rem" }}>
      {/* Header */}
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.4rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#A78BFA", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>Proof</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          Arrange the proof blocks in the correct logical order. Tap two blocks to swap them.
        </p>
      </div>

      {/* Progress */}
      <div style={{
        textAlign: "center", padding: "6px 14px", margin: "6px 0 10px",
        background: proven.length === THEOREMS.length ? "rgba(16,185,129,0.08)" : "rgba(167,139,250,0.05)",
        borderRadius: 8, fontSize: 12, fontWeight: 500,
        color: proven.length === THEOREMS.length ? "#059669" : "#7C3AED",
      }}>
        {proven.length === THEOREMS.length
          ? "✓ All theorems proven. You are a monogate mathematician."
          : `${proven.length}/${THEOREMS.length} theorems proven`}
      </div>

      <div className="proof-main-grid" style={{ display: "grid", gridTemplateColumns: "1fr 200px", gap: 10 }}>
        {/* PROOF AREA */}
        <div>
          {/* Theorem statement */}
          <div style={{
            padding: "14px 16px", borderRadius: 12, marginBottom: 10,
            background: isCorrect ? "rgba(16,185,129,0.06)" : `${theorem.color}06`,
            border: `1.5px solid ${isCorrect ? "rgba(16,185,129,0.2)" : `${theorem.color}20`}`,
            transition: "all 0.3s",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: isCorrect ? "#059669" : theorem.color, textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>
              {isCorrect ? "✓ Proven!" : `Theorem — difficulty ${"★".repeat(theorem.difficulty)}${"☆".repeat(3 - theorem.difficulty)}`}
            </div>
            <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-text-primary, #1a1a2e)", fontFamily: "var(--font-mono)", marginBottom: 4 }}>{theorem.name}</div>
            <div style={{ fontSize: 12, color: "var(--color-text-secondary, #666)" }}>{theorem.statement}</div>
          </div>

          {/* Position indicator */}
          {!isCorrect && (
            <div style={{ fontSize: 11, color: "var(--color-text-secondary, #999)", marginBottom: 6, textAlign: "center" }}>
              {correctCount}/{totalBlocks} blocks in correct position
              {swapFirst && <span style={{ color: "#F59E0B" }}> — tap another block to swap</span>}
            </div>
          )}

          {/* PROOF BLOCKS — draggable/swappable */}
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {currentOrder.map((blockId, index) => {
              const block = theorem.blocks.find(b => b.id === blockId);
              if (!block) return null;
              const inCorrectPos = correctOrder[index] === blockId;
              const isSwapSelected = swapFirst === blockId;
              const tc = TYPE_COLORS[block.type];

              return (
                <div key={blockId}
                  draggable={!isCorrect}
                  onDragStart={() => handleDragStart(blockId)}
                  onDragEnter={() => handleDragEnter(blockId)}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={() => handleDrop(blockId)}
                  onDragEnd={() => { setDragBlock(null); setDragOver(null); }}
                  onClick={() => handleBlockClick(blockId)}
                  style={{
                    display: "flex", alignItems: "center", gap: 10,
                    padding: "10px 14px", borderRadius: 10,
                    cursor: isCorrect ? "default" : "pointer",
                    background: isCorrect
                      ? inCorrectPos ? "rgba(16,185,129,0.06)" : "var(--color-background-secondary, #f8f5ff)"
                      : isSwapSelected ? `${tc}15`
                      : dragOver === blockId ? "rgba(139,92,246,0.08)"
                      : "var(--color-background-secondary, #f8f5ff)",
                    border: isCorrect
                      ? inCorrectPos ? "1.5px solid rgba(16,185,129,0.2)" : "1.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))"
                      : isSwapSelected ? `2px solid ${tc}`
                      : `1.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))`,
                    transition: "all 0.15s",
                    userSelect: "none",
                    opacity: dragBlock === blockId ? 0.4 : 1,
                  }}>
                  {/* Position number */}
                  <div style={{
                    width: 22, height: 22, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center",
                    background: isCorrect && inCorrectPos ? "#059669" : inCorrectPos ? "rgba(16,185,129,0.15)" : "var(--color-background-primary, white)",
                    border: `1px solid ${isCorrect && inCorrectPos ? "#059669" : inCorrectPos ? "rgba(16,185,129,0.3)" : "var(--color-border-tertiary, rgba(0,0,0,0.08))"}`,
                    fontSize: 10, fontWeight: 600, fontFamily: "var(--font-mono)",
                    color: isCorrect && inCorrectPos ? "white" : inCorrectPos ? "#059669" : "var(--color-text-secondary, #aaa)",
                  }}>{index + 1}</div>

                  {/* Type badge */}
                  <div style={{
                    padding: "2px 6px", borderRadius: 4, fontSize: 8, fontWeight: 600,
                    background: `${tc}15`, color: tc, letterSpacing: 0.5,
                    textTransform: "uppercase", whiteSpace: "nowrap",
                  }}>{TYPE_LABELS[block.type]}</div>

                  {/* Block text */}
                  <div style={{
                    flex: 1, fontSize: 12,
                    fontFamily: block.type === "conclusion" ? "var(--font-mono, monospace)" : "var(--font-sans)",
                    color: block.type === "conclusion" ? "#FDE68A" : "var(--color-text-primary, #333)",
                    fontWeight: block.type === "conclusion" ? 600 : 400,
                    lineHeight: 1.4,
                  }}>{block.text}</div>

                  {/* Correct indicator */}
                  {isCorrect && inCorrectPos && (
                    <span style={{ fontSize: 14, color: "#059669" }}>✓</span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Controls */}
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <button onClick={resetTheorem} style={{
              padding: "8px 16px", borderRadius: 8, border: "1.5px solid var(--color-border-tertiary, #ddd)",
              background: "var(--color-background-primary, white)", color: "var(--color-text-secondary, #666)",
              fontSize: 11, cursor: "pointer",
            }}>Shuffle</button>
            <button onClick={() => setShowHint(h => !h)} style={{
              padding: "8px 16px", borderRadius: 8, border: `1.5px solid ${showHint ? "#F59E0B40" : "var(--color-border-tertiary, #ddd)"}`,
              background: showHint ? "rgba(245,158,11,0.06)" : "var(--color-background-primary, white)",
              color: showHint ? "#D97706" : "var(--color-text-secondary, #666)",
              fontSize: 11, cursor: "pointer",
            }}>{showHint ? "Hide hint" : "Hint"}</button>
          </div>

          {showHint && !isCorrect && (
            <div style={{
              marginTop: 8, padding: "10px 14px", borderRadius: 8,
              background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.12)",
              fontSize: 11, color: "#D97706", lineHeight: 1.6,
            }}>
              {theorem.id === "exp" && "Start with the definition of eml. Then substitute y = 1. What is ln(1)?"}
              {theorem.id === "e" && "Use the result from Theorem 1. What happens when x = 1?"}
              {theorem.id === "ln" && "Work from the inside out. Start with eml(1, x), then wrap it, then wrap again."}
              {theorem.id === "barrier" && "Start with the assumption (proof by contradiction). Then establish facts about EML trees and sin(x). The contradiction comes from zero counts."}
              {theorem.id === "bypass" && "Start with Euler's formula. Apply eml with ix. Then take the imaginary part."}
              {theorem.id === "closure" && "Define EML-3 first. Establish that Fourier algebra is closed. Then show products stay oscillatory. The ring structure follows."}
              {theorem.id === "identity" && "You already proved ln(x) in Theorem 3. Wrap it in one more eml call with y=1. What does exp(ln(x)) equal?"}
              {theorem.id === "pumping" && "Start with the base case k=1. State the inductive hypothesis. A depth-k tree is eml(f,g) — use Rolle's theorem to count zeros of exp(f)−g."}
              {theorem.id === "weierstrass" && "Start with the classical Weierstrass theorem. Then show monomials xⁿ are EML-2. Linear combinations of EML trees include all polynomials — and polynomials are already dense."}
            </div>
          )}

          {/* Success message */}
          {isCorrect && (
            <div style={{
              marginTop: 10, padding: "14px 18px", borderRadius: 10,
              background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.15)",
              textAlign: "center", animation: "fadeIn 0.5s ease",
            }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: "#059669", marginBottom: 4 }}>Theorem proven. ∎</div>
              <div style={{ fontSize: 12, color: "var(--color-text-secondary, #888)" }}>
                The proof is logically valid. Each step follows from the previous.
              </div>
            </div>
          )}
        </div>

        {/* RIGHT PANEL — theorem selector */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>Theorems</div>
            {THEOREMS.map((t, i) => {
              const isProven = proven.includes(t.id);
              const isActive = i === selectedTheorem;
              return (
                <button key={t.id} onClick={() => { setSelectedTheorem(i); setSwapFirst(null); setShowHint(false); }}
                  style={{
                    display: "block", width: "100%", padding: "8px 10px", marginBottom: 4, borderRadius: 8,
                    textAlign: "left", cursor: "pointer",
                    background: isActive ? `${t.color}12` : "var(--color-background-primary, white)",
                    border: isActive ? `1.5px solid ${t.color}30` : "1px solid var(--color-border-tertiary, rgba(0,0,0,0.04))",
                  }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: 11, fontWeight: 600, color: isProven ? "#059669" : t.color }}>
                      {isProven ? "✓ " : ""}{t.name}
                    </span>
                    <span style={{ fontSize: 9, color: "var(--color-text-secondary, #aaa)" }}>
                      {"★".repeat(t.difficulty)}
                    </span>
                  </div>
                  <div style={{ fontSize: 9, color: "var(--color-text-secondary, #999)", marginTop: 2 }}>
                    {t.blocks.length} steps
                  </div>
                </button>
              );
            })}
          </div>

          {/* Stats */}
          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Progress</div>
            <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #1a1a2e)" }}>
              {proven.length}/{THEOREMS.length}
            </div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)" }}>theorems proven</div>
            {proven.length >= 3 && (
              <div style={{ fontSize: 9, color: "#A78BFA", fontStyle: "italic", marginTop: 6 }}>
                {proven.length >= THEOREMS.length ? "You've proven everything. Mastery." : "You're thinking like a mathematician now."}
              </div>
            )}
          </div>

          {/* How to play */}
          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>How to play</div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #666)", lineHeight: 1.7 }}>
              The proof blocks are shuffled. Tap two blocks to swap their positions. Arrange them in valid logical order — each step should follow from the previous. The number badge turns green when a block is in the right position.
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: "0.75rem 1rem", marginTop: 12,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          Mathematics isn't about knowing theorems — it's about understanding WHY they're true.
          Each proof is a chain of logic. Your job: find the right order.
          From simple identities to the Infinite Zeros Barrier — prove them all.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none", fontWeight: 500 }}>monogate.dev</a>
        {" · "}
        <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: "#7C3AED", textDecoration: "none" }}>arXiv:2603.21852</a>
      </div>

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } } @media(max-width:600px){.proof-main-grid{grid-template-columns:1fr!important;}}`}</style>
    </div>
  );
}
