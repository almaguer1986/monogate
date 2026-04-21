import { useState, useRef, useEffect } from "react";

const TARGET_FN = (x) => Math.exp(-x);

const OPERATORS = [
  { id: "eml", name: "EML", formula: "exp(a) − ln(b)", constant: "1",
    gate: (a, b) => Math.exp(a) - Math.log(Math.max(b, 1e-10)),
    color: "#A78BFA", mse: 0.5495,
    why: "eml(x, 1) = exp(x). Positive exponent only. The subtraction of ln(b) can't negate the exp(a) argument for all x." },
  { id: "edl", name: "EDL", formula: "exp(a) / ln(b)", constant: "e",
    gate: (a, b) => { const lb = Math.log(Math.max(b, 1e-10)); return lb === 0 ? Infinity : Math.exp(a) / lb; },
    color: "#06B6D4", mse: 0.5495,
    why: "edl(x, e) = exp(x)/ln(e) = exp(x). Same positive exponent. Division by ln(b) can't flip the sign of the entire exp." },
  { id: "exl", name: "EXL", formula: "exp(a) × ln(b)", constant: "1",
    gate: (a, b) => Math.exp(a) * Math.log(Math.max(b, 1e-10)),
    color: "#EC4899", mse: 0.1453,
    why: "EXL gets closer (MSE 0.145 vs 0.549) because exp(a)×ln(b) can produce decaying shapes via the logarithmic factor. But it can't reach zero MSE — the multiplicative structure can approximate but never exactly match exp(−x)." },
  { id: "eal", name: "EAL", formula: "exp(a) + ln(b)", constant: "1",
    gate: (a, b) => Math.exp(a) + Math.log(Math.max(b, 1e-10)),
    color: "#F59E0B", mse: null,
    why: "EAL adds exp and ln — both terms have the wrong monotonicity to produce a decaying exponential. Blocked." },
  { id: "emn", name: "EMN", formula: "ln(b) − exp(a)", constant: "−∞",
    gate: (a, b) => Math.log(Math.max(b, 1e-10)) - Math.exp(a),
    color: "#64748B", mse: null,
    why: "EMN = ln(b) − exp(a). This is always negative for large a (exp dominates). Can't produce the positive values of exp(−x). Blocked." },
];

const DEML = {
  id: "deml", name: "DEML", formula: "exp(−a) − ln(b)", constant: "1",
  gate: (a, b) => Math.exp(-a) - Math.log(Math.max(b, 1e-10)),
  color: "#10B981",
  proof: [
    { step: "deml(x, 1)", expansion: "exp(−x) − ln(1)", result: "exp(−x) − 0 = exp(−x)" },
  ],
  applications: [
    { name: "Radioactive decay", formula: "N(t) = N₀ · exp(−λt)", arg: "λt", nodes: 1 },
    { name: "RC discharge", formula: "V(t) = V₀ · exp(−t/τ)", arg: "t/τ", nodes: 1 },
    { name: "Boltzmann factor", formula: "P(E) = exp(−E/kT)", arg: "E/kT", nodes: 1 },
    { name: "Cooling law", formula: "ΔT(t) = ΔT₀ · exp(−t/τ)", arg: "t/τ", nodes: 1 },
    { name: "Discount factor", formula: "D(T) = exp(−rT)", arg: "rT", nodes: 1 },
  ],
};

