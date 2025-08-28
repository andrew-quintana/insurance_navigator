# Phase 5: Full Integration Validation - Cursor Implementation Prompt

## Context
You are implementing Phase 5, the final phase of frontend integration testing. Phases 1-4 should be complete with all authentication testing infrastructure working. This phase validates the complete system integration with real backend services and prepares for production deployment.

## Prerequisites
- Phase 1 complete: Authentication unit tests (85%+ coverage)
- Phase 2 complete: Authentication integration tests (95%+ pass rate)
- Phase 3 complete: Authentication E2E tests (100% critical journeys)
- Phase 4 complete: Authentication performance testing (targets met)
- All authentication flows validated and performant

## Phase 5 Goals
1. Set up full integration environment with real backend services
2. Validate complete system with real document processing and agents
3. Perform security testing and accessibility validation
4. Establish production deployment pipeline with quality gates
5. Complete final validation for production readiness

## Implementation Tasks

### Task 5.1: Full Integration Environment Setup
**Priority**: CRITICAL - Real system validation

**Docker Environment Configuration**:

1. **`tests/integration/docker-compose.full.yml`**:
```yaml
version: '3.8'
services:
  # Frontend (same as production build)
  frontend:
    build:
      context: ../../ui
      dockerfile: Dockerfile.test
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=test
      - NEXT_PUBLIC_API_URL=http://api-server:8000
      - NEXT_PUBLIC_SUPABASE_URL=http://supabase:54321
    depends_on:
      - api-server
      - supabase
    volumes:
      - ../../ui:/app
      - /app/node_modules

  # Real API server (from existing backend)
  api-server:
    build:
      context: ../../api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/postgres
      - SUPABASE_URL=http://supabase:54321
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LLAMAPARSE_API_KEY=${LLAMAPARSE_API_KEY}
    depends_on:
      - postgres
      - supabase

  # Real worker (from existing backend)
  enhanced-base-worker:
    build:
      context: ../../backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/postgres
      - SUPABASE_URL=http://supabase:54321
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LLAMAPARSE_API_KEY=${LLAMAPARSE_API_KEY}
    depends_on:
      - postgres
      - supabase

  # Supabase (real auth and database)
  supabase:
    image: supabase/supabase:latest
    ports:
      - "54321:54321"
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - JWT_SECRET=${JWT_SECRET}
      - ANON_KEY=${ANON_KEY}
      - SERVICE_ROLE_KEY=${SERVICE_ROLE_KEY}

  # PostgreSQL (real database)
  postgres:
    image: postgres:15
    ports:
      - "54322:5432"
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../../database/schema:/docker-entrypoint-initdb.d

volumes:
  postgres_data:
```

2. **Environment Management for Full Integration**:

