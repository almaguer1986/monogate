import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "monogate — EML operator library",
  description:
    "monogate is a library for the EML operator: eml(x, y) = exp(x) − ln(y). " +
    "Explorer, challenge board, search tool, and open problems.",
};

const C = {
  bg: "#08090e",
  surface: "#0d0f18",
  border: "#1c1f2e",
  border2: "#252836",
  text: "#d4d4d4",
  muted: "#4a4d62",
  orange: "#e8a020",
  blue: "#6ab0f5",
  green: "#4ade80",
  purple: "#a78bfa",
};

const SECTIONS = [
  {
    href: "/explorer",
    label: "Explorer",
    desc: "Build and optimize EML expression trees interactively.",
    color: C.blue,
    tag: "tool",
  },
  {
    href: "/challenge",
    label: "Challenge Board",
    desc: "Open problems: construct sin, cos, π, i from eml(x,y) = exp(x) − ln(y). Submit a construction, get credited permanently.",
    color: C.orange,
    tag: "challenge",
  },
  {
    href: "/play",
    label: "Play",
    desc: "Games and interactive experiments built on the EML grammar.",
    color: C.green,
    tag: "games",
  },
  {
    href: "/docs",
    label: "Docs",
    desc: "API reference, quickstart, and tutorial for the monogate library.",
    color: C.purple,
    tag: "docs",
  },
];

export default function LandingPage() {
  return (
    <div style={{ background: C.bg, minHeight: "100vh", maxWidth: 680, margin: "0 auto", padding: "0 16px 80px" }}>

      {/* Nav */}
      <nav style={{ borderBottom: `1px solid ${C.border}`, padding: "16px 0", marginBottom: 60, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: C.orange, letterSpacing: "0.06em" }}>monogate</span>
        <div style={{ display: "flex", gap: 20 }}>
          {[
            { href: "/explorer", label: "Explorer" },
            { href: "/challenge", label: "Challenge" },
            { href: "/play", label: "Play" },
            { href: "/docs", label: "Docs" },
            { href: "https://monogate.org", label: "Research ↗", external: true },
          ].map(({ href, label, external }) => (
            <a key={label} href={href}
              {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
              style={{ fontSize: 12, color: C.muted, textDecoration: "none" }}
            >{label}</a>
          ))}
        </div>
      </nav>

      {/* Hero */}
      <section style={{ marginBottom: 56 }}>
        <div style={{ fontSize: 11, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 16 }}>
          EML universal operator
        </div>
        <div style={{ fontSize: 36, fontWeight: 700, color: C.orange, fontFamily: "monospace", marginBottom: 16, letterSpacing: "-0.02em" }}>
          eml(x, y) = exp(x) − ln(y)
        </div>
        <p style={{ fontSize: 15, color: C.text, lineHeight: 1.8, maxWidth: 560, marginBottom: 24 }}>
          One binary operator. Every elementary function as a finite binary tree.
          Odrzywołek (2026) proves that exp, ln, sin, cos, tan, polynomials, and all
          elementary functions are finite compositions of eml with constant 1.
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <code style={{ fontSize: 12, color: C.green, background: "rgba(74,222,128,0.07)", border: `1px solid rgba(74,222,128,0.2)`, borderRadius: 4, padding: "6px 12px" }}>
            npm install monogate
          </code>
          <code style={{ fontSize: 12, color: C.purple, background: "rgba(167,139,250,0.07)", border: `1px solid rgba(167,139,250,0.2)`, borderRadius: 4, padding: "6px 12px" }}>
            pip install monogate
          </code>
        </div>
      </section>

      {/* Section cards */}
      <section style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 48 }}>
        {SECTIONS.map(({ href, label, desc, color, tag }) => (
          <a key={href} href={href} style={{ display: "block", background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "18px 22px", textDecoration: "none", color: "inherit" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8, marginBottom: 6 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color }}>{label}</div>
              <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color, background: `${color}15`, border: `1px solid ${color}30`, borderRadius: 3, padding: "2px 6px" }}>
                {tag}
              </span>
            </div>
            <div style={{ fontSize: 12, color: C.muted, lineHeight: 1.7 }}>{desc}</div>
          </a>
        ))}
      </section>

      {/* Links */}
      <footer style={{ borderTop: `1px solid ${C.border}`, paddingTop: 20, display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10, fontSize: 10, color: C.muted }}>
        <div style={{ display: "flex", gap: 16 }}>
          {[
            { href: "https://arxiv.org/abs/2603.21852", label: "arXiv:2603.21852" },
            { href: "https://github.com/almaguer1986/monogate", label: "GitHub" },
            { href: "https://www.npmjs.com/package/monogate", label: "npm" },
            { href: "https://monogate.org", label: "monogate.org" },
          ].map(({ href, label }) => (
            <a key={label} href={href} target="_blank" rel="noopener noreferrer" style={{ color: C.muted }}>{label}</a>
          ))}
        </div>
        <span>Odrzywołek 2026 · CC BY 4.0</span>
      </footer>
    </div>
  );
}
