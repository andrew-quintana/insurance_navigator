import { beforeAll, afterAll, beforeEach } from 'vitest';
import { FullIntegrationEnvironment } from './full-environment';

const environment = new FullIntegrationEnvironment();

// Global test setup
beforeAll(async () => {
  console.log('🚀 Setting up full integration test environment...');
  await environment.start();
}, 300000); // 5 minutes timeout

afterAll(async () => {
  console.log('🛑 Cleaning up full integration test environment...');
  await environment.stop();
}, 300000); // 5 minutes timeout

beforeEach(async () => {
  // Reset test data between tests
  await environment.resetData();
}, 60000); // 1 minute timeout

// Export environment for use in tests
export { environment };