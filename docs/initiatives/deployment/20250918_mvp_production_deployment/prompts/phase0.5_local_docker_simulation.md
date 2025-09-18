# Phase 0.5 Implementation Prompt - Local Docker Simulation

**Initiative**: MVP Production Deployment  
**Phase**: 0.5 of 4 - Local Docker Simulation  
**Duration**: 2-3 days  
**Prerequisites**: Phase 0 context harvest completed

## Objective

Implement local Docker simulation that mirrors the Render production environment to catch deployment issues early in the development cycle, reducing the need for production deployments to discover configuration and build problems.

## Problem Statement

The current local development setup differs significantly from the Render production environment:
- **Local**: Direct Python execution, no Docker, direct file system access
- **Production**: Docker containerized, multi-stage build, isolated environment

This mismatch causes issues to be discovered only during production deployments, leading to:
- Failed builds in production
- Module import errors
- Dependency conflicts
- Configuration mismatches

## Required Reading

Before starting implementation, review these documents:

### Core Planning Documents
- **Initiative Overview**: `@docs/initiatives/deployment/20250918_mvp_production_deployment/README.md`
- **Technical Architecture**: `@docs/initiatives/deployment/20250918_mvp_production_deployment/scoping/RFC.md`
- **Implementation Plan**: `@docs/initiatives/deployment/20250918_mvp_production_deployment/scoping/TODO.md` (Phase 0.5 section)

### Current Infrastructure References
- **Current Production Config**: `@.env.production` - Production environment settings
- **Current Dockerfile**: `@Dockerfile` - Root-level Dockerfile for API service
- **Worker Dockerfile**: `@backend/workers/Dockerfile` - Worker service Dockerfile
- **Render Configuration**: `@config/render/render.yaml` - Render deployment config

## Implementation Tasks

### 1. Local Docker Environment Setup

#### Docker Compose Configuration
Create `docker-compose.yml` that mirrors the Render production setup:

```yaml
version: '3.8'
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      # ... other production environment variables
    volumes:
      - .:/app
    command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    build:
      context: .
      dockerfile: backend/workers/Dockerfile
    environment:
      - ENVIRONMENT=production
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      # ... other production environment variables
    volumes:
      - .:/app
    command: ["python", "backend/workers/enhanced_runner.py"]
    healthcheck:
      test: ["CMD", "python", "-c", "from backend.workers.enhanced_base_worker import EnhancedBaseWorker; print('Enhanced worker import successful')"]
      interval: 15s
      timeout: 5s
      retries: 2

  frontend:
    build:
      context: ./ui
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    depends_on:
      - api
```

#### Local Development Scripts
Create scripts for local Docker development:

**`scripts/local-docker-dev.sh`**:
```bash
#!/bin/bash
# Local Docker development script

echo "🐳 Starting local Docker development environment..."

# Load production environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
    echo "✅ Loaded production environment variables"
else
    echo "❌ .env.production not found"
    exit 1
fi

# Build and start services
docker-compose up --build

echo "🚀 Local development environment started!"
echo "API: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Worker: Running in background"
```

**`scripts/local-docker-test.sh`**:
```bash
#!/bin/bash
# Local Docker testing script

echo "🧪 Running local Docker tests..."

# Test API service
echo "Testing API service..."
docker-compose exec api python -c "from api.upload_pipeline.webhooks import router; print('✅ API imports successful')"

# Test worker service
echo "Testing worker service..."
docker-compose exec worker python -c "from backend.workers.enhanced_base_worker import EnhancedBaseWorker; print('✅ Worker imports successful')"

# Test health endpoints
echo "Testing health endpoints..."
curl -f http://localhost:8000/health || echo "❌ API health check failed"
curl -f http://localhost:3000 || echo "❌ Frontend health check failed"

echo "✅ Local Docker tests completed!"
```

### 2. Local Testing and Validation

#### Pre-Deployment Testing
Create comprehensive local testing procedures:

**`scripts/pre-deploy-test.sh`**:
```bash
#!/bin/bash
# Pre-deployment testing script

echo "🔍 Running pre-deployment tests..."

# 1. Test Docker builds locally
echo "1. Testing Docker builds..."
docker-compose build --no-cache

# 2. Test module imports
echo "2. Testing module imports..."
docker-compose run --rm api python -c "import api; import backend; print('✅ All imports successful')"

# 3. Test dependency resolution
echo "3. Testing dependency resolution..."
docker-compose run --rm api pip check

# 4. Test health checks
echo "4. Testing health checks..."
docker-compose up -d
sleep 30
curl -f http://localhost:8000/health || echo "❌ Health check failed"
docker-compose down

echo "✅ Pre-deployment tests completed!"
```

#### Local Environment Validation
Create validation scripts that match production behavior:

