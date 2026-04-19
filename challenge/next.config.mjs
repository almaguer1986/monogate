/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["monogate"],
  async redirects() {
    return [
      // Legacy top-level routes → new locations
      { source: "/search", destination: "/challenge/search", permanent: true },
      { source: "/leaderboard", destination: "/challenge/leaderboard", permanent: true },
      { source: "/theorems", destination: "https://monogate.org/theorems", permanent: false },
      { source: "/one-operator", destination: "https://monogate.org", permanent: false },
      // Cross-domain shortcuts
      { source: "/games", destination: "https://games.monogate.dev", permanent: false },
      { source: "/play", destination: "https://games.monogate.dev", permanent: false },
      { source: "/explorer", destination: "https://www.monogate.dev", permanent: false },
    ];
  },
};

export default nextConfig;
