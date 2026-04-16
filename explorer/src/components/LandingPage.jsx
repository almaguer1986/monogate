// explorer/src/components/LandingPage.jsx
// Landing page — shown on first visit (no URL params).
// onEnter(tab?) — enters the explorer, optionally jumping to a specific tab.

const C = {
  bg:      "#07080f",
  surface: "#0d0e1c",
  border:  "#191b2e",
  text:    "#cdd0e0",
  muted:   "#4e5168",
  accent:  "#e8a020",
  green:   "#5ec47a",
};

const BENCH = [
  { op: "sin(x)  8-term Taylor", best: 63,  eml: 245, pct: 74 },
  { op: "pow(x, n)",             best: 3,   eml: 15,  pct: 80 },
  { op: "div(x, y)",             best: 1,   eml: 15,  pct: 93 },
  { op: "ln(x)",                 best: 1,   eml: 3,   pct: 67 },
];

const IS     = ["Symbolic math optimizer", "Research & educational tool", "Scalar / embedded math", "Novel operator theory results"];
const IS_NOT = ["PyTorch inference accelerator", "Faster than torch.sin (9,000×)", "General ML optimization library", "Production-ready for most models"];

function NavLink({ label, tab, onEnter, accent }) {
  const base = {
    padding: "8px 14px", fontSize: 10, borderRadius: 4,
    border: `1px solid ${accent ? C.accent : C.border}`,
    color: accent ? C.accent : C.muted,
    background: accent ? "rgba(232,160,32,0.08)" : "transparent",
    cursor: "pointer", fontFamily: "'Space Mono', monospace",
    letterSpacing: "0.04em", fontWeight: accent ? 700 : 400,
    textDecoration: "none", display: "inline-block",
    transition: "color 0.15s, border-color 0.15s",
  };
  return (
    <button style={base} onClick={() => onEnter(tab)}
      onMouseEnter={e => { e.currentTarget.style.color = accent ? C.accent : C.text; e.currentTarget.style.borderColor = accent ? C.accent : C.muted; }}
      onMouseLeave={e => { e.currentTarget.style.color = accent ? C.accent : C.muted; e.currentTarget.style.borderColor = accent ? C.accent : C.border; }}
    >
      {label}
    </button>
  );
}

