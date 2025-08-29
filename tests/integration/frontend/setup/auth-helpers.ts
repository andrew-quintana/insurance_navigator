export interface User {
  id: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  access_token: string;
  refresh_token: string;
  user_id: string;
  expires_at: string;
}

export interface AuthResponse {
  user: User;
  session: Session;
}

export class AuthTestHelper {
  private baseUrl: string;
  private testUsers: Map<string, { user: User; session: Session }> = new Map();

  constructor(baseUrl: string = 'http://localhost:3001') {
    this.baseUrl = baseUrl;
  }

  /**
   * Create a new test user with email validation
   */
  async createTestUser(email: string, password: string): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/v1/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to create user: ${response.status}`);
      }

      const result = await response.json();
      
      // Store test user for cleanup
      this.testUsers.set(email, {
        user: result.user,
        session: result.session
      });

      return result;
    } catch (error) {
      console.error('Error creating test user:', error);
      throw error;
    }
  }

  /**
   * Login an existing user with credentials
   */
  async loginUser(email: string, password: string): Promise<Session> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/v1/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          grant_type: 'password',
          email,
          password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Login failed: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error logging in user:', error);
      throw error;
    }
  }

  /**
   * Set up an authenticated session for testing
   */
  async setupAuthenticatedSession(email?: string, password?: string): Promise<{ user: User; session: Session }> {
    const testEmail = email || `test-${Date.now()}@example.com`;
    const testPassword = password || 'TestPassword123!';

    try {
      // Try to create user first (may fail if already exists)
      try {
        const result = await this.createTestUser(testEmail, testPassword);
        return result;
      } catch (error: any) {
        if (error.message.includes('already registered')) {
          // User exists, try to login
          const session = await this.loginUser(testEmail, testPassword);
          
          // Get user info
          const userResponse = await fetch(`${this.baseUrl}/auth/v1/user`, {
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
            },
          });

          if (!userResponse.ok) {
            throw new Error('Failed to get user info after login');
          }

          const user = await userResponse.json();
          
          return {
            user,
            session
          };
        }
        throw error;
      }
    } catch (error) {
      console.error('Error setting up authenticated session:', error);
      throw error;
    }
  }

  /**
   * Mock session expiry for testing token refresh scenarios
   */
  async mockSessionExpiry(): Promise<void> {
    // This would need backend support to actually expire tokens
    // For now, we'll simulate by clearing stored sessions
    console.log('Mocking session expiry...');
    
    // In a real scenario, you might:
    // 1. Wait for token to expire naturally
    // 2. Call backend to invalidate token
    // 3. Modify token expiration time in backend
    
    // For testing purposes, we'll just wait a bit
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  /**
   * Refresh user token using refresh token
   */
  async refreshUserToken(refreshToken: string): Promise<Session> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/v1/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          grant_type: 'refresh_token',
          refresh_token: refreshToken,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Token refresh failed: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error refreshing token:', error);
      throw error;
    }
  }

  /**
   * Validate current session
   */
  async validateSession(accessToken: string): Promise<User> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/v1/user`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Session validation failed: ${response.status}`);
      }

      const user = await response.json();
      return user;
    } catch (error) {
      console.error('Error validating session:', error);
      throw error;
    }
  }

  /**
   * Logout user and clear session
   */
  async logoutUser(accessToken: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/v1/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Logout failed: ${response.status}`);
      }

      console.log('User logged out successfully');
    } catch (error) {
      console.error('Error logging out user:', error);
      throw error;
    }
  }

  /**
   * Clean up test users and sessions
   */
  async cleanupTestUsers(): Promise<void> {
    try {
      // Clear all test users from the mock service
      const response = await fetch(`${this.baseUrl}/test/users`, {
        method: 'DELETE',
      });

      if (response.ok) {
        console.log('All test users cleared');
        this.testUsers.clear();
      } else {
        console.warn('Failed to clear test users via API');
      }
    } catch (error) {
      console.error('Error cleaning up test users:', error);
      // Don't throw error during cleanup
    }
  }

  /**
   * Get list of test users
   */
  async getTestUsers(): Promise<User[]> {
    try {
      const response = await fetch(`${this.baseUrl}/test/users`);
      
      if (!response.ok) {
        throw new Error(`Failed to get test users: ${response.status}`);
      }

      const users = await response.json();
      return users;
    } catch (error) {
      console.error('Error getting test users:', error);
      return [];
    }
  }

  /**
   * Create multiple test users for load testing
   */
  async createMultipleTestUsers(count: number, baseEmail: string = 'load-test'): Promise<AuthResponse[]> {
    const users: AuthResponse[] = [];
    
    for (let i = 0; i < count; i++) {
      const email = `${baseEmail}-${i}-${Date.now()}@example.com`;
      const password = 'LoadTest123!';
      
      try {
        const user = await this.createTestUser(email, password);
        users.push(user);
      } catch (error) {
        console.error(`Failed to create user ${i}:`, error);
      }
    }
    
    return users;
  }

  /**
   * Test authentication service health
   */
  async testServiceHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok;
    } catch (error) {
      console.error('Auth service health check failed:', error);
      return false;
    }
  }

  /**
   * Wait for authentication service to be ready
   */
  async waitForServiceReady(maxAttempts: number = 30, delay: number = 1000): Promise<void> {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      if (await this.testServiceHealth()) {
        console.log(`Auth service ready after ${attempt} attempts`);
        return;
      }
      
      console.log(`Auth service not ready, attempt ${attempt}/${maxAttempts}`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    throw new Error(`Auth service failed to become ready after ${maxAttempts} attempts`);
  }
}
