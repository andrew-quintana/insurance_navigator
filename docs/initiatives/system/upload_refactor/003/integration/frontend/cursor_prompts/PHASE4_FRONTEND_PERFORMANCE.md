# Phase 4: Frontend Integration Performance Testing & Load Validation - Cursor Implementation Prompt

## Context
You are implementing Phase 4 of comprehensive frontend integration testing. Phases 1-3 should be complete with unit tests, integration tests, and E2E tests all passing. This phase focuses on performance testing covering the complete frontend integration scope.

## Required Reading
**Before starting, review these documentation files:**
1. `docs/initiatives/system/upload_refactor/003/integration/frontend/TESTING_SPEC001.md` - Performance testing scope
2. `docs/initiatives/system/upload_refactor/003/integration/frontend/TODO001.md` - Phase 4 detailed tasks
3. `docs/initiatives/system/upload_refactor/003/integration/frontend/phase3/PHASE3_HANDOFF.md` - Phase 3 completion status
4. Review previous phase deliverables to understand current test infrastructure

## Prerequisites  
- Phase 1 complete: Authentication unit tests (85%+ coverage)
- Phase 2 complete: Authentication integration tests (95%+ pass rate)
- Phase 3 complete: Authentication E2E tests (100% pass rate on critical journeys)
- All authentication flows validated and stable

