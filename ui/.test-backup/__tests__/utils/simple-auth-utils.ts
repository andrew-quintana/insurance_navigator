// Simple auth test utilities
export const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
  name: 'Test User'
}

export const mockSession = {
  access_token: 'mock-jwt-token',
  refresh_token: 'mock-refresh-token',
  user: mockUser
}

export function setupAuthenticatedUser() {
  console.log('setupAuthenticatedUser function called');
  const mock = {
    auth: {
      getSession: jest.fn().mockResolvedValue({ data: { session: mockSession } }),
      signInWithPassword: jest.fn().mockResolvedValue({ data: { user: mockUser, session: mockSession } })
    }
  };
  console.log('Created mock:', mock);
  return mock;
}

export function setupUnauthenticatedUser() {
  console.log('setupUnauthenticatedUser function called');
  const mock = {
    auth: {
      getSession: jest.fn().mockResolvedValue({ data: { session: null } }),
      signInWithPassword: jest.fn().mockResolvedValue({ data: { user: null, session: null } })
    }
  };
  console.log('Created mock:', mock);
  return mock;
}


