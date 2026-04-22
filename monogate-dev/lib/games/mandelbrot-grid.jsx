// Mandelbrot Comparison Grid — all 16 F16 operators side by side.
//
// For each F16 operator, iterate z_{n+1} = op(z_n, c) from z_0 = 0 on the
// complex plane and render the Mandelbrot-analogue set. Stats from the
// Session C geometry sweep (300×300, max_iter=80) populate an area and box-
// counting-dimension readout under each tile.
//
// Completeness coloring (structural rule T26–T28):
//   green  = exp(+z) → complete (EML, EAL, EXL, EDL, EMN, EAN, EXN, EDN)
//   amber  = exp(-z) → approx/incomplete (DEML, DEAL, DEXL, DEDL, DEMN, …)
//
// Sort: name (default) / area (desc) / dimension (desc).

import { useState, useRef, useEffect, useMemo } from "react";

function cExp(r, i) { const e = Math.exp(r); return [e * Math.cos(i), e * Math.sin(i)]; }
function cLn(r, i) {
  const mag = Math.sqrt(r * r + i * i);
  if (mag < 1e-300) return [-700, 0];
  return [Math.log(mag), Math.atan2(i, r)];
}
function cLnNeg(r, i) { // ln(-c) = ln(c) + iπ (principal)
  const [lr, li] = cLn(-r, -i);
  return [lr, li];
}

// 16 F16 operators: 8 L-variants (ln(+c)) and 8 N-variants (ln(-c)).
function buildOp(expSign, arith, logFn) {
  return (zr, zi, cr, ci) => {
    const [er, ei] = cExp(expSign * zr, expSign * zi);
    const [lr, li] = logFn(cr, ci);
    switch (arith) {
      case "sub": return [er - lr, ei - li];
      case "add": return [er + lr, ei + li];
      case "mul": return [er * lr - ei * li, er * li + ei * lr];
      case "div": {
        const d = lr * lr + li * li;
        if (d < 1e-30) return [1e10, 0];
        return [(er * lr + ei * li) / d, (ei * lr - er * li) / d];
      }
    }
  };
}

const OPS = [
  { key: "EML",  formula: "exp(z) − ln(c)",   expSign: 1,  arith: "sub", log: cLn,    family: "complete",   area: 52.24, dim: 1.9568 },
  { key: "EAL",  formula: "exp(z) + ln(c)",   expSign: 1,  arith: "add", log: cLn,    family: "complete",   area: 24.27, dim: 1.8963 },
  { key: "EXL",  formula: "exp(z) · ln(c)",   expSign: 1,  arith: "mul", log: cLn,    family: "complete",   area: 35.90, dim: 1.9237 },
  { key: "EDL",  formula: "exp(z) / ln(c)",   expSign: 1,  arith: "div", log: cLn,    family: "complete",   area: 48.41, dim: 1.9384 },
  { key: "EMN",  formula: "ln(−c) − exp(z)",  expSign: 1,  arith: "sub", log: cLnNeg, family: "complete",   area: 52.24, dim: 1.9568 },
  { key: "EAN",  formula: "exp(z) + ln(−c)",  expSign: 1,  arith: "add", log: cLnNeg, family: "complete",   area: 24.27, dim: 1.8963 },
  { key: "EXN",  formula: "exp(z) · ln(−c)",  expSign: 1,  arith: "mul", log: cLnNeg, family: "complete",   area: 35.90, dim: 1.9237 },
  { key: "EDN",  formula: "exp(z) / ln(−c)",  expSign: 1,  arith: "div", log: cLnNeg, family: "complete",   area: 48.41, dim: 1.9384 },
  { key: "DEML", formula: "exp(−z) − ln(c)",  expSign: -1, arith: "sub", log: cLn,    family: "approx",     area: 32.13, dim: 1.8536 },
  { key: "DEAL", formula: "exp(−z) + ln(c)",  expSign: -1, arith: "add", log: cLn,    family: "approx",     area: 52.64, dim: 1.9590 },
  { key: "DEXL", formula: "exp(−z) · ln(c)",  expSign: -1, arith: "mul", log: cLn,    family: "approx",     area: 44.49, dim: 1.9196 },
  { key: "DEDL", formula: "exp(−z) / ln(c)",  expSign: -1, arith: "div", log: cLn,    family: "approx",     area: 53.62, dim: 1.9638 },
  { key: "DEMN", formula: "exp(−z) − ln(−c)", expSign: -1, arith: "sub", log: cLnNeg, family: "approx",     area: 32.13, dim: 1.8536 },
  { key: "DEAN", formula: "exp(−z) + ln(−c)", expSign: -1, arith: "add", log: cLnNeg, family: "approx",     area: 52.64, dim: 1.9590 },
  { key: "DEXN", formula: "exp(−z) · ln(−c)", expSign: -1, arith: "mul", log: cLnNeg, family: "approx",     area: 44.49, dim: 1.9196 },
  { key: "DEDN", formula: "exp(−z) / ln(−c)", expSign: -1, arith: "div", log: cLnNeg, family: "approx",     area: 53.62, dim: 1.9638 },
];

