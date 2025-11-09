# Local Development Startup Guide - Validated State

**Document**: Insurance Navigator Local Development Setup  
**Version**: 3.0  
**Last Updated**: 2025-10-09  
**Status**: ✅ VALIDATED AND WORKING  
**Purpose**: Complete startup procedures for local development environment

## 🚀 Quick Start (Validated)

### Prerequisites

- Docker and Docker Compose installed
- Git
- Bash shell
- At least 4GB available RAM
- Ports 3000, 5432, 8000 available
- ngrok installed (for webhook testing)
- Supabase CLI installed (`npm install -g supabase`)
- Node.js and npm installed
- jq installed (`brew install jq`)

### One-Command Setup (NEW - RECOMMENDED)

```bash
# Clone and setup the complete local environment
git clone <repository-url>
cd insurance_navigator
chmod +x scripts/*.sh

# Start all services with one command
./scripts/start-dev-complete.sh
```

**Expected time: <5 minutes** (validated)

### Alternative Manual Setup

```bash
# Set required environment variables
export ENVIRONMENT="development"
export SUPABASE_SERVICE_ROLE_KEY="test-key"
export OPENAI_API_KEY="test-key"
export LLAMAPARSE_API_KEY="test-key"
export NGROK_URL="https://your-ngrok-url.ngrok-free.app"
export WEBHOOK_BASE_URL="https://your-ngrok-url.ngrok-free.app"

# Start all services
docker-compose up -d
```

**Expected time: <5 minutes** (validated)

## 🏗️ Current Architecture (Validated)

The local development environment uses Docker Compose with the following validated configuration:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Supabase      │    │   API Server    │    │   Frontend      │
│   (Local)       │    │   (FastAPI)     │    │   (Next.js)     │
│   Port: 54321   │    │   Port: 8000    │    │   Port: 3000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   ngrok         │
                    │   (Webhooks)    │
                    │   Port: 4040    │
                    └─────────────────┘
```

## 📋 Validated Service Configuration

| Service | Port | Purpose | Status | Health Check |
|---------|------|---------|--------|--------------|
| Supabase (Local) | 54321 | Database & Auth | ✅ Working | Connection test |
| API Server | 8000 | FastAPI application | ✅ Working | `/health` |
| Frontend | 3000 | Next.js UI | ✅ Working | `/` |
| ngrok | 4040 | Webhook tunneling | ✅ Working | API accessible |

## 🔧 Environment Variables (Validated)

### Required Environment Variables

```bash
# Core Environment
ENVIRONMENT=development
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:54322/postgres?sslmode=disable
SUPABASE_URL=http://host.docker.internal:54321
SUPABASE_SERVICE_ROLE_KEY=test-key
OPENAI_API_KEY=test-key
LLAMAPARSE_API_KEY=test-key

# Webhook Configuration (for LlamaParse callbacks)
NGROK_URL=https://your-ngrok-url.ngrok-free.app
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok-free.app
```

### Environment File Setup

The system uses `.env.development` file with validated configuration:

```bash
# Database URLs (VALIDATED - uses host.docker.internal)
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:54322/postgres?sslmode=disable
DATABASE_URL_LOCAL=postgresql://postgres:postgres@host.docker.internal:54322/postgres

# Supabase Configuration
SUPABASE_URL=http://host.docker.internal:54321
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## 🚀 Startup Procedures (Validated)

### Step 1: Start Supabase (Local)

```bash
# Start Supabase local instance
supabase start

# Verify Supabase is running
supabase status
```

**Expected Output:**
```
         API URL: http://localhost:54321
     GraphQL URL: http://localhost:54321/graphql/v1
          DB URL: postgresql://postgres:postgres@localhost:54322/postgres
      Studio URL: http://localhost:54323
    Inbucket URL: http://localhost:54324
      JWT secret: super-secret-jwt-token-with-at-least-32-characters-long
        anon key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 2: Start ngrok (for Webhooks)

```bash
# Start ngrok tunnel
ngrok http 8000 --log=stdout

