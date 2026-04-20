import { useState, useRef, useEffect, useCallback } from "react";

const OPERATORS = {
  EML: { name: "EML", formula: "exp(z) − ln(c)", color: "#4facfe", fn: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    const [lr, li] = cLn(cr, ci);
    return [er - lr, ei - li];
  }},
  DEML: { name: "DEML", formula: "exp(−z) − ln(c)", color: "#f5576c", fn: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(-zr, -zi);
    const [lr, li] = cLn(cr, ci);
    return [er - lr, ei - li];
  }},
  EXL: { name: "EXL", formula: "exp(z) · ln(c)", color: "#0fd38d", fn: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    const [lr, li] = cLn(cr, ci);
    return [er*lr - ei*li, er*li + ei*lr];
  }},
  EDL: { name: "EDL", formula: "exp(z) / ln(c)", color: "#fccb52", fn: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    const [lr, li] = cLn(cr, ci);
    const d = lr*lr + li*li;
    if (d < 1e-30) return [1e10, 0];
    return [(er*lr + ei*li)/d, (ei*lr - er*li)/d];
  }},
  EAL: { name: "EAL", formula: "exp(z) + ln(c)", color: "#a18cd1", fn: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    const [lr, li] = cLn(cr, ci);
    return [er + lr, ei + li];
  }},
  EMN: { name: "EMN", formula: "ln(c) − exp(z)", color: "#ff9966", fn: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    const [lr, li] = cLn(cr, ci);
    return [lr - er, li - ei];
  }},
  EPL: { name: "EPL", formula: "exp(z)^ln(c)", color: "#96e6a1", fn: (zr, zi, cr, ci) => {
    const [lr, li] = cLn(cr, ci);
    const wr = zr*lr - zi*li;
    const wi = zr*li + zi*lr;
    return cExp(wr, wi);
  }},
  LEAd: { name: "LEAd", formula: "ln(exp(z) + c)", color: "#e0c3fc", fn: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    return cLn(er + cr, ei + ci);
  }},
};

function cExp(r, i) {
  const e = Math.exp(r);
  return [e * Math.cos(i), e * Math.sin(i)];
}

function cLn(r, i) {
  const mag = Math.sqrt(r*r + i*i);
  if (mag < 1e-300) return [-700, 0];
  return [Math.log(mag), Math.atan2(i, r)];
}

function iterate(op, cr, ci, maxIter, escapeR) {
  let zr = 0, zi = 0;
  for (let n = 0; n < maxIter; n++) {
    try {
      [zr, zi] = op(zr, zi, cr, ci);
    } catch { return n; }
    if (zr*zr + zi*zi > escapeR*escapeR) {
      const smooth = n + 1 - Math.log(Math.log(Math.sqrt(zr*zr+zi*zi)+1)+1) / Math.log(2);
      return Math.max(0, smooth);
    }
    if (isNaN(zr) || isNaN(zi) || !isFinite(zr) || !isFinite(zi)) return n;
  }
  return -1;
}

const PALETTES = {
  deep: (t) => {
    const h = 220 + t * 160;
    const s = 70 + (1-t)*30;
    const l = 8 + Math.pow(t, 0.4) * 55;
    return hslStr(h%360, s, l);
  },
  fire: (t) => {
    const h = -20 + t * 80;
    const s = 85 + (1-t)*15;
    const l = 8 + Math.pow(t, 0.35) * 60;
    return hslStr(((h%360)+360)%360, s, l);
  },
  aurora: (t) => {
    const h = 120 + t * 200;
    const s = 60 + (1-t)*40;
    const l = 6 + Math.pow(t, 0.45) * 52;
    return hslStr(h%360, s, l);
  },
  mono: (t) => {
    const l = 5 + Math.pow(t, 0.5) * 80;
    return hslStr(220, 5, l);
  },
};

function hslStr(h, s, l) {
  return `hsl(${h},${s}%,${l}%)`;
}

function hslToRgb(h, s, l) {
  h /= 360; s /= 100; l /= 100;
  let r, g, b;
  if (s === 0) { r = g = b = l; } else {
    const q = l < 0.5 ? l*(1+s) : l+s-l*s;
    const p = 2*l-q;
    const hue2rgb = (p,q,t) => { if(t<0)t+=1;if(t>1)t-=1;if(t<1/6)return p+(q-p)*6*t;if(t<1/2)return q;if(t<2/3)return p+(q-p)*(2/3-t)*6;return p; };
    r = hue2rgb(p,q,h+1/3); g = hue2rgb(p,q,h); b = hue2rgb(p,q,h-1/3);
  }
  return [Math.round(r*255), Math.round(g*255), Math.round(b*255)];
}

