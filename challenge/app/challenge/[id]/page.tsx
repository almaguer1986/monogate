import { notFound } from "next/navigation";
import { supabase } from "@/lib/supabase";
import type { Challenge, Submission } from "@/types";
import SubmissionForm from "./SubmissionForm";

export const revalidate = 0; // always fresh — submissions should appear immediately

const C = {
  bg: "#08090e", surface: "#0d0f18", surface2: "#12151f",
  border: "#1c1f2e", border2: "#252836",
  text: "#d4d4d4", muted: "#4a4d62",
  orange: "#e8a020", blue: "#6ab0f5", green: "#4ade80", red: "#f87171",
};

const GRAMMAR_RULES: Record<string, { allowed: string[]; forbidden: string[]; note: string }> = {
  "strict-principal-branch": {
    allowed: [
      "eml(x, y) = exp(x) − ln(y)  — the single operator",
      "Terminal: constant 1",
      "Terminal: variable x (for function challenges)",
      "Compositions: any finite binary tree over the above",
    ],
    forbidden: [
      "ln(0) — undefined, throws RangeError",
      "Math.sin, Math.cos, Math.PI, or any Math.* shortcut",
      "Any function outside the EML grammar",
      "Extended-reals convention (ln(0) = −∞) — not this grammar",
    ],
    note:
      "Under extended-reals grammar (pveierland/eml-eval), i is solved at K=75. " +
      "This challenge is the strict grammar variant where ln(0) throws.",
  },
};

async function getChallenge(id: string): Promise<Challenge | null> {
  const { data } = await supabase
    .from("challenges")
    .select("*")
    .eq("id", id)
    .single();
  return data ?? null;
}

async function getSubmissions(challengeId: string): Promise<Submission[]> {
  const { data } = await supabase
    .from("submissions")
    .select("*")
    .eq("challenge_id", challengeId)
    .order("nodes", { ascending: true })
    .order("created_at", { ascending: true });
  return data ?? [];
}

function StatusBadge({ status }: { status: string }) {
  const solved = status === "solved";
  const closed = status === "closed";
  const bgColor = solved ? "rgba(94,196,122,0.10)" : closed ? "rgba(248,113,113,0.10)" : "rgba(232,160,32,0.10)";
  const borderColor = solved ? C.green : closed ? C.red : C.orange;
  const label = solved ? "SOLVED" : closed ? "CLOSED — IMPOSSIBLE" : "OPEN";
  return (
    <span style={{
      display: "inline-block", fontSize: 9, fontWeight: 700,
      letterSpacing: "0.12em", padding: "3px 8px", borderRadius: 3,
      background: bgColor,
      border: `1px solid ${borderColor}`,
      color: borderColor,
    }}>
      {label}
    </span>
  );
}

function fmt(d: string) {
  return new Date(d).toISOString().slice(0, 10);
}