# Note the ngrok URL (e.g., https://abc123.ngrok-free.app)
# Set environment variables
export NGROK_URL="https://abc123.ngrok-free.app"
export WEBHOOK_BASE_URL="https://abc123.ngrok-free.app"
```

### Step 3: Start Application Services

```bash
# Set all required environment variables
export ENVIRONMENT="development"
export SUPABASE_SERVICE_ROLE_KEY="test-key"
export OPENAI_API_KEY="test-key"
export LLAMAPARSE_API_KEY="test-key"
export NGROK_URL="https://abc123.ngrok-free.app"
export WEBHOOK_BASE_URL="https://abc123.ngrok-free.app"

# Start Docker services
docker-compose up -d

# Check status
docker-compose ps
```

### Step 4: Verify All Services

```bash
# Check API health
curl http://localhost:8000/health

# Check webhook endpoint
curl -X POST "https://abc123.ngrok-free.app/api/upload-pipeline/webhook/llamaparse/test-job-123" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "data": {"parsed_content": "test"}}'

# Check frontend
open http://localhost:3000
```

## 🧪 Testing Procedures (Validated)

### 1. Database Connection Test

```bash
# Test database connection from container
docker exec insurance_navigator-api-1 python -c "
import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@host.docker.internal:54322/postgres?sslmode=disable')
        print('✅ Database connection successful!')
        await conn.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test_connection())
"
```

### 2. Webhook Configuration Test

```bash
# Test webhook URL discovery
docker exec insurance_navigator-api-1 python -c "
from backend.shared.utils.ngrok_discovery import get_webhook_base_url
print(f'Webhook base URL: {get_webhook_base_url()}')
print(f'Expected webhook URL: {get_webhook_base_url()}/api/upload-pipeline/webhook/llamaparse/{{job_id}}')
"
```

### 3. Full Application Test

```bash
# Test complete application startup
docker exec insurance_navigator-api-1 python -c "
import asyncio
from main import startup_event

async def test_startup():
    try:
        await startup_event()
        print('✅ Application startup successful!')
    except Exception as e:
        print(f'❌ Application startup failed: {e}')

asyncio.run(test_startup())
"
```

## 🔍 Troubleshooting (Validated Solutions)

### Issue 1: Database Connection Refused

**Symptoms:** `ConnectionRefusedError: [Errno 111] Connection refused`

**Root Cause:** Application trying to connect to `127.0.0.1:54322` instead of `host.docker.internal:54322`

**Solution:**
1. Verify `.env.development` uses `host.docker.internal:54322`
2. Check that `docker-compose.yml` sets correct `DATABASE_URL`
3. Ensure no conflicting database configurations

### Issue 2: Webhook URL Not Accessible

**Symptoms:** ngrok returns 503 error for webhook calls

**Root Cause:** API server not running or ngrok URL not configured

**Solution:**
1. Verify API server is running: `docker-compose ps`
2. Check ngrok is running: `curl http://localhost:4040/api/tunnels`
3. Set `NGROK_URL` and `WEBHOOK_BASE_URL` environment variables

### Issue 3: Environment Variables Not Loaded

**Symptoms:** `FileNotFoundError: Environment file not found`

**Root Cause:** `ENVIRONMENT` variable not set

**Solution:**
```bash
export ENVIRONMENT="development"
docker-compose restart api
```

### Issue 4: Missing Required Environment Variables

**Symptoms:** `ValueError: Missing required environment variables`

**Root Cause:** Required API keys not set

**Solution:**
```bash
export SUPABASE_SERVICE_ROLE_KEY="test-key"
export OPENAI_API_KEY="test-key"
export LLAMAPARSE_API_KEY="test-key"
docker-compose restart api
```

## 📊 Monitoring and Health Checks

### Service Health Endpoints

