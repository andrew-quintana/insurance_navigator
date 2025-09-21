# Mock Integration Environment Setup Guide

## Document Context
This guide provides complete procedures for setting up and using the mock integration environment for the Upload Pipeline + Agent Workflow Integration project.

**Reference Documents**:
- `TODO001.md` - Main implementation tasks and requirements
- `PRD001.md` - Product requirements and success criteria
- `RFC001.md` - Technical architecture and design decisions

## Overview

The mock integration environment provides a complete development and testing environment using mock services instead of real external APIs. This environment enables:

- **Development**: Full development workflow without external API costs
- **Testing**: Comprehensive testing with deterministic responses
- **Integration Validation**: End-to-end integration testing
- **Performance Testing**: Performance validation under controlled conditions

## Prerequisites

### **System Requirements**
- **Docker**: Docker Desktop 4.0+ or Docker Engine 20.10+
- **Docker Compose**: Docker Compose 2.0+
- **Git**: Git 2.30+ for repository access
- **Disk Space**: Minimum 5GB available disk space
- **Memory**: Minimum 8GB RAM available for Docker

### **Software Dependencies**
- **Python**: Python 3.9+ (for local testing and scripts)
- **Node.js**: Node.js 16+ (for some mock services)
- **PostgreSQL Client**: psql or equivalent for database access

### **Network Requirements**
- **Ports**: Ensure the following ports are available:
  - `5432`: PostgreSQL database
  - `8000`: API server
  - `8001`: Agent API
  - `8002`: Local storage service
  - `8003`: Mock LlamaParse service
  - `8004`: Mock OpenAI service
  - `8005`: Enhanced base worker

## Quick Start Setup

### **1. Clone and Navigate to Project**
```bash
git clone <repository-url>
cd insurance_navigator
```

### **2. Launch Mock Integration Environment**
```bash
# Launch the complete mock integration stack
docker-compose -f docker-compose.mock-integration.yml up -d

# Wait for all services to be healthy
./scripts/wait-for-services.sh
```

### **3. Verify Environment Health**
```bash
# Check service status
docker-compose -f docker-compose.mock-integration.yml ps

# Verify all services are healthy
./scripts/validate-mock-environment-health.sh
```

### **4. Test Basic Functionality**
```bash
# Run basic integration tests
python -m pytest tests/integration/test_mock_e2e_integration.py -v

# Test upload pipeline
python -m pytest tests/integration/test_upload_pipeline_mock.py -v

# Test agent workflows
python -m pytest tests/integration/test_agent_workflows_mock.py -v
```

## Detailed Setup Instructions

### **Environment Configuration**

#### **1. Environment Variables**
Create a `.env.mock` file with the following configuration:

```bash
# Database Configuration
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# API Configuration
API_SERVER_HOST=localhost
API_SERVER_PORT=8000
AGENT_API_HOST=localhost
AGENT_API_PORT=8001

# Mock Service Configuration
MOCK_LLAMAPARSE_URL=http://localhost:8003
MOCK_OPENAI_URL=http://localhost:8004
LOCAL_STORAGE_URL=http://localhost:8002

# Worker Configuration
WORKER_HOST=localhost
WORKER_PORT=8005

# JWT Configuration
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_JWT_TOKEN}
```

#### **2. Docker Compose Configuration**
The mock integration environment uses `docker-compose.mock-integration.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/scripts/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api-server:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/postgres
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  agent-api:
    build:
      context: ./agents
      dockerfile: Dockerfile
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/postgres
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  local-storage:
    build:
      context: ./testing/mocks
      dockerfile: storage_server.Dockerfile
    ports:
      - "8002:8000"
    volumes:
      - ./storage:/app/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mock-llamaparse:
    build:
      context: ./testing/mocks
      dockerfile: llamaparse_mock.Dockerfile
    ports:
      - "8003:8000"
    environment:
      - MOCK_DELAY=2.0
      - MOCK_FAILURE_RATE=0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mock-openai:
    build:
      context: ./testing/mocks
      dockerfile: openai_mock.Dockerfile
    ports:
      - "8004:8000"
    environment:
      - MOCK_DELAY=0.5
      - MOCK_FAILURE_RATE=0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  enhanced-base-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/postgres
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - MOCK_LLAMAPARSE_URL=http://mock-llamaparse:8000
      - MOCK_OPENAI_URL=http://mock-openai:8000
    depends_on:
      postgres:
        condition: service_healthy
      mock-llamaparse:
        condition: service_healthy
      mock-openai:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
```

