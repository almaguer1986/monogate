// EML Fractal Studio — Flagship 1 for monogate.dev/lab
//
// Three modes over a single fractal canvas:
//   Visual    — silent Mandelbrot for 8 EML-family operators (default).
//   Audio     — hover plays a tone, click locks a tone (up to 6) as a chord.
//   Sequencer — vertical scan line sweeps left-to-right; iteration counts
//               become notes. The fractal boundary becomes a musical score.
//
// The fractal IS the instrument. One app, one space, vision and sound from
// the same operator.

import { useState, useRef, useEffect, useCallback } from "react";
import { ORBIT_BY_OP, SHARKOVSKII_OPS } from "./orbit-data.js";

// ─── Operator definitions ────────────────────────────────────────────────────

const OPERATORS = {
  EML:  { name: "EML",  formula: "exp(z) − ln(c)",  color: "#4facfe" },
  DEML: { name: "DEML", formula: "exp(−z) − ln(c)", color: "#f5576c" },
  EXL:  { name: "EXL",  formula: "exp(z) · ln(c)",  color: "#0fd38d" },
  EDL:  { name: "EDL",  formula: "exp(z) / ln(c)",  color: "#fccb52" },
  EAL:  { name: "EAL",  formula: "exp(z) + ln(c)",  color: "#a18cd1" },
  EMN:  { name: "EMN",  formula: "ln(c) − exp(z)",  color: "#ff9966" },
  EPL:  { name: "EPL",  formula: "exp(z)^ln(c)",    color: "#96e6a1" },
  LEAd: { name: "LEAd", formula: "ln(exp(z) + c)",  color: "#e0c3fc" },
};

function cExp(r, i) {
  const e = Math.exp(r);
  return [e * Math.cos(i), e * Math.sin(i)];
}

function cLn(r, i) {
  const mag = Math.sqrt(r * r + i * i);
  if (mag < 1e-300) return [-700, 0];
  return [Math.log(mag), Math.atan2(i, r)];
}

const OP_FNS = {
  EML: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    const [lr, li] = cLn(cr, ci);
    return [er - lr, ei - li];
  },
  DEML: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(-zr, -zi);
    const [lr, li] = cLn(cr, ci);
    return [er - lr, ei - li];
  },
  EXL: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    const [lr, li] = cLn(cr, ci);
    return [er * lr - ei * li, er * li + ei * lr];
  },
  EDL: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    const [lr, li] = cLn(cr, ci);
    const d = lr * lr + li * li;
    if (d < 1e-30) return [1e10, 0];
    return [(er * lr + ei * li) / d, (ei * lr - er * li) / d];
  },
  EAL: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    const [lr, li] = cLn(cr, ci);
    return [er + lr, ei + li];
  },
  EMN: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    const [lr, li] = cLn(cr, ci);
    return [lr - er, li - ei];
  },
  EPL: (zr, zi, cr, ci) => {
    const [lr, li] = cLn(cr, ci);
    const wr = zr * lr - zi * li;
    const wi = zr * li + zi * lr;
    return cExp(wr, wi);
  },
  LEAd: (zr, zi, cr, ci) => {
    const [er, ei] = cExp(zr, zi);
    return cLn(er + cr, ei + ci);
  },
};

// Build a blended operator (1 − t)·op1 + t·op2, linearly interpolating both
// real and imaginary parts at every iteration step. t=0 ⇒ op1, t=1 ⇒ op2.
// A uniform in-between gives a continuous fractal morph between the two
// operators' Mandelbrot sets.
function makeBlendedOp(op1, op2, t) {
  const s = 1 - t;
  return (zr, zi, cr, ci) => {
    const [r1, i1] = op1(zr, zi, cr, ci);
    const [r2, i2] = op2(zr, zi, cr, ci);
    return [s * r1 + t * r2, s * i1 + t * i2];
  };
}

// Returns -1 if the point never escapes. Otherwise a smooth-coloring value.
function iterate(op, cr, ci, maxIter, escapeR) {
  let zr = 0;
  let zi = 0;
  for (let n = 0; n < maxIter; n++) {
    const next = op(zr, zi, cr, ci);
    zr = next[0];
    zi = next[1];
    if (!isFinite(zr) || !isFinite(zi) || isNaN(zr) || isNaN(zi)) return n;
    const mag2 = zr * zr + zi * zi;
    if (mag2 > escapeR * escapeR) {
      const smooth = n + 1 - Math.log(Math.log(Math.sqrt(mag2) + 1) + 1) / Math.log(2);
      return Math.max(0, smooth);
    }
  }
  return -1;
}

// ─── Palettes ────────────────────────────────────────────────────────────────

const PALETTES = {
  deep:   (t) => hslStr(((220 + t * 160) % 360 + 360) % 360, 70 + (1 - t) * 30, 8 + Math.pow(t, 0.4) * 55),
  fire:   (t) => hslStr((((-20 + t * 80) % 360) + 360) % 360, 85 + (1 - t) * 15, 8 + Math.pow(t, 0.35) * 60),
  aurora: (t) => hslStr(((120 + t * 200) % 360 + 360) % 360, 60 + (1 - t) * 40, 6 + Math.pow(t, 0.45) * 52),
  mono:   (t) => hslStr(220, 5, 5 + Math.pow(t, 0.5) * 80),
};

function hslStr(h, s, l) { return `hsl(${h},${s}%,${l}%)`; }

