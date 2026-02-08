# Insurance Navigator - Local Setup & Testing Guide

## 🚀 Quick Start Guide

This comprehensive guide will get your Insurance Navigator application running locally with all services properly configured and tested.

## Prerequisites

- Python 3.11+ with pip
- Node.js 18+ with npm
- Docker and Docker Compose
- Supabase CLI (`npm install -g @supabase/cli`)
- Git

## 📋 Complete Setup Process

### 1. Environment Setup

```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd insurance_navigator

# Create and activate Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Database Setup (Supabase)

```bash
# Start local Supabase instance
supabase start

# Note the output - you'll need these values:
# API URL: http://127.0.0.1:54321
# Database URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

**Expected Output:**
```
API URL: http://127.0.0.1:54321
GraphQL URL: http://127.0.0.1:54321/graphql/v1
S3 Storage URL: http://127.0.0.1:54321/storage/v1/s3
Database URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
Studio URL: http://127.0.0.1:54323
```

### 3. Environment Configuration

Verify your `.env.development` file has the correct local URLs:

```bash
# Check current environment configuration
cat .env.development | grep -E "DATABASE_URL|SUPABASE_URL"
```

**Should show:**
```
SUPABASE_URL=http://127.0.0.1:54321
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
DATABASE_URL_LOCAL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

If incorrect, update the environment variables:

```bash
# Update environment variables for local development
export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
export DATABASE_URL_LOCAL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
export SUPABASE_URL="http://127.0.0.1:54321"
```

### 4. Backend API Setup

```bash
# Start the FastAPI backend server
python main.py
```

**Expected Output:**
```
✅ Upload Pipeline Config: Loaded environment variables from .env.development
WebSocket routes included for real-time workflow updates
=== Starting server on 0.0.0.0:8000 ===
INFO:     Started server process [XXXXX]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5. Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd ui

# Install dependencies
npm install

# Start development server
npm run dev
```

**Expected Output:**
```
✓ Ready in 2.3s
✓ Local:        http://localhost:3000
✓ Network:      http://192.168.x.x:3000
```

## 🧪 Testing & Validation

### Backend Health Check

```bash
# Test API health endpoint
curl -s http://localhost:8000/health | jq '.'
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-08T06:XX:XX.XXXXXX",
  "services": {
    "database": {
      "status": "healthy",
      "healthy": true,
      "last_check": XXXXX.XXX,
      "error": null
    },
    "rag": {
      "status": "healthy",
      "healthy": true,
      "last_check": XXXXX.XXX,
      "error": null
    },
    "conversation_service": {
      "status": "healthy",
      "healthy": true,
      "last_check": null,
      "error": null
    },
    "storage_service": {
      "status": "healthy",
      "healthy": true,
      "last_check": null,
      "error": null
    }
  },
  "version": "3.0.0"
}
```

### API Endpoint Testing

```bash
# Test API documentation access
curl -s http://localhost:8000/docs | head -10
```

Should return HTML content with Swagger UI.

### Database Connectivity Test

```bash
# Check database connection
python -c "
import asyncio
import asyncpg

async def test_db():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
        result = await conn.fetchval('SELECT version()')
        print('✅ Database connected:', result[:50] + '...')
        await conn.close()
    except Exception as e:
        print('❌ Database connection failed:', e)

asyncio.run(test_db())
"
```

### Frontend Build Test

```bash
# Test frontend build process
cd ui
npm run build
```

**Expected Output:**
```
✓ Compiled successfully in X.Xs
   Linting and checking validity of types ...
```

### Comprehensive API Integration Test

```bash
# Run the comprehensive API test suite
python test_api_endpoint_direct.py
```

**Expected Output:**
```
🎉 ALL API INTEGRATION TESTS PASSED!
✅ Chat endpoint logic is working correctly
✅ UnifiedNavigatorAgent integration is complete
✅ WebSocket workflow broadcasts are functional

🚀 The API is ready for frontend integration!
```

## 🌐 Access Points

Once everything is running:

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Supabase Studio**: http://localhost:54323
- **Health Check**: http://localhost:8000/health

## 🔧 Development Workflow

### Making Code Changes

1. **Backend Changes:**
   ```bash
   # The server auto-reloads on code changes
   # Watch the terminal for any errors
   ```

2. **Frontend Changes:**
   ```bash
   # Next.js dev server auto-reloads
   # Check browser console for any errors
   ```

3. **Database Schema Changes:**
   ```bash
   # Create new migration
   supabase migration new your_migration_name
   
   # Apply migrations
   supabase db push
   ```

### Running Tests

```bash
# Backend API tests
python test_api_endpoint_direct.py

