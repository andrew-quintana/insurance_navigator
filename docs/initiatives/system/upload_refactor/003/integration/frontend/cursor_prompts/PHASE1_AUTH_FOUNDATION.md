# Phase 1: Authentication Foundation Testing - Cursor Implementation Prompt

## Context
You are implementing Phase 1 of frontend integration testing for an insurance document upload and AI agent chat system. This phase focuses on establishing authentication-first testing infrastructure and unit tests. Authentication is PRIORITY #1 since all other features depend on it.

## Current System Overview
- **Frontend**: Next.js/React UI in `/ui` directory
- **Backend**: FastAPI with upload pipeline and AI agents
- **Authentication**: Supabase Auth with JWT tokens
- **Database**: PostgreSQL with Supabase
- **Key Components**: DocumentUpload, DocumentManager, ChatInterface
- **API Client**: `/ui/lib/api-client.ts` and `/ui/lib/supabase-client.ts`

## Phase 1 Goals
1. Set up Jest + React Testing Library with authentication mocks
2. Create comprehensive authentication component unit tests
3. Create authenticated API client unit tests
4. Establish CI/CD pipeline with coverage reporting
5. Achieve 85%+ code coverage including authentication flows

## Implementation Tasks

### Task 1.1: Authentication Testing Infrastructure Setup
**Priority**: CRITICAL - This is the foundation for all other tests

```bash
# Install dependencies
cd ui
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom msw
```

**Files to Create/Update**:

1. **`ui/jest.config.js`** - Configure Jest with Next.js and authentication mocks
2. **`ui/jest.setup.js`** - Set up test environment with Supabase and API mocks
3. **`ui/__mocks__/`** directory - Mock implementations for auth services
4. **`ui/__tests__/`** directory structure for organized tests

**Key Requirements**:
- Mock Supabase auth client with realistic auth flows
- Mock Next.js router for authentication redirects
- Set up MSW for API mocking with auth headers
- Configure coverage thresholds: 85% lines, 80% branches
- Include authentication-aware test utilities

### Task 1.2: Authentication Component Unit Tests
**Priority**: CRITICAL - Authentication must work before other features

**Components to Test** (in order of priority):

1. **Authentication Components** (Create if missing):
   - Login form component
   - Registration form component  
   - Protected route wrapper component
   - Session state management components

2. **`DocumentUpload.tsx`** - Test with authentication context:
   - Requires authentication before allowing upload
   - Shows login prompt for unauthenticated users
   - Includes auth headers in upload requests
   - Handles auth errors during upload

3. **`DocumentManager.tsx`** - Test with user context:
   - Shows only user's own documents
   - Requires authentication for document operations
   - Handles session expiry during operations

4. **`app/chat/page.tsx`** - Test with authenticated context:
   - Requires authentication for chat access
   - Includes user context in chat requests
   - Handles auth errors gracefully

**Test Coverage Requirements**:
- Authentication success/failure scenarios
- Session persistence and expiry
- Protected route access control
- Error handling for auth failures
- User data isolation

### Task 1.3: Authentication API Client Unit Tests  
**Priority**: CRITICAL - API client handles all auth communications

**Files to Test**:

1. **`lib/supabase-client.ts`** (PRIORITY #1):
   ```typescript
   // Test functions to implement:
   - signUp(email, password) // User registration
   - signIn(email, password) // User login
   - signOut() // Session cleanup
   - getSession() // Current session
   - refreshSession() // Token refresh
   - resetPassword(email) // Password reset
   ```

2. **`lib/api-client.ts`** (Authenticated requests):
   ```typescript
   // Test functions with auth headers:
   - uploadDocument(file, progressCallback) // With auth
   - getDocuments(userId) // User-specific
   - deleteDocument(docId) // With ownership check
   - sendChatMessage(message, context) // With user context
   ```

**Test Scenarios**:
- Successful authentication flows
- Invalid credential handling  
- Token refresh during long operations
- Authentication header inclusion
- Session expiry handling
- Network error retry with auth

### Task 1.4: CI/CD Integration
**Files to Update**:
- `.github/workflows/` - Add test automation
- `ui/package.json` - Add test scripts

**Required Scripts**:
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --watchAll=false"
  }
}
```

## Implementation Guidelines

### Authentication Test Patterns
```typescript
// Authentication setup for tests
beforeEach(async () => {
  // Mock authenticated user
  mockSupabaseAuth.mockImplementation(() => ({
    user: { id: 'test-user-id', email: 'test@example.com' },
    session: { access_token: 'mock-jwt-token' }
  }));
});

// Test unauthenticated access
it('should redirect unauthenticated users', () => {
  mockSupabaseAuth.mockImplementation(() => ({ user: null, session: null }));
  // Test component behavior
});
```

### Error Handling Patterns
```typescript
// Test authentication errors
it('should handle authentication errors', async () => {
  mockSupabaseAuth.signIn.mockRejectedValue(new Error('Invalid credentials'));
  // Test error handling
});
```

## Success Criteria
- [ ] All authentication tests pass (100% for auth flows)
- [ ] 85%+ overall code coverage
- [ ] CI pipeline runs tests successfully
- [ ] Authentication mocks work reliably
- [ ] All components handle auth states correctly
- [ ] API client includes auth headers properly
- [ ] Error scenarios covered comprehensively

## Next Phase
After Phase 1 completion, you'll move to Phase 2: Authentication Integration Testing with mock services and full request/response cycle validation.

## File Structure Expected
```
ui/
├── __tests__/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.test.tsx
│   │   │   ├── RegisterForm.test.tsx
│   │   │   └── ProtectedRoute.test.tsx
│   │   ├── DocumentUpload.test.tsx
│   │   ├── DocumentManager.test.tsx
│   │   └── ChatPage.test.tsx
│   ├── lib/
│   │   ├── supabase-client.test.ts
│   │   └── api-client.test.ts
│   └── utils/
│       └── auth-helpers.test.ts
├── __mocks__/
│   ├── @supabase/
│   ├── next/
│   └── lib/
├── jest.config.js
├── jest.setup.js
└── package.json (updated)
```

Start with Task 1.1 (infrastructure) and work sequentially through each task. Focus on authentication first - it's the foundation everything else builds on.