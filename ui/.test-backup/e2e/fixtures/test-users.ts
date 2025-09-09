import { TestUser } from '../utils/auth-helpers';

export const createTestUser = (): TestUser => ({
  email: `test-${Date.now()}-${Math.random().toString(36).substring(2, 8)}@example.com`,
  password: 'SecureTestPassword123!'
});

export const createTestUserWithPrefix = (prefix: string): TestUser => ({
  email: `${prefix}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}@example.com`,
  password: 'SecureTestPassword123!'
});

export const createTestUserForBrowser = (browserName: string): TestUser => ({
  email: `test-${browserName}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}@example.com`,
  password: 'SecureTestPassword123!'
});

export const createTestUserForDevice = (deviceType: string): TestUser => ({
  email: `test-${deviceType}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}@example.com`,
  password: 'SecureTestPassword123!'
});

export const createTestUserForPerformance = (): TestUser => ({
  email: `perf-test-${Date.now()}-${Math.random().toString(36).substring(2, 8)}@example.com`,
  password: 'SecureTestPassword123!'
});

export const createTestUserForLoad = (index: number): TestUser => ({
  email: `load-test-${index}-${Date.now()}@example.com`,
  password: 'SecureTestPassword123!'
});

// Predefined test users for specific scenarios
export const TEST_USERS = {
  standard: {
    email: 'standard-test@example.com',
    password: 'SecureTestPassword123!'
  },
  performance: {
    email: 'performance-test@example.com',
    password: 'SecureTestPassword123!'
  },
  load: {
    email: 'load-test@example.com',
    password: 'SecureTestPassword123!'
  },
  mobile: {
    email: 'mobile-test@example.com',
    password: 'SecureTestPassword123!'
  },
  tablet: {
    email: 'tablet-test@example.com',
    password: 'SecureTestPassword123!'
  }
};

// Test user credentials for different browsers
export const BROWSER_TEST_USERS = {
  chrome: createTestUserForBrowser('chrome'),
  firefox: createTestUserForBrowser('firefox'),
  safari: createTestUserForBrowser('safari')
};

// Test user credentials for different devices
export const DEVICE_TEST_USERS = {
  mobile: createTestUserForDevice('mobile'),
  tablet: createTestUserForDevice('tablet'),
  desktop: createTestUserForDevice('desktop')
};
