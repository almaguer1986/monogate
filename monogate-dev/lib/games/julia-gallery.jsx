// Julia Set Gallery — 8 F16 operators × 5 parameter values = 40 tiles.
//
// Highlighted exceptional cases (from the Session D exhaustive render):
//   EDL, DEDL at c = 0       → full-fill (Fatou = C)
//   EXL, DEXL at c = 1       → full-fill (Fatou = C)
//   DEAL at c = -0.5 + 0.5i  → dust (area ≈ 0.01, 0% connected)
//   EAL at c = 2 + i         → empty (full escape)
//
// Tiles render at 90×90 on a worker-free batched loop; click a tile to open
// it full-size at 240×240 with 80-iter smooth coloring.

import { useState, useRef, useEffect } from "react";

// ─── Ops ─────────────────────────────────────────────────────────────────────

function cExp(r, i) { const e = Math.exp(r); return [e * Math.cos(i), e * Math.sin(i)]; }
function cLn(r, i) {
  const mag = Math.sqrt(r * r + i * i);
  if (mag < 1e-300) return [-700, 0];
  return [Math.log(mag), Math.atan2(i, r)];
}

const OP_FNS = {
  EML:  (zr, zi, cr, ci) => { const [er, ei] = cExp(zr, zi); const [lr, li] = cLn(cr, ci); return [er - lr, ei - li]; },
  DEML: (zr, zi, cr, ci) => { const [er, ei] = cExp(-zr, -zi); const [lr, li] = cLn(cr, ci); return [er - lr, ei - li]; },
  EXL:  (zr, zi, cr, ci) => { const [er, ei] = cExp(zr, zi); const [lr, li] = cLn(cr, ci); return [er * lr - ei * li, er * li + ei * lr]; },
  DEXL: (zr, zi, cr, ci) => { const [er, ei] = cExp(-zr, -zi); const [lr, li] = cLn(cr, ci); return [er * lr - ei * li, er * li + ei * lr]; },
  EDL:  (zr, zi, cr, ci) => { const [er, ei] = cExp(zr, zi); const [lr, li] = cLn(cr, ci); const d = lr * lr + li * li; if (d < 1e-30) return [1e10, 0]; return [(er * lr + ei * li) / d, (ei * lr - er * li) / d]; },
  DEDL: (zr, zi, cr, ci) => { const [er, ei] = cExp(-zr, -zi); const [lr, li] = cLn(cr, ci); const d = lr * lr + li * li; if (d < 1e-30) return [1e10, 0]; return [(er * lr + ei * li) / d, (ei * lr - er * li) / d]; },
  EAL:  (zr, zi, cr, ci) => { const [er, ei] = cExp(zr, zi); const [lr, li] = cLn(cr, ci); return [er + lr, ei + li]; },
  DEAL: (zr, zi, cr, ci) => { const [er, ei] = cExp(-zr, -zi); const [lr, li] = cLn(cr, ci); return [er + lr, ei + li]; },
};

const OPS = ["EML", "DEML", "EAL", "DEAL", "EXL", "DEXL", "EDL", "DEDL"];
const OP_COLORS = {
  EML:  "#4facfe", DEML: "#f5576c",
  EAL:  "#a18cd1", DEAL: "#c4a7f5",
  EXL:  "#0fd38d", DEXL: "#7af0c8",
  EDL:  "#fccb52", DEDL: "#e8a020",
};

const C_VALUES = [
  { name: "0",           c: [0.0, 0.0] },
  { name: "1",           c: [1.0, 0.0] },
  { name: "−0.5 + 0.5i", c: [-0.5, 0.5] },
  { name: "2 + i",       c: [2.0, 1.0] },
  { name: "i",           c: [0.0, 1.0] },
];

// Keys for special-case highlighting: `${op}|${cIdx}`
const FULL_FILL = new Set(["EDL|0", "DEDL|0", "EXL|1", "DEXL|1"]);
const DUST = new Set(["DEAL|2"]);
const EMPTY = new Set(["EAL|3"]);

