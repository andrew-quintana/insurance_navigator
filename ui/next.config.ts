import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Basic configuration
  output: 'standalone',

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
