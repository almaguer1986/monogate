import { useState, useRef, useEffect, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════════
// EML CORE
// ═══════════════════════════════════════════════════════════════════
const eml = (x, y) => {
  const ex = Math.exp(Math.min(x, 20));
  if (y <= 0) return ex;
  return ex - Math.log(y);
};

function evalNode(node, nodes, varVal, depth = 0) {
  if (depth > 25) return 0;
  if (node.type === "constant") return node.value;
  if (node.type === "variable") return varVal;
  const lN = node.inputs?.left ? nodes.find(n => n.id === node.inputs.left) : null;
  const rN = node.inputs?.right ? nodes.find(n => n.id === node.inputs.right) : null;
  const lV = lN ? evalNode(lN, nodes, varVal, depth + 1) : 1;
  const rV = rN ? evalNode(rN, nodes, varVal, depth + 1) : 1;
  const result = eml(lV, rV);
  return Math.max(-1e8, Math.min(1e8, isNaN(result) || !isFinite(result) ? 0 : result));
}

function getEvalChain(node, nodes, varVal, depth = 0) {
  if (depth > 25) return [];
  if (node.type === "constant") return [{ eq: `${node.value}`, val: node.value }];
  if (node.type === "variable") return [{ eq: `x = ${varVal.toFixed(2)}`, val: varVal }];
  const lN = node.inputs?.left ? nodes.find(n => n.id === node.inputs.left) : null;
  const rN = node.inputs?.right ? nodes.find(n => n.id === node.inputs.right) : null;
  const lV = lN ? evalNode(lN, nodes, varVal, depth + 1) : 1;
  const rV = rN ? evalNode(rN, nodes, varVal, depth + 1) : 1;
  const result = eml(lV, rV);
  const clamped = Math.max(-1e8, Math.min(1e8, isNaN(result) || !isFinite(result) ? 0 : result));
  return [
    ...(lN ? getEvalChain(lN, nodes, varVal, depth + 1) : []),
    ...(rN ? getEvalChain(rN, nodes, varVal, depth + 1) : []),
    { eq: `eml(${lV.toFixed(2)}, ${rV.toFixed(2)})`, val: clamped },
  ];
}

function treeDepth(node, nodes, d = 0) {
  if (d > 25 || node.type === "constant" || node.type === "variable") return d;
  const l = node.inputs?.left ? nodes.find(n => n.id === node.inputs.left) : null;
  const r = node.inputs?.right ? nodes.find(n => n.id === node.inputs.right) : null;
  return Math.max(l ? treeDepth(l, nodes, d + 1) : d, r ? treeDepth(r, nodes, d + 1) : d);
}

function wouldCycle(fromId, toId, nodes) {
  // Would connecting toId's output into fromId's input create a cycle?
  // Check if fromId is an ancestor of toId
  const visited = new Set();
  const check = (id) => {
    if (id === fromId) return true;
    if (visited.has(id)) return false;
    visited.add(id);
    const node = nodes.find(n => n.id === id);
    if (!node || node.type !== "eml") return false;
    return (node.inputs?.left && check(node.inputs.left)) || (node.inputs?.right && check(node.inputs.right));
  };
  return check(toId);
}

function identifyResult(val) {
  const checks = [
    { name: "e", ref: Math.E }, { name: "e − 1", ref: Math.E - 1 }, { name: "e²", ref: Math.E ** 2 },
    { name: "e^e", ref: Math.E ** Math.E }, { name: "1", ref: 1 }, { name: "0", ref: 0 },
    { name: "2", ref: 2 }, { name: "3", ref: 3 }, { name: "π", ref: Math.PI },
    { name: "ln(2)", ref: Math.log(2) }, { name: "−1", ref: -1 }, { name: "1/e", ref: 1 / Math.E },
    { name: "e³", ref: Math.E ** 3 }, { name: "√e", ref: Math.sqrt(Math.E) },
  ];
  for (const c of checks) if (Math.abs(val - c.ref) < 0.005) return c.name;
  return null;
}

// ═══════════════════════════════════════════════════════════════════
// PRESETS
// ═══════════════════════════════════════════════════════════════════
// Build expression string from tree
function buildExpr(node, nodes, depth = 0) {
  if (depth > 25) return "...";
  if (node.type === "constant") return `${node.value}`;
  if (node.type === "variable") return "x";
  const lN = node.inputs?.left ? nodes.find(n => n.id === node.inputs.left) : null;
  const rN = node.inputs?.right ? nodes.find(n => n.id === node.inputs.right) : null;
  const lE = lN ? buildExpr(lN, nodes, depth + 1) : "1";
  const rE = rN ? buildExpr(rN, nodes, depth + 1) : "1";
  return `eml(${lE}, ${rE})`;
}

// ═══════════════════════════════════════════════════════════════════
// CHALLENGE TARGETS
// ═══════════════════════════════════════════════════════════════════
const CHALLENGES = [
  { name: "Build e", target: Math.E, hint: "eml(1, 1)", stars3: 3, stars2: 4, stars1: 6 },
  { name: "Build e²", target: Math.E ** 2, hint: "What does eml(2, 1) give you?", stars3: 3, stars2: 4, stars1: 6 },
  { name: "Build e^e", target: Math.E ** Math.E, hint: "Feed e into another eml", stars3: 5, stars2: 6, stars1: 8 },
  { name: "Build 2", target: 2, hint: "e − (e−1) = 2? Or eml with the right constants...", stars3: 4, stars2: 6, stars1: 8 },
  { name: "Build 1/e", target: 1 / Math.E, hint: "What about negative inputs?", stars3: 3, stars2: 5, stars1: 7 },
  { name: "Build 0", target: 0, hint: "When does exp(x) = ln(y)?", stars3: 3, stars2: 5, stars1: 7 },
];

const PRESETS = [
  { name: "Start here", nodes: [
    { id: "c1", type: "constant", value: 1, x: 60, y: 90 },
    { id: "c2", type: "constant", value: 1, x: 60, y: 220 },
    { id: "e1", type: "eml", x: 310, y: 145, inputs: { left: null, right: null } },
  ], output: "e1" },
  { name: "e = 2.718", nodes: [
    { id: "c1", type: "constant", value: 1, x: 60, y: 90 },
    { id: "c2", type: "constant", value: 1, x: 60, y: 220 },
    { id: "e1", type: "eml", x: 310, y: 145, inputs: { left: "c1", right: "c2" } },
  ], output: "e1" },
  { name: "e^e", nodes: [
    { id: "c1", type: "constant", value: 1, x: 40, y: 60 },
    { id: "c2", type: "constant", value: 1, x: 40, y: 170 },
    { id: "c3", type: "constant", value: 1, x: 230, y: 240 },
    { id: "e1", type: "eml", x: 200, y: 105, inputs: { left: "c1", right: "c2" } },
    { id: "e2", type: "eml", x: 420, y: 160, inputs: { left: "e1", right: "c3" } },
  ], output: "e2" },
  { name: "ln(x)", nodes: [
    { id: "v1", type: "variable", x: 30, y: 60 },
    { id: "c1", type: "constant", value: 1, x: 30, y: 170 },
    { id: "c2", type: "constant", value: 1, x: 30, y: 280 },
    { id: "c3", type: "constant", value: 1, x: 300, y: 260 },
    { id: "e1", type: "eml", x: 170, y: 100, inputs: { left: "c1", right: "v1" } },
    { id: "e2", type: "eml", x: 170, y: 220, inputs: { left: "e1", right: "c2" } },
    { id: "e3", type: "eml", x: 430, y: 170, inputs: { left: "c3", right: "e2" } },
  ], output: "e3" },
  { name: "exp(x)", nodes: [
    { id: "v1", type: "variable", x: 60, y: 110 },
    { id: "c1", type: "constant", value: 1, x: 60, y: 230 },
    { id: "e1", type: "eml", x: 310, y: 155, inputs: { left: "v1", right: "c1" } },
  ], output: "e1" },
  { name: "Blank", nodes: [], output: null },
];

// ═══════════════════════════════════════════════════════════════════
// VIZ MODES
// ═══════════════════════════════════════════════════════════════════
function RingsVis({ value, depth, hasVar, curveData }) {
  const ref = useRef(null), t = useRef(0), f = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height, cx = w / 2, cy = h / 2;
    t.current = 0;
    const go = () => {
      t.current += 0.02; const time = t.current;
      ctx.fillStyle = "rgba(6,2,15,0.12)"; ctx.fillRect(0, 0, w, h);
      const v = Math.max(-50, Math.min(50, value || 0));
      const hue = ((v * 30) + 200) % 360;
      const rings = Math.max(1, Math.min(15, Math.abs(v) * 1.2));
      const speed = 0.3 + Math.abs(v) * 0.04;
      for (let i = 0; i < rings; i++) {
        const frac = i / rings, r = 8 + frac * (Math.min(w, h) * 0.42);
        const wobble = Math.sin(time * speed + i * 0.8) * 4 * (depth + 1);
        ctx.beginPath();
        for (let a = 0; a < Math.PI * 2; a += 0.04) {
          const rr = r + Math.sin(a * (depth + 2) + time * speed) * wobble + Math.sin(a * 3 + time * 0.7 + i) * 2;
          if (a === 0) ctx.moveTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr); else ctx.lineTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr);
        }
        ctx.closePath(); ctx.strokeStyle = `hsla(${(hue + i * 18) % 360},85%,62%,${0.12 + (1 - frac) * 0.45})`; ctx.lineWidth = 1 + (1 - frac) * 2; ctx.stroke();
      }
      const cr = 5 + Math.sin(time * 2) * 2.5;
      const cg = ctx.createRadialGradient(cx, cy, 0, cx, cy, cr * 3);
      cg.addColorStop(0, `hsla(${hue},90%,85%,0.7)`); cg.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = cg; ctx.beginPath(); ctx.arc(cx, cy, cr * 3, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(cx, cy, cr, 0, Math.PI * 2); ctx.fillStyle = `hsla(${hue},90%,85%,0.9)`; ctx.fill();
      for (let i = 0; i < Math.min(depth * 4 + 2, 20); i++) {
        const a = (i / 20) * Math.PI * 2 + time * 0.4, pr = 15 + Math.sin(time * 0.8 + i * 1.5) * 12 + depth * 6;
        ctx.beginPath(); ctx.arc(cx + Math.cos(a) * pr, cy + Math.sin(a) * pr, 1.5, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${(hue + i * 20) % 360},85%,70%,${0.3 + Math.sin(time + i * 2) * 0.2})`; ctx.fill();
      }
      f.current = requestAnimationFrame(go);
    };
    ctx.fillStyle = "#06020F"; ctx.fillRect(0, 0, w, h); go();
    return () => cancelAnimationFrame(f.current);
  }, [value, depth]);
  return <canvas ref={ref} width={280} height={280} style={{ width: "100%", height: "100%", display: "block", borderRadius: 12 }} />;
}

function CurveVis({ curveData, depth }) {
  const ref = useRef(null), t = useRef(0), f = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height;
    t.current = 0;
    const go = () => {
      t.current += 0.02; const time = t.current;
      ctx.fillStyle = "rgba(6,2,15,0.15)"; ctx.fillRect(0, 0, w, h);
      if (!curveData || curveData.length === 0) { f.current = requestAnimationFrame(go); return; }
      // Find bounds
      let minY = Infinity, maxY = -Infinity;
      curveData.forEach(p => { if (isFinite(p.y)) { minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y); } });
      if (!isFinite(minY)) { minY = -5; maxY = 5; }
      const rangeY = Math.max(maxY - minY, 0.1);
      const pad = 30;
      // Axes
      const zeroY = h - pad - ((0 - minY) / rangeY) * (h - pad * 2);
      const zeroX = pad + ((0 - (-5)) / 10) * (w - pad * 2);
      ctx.strokeStyle = "rgba(139,92,246,0.15)"; ctx.lineWidth = 0.5;
      ctx.beginPath(); ctx.moveTo(pad, zeroY); ctx.lineTo(w - pad, zeroY); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(zeroX, pad); ctx.lineTo(zeroX, h - pad); ctx.stroke();
      // Axis labels
      ctx.fillStyle = "rgba(139,92,246,0.3)"; ctx.font = "9px monospace"; ctx.textAlign = "center";
      ctx.fillText("x", w - pad + 10, zeroY + 4);
      ctx.fillText("f(x)", zeroX, pad - 8);
      // Curve
      ctx.beginPath();
      let started = false;
      const hue = ((depth * 60) + 200) % 360;
      curveData.forEach((p, i) => {
        if (!isFinite(p.y)) { started = false; return; }
        const sx = pad + ((p.x - (-5)) / 10) * (w - pad * 2);
        const sy = h - pad - ((p.y - minY) / rangeY) * (h - pad * 2);
        if (!started) { ctx.moveTo(sx, sy); started = true; } else ctx.lineTo(sx, sy);
      });
      ctx.strokeStyle = `hsla(${hue},85%,65%,0.8)`; ctx.lineWidth = 2.5; ctx.stroke();
      // Glow particles on curve
      curveData.forEach((p, i) => {
        if (i % 4 !== 0 || !isFinite(p.y)) return;
        const sx = pad + ((p.x - (-5)) / 10) * (w - pad * 2);
        const sy = h - pad - ((p.y - minY) / rangeY) * (h - pad * 2);
        const sz = 1.5 + Math.sin(time * 2 + i * 0.3) * 0.8;
        ctx.beginPath(); ctx.arc(sx, sy, sz, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${(hue + i * 2) % 360},90%,75%,${0.4 + Math.sin(time + i) * 0.2})`; ctx.fill();
      });
      f.current = requestAnimationFrame(go);
    };
    ctx.fillStyle = "#06020F"; ctx.fillRect(0, 0, w, h); go();
    return () => cancelAnimationFrame(f.current);
  }, [curveData, depth]);
  return <canvas ref={ref} width={280} height={280} style={{ width: "100%", height: "100%", display: "block", borderRadius: 12 }} />;
}

