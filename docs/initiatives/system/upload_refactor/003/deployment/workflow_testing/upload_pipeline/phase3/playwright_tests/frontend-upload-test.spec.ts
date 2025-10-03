import { test, expect, Page } from '@playwright/test';
import { promises as fs } from 'fs';
import path from 'path';

// Test configuration
const TEST_CONFIG = {
  frontendUrl: 'https://insurancenavigator.vercel.app',
  apiBaseUrl: 'https://insurance-navigator-api.onrender.com',
  testUser: {
    email: `frontend_test_${Date.now()}@example.com`,
    password: 'test_password_123',
    name: `Frontend Test User ${Date.now()}`
  },
  testFile: {
    name: 'frontend_test_document.pdf',
    content: `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Frontend Test Document) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF`
  }
};

// Helper functions
async function createTestFile(): Promise<string> {
  const filePath = path.join('/tmp', TEST_CONFIG.testFile.name);
  await fs.writeFile(filePath, TEST_CONFIG.testFile.content);
  return filePath;
}

async function registerUser(page: Page): Promise<void> {
  console.log('🔐 Registering test user...');
  
  // Navigate to the main page
  await page.goto('/');
  
  // Look for login/register button or navigation
  const authButton = page.locator('text=Login').or(page.locator('text=Sign In')).or(page.locator('text=Get Started')).or(page.locator('[data-testid="login-button"]'));
  await expect(authButton).toBeVisible({ timeout: 10000 });
  await authButton.click();
  
  // Look for register/signup link or form
  const registerLink = page.locator('text=Sign up').or(page.locator('text=Register')).or(page.locator('text=Create Account')).or(page.locator('[data-testid="register-link"]'));
  await expect(registerLink).toBeVisible({ timeout: 5000 });
  await registerLink.click();
  
  // Fill registration form
  await page.fill('input[type="email"]', TEST_CONFIG.testUser.email);
  await page.fill('input[type="password"]', TEST_CONFIG.testUser.password);
  await page.fill('input[name="name"]', TEST_CONFIG.testUser.name);
  
  // Submit registration
  const submitButton = page.locator('button[type="submit"]').or(page.locator('text=Register')).or(page.locator('text=Sign Up')).or(page.locator('text=Create Account'));
  await submitButton.click();
  
  // Wait for successful registration (be more flexible with success indicators)
  await expect(page.locator('text=success').or(page.locator('text=Welcome')).or(page.locator('text=Dashboard')).or(page.locator('text=Chat')).or(page.locator('text=Upload'))).toBeVisible({ timeout: 15000 });
  
  console.log('✅ User registered successfully');
}

async function loginUser(page: Page): Promise<void> {
  console.log('🔑 Logging in user...');
  
  // Navigate to login page
  await page.goto('/');
  
  // Look for login button
  const loginButton = page.locator('text=Login').or(page.locator('text=Sign In')).or(page.locator('[data-testid="login-button"]'));
  await expect(loginButton).toBeVisible({ timeout: 10000 });
  await loginButton.click();
  
  // Fill login form
  await page.fill('input[type="email"]', TEST_CONFIG.testUser.email);
  await page.fill('input[type="password"]', TEST_CONFIG.testUser.password);
  
  // Submit login
  const submitButton = page.locator('button[type="submit"]').or(page.locator('text=Login')).or(page.locator('text=Sign In'));
  await submitButton.click();
  
  // Wait for successful login
  await expect(page.locator('text=Welcome').or(page.locator('text=Dashboard')).or(page.locator('text=Chat'))).toBeVisible({ timeout: 10000 });
  
  console.log('✅ User logged in successfully');
}

async function uploadDocument(page: Page, filePath: string): Promise<void> {
  console.log('📤 Uploading document...');
  
  // Look for upload functionality based on the landing page content
  const uploadElements = [
    'text=Upload your Medicare plan',
    'text=Upload',
    'text=Upload Document',
    '[data-testid="upload-button"]',
    'button:has-text("Upload")',
    'input[type="file"]'
  ];
  
  let uploadButton = null;
  for (const selector of uploadElements) {
    try {
      const element = page.locator(selector);
      if (await element.isVisible({ timeout: 2000 })) {
        uploadButton = element;
        console.log(`Found upload element: ${selector}`);
        break;
      }
    } catch (e) {
      // Continue to next selector
    }
  }
  
  if (!uploadButton) {
    throw new Error('No upload functionality found on the page');
  }
  
  // If it's a file input, upload directly
  if (await uploadButton.getAttribute('type') === 'file') {
    await uploadButton.setInputFiles(filePath);
  } else {
    // Click the upload button first
    await uploadButton.click();
    
    // Wait for file input to appear
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible({ timeout: 10000 });
    await fileInput.setInputFiles(filePath);
  }
  
  // Look for submit/upload button in modal or form
  const submitUploadButton = page.locator('button:has-text("Upload")').or(page.locator('button:has-text("Submit")')).or(page.locator('button[type="submit"]')).or(page.locator('text=Continue'));
  await expect(submitUploadButton).toBeVisible({ timeout: 10000 });
  await submitUploadButton.click();
  
  // Wait for upload success message (be more flexible)
  await expect(page.locator('text=success').or(page.locator('text=uploaded')).or(page.locator('text=complete')).or(page.locator('text=✅')).or(page.locator('text=processing')).or(page.locator('text=Processing'))).toBeVisible({ timeout: 30000 });
  
  console.log('✅ Document uploaded successfully');
}

