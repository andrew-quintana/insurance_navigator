# Frontend E2E Testing with Playwright

This directory contains comprehensive end-to-end testing for the frontend integration using Playwright. The testing focuses on authentication-first validation across all browsers and devices.

## Overview

The E2E testing suite validates the complete frontend integration scope including:
- **Authentication Flow** (PRIORITY #1)
- **Document Upload Components**
- **Chat Interface Integration**
- **Document State Management**
- **Agent Conversation Quality**
- **Cross-browser Compatibility**
- **Responsive Design**
- **Performance Optimization**

## Prerequisites

- Node.js 18+ installed
- Playwright browsers installed (`npx playwright install`)
- Frontend development server running on port 3000
- Mock services running (from Phase 2 integration testing)

## Quick Start

### 1. Install Dependencies
```bash
cd ui
npm install
```

### 2. Install Playwright Browsers
```bash
npx playwright install
```

### 3. Start Development Server
```bash
npm run dev
```

### 4. Run E2E Tests
```bash
# Run all tests
npm run test:e2e

# Run specific test categories
npx playwright test auth-flow.spec.ts
npx playwright test authenticated-upload-chat.spec.ts
npx playwright test auth-cross-browser.spec.ts

# Run with specific browser
npx playwright test --project=chromium-auth
npx playwright test --project=firefox-auth
npx playwright test --project=safari-auth

# Run with mobile/tablet viewports
npx playwright test --project=mobile-auth
npx playwright test --project=tablet-auth
```

## Test Structure

### Test Files
- **`auth-flow.spec.ts`** - Core authentication flow testing (PRIORITY #1)
- **`authenticated-upload-chat.spec.ts`** - Complete upload → chat user journey
- **`auth-cross-browser.spec.ts`** - Cross-browser compatibility validation
- **`auth-mobile.spec.ts`** - Mobile device testing
- **`auth-tablet.spec.ts`** - Tablet device testing

### Page Objects
- **`AuthPage.ts`** - Authentication page interactions
- **`UploadPage.ts`** - Document upload page interactions
- **`ChatPage.ts`** - Chat interface interactions

### Test Utilities
- **`auth-helpers.ts`** - Authentication test utilities
- **`test-users.ts`** - Test user fixture management

## Test Configuration

### Playwright Config (`playwright.config.ts`)
- **Base URL**: `http://localhost:3000`
- **Test Timeout**: 60 seconds per test
- **Expect Timeout**: 10 seconds for assertions
- **Parallel Execution**: Enabled for faster testing
- **Retries**: 2 retries in CI, 0 in development

### Browser Projects
- **`chromium-auth`** - Chrome authentication tests
- **`chromium-features`** - Chrome feature tests (runs after auth)
- **`firefox-auth`** - Firefox authentication tests
- **`safari-auth`** - Safari authentication tests
- **`mobile-auth`** - Mobile device tests (iPhone 12)
- **`tablet-auth`** - Tablet device tests (iPad)

### Web Server
- **Command**: `npm run dev`
- **URL**: `http://localhost:3000`
- **Startup Timeout**: 2 minutes
- **Reuse Server**: Enabled in development, disabled in CI

## Test Scenarios

### Authentication Flow (PRIORITY #1)
1. **User Registration**
   - New user registration with email validation
   - Password strength validation
   - Duplicate email handling
   - Form validation errors

2. **User Login**
   - Valid credential authentication
   - Invalid credential rejection
   - Session management
   - Token refresh handling

3. **Session Management**
   - Session persistence across page refresh
   - Cross-tab authentication state
   - Session expiry handling
   - Logout functionality

4. **Protected Routes**
   - Unauthenticated access redirection
   - Authenticated route access
   - Session expiry redirection

### Document Upload → Chat Flow
1. **Document Upload**
   - File selection and validation
   - Upload progress tracking
   - Success/error handling
   - Document management

2. **Chat Integration**
   - Message sending and receiving
   - Agent response handling
   - Document context integration
   - Conversation persistence

3. **Error Handling**
   - Network failures
   - Service unavailability
   - Invalid file uploads
   - Authentication errors

### Cross-Browser Compatibility
1. **Browser-Specific Features**
   - Form behavior consistency
   - Keyboard navigation
   - Touch interactions
   - Storage mechanisms

2. **Performance Validation**
   - Response time consistency
   - Memory usage patterns
   - Resource loading
   - Error handling

### Responsive Design
1. **Mobile Testing**
   - Touch interactions
   - Viewport adaptation
   - Performance optimization
   - Accessibility features

2. **Tablet Testing**
   - Hybrid input methods
   - Orientation changes
   - Touch/cursor interactions
   - Responsive layouts

## Test Data Management

### Test Users
- **Dynamic Generation**: Unique email addresses for each test run
- **Browser-Specific**: Separate users for cross-browser testing
- **Device-Specific**: Separate users for mobile/tablet testing
- **Performance Testing**: Dedicated users for load testing

### Test Documents
- **Sample Policy**: Basic upload testing
- **Large Handbook**: Performance validation
- **User-Specific**: Multi-user isolation testing
- **Invalid Files**: Error handling validation

## Running Tests

### Development Mode
```bash
# Start development server
npm run dev

# Run tests in another terminal
npm run test:e2e

# Run specific test file
npx playwright test auth-flow.spec.ts

# Run with UI
npx playwright test --ui
```

### CI/CD Mode
```bash
# Run all tests in CI mode
npx playwright test --project=chromium-auth
npx playwright test --project=firefox-auth
npx playwright test --project=safari-auth

# Generate HTML report
npx playwright test --reporter=html
```

### Debug Mode
```bash
# Run with debug logging
DEBUG=pw:api npx playwright test

# Run with headed browser
npx playwright test --headed

# Run with slow motion
npx playwright test --headed --timeout=0
```

## Test Results

### HTML Report
- **Location**: `playwright-report/`
- **Features**: Test results, screenshots, videos, traces
- **Usage**: Open `index.html` in browser

### Test Artifacts
- **Screenshots**: On test failure
- **Videos**: On test failure
- **Traces**: On first retry
- **Logs**: Console output and errors

### Coverage Reports
- **Test Results**: Pass/fail statistics
- **Browser Coverage**: Cross-browser validation
- **Device Coverage**: Mobile/tablet validation
- **Performance Metrics**: Response time measurements

## Troubleshooting

### Common Issues

1. **Development Server Not Running**
   ```bash
   # Ensure dev server is running on port 3000
   npm run dev
   ```

2. **Browser Installation Issues**
   ```bash
   # Reinstall browsers
   npx playwright install --force
   ```

3. **Test Timeout Issues**
   - Check network connectivity
   - Verify mock services are running
   - Increase timeout values in config

4. **Authentication Failures**
   - Verify mock auth service is running
   - Check test user creation
   - Validate auth endpoints

### Debug Commands
```bash
# Run single test with debug
npx playwright test auth-flow.spec.ts --debug

# Run with verbose logging
npx playwright test --reporter=list

# Generate trace for debugging
npx playwright test --trace=on
```

## Best Practices

### Test Design
1. **Authentication First**: All tests require authentication
2. **Isolation**: Each test is independent
3. **Realistic Scenarios**: Test actual user workflows
4. **Error Handling**: Validate error scenarios
5. **Performance**: Measure response times

### Test Maintenance
1. **Page Objects**: Use page objects for maintainability
2. **Test Data**: Generate unique test data
3. **Assertions**: Use descriptive assertion messages
4. **Documentation**: Document test scenarios
5. **Regular Updates**: Keep tests current with UI changes

## Next Steps

After completing E2E testing:
1. **Phase 4**: Performance testing with load validation
2. **Phase 5**: Production readiness validation
3. **Cloud Deployment**: Deploy integrated system

## Support

For issues with E2E testing:
1. Check test logs and artifacts
2. Verify environment setup
3. Review test configuration
4. Consult Playwright documentation
5. Review test implementation patterns
