import { useState, useRef, useEffect } from "react";

// ═══════════════════════════════════════════════════════════════════
// SEARCH LEVELS — N=1 through N=12, from §35
// Each level: trees searched, best MSE found, what was tried
// ═══════════════════════════════════════════════════════════════════
const SEARCH_LEVELS = [
  { n: 1, label: "N=1",  trees: 1,          mse: 0.4932,  color: "#64748B",
    desc: "1-node trees: only exp(x) and exp(-x). No ln terms possible.",
    result: "Best: exp(x) approximation. MSE 0.4932. Far from zero." },
  { n: 2, label: "N=2",  trees: 8,          mse: 0.2847,  color: "#64748B",
    desc: "2-node trees: eml(eml(x,1),1) and variants.",
    result: "Best: double-exponential. MSE 0.2847. Improving, but no oscillation." },
  { n: 3, label: "N=3",  trees: 64,         mse: 0.0590,  color: "#06B6D4",
    desc: "3-node trees: 64 candidates. First appearance of log-involving branches.",
    result: "Best: MSE 0.0590. Getting closer — but still no zeros." },
  { n: 4, label: "N=4",  trees: 512,        mse: 0.0412,  color: "#06B6D4",
    desc: "4-node trees: 512 candidates. ln(x) constructible here.",
    result: "Best: 0.0412. The EML Identity Theorem lives here (4 nodes = x). Still no sin." },
  { n: 5, label: "N=5",  trees: 4096,       mse: 0.0271,  color: "#8B5CF6",
    desc: "5-node trees: 4,096 candidates. Richer compositions available.",
    result: "Best: 0.0271. Measurement depth fully unlocked. Still no oscillation." },
  { n: 6, label: "N=6",  trees: 32768,      mse: 0.0188,  color: "#8B5CF6",
    desc: "6-node trees: 32,768 candidates. EML-2 ceiling reached.",
    result: "Best: 0.0188. Hitting the real-analytic ceiling. Zeros impossible." },
  { n: 7, label: "N=7",  trees: 262144,     mse: 0.0141,  color: "#8B5CF6",
    desc: "7-node trees: 262,144 candidates.",
    result: "Best: 0.0141. Marginal improvement. Real EML barrier confirmed." },
  { n: 8, label: "N=8",  trees: 2097152,    mse: 0.0109,  color: "#EC4899",
    desc: "8-node trees: 2,097,152 candidates. Search takes minutes.",
    result: "Best: 0.0109. Diminishing returns. T01 becoming undeniable." },
  { n: 9, label: "N=9",  trees: 16777216,   mse: 0.0088,  color: "#EC4899",
    desc: "9-node trees: 16,777,216 candidates.",
    result: "Best: 0.0088. Still positive MSE floor. No zeros permitted." },
  { n: 10, label: "N=10", trees: 134217728,  mse: 0.0071,  color: "#EC4899",
    desc: "10-node trees: 134,217,728 candidates.",
    result: "Best: 0.0071. Approaching theoretical lower bound over ℝ." },
  { n: 11, label: "N=11", trees: 1073741824, mse: 0.0059,  color: "#EC4899",
    desc: "11-node trees: 1,073,741,824. Over a billion trees.",
    result: "Best: 0.0059. The MSE floor is positive. No escape from T01." },
  { n: 12, label: "N=12", trees: 1704034304, mse: 0.0048,  color: "#EF4444",
    desc: "N=12 exhaustive search: 1,704,034,304 trees. Zero sin(x) candidates found.",
    result: "Best: 0.0048. The real-domain barrier is confirmed computationally." },
  { n: "C", label: "ℂ bypass", trees: 1, mse: 0, color: "#FDE68A",
    desc: "T03 — Euler Gateway: sin(x) = Im(eml(ix, 1)). Over ℂ, 1 node.",
    result: "MSE = 0. Exact. Not approximate. One complex EML node solves what 1.7 billion real trees cannot." },
];

