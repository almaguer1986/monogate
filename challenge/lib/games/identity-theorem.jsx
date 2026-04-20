import { useState } from "react";

const PROOF_STEPS = [
  {
    step: 1,
    input: "eml(x, 1)",
    expansion: "exp(x) − ln(1)",
    simplification: "exp(x) − 0",
    result: "exp(x)",
    explanation: "ln(1) = 0, so the second term vanishes. You get the exponential.",
    color: "#06B6D4",
  },
  {
    step: 2,
    input: "eml(1, exp(x))",
    expansion: "exp(1) − ln(exp(x))",
    simplification: "e − x",
    result: "e − x",
    explanation: "exp(1) = e. ln(exp(x)) = x. The exponential and logarithm cancel, leaving e − x.",
    color: "#8B5CF6",
  },
  {
    step: 3,
    input: "eml(e − x, 1)",
    expansion: "exp(e − x) − ln(1)",
    simplification: "exp(e − x)",
    result: "exp(e − x)",
    explanation: "Same as step 1: ln(1) = 0. You're left with exp(e − x).",
    color: "#EC4899",
  },
  {
    step: 4,
    input: "eml(1, exp(e − x))",
    expansion: "exp(1) − ln(exp(e − x))",
    simplification: "e − (e − x)",
    result: "x",
    explanation: "exp(1) = e. ln(exp(e−x)) = e−x. Then e − (e − x) = x. The identity function. Four nodes. □",
    color: "#10B981",
  },
];

// Test values to verify
const TEST_VALS = [0.5, 1.0, 1.5, 2.0, 2.718, 3.14159, 0.001, 42];

function verify(x) {
  // eml(1, eml(eml(1, eml(x, 1)), 1))
  const s1 = Math.exp(x) - Math.log(1);        // eml(x, 1) = exp(x)
  const s2 = Math.exp(1) - Math.log(s1);        // eml(1, exp(x)) = e - x
  const s3 = Math.exp(s2) - Math.log(1);        // eml(e-x, 1) = exp(e-x)
  const s4 = Math.exp(1) - Math.log(s3);        // eml(1, exp(e-x)) = e - (e-x) = x
  return { s1, s2, s3, s4, error: Math.abs(s4 - x) };
}

// Why simpler depths fail
const FAILED_ATTEMPTS = [
  { depth: 1, trees: ["eml(x, 1) = exp(x)", "eml(1, x) = e − ln(x)", "eml(1, 1) = e"],
    why: "Depth-1 trees produce exp(x), e − ln(x), or constants. None equal x." },
  { depth: 2, trees: ["eml(eml(x,1), 1) = exp(exp(x))", "eml(1, eml(x,1)) = e − x", "eml(x, eml(1,1)) = exp(x) − 1"],
    why: "Depth-2 trees produce double exponentials, e − x, or shifted exponentials. Close (e − x is linear) but not x." },
  { depth: 3, trees: ["eml(eml(1, eml(x,1)), 1) = exp(e − x)", "eml(x, eml(1, eml(x,1))) = exp(x) − ln(e − x)"],
    why: "Depth-3 trees produce exp(e − x) or combinations with residual exponentials. Still not x." },
];

