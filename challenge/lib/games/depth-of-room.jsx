import { useState, useRef, useEffect, useCallback } from "react";

const DEPTH_BANDS = [
  { id: 0, label: "EML-0", name: "Silence / Discrete", color: "#64748B",
    desc: "Quiet. Isolated clicks. Digital sounds. The absence of pattern.",
    examples: "keyboard clicks, dripping faucet, clock tick" },
  { id: 1, label: "EML-1", name: "Steady State / Drone", color: "#06B6D4",
    desc: "Continuous hum. Constant energy. Something running without variation.",
    examples: "fan, refrigerator, traffic drone, air conditioning" },
  { id: 2, label: "EML-2", name: "Information / Speech", color: "#8B5CF6",
    desc: "Structured variation. Information being exchanged. Measurement.",
    examples: "conversation, podcast, TV news, typing rhythm" },
  { id: 3, label: "EML-3", name: "Oscillation / Music", color: "#EC4899",
    desc: "Rhythmic pattern. Periodicity. Waves. Something that repeats and varies.",
    examples: "music, birdsong, sirens, rhythmic machinery" },
  { id: "inf", label: "EML-∞", name: "Complex / Irreducible", color: "#FDE68A",
    desc: "Too complex to classify. Multiple layers. A city. A forest. A crowd.",
    examples: "busy cafe, thunderstorm, construction site, concert" },
];