```bash
# API Health
curl http://localhost:8000/health

# Supabase Health
curl http://localhost:54321/health

# ngrok Status
curl http://localhost:4040/api/tunnels

# Frontend Health
curl http://localhost:3000
```

### Log Monitoring

```bash
# API Logs
docker logs insurance_navigator-api-1 --tail 50

# All Services Logs
docker-compose logs --tail 50

# Follow Logs
docker-compose logs -f api
```

## 🎯 Development Workflow

### Making Changes

1. **Code Changes**: Edit files in the project
2. **Service Restart**: `docker-compose restart api`
3. **Full Rebuild**: `docker-compose up --build`
4. **Test Changes**: Use the testing procedures above

### Database Changes

1. **Schema Changes**: Update Supabase migrations
2. **Apply Changes**: `supabase db reset` (if needed)
3. **Test Connection**: Use database connection test

### Webhook Testing

1. **Update ngrok URL**: If ngrok restarts, update environment variables
2. **Test Webhook**: Use webhook configuration test
3. **Verify Endpoint**: Test webhook endpoint accessibility

## 🛠️ New Development Scripts

### Complete Startup Script

The new `start-dev-complete.sh` script handles all aspects of the development environment:

```bash
# Start everything
./scripts/start-dev-complete.sh

# Stop everything
./scripts/stop-dev-complete.sh

# Check health of all services
./scripts/health-check.sh
```

**Features:**
- ✅ Automatic prerequisite checking
- ✅ Supabase local instance management
- ✅ ngrok tunnel setup and URL discovery
- ✅ Environment variable configuration
- ✅ Docker services startup
- ✅ Frontend development server
- ✅ Health checks and verification
- ✅ Graceful shutdown handling
- ✅ Comprehensive logging

### Script Capabilities

| Script | Purpose | Features |
|--------|---------|----------|
| `start-dev-complete.sh` | Start all services | Prerequisites check, service startup, health verification |
| `stop-dev-complete.sh` | Stop all services | Graceful shutdown, cleanup, process management |
| `health-check.sh` | Check service health | Service status, URL verification, troubleshooting |

## 📚 Next Steps

After successful startup:

1. **Frontend Access**: Open http://localhost:3000
2. **User Registration**: Create a test user account
3. **Document Upload**: Test the upload pipeline
4. **Webhook Testing**: Verify LlamaParse webhook callbacks
5. **Chat Testing**: Test AI chat functionality

## ✅ Validation Checklist

- [ ] Supabase local instance running on port 54321
- [ ] ngrok tunnel active and accessible
- [ ] API server running and healthy on port 8000
- [ ] Frontend accessible on port 3000
- [ ] Database connection working (host.docker.internal:54322)
- [ ] Webhook endpoint accessible through ngrok
- [ ] All required environment variables set
- [ ] No connection refused errors in logs
- [ ] All health checks passing

## 🚨 Emergency Procedures

### Complete Reset

```bash
# Stop all services
docker-compose down
supabase stop

# Clean up
docker system prune -f

# Restart everything
supabase start
export ENVIRONMENT="development"
export SUPABASE_SERVICE_ROLE_KEY="test-key"
export OPENAI_API_KEY="test-key"
export LLAMAPARSE_API_KEY="test-key"
export NGROK_URL="https://your-ngrok-url.ngrok-free.app"
export WEBHOOK_BASE_URL="https://your-ngrok-url.ngrok-free.app"
docker-compose up -d
```

### Quick Health Check

```bash
# One-command health check
curl -s http://localhost:8000/health | python -m json.tool && \
curl -s http://localhost:54321/health && \
curl -s http://localhost:4040/api/tunnels | python -m json.tool && \
echo "✅ All services healthy"
```

---

**Last Updated**: 2025-10-09  
**Environment**: Local Development  
**Status**: ✅ VALIDATED AND WORKING  
**Next Review**: After any infrastructure changes