const TILE_SIZE = 90;
const TILE_ITER = 50;
const FULL_SIZE = 240;
const FULL_ITER = 80;
const VIEW = { xMin: -3, xMax: 3, yMin: -3, yMax: 3 };
const ESCAPE_R = 8;

function iterate(opFn, zr0, zi0, cr, ci, maxIter) {
  let zr = zr0, zi = zi0;
  for (let n = 0; n < maxIter; n++) {
    [zr, zi] = opFn(zr, zi, cr, ci);
    if (!Number.isFinite(zr) || !Number.isFinite(zi)) return n;
    if (zr * zr + zi * zi > ESCAPE_R * ESCAPE_R) return n;
  }
  return -1;
}

function renderJulia(opKey, cr, ci, size, maxIter) {
  const fn = OP_FNS[opKey];
  const img = new Uint8ClampedArray(size * size * 4);
  const color = hexToRgb(OP_COLORS[opKey]);
  for (let py = 0; py < size; py++) {
    const zi = VIEW.yMin + (py / size) * (VIEW.yMax - VIEW.yMin);
    for (let px = 0; px < size; px++) {
      const zr = VIEW.xMin + (px / size) * (VIEW.xMax - VIEW.xMin);
      const it = iterate(fn, zr, zi, cr, ci, maxIter);
      const idx = (py * size + px) * 4;
      if (it < 0) {
        img[idx] = 10; img[idx+1] = 8; img[idx+2] = 20;
      } else {
        const t = Math.min(it / maxIter, 1);
        img[idx]     = Math.round(color[0] * (0.15 + 0.85 * t));
        img[idx + 1] = Math.round(color[1] * (0.15 + 0.85 * t));
        img[idx + 2] = Math.round(color[2] * (0.15 + 0.85 * t));
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

export default function JuliaGallery() {
  const [tiles, setTiles] = useState({});
  const [progress, setProgress] = useState({ done: 0, total: OPS.length * C_VALUES.length });
  const [expanded, setExpanded] = useState(null); // { op, cIdx }
  const expandedCanvasRef = useRef(null);

  // Batched render on mount: render tiles one by one with a short yield.
  useEffect(() => {
    let cancelled = false;
    const queue = [];
    for (const op of OPS) {
      for (let cIdx = 0; cIdx < C_VALUES.length; cIdx++) {
        queue.push({ op, cIdx });
      }
    }
    let i = 0;
    function next() {
      if (cancelled || i >= queue.length) return;
      const { op, cIdx } = queue[i++];
      const [cr, ci] = C_VALUES[cIdx].c;
      const key = `${op}|${cIdx}`;
      const img = renderJulia(op, cr, ci, TILE_SIZE, TILE_ITER);
      if (cancelled) return;
      setTiles((t) => ({ ...t, [key]: img }));
      setProgress({ done: i, total: queue.length });
      setTimeout(next, 0);
    }
    next();
    return () => { cancelled = true; };
  }, []);

  // Expanded canvas render
  useEffect(() => {
    if (!expanded) return;
    const canvas = expandedCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const [cr, ci] = C_VALUES[expanded.cIdx].c;
    const img = renderJulia(expanded.op, cr, ci, FULL_SIZE, FULL_ITER);
    const imageData = new ImageData(img, FULL_SIZE, FULL_SIZE);
    ctx.putImageData(imageData, 0, 0);
  }, [expanded]);

  return (
    <div style={S.root}>
      <header style={S.header}>
        <span style={S.brand}>monogate</span>
        <span style={S.subBrand}>julia set gallery</span>
        <span style={S.formula}>
          {expanded
            ? `z → ${expanded.op}(z, ${C_VALUES[expanded.cIdx].name})`
            : "8 F16 operators · 5 parameter values · 40 Julia sets"}
        </span>
      </header>

      <div style={S.progress}>
        {progress.done < progress.total
          ? `rendering tiles… ${progress.done}/${progress.total}`
          : `${progress.total} tiles rendered · click to expand · ⓘ exceptional cases highlighted`}
      </div>

      <div style={S.grid}>
        <div style={S.headerRow}>
          <div style={S.rowLabel} />
          {C_VALUES.map((cv, i) => (
            <div key={i} style={S.colLabel}>c = {cv.name}</div>
          ))}
        </div>
        {OPS.map((op) => (
          <div key={op} style={S.row}>
            <div style={{ ...S.rowLabel, color: OP_COLORS[op] }}>{op}</div>
            {C_VALUES.map((cv, cIdx) => {
              const key = `${op}|${cIdx}`;
              const img = tiles[key];
              const isFill = FULL_FILL.has(key);
              const isDust = DUST.has(key);
              const isEmpty = EMPTY.has(key);
              return (
                <div
                  key={cIdx}
                  onClick={() => setExpanded({ op, cIdx })}
                  style={{
                    ...S.tile,
                    borderColor: isFill
                      ? OP_COLORS[op]
                      : isDust
                        ? "#f87171"
                        : isEmpty
                          ? "rgba(255,255,255,0.15)"
                          : "rgba(255,255,255,0.06)",
                    boxShadow: isFill
                      ? `0 0 10px ${OP_COLORS[op]}55`
                      : isDust
                        ? "0 0 10px #f8717155"
                        : "none",
                  }}
                  title={
                    isFill ? "Full-fill Julia (Fatou = ℂ)"
                    : isDust ? "Dust Julia (disconnected)"
                    : isEmpty ? "Empty Julia (all points escape)"
                    : `${op} at c=${cv.name}`
                  }
                >
                  <TileCanvas img={img} />
                  {isFill && <span style={S.fillBadge}>FILL</span>}
                  {isDust && <span style={S.dustBadge}>DUST</span>}
                  {isEmpty && <span style={S.emptyBadge}>∅</span>}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {expanded && (
        <div style={S.modal} onClick={() => setExpanded(null)}>
          <div style={S.modalInner} onClick={(e) => e.stopPropagation()}>
            <div style={S.modalHeader}>
              <span style={{ color: OP_COLORS[expanded.op], fontWeight: 600, fontSize: 14 }}>
                {expanded.op}
              </span>
              <span style={{ color: "rgba(255,255,255,0.5)" }}>
                c = {C_VALUES[expanded.cIdx].name}
              </span>
              <div style={{ flex: 1 }} />
              <button onClick={() => setExpanded(null)} style={S.closeBtn}>close</button>
            </div>
            <canvas
              ref={expandedCanvasRef}
              width={FULL_SIZE}
              height={FULL_SIZE}
              style={S.modalCanvas}
            />
            <div style={S.modalFoot}>
              z-plane: [{VIEW.xMin}, {VIEW.xMax}] × [{VIEW.yMin}, {VIEW.yMax}]i · {FULL_ITER} iterations
            </div>
          </div>
        </div>
      )}

      <div style={S.help}>
        A Julia set fixes the parameter c and colors each starting point z by
        how fast it escapes. We render Julia sets for the 8 real-core F16
        operators at five instructive c-values. Outliers: EXL and DEXL at
        c = 1, EDL and DEDL at c = 0 produce <b>full-fill</b> Julia sets
        (the Fatou component is all of ℂ); DEAL at c = −0.5 + 0.5i degenerates
        to a <b>dust</b> (area ≈ 0.01, 0% connected); EAL at c = 2 + i is
        <b> empty</b>. For the additive-arithmetic operators (EML, EAL, DEML,
        DEAL), the Julia sets are connected on most c. For the multiplicative
        operators (EXL, DEXL, EXN, DEXN — the chaotic family), connectedness
        varies sharply with c: small c-perturbations cross connectedness
        boundaries.
      </div>
    </div>
  );
}

function TileCanvas({ img }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !img) return;
    const ctx = canvas.getContext("2d");
    const imageData = new ImageData(img, TILE_SIZE, TILE_SIZE);
    ctx.putImageData(imageData, 0, 0);
  }, [img]);
  return (
    <canvas
      ref={ref}
      width={TILE_SIZE}
      height={TILE_SIZE}
      style={{ display: "block", width: "100%", height: "100%" }}
    />
  );
}

const FONT = "'IBM Plex Mono', 'SF Mono', 'Fira Code', monospace";
const S = {
  root: {
    background: "#08080c",
    color: "#e8e8f0",
    fontFamily: FONT,
    minHeight: "100vh",
    padding: "20px 24px 80px",
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
  formula: { fontSize: 11, color: "rgba(255,255,255,0.2)", marginLeft: "auto" },
  progress: {
    fontSize: 11, color: "rgba(255,255,255,0.5)", marginBottom: 16,
  },
  grid: {
    display: "flex", flexDirection: "column", gap: 6,
    maxWidth: 720, margin: "0 auto",
  },
  headerRow: { display: "flex", gap: 6, alignItems: "end" },
  row: { display: "flex", gap: 6 },
  rowLabel: {
    width: 60, fontSize: 11, fontWeight: 600,
    display: "flex", alignItems: "center",
  },
  colLabel: {
    flex: 1, minWidth: TILE_SIZE, fontSize: 9,
    color: "rgba(255,255,255,0.45)",
    textAlign: "center", padding: "0 0 4px",
  },
  tile: {
    position: "relative",
    flex: 1, minWidth: TILE_SIZE, aspectRatio: "1 / 1",
    border: "1px solid",
    borderRadius: 4, overflow: "hidden", cursor: "pointer",
    background: "#0a0a12",
    transition: "transform 0.15s",
  },
  fillBadge: {
    position: "absolute", top: 4, right: 4,
    background: "rgba(15,211,141,0.92)", color: "#08080c",
    fontSize: 8, fontWeight: 700, padding: "1px 5px", borderRadius: 2,
    letterSpacing: "0.04em",
  },
  dustBadge: {
    position: "absolute", top: 4, right: 4,
    background: "rgba(248,113,113,0.92)", color: "#08080c",
    fontSize: 8, fontWeight: 700, padding: "1px 5px", borderRadius: 2,
    letterSpacing: "0.04em",
  },
  emptyBadge: {
    position: "absolute", top: 4, right: 4,
    background: "rgba(255,255,255,0.2)", color: "#e8e8f0",
    fontSize: 10, fontWeight: 700, padding: "0px 5px", borderRadius: 2,
  },

  modal: {
    position: "fixed", inset: 0, zIndex: 1000,
    background: "rgba(0,0,0,0.75)",
    display: "flex", alignItems: "center", justifyContent: "center",
    backdropFilter: "blur(3px)",
  },
  modalInner: {
    background: "#0a0a12", border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: 8, padding: 16,
    display: "flex", flexDirection: "column", gap: 12,
  },
  modalHeader: { display: "flex", gap: 12, alignItems: "center", fontSize: 12 },
  modalCanvas: { display: "block", imageRendering: "pixelated",
    width: FULL_SIZE, height: FULL_SIZE, borderRadius: 4 },
  modalFoot: { fontSize: 10, color: "rgba(255,255,255,0.4)", textAlign: "center" },
  closeBtn: {
    background: "transparent", border: "1px solid rgba(255,255,255,0.15)",
    color: "rgba(255,255,255,0.5)", fontSize: 10,
    padding: "4px 10px", borderRadius: 3, cursor: "pointer",
    fontFamily: "inherit",
  },

  help: {
    maxWidth: 720, margin: "28px auto 0",
    lineHeight: 1.7, fontSize: 12,
    color: "rgba(255,255,255,0.55)", fontFamily: "system-ui, sans-serif",
  },
};
