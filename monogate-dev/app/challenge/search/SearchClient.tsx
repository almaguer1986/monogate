"use client";

import { useState, useRef, useCallback } from "react";
import {
  runSearch,
  TARGET_META,
  type TargetKey,
  type SearchProgress,
  type SearchResult,
} from "@/lib/eml-search";
import { autoSubmit } from "./actions";
import ExhaustiveClient from "./ExhaustiveClient";

const C = {
  bg: "#08090e", surface: "#0d0f18", surface2: "#12151f",
  border: "#1c1f2e", border2: "#252836",
  text: "#d4d4d4", muted: "#4a4d62",
  orange: "#e8a020", blue: "#6ab0f5", green: "#4ade80", red: "#f87171",
};

type Mode = "exhaustive" | "gradient";
type Phase = "idle" | "running" | "done";
type SubmitState = "idle" | "submitting" | "done" | "error";

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div>
      <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 15, color, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: 10, color: C.orange, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 12 }}>
      {children}
    </div>
  );
}

export default function SearchClient() {
  const [mode, setMode]               = useState<Mode>("exhaustive");
  const [target, setTarget]           = useState<TargetKey>("sin");
  const [depth, setDepth]             = useState(3);
  const [phase, setPhase]             = useState<Phase>("idle");
  const [progress, setProgress]       = useState<SearchProgress | null>(null);
  const [result, setResult]           = useState<SearchResult | null | undefined>(undefined);
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const ctrlRef = useRef<{ stop: () => void } | null>(null);

  const handleRun = useCallback(async () => {
    if (phase === "running") {
      ctrlRef.current?.stop();
      setPhase("done");
      return;
    }

    setPhase("running");
    setProgress(null);
    setResult(undefined);
    setSubmitState("idle");
    setSubmitError(null);

    ctrlRef.current = runSearch(
      target,
      depth,
      (p: SearchProgress) => setProgress(p),
      async (r: SearchResult | null) => {
        setResult(r);
        setPhase("done");

        if (r && r.loss < 1e-10) {
          setSubmitState("submitting");
          try {
            const res = await autoSubmit(TARGET_META[target].challengeId, r.expression);
            if (res.success) {
              setSubmitState("done");
            } else {
              setSubmitState("error");
              setSubmitError(res.error ?? "Submit failed.");
            }
          } catch {
            setSubmitState("error");
            setSubmitError("Network error during auto-submit.");
          }
        }
      }
    );
  }, [target, depth, phase]);

  const pct     = progress ? Math.min(100, (progress.iteration / 10_000) * 100) : 0;
  const meta    = TARGET_META[target];
  const found   = result != null && result.loss < 1e-10;
  const isI     = target === "i";

  return (
    <div style={{ background: C.bg, minHeight: "100vh", maxWidth: 760, margin: "0 auto", padding: "0 16px 60px" }}>

      {/* Header */}
      <header style={{ borderBottom: `1px solid ${C.border}`, padding: "28px 0 22px", marginBottom: 36 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>
              <a href="/" style={{ color: C.muted }}>monogate.dev</a>
              {" / search"}
            </div>
            <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em" }}>
              {mode === "exhaustive" ? "EML Tree Enumerator" : "EML Symbolic Regression"}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            {(["exhaustive", "gradient"] as Mode[]).map((m) => (
              <button key={m} onClick={() => setMode(m)} style={{
                padding: "5px 14px", fontSize: 10, fontWeight: 700,
                letterSpacing: "0.06em", textTransform: "uppercase",
                background: mode === m ? "rgba(232,160,32,0.12)" : "transparent",
                border: `1px solid ${mode === m ? C.orange : C.border2}`,
                color: mode === m ? C.orange : C.muted,
                borderRadius: 4, cursor: "pointer",
                fontFamily: "'Space Mono', monospace",
              }}>
                {m === "exhaustive" ? "Exhaustive" : "Gradient"}
              </button>
            ))}
          </div>
        </div>
        <div style={{ marginTop: 10, fontSize: 11, color: C.muted, lineHeight: 1.8, maxWidth: 560 }}>
          {mode === "exhaustive"
            ? "Exhaustive enumeration of all EML trees up to N nodes, evaluated over ℂ. Deterministic — finds proven constructions or proves none exist up to the chosen depth."
            : "Gradient descent over random EML tree topologies. Searches for a construction that equals the target function at all test points. These are open problems — convergence is not guaranteed."
          }
        </div>
      </header>

      {/* Exhaustive mode */}
      {mode === "exhaustive" && <ExhaustiveClient />}

      {/* Gradient mode */}
      {mode === "gradient" && <>

      {/* Control panel */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "20px 24px", marginBottom: 24 }}>

        {/* Target */}
        <div style={{ marginBottom: 20 }}>
          <SectionLabel>Target function</SectionLabel>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {(["sin", "cos", "pi", "i"] as TargetKey[]).map((k) => (
              <button
                key={k}
                onClick={() => {
                  if (phase === "running") return;
                  setTarget(k);
                  setPhase("idle");
                  setResult(undefined);
                  setProgress(null);
                }}
                disabled={phase === "running"}
                style={{
                  padding: "7px 16px", fontSize: 12, fontWeight: 700,
                  background: target === k ? "rgba(232,160,32,0.15)" : "transparent",
                  border: `1px solid ${target === k ? C.orange : C.border2}`,
                  color: target === k ? C.orange : C.muted,
                  borderRadius: 4, cursor: phase === "running" ? "not-allowed" : "pointer",
                  fontFamily: "'Space Mono', monospace",
                }}
              >
                {TARGET_META[k].label}
              </button>
            ))}
          </div>
        </div>

        {/* Depth */}
        <div style={{ marginBottom: 20 }}>
          <SectionLabel>Max tree depth</SectionLabel>
          <div style={{ display: "flex", gap: 8 }}>
            {[2, 3, 4].map((d) => (
              <button
                key={d}
                onClick={() => { if (phase !== "running") setDepth(d); }}
                disabled={phase === "running"}
                style={{
                  padding: "7px 22px", fontSize: 12, fontWeight: 700,
                  background: depth === d ? "rgba(106,176,245,0.12)" : "transparent",
                  border: `1px solid ${depth === d ? C.blue : C.border2}`,
                  color: depth === d ? C.blue : C.muted,
                  borderRadius: 4, cursor: phase === "running" ? "not-allowed" : "pointer",
                  fontFamily: "'Space Mono', monospace",
                }}
              >
                {d}
              </button>
            ))}
          </div>
          <div style={{ fontSize: 10, color: C.muted, marginTop: 8, lineHeight: 1.7 }}>
            Deeper trees have more parameters. Depth 3 is a good starting point.
            Each random restart samples a new topology.
          </div>
        </div>

        {/* i warning */}
        {isI && (
          <div style={{
            padding: "10px 14px", marginBottom: 16, borderRadius: 6,
            background: "rgba(248,113,113,0.06)", border: `1px solid ${C.red}`,
            fontSize: 11, color: C.muted, lineHeight: 1.8,
          }}>
            <span style={{ color: C.red, fontWeight: 700 }}>i</span> is the imaginary unit.
            Under strict principal-branch grammar with real arithmetic, no EML tree can
            evaluate to i. This is the deepest open problem — search is disabled.
            See{" "}
            <a href="/challenge/i-strict" style={{ color: C.red }}>the challenge page</a> for context.
          </div>
        )}

        {/* Run / Stop button */}
        <button
          onClick={handleRun}
          disabled={isI}
          style={{
            padding: "10px 32px", fontSize: 12, fontWeight: 700,
            letterSpacing: "0.06em", textTransform: "uppercase",
            background: phase === "running"
              ? "rgba(248,113,113,0.12)"
              : isI
              ? "transparent"
              : "rgba(232,160,32,0.14)",
            border: `1px solid ${phase === "running" ? C.red : isI ? C.border2 : C.orange}`,
            color: phase === "running" ? C.red : isI ? C.muted : C.orange,
            borderRadius: 4,
            cursor: isI ? "not-allowed" : "pointer",
            fontFamily: "'Space Mono', monospace",
          }}
        >
          {phase === "running" ? "■  STOP" : "▶  RUN"}
        </button>
      </div>

      {/* Progress panel */}
      {(phase === "running" || (phase === "done" && progress != null)) && (
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "20px 24px", marginBottom: 24 }}>
          <SectionLabel>Search progress</SectionLabel>

          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: 11, color: C.muted }}>
            <span>Iteration {progress?.iteration ?? 0} / 10 000</span>
            <span>{pct.toFixed(0)}%</span>
          </div>

          <div style={{ height: 4, background: C.surface2, borderRadius: 2, marginBottom: 18, overflow: "hidden" }}>
            <div style={{
              height: "100%", borderRadius: 2,
              width: `${pct}%`,
              background: found ? C.green : phase === "running" ? C.orange : C.muted,
              transition: "width 0.15s ease",
            }} />
          </div>

          <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
            <Stat
              label="Best loss"
              value={!progress || progress.bestLoss === Infinity ? "—" : progress.bestLoss.toExponential(3)}
              color={progress && progress.bestLoss < 1e-10 ? C.green : C.text}
            />
            <Stat label="Target" value="< 1×10⁻¹⁰" color={C.muted} />
            {phase === "running" && (
              <Stat label="Restarts" value={String(Math.floor((progress?.iteration ?? 0) / 500))} color={C.muted} />
            )}
          </div>
        </div>
      )}

      {/* Result panel */}
      {phase === "done" && result !== undefined && (
        <div style={{
          background: found ? "rgba(74,222,128,0.05)" : C.surface,
          border: `1px solid ${found ? C.green : C.border}`,
          borderRadius: 8, padding: "20px 24px",
        }}>
          {found && result ? (
            <>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.green, marginBottom: 16 }}>
                ✓  Valid construction found
              </div>

              <div style={{ marginBottom: 18 }}>
                <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>
                  Expression
                </div>
                <div style={{
                  fontFamily: "monospace", fontSize: 11, color: C.blue,
                  background: C.surface2, padding: "12px 16px", borderRadius: 6,
                  wordBreak: "break-all", lineHeight: 1.8,
                }}>
                  {result.expression}
                </div>
              </div>

              <div style={{ display: "flex", gap: 28, marginBottom: 18, flexWrap: "wrap" }}>
                <Stat label="Nodes" value={String(result.nodes)} color={C.text} />
                <Stat label="Depth" value={String(result.depth)} color={C.text} />
                <Stat label="Loss" value={result.loss.toExponential(3)} color={C.green} />
              </div>

              {submitState === "submitting" && (
                <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.7 }}>
                  Submitting to leaderboard…
                </div>
              )}
              {submitState === "done" && (
                <div style={{ fontSize: 11, color: C.green, lineHeight: 1.7 }}>
                  ✓ Recorded on the leaderboard as <span style={{ color: C.text }}>search-bot</span>.{" "}
                  <a href={`/challenge/${meta.challengeId}`} style={{ color: C.green }}>
                    View leaderboard →
                  </a>
                </div>
              )}
              {submitState === "error" && (
                <div style={{ fontSize: 11, color: C.red, lineHeight: 1.7 }}>
                  Auto-submit failed: {submitError}
                </div>
              )}
            </>
          ) : (
            <>
              <div style={{ fontSize: 13, fontWeight: 700, color: C.muted, marginBottom: 12 }}>
                No construction found
              </div>
              <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.8, marginBottom: 8 }}>
                Searched {progress?.iteration ?? 10_000} iterations at depth {depth}.
              </div>
              <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.8, marginBottom: 8 }}>
                Best loss:{" "}
                <span style={{ color: C.text }}>
                  {progress && progress.bestLoss < Infinity
                    ? progress.bestLoss.toExponential(4)
                    : "no valid evaluation — all trees hit ln(0)"}
                </span>
                {" "}&nbsp; Target: &lt; 1×10⁻¹⁰.
              </div>
              <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.8, marginBottom: 18 }}>
                This is expected —{" "}
                <a href={`/challenge/${meta.challengeId}`} style={{ color: C.orange }}>
                  {meta.label}
                </a>{" "}
                is an open problem. No EML construction is known under strict
                principal-branch grammar. Try depth 4 or run again with a different
                random seed.
              </div>
              {result && (
                <div style={{ marginBottom: 18 }}>
                  <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>
                    Best attempt
                  </div>
                  <div style={{
                    fontFamily: "monospace", fontSize: 10, color: C.muted,
                    background: C.surface2, padding: "10px 14px", borderRadius: 6,
                    wordBreak: "break-all", lineHeight: 1.7,
                  }}>
                    {result.expression}
                  </div>
                </div>
              )}
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <button
                  onClick={handleRun}
                  style={{
                    padding: "8px 22px", fontSize: 11, fontWeight: 700,
                    background: "rgba(232,160,32,0.12)", border: `1px solid ${C.orange}`,
                    color: C.orange, borderRadius: 4, cursor: "pointer",
                    fontFamily: "'Space Mono', monospace",
                  }}
                >
                  ▶ Run again
                </button>
                <a
                  href={`/challenge/${meta.challengeId}`}
                  style={{
                    display: "inline-flex", alignItems: "center",
                    padding: "8px 22px", fontSize: 11,
                    border: `1px solid ${C.border2}`, color: C.muted, borderRadius: 4,
                  }}
                >
                  View challenge →
                </a>
              </div>
            </>
          )}
        </div>
      )}

      {/* How it works — shown only when idle */}
      {phase === "idle" && (
        <div style={{ background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8, padding: "20px 24px" }}>
          <SectionLabel>How it works</SectionLabel>
          <div style={{ display: "flex", flexDirection: "column", gap: 12, fontSize: 11, color: C.muted, lineHeight: 1.8 }}>
            <div>
              <span style={{ color: C.text }}>1. Random tree.</span>{"  "}
              A random EML tree topology is sampled at the chosen depth.
              Every leaf is a learnable scalar weight initialized to a positive value.
            </div>
            <div>
              <span style={{ color: C.text }}>2. Gradient descent.</span>{"  "}
              Adam optimizer minimizes MSE between tree output and target at 10 test points.
              Gradients flow through{" "}
              <span style={{ color: C.orange }}>eml(x, y) = exp(x) − ln(y)</span>{" "}
              via reverse-mode automatic differentiation.
            </div>
            <div>
              <span style={{ color: C.text }}>3. Random restarts.</span>{"  "}
              Every 500 iterations, a new random tree is sampled. The globally best
              weights and loss are tracked across all restarts.
            </div>
            <div>
              <span style={{ color: C.text }}>4. Strict grammar.</span>{"  "}
              ln(y) returns NaN if y ≤ 0. Ill-conditioned evaluations are skipped —
              no extended-reals shortcut. Same constraints as manual submissions.
            </div>
            <div>
              <span style={{ color: C.text }}>5. Auto-submit.</span>{"  "}
              If loss falls below 1×10⁻¹⁰, the expression is automatically submitted
              to the challenge leaderboard as{" "}
              <span style={{ color: C.text }}>search-bot</span>.
            </div>
          </div>
        </div>
      )}

      </>}

      <footer style={{
        marginTop: 48, paddingTop: 20, borderTop: `1px solid ${C.border}`,
        display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10,
        fontSize: 10, color: C.muted,
      }}>
        <a href="/" style={{ color: C.muted }}>← All challenges</a>
        <a href="/how-to-submit" style={{ color: C.muted }}>Submit manually →</a>
      </footer>
    </div>
  );
}
