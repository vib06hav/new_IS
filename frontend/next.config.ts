import type { NextConfig } from "next";
import path from "path";

const backendApiUrl = process.env.BACKEND_API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(__dirname, ".."),
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendApiUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