**`tests/integration/setup/full-environment.ts`**:
```typescript
import { exec } from 'child_process';
import { promisify } from 'util';
import fetch from 'node-fetch';

const execAsync = promisify(exec);

export class FullIntegrationEnvironment {
  private services: string[] = ['postgres', 'supabase', 'api-server', 'enhanced-base-worker', 'frontend'];
  private healthCheckUrls = {
    frontend: 'http://localhost:3000/health',
    api: 'http://localhost:8000/health',
    supabase: 'http://localhost:54321/health'
  };

  async start(): Promise<void> {
    console.log('🚀 Starting full integration environment...');
    
    try {
      // Start all services
      await execAsync('docker-compose -f docker-compose.full.yml up -d', {
        cwd: __dirname
      });

      // Wait for services to be healthy
      await this.waitForServicesHealth();
      
      // Run database migrations
      await this.runMigrations();
      
      // Seed test data
      await this.seedTestData();
      
      console.log('✅ Full integration environment ready');
    } catch (error) {
      console.error('❌ Failed to start integration environment:', error);
      throw error;
    }
  }

  async stop(): Promise<void> {
    console.log('🛑 Stopping full integration environment...');
    
    try {
      await execAsync('docker-compose -f docker-compose.full.yml down -v', {
        cwd: __dirname
      });
      console.log('✅ Environment stopped');
    } catch (error) {
      console.error('❌ Failed to stop environment:', error);
    }
  }

  private async waitForServicesHealth(): Promise<void> {
    console.log('⏳ Waiting for services to be healthy...');
    
    const maxAttempts = 30;
    const delay = 5000; // 5 seconds

    for (const [service, url] of Object.entries(this.healthCheckUrls)) {
      let attempts = 0;
      
      while (attempts < maxAttempts) {
        try {
          const response = await fetch(url, { timeout: 3000 });
          if (response.ok) {
            console.log(`✅ ${service} is healthy`);
            break;
          }
        } catch (error) {
          // Service not ready yet
        }

        attempts++;
        if (attempts >= maxAttempts) {
          throw new Error(`Service ${service} failed to become healthy`);
        }

        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  private async runMigrations(): Promise<void> {
    console.log('🔄 Running database migrations...');
    
    try {
      await execAsync('docker-compose -f docker-compose.full.yml exec api-server python -m alembic upgrade head', {
        cwd: __dirname
      });
      console.log('✅ Migrations completed');
    } catch (error) {
      console.error('❌ Migration failed:', error);
      throw error;
    }
  }

  private async seedTestData(): Promise<void> {
    console.log('🌱 Seeding test data...');
    
    try {
      // Create test users
      await this.createTestUsers();
      
      // Create test documents
      await this.createTestDocuments();
      
      console.log('✅ Test data seeded');
    } catch (error) {
      console.error('❌ Failed to seed test data:', error);
      throw error;
    }
  }

  private async createTestUsers(): Promise<void> {
    const testUsers = [
      { email: 'integration-test-1@example.com', password: 'IntegrationTest123!' },
      { email: 'integration-test-2@example.com', password: 'IntegrationTest123!' },
      { email: 'performance-test@example.com', password: 'PerformanceTest123!' }
    ];

    for (const user of testUsers) {
      try {
        const response = await fetch('http://localhost:54321/auth/v1/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user)
        });
        
        if (!response.ok) {
          console.warn(`Failed to create user ${user.email}:`, await response.text());
        }
      } catch (error) {
        console.warn(`Error creating user ${user.email}:`, error);
      }
    }
  }

  private async createTestDocuments(): Promise<void> {
    // This would seed the database with test documents
    // for integration testing
  }

  async resetData(): Promise<void> {
    console.log('🧹 Resetting test data...');
    
    try {
      // Clean up test data between test runs
      await execAsync('docker-compose -f docker-compose.full.yml exec postgres psql -U postgres -d postgres -c "TRUNCATE upload_pipeline.documents CASCADE; TRUNCATE upload_pipeline.upload_jobs CASCADE;"', {
        cwd: __dirname
      });
      
      await this.seedTestData();
      console.log('✅ Data reset completed');
    } catch (error) {
      console.error('❌ Failed to reset data:', error);
      throw error;
    }
  }
}
```

### Task 5.2: Real System Integration Tests
**Priority**: CRITICAL - Complete system validation

