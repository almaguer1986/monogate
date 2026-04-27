import { useState } from "react";

const C = {
  bg: "#07080f", surface: "#0d0e1c", border: "#191b2e",
  text: "#cdd0e0", muted: "#4e5168", accent: "#e8a020",
  blue: "#6ab0f5", green: "#5ec47a", red: "#e05060", tag: "#1a1c2e",
};

const PILL = {
  EML: { bg: "rgba(124,111,247,0.14)", border: "#7c6ff7", color: "#a09cf7" },
  EDL: { bg: "rgba(45,212,191,0.10)", border: "#2dd4bf", color: "#2dd4bf" },
  EXL: { bg: "rgba(245,158,11,0.12)", border: "#f59e0b", color: "#f5b435" },
};

// ── Known exact constructions ──────────────────────────────────────────────────
const SOLVED = [
  { fn: "exp(x)",   bestN: 1,  emlN: 1,  op: "EML", note: "eml(x, 1) — identity" },
  { fn: "ln(x)",    bestN: 1,  emlN: 3,  op: "EXL", note: "1-node EXL: exl(1, x)" },
  { fn: "x / y",   bestN: 1,  emlN: 15, op: "EDL", note: "1-node EDL division" },
  { fn: "pow(x,n)", bestN: 3,  emlN: 15, op: "EXL", note: "3-node EXL construction" },
  { fn: "sqrt(x)", bestN: 3,  emlN: 15, op: "EXL", note: "pow(x, 0.5) via EXL" },
  { fn: "x × y",   bestN: 7,  emlN: 13, op: "EDL", note: "7-node EDL construction" },
  { fn: "x + y",   bestN: 11, emlN: 11, op: "EML", note: "11-node EML (no improvement possible for add)" },
];

// ── Open challenges ────────────────────────────────────────────────────────────
const OPEN = [
  {
    id: "sin8",
    label: "sin(x) — 8-term Taylor",
    bestN: 63, emlN: 245, err: "7.7e-7", terms: 8,
    note: "Best known: 8-term Taylor via BEST hybrid. Exact construction from terminal {1} unknown. Right-chain topologies ruled out by Odrzywołek (2026).",
  },
  {
    id: "sin13",
    label: "sin(x) — machine precision",
    bestN: 108, emlN: 420, err: "6.5e-15", terms: 13,
    note: "13-term Taylor reaches machine precision (< 1e-14). Still an approximation — exact EML sin remains an open problem.",
  },
  {
    id: "cos8",
    label: "cos(x) — 8-term Taylor",
    bestN: 63, emlN: 245, err: "7.7e-7", terms: 8,
    note: "Same topology as sin(x). Exact construction also unknown. Affine Leaf Necessity applies (at least one affine leaf required).",
  },
  {
    id: "pi",
    label: "π (constant)",
    bestN: null, emlN: null, err: null, terms: null,
    note: "No finite EML expression for π from terminal {1} is known. Whether π is EML-definable is an open question.",
  },
  {
    id: "i",
    label: "i (imaginary unit)",
    bestN: null, emlN: null, err: null, terms: null,
    note: "Complex unit — outside real domain of EML. Extension to complex EML (where exp/ln operate on ℂ) is open research.",
  },
];

// ── Components ─────────────────────────────────────────────────────────────────
function OpPill({ op }) {
  if (!op) return null;
  const s = PILL[op];
  return (
    <span style={{
      fontSize: 9, padding: "1px 6px", borderRadius: 3,
      background: s.bg, border: `1px solid ${s.border}`, color: s.color,
      fontWeight: 700, letterSpacing: "0.04em", flexShrink: 0,
    }}>{op}</span>
  );
}

function SavingsBadge({ bestN, emlN }) {
  const sav = Math.round((1 - bestN / emlN) * 100);
  if (sav <= 0) return <span style={{ fontSize: 10, color: C.muted }}>—</span>;
  return (
    <span style={{ fontSize: 10, color: C.green, fontWeight: 700 }}>−{sav}%</span>
  );
}

