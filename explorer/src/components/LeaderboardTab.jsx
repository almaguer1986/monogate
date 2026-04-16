/**
 * LeaderboardTab — Challenge Board v2 live leaderboard + problem browser.
 *
 * Loads problems.json and leaderboard.json from /challenge/ (served statically).
 * Falls back to bundled data if the fetch fails (offline / dev mode).
 */

import { useState, useEffect } from "react";

// ── arXiv config ─────────────────────────────────────────────────────────────
// Run: python scripts/update_arxiv_id.py <id>   (updates this line automatically)
const ARXIV_ID  = "";   // ARXIV_ID_PLACEHOLDER — leave empty until submitted
const ARXIV_URL = ARXIV_ID
  ? `https://arxiv.org/abs/${ARXIV_ID}`
  : "https://github.com/almaguer1986/monogate/blob/master/python/paper/preprint.tex";
const ARXIV_LABEL = ARXIV_ID ? `arXiv:${ARXIV_ID} →` : "preprint (pending) →";

// ── Colours (matches App.jsx C palette) ──────────────────────────────────────
const C = {
  bg:      "#07080f",
  surface: "#0d0e1c",
  border:  "#191b2e",
  text:    "#cdd0e0",
  muted:   "#4e5168",
  accent:  "#e8a020",
  blue:    "#6ab0f5",
  green:   "#5ec47a",
  red:     "#e05060",
  tag:     "#1a1c2e",
  gold:    "#f5d020",
  silver:  "#c0c0c0",
  bronze:  "#cd7f32",
};

// ── Tier styling ──────────────────────────────────────────────────────────────
const TIER_META = {
  exact:       { label: "Exact",       color: C.gold,   icon: "🏆" },
  tight:       { label: "Tight",       color: C.green,  icon: "🥇" },
  medium:      { label: "Medium",      color: C.blue,   icon: "🥈" },
  approximate: { label: "Approx",      color: C.accent, icon: "🥉" },
  near_miss:   { label: "Near miss",   color: C.muted,  icon: "🎯" },
  open:        { label: "Open",        color: C.muted,  icon: "○"  },
};

const DIFF_COLOR = {
  easy:            C.green,
  medium:          C.accent,
  hard:            C.red,
  very_hard:       "#e040fb",
  impossible_real: C.muted,
};

// ── Bundled fallback data ─────────────────────────────────────────────────────
const FALLBACK_PROBLEMS = [
  { id: "sin_x",    name: "sin(x)",    difficulty: "impossible_real", points: 50, status: "open",      category: "barrier"         },
  { id: "cos_x",    name: "cos(x)",    difficulty: "impossible_real", points: 30, status: "open",      category: "barrier"         },
  { id: "lambert_w",name: "W₀(x)",     difficulty: "hard",            points: 15, status: "open",      category: "special_functions"},
  { id: "erf_x",    name: "erf(x)",    difficulty: "hard",            points: 12, status: "open",      category: "special_functions"},
  { id: "airy_ai",  name: "Ai(x)",     difficulty: "very_hard",       points: 20, status: "open",      category: "special_functions"},
  { id: "bessel_j0",name: "J₀(x)",     difficulty: "very_hard",       points: 15, status: "open",      category: "special_functions"},
  { id: "exp_neg_x2",name:"exp(-x²)",  difficulty: "easy",            points:  4, status: "challenge", category: "gaussian"        },
  { id: "softplus_exact",name:"softplus(x)", difficulty:"medium",     points:  5, status: "challenge", category: "ml_activations"  },
  { id: "swish",    name: "swish(x)",  difficulty: "medium",          points:  6, status: "open",      category: "ml_activations"  },
];

const FALLBACK_LB = {
  entries: [
    { rank: 1, submitter: "monogate-team", problem_id: "sin_x", formula: "Im(eml(i·x, 1))",
      domain: "complex", mse: 0, eml_nodes: 1, tier: "exact", submitted: "2026-04-16",
      notes: "Euler path: Im(exp(ix)) = sin(x). One node in complex EML." },
    { rank: 2, submitter: "monogate-team", problem_id: "lambert_w",
      formula: "eml(eml(1, eml(x, 1)), 1)", domain: "real",
      mse: 0.012, eml_nodes: 3, tier: "approximate", submitted: "2026-04-16",
      notes: "Fixed-point unrolling of y = x·exp(-y)." },
  ],
  problem_stats: {
    sin_x:     { best_mse: 0,     best_nodes: 1, tier: "exact",       n_submissions: 1 },
    lambert_w: { best_mse: 0.012, best_nodes: 3, tier: "approximate", n_submissions: 1 },
  }
};

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmtMse(v) {
  if (v === null || v === undefined) return "—";
  if (v === 0) return "0 (exact)";
  if (v < 1e-12) return "< 1e−12";
  return v.toExponential(2);
}

