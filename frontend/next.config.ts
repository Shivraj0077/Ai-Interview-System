import type { NextConfig } from "next";

// The browser only ever talks to this Next.js origin; /api/* is proxied to the
// Python backend, which holds every API key. Nothing secret reaches the client.
const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
  experimental: {
    // Submitting an answer runs evaluation + next-question generation server-side.
    proxyTimeout: 120_000,
  },
};

export default nextConfig;
