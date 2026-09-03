import type { NextConfig } from "next";

// 浏览器只访问 Next.js；/api 被转发到 FastAPI，这样 Cookie 不会跨域丢失。
const apiUrl = process.env.API_INTERNAL_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