// Cache compiled op functions
for (const o of OPS) o.fn = buildOp(o.expSign, o.arith, o.log);

const FAMILY_COLORS = {
  complete: "#5ec47a",
  approx:   "#fccb52",
};

const VIEW = { xMin: -4, xMax: 5, yMin: -3, yMax: 3 };
const TILE_W = 160;
const TILE_H = Math.round(TILE_W * (VIEW.yMax - VIEW.yMin) / (VIEW.xMax - VIEW.xMin));
const MAX_ITER = 40;
const ESCAPE_R = 8;

function iterate(fn, cr, ci, maxIter) {
  let zr = 0, zi = 0;
  for (let n = 0; n < maxIter; n++) {
    [zr, zi] = fn(zr, zi, cr, ci);
    if (!Number.isFinite(zr) || !Number.isFinite(zi)) return n;
    if (zr * zr + zi * zi > ESCAPE_R * ESCAPE_R) return n;
  }
  return -1;
}

function renderTile(fn, familyColor) {
  const img = new Uint8ClampedArray(TILE_W * TILE_H * 4);
  const [r0, g0, b0] = hexToRgb(familyColor);
  for (let py = 0; py < TILE_H; py++) {
    const ci = VIEW.yMin + (py / TILE_H) * (VIEW.yMax - VIEW.yMin);
    for (let px = 0; px < TILE_W; px++) {
      const cr = VIEW.xMin + (px / TILE_W) * (VIEW.xMax - VIEW.xMin);
      const it = iterate(fn, cr, ci, MAX_ITER);
      const idx = (py * TILE_W + px) * 4;
      if (it < 0) {
        img[idx] = 6; img[idx + 1] = 6; img[idx + 2] = 12;
      } else {
        const t = Math.min(it / MAX_ITER, 1);
        img[idx]     = Math.round(r0 * (0.2 + 0.8 * t));
        img[idx + 1] = Math.round(g0 * (0.2 + 0.8 * t));
        img[idx + 2] = Math.round(b0 * (0.2 + 0.8 * t));
      }
      img[idx + 3] = 255;
    }
  }
  return img;
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

export default function MandelbrotGrid() {
  const [tiles, setTiles] = useState({});
  const [sortBy, setSortBy] = useState("name");
  const [filter, setFilter] = useState("all");
  const [progress, setProgress] = useState({ done: 0, total: OPS.length });
  const [hoveredOp, setHoveredOp] = useState(null);

  useEffect(() => {
    let cancelled = false;
    let i = 0;
    function next() {
      if (cancelled || i >= OPS.length) return;
      const op = OPS[i++];
      const img = renderTile(op.fn, FAMILY_COLORS[op.family]);
      if (cancelled) return;
      setTiles((t) => ({ ...t, [op.key]: img }));
      setProgress({ done: i, total: OPS.length });
      setTimeout(next, 0);
    }
    next();
    return () => { cancelled = true; };
  }, []);

  const sortedFilteredOps = useMemo(() => {
    const filtered = filter === "all"
      ? OPS
      : OPS.filter((o) => o.family === filter);
    const sorted = [...filtered];
    if (sortBy === "area") sorted.sort((a, b) => b.area - a.area);
    else if (sortBy === "dim") sorted.sort((a, b) => b.dim - a.dim);
    // else: name order (array order)
    return sorted;
  }, [sortBy, filter]);

  const totalArea = OPS.reduce((a, o) => a + o.area, 0);
  const avgDim = OPS.reduce((a, o) => a + o.dim, 0) / OPS.length;
  const completeCount = OPS.filter((o) => o.family === "complete").length;

  return (
    <div style={S.root}>
      <header style={S.header}>
        <span style={S.brand}>monogate</span>
        <span style={S.subBrand}>mandelbrot grid · 16 F16 operators</span>
        <span style={S.formula}>
          {hoveredOp
            ? `z → ${OPS.find((o) => o.key === hoveredOp)?.formula}`
            : "hover a tile for details"}
        </span>
      </header>

      <div style={S.statBar}>
        <Stat label="operators" value="16" />
        <Stat label="complete family" value={String(completeCount)} color={FAMILY_COLORS.complete} />
        <Stat label="approx family" value={String(OPS.length - completeCount)} color={FAMILY_COLORS.approx} />
        <Stat label="total area" value={totalArea.toFixed(1)} />
        <Stat label="avg box-dim" value={avgDim.toFixed(3)} />
        <Stat label="rendered" value={`${progress.done}/${progress.total}`} />
      </div>

      <div style={S.controls}>
        <span style={S.label}>sort</span>
        {[["name","name"],["area","area ↓"],["dim","box-dim ↓"]].map(([k, l]) => (
          <button
            key={k}
            onClick={() => setSortBy(k)}
            style={{
              ...S.btn,
              background: sortBy === k ? "rgba(255,255,255,0.12)" : "transparent",
              color: sortBy === k ? "#e8e8f0" : "rgba(255,255,255,0.5)",
            }}
          >{l}</button>
        ))}
        <div style={S.divider} />
        <span style={S.label}>family</span>
        {[["all","all"],["complete","complete"],["approx","approx"]].map(([k, l]) => (
          <button
            key={k}
            onClick={() => setFilter(k)}
            style={{
              ...S.btn,
              background: filter === k ? "rgba(255,255,255,0.12)" : "transparent",
              color: filter === k ? "#e8e8f0" : "rgba(255,255,255,0.5)",
              borderColor: filter === k && k !== "all" ? FAMILY_COLORS[k] + "aa" : "rgba(255,255,255,0.1)",
            }}
          >{l}</button>
        ))}
      </div>

      <div style={S.grid}>
        {sortedFilteredOps.map((op) => (
          <Tile
            key={op.key}
            op={op}
            img={tiles[op.key]}
            hovered={hoveredOp === op.key}
            onHover={() => setHoveredOp(op.key)}
            onLeave={() => setHoveredOp(null)}
          />
        ))}
      </div>

      <div style={S.help}>
        Each tile iterates z<sub>n+1</sub> = op(z<sub>n</sub>, c) from
        z<sub>0</sub> = 0, coloring by escape speed over
        c ∈ [−4, 5] × [−3, 3]i. Area and box-counting dimension come from
        Session C (300×300, max-iter 80). Green tiles are the
        "complete" family (the structural rule T26–T28: exp(+z) always gives
        exact completeness). Amber tiles are the "approx" family (exp(−z);
        approximately complete but not exactly). The N-variants replace
        ln(+c) with ln(−c) = ln(c) + iπ; on the complex viewport this shifts
        the image but preserves geometry, so the paired areas and dimensions
        match exactly.
      </div>
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div style={S.statCell}>
      <div style={{ fontSize: 9, color: "rgba(255,255,255,0.4)", letterSpacing: "0.05em", textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 600, color: color || "#e8e8f0" }}>{value}</div>
    </div>
  );
}

function Tile({ op, img, hovered, onHover, onLeave }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !img) return;
    const ctx = canvas.getContext("2d");
    ctx.putImageData(new ImageData(img, TILE_W, TILE_H), 0, 0);
  }, [img]);

  const familyColor = FAMILY_COLORS[op.family];
  return (
    <div
      style={{
        ...S.tileWrap,
        borderColor: hovered ? familyColor : "rgba(255,255,255,0.08)",
        transform: hovered ? "translateY(-2px)" : "none",
        boxShadow: hovered ? `0 6px 18px ${familyColor}33` : "none",
      }}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
    >
      <canvas
        ref={ref}
        width={TILE_W}
        height={TILE_H}
        style={{
          display: "block", width: "100%", height: "auto",
          background: "#0a0a10",
        }}
      />
      <div style={S.tileFoot}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{
            display: "inline-block", width: 7, height: 7,
            borderRadius: "50%", background: familyColor,
          }} />
          <span style={{ color: "#e8e8f0", fontWeight: 600 }}>{op.key}</span>
        </div>
        <div style={{ fontSize: 9, color: "rgba(255,255,255,0.5)", marginTop: 2 }}>
          area {op.area.toFixed(1)} · dim {op.dim.toFixed(3)}
        </div>
      </div>
    </div>
  );
}

