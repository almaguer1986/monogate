import { supabase } from "@/lib/supabase";
import type { Challenge, SubmissionWithChallenge } from "@/types";

export const revalidate = 60;

const C = {
  bg: "#08090e", surface: "#0d0f18", surface2: "#12151f",
  border: "#1c1f2e", border2: "#252836",
  text: "#d4d4d4", muted: "#4a4d62",
  orange: "#e8a020", blue: "#6ab0f5", green: "#4ade80", red: "#f87171",
};

async function getData() {
  const [subRes, chalRes] = await Promise.all([
    supabase
      .from("submissions")
      .select("*, challenges(id, name)")
      .eq("valid", true)
      .order("nodes", { ascending: true })
      .order("created_at", { ascending: true }),
    supabase
      .from("challenges")
      .select("*")
      .order("created_at", { ascending: true }),
  ]);

  const submissions = (subRes.data ?? []) as SubmissionWithChallenge[];
  const challenges = (chalRes.data ?? []) as Challenge[];
  return { submissions, challenges };
}

function fmt(d: string) {
  return new Date(d).toISOString().slice(0, 10);
}

export default async function LeaderboardPage() {
  const { submissions, challenges } = await getData();

  // Track which is the record per challenge (first seen = fewest nodes = record)
  const recordIds = new Set<string>();
  const seenChallenge = new Set<string>();
  for (const s of submissions) {
    if (!seenChallenge.has(s.challenge_id)) {
      recordIds.add(s.id);
      seenChallenge.add(s.challenge_id);
    }
  }

  const chalMap = Object.fromEntries(challenges.map((c) => [c.id, c]));
  const solvedChallenges = challenges.filter((c) => c.status === "solved");

  return (
    <div style={{ background: C.bg, minHeight: "100vh", maxWidth: 760, margin: "0 auto", padding: "0 16px 60px" }}>

      {/* Header */}
      <header style={{ borderBottom: `1px solid ${C.border}`, padding: "28px 0 22px", marginBottom: 36 }}>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>
          <a href="/" style={{ color: C.muted, textDecoration: "none" }}>monogate.dev</a>
          {" / leaderboard"}
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "-0.02em" }}>
          Global Leaderboard
        </div>
        <div style={{ marginTop: 10, fontSize: 11, color: C.muted, lineHeight: 1.8 }}>
          All valid constructions across all challenges, ranked by node count ascending.
          Attribution is permanent — your name stays on your record even if someone beats it.
        </div>
      </header>

      {/* Summary strip */}
      <div style={{
        display: "flex", gap: 24, flexWrap: "wrap",
        padding: "14px 20px", marginBottom: 28,
        background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8,
      }}>
        <Stat label="Total valid submissions" value={String(submissions.length)} color={C.text} />
        <Stat label="Challenges solved" value={`${solvedChallenges.length} / ${challenges.length}`} color={solvedChallenges.length > 0 ? C.green : C.muted} />
        <Stat label="Open problems" value={String(challenges.filter(c => c.status === "open").length)} color={C.orange} />
      </div>

      {/* Per-challenge sections */}
      {challenges.map((challenge) => {
        const chalSubs = submissions.filter((s) => s.challenge_id === challenge.id);
        return (
          <section key={challenge.id} style={{ marginBottom: 32 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
              <a href={`/challenge/${challenge.id}`} style={{
                fontSize: 9, color: C.muted, letterSpacing: "0.12em",
                textTransform: "uppercase", textDecoration: "none",
              }}>
                {challenge.name} ↗
              </a>
              <div style={{ flex: 1, height: "1px", background: C.border }} />
              {challenge.status === "solved" && (
                <span style={{
                  fontSize: 9, fontWeight: 700, letterSpacing: "0.1em",
                  padding: "2px 7px", borderRadius: 3,
                  background: "rgba(94,196,122,0.10)",
                  border: `1px solid ${C.green}`,
                  color: C.green,
                }}>SOLVED</span>
              )}
            </div>

            <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
              <div style={{
                display: "grid", gridTemplateColumns: "36px 1fr 70px 60px 100px",
                padding: "7px 16px", borderBottom: `1px solid ${C.border}`,
                fontSize: 9, color: C.muted, letterSpacing: "0.08em", textTransform: "uppercase",
              }}>
                <div>#</div><div>Author</div><div>Nodes</div><div>Depth</div><div>Date</div>
              </div>

              {chalSubs.length === 0 ? (
                <div style={{ padding: "20px 16px", color: C.muted, fontSize: 11 }}>
                  No valid constructions yet.{" "}
                  <a href={`/challenge/${challenge.id}`} style={{ color: C.orange }}>
                    Submit one.
                  </a>
                </div>
              ) : (
                chalSubs.map((s, i) => {
                  const isRecord = recordIds.has(s.id);
                  return (
                    <div key={s.id} style={{
                      display: "grid", gridTemplateColumns: "36px 1fr 70px 60px 100px",
                      padding: "10px 16px", fontSize: 12, alignItems: "start",
                      borderBottom: i < chalSubs.length - 1 ? `1px solid ${C.border}` : "none",
                      background: isRecord ? "rgba(94,196,122,0.035)" : "transparent",
                    }}>
                      <div style={{ color: isRecord ? C.green : C.muted, fontWeight: isRecord ? 700 : 400, paddingTop: 1 }}>
                        {isRecord ? "★" : i + 1}
                      </div>
                      <div>
                        <div style={{ color: isRecord ? C.green : C.text, fontWeight: isRecord ? 700 : 400 }}>
                          {s.author}
                          {isRecord && (
                            <span style={{ marginLeft: 8, fontSize: 9, color: C.green, fontWeight: 400, letterSpacing: "0.08em" }}>
                              RECORD
                            </span>
                          )}
                        </div>
                        {s.notes && (
                          <div style={{ fontSize: 10, color: C.muted, marginTop: 3, lineHeight: 1.5, maxWidth: 340 }}>
                            {s.notes.length > 100 ? s.notes.slice(0, 100) + "…" : s.notes}
                          </div>
                        )}
                      </div>
                      <div style={{ color: isRecord ? C.green : C.text }}>{s.nodes ?? "—"}</div>
                      <div style={{ color: C.muted }}>{s.depth ?? "—"}</div>
                      <div style={{ color: C.muted, fontSize: 10 }}>{fmt(s.created_at)}</div>
                    </div>
                  );
                })
              )}
            </div>
          </section>
        );
      })}

      {submissions.length === 0 && (
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8,
          padding: "48px 24px", textAlign: "center", color: C.muted, fontSize: 12,
        }}>
          No valid submissions yet across any challenge.{" "}
          <a href="/" style={{ color: C.orange }}>Pick a problem and submit the first construction.</a>
        </div>
      )}

      <footer style={{
        marginTop: 48, paddingTop: 20, borderTop: `1px solid ${C.border}`,
        display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10,
        fontSize: 10, color: C.muted,
      }}>
        <a href="/" style={{ color: C.muted }}>← All challenges</a>
        <a href="https://arxiv.org/abs/2603.21852" target="_blank" rel="noopener noreferrer" style={{ color: C.muted }}>
          arXiv:2603.21852
        </a>
      </footer>
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
