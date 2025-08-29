const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  // Add more setup options before each test is run
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  
  // Test environment
  testEnvironment: 'jsdom',
  
  // Module name mapping for absolute imports and path aliases
  moduleNameMapper: {
    '^@/components/(.*)$': '<rootDir>/components/$1',
    '^@/lib/(.*)$': '<rootDir>/lib/$1',
    '^@/app/(.*)$': '<rootDir>/app/$1',
    '^@/__tests__/(.*)$': '<rootDir>/__tests__/$1',
  },
  
  // Test file patterns - only run UI tests
  testMatch: [
    '<rootDir>/__tests__/**/*.(ts|tsx|js)',
    '<rootDir>/**/*.(test|spec).(ts|tsx|js)'
  ],
  
  // Coverage configuration - only UI files
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    'app/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/.next/**',
    '!**/coverage/**',
    '!**/*.config.js',
  ],
  
  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 85,
      statements: 85,
    },
  },
  
  // Transform ignore patterns for ESM modules
  transformIgnorePatterns: [
    'node_modules/(?!(react-markdown|remark-.*|rehype-.*|unified|unist-.*|vfile|.*\\.mjs$))'
  ],
  
  // Test timeout
  testTimeout: 10000,
  
  // Only run tests in the UI directory
  testPathIgnorePatterns: [
    '/node_modules/',
    '/.next/',
    '/coverage/',
    '/tests/',
    '/scripts/',
    '/config/',
    '/backend/',
    '/api/',
    '/supabase/',
    '/db/',
    '/data/',
    '/agents/',
    '/utils/',
    '/shared/',
    '/tools/',
    '/docs/',
    '/examples/',
    '/migrations/',
    '/sql/',
    '/docker/',
    '/nginx/',
    '/render/',
    '/deno/',
    '/migration_stage_rename.sql',
    '/main.py',
    '/setup.py',
    '/pyproject.toml',
    '/requirements.txt',
    '/pytest.ini',
    '/jest.config.js',
    '/tsconfig.json',
    '/package.json',
    '/package-lock.json',
    '/deno.json',
    '/deno.lock',
    '/docker-compose.yml',
    '/Dockerfile',
    '/README.md',
    '/PROPRIETARY_LICENSE',
    '/env.local.example',
    '/env.production.example',
    '/env.real-api.example',
    '/import_map.json',
    '/supabase.config.json',
    '/test_*.py',
    '/test_*.ts',
    '/test_*.js',
    '/debug_*.py',
    '/phase*.json',
    '/api_phase*.log',
    '/basic_real_api_test_results_*.json',
    '/corrected_real_api_test_results_*.json',
    '/fixed_real_api_test_results_*.json',
    '/llamaparse_endpoint_discovery_*.json',
    '/test_closeout_*.py',
    '/test_complete_*.py',
    '/test_dev_config_*.py',
    '/test_end_to_end.py',
    '/test_enhanced_*.py',
    '/test_single_*.py',
    '/test_upload.pdf',
    '/test_document.pdf',
    '/test_serverless_*.pdf',
    '/test_serverless_*.txt',
    '/scan_classic_hmo_*.pdf',
    '/simulated_insurance_document.pdf',
    '/insurance_navigator_example.py',
    '/healthcare_regulatory_documents.py',
    '/healthcare_urls.txt',
    '/validate_docs.py',
    '/README_LOCAL_DEVELOPMENT.md',
    '/README.md',
    '/PROPRIETARY_LICENSE',
    '/env.local.example',
    '/env.production.example',
    '/env.real-api.example',
    '/import_map.json',
    '/supabase.config.json',
    '/test_*.py',
    '/test_*.ts',
    '/test_*.js',
    '/debug_*.py',
    '/phase*.json',
    '/api_phase*.log',
    '/basic_real_api_test_results_*.json',
    '/corrected_real_api_test_results_*.json',
    '/fixed_real_api_test_results_*.json',
    '/llamaparse_endpoint_discovery_*.json',
    '/test_closeout_*.py',
    '/test_complete_*.py',
    '/test_dev_config_*.py',
    '/test_end_to_end.py',
    '/test_enhanced_*.py',
    '/test_single_*.py',
    '/test_upload.pdf',
    '/test_document.pdf',
    '/test_serverless_*.pdf',
    '/test_serverless_*.txt',
    '/scan_classic_hmo_*.pdf',
    '/simulated_insurance_document.pdf',
    '/insurance_navigator_example.py',
    '/healthcare_regulatory_documents.py',
    '/healthcare_urls.txt',
    '/validate_docs.py',
    '/README_LOCAL_DEVELOPMENT.md'
  ],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)