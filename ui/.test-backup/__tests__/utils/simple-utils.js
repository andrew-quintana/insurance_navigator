module.exports = {
  mockUser: {
    id: 'test-user-id',
    email: 'test@example.com',
    user_metadata: { name: 'Test User' }
  },
  
  mockSession: {
    access_token: 'mock-jwt-token',
    refresh_token: 'mock-refresh-token',
    expires_at: Date.now() + 3600000,
    user: {
      id: 'test-user-id',
      email: 'test@example.com',
      user_metadata: { name: 'Test User' }
    }
  }
}


