# RFC 001 — MVP Production Deployment Architecture

## Design Overview

This RFC outlines the technical architecture for deploying the Insurance Navigator MVP to production, focusing on environment configuration management, automated deployment pipelines, and operational reliability within existing cloud infrastructure constraints.

**Core Architecture:**
```
GitHub Repository → CI/CD Pipeline → Cloud Deployment
     │                    │               │
     │                    ├─ Build/Test   ├─ Render (API Backend)
     │                    ├─ Environment  ├─ Vercel (Frontend)
     │                    └─ Deploy       └─ Supabase (Database)
```

**Key Design Principles:**
- Environment isolation with clear boundaries
- Infrastructure as Code where possible
- Automated testing and validation
- Graceful handling of free tier limitations
- Security-first approach to secrets management

## Interface Contracts (verbatim)

### Environment Configuration Interface
```typescript
interface EnvironmentConfig {
  environment: 'development' | 'production';
  api: {
    baseUrl: string;
    corsOrigins: string[];
    rateLimiting: boolean;
  };
  database: {
    url: string;
    poolSize: number;
    connectionTimeout: number;
  };
  frontend: {
    appUrl: string;
    apiBaseUrl: string;
    analyticsEnabled: boolean;
  };
  external: {
    openaiApiKey: string;
    anthropicApiKey: string;
    llamaCloudApiKey: string;
    resendApiKey: string;
  };
  security: {
    jwtSecret: string;
    encryptionKey: string;
    bypassEnabled: boolean;
  };
}
```

### Deployment Pipeline Interface
```yaml
# .github/workflows/production-deploy.yml
name: Production Deployment
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Environment Validation
        run: npm run validate:production
      - name: Security Scan
        run: npm run security:scan
      - name: Type Check
        run: npm run type-check

  deploy-api:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: curl -X POST $RENDER_DEPLOY_HOOK_URL

  deploy-frontend:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Vercel
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
        run: vercel --prod --token $VERCEL_TOKEN
```

### Health Check Interface
```typescript
interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  environment: string;
  services: {
    database: ServiceStatus;
    external_apis: ServiceStatus;
    storage: ServiceStatus;
  };
  performance: {
    response_time_ms: number;
    memory_usage_mb: number;
    uptime_seconds: number;
  };
}

interface ServiceStatus {
  status: 'up' | 'down' | 'degraded';
  last_check: string;
  error?: string;
}
```

## Implementation Plan

### Phase 1: Environment Configuration Refactoring (Week 1)
**Objective:** Establish clear environment separation and configuration management

**Tasks:**
1. **Environment Configuration Consolidation**
   - Create `config/environments/` directory structure
   - Implement environment-specific configuration loading
   - Add configuration validation utilities
   - Document environment variable requirements

2. **Security Hardening**
   - Audit all environment variables for security classification
   - Implement secrets validation patterns
   - Add environment variable encryption where needed
   - Create secure defaults for production

3. **Development/Production Isolation**
   - Separate development and production environment files
   - Implement environment detection logic
   - Add configuration testing for both environments
   - Document environment switching procedures

**Deliverables:**
- `config/environments/development.ts`
- `config/environments/production.ts` 
- `scripts/validate-environment.ts`
- Updated documentation for environment management

### Phase 2: CI/CD Pipeline Implementation (Week 2)
**Objective:** Automate deployment processes with proper validation

**Tasks:**
1. **GitHub Actions Workflow Setup**
   - Create production deployment workflow
   - Implement build and test validation
   - Add security scanning integration
   - Configure deployment triggers and approvals

2. **Deployment Automation**
   - Configure Render auto-deploy from GitHub
   - Set up Vercel production deployment
   - Implement deployment status monitoring
   - Add rollback capabilities

3. **Quality Gates**
   - TypeScript compilation validation
   - ESLint and security rule enforcement
   - Test suite execution requirements
   - Performance benchmark validation

**Deliverables:**
- `.github/workflows/production-deploy.yml`
- `.github/workflows/pr-validation.yml`
- `scripts/deployment/validate-build.ts`
- Deployment monitoring dashboard setup

### Phase 3: Production Operations Setup (Week 3)
**Objective:** Implement monitoring, logging, and maintenance procedures

**Tasks:**
1. **Health Monitoring Implementation**
   - Create comprehensive health check endpoints
   - Implement uptime monitoring integration
   - Add performance metrics collection
   - Configure alerting for critical failures

2. **Logging and Error Tracking**
   - Centralize application logging
   - Implement error aggregation and alerting
   - Add performance monitoring
   - Create log retention policies

3. **Free Tier Optimization**
   - Implement keep-warm strategies for Render
   - Optimize cold start performance
   - Add graceful degradation for sleep modes
   - Document free tier limitations and workarounds

**Deliverables:**
- `/api/health` comprehensive endpoint
- Monitoring dashboard configuration
- `scripts/keep-warm.ts` automated solution
- Operations runbook documentation

## Migration Strategy

### Data Migration
- **Database Schema**: No migration required - production database already established
- **Environment Variables**: Systematic migration using validation scripts
- **File Storage**: No migration - Supabase storage already configured

### Deployment Migration
1. **Current State Assessment**
   - Audit existing Render and Vercel configurations
   - Document current deployment procedures
   - Identify configuration gaps and inconsistencies

2. **Gradual Implementation**
   - Phase 1: Environment configuration without changing deployment
   - Phase 2: Implement CI/CD alongside manual deployment
   - Phase 3: Full automation with monitoring

3. **Rollback Strategy**
   - Maintain manual deployment capability during transition
   - Document rollback procedures for each phase
   - Test rollback scenarios before production implementation

## Testing Strategy

### Environment Testing
- **Configuration Validation**: Automated testing of environment configurations
- **Cross-Environment Consistency**: Validation scripts for environment parity
- **Security Testing**: Automated security scanning and secret validation

### Deployment Testing
- **Staging Environment**: Use preview deployments for validation
- **Integration Testing**: End-to-end testing in production-like environment
- **Performance Testing**: Load testing with free tier constraints
- **Rollback Testing**: Validation of rollback procedures

### Production Validation
- **Health Check Testing**: Comprehensive health endpoint validation
- **Monitoring Validation**: Alerting and monitoring system testing
- **User Acceptance Testing**: Key user journeys in production environment

## Rollout Plan

### Phase 1 Rollout (Days 1-7)
- Deploy environment configuration changes to development
- Test configuration validation in development environment
- Create production environment configuration (without deployment)
- Document environment switching procedures

### Phase 2 Rollout (Days 8-14)
- Implement CI/CD pipeline in development branch
- Test automated deployment to staging/preview environments
- Configure production deployment triggers (manual approval required)
- Validate rollback procedures

### Phase 3 Rollout (Days 15-21)
- Deploy monitoring and health check systems
- Enable automated production deployments
- Implement keep-warm strategies for free tier
- Complete operations documentation

### Production Cutover (Day 22)
- Switch to automated deployment for production
- Enable full monitoring and alerting
- Document lessons learned and process improvements
- Provide team training on new deployment procedures

### Success Criteria
- ✅ Zero manual steps required for standard deployments
- ✅ Complete environment isolation between development and production
- ✅ Sub-10 minute deployment times with validation
- ✅ 99.5% deployment success rate
- ✅ Comprehensive monitoring and alerting coverage
- ✅ Team capability to manage deployments independently