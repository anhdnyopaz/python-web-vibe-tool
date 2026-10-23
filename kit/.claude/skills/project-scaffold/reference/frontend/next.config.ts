import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Cho phép mở bản dev qua Traefik (test E2E) và link chia sẻ (Cloudflare Quick Tunnel / ngrok).
  allowedDevOrigins: ["traefik", "*.trycloudflare.com", "*.ngrok-free.app", "*.ngrok.app"],
};

export default nextConfig;
