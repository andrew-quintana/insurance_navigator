/**
 * API Client Configuration for Medicare Navigator
 * Handles all API communications with error handling and retry logic
 */

// Types
export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: unknown;
}

export interface ApiResponse<T = unknown> {
  data?: T;
  error?: ApiError;
  success: boolean;
}

export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: unknown;
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
  cache?: RequestCache;
}

// Configuration
const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  version: process.env.NEXT_PUBLIC_API_VERSION || 'v1',
  timeout: 30000, // 30 seconds
  retries: 3,
  retryDelay: 1000, // 1 second
} as const;

// Debug logging for production troubleshooting
if (typeof window !== 'undefined') {
  console.log('🔍 API Client Debug Info:');
  console.log('NEXT_PUBLIC_API_BASE_URL:', process.env.NEXT_PUBLIC_API_BASE_URL);
  console.log('API_CONFIG.baseUrl:', API_CONFIG.baseUrl);
  console.log('All NEXT_PUBLIC_ Environment variables:');
  
  // Log all environment variables that start with NEXT_PUBLIC_
  Object.keys(process.env).forEach(key => {
    if (key.startsWith('NEXT_PUBLIC_')) {
      console.log(`  ${key}:`, process.env[key]);
    }
  });
  
  console.log('Environment variables object:', {
    NODE_ENV: process.env.NODE_ENV,
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_WEB_URL: process.env.NEXT_PUBLIC_WEB_URL
  });
  
  // Check if running in production
  console.log('Build environment:', {
    isProduction: process.env.NODE_ENV === 'production',
    isDevelopment: process.env.NODE_ENV === 'development',
    actualNodeEnv: process.env.NODE_ENV
  });
}

// Utility functions
const sleep = (ms: number): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms));

const isNetworkError = (error: unknown): boolean => {
  if (error instanceof TypeError) {
    return error.message.includes('fetch') || error.message.includes('network');
  }
  if (error instanceof Error) {
    return error.message.toLowerCase().includes('network') || 
           error.message.toLowerCase().includes('fetch') ||
           error.message.toLowerCase().includes('connection') ||
           error.message.toLowerCase().includes('timeout');
  }
  return false;
};

const shouldRetry = (status: number): boolean => {
  return status >= 500 || status === 408 || status === 429;
};

/**
 * Custom API Error class
 */
export class APIError extends Error {
  public status: number;
  public code?: string;
  public details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/**
 * Get authentication token from storage
 */
const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  
  try {
    return localStorage.getItem('token') || 
           localStorage.getItem('supabase.auth.token') ||
           sessionStorage.getItem('token') ||
           sessionStorage.getItem('supabase.auth.token') ||
           document.cookie
             .split('; ')
             .find(row => row.startsWith('auth-token='))
             ?.split('=')[1] || null;
  } catch {
    return null;
  }
};

/**
 * Build full API URL
 */
const buildUrl = (endpoint: string): string => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  const baseUrl = API_CONFIG.baseUrl.endsWith('/') 
    ? API_CONFIG.baseUrl.slice(0, -1) 
    : API_CONFIG.baseUrl;
  
  return `${baseUrl}/api/${API_CONFIG.version}/${cleanEndpoint}`;
};

/**
 * Build request headers
 */
const buildHeaders = async (customHeaders: Record<string, string> = {}): Promise<HeadersInit> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...customHeaders,
  };

  const token = await getAuthToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  // Add CSRF token if available
  const csrfToken = process.env.NEXT_PUBLIC_CSRF_TOKEN;
  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  return headers;
};

/**
 * Create AbortController with timeout
 */
const createAbortController = (timeout: number): AbortController => {
  const controller = new AbortController();
  
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeout);

  // Clear timeout if request completes normally
  controller.signal.addEventListener('abort', () => {
    clearTimeout(timeoutId);
  });

  return controller;
};

/**
 * Main API request function with retry logic
 */
