# Frontend Integration Testing - Cursor Implementation Guide

## Overview
This directory contains comprehensive prompts for implementing authentication-first frontend integration testing using cursor coding agent. The testing approach follows a 5-phase implementation strategy with authentication as the foundational requirement.

## Authentication-First Approach
🔐 **Authentication is PRIORITY #1** - All other features (upload, chat, document management) depend on authentication working properly. Each phase builds on authenticated user contexts.

## Phase Implementation Order

### Phase 1: Authentication Foundation Testing
**File**: `PHASE1_AUTH_FOUNDATION.md`
**Duration**: Week 1 (5 days)
**Focus**: Unit testing infrastructure with authentication mocks

**Key Deliverables**:
- Jest + React Testing Library setup with auth mocks
- Authentication component unit tests (login/register/session)
- Authenticated API client unit tests
- 85%+ code coverage including authentication flows

**Start Here**: This is the foundation - all other phases depend on this being complete.

### Phase 2: Authentication Integration Testing  
**File**: `PHASE2_AUTH_INTEGRATION.md`
**Duration**: Week 2 (5 days)
**Focus**: Mock services with authentication integration testing

**Key Deliverables**:
- Mock authentication service with Docker
- Integration test framework with auth-aware utilities
- Complete authenticated API integration validation
- 95%+ pass rate on integration test suite

### Phase 3: Authentication E2E Testing
**File**: `PHASE3_AUTH_E2E.md`  
**Duration**: Week 3 (5 days)
**Focus**: Playwright E2E testing for authenticated user journeys

**Key Deliverables**:
- Playwright setup with authentication page objects
- Cross-browser authentication compatibility
- Complete authenticated upload → chat E2E flow
- 100% pass rate on critical authenticated journeys

### Phase 4: Authentication Performance Testing
**File**: `PHASE4_AUTH_PERFORMANCE.md`
**Duration**: Week 4 (5 days)  
**Focus**: Performance validation under authenticated load

**Key Deliverables**:
- Authentication performance metrics collection
- Artillery.js load testing with authenticated scenarios
- Performance baseline establishment
- Authentication response time < 1 second

### Phase 5: Full Integration Validation
**File**: `PHASE5_FULL_INTEGRATION.md`
**Duration**: Week 5 (5 days)
**Focus**: Production-ready validation with real services

**Key Deliverables**:
- Full integration environment with real backend
- Security and accessibility validation
- Deployment pipeline with quality gates
- Production readiness confirmation

## Using These Prompts with Cursor

### Step-by-Step Implementation

1. **Start with Phase 1**:
   ```bash
   # Open Phase 1 prompt
   cursor docs/initiatives/system/upload_refactor/003/integration/frontend/cursor_prompts/PHASE1_AUTH_FOUNDATION.md
   
   # Follow the prompt step-by-step
   # Implement Task 1.1 → 1.2 → 1.3 → 1.4
   ```

2. **Validate Each Phase Before Moving Forward**:
   - Unit tests must pass with 85%+ coverage
   - Integration tests must achieve 95%+ pass rate  
   - E2E tests must have 100% pass rate on critical journeys
   - Performance tests must meet target thresholds

3. **Sequential Implementation**:
   - Do NOT skip phases - each builds on the previous
   - Authentication must work before implementing upload/chat features
   - Complete all tasks in a phase before moving to the next

### Cursor Workflow Tips

**For Each Phase**:
1. Open the phase prompt file in cursor
2. Read the entire prompt to understand context and goals
3. Implement tasks in the specified order (1.1 → 1.2 → 1.3 → etc.)
4. Run tests after each task to validate progress
5. Only move to next phase after meeting all success criteria

**Authentication Context**:
```typescript
// Always establish authentication context first
beforeEach(async () => {
  const { session } = await setupAuthenticatedUser();
  // Now test authenticated features
});
```

**Error Handling Pattern**:
```typescript
// Test both authenticated and unauthenticated scenarios
test('should require authentication', async () => {
  // Test without auth - should fail
  await expect(protectedOperation()).rejects.toThrow(/auth/i);
  
  // Test with auth - should succeed  
  await setupAuth();
  await expect(protectedOperation()).resolves.toBeDefined();
});
```

