import { useState } from "react";

// Real data from the exhaustive search (§35, §6.2)
const SEARCH_DEPTHS = [
  { n: 1, catalan: 1, leafAssign: 4, trees: 4, cumulative: 4, bestMSE: 12.4, time: "<1ms" },
  { n: 2, catalan: 2, leafAssign: 8, trees: 16, cumulative: 20, bestMSE: 8.7, time: "<1ms" },
  { n: 3, catalan: 5, leafAssign: 16, trees: 80, cumulative: 100, bestMSE: 3.2, time: "<1ms" },
  { n: 4, catalan: 14, leafAssign: 32, trees: 448, cumulative: 548, bestMSE: 1.8, time: "<1ms" },
  { n: 5, catalan: 42, leafAssign: 64, trees: 2688, cumulative: 3236, bestMSE: 0.91, time: "<1ms" },
  { n: 6, catalan: 132, leafAssign: 128, trees: 16896, cumulative: 20132, bestMSE: 0.62, time: "<1ms" },
  { n: 7, catalan: 429, leafAssign: 256, trees: 109824, cumulative: 129956, bestMSE: 0.45, time: "1s" },
  { n: 8, catalan: 1430, leafAssign: 512, trees: 732160, cumulative: 862116, bestMSE: 0.31, time: "25s" },
  { n: 9, catalan: 4862, leafAssign: 1024, trees: 4978688, cumulative: 5840804, bestMSE: 0.22, time: "2m" },
  { n: 10, catalan: 16796, leafAssign: 2048, trees: 34398208, cumulative: 40239012, bestMSE: 0.18, time: "8m" },
  { n: 11, catalan: 58786, leafAssign: 4096, trees: 240787456, cumulative: 281026468, bestMSE: 0.148, time: "5.4m" },
  { n: 12, catalan: 208012, leafAssign: 8192, trees: 1704034304, cumulative: 1704034304, bestMSE: 0.112, time: "2m46s" },
];

function formatNum(n) {
  if (n >= 1e9) return (n / 1e9).toFixed(2) + "B";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return String(n);
}

function SearchBar({ depth, isRevealed, isNext, onReveal }) {
  const d = SEARCH_DEPTHS[depth];
  const maxLog = Math.log10(1704034304);
  const barPct = isRevealed ? (Math.log10(Math.max(d.cumulative, 1)) / maxLog) * 100 : 0;
  const mseBarPct = isRevealed ? Math.max(3, (d.bestMSE / 12.4) * 100) : 0;

  return (
    <button
      onClick={isNext ? onReveal : undefined}
      disabled={!isNext}
      style={{
        display: "block", width: "100%", padding: "8px 12px", marginBottom: 3,
        borderRadius: 8, textAlign: "left",
        cursor: isNext ? "pointer" : "default",
        background: isRevealed ? "rgba(239,68,68,0.03)" : isNext ? "rgba(167,139,250,0.04)" : "var(--color-background-secondary, #f5f5f5)",
        border: isNext ? "2px solid rgba(167,139,250,0.2)" : isRevealed ? "1px solid rgba(239,68,68,0.08)" : "1px solid transparent",
        opacity: !isRevealed && !isNext ? 0.3 : 1,
        transition: "all 0.2s",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: isRevealed ? 4 : 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center",
            background: isRevealed ? "rgba(239,68,68,0.08)" : isNext ? "rgba(167,139,250,0.08)" : "rgba(0,0,0,0.03)",
            fontSize: 11, fontWeight: 700, fontFamily: "var(--font-mono)",
            color: isRevealed ? "#EF4444" : isNext ? "#A78BFA" : "var(--color-text-secondary, #ccc)",
          }}>N={d.n}</div>
          {isNext && !isRevealed && (
            <span style={{ fontSize: 10, color: "#A78BFA", fontWeight: 500 }}>click to search</span>
          )}
          {isRevealed && (
            <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary, #888)" }}>
              {formatNum(d.cumulative)} trees
            </span>
          )}
        </div>
        {isRevealed && (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 10, color: "var(--color-text-secondary, #999)" }}>{d.time}</span>
            <span style={{ fontSize: 13, fontFamily: "var(--font-mono)", fontWeight: 700, color: "#EF4444" }}>
              MSE: {d.bestMSE.toFixed(3)}
            </span>
          </div>
        )}
      </div>

      {isRevealed && (
        <div style={{ display: "flex", gap: 6 }}>
          {/* Tree count bar */}
          <div style={{ flex: 1 }}>
            <div style={{ height: 4, borderRadius: 2, background: "rgba(167,139,250,0.06)", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${barPct}%`, background: "rgba(167,139,250,0.3)", borderRadius: 2, transition: "width 0.5s" }} />
            </div>
          </div>
          {/* MSE bar */}
          <div style={{ flex: 1 }}>
            <div style={{ height: 4, borderRadius: 2, background: "rgba(239,68,68,0.06)", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${mseBarPct}%`, background: "rgba(239,68,68,0.3)", borderRadius: 2, transition: "width 0.5s" }} />
            </div>
          </div>
        </div>
      )}
    </button>
  );
}

