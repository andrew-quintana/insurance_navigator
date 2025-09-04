import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AuthTestHelper } from '../setup/auth-helpers';
import { TestEnvironment } from '../setup/environment';

describe('Authentication Integration Tests', () => {
  let authHelper: AuthTestHelper;
  let testEnvironment: TestEnvironment;

  beforeEach(async () => {
    authHelper = new AuthTestHelper();
    testEnvironment = new TestEnvironment();
    
    // Ensure services are ready
    await testEnvironment.waitForServicesReady();
  });

  afterEach(async () => {
    // Clean up test data between tests
    await authHelper.cleanupTestUsers();
  });

  describe('User Registration Integration', () => {
    it('should register new user with email validation', async () => {
      const testEmail = `test-${Date.now()}@example.com`;
      const testPassword = 'SecurePassword123!';
      
      const result = await authHelper.createTestUser(testEmail, testPassword);
      
      expect(result.user.email).toBe(testEmail);
      expect(result.user.id).toBeDefined();
      expect(result.session.access_token).toBeDefined();
      expect(result.session.refresh_token).toBeDefined();
      expect(result.session.user_id).toBe(result.user.id);
    });

    it('should handle duplicate email registration', async () => {
      const testEmail = `duplicate-${Date.now()}@example.com`;
      const testPassword = 'DuplicateTest123!';
      
      // Create first user
      await authHelper.createTestUser(testEmail, testPassword);
      
      // Try to create second user with same email
      await expect(
        authHelper.createTestUser(testEmail, 'DifferentPassword123!')
      ).rejects.toThrow(/email already registered/i);
    });

    it('should validate required fields', async () => {
      // Test missing email
      await expect(
        fetch('http://localhost:3001/auth/v1/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password: 'TestPassword123!' })
        })
      ).resolves.toMatchObject({
        status: 400
      });

      // Test missing password
      await expect(
        fetch('http://localhost:3001/auth/v1/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: 'test@example.com' })
        })
      ).resolves.toMatchObject({
        status: 400
      });
    });

    it('should generate unique user IDs for different users', async () => {
      const user1 = await authHelper.createTestUser(`user1-${Date.now()}@example.com`, 'Password123!');
      const user2 = await authHelper.createTestUser(`user2-${Date.now()}@example.com`, 'Password123!');
      
      expect(user1.user.id).not.toBe(user2.user.id);
      expect(user1.user.id).toMatch(/^user_\d+_[a-z0-9]+$/);
      expect(user2.user.id).toMatch(/^user_\d+_[a-z0-9]+$/);
    });
  });

  describe('User Login Integration', () => {
    it('should login with valid credentials', async () => {
      const testEmail = `login-test-${Date.now()}@example.com`;
      const testPassword = 'LoginTest123!';
      
      // First create a user
      await authHelper.createTestUser(testEmail, testPassword);
      
      // Then login
      const session = await authHelper.loginUser(testEmail, testPassword);
      
      expect(session.access_token).toBeDefined();
      expect(session.refresh_token).toBeDefined();
      expect(session.user_id).toBeDefined();
      expect(session.expires_at).toBeDefined();
    });

    it('should reject invalid credentials', async () => {
      const testEmail = `invalid-cred-${Date.now()}@example.com`;
      const testPassword = 'ValidPassword123!';
      
      // Create user
      await authHelper.createTestUser(testEmail, testPassword);
      
      // Try to login with wrong password
      await expect(
        authHelper.loginUser(testEmail, 'WrongPassword123!')
      ).rejects.toThrow(/invalid.*credentials/i);
      
      // Try to login with non-existent email
      await expect(
        authHelper.loginUser('nonexistent@example.com', testPassword)
      ).rejects.toThrow(/invalid.*credentials/i);
    });

    it('should handle login with non-existent user', async () => {
      await expect(
        authHelper.loginUser('nonexistent@example.com', 'AnyPassword123!')
      ).rejects.toThrow(/invalid.*credentials/i);
    });
  });

  describe('Session Management Integration', () => {
    it('should validate session with valid token', async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      
      const validatedUser = await authHelper.validateSession(session.access_token);
      
      expect(validatedUser.id).toBe(user.id);
      expect(validatedUser.email).toBe(user.email);
    });

    it('should reject invalid tokens', async () => {
      await expect(
        authHelper.validateSession('invalid-token')
      ).rejects.toThrow(/invalid.*token|unauthorized/i);
    });

    it('should refresh expired tokens', async () => {
      const { session } = await authHelper.setupAuthenticatedSession();
      
      // Mock session expiry (this would need backend support)
      await authHelper.mockSessionExpiry();
      
      // Try to refresh token
      const refreshed = await authHelper.refreshUserToken(session.refresh_token);
      
      expect(refreshed.access_token).toBeDefined();
      expect(refreshed.refresh_token).toBeDefined();
      expect(refreshed.user_id).toBe(session.user_id);
    });

    it('should handle invalid refresh tokens', async () => {
      await expect(
        authHelper.refreshUserToken('invalid-refresh-token')
      ).rejects.toThrow(/invalid.*refresh.*token|unauthorized/i);
    });

    it('should maintain user context across token refresh', async () => {
      const { user, session } = await authHelper.setupAuthenticatedSession();
      
      const refreshed = await authHelper.refreshUserToken(session.refresh_token);
      
      // Validate new token works
      const validatedUser = await authHelper.validateSession(refreshed.access_token);
      expect(validatedUser.id).toBe(user.id);
      expect(validatedUser.email).toBe(user.email);
    });
  });

  describe('Logout Integration', () => {
    it('should successfully logout user', async () => {
      const { session } = await authHelper.setupAuthenticatedSession();
      
      await authHelper.logoutUser(session.access_token);
      
      // Verify token is no longer valid
      await expect(
        authHelper.validateSession(session.access_token)
      ).rejects.toThrow(/invalid.*token|unauthorized/i);
    });

    it('should handle logout with invalid token', async () => {
      await expect(
        authHelper.logoutUser('invalid-token')
      ).rejects.toThrow(/invalid.*token|unauthorized/i);
    });
  });

  describe('Authentication Service Health', () => {
    it('should respond to health checks', async () => {
      const isHealthy = await authHelper.testServiceHealth();
      expect(isHealthy).toBe(true);
    });

    it('should provide service information', async () => {
      const response = await fetch('http://localhost:3001/health');
      const healthData = await response.json();
      
      expect(healthData.status).toBe('healthy');
      expect(healthData.service).toBe('mock-auth-service');
    });
  });

  describe('Test Data Management', () => {
    it('should list test users', async () => {
      // Create some test users
      await authHelper.createTestUser(`list-test-1-${Date.now()}@example.com`, 'Password123!');
      await authHelper.createTestUser(`list-test-2-${Date.now()}@example.com`, 'Password123!');
      
      const users = await authHelper.getTestUsers();
      expect(users.length).toBeGreaterThanOrEqual(2);
      
      // Verify user structure
      users.forEach(user => {
        expect(user.id).toBeDefined();
        expect(user.email).toBeDefined();
        expect(user.created_at).toBeDefined();
      });
    });

    it('should clear test users', async () => {
      // Create a test user
      await authHelper.createTestUser(`clear-test-${Date.now()}@example.com`, 'Password123!');
      
      // Clear all test users
      await authHelper.cleanupTestUsers();
      
      // Verify users are cleared
      const users = await authHelper.getTestUsers();
      expect(users.length).toBe(0);
    });
  });

  describe('Load Testing Preparation', () => {
    it('should create multiple test users for load testing', async () => {
      const userCount = 5;
      const users = await authHelper.createMultipleTestUsers(userCount, 'load-test');
      
      expect(users.length).toBe(userCount);
      
      // Verify each user has valid structure
      users.forEach(user => {
        expect(user.user.id).toBeDefined();
        expect(user.user.email).toBeDefined();
        expect(user.session.access_token).toBeDefined();
        expect(user.session.refresh_token).toBeDefined();
      });
    });

    it('should handle concurrent user creation', async () => {
      const promises = [];
      const userCount = 10;
      
      for (let i = 0; i < userCount; i++) {
        const email = `concurrent-${i}-${Date.now()}@example.com`;
        const password = 'ConcurrentTest123!';
        promises.push(authHelper.createTestUser(email, password));
      }
      
      const results = await Promise.allSettled(promises);
      const successful = results.filter(r => r.status === 'fulfilled');
      
      expect(successful.length).toBe(userCount);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      // Test with invalid service URL
      const invalidAuthHelper = new AuthTestHelper('http://localhost:9999');
      
      await expect(
        invalidAuthHelper.createTestUser('test@example.com', 'password')
      ).rejects.toThrow();
    });

    it('should handle malformed requests', async () => {
      // Test with malformed JSON
      const response = await fetch('http://localhost:3001/auth/v1/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: 'invalid json'
      });
      
      expect(response.status).toBe(400);
    });

    it('should handle missing authorization headers', async () => {
      const { session } = await authHelper.setupAuthenticatedSession();
      
      // Try to validate session without auth header
      const response = await fetch('http://localhost:3001/auth/v1/user');
      
      expect(response.status).toBe(401);
    });
  });
});