// ═══════════════════════════════════════════════════════════════════
// VISUALIZATION
// ═══════════════════════════════════════════════════════════════════
function SearchCanvas({ revealed, pulse }) {
  const ref = useRef(null), t = useRef(0), f = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height;
    t.current = 0;
    const go = () => {
      t.current += 0.012; const time = t.current;
      ctx.fillStyle = "rgba(6,2,14,0.07)"; ctx.fillRect(0, 0, w, h);

      // Grid
      for (let i = 0; i < 16; i++) for (let j = 0; j < 10; j++) {
        ctx.beginPath(); ctx.arc(i * 44 + 10, j * 40 + 10, 0.4, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(139,92,246,0.04)"; ctx.fill();
      }

      ctx.fillStyle = `rgba(167,139,250,${0.04 + Math.sin(time * 0.5) * 0.01})`;
      ctx.font = "11px monospace"; ctx.textAlign = "center";
      ctx.fillText("eml(x, y) = exp(x) − ln(y)", w / 2, 22);

      const maxN = 12;
      const barW = (w - 80) / (maxN + 1);
      const chartBottom = h - 40;
      const chartTop = 50;
      const chartH = chartBottom - chartTop;

      // Axes
      ctx.strokeStyle = "rgba(167,139,250,0.08)"; ctx.lineWidth = 0.5;
      ctx.beginPath(); ctx.moveTo(50, chartTop); ctx.lineTo(50, chartBottom); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(50, chartBottom); ctx.lineTo(w - 30, chartBottom); ctx.stroke();

      // Y axis label
      ctx.fillStyle = "rgba(167,139,250,0.15)"; ctx.font = "8px monospace"; ctx.textAlign = "right";
      ctx.fillText("MSE", 48, chartTop + 4);
      ctx.fillText("0.50", 48, chartTop + 10);
      ctx.fillText("0.00", 48, chartBottom);

      // Zero line (unreachable)
      ctx.strokeStyle = "rgba(239,68,68,0.06)"; ctx.lineWidth = 0.8;
      ctx.setLineDash([3, 5]);
      ctx.beginPath(); ctx.moveTo(50, chartBottom); ctx.lineTo(w - 30, chartBottom); ctx.stroke();
      ctx.setLineDash([]);

      // Bars + labels
      SEARCH_LEVELS.forEach((level, i) => {
        if (!revealed.includes(i)) return;
        const isComplex = level.n === "C";
        const x = 50 + (i + 0.5) * barW;
        const barH_norm = level.mse / 0.52;
        const barHeight = barH_norm * chartH;
        const barY = chartBottom - barHeight;

        const [r, g, b] = [parseInt(level.color.slice(1, 3), 16), parseInt(level.color.slice(3, 5), 16), parseInt(level.color.slice(5, 7), 16)];

        if (isComplex) {
          // Special: zero bar — golden glow at axis
          const grd = ctx.createRadialGradient(x, chartBottom, 0, x, chartBottom, 30);
          grd.addColorStop(0, `rgba(${r},${g},${b},${0.3 + Math.sin(time * 2) * 0.1})`);
          grd.addColorStop(1, "rgba(0,0,0,0)");
          ctx.fillStyle = grd; ctx.beginPath(); ctx.arc(x, chartBottom, 30, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = `rgba(${r},${g},${b},${0.8 + Math.sin(time * 3) * 0.1})`;
          ctx.font = "bold 12px monospace"; ctx.textAlign = "center";
          ctx.fillText("0", x, chartBottom - 5);
        } else {
          // Bar
          const barGrd = ctx.createLinearGradient(x, barY, x, chartBottom);
          barGrd.addColorStop(0, `rgba(${r},${g},${b},0.6)`);
          barGrd.addColorStop(1, `rgba(${r},${g},${b},0.2)`);
          ctx.fillStyle = barGrd;
          ctx.fillRect(x - barW * 0.3, barY, barW * 0.6, barHeight);
          // MSE label on top of bar
          if (barHeight > 12) {
            ctx.fillStyle = `rgba(${r},${g},${b},0.7)`;
            ctx.font = "7px monospace"; ctx.textAlign = "center";
            ctx.fillText(level.mse.toFixed(3), x, barY - 3);
          }
        }

        // N label below axis
        ctx.fillStyle = `rgba(${r},${g},${b},0.5)`;
        ctx.font = isComplex ? "bold 8px monospace" : "7px monospace"; ctx.textAlign = "center";
        ctx.fillText(level.label, x, chartBottom + 12);
      });

      // T01 annotation when many bars revealed
      if (revealed.length >= 8 && !revealed.includes(SEARCH_LEVELS.length - 1)) {
        ctx.fillStyle = `rgba(239,68,68,${0.04 + Math.sin(time) * 0.02})`;
        ctx.font = "9px monospace"; ctx.textAlign = "center";
        ctx.fillText("T01: finite real EML trees are real-analytic → zero-count bounded", w / 2, h - 22);
      }

      f.current = requestAnimationFrame(go);
    };
    ctx.fillStyle = "#06020E"; ctx.fillRect(0, 0, w, h); go();
    return () => cancelAnimationFrame(f.current);
  }, [revealed, pulse]);
  return <canvas ref={ref} width={680} height={400} style={{ width: "100%", height: "100%", display: "block", borderRadius: 12 }} />;
}

