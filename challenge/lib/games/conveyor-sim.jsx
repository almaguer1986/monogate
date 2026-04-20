import { useState, useRef, useEffect, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════════
// THE BELT — a living system traversing the depth hierarchy
// ═══════════════════════════════════════════════════════════════════
export default function ConveyorSim() {
  const [running, setRunning] = useState(false);
  const [failed, setFailed] = useState(false);
  const [stopped, setStopped] = useState(false);
  const [tension, setTension] = useState(50);
  const [speed, setSpeed] = useState(60);
  const [time, setTime] = useState(0);
  const [health, setHealth] = useState(100);
  const [vibrationLevel, setVibrationLevel] = useState(0);
  const [wearDepth, setWearDepth] = useState(0);
  const [score, setScore] = useState(null);
  const [depthRevealed, setDepthRevealed] = useState([]);
  const canvasRef = useRef(null);
  const acRef = useRef(null);
  const oscRef = useRef(null);
  const gainRef = useRef(null);
  const intervalRef = useRef(null);
  const frameRef = useRef(null);

  // Start the belt
  const startBelt = useCallback(() => {
    setRunning(true);
    setFailed(false);
    setStopped(false);
    setTime(0);
    setHealth(100);
    setVibrationLevel(0);
    setWearDepth(0);
    setScore(null);
    setDepthRevealed([]);

    // Start audio — bearing hum
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)();
      acRef.current = ac;
      const osc = ac.createOscillator();
      osc.type = "sine";
      osc.frequency.setValueAtTime(120, ac.currentTime);
      const gain = ac.createGain();
      gain.gain.setValueAtTime(0.02, ac.currentTime);
      osc.connect(gain);
      gain.connect(ac.destination);
      osc.start();
      oscRef.current = osc;
      gainRef.current = gain;
    } catch {}
  }, []);

  // Stop the belt (player decision)
  const stopBelt = () => {
    if (!running || failed) return;
    setStopped(true);
    setRunning(false);

    // Score based on when they stopped
    let s = "perfect";
    let msg = "";
    if (health > 80) {
      s = "early";
      msg = "Belt was still healthy. You stopped too early. EML-2 measurement said it was fine.";
    } else if (health > 40) {
      s = "good";
      msg = "Good call. Vibrations were changing. Your EML-3 ear caught the shift.";
    } else if (health > 15) {
      s = "perfect";
      msg = "Perfect timing. The bearing was about to go. EML-2 logarithmic wear and EML-3 oscillatory vibration both confirmed it. You read the gauges correctly.";
    } else {
      s = "late";
      msg = "Almost too late. Another minute and you'd have had a catastrophic failure.";
    }
    setScore({ grade: s, msg });

    // Stop audio
    try { oscRef.current?.stop(); acRef.current?.close(); } catch {}
  };

  // Simulation tick
  useEffect(() => {
    if (!running) return;

    const tick = setInterval(() => {
      setTime(t => {
        const newTime = t + 0.1;

        // Health degrades based on tension and speed
        const stressFactor = (tension / 50) * (speed / 60);
        const degradation = 0.15 * stressFactor * (1 + newTime * 0.02);

        setHealth(h => {
          const newHealth = Math.max(0, h - degradation);

          // Update vibration — gets worse as health drops
          const vib = Math.max(0, (100 - newHealth) / 100);
          const jitter = Math.sin(newTime * 15) * 0.1 + Math.sin(newTime * 23) * 0.05;
          setVibrationLevel(vib + jitter * vib);

          // Update wear depth (logarithmic — EML-2)
          setWearDepth(Math.log(1 + newTime * stressFactor * 0.3) * 2);

          // Update audio — pitch rises as bearing degrades
          try {
            if (oscRef.current && acRef.current) {
              const baseFreq = 120 + (100 - newHealth) * 3;
              const wobble = Math.sin(newTime * 8) * (100 - newHealth) * 0.15;
              oscRef.current.frequency.setValueAtTime(baseFreq + wobble, acRef.current.currentTime);
              gainRef.current.gain.setValueAtTime(0.02 + vib * 0.04, acRef.current.currentTime);
            }
          } catch {}

          // Depth reveals based on time
          if (newTime > 3 && !depthRevealed.includes(0)) setDepthRevealed(d => [...d, 0]);
          if (newTime > 8 && !depthRevealed.includes(1)) setDepthRevealed(d => [...d, 1]);
          if (newTime > 15 && !depthRevealed.includes(2)) setDepthRevealed(d => [...d, 2]);
          if (newTime > 25 && !depthRevealed.includes(3)) setDepthRevealed(d => [...d, 3]);

          // Catastrophic failure
          if (newHealth <= 0) {
            setFailed(true);
            setRunning(false);
            setScore({ grade: "failed", msg: "Catastrophic failure. The bearing seized. The belt snapped. EML-∞ onset: the cascade became irreversible before the gauges could fully confirm it. EML-3 vibration peaked, EML-2 wear was critical." });
            try { oscRef.current?.stop(); acRef.current?.close(); } catch {}
          }

          return newHealth;
        });

        return newTime;
      });
    }, 100);

    intervalRef.current = tick;
    return () => clearInterval(tick);
  }, [running, tension, speed, depthRevealed]);

  // Canvas visualization
  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    const w = c.width, h = c.height;
    let t = 0;

    const draw = () => {
      t += 0.02;
      ctx.fillStyle = "rgba(10,8,20,0.12)";
      ctx.fillRect(0, 0, w, h);

      const shake = vibrationLevel * 3;
      const ox = Math.sin(t * 15) * shake;
      const oy = Math.cos(t * 13) * shake;

      // The belt — two rollers and a belt loop
      const beltY = h * 0.5;
      const leftX = 80, rightX = w - 80;
      const rollerR = 25;

      // Belt surface (moving)
      if (running || (!stopped && !failed)) {
        const beltSpeed = running ? speed * 0.02 : 0;
        // Top belt
        ctx.beginPath();
        ctx.moveTo(leftX + ox, beltY - rollerR + oy);
        for (let x = leftX; x <= rightX; x += 3) {
          const wobble = Math.sin((x + t * beltSpeed * 10) * 0.05) * vibrationLevel * 4;
          ctx.lineTo(x + ox, beltY - rollerR + wobble + oy);
        }
        ctx.strokeStyle = `rgba(${health > 50 ? 100 : 200},${health > 50 ? 180 : 80},${health > 50 ? 100 : 80},0.6)`;
        ctx.lineWidth = 4;
        ctx.stroke();

        // Bottom belt
        ctx.beginPath();
        ctx.moveTo(leftX + ox, beltY + rollerR + oy);
        for (let x = leftX; x <= rightX; x += 3) {
          const wobble = Math.sin((x + t * beltSpeed * 10) * 0.05 + 2) * vibrationLevel * 3;
          ctx.lineTo(x + ox, beltY + rollerR + wobble + oy);
        }
        ctx.strokeStyle = `rgba(${health > 50 ? 80 : 160},${health > 50 ? 140 : 60},${health > 50 ? 80 : 60},0.4)`;
        ctx.lineWidth = 3;
        ctx.stroke();
      }

      // Rollers
      [leftX, rightX].forEach(rx => {
        ctx.beginPath();
        ctx.arc(rx + ox, beltY + oy, rollerR, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(167,139,250,${0.3 + vibrationLevel * 0.2})`;
        ctx.lineWidth = 2;
        ctx.stroke();
        // Rotation indicator
        const angle = running ? t * speed * 0.05 : 0;
        ctx.beginPath();
        ctx.moveTo(rx + ox, beltY + oy);
        ctx.lineTo(rx + Math.cos(angle) * (rollerR - 3) + ox, beltY + Math.sin(angle) * (rollerR - 3) + oy);
        ctx.strokeStyle = "rgba(167,139,250,0.5)";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });

      // Vibration particles (EML-3 visualization)
      if (vibrationLevel > 0.2) {
        for (let i = 0; i < vibrationLevel * 15; i++) {
          const px = leftX + Math.random() * (rightX - leftX);
          const py = beltY + (Math.random() - 0.5) * rollerR * 3;
          ctx.beginPath();
          ctx.arc(px + ox, py + oy, 1 + Math.random(), 0, Math.PI * 2);
          ctx.fillStyle = `rgba(236,72,153,${vibrationLevel * 0.3})`;
          ctx.fill();
        }
      }

      // Failure state
      if (failed) {
        // Broken belt pieces
        for (let i = 0; i < 20; i++) {
          const px = leftX + Math.random() * (rightX - leftX);
          const py = beltY + (Math.random() - 0.5) * 80;
          ctx.beginPath();
          ctx.moveTo(px, py);
          ctx.lineTo(px + Math.random() * 20 - 10, py + Math.random() * 20 - 10);
          ctx.strokeStyle = "rgba(239,68,68,0.3)";
          ctx.lineWidth = 2;
          ctx.stroke();
        }
        ctx.fillStyle = "rgba(239,68,68,0.06)";
        ctx.font = "bold 24px monospace";
        ctx.textAlign = "center";
        ctx.fillText("FAILURE", w / 2, beltY);
      }

      // Stopped state — peaceful
      if (stopped) {
        ctx.fillStyle = "rgba(16,185,129,0.04)";
        ctx.font = "14px monospace";
        ctx.textAlign = "center";
        ctx.fillText("STOPPED", w / 2, beltY - 50);
      }

      // Depth labels
      ctx.font = "9px monospace";
      ctx.textAlign = "left";
      if (depthRevealed.includes(0)) {
        ctx.fillStyle = "rgba(100,116,139,0.15)";
        ctx.fillText("EML-0: belt segments = discrete", 10, 20);
      }
      if (depthRevealed.includes(1)) {
        ctx.fillStyle = "rgba(6,182,212,0.15)";
        ctx.fillText("EML-1: tension = exponential stress", 10, 32);
      }
      if (depthRevealed.includes(2)) {
        ctx.fillStyle = "rgba(139,92,246,0.15)";
        ctx.fillText("EML-2: wear depth = logarithmic measurement", 10, 44);
      }
      if (depthRevealed.includes(3)) {
        ctx.fillStyle = "rgba(236,72,153,0.15)";
        ctx.fillText("EML-3: vibration = oscillatory signature", 10, 56);
      }

      frameRef.current = requestAnimationFrame(draw);
    };
    ctx.fillStyle = "#0A0814";
    ctx.fillRect(0, 0, w, h);
    draw();
    return () => cancelAnimationFrame(frameRef.current);
  }, [running, failed, stopped, health, vibrationLevel, speed, depthRevealed]);

  // Cleanup
  useEffect(() => {
    return () => {
      clearInterval(intervalRef.current);
      cancelAnimationFrame(frameRef.current);
      try { oscRef.current?.stop(); acRef.current?.close(); } catch {}
    };
  }, []);

  const healthColor = health > 60 ? "#10B981" : health > 30 ? "#F59E0B" : "#EF4444";

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 680, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.4rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#F59E0B", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>The Conveyor Belt</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          Adjust tension. Read the wear gauge. Listen to the bearing. Stop the belt before it fails. The math was always under your hands.
        </p>
      </div>

      {/* Canvas */}
      <div style={{ borderRadius: 14, overflow: "hidden", border: `1px solid ${failed ? "rgba(239,68,68,0.2)" : "rgba(245,158,11,0.1)"}`, marginBottom: 10 }}>
        <canvas ref={canvasRef} width={680} height={260} style={{ width: "100%", display: "block", borderRadius: 12 }} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 180px", gap: 10 }}>
        <div>
          {/* Controls */}
          {!running && !stopped && !failed && (
            <button onClick={startBelt} style={{
              display: "block", width: "100%", padding: "14px", borderRadius: 10,
              cursor: "pointer", background: "rgba(16,185,129,0.08)", border: "2px solid rgba(16,185,129,0.2)",
              fontSize: 16, fontWeight: 700, color: "#059669", marginBottom: 10,
            }}>Start the belt</button>
          )}

          {running && (
            <>
              {/* Tension control — EML-1 */}
              <div style={{ marginBottom: 10, padding: "10px 14px", borderRadius: 10, background: "rgba(6,182,212,0.04)", border: "1px solid rgba(6,182,212,0.1)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 10, fontWeight: 600, color: "#06B6D4", textTransform: "uppercase", letterSpacing: 1 }}>Belt tension</span>
                  <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "#06B6D4" }}>EML-1 exponential</span>
                </div>
                <input type="range" min="20" max="100" value={tension} onChange={e => setTension(Number(e.target.value))}
                  style={{ width: "100%", accentColor: "#06B6D4" }} />
                <div style={{ fontSize: 11, color: "var(--color-text-secondary, #888)", marginTop: 2 }}>
                  {tension < 40 ? "Too loose — belt slips" : tension > 75 ? "High tension — accelerated wear" : "Normal range"}
                </div>
              </div>

              {/* Speed control */}
              <div style={{ marginBottom: 10, padding: "10px 14px", borderRadius: 10, background: "rgba(167,139,250,0.04)", border: "1px solid rgba(167,139,250,0.1)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 10, fontWeight: 600, color: "#A78BFA", textTransform: "uppercase", letterSpacing: 1 }}>Belt speed</span>
                  <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "#A78BFA" }}>{speed} ft/min</span>
                </div>
                <input type="range" min="20" max="120" value={speed} onChange={e => setSpeed(Number(e.target.value))}
                  style={{ width: "100%", accentColor: "#A78BFA" }} />
              </div>

              {/* STOP BUTTON */}
              <button onClick={stopBelt} style={{
                display: "block", width: "100%", padding: "16px", borderRadius: 10,
                cursor: "pointer", background: "rgba(239,68,68,0.08)", border: "2px solid rgba(239,68,68,0.2)",
                fontSize: 18, fontWeight: 700, color: "#EF4444",
              }}>STOP THE BELT</button>
              <div style={{ fontSize: 10, color: "var(--color-text-secondary, #999)", textAlign: "center", marginTop: 4 }}>
                Listen. Watch the gauges. Trust your gut. Stop it before it breaks.
              </div>
            </>
          )}

          {/* Score */}
          {score && (
            <div style={{
              marginTop: 10, padding: "16px 20px", borderRadius: 12,
              background: score.grade === "perfect" ? "rgba(253,230,138,0.06)" : score.grade === "failed" ? "rgba(239,68,68,0.06)" : score.grade === "good" ? "rgba(16,185,129,0.06)" : "rgba(139,92,246,0.06)",
              border: `1.5px solid ${score.grade === "perfect" ? "rgba(253,230,138,0.15)" : score.grade === "failed" ? "rgba(239,68,68,0.15)" : score.grade === "good" ? "rgba(16,185,129,0.15)" : "rgba(139,92,246,0.15)"}`,
              animation: "fadeIn 0.5s ease",
            }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: score.grade === "perfect" ? "#FDE68A" : score.grade === "failed" ? "#EF4444" : score.grade === "good" ? "#10B981" : "#A78BFA", marginBottom: 6 }}>
                {score.grade === "perfect" ? "Perfect call." : score.grade === "failed" ? "Belt destroyed." : score.grade === "good" ? "Good instinct." : "Too early."}
              </div>
              <div style={{ fontSize: 12, color: "var(--color-text-secondary, #777)", lineHeight: 1.6 }}>{score.msg}</div>
              {score.grade === "perfect" && (
                <div style={{ fontSize: 11, color: "#FDE68A", fontStyle: "italic", marginTop: 8, fontFamily: "var(--font-mono)", lineHeight: 1.6 }}>
                  EML-2: logarithmic wear measurement told you the bearing was degrading.<br />
                  EML-3: oscillatory signature confirmed it. You read both strata correctly.
                </div>
              )}
            </div>
          )}

          {(stopped || failed) && (
            <button onClick={startBelt} style={{
              display: "block", width: "100%", marginTop: 8, padding: "10px", borderRadius: 8,
              border: "1.5px solid var(--color-border-tertiary, #ddd)",
              background: "var(--color-background-primary, white)", color: "var(--color-text-secondary, #666)",
              fontSize: 11, cursor: "pointer",
            }}>Run another belt</button>
          )}
        </div>

        {/* RIGHT PANEL — gauges */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {/* Health gauge */}
          <div style={{ padding: "10px 12px", borderRadius: 10, background: "var(--color-background-secondary, #faf5ff)", border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))" }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: healthColor, textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Belt health</div>
            <div style={{ fontSize: 26, fontWeight: 700, fontFamily: "var(--font-mono)", color: healthColor }}>{Math.round(health)}%</div>
            <div style={{ height: 6, borderRadius: 3, background: "rgba(0,0,0,0.06)", overflow: "hidden", marginTop: 4 }}>
              <div style={{ height: "100%", width: `${health}%`, background: healthColor, borderRadius: 3, transition: "width 0.3s, background 0.3s" }} />
            </div>
          </div>

          {/* Wear depth gauge — EML-2 */}
          <div style={{ padding: "10px 12px", borderRadius: 10, background: "rgba(139,92,246,0.03)", border: "1px solid rgba(139,92,246,0.08)" }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#8B5CF6", textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>Wear depth</div>
            <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "var(--font-mono)", color: "#8B5CF6" }}>{wearDepth.toFixed(2)} mm</div>
            <div style={{ fontSize: 9, color: "var(--color-text-secondary, #999)" }}>EML-2: logarithmic</div>
          </div>

          {/* Vibration gauge — EML-3 */}
          <div style={{ padding: "10px 12px", borderRadius: 10, background: "rgba(236,72,153,0.03)", border: "1px solid rgba(236,72,153,0.08)" }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "#EC4899", textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>Vibration</div>
            <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "var(--font-mono)", color: "#EC4899" }}>{(vibrationLevel * 100).toFixed(0)}%</div>
            <div style={{ fontSize: 9, color: "var(--color-text-secondary, #999)" }}>EML-3: oscillatory</div>
            <div style={{ fontSize: 9, color: vibrationLevel > 0.5 ? "#EC4899" : "var(--color-text-secondary, #bbb)", marginTop: 2, fontStyle: "italic" }}>
              {vibrationLevel < 0.15 ? "Normal" : vibrationLevel < 0.4 ? "Elevated — listen..." : vibrationLevel < 0.7 ? "High — bearing degrading" : "Critical — act NOW"}
            </div>
          </div>

          {/* Time */}
          <div style={{ padding: "10px 12px", borderRadius: 10, background: "var(--color-background-secondary, #faf5ff)", border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))" }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "var(--color-text-secondary, #999)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>Runtime</div>
            <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--color-text-primary, #333)" }}>{time.toFixed(1)}s</div>
          </div>

          {/* The depth hierarchy revealed */}
          {depthRevealed.length > 0 && (
            <div style={{ padding: "8px 10px", borderRadius: 8, background: "rgba(253,230,138,0.03)", border: "1px solid rgba(253,230,138,0.08)" }}>
              <div style={{ fontSize: 8, fontWeight: 600, color: "#FDE68A", textTransform: "uppercase", letterSpacing: 1, marginBottom: 3 }}>The hierarchy</div>
              {depthRevealed.includes(0) && <div style={{ fontSize: 9, color: "#64748B" }}>0: belt segments</div>}
              {depthRevealed.includes(1) && <div style={{ fontSize: 9, color: "#06B6D4" }}>1: tension stress</div>}
              {depthRevealed.includes(2) && <div style={{ fontSize: 9, color: "#8B5CF6" }}>2: wear measurement</div>}
              {depthRevealed.includes(3) && <div style={{ fontSize: 9, color: "#EC4899" }}>3: vibration pattern</div>}
              {(failed || (stopped && score?.grade === "perfect")) && <div style={{ fontSize: 9, color: "#FDE68A" }}>∞: your knowing</div>}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: "0.75rem 1rem", marginTop: 12,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          A conveyor belt contains the full EML hierarchy. Belt segments are discrete (EML-0). Tension follows exponential stress curves (EML-1).
          Wear depth is measured logarithmically (EML-2). Bearing vibration is an oscillatory signature (EML-3). Catastrophic failure is
          EML-∞ onset — the threshold where finite measurements no longer predict the cascade. Read EML-2 (wear depth) and EML-3 (vibration) together. Stop before the threshold.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.org" target="_blank" rel="noopener noreferrer" style={{ color: "#F59E0B", textDecoration: "none", fontWeight: 500 }}>monogate.org</a>
        {" · "}
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none" }}>monogate.dev</a>
      </div>

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }`}</style>
    </div>
  );
}
