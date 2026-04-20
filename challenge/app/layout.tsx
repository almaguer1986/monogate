import type { Metadata } from "next";
import "./globals.css";
import Nav from "./components/Nav";

const siteUrl = "https://monogate.dev";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "monogate.dev — The EML Challenge Board",
    template: "%s — monogate.dev",
  },
  description:
    "Canonical validator and leaderboard for open problems in the EML operator. " +
    "eml(x,y) = exp(x) − ln(y) · arXiv:2603.21852 · Odrzywołek 2026. " +
    "Submit a construction for sin, cos, π, or i. Get credited permanently.",
  keywords: [
    "EML operator", "elementary functions", "exp minus log", "arXiv:2603.21852",
    "mathematics", "open problems", "monogate", "sin cos pi i",
  ],
  authors: [{ name: "monogate.dev" }],
  openGraph: {
    type: "website",
    siteName: "monogate.dev",
    title: "monogate.dev — The EML Challenge Board",
    description:
      "Open problems in the EML operator: construct sin, cos, π, i from eml(x,y) = exp(x) − ln(y). Submit a construction. Get credited permanently.",
    url: siteUrl,
  },
  twitter: {
    card: "summary",
    title: "monogate.dev — The EML Challenge Board",
    description:
      "Open problems in eml(x,y) = exp(x) − ln(y). Construct sin, cos, π, or i from a single binary operator. arXiv:2603.21852",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        {children}
      </body>
    </html>
  );
}