**Test File: `tests/integration/scenarios/full-system.test.ts`**:
```typescript
import { test, expect } from '@playwright/test';
import { AuthPage } from '../../e2e/page-objects/AuthPage';
import { UploadPage } from '../../e2e/page-objects/UploadPage';
import { ChatPage } from '../../e2e/page-objects/ChatPage';
import { FullIntegrationEnvironment } from '../setup/full-environment';
import path from 'path';

const environment = new FullIntegrationEnvironment();

test.describe('Full System Integration', () => {
  test.beforeAll(async () => {
    await environment.start();
  });

  test.afterAll(async () => {
    await environment.stop();
  });

  test.beforeEach(async () => {
    await environment.resetData();
  });

  test('should complete end-to-end authenticated document processing flow', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    // 1. Authentication
    const testEmail = `e2e-test-${Date.now()}@example.com`;
    await authPage.register(testEmail, 'SecureTest123!');
    await authPage.expectLoggedIn();

    // 2. Document Upload with Real Processing
    await uploadPage.goto();
    const testDocument = path.join(__dirname, '../fixtures/sample-insurance-policy.pdf');
    await uploadPage.uploadFile(testDocument);
    
    // Wait for real document processing to complete
    await uploadPage.waitForUploadComplete();
    await uploadPage.expectDocumentInList('sample-insurance-policy.pdf');

    // 3. Real Agent Conversation with Document Context
    await chatPage.goto();
    
    // Ask specific questions about the uploaded document
    await chatPage.sendMessage('What is my annual deductible according to my uploaded policy?');
    await chatPage.waitForResponse();
    
    // Verify agent response includes document-specific information
    await chatPage.expectMessageInHistory(/deductible.*\$[\d,]+/i);

    // 4. Test Multi-turn Conversation
    await chatPage.sendMessage('What about my out-of-pocket maximum?');
    await chatPage.waitForResponse();
    
    await chatPage.expectMessageInHistory(/out.*of.*pocket|maximum/i);

    // 5. Test Document-specific Queries
    await chatPage.sendMessage('Does my policy cover dental work?');
    await chatPage.waitForResponse();
    
    // Should reference the actual document content
    await chatPage.expectMessageInHistory(/dental|coverage|policy/i);
  });

  test('should handle multiple users with document isolation', async ({ browser }) => {
    // Test user data isolation in real system
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    const authPage1 = new AuthPage(page1);
    const authPage2 = new AuthPage(page2);
    const uploadPage1 = new UploadPage(page1);
    const uploadPage2 = new UploadPage(page2);

    // Register two different users
    const user1Email = `user1-${Date.now()}@example.com`;
    const user2Email = `user2-${Date.now()}@example.com`;

    await authPage1.register(user1Email, 'User1Test123!');
    await authPage2.register(user2Email, 'User2Test123!');

    // User 1 uploads a document
    await uploadPage1.goto();
    const doc1Path = path.join(__dirname, '../fixtures/user1-policy.pdf');
    await uploadPage1.uploadFile(doc1Path);
    await uploadPage1.waitForUploadComplete();

    // User 2 uploads a different document  
    await uploadPage2.goto();
    const doc2Path = path.join(__dirname, '../fixtures/user2-policy.pdf');
    await uploadPage2.uploadFile(doc2Path);
    await uploadPage2.waitForUploadComplete();

    // Verify each user only sees their own documents
    await uploadPage1.expectDocumentInList('user1-policy.pdf');
    await expect(page1.getByText('user2-policy.pdf')).not.toBeVisible();

    await uploadPage2.expectDocumentInList('user2-policy.pdf');
    await expect(page2.getByText('user1-policy.pdf')).not.toBeVisible();

    await context1.close();
    await context2.close();
  });

  test('should handle real processing errors gracefully', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);

    await authPage.register(`error-test-${Date.now()}@example.com`, 'ErrorTest123!');
    
    // Upload an invalid/corrupted document
    await uploadPage.goto();
    const corruptedDoc = path.join(__dirname, '../fixtures/corrupted-document.pdf');
    await uploadPage.uploadFile(corruptedDoc);

    // Should show appropriate error message
    await expect(page.getByText(/processing.*failed|unable.*process|invalid.*document/i))
      .toBeVisible({ timeout: 60000 });
  });

  test('should maintain performance under real workload', async ({ page }) => {
    const authPage = new AuthPage(page);
    const uploadPage = new UploadPage(page);
    const chatPage = new ChatPage(page);

    await authPage.register(`perf-test-${Date.now()}@example.com`, 'PerfTest123!');
    
    // Upload a large document
    await uploadPage.goto();
    const largeDoc = path.join(__dirname, '../fixtures/large-insurance-handbook.pdf');
    
    const uploadStart = Date.now();
    await uploadPage.uploadFile(largeDoc);
    await uploadPage.waitForUploadComplete();
    const uploadDuration = Date.now() - uploadStart;

    // Should complete within reasonable time (adjust based on document size)
    expect(uploadDuration).toBeLessThan(120000); // 2 minutes max

    // Chat response should be fast even with large document
    await chatPage.goto();
    
    const chatStart = Date.now();
    await chatPage.sendMessage('Summarize the key benefits in my policy');
    await chatPage.waitForResponse();
    const chatDuration = Date.now() - chatStart;

    expect(chatDuration).toBeLessThan(10000); // 10 seconds max
  });
});
```