const FONT = "'IBM Plex Mono', 'SF Mono', 'Fira Code', monospace";
const S = {
  root: {
    background: "#08080c", color: "#e8e8f0", fontFamily: FONT,
    minHeight: "100vh", padding: "20px 24px 80px",
  },
  header: {
    display: "flex", gap: 16, alignItems: "baseline", flexWrap: "wrap",
    marginBottom: 10, paddingBottom: 10,
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  brand: {
    fontSize: 13, fontWeight: 600, letterSpacing: "0.15em",
    textTransform: "uppercase", color: "#4facfe",
  },
  subBrand: { fontSize: 13, color: "rgba(255,255,255,0.3)" },
  formula: { fontSize: 11, color: "rgba(255,255,255,0.4)", marginLeft: "auto" },

  statBar: {
    display: "flex", gap: 18, flexWrap: "wrap",
    padding: "12px 0", margin: "0 0 14px",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  statCell: { display: "flex", flexDirection: "column", minWidth: 100 },

  controls: {
    display: "flex", gap: 6, alignItems: "center",
    flexWrap: "wrap", marginBottom: 14,
  },
  label: { fontSize: 10, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.08em" },
  btn: {
    borderRadius: 4, padding: "4px 10px", fontSize: 11, fontFamily: "inherit",
    cursor: "pointer", border: "1px solid rgba(255,255,255,0.1)",
    background: "transparent", color: "rgba(255,255,255,0.5)",
  },
  divider: { width: 1, height: 20, background: "rgba(255,255,255,0.08)", margin: "0 6px" },

  grid: {
    display: "grid",
    gridTemplateColumns: `repeat(auto-fill, minmax(${TILE_W}px, 1fr))`,
    gap: 10,
  },
  tileWrap: {
    border: "1px solid", borderRadius: 5, overflow: "hidden",
    background: "#0a0a12", transition: "all 0.2s", cursor: "pointer",
  },
  tileFoot: {
    padding: "6px 8px 8px",
    fontSize: 11,
    borderTop: "1px solid rgba(255,255,255,0.06)",
  },

  help: {
    maxWidth: 820, margin: "28px auto 0",
    lineHeight: 1.7, fontSize: 12,
    color: "rgba(255,255,255,0.55)", fontFamily: "system-ui, sans-serif",
  },
};
