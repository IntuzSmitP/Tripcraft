import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow LAN access from your IP
  allowedDevOrigins: ['192.168.10.180'],
};

export default nextConfig;
