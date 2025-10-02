import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Basic configuration
  output: 'standalone',

  // Basic compression
  compress: true,
  poweredByHeader: false,

  // API rewrites for backend communication
  async rewrites() {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${apiBaseUrl}/api/:path*`,
      },
      {
        source: '/auth/:path*',
        destination: `${apiBaseUrl}/auth/:path*`,
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