### **Database Setup**

#### **1. Schema Migration**
The database schema is automatically applied when the PostgreSQL container starts:

```bash
# Verify schema creation
docker exec -it insurance_navigator_postgres_1 psql -U postgres -d postgres -c "\dt upload_pipeline.*"

# Expected tables:
# - upload_pipeline.documents
# - upload_pipeline.upload_jobs
# - upload_pipeline.document_chunks
# - upload_pipeline.document_vector_buffer
# - upload_pipeline.events
```

#### **2. Vector Extension Verification**
Verify the pgvector extension is properly installed:

```bash
# Check pgvector extension
docker exec -it insurance_navigator_postgres_1 psql -U postgres -d postgres -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Verify vector type support
docker exec -it insurance_navigator_postgres_1 psql -U postgres -d postgres -c "SELECT typname, typarray FROM pg_type WHERE typname = 'vector';"
```

### **Mock Service Configuration**

#### **1. Mock LlamaParse Service**
The mock LlamaParse service provides deterministic document parsing:

```bash
# Test mock LlamaParse service
curl -X POST http://localhost:8003/parse \
  -H "Content-Type: application/json" \
  -d '{
    "document_url": "test-document.pdf",
    "webhook_url": "http://localhost:8000/webhook/llamaparse"
  }'

# Expected response:
# {
#   "id": "mock-parse-id",
#   "status": "processing",
#   "webhook_url": "http://localhost:8000/webhook/llamaparse"
# }
```

#### **2. Mock OpenAI Service**
The mock OpenAI service provides deterministic embeddings and responses:

```bash
# Test mock OpenAI embeddings
curl -X POST http://localhost:8004/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-key" \
  -d '{
    "input": "test text for embedding",
    "model": "text-embedding-3-small"
  }'

# Expected response:
# {
#   "data": [{"embedding": [0.1, 0.2, ...]}],
#   "model": "text-embedding-3-small",
#   "usage": {"prompt_tokens": 5, "total_tokens": 5}
# }
```

#### **3. Local Storage Service**
The local storage service provides file storage for development:

```bash
# Test local storage service
curl -X GET http://localhost:8002/health

# Expected response:
# {"status": "healthy", "service": "local-storage"}
```

## Testing and Validation

### **Environment Health Checks**

#### **1. Service Health Verification**
```bash
# Check all service health
./scripts/validate-mock-environment-health.sh

# Expected output:
# ✅ PostgreSQL: Healthy
# ✅ API Server: Healthy
# ✅ Agent API: Healthy
# ✅ Local Storage: Healthy
# ✅ Mock LlamaParse: Healthy
# ✅ Mock OpenAI: Healthy
# ✅ Enhanced Base Worker: Healthy
```

#### **2. Database Connectivity Test**
```bash
# Test database connectivity
python -c "
import asyncpg
import asyncio

async def test_db():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/postgres')
        result = await conn.fetch('SELECT 1 as test')
        print('✅ Database connection successful')
        await conn.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test_db())
"
```

#### **3. API Endpoint Testing**
```bash
# Test API server health
curl -f http://localhost:8000/health

# Test agent API health
curl -f http://localhost:8001/health

# Test integration health
curl -f http://localhost:8000/integration/health
```

### **Integration Testing**

#### **1. End-to-End Integration Test**
```bash
# Run complete integration test
python -m pytest tests/integration/test_mock_e2e_integration.py::TestMockEndToEndIntegration::test_upload_to_conversation_with_mocks -v

# Expected result: PASS
# Test validates complete flow: upload → process → query → conversation
```

#### **2. Mock Service Consistency Test**
```bash
# Test mock service consistency
python -m pytest tests/integration/test_unified_mocks.py::test_mock_service_consistency -v

# Expected result: PASS
# Test validates deterministic responses across all mock services
```

#### **3. Performance Validation Test**
```bash
# Test performance targets
python -m pytest tests/integration/performance_validator.py::test_validate_e2e_performance -v

# Expected result: PASS
# Test validates <90 second end-to-end performance target
```

## Common Issues and Troubleshooting

### **Service Startup Issues**

#### **1. Port Conflicts**
**Problem**: Services fail to start due to port conflicts
**Symptoms**: Docker Compose errors about ports already in use
**Solution**:
```bash
# Check for processes using required ports
lsof -i :5432  # PostgreSQL
lsof -i :8000  # API Server
lsof -i :8001  # Agent API
lsof -i :8002  # Local Storage
lsof -i :8003  # Mock LlamaParse
lsof -i :8004  # Mock OpenAI
lsof -i :8005  # Enhanced Base Worker

# Stop conflicting processes or change ports in docker-compose.yml
```

