# Manual Testing Guide - Insurance Navigator

## 🎯 **Current System State**

### **Services Running:**
- **API Server**: `http://localhost:8000` (PID: 70652)
- **Worker Service**: `http://localhost:8001` (PID: 57420)
- **Database**: Supabase (production) with `upload_pipeline` schema

### **Authentication:**
- **Test User**: `upload_test@example.com`
- **Password**: `UploadTest123!`
- **Access Token**: Use `/login` endpoint to get fresh token

## 🔧 **Testing Infrastructure**

### **Monitoring Tools:**
```bash
# Monitor both services
python monitor_logs.py

# Check API server logs
tail -f logs/api_server.log

# Check worker service logs  
tail -f logs/worker_service.log
```

### **Health Checks:**
```bash
# API Server
curl http://localhost:8000/health

# Worker Service
curl http://localhost:8001/health

# Resilience Systems
curl http://localhost:8000/debug-resilience
```

## 📊 **Known Failure Modes & Root Causes**

### **1. Schema Issues (RESOLVED)**
- **Problem**: Document status endpoint returning "Document not found"
- **Root Cause**: Supabase client not configured with `upload_pipeline` schema
- **Solution**: Implemented direct database queries bypassing Supabase client
- **Status**: ✅ Fixed

### **2. Authentication Token Expiration**
- **Problem**: 401 Unauthorized responses
- **Root Cause**: JWT tokens expire after 1 hour
- **Solution**: Refresh token using `/login` endpoint
- **Status**: ⚠️ Expected behavior

### **3. API Server Startup Hanging**
- **Problem**: Server hangs during initialization
- **Root Cause**: Service initialization dependencies and configuration loading
- **Solution**: Restart with proper environment variables
- **Status**: ⚠️ Intermittent

### **4. Database Connection Issues**
- **Problem**: Worker service database connection failures
- **Root Cause**: SSL configuration and environment variable loading
- **Solution**: Dynamic SSL configuration for local development
- **Status**: ✅ Fixed

### **5. Content Deduplication (NEW FEATURE)**
- **Problem**: Different users uploading same content causing duplicate processing
- **Root Cause**: No content deduplication mechanism
- **Solution**: Implemented content deduplication that copies processed data from existing documents
- **Status**: ✅ Implemented and tested

## 🧪 **Testing Procedures**

### **Upload Pipeline Test:**
```bash
# 1. Get fresh token
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "upload_test@example.com", "password": "UploadTest123!"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. Create upload
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"filename": "test.pdf", "bytes_len": 1024000, "mime": "application/pdf", "sha256": "test_hash", "ocr": false}'

# 3. Check document status
curl -X GET "http://localhost:8000/documents/{document_id}/status" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### **Chat Interface Test:**
```bash
# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"message": "Test message", "user_id": "test_user"}'
```

### **Content Deduplication Test:**
```bash
# Test content deduplication with same content hash
# 1. Upload with user 1
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "filename": "test_dedup.pdf",
    "bytes_len": 1000,
    "mime": "application/pdf",
    "sha256": "dedup_test_hash_12345678901234567890123456789012",
    "ocr": false
  }'

# 2. Upload same content with different user (should trigger deduplication)
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test_dedup.pdf",
    "bytes_len": 1000,
    "mime": "application/pdf",
    "sha256": "dedup_test_hash_12345678901234567890123456789012",
    "ocr": false
  }'

# 3. Check logs for deduplication activity
tail -f logs/api_server.log | grep -E "(deduplication|Content deduplication|Copying processed data)"
```

## 🐛 **Debugging Commands**

### **Database Queries:**
```bash
# Check documents
python -c "
import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('.env.production')
async def check():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    docs = await conn.fetch('SELECT * FROM upload_pipeline.documents ORDER BY created_at DESC LIMIT 5')
    for doc in docs:
        print(f'{doc[\"document_id\"]} - {doc[\"filename\"]} - {doc[\"processing_status\"]}')
    await conn.close()
asyncio.run(check())
"
```

### **Service Status:**
```bash
# Check running processes
ps aux | grep -E "(python.*main.py|upload_pipeline)" | grep -v grep

# Check port usage
lsof -i :8000
lsof -i :8001
```

## 📝 **Testing Checklist**

### **Before Testing:**
- [ ] Both services running and healthy
- [ ] Fresh authentication token obtained
- [ ] Log monitoring active
- [ ] Database connectivity confirmed

### **During Testing:**
- [ ] Monitor logs for errors
- [ ] Verify database persistence
- [ ] Check response times
- [ ] Test error scenarios

### **After Testing:**
- [ ] Document any new failure modes
- [ ] Update root cause analysis
- [ ] Record test results
- [ ] Note any system improvements needed

## 🚨 **Emergency Procedures**

### **Service Restart:**
```bash
# Stop services
pkill -f "python.*main.py"
pkill -f "upload_pipeline"

# Start API server
ENVIRONMENT=development python main.py > logs/api_server.log 2>&1 &

# Start worker service
DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres?sslmode=disable" \
python -m uvicorn api.upload_pipeline.main:app --host 0.0.0.0 --port 8001 --log-level info > logs/worker_service.log 2>&1 &
```

### **Database Reset (if needed):**
```bash
# Connect to database and check tables
python -c "
import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('.env.production')
async def check():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    tables = await conn.fetch('SELECT table_name FROM information_schema.tables WHERE table_schema = \'upload_pipeline\'')
    print('Tables:', [t['table_name'] for t in tables])
    await conn.close()
asyncio.run(check())
"
```

## 📈 **Success Metrics**

- **Upload Success Rate**: >99%
- **Document Processing Time**: <5 seconds
- **API Response Time**: <2 seconds
- **Error Rate**: <1%
- **Database Persistence**: 100%

---

**Last Updated**: $(date)
**System Version**: Phase 3 Production Ready
**Testing Status**: Active Manual Testing
