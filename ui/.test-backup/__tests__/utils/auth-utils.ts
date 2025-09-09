// Comprehensive auth test utilities
export const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
  user_metadata: { name: 'Test User' }
}

export const mockSession = {
  access_token: 'mock-jwt-token',
  refresh_token: 'mock-refresh-token',
  expires_at: Date.now() + 3600000, // 1 hour from now
  user: mockUser
}

export function setupAuthenticatedUser() {
  const mockSupabase = {
    auth: {
      getSession: jest.fn().mockResolvedValue({ 
        data: { session: mockSession },
        error: null
      }),
      signInWithPassword: jest.fn().mockResolvedValue({ 
        data: { user: mockUser, session: mockSession },
        error: null
      }),
      signUp: jest.fn().mockResolvedValue({ 
        data: { user: mockUser, session: mockSession },
        error: null
      }),
      refreshSession: jest.fn().mockResolvedValue({ 
        data: { session: mockSession, user: mockUser },
        error: null
      }),
      onAuthStateChange: jest.fn().mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } }
      })
    }
  };
  return mockSupabase;
}

export function setupUnauthenticatedUser() {
  const mockSupabase = {
    auth: {
      getSession: jest.fn().mockResolvedValue({ 
        data: { session: null },
        error: null
      }),
      signInWithPassword: jest.fn().mockResolvedValue({ 
        data: { user: null, session: null },
        error: { message: 'Invalid credentials' }
      }),
      onAuthStateChange: jest.fn().mockReturnValue({
        data: { subscription: { unsubscribe: jest.fn() } }
      })
    }
  };
  return mockSupabase;
}

export function mockSessionExpiry() {
  const expiredSession = {
    ...mockSession,
    expires_at: Date.now() - 1000 // Expired 1 second ago
  }
  
  return {
    auth: {
      getSession: jest.fn().mockResolvedValue({
        data: { session: expiredSession },
        error: null
      })
    }
  };
}

export function mockTokenRefresh() {
  const newSession = {
    ...mockSession,
    access_token: 'new-mock-jwt-token',
    expires_at: Date.now() + 3600000
  }
  
  return {
    auth: {
      refreshSession: jest.fn().mockResolvedValue({
        data: { session: newSession, user: mockUser },
        error: null
      })
    }
  };
}

export function resetAuthMocks() {
  jest.clearAllMocks()
}

export function createTestUser(suffix?: string) {
  return {
    email: `test-${suffix || Date.now()}@example.com`,
    password: 'TestPassword123!'
  }
}

export function simulateAuthStateChange(user: any, session: any) {
  console.log('Auth state change simulated:', { user, session });
}