# Frontend build verification
cd ui && npm run build

# Type checking
cd ui && npm run type-check
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### 1. Database Connection Errors

**Error:** `[Errno 8] nodename nor servname provided, or not known`

**Solution:**
```bash
# Stop existing Supabase instances
supabase stop

# Start fresh
supabase start

# Update environment variables
export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
export DATABASE_URL_LOCAL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
```

#### 2. Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Find and kill process using port 3000
lsof -ti:3000 | xargs kill -9
```

#### 3. Frontend Build Failures

**Error:** TypeScript compilation errors

**Solution:**
```bash
cd ui
# Check for linting errors
npm run lint

# Fix auto-fixable issues
npm run lint:fix

# Check types specifically
npm run type-check
```

#### 4. API Import Errors

**Error:** Module import failures

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify Python path
python -c "import sys; print(sys.path)"
```

### Environment Validation Commands

```bash
# Check all required services
echo "🔍 Environment Validation"
echo "=========================="

# Python environment
echo "Python: $(python --version)"
echo "Virtual Environment: ${VIRTUAL_ENV:-'Not activated'}"

# Node environment  
echo "Node: $(node --version)"
echo "NPM: $(npm --version)"

# Docker
echo "Docker: $(docker --version)"

# Supabase
echo "Supabase CLI: $(supabase --version)"

# Check if services are running
echo -e "\n📡 Service Status"
echo "=================="

# Backend API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend API: Running"
else
    echo "❌ Backend API: Not running"
fi

# Frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend: Running"
else
    echo "❌ Frontend: Not running"
fi

# Supabase
if curl -s http://localhost:54321/health > /dev/null; then
    echo "✅ Supabase: Running"
else
    echo "❌ Supabase: Not running"
fi
```

## 🎯 Testing Scenarios

### 1. Complete User Flow Test

1. **Access Frontend**: Visit http://localhost:3000
2. **Navigate to Chat**: Go to `/chat` page
3. **Send Test Message**: Try: "What are my prescription drug benefits?"
4. **Observe Workflow**: Watch real-time status updates
5. **Verify Response**: Ensure appropriate tool selection and response

### 2. API Direct Test

```bash
# Test chat endpoint (requires authentication bypass or valid token)
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-test-token" \
  -d '{
    "message": "What does my insurance cover?",
    "conversation_id": "test-123",
    "user_language": "en"
  }'
```

### 3. WebSocket Connection Test

Open browser console on http://localhost:3000/chat and run:

```javascript
// Test WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/workflow/test-workflow-123');
ws.onopen = () => console.log('✅ WebSocket connected');
ws.onmessage = (event) => console.log('📨 Message:', JSON.parse(event.data));
ws.onerror = (error) => console.log('❌ WebSocket error:', error);
```

## 📈 Performance Monitoring

### Response Time Benchmarks

- **Health Check**: < 100ms
- **Quick Info Queries**: 30-50ms
- **Access Strategy Queries**: 1-3 seconds (includes web research)
- **RAG Queries**: 100-500ms
- **WebSocket Connection**: < 50ms

### Memory Usage

```bash
# Monitor backend memory usage
ps aux | grep python | grep main.py

# Monitor frontend build size
cd ui && npm run build && ls -lah .next/
```

## 🔄 Reset Instructions

### Complete Environment Reset

```bash
# Stop all services
supabase stop
# Kill any remaining processes
pkill -f "python main.py"
pkill -f "next-server"

# Clean and restart
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd ui
rm -rf node_modules .next
npm install

# Restart services
supabase start
# Update environment variables again
export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
export DATABASE_URL_LOCAL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
```

---

## 📝 Notes

- This setup uses local Supabase for development
- All environment variables are configured for localhost
- WebSocket connections enable real-time workflow status
- The unified navigator agent handles intelligent tool selection
- Mock mode is used for external API calls during testing

## 🎉 Success Indicators

Your local setup is fully operational when:

- ✅ All services show "healthy" in health check
- ✅ Frontend loads without console errors
- ✅ Chat interface accepts and processes messages
- ✅ Real-time workflow status updates appear
- ✅ API test suite passes completely
- ✅ Database connections are stable

**Ready to develop! 🚀**