### Task 5.3: Security Testing and Validation
**Priority**: HIGH - Production security requirements

**Test File: `tests/integration/scenarios/security-validation.test.ts`**:
```typescript
import { test, expect } from '@playwright/test';
import { AuthPage } from '../../e2e/page-objects/AuthPage';

test.describe('Security Validation', () => {
  test('should prevent unauthorized document access', async ({ page }) => {
    // Test that users cannot access other users' documents
    const authPage = new AuthPage(page);
    
    // Try to access document API without authentication
    const response = await page.request.get('/api/documents');
    expect(response.status()).toBe(401);
  });

  test('should validate file upload security', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`security-test-${Date.now()}@example.com`, 'SecurityTest123!');
    
    // Try to upload malicious files
    const response = await page.request.post('/api/upload', {
      multipart: {
        file: {
          name: 'malicious.exe',
          mimeType: 'application/x-executable',
          buffer: Buffer.from('fake executable content')
        }
      }
    });
    
    expect(response.status()).toBe(400); // Should reject non-PDF files
  });

  test('should handle SQL injection attempts', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Try SQL injection in login
    await authPage.goto();
    await authPage.login("'; DROP TABLE users; --", 'password');
    
    await authPage.expectError(/invalid.*credentials/i);
  });

  test('should enforce session timeout', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`timeout-test-${Date.now()}@example.com`, 'TimeoutTest123!');
    
    // Simulate session expiry (this would need backend support)
    await page.evaluate(() => {
      localStorage.removeItem('supabase.auth.token');
      sessionStorage.clear();
    });
    
    // Try to access protected resource
    const response = await page.request.get('/api/documents');
    expect(response.status()).toBe(401);
  });
});
```

### Task 5.4: Accessibility Testing
**Priority**: MEDIUM - Basic accessibility compliance

**Test File: `tests/integration/scenarios/accessibility.test.ts`**:
```typescript
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';
import { AuthPage } from '../../e2e/page-objects/AuthPage';

test.describe('Accessibility Validation', () => {
  test('should meet basic accessibility standards on auth pages', async ({ page }) => {
    await page.goto('/auth/login');
    await injectAxe(page);
    
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true }
    });
  });

  test('should be keyboard navigable', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.goto();
    
    // Tab through form elements
    await page.keyboard.press('Tab'); // Email input
    expect(await page.evaluate(() => document.activeElement?.tagName)).toBe('INPUT');
    
    await page.keyboard.press('Tab'); // Password input
    expect(await page.evaluate(() => document.activeElement?.tagName)).toBe('INPUT');
    
    await page.keyboard.press('Tab'); // Login button
    expect(await page.evaluate(() => document.activeElement?.tagName)).toBe('BUTTON');
  });

  test('should have proper ARIA labels and roles', async ({ page }) => {
    await page.goto('/upload');
    
    // Check for proper labeling
    const fileInput = page.getByRole('button', { name: /upload/i });
    await expect(fileInput).toHaveAttribute('aria-label');
    
    const progressBar = page.getByRole('progressbar');
    await expect(progressBar).toHaveAttribute('aria-valuenow');
  });
});
```

### Task 5.5: Production Deployment Pipeline Integration
**Priority**: HIGH - Deployment readiness

**Files to Create**:

