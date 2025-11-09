# Phase 1.5: Docker Setup Guide

**Quick Reference for Using Existing Docker Infrastructure**

---

## ⚡ Quick Start (One Command)

```bash
# Start everything (Supabase + API + Worker + Frontend)
overmind start
# or use convenience wrapper
./scripts/dev-start.sh
```

Then in another terminal:
```bash
export PRODUCTION_API_URL="http://localhost:8000"
python tests/fm_038/chat_flow_investigation.py
```

---

## 🐳 Step-by-Step Docker Setup

### 1. Start Supabase
```bash
# Start local Supabase (PostgreSQL + Auth + Storage)
supabase start

# Check status
supabase status

# You should see:
# API URL: http://localhost:54321
# DB URL: postgresql://postgres:postgres@localhost:54322/postgres
```

### 2. Start API Server and Worker
```bash
# Start both services in detached mode
docker-compose up -d api worker

# Check if running
docker-compose ps

# Should show:
# api     running   0.0.0.0:8000->8000/tcp
# worker  running
```

### 3. Verify Services
```bash
# Check API health
curl http://localhost:8000/health

# Should return: {"status":"healthy"} or similar

# Check Docker logs if issues
docker-compose logs api
docker-compose logs worker
```

### 4. Create Test User
```bash
# Get Supabase credentials
SUPABASE_URL=$(supabase status | grep "API URL" | awk '{print $3}')
SUPABASE_SERVICE_KEY=$(supabase status | grep "service_role key" | awk '{print $3}')

# Create test user
curl -X POST "${SUPABASE_URL}/auth/v1/admin/users" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "sendaqmail@gmail.com",
    "password": "xasdez-katjuc-zyttI2",
    "email_confirm": true
  }'

# Should return user object with id
```

### 5. Run Investigation
```bash
# Point to local API
export PRODUCTION_API_URL="http://localhost:8000"

# Run investigation
python tests/fm_038/chat_flow_investigation.py
```

---

## 🔧 Docker Infrastructure Overview

### Services Defined in docker-compose.yml

#### API Service
```yaml
api:
  build: .                        # Uses Dockerfile in root
  ports:
    - "8000:8000"                 # Expose on localhost:8000
  environment:
    - SUPABASE_URL=http://host.docker.internal:54321
    - DATABASE_URL=postgresql://...@host.docker.internal:54322/postgres
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Worker Service
```yaml
worker:
  build: backend/workers/        # Uses workers/Dockerfile
  environment:
    # Same env vars as API
  command: python -m backend.workers.upload_processor
```

### Network Configuration
- Services connect to local Supabase via `host.docker.internal`
- API exposed on `localhost:8000`
- All services on `supabase_network_insurance_navigator` network

---

## 📋 Common Commands

### Starting Services
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api

# Start with logs visible
docker-compose up api worker
```

### Stopping Services
```bash
# Stop all services
docker-compose down

# Stop specific service
docker-compose stop api

# Stop and remove volumes
docker-compose down -v
```

### Viewing Logs
```bash
# Follow logs for all services
docker-compose logs -f

# Follow logs for specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Rebuilding
```bash
# Rebuild after code changes
docker-compose build api

# Rebuild and restart
docker-compose up -d --build api

# Full rebuild
docker-compose build --no-cache
```

### Executing Commands
```bash
# Run command in API container
docker-compose exec api python -c "print('hello')"

# Open shell in API container
docker-compose exec api bash

# Run one-off command
docker-compose run --rm api python -m pytest
```

---

## 🔍 Troubleshooting

### Issue: "Cannot connect to Docker daemon"
```bash
# Check if Docker Desktop is running
docker info

# If not, start Docker Desktop app
```

### Issue: "Port 8000 already in use"
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Issue: "Supabase connection failed"
```bash
# Check Supabase is running
supabase status

# If not started
supabase start

# Check network connectivity
ping host.docker.internal
```

### Issue: "API container exits immediately"
```bash
# Check logs for error
docker-compose logs api