export default function DepthOfRoom() {
  const [listening, setListening] = useState(false);
  const [permission, setPermission] = useState(null);
  const [dominantDepth, setDominantDepth] = useState(null);
  const [depthScores, setDepthScores] = useState({ 0: 0, 1: 0, 2: 0, 3: 0, inf: 0 });
  const [history, setHistory] = useState([]);
  const [elapsed, setElapsed] = useState(0);
  const [done, setDone] = useState(false);

  const canvasRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);
  const acRef = useRef(null);
  const frameRef = useRef(null);
  const startRef = useRef(0);
  const dataRef = useRef(null);

  const LISTEN_DURATION = 12;

  const classifyFrame = useCallback((dataArray, bufferLength) => {
    // Energy in frequency bands
    const nyquist = 22050;
    const binWidth = nyquist / bufferLength;

    let totalEnergy = 0;
    let lowEnergy = 0;     // 0-200Hz: drones, hums
    let midEnergy = 0;     // 200-2000Hz: speech, information
    let highEnergy = 0;    // 2000-8000Hz: sibilance, brightness
    let veryHighEnergy = 0; // 8000+: noise, complexity

    for (let i = 0; i < bufferLength; i++) {
      const freq = i * binWidth;
      const val = dataArray[i] / 255;
      const energy = val * val;
      totalEnergy += energy;
      if (freq < 200) lowEnergy += energy;
      else if (freq < 2000) midEnergy += energy;
      else if (freq < 8000) highEnergy += energy;
      else veryHighEnergy += energy;
    }

    if (totalEnergy < 0.5) return 0; // Silence = EML-0

    const lowRatio = lowEnergy / totalEnergy;
    const midRatio = midEnergy / totalEnergy;
    const highRatio = highEnergy / totalEnergy;
    const veryHighRatio = veryHighEnergy / totalEnergy;

    // Spectral flatness — measure of how noise-like the signal is
    let logSum = 0, linSum = 0;
    for (let i = 1; i < bufferLength; i++) {
      const val = Math.max(dataArray[i], 1) / 255;
      logSum += Math.log(val);
      linSum += val;
    }
    const geometricMean = Math.exp(logSum / (bufferLength - 1));
    const arithmeticMean = linSum / (bufferLength - 1);
    const flatness = arithmeticMean > 0 ? geometricMean / arithmeticMean : 0;

    // Spectral variation — detect periodicity by comparing consecutive frames
    // High variation = speech/music. Low variation = drone.

    // Classification logic
    if (totalEnergy < 2) {
      return 0; // EML-0: very quiet, discrete
    }

    if (flatness > 0.6 && totalEnergy > 15) {
      return "inf"; // EML-∞: very flat spectrum = complex noise (crowd, construction)
    }

    if (lowRatio > 0.6 && midRatio < 0.25) {
      return 1; // EML-1: dominated by low frequency drone
    }

    if (midRatio > 0.4 && highRatio > 0.15) {
      // Could be speech (EML-2) or music (EML-3)
      // Music tends to have more periodic structure — harder to detect without temporal analysis
      // Use high frequency content as proxy: music has more harmonic highs
      if (highRatio > 0.25) {
        return 3; // EML-3: strong harmonics = music/oscillatory
      }
      return 2; // EML-2: mid-heavy with some high = speech/information
    }

    if (midRatio > 0.35) {
      return 2; // EML-2: mid-frequency dominant = information
    }

    if (highRatio > 0.3) {
      return 3; // EML-3: high harmonic content = oscillatory
    }

    return 1; // Default: steady state
  }, []);

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      setPermission(true);
      setListening(true);
      setDone(false);
      setHistory([]);
      setDepthScores({ 0: 0, 1: 0, 2: 0, 3: 0, inf: 0 });
      setElapsed(0);

      const ac = new (window.AudioContext || window.webkitAudioContext)();
      acRef.current = ac;
      const source = ac.createMediaStreamSource(stream);
      const analyser = ac.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
      analyserRef.current = analyser;

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      dataRef.current = dataArray;

      startRef.current = performance.now();

      const tick = () => {
        const now = performance.now();
        const secs = (now - startRef.current) / 1000;
        setElapsed(secs);

        if (secs >= LISTEN_DURATION) {
          // Done
          setListening(false);
          setDone(true);
          stream.getTracks().forEach(t => t.stop());
          try { ac.close(); } catch {}
          return;
        }

        analyser.getByteFrequencyData(dataArray);
        const depth = classifyFrame(dataArray, bufferLength);
        setDominantDepth(depth);
        setDepthScores(prev => ({ ...prev, [depth]: (prev[depth] || 0) + 1 }));
        setHistory(prev => [...prev.slice(-120), depth]);

        frameRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch (err) {
      setPermission(false);
    }
  };

  // Canvas — real-time spectrogram colored by depth
  useEffect(() => {
    const c = canvasRef.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height;
    let animFrame;
    let col = 0;

    const draw = () => {
      if (listening && analyserRef.current && dataRef.current) {
        analyserRef.current.getByteFrequencyData(dataRef.current);
        const bufferLength = analyserRef.current.frequencyBinCount;

        // Draw one column of spectrogram
        const barHeight = h / 64;
        for (let i = 0; i < 64; i++) {
          const idx = Math.floor(i * bufferLength / 64);
          const val = dataRef.current[idx] / 255;

          const band = DEPTH_BANDS.find(b => b.id === dominantDepth) || DEPTH_BANDS[0];
          const r = parseInt(band.color.slice(1, 3), 16);
          const g = parseInt(band.color.slice(3, 5), 16);
          const b2 = parseInt(band.color.slice(5, 7), 16);

          ctx.fillStyle = `rgba(${r},${g},${b2},${val * 0.8})`;
          ctx.fillRect(col, h - (i + 1) * barHeight, 3, barHeight);
        }
        col = (col + 3) % w;

        // Draw cursor line
        ctx.fillStyle = "rgba(255,255,255,0.3)";
        ctx.fillRect(col, 0, 1, h);
        // Clear ahead
        ctx.fillStyle = "rgba(6,2,14,0.8)";
        ctx.fillRect(col + 1, 0, 20, h);
      } else if (!listening && !done) {
        // Idle
        ctx.fillStyle = "rgba(6,2,14,0.02)";
        ctx.fillRect(0, 0, w, h);
        ctx.fillStyle = "rgba(167,139,250,0.04)";
        ctx.font = "12px monospace"; ctx.textAlign = "center";
        ctx.fillText("waiting to listen...", w / 2, h / 2);
      }

      animFrame = requestAnimationFrame(draw);
    };
    ctx.fillStyle = "#06020E"; ctx.fillRect(0, 0, w, h);
    draw();
    return () => cancelAnimationFrame(animFrame);
  }, [listening, dominantDepth, done]);

  // Cleanup
  useEffect(() => {
    return () => {
      cancelAnimationFrame(frameRef.current);
      try { streamRef.current?.getTracks().forEach(t => t.stop()); } catch {}
      try { acRef.current?.close(); } catch {}
    };
  }, []);

  // Final result — most dominant depth
  const totalSamples = Object.values(depthScores).reduce((a, b) => a + b, 0);
  const finalDepth = done ? Object.entries(depthScores).reduce((best, [k, v]) => v > best[1] ? [k, v] : best, ["0", 0])[0] : null;
  const finalBand = finalDepth !== null ? DEPTH_BANDS.find(b => String(b.id) === String(finalDepth)) : null;

  return (
    <div style={{ fontFamily: "var(--font-sans, system-ui, sans-serif)", maxWidth: 640, margin: "0 auto", padding: "0 0 2rem" }}>
      <div style={{ textAlign: "center", padding: "1rem 1rem 0.5rem" }}>
        <div style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#A78BFA", fontWeight: 500, marginBottom: 3 }}>monogate.dev</div>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 4px", color: "var(--color-text-primary, #1a1a2e)" }}>The Depth of This Room</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary, #6b7280)", margin: 0 }}>
          Your room has a mathematical depth. Let the equation listen.
        </p>
      </div>

      {/* Spectrogram canvas */}
      <div style={{ borderRadius: 14, overflow: "hidden", border: `1px solid ${dominantDepth !== null ? (DEPTH_BANDS.find(b => b.id === dominantDepth)?.color || "#A78BFA") + "20" : "rgba(167,139,250,0.1)"}`, marginBottom: 10 }}>
        <canvas ref={canvasRef} width={640} height={200} style={{ width: "100%", display: "block", borderRadius: 12 }} />
      </div>

      {/* Current depth indicator */}
      {listening && dominantDepth !== null && (
        <div style={{
          textAlign: "center", padding: "10px 16px", marginBottom: 10,
          background: `${DEPTH_BANDS.find(b => b.id === dominantDepth)?.color || "#888"}08`,
          border: `1.5px solid ${DEPTH_BANDS.find(b => b.id === dominantDepth)?.color || "#888"}20`,
          borderRadius: 10, animation: "fadeIn 0.2s ease", transition: "all 0.3s",
        }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: DEPTH_BANDS.find(b => b.id === dominantDepth)?.color, fontFamily: "var(--font-mono)" }}>
            {DEPTH_BANDS.find(b => b.id === dominantDepth)?.label}
          </div>
          <div style={{ fontSize: 13, color: "var(--color-text-primary, #333)", fontWeight: 500 }}>
            {DEPTH_BANDS.find(b => b.id === dominantDepth)?.name}
          </div>
          <div style={{ fontSize: 11, color: "var(--color-text-secondary, #888)", marginTop: 2, fontStyle: "italic" }}>
            {DEPTH_BANDS.find(b => b.id === dominantDepth)?.desc}
          </div>
        </div>
      )}

      {/* Progress */}
      {listening && (
        <div style={{ marginBottom: 10 }}>
          <div style={{ height: 4, borderRadius: 2, background: "var(--color-background-secondary, #eee)", overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${(elapsed / LISTEN_DURATION) * 100}%`, background: DEPTH_BANDS.find(b => b.id === dominantDepth)?.color || "#A78BFA", borderRadius: 2, transition: "width 0.2s" }} />
          </div>
          <div style={{ fontSize: 10, color: "var(--color-text-secondary, #999)", textAlign: "center", marginTop: 4 }}>
            Listening... {Math.ceil(LISTEN_DURATION - elapsed)}s remaining
          </div>
        </div>
      )}

      {/* Depth distribution */}
      {(listening || done) && totalSamples > 0 && (
        <div style={{ marginBottom: 10 }}>
          <div style={{ display: "flex", gap: 3, height: 40, borderRadius: 8, overflow: "hidden" }}>
            {DEPTH_BANDS.map(band => {
              const pct = totalSamples > 0 ? ((depthScores[band.id] || 0) / totalSamples) * 100 : 0;
              return pct > 0 ? (
                <div key={band.id} style={{
                  flex: pct, background: `${band.color}30`, borderLeft: `2px solid ${band.color}`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  minWidth: pct > 5 ? 30 : 0, transition: "flex 0.3s",
                }}>
                  {pct > 8 && <span style={{ fontSize: 9, color: band.color, fontWeight: 600, fontFamily: "var(--font-mono)" }}>{band.label}</span>}
                </div>
              ) : null;
            })}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
            {DEPTH_BANDS.map(band => {
              const pct = totalSamples > 0 ? ((depthScores[band.id] || 0) / totalSamples) * 100 : 0;
              return (
                <div key={band.id} style={{ textAlign: "center", flex: 1 }}>
                  <div style={{ fontSize: 9, color: pct > 10 ? band.color : "var(--color-text-secondary, #ccc)", fontFamily: "var(--font-mono)" }}>
                    {pct > 0 ? `${pct.toFixed(0)}%` : ""}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Start / Result */}
      {!listening && !done && (
        <div>
          <div style={{
            padding: "12px 16px", borderRadius: 10, marginBottom: 10,
            background: "rgba(245,158,11,0.04)", border: "1px solid rgba(245,158,11,0.12)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <span style={{ fontSize: 16 }}>🎤</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: "#D97706" }}>Microphone Required</span>
            </div>
            <div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", lineHeight: 1.6 }}>
              This experience uses your device microphone to listen to ambient sound for 12 seconds.
              Audio is analyzed locally in your browser — nothing is recorded, stored, or sent anywhere.
              Your browser will ask for microphone permission when you press Listen.
            </div>
          </div>
          <button onClick={startListening} style={{
            display: "block", width: "100%", padding: "16px 24px", borderRadius: 12,
            cursor: "pointer", textAlign: "center",
            background: "rgba(167,139,250,0.06)", border: "2px solid rgba(167,139,250,0.2)",
          }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#A78BFA" }}>Listen</div>
            <div style={{ fontSize: 11, color: "var(--color-text-secondary, #888)", marginTop: 2 }}>
              12 seconds. The equation will classify your environment.
            </div>
          </button>
        </div>
      )}

      {permission === false && (
        <div style={{ textAlign: "center", padding: 16, color: "#EF4444", fontSize: 12 }}>
          Microphone access denied. The experience needs to hear your room to classify it.
        </div>
      )}

      {/* Final result */}
      {done && finalBand && (
        <div style={{
          padding: "20px 24px", borderRadius: 14,
          background: `${finalBand.color}06`, border: `1.5px solid ${finalBand.color}15`,
          textAlign: "center", animation: "fadeIn 0.5s ease",
        }}>
          <div style={{ fontSize: 12, color: "var(--color-text-secondary, #999)", marginBottom: 4 }}>Your room is operating at</div>
          <div style={{ fontSize: 36, fontWeight: 700, color: finalBand.color, fontFamily: "var(--font-mono)" }}>{finalBand.label}</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-text-primary, #333)", marginBottom: 6 }}>{finalBand.name}</div>
          <div style={{ fontSize: 12, color: "var(--color-text-secondary, #777)", lineHeight: 1.6, marginBottom: 8 }}>{finalBand.desc}</div>
          <div style={{ fontSize: 11, color: "var(--color-text-secondary, #aaa)", fontStyle: "italic" }}>
            Common sounds at this depth: {finalBand.examples}
          </div>

          <div style={{ marginTop: 14, padding: "10px 14px", borderRadius: 8, background: `${finalBand.color}06` }}>
            <div style={{ fontSize: 11, color: "var(--color-text-secondary, #666)", lineHeight: 1.6 }}>
              {String(finalDepth) === "0" && "Your room is quiet. Discrete sounds, if any. This is the arithmetic floor — the simplest depth. Pure silence is EML-0, and so is a single clock tick."}
              {String(finalDepth) === "1" && "Your room has a steady hum. Something is running — a fan, a fridge, traffic outside. Constant energy with no variation. Exponential output, no oscillation. The growth stratum."}
              {String(finalDepth) === "2" && "Your room carries information. Someone is talking, or a screen is playing. Structured variation — the hallmark of measurement. Your environment is exchanging data."}
              {String(finalDepth) === "3" && "Your room is oscillating. Music, rhythmic machinery, birdsong — something with periodicity. Waves are present. Your environment is vibrating at EML-3: the stratum of sin(x), cos(x), and Fourier series."}
              {String(finalDepth) === "inf" && "Your room is complex beyond simple classification. Multiple layers of sound interacting. A city, a crowd, a storm. The depth hierarchy can classify each component, but the whole is irreducible. That's EML-∞."}
            </div>
          </div>

          <button onClick={startListening} style={{
            marginTop: 12, padding: "10px 20px", borderRadius: 8, cursor: "pointer",
            background: "rgba(167,139,250,0.06)", border: "1.5px solid rgba(167,139,250,0.15)",
            fontSize: 12, color: "#A78BFA", fontWeight: 500,
          }}>Listen again</button>
        </div>
      )}

      {/* Footer */}
      <div style={{
        padding: "0.75rem 1rem", marginTop: 12,
        background: "var(--color-background-secondary, #faf5ff)", borderRadius: 10,
        border: "0.5px solid var(--color-border-tertiary, rgba(0,0,0,0.06))",
      }}>
        <p style={{ fontSize: 12, color: "var(--color-text-secondary, #555)", margin: 0, lineHeight: 1.6 }}>
          Every room has a mathematical depth. Silence is EML-0. The hum of a refrigerator is EML-1.
          A conversation is EML-2 — information being exchanged. Music is EML-3 — oscillation, rhythm, waves.
          And the full complexity of a living space — layers of sound interacting in irreducible ways — approaches EML-∞.
          The equation classifies everything. Including the air around you, right now.
        </p>
      </div>

      <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--color-text-secondary, #999)" }}>
        <a href="https://monogate.org" target="_blank" rel="noopener noreferrer" style={{ color: "#A78BFA", textDecoration: "none", fontWeight: 500 }}>monogate.org</a>
        {" · "}
        <a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: "#06B6D4", textDecoration: "none" }}>monogate.dev</a>
      </div>

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }`}</style>
    </div>
  );
}
