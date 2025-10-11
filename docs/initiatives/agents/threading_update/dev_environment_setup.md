# Development Environment Setup Guide

## Overview

This guide provides instructions for setting up the development environment for the Threading Update Initiative. The development environment should already be deployed, but this guide serves as a reference for troubleshooting and setup.

## Prerequisites

### System Requirements
- **OS**: macOS (Darwin 24.6.0)
- **Python**: 3.9+ (Anaconda environment)
- **Docker**: Docker Desktop running
- **Git**: For version control

### Required Services
- **Supabase**: Local Docker containers
- **PostgreSQL**: Database running on port 54322
- **Redis**: For caching (if used)

## Environment Setup

### 1. Check Current Status

**Verify Docker containers are running:**
```bash
docker ps
```

**Expected containers:**
- `supabase_db` (PostgreSQL on port 54322)
- `supabase_studio` (Supabase Studio)
- `supabase_auth` (Supabase Auth)
- `supabase_rest` (Supabase REST API)

### 2. Start Development Environment

**If containers are not running:**
```bash
# Start Supabase containers
cd /Users/aq_home/1Projects/accessa/insurance_navigator
docker-compose up -d
```

**Wait for services to be ready:**
```bash
# Check if database is accessible
psql postgresql://postgres:postgres@localhost:54322/postgres -c "SELECT 1;"
```

### 3. Environment Variables

**Check environment variables:**
```bash
# Load development environment
export ENVIRONMENT=development
export OPENAI_API_KEY=$(python -c "from config.environment_loader import load_environment; print(load_environment().get('OPENAI_API_KEY'))")
export ANTHROPIC_API_KEY=$(python -c "from config.environment_loader import load_environment; print(load_environment().get('ANTHROPIC_API_KEY'))")
```

**Verify API keys:**
```bash
echo "OpenAI API Key: ${OPENAI_API_KEY:0:10}..."
echo "Anthropic API Key: ${ANTHROPIC_API_KEY:0:10}..."
```

### 4. Start the Server

**Start the development server:**
```bash
python main.py
```

**Expected output:**
```
Environment loaded: development on local (cloud: False)
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5. Verify Server Health

**Test health endpoint:**
```bash
curl -s http://localhost:8000/health | jq .
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-10T18:33:29.216Z",
  "services": {
    "database": "healthy",
    "rag_service": "healthy",
    "memory_usage": "healthy"
  }
}
```

## Testing the Current Implementation

### 1. Test Single Request

**Login to get auth token:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "sendaqmail@gmail.com", "password": "xasdez-katjuc-zyttI2"}' \
  --max-time 10
```

**Test chat endpoint:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"message": "What is my deductible?"}' \
  --max-time 30
```

### 2. Test Concurrent Requests

**Create test script:**
```bash
cat > test_concurrent.py << 'EOF'
import asyncio
import aiohttp
import time

