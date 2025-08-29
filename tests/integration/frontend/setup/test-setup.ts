import { beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { TestEnvironment } from './environment';
import { AuthTestHelper } from './auth-helpers';

// Global test environment
let testEnvironment: TestEnvironment;
let globalAuthHelper: AuthTestHelper;

// Global setup - runs once before all tests
beforeAll(async () => {
  console.log('🚀 Setting up global test environment...');
  
  testEnvironment = new TestEnvironment();
  globalAuthHelper = new AuthTestHelper();
  
  try {
    // Start mock services
    await testEnvironment.startMockServices();
    
    // Wait for services to be ready
    await testEnvironment.waitForServicesReady();
    
    console.log('✅ Global test environment ready');
  } catch (error) {
    console.error('❌ Failed to setup global test environment:', error);
    throw error;
  }
}, 120000); // 2 minutes timeout for global setup

// Global teardown - runs once after all tests
afterAll(async () => {
  console.log('🧹 Cleaning up global test environment...');
  
  try {
    await testEnvironment.cleanup();
    console.log('✅ Global test environment cleaned up');
  } catch (error) {
    console.error('❌ Failed to cleanup global test environment:', error);
  }
}, 60000); // 1 minute timeout for global cleanup

// Per-test setup - runs before each test
beforeEach(async () => {
  console.log('🧹 Resetting test data...');
  
  try {
    // Reset test data between tests
    await testEnvironment.resetDatabase();
    await globalAuthHelper.cleanupTestUsers();
    console.log('✅ Test data reset completed');
  } catch (error) {
    console.error('❌ Failed to reset test data:', error);
    // Don't throw error during cleanup to avoid blocking tests
  }
}, 30000); // 30 seconds timeout for test setup

// Per-test teardown - runs after each test
afterEach(async () => {
  // Additional per-test cleanup if needed
  // Most cleanup is handled in beforeEach for the next test
}, 10000); // 10 seconds timeout for test teardown

// Global error handlers
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

// Export global test utilities
export { testEnvironment, globalAuthHelper };

// Global test helpers
export const waitForServiceHealth = async (serviceUrl: string, maxAttempts = 30): Promise<boolean> => {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await fetch(serviceUrl, { timeout: 5000 });
      if (response.ok) {
        return true;
      }
    } catch (error) {
      // Service not ready yet
    }
    
    if (attempt >= maxAttempts) {
      return false;
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  return false;
};

export const createTestFile = (content: string, filename: string, mimeType: string): File => {
  return new File([content], filename, { type: mimeType });
};

export const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Test data utilities
export const generateTestEmail = (prefix: string = 'test'): string => {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}@example.com`;
};

export const generateTestPassword = (): string => {
  return `TestPassword${Math.random().toString(36).substr(2, 8)}!`;
};

// Performance testing utilities
export const measurePerformance = async <T>(
  operation: () => Promise<T>,
  operationName: string = 'Operation'
): Promise<{ result: T; duration: number }> => {
  const startTime = performance.now();
  const result = await operation();
  const endTime = performance.now();
  const duration = endTime - startTime;
  
  console.log(`⏱️  ${operationName} completed in ${duration.toFixed(2)}ms`);
  
  return { result, duration };
};

// Load testing utilities
export const runConcurrentOperations = async <T>(
  operations: (() => Promise<T>)[],
  maxConcurrency: number = 5
): Promise<T[]> => {
  const results: T[] = [];
  const running: Promise<T>[] = [];
  
  for (const operation of operations) {
    if (running.length >= maxConcurrency) {
      // Wait for one operation to complete
      const completed = await Promise.race(running);
      results.push(completed);
      running.splice(running.indexOf(Promise.resolve(completed)), 1);
    }
    
    // Start new operation
    running.push(operation());
  }
  
  // Wait for remaining operations
  const remainingResults = await Promise.all(running);
  results.push(...remainingResults);
  
  return results;
};

// Assertion utilities
export const assertServiceHealthy = async (serviceUrl: string, serviceName: string): Promise<void> => {
  const isHealthy = await waitForServiceHealth(serviceUrl);
  if (!isHealthy) {
    throw new Error(`Service ${serviceName} is not healthy at ${serviceUrl}`);
  }
};

export const assertResponseTime = (actualTime: number, expectedMaxTime: number, operationName: string): void => {
  if (actualTime > expectedMaxTime) {
    throw new Error(
      `${operationName} took ${actualTime.toFixed(2)}ms, expected less than ${expectedMaxTime}ms`
    );
  }
};

// Test environment validation
export const validateTestEnvironment = async (): Promise<void> => {
  const services = [
    { url: 'http://localhost:3001/health', name: 'Auth Service' },
    { url: 'http://localhost:3002/health', name: 'API Service' }
  ];
  
  for (const service of services) {
    await assertServiceHealthy(service.url, service.name);
  }
  
  console.log('✅ Test environment validation passed');
};
