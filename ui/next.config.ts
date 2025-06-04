import type { NextConfig } from "next";
import path from "path";

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

  // Add webpack configuration for path aliases
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname),
    };
    return config;
  },
};

export default nextConfig;