#### **2. Database Connection Issues**
**Problem**: Services cannot connect to PostgreSQL
**Symptoms**: Connection timeout errors in service logs
**Solution**:
```bash
# Wait for PostgreSQL to be fully ready
docker-compose -f docker-compose.mock-integration.yml logs postgres

# Verify PostgreSQL is accepting connections
docker exec -it insurance_navigator_postgres_1 pg_isready -U postgres

# Check database schema
docker exec -it insurance_navigator_postgres_1 psql -U postgres -d postgres -c "\dt upload_pipeline.*"
```

#### **3. Mock Service Health Issues**
**Problem**: Mock services fail health checks
**Symptoms**: Services marked as unhealthy in Docker Compose
**Solution**:
```bash
# Check mock service logs
docker-compose -f docker-compose.mock-integration.yml logs mock-llamaparse
docker-compose -f docker-compose.mock-integration.yml logs mock-openai

# Restart unhealthy services
docker-compose -f docker-compose.mock-integration.yml restart mock-llamaparse mock-openai

# Verify service health
curl -f http://localhost:8003/health
curl -f http://localhost:8004/health
```

### **Performance Issues**

#### **1. Slow Service Startup**
**Problem**: Services take too long to start
**Symptoms**: Health checks timeout during startup
**Solution**:
```bash
# Increase health check timeouts in docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 60s  # Increase from 30s
  timeout: 20s   # Increase from 10s
  retries: 5

# Use startup dependencies
depends_on:
  postgres:
    condition: service_healthy
```

#### **2. High Memory Usage**
**Problem**: Docker containers use excessive memory
**Symptoms**: System becomes slow or unresponsive
**Solution**:
```bash
# Add memory limits to services in docker-compose.yml
services:
  api-server:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

# Monitor resource usage
docker stats
```

### **Testing Issues**

#### **1. Test Failures Due to Service Unavailability**
**Problem**: Tests fail because services are not ready
**Symptoms**: Connection refused or timeout errors in tests
**Solution**:
```bash
# Ensure all services are healthy before testing
./scripts/wait-for-services.sh

# Use health check utilities in tests
from tests.utils.health_checks import wait_for_service_health

@pytest.fixture(autouse=True)
async def ensure_services_healthy():
    await wait_for_service_health()
```

#### **2. Mock Service Inconsistencies**
**Problem**: Mock services provide inconsistent responses
**Symptoms**: Tests fail intermittently due to response variations
**Solution**:
```bash
# Verify mock service configuration
docker-compose -f docker-compose.mock-integration.yml config

# Check mock service environment variables
docker exec -it insurance_navigator_mock_llamaparse_1 env | grep MOCK
docker exec -it insurance_navigator_mock_openai_1 env | grep MOCK

# Restart mock services to ensure consistent state
docker-compose -f docker-compose.mock-integration.yml restart mock-llamaparse mock-openai
```

## Environment Management

### **Starting and Stopping**

#### **1. Start Environment**
```bash
# Start all services
docker-compose -f docker-compose.mock-integration.yml up -d

# Start specific services
docker-compose -f docker-compose.mock-integration.yml up -d postgres api-server
```

#### **2. Stop Environment**
```bash
# Stop all services
docker-compose -f docker-compose.mock-integration.yml down

# Stop and remove volumes
docker-compose -f docker-compose.mock-integration.yml down -v

# Stop specific services
docker-compose -f docker-compose.mock-integration.yml stop postgres
```

#### **3. Restart Environment**
```bash
# Restart all services
docker-compose -f docker-compose.mock-integration.yml restart

# Restart specific services
docker-compose -f docker-compose.mock-integration.yml restart api-server
```

### **Logs and Monitoring**

#### **1. View Service Logs**
```bash
# View all service logs
docker-compose -f docker-compose.mock-integration.yml logs

# View specific service logs
docker-compose -f docker-compose.mock-integration.yml logs api-server

# Follow logs in real-time
docker-compose -f docker-compose.mock-integration.yml logs -f postgres
```

#### **2. Service Status Monitoring**
```bash
# Check service status
docker-compose -f docker-compose.mock-integration.yml ps

# Check service health
docker-compose -f docker-compose.mock-integration.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

### **Data Management**

#### **1. Database Reset**
```bash
# Reset database (removes all data)
docker-compose -f docker-compose.mock-integration.yml down -v
docker-compose -f docker-compose.mock-integration.yml up -d postgres

