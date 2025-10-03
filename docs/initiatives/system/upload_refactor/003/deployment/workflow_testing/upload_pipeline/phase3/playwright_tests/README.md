# Frontend Upload Pipeline Tests

This directory contains comprehensive Playwright tests for the frontend upload pipeline functionality.

## Overview

These tests automate the complete user journey through the Vercel frontend application, including:
- User registration and authentication
- Document upload through the UI
- Real-time processing monitoring
- Error handling verification
- Mobile responsiveness testing

## Prerequisites

### Required Environment Variables

Create a `.env.production` file in the project root with:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Database Configuration  
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://insurance-navigator-api.onrender.com

# Other API Keys (if needed for testing)
OPENAI_API_KEY=your_openai_api_key_here
LLAMAPARSE_API_KEY=your_llamaparse_api_key_here
```

### Installation

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install
```

## Running Tests

### Quick Start
```bash
# Run all tests
npm run test:playwright

# Run with UI (interactive mode)
npm run test:playwright:ui

# Run in headed mode (see browser)
npm run test:playwright:headed

# Debug mode
npm run test:playwright:debug
```

### Using the Test Runner
```bash
# Run the comprehensive test suite
./tests/playwright/run-tests.sh
```

## Test Structure

### `frontend-upload-test.spec.ts`
Main test file containing:

1. **Complete Upload Workflow Test**
   - User registration
   - User login
   - Document upload
   - Processing verification

2. **Existing User Upload Test**
   - Login with existing user
   - Document upload
   - Processing verification

3. **Error Handling Test**
   - Invalid file type upload
   - Error message verification

4. **Mobile Responsiveness Test**
   - Mobile viewport testing
   - UI element visibility

### `database-monitor.ts`
Helper class for monitoring database operations:
- Upload job status tracking
- Processing completion verification
- Statistics collection

## Test Configuration

### `playwright.config.ts`
- **Base URL**: Vercel production app
- **Browsers**: Chrome, Firefox, Safari, Mobile
- **Retries**: 2 on CI, 0 locally
- **Screenshots**: On failure
- **Videos**: On failure
- **Traces**: On retry

## What Gets Tested

### Frontend Functionality
- ✅ User registration flow
- ✅ User login flow  
- ✅ Document upload UI
- ✅ File validation
- ✅ Success/error messaging
- ✅ Mobile responsiveness

### Backend Integration
- ✅ API endpoint calls
- ✅ Authentication handling
- ✅ File upload processing
- ✅ Database record creation

### End-to-End Workflow
- ✅ Complete user journey
- ✅ Real-time processing
- ✅ Error handling
- ✅ Cross-browser compatibility

## Test Reports

After running tests, reports are generated in:
- **HTML Report**: `test-results/index.html`
- **JSON Report**: `test-results/results.json`
- **JUnit Report**: `test-results/results.xml`

## Troubleshooting

### Common Issues

1. **Environment Variables Missing**
   ```bash
   # Check if .env.production exists
   ls -la .env.production
   ```

2. **Browser Installation**
   ```bash
   # Reinstall browsers
   npx playwright install
   ```

3. **Test Timeouts**
   - Increase timeout in `playwright.config.ts`
   - Check network connectivity
   - Verify Vercel app is accessible

4. **Element Not Found**
   - Check if Vercel app is deployed
   - Verify UI element selectors
   - Run in headed mode to see what's happening

### Debug Mode
```bash
# Run with debug output
npm run test:playwright:debug

# Run specific test
npx playwright test frontend-upload-test.spec.ts --debug
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- Headless mode by default
- Retry failed tests
- Generate multiple report formats
- Cross-browser testing

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Use descriptive test names
3. Include proper error handling
4. Add appropriate timeouts
5. Update this README if needed