function tag(txt, color) {
  return (
    <span style={{
      background: color + "22",
      color,
      border: `1px solid ${color}44`,
      borderRadius: 4,
      padding: "1px 6px",
      fontSize: 11,
      fontWeight: 600,
    }}>
      {txt}
    </span>
  );
}

// ── Submission template generator ────────────────────────────────────────────
function makeTemplate(problem) {
  return JSON.stringify({
    problem_id: problem.id,
    formula:    "eml(?, ?)",
    submitter:  "your-github-handle",
    notes:      "",
  }, null, 2);
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function LeaderboardTab() {
  const [problems, setProblems]       = useState(FALLBACK_PROBLEMS);
  const [leaderboard, setLeaderboard] = useState(FALLBACK_LB);
  const [loading, setLoading]         = useState(true);
  const [activeTab, setActiveTab]     = useState("problems");   // "problems" | "leaderboard" | "submit"
  const [selected, setSelected]       = useState(null);          // selected problem for detail view
  const [copied, setCopied]           = useState(false);

  // ── Fetch live data ──────────────────────────────────────────────────────
  useEffect(() => {
    Promise.all([
      fetch("/challenge/problems.json").catch(() => null),
      fetch("/challenge/leaderboard.json").catch(() => null),
    ]).then(async ([pr, lr]) => {
      if (pr && pr.ok) {
        const d = await pr.json();
        setProblems(d.problems || FALLBACK_PROBLEMS);
      }
      if (lr && lr.ok) {
        const d = await lr.json();
        setLeaderboard(d);
      }
      setLoading(false);
    });
  }, []);

  const stats = leaderboard.problem_stats || {};

  // ── Tab bar ───────────────────────────────────────────────────────────────
  const tabs = ["problems", "leaderboard", "submit"];
  const tabLabels = { problems: "Problems", leaderboard: "Leaderboard", submit: "Submit" };

  // ── Sub-views ─────────────────────────────────────────────────────────────
  const renderProblems = () => (
    <div>
      {["barrier", "special_functions", "gaussian", "ml_activations", "pinn"].map(cat => {
        const catProbs = problems.filter(p => p.category === cat);
        if (!catProbs.length) return null;
        const catLabel = {
          barrier: "🚧 Sin Barrier (proven impossible in real EML)",
          special_functions: "📐 Special Functions",
          gaussian: "🔔 Gaussian",
          ml_activations: "⚡ ML Activations",
          pinn: "🌊 PINN / Physics",
        }[cat] || cat;

        return (
          <div key={cat} style={{ marginBottom: 28 }}>
            <div style={{ color: C.muted, fontSize: 12, fontWeight: 700,
                          letterSpacing: 1, textTransform: "uppercase",
                          marginBottom: 8, paddingBottom: 4,
                          borderBottom: `1px solid ${C.border}` }}>
              {catLabel}
            </div>
            {catProbs.map(p => {
              const s    = stats[p.id] || {};
              const tier = s.tier || (p.status === "challenge" ? "challenge" : "open");
              const tm   = TIER_META[tier] || TIER_META.open;
              const dc   = DIFF_COLOR[p.difficulty] || C.text;
              const isSelected = selected?.id === p.id;

              return (
                <div
                  key={p.id}
                  onClick={() => setSelected(isSelected ? null : p)}
                  style={{
                    background: isSelected ? C.surface : "transparent",
                    border: `1px solid ${isSelected ? C.accent : C.border}`,
                    borderRadius: 8,
                    padding: "10px 14px",
                    marginBottom: 6,
                    cursor: "pointer",
                    transition: "border-color 0.15s",
                  }}
                >
                  {/* Row */}
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: 18, minWidth: 24 }}>{tm.icon}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <span style={{ color: C.text, fontWeight: 600, fontSize: 14 }}>
                        {p.name}
                      </span>
                      {" "}
                      <span style={{ color: C.muted, fontSize: 12 }}>{p.id}</span>
                    </div>
                    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                      {tag(p.difficulty.replace("_", " "), dc)}
                      {tag(tier, tm.color)}
                      <span style={{ color: C.accent, fontSize: 12, minWidth: 28, textAlign: "right" }}>
                        {p.points}pts
                      </span>
                    </div>
                  </div>

                  {/* Expanded detail */}
                  {isSelected && (
                    <div style={{ marginTop: 12, paddingTop: 12,
                                  borderTop: `1px solid ${C.border}` }}>
                      <p style={{ color: C.text, fontSize: 13, margin: "0 0 8px" }}>
                        {p.description}
                      </p>
                      {p.hint && (
                        <p style={{ color: C.accent, fontSize: 12, margin: "0 0 8px" }}>
                          💡 Hint: {p.hint}
                        </p>
                      )}
                      {s.best_mse !== null && s.best_mse !== undefined && (
                        <p style={{ color: C.muted, fontSize: 12, margin: "0 0 8px" }}>
                          Current best: MSE = {fmtMse(s.best_mse)}
                          {s.best_nodes ? `, ${s.best_nodes} nodes` : ""}
                        </p>
                      )}
                      {p.best_known?.complex_exact && (
                        <p style={{ color: C.green, fontSize: 12, margin: "0 0 8px" }}>
                          ✓ Complex exact: {p.best_known.complex_exact}
                        </p>
                      )}
                      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                        <button
                          onClick={e => { e.stopPropagation(); setActiveTab("submit"); }}
                          style={{
                            background: C.accent + "22",
                            border: `1px solid ${C.accent}`,
                            color: C.accent,
                            borderRadius: 6,
                            padding: "4px 12px",
                            fontSize: 12,
                            cursor: "pointer",
                          }}
                        >
                          Submit solution
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );

  const renderLeaderboard = () => (
    <div>
      <div style={{ color: C.muted, fontSize: 12, marginBottom: 16 }}>
        {leaderboard.entries?.length || 0} entries · updated {leaderboard.updated || "live"}
      </div>

      {(!leaderboard.entries || leaderboard.entries.length === 0) ? (
        <div style={{ color: C.muted, textAlign: "center", padding: 32 }}>
          No entries yet — be the first to submit!
        </div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ color: C.muted, fontSize: 11, borderBottom: `1px solid ${C.border}` }}>
              <th style={{ padding: "4px 8px", textAlign: "left" }}>#</th>
              <th style={{ padding: "4px 8px", textAlign: "left" }}>Submitter</th>
              <th style={{ padding: "4px 8px", textAlign: "left" }}>Problem</th>
              <th style={{ padding: "4px 8px", textAlign: "right" }}>MSE</th>
              <th style={{ padding: "4px 8px", textAlign: "right" }}>Nodes</th>
              <th style={{ padding: "4px 8px", textAlign: "center" }}>Tier</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.entries.map((e, i) => {
              const tm = TIER_META[e.tier] || TIER_META.open;
              const rankColor = i === 0 ? C.gold : i === 1 ? C.silver : i === 2 ? C.bronze : C.muted;
              return (
                <tr key={i} style={{ borderBottom: `1px solid ${C.border}30` }}>
                  <td style={{ padding: "6px 8px", color: rankColor, fontWeight: 700 }}>
                    {e.rank || i + 1}
                  </td>
                  <td style={{ padding: "6px 8px", color: C.blue }}>{e.submitter}</td>
                  <td style={{ padding: "6px 8px", color: C.text }}>
                    <code style={{ fontSize: 12 }}>{e.problem_id}</code>
                  </td>
                  <td style={{ padding: "6px 8px", color: C.text, textAlign: "right",
                               fontFamily: "monospace" }}>
                    {fmtMse(e.mse)}
                  </td>
                  <td style={{ padding: "6px 8px", color: C.accent, textAlign: "right" }}>
                    {e.eml_nodes}
                  </td>
                  <td style={{ padding: "6px 8px", textAlign: "center" }}>
                    {tag(tm.label, tm.color)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );

  const renderSubmit = () => {
    const template = makeTemplate(selected || problems[0] || { id: "lambert_w" });
    return (
      <div>
        <h3 style={{ color: C.text, margin: "0 0 12px", fontSize: 15 }}>
          Submit a solution
        </h3>

        <ol style={{ color: C.text, fontSize: 13, lineHeight: 1.8, paddingLeft: 20 }}>
          <li>
            Create a file{" "}
            <code style={{ color: C.accent }}>challenge/submissions/your-handle/problem-id.json</code>
          </li>
          <li>
            Use this template (edit formula and submitter):
          </li>
        </ol>

        <div style={{ position: "relative", margin: "12px 0" }}>
          <pre style={{
            background: C.surface,
            border: `1px solid ${C.border}`,
            borderRadius: 8,
            padding: 16,
            fontSize: 13,
            color: C.text,
            overflowX: "auto",
            margin: 0,
          }}>
            {template}
          </pre>
          <button
            onClick={() => {
              navigator.clipboard?.writeText(template);
              setCopied(true);
              setTimeout(() => setCopied(false), 1500);
            }}
            style={{
              position: "absolute",
              top: 8,
              right: 8,
              background: C.tag,
              border: `1px solid ${C.border}`,
              borderRadius: 4,
              color: copied ? C.green : C.muted,
              padding: "2px 8px",
              fontSize: 11,
              cursor: "pointer",
            }}
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>

        <ol start={3} style={{ color: C.text, fontSize: 13, lineHeight: 1.8, paddingLeft: 20 }}>
          <li>
            Validate locally:{" "}
            <code style={{ color: C.accent }}>monogate-validate your-file.json</code>
          </li>
          <li>
            Open a Pull Request — the GitHub Action will post the validation result as a comment.
          </li>
        </ol>

        <div style={{
          marginTop: 20,
          padding: "12px 16px",
          background: C.surface,
          borderRadius: 8,
          border: `1px solid ${C.border}`,
        }}>
          <div style={{ color: C.muted, fontSize: 11, marginBottom: 6, fontWeight: 700,
                        letterSpacing: 1, textTransform: "uppercase" }}>
            Scoring tiers
          </div>
          {Object.entries(TIER_META).filter(([k]) => k !== "open").map(([tier, meta]) => (
            <div key={tier} style={{ display: "flex", gap: 10, alignItems: "center",
                                     marginBottom: 4 }}>
              <span style={{ fontSize: 16 }}>{meta.icon}</span>
              <span style={{ color: meta.color, width: 80, fontSize: 13 }}>{meta.label}</span>
              <span style={{ color: C.muted, fontSize: 12 }}>
                {tier === "exact" ? "max error < 1e−12" :
                 tier === "tight" ? "max error < 1e−8" :
                 tier === "medium" ? "max error < 1e−5" :
                 tier === "approximate" ? "max error < 0.001" :
                 "max error < 0.05"}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div style={{ fontFamily: "monospace", color: C.text, padding: "20px 0" }}>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ color: C.text, margin: "0 0 4px", fontSize: 18 }}>
          Challenge Board v2
        </h2>
        <p style={{ color: C.muted, margin: 0, fontSize: 13 }}>
          Open problems in EML / BEST symbolic regression. Prove the impossible, find the compact.
        </p>
      </div>

      {/* arXiv reference banner */}
      <div style={{
        background: "#0d0f1a",
        border: `1px solid ${C.blue}44`,
        borderRadius: 8,
        padding: "10px 16px",
        marginBottom: 20,
        display: "flex",
        alignItems: "center",
        gap: 12,
        flexWrap: "wrap",
        fontSize: 12,
      }}>
        <span style={{ fontSize: 16 }}>📎</span>
        <span style={{ color: C.muted }}>Canonical reference:</span>
        <span style={{ color: C.text, fontWeight: 600 }}>
          Almaguer (2026) — "Practical Extensions to the EML Universal Operator:
          Hybrid Routing, Phantom Attractors, Performance Kernels, and the N=11 Sin Barrier"
        </span>
        <a
          href={ARXIV_URL}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: C.blue,
            textDecoration: "none",
            border: `1px solid ${C.blue}44`,
            borderRadius: 4,
            padding: "2px 8px",
            whiteSpace: "nowrap",
          }}
        >
          {ARXIV_LABEL}
        </a>
      </div>

      {/* Tab bar */}
      <div style={{ display: "flex", gap: 4, marginBottom: 20,
                    borderBottom: `1px solid ${C.border}`, paddingBottom: 0 }}>
        {tabs.map(t => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            style={{
              background: activeTab === t ? C.surface : "transparent",
              border: "none",
              borderBottom: `2px solid ${activeTab === t ? C.accent : "transparent"}`,
              color: activeTab === t ? C.text : C.muted,
              padding: "6px 16px",
              cursor: "pointer",
              fontSize: 13,
              fontFamily: "monospace",
              transition: "color 0.15s",
            }}
          >
            {tabLabels[t]}
          </button>
        ))}
        {loading && (
          <span style={{ marginLeft: "auto", color: C.muted, fontSize: 11,
                         alignSelf: "center" }}>
            Loading live data…
          </span>
        )}
      </div>

      {/* Content */}
      {activeTab === "problems"     && renderProblems()}
      {activeTab === "leaderboard"  && renderLeaderboard()}
      {activeTab === "submit"       && renderSubmit()}
    </div>
  );
}