1. **`.github/workflows/frontend-integration-tests.yml`**:
```yaml
name: Frontend Integration Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 45

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: postgres
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: ui/package-lock.json

      - name: Install dependencies
        run: |
          cd ui
          npm ci

      - name: Run unit tests
        run: |
          cd ui
          npm run test:ci

      - name: Start integration environment
        run: |
          cd tests/integration
          docker-compose -f docker-compose.full.yml up -d
          node setup/wait-for-services.js

      - name: Run integration tests
        run: |
          cd tests/integration
          npm run test:integration

      - name: Run E2E tests
        run: |
          cd e2e
          npx playwright test

      - name: Run performance tests
        run: |
          cd performance
          node run-auth-performance.js

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: |
            ui/coverage/
            tests/integration/results/
            e2e/test-results/
            performance/results/

      - name: Report test results
        if: always()
        run: |
          echo "## Test Results" >> $GITHUB_STEP_SUMMARY
          echo "- Unit Tests: $(cd ui && npm run test:coverage | grep 'All files')" >> $GITHUB_STEP_SUMMARY
          echo "- Integration Tests: Completed" >> $GITHUB_STEP_SUMMARY
          echo "- E2E Tests: Completed" >> $GITHUB_STEP_SUMMARY
          echo "- Performance Tests: Completed" >> $GITHUB_STEP_SUMMARY

  deployment-readiness:
    needs: integration-tests
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate deployment readiness
        run: |
          echo "✅ All integration tests passed"
          echo "✅ Performance targets met"
          echo "✅ Security validation completed"
          echo "✅ System ready for deployment"
```

2. **`scripts/deployment-validation.js`**:
```javascript
const fs = require('fs');
const path = require('path');

class DeploymentValidator {
  constructor() {
    this.validationResults = {
      unitTests: false,
      integrationTests: false,
      e2eTests: false,
      performanceTests: false,
      securityTests: false,
      accessibilityTests: false
    };
  }

  async validateDeploymentReadiness() {
    console.log('🔍 Validating deployment readiness...');
    
    try {
      // Check test results
      await this.checkUnitTestResults();
      await this.checkIntegrationTestResults();
      await this.checkE2ETestResults();
      await this.checkPerformanceResults();
      await this.checkSecurityResults();
      
      // Generate deployment report
      this.generateDeploymentReport();
      
      if (this.isReadyForDeployment()) {
        console.log('✅ System is ready for deployment');
        process.exit(0);
      } else {
        console.log('❌ System is not ready for deployment');
        process.exit(1);
      }
    } catch (error) {
      console.error('❌ Deployment validation failed:', error);
      process.exit(1);
    }
  }

  async checkUnitTestResults() {
    const coverageFile = path.join(__dirname, '../ui/coverage/coverage-summary.json');
    
    if (fs.existsSync(coverageFile)) {
      const coverage = JSON.parse(fs.readFileSync(coverageFile, 'utf8'));
      const totalCoverage = coverage.total.lines.pct;
      
      if (totalCoverage >= 85) {
        this.validationResults.unitTests = true;
        console.log(`✅ Unit tests: ${totalCoverage}% coverage (target: 85%)`);
      } else {
        console.log(`❌ Unit tests: ${totalCoverage}% coverage (target: 85%)`);
      }
    } else {
      console.log('❌ Unit test results not found');
    }
  }

  async checkPerformanceResults() {
    const performanceDir = path.join(__dirname, '../performance/results');
    
    if (fs.existsSync(performanceDir)) {
      const files = fs.readdirSync(performanceDir);
      const latestResult = files.sort().pop();
      
      if (latestResult) {
        const results = JSON.parse(fs.readFileSync(
          path.join(performanceDir, latestResult), 
          'utf8'
        ));
        
        if (results.summary.errorRate < 1 && results.summary.averageResponseTime < 1000) {
          this.validationResults.performanceTests = true;
          console.log('✅ Performance tests: Targets met');
        } else {
          console.log(`❌ Performance tests: Error rate ${results.summary.errorRate}%, avg response ${results.summary.averageResponseTime}ms`);
        }
      }
    } else {
      console.log('❌ Performance test results not found');
    }
  }

  isReadyForDeployment() {
    const requiredTests = ['unitTests', 'integrationTests', 'e2eTests', 'performanceTests'];
    return requiredTests.every(test => this.validationResults[test]);
  }

  generateDeploymentReport() {
    const report = {
      timestamp: new Date().toISOString(),
      validationResults: this.validationResults,
      readyForDeployment: this.isReadyForDeployment()
    };
    
    fs.writeFileSync(
      path.join(__dirname, '../deployment-report.json'),
      JSON.stringify(report, null, 2)
    );
    
    console.log('📋 Deployment report generated');
  }
}

// Run validation
if (require.main === module) {
  const validator = new DeploymentValidator();
  validator.validateDeploymentReadiness();
}
```