# Common issues:
# - Missing environment variables
# - Python import errors
# - Port conflicts

# Try rebuilding
docker-compose build --no-cache api
docker-compose up api
```

### Issue: "Database connection error"
```bash
# Verify Supabase DB is accessible
psql "postgresql://postgres:postgres@localhost:54322/postgres"

# Check docker-compose environment
docker-compose config | grep DATABASE_URL

# Test from within container
docker-compose exec api python -c "
import os
print('DB URL:', os.getenv('DATABASE_URL'))
"
```

---

## 🎯 Environment Variables

### Required Variables
These should be in your `.env.development` file:

```bash
# Supabase (populated by `supabase start`)
SUPABASE_ANON_KEY=eyJhbG...
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...

# Security
JWT_SECRET=your-jwt-secret
DOCUMENT_ENCRYPTION_KEY=your-32-char-key

# API Keys (use real keys or mock-key for testing)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LLAMAPARSE_API_KEY=llx_...
RESEND_API_KEY=re_...
```

### Getting Supabase Keys
```bash
# After running `supabase start`
supabase status

# Look for:
# anon key: eyJhbG...
# service_role key: eyJhbG...
```

---

## 🚀 Full Workflow

### Complete Setup from Scratch
```bash
# 1. Ensure Docker is running
docker info

# 2. Start Supabase
supabase start

# 3. Get Supabase keys and update .env.development
ANON_KEY=$(supabase status | grep "anon key" | awk '{print $3}')
SERVICE_KEY=$(supabase status | grep "service_role key" | awk '{print $3}')

# 4. Build and start services
docker-compose build
docker-compose up -d api worker

# 5. Wait for services to be ready
sleep 10
curl http://localhost:8000/health

# 6. Create test user
SUPABASE_URL=$(supabase status | grep "API URL" | awk '{print $3}')
curl -X POST "${SUPABASE_URL}/auth/v1/admin/users" \
  -H "apikey: ${SERVICE_KEY}" \
  -H "Authorization: Bearer ${SERVICE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"email":"sendaqmail@gmail.com","password":"xasdez-katjuc-zyttI2","email_confirm":true}'

# 7. Run investigation
export PRODUCTION_API_URL="http://localhost:8000"
python tests/fm_038/chat_flow_investigation.py
```

### Cleanup Everything
```bash
# Stop and remove containers
docker-compose down

# Stop Supabase
supabase stop

# Remove volumes (fresh start next time)
docker-compose down -v
supabase db reset
```

---

## 📊 Monitoring Services

### Check Service Health
```bash
# API health endpoint
curl http://localhost:8000/health

# Supabase health
curl http://localhost:54321/health

# Docker service status
docker-compose ps
```

### View Resource Usage
```bash
# Container stats (live)
docker stats

# Disk usage
docker system df

# API container logs
docker-compose logs -f api | grep -E "ERROR|WARNING|INFO"
```

---

## 💡 Tips

### Development Workflow
1. Keep `docker-compose logs -f` running in one terminal
2. Run investigation script in another terminal
3. Make code changes as needed (hot reload enabled)
4. Re-run investigation to test changes

### Fast Iteration
```bash
# After code changes, API auto-reloads
# Just re-run investigation:
python tests/fm_038/chat_flow_investigation.py
```

### Clean Slate
```bash
# Complete reset
docker-compose down -v
supabase db reset
docker-compose build --no-cache
docker-compose up -d
```

---

## ✅ Verification Checklist

Before running investigation, verify:

- [ ] Docker Desktop is running
- [ ] `supabase status` shows services running
- [ ] `curl localhost:8000/health` returns success
- [ ] `docker-compose ps` shows api and worker running
- [ ] Test user exists in Supabase
- [ ] Environment variables set correctly

---

**Quick Reference:** Use `overmind start` or `./scripts/dev-start.sh` for one-command setup!

**Documentation:** See `PHASE_1_5_QUICKSTART.md` for full guide

**Status:** Ready to use with Phase 1.5 iterations

