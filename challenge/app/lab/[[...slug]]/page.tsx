"use client";

import dynamic from "next/dynamic";

const GamesApp = dynamic(() => import("../../../lib/games/GamesApp"), {
  ssr: false,
  loading: () => (
    <div style={{
      minHeight: "100vh", background: "#08060E",
      display: "flex", alignItems: "center", justifyContent: "center",
      color: "#A78BFA", fontFamily: "monospace", fontSize: 13,
    }}>
      loading lab…
    </div>
  ),
});

export default function LabPage() {
  return (
    <div style={{ margin: 0, padding: 0, background: "#08060E", minHeight: "100vh" }}>
      <GamesApp />
    </div>
  );
}
