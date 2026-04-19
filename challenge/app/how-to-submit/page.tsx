import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How to Submit — monogate.dev",
  description: "Grammar rules, validation details, and submission guide for EML challenge constructions.",
};

const C = {
  bg: "#08090e", surface: "#0d0f18", surface2: "#12151f",
  border: "#1c1f2e", border2: "#252836",
  text: "#d4d4d4", muted: "#4a4d62",
  orange: "#e8a020", blue: "#6ab0f5", green: "#4ade80", red: "#f87171",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: 36 }}>
      <div style={{ fontSize: 10, color: C.orange, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 12 }}>
        {title}
      </div>
      {children}
    </section>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "16px 20px" }}>
      {children}
    </div>
  );
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code style={{
      fontFamily: "'Space Mono', monospace", fontSize: 12,
      color: C.orange, background: "rgba(232,160,32,0.08)",
      padding: "1px 5px", borderRadius: 3,
    }}>
      {children}
    </code>
  );
}

function Row({ check, text, color }: { check: string; text: string; color: string }) {
  return (
    <div style={{ display: "flex", gap: 10, fontSize: 11, color: C.text, lineHeight: 1.9 }}>
      <span style={{ color, flexShrink: 0 }}>{check}</span>
      <span>{text}</span>
    </div>
  );
}

