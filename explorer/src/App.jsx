import { useState, useMemo } from "react";
import BestCalc from "./components/BestCalc.jsx";
import LandingPage from "./components/LandingPage.jsx";
import AttractorViz from "./components/AttractorViz.jsx";
import BenchmarkTab from "./components/BenchmarkTab.jsx";
import ExprTreeTab from "./components/ExprTreeTab.jsx";
import { op, exp, ln, E, ZERO, sub, neg, add, mul, div, pow, recip,
         BEST, sin_best, cos_best, pow_exl, div_edl, ln_exl } from "./eml.js";
const deml = (x, y) => Math.exp(-x) - Math.log(y);
const exp_neg = (x) => deml(x, 1);
import {
  exp_t, ln_t, sub_t, neg_t, add_t, mul_t, div_t, pow_t, recip_t, sqrt_t,
  E_t, mkVar, mkLit,
  countNodes, countDepth, bfsOrder, OPEN_CHALLENGES,
} from "./eml_tree.js";
import TreeViz from "./TreeViz.jsx";

// ─── Safe eval ────────────────────────────────────────────────────────────────
function safeEval(expr, x) {
  try {
    const clean = expr.trim();
    if (!/^[emlxadivosubnegpwrct\d\s.,()e\-+/*]+$/i.test(clean)) return null;
    const js = clean.replace(/\beml\b/g,"_op");
    const fn = new Function(
      "_op","exp","ln","neg","add","sub","mul","div","pow","recip","x",
      `"use strict"; return (${js});`
    );
    const r = fn(op,exp,ln,neg,add,sub,mul,div,pow,recip,x);
    return isFinite(r) ? r : null;
  } catch { return null; }
}

const fmt = v => {
  if (v === null || !isFinite(v)) return "—";
  if (v === 0) return "0";
  const a = Math.abs(v);
  if (a < 0.0001 || a >= 1e7) return v.toExponential(4);
  return parseFloat(v.toPrecision(8)).toString();
};
const fmtErr = e => {
  if (e === null || !isFinite(e)) return "—";
  if (e < 1e-14) return "< 1e−14";
  return e.toExponential(2);
};
const errCol = e => e === null ? C.muted : e < 1e-10 ? C.green : e < 1e-5 ? C.accent : C.red;

// ─── Colours ──────────────────────────────────────────────────────────────────
const C = {
  bg:"#07080f", surface:"#0d0e1c", border:"#191b2e",
  text:"#cdd0e0", muted:"#4e5168", accent:"#e8a020",
  blue:"#6ab0f5", green:"#5ec47a", red:"#e05060", tag:"#1a1c2e",
};

// ─── Identity catalogue ───────────────────────────────────────────────────────
const IDENTITIES = [
  { id:"exp",   name:"eˣ",    category:"core",
    emlForm:"eml(x, 1)",
    proof:"exp(x) − ln(1) = eˣ",
    nodes:1, depth:1, status:"verified",
    evalEml: x => op(x,1),   evalStd: x => Math.exp(x),
    domain:{ min:-3, max:3, default:1 }, xLabel:"x" },
  { id:"ln",    name:"ln x",  category:"core",
    emlForm:"eml(1, eml(eml(1,x), 1))",
    proof:"let s=e−ln(x); eml(s,1)=eᵉ/x; eml(1,eᵉ/x)=ln(x)",
    nodes:3, depth:3, status:"verified",
    evalEml: x => ln(x),     evalStd: x => Math.log(x),
    domain:{ min:0.01, max:10, default:2 }, xLabel:"x" },
  { id:"neg",   name:"−y",    category:"arithmetic",
    emlForm:"two-regime (see source)",
    proof:"Regime A(y≤0): tower formula. Regime B(y>0): 1−(y+1)=−y",
    nodes:9, depth:5, status:"proven",
    evalEml: x => neg(x),    evalStd: x => -x,
    domain:{ min:-10, max:10, default:3 }, xLabel:"y" },
  { id:"sub",   name:"x − y", category:"arithmetic",
    emlForm:"eml(ln(x), exp(y))",
    proof:"exp(ln(x)) − ln(exp(y)) = x − y",
    nodes:5, depth:4, status:"verified",
    evalEml: x => sub(x, 2), evalStd: x => x - 2,
    domain:{ min:0.01, max:10, default:5 }, xLabel:"x", note:"y fixed at 2" },
  { id:"add",   name:"x + y", category:"arithmetic",
    emlForm:"eml(ln(x), eml(neg(y), 1))",
    proof:"exp(ln(x)) − ln(exp(−y)) = x + y",
    nodes:11, depth:6, status:"proven",
    evalEml: x => add(x, 3), evalStd: x => x + 3,
    domain:{ min:0.01, max:10, default:2 }, xLabel:"x", note:"y fixed at 3" },
  { id:"mul",   name:"x × y", category:"arithmetic",
    emlForm:"eml(add(ln(x), ln(y)), 1)",
    proof:"exp(ln(x)+ln(y)) = xy",
    nodes:13, depth:7, status:"proven",
    evalEml: x => mul(x, 3), evalStd: x => x * 3,
    domain:{ min:0.01, max:10, default:2 }, xLabel:"x", note:"y fixed at 3" },
  { id:"div",   name:"x / y", category:"arithmetic",
    emlForm:"eml(add(ln(x), neg(ln(y))), 1)",
    proof:"exp(ln(x)−ln(y)) = x/y",
    nodes:15, depth:8, status:"proven",
    evalEml: x => div(x, 2), evalStd: x => x / 2,
    domain:{ min:0.01, max:10, default:6 }, xLabel:"x", note:"y fixed at 2" },
  { id:"pow",   name:"xⁿ",    category:"arithmetic",
    emlForm:"eml(mul(n, ln(x)), 1)",
    proof:"exp(n·ln(x)) = xⁿ",
    nodes:15, depth:8, status:"proven",
    evalEml: x => pow(x, 2), evalStd: x => Math.pow(x, 2),
    domain:{ min:0.01, max:10, default:3 }, xLabel:"x", note:"n fixed at 2" },
  { id:"recip", name:"1/x",   category:"arithmetic",
    emlForm:"eml(neg(ln(x)), 1)",
    proof:"exp(−ln(x)) = x⁻¹",
    nodes:5, depth:4, status:"proven",
    evalEml: x => recip(x),  evalStd: x => 1/x,
    domain:{ min:0.1, max:5, default:2 }, xLabel:"x" },
  { id:"e",     name:"e",     category:"constant",
    emlForm:"eml(1, 1)",
    proof:"exp(1) − ln(1) = e",
    nodes:1, depth:1, status:"verified",
    evalEml: () => op(1,1), evalStd: () => Math.E,
    domain:null, isConstant:true },
  { id:"zero",  name:"0",     category:"constant",
    emlForm:"eml(1, eml(eml(1,1), 1))",
    proof:"eml(1,1)=e → eml(e,1)=eᵉ → eml(1,eᵉ)=e−e=0",
    nodes:3, depth:3, status:"verified",
    evalEml: () => ZERO,    evalStd: () => 0,
    domain:null, isConstant:true },
  { id:"exp_neg", name:"e^(−x)", category:"deml",
    emlForm:"deml(x, 1)",
    proof:"exp(−x) − ln(1) = exp(−x). DEML dual gate: 1-node native.",
    nodes:1, depth:1, status:"verified",
    evalEml: x => exp_neg(x), evalStd: x => Math.exp(-x),
    domain:{ min:-3, max:3, default:1 }, xLabel:"x" },
  { id:"deml_ln", name:"ln x (DEML)", category:"deml",
    emlForm:"eml(1, eml(eml(1,x), 1))",
    proof:"Same 3-node EML construction. DEML: negated exponent barrier not in ln path.",
    nodes:3, depth:3, status:"verified",
    evalEml: x => ln(x), evalStd: x => Math.log(x),
    domain:{ min:0.01, max:10, default:2 }, xLabel:"x" },
];

const CATEGORIES = ["core","constant","arithmetic","deml"];
const CAT_LABELS  = { core:"Core Functions", constant:"Constants", arithmetic:"Arithmetic", deml:"DEML Dual Gate" };

const STATUS_COL  = { verified: C.green, proven: C.blue, experimental: C.accent, open: C.muted };
const STATUS_SYM  = { verified:"✓", proven:"✓", experimental:"~", open:"?" };

const PRESETS = [
  { label:"eml(x,1)",          expr:"eml(x, 1)" },
  { label:"ln x",              expr:"eml(1, eml(eml(1, x), 1))" },
  { label:"neg(x)",            expr:"neg(x)" },
  { label:"add(x, 3)",         expr:"add(x, 3)" },
  { label:"mul(x, 2)",         expr:"mul(x, 2)" },
  { label:"pow(x, 3)",         expr:"pow(x, 3)" },
  { label:"div(10, x)",        expr:"div(10, x)" },
];

// ─── Mini bar chart for complexity ───────────────────────────────────────────
function ComplexityBar({ value, max=15, color=C.accent }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:6 }}>
      <div style={{ flex:1, height:4, background:C.border, borderRadius:2, overflow:"hidden" }}>
        <div style={{ width:`${(value/max)*100}%`, height:"100%",
          background:color, borderRadius:2, transition:"width 0.3s" }}/>
      </div>
      <span style={{ fontSize:10, color:C.text, minWidth:14 }}>{value}</span>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function App() {
  const [activeId,   setActiveId]   = useState("exp");
  const [xVal,       setXVal]       = useState(1.0);
  const [customExpr, setCustomExpr] = useState("pow(x, 3)");
  const [customX,    setCustomX]    = useState(2.0);
  const [tab,        setTab]        = useState(() => {
    const p = new URLSearchParams(window.location.search);
    return p.get("tab") ?? "calc";
  });
  // Show landing on first visit; bypass if URL has params (deep links still work)
  const [showLanding, setShowLanding] = useState(() => {
    const p = new URLSearchParams(window.location.search);
    return !p.has("expr") && !p.has("tab") && !p.has("mode");
  });
  const [bestX,      setBestX]      = useState(1.0);
  const [treeExpr,   setTreeExpr]   = useState("pow(x, 3)");
  const [treeKey,    setTreeKey]    = useState(0); // increment to restart animation
  const [treeRoot,   setTreeRoot]   = useState(null);
  const [treeError,  setTreeError]  = useState(null);
  const [showLearn,  setShowLearn]  = useState(false);

  const buildTree = (expr) => {
    const clean = expr.trim();
    const challenge = OPEN_CHALLENGES.find(k => new RegExp(`\\b${k}\\b`).test(clean.toLowerCase()));
    if (challenge) {
      setTreeError(`"${challenge}" — no known EML construction under strict principal-branch grammar (open problem). Pull requests welcome.`);
      setTreeRoot(null);
      return;
    }
    if (!/^[emlxadivosubnegpwrctq\d\s.,()e\-+/*]+$/i.test(clean)) {
      setTreeError("Invalid expression. Use: exp ln neg add sub mul div pow recip sqrt eml x");
      setTreeRoot(null);
      return;
    }
    try {
      const X = mkVar("x");
      const ctx = {
        eml: (a, b) => ({ tag: "eml", left: a, right: b }),
        exp: exp_t, ln: ln_t, sub: sub_t, neg: neg_t,
        add: add_t, mul: mul_t, div: div_t, pow: pow_t,
        recip: recip_t, sqrt: sqrt_t,
        x: X, e: E_t,
      };
      const js = clean.replace(/\beml\b/g, "_eml");
      const fn = new Function(
        "_eml","exp","ln","neg","add","sub","mul","div","pow","recip","sqrt","x","e",
        `"use strict"; return (${js});`
      );
      const result = fn(
        ctx.eml, exp_t, ln_t, neg_t, add_t, sub_t, mul_t, div_t, pow_t, recip_t, sqrt_t, X, E_t
      );
      if (!result || typeof result !== "object" || !result.tag) throw new Error("bad result");
      setTreeRoot(result);
      setTreeError(null);
      setTreeKey(k => k + 1);
    } catch (err) {
      setTreeError("Could not build tree — check expression syntax.");
      setTreeRoot(null);
    }
  };

  const identity = IDENTITIES.find(i => i.id === activeId);

  const emlResult = identity.isConstant ? identity.evalEml() : (() => { try { const r = identity.evalEml(xVal); return isFinite(r)?r:null; } catch { return null; }})();
  const stdResult = identity.isConstant ? identity.evalStd() : (() => { try { const r = identity.evalStd(xVal); return isFinite(r)?r:null; } catch { return null; }})();
  const error     = (emlResult!==null && stdResult!==null) ? Math.abs(emlResult-stdResult) : null;

  const tableRows = useMemo(() => {
    if (!identity.domain) return [];
    const { min, max } = identity.domain;
    return [0, 0.25, 0.5, 0.75, 1].map(t => {
      const x = min + (max-min)*t;
      const s = (() => { try { const r = identity.evalStd(x); return isFinite(r)?r:null; } catch { return null; }})();
      const e = (() => { try { const r = identity.evalEml(x); return isFinite(r)?r:null; } catch { return null; }})();
      return { x, std:s, eml:e, err: s!==null&&e!==null ? Math.abs(s-e) : null };
    });
  }, [identity, xVal]);

  const customResult = safeEval(customExpr, customX);

  // Landing page — rendered instead of explorer on first visit
  if (showLanding) {
    return (
      <LandingPage onEnter={(targetTab) => {
        if (targetTab) setTab(targetTab);
        setShowLanding(false);
      }} />
    );
  }

  return (
    <div style={{ background:C.bg, minHeight:"100vh", color:C.text,
      fontFamily:"'Space Mono', monospace", padding:"20px 16px",
      maxWidth:780, margin:"0 auto", boxSizing:"border-box" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
        * { box-sizing:border-box; }
        input[type=range]{-webkit-appearance:none;width:100%;height:3px;border-radius:2px;
          background:#1c1e30;outline:none;cursor:pointer;}
        input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:13px;height:13px;
          border-radius:50%;background:#e8a020;cursor:pointer;}
        input[type=text]{outline:none;}
        button{cursor:pointer;font-family:'Space Mono',monospace;}
        ::-webkit-scrollbar{width:4px;} ::-webkit-scrollbar-track{background:transparent;}
        ::-webkit-scrollbar-thumb{background:#2a2c40;border-radius:2px;}
      `}</style>

      {/* Header */}
      <div style={{ borderBottom:`1px solid ${C.border}`, paddingBottom:16, marginBottom:20 }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", flexWrap:"wrap", gap:8 }}>
          <div>
            <div style={{ display:"flex", alignItems:"center", gap:10 }}>
              <button
                onClick={() => setShowLanding(true)}
                style={{
                  fontSize:18, fontWeight:700, color:C.accent,
                  letterSpacing:"-0.02em", background:"none",
                  border:"none", padding:0, cursor:"pointer",
                  fontFamily:"'Space Mono',monospace",
                }}
                title="← Home"
              >
                monogate
              </button>
              <span style={{ fontSize:10, color:C.muted }}>EML Explorer</span>
            </div>
            <div style={{ fontSize:10, color:C.muted, marginTop:3 }}>
              eml(x,y) = exp(x) − ln(y) · Odrzywołek 2026 · arXiv:2603.21852 · v1.4.0
            </div>
          </div>
          <div style={{ display:"flex", gap:4, flexWrap:"wrap", alignItems:"center" }}>
            {[
              { label:"⊞ Challenges ↗", href:"https://monogate.dev/challenge" },
              { label:"Theorems ↗", href:"https://monogate.org/theorems" },
            ].map(({ label, href }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noreferrer"
                style={{
                  padding:"5px 10px", fontSize:10, borderRadius:4,
                  border:`1px solid ${C.border}`, color:C.muted,
                  textDecoration:"none", fontFamily:"'Space Mono',monospace",
                  letterSpacing:"0.04em", whiteSpace:"nowrap",
                }}
                onMouseEnter={e => { e.currentTarget.style.color = C.text; e.currentTarget.style.borderColor = C.muted; }}
                onMouseLeave={e => { e.currentTarget.style.color = C.muted; e.currentTarget.style.borderColor = C.border; }}
              >
                {label}
              </a>
            ))}
            {["calc","verify","table","tree","best","sandbox","deml","attractor","benchmarks"].map(t => {
              const isCalc  = t === "calc";
              const isBench = t === "benchmarks";
              const isHighlit = isCalc || isBench || t === "attractor" || t === "deml";
              const isActive = tab === t;
              const LABELS = {
                calc: "✦ calc",
                attractor: "⊛ attractor",
                deml: "⊖ DEML",
                benchmarks: "▶ bench",
              };
              return (
                <button key={t} onClick={() => setTab(t)} style={{
                  padding: isHighlit ? "5px 12px" : "5px 10px",
                  fontSize: isHighlit ? 11 : 10,
                  fontWeight: isHighlit ? 700 : 400,
                  borderRadius:4, textTransform:"uppercase", letterSpacing:"0.04em",
                  background: isActive
                    ? "rgba(232,160,32,0.12)"
                    : isHighlit ? "rgba(232,160,32,0.06)" : "transparent",
                  border:`1px solid ${isActive ? C.accent : isHighlit ? "rgba(232,160,32,0.35)" : C.border}`,
                  color: isActive ? C.accent : isHighlit ? C.accent : C.muted,
                }}>
                  {LABELS[t] ?? t}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── TAB: VERIFY ── */}
      {tab === "verify" && (
        <div>
          {/* Category tabs */}
          {CATEGORIES.map(cat => {
            const items = IDENTITIES.filter(i => i.category === cat);
            return (
              <div key={cat} style={{ marginBottom:16 }}>
                <div style={{ fontSize:9, color:C.muted, letterSpacing:"0.1em",
                  textTransform:"uppercase", marginBottom:8 }}>{CAT_LABELS[cat]}</div>
                <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                  {items.map(i => (
                    <button key={i.id}
                      onClick={() => { setActiveId(i.id); if(i.domain) setXVal(i.domain.default); }}
                      style={{
                        padding:"6px 14px", fontSize:12, borderRadius:4,
                        background: i.id===activeId ? "rgba(232,160,32,0.12)" : C.tag,
                        border:`1px solid ${i.id===activeId ? C.accent : C.border}`,
                        color: i.id===activeId ? C.accent : C.text,
                      }}>
                      {i.name}
                      <span style={{ marginLeft:5, fontSize:9,
                        color: STATUS_COL[i.status] ?? C.muted }}>
                        {STATUS_SYM[i.status]}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}

          {/* Active identity card */}
          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>

            <div style={{ display:"flex", justifyContent:"space-between",
              alignItems:"flex-start", gap:12, flexWrap:"wrap", marginBottom:14 }}>
              <div style={{ flex:1, minWidth:200 }}>
                <div style={{ fontSize:15, color:C.accent, marginBottom:6, wordBreak:"break-all" }}>
                  {identity.emlForm}
                </div>
                <div style={{ fontSize:10, color:C.muted, lineHeight:1.8, fontStyle:"italic" }}>
                  {identity.proof}
                </div>
                {identity.note && (
                  <div style={{ fontSize:9, color:C.muted, marginTop:6 }}>
                    ⚠ {identity.note}
                  </div>
                )}
              </div>
              <div style={{ width:130, flexShrink:0 }}>
                <div style={{ fontSize:9, color:C.muted, letterSpacing:"0.08em",
                  textTransform:"uppercase", marginBottom:8 }}>complexity</div>
                <div style={{ fontSize:9, color:C.muted, marginBottom:4 }}>
                  nodes
                </div>
                <ComplexityBar value={identity.nodes} color={C.accent} />
                <div style={{ fontSize:9, color:C.muted, marginTop:8, marginBottom:4 }}>
                  depth
                </div>
                <ComplexityBar value={identity.depth} max={10} color={C.blue} />
                <div style={{ marginTop:8, fontSize:9,
                  color: STATUS_COL[identity.status] }}>
                  {identity.status.toUpperCase()}
                </div>
              </div>
            </div>

            {/* Constant display */}
            {identity.isConstant ? (
              <div style={{ borderTop:`1px solid ${C.border}`, paddingTop:12 }}>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8 }}>
                  {[
                    { label:"standard", val:stdResult, col:C.blue },
                    { label:"EML",      val:emlResult, col:C.accent },
                  ].map(({ label, val, col }) => (
                    <div key={label} style={{ background:C.bg,
                      border:`1px solid ${C.border}`, borderRadius:5, padding:"10px 12px" }}>
                      <div style={{ fontSize:9, color:C.muted, textTransform:"uppercase",
                        letterSpacing:"0.1em", marginBottom:4 }}>{label}</div>
                      <div style={{ color:col, fontSize:13 }}>{val}</div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop:8, fontSize:10, color:C.green }}>
                  ✓ error: {Math.abs(stdResult - emlResult).toExponential(2)}
                </div>
              </div>
            ) : (
              /* Slider + live comparison */
              <div style={{ borderTop:`1px solid ${C.border}`, paddingTop:12 }}>
                <div style={{ display:"flex", justifyContent:"space-between",
                  fontSize:10, marginBottom:6 }}>
                  <span style={{ color:C.muted }}>
                    {identity.xLabel} = <span style={{ color:C.text }}>{xVal.toFixed(4)}</span>
                  </span>
                  <span style={{ color: errCol(error) }}>
                    {error !== null
                      ? (error < 1e-13 ? "error < 1e−13 ✓" : `error: ${fmtErr(error)}`)
                      : "domain error"}
                  </span>
                </div>
                <input type="range"
                  min={identity.domain.min} max={identity.domain.max} step={0.001}
                  value={xVal} onChange={e => setXVal(parseFloat(e.target.value))} />
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginTop:10 }}>
                  {[
                    { label:"standard", val:stdResult, col:C.blue },
                    { label:"EML",      val:emlResult, col:C.accent },
                  ].map(({ label, val, col }) => (
                    <div key={label} style={{ background:C.bg,
                      border:`1px solid ${C.border}`, borderRadius:5, padding:"10px 12px" }}>
                      <div style={{ fontSize:9, color:C.muted, textTransform:"uppercase",
                        letterSpacing:"0.1em", marginBottom:4 }}>{label}</div>
                      <div style={{ color:col, fontSize:14 }}>{fmt(val)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Verification table */}
          {!identity.isConstant && tableRows.length > 0 && (
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, overflow:"hidden" }}>
              <div style={{ display:"grid", gridTemplateColumns:"0.7fr 1.3fr 1.3fr 1fr",
                padding:"7px 14px", borderBottom:`1px solid ${C.border}`,
                fontSize:9, color:C.muted, letterSpacing:"0.06em", textTransform:"uppercase" }}>
                {[identity.xLabel,"standard","EML","|error|"].map(h=><div key={h}>{h}</div>)}
              </div>
              {tableRows.map((row,i) => (
                <div key={i} style={{
                  display:"grid", gridTemplateColumns:"0.7fr 1.3fr 1.3fr 1fr",
                  padding:"6px 14px", fontSize:11,
                  borderBottom: i<tableRows.length-1 ? `1px solid ${C.border}` : "none",
                  background: i%2===0 ? "transparent" : "rgba(255,255,255,0.012)"
                }}>
                  <div style={{ color:C.muted }}>{row.x.toFixed(3)}</div>
                  <div style={{ color:C.blue }}>{fmt(row.std)}</div>
                  <div style={{ color:C.accent }}>{fmt(row.eml)}</div>
                  <div style={{ color:errCol(row.err) }}>{fmtErr(row.err)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── TAB: TABLE ── */}
      {tab === "table" && (
        <div>
          <div style={{ fontSize:10, color:C.muted, marginBottom:14, lineHeight:1.8 }}>
            EML complexity table — node count and depth per identity.
            This ranking of elementary functions by tree depth is new to mathematics.
          </div>
          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, overflow:"hidden" }}>
            <div style={{ display:"grid",
              gridTemplateColumns:"1.2fr 2fr 0.6fr 0.6fr 0.8fr",
              padding:"8px 14px", borderBottom:`1px solid ${C.border}`,
              fontSize:9, color:C.muted, letterSpacing:"0.06em", textTransform:"uppercase" }}>
              {["Function","EML form","Nodes","Depth","Status"].map(h=><div key={h}>{h}</div>)}
            </div>
            {IDENTITIES.map((id, i) => (
              <div key={id.id} style={{
                display:"grid", gridTemplateColumns:"1.2fr 2fr 0.6fr 0.6fr 0.8fr",
                padding:"9px 14px", fontSize:11, alignItems:"center",
                borderBottom: i<IDENTITIES.length-1 ? `1px solid ${C.border}` : "none",
                background: i%2===0 ? "transparent" : "rgba(255,255,255,0.012)",
                cursor:"pointer"
              }} onClick={() => { setActiveId(id.id); setTab("verify"); if(id.domain) setXVal(id.domain.default); }}>
                <div style={{ color:C.accent }}>{id.name}</div>
                <div style={{ color:C.muted, fontSize:9, wordBreak:"break-all" }}>{id.emlForm}</div>
                <div>
                  <ComplexityBar value={id.nodes} color={C.accent} />
                </div>
                <div>
                  <ComplexityBar value={id.depth} max={10} color={C.blue} />
                </div>
                <div style={{ fontSize:9, color: STATUS_COL[id.status] }}>
                  {STATUS_SYM[id.status]} {id.status}
                </div>
              </div>
            ))}
            {/* Open challenges + BEST Taylor results */}
            {[
              { name:"sin x", note:"PROVED IMPOSSIBLE over ℝ (T01 Infinite Zeros Barrier). Taylor via BEST: 63n.", nodes:"63*", status:"impossible", onClick:null },
              { name:"cos x", note:"PROVED IMPOSSIBLE over ℝ (T01 Infinite Zeros Barrier). Taylor via BEST: 54n.", nodes:"54*", status:"impossible", onClick:null },
              { name:"tan x", note:"sin/cos ratio — composable", nodes:"~120*", status:"open", onClick:null },
              { name:"π",     note:"no closed-form EML expression", nodes:"?", status:"open", onClick:null },
              { name:"i (strict)", note:"T19: proved unreachable from {eml,1} under principal-branch semantics. Lean-verified.", nodes:"—", status:"impossible", onClick:null },
              { name:"i (extended)", note:"Closest approach: 0.99999524 at depth 6. Open under relaxed semantics.", nodes:"?", status:"open", onClick:null },
            ].map(({name,note,nodes,status,onClick},i) => (
              <div key={name} onClick={onClick || undefined} style={{
                display:"grid", gridTemplateColumns:"1.2fr 2fr 0.6fr 0.6fr 0.8fr",
                padding:"9px 14px", fontSize:11, alignItems:"center",
                borderBottom: i<5 ? `1px solid ${C.border}` : "none",
                background: "rgba(78,81,104,0.06)",
                cursor: onClick ? "pointer" : "default",
              }}>
                <div style={{ color: status==="impossible" ? C.red : C.muted }}>{name}</div>
                <div style={{ color: status==="impossible" ? "#f87171" : C.muted, fontSize:9 }}>{note}</div>
                <div style={{ color: status==="impossible" ? C.red : C.muted, fontSize:9 }}>{nodes}</div>
                <div style={{ color:C.muted, fontSize:9 }}>—</div>
                <div style={{ fontSize:9, color: status==="impossible" ? C.red : C.muted }}>
                  {status==="impossible" ? "✗ proved" : "? open"}
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop:10, fontSize:9, color:C.muted, lineHeight:1.8 }}>
            Click any row to jump to its verification. · Open challenges welcome — open a PR.
          </div>
        </div>
      )}

      {/* ── TAB: SANDBOX ── */}
      {tab === "sandbox" && (
        <div>
          <div style={{ fontSize:10, color:C.muted, marginBottom:14, lineHeight:1.8 }}>
            Compose your own EML expression. Available:{" "}
            {["eml","exp","ln","neg","add","sub","mul","div","pow","recip","x"].map(fn => (
              <span key={fn} style={{ color:C.accent, marginRight:6 }}>{fn}</span>
            ))}
          </div>

          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>
            {/* Presets */}
            <div style={{ display:"flex", gap:6, flexWrap:"wrap", marginBottom:12 }}>
              {PRESETS.map(p => (
                <button key={p.label} onClick={() => setCustomExpr(p.expr)} style={{
                  fontSize:10, padding:"4px 10px",
                  background: customExpr===p.expr ? "rgba(232,160,32,0.12)" : C.tag,
                  border:`1px solid ${customExpr===p.expr ? C.accent : C.border}`,
                  color: customExpr===p.expr ? C.accent : C.muted, borderRadius:3 }}>
                  {p.label}
                </button>
              ))}
            </div>

            <input type="text" value={customExpr}
              onChange={e => setCustomExpr(e.target.value)}
              style={{ width:"100%", background:C.bg, border:`1px solid ${C.border}`,
                borderRadius:4, color:C.accent, padding:"9px 12px", fontSize:13,
                fontFamily:"'Space Mono',monospace", marginBottom:14 }} />

            <div style={{ display:"flex", gap:12, alignItems:"center", flexWrap:"wrap" }}>
              <div style={{ flex:1, minWidth:160 }}>
                <div style={{ display:"flex", justifyContent:"space-between",
                  fontSize:10, color:C.muted, marginBottom:6 }}>
                  <span>x</span>
                  <span style={{ color:C.text }}>{customX.toFixed(4)}</span>
                </div>
                <input type="range" min={0.01} max={10} step={0.001}
                  value={customX} onChange={e => setCustomX(parseFloat(e.target.value))} />
              </div>
              <div style={{
                minWidth:120, padding:"12px 20px", borderRadius:6,
                textAlign:"center", fontSize:15, fontWeight:700,
                background: customResult!==null ? "rgba(94,196,122,0.07)" : "rgba(224,80,96,0.07)",
                border:`1px solid ${customResult!==null ? C.green : C.red}`,
                color: customResult!==null ? C.green : C.red,
              }}>
                {customResult !== null ? fmt(customResult) : "error"}
              </div>
            </div>
          </div>

          {/* Sweep table for custom expr */}
          {customResult !== null && (
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, overflow:"hidden" }}>
              <div style={{ padding:"7px 14px", borderBottom:`1px solid ${C.border}`,
                fontSize:9, color:C.muted, letterSpacing:"0.06em", textTransform:"uppercase" }}>
                sweep x across [0.1 → 10]
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(5, 1fr)" }}>
                {[0.1, 1, 2.5, 5, 10].map((x, i) => {
                  const r = safeEval(customExpr, x);
                  return (
                    <div key={x} style={{
                      padding:"10px 12px", textAlign:"center",
                      borderRight: i<4 ? `1px solid ${C.border}` : "none",
                    }}>
                      <div style={{ fontSize:9, color:C.muted, marginBottom:5 }}>x={x}</div>
                      <div style={{ fontSize:12, color: r!==null ? C.accent : C.red }}>
                        {r !== null ? fmt(r) : "—"}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── TAB: TREE ── */}
      {tab === "tree" && (
        <div>
          <div style={{ fontSize:10, color:C.muted, marginBottom:14, lineHeight:1.8 }}>
            Type any EML expression and watch it decompose into a branching tree.
            Every internal node is one{" "}<span style={{ color:C.accent }}>eml(·,·)</span>{" "}call.
            Leaves are terminals:{" "}<span style={{ color:C.blue }}>1</span>,{" "}
            <span style={{ color:C.blue }}>x</span>, numeric literals.
          </div>

          {/* Input row */}
          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>
            <div style={{ display:"flex", gap:6, flexWrap:"wrap", marginBottom:12 }}>
              {[
                "exp(x)", "ln(x)", "mul(x, x)", "pow(x, 3)",
                "add(2, 3)", "recip(x)", "sqrt(x)", "div(x, 2)",
              ].map(preset => (
                <button key={preset}
                  onClick={() => { setTreeExpr(preset); buildTree(preset); }}
                  style={{
                    fontSize:10, padding:"4px 10px",
                    background: treeExpr === preset ? "rgba(232,160,32,0.12)" : C.tag,
                    border:`1px solid ${treeExpr === preset ? C.accent : C.border}`,
                    color: treeExpr === preset ? C.accent : C.muted, borderRadius:3,
                  }}>
                  {preset}
                </button>
              ))}
            </div>

            <div style={{ display:"flex", gap:8 }}>
              <input type="text" value={treeExpr}
                onChange={e => setTreeExpr(e.target.value)}
                onKeyDown={e => e.key === "Enter" && buildTree(treeExpr)}
                placeholder="e.g. pow(x, 3)"
                style={{ flex:1, background:C.bg, border:`1px solid ${C.border}`,
                  borderRadius:4, color:C.accent, padding:"9px 12px", fontSize:13,
                  fontFamily:"'Space Mono',monospace" }} />
              <button onClick={() => buildTree(treeExpr)} style={{
                padding:"9px 20px", fontSize:11, fontWeight:700,
                background:"rgba(232,160,32,0.15)", border:`1px solid ${C.accent}`,
                color:C.accent, borderRadius:4, letterSpacing:"0.04em",
              }}>
                BUILD
              </button>
            </div>
          </div>

          {/* Error message */}
          {treeError && (
            <div style={{ background:"rgba(224,80,96,0.08)", border:`1px solid ${C.red}`,
              borderRadius:6, padding:"10px 14px", marginBottom:12,
              fontSize:11, color:C.red, lineHeight:1.7 }}>
              {treeError}
            </div>
          )}

          {/* Stats + Tree */}
          {treeRoot && !treeError && (() => {
            const nodes = countNodes(treeRoot);
            const depth = countDepth(treeRoot);
            const done  = bfsOrder(treeRoot).length;
            return (
              <div>
                <div style={{ display:"flex", gap:20, marginBottom:14 }}>
                  {[
                    { label:"Nodes", value: nodes, color: C.accent },
                    { label:"Depth", value: depth, color: C.blue },
                    { label:"eml calls", value: Math.floor(nodes / 2), color: C.green },
                  ].map(({ label, value, color }) => (
                    <div key={label} style={{ background:C.surface,
                      border:`1px solid ${C.border}`, borderRadius:6,
                      padding:"8px 16px", textAlign:"center" }}>
                      <div style={{ fontSize:9, color:C.muted, letterSpacing:"0.08em",
                        textTransform:"uppercase", marginBottom:4 }}>{label}</div>
                      <div style={{ fontSize:22, fontWeight:700, color }}>{value}</div>
                    </div>
                  ))}
                  <button onClick={() => setTreeKey(k => k + 1)} style={{
                    marginLeft:"auto", padding:"8px 16px", fontSize:10,
                    background:"transparent", border:`1px solid ${C.border}`,
                    color:C.muted, borderRadius:6, letterSpacing:"0.04em",
                    alignSelf:"center",
                  }}>
                    REPLAY ↺
                  </button>
                </div>
                <div style={{ background:C.surface, border:`1px solid ${C.border}`,
                  borderRadius:8, padding:16, overflowX:"auto" }}>
                  <TreeViz root={treeRoot} animKey={treeKey} />
                </div>
                <div style={{ marginTop:8, fontSize:9, color:C.muted }}>
                  orange = eml operator node · blue = terminal (1, x, literal)
                </div>
              </div>
            );
          })()}

          {/* Empty state — shown before first build */}
          {!treeRoot && !treeError && (
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, padding:"40px 16px", textAlign:"center" }}>
              <div style={{ fontSize:11, color:C.muted }}>
                Type an expression above and press BUILD to render its EML tree.
              </div>
              <div style={{ marginTop:8, fontSize:9, color:C.muted }}>
                Try: <span style={{ color:C.accent }}>pow(x, 3)</span> — 15 nodes, depth 8
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── TAB: BEST ── */}
      {tab === "best" && (() => {
        const sinVal  = (() => { try { const r = sin_best(bestX); return isFinite(r) ? r : null; } catch { return null; }})();
        const cosVal  = (() => { try { const r = cos_best(bestX); return isFinite(r) ? r : null; } catch { return null; }})();
        const sinRef  = Math.sin(bestX);
        const cosRef  = Math.cos(bestX);
        const sinErr  = sinVal !== null ? Math.abs(sinVal - sinRef) : null;
        const cosErr  = cosVal !== null ? Math.abs(cosVal - cosRef) : null;

        const ROUTING = [
          { op:"exp_neg",via:"DEML",nodes:1,  eml:10, formula:"deml(x, 1) — 1-node native (R1 result)" },
          { op:"ln",    via:"EXL", nodes:1,  eml:3,  formula:"exl(0, x)" },
          { op:"pow",   via:"EXL", nodes:3,  eml:15, formula:"exl(exl(exl(0,n),x),e)" },
          { op:"div",   via:"EDL", nodes:1,  eml:15, formula:"edl(ln(x),exp(y))" },
          { op:"recip", via:"EDL", nodes:2,  eml:5,  formula:"edl(0,edl(x,e))" },
          { op:"mul",   via:"EDL", nodes:7,  eml:13, formula:"div_edl(x, recip_edl(y))" },
          { op:"neg",   via:"EDL", nodes:6,  eml:9,  formula:"edl(ln(x), 1/e)" },
          { op:"exp",   via:"EML", nodes:1,  eml:1,  formula:"eml(x, 1)" },
          { op:"sub",   via:"EML", nodes:5,  eml:5,  formula:"eml(ln(x), exp(y))" },
          { op:"add",   via:"EML", nodes:11, eml:11, formula:"eml(ln(x), eml(neg(y),1))" },
        ];
        const totalBest = ROUTING.reduce((s, r) => s + r.nodes, 0);
        const totalEml  = ROUTING.reduce((s, r) => s + r.eml, 0);

        const VIA_COL = { EXL: C.blue, EDL: "#b08af5", EML: C.accent, DEML: "#2dd4bf" };

        return (
          <div>
            <div style={{ fontSize:10, color:C.muted, marginBottom:16, lineHeight:1.8 }}>
              <b style={{ color:C.accent }}>BEST</b> routes each operation to whichever operator (EML/EDL/EXL/DEML)
              uses fewest nodes. Total: <b style={{ color:C.accent }}>{totalBest}</b> nodes vs{" "}
              <b style={{ color:C.muted }}>{totalEml}</b> all-EML — saves{" "}
              <b style={{ color:C.green }}>{totalEml - totalBest} ({Math.round(100*(totalEml-totalBest)/totalEml)}%)</b>.
              DEML added for exp_neg (R1: DEML is incomplete but exp(−x) is its native 1-node output).
            </div>

            {/* Routing table */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, overflow:"hidden", marginBottom:16 }}>
              <div style={{ display:"grid", gridTemplateColumns:"0.8fr 0.7fr 0.5fr 0.5fr 0.6fr 2fr",
                padding:"7px 14px", borderBottom:`1px solid ${C.border}`,
                fontSize:9, color:C.muted, letterSpacing:"0.06em", textTransform:"uppercase" }}>
                {["Op","Via","Nodes","EML","Saving","Formula"].map(h=><div key={h}>{h}</div>)}
              </div>
              {ROUTING.map((r, i) => {
                const saving = r.eml - r.nodes;
                return (
                  <div key={r.op} style={{
                    display:"grid", gridTemplateColumns:"0.8fr 0.7fr 0.5fr 0.5fr 0.6fr 2fr",
                    padding:"7px 14px", fontSize:11, alignItems:"center",
                    borderBottom: i < ROUTING.length - 1 ? `1px solid ${C.border}` : "none",
                    background: i%2===0 ? "transparent" : "rgba(255,255,255,0.012)",
                  }}>
                    <div style={{ color:C.text }}>{r.op}</div>
                    <div style={{ color: VIA_COL[r.via] ?? C.muted, fontSize:10, fontWeight:700 }}>{r.via}</div>
                    <div style={{ color:C.accent }}>{r.nodes}n</div>
                    <div style={{ color:C.muted }}>{r.eml}n</div>
                    <div style={{ color: saving > 0 ? C.green : C.muted, fontSize:10 }}>
                      {saving > 0 ? `−${saving}n` : "same"}
                    </div>
                    <div style={{ color:C.muted, fontSize:9, wordBreak:"break-all" }}>{r.formula}</div>
                  </div>
                );
              })}
            </div>

            {/* sin(x) + cos(x) live demo */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, padding:16, marginBottom:12 }}>
              <div style={{ fontSize:9, color:C.muted, textTransform:"uppercase",
                letterSpacing:"0.1em", marginBottom:12 }}>sin(x) and cos(x) via 8-term Taylor</div>
              <div style={{ display:"flex", justifyContent:"space-between",
                fontSize:10, color:C.muted, marginBottom:6 }}>
                <span>x = <span style={{ color:C.text }}>{bestX.toFixed(4)}</span></span>
                <span style={{ color:C.muted }}>63 nodes (BEST) vs 245 all-EML</span>
              </div>
              <input type="range" min={-Math.PI} max={Math.PI} step={0.001}
                value={bestX} onChange={e => setBestX(parseFloat(e.target.value))} />

              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8, marginTop:12 }}>
                {[
                  { label:"sin(x)", best:sinVal, ref:sinRef, err:sinErr, note:"pow_exl (3n) × 7 terms + sub_eml" },
                  { label:"cos(x)", best:cosVal, ref:cosRef, err:cosErr, note:"pow_exl (3n) × 7 terms + add_eml" },
                ].map(({ label, best, ref, err, note }) => (
                  <div key={label} style={{ background:C.bg, border:`1px solid ${C.border}`,
                    borderRadius:5, padding:"10px 12px" }}>
                    <div style={{ fontSize:9, color:C.muted, textTransform:"uppercase",
                      letterSpacing:"0.1em", marginBottom:6 }}>{label}</div>
                    <div style={{ display:"flex", justifyContent:"space-between",
                      alignItems:"flex-end", gap:8 }}>
                      <div>
                        <div style={{ fontSize:9, color:C.muted, marginBottom:2 }}>BEST</div>
                        <div style={{ fontSize:14, color:C.accent }}>{best !== null ? fmt(best) : "—"}</div>
                      </div>
                      <div>
                        <div style={{ fontSize:9, color:C.muted, marginBottom:2 }}>reference</div>
                        <div style={{ fontSize:14, color:C.blue }}>{fmt(ref)}</div>
                      </div>
                      <div style={{ textAlign:"right" }}>
                        <div style={{ fontSize:9, color:C.muted, marginBottom:2 }}>|error|</div>
                        <div style={{ fontSize:12, color: errCol(err) }}>{fmtErr(err)}</div>
                      </div>
                    </div>
                    <div style={{ fontSize:8, color:C.muted, marginTop:6 }}>{note}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Node count accuracy table */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, overflow:"hidden" }}>
              <div style={{ padding:"7px 14px", borderBottom:`1px solid ${C.border}`,
                fontSize:9, color:C.muted, letterSpacing:"0.06em", textTransform:"uppercase" }}>
                sin(x) node count vs accuracy (Taylor terms)
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"0.6fr 0.8fr 0.8fr 0.8fr 1fr",
                padding:"7px 14px", borderBottom:`1px solid ${C.border}`,
                fontSize:9, color:C.muted }}>
                {["Terms","Nodes (BEST)","Nodes (EML)","Saving","Max error"].map(h=><div key={h}>{h}</div>)}
              </div>
              {[
                [4, 27, 105, "7.5e-2"], [6, 45, 175, "4.5e-4"], [8, 63, 245, "7.7e-7"],
                [10, 81, 315, "5.3e-10"], [12, 99, 385, "1.8e-13"],
              ].map(([terms, nb, ne, err], i) => (
                <div key={terms} style={{
                  display:"grid", gridTemplateColumns:"0.6fr 0.8fr 0.8fr 0.8fr 1fr",
                  padding:"6px 14px", fontSize:11,
                  borderBottom: i < 4 ? `1px solid ${C.border}` : "none",
                  background: i%2===0 ? "transparent" : "rgba(255,255,255,0.012)",
                }}>
                  <div style={{ color:C.muted }}>{terms}</div>
                  <div style={{ color:C.accent }}>{nb}</div>
                  <div style={{ color:C.muted }}>{ne}</div>
                  <div style={{ color:C.green }}>−{ne-nb} (74%)</div>
                  <div style={{ color: parseFloat(err) < 1e-6 ? C.green : C.muted }}>{err}</div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      {/* ── TAB: CALC ── */}
      {tab === "calc" && <BestCalc />}

      {/* ── TAB: BENCHMARKS ── */}
      {tab === "benchmarks" && <BenchmarkTab />}

      {/* ── TAB: ATTRACTOR ── */}
      {tab === "attractor" && <AttractorViz />}

      {/* ── TAB: FRACTAL ── */}

      {/* ── TAB: SYNTH ── */}

      {/* ── FEATURED ── */}
      <div style={{ marginTop:28, borderTop:`1px solid ${C.border}`, paddingTop:20 }}>
        <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:12 }}>
          Featured
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:10 }}>
          {[
            {
              tab: "tree", label: "✦ tree",
              title: "Expression Trees",
              desc: "Type any math expression, watch it decompose into EML nodes.",
              badge: "interactive",
            },
            {
              tab: "best", label: "best",
              title: "BEST Routing",
              desc: "See how hybrid routing cuts node count by 52–74%.",
              badge: "benchmark",
            },
            {
              tab: "attractor", label: "⊛ attractor",
              title: "The Phantom",
              desc: "Watch gradient descent converge to the wrong answer — then fix it.",
              badge: "experiment",
            },
          ].map(({ tab: t, label, title, desc, badge }) => (
            <button key={t} onClick={() => setTab(t)} style={{
              background: tab === t ? "rgba(232,160,32,0.10)" : C.surface,
              border:`1px solid ${tab === t ? C.accent : C.border}`,
              borderRadius:8, padding:"14px 16px", textAlign:"left", cursor:"pointer",
            }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
                <span style={{ fontSize:12, fontWeight:700, color:C.accent,
                  fontFamily:"'Space Mono',monospace", textTransform:"uppercase" }}>{label}</span>
                <span style={{ fontSize:8, color:C.muted, background:"rgba(255,255,255,0.04)",
                  border:`1px solid ${C.border}`, borderRadius:3, padding:"2px 6px",
                  letterSpacing:"0.06em", textTransform:"uppercase" }}>{badge}</span>
              </div>
              <div style={{ fontSize:11, fontWeight:600, color:C.text, marginBottom:5 }}>{title}</div>
              <div style={{ fontSize:10, color:C.muted, lineHeight:1.6 }}>{desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* ── LEARN SECTION ── */}
      <div style={{ marginTop:28, borderTop:`1px solid ${C.border}`, paddingTop:20 }}>
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between",
          flexWrap:"wrap", gap:8, marginBottom: showLearn ? 20 : 0 }}>
          <div style={{ display:"flex", alignItems:"center", gap:10 }}>
            <span style={{ fontSize:13, fontWeight:700, color:C.text }}>Learn how this works</span>
            <span style={{ fontSize:9, color:C.accent, fontFamily:"'Space Mono',monospace" }}>
              optional deep dive
            </span>
          </div>
          <button
            onClick={() => setShowLearn(v => !v)}
            style={{ fontSize:10, color:C.accent, background:"transparent", border:"none",
              padding:0, display:"flex", alignItems:"center", gap:4, letterSpacing:"0.04em" }}>
            {showLearn ? "Hide" : "Show"} explainer
            <span style={{ display:"inline-block", transform: showLearn ? "rotate(180deg)" : "none",
              transition:"transform 0.2s" }}>↓</span>
          </button>
        </div>

        {showLearn && (
          <div style={{ display:"flex", flexDirection:"column", gap:32 }}>

            {/* 1 — What is EML? */}
            <div>
              <div style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:12 }}>
                1 — What is EML?
              </div>
              <p style={{ fontSize:11, color:C.muted, lineHeight:1.8, marginBottom:10 }}>
                A normal scientific calculator has dozens of different buttons: sin, cos, log,
                +, −, ×, ÷, xⁿ, and so on.
              </p>
              <p style={{ fontSize:11, color:C.muted, lineHeight:1.8, marginBottom:10 }}>
                Odrzywołek (2026) proved you only need <span style={{ color:C.text }}>one</span>:
              </p>
              <div style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:6,
                padding:"14px 18px", fontFamily:"'Space Mono',monospace", color:C.accent,
                fontSize:13, textAlign:"center", margin:"16px 0" }}>
                eml(x, y) = exp(x) − ln(y)
              </div>
              <p style={{ fontSize:11, color:C.muted, lineHeight:1.8, marginBottom:14 }}>
                That's it. One function. Two inputs. With this and the constant 1, you can build
                every other button on the calculator by combining it with itself.
              </p>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(180px,1fr))",
                gap:8 }}>
                {[
                  ["eˣ", "eml(x, 1)"],
                  ["ln(x)", "eml(1, eml(eml(1, x), 1))"],
                  ["x + y", "eml(ln(x), eml(neg(y), 1))"],
                ].map(([label, form]) => (
                  <div key={label} style={{ background:C.surface, border:`1px solid ${C.border}`,
                    borderRadius:6, padding:"10px 12px", fontSize:10 }}>
                    <span style={{ color:C.text, fontWeight:700 }}>{label}</span>
                    <span style={{ color:C.muted }}> = </span>
                    <span style={{ color:C.blue }}>{form}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 2 — What Node Cost Means */}
            <div>
              <div style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:12 }}>
                2 — What "Node Cost" Means
              </div>
              <p style={{ fontSize:11, color:C.muted, lineHeight:1.8, marginBottom:10 }}>
                Every EML expression is a binary tree. Each internal node is one application
                of the eml operator.
              </p>
              <p style={{ fontSize:11, color:C.muted, lineHeight:1.8, marginBottom:10 }}>
                When we say <span style={{ color:C.text }}>ln(x) costs 3 nodes</span>, we mean
                you need to nest eml three times:
              </p>
              <div style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:6,
                padding:"12px 16px", fontFamily:"'Space Mono',monospace", fontSize:11,
                color:C.blue, margin:"14px 0" }}>
                eml(1, eml(eml(1, x), 1))
              </div>
              <p style={{ fontSize:10, color:C.muted, lineHeight:1.7, marginBottom:16 }}>
                Node count measures computational depth — how many exp and ln operations you
                actually execute. Fewer nodes = shallower tree, faster evaluation, less
                numerical error accumulation.
              </p>
              <div style={{ background:C.surface, border:`1px solid ${C.border}`,
                borderRadius:6, padding:"12px 16px" }}>
                <div style={{ fontSize:9, color:C.muted, textTransform:"uppercase",
                  letterSpacing:"0.06em", marginBottom:10 }}>
                  Reference costs (pure EML)
                </div>
                {[
                  ["exp(x)", "1 node"],
                  ["ln(x)", "3 nodes"],
                  ["x × y", "13 nodes"],
                  ["xⁿ", "15 nodes"],
                  ["sin(x) 8-term Taylor", "245 nodes"],
                ].map(([op, cost]) => (
                  <div key={op} style={{ display:"flex", justifyContent:"space-between",
                    padding:"4px 0", borderBottom:`1px solid ${C.border}`, fontSize:11 }}>
                    <span style={{ color:C.text, fontFamily:"'Space Mono',monospace" }}>{op}</span>
                    <span style={{ color:C.muted }}>{cost}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 3 — Why Hybrid Execution Works */}
            <div>
              <div style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:12 }}>
                3 — Why Hybrid Execution Works
              </div>
              <p style={{ fontSize:11, color:C.muted, lineHeight:1.8, marginBottom:14 }}>
                EML isn't the only operator of its kind. There are natural cousins with different strengths:
              </p>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(160px,1fr))",
                gap:8, marginBottom:16 }}>
                {[
                  { name:"EML", formula:"exp(x) − ln(y)", note:"Best at + and −", color:"#7c6ff7" },
                  { name:"EDL", formula:"exp(x) / ln(y)", note:"Best at ÷  (1 node!)", color:"#2dd4bf" },
                  { name:"EXL", formula:"exp(x) · ln(y)", note:"Best at ln (1 node) and powers", color:"#f59e0b" },
                ].map(op => (
                  <div key={op.name} style={{ background:C.surface,
                    border:`1px solid ${op.color}33`, borderRadius:6, padding:"12px 14px" }}>
                    <div style={{ fontSize:11, fontWeight:700, color:op.color, marginBottom:4 }}>
                      {op.name}
                    </div>
                    <div style={{ fontSize:10, color:C.text, fontFamily:"'Space Mono',monospace",
                      marginBottom:6 }}>{op.formula}</div>
                    <div style={{ fontSize:9, color:C.muted }}>{op.note}</div>
                  </div>
                ))}
              </div>
              <p style={{ fontSize:11, color:C.muted, lineHeight:1.8, marginBottom:12 }}>
                <span style={{ color:C.text }}>BEST</span> is a smart router that automatically
                picks the right operator for each operation:
              </p>
              <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:6,
                overflow:"hidden" }}>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 60px 80px 90px",
                  padding:"8px 12px", background:C.bg,
                  fontSize:9, color:C.muted, textTransform:"uppercase", letterSpacing:"0.05em" }}>
                  <span>Operation</span><span>Uses</span>
                  <span style={{ textAlign:"right" }}>BEST nodes</span>
                  <span style={{ textAlign:"right" }}>EML baseline</span>
                </div>
                {[
                  { op:"ln(x)",  src:"EXL", srcColor:"#f59e0b", best:1,  eml:3  },
                  { op:"xⁿ",    src:"EXL", srcColor:"#f59e0b", best:3,  eml:15 },
                  { op:"x / y", src:"EDL", srcColor:"#2dd4bf", best:1,  eml:15 },
                  { op:"x × y", src:"EDL", srcColor:"#2dd4bf", best:7,  eml:13 },
                  { op:"x + y", src:"EML", srcColor:"#7c6ff7", best:11, eml:11 },
                ].map(row => (
                  <div key={row.op} style={{ display:"grid",
                    gridTemplateColumns:"1fr 60px 80px 90px",
                    padding:"7px 12px", borderTop:`1px solid ${C.border}`, fontSize:11 }}>
                    <span style={{ color:C.text, fontFamily:"'Space Mono',monospace" }}>{row.op}</span>
                    <span style={{ color:row.srcColor, fontWeight:700 }}>{row.src}</span>
                    <span style={{ textAlign:"right", color:C.accent }}>{row.best}n</span>
                    <span style={{ textAlign:"right", color:C.muted,
                      textDecoration:"line-through" }}>{row.eml}n</span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}
      </div>

      {/* ── TAB: DEML ── */}
      {tab === "deml" && (
        <div>
          <div style={{ marginBottom:16 }}>
            <div style={{ fontSize:14, fontWeight:700, color:C.accent, marginBottom:6 }}>
              DEML — Dual Gate Operator
            </div>
            <div style={{ fontSize:11, color:C.muted, lineHeight:1.8, marginBottom:14 }}>
              <code style={{ color:C.blue }}>deml(x, y) = exp(−x) − ln(y)</code>
              {" "}is the dual of EML. While EML natively represents eˣ in 1 node,
              DEML natively represents <code style={{ color:C.blue }}>e^(−x)</code> in 1 node —
              breaking the <strong style={{ color:C.text }}>negative-exponent barrier</strong>.
              In a census of 15 common physics functional forms, 14 require exp(−x) which
              standard EML cannot represent in 1 node.
            </div>
          </div>

          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:10 }}>
              Key identity
            </div>
            <div style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:6,
              padding:"12px 16px", fontFamily:"'Space Mono',monospace", fontSize:12,
              color:C.accent, marginBottom:12 }}>
              deml(x, 1) = exp(−x) − ln(1) = exp(−x)
            </div>
            <div style={{ fontSize:10, color:C.muted, lineHeight:1.8 }}>
              This is the structural mirror of EML's <code>eml(x,1) = exp(x)</code>.
              In BEST routing, EML handles exp(+x) (1 node) and DEML handles exp(−x) (1 node) —
              making Boltzmann factors and Gaussian decay natively reachable without
              a tower construction. DEML alone is incomplete (cannot express exp(+x)).
            </div>
          </div>

          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:10 }}>
              Live verification
            </div>
            {[
              { x:-2, label:"x = −2" },
              { x:0, label:"x = 0" },
              { x:1, label:"x = 1" },
              { x:2.5, label:"x = 2.5" },
            ].map(({ x, label }) => {
              const demlVal = deml(x, 1);
              const refVal  = Math.exp(-x);
              const err     = Math.abs(demlVal - refVal);
              return (
                <div key={x} style={{ display:"grid", gridTemplateColumns:"80px 1fr 1fr 80px",
                  gap:8, padding:"6px 0", borderBottom:`1px solid ${C.border}`,
                  fontSize:10, alignItems:"center" }}>
                  <span style={{ color:C.muted }}>{label}</span>
                  <span style={{ color:C.blue, fontFamily:"'Space Mono',monospace" }}>
                    deml: {demlVal.toExponential(4)}
                  </span>
                  <span style={{ color:C.text, fontFamily:"'Space Mono',monospace" }}>
                    ref: {refVal.toExponential(4)}
                  </span>
                  <span style={{ color: err < 1e-12 ? C.green : C.red, textAlign:"right" }}>
                    {err < 1e-14 ? "< 1e−14" : err.toExponential(2)}
                  </span>
                </div>
              );
            })}
          </div>

          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:10 }}>
              EML + DEML operator comparison
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 60px 60px 60px",
              padding:"6px 10px", background:C.bg,
              fontSize:9, color:C.muted, textTransform:"uppercase", letterSpacing:"0.05em",
              borderRadius:"4px 4px 0 0" }}>
              <span>Function</span><span>EML</span><span>DEML</span><span>BEST</span>
            </div>
            {[
              { fn:"exp(x)",    eml:1,   deml:"—",  best:1  },
              { fn:"exp(−x)",   eml:"✗", deml:1,    best:1  },
              { fn:"ln(x)",     eml:3,   deml:3,    best:1  },
              { fn:"x / y",     eml:15,  deml:"—",  best:1  },
              { fn:"x × y",     eml:13,  deml:"—",  best:7  },
            ].map(row => (
              <div key={row.fn} style={{ display:"grid", gridTemplateColumns:"1fr 60px 60px 60px",
                padding:"6px 10px", borderTop:`1px solid ${C.border}`, fontSize:11 }}>
                <span style={{ color:C.text, fontFamily:"'Space Mono',monospace" }}>{row.fn}</span>
                <span style={{ color: row.eml === "✗" ? C.red : C.muted }}>{row.eml}</span>
                <span style={{ color: row.deml === "—" ? C.muted : C.accent }}>{row.deml}</span>
                <span style={{ color:C.green }}>{row.best}</span>
              </div>
            ))}
          </div>

          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:8 }}>
              Python API (v1.3.0)
            </div>
            <pre style={{ fontSize:10, color:C.blue, background:C.bg,
              padding:"10px 14px", borderRadius:6, margin:0, overflowX:"auto" }}>
{`from monogate import DEML, exp_neg_deml

# 1-node native: exp(−x)
val = exp_neg_deml(1.0)  # → e^(-1) ≈ 0.3679

# Full DEML gate
val2 = DEML.func(2.0, 1.0)  # → exp(-2)`}
            </pre>
          </div>
        </div>
      )}

      {false && (
        <div>
          <div style={{ fontSize:14, fontWeight:700, color:C.accent, marginBottom:14 }}>
            Research Frontiers (Sessions 6–9)
          </div>

          {[
            {
              session: "Session 6 — Physics Law Complexity Census",
              color: "#6ab0f5",
              finding: "1 / 15 physics laws natively representable in EML. 14 blocked by negative-exponent barrier.",
              detail: "15 functional forms (Boltzmann, Arrhenius, Gaussian, …) vs 50 random controls. Random controls 2× easier than physics laws — laws cluster near structural barriers.",
              status: "Complete",
            },
            {
              session: "Session 7 — Operator Comparison",
              color: "#5ec47a",
              finding: "All 5 EML-family operators (EML/EDL/EXL/EAL/EMN) share the negative-exponent barrier. Root cause is structural: every operator uses exp(left_subtree) as first component.",
              detail: "Barrier is operator-independent. No single EML-family operator can represent exp(−x) in fewer nodes than the tower formula.",
              status: "Complete",
            },
            {
              session: "Session 8 — Symbolic Distillation",
              color: "#e8a020",
              finding: "NN → EML distillation pipeline confirms barrier is structural, not search-depth limited. MLP with tanh activations cannot be distilled into EML for decay laws.",
              detail: "Distillation MSE < 1e-4 for growth functions; > 0.1 for decay functions. Confirms Sessions 6–7 conclusions from a different angle.",
              status: "Complete",
            },
            {
              session: "Session 9 — DEML Dual Gate",
              color: "#e05060",
              finding: "DEML: deml(x,y) = exp(−x) − ln(y). With deml(x,1) = exp(−x) as 1-node native, the negative-exponent barrier is broken.",
              detail: "EML+DEML combined census pending. Hypothesis: 8–12 of 15 physics laws become native under EML+DEML routing vs 1/15 for EML alone.",
              status: "Active",
            },
          ].map(item => (
            <div key={item.session} style={{ background:C.surface,
              border:`1px solid ${item.color}33`, borderRadius:8,
              padding:"12px 16px", marginBottom:12 }}>
              <div style={{ display:"flex", justifyContent:"space-between",
                alignItems:"flex-start", marginBottom:8 }}>
                <div style={{ fontSize:11, fontWeight:700, color:item.color }}>
                  {item.session}
                </div>
                <span style={{ fontSize:9, padding:"2px 8px", borderRadius:3,
                  background: item.status === "Active" ? "rgba(232,160,32,0.15)" : "rgba(94,196,122,0.15)",
                  color: item.status === "Active" ? C.accent : C.green,
                  border:`1px solid ${item.status === "Active" ? C.accent : C.green}33` }}>
                  {item.status}
                </span>
              </div>
              <div style={{ fontSize:11, color:C.text, marginBottom:6, lineHeight:1.6 }}>
                {item.finding}
              </div>
              <div style={{ fontSize:10, color:C.muted, lineHeight:1.7 }}>
                {item.detail}
              </div>
            </div>
          ))}

          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:10 }}>
              Open problems
            </div>
            {[
              { id:"P1", text:"Does a complete EML-family operator exist that encodes all 15 physics laws in ≤ 5 nodes each?", status:"open" },
              { id:"P2", text:"DEML partially resolves the negative-exponent barrier. What is the minimal set of operators for full physics law coverage?", status:"partial" },
              { id:"P3", text:"Phantom attractor closed form: is λ_crit = 0.001 a phase transition in the mathematical sense?", status:"open" },
              { id:"P4", text:"What is the N=12 exhaustive search result? (Requires Rust port — Session 10)", status:"planned" },
            ].map(p => (
              <div key={p.id} style={{ display:"flex", gap:10, padding:"6px 0",
                borderBottom:`1px solid ${C.border}`, fontSize:10 }}>
                <span style={{ color:C.accent, minWidth:24, fontWeight:700 }}>{p.id}</span>
                <span style={{ color:C.muted, flex:1, lineHeight:1.6 }}>{p.text}</span>
                <span style={{ color: p.status === "partial" ? C.accent : p.status === "planned" ? C.blue : C.muted,
                  minWidth:50, textAlign:"right" }}>{p.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── TAB: EXPLORER (removed) ── */}
      {false && (
        <div>
          <div style={{ fontSize:14, fontWeight:700, color:C.accent, marginBottom:6 }}>
            Mathematical Explorer
          </div>
          <div style={{ fontSize:11, color:C.muted, lineHeight:1.8, marginBottom:16 }}>
            EMLProverV2 — self-improving identity discovery engine. Generates conjectures
            via 5 mutation tiers, scores by elegance/novelty/interestingness, and
            maintains a catalog of {">"}200 verified EML identities.
          </div>

          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(160px,1fr))",
            gap:10, marginBottom:16 }}>
            {[
              { label:"Catalog size", value:"200+", sub:"verified identities", color:C.accent },
              { label:"Mutation tiers", value:"5", sub:"Tier 1–5 strategies", color:C.blue },
              { label:"UCB1 bandit", value:"Active", sub:"adaptive operator selection", color:C.green },
              { label:"Explore depth", value:"N=10", sub:"max tree depth searched", color:"#f59e0b" },
            ].map(card => (
              <div key={card.label} style={{ background:C.surface,
                border:`1px solid ${card.color}33`, borderRadius:8, padding:"12px 14px" }}>
                <div style={{ fontSize:20, fontWeight:700, color:card.color, marginBottom:2 }}>
                  {card.value}
                </div>
                <div style={{ fontSize:9, color:C.text, textTransform:"uppercase",
                  letterSpacing:"0.06em", marginBottom:2 }}>{card.label}</div>
                <div style={{ fontSize:9, color:C.muted }}>{card.sub}</div>
              </div>
            ))}
          </div>

          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:10 }}>
              Sample identities from catalog
            </div>
            {[
              { expr:"eml(eml(x,1), eml(1,y))", equiv:"exp(exp(x)) − ln(ln(y))", tier:1, nodes:3 },
              { expr:"eml(ln(x), eml(y, 1))",   equiv:"x / exp(y)",              tier:2, nodes:5 },
              { expr:"eml(1, eml(x, eml(1,1)))", equiv:"e − (exp(x) − e)",       tier:3, nodes:5 },
              { expr:"eml(add(x,y), 1)",          equiv:"exp(x+y) = eˣ · eʸ",    tier:1, nodes:13 },
            ].map((row, i) => (
              <div key={i} style={{ padding:"8px 0", borderBottom:`1px solid ${C.border}`,
                fontSize:10 }}>
                <div style={{ display:"flex", justifyContent:"space-between",
                  alignItems:"center", marginBottom:3 }}>
                  <code style={{ color:C.blue }}>{row.expr}</code>
                  <span style={{ fontSize:9, color:C.muted }}>T{row.tier} · {row.nodes}n</span>
                </div>
                <div style={{ color:C.muted }}>≡ {row.equiv}</div>
              </div>
            ))}
          </div>

          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:10 }}>
              Mutation tiers
            </div>
            {[
              { tier:"T1", name:"Direct substitution", desc:"Replace sub-tree with known equivalent" },
              { tier:"T2", name:"Algebraic identity", desc:"Apply eml(eml(a,b),c) = exp(exp(a)−ln(b))−ln(c)" },
              { tier:"T3", name:"Symmetry mutation", desc:"Swap left/right, negate arguments" },
              { tier:"T4", name:"Depth extension", desc:"Add one node layer, test equivalence" },
              { tier:"T5", name:"Analogy", desc:"Port identity from EML to EDL/EXL/DEML family" },
            ].map(row => (
              <div key={row.tier} style={{ display:"flex", gap:10, padding:"5px 0",
                borderBottom:`1px solid ${C.border}`, fontSize:10 }}>
                <span style={{ color:C.accent, minWidth:24, fontWeight:700 }}>{row.tier}</span>
                <span style={{ color:C.text, minWidth:140 }}>{row.name}</span>
                <span style={{ color:C.muted, flex:1 }}>{row.desc}</span>
              </div>
            ))}
          </div>

          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:8 }}>
              Python API (v1.3.0)
            </div>
            <pre style={{ fontSize:10, color:C.blue, background:C.bg,
              padding:"10px 14px", borderRadius:6, margin:0, overflowX:"auto" }}>
{`from monogate.prover import EMLProverV2

prover = EMLProverV2()
# Explore automatically (UCB1 bandit over mutation strategies)
prover.explore(n_rounds=100)

# View mutation hit rates
for row in prover.mutation_stats():
    print(row["mutation"], row["hit_rate"], row["tried"])

# Access catalog
catalog = prover.catalog  # list of verified identities`}
            </pre>
          </div>
        </div>
      )}

      {/* ── TAB: QUANTUM (removed) ── */}
      {false && (
        <div>
          <div style={{ fontSize:12, fontWeight:700, color:C.accent, marginBottom:4 }}>
            Quantum EML — Matrix Gates and Thermodynamics
          </div>
          <div style={{ fontSize:10, color:C.muted, marginBottom:16 }}>
            Quantum thermodynamics is EML arithmetic on density matrices.
            meml(A,B) = expm(A) - logm(B)
          </div>

          {/* Core identities */}
          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:10 }}>
              Core EML Identities in Quantum Mechanics
            </div>
            {[
              { name:"Partition function",  expr:"Z = Tr(mdeml(beta*H, I))",        desc:"Z = Tr(expm(-beta*H))  —  1-node DEML expression" },
              { name:"Von Neumann entropy", expr:"S(rho) = Tr(rho * meml(0, rho)) - 1", desc:"S = -Tr(rho * ln rho)  —  1-node EML expression" },
              { name:"Free energy",         expr:"F = -kT * ln(Tr(mdeml(beta*H, I)))",  desc:"F = -kT * ln(Z)  —  scalar EML over partition fn" },
              { name:"Mutual information",  expr:"I(A:B) = S(rhoA) + S(rhoB) - S(rhoAB)", desc:"Bell state: I(A:B) = 2*ln(2)  (maximal)" },
            ].map((row, i) => (
              <div key={i} style={{ padding:"8px 0", borderBottom:`1px solid ${C.border}`,
                fontSize:10 }}>
                <div style={{ display:"flex", justifyContent:"space-between",
                  alignItems:"center", marginBottom:3 }}>
                  <span style={{ color:C.blue, fontWeight:700 }}>{row.name}</span>
                </div>
                <code style={{ color:C.accent, display:"block", marginBottom:3 }}>{row.expr}</code>
                <div style={{ color:C.muted }}>{row.desc}</div>
              </div>
            ))}
          </div>

          {/* Matrix gates */}
          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:10 }}>
              Matrix EML Gates (Python API)
            </div>
            <pre style={{ fontSize:10, color:C.blue, background:C.bg,
              padding:"10px 14px", borderRadius:6, margin:0, overflowX:"auto" }}>
{`from monogate.quantum import (
    meml, mdeml,                    # matrix EML/DEML gates
    von_neumann_entropy,            # S(rho) = -Tr(rho ln rho)
    partition_function,             # Z = Tr(mdeml(beta*H, I))
    quantum_free_energy,            # F = -kT * ln(Z)
    thermal_state,                  # rho = expm(-beta*H) / Z
    quantum_mutual_info,            # I(A:B) = S_A + S_B - S_AB
    bell_state, partial_trace,      # test systems
)

import numpy as np
H = np.diag([0.5, -0.5])           # spin-1/2 Hamiltonian
beta = 1.0                          # inverse temperature

Z = partition_function(H, beta)    # = 2*cosh(0.5)
F = quantum_free_energy(H, beta)   # = -kT * ln(Z)

rho_bell = bell_state(0)           # |Phi+> density matrix
I_AB = quantum_mutual_info(rho_bell, 2, 2)  # = 2*ln(2)`}
            </pre>
          </div>

          {/* Verification results */}
          <div style={{ background:C.surface, border:`1px solid ${C.border}`,
            borderRadius:8, padding:16, marginBottom:12 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.text, marginBottom:10 }}>
              Verified Results (19 tests passing)
            </div>
            {[
              { test:"Partition function",       result:"Z = 2·cosh(0.5) at beta=1, omega=1", pass:true },
              { test:"Von Neumann entropy",      result:"S(I/n) = ln(n) for n=2,3,4", pass:true },
              { test:"Entropy via meml gate",    result:"matches eigenvalue method to 1e-10", pass:true },
              { test:"Bell state mutual info",   result:"I(A:B) = 2·ln(2) = 1.386...", pass:true },
              { test:"Product state",            result:"I(A:B) = 0 (no entanglement)", pass:true },
              { test:"Free energy consistency",  result:"F = E - T*S at thermal equilibrium", pass:true },
              { test:"High-T thermal state",     result:"rho -> I/n as beta -> 0", pass:true },
              { test:"Harmonic oscillator Z",    result:"< 1% error at 20 levels", pass:true },
            ].map((row, i) => (
              <div key={i} style={{ display:"flex", alignItems:"center", gap:10,
                padding:"5px 0", borderBottom:`1px solid ${C.border}`, fontSize:10 }}>
                <span style={{ color: row.pass ? C.green : C.red, minWidth:12 }}>
                  {row.pass ? "✓" : "✗"}
                </span>
                <span style={{ color:C.text, minWidth:180 }}>{row.test}</span>
                <span style={{ color:C.muted }}>{row.result}</span>
              </div>
            ))}
          </div>

          {/* Key theorem */}
          <div style={{ background:`rgba(106,176,245,0.05)`, border:`1px solid rgba(106,176,245,0.2)`,
            borderRadius:8, padding:16 }}>
            <div style={{ fontSize:11, fontWeight:700, color:C.blue, marginBottom:8 }}>
              Theorem: Quantum Thermodynamics is EML Arithmetic on Density Matrices
            </div>
            <div style={{ fontSize:10, color:C.muted, lineHeight:1.6 }}>
              The partition function Z = Tr(mdeml(beta*H, I)) is a 1-node DEML expression.<br/>
              The von Neumann entropy S(rho) = Tr(rho * meml(0, rho)) - 1 is a 1-node EML expression.<br/>
              The free energy F = -kT * ln(Z) is a scalar EML composition over the partition function.<br/>
              EML and DEML gates are the natural language for quantum statistical mechanics.
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{ marginTop:20, paddingTop:14, borderTop:`1px solid ${C.border}`,
        fontSize:9, color:C.muted, display:"flex", justifyContent:"space-between",
        flexWrap:"wrap", gap:6 }}>
        <span>Odrzywołek (2026) · arXiv:2603.21852 · CC BY 4.0</span>
        <span>Research by Arturo R. Almaguer · github.com/agent-maestro/monogate</span>
      </div>
    </div>
  );
}
