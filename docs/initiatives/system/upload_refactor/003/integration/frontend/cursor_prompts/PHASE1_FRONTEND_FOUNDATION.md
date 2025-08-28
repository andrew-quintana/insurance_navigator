# Phase 1: Frontend Integration Foundation & Unit Testing - Cursor Implementation Prompt

## Context
You are implementing Phase 1 of comprehensive frontend integration testing for an insurance document upload and AI agent chat system. This phase establishes the complete testing foundation with authentication-first approach.

## Required Reading
**Before starting, read these documentation files to understand the complete scope:**
1. `docs/initiatives/system/upload_refactor/003/integration/frontend/TESTING_SPEC001.md` - Complete frontend integration scope
2. `docs/initiatives/system/upload_refactor/003/integration/frontend/RFC001.md` - Technical architecture
3. `docs/initiatives/system/upload_refactor/003/integration/frontend/TODO001.md` - Phase 1 implementation tasks

Authentication is PRIORITY #1 since all other features depend on it, but this phase covers the complete frontend integration scope.

## Current System Overview
- **Frontend**: Next.js/React UI in `/ui` directory
- **Backend**: FastAPI with upload pipeline and AI agents
- **Authentication**: Supabase Auth with JWT tokens
- **Database**: PostgreSQL with Supabase
- **Key Components**: DocumentUpload, DocumentManager, ChatInterface
- **API Client**: `/ui/lib/api-client.ts` and `/ui/lib/supabase-client.ts`

## Phase 1 Goals (Reference: TODO001.md Phase 1)
1. Audit existing unit tests from previous efforts
2. Set up Jest + React Testing Library with authentication mocks
3. Create comprehensive unit tests for all frontend components:
   - Authentication components (PRIORITY #1)
   - Frontend upload components (DocumentUpload, DocumentManager, DocumentUploadModal)
   - Chat interface components
   - Document state management components
   - Responsive design components
4. Create authenticated API client unit tests
5. Establish CI/CD pipeline with coverage reporting
6. Achieve 85%+ code coverage including complete frontend integration scope

## Implementation Tasks

### Task 1.1: Complete Frontend Testing Infrastructure Setup
**Priority**: CRITICAL - This is the foundation for all frontend integration testing

**Reference**: TODO001.md Section 1.1 for detailed tasks

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

### Task 1.2: Complete Frontend Component Unit Tests
**Priority**: CRITICAL - All frontend components with authentication-first approach

**Reference**: TODO001.md Section 1.2 for complete component list and requirements

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

### Task 1.3: Complete API Client Unit Tests
**Priority**: CRITICAL - API client handles all frontend-backend communications

**Reference**: TODO001.md Section 1.3 for detailed API testing requirements

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

## Success Criteria (Reference: TODO001.md Phase 1 Acceptance Criteria)
- [ ] All unit tests pass including complete frontend integration scope
- [ ] 85%+ code coverage on all frontend components including auth flows
- [ ] Upload components tested with various file types and sizes
- [ ] Chat components tested with document context integration
- [ ] Responsive design tested across viewport sizes
- [ ] Cross-browser compatibility validated in unit tests
- [ ] Authentication errors properly handled and tested
- [ ] Document state transitions thoroughly tested
- [ ] CI pipeline runs tests successfully
- [ ] Tests run in < 60 seconds including complete setup

## Phase 1 Documentation Requirements
**Create these deliverables in `docs/initiatives/system/upload_refactor/003/integration/frontend/phase1/`:**
1. **PHASE1_COMPLETION_SUMMARY.md** - Summary of all work completed
2. **PHASE1_TEST_COVERAGE_REPORT.md** - Detailed coverage analysis
3. **PHASE1_DECISIONS.md** - Technical decisions made during implementation
4. **PHASE1_HANDOFF.md** - Handoff notes for Phase 2
5. **PHASE1_TESTING_RESULTS.md** - Test results and any issues found

## Next Phase
After Phase 1 completion with proper documentation, you'll move to Phase 2: Complete Frontend Integration Testing with mock services covering the full scope.

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