async function verifyUploadProcessing(page: Page): Promise<void> {
  console.log('🔍 Verifying upload processing...');
  
  // Look for processing indicators
  const processingIndicator = page.locator('text=processing').or(page.locator('text=Processing')).or(page.locator('[data-testid="processing"]'));
  
  // Wait for processing to complete (up to 2 minutes)
  await expect(processingIndicator).not.toBeVisible({ timeout: 120000 });
  
  // Look for completion message
  await expect(page.locator('text=complete').or(page.locator('text=Complete')).or(page.locator('text=✅')).or(page.locator('text=success'))).toBeVisible({ timeout: 10000 });
  
  console.log('✅ Upload processing completed');
}

test.describe('Frontend Upload Pipeline', () => {
  let testFilePath: string;

  test.beforeAll(async () => {
    // Create test file
    testFilePath = await createTestFile();
    console.log(`�� Created test file: ${testFilePath}`);
  });

  test.afterAll(async () => {
    // Cleanup test file
    try {
      await fs.unlink(testFilePath);
      console.log('🧹 Cleaned up test file');
    } catch (error) {
      console.log('⚠️ Could not clean up test file:', error);
    }
  });

  test('Complete upload workflow - Registration, Login, Upload, Processing', async ({ page }) => {
    console.log('🚀 Starting complete frontend upload workflow test');
    
    // Step 1: Register user
    await registerUser(page);
    
    // Step 2: Login user (in case registration didn't auto-login)
    await loginUser(page);
    
    // Step 3: Upload document
    await uploadDocument(page, testFilePath);
    
    // Step 4: Verify processing
    await verifyUploadProcessing(page);
    
    console.log('🎉 Complete frontend upload workflow test passed!');
  });

  test('Upload with existing user - Login, Upload, Processing', async ({ page }) => {
    console.log('🚀 Starting upload with existing user test');
    
    // Step 1: Login with existing user
    await loginUser(page);
    
    // Step 2: Upload document
    await uploadDocument(page, testFilePath);
    
    // Step 3: Verify processing
    await verifyUploadProcessing(page);
    
    console.log('🎉 Upload with existing user test passed!');
  });

  test('Error handling - Invalid file type', async ({ page }) => {
    console.log('🚀 Starting error handling test');
    
    // Create invalid file
    const invalidFilePath = '/tmp/invalid_file.txt';
    await fs.writeFile(invalidFilePath, 'This is not a PDF file');
    
    try {
      // Login user
      await loginUser(page);
      
      // Try to upload invalid file
      const uploadButton = page.locator('text=Upload').or(page.locator('text=Upload Document')).or(page.locator('[data-testid="upload-button"]'));
      await expect(uploadButton).toBeVisible({ timeout: 10000 });
      await uploadButton.click();
      
      const fileInput = page.locator('input[type="file"]');
      await expect(fileInput).toBeVisible({ timeout: 5000 });
      await fileInput.setInputFiles(invalidFilePath);
      
      // Should show error message
      await expect(page.locator('text=error').or(page.locator('text=Error')).or(page.locator('text=invalid')).or(page.locator('text=❌'))).toBeVisible({ timeout: 10000 });
      
      console.log('✅ Error handling test passed - Invalid file rejected');
    } finally {
      // Cleanup
      try {
        await fs.unlink(invalidFilePath);
      } catch (error) {
        // Ignore cleanup errors
      }
    }
  });

  test('UI responsiveness - Mobile viewport', async ({ page }) => {
    console.log('🚀 Starting mobile responsiveness test');
    
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Login user
    await loginUser(page);
    
    // Verify UI elements are visible and functional
    const uploadButton = page.locator('text=Upload').or(page.locator('text=Upload Document')).or(page.locator('[data-testid="upload-button"]'));
    await expect(uploadButton).toBeVisible({ timeout: 10000 });
    
    console.log('✅ Mobile responsiveness test passed');
  });
});