function GraphCanvas({ triedOps, demlUnlocked }) {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height;
    let t = 0, fr;
    const draw = () => {
      t += 0.01;
      ctx.fillStyle = "rgba(6,2,14,0.08)"; ctx.fillRect(0, 0, w, h);
      const margin = { left: 40, right: 15, top: 15, bottom: 25 };
      const gw = w - margin.left - margin.right, gh = h - margin.top - margin.bottom;
      const xMin = -0.5, xMax = 4, yMin = -0.5, yMax = 1.5;
      const toX = (x) => margin.left + ((x - xMin) / (xMax - xMin)) * gw;
      const toY = (y) => margin.top + (1 - (y - yMin) / (yMax - yMin)) * gh;
      // Grid
      ctx.strokeStyle = "rgba(167,139,250,0.04)"; ctx.lineWidth = 0.5;
      for (let y = 0; y <= 1.5; y += 0.5) { ctx.beginPath(); ctx.moveTo(margin.left, toY(y)); ctx.lineTo(w - margin.right, toY(y)); ctx.stroke(); }
      ctx.fillStyle = "rgba(167,139,250,0.1)"; ctx.font = "8px monospace"; ctx.textAlign = "right";
      for (let y = 0; y <= 1.5; y += 0.5) ctx.fillText(y.toFixed(1), margin.left - 4, toY(y) + 3);
      // Axes
      ctx.strokeStyle = "rgba(167,139,250,0.08)"; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(toX(0), margin.top); ctx.lineTo(toX(0), h - margin.bottom); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(margin.left, toY(0)); ctx.lineTo(w - margin.right, toY(0)); ctx.stroke();
      // Target: exp(-x)
      ctx.beginPath();
      for (let px = 0; px < gw; px += 2) {
        const x = xMin + (px / gw) * (xMax - xMin);
        const y = TARGET_FN(x);
        const sx = margin.left + px, sy = toY(y);
        if (px === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
      }
      ctx.strokeStyle = "rgba(255,255,255,0.4)"; ctx.lineWidth = 2.5; ctx.setLineDash([6, 3]); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = "rgba(255,255,255,0.3)"; ctx.font = "10px monospace"; ctx.textAlign = "left";
      ctx.fillText("target: exp(−x)", toX(0.3), toY(TARGET_FN(0.3)) - 8);
      // Failed operator attempts
      triedOps.forEach(opId => {
        const op = OPERATORS.find(o => o.id === opId);
        if (!op) return;
        ctx.beginPath();
        for (let px = 0; px < gw; px += 2) {
          const x = xMin + (px / gw) * (xMax - xMin);
          let y;
          if (op.id === "eml") y = Math.exp(x); // Best depth-1: eml(x,1) = exp(x)
          else if (op.id === "edl") y = Math.exp(x); // Same
          else if (op.id === "exl") y = Math.exp(x) * Math.log(Math.max(Math.exp(-x * 0.3) + 1, 0.01)); // Approximate
          else if (op.id === "eal") y = Math.exp(x * 0.3) + Math.log(Math.max(x + 1, 0.01));
          else y = Math.log(Math.max(x + 1, 0.01)) - Math.exp(x * 0.2);
          y = Math.max(yMin, Math.min(yMax, y));
          const sx = margin.left + px, sy = toY(y);
          if (px === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
        }
        ctx.strokeStyle = `${op.color}50`; ctx.lineWidth = 1.5; ctx.stroke();
      });
      // DEML success
      if (demlUnlocked) {
        ctx.beginPath();
        for (let px = 0; px < gw; px += 2) {
          const x = xMin + (px / gw) * (xMax - xMin);
          const y = Math.exp(-x);
          const sx = margin.left + px, sy = toY(y);
          if (px === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
        }
        ctx.strokeStyle = "#10B981"; ctx.lineWidth = 3; ctx.stroke();
        ctx.fillStyle = "rgba(16,185,129,0.4)"; ctx.font = "11px monospace"; ctx.textAlign = "right";
        ctx.fillText("deml(x, 1) = exp(−x) ✓", w - margin.right - 4, toY(TARGET_FN(2)) + 14);
      }
      // BLOCKED label
      if (triedOps.length >= 5 && !demlUnlocked) {
        ctx.fillStyle = `rgba(239,68,68,${0.08 + Math.sin(t * 2) * 0.03})`; ctx.font = "bold 16px monospace"; ctx.textAlign = "center";
        ctx.fillText("ALL FIVE BLOCKED", w / 2, h / 2);
      }
      fr = requestAnimationFrame(draw);
    };
    ctx.fillStyle = "#06020E"; ctx.fillRect(0, 0, w, h); draw();
    return () => cancelAnimationFrame(fr);
  }, [triedOps, demlUnlocked]);
  return <canvas ref={ref} width={580} height={280} style={{ width: "100%", display: "block", borderRadius: 12 }}
    role="img" aria-label="Graph showing exp(-x) target and operator attempts" />;
}

export default function NegativeExponent() {
  const [triedOps, setTriedOps] = useState([]);
  const [demlUnlocked, setDemlUnlocked] = useState(false);
  const [selectedOp, setSelectedOp] = useState(null);

  const tryOperator = (id) => {
    if (!triedOps.includes(id)) setTriedOps(prev => [...prev, id]);
    setSelectedOp(id);
  };

  const allTried = triedOps.length >= 5;

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 620, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.5rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#EF4444", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>The Negative Exponent</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          Build exp(−x) from the EML operator family. Try all five. Watch them all fail.
        </p>
      </div>

      {/* Graph */}
      <div style={{ borderRadius: 14, overflow: "hidden", border: `1px solid ${demlUnlocked ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.1)"}`, marginBottom: 10 }}>
        <GraphCanvas triedOps={triedOps} demlUnlocked={demlUnlocked} />
      </div>

      {/* The challenge */}
      <div style={{ padding: "10px 14px", borderRadius: 10, background: "rgba(167,139,250,0.03)", border: "1px solid rgba(167,139,250,0.06)", marginBottom: 10, textAlign: "center" }}>
        <div style={{ fontSize: 12, color: "var(--color-text-secondary, #666)" }}>
          The dashed white line is <span style={{ fontFamily: "var(--font-mono)", color: "#A78BFA" }}>exp(−x)</span> — the universal decay function. 
          Every operator below uses <span style={{ fontFamily: "var(--font-mono)", color: "#A78BFA" }}>exp(a)</span> as its first component. 
          Since leaves are {"{x, constants}"}, the exponent argument can never be −x for all x.
        </div>
      </div>

      {/* Operator buttons */}
      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-secondary, #999)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
        Try each operator ({triedOps.length}/5 attempted)
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 5, marginBottom: 10 }}>
        {OPERATORS.map(op => {
          const tried = triedOps.includes(op.id);
          const isSel = selectedOp === op.id;
          return (
            <button key={op.id} onClick={() => tryOperator(op.id)} style={{
              padding: "10px 6px", borderRadius: 8, cursor: "pointer", textAlign: "center",
              background: tried ? `${op.color}10` : "var(--color-background-secondary, #faf5ff)",
              border: isSel ? `2px solid ${op.color}` : tried ? `1.5px solid ${op.color}20` : "1.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
              transition: "all 0.15s",
            }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: op.color }}>{op.name}</div>
              <div style={{ fontSize: 8, color: "var(--color-text-secondary, #999)", marginTop: 2 }}>{op.formula.split(" ")[0]}...</div>
              {tried && <div style={{ fontSize: 9, color: "#EF4444", fontWeight: 600, marginTop: 3 }}>BLOCKED</div>}
            </button>
          );
        })}
      </div>

      {/* Selected operator detail */}
      {selectedOp && (() => {
        const op = OPERATORS.find(o => o.id === selectedOp);
        return op ? (
          <div style={{
            padding: "12px 16px", borderRadius: 10, marginBottom: 10,
            background: "rgba(239,68,68,0.03)", border: `1px solid ${op.color}15`,
            animation: "fadeIn 0.2s ease",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: op.color }}>{op.name}: {op.formula}</div>
              {op.mse !== null && <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "#EF4444" }}>MSE: {op.mse}</div>}
            </div>
            <div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", lineHeight: 1.6 }}>{op.why}</div>
            <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #999)", marginTop: 4 }}>
              Constant: {op.constant} · Complete: {op.id === "eml" || op.id === "edl" ? "Yes" : "No"}
            </div>
          </div>
        ) : null;
      })()}

      {/* All blocked — structural reason */}
      {allTried && !demlUnlocked && (
        <div style={{
          padding: "14px 18px", borderRadius: 12, marginBottom: 10,
          background: "rgba(239,68,68,0.04)", border: "1.5px solid rgba(239,68,68,0.12)",
          animation: "fadeIn 0.5s ease",
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#EF4444", marginBottom: 6 }}>All five blocked. Here's why:</div>
          <div style={{ fontSize: 12, color: "var(--color-text-secondary, #666)", lineHeight: 1.7 }}>
            Every operator in the EML family uses exp(a) as its first component, where a is built from 
            leaves {"{x, constants}"}. The subtree a evaluates to a positive-coefficient expression, so 
            the exponent is always positive for positive x. No combination of exp, ln, ×, /, +, − applied 
            to exp(positive) can produce exp(negative) for all x simultaneously. 
            The barrier is structural — no MCTS budget or search depth can resolve it.
          </div>
          <div style={{ fontSize: 12, color: "var(--color-text-secondary, #666)", lineHeight: 1.7, marginTop: 8 }}>
            This blocks every decay law in physics: radioactive decay, RC discharge, Boltzmann factors, 
            cooling laws, discount factors. All require exp(−x). None are reachable.
          </div>
          <button onClick={() => setDemlUnlocked(true)} style={{
            display: "block", width: "100%", marginTop: 12, padding: "14px", borderRadius: 10,
            cursor: "pointer",
            background: "rgba(16,185,129,0.08)", border: "2px solid rgba(16,185,129,0.2)",
            fontSize: 14, fontWeight: 700, color: "#10B981",
          }}>Introduce the DEML gate</button>
        </div>
      )}

      {/* DEML solution */}
      {demlUnlocked && (
        <div style={{
          padding: "16px 20px", borderRadius: 14, marginBottom: 10,
          background: "rgba(16,185,129,0.04)", border: "2px solid rgba(16,185,129,0.15)",
          animation: "fadeIn 0.5s ease",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#10B981" }}>DEML</div>
            <div style={{ fontSize: 13, fontFamily: "var(--font-mono)", color: "#10B981" }}>exp(−a) − ln(b) · constant = 1</div>
          </div>

          {/* The proof */}
          <div style={{ padding: "10px 14px", borderRadius: 8, background: "var(--color-background-primary, white)", border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))", marginBottom: 10 }}>
            <div style={{ fontSize: 10, fontWeight: 600, color: "#10B981", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Proof (1 step)</div>
            {DEML.proof.map((p, i) => (
              <div key={i} style={{ fontSize: 13, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #444)", lineHeight: 1.8 }}>
                {p.step} = {p.expansion} = <span style={{ color: "#10B981", fontWeight: 700 }}>{p.result}</span>
              </div>
            ))}
            <div style={{ fontSize: 11, color: "var(--color-text-secondary, #888)", marginTop: 4 }}>
              ln(1) = 0, so deml(x, 1) = exp(−x). One node. Exact. The barrier dissolves.
            </div>
          </div>

          {/* What this unlocks */}
          <div style={{ fontSize: 11, fontWeight: 600, color: "#10B981", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
            What DEML unlocks: every decay law is now 1 node
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(1, 1fr)", gap: 4 }}>
            {DEML.applications.map(app => (
              <div key={app.name} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "6px 10px", borderRadius: 6, background: "rgba(16,185,129,0.04)",
              }}>
                <div>
                  <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary, #444)" }}>{app.name}</span>
                  <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #999)", marginLeft: 8 }}>{app.formula}</span>
                </div>
                <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "#10B981", fontWeight: 600 }}>
                  deml({app.arg}, 1) · {app.nodes} node
                </div>
              </div>
            ))}
          </div>

          <div style={{
            marginTop: 10, padding: "8px 12px", borderRadius: 8,
            background: "rgba(16,185,129,0.04)", border: "1px solid rgba(16,185,129,0.08)",
          }}>
            <div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", lineHeight: 1.6 }}>
              DEML is not complete — it can express exp(−x) but not exp(+x). Paired with EML in the 
              BEST router, both signs become 1-node primitives. The negative-exponent barrier is 
              resolved by extending the grammar, not by searching harder within the existing one.
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{
        padding: "0.75rem 1rem", marginTop: 10,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          The negative-exponent barrier is a fundamental limitation of the EML operator family. 
          All five operators (EML, EDL, EXL, EAL, EMN) use exp(a) with a built from positive-coefficient 
          leaves, so the exponent can never be −x for all x. This blocks every exponential decay law 
          in physics and finance. The DEML dual gate — deml(x,y) = exp(−x) − ln(y) — resolves 
          the barrier in one node: deml(x, 1) = exp(−x). DEML + EML together cover both signs.
          Data from §16 (operator comparison) and §19 (DEML gate) of the research notes.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.org" target="_blank" rel="noopener noreferrer" style={{ color: "#10B981", textDecoration: "none", fontWeight: 500 }}>monogate.org</a>
        {" · "}<a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#06B6D4", textDecoration: "none" }}>monogate.dev</a>
      </div>

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }`}</style>
    </div>
  );
}