## Phase 4 Goals (Reference: TODO001.md Phase 4)
1. Implement comprehensive performance metrics collection covering:
   - Authentication performance (PRIORITY #1)
   - Upload component performance with large files
   - Chat interface response times
   - Document state management performance
   - Cross-browser performance validation
   - Responsive design performance across devices
2. Create load testing scenarios with Artillery.js for complete scope
3. Validate performance under concurrent users across all components
4. Establish performance baselines and regression detection
5. Ensure all frontend components meet MVP performance targets

## Implementation Tasks

### Task 4.1: Complete Frontend Performance Metrics Implementation
**Priority**: CRITICAL - Foundation for comprehensive performance monitoring

**Reference**: TODO001.md Section 4.1 for detailed performance metrics requirements across all components

**Files to Create**:

1. **`ui/lib/performance/auth-metrics.ts`**:
```typescript
export interface AuthenticationMetrics {
  loginTime: number;           // Time to complete login
  registrationTime: number;    // Time to complete registration
  sessionValidation: number;   // Token validation timing
  tokenRefreshTime: number;    // Token refresh duration
  logoutTime: number;         // Time to complete logout
  memoryUsage: MemoryInfo;    // Browser memory during auth
  networkRequests: NetworkRequest[]; // Auth-related API calls
}

export class AuthMetricsCollector {
  private startTime: number = 0;
  private metrics: AuthenticationMetrics[] = [];

  startMeasurement(operation: string): void {
    this.startTime = performance.now();
    console.log(`Starting ${operation} measurement`);
  }

  endMeasurement(operation: string): number {
    const duration = performance.now() - this.startTime;
    console.log(`${operation} completed in ${duration}ms`);
    return duration;
  }

  async collectLoginMetrics(email: string, password: string): Promise<AuthMetrics> {
    this.startMeasurement('login');
    
    const memoryBefore = performance.memory ? { ...performance.memory } : null;
    const networkBefore = this.getNetworkRequests();
    
    try {
      // This would integrate with your auth service
      const result = await loginUser(email, password);
      
      const duration = this.endMeasurement('login');
      const memoryAfter = performance.memory ? { ...performance.memory } : null;
      const networkAfter = this.getNetworkRequests();
      
      return {
        operation: 'login',
        duration,
        success: true,
        memoryUsed: memoryAfter ? memoryAfter.usedJSHeapSize - memoryBefore.usedJSHeapSize : 0,
        networkRequests: this.calculateNetworkDelta(networkBefore, networkAfter),
        timestamp: Date.now()
      };
    } catch (error) {
      return {
        operation: 'login',
        duration: this.endMeasurement('login'),
        success: false,
        error: error.message,
        timestamp: Date.now()
      };
    }
  }

  async collectRegistrationMetrics(email: string, password: string): Promise<AuthMetrics> {
    // Similar implementation for registration
  }

  async collectSessionValidationMetrics(): Promise<AuthMetrics> {
    this.startMeasurement('session-validation');
    
    try {
      await validateSession();
      const duration = this.endMeasurement('session-validation');
      
      return {
        operation: 'session-validation',
        duration,
        success: true,
        timestamp: Date.now()
      };
    } catch (error) {
      return {
        operation: 'session-validation', 
        duration: this.endMeasurement('session-validation'),
        success: false,
        error: error.message,
        timestamp: Date.now()
      };
    }
  }

  private getNetworkRequests(): NetworkRequest[] {
    // Collect network performance entries
    return performance.getEntriesByType('navigation') as NetworkRequest[];
  }

  private calculateNetworkDelta(before: NetworkRequest[], after: NetworkRequest[]): NetworkRequest[] {
    return after.slice(before.length);
  }

  exportMetrics(): AuthenticationMetrics[] {
    return [...this.metrics];
  }

  clearMetrics(): void {
    this.metrics = [];
  }
}
```

2. **`ui/lib/performance/frontend-metrics.ts`**:
```typescript
export interface FrontendPerformanceMetrics {
  authenticationTime: number;      // Login/registration response time
  sessionValidation: number;       // Token validation timing  
  uploadInitiation: number;        // Time to start upload (authenticated)
  uploadCompletion: number;        // End-to-end upload time (authenticated)
  chatResponseTime: number;        // Agent response latency (authenticated)
  memoryUsage: MemoryInfo;         // Browser memory consumption
  coreWebVitals: CoreWebVitals;    // LCP, FID, CLS metrics
  networkRequests: NetworkRequest[]; // API call performance
}

export class FrontendMetricsCollector {
  private authMetrics: AuthMetricsCollector;
  
  constructor() {
    this.authMetrics = new AuthMetricsCollector();
  }

  async collectUploadMetrics(file: File): Promise<UploadMetrics> {
    const startTime = performance.now();
    const memoryBefore = performance.memory?.usedJSHeapSize || 0;
    
    try {
      // Monitor authenticated upload
      const result = await uploadDocument(file);
      
      const duration = performance.now() - startTime;
      const memoryAfter = performance.memory?.usedJSHeapSize || 0;
      
      return {
        fileName: file.name,
        fileSize: file.size,
        uploadTime: duration,
        memoryUsed: memoryAfter - memoryBefore,
        success: true,
        timestamp: Date.now()
      };
    } catch (error) {
      return {
        fileName: file.name,
        fileSize: file.size,
        uploadTime: performance.now() - startTime,
        success: false,
        error: error.message,
        timestamp: Date.now()
      };
    }
  }

  async collectChatMetrics(message: string): Promise<ChatMetrics> {
    const startTime = performance.now();
    
    try {
      const response = await sendChatMessage(message);
      const duration = performance.now() - startTime;
      
      return {
        messageLength: message.length,
        responseTime: duration,
        responseLength: response.text.length,
        success: true,
        timestamp: Date.now()
      };
    } catch (error) {
      return {
        messageLength: message.length,
        responseTime: performance.now() - startTime,
        success: false,
        error: error.message,
        timestamp: Date.now()
      };
    }
  }

  collectCoreWebVitals(): Promise<CoreWebVitals> {
    return new Promise((resolve) => {
      // Use web-vitals library or Performance Observer
      const vitals = {
        lcp: 0, // Largest Contentful Paint
        fid: 0, // First Input Delay  
        cls: 0  // Cumulative Layout Shift
      };
      
      // Implement web vitals collection
      resolve(vitals);
    });
  }
}
```

### Task 4.2: Complete Frontend Load Testing Implementation
**Priority**: CRITICAL - Test system under load across all components

**Reference**: TODO001.md Section 4.2 for complete load testing scenarios

**Installation**:
```bash
npm install --save-dev artillery artillery-plugin-metrics-by-endpoint
```

**Files to Create**:

1. **`performance/artillery-auth.yml`**:
```yaml
config:
  target: http://localhost:3000
  phases:
    # Gradual ramp up of authenticated users
    - duration: 60
      arrivalRate: 1
      name: "Auth warmup"
    - duration: 300
      arrivalRate: 2  
      name: "Auth ramp up"
    - duration: 600
      arrivalRate: 5
      name: "Sustained auth load"
    - duration: 120
      arrivalRate: 1
      name: "Auth cool down"

  plugins:
    metrics-by-endpoint:
      useOnlyRequestNames: true

scenarios:
  # User Registration Load Test
  - name: "User Registration Flow"
    weight: 20
    flow:
      - post:
          url: "/api/auth/register"
          json:
            email: "load-test-{{ $randomString() }}@example.com"
            password: "LoadTest123!"
          capture:
            - json: "$.access_token"
              as: "authToken"
            - json: "$.user.id"
              as: "userId"
          expect:
            - statusCode: 200
      - think: 2
      
  # User Login Load Test  
  - name: "User Login Flow"
    weight: 30
    flow:
      # First register
      - post:
          url: "/api/auth/register"
          json:
            email: "login-test-{{ $randomString() }}@example.com"
            password: "LoginTest123!"
          capture:
            - json: "$.user.email"
              as: "userEmail"
      - think: 1
      # Then login
      - post:
          url: "/api/auth/login"
          json:
            email: "{{ userEmail }}"
            password: "LoginTest123!"
          capture:
            - json: "$.access_token"
              as: "authToken"
          expect:
            - statusCode: 200
      - think: 2

  # Authenticated Upload and Chat Flow
  - name: "Authenticated Upload and Chat Flow"  
    weight: 40
    flow:
      # Login first
      - post:
          url: "/api/auth/login"
          json:
            email: "test-user@example.com"
            password: "TestPassword123!"
          capture:
            - json: "$.access_token"
              as: "authToken"
            - json: "$.user.id" 
              as: "userId"
      - think: 1
      
      # Upload document
      - post:
          url: "/api/upload"
          headers:
            Authorization: "Bearer {{ authToken }}"
          formData:
            file: "@./fixtures/sample-policy.pdf"
          capture:
            - json: "$.documentId"
              as: "documentId"
          expect:
            - statusCode: 200
      - think: 3
      
      # Send chat message
      - post:
          url: "/api/chat"
          headers:
            Authorization: "Bearer {{ authToken }}"
          json:
            message: "What is my deductible?"
            conversationId: "load-test-{{ $uuid }}"
            userId: "{{ userId }}"
          expect:
            - statusCode: 200
            - hasProperty: "text"
      - think: 2

  # Session Management Load Test
  - name: "Session Management Flow"
    weight: 10
    flow:
      # Login
      - post:
          url: "/api/auth/login"
          json:
            email: "session-test@example.com"
            password: "SessionTest123!"
          capture:
            - json: "$.access_token"
              as: "authToken"
            - json: "$.refresh_token"
              as: "refreshToken"
      - think: 5
      
      # Validate session
      - get:
          url: "/api/auth/user"
          headers:
            Authorization: "Bearer {{ authToken }}"
          expect:
            - statusCode: 200
      - think: 10
      
      # Refresh token
      - post:
          url: "/api/auth/refresh"
          json:
            refresh_token: "{{ refreshToken }}"
          capture:
            - json: "$.access_token"
              as: "newAuthToken"
          expect:
            - statusCode: 200
      - think: 2
      
      # Use new token
      - get:
          url: "/api/auth/user"
          headers:
            Authorization: "Bearer {{ newAuthToken }}"
          expect:
            - statusCode: 200
```

2. **`performance/artillery-stress-auth.yml`** (Stress Testing):
```yaml
config:
  target: http://localhost:3000
  phases:
    # Stress test with high concurrent auth load
    - duration: 60
      arrivalRate: 10
      name: "Auth stress test"
    - duration: 120  
      arrivalRate: 20
      name: "Peak auth load"

scenarios:
  - name: "Concurrent Authentication Stress"
    weight: 100
    flow:
      # Rapid fire registration and login
      - post:
          url: "/api/auth/register"
          json:
            email: "stress-{{ $randomString() }}-{{ $timestamp }}@example.com"
            password: "StressTest123!"
      - post:
          url: "/api/auth/login"
          json:
            email: "stress-{{ $randomString() }}-{{ $timestamp }}@example.com"  
            password: "StressTest123!"
      # Immediate operations to test session handling
      - get:
          url: "/api/auth/user"
          headers:
            Authorization: "Bearer {{ authToken }}"
```

### Task 4.3: Performance Test Integration
**Priority**: HIGH - Automate performance testing

**Files to Create**:

1. **`performance/run-auth-performance.js`**:
```javascript
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class AuthPerformanceRunner {
  constructor() {
    this.resultsDir = path.join(__dirname, 'results');
    this.ensureResultsDir();
  }

  ensureResultsDir() {
    if (!fs.existsSync(this.resultsDir)) {
      fs.mkdirSync(this.resultsDir, { recursive: true });
    }
  }

  async runAuthLoadTest() {
    console.log('🚀 Starting authentication load test...');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(this.resultsDir, `auth-load-${timestamp}.json`);
    
    try {
      execSync(`artillery run artillery-auth.yml --output ${outputFile}`, {
        cwd: __dirname,
        stdio: 'inherit'
      });
      
      console.log('✅ Authentication load test completed');
      return this.analyzeResults(outputFile);
    } catch (error) {
      console.error('❌ Authentication load test failed:', error.message);
      throw error;
    }
  }

  async runAuthStressTest() {
    console.log('🔥 Starting authentication stress test...');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(this.resultsDir, `auth-stress-${timestamp}.json`);
    
    try {
      execSync(`artillery run artillery-stress-auth.yml --output ${outputFile}`, {
        cwd: __dirname,
        stdio: 'inherit'
      });
      
      console.log('✅ Authentication stress test completed');
      return this.analyzeResults(outputFile);
    } catch (error) {
      console.error('❌ Authentication stress test failed:', error.message);
      throw error;
    }
  }

  analyzeResults(outputFile) {
    const results = JSON.parse(fs.readFileSync(outputFile, 'utf8'));
    
    const analysis = {
      summary: {
        totalRequests: results.aggregate.counters?.['http.requests'] || 0,
        successfulRequests: results.aggregate.counters?.['http.responses'] || 0,
        errorRate: this.calculateErrorRate(results.aggregate),
        averageResponseTime: results.aggregate.summaries?.['http.response_time']?.mean || 0,
        p95ResponseTime: results.aggregate.summaries?.['http.response_time']?.p95 || 0,
        p99ResponseTime: results.aggregate.summaries?.['http.response_time']?.p99 || 0
      },
      authMetrics: {
        loginResponseTime: results.aggregate.summaries?.['http.response_time']?.mean || 0,
        registrationResponseTime: results.aggregate.summaries?.['http.response_time']?.mean || 0,
        sessionValidationTime: results.aggregate.summaries?.['http.response_time']?.mean || 0
      },
      thresholds: this.checkPerformanceThresholds(results.aggregate)
    };

    console.log('\n📊 Performance Analysis:');
    console.log(`Total Requests: ${analysis.summary.totalRequests}`);
    console.log(`Success Rate: ${(100 - analysis.summary.errorRate).toFixed(2)}%`);
    console.log(`Average Response Time: ${analysis.summary.averageResponseTime.toFixed(2)}ms`);
    console.log(`95th Percentile: ${analysis.summary.p95ResponseTime.toFixed(2)}ms`);
    
    // Check if we meet performance targets
    const performanceTargets = {
      authenticationTime: 1000,    // < 1 second
      sessionValidation: 500,      // < 500ms  
      errorRate: 1                 // < 1%
    };

    console.log('\n🎯 Performance Targets:');
    console.log(`Authentication Time: ${analysis.authMetrics.loginResponseTime.toFixed(2)}ms (target: <${performanceTargets.authenticationTime}ms) ${analysis.authMetrics.loginResponseTime < performanceTargets.authenticationTime ? '✅' : '❌'}`);
    console.log(`Session Validation: ${analysis.authMetrics.sessionValidationTime.toFixed(2)}ms (target: <${performanceTargets.sessionValidation}ms) ${analysis.authMetrics.sessionValidationTime < performanceTargets.sessionValidation ? '✅' : '❌'}`);
    console.log(`Error Rate: ${analysis.summary.errorRate.toFixed(2)}% (target: <${performanceTargets.errorRate}%) ${analysis.summary.errorRate < performanceTargets.errorRate ? '✅' : '❌'}`);

    return analysis;
  }

  calculateErrorRate(aggregate) {
    const totalRequests = aggregate.counters?.['http.requests'] || 0;
    const errors = aggregate.counters?.['http.codes.4xx'] + aggregate.counters?.['http.codes.5xx'] || 0;
    return totalRequests > 0 ? (errors / totalRequests) * 100 : 0;
  }

  checkPerformanceThresholds(aggregate) {
    const avgResponseTime = aggregate.summaries?.['http.response_time']?.mean || 0;
    const errorRate = this.calculateErrorRate(aggregate);
    
    return {
      responseTimeOk: avgResponseTime < 1000,  // < 1 second for auth
      errorRateOk: errorRate < 1,              // < 1% error rate
      p95Ok: (aggregate.summaries?.['http.response_time']?.p95 || 0) < 2000  // < 2 seconds p95
    };
  }
}

// Run performance tests
async function main() {
  const runner = new AuthPerformanceRunner();
  
  try {
    await runner.runAuthLoadTest();
    await runner.runAuthStressTest();
  } catch (error) {
    console.error('Performance tests failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = AuthPerformanceRunner;
```

### Task 4.4: Browser Performance Monitoring
**Priority**: MEDIUM - Real-time performance monitoring

**Files to Create**:

1. **`ui/lib/performance/browser-monitor.ts`**:
```typescript
export class BrowserPerformanceMonitor {
  private observer: PerformanceObserver | null = null;
  private metrics: PerformanceEntry[] = [];

  start() {
    if ('PerformanceObserver' in window) {
      this.observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.metrics.push(entry);
          this.analyzeEntry(entry);
        }
      });

      // Monitor different performance metrics
      this.observer.observe({ entryTypes: ['navigation', 'resource', 'measure', 'paint'] });
    }
  }

  stop() {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
  }

  private analyzeEntry(entry: PerformanceEntry) {
    // Log slow authentication operations
    if (entry.name.includes('auth') || entry.name.includes('login')) {
      if (entry.duration > 1000) {
        console.warn(`Slow auth operation: ${entry.name} took ${entry.duration}ms`);
      }
    }

    // Monitor memory usage
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      if (memory.usedJSHeapSize > 50 * 1024 * 1024) { // 50MB
        console.warn(`High memory usage: ${memory.usedJSHeapSize / 1024 / 1024}MB`);
      }
    }
  }

  getMetrics() {
    return {
      navigationMetrics: this.metrics.filter(m => m.entryType === 'navigation'),
      resourceMetrics: this.metrics.filter(m => m.entryType === 'resource'),
      paintMetrics: this.metrics.filter(m => m.entryType === 'paint'),
      measureMetrics: this.metrics.filter(m => m.entryType === 'measure')
    };
  }

  exportMetrics() {
    return JSON.stringify(this.getMetrics(), null, 2);
  }
}
```

## Implementation Guidelines

### Performance Test Execution
```bash
# Run all performance tests
cd performance
node run-auth-performance.js

# Run specific test
artillery run artillery-auth.yml

# Generate HTML report
artillery run artillery-auth.yml --output results.json
artillery report results.json
```

### Memory Leak Detection
```typescript
// Add to your test setup
const startMemory = performance.memory?.usedJSHeapSize || 0;

// After operations
const endMemory = performance.memory?.usedJSHeapSize || 0;
const memoryIncrease = endMemory - startMemory;

if (memoryIncrease > 10 * 1024 * 1024) { // 10MB threshold
  console.warn(`Potential memory leak: ${memoryIncrease / 1024 / 1024}MB increase`);
}
```

### Performance Regression Detection
```javascript
// Compare with baseline metrics
const baseline = require('./baseline-metrics.json');
const current = getCurrentMetrics();

if (current.authResponseTime > baseline.authResponseTime * 1.2) {
  throw new Error(`Performance regression: Auth response time increased by ${((current.authResponseTime / baseline.authResponseTime - 1) * 100).toFixed(1)}%`);
}
```

## Success Criteria (Reference: TODO001.md Phase 4 Acceptance Criteria)
- [ ] Performance metrics collected for all frontend components
- [ ] Authentication performance: response time < 1 second (PRIORITY #1)
- [ ] Upload performance: large files (50MB) handled efficiently
- [ ] Chat performance: response times < 5 seconds under load
- [ ] Document state management: real-time updates < 2 seconds
- [ ] Cross-browser performance validated across Chrome, Firefox, Safari
- [ ] Responsive design performance optimized for mobile, tablet, desktop
- [ ] Load testing supports concurrent users across all features
- [ ] Memory usage stable during extended sessions across all components
- [ ] Error rate < 1% under load for complete frontend scope
- [ ] Performance regression detection working for all components
- [ ] Baseline metrics established for future comparisons

## Performance Targets
```javascript
const PERFORMANCE_TARGETS = {
  authenticationTime: 1000,     // < 1 second
  sessionValidation: 500,       // < 500ms
  tokenRefresh: 1000,          // < 1 second
  uploadInitiation: 2000,      // < 2 seconds (authenticated)
  chatResponseTime: 5000,      // < 5 seconds (authenticated)
  memoryStability: true,       // No leaks during 2-hour sessions
  errorRate: 1,                // < 1% under load
  concurrentUsers: 10          // Support 10 concurrent auth users
};
```

## File Structure Expected
```
performance/
├── artillery-auth.yml
├── artillery-stress-auth.yml
├── run-auth-performance.js
├── fixtures/
│   └── sample-policy.pdf
└── results/
    ├── baseline-metrics.json
    └── [timestamp-results].json

ui/lib/performance/
├── auth-metrics.ts
├── frontend-metrics.ts
└── browser-monitor.ts
```

## Phase 4 Documentation Requirements
**Create these deliverables in `docs/initiatives/system/upload_refactor/003/integration/frontend/phase4/`:**
1. **PHASE4_COMPLETION_SUMMARY.md** - Summary of all performance testing implemented
2. **PHASE4_PERFORMANCE_BASELINE.md** - Performance baselines for all components
3. **PHASE4_LOAD_TEST_RESULTS.md** - Detailed load testing results across all scenarios
4. **PHASE4_PERFORMANCE_OPTIMIZATION.md** - Performance optimization recommendations
5. **PHASE4_DECISIONS.md** - Technical decisions made during performance testing
6. **PHASE4_HANDOFF.md** - Handoff notes for Phase 5 production validation

## Next Phase
After Phase 4 completion with proper documentation, you'll move to Phase 5: Complete Frontend Integration Validation with real backend services covering the complete scope.

Start with Task 4.1 (metrics collection) as it's needed for all other performance testing tasks.