export default function IdentityTheorem() {
  const [revealedStep, setRevealedStep] = useState(0);
  const [showVerification, setShowVerification] = useState(false);
  const [showFailures, setShowFailures] = useState(false);
  const [customX, setCustomX] = useState(2.5);

  const customResult = verify(customX);

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 620, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.5rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#10B981", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>The Identity</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          Build a tree that computes x. Just x. It's harder than you think.
        </p>
      </div>

      {/* The challenge */}
      <div style={{ padding: "16px 20px", borderRadius: 14, background: "rgba(167,139,250,0.04)", border: "1px solid rgba(167,139,250,0.1)", marginBottom: 12, textAlign: "center" }}>
        <div style={{ fontSize: 13, color: "var(--color-text-secondary, #666)", marginBottom: 8 }}>
          Every node computes <span style={{ fontFamily: "var(--font-mono)", color: "#A78BFA" }}>eml(a, b) = exp(a) − ln(b)</span>
        </div>
        <div style={{ fontSize: 13, color: "var(--color-text-secondary, #666)" }}>
          Your leaves are <span style={{ fontFamily: "var(--font-mono)", color: "#A78BFA" }}>x</span> and <span style={{ fontFamily: "var(--font-mono)", color: "#A78BFA" }}>1</span>. Build a tree whose output equals its input.
        </div>
      </div>

      {/* Why it's hard — failed attempts */}
      <button onClick={() => setShowFailures(!showFailures)} style={{
        display: "block", width: "100%", padding: "10px 14px", borderRadius: 8, marginBottom: 8,
        cursor: "pointer", textAlign: "left",
        background: showFailures ? "rgba(239,68,68,0.04)" : "var(--color-background-secondary, #faf5ff)",
        border: showFailures ? "1px solid rgba(239,68,68,0.1)" : "1px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: showFailures ? "#EF4444" : "var(--color-text-secondary, #888)" }}>
          {showFailures ? "▾ Why depths 1, 2, and 3 fail" : "▸ Why is this hard? (depths 1–3 all fail)"}
        </div>
      </button>

      {showFailures && (
        <div style={{ marginBottom: 12 }}>
          {FAILED_ATTEMPTS.map(attempt => (
            <div key={attempt.depth} style={{
              padding: "10px 14px", borderRadius: 8, marginBottom: 4,
              background: "rgba(239,68,68,0.03)", border: "1px solid rgba(239,68,68,0.06)",
            }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "#EF4444", marginBottom: 4 }}>Depth {attempt.depth}: ✗</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                {attempt.trees.map((tree, i) => (
                  <div key={i} style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #777)" }}>{tree}</div>
                ))}
              </div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary, #888)", marginTop: 4, fontStyle: "italic" }}>{attempt.why}</div>
            </div>
          ))}
        </div>
      )}

      {/* The proof — step by step */}
      <div style={{ fontSize: 12, fontWeight: 600, color: "#10B981", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>
        The depth-4 proof (click each step)
      </div>

      {PROOF_STEPS.map((ps, i) => {
        const isRevealed = i < revealedStep;
        const isCurrent = i === revealedStep;
        const isLocked = i > revealedStep;

        return (
          <button key={ps.step} onClick={() => { if (isCurrent) setRevealedStep(revealedStep + 1); }}
            disabled={isLocked}
            style={{
              display: "block", width: "100%", padding: "12px 16px", marginBottom: 6,
              borderRadius: 10, cursor: isCurrent ? "pointer" : "default",
              textAlign: "left", transition: "all 0.2s",
              background: isRevealed ? `${ps.color}08` : isCurrent ? `${ps.color}04` : "var(--color-background-secondary, #f5f5f5)",
              border: isRevealed ? `1.5px solid ${ps.color}25` : isCurrent ? `2px solid ${ps.color}30` : "1.5px solid transparent",
              opacity: isLocked ? 0.3 : 1,
            }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: isRevealed ? 8 : 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{
                  width: 24, height: 24, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center",
                  background: isRevealed ? `${ps.color}20` : "var(--color-background-secondary, #eee)",
                  fontSize: 11, fontWeight: 700, color: isRevealed ? ps.color : "var(--color-text-secondary, #bbb)",
                }}>{ps.step}</div>
                <span style={{ fontSize: 13, fontFamily: "var(--font-mono)", color: isRevealed ? ps.color : "var(--color-text-secondary, #999)", fontWeight: 600 }}>
                  {ps.input}
                </span>
              </div>
              {isRevealed && (
                <span style={{ fontSize: 15, fontFamily: "var(--font-mono)", fontWeight: 700, color: ps.color }}>
                  = {ps.result}
                </span>
              )}
              {isCurrent && (
                <span style={{ fontSize: 10, color: ps.color, fontWeight: 500 }}>click to reveal →</span>
              )}
            </div>

            {isRevealed && (
              <div style={{ animation: "fadeIn 0.3s ease" }}>
                <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #888)", marginBottom: 2 }}>
                  = {ps.expansion}
                </div>
                <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #888)", marginBottom: 4 }}>
                  = {ps.simplification}
                </div>
                <div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", fontStyle: "italic" }}>
                  {ps.explanation}
                </div>
              </div>
            )}
          </button>
        );
      })}

      {/* QED */}
      {revealedStep >= 4 && (
        <div style={{
          padding: "16px 20px", borderRadius: 14, marginTop: 10, marginBottom: 10,
          background: "rgba(16,185,129,0.04)", border: "2px solid rgba(16,185,129,0.15)",
          textAlign: "center", animation: "fadeIn 0.5s ease",
        }}>
          <div style={{ fontSize: 24, fontWeight: 700, fontFamily: "var(--font-mono)", color: "#10B981", marginBottom: 6 }}>
            eml(1, eml(eml(1, eml(x, 1)), 1)) = x
          </div>
          <div style={{ fontSize: 13, color: "var(--color-text-secondary, #666)", lineHeight: 1.7 }}>
            Four nodes. The simplest non-trivial EML identity. It takes four nested operations 
            of exp(a) − ln(b) to compute the function that does nothing. Depth 4 is minimal — 
            no tree of depth 1, 2, or 3 can produce the identity.
          </div>
        </div>
      )}

      {/* Interactive verification */}
      {revealedStep >= 4 && (
        <div style={{
          padding: "14px 18px", borderRadius: 12, marginBottom: 10,
          background: "var(--color-background-secondary, #faf5ff)",
          border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
        }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#10B981", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Verify it yourself</div>

          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
            <span style={{ fontSize: 12, color: "var(--color-text-secondary, #888)" }}>x =</span>
            <input type="range" min="0.1" max="10" step="0.1" value={customX} onChange={e => setCustomX(Number(e.target.value))}
              aria-label="x value" style={{ flex: 1, accentColor: "#10B981", cursor: "pointer" }} />
            <span style={{ fontSize: 14, fontFamily: "var(--font-mono)", color: "#10B981", fontWeight: 700, minWidth: 50, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>{customX.toFixed(1)}</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 4 }}>
            {PROOF_STEPS.map((ps, i) => (
              <div key={i} style={{ padding: "6px 8px", borderRadius: 6, background: `${ps.color}06`, textAlign: "center" }}>
                <div style={{ fontSize: 8, color: ps.color, fontWeight: 600 }}>Step {ps.step}</div>
                <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: ps.color, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
                  {i === 0 ? customResult.s1.toFixed(4) : i === 1 ? customResult.s2.toFixed(4) : i === 2 ? customResult.s3.toFixed(4) : customResult.s4.toFixed(4)}
                </div>
                <div style={{ fontSize: 8, color: "var(--color-text-secondary, #aaa)" }}>{ps.result.replace("x", customX.toFixed(1))}</div>
              </div>
            ))}
          </div>

          <div style={{ textAlign: "center", marginTop: 8 }}>
            <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "#10B981" }}>
              Output: {customResult.s4.toFixed(10)} · Error: {customResult.error.toExponential(2)}
            </span>
          </div>

          {/* Batch verification */}
          <button onClick={() => setShowVerification(!showVerification)} style={{
            display: "block", width: "100%", marginTop: 8, padding: "6px 12px", borderRadius: 6,
            cursor: "pointer", background: "rgba(16,185,129,0.06)",
            border: "1px solid rgba(16,185,129,0.1)",
            fontSize: 10, color: "#10B981", fontWeight: 500,
          }}>{showVerification ? "Hide batch test" : "Test 8 values at once"}</button>

          {showVerification && (
            <div style={{ marginTop: 8 }}>
              {TEST_VALS.map(x => {
                const r = verify(x);
                return (
                  <div key={x} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontFamily: "var(--font-mono)", padding: "2px 0", borderBottom: "1px solid rgba(0,0,0,0.03)" }}>
                    <span style={{ color: "var(--color-text-secondary, #888)" }}>x = {x}</span>
                    <span style={{ color: "#10B981" }}>output = {r.s4.toFixed(10)}</span>
                    <span style={{ color: r.error < 1e-10 ? "#10B981" : "#EF4444" }}>err = {r.error.toExponential(1)}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div style={{
        padding: "0.75rem 1rem", marginTop: 10,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          The EML Identity Theorem: the simplest function (x → x) requires the non-trivial 
          composition eml(1, eml(eml(1, eml(x,1)), 1)). This was discovered computationally 
          during EML Fourier analysis and proved algebraically in four steps. Depth 4 is minimal — 
          no EML tree of depth 1, 2, or 3 equals the identity function. The proof uses only 
          eml(a,b) = exp(a) − ln(b), the fact that ln(1) = 0, and the fact that ln(exp(z)) = z.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.org" target="_blank" rel="noopener noreferrer" style={{ color: "#10B981", textDecoration: "none", fontWeight: 500 }}>monogate.org</a>
        {" · "}<a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#06B6D4", textDecoration: "none" }}>monogate.dev</a>
      </div>

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }`}</style>
    </div>
  );
}
