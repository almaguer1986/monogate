"use client";

import { useState, useRef, useCallback } from "react";
import {
  runExhaustive,
  totalTrees,
  TARGETS,
  type TargetKey,
  type SearchProgress,
  type SearchController,
} from "@/lib/complex-search";

const C = {
  bg: "#08090e", surface: "#0d0f18", surface2: "#12151f",
  border: "#1c1f2e", border2: "#252836",
  text: "#d4d4d4", muted: "#4a4d62",
  orange: "#e8a020", blue: "#6ab0f5", green: "#4ade80", red: "#f87171",
};

const KEYS: TargetKey[] = ["i", "pi", "neg_i_pi", "e", "zero", "sqrt2"];

const CATALAN = [1,1,2,5,14,42,132,429,1430,4862,16796,58786,208012];

function fmt(n: number): string {
  return n.toLocaleString("en-US");
}

function fmtDist(d: number): string {
  if (d === Infinity) return "—";
  if (d < 1e-14) return "< 1e−14";
  return d.toExponential(3);
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: 10, color: C.orange, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 12 }}>
      {children}
    </div>
  );
}

function Stat({ label, value, color = C.text }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 13, color, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

type Phase = "idle" | "running" | "done";

export default function ExhaustiveClient() {
  const [target,   setTarget]   = useState<TargetKey>("i");
  const [maxNodes, setMaxNodes] = useState(8);
  const [phase,    setPhase]    = useState<Phase>("idle");
  const [progress, setProgress] = useState<SearchProgress | null>(null);
  const ctrlRef = useRef<SearchController | null>(null);

  const total = totalTrees(maxNodes);

  const handleSearch = useCallback(() => {
    if (phase === "running") {
      ctrlRef.current?.stop();
      setPhase("done");
      return;
    }

    setPhase("running");
    setProgress(null);

    ctrlRef.current = runExhaustive(
      target,
      maxNodes,
      (p) => setProgress({ ...p }),
      (p) => { setProgress({ ...p }); setPhase("done"); },
    );
  }, [phase, target, maxNodes]);

  const pct   = progress ? Math.min(100, (progress.evaluated / progress.total) * 100) : 0;
  const found = progress?.found ?? false;
  const meta  = TARGETS[target];

  return (
    <div>
      {/* Controls */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "20px 24px", marginBottom: 24 }}>

        {/* Target selector */}
        <div style={{ marginBottom: 20 }}>
          <SectionLabel>Target value</SectionLabel>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {KEYS.map((k) => {
              const t = TARGETS[k];
              const active = k === target;
              return (
                <button key={k}
                  onClick={() => { if (phase !== "running") { setTarget(k); setProgress(null); } }}
                  disabled={phase === "running"}
                  style={{
                    padding: "7px 16px", fontSize: 12, fontWeight: 700,
                    background: active ? "rgba(232,160,32,0.15)" : "transparent",
                    border: `1px solid ${active ? C.orange : C.border2}`,
                    color: active ? C.orange : C.muted,
                    borderRadius: 4, cursor: phase === "running" ? "not-allowed" : "pointer",
                    fontFamily: "'Space Mono', monospace",
                  }}
                >
                  {t.label}
                  {t.known && (
                    <span style={{ marginLeft: 6, fontSize: 9, color: C.green, fontWeight: 400 }}>
                      ✓{t.known}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Max nodes slider */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
            <SectionLabel>Max nodes — {maxNodes}</SectionLabel>
            <span style={{ fontSize: 10, color: C.muted }}>
              ≤ {fmt(total)} trees
              {maxNodes < 12 && (
                <span style={{ color: C.muted }}> · +{fmt(CATALAN[maxNodes + 1])} at {maxNodes + 1}</span>
              )}
            </span>
          </div>
          <input
            type="range" min={1} max={12} value={maxNodes}
            onChange={(e) => { if (phase !== "running") { setMaxNodes(Number(e.target.value)); setProgress(null); } }}
            disabled={phase === "running"}
            style={{
              width: "100%", height: 3, borderRadius: 2,
              background: C.surface2, outline: "none", cursor: "pointer",
              accentColor: C.orange,
            }}
          />
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: C.muted, marginTop: 5 }}>
            <span>1</span>
            {[3,5,7,9,11].map(n => <span key={n}>{n}</span>)}
            <span>12</span>
          </div>
        </div>

        {/* Sanity check note */}
        {meta.known && (
          <div style={{
            padding: "10px 14px", marginBottom: 16, borderRadius: 6,
            background: "rgba(74,222,128,0.05)", border: `1px solid ${C.green}`,
            fontSize: 11, color: C.muted, lineHeight: 1.8,
          }}>
            <span style={{ color: C.green, fontWeight: 700 }}>Known construction:</span>{" "}
            {TARGETS[target].label} is constructible in {meta.known}.
            {maxNodes < parseInt(meta.known) && (
              <span style={{ color: C.red }}>{" "}Increase max nodes to find it.</span>
            )}
          </div>
        )}

        {/* SEARCH / STOP */}
        <button onClick={handleSearch} style={{
          padding: "10px 32px", fontSize: 12, fontWeight: 700,
          letterSpacing: "0.06em", textTransform: "uppercase",
          background: phase === "running" ? "rgba(248,113,113,0.12)" : "rgba(232,160,32,0.14)",
          border: `1px solid ${phase === "running" ? C.red : C.orange}`,
          color: phase === "running" ? C.red : C.orange,
          borderRadius: 4, cursor: "pointer",
          fontFamily: "'Space Mono', monospace",
        }}>
          {phase === "running" ? "■  STOP" : "▶  SEARCH"}
        </button>
      </div>

      {/* Progress + results */}
      {(phase !== "idle" || progress) && progress && (
        <>
          {/* CONSTRUCTION FOUND banner */}
          {found && (
            <div style={{
              padding: "14px 20px", marginBottom: 16, borderRadius: 8,
              background: "rgba(74,222,128,0.07)", border: `1px solid ${C.green}`,
              fontSize: 14, fontWeight: 700, color: C.green, letterSpacing: "0.04em",
            }}>
              ✓  CONSTRUCTION FOUND — {progress.bestNodes} node{progress.bestNodes !== 1 ? "s" : ""}
            </div>
          )}

          {/* Progress bar */}
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "20px 24px", marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: C.muted, marginBottom: 8 }}>
              <span>{fmt(progress.evaluated)} / {fmt(progress.total)} trees</span>
              <span>{pct.toFixed(1)}%</span>
            </div>
            <div style={{ height: 4, background: C.surface2, borderRadius: 2, marginBottom: 16, overflow: "hidden" }}>
              <div style={{
                height: "100%", borderRadius: 2,
                width: `${pct}%`,
                background: found ? C.green : phase === "running" ? C.orange : C.muted,
                transition: "width 0.1s ease",
              }} />
            </div>

            {/* Stats */}
            <div style={{ display: "flex", gap: 28, flexWrap: "wrap" }}>
              <Stat
                label="Best distance"
                value={fmtDist(progress.bestDist)}
                color={found ? C.green : progress.bestDist < 1 ? C.orange : C.text}
              />
              <Stat label="Threshold" value="< 1e−8" color={C.muted} />
              <Stat label="Errors (ln 0)" value={fmt(progress.errors)} color={C.muted} />
              <Stat label="Elapsed" value={`${(progress.elapsed / 1000).toFixed(1)}s`} color={C.muted} />
            </div>
          </div>

          {/* Best match card */}
          {progress.bestExpr && (
            <div style={{
              background: found ? "rgba(74,222,128,0.05)" : C.surface,
              border: `1px solid ${found ? C.green : C.border}`,
              borderRadius: 8, padding: "20px 24px", marginBottom: 16,
            }}>
              <SectionLabel>{found ? "Construction" : "Best match so far"}</SectionLabel>

              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>
                  Expression
                </div>
                <div style={{
                  fontFamily: "monospace", fontSize: 11,
                  color: found ? C.green : C.orange,
                  background: C.surface2, padding: "12px 16px", borderRadius: 6,
                  wordBreak: "break-all", lineHeight: 1.8,
                }}>
                  {progress.bestExpr}
                </div>
              </div>

              <div style={{ display: "flex", gap: 28, flexWrap: "wrap" }}>
                <Stat label="Value" value={progress.bestValue} color={found ? C.green : C.blue} />
                <Stat label="Target" value={meta.label} color={C.muted} />
                <Stat label="Distance" value={fmtDist(progress.bestDist)} color={found ? C.green : C.text} />
                <Stat label="Nodes" value={String(progress.bestNodes)} color={C.text} />
              </div>
            </div>
          )}

          {/* Live feed */}
          {progress.feed.length > 0 && (
            <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
              <div style={{
                display: "grid", gridTemplateColumns: "40px 1fr 100px 90px",
                padding: "7px 14px", borderBottom: `1px solid ${C.border}`,
                fontSize: 9, color: C.muted, letterSpacing: "0.06em", textTransform: "uppercase",
              }}>
                {["N", "Expression", "Value", "Distance"].map(h => <div key={h}>{h}</div>)}
              </div>
              {[...progress.feed].reverse().map((row, i) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "40px 1fr 100px 90px",
                  padding: "6px 14px", fontSize: 10,
                  borderBottom: i < progress.feed.length - 1 ? `1px solid ${C.border}` : "none",
                  background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.012)",
                  alignItems: "center",
                }}>
                  <div style={{ color: C.muted }}>{row.nodes}</div>
                  <div style={{
                    color: C.muted, fontSize: 9, overflow: "hidden",
                    textOverflow: "ellipsis", whiteSpace: "nowrap", paddingRight: 8,
                  }}>
                    {row.expr.length > 60 ? row.expr.slice(0, 57) + "…" : row.expr}
                  </div>
                  <div style={{ color: C.blue, fontSize: 10 }}>{row.value}</div>
                  <div style={{
                    color: row.dist < 1e-8 ? C.green : row.dist < 0.1 ? C.orange : C.muted,
                    fontSize: 10,
                  }}>
                    {fmtDist(row.dist)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Idle explanation */}
      {phase === "idle" && !progress && (
        <div style={{ background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "20px 24px" }}>
          <SectionLabel>How it works</SectionLabel>
          <div style={{ display: "flex", flexDirection: "column", gap: 12, fontSize: 11, color: C.muted, lineHeight: 1.8 }}>
            <div>
              <span style={{ color: C.text }}>1. Exhaustive enumeration.</span>{"  "}
              Every binary tree with 0 through N internal{" "}
              <span style={{ color: C.orange }}>eml</span> nodes is generated
              exactly once. Leaves always evaluate to{" "}
              <span style={{ color: C.orange }}>1</span>. The total is the sum
              of Catalan numbers C(0) + … + C(N).
            </div>
            <div>
              <span style={{ color: C.text }}>2. Complex evaluation.</span>{"  "}
              Each tree is evaluated over ℂ using strict principal-branch ln:
              arg(z) ∈ (−π, π]. If{" "}
              <span style={{ color: C.orange }}>ln(0)</span> is reached at any
              intermediate node, the tree is skipped (counted as an error).
            </div>
            <div>
              <span style={{ color: C.text }}>3. Distance to target.</span>{"  "}
              The result is compared to the target value by{" "}
              <span style={{ color: C.orange }}>|z − target|</span> in ℂ.
              A distance below 1×10⁻⁸ counts as a construction found.
            </div>
            <div>
              <span style={{ color: C.text }}>4. Deterministic.</span>{"  "}
              Unlike gradient descent, this search is exhaustive: if no
              construction exists up to N nodes under this grammar, it will
              not be found. Sanity checks: e (1 node), 0 (3 nodes), −iπ (11 nodes).
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