function hslToRgb(h, s, l) {
  h /= 360; s /= 100; l /= 100;
  let r, g, b;
  if (s === 0) {
    r = g = b = l;
  } else {
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    const h2r = (pp, qq, tt) => {
      if (tt < 0) tt += 1;
      if (tt > 1) tt -= 1;
      if (tt < 1 / 6) return pp + (qq - pp) * 6 * tt;
      if (tt < 1 / 2) return qq;
      if (tt < 2 / 3) return pp + (qq - pp) * (2 / 3 - tt) * 6;
      return pp;
    };
    r = h2r(p, q, h + 1 / 3);
    g = h2r(p, q, h);
    b = h2r(p, q, h - 1 / 3);
  }
  return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

function paletteRgb(name, t) {
  const fn = PALETTES[name] || PALETTES.deep;
  const m = fn(t).match(/hsl\(([\d.]+),([\d.]+)%,([\d.]+)%\)/);
  if (!m) return [0, 0, 0];
  return hslToRgb(parseFloat(m[1]), parseFloat(m[2]), parseFloat(m[3]));
}

// ─── Audio engine ────────────────────────────────────────────────────────────
//
// One AudioContext per studio instance, created lazily on first audio use
// (required on iOS Safari). Six locked tones max. Single hover oscillator
// whose frequency is retuned in place — avoids the OscillatorNode churn
// that would otherwise crackle on mousemove.

const BASE_HZ = 80;
const TOP_HZ = 3000;
const MAX_LOCKED = 6;
const ESCAPE_R = 50;

function iterToFreq(iter, maxIter) {
  // Points that never escape map to the bass drone at BASE_HZ.
  if (iter < 0) return BASE_HZ;
  const t = Math.min(Math.max(iter / maxIter, 0), 1);
  return BASE_HZ * Math.pow(TOP_HZ / BASE_HZ, t);
}

function createAudio() {
  const Ctx = typeof window === "undefined"
    ? null
    : (window.AudioContext || window.webkitAudioContext);
  if (!Ctx) return null;
  const ctx = new Ctx();

  const master = ctx.createGain();
  master.gain.value = 0.3;

  // Dry/wet reverb bus. Reverb is bypassed by default (wet=0).
  const dry = ctx.createGain();
  dry.gain.value = 1;
  const wet = ctx.createGain();
  wet.gain.value = 0;

  const convolver = ctx.createConvolver();
  convolver.buffer = makeReverbImpulse(ctx, 1.6, 2.5);

  dry.connect(master);
  convolver.connect(wet);
  wet.connect(master);
  master.connect(ctx.destination);

  return { ctx, master, dry, wet, convolver };
}

function makeReverbImpulse(ctx, duration, decay) {
  const rate = ctx.sampleRate;
  const length = Math.floor(rate * duration);
  const impulse = ctx.createBuffer(2, length, rate);
  for (let ch = 0; ch < 2; ch++) {
    const data = impulse.getChannelData(ch);
    for (let i = 0; i < length; i++) {
      const t = i / length;
      data[i] = (Math.random() * 2 - 1) * Math.pow(1 - t, decay);
    }
  }
  return impulse;
}

function spawnTone(audio, freq, gain = 0.07) {
  const osc = audio.ctx.createOscillator();
  const g = audio.ctx.createGain();
  osc.type = "sine";
  osc.frequency.value = freq;
  const now = audio.ctx.currentTime;
  g.gain.setValueAtTime(0, now);
  g.gain.linearRampToValueAtTime(gain, now + 0.04);
  osc.connect(g);
  g.connect(audio.dry);
  g.connect(audio.convolver);
  osc.start();
  return { osc, gain: g };
}

function killTone(audio, tone) {
  if (!tone) return;
  const now = audio.ctx.currentTime;
  try {
    tone.gain.gain.cancelScheduledValues(now);
    tone.gain.gain.setValueAtTime(tone.gain.gain.value, now);
    tone.gain.gain.linearRampToValueAtTime(0, now + 0.08);
    tone.osc.stop(now + 0.12);
  } catch { /* already stopped */ }
}

// Schedule a short percussive note at an absolute AudioContext time.
function scheduleNote(audio, time, freq, duration = 0.14, gain = 0.08) {
  const osc = audio.ctx.createOscillator();
  const g = audio.ctx.createGain();
  osc.type = "sine";
  osc.frequency.value = freq;
  g.gain.setValueAtTime(0, time);
  g.gain.linearRampToValueAtTime(gain, time + 0.01);
  g.gain.linearRampToValueAtTime(0, time + duration);
  osc.connect(g);
  g.connect(audio.dry);
  g.connect(audio.convolver);
  osc.start(time);
  osc.stop(time + duration + 0.02);
}

// ─── Component ───────────────────────────────────────────────────────────────

const W = 680;
const H = 425;

const DEFAULT_VIEW = { xMin: -3.5, xMax: 4.5, yMin: -2.5, yMax: 2.5 };
const ITER_STEPS = [50, 80, 200, 400];

export default function FractalStudio() {
  const canvasRef = useRef(null);
  const renderRef = useRef(0);
  const iterGridRef = useRef(null); // Float32Array of iteration counts per pixel

  const [op, setOp] = useState("EML");
  const [op2, setOp2] = useState("DEML");
  const [morphOn, setMorphOn] = useState(false);
  const [morphT, setMorphT] = useState(0.5);
  const [palette, setPalette] = useState("deep");
  const [maxIter, setMaxIter] = useState(80);
  const [view, setView] = useState(DEFAULT_VIEW);
  const [history, setHistory] = useState([]);
  const [rendering, setRendering] = useState(false);
  const [mousePos, setMousePos] = useState(null);
  const [dragStart, setDragStart] = useState(null);

  const [mode, setMode] = useState("visual");      // visual | audio | sequencer
  const [lockedPoints, setLockedPoints] = useState([]);
  const [reverbOn, setReverbOn] = useState(false);
  const [masterVol, setMasterVol] = useState(0.3);
  const [bpm, setBpm] = useState(120);
  const [loop, setLoop] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [scanX, setScanX] = useState(0);
  const [orbitPlayback, setOrbitPlayback] = useState(false);
  const [orbitStep, setOrbitStep] = useState(0);
  const oscCanvasRef = useRef(null);

  // Audio refs (not state; we don't want re-renders on every oscillator tick)
  const audioRef = useRef(null);
  const hoverToneRef = useRef(null);
  const lockedToneMapRef = useRef(new Map());   // id → {osc, gain}
  const lastHoverFreqRef = useRef(0);

  // Current iteration operator: optionally blended with op2 via slider t.
  const activeOpFn = useCallback(() => {
    if (!morphOn) return OP_FNS[op];
    return makeBlendedOp(OP_FNS[op], OP_FNS[op2], morphT);
  }, [op, op2, morphOn, morphT]);

  // ── Render loop ───────────────────────────────────────────────────────────
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const opFn = activeOpFn();
    const { xMin, xMax, yMin, yMax } = view;
    const renderId = ++renderRef.current;

    const grid = new Float32Array(W * H);
    iterGridRef.current = grid;

    setRendering(true);

    const rowHeight = 8;
    let py = 0;

    function renderChunk() {
      if (renderId !== renderRef.current) return;
      const image = ctx.createImageData(W, rowHeight);
      const data = image.data;
      const endY = Math.min(py + rowHeight, H);

      for (let y = py; y < endY; y++) {
        for (let px = 0; px < W; px++) {
          const cr = xMin + (px / W) * (xMax - xMin);
          const ci = yMin + (y / H) * (yMax - yMin);
          const it = iterate(opFn, cr, ci, maxIter, ESCAPE_R);
          grid[y * W + px] = it;
          const idx = ((y - py) * W + px) * 4;
          if (it < 0) {
            data[idx] = 6; data[idx + 1] = 6; data[idx + 2] = 10;
          } else {
            const t = Math.min(it / maxIter, 1);
            const [r, g, b] = paletteRgb(palette, t);
            data[idx] = r; data[idx + 1] = g; data[idx + 2] = b;
          }
          data[idx + 3] = 255;
        }
      }
      ctx.putImageData(image, 0, py);
      py = endY;
      if (py < H) {
        requestAnimationFrame(renderChunk);
      } else {
        setRendering(false);
      }
    }
    renderChunk();
  }, [view, op, op2, morphOn, morphT, palette, maxIter, activeOpFn]);

  useEffect(() => { render(); }, [render]);

  // Re-tune locked tones when op/maxIter/morph changes (same points, new iters)
  useEffect(() => {
    if (!audioRef.current || lockedPoints.length === 0) return;
    const opFn = activeOpFn();
    setLockedPoints((prev) => prev.map((lp) => {
      const it = iterate(opFn, lp.cr, lp.ci, maxIter, ESCAPE_R);
      const freq = iterToFreq(it, maxIter);
      const tone = lockedToneMapRef.current.get(lp.id);
      if (tone) {
        const now = audioRef.current.ctx.currentTime;
        tone.osc.frequency.setTargetAtTime(freq, now, 0.08);
      }
      return { ...lp, iter: it, freq };
    }));
    // Only depends on op/maxIter/morph — changing palette doesn't alter iters.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [op, op2, morphOn, morphT, maxIter]);

  // Master volume follow-through
  useEffect(() => {
    if (!audioRef.current) return;
    const now = audioRef.current.ctx.currentTime;
    audioRef.current.master.gain.setTargetAtTime(masterVol, now, 0.05);
  }, [masterVol]);

  // Reverb follow-through
  useEffect(() => {
    if (!audioRef.current) return;
    const now = audioRef.current.ctx.currentTime;
    const target = reverbOn ? 0.35 : 0;
    audioRef.current.wet.gain.setTargetAtTime(target, now, 0.05);
  }, [reverbOn]);

  // Stop everything on unmount
  useEffect(() => () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (hoverToneRef.current) killTone(audio, hoverToneRef.current);
    lockedToneMapRef.current.forEach((t) => killTone(audio, t));
    try { audio.ctx.close(); } catch { /* ignore */ }
  }, []);

  // ── Audio helpers ────────────────────────────────────────────────────────
  function ensureAudio() {
    if (audioRef.current) return audioRef.current;
    const a = createAudio();
    if (!a) return null;
    audioRef.current = a;
    a.master.gain.value = masterVol;
    a.wet.gain.value = reverbOn ? 0.35 : 0;
    return a;
  }

  function playHover(freq) {
    const audio = ensureAudio();
    if (!audio) return;
    if (!hoverToneRef.current) {
      hoverToneRef.current = spawnTone(audio, freq, 0.05);
    }
    if (Math.abs(freq - lastHoverFreqRef.current) > 0.5) {
      const now = audio.ctx.currentTime;
      hoverToneRef.current.osc.frequency.setTargetAtTime(freq, now, 0.02);
      lastHoverFreqRef.current = freq;
    }
  }

  function fadeHover() {
    if (!audioRef.current || !hoverToneRef.current) return;
    const audio = audioRef.current;
    const now = audio.ctx.currentTime;
    hoverToneRef.current.gain.gain.setTargetAtTime(0, now, 0.05);
  }

  function resumeHover() {
    if (!audioRef.current || !hoverToneRef.current) return;
    const audio = audioRef.current;
    const now = audio.ctx.currentTime;
    hoverToneRef.current.gain.gain.setTargetAtTime(0.05, now, 0.02);
  }

  function stopHover() {
    if (!audioRef.current || !hoverToneRef.current) return;
    killTone(audioRef.current, hoverToneRef.current);
    hoverToneRef.current = null;
    lastHoverFreqRef.current = 0;
  }

  // ── Mode switching cleanup ───────────────────────────────────────────────
  useEffect(() => {
    if (mode !== "audio") {
      stopHover();
    }
    if (mode !== "sequencer") {
      setIsPlaying(false);
    }
    // Clear locked tones when leaving audio mode entirely; keep them when
    // switching audio↔sequencer so chord survives round-trips.
    if (mode === "visual") {
      const audio = audioRef.current;
      if (audio) {
        lockedToneMapRef.current.forEach((t) => killTone(audio, t));
      }
      lockedToneMapRef.current.clear();
      setLockedPoints([]);
    }
  }, [mode]);

  // ── Coord helpers ────────────────────────────────────────────────────────
  function pxToComplex(px, py) {
    const { xMin, xMax, yMin, yMax } = view;
    return [xMin + (px / W) * (xMax - xMin), yMin + (py / H) * (yMax - yMin)];
  }

  function iterAtPixel(px, py) {
    const grid = iterGridRef.current;
    if (grid && px >= 0 && px < W && py >= 0 && py < H) {
      return grid[py * W + px];
    }
    const [cr, ci] = pxToComplex(px, py);
    return iterate(activeOpFn(), cr, ci, maxIter, ESCAPE_R);
  }

  // ── Interaction handlers ─────────────────────────────────────────────────
  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = (e.clientX - rect.left) / rect.width;
    const my = (e.clientY - rect.top) / rect.height;
    const { xMin, xMax, yMin, yMax } = view;
    const cx = xMin + mx * (xMax - xMin);
    const cy = yMin + my * (yMax - yMin);
    const factor = e.deltaY > 0 ? 1.3 : 0.7;
    const nw = (xMax - xMin) * factor;
    const nh = (yMax - yMin) * factor;
    setHistory((h) => [...h, view]);
    setView({
      xMin: cx - mx * nw, xMax: cx + (1 - mx) * nw,
      yMin: cy - my * nh, yMax: cy + (1 - my) * nh,
    });
  }, [view]);

  const handleMouseDown = useCallback((e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    setDragStart({ x: e.clientX, y: e.clientY, view: { ...view }, rect, moved: false });
  }, [view]);

  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const localX = e.clientX - rect.left;
    const localY = e.clientY - rect.top;
    const px = Math.floor((localX / rect.width) * W);
    const py = Math.floor((localY / rect.height) * H);
    const [cr, ci] = pxToComplex(px, py);
    setMousePos({ r: cr.toFixed(4), i: ci.toFixed(4) });

    if (dragStart) {
      if (Math.abs(e.clientX - dragStart.x) + Math.abs(e.clientY - dragStart.y) > 3) {
        dragStart.moved = true;
      }
      const dx = (e.clientX - dragStart.x) / dragStart.rect.width;
      const dy = (e.clientY - dragStart.y) / dragStart.rect.height;
      const sv = dragStart.view;
      const w = sv.xMax - sv.xMin;
      const h = sv.yMax - sv.yMin;
      setView({
        xMin: sv.xMin - dx * w, xMax: sv.xMax - dx * w,
        yMin: sv.yMin - dy * h, yMax: sv.yMax - dy * h,
      });
      return;
    }

    if (mode === "audio") {
      const it = iterAtPixel(px, py);
      playHover(iterToFreq(it, maxIter));
    }
  }, [dragStart, view, mode, maxIter, op, op2, morphOn, morphT]);

  const handleMouseUp = useCallback((e) => {
    const ds = dragStart;
    setDragStart(null);
    if (ds && ds.moved) {
      setHistory((h) => [...h, ds.view]);
      return;
    }
    // Click-without-drag in Audio mode: toggle a locked tone.
    if (mode !== "audio" || !ds) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const localX = e.clientX - rect.left;
    const localY = e.clientY - rect.top;
    const px = Math.floor((localX / rect.width) * W);
    const py = Math.floor((localY / rect.height) * H);
    toggleLockedPoint(px, py);
  }, [dragStart, mode]);

  const handleMouseLeave = useCallback(() => {
    setMousePos(null);
    setDragStart(null);
    if (mode === "audio") fadeHover();
  }, [mode]);

  const handleMouseEnter = useCallback(() => {
    if (mode === "audio" && hoverToneRef.current) resumeHover();
  }, [mode]);

  // ── Locked tones ─────────────────────────────────────────────────────────
  function toggleLockedPoint(px, py) {
    // If user clicked near an existing lock, remove it. Radius = 10px.
    const existing = lockedPoints.find(
      (lp) => Math.abs(lp.px - px) < 10 && Math.abs(lp.py - py) < 10
    );
    if (existing) {
      const audio = audioRef.current;
      if (audio) {
        const tone = lockedToneMapRef.current.get(existing.id);
        if (tone) killTone(audio, tone);
      }
      lockedToneMapRef.current.delete(existing.id);
      setLockedPoints((prev) => prev.filter((lp) => lp.id !== existing.id));
      return;
    }
    if (lockedPoints.length >= MAX_LOCKED) return;
    const [cr, ci] = pxToComplex(px, py);
    const it = iterate(activeOpFn(), cr, ci, maxIter, ESCAPE_R);
    const freq = iterToFreq(it, maxIter);
    const audio = ensureAudio();
    if (!audio) return;
    const id = Date.now() + Math.random();
    const tone = spawnTone(audio, freq, 0.06);
    lockedToneMapRef.current.set(id, tone);
    setLockedPoints((prev) => [...prev, { id, px, py, cr, ci, iter: it, freq }]);
  }

  function clearLocked() {
    const audio = audioRef.current;
    if (audio) {
      lockedToneMapRef.current.forEach((t) => killTone(audio, t));
    }
    lockedToneMapRef.current.clear();
    setLockedPoints([]);
  }

  // ── Sequencer ────────────────────────────────────────────────────────────
  const SEQ_ROWS = 8;
  const scanRef = useRef(0);
  const lastScheduledColRef = useRef(-1);
  const orbitIdxRef = useRef(0);
  const lastScheduledOrbitRef = useRef(-1);

  useEffect(() => {
    if (mode !== "sequencer" || !isPlaying) return;
    ensureAudio();
    let rafId = 0;
    let last = performance.now();
    lastScheduledColRef.current = -1;
    lastScheduledOrbitRef.current = -1;

    // Orbit dataset (present only for the 8 F16 operators we sampled).
    const orbit = orbitPlayback ? ORBIT_BY_OP[op] : null;

    function step(now) {
      const dt = (now - last) / 1000;
      last = now;

      if (orbit) {
        // Orbit playback: step through 256 orbit samples at BPM-derived rate.
        // At 120 BPM, one full orbit loop ≈ 4 seconds (~16 samples/sec).
        const samplesPerSec = (orbit.re.length / 4) * (bpm / 120);
        orbitIdxRef.current += samplesPerSec * dt;
        if (orbitIdxRef.current >= orbit.re.length) {
          if (loop) {
            orbitIdxRef.current = 0;
            lastScheduledOrbitRef.current = -1;
          } else {
            orbitIdxRef.current = orbit.re.length - 1;
            setIsPlaying(false);
          }
        }
        const floatIdx = orbitIdxRef.current;
        const intIdx = Math.floor(floatIdx);
        setOrbitStep(intIdx);

        // Visual: scan line = x-position mapped from orbit Re value in its range.
        const [reLo, reHi] = orbit.re_range;
        const span = Math.max(reHi - reLo, 1e-9);
        const reNow = orbit.re[Math.min(intIdx, orbit.re.length - 1)] ?? 0;
        const px = ((reNow - reLo) / span) * W;
        setScanX(Math.max(0, Math.min(W - 1, px)));

        if (intIdx > lastScheduledOrbitRef.current) {
          scheduleOrbitSample(orbit, intIdx);
          lastScheduledOrbitRef.current = intIdx;
        }
      } else {
        // One beat = one column of W pixels divided by BPM-derived column rate.
        // At 120 BPM with W=680, one full sweep in 4 beats = 2 sec.
        const pxPerSec = (W / 4) * (bpm / 60);
        scanRef.current += pxPerSec * dt;
        if (scanRef.current >= W) {
          if (loop) {
            scanRef.current = 0;
            lastScheduledColRef.current = -1;
          } else {
            scanRef.current = W;
            setIsPlaying(false);
          }
        }
        setScanX(scanRef.current);

        // Schedule any new integer columns we've crossed.
        const targetCol = Math.floor(scanRef.current);
        if (targetCol > lastScheduledColRef.current) {
          scheduleColumn(targetCol);
          lastScheduledColRef.current = targetCol;
        }
      }

      rafId = requestAnimationFrame(step);
    }
    rafId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafId);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, isPlaying, bpm, loop, op, op2, morphOn, morphT, maxIter, view, orbitPlayback]);

  function scheduleOrbitSample(orbit, idx) {
    const audio = audioRef.current;
    if (!audio) return;
    const re = orbit.re[idx];
    const im = orbit.im[idx];
    if (!Number.isFinite(re) || !Number.isFinite(im)) return;
    // Map magnitude to frequency over a 2-octave range (220Hz..880Hz).
    const mag = Math.hypot(re, im);
    const [reLo, reHi] = orbit.re_range;
    const [imLo, imHi] = orbit.im_range;
    const magMax = Math.max(
      Math.hypot(reLo, imLo), Math.hypot(reLo, imHi),
      Math.hypot(reHi, imLo), Math.hypot(reHi, imHi), 1e-6
    );
    const t = Math.min(mag / magMax, 1);
    const freq = 220 * Math.pow(4, t);
    const when = audio.ctx.currentTime + 0.02;
    scheduleNote(audio, when, freq, 0.14, 0.05);
  }

  function scheduleColumn(px) {
    const audio = audioRef.current;
    if (!audio) return;
    const now = audio.ctx.currentTime + 0.02;
    const grid = iterGridRef.current;
    for (let row = 0; row < SEQ_ROWS; row++) {
      const py = Math.floor(((row + 0.5) / SEQ_ROWS) * H);
      let it;
      if (grid) {
        it = grid[py * W + px];
      } else {
        const [cr, ci] = pxToComplex(px, py);
        it = iterate(activeOpFn(), cr, ci, maxIter, ESCAPE_R);
      }
      if (it < 0) continue;                      // points-in-set: silent
      if (it >= maxIter - 1) continue;           // ignore escape-cap pixels
      const freq = iterToFreq(it, maxIter);
      scheduleNote(audio, now + row * 0.004, freq, 0.12, 0.04);
    }
  }

  function toggleSequencer() {
    if (isPlaying) {
      setIsPlaying(false);
      return;
    }
    ensureAudio();
    scanRef.current = 0;
    lastScheduledColRef.current = -1;
    orbitIdxRef.current = 0;
    lastScheduledOrbitRef.current = -1;
    setScanX(0);
    setOrbitStep(0);
    setIsPlaying(true);
  }

  // ── Oscilloscope: draw the orbit trace whenever orbit playback is on ─────
  useEffect(() => {
    if (mode !== "sequencer" || !orbitPlayback) return;
    const canvas = oscCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const orbit = ORBIT_BY_OP[op];
    if (!orbit) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }
    const CW = canvas.width;
    const CH = canvas.height;
    ctx.clearRect(0, 0, CW, CH);

    // Background panel
    ctx.fillStyle = "rgba(8,8,12,0.82)";
    ctx.fillRect(0, 0, CW, CH);
    ctx.strokeStyle = "rgba(255,255,255,0.1)";
    ctx.strokeRect(0.5, 0.5, CW - 1, CH - 1);

    // Axes
    const cx = CW / 2;
    const cy = CH / 2;
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    ctx.beginPath();
    ctx.moveTo(0, cy); ctx.lineTo(CW, cy);
    ctx.moveTo(cx, 0); ctx.lineTo(cx, CH);
    ctx.stroke();

    const [reLo, reHi] = orbit.re_range;
    const [imLo, imHi] = orbit.im_range;
    const rePad = Math.max((reHi - reLo) * 0.1, 0.1);
    const imPad = Math.max((imHi - imLo) * 0.1, 0.1);
    const reMin = reLo - rePad, reMax = reHi + rePad;
    const imMin = imLo - imPad, imMax = imHi + imPad;
    const toX = (r) => ((r - reMin) / (reMax - reMin)) * CW;
    const toY = (i) => CH - ((i - imMin) / (imMax - imMin)) * CH;

    // Static trace of the full orbit (faded)
    ctx.strokeStyle = OPERATORS[op].color + "55";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i < orbit.re.length; i++) {
      const x = toX(orbit.re[i]);
      const y = toY(orbit.im[i]);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Active segment up to current orbit step (solid, bright)
    const cur = Math.min(orbitStep, orbit.re.length - 1);
    const TAIL = 48;
    const tailStart = Math.max(0, cur - TAIL);
    ctx.strokeStyle = OPERATORS[op].color;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = tailStart; i <= cur; i++) {
      const x = toX(orbit.re[i]);
      const y = toY(orbit.im[i]);
      if (i === tailStart) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Current point
    const px = toX(orbit.re[cur]);
    const py = toY(orbit.im[cur]);
    ctx.fillStyle = OPERATORS[op].color;
    ctx.beginPath();
    ctx.arc(px, py, 3.5, 0, Math.PI * 2);
    ctx.fill();
  }, [mode, orbitPlayback, orbitStep, op]);

  // ── Misc actions ─────────────────────────────────────────────────────────
  const resetView = () => { setHistory((h) => [...h, view]); setView(DEFAULT_VIEW); };
  const goBack = () => {
    if (history.length === 0) return;
    const prev = history[history.length - 1];
    setHistory((h) => h.slice(0, -1));
    setView(prev);
  };

  const zoom = view.xMax - view.xMin;
  const opColor = OPERATORS[op].color;
  const chordCost = lockedPoints.reduce((a, lp) => a + Math.max(0, Math.round(lp.iter)), 0);

  // ── UI ───────────────────────────────────────────────────────────────────
  return (
    <div style={S.root}>
      <header style={S.header}>
        <span style={S.brand}>monogate</span>
        <span style={S.subBrand}>fractal studio</span>
        <span style={S.formula}>
          {morphOn
            ? `z → (1−t)·${OPERATORS[op].formula} + t·${OPERATORS[op2].formula}`
            : `z → ${OPERATORS[op].formula}`}
        </span>
      </header>

      <div style={S.topBar}>
        {Object.entries(OPERATORS).map(([key, val]) => (
          <button
            key={key}
            onClick={() => setOp(key)}
            style={{
              ...S.opBtn,
              background: op === key ? val.color : "rgba(255,255,255,0.04)",
              color: op === key ? "#08080c" : "rgba(255,255,255,0.5)",
              border: op === key ? "none" : "1px solid rgba(255,255,255,0.08)",
              fontWeight: op === key ? 600 : 400,
            }}
          >
            {val.name}
          </button>
        ))}
        <div style={S.divider} />
        {Object.keys(PALETTES).map((p) => (
          <button
            key={p}
            onClick={() => setPalette(p)}
            style={{
              ...S.palBtn,
              background: palette === p ? "rgba(255,255,255,0.12)" : "transparent",
              color: palette === p ? "#e8e8f0" : "rgba(255,255,255,0.3)",
              borderColor: palette === p ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.06)",
            }}
          >
            {p}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <button
          onClick={() => setMorphOn((v) => !v)}
          style={{
            ...S.palBtn,
            background: morphOn ? "rgba(252,203,82,0.18)" : "transparent",
            color: morphOn ? "#fccb52" : "rgba(255,255,255,0.35)",
            borderColor: morphOn ? "#fccb52" : "rgba(255,255,255,0.08)",
            fontWeight: morphOn ? 600 : 400,
          }}
        >
          morph {morphOn ? "on" : "off"}
        </button>
        <ModeToggle mode={mode} setMode={setMode} />
      </div>

      {morphOn && (
        <div style={S.morphBar}>
          <span style={S.morphLabel}>
            morph: {OPERATORS[op].name} → {OPERATORS[op2].name}
          </span>
          <div style={S.divider} />
          <span style={S.morphLabel}>op2</span>
          {Object.entries(OPERATORS).map(([key, val]) => (
            <button
              key={key}
              onClick={() => setOp2(key)}
              style={{
                ...S.opBtn,
                background: op2 === key ? val.color : "rgba(255,255,255,0.04)",
                color: op2 === key ? "#08080c" : "rgba(255,255,255,0.5)",
                border: op2 === key ? "none" : "1px solid rgba(255,255,255,0.08)",
                fontWeight: op2 === key ? 600 : 400,
                opacity: op === key ? 0.4 : 1,
              }}
              disabled={op === key}
              title={op === key ? "op1 and op2 must differ" : ""}
            >
              {val.name}
            </button>
          ))}
          <div style={S.divider} />
          <span style={S.morphLabel}>t = {morphT.toFixed(2)}</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={morphT}
            onChange={(e) => setMorphT(parseFloat(e.target.value))}
            style={{ ...S.slider, flex: 1, minWidth: 120 }}
          />
          <button
            onClick={() => setMorphT(0)}
            style={S.btn}
            title="snap to op1"
          >
            ←
          </button>
          <button
            onClick={() => setMorphT(0.5)}
            style={S.btn}
            title="snap to middle"
          >
            ½
          </button>
          <button
            onClick={() => setMorphT(1)}
            style={S.btn}
            title="snap to op2"
          >
            →
          </button>
        </div>
      )}

      <div style={S.canvasWrap}>
        <canvas
          ref={canvasRef}
          width={W}
          height={H}
          style={{
            width: "100%",
            height: "100%",
            display: "block",
            cursor: dragStart ? "grabbing" : mode === "audio" ? "crosshair" : "grab",
          }}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
          onMouseEnter={handleMouseEnter}
        />

        {/* Locked-point rings (Audio mode only) */}
        {mode === "audio" && lockedPoints.map((lp) => (
          <div
            key={lp.id}
            style={{
              position: "absolute",
              left: `${(lp.px / W) * 100}%`,
              top: `${(lp.py / H) * 100}%`,
              width: 18, height: 18,
              transform: "translate(-50%, -50%)",
              border: `1.5px solid ${opColor}`,
              borderRadius: "50%",
              pointerEvents: "none",
              boxShadow: `0 0 12px ${opColor}77`,
              background: "rgba(0,0,0,0.15)",
            }}
            title={`iter=${Math.max(0, Math.round(lp.iter))}, freq=${Math.round(lp.freq)}Hz`}
          />
        ))}

        {/* Scan line (Sequencer mode only) */}
        {mode === "sequencer" && (
          <div
            style={{
              position: "absolute",
              left: `${(scanX / W) * 100}%`,
              top: 0, bottom: 0, width: 2,
              background: opColor,
              opacity: 0.75,
              pointerEvents: "none",
              boxShadow: `0 0 6px ${opColor}`,
            }}
          />
        )}

        {/* Orbit oscilloscope overlay (Sequencer + orbit-playback only) */}
        {mode === "sequencer" && orbitPlayback && ORBIT_BY_OP[op] && (
          <div style={S.oscWrap}>
            <div style={S.oscHeader}>
              <span style={{ color: opColor, fontWeight: 600 }}>orbit</span>
              <span style={S.oscMeta}>
                {ORBIT_BY_OP[op].formula} · c={ORBIT_BY_OP[op].c[0]}
                {ORBIT_BY_OP[op].c[1] >= 0 ? "+" : ""}
                {ORBIT_BY_OP[op].c[1]}i
              </span>
              {SHARKOVSKII_OPS.includes(op) && (
                <span style={S.sharkBadge}>Sharkovskii · period 3</span>
              )}
              {ORBIT_BY_OP[op].period && ORBIT_BY_OP[op].period > 1 &&
                !SHARKOVSKII_OPS.includes(op) && (
                <span style={S.periodBadge}>
                  period {ORBIT_BY_OP[op].period}
                </span>
              )}
            </div>
            <canvas
              ref={oscCanvasRef}
              width={260}
              height={140}
              style={S.oscCanvas}
            />
            <div style={S.oscFoot}>
              step {orbitStep} / {ORBIT_BY_OP[op].re.length}
            </div>
          </div>
        )}

        {rendering && <div style={{ ...S.renderTag, color: opColor }}>rendering...</div>}

        <div style={S.gradientBar}>
          <div>
            <div style={S.formulaBig}>
              {morphOn
                ? `z → (1−t)·${OPERATORS[op].formula} + t·${OPERATORS[op2].formula}`
                : `z → ${OPERATORS[op].formula}`}
            </div>
            <div style={S.formulaSub}>
              {morphOn
                ? `${OPERATORS[op].name} → ${OPERATORS[op2].name} · t = ${morphT.toFixed(2)}`
                : `The ${OPERATORS[op].name} Mandelbrot set`}
              {mode === "audio" && lockedPoints.length > 0 && (
                <span style={{ marginLeft: 12, color: opColor }}>
                  · chord cost: {chordCost}n ({lockedPoints.length}/{MAX_LOCKED})
                </span>
              )}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            {mousePos && (
              <div style={S.coord}>c = {mousePos.r} + {mousePos.i}i</div>
            )}
            <div style={S.zoomReadout}>
              zoom: {zoom < 0.01 ? zoom.toExponential(2) : zoom.toFixed(2)} · iter: {maxIter}
            </div>
          </div>
        </div>
      </div>

      <div style={S.bottomBar}>
        <button onClick={resetView} style={S.btn}>reset</button>
        <button onClick={goBack} disabled={history.length === 0} style={{ ...S.btn, opacity: history.length ? 1 : 0.3 }}>back</button>
        <div style={S.divider} />
        <span style={S.label}>iterations</span>
        {ITER_STEPS.map((n) => (
          <button
            key={n}
            onClick={() => setMaxIter(n)}
            style={{
              ...S.btn,
              background: maxIter === n ? "rgba(255,255,255,0.1)" : "transparent",
              color: maxIter === n ? "#e8e8f0" : "rgba(255,255,255,0.3)",
              borderColor: maxIter === n ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.06)",
            }}
          >
            {n}
          </button>
        ))}

        {mode !== "visual" && (
          <>
            <div style={S.divider} />
            <label style={S.label}>♪</label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={masterVol}
              onChange={(e) => setMasterVol(parseFloat(e.target.value))}
              style={S.slider}
            />
            <button
              onClick={() => setReverbOn((r) => !r)}
              style={{
                ...S.btn,
                background: reverbOn ? "rgba(255,255,255,0.12)" : "transparent",
                color: reverbOn ? "#e8e8f0" : "rgba(255,255,255,0.4)",
              }}
            >
              reverb {reverbOn ? "on" : "off"}
            </button>
          </>
        )}

        {mode === "audio" && lockedPoints.length > 0 && (
          <button onClick={clearLocked} style={S.btn}>clear chord</button>
        )}

        {mode === "sequencer" && (
          <>
            <div style={S.divider} />
            <span style={S.label}>bpm {bpm}</span>
            <input
              type="range"
              min={30}
              max={240}
              step={1}
              value={bpm}
              onChange={(e) => setBpm(parseInt(e.target.value, 10))}
              style={S.slider}
            />
            <button
              onClick={() => setLoop((l) => !l)}
              style={{
                ...S.btn,
                background: loop ? "rgba(255,255,255,0.12)" : "transparent",
                color: loop ? "#e8e8f0" : "rgba(255,255,255,0.4)",
              }}
            >
              loop {loop ? "↻" : "→"}
            </button>
            <button
              onClick={() => {
                setOrbitPlayback((v) => !v);
                orbitIdxRef.current = 0;
                lastScheduledOrbitRef.current = -1;
                setOrbitStep(0);
              }}
              disabled={!ORBIT_BY_OP[op]}
              style={{
                ...S.btn,
                background: orbitPlayback ? "rgba(255,255,255,0.12)" : "transparent",
                color: orbitPlayback ? "#e8e8f0" : "rgba(255,255,255,0.4)",
                opacity: ORBIT_BY_OP[op] ? 1 : 0.35,
              }}
              title={ORBIT_BY_OP[op]
                ? "Drive tones from the operator's real orbit instead of the scan line"
                : "No embedded orbit for this operator"}
            >
              orbit {orbitPlayback ? "on" : "off"}
            </button>
            <button
              onClick={toggleSequencer}
              style={{
                ...S.btn,
                background: isPlaying ? opColor : "transparent",
                color: isPlaying ? "#08080c" : opColor,
                borderColor: opColor,
                fontWeight: 600,
              }}
            >
              {isPlaying ? "■ stop" : "▶ play"}
            </button>
          </>
        )}

        <div style={{ flex: 1 }} />
        <span style={S.hint}>{HINT_BY_MODE[mode]}</span>
      </div>
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function ModeToggle({ mode, setMode }) {
  const items = [
    { key: "visual",    label: "visual" },
    { key: "audio",     label: "audio" },
    { key: "sequencer", label: "sequencer" },
  ];
  return (
    <div style={S.modeToggleWrap}>
      {items.map((it) => (
        <button
          key={it.key}
          onClick={() => setMode(it.key)}
          style={{
            ...S.modeBtn,
            background: mode === it.key ? "#e8e8f0" : "transparent",
            color: mode === it.key ? "#08080c" : "rgba(255,255,255,0.55)",
            fontWeight: mode === it.key ? 600 : 400,
          }}
        >
          {it.label}
        </button>
      ))}
    </div>
  );
}

const HINT_BY_MODE = {
  visual: "scroll to zoom · drag to pan · 8 operators · 4 palettes",
  audio: "hover to hear · click to lock · up to 6 tones · drag to pan",
  sequencer: "scan line or orbit drives tones · BPM sets the tempo · DEXL/DEXN carry period-3 Sharkovskii chaos",
};

// ─── Inline styles ───────────────────────────────────────────────────────────

const FONT = "'IBM Plex Mono', 'SF Mono', 'Fira Code', monospace";

const S = {
  root: {
    background: "#08080c",
    color: "#e8e8f0",
    fontFamily: FONT,
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    padding: "20px 24px 12px",
    display: "flex",
    alignItems: "baseline",
    gap: 16,
    flexWrap: "wrap",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  brand: {
    fontSize: 13, fontWeight: 600, letterSpacing: "0.15em",
    textTransform: "uppercase", color: "#4facfe", opacity: 0.9,
  },
  subBrand: { fontSize: 13, color: "rgba(255,255,255,0.3)" },
  formula: { fontSize: 11, color: "rgba(255,255,255,0.15)", marginLeft: "auto" },

  topBar: {
    display: "flex", gap: 6, padding: "12px 24px",
    flexWrap: "wrap", alignItems: "center",
  },
  morphBar: {
    display: "flex", gap: 6, padding: "0 24px 12px",
    flexWrap: "wrap", alignItems: "center",
    borderBottom: "1px solid rgba(252,203,82,0.10)",
    marginBottom: 8,
  },
  morphLabel: {
    fontSize: 10, color: "rgba(252,203,82,0.6)",
    letterSpacing: "0.08em", textTransform: "uppercase",
    fontFamily: FONT, marginRight: 2,
  },
  opBtn: {
    borderRadius: 4, padding: "5px 12px", fontSize: 12,
    fontFamily: "inherit", cursor: "pointer", transition: "all 0.2s",
  },
  palBtn: {
    borderRadius: 4, padding: "5px 10px", fontSize: 11, fontFamily: "inherit",
    cursor: "pointer", textTransform: "capitalize", border: "1px solid",
  },
  divider: { width: 1, height: 20, background: "rgba(255,255,255,0.08)", margin: "0 4px" },

  oscWrap: {
    position: "absolute",
    right: 12, bottom: 46,
    background: "rgba(8,8,12,0.82)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 6,
    padding: "8px 10px",
    pointerEvents: "none",
    fontSize: 10,
    lineHeight: 1.3,
    minWidth: 260,
  },
  oscHeader: {
    display: "flex", alignItems: "center", gap: 8,
    marginBottom: 6, flexWrap: "wrap",
  },
  oscMeta: { color: "rgba(255,255,255,0.45)", fontSize: 9 },
  oscCanvas: { display: "block", borderRadius: 3 },
  oscFoot: { marginTop: 6, color: "rgba(255,255,255,0.35)", fontSize: 9 },
  sharkBadge: {
    background: "#f87171",
    color: "#08080c",
    fontSize: 9,
    fontWeight: 700,
    padding: "2px 6px",
    borderRadius: 3,
    letterSpacing: "0.04em",
  },
  periodBadge: {
    background: "rgba(252,203,82,0.18)",
    color: "#fccb52",
    fontSize: 9,
    fontWeight: 600,
    padding: "2px 6px",
    borderRadius: 3,
    border: "1px solid rgba(252,203,82,0.4)",
  },

  modeToggleWrap: {
    display: "flex", border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: 4, overflow: "hidden",
  },
  modeBtn: {
    padding: "5px 12px", fontSize: 11, fontFamily: "inherit",
    cursor: "pointer", border: "none", textTransform: "lowercase",
    transition: "all 0.15s",
  },

  canvasWrap: {
    flex: 1, position: "relative", margin: "0 24px 12px",
    borderRadius: 6, overflow: "hidden",
    border: "1px solid rgba(255,255,255,0.06)",
    aspectRatio: `${W} / ${H}`,
  },
  renderTag: {
    position: "absolute", top: 12, right: 12,
    background: "rgba(0,0,0,0.7)", borderRadius: 4, padding: "4px 10px",
    fontSize: 11, backdropFilter: "blur(8px)",
  },
  gradientBar: {
    position: "absolute", bottom: 0, left: 0, right: 0,
    padding: "12px 16px",
    background: "linear-gradient(transparent, rgba(0,0,0,0.8))",
    display: "flex", justifyContent: "space-between",
    alignItems: "flex-end", pointerEvents: "none",
  },
  formulaBig: { fontSize: 18, fontWeight: 500, color: "rgba(255,255,255,0.85)", marginBottom: 2 },
  formulaSub: { fontSize: 11, color: "rgba(255,255,255,0.35)" },
  coord: { fontSize: 11, color: "rgba(255,255,255,0.4)", marginBottom: 2 },
  zoomReadout: { fontSize: 11, color: "rgba(255,255,255,0.25)" },

  bottomBar: {
    padding: "8px 24px 16px", display: "flex", gap: 8,
    alignItems: "center", flexWrap: "wrap",
  },
  btn: {
    background: "transparent", color: "rgba(255,255,255,0.5)",
    border: "1px solid rgba(255,255,255,0.08)", borderRadius: 4,
    padding: "4px 12px", fontSize: 11, fontFamily: FONT, cursor: "pointer",
  },
  label: { fontSize: 11, color: "rgba(255,255,255,0.3)", marginRight: 4 },
  slider: { width: 100, accentColor: "#4facfe" },
  hint: { fontSize: 10, color: "rgba(255,255,255,0.15)", letterSpacing: "0.1em" },
};