# Wait for database to be ready
./scripts/wait-for-postgres.sh
```

#### **2. Storage Cleanup**
```bash
# Clean up local storage
rm -rf ./storage/*

# Clean up Docker volumes
docker volume prune
```

## Development Workflow

### **Using Mock Environment for Development**

#### **1. Development Setup**
```bash
# Start mock environment
docker-compose -f docker-compose.mock-integration.yml up -d

# Verify environment health
./scripts/validate-mock-environment-health.sh

# Run development tests
python -m pytest tests/ -v
```

#### **2. Code Changes and Testing**
```bash
# Make code changes
# ...

# Run tests to validate changes
python -m pytest tests/integration/ -v

# Run specific test suites
python -m pytest tests/integration/test_agent_workflows_mock.py -v
```

#### **3. Debugging**
```bash
# View service logs for debugging
docker-compose -f docker-compose.mock-integration.yml logs -f api-server

# Access service directly for debugging
docker exec -it insurance_navigator_api_server_1 bash

# Check database state
docker exec -it insurance_navigator_postgres_1 psql -U postgres -d postgres
```

### **Switching Between Mock and Real APIs**

#### **1. Environment Switching**
```bash
# Stop mock environment
docker-compose -f docker-compose.mock-integration.yml down

# Start real API environment
docker-compose -f docker-compose.real-api.yml up -d

# Verify real API environment
./scripts/validate-real-api-environment.sh
```

#### **2. Configuration Management**
```bash
# Use mock configuration
export ENVIRONMENT=mock
python -m pytest tests/integration/ -v

# Use real API configuration
export ENVIRONMENT=real
python -m pytest tests/integration/ -v
```

## Performance Optimization

### **Environment Performance Tuning**

#### **1. Docker Resource Limits**
```yaml
# Optimize resource allocation in docker-compose.yml
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

#### **2. Database Performance**
```bash
# Optimize PostgreSQL configuration
docker exec -it insurance_navigator_postgres_1 psql -U postgres -d postgres -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
SELECT pg_reload_conf();
"
```

#### **3. Service Performance**
```bash
# Monitor service performance
docker stats

# Check service resource usage
docker exec -it insurance_navigator_api_server_1 top
docker exec -it insurance_navigator_postgres_1 top
```

## Troubleshooting Checklist

### **Environment Setup Issues**
- [ ] **Docker and Docker Compose**: Verify versions and installation
- [ ] **Port Availability**: Check for port conflicts
- [ ] **Disk Space**: Ensure sufficient disk space
- [ ] **Memory**: Ensure sufficient RAM for Docker

### **Service Health Issues**
- [ ] **PostgreSQL**: Verify database is running and accessible
- [ ] **API Services**: Check service health endpoints
- [ ] **Mock Services**: Verify mock service responses
- [ ] **Worker Services**: Check worker service status

### **Database Issues**
- [ ] **Schema**: Verify upload_pipeline schema exists
- [ ] **Extensions**: Check pgvector extension installation
- [ ] **Connections**: Test database connectivity
- [ ] **Permissions**: Verify user permissions

### **Testing Issues**
- [ ] **Service Readiness**: Ensure all services are healthy
- [ ] **Mock Consistency**: Verify mock service responses
- [ ] **Test Data**: Check test data availability
- [ ] **Environment Variables**: Verify configuration

## Conclusion

The mock integration environment provides a complete development and testing environment that enables:

- **Full Development Workflow**: Complete development without external dependencies
- **Deterministic Testing**: Consistent and reliable testing results
- **Performance Validation**: Performance testing under controlled conditions
- **Integration Validation**: End-to-end integration testing

### **Key Benefits**
1. **Cost Effective**: No external API costs during development
2. **Reliable**: Deterministic responses for consistent testing
3. **Fast**: Local services for rapid development cycles
4. **Comprehensive**: Full integration testing capability

### **Next Steps**
1. **Environment Setup**: Follow this guide to set up the mock environment
2. **Testing**: Run integration tests to validate the environment
3. **Development**: Use the environment for ongoing development
4. **Real API Testing**: Switch to real APIs when needed for production validation

The mock environment is designed to provide a production-like experience while maintaining the benefits of controlled, deterministic testing.

---

**Document Status**: ✅ COMPLETE  
**Last Updated**: August 27, 2025  
**Environment Status**: ✅ FULLY OPERATIONAL  
**Testing Status**: ✅ COMPREHENSIVE COVERAGE
