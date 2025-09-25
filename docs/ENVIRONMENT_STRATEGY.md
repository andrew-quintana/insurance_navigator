# Environment Strategy Documentation

## Overview

The Insurance Navigator follows a strict **environment separation strategy** where each environment uses consistent component types:

- **Development**: All LOCAL components
- **Staging**: All CLOUD STAGING instances  
- **Production**: All CLOUD PRODUCTION instances

## Environment Configurations

### 🏠 Development Environment
**All components are LOCAL**

| Component | URL | Configuration |
|-----------|-----|---------------|
| Frontend | http://localhost:3000 | `ui/.env.development` |
| Backend | http://localhost:8000 | `.env.development` |
| Database | http://127.0.0.1:54321 | Supabase local |
| Studio | http://127.0.0.1:54323 | Supabase Studio |

**Start Command:**
```bash
./scripts/start-env.sh dev
```

### 🌐 Staging Environment
**All components are CLOUD STAGING instances**

| Component | URL | Configuration |
|-----------|-----|---------------|
| Frontend | https://insurance-navigator-git-staging-andrew-quintanas-projects.vercel.app | `ui/.env.staging` |
| Backend | ***REMOVED*** | `.env.staging` |
| Database | ***REMOVED*** | Supabase staging |

**Start Command:**
```bash
./scripts/start-env.sh staging
```

### 🚀 Production Environment
**All components are CLOUD PRODUCTION instances**

| Component | URL | Configuration |
|-----------|-----|---------------|
| Frontend | https://insurancenavigator.vercel.app | `ui/.env.production` |
| Backend | ***REMOVED*** | `.env.production` |
| Database | ***REMOVED*** | Supabase production |

**Start Command:**
```bash
./scripts/start-env.sh prod
```

## Environment Switching

### Quick Start Commands

```bash
# Development (all local)
./scripts/start-env.sh dev

# Staging (all cloud staging)
./scripts/start-env.sh staging

# Production (all cloud production)
./scripts/start-env.sh prod
```

### Manual Environment Switching

1. **Switch Backend Environment:**
   ```bash
   cp .env.{environment} .env
   ```

2. **Switch Frontend Environment:**
   ```bash
   cd ui
   cp .env.{environment} .env.local
   ```

3. **Restart Services:**
   ```bash
   # For development
   docker-compose restart
   npm run dev
   
   # For staging/production
   # Services are managed by Render/Vercel
   ```

## Testing Environment Requirements

### Unit Tests
- **Environment**: Development (local)
- **Reason**: Fast execution, isolated testing
- **Command**: `pytest tests/unit/`

### Integration Tests
- **Environment**: Staging (cloud staging)
- **Reason**: Real cloud services, realistic data
- **Command**: `pytest tests/integration/`

### End-to-End Tests
- **Environment**: Production (cloud production)
- **Reason**: Full production-like testing
- **Command**: `pytest tests/e2e/`

### Performance Tests
- **Environment**: Staging (cloud staging)
- **Reason**: Production-like performance without production risk
- **Command**: `artillery run performance/artillery-stress-auth.yml`

## Environment Variables

### Backend Environment Variables

Each environment has its own `.env.{environment}` file:

```bash
# Development (.env.development)
SUPABASE_URL=http://127.0.0.1:54321
API_BASE_URL=http://localhost:8000
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres

# Staging (.env.staging)
SUPABASE_URL=***REMOVED***
API_BASE_URL=***REMOVED***
DATABASE_URL=postgresql://postgres:ERaZFjCEnuJsliSQ@db.dfgzeastcxnoqshgyotp.supabase.co:5432/postgres

# Production (.env.production)
SUPABASE_URL=***REMOVED***
API_BASE_URL=***REMOVED***
DATABASE_URL=postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres
```

### Frontend Environment Variables

Each environment has its own `ui/.env.{environment}` file:

```bash
# Development (ui/.env.development)
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_API_URL=http://localhost:8000

# Staging (ui/.env.staging)
NEXT_PUBLIC_SUPABASE_URL=***REMOVED***
NEXT_PUBLIC_API_URL=***REMOVED***

# Production (ui/.env.production)
NEXT_PUBLIC_SUPABASE_URL=***REMOVED***
NEXT_PUBLIC_API_URL=***REMOVED***
```

## Cursor Agent Instructions

### When User Requests Environment Startup

1. **Identify Environment**: Determine if user wants dev/staging/prod
2. **Run Start Script**: Use appropriate `./scripts/start-env.sh {environment}`
3. **Verify Services**: Check that all components are running
4. **Provide URLs**: Give user access URLs and status

### When Coding Agent Needs Testing

1. **Determine Test Level**: Unit/Integration/E2E/Performance
2. **Select Environment**: Based on test requirements
3. **Start Environment**: Use appropriate start script
4. **Run Tests**: Execute tests in selected environment
5. **Report Results**: Include environment context in results

### Environment Validation

Before any deployment or testing:
1. Verify all components are using same environment level
2. Check environment variables are correctly set
3. Validate service connectivity
4. Confirm database connections

## Troubleshooting

### Common Issues

1. **Mixed Environments**: Ensure all components use same environment level
2. **Wrong URLs**: Check environment variable configuration
3. **CORS Issues**: Verify frontend/backend URL matching
4. **Database Connection**: Confirm database URL and credentials

### Environment Health Checks

```bash
# Check development
curl http://localhost:8000/health
curl http://localhost:3000

# Check staging
curl ***REMOVED***/health
curl https://insurance-navigator-git-staging-andrew-quintanas-projects.vercel.app

# Check production
curl ***REMOVED***/health
curl https://insurancenavigator.vercel.app
```

## Security Considerations

- **Development**: Debug enabled, local only
- **Staging**: Debug disabled, cloud staging instances
- **Production**: Debug disabled, cloud production instances
- **Secrets**: Each environment has its own API keys and credentials
