# 003 Worker Refactor - Local Development Environment

This document provides comprehensive instructions for setting up and using the local development environment for the 003 Worker Refactor iteration.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git
- Bash shell
- At least 4GB available RAM
- Ports 3000, 5432, 8000-8002 available

### One-Command Setup

```bash
# Clone and setup the complete local environment
git clone <repository-url>
cd insurance_navigator
chmod +x scripts/*.sh
./scripts/setup-local-env.sh
```

This will:
- Create all necessary directories
- Set up environment configuration
- Build and start all Docker services
- Run database migrations
- Perform initial health checks

**Expected time: <30 minutes** (meeting our KPI)

## 🏗️ Architecture Overview

The local development environment replicates the production stack using Docker Compose:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │  Supabase       │    │   API Server    │
│   (pgvector)    │    │  Storage        │    │   (FastAPI)     │
│   Port: 5432    │    │  Port: 8000     │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   BaseWorker    │
                    │   (Processing)  │
                    │   Port: 8000    │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Mock LlamaParse │    │  Mock OpenAI    │    │   Monitoring    │
│   Port: 8001    │    │   Port: 8002    │    │   Port: 3000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Directory Structure

```
insurance_navigator/
├── backend/                    # Backend application code
│   ├── api/                   # FastAPI API server
│   ├── workers/               # Worker processes
│   ├── shared/                # Shared utilities and models
│   │   ├── db/               # Database connection and models
│   │   ├── schemas/          # Pydantic models
│   │   └── utils/            # Common utilities
│   ├── scripts/               # Database scripts and migrations
│   └── tests/                 # Test suites
├── infrastructure/             # Infrastructure configuration
├── testing/                   # Testing utilities and mocks
│   └── mocks/                # Mock external services
├── monitoring/                # Local monitoring dashboard
├── scripts/                   # Setup and utility scripts
└── docker-compose.yml         # Complete local environment
```

## 🔧 Services Configuration

### Core Services

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| PostgreSQL | 5432 | Database with pgvector | Connection test |
| API Server | 8000 | FastAPI application | `/health` |
| BaseWorker | 8000 | Processing pipeline | `/health` |
| Mock LlamaParse | 8001 | Document parsing simulation | `/health` |
| Mock OpenAI | 8002 | Embeddings simulation | `/health` |
| Monitoring | 3000 | Local dashboard | `/health` |

### Environment Variables

Copy `env.local.example` to `.env.local` and modify as needed:

```bash
cp env.local.example .env.local
# Edit .env.local with your preferences
```

## 🚀 Development Workflow

### 1. Start the Environment

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f [service-name]
```

### 2. Run Tests

```bash
# Quick validation
./scripts/run-local-tests.sh

# Comprehensive validation
./scripts/validate-local-environment.sh
```

### 3. Monitor Services

Open [http://localhost:3000](http://localhost:3000) for the monitoring dashboard.

### 4. Stop the Environment

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (resets data)
docker-compose down -v
```

## 🧪 Testing Strategy

### Local Testing Levels

1. **Unit Tests** (`backend/tests/unit/`)
   - Individual component testing
   - Mocked dependencies
   - Fast execution

2. **Integration Tests** (`backend/tests/integration/`)
   - Service interaction testing
   - Database operations
   - Mock service validation

3. **End-to-End Tests** (`backend/tests/e2e/`)
   - Complete pipeline validation
   - Real data flow testing
   - Performance benchmarks

4. **Performance Tests** (`backend/tests/performance/`)
   - Load testing
   - Resource utilization
   - Scalability validation

### Mock Services

- **Mock LlamaParse**: Simulates document parsing with configurable delays
- **Mock OpenAI**: Simulates embeddings generation with rate limiting
- **Deterministic**: Same input always produces same output
- **Configurable**: Adjustable response times and error rates

## 📊 Monitoring and Observability

### Local Dashboard Features

- Real-time service health status
- Response time monitoring
- System metrics overview
- Auto-refresh every 10 seconds
- Visual status indicators

### Logging

All services use structured logging with correlation IDs:

```python
from backend.shared.utils.common import get_correlation_id, log_with_context

correlation_id = get_correlation_id()
log_with_context("Processing job", correlation_id=correlation_id, job_id=job_id)
```

### Health Checks

Each service provides a `/health` endpoint:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:3000/health
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using a port
   lsof -i :8000
   
   # Stop conflicting services
   sudo lsof -ti:8000 | xargs kill -9
   ```

2. **Docker Issues**
   ```bash
   # Reset Docker environment
   docker-compose down -v
   docker system prune -f
   ./scripts/setup-local-env.sh
   ```

3. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose logs postgres
   
   # Reset database
   docker-compose down -v
   ./scripts/setup-local-env.sh
   ```

### Debug Mode

Enable debug logging by setting in `.env.local`:

```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

## 📈 Performance Benchmarks

### Local Environment Targets

- **Startup Time**: <5 minutes for all services
- **Database Migration**: <2 minutes
- **Health Check Response**: <100ms average
- **Memory Usage**: <2GB total
- **CPU Usage**: <50% average

### Validation Commands

```bash
# Performance validation
./scripts/validate-local-environment.sh

# Quick health check
./scripts/run-local-tests.sh
```

## 🔄 Development Iterations

### Making Changes

1. **Code Changes**: Edit files in `backend/`
2. **Service Restart**: `docker-compose restart [service]`
3. **Full Rebuild**: `docker-compose up --build`
4. **Test Changes**: `./scripts/run-local-tests.sh`

### Database Schema Changes

1. **Create Migration**: Add to `backend/scripts/migrations/`
2. **Apply Migration**: `./scripts/setup-local-env.sh` (includes migrations)
3. **Test Schema**: `./scripts/validate-local-environment.sh`

## 📚 Next Steps

After completing local environment setup:

1. **Phase 2**: Infrastructure validation and deployment
2. **Phase 3**: Enhanced BaseWorker implementation
3. **Phase 4**: Advanced monitoring and alerting
4. **Phase 5**: Performance optimization
5. **Phase 6**: Security hardening
6. **Phase 7**: Production deployment
7. **Phase 8**: Post-deployment validation

## 🤝 Contributing

### Development Guidelines

- Always test locally before committing
- Follow the established directory structure
- Use the provided testing scripts
- Document any environment-specific changes
- Update this README for significant changes

### Code Quality

- Run local tests: `./scripts/run-local-tests.sh`
- Validate environment: `./scripts/validate-local-environment.sh`
- Check service health: Monitor dashboard at [http://localhost:3000](http://localhost:3000)

## 📞 Support

For issues with the local development environment:

1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs [service]`
3. Validate environment: `./scripts/validate-local-environment.sh`
4. Check the monitoring dashboard: [http://localhost:3000](http://localhost:3000)

---

**Last Updated**: Phase 1 Implementation
**Environment**: Local Development
**Status**: Ready for Development
