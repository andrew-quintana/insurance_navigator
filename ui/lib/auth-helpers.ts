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
 * Get authentication token from localStorage
 */
export const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token') || localStorage.getItem('supabase.auth.token');
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  const token = getAuthToken();
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