export default function BillionTrees() {
  const [revealed, setRevealed] = useState(0);
  const [bypassed, setBypassed] = useState(false);

  const revealNext = () => {
    if (revealed < 12) setRevealed(revealed + 1);
  };

  const allRevealed = revealed >= 12;
  const currentData = revealed > 0 ? SEARCH_DEPTHS[revealed - 1] : null;

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 620, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.5rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#EF4444", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>1.7 Billion Trees</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          Every possible EML tree up to 12 nodes. Not one produces sin(x).
        </p>
      </div>

      {/* The question */}
      <div style={{
        padding: "14px 18px", borderRadius: 12, marginBottom: 10,
        background: "rgba(167,139,250,0.03)", border: "1px solid rgba(167,139,250,0.08)", textAlign: "center",
      }}>
        <div style={{ fontSize: 14, fontFamily: "var(--font-mono)", color: "#A78BFA", marginBottom: 4 }}>
          Does any finite tree of eml(x, y) = exp(x) {"\u2212"} ln(y) equal sin(x)?
        </div>
        <div style={{ fontSize: 12, color: "var(--color-text-secondary, #888)" }}>
          Terminals: {"{"}1, x{"}"}. Every binary tree shape. Every leaf assignment. Every depth up to 12.
        </div>
      </div>

      {/* Counter */}
      {revealed > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 10 }}>
          <div style={{
            padding: "12px", borderRadius: 10, textAlign: "center",
            background: "rgba(167,139,250,0.04)", border: "1px solid rgba(167,139,250,0.1)",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#A78BFA", textTransform: "uppercase", letterSpacing: 1 }}>Trees searched</div>
            <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "var(--font-mono)", color: "#A78BFA", fontVariantNumeric: "tabular-nums" }}>
              {formatNum(currentData.cumulative)}
            </div>
          </div>
          <div style={{
            padding: "12px", borderRadius: 10, textAlign: "center",
            background: bypassed ? "rgba(16,185,129,0.04)" : "rgba(239,68,68,0.04)",
            border: bypassed ? "1px solid rgba(16,185,129,0.1)" : "1px solid rgba(239,68,68,0.1)",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: bypassed ? "#10B981" : "#EF4444", textTransform: "uppercase", letterSpacing: 1 }}>
              {bypassed ? "Complex MSE" : "Best MSE"}
            </div>
            <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "var(--font-mono)", color: bypassed ? "#10B981" : "#EF4444", fontVariantNumeric: "tabular-nums" }}>
              {bypassed ? "0.000" : currentData.bestMSE.toFixed(3)}
            </div>
          </div>
        </div>
      )}

      {/* Search depth rows */}
      <div style={{ marginBottom: 10 }}>
        {SEARCH_DEPTHS.map((d, i) => (
          <SearchBar
            key={d.n}
            depth={i}
            isRevealed={i < revealed}
            isNext={i === revealed && !allRevealed}
            onReveal={revealNext}
          />
        ))}
      </div>

      {/* All searched — the barrier */}
      {allRevealed && !bypassed && (
        <div style={{
          padding: "16px 20px", borderRadius: 14, marginBottom: 10,
          background: "rgba(239,68,68,0.04)", border: "1.5px solid rgba(239,68,68,0.12)",
        }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: "#EF4444", marginBottom: 6, textAlign: "center" }}>
            1,704,034,304 trees. Zero candidates.
          </div>
          <div style={{ fontSize: 12, color: "var(--color-text-secondary, #666)", lineHeight: 1.7, marginBottom: 8 }}>
            Every composition of eml(x, y) = exp(x) {"\u2212"} ln(y) with up to 12 internal nodes 
            and terminals {"{"}1, x{"}"} has been evaluated. Not one matches sin(x) at any useful tolerance. 
            The best MSE after 1.7 billion trees is 0.112 — nowhere close.
          </div>
          <div style={{ fontSize: 12, color: "var(--color-text-secondary, #666)", lineHeight: 1.7, marginBottom: 10 }}>
            This is not a sampling failure. This is exhaustive. Every Catalan tree shape. Every 
            possible leaf assignment. The Infinite Zeros Barrier theorem proves WHY: sin(x) has 
            zeros at every multiple of {"\u03C0"} — infinitely many. But every finite real EML tree is 
            real-analytic with finitely many zeros. No finite tree can match a function with 
            infinite zeros. Not at N=12. Not at N=1000. Not ever.
          </div>

          <button onClick={() => setBypassed(true)} style={{
            display: "block", width: "100%", padding: "14px", borderRadius: 10,
            cursor: "pointer",
            background: "rgba(16,185,129,0.08)", border: "2px solid rgba(16,185,129,0.2)",
            fontSize: 15, fontWeight: 700, color: "#10B981",
          }}>Go complex</button>
        </div>
      )}

      {/* The bypass */}
      {bypassed && (
        <div style={{
          padding: "20px 24px", borderRadius: 14, marginBottom: 10,
          background: "rgba(16,185,129,0.04)", border: "2px solid rgba(16,185,129,0.15)",
          textAlign: "center",
        }}>
          <div style={{ fontSize: 28, fontWeight: 700, fontFamily: "var(--font-mono)", color: "#10B981", marginBottom: 8 }}>
            sin(x) = Im(eml(ix, 1))
          </div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#10B981", marginBottom: 12 }}>
            One node. Exact. Machine precision.
          </div>
          <div style={{ fontSize: 13, color: "var(--color-text-secondary, #666)", lineHeight: 1.7, textAlign: "left" }}>
            Over the complex numbers, eml(ix, 1) = exp(ix) {"\u2212"} ln(1) = exp(ix). By Euler's 
            formula, exp(ix) = cos(x) + i{"\u00B7"}sin(x). The imaginary part is sin(x). Exactly. 
            For all real x. One complex EML node does what 1.7 billion real trees could not.
          </div>
          <div style={{
            marginTop: 12, padding: "10px 14px", borderRadius: 8,
            background: "var(--color-background-primary, white)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
            textAlign: "left",
          }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#10B981", marginBottom: 4 }}>The proof (3 lines)</div>
            <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #444)", lineHeight: 1.8 }}>
              eml(ix, 1) = exp(ix) {"\u2212"} ln(1) = exp(ix)<br />
              exp(ix) = cos(x) + i{"\u00B7"}sin(x){"  "}(Euler)<br />
              Im(exp(ix)) = sin(x){"  "}{"\u25A1"}
            </div>
          </div>
        </div>
      )}

      {/* Stats table — after bypass */}
      {bypassed && (
        <div style={{
          padding: "12px 16px", borderRadius: 10, marginBottom: 10,
          background: "var(--color-background-secondary, #faf5ff)",
          border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
        }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-secondary, #999)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>Search summary</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 6, textAlign: "center" }}>
            <div>
              <div style={{ fontSize: 8, color: "var(--color-text-secondary, #aaa)" }}>Total trees</div>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "var(--font-mono)", color: "#A78BFA" }}>1.7B</div>
            </div>
            <div>
              <div style={{ fontSize: 8, color: "var(--color-text-secondary, #aaa)" }}>Max depth</div>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "var(--font-mono)", color: "#A78BFA" }}>N=12</div>
            </div>
            <div>
              <div style={{ fontSize: 8, color: "var(--color-text-secondary, #aaa)" }}>Real candidates</div>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "var(--font-mono)", color: "#EF4444" }}>0</div>
            </div>
            <div>
              <div style={{ fontSize: 8, color: "var(--color-text-secondary, #aaa)" }}>Complex nodes</div>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "var(--font-mono)", color: "#10B981" }}>1</div>
            </div>
          </div>
          <div style={{ marginTop: 8, fontSize: 11, color: "var(--color-text-secondary, #888)", textAlign: "center" }}>
            Runtime: 2 min 46 sec on 8-thread Rust (rayon). 10M trees/sec.
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{
        padding: "0.75rem 1rem", marginTop: 10,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          The most exhaustive search ever conducted within the EML framework. Every possible 
          composition of eml(x, y) = exp(x) {"\u2212"} ln(y) with terminals {"{"}1, x{"}"} and up 
          to 12 internal nodes was enumerated using Catalan tree shapes and 2{"\u207F\u207A\u00B9"} leaf 
          assignments. The Infinite Zeros Barrier theorem proves no real-valued construction 
          exists at ANY depth: sin(x) has infinitely many zeros, finite EML trees have finitely 
          many. The complex bypass resolves the barrier in one node via Euler's formula. 
          Search data: monogate-core Rust binary, results/sin_n12.json.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.org" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none", fontWeight: 500 }}>monogate.org</a>
        {" \u00B7 "}
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#06B6D4", textDecoration: "none" }}>monogate.dev</a>
      </div>
    </div>
  );
}