export default function LandingPage({ onEnter }) {
  return (
    <div style={{
      background: C.bg, minHeight: "100vh", color: C.text,
      fontFamily: "'Space Mono', monospace",
      padding: "60px 24px 100px",
      boxSizing: "border-box",
    }}>
      <div style={{ maxWidth: 760, margin: "0 auto" }}>

        {/* ── Headline ─────────────────────────────────────────────────── */}
        <div style={{ marginBottom: 40 }}>
          <div style={{
            fontSize: 10, color: C.muted, letterSpacing: "0.14em",
            textTransform: "uppercase", marginBottom: 20,
          }}>
            arXiv:2603.21852 · Odrzywołek 2026
          </div>

          <h1 style={{
            fontSize: "clamp(44px, 9vw, 76px)", fontWeight: 700,
            color: "#fff", margin: "0 0 14px",
            letterSpacing: "-0.03em", lineHeight: 1,
          }}>
            monogate
          </h1>

          <p style={{
            fontSize: "clamp(14px, 2.2vw, 17px)", color: C.muted,
            margin: "0 0 24px", lineHeight: 1.6, maxWidth: 540,
          }}>
            A symbolic math optimizer built on a single binary operator.
            Every elementary function as a finite binary tree.
          </p>

          <code style={{
            display: "inline-block",
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 5, padding: "9px 16px",
            fontSize: 13, color: C.accent,
          }}>
            eml(x, y) = exp(x) − ln(y)
          </code>
        </div>

        {/* ── Primary CTA ──────────────────────────────────────────────── */}
        <div style={{ marginBottom: 64 }}>
          <button
            onClick={() => onEnter("calc")}
            style={{
              background: C.accent, color: "#000", fontWeight: 700,
              border: "none", borderRadius: 7,
              padding: "14px 32px", fontSize: 14, cursor: "pointer",
              fontFamily: "'Space Mono', monospace",
              letterSpacing: "0.02em", marginRight: 10,
            }}
            onMouseEnter={e => { e.currentTarget.style.opacity = "0.88"; }}
            onMouseLeave={e => { e.currentTarget.style.opacity = "1"; }}
          >
            Open Explorer →
          </button>
          <span style={{ fontSize: 10, color: C.muted }}>
            calculator · tree visualizer · optimizer · challenge board
          </span>
        </div>

        {/* ── Key findings ─────────────────────────────────────────────── */}
        <Section label="What we found">
          {[
            {
              label: "BEST hybrid routing",
              body: "Routes each primitive to its cheapest operator — EXL for ln/pow, EDL for div/mul, EML for add/sub. Cuts total tree size by up to 74% vs pure EML.",
            },
            {
              label: "Phantom attractor phase transition",
              body: "EML gradient descent traps at spurious minima in 100% of trials at λ=0. Complexity penalty λ=0.005 flips convergence to 100% — a sharp phase transition.",
            },
            {
              label: "sin(x) conjecture",
              body: "862,116 real-valued EML trees enumerated (N≤8). No exact construction found for sin(x) from terminal {1}. The infinite-zeros barrier suggests none exists for any N.",
            },
          ].map(({ label, body }) => (
            <div key={label} style={{
              display: "flex", gap: 14, marginBottom: 14,
              paddingBottom: 14, borderBottom: `1px solid ${C.border}`,
            }}>
              <div style={{ width: 3, minWidth: 3, borderRadius: 2, background: C.accent }} />
              <div>
                <div style={{ fontSize: 11, color: C.text, fontWeight: 700, marginBottom: 4 }}>
                  {label}
                </div>
                <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.7 }}>{body}</div>
              </div>
            </div>
          ))}
        </Section>

        {/* ── Benchmark table ──────────────────────────────────────────── */}
        <Section label="Measured node savings">
          <div style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 8, overflow: "hidden",
          }}>
            <div style={{
              display: "grid", gridTemplateColumns: "2fr 72px 72px 64px 1fr",
              padding: "7px 16px", borderBottom: `1px solid ${C.border}`,
              fontSize: 8, color: C.muted, letterSpacing: "0.10em", textTransform: "uppercase",
            }}>
              {["Operation", "BEST", "EML", "Saving", ""].map((h, i) => (
                <div key={i} style={{ textAlign: i > 0 ? "right" : "left" }}>{h}</div>
              ))}
            </div>

            {BENCH.map(({ op, best, eml, pct }, i) => (
              <div key={op} style={{
                display: "grid", gridTemplateColumns: "2fr 72px 72px 64px 1fr",
                padding: "10px 16px", alignItems: "center",
                borderBottom: i < BENCH.length - 1 ? `1px solid ${C.border}` : "none",
                background: i % 2 ? "rgba(255,255,255,0.012)" : "transparent",
              }}>
                <div style={{ fontSize: 10, color: C.text }}>{op}</div>
                <div style={{ fontSize: 11, color: C.accent, textAlign: "right", fontWeight: 700 }}>{best}n</div>
                <div style={{ fontSize: 10, color: C.muted, textAlign: "right", textDecoration: "line-through" }}>{eml}n</div>
                <div style={{ fontSize: 11, color: C.green, textAlign: "right", fontWeight: 700 }}>−{pct}%</div>
                <div style={{ paddingLeft: 12 }}>
                  <div style={{ height: 4, borderRadius: 2, background: C.border, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${pct}%`, background: C.green, borderRadius: 2 }} />
                  </div>
                </div>
              </div>
            ))}

            <div style={{
              padding: "8px 16px", borderTop: `1px solid ${C.border}`,
              fontSize: 9, color: C.muted, lineHeight: 1.7,
            }}>
              ~20% savings needed to cross the Python call-overhead threshold.
              At 74%, sin/cos deliver <span style={{ color: C.green }}>2.8–3.4× wall-clock speedup</span>.
            </div>
          </div>
        </Section>

        {/* ── Is / Is not ──────────────────────────────────────────────── */}
        <Section label="What it is — what it isn't">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div style={{
              background: "rgba(94,196,122,0.04)",
              border: "1px solid rgba(94,196,122,0.18)",
              borderRadius: 8, padding: "14px 16px",
            }}>
              <div style={{ fontSize: 8, color: C.green, letterSpacing: "0.10em", textTransform: "uppercase", marginBottom: 12, fontWeight: 700 }}>
                This is
              </div>
              {IS.map(s => (
                <div key={s} style={{ display: "flex", gap: 8, marginBottom: 8, fontSize: 10, color: C.text, lineHeight: 1.5 }}>
                  <span style={{ color: C.green, flexShrink: 0 }}>+</span>{s}
                </div>
              ))}
            </div>
            <div style={{
              background: "rgba(78,81,104,0.07)",
              border: `1px solid ${C.border}`,
              borderRadius: 8, padding: "14px 16px",
            }}>
              <div style={{ fontSize: 8, color: C.muted, letterSpacing: "0.10em", textTransform: "uppercase", marginBottom: 12, fontWeight: 700 }}>
                Not this
              </div>
              {IS_NOT.map(s => (
                <div key={s} style={{ display: "flex", gap: 8, marginBottom: 8, fontSize: 10, color: C.muted, lineHeight: 1.5 }}>
                  <span style={{ flexShrink: 0 }}>−</span>{s}
                </div>
              ))}
            </div>
          </div>
        </Section>

        {/* ── Explorer nav ─────────────────────────────────────────────── */}
        <Section label="Jump to">
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <NavLink label="✦ calc"    tab="calc"    onEnter={onEnter} accent />
            <NavLink label="⚙ opt"     tab="opt"     onEnter={onEnter} />
            <NavLink label="⬡ nerf"    tab="nerf"    onEnter={onEnter} />
            <NavLink label="✦ viz"     tab="viz"     onEnter={onEnter} />
            <NavLink label="sin↗"      tab="sinex"   onEnter={onEnter} />
            <NavLink label="⚡ demo"   tab="demo"    onEnter={onEnter} />
            <NavLink label="⊞ board"   tab="board"   onEnter={onEnter} />
            <NavLink label="table"     tab="table"   onEnter={onEnter} />
            <NavLink label="verify"    tab="verify"  onEnter={onEnter} />
          </div>
        </Section>

        {/* ── External links ───────────────────────────────────────────── */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 56 }}>
          {[
            { label: "GitHub",  href: "https://github.com/almaguer1986/monogate" },
            { label: "npm",     href: "https://www.npmjs.com/package/monogate" },
            { label: "PyPI",    href: "https://pypi.org/project/monogate/" },
            { label: "arXiv",   href: "https://arxiv.org/abs/2603.21852" },
          ].map(({ label, href }) => (
            <a key={label} href={href} target="_blank" rel="noreferrer" style={{
              padding: "7px 14px", fontSize: 10, borderRadius: 4,
              border: `1px solid ${C.border}`, color: C.muted,
              textDecoration: "none", fontFamily: "'Space Mono', monospace",
              letterSpacing: "0.04em",
              transition: "color 0.15s, border-color 0.15s",
            }}
              onMouseEnter={e => { e.currentTarget.style.color = C.text; e.currentTarget.style.borderColor = C.muted; }}
              onMouseLeave={e => { e.currentTarget.style.color = C.muted; e.currentTarget.style.borderColor = C.border; }}
            >
              {label}
            </a>
          ))}
        </div>

        {/* ── Footer ───────────────────────────────────────────────────── */}
        <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 20, fontSize: 9, color: C.muted, lineHeight: 2 }}>
          Based on{" "}
          <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noreferrer"
            style={{ color: C.muted, textDecoration: "underline" }}>
            arXiv:2603.21852
          </a>
          {" "}· Odrzywołek 2026 · CC BY 4.0
          <span style={{ color: "#1e2030", marginLeft: 12 }}>
            github.com/almaguer1986/monogate
          </span>
        </div>

      </div>
    </div>
  );
}

function Section({ label, children }) {
  return (
    <div style={{ marginBottom: 44 }}>
      <div style={{
        fontSize: 8, color: C.muted, letterSpacing: "0.14em",
        textTransform: "uppercase", marginBottom: 14,
      }}>
        {label}
      </div>
      {children}
    </div>
  );
}