export default function HowToSubmitPage() {
  return (
    <div style={{ background: C.bg, minHeight: "100vh", maxWidth: 760, margin: "0 auto", padding: "0 16px 60px" }}>

      <header style={{ borderBottom: `1px solid ${C.border}`, padding: "28px 0 22px", marginBottom: 36 }}>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>
          <a href="/" style={{ color: C.muted, textDecoration: "none" }}>monogate.dev</a>
          {" / how to submit"}
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em" }}>
          How to Submit
        </div>
        <div style={{ marginTop: 10, fontSize: 11, color: C.muted, lineHeight: 1.8, maxWidth: 540 }}>
          A valid submission is a finite EML expression tree that equals the target function exactly
          (within floating-point tolerance) at all test points, built only from the allowed grammar.
        </div>
      </header>

      <Section title="The Grammar">
        <Card>
          <div style={{ fontSize: 13, color: C.orange, fontWeight: 700, marginBottom: 12 }}>
            eml(x, y) = exp(x) − ln(y)
          </div>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 16, lineHeight: 1.8 }}>
            One binary operator. One terminal. Every construction is a finite binary tree where
            every internal node is <Code>eml</Code>, every leaf is the constant <Code>1</Code>,
            the variable <Code>x</Code>, or a numeric literal.
          </div>
          <div style={{ fontFamily: "monospace", fontSize: 11, color: C.blue, lineHeight: 2,
            background: C.surface2, padding: "12px 16px", borderRadius: 6, marginBottom: 0 }}>
            S → 1{"\n"}
            S → x{"\n"}
            S → eml(S, S){"\n"}
          </div>
        </Card>
      </Section>

      <Section title="Available Primitives">
        <Card>
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 10 }}>
              Derived functions (all proven EML constructions)
            </div>
            {[
              ["exp(x)", "eml(x, 1)  — Nodes:1  Depth:1"],
              ["ln(x)", "eml(1, eml(eml(1, x), 1))  — Nodes:3  Depth:3"],
              ["neg(x)", "shift formula  — Nodes:9  Depth:5"],
              ["add(x, y)", "eml(ln(x), eml(neg(y), 1))  — Nodes:11  Depth:6"],
              ["sub(x, y)", "eml(ln(x), exp(y))  — Nodes:5  Depth:4"],
              ["mul(x, y)", "eml(add(ln(x), ln(y)), 1)  — Nodes:13  Depth:7"],
              ["div(x, y)", "eml(add(ln(x), neg(ln(y))), 1)  — Nodes:15  Depth:8"],
              ["pow(x, n)", "eml(mul(n, ln(x)), 1)  — Nodes:15  Depth:8"],
              ["recip(x)", "eml(neg(ln(x)), 1)  — Nodes:5  Depth:4"],
            ].map(([fn, desc]) => (
              <div key={fn} style={{ display: "flex", gap: 16, fontSize: 11, lineHeight: 1.9, flexWrap: "wrap" }}>
                <span style={{ color: C.orange, minWidth: 100 }}>{fn}</span>
                <span style={{ color: C.muted, fontFamily: "monospace", fontSize: 10 }}>{desc}</span>
              </div>
            ))}
          </div>
          <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 14 }}>
            <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 10 }}>
              Not allowed — these are the open problems
            </div>
            {["sin  cos  tan  π  i  Math.*  any trig identity"].map((item) => (
              <div key={item} style={{ fontSize: 11, color: C.muted, display: "flex", gap: 8 }}>
                <span style={{ color: C.red }}>✗</span> {item}
              </div>
            ))}
          </div>
        </Card>
      </Section>

      <Section title="How Validation Works">
        <Card>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {[
              {
                step: "01",
                title: "Syntax check",
                body: "Expression is scanned against an allowlist of EML primitives. Any reference to Math.*, sin, cos, tan, pi is rejected immediately.",
              },
              {
                step: "02",
                title: "Tree construction",
                body: "The expression is evaluated in a sandboxed context where every function returns a tree node instead of a number. This produces the full AST from which node count and depth are computed.",
              },
              {
                step: "03",
                title: "Numeric test cases",
                body: "The same expression is evaluated numerically at multiple known points. For sin(x): tested at x = 0, π/6, π/4, π/2, π, and −π/6. Error must be below 1×10⁻¹⁰ at each point.",
              },
              {
                step: "04",
                title: "Storage",
                body: "Valid and invalid submissions are both stored. Invalid submissions show the specific test case that failed and the actual error. All submissions are permanent — the full history is visible on each challenge page.",
              },
              {
                step: "05",
                title: "Record update",
                body: "If valid and fewer nodes than the current best, the challenge record updates automatically via a database trigger. Your name appears on the leaderboard immediately.",
              },
            ].map(({ step, title, body }) => (
              <div key={step} style={{ display: "flex", gap: 16 }}>
                <div style={{ fontSize: 11, color: C.muted, minWidth: 24, paddingTop: 1 }}>{step}</div>
                <div>
                  <div style={{ fontSize: 12, color: C.text, fontWeight: 700, marginBottom: 4 }}>{title}</div>
                  <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.7 }}>{body}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </Section>

      <Section title="What Counts as Valid">
        <Card>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <Row check="✓" color={C.green} text="Pure EML expression: only eml, exp, ln, neg, add, sub, mul, div, pow, recip, terminal 1, variable x, numeric literals." />
            <Row check="✓" color={C.green} text="Passes all numeric test cases within tolerance 1×10⁻¹⁰." />
            <Row check="✓" color={C.green} text="No intermediate step passes 0 as the y-argument of eml (which would call ln(0), undefined under strict grammar)." />
            <Row check="✗" color={C.red}   text="Math.sin, Math.cos, Math.PI — even if wrapped in an EML-looking expression." />
            <Row check="✗" color={C.red}   text="Extended-reals convention (ln(0) = −∞). This board validates strict principal-branch grammar only." />
            <Row check="✗" color={C.red}   text="Expressions that pass numeric tests by coincidence but don't implement the target function generally." />
          </div>
          <div style={{ marginTop: 14, paddingTop: 14, borderTop: `1px solid ${C.border}`, fontSize: 10, color: C.muted, lineHeight: 1.7 }}>
            Node counting includes every internal eml call in the full expanded tree — using <Code>neg(x)</Code> in your expression counts all 9 nodes of its internal construction, not 1.
          </div>
        </Card>
      </Section>

      <Section title="Attribution">
        <Card>
          <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.9 }}>
            Your name is attached to your submission permanently. If you hold the record and someone
            submits a shorter construction, their name becomes the new record holder — but your entry
            stays on the leaderboard with your original timestamp and node count. The full history
            of every valid construction is visible on the challenge page, ordered by node count.
            There is no deletion.
          </div>
        </Card>
      </Section>

      <Section title="Tips">
        <Card>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 11, color: C.muted, lineHeight: 1.7 }}>
            <div>
              <span style={{ color: C.text }}>Use the Explorer first.</span>{" "}
              <a href="https://explorer.monogate.dev" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>
                explorer.monogate.dev
              </a>{" "}
              has a tree visualizer and sandbox where you can build and test expressions interactively before submitting.
            </div>
            <div>
              <span style={{ color: C.text }}>Install monogate locally.</span>{" "}
              <Code>npm install monogate</Code> — then test your expression in Node before submitting.
            </div>
            <div>
              <span style={{ color: C.text }}>The complex extension.</span>{" "}
              The path to sin and cos runs through the complex plane:
              {" "}<Code>e^(ix) = cos(x) + i·sin(x)</Code>. Whether the strict grammar reaches i from terminal &#123;1&#125; alone is the open question that unlocks trig.
            </div>
            <div>
              <span style={{ color: C.text }}>Read the paper.</span>{" "}
              Odrzywołek (2026),{" "}
              <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>
                arXiv:2603.21852
              </a>. The proof techniques and known constructions are all there.
            </div>
          </div>
        </Card>
      </Section>

      <footer style={{
        marginTop: 48, paddingTop: 20, borderTop: `1px solid ${C.border}`,
        display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10,
        fontSize: 10, color: C.muted,
      }}>
        <a href="/challenge" style={{ color: C.muted }}>← All challenges</a>
        <a href="https://github.com/almaguer1986/monogate" target="_blank" rel="noopener noreferrer" style={{ color: C.muted }}>
          github.com/almaguer1986/monogate
        </a>
      </footer>
    </div>
  );
}