## Key Testing Infrastructure

### Authentication Test Stack
- **Jest + React Testing Library**: Unit testing with auth mocks
- **MSW (Mock Service Worker)**: API mocking with authentication
- **Playwright**: E2E testing with cross-browser auth validation  
- **Artillery.js**: Load testing with authenticated user scenarios
- **Docker Compose**: Integration environments with auth services

### Authentication Flow Priority
1. **User Registration** → Email validation and account creation
2. **User Login** → Credential validation and session creation
3. **Session Management** → Token persistence and refresh
4. **Protected Routes** → Access control for authenticated features
5. **Logout** → Session cleanup and redirect

### Performance Targets
```javascript
const AUTH_PERFORMANCE_TARGETS = {
  registrationTime: 1000,      // < 1 second
  loginTime: 1000,             // < 1 second  
  sessionValidation: 500,      // < 500ms
  tokenRefresh: 1000,          // < 1 second
  logoutTime: 500,             // < 500ms
};
```

## Success Metrics

### Phase Completion Criteria
- **Phase 1**: 85%+ unit test coverage, all auth unit tests pass
- **Phase 2**: 95%+ integration test pass rate, auth flows validated  
- **Phase 3**: 100% critical E2E journeys pass, cross-browser auth works
- **Phase 4**: Performance targets met, load testing successful
- **Phase 5**: Production readiness validated, deployment pipeline ready

### Overall Success Criteria
✅ **Authentication Foundation**: Complete auth flow testing  
✅ **Feature Integration**: Authenticated upload and chat flows  
✅ **Cross-browser Support**: Auth works in Chrome, Firefox, Safari  
✅ **Performance Validation**: Auth meets response time targets  
✅ **Production Readiness**: Security, accessibility, deployment validated

## File Structure Overview
```
ui/
├── __tests__/
│   ├── components/
│   │   ├── auth/           # Authentication components
│   │   ├── DocumentUpload.test.tsx
│   │   └── ChatPage.test.tsx
│   └── lib/
│       ├── supabase-client.test.ts  # Auth API tests
│       └── api-client.test.ts       # Authenticated API tests

tests/integration/
├── docker-compose.mock.yml          # Mock auth services
├── setup/
│   ├── auth-helpers.ts             # Auth test utilities
│   └── environment.ts              # Environment management
└── scenarios/
    ├── auth-flow.test.ts           # Authentication integration
    ├── upload-flow.test.ts         # Authenticated upload
    └── chat-flow.test.ts           # Authenticated chat

e2e/
├── playwright.config.ts            # Cross-browser config
├── tests/
│   ├── auth-flow.spec.ts           # Auth E2E tests
│   └── authenticated-*.spec.ts     # Feature E2E tests
└── page-objects/
    ├── AuthPage.ts                 # Auth page object
    ├── UploadPage.ts               # Upload page object  
    └── ChatPage.ts                 # Chat page object

performance/
├── artillery-auth.yml              # Auth load testing
└── run-auth-performance.js        # Performance runner
```

## Common Patterns

### Authentication Setup Pattern
```typescript
export const setupAuthenticatedUser = async () => {
  const user = createTestUser();
  await authService.register(user.email, user.password);
  const session = await authService.login(user.email, user.password);
  return { user, session };
};
```

### Protected Feature Testing Pattern
```typescript
describe('Protected Feature', () => {
  beforeEach(async () => {
    await setupAuthenticatedUser();
  });
  
  test('should work with authentication', () => {
    // Test authenticated feature
  });
});
```

### Cross-browser Authentication Pattern
```typescript
test.describe('Cross-browser Auth', () => {
  ['chromium', 'firefox', 'webkit'].forEach(browserName => {
    test(`should work in ${browserName}`, async ({ browser }) => {
      // Test auth in specific browser
    });
  });
});
```

Start with **Phase 1** and work sequentially through each phase. Authentication is the foundation - get it working first, then build authenticated features on top of it.

## Next Steps After Completion
Upon successful completion of all 5 phases, the system will be ready for the **Cloud Deployment Initiative**:
- **Vercel**: Frontend deployment  
- **Render**: Backend deployment
- **Supabase**: Production database
- **End-to-end cloud validation**: Complete production system testing