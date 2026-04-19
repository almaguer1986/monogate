import type { Metadata } from "next";
import SearchClient from "./SearchClient";

export const metadata: Metadata = {
  title: "Search — monogate.dev",
  description:
    "EML Symbolic Regression — gradient descent search over random EML tree topologies. " +
    "Attempts to find constructions for sin, cos, π from eml(x,y) = exp(x) − ln(y).",
};

export default function SearchPage() {
  return <SearchClient />;
}