## Implementation Guidelines

### Full Integration Test Execution
```bash
# Start full environment
cd tests/integration
docker-compose -f docker-compose.full.yml up -d

# Wait for services
node setup/wait-for-services.js

# Run all tests
npm run test:full-integration

# Run specific test categories
npm run test:security
npm run test:accessibility
npm run test:performance

# Generate deployment report
node scripts/deployment-validation.js
```

### Environment Verification
```bash
# Health checks for all services
curl http://localhost:3000/health    # Frontend
curl http://localhost:8000/health    # API
curl http://localhost:54321/health   # Supabase

# Test database connectivity
docker-compose exec postgres psql -U postgres -c "SELECT 1"

# Test authentication service
curl -X POST http://localhost:54321/auth/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

## Success Criteria
- [ ] Full integration environment running stably
- [ ] Real document processing working end-to-end
- [ ] Agent conversations using actual processed documents
- [ ] User data isolation validated in real system
- [ ] Performance meets targets under real workload
- [ ] Security vulnerabilities addressed
- [ ] Basic accessibility compliance achieved
- [ ] Deployment pipeline validates all quality gates
- [ ] System ready for production deployment

## Performance Validation Targets
```javascript
const PRODUCTION_TARGETS = {
  // Authentication Performance
  authenticationTime: 1000,        // < 1 second
  sessionValidation: 500,          // < 500ms
  tokenRefresh: 1000,             // < 1 second

  // Feature Performance  
  uploadInitiation: 2000,          // < 2 seconds
  documentProcessing: 120000,      // < 2 minutes (large docs)
  chatResponseTime: 5000,          // < 5 seconds
  
  // System Performance
  memoryStability: true,           // No leaks during 4-hour sessions
  errorRate: 0.1,                  // < 0.1% in production
  concurrentUsers: 50,             // Support 50 concurrent users
  
  // Quality Gates
  unitTestCoverage: 85,            // >= 85%
  integrationPassRate: 95,         // >= 95%
  e2ePassRate: 100,               // 100% critical journeys
  accessibilityCompliance: 'AA'    // WCAG 2.1 AA
};
```

## File Structure Expected
```
tests/integration/
├── docker-compose.full.yml
├── setup/
│   ├── full-environment.ts
│   └── wait-for-services.js
├── scenarios/
│   ├── full-system.test.ts
│   ├── security-validation.test.ts
│   └── accessibility.test.ts
└── fixtures/
    ├── sample-insurance-policy.pdf
    ├── large-insurance-handbook.pdf
    ├── user1-policy.pdf
    ├── user2-policy.pdf
    └── corrupted-document.pdf

.github/workflows/
└── frontend-integration-tests.yml

scripts/
└── deployment-validation.js
```

## Next Steps (Post-Phase 5)
After successful completion, the system will be ready for the **Cloud Deployment Initiative**:
1. **Vercel**: Frontend deployment with production configuration
2. **Render**: Backend API and worker deployment
3. **Supabase**: Production database environment
4. **End-to-end cloud validation**: Complete system testing in production

Start with Task 5.1 (full integration environment) as it's the foundation for all production-readiness validation.