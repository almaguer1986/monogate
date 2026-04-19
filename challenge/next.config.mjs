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
      // /games → /play (canonical)
      { source: "/games", destination: "/play", permanent: true },
    ];
  },
  async rewrites() {
    return [
      // Proxy /play/* to games.monogate.dev/play/* — URL stays at monogate.dev
      { source: "/play", destination: "https://games.monogate.dev/play" },
      { source: "/play/:path*", destination: "https://games.monogate.dev/play/:path*" },
      // Proxy /explorer/* to explorer.monogate.dev/explorer/* — URL stays at monogate.dev
      { source: "/explorer", destination: "https://explorer.monogate.dev/explorer" },
      { source: "/explorer/:path*", destination: "https://explorer.monogate.dev/explorer/:path*" },
    ];
  },
};

export default nextConfig;
