import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    testTimeout: 300000, // 5 minutes for integration tests
    hookTimeout: 300000, // 5 minutes for setup/teardown
    teardownTimeout: 300000, // 5 minutes for cleanup
    include: ['scenarios/**/*.test.ts'],
    exclude: ['node_modules/**', 'dist/**'],
    reporter: ['verbose', 'json', 'html'],
    outputFile: {
      json: './results/integration-results.json',
      html: './results/integration-report.html'
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './results/coverage',
      include: ['scenarios/**/*.ts'],
      exclude: ['scenarios/**/*.test.ts']
    },
    setupFiles: ['./setup/test-setup.ts'],
    maxConcurrency: 1, // Run integration tests sequentially
    retry: 2,
    bail: 1 // Stop on first failure for faster feedback
  }
});