export async function apiRequest<T = unknown>(
  endpoint: string,
  config: RequestConfig = {}
): Promise<ApiResponse<T>> {
  const {
    method = 'GET',
    body,
    headers = {},
    timeout = API_CONFIG.timeout,
    retries = API_CONFIG.retries,
    cache = 'default',
  } = config;

  const url = buildUrl(endpoint);
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = createAbortController(timeout);
      
      const requestInit: RequestInit = {
        method,
        headers: await buildHeaders(headers),
        signal: controller.signal,
        cache,
      };

      if (body && method !== 'GET') {
        requestInit.body = JSON.stringify(body);
      }

      const response = await fetch(url, requestInit);
      
      // Handle non-JSON responses
      const contentType = response.headers.get('content-type');
      let responseData: unknown;
      
      if (contentType?.includes('application/json')) {
        responseData = await response.json();
      } else {
        responseData = await response.text();
      }

      // Handle successful responses
      if (response.ok) {
        return {
          data: responseData as T,
          success: true,
        };
      }

      // Handle client/server errors
      const error: ApiError = {
        message: typeof responseData === 'object' && responseData && 'message' in responseData
          ? String(responseData.message)
          : `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
        code: typeof responseData === 'object' && responseData && 'code' in responseData
          ? String(responseData.code)
          : undefined,
        details: responseData,
      };

      // Don't retry client errors (4xx)
      if (!shouldRetry(response.status)) {
        return { error, success: false };
      }

      lastError = new APIError(error.message, error.status, error.code, error.details);

    } catch (err) {
      lastError = err instanceof Error ? err : new Error('Unknown error occurred');
      
      // Don't retry if it's not a network error
      if (!isNetworkError(err) && attempt === 0) {
        break;
      }
    }

    // Wait before retrying (with exponential backoff)
    if (attempt < retries) {
      const delay = API_CONFIG.retryDelay * Math.pow(2, attempt);
      await sleep(delay);
    }
  }

  // Return final error
  const finalError: ApiError = lastError instanceof APIError
    ? {
        message: lastError.message,
        status: lastError.status,
        code: lastError.code,
        details: lastError.details,
      }
    : {
        message: lastError?.message || 'Request failed after retries',
        status: 0,
      };

  return { error: finalError, success: false };
}

/**
 * Convenience methods for different HTTP verbs
 */
export const api = {
  get: <T = unknown>(endpoint: string, config?: Omit<RequestConfig, 'method'>) =>
    apiRequest<T>(endpoint, { ...config, method: 'GET' }),

  post: <T = unknown>(endpoint: string, body?: unknown, config?: Omit<RequestConfig, 'method' | 'body'>) =>
    apiRequest<T>(endpoint, { ...config, method: 'POST', body }),

  put: <T = unknown>(endpoint: string, body?: unknown, config?: Omit<RequestConfig, 'method' | 'body'>) =>
    apiRequest<T>(endpoint, { ...config, method: 'PUT', body }),

  patch: <T = unknown>(endpoint: string, body?: unknown, config?: Omit<RequestConfig, 'method' | 'body'>) =>
    apiRequest<T>(endpoint, { ...config, method: 'PATCH', body }),

  delete: <T = unknown>(endpoint: string, config?: Omit<RequestConfig, 'method'>) =>
    apiRequest<T>(endpoint, { ...config, method: 'DELETE' }),
};

/**
 * Health check utility
 */
export async function healthCheck(): Promise<ApiResponse<{ status: string; timestamp?: number }>> {
  try {
    const response = await api.get<{ status: string; timestamp?: number }>('/health');
    return response;
  } catch (error) {
    return {
      success: false,
      error: {
        message: error instanceof Error ? error.message : 'Health check failed',
        status: 0,
      },
    };
  }
}

/**
 * Get API configuration info
 */
export function getApiConfig() {
  return {
    baseUrl: API_CONFIG.baseUrl,
    version: API_CONFIG.version,
    timeout: API_CONFIG.timeout,
    retries: API_CONFIG.retries,
    retryDelay: API_CONFIG.retryDelay,
  };
} 