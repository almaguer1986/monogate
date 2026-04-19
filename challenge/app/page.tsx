import { supabase } from "@/lib/supabase";
import type { Challenge } from "@/types";

export const revalidate = 60;

const C = {
  bg: "#08090e",
  surface: "#0d0f18",
  surface2: "#12151f",
  border: "#1c1f2e",
  border2: "#252836",
  text: "#d4d4d4",
  muted: "#4a4d62",
  orange: "#e8a020",
  blue: "#6ab0f5",
  green: "#4ade80",
  red: "#f87171",
};

async function getChallenges(): Promise<Challenge[]> {
  const { data: challenges, error } = await supabase
    .from("challenges")
    .select("*")
    .order("created_at", { ascending: true });

  if (error || !challenges) return [];

  const { data: counts } = await supabase
    .from("submissions")
    .select("challenge_id")
    .eq("valid", true);

  const countMap: Record<string, number> = {};
  for (const row of counts ?? []) {
    countMap[row.challenge_id] = (countMap[row.challenge_id] ?? 0) + 1;
  }

  const bestIds = challenges
    .map((c) => c.best_submission_id)
    .filter(Boolean) as string[];

  const authorMap: Record<string, string> = {};
  if (bestIds.length > 0) {
    const { data: bestSubs } = await supabase
      .from("submissions")
      .select("id, author")
      .in("id", bestIds);
    for (const s of bestSubs ?? []) {
      authorMap[s.id] = s.author;
    }
  }

  return challenges.map((c) => ({
    ...c,
    submission_count: countMap[c.id] ?? 0,
    best_author: c.best_submission_id ? (authorMap[c.best_submission_id] ?? null) : null,
  }));
}

function StatusBadge({ status }: { status: string }) {
  const solved = status === "solved";
  return (
    <span style={{
      display: "inline-block",
      fontSize: 9,
      fontWeight: 700,
      letterSpacing: "0.12em",
      padding: "3px 8px",
      borderRadius: 3,
      background: solved ? "rgba(94,196,122,0.10)" : "rgba(232,160,32,0.10)",
      border: `1px solid ${solved ? C.green : C.orange}`,
      color: solved ? C.green : C.orange,
    }}>
      {solved ? "SOLVED" : "OPEN"}
    </span>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div>
      <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 2 }}>
        {label}
      </div>
      <div style={{ fontSize: 13, color, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function ChallengeCard({ challenge }: { challenge: Challenge }) {
  const hasBest = challenge.best_known_nodes !== null;
  return (
    <a
      href={`/challenge/${challenge.id}`}
      style={{
        display: "block",
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: 8,
        padding: "20px 24px",
        textDecoration: "none",
        color: "inherit",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 10 }}>
        <div style={{ fontSize: 20, fontWeight: 700, color: C.orange, letterSpacing: "-0.02em" }}>
          {challenge.name}
        </div>
        <StatusBadge status={challenge.status} />
      </div>

      <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.7, marginBottom: 16 }}>
        {challenge.description}
      </div>

      <div style={{ display: "flex", gap: 24, flexWrap: "wrap", paddingTop: 14, borderTop: `1px solid ${C.border}` }}>
        <Stat label="Best nodes" value={hasBest ? String(challenge.best_known_nodes) : "—"} color={hasBest ? C.text : C.muted} />
        <Stat label="Best depth" value={hasBest ? String(challenge.best_known_depth) : "—"} color={hasBest ? C.text : C.muted} />
        <Stat label="Valid submissions" value={String(challenge.submission_count ?? 0)} color={C.text} />
        {challenge.best_author && (
          <Stat label="Record holder" value={challenge.best_author} color={C.blue} />
        )}
      </div>
    </a>
  );
}

function PillLink({ href, label, internal }: { href: string; label: string; internal?: boolean }) {
  const props = internal
    ? { href }
    : { href, target: "_blank", rel: "noopener noreferrer" };
  return (
    <a {...props} className="eco-btn">
      {label}
    </a>
  );
}

