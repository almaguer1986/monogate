import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Docs — monogate",
  description: "API reference and quickstart for the monogate EML operator library.",
};

const C = {
  bg: "#08090e", surface: "#0d0f18", border: "#1c1f2e",
  text: "#d4d4d4", muted: "#4a4d62", orange: "#e8a020",
  blue: "#6ab0f5", green: "#4ade80", purple: "#a78bfa",
};

function Code({ children }: { children: string }) {
  return (
    <pre style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, padding: "14px 16px", fontSize: 12, color: C.green, overflowX: "auto", margin: "12px 0" }}>
      {children}
    </pre>
  );
}

function H2({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: 10, color: C.orange, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 12, marginTop: 36 }}>{children}</div>;
}

export default function DocsPage() {
  return (
    <div style={{ background: C.bg, minHeight: "100vh", maxWidth: 680, margin: "0 auto", padding: "0 16px 80px" }}>

      <nav style={{ borderBottom: `1px solid ${C.border}`, padding: "16px 0", marginBottom: 36, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <a href="/" style={{ fontSize: 13, fontWeight: 700, color: C.orange, letterSpacing: "0.06em", textDecoration: "none" }}>monogate</a>
        <div style={{ display: "flex", gap: 20 }}>
          {[
            { href: "/explorer", label: "Explorer" },
            { href: "/challenge", label: "Challenge" },
            { href: "/play", label: "Play" },
            { href: "/docs", label: "Docs", active: true },
            { href: "https://monogate.org", label: "Research ↗", external: true },
          ].map(({ href, label, active, external }) => (
            <a key={label} href={href}
              {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
              style={{ fontSize: 12, color: active ? C.text : C.muted, textDecoration: "none" }}
            >{label}</a>
          ))}
        </div>
      </nav>

      <h1 style={{ fontSize: 26, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", marginBottom: 8 }}>Documentation</h1>
      <p style={{ fontSize: 13, color: C.muted, marginBottom: 36 }}>monogate — EML operator library · <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>arXiv:2603.21852</a></p>

      <H2>Install</H2>
      <Code>{`npm install monogate      # JavaScript / TypeScript
pip install monogate     # Python`}</Code>

      <H2>Quickstart — JavaScript</H2>
      <Code>{`import { eml, evalTree, countNodes } from "monogate";

// Build an EML tree
const tree = eml(1, eml(1, 1));  // eml(1, eml(1,1))

// Evaluate at a point
const result = evalTree(tree, { x: 1.0 });

// Count nodes
const n = countNodes(tree);  // integer`}</Code>

      <H2>Quickstart — Python</H2>
      <Code>{`from monogate import eml, eval_tree, count_nodes

# Build a tree
tree = eml(1, eml(1, 1))

# Evaluate
result = eval_tree(tree, x=1.0)

# Count nodes
n = count_nodes(tree)`}</Code>

      <H2>The operator</H2>
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "16px 20px", fontSize: 13, color: C.text, lineHeight: 1.8 }}>
        <div style={{ fontFamily: "monospace", fontSize: 16, color: C.orange, marginBottom: 10 }}>eml(x, y) = exp(x) − ln(y)</div>
        <div style={{ fontSize: 11, color: C.muted }}>
          Grammar: S → 1 | eml(S, S)<br />
          Principal-branch ln · ln(0) is undefined (throws)<br />
          Terminal: constant 1, variable x
        </div>
      </div>

      <H2>Links</H2>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {[
          { href: "https://github.com/almaguer1986/monogate", label: "GitHub — source code" },
          { href: "https://www.npmjs.com/package/monogate", label: "npm — JavaScript package" },
          { href: "https://pypi.org/project/monogate/", label: "PyPI — Python package" },
          { href: "https://arxiv.org/abs/2603.21852", label: "arXiv:2603.21852 — Odrzywołek 2026" },
          { href: "https://monogate.org", label: "monogate.org — research essays and theorem catalog" },
        ].map(({ href, label }) => (
          <a key={href} href={href} target="_blank" rel="noopener noreferrer"
            style={{ fontSize: 13, color: C.blue, textDecoration: "none" }}
          >→ {label}</a>
        ))}
      </div>

      <footer style={{ borderTop: `1px solid ${C.border}`, paddingTop: 20, marginTop: 48, fontSize: 10, color: C.muted }}>
        <a href="/" style={{ color: C.muted }}>← monogate.dev</a>
      </footer>
    </div>
  );
}
