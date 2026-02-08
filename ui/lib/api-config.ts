/**
 * Centralized API Configuration
 * 
 * This module provides a single source of truth for API endpoints and WebSocket URLs.
 * It ensures consistency across all components and handles environment-specific configurations.
 */

// Environment detection
const isProduction = process.env.NODE_ENV === 'production';
const isDevelopment = process.env.NODE_ENV === 'development';

// Get API base URL from environment with proper fallbacks
const getApiBaseUrl = (): string => {
  // Priority order:
  // 1. NEXT_PUBLIC_API_BASE_URL (explicitly set)
  // 2. NEXT_PUBLIC_API_URL (legacy fallback) 
  // 3. Development default
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL 
    || process.env.NEXT_PUBLIC_API_URL
    || 'http://localhost:8000';
    
  return apiBaseUrl;
};

// Convert HTTP URL to WebSocket URL
const getWebSocketUrl = (httpUrl: string): string => {
  try {
    const url = new URL(httpUrl);
    const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${url.host}`;
  } catch (error) {
    console.error('Invalid API base URL:', httpUrl, error);
    // Fallback for malformed URLs
    return httpUrl.replace('https://', 'wss://').replace('http://', 'ws://');
  }
};

// Main configuration object
export const API_CONFIG = {
  // HTTP API configuration
  baseUrl: getApiBaseUrl(),
  version: process.env.NEXT_PUBLIC_API_VERSION || 'v1',
  timeout: 30000, // 30 seconds
  retries: 3,
  retryDelay: 1000, // 1 second
  
  // WebSocket configuration
  wsBaseUrl: getWebSocketUrl(getApiBaseUrl()),
  wsReconnectAttempts: 5,
  wsReconnectDelay: 1000,
  
  // Environment info
  environment: process.env.NODE_ENV || 'development',
  isProduction,
  isDevelopment,
} as const;

// Helper functions for common URL construction
export const buildApiUrl = (path: string): string => {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_CONFIG.baseUrl}${cleanPath}`;
};

export const buildWebSocketUrl = (path: string, params?: Record<string, string>): string => {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  let url = `${API_CONFIG.wsBaseUrl}${cleanPath}`;
  
  if (params) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }
  
  return url;
};

// Debug logging for production troubleshooting (browser only)
if (typeof window !== 'undefined') {
  console.log('🔧 API Configuration Debug Info:');
  console.log('API Base URL:', API_CONFIG.baseUrl);
  console.log('WebSocket Base URL:', API_CONFIG.wsBaseUrl);
  console.log('Environment:', API_CONFIG.environment);
  console.log('Full Config:', API_CONFIG);
  
  // Log all relevant environment variables
  const envVars = {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_API_VERSION: process.env.NEXT_PUBLIC_API_VERSION,
    NODE_ENV: process.env.NODE_ENV,
  };
  console.log('Environment Variables:', envVars);
}