export default async function ChallengePage({ params }: { params: { id: string } }) {
  const [challenge, allSubmissions] = await Promise.all([
    getChallenge(params.id),
    getSubmissions(params.id),
  ]);

  if (!challenge) notFound();

  const validSubmissions = allSubmissions.filter((s) => s.valid);
  const invalidSubmissions = allSubmissions.filter((s) => !s.valid);
  const grammar = GRAMMAR_RULES[challenge.grammar] ?? GRAMMAR_RULES["strict-principal-branch"];

  return (
    <div style={{ background: C.bg, minHeight: "100vh", maxWidth: 760, margin: "0 auto", padding: "0 16px 60px" }}>

      {/* Header */}
      <header style={{ borderBottom: `1px solid ${C.border}`, padding: "28px 0 22px", marginBottom: 36 }}>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>
          <a href="/" style={{ color: C.muted, textDecoration: "none" }}>monogate.dev</a>
          {" / "}
          <a href="/challenge" style={{ color: C.muted, textDecoration: "none" }}>challenges</a>
          {" / "}
          <span style={{ color: C.text }}>{challenge.name}</span>
        </div>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 14, flexWrap: "wrap" }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: C.orange, letterSpacing: "-0.02em", lineHeight: 1 }}>
            {challenge.name}
          </div>
          <div style={{ paddingTop: 4 }}>
            <StatusBadge status={challenge.status} />
          </div>
        </div>
        <div style={{ marginTop: 12, fontSize: 11, color: C.muted, lineHeight: 1.8, maxWidth: 580 }}>
          {challenge.description}
        </div>
      </header>

      {/* Best known */}
      {challenge.best_known_nodes !== null && (
        <div style={{
          background: "rgba(94,196,122,0.05)", border: `1px solid ${C.green}`,
          borderRadius: 8, padding: "14px 20px", marginBottom: 28,
          display: "flex", gap: 28, flexWrap: "wrap",
        }}>
          <Stat label="Best nodes" value={String(challenge.best_known_nodes)} color={C.green} />
          <Stat label="Best depth" value={String(challenge.best_known_depth ?? "—")} color={C.green} />
          <Stat label="Valid submissions" value={String(validSubmissions.length)} color={C.text} />
        </div>
      )}

      {/* Grammar specification */}
      <section style={{ marginBottom: 32 }}>
        <SectionTitle>Grammar</SectionTitle>
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "16px 20px" }}>
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 11, color: C.orange, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 10 }}>
              Allowed
            </div>
            {grammar.allowed.map((rule, i) => (
              <div key={i} style={{ fontSize: 14, color: "#e0e0e0", lineHeight: 1.9, display: "flex", gap: 10 }}>
                <span style={{ color: C.green }}>✓</span>
                <span style={{ fontFamily: "monospace" }}>{rule}</span>
              </div>
            ))}
          </div>
          <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 14, marginBottom: grammar.note ? 14 : 0 }}>
            <div style={{ fontSize: 11, color: C.orange, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 10 }}>
              Forbidden
            </div>
            {grammar.forbidden.map((rule, i) => (
              <div key={i} style={{ fontSize: 14, color: "#e0e0e0", lineHeight: 1.9, display: "flex", gap: 10 }}>
                <span style={{ color: C.red }}>✗</span>
                <span>{rule}</span>
              </div>
            ))}
          </div>
          {grammar.note && (
            <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 12, fontSize: 11, color: "#a0a0a0", lineHeight: 1.8, fontStyle: "italic" }}>
              {grammar.note}
            </div>
          )}
        </div>
      </section>

      {/* Leaderboard */}
      <section style={{ marginBottom: 32 }}>
        <SectionTitle>
          Leaderboard — {validSubmissions.length} valid construction{validSubmissions.length !== 1 ? "s" : ""}
        </SectionTitle>

        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
          {/* Header row */}
          <div style={{
            display: "grid", gridTemplateColumns: "40px 1fr 70px 60px 100px",
            padding: "8px 16px", borderBottom: `1px solid ${C.border}`,
            fontSize: 9, color: C.muted, letterSpacing: "0.08em", textTransform: "uppercase",
          }}>
            <div>#</div><div>Author</div><div>Nodes</div><div>Depth</div><div>Date</div>
          </div>

          {validSubmissions.length === 0 ? (
            <div style={{ padding: "40px 16px", textAlign: "center", color: "#a0a0a0", fontSize: 13 }}>
              No valid constructions yet. Be the first.
            </div>
          ) : (
            validSubmissions.map((s, i) => (
              <div key={s.id} style={{
                display: "grid", gridTemplateColumns: "40px 1fr 70px 60px 100px",
                padding: "10px 16px", fontSize: 12,
                borderBottom: i < validSubmissions.length - 1 ? `1px solid ${C.border}` : "none",
                background: i === 0 ? "rgba(94,196,122,0.04)" : "transparent",
                alignItems: "start",
              }}>
                <div style={{ color: i === 0 ? C.green : C.muted, fontWeight: i === 0 ? 700 : 400 }}>
                  {i === 0 ? "★" : i + 1}
                </div>
                <div>
                  <div style={{ color: i === 0 ? C.green : C.text }}>{s.author}</div>
                  {s.notes && (
                    <div style={{ fontSize: 10, color: C.muted, marginTop: 3, lineHeight: 1.5, maxWidth: 360 }}>
                      {s.notes.length > 120 ? s.notes.slice(0, 120) + "…" : s.notes}
                    </div>
                  )}
                </div>
                <div style={{ color: C.text }}>{s.nodes ?? "—"}</div>
                <div style={{ color: C.muted }}>{s.depth ?? "—"}</div>
                <div style={{ color: C.muted, fontSize: 10 }}>{fmt(s.created_at)}</div>
              </div>
            ))
          )}
        </div>

        {/* Invalid submissions count */}
        {invalidSubmissions.length > 0 && (
          <div style={{ marginTop: 8, fontSize: 10, color: C.muted }}>
            {invalidSubmissions.length} invalid submission{invalidSubmissions.length !== 1 ? "s" : ""} not shown.
          </div>
        )}
      </section>

      {/* Search tool nudge */}
      <div style={{
        marginBottom: 20, padding: "12px 18px",
        border: `1px solid ${C.border2}`, borderRadius: 6,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        gap: 12, flexWrap: "wrap",
      }}>
        <span style={{ fontSize: 13, color: "#a0a0a0" }}>
          Not sure where to start?
        </span>
        <a href="/search" style={{
          fontSize: 13, fontWeight: 700, color: C.orange,
          letterSpacing: "0.02em", whiteSpace: "nowrap",
        }}>
          Try the symbolic regression search tool →
        </a>
      </div>

      {/* Submission form */}
      <SubmissionForm challengeId={challenge.id} challengeName={challenge.name} />

      {/* Footer */}
      <footer style={{
        marginTop: 48, paddingTop: 20, borderTop: `1px solid ${C.border}`,
        display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10,
        fontSize: 10, color: C.muted,
      }}>
        <a href="/challenge" style={{ color: C.muted }}>← All challenges</a>
        <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: C.muted }}>
          arXiv:2603.21852
        </a>
      </footer>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontSize: 10, color: C.orange, letterSpacing: "0.12em",
      textTransform: "uppercase", marginBottom: 12,
    }}>
      {children}
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div>
      <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 2 }}>
        {label}
      </div>
      <div style={{ fontSize: 15, color, fontWeight: 700 }}>{value}</div>
    </div>
  );
}