export default async function HomePage() {
  const challenges = await getChallenges();

  return (
    <div style={{ background: C.bg, minHeight: "100vh", maxWidth: 760, margin: "0 auto", padding: "0 16px 60px" }}>

      {/* Header */}
      <header style={{ borderBottom: `1px solid ${C.border}`, padding: "28px 0 22px", marginBottom: 36 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: C.orange, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>
              monogate.dev
            </div>
            <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em", lineHeight: 1.2 }}>
              The EML Challenge Board
            </div>
          </div>
          <div style={{ display: "flex", gap: 16 }}>
            <a href="/search" className="nav-link">Search</a>
            <a href="/leaderboard" className="nav-link">Leaderboard</a>
            <a href="/theorems" className="nav-link">Theorems</a>
            <a href="/how-to-submit" className="nav-link">How to Submit</a>
          </div>
        </div>
        <div style={{ marginTop: 14, fontSize: 11, color: C.muted, lineHeight: 1.8, maxWidth: 540 }}>
          Canonical validator and leaderboard for open problems in the EML operator.
          Submit a construction. Get credited permanently.{" "}
          <a href="https://arxiv.org/abs/2603.21852" className="arxiv-link" style={{ color: C.blue }} target="_blank" rel="noopener noreferrer">
            arXiv:2603.21852
          </a>
        </div>
      </header>

      {/* Operator card — math only */}
      <div className="operator-card" style={{ borderRadius: 8, padding: "14px 20px", marginBottom: 10 }}>
        <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>
          The operator
        </div>
        <div style={{ fontSize: 16, color: C.orange, fontWeight: 700 }}>eml(x, y) = exp(x) − ln(y)</div>
        <div style={{ fontSize: 10, color: C.muted, marginTop: 4 }}>
          Grammar: S → 1 | eml(S, S) · strict principal-branch ln · ln(0) undefined
        </div>
      </div>

      {/* Ecosystem row */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>
          ecosystem
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <PillLink href="/search" label="Search tool ↗" internal />
          <PillLink href="https://explorer.monogate.dev" label="Explorer ↗" />
          <PillLink href="https://www.npmjs.com/package/monogate" label="npm ↗" />
          <PillLink href="https://github.com/almaguer1986/monogate" label="GitHub ↗" />
        </div>
      </div>

      {/* Section heading */}
      <div style={{ fontSize: 10, color: C.orange, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 14 }}>
        Open Challenges — {challenges.length} problems
      </div>

      {/* Cards */}
      {challenges.length === 0 ? (
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8,
          padding: "40px 24px", textAlign: "center", color: C.muted, fontSize: 12,
        }}>
          No challenges found. Run the SQL schema in the Supabase dashboard to seed data.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {challenges.map((c) => <ChallengeCard key={c.id} challenge={c} />)}
        </div>
      )}

      {/* Footer */}
      <footer style={{
        marginTop: 48, paddingTop: 20, borderTop: `1px solid ${C.border}`,
        display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10,
        fontSize: 10, color: C.muted,
      }}>
        <span>Odrzywołek (2026) · arXiv:2603.21852v2 · CC BY 4.0 · <a href="https://games.monogate.dev" style={{ color: C.muted }}>Games ↗</a></span>
        <div style={{ display: "flex", gap: 14 }}>
          {[
            { href: "https://explorer.monogate.dev", label: "Explorer" },
            { href: "https://www.npmjs.com/package/monogate", label: "npm" },
            { href: "https://github.com/almaguer1986/monogate", label: "GitHub" },
            { href: "https://arxiv.org/abs/2603.21852", label: "arXiv" },
          ].map(({ href, label }) => (
            <a key={label} href={href} target="_blank" rel="noopener noreferrer" style={{ color: C.muted }}>
              {label}
            </a>
          ))}
        </div>
      </footer>
    </div>
  );
}
