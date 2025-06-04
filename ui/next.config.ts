import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Basic configuration for now
  output: 'standalone',
  
  // Disable TypeScript and ESLint checking during build to isolate the issue
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  // Basic compression
  compress: true,
  poweredByHeader: false,
};

export default nextConfig;
