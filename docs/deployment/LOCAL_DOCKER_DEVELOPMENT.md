# Local Docker Development Guide

**Initiative**: MVP Production Deployment - Phase 0.5  
**Date**: 2025-01-18  
**Status**: Implementation Ready

## Overview

This guide explains how to use local Docker simulation to match the Render production environment, allowing you to catch deployment issues early in the development cycle.

## Problem Solved

The current local development setup differs significantly from the Render production environment:
- **Local**: Direct Python execution, no Docker, direct file system access
- **Production**: Docker containerized, multi-stage build, isolated environment

This mismatch causes issues to be discovered only during production deployments, leading to:
- Failed builds in production
- Module import errors (`ModuleNotFoundError: No module named 'api'`)
- Dependency conflicts (httpx version conflicts)
- Configuration mismatches

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Production environment variables in `.env.production`

### Start Local Docker Environment
```bash
# Start all services (API, Worker, Frontend)
npm run dev:docker

# Or start in detached mode
npm run dev:docker:detached
```

### Run Pre-Deployment Tests
```bash
# Test everything before pushing to production
npm run pre-deploy:test
```

### Check Service Status
```bash
# View logs
npm run docker:logs

# Check container health
npm run test:local-production

# Access container shell
npm run docker:shell
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | FastAPI backend with health checks |
| **Frontend** | http://localhost:3000 | Next.js frontend application |
| **Worker** | Background | Background worker for processing tasks |

## Development Workflow

### 1. Local Development with Docker
```bash
# Start Docker environment
npm run dev:docker

# Make changes to code
# Changes are automatically reflected due to volume mounting

# Test changes
curl http://localhost:8000/health
```

### 2. Pre-Deployment Testing
```bash
# Run comprehensive tests before pushing
npm run pre-deploy:test

# This will:
# - Build Docker images locally
# - Test module imports
# - Test dependency resolution
# - Test health checks
```

### 3. Debugging Issues
```bash
# View logs for all services
npm run docker:logs

# View logs for specific service
docker-compose logs api
docker-compose logs worker
docker-compose logs frontend

# Access container shell for debugging
npm run docker:shell
```

## Testing Procedures

### Module Import Testing
```bash
# Test API module imports
docker-compose exec api python -c "from api.upload_pipeline.webhooks import router; print('✅ API imports successful')"

# Test worker module imports
docker-compose exec worker python -c "from backend.workers.enhanced_base_worker import EnhancedBaseWorker; print('✅ Worker imports successful')"
```

### Dependency Resolution Testing
```bash
# Check for dependency conflicts
docker-compose exec api pip check

# This will catch issues like httpx version conflicts
```

### Health Check Testing
```bash
# Test API health endpoint
curl -f http://localhost:8000/health

# Test frontend
curl -f http://localhost:3000
```

## Configuration

### Environment Variables
The Docker environment uses production environment variables from `.env.production`:

```bash
# Load production environment variables
export $(cat .env.production | grep -v '^#' | xargs)
```

### Docker Compose Configuration
The `docker-compose.yml` file mirrors the Render production setup:
- Uses the same Dockerfiles as production
- Mounts volumes for development
- Sets up health checks
- Configures environment variables

## Troubleshooting

### Common Issues

#### 1. Module Import Errors
```bash
# Error: ModuleNotFoundError: No module named 'api'
# Solution: Check Docker build context and file copying
docker-compose build --no-cache api
```

#### 2. Dependency Conflicts
```bash
# Error: ResolutionImpossible: httpx version conflict
# Solution: Check requirements.txt and update versions
docker-compose exec api pip check
```

#### 3. Health Check Failures
```bash
# Error: Health check failed
# Solution: Check service logs and configuration
docker-compose logs api
```

#### 4. Environment Variable Issues
```bash
# Error: Missing environment variables
# Solution: Ensure .env.production exists and is loaded
ls -la .env.production
```

### Clean Environment
```bash
# Clean up Docker environment
npm run docker:clean

# This will:
# - Stop all containers
# - Remove volumes
# - Clean up unused images
```

## Integration with CI/CD

### Pre-Deployment Validation
Before pushing to production, always run:
```bash
npm run pre-deploy:test
```

This ensures that:
- Docker builds work locally
- Module imports are correct
- Dependencies resolve properly
- Health checks pass

### Continuous Integration
The local Docker environment can be integrated into CI/CD pipelines:
```yaml
# Example GitHub Actions step
- name: Test Docker Build
  run: |
    docker-compose build
    docker-compose run --rm api python -c "import api; import backend"
```

## Best Practices

### 1. Always Test Locally First
- Run `npm run pre-deploy:test` before pushing
- Fix issues locally before production deployment
- Use local Docker environment for development

### 2. Monitor Health Checks
- Check health endpoints regularly
- Monitor container logs for errors
- Use health checks to validate changes

### 3. Keep Environment in Sync
- Use production environment variables
- Keep Dockerfiles in sync with production
- Test configuration changes locally

### 4. Debug Systematically
- Check Docker build logs
- Verify module imports
- Test dependency resolution
- Validate health checks

## Scripts Reference

| Script | Command | Description |
|--------|---------|-------------|
| Start Docker | `npm run dev:docker` | Start all services with Docker |
| Start Detached | `npm run dev:docker:detached` | Start services in background |
| Pre-Deploy Test | `npm run pre-deploy:test` | Run comprehensive pre-deployment tests |
| Local Production Test | `npm run test:local-production` | Validate local environment matches production |
| View Logs | `npm run docker:logs` | View logs for all services |
| Container Shell | `npm run docker:shell` | Access API container shell |
| Clean Environment | `npm run docker:clean` | Clean up Docker environment |

## Support

### Getting Help
- Check container logs: `npm run docker:logs`
- Access container shell: `npm run docker:shell`
- Review Docker configuration: `docker-compose.yml`

### Common Commands
```bash
# Check container status
docker-compose ps

# View specific service logs
docker-compose logs api

# Rebuild specific service
docker-compose build api

# Restart specific service
docker-compose restart api
```

## Next Steps

1. **Start Using Local Docker**: Begin using `npm run dev:docker` for development
2. **Run Pre-Deployment Tests**: Always run `npm run pre-deploy:test` before pushing
3. **Integrate with CI/CD**: Add local Docker testing to deployment pipeline
4. **Monitor and Improve**: Use local Docker environment to catch issues early

This local Docker simulation provides the foundation for reliable development and testing that matches production behavior, significantly reducing deployment failures and improving development velocity.
