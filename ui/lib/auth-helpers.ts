export interface User {
  id: string;
  email: string;
  created_at?: string;
  updated_at?: string;
}

export interface Session {
  access_token: string;
  refresh_token: string;
  expires_at?: number;
  user: User;
}

/**
 * Get current user from authentication token
 */
export const getCurrentUser = async (token: string): Promise<User> => {
  try {
    const response = await fetch('/api/auth/user', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to get current user');
    }
    
    const userData = await response.json();
    return userData.user || userData;
  } catch (error) {
    console.error('Error getting current user:', error);
    throw new Error('Authentication failed');
  }
};

/**
 * Validate if a user has access to specific documents
 */
export const validateUserAccess = async (token: string, userId: string): Promise<boolean> => {
  try {
    const currentUser = await getCurrentUser(token);
    return currentUser.id === userId;
  } catch (error) {
    console.error('Error validating user access:', error);
    return false;
  }
};

/**
 * Get authentication token from localStorage or Supabase session
 */
export const getAuthToken = async (): Promise<string | null> => {
  if (typeof window === 'undefined') return null;
  
  // First try to get token from localStorage
  let token = localStorage.getItem('token') || localStorage.getItem('supabase.auth.token');
  
  if (token) {
    return token;
  }
  
  // If no token in localStorage, try to get from Supabase session
  try {
    const { createClient } = await import('@supabase/supabase-js');
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    
    if (supabaseUrl && supabaseAnonKey) {
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session?.access_token) {
        // Store the token for future use
        localStorage.setItem('token', session.access_token);
        return session.access_token;
      }
    }
  } catch (error) {
    console.warn('Failed to get token from Supabase session:', error);
  }
  
  return null;
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = async (): Promise<boolean> => {
  const token = await getAuthToken();
  return !!token;
};

/**
 * Clear authentication data
 */
export const clearAuth = (): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('token');
  localStorage.removeItem('supabase.auth.token');
  sessionStorage.clear();
};