function SpiralVis({ value, depth }) {
  const ref = useRef(null), t = useRef(0), f = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height, cx = w / 2, cy = h / 2;
    t.current = 0;
    const go = () => {
      t.current += 0.016; const time = t.current;
      ctx.fillStyle = "rgba(6,2,15,0.08)"; ctx.fillRect(0, 0, w, h);
      const v = Math.max(0.5, Math.min(20, Math.abs(value || 1)));
      const hue = ((value * 30) + 200) % 360;
      const arms = Math.max(1, Math.min(8, depth + 1));
      const count = 300;
      for (let arm = 0; arm < arms; arm++) {
        const armOff = (arm / arms) * Math.PI * 2;
        ctx.beginPath();
        for (let i = 0; i < count; i++) {
          const frac = i / count;
          const angle = frac * v * 1.5 + armOff + time * 0.3;
          const r = frac * Math.min(w, h) * 0.42;
          const px = cx + Math.cos(angle) * r, py = cy + Math.sin(angle) * r;
          if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.strokeStyle = `hsla(${(hue + arm * (360 / arms)) % 360},80%,60%,${0.3 + Math.sin(time + arm) * 0.15})`;
        ctx.lineWidth = 1.5; ctx.stroke();
      }
      // Center
      ctx.beginPath(); ctx.arc(cx, cy, 4, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${hue},90%,85%,0.8)`; ctx.fill();
      f.current = requestAnimationFrame(go);
    };
    ctx.fillStyle = "#06020F"; ctx.fillRect(0, 0, w, h); go();
    return () => cancelAnimationFrame(f.current);
  }, [value, depth]);
  return <canvas ref={ref} width={280} height={280} style={{ width: "100%", height: "100%", display: "block", borderRadius: 12 }} />;
}

// ═══════════════════════════════════════════════════════════════════
// AUDIO
// ═══════════════════════════════════════════════════════════════════
function useAudio(value, depth, enabled) {
  const acRef = useRef(null), oscsRef = useRef([]), gainRef = useRef(null);
  useEffect(() => {
    if (!enabled) {
      oscsRef.current.forEach(o => { try { o.stop(); } catch {} });
      if (acRef.current) try { acRef.current.close(); } catch {};
      acRef.current = null; oscsRef.current = []; return;
    }
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)();
      acRef.current = ac;
      const gain = ac.createGain(); gain.gain.setValueAtTime(0.04, ac.currentTime);
      gain.connect(ac.destination); gainRef.current = gain;
      const harmonics = [1, 1.5, 2, 3];
      harmonics.forEach((h, i) => {
        const o = ac.createOscillator(); o.type = i === 0 ? "sine" : "triangle";
        o.frequency.setValueAtTime(220, ac.currentTime);
        const g = ac.createGain(); g.gain.setValueAtTime(0.03 / (h), ac.currentTime);
        o.connect(g); g.connect(gain); o.start(); oscsRef.current.push(o);
      });
    } catch {}
    return () => {
      oscsRef.current.forEach(o => { try { o.stop(); } catch {} });
      if (acRef.current) try { acRef.current.close(); } catch {};
      oscsRef.current = [];
    };
  }, [enabled]);

  useEffect(() => {
    if (!enabled || !acRef.current || oscsRef.current.length === 0) return;
    const base = 110 + Math.max(-200, Math.min(400, (value || 0) * 30));
    oscsRef.current.forEach((o, i) => {
      const h = [1, 1.5, 2, 3][i];
      o.frequency.setValueAtTime(Math.max(20, base * h), acRef.current.currentTime);
    });
  }, [value, enabled]);
}

// ═══════════════════════════════════════════════════════════════════
// AUTO ARRANGE
// ═══════════════════════════════════════════════════════════════════
function autoArrange(nodes, outputId) {
  if (nodes.length === 0) return nodes;
  // Assign depth to each node (distance from output)
  const depthMap = {};
  const assignDepth = (id, d) => {
    if (depthMap[id] !== undefined && depthMap[id] >= d) return;
    depthMap[id] = d;
    const node = nodes.find(n => n.id === id);
    if (node?.type === "eml" && node.inputs) {
      if (node.inputs.left) assignDepth(node.inputs.left, d + 1);
      if (node.inputs.right) assignDepth(node.inputs.right, d + 1);
    }
  };
  if (outputId) assignDepth(outputId, 0);
  // Unconnected nodes
  nodes.forEach(n => { if (depthMap[n.id] === undefined) depthMap[n.id] = 0; });
  const maxD = Math.max(...Object.values(depthMap));
  // Group by depth
  const groups = {};
  nodes.forEach(n => { const d = depthMap[n.id] || 0; if (!groups[d]) groups[d] = []; groups[d].push(n.id); });
  // Position: rightmost = depth 0
  const arranged = nodes.map(n => {
    const d = depthMap[n.id] || 0;
    const group = groups[d] || [n.id];
    const idx = group.indexOf(n.id);
    const x = 450 - d * 150;
    const spacing = 70;
    const totalH = (group.length - 1) * spacing;
    const y = 200 - totalH / 2 + idx * spacing;
    return { ...n, x: Math.max(30, x), y: Math.max(30, Math.min(340, y)) };
  });
  return arranged;
}

// ═══════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════
let nextId = 100;
const NW = 100, NH_E = 66, NH_C = 44, NH_V = 44;
function nodeH(n) { return n.type === "eml" ? NH_E : NH_C; }

export default function EmlBuilder() {
  const [nodes, setNodes] = useState(PRESETS[0].nodes.map(n => ({ ...n, inputs: n.inputs ? { ...n.inputs } : undefined })));
  const [outputId, setOutputId] = useState(PRESETS[0].output);
  const [draggingNode, setDraggingNode] = useState(null);
  const [connecting, setConnecting] = useState(null); // { fromId, slot, direction: "from-input" | "from-output" }
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [pulse, setPulse] = useState(0);
  const [varVal, setVarVal] = useState(1);
  const [vizMode, setVizMode] = useState("rings"); // rings, curve, spiral
  const [audioOn, setAudioOn] = useState(false);
  const [editingConst, setEditingConst] = useState(null);
  const [editVal, setEditVal] = useState("");
  const [zoom, setZoom] = useState(1);
  const [challenge, setChallenge] = useState(null); // index into CHALLENGES or null
  const svgRef = useRef(null);
  const dragOff = useRef({ x: 0, y: 0 });

  useEffect(() => { let fr; const tick = () => { setPulse(p => p + 0.03); fr = requestAnimationFrame(tick); }; tick(); return () => cancelAnimationFrame(fr); }, []);

  // Auto-detect if tree has variables
  const hasVar = nodes.some(n => n.type === "variable");
  const outputNode = outputId ? nodes.find(n => n.id === outputId) : null;
  const evalVal = outputNode ? evalNode(outputNode, nodes, varVal) : 0;
  const depth = outputNode ? treeDepth(outputNode, nodes) : 0;
  const identity = !hasVar ? identifyResult(evalVal) : null;
  const chain = outputNode ? getEvalChain(outputNode, nodes, varVal) : [];
  const hasOutput = outputNode && (outputNode.type !== "eml" || outputNode.inputs?.left || outputNode.inputs?.right);
  const expr = outputNode ? buildExpr(outputNode, nodes) : "";
  const VBW = 580 / zoom, VBH = 420 / zoom;
  const vbX = (580 - VBW) / 2, vbY = (420 - VBH) / 2;

  // Challenge evaluation
  const activeChallenge = challenge !== null ? CHALLENGES[challenge] : null;
  const challengeHit = activeChallenge && hasOutput && Math.abs(evalVal - activeChallenge.target) < 0.01;
  const challengeStars = activeChallenge && challengeHit ? (nodes.length <= activeChallenge.stars3 ? 3 : nodes.length <= activeChallenge.stars2 ? 2 : nodes.length <= activeChallenge.stars1 ? 1 : 0) : 0;

  // Curve data for variable mode
  const curveData = hasVar && outputNode ? Array.from({ length: 100 }, (_, i) => {
    const x = -5 + (i / 99) * 10;
    const y = evalNode(outputNode, nodes, x);
    return { x, y: isFinite(y) ? y : NaN };
  }) : [];

  // Audio
  useAudio(evalVal, depth, audioOn && hasOutput);

  // Hint
  const hint = (() => {
    const emlNodes = nodes.filter(n => n.type === "eml");
    const connected = emlNodes.filter(n => n.inputs?.left || n.inputs?.right);
    if (nodes.length === 0) return { msg: "Add an eml node and some constants to get started", type: "info" };
    if (emlNodes.length === 0) return { msg: "Add an eml(x,y) node — that's the operator", type: "info" };
    if (connected.length === 0) return { msg: "Click a purple (x) or pink (y) port, then click a green (out) port to connect", type: "info" };
    if (connected.some(n => n.inputs?.left && n.inputs?.right)) return { msg: hasVar ? `f(${varVal.toFixed(1)}) = ${evalVal.toFixed(4)} — drag the x slider to explore` : `Computing! Result: ${evalVal.toFixed(4)}${identity ? ` = ${identity}` : ""}`, type: "done" };
    return { msg: "One input connected — now connect the other port too", type: "info" };
  })();

  const getPos = useCallback((e) => {
    const svg = svgRef.current; if (!svg) return { x: 0, y: 0 };
    const rect = svg.getBoundingClientRect();
    const src = e.touches?.length ? e.touches[0] : e.changedTouches?.length ? e.changedTouches[0] : e;
    const w = 580 / zoom, h = 420 / zoom;
    return { x: (580 - w) / 2 + (src.clientX - rect.left) * (w / rect.width), y: (420 - h) / 2 + (src.clientY - rect.top) * (h / rect.height) };
  }, [zoom]);

  const handleMouseMove = (e) => {
    const p = getPos(e); setMousePos(p);
    if (draggingNode) setNodes(prev => prev.map(n => n.id === draggingNode ? { ...n, x: Math.max(5, Math.min(480, p.x - dragOff.current.x)), y: Math.max(5, Math.min(370, p.y - dragOff.current.y)) } : n));
  };

  const handleMouseUp = (e) => {
    setDraggingNode(null);
    // Do NOT clear connecting here — ports handle their own clicks via onMouseDown
  };

  // Click empty canvas = cancel connecting
  const handleCanvasClick = (e) => {
    if (e.target === svgRef.current || e.target.tagName === "circle" && parseFloat(e.target.getAttribute("r")) < 1) {
      // Clicked on empty space or grid dot
      setConnecting(null);
    }
  };

  const startDrag = (id, e) => { if (connecting) return; e.stopPropagation(); e.preventDefault(); const node = nodes.find(n => n.id === id); const p = getPos(e); dragOff.current = { x: p.x - node.x, y: p.y - node.y }; setDraggingNode(id); };

  const handlePortMouseDown = (nodeId, portType, slot, e) => {
    e.stopPropagation();
    e.preventDefault();
    if (!connecting) {
      // Start a connection
      if (portType === "input") setConnecting({ fromId: nodeId, slot, direction: "from-input" });
      else setConnecting({ fromId: nodeId, direction: "from-output" });
      return;
    }
    // Complete a connection
    if (connecting.fromId === nodeId) { setConnecting(null); return; }
    if (connecting.direction === "from-input" && portType === "output") {
      if (wouldCycle(connecting.fromId, nodeId, nodes)) { setConnecting(null); return; }
      setNodes(prev => prev.map(n => n.id === connecting.fromId && n.type === "eml" ? { ...n, inputs: { ...n.inputs, [connecting.slot]: nodeId } } : n));
    } else if (connecting.direction === "from-output" && portType === "input") {
      if (wouldCycle(nodeId, connecting.fromId, nodes)) { setConnecting(null); return; }
      setNodes(prev => prev.map(n => n.id === nodeId && n.type === "eml" ? { ...n, inputs: { ...n.inputs, [slot]: connecting.fromId } } : n));
    } else if (connecting.direction === "from-input" && portType === "input") {
      // Clicked another input — restart connection from this input instead
      setConnecting({ fromId: nodeId, slot, direction: "from-input" });
      return;
    } else if (connecting.direction === "from-output" && portType === "output") {
      // Clicked another output — restart from this output
      setConnecting({ fromId: nodeId, direction: "from-output" });
      return;
    }
    setConnecting(null);
  };

  // Disconnect by clicking a filled port
  const disconnectPort = (nodeId, slot, e) => {
    e.stopPropagation();
    e.preventDefault();
    setNodes(prev => prev.map(n => n.id === nodeId ? { ...n, inputs: { ...n.inputs, [slot]: null } } : n));
  };

  const addEml = (x, y) => { const id = `eml_${nextId++}`; setNodes(prev => [...prev, { id, type: "eml", x: x || 250 + Math.random() * 60, y: y || 120 + Math.random() * 80, inputs: { left: null, right: null } }]); if (!outputId) setOutputId(id); };
  const addConst = (v) => { const id = `c_${nextId++}`; setNodes(prev => [...prev, { id, type: "constant", value: v, x: 50 + Math.random() * 60, y: 80 + Math.random() * 200 }]); };
  const addVariable = () => { if (hasVar) return; const id = `v_${nextId++}`; setNodes(prev => [...prev, { id, type: "variable", x: 50, y: 150 }]); };
  const removeNode = (id) => { setNodes(prev => prev.map(n => n.type === "eml" && n.inputs ? { ...n, inputs: { left: n.inputs.left === id ? null : n.inputs.left, right: n.inputs.right === id ? null : n.inputs.right } } : n).filter(n => n.id !== id)); if (outputId === id) setOutputId(null); };
  const dupNode = (id) => { const orig = nodes.find(n => n.id === id); if (!orig) return; const nid = `${orig.type}_${nextId++}`; setNodes(prev => [...prev, { ...orig, id: nid, x: orig.x + 30, y: orig.y + 30, inputs: orig.inputs ? { left: null, right: null } : undefined }]); };
  const changeConst = (id, d) => { setNodes(prev => prev.map(n => n.id === id && n.type === "constant" ? { ...n, value: Math.round((n.value + d) * 10) / 10 } : n)); };
  const commitEdit = (id) => { const v = parseFloat(editVal); if (!isNaN(v)) setNodes(prev => prev.map(n => n.id === id ? { ...n, value: v } : n)); setEditingConst(null); };
  const doAutoArrange = () => { setNodes(prev => autoArrange(prev, outputId)); };
  const loadPreset = (p) => { nextId = 100; setNodes(p.nodes.map(n => ({ ...n, inputs: n.inputs ? { ...n.inputs } : undefined }))); setOutputId(p.output); setConnecting(null); setDraggingNode(null); setEditingConst(null); };
  const handleCanvasDblClick = (e) => { const p = getPos(e); addEml(p.x - NW / 2, p.y - NH_E / 2); };

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 760, margin: "0 auto", padding: "0 0 2rem" }}>
      {/* Header */}
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.4rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#06B6D4", fontWeight: 500, marginBottom: 4 }}>monogate.dev</div>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>EML Builder</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          Connect bricks. Watch <code style={{ background: "var(--color-background-secondary, #f0f0ff)", padding: "1px 4px", borderRadius: 4, fontFamily: "var(--font-mono)", fontSize: 11, color: "#7C3AED" }}>eml(x,y) = exp(x) − ln(y)</code> compute live.
        </p>
      </div>

      {/* Hint */}
      <div style={{ textAlign: "center", padding: "6px 14px", margin: "6px 0",
        background: hint.type === "done" ? "rgba(16,185,129,0.08)" : "rgba(124,58,237,0.06)",
        borderRadius: 8, fontSize: 12, color: hint.type === "done" ? "#059669" : "#7C3AED", fontWeight: 500,
        border: `1px solid ${hint.type === "done" ? "rgba(16,185,129,0.12)" : "rgba(124,58,237,0.08)"}`,
      }}>{hint.type === "done" ? "✓ " : "→ "}{hint.msg}</div>

      {/* Main grid */}
      <div className="eml-main-grid" style={{ display: "grid", gridTemplateColumns: "1fr 210px", gap: 10 }}>
        {/* CANVAS */}
        <div className="eml-canvas-wrap" style={{ position: "relative", background: "var(--color-background-secondary, #f8f5ff)", border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.1))", borderRadius: 14, overflow: "hidden", aspectRatio: "580/420" }}>
          <svg ref={svgRef} width="100%" height="100%" viewBox={`${vbX} ${vbY} ${VBW} ${VBH}`} style={{ position: "absolute", top: 0, left: 0, touchAction: "none", cursor: connecting ? "crosshair" : "default" }}
            onMouseMove={handleMouseMove} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp} onDoubleClick={handleCanvasDblClick} onClick={handleCanvasClick}
            onTouchMove={(e) => { e.preventDefault(); handleMouseMove(e); }}
            onTouchEnd={(e) => { e.preventDefault(); handleMouseUp(e); }}>
            {/* Grid */}
            {Array.from({ length: 12 }).map((_, i) => Array.from({ length: 9 }).map((_, j) => (
              <circle key={`${i}-${j}`} cx={i * 50 + 24} cy={j * 48 + 22} r="0.5" fill="var(--color-border-tertiary,#ddd)" opacity="0.2" />
            )))}

            {/* CONNECTIONS */}
            {nodes.filter(n => n.type === "eml" && n.inputs).map(n => {
              const draw = (sourceId, slot) => {
                const sN = nodes.find(nn => nn.id === sourceId); if (!sN) return null;
                const sx = sN.x + NW, sy = sN.y + nodeH(sN) / 2;
                const ey = n.y + (slot === "left" ? 22 : 44), ex = n.x;
                const cpx = (sx + ex) / 2;
                const color = slot === "left" ? "#8B5CF6" : "#EC4899";
                const sVal = evalNode(sN, nodes, varVal);
                return (
                  <g key={`${n.id}-${slot}`}>
                    <path d={`M${sx} ${sy} C${cpx} ${sy},${cpx} ${ey},${ex} ${ey}`} fill="none" stroke={color} strokeWidth="2.5" strokeOpacity="0.15" />
                    <path d={`M${sx} ${sy} C${cpx} ${sy},${cpx} ${ey},${ex} ${ey}`} fill="none" stroke={color} strokeWidth="2" strokeOpacity="0.55" strokeDasharray="6 6" strokeDashoffset={-pulse * 40} />
                    <text x={(sx + ex) / 2} y={(sy + ey) / 2 - 8} textAnchor="middle" style={{ fontSize: 9, fill: color, fontFamily: "var(--font-mono)", opacity: 0.6 }}>{isFinite(sVal) ? sVal.toFixed(2) : "—"}</text>
                  </g>
                );
              };
              return <g key={`conn-${n.id}`}>{n.inputs.left && draw(n.inputs.left, "left")}{n.inputs.right && draw(n.inputs.right, "right")}</g>;
            })}

            {/* Active connection line */}
            {connecting && (() => {
              const fN = nodes.find(n => n.id === connecting.fromId); if (!fN) return null;
              let sx, sy;
              if (connecting.direction === "from-input") { sx = fN.x; sy = fN.y + (connecting.slot === "left" ? 22 : 44); }
              else { sx = fN.x + NW; sy = fN.y + nodeH(fN) / 2; }
              const color = connecting.direction === "from-input" ? (connecting.slot === "left" ? "#8B5CF6" : "#EC4899") : "#10B981";
              return <line x1={sx} y1={sy} x2={mousePos.x} y2={mousePos.y} stroke={color} strokeWidth="2.5" strokeDasharray="5 5" strokeOpacity="0.8" />;
            })()}

            {/* NODES */}
            {nodes.map(n => {
              const isOut = n.id === outputId;
              const nH = nodeH(n);
              const nVal = evalNode(n, nodes, varVal);
              const needsL = n.type === "eml" && !n.inputs?.left;
              const needsR = n.type === "eml" && !n.inputs?.right;
              const hasL = n.type === "eml" && n.inputs?.left;
              const hasR = n.type === "eml" && n.inputs?.right;

              return (
                <g key={n.id}>
                  {isOut && <rect x={n.x - 5} y={n.y - 5} width={NW + 10} height={nH + 10} rx="14" fill="none" stroke="#FDE68A" strokeWidth="2" strokeDasharray="6 4" strokeOpacity={0.4 + Math.sin(pulse * 3) * 0.3} />}

                  {/* Body */}
                  <rect x={n.x} y={n.y} width={NW} height={nH} rx="10"
                    fill={n.type === "eml" ? "#7C3AED" : n.type === "variable" ? "#0E7490" : "#1E293B"}
                    stroke={n.type === "eml" ? "#A78BFA" : n.type === "variable" ? "#22D3EE" : "#475569"} strokeWidth="1.5"
                    style={{ cursor: "grab" }} onMouseDown={(e) => startDrag(n.id, e)} onTouchStart={(e) => startDrag(n.id, e)} />

                  {/* Label */}
                  {n.type === "eml" && <>
                    <text x={n.x + NW / 2} y={n.y + 14} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 10, fontFamily: "var(--font-mono)", fill: "#E9D5FF", fontWeight: 600, pointerEvents: "none", letterSpacing: 0.5 }}>eml(x, y)</text>
                    <text x={n.x + NW / 2} y={n.y + nH - 12} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 11, fontFamily: "var(--font-mono)", fill: "#C4B5FD", pointerEvents: "none", fontWeight: 500 }}>= {isFinite(nVal) ? nVal.toFixed(4) : "—"}</text>
                  </>}
                  {n.type === "constant" && (
                    editingConst === n.id ? (
                      <foreignObject x={n.x + 20} y={n.y + 6} width={60} height={30}>
                        <input type="number" autoFocus value={editVal} onChange={(e) => setEditVal(e.target.value)}
                          onBlur={() => commitEdit(n.id)} onKeyDown={(e) => { if (e.key === "Enter") commitEdit(n.id); }}
                          style={{ width: 55, fontSize: 16, fontFamily: "var(--font-mono)", textAlign: "center", background: "transparent", border: "none", color: "#FDE68A", outline: "none", fontWeight: 700 }} />
                      </foreignObject>
                    ) : (
                      <text x={n.x + NW / 2} y={n.y + nH / 2} textAnchor="middle" dominantBaseline="middle"
                        style={{ fontSize: 18, fontFamily: "var(--font-mono)", fill: "#FDE68A", fontWeight: 700, pointerEvents: "none" }}>{n.value}</text>
                    )
                  )}
                  {n.type === "variable" && (
                    <text x={n.x + NW / 2} y={n.y + nH / 2} textAnchor="middle" dominantBaseline="middle"
                      style={{ fontSize: 16, fontFamily: "var(--font-mono)", fill: "#67E8F9", fontWeight: 700, pointerEvents: "none" }}>x = {varVal.toFixed(1)}</text>
                  )}

                  {/* INPUT PORTS */}
                  {n.type === "eml" && <>
                    {/* X port */}
                    <g style={{ cursor: "pointer" }} onMouseDown={(e) => hasL ? disconnectPort(n.id, "left", e) : handlePortMouseDown(n.id, "input", "left", e)} onTouchStart={(e) => hasL ? disconnectPort(n.id, "left", e) : handlePortMouseDown(n.id, "input", "left", e)}>
                      <circle cx={n.x} cy={n.y + 22} r={18} fill="transparent" style={{ pointerEvents: "all" }} />
                      <circle cx={n.x} cy={n.y + 22} r={connecting ? 9 + Math.sin(pulse * 5) * 1.5 : needsL ? 8 + Math.sin(pulse * 4) * 1.5 : 7}
                        fill={hasL ? "#8B5CF6" : "rgba(139,92,246,0.15)"} stroke="#8B5CF6" strokeWidth={needsL || connecting ? 2 : 1.5}
                        strokeOpacity={needsL ? 0.6 + Math.sin(pulse * 3) * 0.4 : 0.8} />
                      <text x={n.x} y={n.y + 23} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 9, fill: hasL ? "white" : "#C4B5FD", fontFamily: "var(--font-mono)", fontWeight: 700, pointerEvents: "none" }}>x</text>
                    </g>
                    {needsL && !connecting && <text x={n.x - 14} y={n.y + 23} textAnchor="end" dominantBaseline="middle" style={{ fontSize: 8, fill: "#A78BFA", fontFamily: "var(--font-mono)", opacity: 0.4 + Math.sin(pulse * 2) * 0.3 }}>click</text>}
                    {/* Y port */}
                    <g style={{ cursor: "pointer" }} onMouseDown={(e) => hasR ? disconnectPort(n.id, "right", e) : handlePortMouseDown(n.id, "input", "right", e)} onTouchStart={(e) => hasR ? disconnectPort(n.id, "right", e) : handlePortMouseDown(n.id, "input", "right", e)}>
                      <circle cx={n.x} cy={n.y + 44} r={18} fill="transparent" style={{ pointerEvents: "all" }} />
                      <circle cx={n.x} cy={n.y + 44} r={connecting ? 9 + Math.sin(pulse * 5 + 1) * 1.5 : needsR ? 8 + Math.sin(pulse * 4 + 1) * 1.5 : 7}
                        fill={hasR ? "#EC4899" : "rgba(236,72,153,0.15)"} stroke="#EC4899" strokeWidth={needsR || connecting ? 2 : 1.5}
                        strokeOpacity={needsR ? 0.6 + Math.sin(pulse * 3 + 1) * 0.4 : 0.8} />
                      <text x={n.x} y={n.y + 45} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 9, fill: hasR ? "white" : "#F9A8D4", fontFamily: "var(--font-mono)", fontWeight: 700, pointerEvents: "none" }}>y</text>
                    </g>
                    {needsR && !connecting && <text x={n.x - 14} y={n.y + 45} textAnchor="end" dominantBaseline="middle" style={{ fontSize: 8, fill: "#F472B6", fontFamily: "var(--font-mono)", opacity: 0.4 + Math.sin(pulse * 2 + 1) * 0.3 }}>click</text>}
                  </>}

                  {/* OUTPUT PORT */}
                  <g style={{ cursor: "pointer" }} onMouseDown={(e) => handlePortMouseDown(n.id, "output", null, e)} onTouchStart={(e) => handlePortMouseDown(n.id, "output", null, e)}>
                    <circle cx={n.x + NW} cy={n.y + nH / 2} r={18} fill="transparent" style={{ pointerEvents: "all" }} />
                    <circle cx={n.x + NW} cy={n.y + nH / 2} r={connecting?.direction === "from-input" ? 10 + Math.sin(pulse * 5) * 2 : 6}
                      fill={connecting?.direction === "from-input" ? "rgba(16,185,129,0.3)" : "#10B981"}
                      stroke="#34D399" strokeWidth={connecting?.direction === "from-input" ? 2 : 1.5}
                      strokeOpacity={connecting?.direction === "from-input" ? 0.6 + Math.sin(pulse * 4) * 0.4 : 0.8} />
                    <text x={n.x + NW} y={n.y + nH / 2 + 1} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 7, fill: "white", fontFamily: "var(--font-mono)", fontWeight: 700, pointerEvents: "none" }}>out</text>
                  </g>

                  {/* Actions: delete, dup, set output */}
                  <g style={{ cursor: "pointer" }} onClick={() => removeNode(n.id)}><circle cx={n.x + NW - 8} cy={n.y + 8} r="7" fill="rgba(0,0,0,0.2)" /><text x={n.x + NW - 8} y={n.y + 9} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 9, fill: "rgba(255,255,255,0.5)", pointerEvents: "none" }}>✕</text></g>
                  <g style={{ cursor: "pointer" }} onClick={() => dupNode(n.id)}><circle cx={n.x + NW - 24} cy={n.y + 8} r="7" fill="rgba(0,0,0,0.15)" /><text x={n.x + NW - 24} y={n.y + 9} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 8, fill: "rgba(255,255,255,0.4)", pointerEvents: "none" }}>⊕</text></g>
                  {!isOut && n.type === "eml" && <g style={{ cursor: "pointer" }} onClick={() => setOutputId(n.id)}><rect x={n.x + 4} y={n.y + 2} width={24} height={12} rx="3" fill="rgba(253,230,138,0.15)" stroke="#FDE68A" strokeWidth="0.5" /><text x={n.x + 16} y={n.y + 9} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 7, fill: "#FDE68A", fontFamily: "var(--font-mono)", fontWeight: 600, pointerEvents: "none" }}>OUT</text></g>}
                  {/* Constant +/- and double-click to edit */}
                  {n.type === "constant" && editingConst !== n.id && <>
                    <g style={{ cursor: "pointer" }} onClick={() => changeConst(n.id, -0.5)}><circle cx={n.x + 12} cy={n.y + nH / 2} r="10" fill="rgba(255,255,255,0.04)" /><text x={n.x + 12} y={n.y + nH / 2 + 1} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 16, fill: "#64748B", pointerEvents: "none", fontWeight: 300 }}>−</text></g>
                    <g style={{ cursor: "pointer" }} onClick={() => changeConst(n.id, 0.5)}><circle cx={n.x + NW - 12} cy={n.y + nH / 2} r="10" fill="rgba(255,255,255,0.04)" /><text x={n.x + NW - 12} y={n.y + nH / 2 + 1} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 16, fill: "#64748B", pointerEvents: "none", fontWeight: 300 }}>+</text></g>
                    {/* Double click to edit */}
                    <rect x={n.x + 25} y={n.y + 5} width={50} height={nH - 10} rx="4" fill="transparent" style={{ cursor: "text" }} onDoubleClick={(e) => { e.stopPropagation(); setEditingConst(n.id); setEditVal(String(n.value)); }} />
                  </>}
                </g>
              );
            })}

            {nodes.length === 0 && <text x="290" y="210" textAnchor="middle" style={{ fontSize: 13, fill: "var(--color-text-secondary,#bbb)", fontFamily: "var(--font-sans)" }}>Tap + buttons below to add nodes · tap ports to connect</text>}
          </svg>
          {/* Zoom controls */}
          <div style={{ position: "absolute", bottom: 8, left: 8, display: "flex", gap: 3, zIndex: 10 }}>
            <button onClick={() => setZoom(z => Math.min(3, +(z + 0.5).toFixed(1)))} style={{ width: 26, height: 26, borderRadius: 6, border: "1px solid rgba(124,58,237,0.25)", background: "rgba(255,255,255,0.9)", cursor: "pointer", fontSize: 14, fontWeight: 700, color: "#7C3AED", lineHeight: 1 }}>+</button>
            {zoom !== 1 && <button onClick={() => setZoom(1)} style={{ height: 26, padding: "0 7px", borderRadius: 6, border: "1px solid rgba(124,58,237,0.25)", background: "rgba(255,255,255,0.9)", cursor: "pointer", fontSize: 9, color: "#7C3AED", fontWeight: 600 }}>fit</button>}
            <button onClick={() => setZoom(z => Math.max(0.5, +(z - 0.5).toFixed(1)))} style={{ width: 26, height: 26, borderRadius: 6, border: "1px solid rgba(124,58,237,0.25)", background: "rgba(255,255,255,0.9)", cursor: "pointer", fontSize: 14, fontWeight: 700, color: "#7C3AED", lineHeight: 1 }}>−</button>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {/* VIZ MODE TABS */}
          <div style={{ display: "flex", gap: 2, borderRadius: 8, overflow: "hidden", border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.08))" }}>
            {[
              { id: "rings", label: "Rings" },
              { id: "curve", label: "f(x)", disabled: !hasVar },
              { id: "spiral", label: "Spiral" },
            ].map(m => (
              <button key={m.id} disabled={m.disabled} onClick={() => !m.disabled && setVizMode(m.id)} style={{
                flex: 1, padding: "5px 0", fontSize: 10, fontWeight: vizMode === m.id ? 600 : 400, border: "none",
                background: vizMode === m.id ? "#7C3AED" : "var(--color-background-secondary, #f5f3ff)",
                color: vizMode === m.id ? "white" : m.disabled ? "var(--color-text-secondary, #ccc)" : "var(--color-text-secondary, #888)",
                cursor: m.disabled ? "not-allowed" : "pointer", fontFamily: "var(--font-mono)",
              }}>{m.label}</button>
            ))}
          </div>

          {/* VISUALIZATION */}
          <div style={{ background: "#06020F", borderRadius: 12, overflow: "hidden", aspectRatio: "1", border: "1px solid rgba(139,92,246,0.15)" }}>
            {!hasOutput ? (
              <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 6 }}>
                <div style={{ fontSize: 24, opacity: 0.12 }}>◇</div>
                <div style={{ fontSize: 10, color: "rgba(167,139,250,0.3)", textAlign: "center", padding: "0 12px" }}>Connect nodes to see the pattern</div>
              </div>
            ) : vizMode === "curve" && hasVar ? (
              <CurveVis curveData={curveData} depth={depth} />
            ) : vizMode === "spiral" ? (
              <SpiralVis value={evalVal} depth={depth} />
            ) : (
              <RingsVis value={evalVal} depth={depth} />
            )}
          </div>

          {/* VARIABLE SLIDER */}
          {hasVar && (
            <div style={{ background: "var(--color-background-secondary, #faf5ff)", borderRadius: 8, padding: "8px 10px", border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <span style={{ fontSize: 9, color: "#0E7490", fontWeight: 500, textTransform: "uppercase", letterSpacing: 1 }}>Variable x</span>
                <span style={{ fontSize: 13, fontFamily: "var(--font-mono)", color: "#0E7490", fontWeight: 600 }}>{varVal.toFixed(2)}</span>
              </div>
              <input type="range" min="-5" max="5" step="0.1" value={varVal} onChange={(e) => setVarVal(parseFloat(e.target.value))}
                style={{ width: "100%", accentColor: "#0E7490" }} />
            </div>
          )}

          {/* RESULT */}
          <div style={{ background: "var(--color-background-secondary, #faf5ff)", borderRadius: 8, padding: "10px 12px", border: `0.5px solid ${challengeHit ? "rgba(16,185,129,0.4)" : "var(--color-border-tertiary, rgba(0,0,0,0.06))"}` }}>
            <div style={{ fontSize: 9, color: "#7C3AED", fontWeight: 500, textTransform: "uppercase", letterSpacing: 1, marginBottom: 3 }}>Result</div>
            <div style={{ fontSize: 22, fontWeight: 600, fontFamily: "var(--font-mono)", color: challengeHit ? "#059669" : "var(--color-text-primary, #1a1a2e)" }}>
              {hasOutput ? (isFinite(evalVal) ? evalVal.toFixed(6) : "overflow") : "—"}
            </div>
            {identity && <div style={{ fontSize: 13, color: "#7C3AED", fontWeight: 600, marginTop: 1 }}>= {identity}</div>}
            {challengeHit && <div style={{ fontSize: 12, color: "#059669", fontWeight: 600, marginTop: 2 }}>{"★".repeat(challengeStars)}{"☆".repeat(3 - challengeStars)} {challengeStars === 3 ? "Perfect!" : challengeStars === 2 ? "Great!" : "Solved!"}</div>}
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)", marginTop: 4, fontFamily: "var(--font-mono)" }}>depth {depth} · {nodes.length} nodes</div>
          </div>

          {/* EXPRESSION */}
          {hasOutput && expr && (
            <div style={{ background: "var(--color-background-secondary, #faf5ff)", borderRadius: 8, padding: "8px 10px", border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))" }}>
              <div style={{ fontSize: 9, color: "#7C3AED", fontWeight: 500, textTransform: "uppercase", letterSpacing: 1, marginBottom: 3 }}>Expression</div>
              <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #444)", wordBreak: "break-all", lineHeight: 1.5 }}>{expr}</div>
            </div>
          )}

          {/* CHALLENGE */}
          {activeChallenge && (
            <div style={{ background: challengeHit ? "rgba(16,185,129,0.06)" : "rgba(245,158,11,0.06)", borderRadius: 8, padding: "8px 10px", border: `1px solid ${challengeHit ? "rgba(16,185,129,0.2)" : "rgba(245,158,11,0.2)"}` }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: challengeHit ? "#059669" : "#D97706", textTransform: "uppercase", letterSpacing: 1, marginBottom: 3 }}>
                {challengeHit ? "✓ Challenge complete!" : "Challenge"}
              </div>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-primary, #333)" }}>{activeChallenge.name}</div>
              <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #666)", marginTop: 2 }}>
                Target: {activeChallenge.target.toFixed(6)}
              </div>
              {!challengeHit && <div style={{ fontSize: 10, color: "#D97706", marginTop: 4, fontStyle: "italic" }}>Hint: {activeChallenge.hint}</div>}
              {challengeHit && <div style={{ fontSize: 10, color: "#059669", marginTop: 4 }}>
                ★★★ = {activeChallenge.stars3} nodes · ★★☆ = {activeChallenge.stars2} · ★☆☆ = {activeChallenge.stars1}
              </div>}
              <button onClick={() => setChallenge(null)} style={{ marginTop: 6, padding: "4px 10px", borderRadius: 6, border: "1px solid var(--color-border-tertiary, #ddd)", background: "var(--color-background-primary, white)", color: "var(--color-text-secondary, #888)", fontSize: 9, cursor: "pointer" }}>Exit challenge</button>
            </div>
          )}

          {/* AUDIO TOGGLE */}
          <button onClick={() => setAudioOn(a => !a)} style={{
            padding: "6px 0", borderRadius: 8, border: `1px solid ${audioOn ? "rgba(124,58,237,0.3)" : "var(--color-border-tertiary, #ddd)"}`,
            background: audioOn ? "rgba(124,58,237,0.08)" : "var(--color-background-primary, white)",
            color: audioOn ? "#7C3AED" : "var(--color-text-secondary, #999)", fontSize: 11, fontWeight: 500, cursor: "pointer",
          }}>{audioOn ? "♪ Sound on" : "♪ Sound off"}</button>

          {/* EVAL CHAIN */}
          {hasOutput && chain.length > 0 && (
            <div style={{ background: "var(--color-background-secondary, #faf5ff)", borderRadius: 8, padding: "8px 10px", border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))", maxHeight: 100, overflowY: "auto" }}>
              <div style={{ fontSize: 9, color: "#7C3AED", fontWeight: 500, textTransform: "uppercase", letterSpacing: 1, marginBottom: 3 }}>Chain</div>
              {chain.map((s, i) => (
                <div key={i} style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #666)", lineHeight: 1.7, borderBottom: i < chain.length - 1 ? "1px solid var(--color-border-tertiary, rgba(0,0,0,0.04))" : "none" }}>
                  <span style={{ color: "#A78BFA" }}>{s.eq}</span> <span style={{ color: "#7C3AED", fontWeight: 600 }}>= {isFinite(s.val) ? s.val.toFixed(4) : "—"}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* TOOLBAR */}
      <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap", alignItems: "center" }}>
        <button onClick={() => addEml()} style={{ padding: "8px 14px", borderRadius: 8, border: "none", background: "#7C3AED", color: "white", fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "var(--font-mono)", boxShadow: "0 2px 6px rgba(124,58,237,0.25)" }}>+ eml(x,y)</button>
        {[1, 2, 0.5, -1, 3].map(v => (
          <button key={v} onClick={() => addConst(v)} style={{ padding: "8px 12px", borderRadius: 8, border: "1.5px solid var(--color-border-tertiary, #ddd)", background: "var(--color-background-primary, white)", color: "var(--color-text-primary, #333)", fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "var(--font-mono)" }}>+ {v}</button>
        ))}
        <button onClick={addVariable} disabled={hasVar} style={{ padding: "8px 14px", borderRadius: 8, border: "none", background: hasVar ? "var(--color-background-secondary, #e5e7eb)" : "#0E7490", color: hasVar ? "var(--color-text-secondary, #999)" : "white", fontSize: 12, fontWeight: 600, cursor: hasVar ? "not-allowed" : "pointer", fontFamily: "var(--font-mono)" }}>+ x</button>

        <div style={{ width: 1, height: 24, background: "var(--color-border-tertiary, #ddd)", margin: "0 4px" }} />

        <button onClick={doAutoArrange} style={{ padding: "8px 12px", borderRadius: 8, border: "1.5px solid var(--color-border-tertiary, #ddd)", background: "var(--color-background-primary, white)", color: "var(--color-text-secondary, #666)", fontSize: 11, cursor: "pointer" }}>Arrange</button>

        <div style={{ flex: 1 }} />

        {PRESETS.map(p => (
          <button key={p.name} onClick={() => loadPreset(p)} style={{ padding: "6px 10px", borderRadius: 6, border: "1px solid var(--color-border-tertiary, #ddd)", background: "var(--color-background-primary, white)", color: "var(--color-text-secondary, #666)", fontSize: 9, cursor: "pointer", fontFamily: "var(--font-sans)" }}>{p.name}</button>
        ))}
      </div>

      {/* CHALLENGES */}
      <div style={{ marginTop: 10 }}>
        <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)", marginBottom: 6, fontWeight: 500, textTransform: "uppercase", letterSpacing: 1 }}>
          Challenges — build the target with fewest nodes
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {CHALLENGES.map((ch, i) => (
            <button key={ch.name} onClick={() => { setChallenge(i); loadPreset({ name: "Blank", nodes: [], output: null }); }}
              style={{
                padding: "6px 12px", borderRadius: 8, fontSize: 11, fontWeight: 500, cursor: "pointer",
                fontFamily: "var(--font-mono)",
                border: challenge === i ? "2px solid #F59E0B" : "1.5px solid var(--color-border-tertiary, #ddd)",
                background: challenge === i ? "rgba(245,158,11,0.08)" : "var(--color-background-primary, white)",
                color: challenge === i ? "#D97706" : "var(--color-text-secondary, #666)",
              }}>
              {ch.name} <span style={{ opacity: 0.5, fontSize: 9 }}>({ch.target.toFixed(2)})</span>
            </button>
          ))}
        </div>
      </div>

      {/* LEGEND */}
      <div style={{ display: "flex", gap: 16, justifyContent: "center", marginTop: 12, fontSize: 10, color: "var(--color-text-secondary, #888)", flexWrap: "wrap" }}>
        <span><span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: "#8B5CF6", marginRight: 3, verticalAlign: "middle" }} />x input</span>
        <span><span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: "#EC4899", marginRight: 3, verticalAlign: "middle" }} />y input</span>
        <span><span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: "#10B981", marginRight: 3, verticalAlign: "middle" }} />output</span>
        <span><span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: "#0E7490", marginRight: 3, verticalAlign: "middle" }} />variable</span>
        <span>⊕ duplicate</span>
        <span>dbl-click = edit/add</span>
      </div>

      {/* Footer */}
      <div style={{ textAlign: "center", marginTop: 14, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#06B6D4", textDecoration: "none", fontWeight: 500 }}>monogate.dev</a>{" · "}<a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none" }}>arXiv:2603.21852</a>
      </div>
      <style>{`
        @media(max-width:600px){
          .eml-main-grid{grid-template-columns:1fr!important;}
          .eml-canvas-wrap{aspect-ratio:4/3!important; min-height:260px;}
        }
      `}</style>
    </div>
  );
}
