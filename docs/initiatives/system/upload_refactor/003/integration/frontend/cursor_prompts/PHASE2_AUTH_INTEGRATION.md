# Phase 2: Authentication Integration Testing - Cursor Implementation Prompt

## Context  
You are implementing Phase 2 of frontend integration testing. Phase 1 (authentication foundation unit tests) should be complete. This phase builds authentication-aware integration tests with mock services that simulate real API interactions.

## Prerequisites
- Phase 1 complete: Unit tests passing with 85%+ coverage
- Jest + RTL infrastructure established
- Authentication mocks working
- CI/CD pipeline running tests

## Phase 2 Goals
1. Create mock authentication service environment
2. Build integration test framework with auth-aware utilities
3. Test complete authenticated API integration flows
4. Validate authentication throughout request/response cycles
5. Achieve 95% pass rate on integration test suite

## Implementation Tasks

### Task 2.1: Authentication Mock Environment Setup
**Priority**: CRITICAL - Foundation for integration testing

**Docker Environment to Create**:

1. **`tests/integration/docker-compose.mock.yml`**:
```yaml
version: '3.8'
services:
  mock-auth-service:
    build: ./mocks/auth-service
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=test
      - JWT_SECRET=test-secret-key
    
  mock-api-service:
    build: ./mocks/api-service
    ports:
      - "3002:3002"
    depends_on:
      - mock-auth-service
    environment:
      - AUTH_SERVICE_URL=http://mock-auth-service:3001
      
  frontend-test:
    build: ../../ui
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_SUPABASE_URL=http://localhost:3001
      - NEXT_PUBLIC_API_URL=http://localhost:3002
```

2. **Mock Authentication Service** (`tests/integration/mocks/auth-service/`):
   - Express server that mimics Supabase Auth API
   - JWT token generation and validation
   - User registration, login, session management
   - Realistic response delays and error scenarios

3. **Mock API Service** (`tests/integration/mocks/api-service/`):
   - Document upload endpoints with auth validation
   - Chat endpoints with user context
   - Proper HTTP status codes and error responses

**Authentication Mock Service Endpoints**:
```javascript
// POST /auth/v1/signup - User registration
// POST /auth/v1/token?grant_type=password - User login  
// POST /auth/v1/token?grant_type=refresh_token - Token refresh
// GET /auth/v1/user - Get current user
// POST /auth/v1/logout - Sign out
```

### Task 2.2: Authentication Integration Test Framework
**Priority**: CRITICAL - Utilities for auth-aware testing

**Files to Create**:

1. **`tests/integration/setup/auth-helpers.ts`**:
```typescript
export class AuthTestHelper {
  async createTestUser(email: string, password: string): Promise<User>
  async loginUser(email: string, password: string): Promise<Session>
  async setupAuthenticatedSession(): Promise<{ user: User, session: Session }>
  async mockSessionExpiry(): Promise<void>
  async refreshUserToken(refreshToken: string): Promise<Session>
  async cleanupTestUsers(): Promise<void>
}
```

2. **`tests/integration/setup/environment.ts`**:
```typescript
export class TestEnvironment {
  async startMockServices(): Promise<void>
  async stopMockServices(): Promise<void>
  async resetDatabase(): Promise<void>
  async seedTestData(): Promise<void>
  async waitForServicesReady(): Promise<void>
}
```

3. **`tests/integration/setup/api-helpers.ts`**:
```typescript
export class AuthenticatedAPIClient {
  constructor(authToken: string)
  async uploadDocument(file: File): Promise<UploadResponse>
  async getDocuments(): Promise<Document[]>
  async sendChatMessage(message: string): Promise<ChatResponse>
  async deleteDocument(docId: string): Promise<void>
}
```

### Task 2.3: Authentication API Integration Tests
**Priority**: CRITICAL - Core authentication flow validation

**Test File: `tests/integration/scenarios/auth-flow.test.ts`**

**Key Test Scenarios**:

1. **User Registration Integration**:
```typescript
describe('User Registration Integration', () => {
  it('should register new user with email validation', async () => {
    const result = await authHelper.createTestUser('test@example.com', 'password123');
    expect(result.user.email).toBe('test@example.com');
    expect(result.session.access_token).toBeDefined();
  });
  
  it('should handle duplicate email registration', async () => {
    await authHelper.createTestUser('test@example.com', 'password123');
    await expect(
      authHelper.createTestUser('test@example.com', 'password456')
    ).rejects.toThrow(/email already registered/i);
  });
});
```

2. **User Login Integration**:
```typescript
describe('User Login Integration', () => {
  it('should login with valid credentials', async () => {
    await authHelper.createTestUser('test@example.com', 'password123');
    const session = await authHelper.loginUser('test@example.com', 'password123');
    expect(session.access_token).toBeDefined();
    expect(session.user.email).toBe('test@example.com');
  });
  
  it('should reject invalid credentials', async () => {
    await expect(
      authHelper.loginUser('test@example.com', 'wrongpassword')
    ).rejects.toThrow(/invalid credentials/i);
  });
});
```

