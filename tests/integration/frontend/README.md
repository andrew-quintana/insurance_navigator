# Frontend Integration Tests

This directory contains comprehensive integration tests for the Insurance Navigator frontend, covering authentication, document upload, chat interface, and real-time features.

## Overview

The integration tests validate the complete frontend integration scope with mock services, ensuring:

- **Authentication Integration** (PRIORITY #1) - User registration, login, session management
- **Frontend Upload Components** - Document upload with authentication and progress tracking
- **Chat Interface Integration** - Real-time conversation with agent workflows
- **Document State Management** - Upload progress and processing status
- **Agent Conversation Quality** - RAG retrieval accuracy and document context
- **Cross-browser Compatibility** - Consistent functionality across browsers
- **Responsive Design** - Mobile, tablet, and desktop experiences
- **Performance Optimization** - Large file handling and conversation response times

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend Integration Tests                 │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Mock Services │ Integration     │    Test Scenarios       │
│                 │ Framework       │                         │
├─────────────────┼─────────────────┼─────────────────────────┤
│ • Auth Service  │ • TestEnvironment│ • Authentication Flow  │
│ • API Service   │ • AuthTestHelper│ • Upload Integration   │
│ • Frontend      │ • APIClient     │ • Chat Integration     │
│ • Docker Compose│ • Test Setup    │ • Error Scenarios      │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## Prerequisites

- **Docker & Docker Compose** - For running mock services
- **Node.js 18+** - For running tests and mock services
- **npm** - For package management

## Quick Start

### 1. Install Dependencies

```bash
cd tests/integration/frontend
npm install
```

### 2. Start Mock Services

```bash
# Start all mock services
npm run start:services

# Check service health
npm run health:check

# Or use the environment setup
npm run setup:environment
```

### 3. Run Tests

```bash
# Run all integration tests
npm run test:all

# Run specific test categories
npm run test:auth      # Authentication tests
npm run test:upload    # Upload integration tests
npm run test:chat      # Chat integration tests

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

## Mock Services

### Authentication Service (Port 3001)

Mimics Supabase Auth API with:
- User registration and login
- JWT token generation and validation
- Session management and token refresh
- User isolation and data privacy

**Endpoints:**
- `POST /auth/v1/signup` - User registration
- `POST /auth/v1/token` - User login and token refresh
- `GET /auth/v1/user` - Get current user
- `POST /auth/v1/logout` - User logout

### API Service (Port 3002)

Handles document uploads and chat with:
- Authenticated file uploads (PDF, DOCX)
- Document processing simulation
- Chat message handling with agent responses
- Real-time progress tracking

**Endpoints:**
- `POST /api/upload` - Document upload
- `GET /api/documents` - User documents
- `POST /api/chat` - Send chat message
- `GET /api/conversations` - User conversations

## Test Structure

### Test Scenarios

```
scenarios/
├── auth-flow.test.ts      # Authentication integration
├── upload-flow.test.ts    # Document upload integration
└── chat-flow.test.ts      # Chat interface integration
```

### Test Setup

```
setup/
├── auth-helpers.ts        # Authentication test utilities
├── environment.ts         # Test environment management
├── api-helpers.ts         # API client for testing
└── test-setup.ts         # Global test configuration
```

### Mock Services

```
mocks/
├── auth-service/          # Mock authentication service
│   ├── server.js         # Express server
│   ├── package.json      # Dependencies
│   └── Dockerfile        # Container configuration
└── api-service/           # Mock API service
    ├── server.js         # Express server
    ├── package.json      # Dependencies
    └── Dockerfile        # Container configuration
```

## Test Categories

### 1. Authentication Integration (PRIORITY #1)

**Coverage:**
- User registration with email validation
- User login with credential validation
- Session management and token refresh
- Protected route access control
- User data isolation

**Key Tests:**
- `should register new user with email validation`
- `should login with valid credentials`
- `should refresh expired tokens`
- `should maintain user context across token refresh`

### 2. Document Upload Integration

**Coverage:**
- Authenticated file uploads
- File validation and size limits
- Upload progress tracking
- Document management and ownership
- Concurrent upload handling

**Key Tests:**
- `should upload document with authentication`
- `should track upload progress`
- `should maintain user isolation during concurrent uploads`
- `should handle file validation errors`

### 3. Chat Interface Integration

**Coverage:**
- Authenticated chat messages
- Agent response integration
- Conversation management
- Document context integration
- Real-time features

**Key Tests:**
- `should send message with user context`
- `should receive agent response with metadata`
- `should integrate with uploaded documents`
- `should handle multiple agent responses in sequence`

## Running Specific Tests

### Authentication Tests Only

```bash
npm run test:auth
```

### Upload Tests Only

```bash
npm run test:upload
```

### Chat Tests Only

```bash
npm run test:chat
```

### Individual Test Files

```bash
# Run specific test file
npx vitest run scenarios/auth-flow.test.ts

# Run with verbose output
npx vitest run scenarios/auth-flow.test.ts --reporter=verbose
```

## Test Configuration

### Vitest Configuration

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    testTimeout: 60000,        // 60 seconds for integration tests
    hookTimeout: 30000,        // 30 seconds for setup/teardown
    coverage: {
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    }
  }
});
```

### Environment Variables

```bash
# Mock service configuration
NODE_ENV=test
JWT_SECRET=test-secret-key-12345
CORS_ORIGIN=http://localhost:3000
UPLOAD_MAX_SIZE=52428800
ALLOWED_FILE_TYPES=application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

## Performance Testing

### Load Testing Preparation

```bash
# Create multiple test users for load testing
npm run test:all -- --reporter=verbose

# Monitor performance metrics
npm run test:coverage
```

### Performance Targets

- **Authentication**: < 1 second response time
- **Document Upload**: < 2 seconds initiation
- **Chat Response**: < 5 seconds agent response
- **Concurrent Users**: Support 10+ simultaneous users

## Debugging

### Service Logs

```bash
# View all service logs
docker-compose -f docker-compose.mock.yml logs

# View specific service logs
docker-compose -f docker-compose.mock.yml logs auth-service
docker-compose -f docker-compose.mock.yml logs api-service
```

### Health Checks

```bash
# Check service health
npm run health:check

# Manual health checks
curl http://localhost:3001/health
curl http://localhost:3002/health
```

### Test Data Inspection

```bash
# View test users
curl http://localhost:3001/test/users

# View test documents
curl http://localhost:3002/test/documents

# Clear test data
curl -X DELETE http://localhost:3002/test/clear
```

## Troubleshooting

### Common Issues

1. **Services Not Starting**
   ```bash
   # Check Docker status
   docker ps
   
   # Restart services
   npm run restart:services
   ```

2. **Port Conflicts**
   ```bash
   # Check port usage
   lsof -i :3001
   lsof -i :3002
   
   # Stop conflicting services
   docker-compose -f docker-compose.mock.yml down -v
   ```

3. **Test Timeouts**
   ```bash
   # Increase timeout in vitest.config.ts
   testTimeout: 120000  # 2 minutes
   ```

4. **Authentication Failures**
   ```bash
   # Check JWT secret consistency
   # Verify service URLs in test configuration
   # Check CORS settings
   ```

### Debug Mode

```bash
# Run tests with debug output
DEBUG=* npm run test:all

# Run specific test with debug
DEBUG=* npx vitest run scenarios/auth-flow.test.ts
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Frontend Integration Tests
  run: |
    cd tests/integration/frontend
    npm install
    npm run start:services
    npm run test:all
    npm run stop:services
```

### Docker CI

```yaml
- name: Build and Test
  run: |
    docker-compose -f tests/integration/frontend/docker-compose.mock.yml up -d
    docker-compose -f tests/integration/frontend/docker-compose.mock.yml exec frontend-test npm run test:all
```

## Coverage Reports

### Generate Coverage

```bash
npm run test:coverage
```

### Coverage Targets

- **Overall Coverage**: 80%+
- **Authentication**: 90%+
- **Upload Integration**: 85%+
- **Chat Integration**: 85%+

### Coverage Reports

Coverage reports are generated in:
- `coverage/` - Detailed coverage data
- `test-results/` - HTML test results

## Next Steps

After completing integration tests:

1. **Phase 3**: E2E Testing with Playwright
2. **Phase 4**: Performance Testing with Artillery
3. **Phase 5**: Production Readiness Validation

## Contributing

### Adding New Tests

1. Create test file in `scenarios/`
2. Follow existing test patterns
3. Add proper setup/teardown
4. Include error scenarios
5. Update coverage targets

### Test Guidelines

- Use descriptive test names
- Test both success and failure scenarios
- Validate authentication requirements
- Test user data isolation
- Include performance assertions
- Clean up test data properly

## Support

For issues or questions:
- Check troubleshooting section
- Review service logs
- Verify environment configuration
- Check test coverage reports
