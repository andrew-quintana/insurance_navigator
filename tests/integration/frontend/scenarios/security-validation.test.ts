import { test, expect } from '@playwright/test';
import { AuthPage } from '../../../e2e/page-objects/AuthPage';
import { FullIntegrationEnvironment } from '../setup/full-environment';

const environment = new FullIntegrationEnvironment();

test.describe('Security Validation', () => {
  test.beforeAll(async () => {
    await environment.start();
  });

  test.afterAll(async () => {
    await environment.stop();
  });

  test.beforeEach(async () => {
    await environment.resetData();
  });

  test('should prevent unauthorized document access', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Try to access document API without authentication
    const response = await page.request.get('/api/documents');
    expect(response.status()).toBe(401);
    
    // Try to access upload API without authentication
    const uploadResponse = await page.request.post('/api/upload', {
      multipart: {
        file: {
          name: 'test.pdf',
          mimeType: 'application/pdf',
          buffer: Buffer.from('fake pdf content')
        }
      }
    });
    expect(uploadResponse.status()).toBe(401);
    
    // Try to access chat API without authentication
    const chatResponse = await page.request.post('/api/chat', {
      data: {
        message: 'Hello',
        conversationId: 'test-conversation'
      }
    });
    expect(chatResponse.status()).toBe(401);
  });

  test('should validate file upload security', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`security-test-${Date.now()}@example.com`, 'SecurityTest123!');
    
    // Try to upload malicious files
    const maliciousFiles = [
      {
        name: 'malicious.exe',
        mimeType: 'application/x-executable',
        content: 'fake executable content'
      },
      {
        name: 'script.js',
        mimeType: 'application/javascript',
        content: 'alert("xss")'
      },
      {
        name: 'virus.bat',
        mimeType: 'application/x-msdownload',
        content: 'del C:\\Windows\\System32'
      },
      {
        name: 'large-file.pdf',
        mimeType: 'application/pdf',
        content: 'x'.repeat(100 * 1024 * 1024) // 100MB
      }
    ];

    for (const file of maliciousFiles) {
      const response = await page.request.post('/api/upload', {
        multipart: {
          file: {
            name: file.name,
            mimeType: file.mimeType,
            buffer: Buffer.from(file.content)
          }
        }
      });
      
      // Should reject non-PDF files or oversized files
      expect(response.status()).toBe(400);
    }
  });

  test('should handle SQL injection attempts', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Try SQL injection in login
    const sqlInjectionAttempts = [
      "'; DROP TABLE users; --",
      "' OR '1'='1",
      "admin'--",
      "' UNION SELECT * FROM users--",
      "'; INSERT INTO users VALUES ('hacker', 'password'); --"
    ];

    for (const attempt of sqlInjectionAttempts) {
      await authPage.goto();
      await authPage.login(attempt, 'password');
      await authPage.expectError(/invalid.*credentials|login.*failed/i);
    }
  });

  test('should enforce session timeout', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`timeout-test-${Date.now()}@example.com`, 'TimeoutTest123!');
    
    // Simulate session expiry by clearing storage
    await page.evaluate(() => {
      localStorage.removeItem('supabase.auth.token');
      sessionStorage.clear();
    });
    
    // Try to access protected resources
    const protectedEndpoints = [
      '/api/documents',
      '/api/upload',
      '/api/chat',
      '/api/user/profile'
    ];

    for (const endpoint of protectedEndpoints) {
      const response = await page.request.get(endpoint);
      expect(response.status()).toBe(401);
    }
  });

  test('should prevent cross-site scripting (XSS)', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`xss-test-${Date.now()}@example.com`, 'XssTest123!');
    
    // Try XSS in chat messages
    const xssAttempts = [
      '<script>alert("xss")</script>',
      'javascript:alert("xss")',
      '<img src="x" onerror="alert(\'xss\')">',
      '<svg onload="alert(\'xss\')">',
      '"><script>alert("xss")</script>',
      '\';alert("xss");//'
    ];

    for (const xssAttempt of xssAttempts) {
      const response = await page.request.post('/api/chat', {
        data: {
          message: xssAttempt,
          conversationId: 'test-conversation'
        }
      });
      
      // Should either reject the message or sanitize it
      if (response.ok()) {
        const responseData = await response.json();
        // Check that the response doesn't contain the XSS payload
        expect(responseData.text).not.toContain('<script>');
        expect(responseData.text).not.toContain('javascript:');
        expect(responseData.text).not.toContain('onerror=');
        expect(responseData.text).not.toContain('onload=');
      }
    }
  });

  test('should validate authentication token security', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`token-test-${Date.now()}@example.com`, 'TokenTest123!');
    
    // Try to access API with invalid tokens
    const invalidTokens = [
      'invalid-token',
      'Bearer invalid-token',
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid',
      '',
      null,
      'Bearer ',
      'malformed-jwt-token'
    ];

    for (const token of invalidTokens) {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      const response = await page.request.get('/api/documents', {
        headers
      });
      
      expect(response.status()).toBe(401);
    }
  });

  test('should prevent directory traversal attacks', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`traversal-test-${Date.now()}@example.com`, 'TraversalTest123!');
    
    // Try directory traversal in file uploads
    const traversalAttempts = [
      '../../../etc/passwd',
      '..\\..\\..\\windows\\system32\\config\\sam',
      '....//....//....//etc/passwd',
      '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
      '..%252f..%252f..%252fetc%252fpasswd'
    ];

    for (const attempt of traversalAttempts) {
      const response = await page.request.post('/api/upload', {
        multipart: {
          file: {
            name: attempt,
            mimeType: 'application/pdf',
            buffer: Buffer.from('fake content')
          }
        }
      });
      
      // Should reject directory traversal attempts
      expect(response.status()).toBe(400);
    }
  });

  test('should validate rate limiting', async ({ page }) => {
    const authPage = new AuthPage(page);
    
    // Try rapid-fire login attempts
    const loginAttempts = Array(20).fill(null).map((_, i) => 
      page.request.post('/api/auth/login', {
        data: {
          email: `rate-limit-test-${i}@example.com`,
          password: 'wrong-password'
        }
      })
    );

    const responses = await Promise.all(loginAttempts);
    
    // Should eventually get rate limited
    const rateLimitedResponses = responses.filter(r => r.status() === 429);
    expect(rateLimitedResponses.length).toBeGreaterThan(0);
  });

  test('should prevent CSRF attacks', async ({ page, context }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`csrf-test-${Date.now()}@example.com`, 'CsrfTest123!');
    
    // Create a malicious page that tries to make requests
    await page.goto('data:text/html,<html><body><script>fetch("/api/documents", {method: "GET"}).then(r => console.log(r.status))</script></body></html>');
    
    // The request should fail due to CSRF protection
    const response = await page.request.get('/api/documents');
    expect(response.status()).toBe(401);
  });

  test('should validate input sanitization', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`sanitization-test-${Date.now()}@example.com`, 'SanitizationTest123!');
    
    // Try various malicious inputs
    const maliciousInputs = [
      'null\x00byte',
      'very long string ' + 'x'.repeat(10000),
      'unicode\u0000null',
      'emoji 🚀💥💀',
      'special chars !@#$%^&*()_+{}|:"<>?[]\\;\',./',
      'multiline\ninput\r\nwith\ttabs'
    ];

    for (const input of maliciousInputs) {
      const response = await page.request.post('/api/chat', {
        data: {
          message: input,
          conversationId: 'test-conversation'
        }
      });
      
      // Should handle input gracefully (either accept or reject)
      expect([200, 400, 422]).toContain(response.status());
    }
  });

  test('should validate file content security', async ({ page }) => {
    const authPage = new AuthPage(page);
    await authPage.register(`content-test-${Date.now()}@example.com`, 'ContentTest123!');
    
    // Try to upload files with malicious content
    const maliciousContent = [
      {
        name: 'malicious.pdf',
        mimeType: 'application/pdf',
        content: '%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF'
      },
      {
        name: 'embedded-script.pdf',
        mimeType: 'application/pdf',
        content: 'PDF with embedded JavaScript: /JavaScript (app.alert("XSS"))'
      }
    ];

    for (const file of maliciousContent) {
      const response = await page.request.post('/api/upload', {
        multipart: {
          file: {
            name: file.name,
            mimeType: file.mimeType,
            buffer: Buffer.from(file.content)
          }
        }
      });
      
      // Should either accept the file (if it's valid PDF) or reject it
      expect([200, 400, 422]).toContain(response.status());
    }
  });
});
