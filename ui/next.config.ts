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

  // API rewrites for backend communication
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },

  // Add webpack configuration for debugging and path resolution
  webpack: (config, { isServer, dev }) => {
    // Debug logging
    console.log('=== WEBPACK DEBUG ===');
    console.log('isServer:', isServer);
    console.log('dev:', dev);
    console.log('Current working directory:', process.cwd());
    
    // Check if lib directory exists
    const fs = require('fs');
    const libPath = path.resolve(process.cwd(), 'lib');
    console.log('lib directory exists:', fs.existsSync(libPath));
    if (fs.existsSync(libPath)) {
      console.log('lib directory contents:', fs.readdirSync(libPath));
    }
    
    // Add path alias for debugging
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(process.cwd()),
    };
    
    console.log('webpack resolve alias:', config.resolve.alias);
    console.log('=== END WEBPACK DEBUG ===');
    
    return config;
  },

  // Improved experimental features for better builds
  experimental: {
    // Ensure proper module resolution
    esmExternals: true,
  },
};

export default nextConfig;