async def test_concurrent_requests():
    # Get auth token
    async with aiohttp.ClientSession() as session:
        login_data = {
            "email": "sendaqmail@gmail.com",
            "password": "xasdez-katjuc-zyttI2"
        }
        
        async with session.post("http://localhost:8000/auth/login", json=login_data) as response:
            if response.status == 200:
                token_data = await response.json()
                token = token_data["access_token"]
            else:
                print(f"Login failed: {response.status}")
                return
    
    # Test concurrent requests
    async def make_request(session, token, request_id):
        headers = {"Authorization": f"Bearer {token}"}
        data = {"message": f"Test request {request_id}: What is my deductible?"}
        
        start_time = time.time()
        try:
            async with session.post("http://localhost:8000/chat", headers=headers, json=data) as response:
                end_time = time.time()
                if response.status == 200:
                    result = await response.json()
                    print(f"Request {request_id}: SUCCESS ({end_time - start_time:.2f}s)")
                    return True
                else:
                    print(f"Request {request_id}: FAILED ({response.status})")
                    return False
        except Exception as e:
            end_time = time.time()
            print(f"Request {request_id}: ERROR ({end_time - start_time:.2f}s) - {e}")
            return False
    
    # Test with increasing concurrency
    for num_requests in [1, 2, 3, 5, 10]:
        print(f"\n=== Testing {num_requests} concurrent requests ===")
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                make_request(session, token, i+1) 
                for i in range(num_requests)
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            success_count = sum(1 for r in results if r is True)
            print(f"Results: {success_count}/{num_requests} successful in {end_time - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_concurrent_requests())
EOF
```

**Run concurrent test:**
```bash
python test_concurrent.py
```

**Expected results:**
- 1 request: SUCCESS (~14s)
- 2-3 requests: SUCCESS (~38s)
- 5+ requests: TIMEOUT/HANGING (current issue)

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
**Error**: `[Errno 48] error while attempting to bind on address ('0.0.0.0', 8000): address already in use`

**Solution**:
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or find and kill manually
ps aux | grep python | grep main.py
kill -9 <PID>
```

#### 2. Database Connection Refused
**Error**: `ConnectionRefusedError: [Errno 61] Connection refused`

**Solution**:
```bash
# Check if Docker is running
docker ps

# Start Supabase containers
docker-compose up -d

# Wait for database to be ready
sleep 10
psql postgresql://postgres:postgres@localhost:54322/postgres -c "SELECT 1;"
```

#### 3. API Key Issues
**Error**: `OPENAI_API_KEY not found` or `401 Unauthorized`

**Solution**:
```bash
# Check environment variables
cat .env.development | grep API_KEY

# Reload environment
export OPENAI_API_KEY=$(python -c "from config.environment_loader import load_environment; print(load_environment().get('OPENAI_API_KEY'))")
export ANTHROPIC_API_KEY=$(python -c "from config.environment_loader import load_environment; print(load_environment().get('ANTHROPIC_API_KEY'))")
```

#### 4. Memory Issues
**Error**: `Health Check Failed: memory_usage`

**Solution**:
```bash
# Check memory usage
top -l 1 | grep python

# Restart server if needed
pkill -f "python main.py"
python main.py
```

### Debug Commands

**Check server logs:**
```bash
# View real-time logs
tail -f logs/app.log

# Or check console output
python main.py 2>&1 | tee server.log
```

**Test specific endpoints:**
```bash
# Health check
curl -s http://localhost:8000/health

# Debug environment
curl -s http://localhost:8000/debug-env

# Debug RAG similarity
curl -s "http://localhost:8000/debug/rag-similarity/f0cfcc46-5fdb-48c4-af13-51c6cf53e408?query=test&threshold=0.4"
```

## Development Workflow

### 1. Making Changes

**Create feature branch:**
```bash
git checkout -b feature/threading-update
```

**Make changes to code:**
```bash
# Edit files
vim agents/tooling/rag/core.py

# Test changes
python main.py
```

**Test changes:**
```bash
# Run concurrent test
python test_concurrent.py

# Check logs for errors
tail -f logs/app.log
```

### 2. Committing Changes

**Stage changes:**
```bash
git add agents/tooling/rag/core.py
git add docs/initiatives/agents/threading_update/
```

**Commit with signature:**
```bash
git commit -S -m "feat: implement async RAG embedding generation

- Replace manual threading with async/await patterns
- Add connection pooling with aiohttp
- Implement concurrency control with asyncio.Semaphore
- Simplify error handling and timeout management
- Resolves hanging failures with concurrent requests"
```

**Push to remote:**
```bash
git push origin feature/threading-update
```

### 3. Testing in Production

**After local testing:**
1. Create pull request
2. Wait for review approval
3. Merge to main
4. Deploy to production
5. Monitor production logs

## Monitoring and Logs

### Key Log Messages

**Successful startup:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**RAG operations:**
```
RAGTool - INFO - Successfully generated embedding: 1536 dimensions
RAGObservability - INFO - RAG Operation SUCCESS
```

**Health checks:**
```
RAGTool - INFO - Using configurable threshold 0.25 for user health_check
```

### Performance Monitoring

**Response times:**
- Single request: ~14s
- 2-3 concurrent: ~38s
- 5+ concurrent: Should not hang

**Resource usage:**
- Memory: Monitor for leaks
- CPU: Should be reasonable
- Connections: Should be pooled

## Next Steps

1. **Verify Environment**: Ensure development environment is working
2. **Test Current Implementation**: Run concurrent tests to confirm hanging issue
3. **Begin Implementation**: Start with Phase 2 implementation
4. **Test Incrementally**: Test each change before moving to next
5. **Monitor Performance**: Track metrics throughout implementation

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Supabase Local Development](https://supabase.com/docs/guides/cli/local-development)
- [FastAPI Development](https://fastapi.tiangolo.com/tutorial/)
- [Python Async Testing](https://docs.python.org/3/library/asyncio.html)
