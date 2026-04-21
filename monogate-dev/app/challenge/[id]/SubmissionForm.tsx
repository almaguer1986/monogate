"use client";

import { useState } from "react";
import { submitSolution, type SubmitResult } from "./actions";

const C = {
  bg: "#08090e", surface: "#0d0f18", surface2: "#12151f",
  border: "#1c1f2e", border2: "#252836",
  text: "#d4d4d4", muted: "#4a4d62",
  orange: "#e8a020", blue: "#6ab0f5", green: "#4ade80", red: "#f87171",
};

type Status = "idle" | "submitting" | "done";

interface Props {
  challengeId: string;
  challengeName: string;
}

export default function SubmissionForm({ challengeId, challengeName }: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [author, setAuthor] = useState("");
  const [expression, setExpression] = useState("");
  const [notes, setNotes] = useState("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (status === "submitting") return;
    setStatus("submitting");
    setResult(null);

    const fd = new FormData();
    fd.append("challengeId", challengeId);
    fd.append("author", author);
    fd.append("expression", expression);
    fd.append("notes", notes);

    const res = await submitSolution(fd);
    setResult(res);
    setStatus("done");
  };

  const handleReset = () => {
    setStatus("idle");
    setResult(null);
  };

  const inputStyle: React.CSSProperties = {
    width: "100%",
    background: C.bg,
    border: `1px solid ${C.border2}`,
    borderRadius: 4,
    color: C.text,
    padding: "9px 12px",
    fontSize: 13,
    fontFamily: "'Space Mono', monospace",
    outline: "none",
  };

  const labelStyle: React.CSSProperties = {
    display: "block",
    fontSize: 9,
    color: C.muted,
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    marginBottom: 6,
  };

  return (
    <div>
      <div style={{ fontSize: 10, color: C.orange, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 14 }}>
        Submit a Construction
      </div>

      {/* Result banner */}
      {status === "done" && result && (
        <div style={{
          borderRadius: 6, padding: "14px 16px", marginBottom: 20,
          background: result.valid ? "rgba(94,196,122,0.07)" : "rgba(224,80,96,0.07)",
          border: `1px solid ${result.valid ? C.green : C.red}`,
        }}>
          {result.valid ? (
            <div>
              <div style={{ fontSize: 13, color: C.green, fontWeight: 700, marginBottom: 6 }}>
                ✓ Valid construction
              </div>
              <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.7 }}>
                Nodes: <span style={{ color: C.text }}>{result.nodes}</span>
                {"  ·  "}
                Depth: <span style={{ color: C.text }}>{result.depth}</span>
                {"  ·  "}
                Submission recorded. Your name is on the board.
              </div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: 13, color: C.red, fontWeight: 700, marginBottom: 6 }}>
                ✗ Invalid
              </div>
              <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.7 }}>
                {result.error ?? "Validation failed."}
              </div>
            </div>
          )}
          <button
            onClick={handleReset}
            style={{
              marginTop: 12, fontSize: 10, padding: "5px 12px",
              background: "transparent",
              border: `1px solid ${C.border2}`,
              color: C.muted, borderRadius: 4,
            }}
          >
            Submit another
          </button>
        </div>
      )}

      {/* Form */}
      {status !== "done" && (
        <form onSubmit={handleSubmit}>
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "20px 20px", display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Author */}
            <div>
              <label style={labelStyle}>Author handle</label>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                placeholder="your name or handle"
                required
                maxLength={64}
                style={inputStyle}
              />
            </div>

            {/* Expression */}
            <div>
              <label style={labelStyle}>EML expression</label>
              <textarea
                value={expression}
                onChange={(e) => setExpression(e.target.value)}
                placeholder={`Expression for ${challengeName} using eml, exp, ln, neg, add, sub, mul, div, pow, recip, x`}
                required
                rows={5}
                style={{ ...inputStyle, resize: "vertical", lineHeight: 1.6 }}
              />
              <div style={{ fontSize: 9, color: C.muted, marginTop: 5, lineHeight: 1.7 }}>
                Available: <span style={{ color: C.orange }}>eml exp ln neg add sub mul div pow recip</span>{" "}
                · terminals: <span style={{ color: C.blue }}>1 x</span>{" "}
                · numeric literals ok
              </div>
            </div>

            {/* Notes */}
            <div>
              <label style={labelStyle}>Notes <span style={{ color: C.muted, fontWeight: 400 }}>(optional)</span></label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Explain your approach, cite a paper, link to a proof…"
                rows={3}
                style={{ ...inputStyle, resize: "vertical", lineHeight: 1.6 }}
              />
            </div>

            {/* Submit */}
            <div>
              <button
                type="submit"
                disabled={status === "submitting"}
                style={{
                  padding: "10px 28px", fontSize: 11, fontWeight: 700,
                  letterSpacing: "0.06em", textTransform: "uppercase",
                  background: status === "submitting" ? "rgba(232,160,32,0.05)" : "rgba(232,160,32,0.12)",
                  border: `1px solid ${C.orange}`,
                  color: status === "submitting" ? C.muted : C.orange,
                  borderRadius: 4,
                  cursor: status === "submitting" ? "not-allowed" : "pointer",
                }}
              >
                {status === "submitting" ? "Validating…" : "Submit"}
              </button>
              <span style={{ marginLeft: 12, fontSize: 10, color: C.muted }}>
                Validated server-side against known test cases.
              </span>
            </div>
          </div>
        </form>
      )}
    </div>
  );
}