// ═══════════════════════════════════════════════════════════════════
// MAIN GAME
// ═══════════════════════════════════════════════════════════════════
export default function TheGap() {
  const [revealed, setRevealed] = useState([]);
  const [lastLevel, setLastLevel] = useState(null);
  const [pulse, setPulse] = useState(0);

  useEffect(() => { let fr; const tick = () => { setPulse(p => p + 0.025); fr = requestAnimationFrame(tick); }; tick(); return () => cancelAnimationFrame(fr); }, []);

  const totalLevels = SEARCH_LEVELS.length;
  const allRevealed = revealed.length === totalLevels;
  const complexRevealed = revealed.includes(totalLevels - 1);

  const revealNext = () => {
    const nextIdx = revealed.length;
    if (nextIdx >= totalLevels) return;
    const level = SEARCH_LEVELS[nextIdx];
    setRevealed(prev => [...prev, nextIdx]);
    setLastLevel(level);
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)();
      const isComplex = level.n === "C";
      if (isComplex) {
        [261.63, 329.63, 392, 523.25].forEach((freq, i) => {
          const o = ac.createOscillator(); o.type = "sine";
          o.frequency.setValueAtTime(freq, ac.currentTime + i * 0.2);
          const g = ac.createGain(); g.gain.setValueAtTime(0.06, ac.currentTime + i * 0.2);
          g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 3);
          o.connect(g); g.connect(ac.destination); o.start(ac.currentTime + i * 0.2);
          o.stop(ac.currentTime + 3.5);
        });
        setTimeout(() => ac.close(), 4500);
      } else {
        const baseFreq = 130 + nextIdx * 18;
        const o = ac.createOscillator(); o.type = "triangle";
        o.frequency.setValueAtTime(baseFreq, ac.currentTime);
        o.frequency.exponentialRampToValueAtTime(baseFreq * 1.3, ac.currentTime + 0.4);
        const g = ac.createGain(); g.gain.setValueAtTime(0.05, ac.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 1.2);
        o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime + 1.5);
        setTimeout(() => ac.close(), 2000);
      }
    } catch {}
  };

  const reset = () => { setRevealed([]); setLastLevel(null); };

  const totalTrees = revealed
    .filter(i => SEARCH_LEVELS[i].n !== "C")
    .reduce((sum, i) => sum + SEARCH_LEVELS[i].trees, 0);

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 740, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.4rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#EF4444", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 26, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>1.7 Billion Trees</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          N=1 through N=12 exhaustive search for sin(x). Watch the MSE shrink — but never reach zero. Then discover what 1 complex node does.
        </p>
      </div>

      <div style={{
        textAlign: "center", padding: "6px 14px", margin: "6px 0 10px",
        background: complexRevealed ? "rgba(253,230,138,0.08)" : "rgba(239,68,68,0.05)",
        borderRadius: 8, fontSize: 12, fontWeight: 500,
        color: complexRevealed ? "#D97706" : "#EF4444",
        border: `1px solid ${complexRevealed ? "rgba(253,230,138,0.2)" : "rgba(239,68,68,0.1)"}`,
      }}>
        {complexRevealed
          ? "The Euler Gateway closes the gap. MSE = 0 exactly."
          : `${totalTrees.toLocaleString()} real trees searched · best MSE: ${revealed.length > 0 ? SEARCH_LEVELS[revealed[revealed.length - 1]]?.mse.toFixed(4) : "—"}`}
      </div>

      <div className="gap-grid" style={{ display: "grid", gridTemplateColumns: "1fr 220px", gap: 10 }}>
        <div>
          <div style={{ borderRadius: 14, overflow: "hidden", border: `1px solid ${complexRevealed ? "rgba(253,230,138,0.15)" : "rgba(239,68,68,0.1)"}`, marginBottom: 10, aspectRatio: "680/400" }}>
            <SearchCanvas revealed={revealed} pulse={pulse} />
          </div>

          {lastLevel && (
            <div style={{
              padding: "8px 14px", borderRadius: 8, marginBottom: 10,
              background: `${lastLevel.color}06`, border: `1px solid ${lastLevel.color}15`,
              animation: "fadeIn 0.3s ease",
            }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: lastLevel.color }}>{lastLevel.label}: {lastLevel.trees.toLocaleString()} trees</div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary, #777)", marginTop: 3 }}>{lastLevel.result}</div>
            </div>
          )}

          <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-secondary, #888)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
            {allRevealed ? "Search complete. T01 confirmed. Euler Gateway found." : "Reveal each search level"}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 6 }}>
            {SEARCH_LEVELS.map((level, i) => {
              const isRev = revealed.includes(i);
              const isNext = i === revealed.length;
              const isComplex = level.n === "C";
              return (
                <button key={level.label} onClick={() => isNext && revealNext()}
                  style={{
                    padding: "10px 12px", borderRadius: 10,
                    cursor: isNext ? "pointer" : "default", textAlign: "left",
                    background: isRev ? `${level.color}08` : isNext ? "rgba(167,139,250,0.06)" : "var(--color-background-secondary, #f8f5ff)",
                    border: isRev ? `1.5px solid ${level.color}25` : isNext ? "1.5px solid rgba(167,139,250,0.2)" : "1.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
                    opacity: isRev ? 0.75 : isNext ? 1 : 0.3,
                    transition: "all 0.2s",
                  }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 2 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: isRev ? level.color : "var(--color-text-secondary, #666)" }}>
                      {isRev && "✓ "}{level.label}
                    </span>
                    {isRev && !isComplex && (
                      <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: level.color }}>
                        MSE {level.mse}
                      </span>
                    )}
                    {isRev && isComplex && (
                      <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: level.color, fontWeight: 700 }}>
                        MSE 0 ✓
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 9, color: "var(--color-text-secondary, #aaa)", lineHeight: 1.4 }}>
                    {isRev ? level.desc : isNext ? "Click to reveal →" : "locked"}
                  </div>
                  {isNext && !isRev && (
                    <div style={{ fontSize: 9, color: "#A78BFA", marginTop: 3, fontFamily: "var(--font-mono)" }}>
                      {isComplex ? "T03 — Euler Gateway" : `${level.trees.toLocaleString()} trees`}
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {allRevealed && (
            <div style={{
              marginTop: 10, padding: "20px 24px", borderRadius: 14,
              background: "rgba(253,230,138,0.04)", border: "1.5px solid rgba(253,230,138,0.15)",
              textAlign: "center", animation: "fadeIn 1s ease",
            }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#FDE68A", marginBottom: 8 }}>
                1.7 billion real trees. Zero sin(x) candidates.
              </div>
              <div style={{ fontSize: 13, color: "var(--color-text-secondary, #888)", lineHeight: 1.7, marginBottom: 10 }}>
                T01 (Infinite Zeros Barrier) explains it: every finite real EML tree is real-analytic, so it has at most finitely many zeros on any bounded interval. sin(x) has infinitely many. No finite real EML tree can equal sin(x). The exhaustive search confirms this computationally.
              </div>
              <div style={{ fontSize: 13, color: "#FDE68A", lineHeight: 1.7, marginBottom: 12 }}>
                But extend to ℂ: sin(x) = Im(eml(ix, 1)). One node. MSE = 0. Exact.
                The barrier is real-domain only. The Euler Gateway (T03) dissolves it.
              </div>
              <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "#A78BFA", lineHeight: 1.7 }}>
                Real EML: ∞ nodes needed (never achieved)<br />
                Complex EML: 1 node (exact)
              </div>
            </div>
          )}

          <button onClick={reset} style={{
            marginTop: 10, padding: "8px 16px", borderRadius: 8, width: "100%",
            border: "1.5px solid var(--color-border-tertiary, #ddd)",
            background: "var(--color-background-primary, white)", color: "var(--color-text-secondary, #666)",
            fontSize: 11, cursor: "pointer",
          }}>Reset — run the search again</button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {lastLevel && (
            <div style={{
              padding: "10px 12px", borderRadius: 10,
              background: `${lastLevel.color}06`, border: `1px solid ${lastLevel.color}15`,
              animation: "fadeIn 0.3s ease",
            }}>
              <div style={{ fontSize: 9, fontWeight: 600, color: lastLevel.color, textTransform: "uppercase", letterSpacing: 1, marginBottom: 3 }}>
                {lastLevel.n === "C" ? "Euler Gateway" : "Search level"}
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--color-text-primary, #1a1a2e)", marginBottom: 4 }}>{lastLevel.label}</div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", lineHeight: 1.6 }}>{lastLevel.desc}</div>
            </div>
          )}

          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#EF4444", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>T01 — Infinite Zeros Barrier</div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #666)", lineHeight: 1.7 }}>
              Any finite real EML tree is a composition of exp and ln — both real-analytic. Real-analytic functions have at most finitely many zeros on any bounded interval (unless identically zero). sin(x) has infinitely many zeros: nπ for all n ∈ ℤ. Contradiction. QED.
            </div>
          </div>

          <div style={{
            padding: "10px 12px", borderRadius: 10,
            background: "var(--color-background-secondary, #faf5ff)",
            border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
          }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Search stats</div>
            <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #1a1a2e)" }}>
              {totalTrees.toLocaleString()}
            </div>
            <div style={{ fontSize: 10, color: "var(--color-text-secondary, #888)", marginBottom: 6 }}>real trees searched</div>
            <div style={{ height: 4, borderRadius: 2, background: "rgba(239,68,68,0.1)", overflow: "hidden" }}>
              <div style={{
                height: "100%",
                width: `${(revealed.filter(i => SEARCH_LEVELS[i].n !== "C").length / 12) * 100}%`,
                background: complexRevealed ? "#FDE68A" : "#EF4444",
                borderRadius: 2, transition: "width 0.3s",
              }} />
            </div>
            <div style={{ fontSize: 9, color: "var(--color-text-secondary, #aaa)", marginTop: 3 }}>
              {revealed.filter(i => SEARCH_LEVELS[i].n !== "C").length}/12 real levels
            </div>
          </div>

          {revealed.length >= 6 && (
            <div style={{
              padding: "8px 10px", borderRadius: 8,
              background: "rgba(236,72,153,0.04)", border: "1px solid rgba(236,72,153,0.08)",
              fontSize: 10, color: "#EC4899", lineHeight: 1.6, animation: "fadeIn 0.5s ease",
            }}>
              EML Pumping Lemma (§27): depth-k trees have at most 2^k zeros. sin(x) has infinitely many. The theoretical ceiling is confirmed.
            </div>
          )}

          {complexRevealed && (
            <div style={{
              padding: "8px 10px", borderRadius: 8,
              background: "rgba(253,230,138,0.04)", border: "1px solid rgba(253,230,138,0.1)",
              fontSize: 10, color: "#FDE68A", lineHeight: 1.6, animation: "fadeIn 0.5s ease",
            }}>
              T03 — Euler Gateway: sin(x) = Im(eml(ix, 1)) = Im(e^{"{ix}"}). The depth-∞ barrier over ℝ dissolves over ℂ. One node. Exact.
            </div>
          )}
        </div>
      </div>

      <div style={{
        padding: "0.75rem 1rem", marginTop: 12,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          §35 of the EML paper: 1,704,034,304 real EML trees were searched exhaustively up to depth N=12. Zero candidates for sin(x) were found. T01 (Infinite Zeros Barrier, §14) provides the structural proof: finite real EML trees are real-analytic, and real-analytic functions have finitely many zeros. sin(x) has infinitely many. T03 (Euler Gateway, §16) provides the resolution: over ℂ, sin(x) = Im(eml(ix, 1)) in exactly one node. The gap between real and complex EML is where the barrier lives.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#EF4444", textDecoration: "none", fontWeight: 500 }}>monogate.dev</a>
        {" · "}
        <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none" }}>arXiv:2603.21852</a>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }
        @media(max-width:600px){.gap-grid{grid-template-columns:1fr!important;}}
      `}</style>
    </div>
  );
}
