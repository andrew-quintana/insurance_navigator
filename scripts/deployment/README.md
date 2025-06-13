# Deployment Scripts

This directory contains scripts for deploying the application to various platforms.

## Scripts

### Deployment Scripts
- `quick-deploy.sh` - Quick deployment script for development
- `deploy-serverless.sh` - Serverless deployment script
- `auto-deploy-serverless.sh` - Automated serverless deployment
- `test-serverless-pipeline.sh` - Test the serverless deployment pipeline
- `restart.sh` - Restart application services

## Usage

### Quick Development Deployment
```bash
./scripts/deployment/quick-deploy.sh
```

### Serverless Deployment
```bash
./scripts/deployment/deploy-serverless.sh
```

### Automated Serverless Deployment
```bash
./scripts/deployment/auto-deploy-serverless.sh
```

### Test Deployment Pipeline
```bash
./scripts/deployment/test-serverless-pipeline.sh
```

### Restart Services
```bash
./scripts/deployment/restart.sh
```

## Prerequisites

- Docker installed and running
- Appropriate cloud platform credentials configured
- Environment variables set up (see `config/environment/env.example`)

## Environment Variables

Make sure to set up the required environment variables before running deployment scripts:

```bash
cp config/environment/env.example .env
# Edit .env with your actual values
``` 