function getPaletteRgb(name, t) {
  const fn = PALETTES[name] || PALETTES.deep;
  const str = fn(t);
  const m = str.match(/hsl\(([\d.]+),([\d.]+)%,([\d.]+)%\)/);
  if (!m) return [0,0,0];
  return hslToRgb(parseFloat(m[1]), parseFloat(m[2]), parseFloat(m[3]));
}

export default function EMLFractalExplorer() {
  const canvasRef = useRef(null);
  const [op, setOp] = useState("EML");
  const [palette, setPalette] = useState("deep");
  const [maxIter, setMaxIter] = useState(80);
  const [view, setView] = useState({ xMin: -3.5, xMax: 4.5, yMin: -2.5, yMax: 2.5 });
  const [rendering, setRendering] = useState(false);
  const [mousePos, setMousePos] = useState(null);
  const [dragStart, setDragStart] = useState(null);
  const [history, setHistory] = useState([]);
  const renderRef = useRef(0);

  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width;
    const H = canvas.height;
    const { xMin, xMax, yMin, yMax } = view;
    const opFn = OPERATORS[op].fn;
    const escapeR = 50;
    const renderId = ++renderRef.current;

    setRendering(true);

    const rowHeight = 8;
    let py = 0;

    function renderChunk() {
      if (renderId !== renderRef.current) return;
      const imageData = ctx.createImageData(W, rowHeight);
      const data = imageData.data;
      const endY = Math.min(py + rowHeight, H);

      for (let y = py; y < endY; y++) {
        for (let px = 0; px < W; px++) {
          const cr = xMin + (px / W) * (xMax - xMin);
          const ci = yMin + (y / H) * (yMax - yMin);
          const result = iterate(opFn, cr, ci, maxIter, escapeR);
          const idx = ((y - py) * W + px) * 4;

          if (result < 0) {
            data[idx] = 6; data[idx+1] = 6; data[idx+2] = 10;
          } else {
            const t = Math.min(result / maxIter, 1);
            const [r, g, b] = getPaletteRgb(palette, t);
            data[idx] = r; data[idx+1] = g; data[idx+2] = b;
          }
          data[idx+3] = 255;
        }
      }
      ctx.putImageData(imageData, 0, py);
      py = endY;
      if (py < H) {
        requestAnimationFrame(renderChunk);
      } else {
        setRendering(false);
      }
    }
    renderChunk();
  }, [view, op, palette, maxIter]);

  useEffect(() => { render(); }, [render]);

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) / rect.width;
    const my = (e.clientY - rect.top) / rect.height;
    const { xMin, xMax, yMin, yMax } = view;
    const cx = xMin + mx * (xMax - xMin);
    const cy = yMin + my * (yMax - yMin);
    const factor = e.deltaY > 0 ? 1.3 : 0.7;
    const nw = (xMax - xMin) * factor;
    const nh = (yMax - yMin) * factor;
    setHistory(h => [...h, view]);
    setView({
      xMin: cx - mx * nw, xMax: cx + (1-mx) * nw,
      yMin: cy - my * nh, yMax: cy + (1-my) * nh,
    });
  }, [view]);

  const handleMouseDown = useCallback((e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    setDragStart({ x: e.clientX, y: e.clientY, view: {...view}, rect });
  }, [view]);

  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const { xMin, xMax, yMin, yMax } = view;
    const mx = (e.clientX - rect.left) / rect.width;
    const my = (e.clientY - rect.top) / rect.height;
    setMousePos({ r: (xMin + mx*(xMax-xMin)).toFixed(4), i: (yMin + my*(yMax-yMin)).toFixed(4) });

    if (dragStart) {
      const dx = (e.clientX - dragStart.x) / dragStart.rect.width;
      const dy = (e.clientY - dragStart.y) / dragStart.rect.height;
      const sv = dragStart.view;
      const w = sv.xMax - sv.xMin;
      const h = sv.yMax - sv.yMin;
      setView({
        xMin: sv.xMin - dx*w, xMax: sv.xMax - dx*w,
        yMin: sv.yMin - dy*h, yMax: sv.yMax - dy*h,
      });
    }
  }, [dragStart, view]);

  const handleMouseUp = useCallback(() => {
    if (dragStart) {
      setHistory(h => [...h, dragStart.view]);
      setDragStart(null);
    }
  }, [dragStart]);

  const resetView = () => {
    setHistory(h => [...h, view]);
    setView({ xMin: -3.5, xMax: 4.5, yMin: -2.5, yMax: 2.5 });
  };

  const goBack = () => {
    if (history.length > 0) {
      const prev = history[history.length - 1];
      setHistory(h => h.slice(0, -1));
      setView(prev);
    }
  };

  const zoom = view.xMax - view.xMin;

  return (
    <div style={{ background: "#08080c", color: "#e8e8f0", fontFamily: "'IBM Plex Mono', 'SF Mono', 'Fira Code', monospace", minHeight: "100vh", display: "flex", flexDirection: "column" }}>

      <div style={{ padding: "20px 24px 12px", display: "flex", alignItems: "baseline", gap: 16, flexWrap: "wrap", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <span style={{ fontSize: 13, fontWeight: 600, letterSpacing: "0.15em", textTransform: "uppercase", color: "#4facfe", opacity: 0.9 }}>monogate</span>
        <span style={{ fontSize: 13, color: "rgba(255,255,255,0.3)" }}>fractal explorer</span>
        <span style={{ fontSize: 11, color: "rgba(255,255,255,0.15)", marginLeft: "auto" }}>
          z → {OPERATORS[op].formula}
        </span>
      </div>

      <div style={{ display: "flex", gap: 6, padding: "12px 24px", flexWrap: "wrap", alignItems: "center" }}>
        {Object.entries(OPERATORS).map(([key, val]) => (
          <button key={key} onClick={() => setOp(key)} style={{
            background: op === key ? val.color : "rgba(255,255,255,0.04)",
            color: op === key ? "#08080c" : "rgba(255,255,255,0.5)",
            border: op === key ? "none" : "1px solid rgba(255,255,255,0.08)",
            borderRadius: 4, padding: "5px 12px", fontSize: 12, fontFamily: "inherit",
            cursor: "pointer", fontWeight: op === key ? 600 : 400,
            transition: "all 0.2s",
          }}>
            {val.name}
          </button>
        ))}
        <div style={{ width: 1, height: 20, background: "rgba(255,255,255,0.08)", margin: "0 4px" }} />
        {Object.keys(PALETTES).map(p => (
          <button key={p} onClick={() => setPalette(p)} style={{
            background: palette === p ? "rgba(255,255,255,0.12)" : "transparent",
            color: palette === p ? "#e8e8f0" : "rgba(255,255,255,0.3)",
            border: "1px solid", borderColor: palette === p ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.06)",
            borderRadius: 4, padding: "5px 10px", fontSize: 11, fontFamily: "inherit",
            cursor: "pointer", textTransform: "capitalize",
          }}>
            {p}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, position: "relative", margin: "0 24px 12px", borderRadius: 6, overflow: "hidden", border: "1px solid rgba(255,255,255,0.06)" }}>
        <canvas
          ref={canvasRef}
          width={680}
          height={425}
          style={{ width: "100%", height: "100%", display: "block", cursor: dragStart ? "grabbing" : "crosshair" }}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={() => { setMousePos(null); setDragStart(null); }}
        />

        {rendering && (
          <div style={{ position: "absolute", top: 12, right: 12, background: "rgba(0,0,0,0.7)", borderRadius: 4, padding: "4px 10px", fontSize: 11, color: OPERATORS[op].color, backdropFilter: "blur(8px)" }}>
            rendering...
          </div>
        )}

        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, padding: "12px 16px", background: "linear-gradient(transparent, rgba(0,0,0,0.8))", display: "flex", justifyContent: "space-between", alignItems: "flex-end", pointerEvents: "none" }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 500, color: "rgba(255,255,255,0.85)", marginBottom: 2 }}>
              z → {OPERATORS[op].formula}
            </div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)" }}>
              The {OPERATORS[op].name} Mandelbrot set
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            {mousePos && (
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 2 }}>
                c = {mousePos.r} + {mousePos.i}i
              </div>
            )}
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.25)" }}>
              zoom: {zoom < 0.01 ? zoom.toExponential(2) : zoom.toFixed(2)} | iter: {maxIter}
            </div>
          </div>
        </div>
      </div>

      <div style={{ padding: "8px 24px 16px", display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <button onClick={resetView} style={btnStyle}>reset</button>
        <button onClick={goBack} disabled={history.length === 0} style={{ ...btnStyle, opacity: history.length > 0 ? 1 : 0.3 }}>back</button>
        <div style={{ width: 1, height: 20, background: "rgba(255,255,255,0.08)", margin: "0 4px" }} />
        <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", marginRight: 4 }}>iterations</span>
        {[50, 100, 200, 400].map(n => (
          <button key={n} onClick={() => setMaxIter(n)} style={{
            ...btnStyle,
            background: maxIter === n ? "rgba(255,255,255,0.1)" : "transparent",
            color: maxIter === n ? "#e8e8f0" : "rgba(255,255,255,0.3)",
            borderColor: maxIter === n ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.06)",
          }}>
            {n}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: 10, color: "rgba(255,255,255,0.15)", letterSpacing: "0.1em" }}>
          scroll to zoom · drag to pan · 8 operators · 4 palettes
        </span>
      </div>
    </div>
  );
}

const btnStyle = {
  background: "transparent",
  color: "rgba(255,255,255,0.5)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 4,
  padding: "4px 12px",
  fontSize: 11,
  fontFamily: "'IBM Plex Mono', 'SF Mono', monospace",
  cursor: "pointer",
};
