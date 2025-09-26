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

  // API rewrites for backend communication
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },

  // Improved experimental features for better builds
  experimental: {
    // Ensure proper module resolution
    esmExternals: true,
  },
};

export default nextConfig;
