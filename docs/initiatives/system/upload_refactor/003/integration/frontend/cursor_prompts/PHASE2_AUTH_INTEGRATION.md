# Phase 2: Complete Frontend Integration Testing & Mock Environment - Cursor Implementation Prompt

## Context  
You are implementing Phase 2 of comprehensive frontend integration testing. Phase 1 (complete frontend unit tests) should be complete. This phase builds integration tests covering the complete frontend scope with mock services.

## Required Reading
**Before starting, review these documentation files:**
1. `docs/initiatives/system/upload_refactor/003/integration/frontend/TESTING_SPEC001.md` - Complete integration scope
2. `docs/initiatives/system/upload_refactor/003/integration/frontend/TODO001.md` - Phase 2 detailed tasks
3. `docs/initiatives/system/upload_refactor/003/integration/frontend/phase1/PHASE1_HANDOFF.md` - Phase 1 completion status
4. Review Phase 1 deliverables to understand current test infrastructure

## Prerequisites
- Phase 1 complete: Unit tests passing with 85%+ coverage
- Jest + RTL infrastructure established
- Authentication mocks working
- CI/CD pipeline running tests

## Phase 2 Goals (Reference: TODO001.md Phase 2)
1. Create comprehensive mock environment for all frontend components
2. Build integration test framework covering complete scope:
   - Authentication integration (PRIORITY #1)
   - Frontend upload components integration
   - Chat interface integration with real-time features
   - Document state management integration
   - Agent conversation quality integration
   - Cross-browser compatibility integration
   - Responsive design integration
   - Performance optimization integration
3. Validate complete frontend-backend integration cycles
4. Achieve 95% pass rate on complete integration test suite

## Implementation Tasks

### Task 2.1: Complete Frontend Mock Environment Setup
**Priority**: CRITICAL - Foundation for complete integration testing

**Reference**: TODO001.md Section 2.1 for detailed mock service requirements

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

### Task 2.2: Complete Frontend Integration Test Framework
**Priority**: CRITICAL - Utilities for comprehensive frontend testing

**Reference**: TODO001.md Section 2.2 for complete framework structure

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

### Task 2.3: Complete Frontend Integration Tests
**Priority**: CRITICAL - All frontend component integration validation

**Reference**: TODO001.md Section 2.3 for complete testing scope including all 8 integration areas

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

## Success Criteria (Reference: TODO001.md Phase 2 Acceptance Criteria)
- [ ] All frontend upload components integrated and tested with backend APIs
- [ ] Chat interface integration with real-time conversation and document workflows validated
- [ ] Document state management with real-time status updates working
- [ ] Agent conversation quality with RAG retrieval accuracy verified
- [ ] Cross-browser compatibility confirmed for upload → conversation flow
- [ ] Responsive design integration tested on mobile, tablet, and desktop
- [ ] Performance optimization validated for large file handling and conversation response times
- [ ] Authentication flows and user data isolation tested across all features
- [ ] Local integration testing validated against Docker Compose backend stack
- [ ] 95%+ pass rate on complete integration test suite

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

## Phase 2 Documentation Requirements
**Create these deliverables in `docs/initiatives/system/upload_refactor/003/integration/frontend/phase2/`:**
1. **PHASE2_COMPLETION_SUMMARY.md** - Summary of all integration testing implemented
2. **PHASE2_MOCK_ENVIRONMENT_DOCUMENTATION.md** - Mock service setup and configuration
3. **PHASE2_INTEGRATION_TEST_RESULTS.md** - Detailed test results for all integration areas
4. **PHASE2_DECISIONS.md** - Technical decisions made during integration testing
5. **PHASE2_HANDOFF.md** - Handoff notes for Phase 3 E2E testing

## Next Phase
After Phase 2 completion with proper documentation, you'll move to Phase 3: Complete Frontend E2E Testing with Playwright for full user journey validation covering the complete scope.

Start with Task 2.1 (mock environment) and ensure the authentication service is working before building tests on top of it.