3. **Session Management Integration**:
```typescript
describe('Session Management Integration', () => {
  it('should refresh expired tokens', async () => {
    const { session } = await authHelper.setupAuthenticatedSession();
    
    // Mock token expiry
    await authHelper.mockSessionExpiry();
    
    const refreshed = await authHelper.refreshUserToken(session.refresh_token);
    expect(refreshed.access_token).toBeDefined();
    expect(refreshed.access_token).not.toBe(session.access_token);
  });
});
```

### Task 2.4: Authenticated Upload Integration Tests
**Priority**: HIGH - Core feature with authentication

**Test File: `tests/integration/scenarios/upload-flow.test.ts`**

```typescript
describe('Authenticated Upload Integration', () => {
  beforeEach(async () => {
    const { session } = await authHelper.setupAuthenticatedSession();
    apiClient = new AuthenticatedAPIClient(session.access_token);
  });
  
  it('should upload document with authentication', async () => {
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const result = await apiClient.uploadDocument(file);
    
    expect(result.documentId).toBeDefined();
    expect(result.userId).toBe(session.user.id);
  });
  
  it('should reject upload without authentication', async () => {
    const unauthenticatedClient = new AuthenticatedAPIClient('invalid-token');
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    
    await expect(unauthenticatedClient.uploadDocument(file))
      .rejects.toThrow(/unauthorized/i);
  });
});
```

### Task 2.5: Authenticated Chat Integration Tests  
**Priority**: HIGH - Agent integration with user context

**Test File: `tests/integration/scenarios/chat-flow.test.ts`**

```typescript
describe('Authenticated Chat Integration', () => {
  beforeEach(async () => {
    const { session } = await authHelper.setupAuthenticatedSession();
    apiClient = new AuthenticatedAPIClient(session.access_token);
  });
  
  it('should send message with user context', async () => {
    const response = await apiClient.sendChatMessage('What is my deductible?');
    
    expect(response.text).toBeDefined();
    expect(response.metadata.userId).toBeDefined();
    expect(response.metadata.documentContext).toBeDefined();
  });
  
  it('should handle authentication during long conversations', async () => {
    // Test token refresh during extended chat
    for (let i = 0; i < 10; i++) {
      const response = await apiClient.sendChatMessage(`Message ${i + 1}`);
      expect(response.text).toBeDefined();
    }
  });
});
```

## Implementation Guidelines

### Test Environment Management
```typescript
// Global test setup
beforeAll(async () => {
  await testEnvironment.startMockServices();
  await testEnvironment.waitForServicesReady();
});

afterAll(async () => {
  await testEnvironment.stopMockServices();
});

beforeEach(async () => {
  await testEnvironment.resetDatabase();
  await authHelper.cleanupTestUsers();
});
```

### Authentication Flow Testing
```typescript
// Pattern for testing auth-dependent features
const testWithAuthentication = async (testFn: (client: AuthenticatedAPIClient) => Promise<void>) => {
  const { session } = await authHelper.setupAuthenticatedSession();
  const client = new AuthenticatedAPIClient(session.access_token);
  await testFn(client);
};
```

### Error Scenario Testing
```typescript
// Test authentication failure scenarios
it('should handle token expiry during operation', async () => {
  const { session } = await authHelper.setupAuthenticatedSession();
  const client = new AuthenticatedAPIClient(session.access_token);
  
  // Start operation
  const uploadPromise = client.uploadDocument(testFile);
  
  // Expire token mid-operation
  setTimeout(() => authHelper.mockSessionExpiry(), 1000);
  
  // Should either succeed with refresh or fail gracefully
  const result = await uploadPromise;
  // Verify appropriate handling
});
```

## Success Criteria
- [ ] Mock authentication service running reliably
- [ ] All authentication integration tests pass (100%)
- [ ] Upload integration tests pass with auth (100%)  
- [ ] Chat integration tests pass with auth (100%)
- [ ] 95%+ pass rate on complete integration test suite
- [ ] Token refresh tested and working
- [ ] Error scenarios properly handled
- [ ] Test data isolation working
- [ ] Environment setup/teardown reliable

## File Structure Expected
```
tests/integration/
├── docker-compose.mock.yml
├── mocks/
│   ├── auth-service/
│   │   ├── Dockerfile
│   │   ├── server.js
│   │   └── package.json
│   └── api-service/
│       ├── Dockerfile
│       ├── server.js
│       └── package.json
├── setup/
│   ├── auth-helpers.ts
│   ├── environment.ts
│   └── api-helpers.ts
├── scenarios/
│   ├── auth-flow.test.ts
│   ├── upload-flow.test.ts
│   └── chat-flow.test.ts
└── fixtures/
    ├── test-users.json
    └── sample-documents/
```

## Next Phase
After Phase 2 completion, you'll move to Phase 3: Authentication E2E Testing with Playwright for full user journey validation across browsers.

Start with Task 2.1 (mock environment) and ensure the authentication service is working before building tests on top of it.