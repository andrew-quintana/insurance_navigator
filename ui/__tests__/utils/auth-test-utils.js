// Mock user data
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

// Mock authenticated user setup
export const setupAuthenticatedUser = () => {
  const { supabase } = require('@/lib/supabase-client')
  
  supabase.auth.getSession.mockResolvedValue({
    data: { session: mockSession },
    error: null
  })
  
  supabase.auth.signInWithPassword.mockResolvedValue({
    data: { user: mockUser, session: mockSession },
    error: null
  })
  
  supabase.auth.signUp.mockResolvedValue({
    data: { user: mockUser, session: mockSession },
    error: null
  })
  
  supabase.auth.refreshSession.mockResolvedValue({
    data: { session: mockSession, user: mockUser },
    error: null
  })
  
  // Mock localStorage for session persistence
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: jest.fn((key) => {
        if (key === 'supabase.auth.token') {
          return JSON.stringify(mockSession)
        }
        return null
      }),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    },
    writable: true,
  })
}

// Mock unauthenticated user setup
export const setupUnauthenticatedUser = () => {
  const { supabase } = require('@/lib/supabase-client')
  
  supabase.auth.getSession.mockResolvedValue({
    data: { session: null },
    error: null
  })
  
  supabase.auth.signInWithPassword.mockResolvedValue({
    data: { user: null, session: null },
    error: { message: 'Invalid credentials' }
  })
  
  // Mock localStorage for no session
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: jest.fn(() => null),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    },
    writable: true,
  })
}

// Mock session expiry
export const mockSessionExpiry = () => {
  const { supabase } = require('@/lib/supabase-client')
  
  const expiredSession = {
    ...mockSession,
    expires_at: Date.now() - 1000 // Expired 1 second ago
  }
  
  supabase.auth.getSession.mockResolvedValue({
    data: { session: expiredSession },
    error: null
  })
}

// Mock token refresh
export const mockTokenRefresh = () => {
  const { supabase } = require('@/lib/supabase-client')
  
  const newSession = {
    ...mockSession,
    access_token: 'new-mock-jwt-token',
    expires_at: Date.now() + 3600000
  }
  
  supabase.auth.refreshSession.mockResolvedValue({
    data: { session: newSession, user: mockUser },
    error: null
  })
}

// Reset all auth mocks
export const resetAuthMocks = () => {
  const { supabase } = require('@/lib/supabase-client')
  
  // Reset all mock functions
  jest.clearAllMocks()
  
  // Reset localStorage mock
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    },
    writable: true,
  })
}

// Helper to create test users with unique emails
export const createTestUser = (suffix) => ({
  email: `test-${suffix || Date.now()}@example.com`,
  password: 'TestPassword123!'
})

// Helper to simulate authentication state change
export const simulateAuthStateChange = (user, session) => {
  const mockCallback = supabase.auth.onAuthStateChange.mock.calls[0]?.[0]
  if (mockCallback) {
    mockCallback('SIGNED_IN', session)
  }
}