**`scripts/validate-local-production.sh`**:
```bash
#!/bin/bash
# Validate local environment matches production

echo "🔍 Validating local environment matches production..."

# Check Docker images
echo "Checking Docker images..."
docker images | grep insurance-navigator

# Check container health
echo "Checking container health..."
docker-compose ps

# Check environment variables
echo "Checking environment variables..."
docker-compose exec api env | grep -E "(SUPABASE|ENVIRONMENT)"

# Check Python path
echo "Checking Python path..."
docker-compose exec api python -c "import sys; print('Python path:', sys.path)"

echo "✅ Local environment validation completed!"
```

### 3. Development Workflow Integration

#### Updated Package.json Scripts
Update `config/node/package.json` with Docker development scripts:

```json
{
  "scripts": {
    "start:backend": "python main.py",
    "start:frontend": "cd ui && npm run dev -- --port 3000",
    "start": "concurrently -n \"BACKEND,FRONTEND\" -c \"blue,green\" -p \"[{name}]\" \"npm run start:backend\" \"npm run start:frontend\"",
    "dev": "npm run start",
    "dev:docker": "docker-compose up --build",
    "dev:docker:detached": "docker-compose up -d --build",
    "test:docker": "docker-compose exec api python -m pytest",
    "test:local-production": "./scripts/validate-local-production.sh",
    "pre-deploy:test": "./scripts/pre-deploy-test.sh",
    "docker:clean": "docker-compose down -v && docker system prune -f",
    "docker:logs": "docker-compose logs -f",
    "docker:shell": "docker-compose exec api bash"
  }
}
```

#### Local Development Documentation
Create comprehensive documentation:

**`docs/deployment/LOCAL_DOCKER_DEVELOPMENT.md`**:
```markdown
# Local Docker Development Guide

## Overview
This guide explains how to use local Docker simulation to match the Render production environment.

## Quick Start
```bash
# Start local Docker environment
npm run dev:docker

# Run pre-deployment tests
npm run pre-deploy:test

# Check logs
npm run docker:logs
```

## Services
- **API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Worker**: Running in background

## Testing
- **Module Imports**: `npm run test:local-production`
- **Health Checks**: `curl http://localhost:8000/health`
- **Dependency Resolution**: `docker-compose exec api pip check`

## Troubleshooting
- **Clean Environment**: `npm run docker:clean`
- **View Logs**: `npm run docker:logs`
- **Shell Access**: `npm run docker:shell`
```

## Success Criteria

Based on the problem statement and requirements:

- [ ] **Docker Environment**: Local Docker setup that mirrors Render production
- [ ] **Module Import Testing**: Local validation of Python module imports
- [ ] **Dependency Resolution**: Local testing of pip dependency resolution
- [ ] **Health Check Validation**: Local testing of health endpoints
- [ ] **Pre-Deployment Testing**: Automated local testing before production deployment
- [ ] **Development Workflow**: Integrated Docker development workflow
- [ ] **Documentation**: Complete local Docker development guide

## Quality Gates

Before considering Phase 0.5 complete:

1. **Docker Build Success**: All Docker images build successfully locally
2. **Module Import Validation**: All Python module imports work in local Docker environment
3. **Dependency Resolution**: No dependency conflicts in local Docker environment
4. **Health Check Functionality**: All health endpoints work in local Docker environment
5. **Pre-Deployment Testing**: Automated local testing catches production issues
6. **Documentation Quality**: Local Docker development procedures are clear and actionable

## Implementation Notes

Document implementation progress using:
- **Implementation Notes**: `@docs/initiatives/deployment/20250918_mvp_production_deployment/docs/phase0.5/implementation_notes.md`
- **Validation Report**: `@docs/initiatives/deployment/20250918_mvp_production_deployment/docs/phase0.5/validation_report.md`

## Phase 0.5 Handoff Requirements

Upon completion, prepare handoff documentation:

### Required Deliverables for Phase 1
1. **Local Docker Simulation**: Complete Docker environment that mirrors production
2. **Pre-Deployment Testing**: Automated local testing procedures
3. **Development Workflow**: Integrated Docker development workflow
4. **Validation Procedures**: Local testing that catches production issues
5. **Documentation**: Complete local Docker development guide

### Handoff Validation
- [ ] All Phase 0.5 tasks completed and tested
- [ ] Local Docker environment matches production behavior
- [ ] Pre-deployment testing catches production issues
- [ ] Development workflow is integrated and documented
- [ ] Team can use local Docker simulation effectively

## Support Resources

- **Technical Architecture**: Reference RFC.md for Docker and deployment design
- **Current Infrastructure**: Reference existing Dockerfiles and Render configuration
- **Problem Context**: Review FRACAS document for specific issues to prevent

This local Docker simulation provides the foundation for reliable development and testing that matches production behavior, significantly reducing deployment failures and improving development velocity.
