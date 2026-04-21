"use client";

import { useState, useEffect, useRef } from "react";
import type { Metadata } from "next";

const eml = (x: number, y: number) => {
  if (y <= 0) return Math.exp(x);
  const lny = Math.log(y);
  return Math.exp(x) - lny;
};

function EmlCalc() {
  const [x, setX] = useState(1);
  const [y, setY] = useState(1);
  const result = eml(x, y);
  return (
    <div style={{ padding: "20px 24px", borderRadius: 14, background: "rgba(167,139,250,0.04)", border: "1px solid rgba(167,139,250,0.12)", margin: "20px 0" }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: "#A78BFA", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>Try it yourself</div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", justifyContent: "center" }}>
        <span style={{ fontSize: 16, color: "#A78BFA", fontFamily: "monospace" }}>eml(</span>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <input type="range" min="-2" max="3" step="0.1" value={x} onChange={e => setX(Number(e.target.value))}
            aria-label="x value" style={{ width: 80, accentColor: "#A78BFA", cursor: "pointer" }} />
          <span style={{ fontSize: 13, fontFamily: "monospace", color: "#A78BFA" }}>{x.toFixed(1)}</span>
        </div>
        <span style={{ fontSize: 16, color: "#666" }}>,</span>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <input type="range" min="0.1" max="5" step="0.1" value={y} onChange={e => setY(Number(e.target.value))}
            aria-label="y value" style={{ width: 80, accentColor: "#06B6D4", cursor: "pointer" }} />
          <span style={{ fontSize: 13, fontFamily: "monospace", color: "#06B6D4" }}>{y.toFixed(1)}</span>
        </div>
        <span style={{ fontSize: 16, color: "#A78BFA", fontFamily: "monospace" }}>)</span>
        <span style={{ fontSize: 16, color: "#666" }}>=</span>
        <span style={{ fontSize: 20, fontWeight: 700, fontFamily: "monospace", color: "#EC4899", minWidth: 80, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
          {isFinite(result) ? result.toFixed(4) : "∞"}
        </span>
      </div>
      <div style={{ fontSize: 11, color: "#999", textAlign: "center", marginTop: 8 }}>
        exp({x.toFixed(1)}) − ln({y.toFixed(1)}) = {isFinite(Math.exp(x)) ? Math.exp(x).toFixed(4) : "∞"} − {Math.log(y).toFixed(4)} = {isFinite(result) ? result.toFixed(4) : "∞"}
      </div>
    </div>
  );
}

function ExpDemo() {
  const [x, setX] = useState(1);
  return (
    <div style={{ padding: "16px 20px", borderRadius: 12, background: "rgba(6,182,212,0.04)", border: "1px solid rgba(6,182,212,0.1)", margin: "16px 0" }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: "#06B6D4", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>One node. That&apos;s all.</div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, justifyContent: "center", flexWrap: "wrap" }}>
        <span style={{ fontFamily: "monospace", color: "#06B6D4", fontSize: 15 }}>eml(</span>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 140 }}>
          <input type="range" min="-2" max="4" step="0.1" value={x} onChange={e => setX(Number(e.target.value))}
            aria-label="x value for exp" style={{ width: "100%", accentColor: "#06B6D4", cursor: "pointer" }} />
          <span style={{ fontFamily: "monospace", color: "#06B6D4", fontSize: 13, marginTop: 2 }}>{x.toFixed(1)}</span>
        </div>
        <span style={{ fontFamily: "monospace", color: "#06B6D4", fontSize: 15 }}>, 1) =</span>
        <span style={{ fontSize: 24, fontWeight: 700, fontFamily: "monospace", color: "#06B6D4", minWidth: 90, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
          {Math.exp(x) < 100 ? Math.exp(x).toFixed(3) : Math.exp(x).toFixed(1)}
        </span>
      </div>
      <div style={{ fontSize: 11, color: "#888", textAlign: "center", marginTop: 8 }}>
        When y = 1, ln(1) = 0, so eml(x, 1) = exp(x). One node. The exponential function.
      </div>
    </div>
  );
}

function NodeCounter() {
  const ops = [
    { name: "exp(x)", nodes: 1, best: 1, color: "#06B6D4" },
    { name: "ln(x)", nodes: 4, best: 1, color: "#8B5CF6" },
    { name: "x + y", nodes: 11, best: 11, color: "#64748B" },
    { name: "x × y", nodes: 13, best: 7, color: "#64748B" },
    { name: "x ÷ y", nodes: 15, best: 1, color: "#64748B" },
    { name: "x²", nodes: 9, best: 5, color: "#06B6D4" },
    { name: "sin(x)", nodes: 108, best: 1, color: "#EC4899" },
  ];
  const [showBest, setShowBest] = useState(false);
  const totalPure = ops.reduce((a, o) => a + o.nodes, 0);
  const totalBest = ops.reduce((a, o) => a + o.best, 0);
  return (
    <div style={{ padding: "20px 24px", borderRadius: 14, background: "rgba(139,92,246,0.04)", border: "1px solid rgba(139,92,246,0.1)", margin: "20px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: "#8B5CF6", textTransform: "uppercase", letterSpacing: 1 }}>Node count</div>
        <button onClick={() => setShowBest(!showBest)} style={{
          padding: "4px 12px", borderRadius: 6, border: "none", cursor: "pointer",
          background: showBest ? "rgba(16,185,129,0.1)" : "rgba(139,92,246,0.08)",
          color: showBest ? "#10B981" : "#8B5CF6", fontSize: 10, fontWeight: 600,
        }}>{showBest ? "BEST routing ON" : "Pure EML"}</button>
      </div>
      {ops.map(op => {
        const count = showBest ? op.best : op.nodes;
        const pct = (count / 108) * 100;
        const saved = op.nodes - op.best;
        return (
          <div key={op.name} style={{ marginBottom: 6 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 2 }}>
              <span style={{ fontSize: 12, fontFamily: "monospace", color: "#d4d4d4", fontWeight: 500 }}>{op.name}</span>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 13, fontFamily: "monospace", fontWeight: 700, color: op.color, fontVariantNumeric: "tabular-nums" }}>{count}</span>
                {showBest && saved > 0 && <span style={{ fontSize: 9, color: "#10B981", fontWeight: 600 }}>−{saved}</span>}
              </div>
            </div>
            <div style={{ height: 6, borderRadius: 3, background: "rgba(255,255,255,0.04)", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${Math.max(1, pct)}%`, background: op.color, borderRadius: 3, transition: "width 0.5s ease" }} />
            </div>
          </div>
        );
      })}
      <div style={{ marginTop: 10, display: "flex", justifyContent: "space-between", fontSize: 12, fontFamily: "monospace" }}>
        <span style={{ color: "#999" }}>Total:</span>
        <span style={{ fontWeight: 700, color: showBest ? "#10B981" : "#8B5CF6" }}>
          {showBest ? totalBest : totalPure} nodes
          {showBest && <span style={{ color: "#10B981", marginLeft: 8 }}>({Math.round((1 - totalBest / totalPure) * 100)}% savings)</span>}
        </span>
      </div>
    </div>
  );
}

function SinBarrier() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [bypassed, setBypassed] = useState(false);
  const visibleRef = useRef(true);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    const c = canvasRef.current; if (!c) return;
    const observer = new IntersectionObserver(([entry]) => { visibleRef.current = entry.isIntersecting; }, { threshold: 0.1 });
    observer.observe(c);

    const ctx = c.getContext("2d")!; const w = c.width, h = c.height;
    let t = 0;
    const draw = () => {
      if (visibleRef.current) {
        t += 0.02;
        ctx.fillStyle = bypassed ? "rgba(6,2,14,0.06)" : "rgba(20,2,2,0.06)";
        ctx.fillRect(0, 0, w, h);
        if (bypassed) {
          ctx.beginPath();
          for (let px = 0; px < w; px++) {
            const x = (px / w) * 4 * Math.PI - 2 * Math.PI + t;
            const y = h / 2 - Math.sin(x) * (h / 2 - 20);
            if (px === 0) ctx.moveTo(px, y); else ctx.lineTo(px, y);
          }
          ctx.strokeStyle = "#EC4899"; ctx.lineWidth = 2.5; ctx.stroke();
          for (let i = -3; i <= 3; i++) {
            const zeroX = ((i * Math.PI + 2 * Math.PI - t) / (4 * Math.PI)) * w;
            if (zeroX > 0 && zeroX < w) {
              ctx.beginPath(); ctx.arc(zeroX, h / 2, 4 + Math.sin(t * 3) * 1, 0, Math.PI * 2);
              ctx.fillStyle = "rgba(236,72,153,0.3)"; ctx.fill();
            }
          }
          ctx.fillStyle = "rgba(236,72,153,0.15)"; ctx.font = "10px monospace"; ctx.textAlign = "center";
          ctx.fillText("sin(x) = Im(eml(ix, 1))", w / 2, 20);
          ctx.fillText("1 complex node", w / 2, h - 12);
        } else {
          for (let attempt = 0; attempt < 4; attempt++) {
            ctx.beginPath();
            for (let px = 0; px < w; px++) {
              const xv = (px / w) * 4 * Math.PI;
              const approx = attempt === 0 ? Math.sin(xv) * Math.exp(-Math.abs(xv - 2 * Math.PI) * 0.3)
                : attempt === 1 ? Math.sin(xv) * (1 - (xv / (4 * Math.PI)) * (xv / (4 * Math.PI)))
                : attempt === 2 ? xv - (xv * xv * xv) / 6 + (xv * xv * xv * xv * xv) / 120
                : Math.sin(xv) + (Math.random() - 0.5) * 0.3;
              const y = h / 2 - approx * (h / 2 - 20);
              if (px === 0) ctx.moveTo(px, y); else ctx.lineTo(px, y);
            }
            ctx.strokeStyle = `rgba(239,68,68,${0.15 - attempt * 0.03})`; ctx.lineWidth = 1; ctx.stroke();
          }
          ctx.fillStyle = `rgba(239,68,68,${0.1 + Math.sin(t * 2) * 0.03})`; ctx.font = "bold 14px monospace"; ctx.textAlign = "center";
          ctx.fillText("IMPOSSIBLE", w / 2, h / 2 - 5);
          ctx.fillStyle = "rgba(239,68,68,0.06)"; ctx.font = "9px monospace";
          ctx.fillText("infinite zeros require infinite nodes", w / 2, h / 2 + 12);
        }
      }
      frameRef.current = requestAnimationFrame(draw);
    };
    ctx.fillStyle = "#140202"; ctx.fillRect(0, 0, w, h); draw();
    return () => { if (frameRef.current) cancelAnimationFrame(frameRef.current); observer.disconnect(); };
  }, [bypassed]);

  return (
    <div style={{ margin: "20px 0" }}>
      <div style={{ borderRadius: 12, overflow: "hidden", border: `1px solid ${bypassed ? "rgba(236,72,153,0.15)" : "rgba(239,68,68,0.15)"}` }}>
        <canvas ref={canvasRef} width={600} height={180} style={{ width: "100%", display: "block", borderRadius: 10 }}
          role="img" aria-label={bypassed ? "Sine wave computed via complex EML bypass" : "Failed attempts to compute sine with real EML — impossible due to infinite zeros"} />
      </div>
      <div style={{ textAlign: "center", marginTop: 10 }}>
        <button onClick={() => setBypassed(!bypassed)} style={{
          padding: "10px 24px", borderRadius: 8, cursor: "pointer",
          background: bypassed ? "rgba(236,72,153,0.08)" : "rgba(239,68,68,0.08)",
          border: `2px solid ${bypassed ? "rgba(236,72,153,0.2)" : "rgba(239,68,68,0.2)"}`,
          fontSize: 13, fontWeight: 700, color: bypassed ? "#EC4899" : "#EF4444",
        }}>{bypassed ? "Back to ℝ — impossible" : "Switch to ℂ — the bypass"}</button>
      </div>
    </div>
  );
}

function DepthLadder() {
  const strata = [
    { d: "∞", name: "Non-constructible", color: "#FDE68A", objects: "sin(x) over ℝ — proved impossible as a finite real EML tree" },
    { d: "3", name: "Oscillatory", color: "#EC4899", objects: "sin(x), cos(x) over ℂ — requires complex bypass, Fourier terms" },
    { d: "2", name: "Logarithmic", color: "#8B5CF6", objects: "ln(x), xⁿ for non-integer n, logarithmic integrals" },
    { d: "1", name: "Exponential", color: "#06B6D4", objects: "exp(x), eˣ, polynomials, exponential integrals" },
    { d: "0", name: "Arithmetic", color: "#64748B", objects: "integers, constants, rational numbers, 1, 0, e, π" },
  ];
  const [active, setActive] = useState<string | null>(null);
  return (
    <div style={{ padding: "20px 24px", borderRadius: 14, background: "rgba(253,230,138,0.03)", border: "1px solid rgba(253,230,138,0.08)", margin: "20px 0" }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: "#FDE68A", textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>Expression depth — a complexity measure</div>
      {strata.map((s, i) => (
        <button key={s.d} onClick={() => setActive(active === s.d ? null : s.d)} style={{
          display: "block", width: "100%", padding: "10px 14px", marginBottom: 4, borderRadius: 8,
          cursor: "pointer", textAlign: "left",
          background: active === s.d ? `${s.color}12` : "transparent",
          border: active === s.d ? `1.5px solid ${s.color}30` : "1.5px solid transparent",
          transition: "all 0.2s",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center",
              background: `${s.color}15`, border: `1px solid ${s.color}25`,
              fontSize: 16, fontWeight: 800, fontFamily: "monospace", color: s.color }}>{s.d}</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: s.color }}>Depth {s.d} · {s.name}</div>
              {active === s.d && <div style={{ fontSize: 11, color: "#888", marginTop: 2 }}>{s.objects}</div>}
            </div>
          </div>
          {i === 0 && (
            <div style={{ textAlign: "center", fontSize: 9, color: "#EF4444", margin: "6px 0 2px", fontFamily: "monospace" }}>
              — no depth 4 exists (proved) —
            </div>
          )}
        </button>
      ))}
    </div>
  );
}

export default function OneOperator() {
  return (
    <div style={{ fontFamily: "'Newsreader', 'Georgia', serif", maxWidth: 640, margin: "0 auto", padding: "2rem 1.2rem 3rem", color: "#d4d4d4" }}>

      <div style={{ textAlign: "center", marginBottom: 40 }}>
        <a href="/" style={{ fontSize: 11, letterSpacing: 4, textTransform: "uppercase", color: "#A78BFA", fontWeight: 600, fontFamily: "monospace", marginBottom: 8, display: "block", textDecoration: "none" }}>monogate</a>
        <h1 style={{ fontSize: "clamp(28px, 8vw, 42px)", fontWeight: 400, margin: "0 0 8px", lineHeight: 1.2, letterSpacing: -1, color: "#d4d4d4" }}>One Operator</h1>
        <p style={{ fontSize: 16, color: "#6b7280", fontStyle: "italic", margin: 0 }}>
          How a single equation generates all elementary functions
        </p>
        <div style={{ width: 40, height: 1, background: "#A78BFA", margin: "20px auto 0" }} />
      </div>

      <p style={{ fontSize: 18, lineHeight: 1.8, marginBottom: 8 }}>
        In March 2026, Andrzej Odrzywołek published a proof that a single binary operator generates
        every elementary function as a finite binary tree:
      </p>
      <div style={{ textAlign: "center", margin: "30px 0", padding: "20px", borderRadius: 14, background: "rgba(167,139,250,0.04)", border: "1px solid rgba(167,139,250,0.08)" }}>
        <div style={{ fontFamily: "monospace", fontSize: 22, color: "#A78BFA", fontWeight: 400 }}>
          eml(x, y) = exp(x) − ln(y)
        </div>
        <div style={{ fontSize: 12, color: "#999", marginTop: 6, fontFamily: "monospace" }}>arXiv:2603.21852</div>
      </div>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        Exponentials. Logarithms. Trigonometry. Polynomials. All of them — as finite compositions
        of this operator with the constant 1. Not approximately. Exactly.
      </p>
      <p style={{ fontSize: 18, lineHeight: 1.8, marginBottom: 0 }}>
        Drag the sliders:
      </p>
      <EmlCalc />

      <h2 style={{ fontSize: 28, fontWeight: 400, marginTop: 40, marginBottom: 12, letterSpacing: -0.5, color: "#d4d4d4" }}>The simplest case</h2>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        Set y = 1. Since ln(1) = 0, the equation becomes eml(x, 1) = exp(x). One operation. One node
        in the tree. The entire exponential function — the foundation of growth, compound interest,
        radioactive decay, and half of calculus — from a single application.
      </p>
      <ExpDemo />

      <h2 style={{ fontSize: 28, fontWeight: 400, marginTop: 40, marginBottom: 12, letterSpacing: -0.5, color: "#d4d4d4" }}>But what does it cost?</h2>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        Exp costs 1 node. Elegant. But addition costs 11. Multiplication costs 13. These are the
        minimum node counts — the exact number of eml operations required to express each function
        as a binary tree.
      </p>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        The node counts aren&apos;t fixed, though. The exp-ln family contains three operators — EML, EDL
        (exp/ln), and EXL (exp×ln) — and routing each primitive to the cheapest operator cuts the
        total dramatically. Toggle it:
      </p>
      <NodeCounter />

      <h2 style={{ fontSize: 28, fontWeight: 400, marginTop: 40, marginBottom: 12, letterSpacing: -0.5, color: "#d4d4d4" }}>The barrier</h2>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        Now try sin(x).
      </p>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        Over the reals, you can&apos;t build it. The sine function crosses zero infinitely often — at every
        multiple of π. But a finite tree of exp and ln has finitely many zeros. This is provable:
        no finite real EML tree can represent any function with infinitely many zeros.
      </p>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        The fix is beautiful. Over the complex numbers, Euler&apos;s formula gives e<sup>ix</sup> = cos(x) + i·sin(x).
        And e<sup>ix</sup> is just eml(ix, 1). One node. The imaginary part is sin(x). The barrier
        dissolves — not by being solved, but by changing the domain.
      </p>
      <SinBarrier />

      <h2 style={{ fontSize: 28, fontWeight: 400, marginTop: 40, marginBottom: 12, letterSpacing: -0.5, color: "#d4d4d4" }}>A complexity measure</h2>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        The node counts reveal structure. Functions cluster into groups by the kind of computation
        they require — arithmetic at the bottom, exponentials above, logarithmic functions higher still,
        oscillatory functions accessible only via the complex bypass, and functions provably
        non-constructible in finite real trees at the top.
      </p>
      <DepthLadder />
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        This isn&apos;t an arbitrary ranking. The gaps between levels are structural. No finite real tree
        crosses the oscillatory barrier. No depth-4 level exists — the jump from oscillatory (3) to
        non-constructible (∞) is direct, with no intermediate complexity class. This has been proved
        and is connected to the minimal number of exponentiations needed to express a function,
        which in turn connects to open problems in transcendental number theory.
      </p>

      <h2 style={{ fontSize: 28, fontWeight: 400, marginTop: 40, marginBottom: 12, letterSpacing: -0.5, color: "#d4d4d4" }}>Why it matters</h2>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        The depth hierarchy is a new complexity measure for mathematical expressions. The question
        &ldquo;how many nested exponentiations does this function require?&rdquo; connects to Schanuel&apos;s conjecture
        — one of the central open problems in transcendental number theory — which predicts the
        algebraic independence of exponential expressions.
      </p>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        If Schanuel&apos;s conjecture holds, it constrains exactly which depth reductions are possible.
        Functions that appear to live at depth 2 can&apos;t be simplified to depth 1 without violating
        algebraic independence. The depth hierarchy would be rigid — not just a classification,
        but an invariant.
      </p>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        More concretely: the BEST routing optimization raises a practical question. For any mathematical
        expression, what is the minimum number of nodes in an exp-ln tree that computes it? This is a
        well-defined optimization problem with applications in numerical computation, symbolic algebra,
        and compiler design. The routing table gives upper bounds. The depth hierarchy suggests lower bounds.
      </p>
      <p style={{ fontSize: 18, lineHeight: 1.8 }}>
        The fact that one binary operator generates all elementary functions is itself remarkable.
        The fact that the construction reveals a natural complexity hierarchy with structural gaps
        is more remarkable still. And the fact that this hierarchy connects to some of the deepest
        open questions about the nature of transcendental numbers makes it worth investigating
        seriously.
      </p>

      <div style={{ textAlign: "center", margin: "50px 0 30px" }}>
        <div style={{ width: 40, height: 1, background: "#A78BFA", margin: "0 auto 24px" }} />
        <div style={{ fontFamily: "monospace", fontSize: 18, color: "#A78BFA", marginBottom: 8 }}>
          eml(x, y) = exp(x) − ln(y)
        </div>
        <p style={{ fontSize: 14, color: "#777", fontStyle: "italic" }}>
          One operator. All elementary functions. A new complexity measure. Open questions.
        </p>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 30 }}>
        {[
          { label: "Try the lab", href: "https://monogate.dev/lab", color: "#EC4899", desc: "Interactive experiments" },
          { label: "Read the paper", href: "https://arxiv.org/abs/2603.21852", color: "#06B6D4", desc: "Odrzywołek 2026" },
          { label: "pip install monogate", href: "https://pypi.org/project/monogate/", color: "#A78BFA", desc: "Python package" },
        ].map(door => (
          <a key={door.label} href={door.href} target="_blank" rel="noopener noreferrer" style={{
            display: "block", padding: "16px 14px", borderRadius: 12, textDecoration: "none",
            textAlign: "center", background: `${door.color}06`, border: `1.5px solid ${door.color}20`,
            flex: "1 1 140px",
          }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: door.color, fontFamily: "monospace" }}>{door.label}</div>
            <div style={{ fontSize: 11, color: "#999", marginTop: 4, fontFamily: "monospace" }}>{door.desc}</div>
          </a>
        ))}
      </div>

      <div style={{ textAlign: "center", fontSize: 12, color: "#aaa", fontFamily: "monospace" }}>
        Built by some guy with an AI and too much free time.
      </div>
    </div>
  );
}