export default function ChallengeBoard() {
  const [expandedId, setExpandedId] = useState(null);

  const btnBase = {
    padding: "5px 12px", fontSize: 10, borderRadius: 4,
    border: `1px solid ${C.border}`, background: "transparent",
    color: C.muted, cursor: "pointer",
    fontFamily: "'Space Mono', monospace", letterSpacing: "0.04em",
  };

  const card = {
    background: C.surface, border: `1px solid ${C.border}`,
    borderRadius: 8, padding: 16, marginBottom: 12,
  };

  const colHeader = {
    fontSize: 9, color: C.muted, textTransform: "uppercase",
    letterSpacing: "0.05em",
  };

  return (
    <div style={{ overflowX: "hidden" }}>

      {/* Header */}
      <div style={{ marginBottom: 18 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: C.accent, marginBottom: 4 }}>
          ✦ Challenge Board
        </div>
        <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.7 }}>
          Shortest known constructions for each math operation using the EML operator family.
          &nbsp;
          <span style={{ color: C.green }}>Solved</span> = exact construction ·{" "}
          <span style={{ color: C.accent }}>Open</span> = best approximation or unsolved
        </div>
      </div>

      {/* ── Solved constructions ── */}
      <div style={card}>
        <div style={{ fontSize: 9, color: C.green, textTransform: "uppercase",
          letterSpacing: "0.06em", marginBottom: 12, fontWeight: 700 }}>
          Solved — exact constructions
        </div>

        {/* Column headers */}
        <div style={{
          display: "grid", gridTemplateColumns: "1fr 44px 56px 56px 56px",
          gap: 8, padding: "0 0 8px", borderBottom: `1px solid ${C.border}`,
        }}>
          <span style={colHeader}>Function</span>
          <span style={colHeader}>Op</span>
          <span style={{ ...colHeader, textAlign: "right" }}>BEST</span>
          <span style={{ ...colHeader, textAlign: "right" }}>EML</span>
          <span style={{ ...colHeader, textAlign: "right" }}>Savings</span>
        </div>

        {SOLVED.map((row, i) => (
          <div key={row.fn} style={{
            display: "grid", gridTemplateColumns: "1fr 44px 56px 56px 56px",
            alignItems: "center", gap: 8,
            padding: "8px 0",
            borderBottom: i < SOLVED.length - 1 ? `1px solid ${C.border}` : "none",
          }}>
            <div>
              <span style={{ fontSize: 11, color: C.text,
                fontFamily: "'Space Mono', monospace" }}>
                {row.fn}
              </span>
              <div style={{ fontSize: 9, color: C.muted, marginTop: 2 }}>{row.note}</div>
            </div>
            <OpPill op={row.op} />
            <span style={{ fontSize: 12, fontWeight: 700, color: C.accent, textAlign: "right" }}>
              {row.bestN}n
            </span>
            <span style={{
              fontSize: 11, textAlign: "right", color: C.muted,
              textDecoration: row.bestN < row.emlN ? "line-through" : "none",
            }}>
              {row.emlN}n
            </span>
            <div style={{ textAlign: "right" }}>
              <SavingsBadge bestN={row.bestN} emlN={row.emlN} />
            </div>
          </div>
        ))}
      </div>

      {/* ── Open challenges ── */}
      <div style={card}>
        <div style={{ fontSize: 9, color: C.accent, textTransform: "uppercase",
          letterSpacing: "0.06em", marginBottom: 12, fontWeight: 700 }}>
          Open challenges
        </div>

        {OPEN.map((row, i) => {
          const isExpanded = expandedId === row.id;
          const hasCounts  = row.bestN !== null;

          return (
            <div key={row.id} style={{
              padding: "12px 0",
              borderBottom: i < OPEN.length - 1 ? `1px solid ${C.border}` : "none",
            }}>
              {/* Row header */}
              <div style={{ display: "flex", justifyContent: "space-between",
                alignItems: "flex-start", flexWrap: "wrap", gap: 8 }}>

                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: C.text,
                    fontFamily: "'Space Mono', monospace" }}>
                    {row.label}
                  </span>
                  <span style={{
                    fontSize: 9, padding: "1px 7px", borderRadius: 3,
                    background: "rgba(232,160,32,0.10)",
                    border: "1px solid rgba(232,160,32,0.35)",
                    color: C.accent,
                  }}>
                    OPEN
                  </span>
                </div>

                {hasCounts && (
                  <div style={{ display: "flex", alignItems: "baseline", gap: 5, flexShrink: 0 }}>
                    <span style={{ fontSize: 16, fontWeight: 700, color: C.accent }}>
                      {row.bestN}n
                    </span>
                    <span style={{ fontSize: 9, color: C.muted }}>BEST</span>
                    <span style={{ fontSize: 11, color: C.muted, textDecoration: "line-through" }}>
                      {row.emlN}n
                    </span>
                    <span style={{ fontSize: 10, color: C.green, fontWeight: 700 }}>
                      −{Math.round((1 - row.bestN / row.emlN) * 100)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Meta row */}
              {row.err && (
                <div style={{ fontSize: 9, color: C.muted, marginTop: 4 }}>
                  {row.terms} Taylor terms ·{" "}
                  max error:{" "}
                  <span style={{
                    color: parseFloat(row.err) < 1e-10 ? C.green : C.muted,
                  }}>
                    {row.err}
                  </span>
                </div>
              )}

              {/* Expand/collapse note */}
              <button
                onClick={() => setExpandedId(isExpanded ? null : row.id)}
                style={{ ...btnBase, padding: "2px 0", fontSize: 9, border: "none",
                  color: C.muted, marginTop: 6, background: "transparent" }}>
                {isExpanded ? "▼ less" : "▶ details"}
              </button>

              {isExpanded && (
                <div style={{
                  marginTop: 8, padding: "10px 12px", borderRadius: 6,
                  background: C.bg, border: `1px solid ${C.border}`,
                  fontSize: 10, color: C.muted, lineHeight: 1.7,
                }}>
                  {row.note}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Submit CTA ── */}
      <div style={{
        ...card, marginBottom: 8,
        borderColor: "rgba(232,160,32,0.25)",
        background: "rgba(232,160,32,0.04)",
      }}>
        <div style={{ fontSize: 11, color: C.text, marginBottom: 6, fontWeight: 600 }}>
          Beat a record? Found a shorter construction?
        </div>
        <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.7, marginBottom: 14 }}>
          Submit via GitHub Issues with: the EML expression tree, node count,
          and a proof or numeric verification script.
        </div>
        <a
          href="https://github.com/agent-maestro/monogate/issues/new?title=New+construction+for+[fn]&labels=construction"
          target="_blank" rel="noreferrer"
          style={{
            ...btnBase,
            color: C.accent, borderColor: "rgba(232,160,32,0.4)",
            textDecoration: "none",
            display: "inline-flex", alignItems: "center", gap: 6,
          }}>
          Submit your construction ↗
        </a>
      </div>

      {/* Footer note */}
      <div style={{ fontSize: 9, color: C.muted, lineHeight: 1.7 }}>
        Node counts use BEST hybrid routing (optimal operator per op) vs pure EML baseline.
        "Exact" = zero approximation error. Open problems per Odrzywołek (2026) — arXiv:2603.21852v2.
      </div>
    </div>
  );
}
