process.env = {
  ...process.env,
  ENV_LEVEL: 'test',
  SUPABASE_URL: 'http://localhost:54321',
  SUPABASE_SERVICE_ROLE_KEY: 'test-key',
  TEST_USER_ID: 'test-user-id',
  TEST_USER_EMAIL: 'test@example.com',
  TEST_USER_PASSWORD: 'test-password'
}; 