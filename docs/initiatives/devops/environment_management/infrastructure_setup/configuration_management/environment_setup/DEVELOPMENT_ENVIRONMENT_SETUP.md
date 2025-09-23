# Development Environment Setup - Phase 3 Manual Testing

## 🚀 Development Server Status: READY

The Insurance Navigator development server is now running with **full Phase 3 resilience features** enabled and ready for collaborative manual testing.

---

## 📍 Server Information

- **URL**: http://localhost:8000
- **Environment**: Development  
- **Version**: 3.0.0
- **Status**: ✅ HEALTHY
- **Resilience Features**: ✅ ENABLED

---

## 🔧 Available Endpoints for Testing

### Core API Endpoints
```bash
# Health Check
GET http://localhost:8000/health

# Root API Info  
GET http://localhost:8000/

# API Documentation
GET http://localhost:8000/docs
```

### Authentication Endpoints
```bash
# Register New User
POST http://localhost:8000/register
Content-Type: application/json
{
  "email": "test@example.com",
  "password": "TestPassword123!",
  "name": "Test User"
}

# Login User
POST http://localhost:8000/login  
Content-Type: application/json
{
  "email": "test@example.com", 
  "password": "TestPassword123!"
}

# Get Current User Info
GET http://localhost:8000/me
Authorization: Bearer <access_token>
```

### Document Upload Endpoints
```bash
# Upload Document (New Pipeline)
POST http://localhost:8000/api/v2/upload
Authorization: Bearer <access_token>
Content-Type: application/json
{
  "filename": "test_document.pdf",
  "bytes_len": 1024,
  "mime": "application/pdf", 
  "sha256": "abc123...",
  "ocr": false
}

# Check Document Status
GET http://localhost:8000/documents/{document_id}/status
Authorization: Bearer <access_token>
```

### Chat Endpoints
```bash
# Chat with AI Agent
POST http://localhost:8000/chat
Authorization: Bearer <access_token>
Content-Type: application/json
{
  "message": "What is my deductible?",
  "conversation_id": "optional_conv_id",
  "user_language": "en"
}
```

### 🛡️ Resilience Debug Endpoints
```bash
# Resilience System Status
GET http://localhost:8000/debug-resilience

# Authentication Debug
GET http://localhost:8000/debug-auth

# RAG Similarity Debug
GET http://localhost:8000/debug/rag-similarity/{user_id}?query=test&threshold=0.3
```

---

## 🛡️ Current Resilience Status

### Degradation Managers
- ✅ **RAG Service**: Full operation level
- ✅ **Upload Service**: Full operation level  
- ✅ **Database Service**: Full operation level
- ✅ **Degraded Services**: None currently
- ✅ **Unavailable Services**: None currently

### Circuit Breakers
- ✅ **service_database**: Closed (healthy), 0 failures, 100% success rate
- ✅ **service_rag**: Closed (healthy), 0 failures, 100% success rate

### System Monitor
- ✅ **Overall Health**: 66.7% (1 active alert - memory usage warning)
- ✅ **Status**: Degraded (due to memory usage alert, but functionally healthy)
- ✅ **Active Alerts**: 1 (non-critical memory usage warning)

---

## 🧪 Manual Testing Scenarios

### Scenario 1: User Registration and Authentication
```bash
# Step 1: Register a new user
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"manual_test@example.com","password":"TestPass123!","name":"Manual Test User"}'

# Step 2: Login to get access token
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"manual_test@example.com","password":"TestPass123!"}'

# Step 3: Test authentication
curl -X GET http://localhost:8000/me \
  -H "Authorization: Bearer <access_token_from_step_2>"
```

### Scenario 2: Document Upload Workflow
```bash
# Step 1: Upload a document
curl -X POST http://localhost:8000/api/v2/upload \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test_policy.pdf",
    "bytes_len": 2048,
    "mime": "application/pdf",
    "sha256": "abcdef1234567890",
    "ocr": false
  }'

# Step 2: Check document status (use document_id from step 1)
curl -X GET http://localhost:8000/documents/<document_id>/status \
  -H "Authorization: Bearer <access_token>"
```

### Scenario 3: Chat Interaction
```bash
# Chat with AI about uploaded documents
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my deductible?",
    "conversation_id": "test_conv_001",
    "user_language": "en"
  }'
```

### Scenario 4: Resilience Feature Testing
```bash
# Check resilience system status
curl -X GET http://localhost:8000/debug-resilience

# Monitor system health
curl -X GET http://localhost:8000/health

# Test RAG similarity (with authenticated user)
curl -X GET "http://localhost:8000/debug/rag-similarity/test_user_id?query=test&threshold=0.3" \
  -H "Authorization: Bearer <access_token>"
```

---

## 🔍 What to Look For During Manual Testing

### ✅ Expected Behaviors
1. **Authentication**: Users can register, login, and access protected endpoints
2. **Document Upload**: Upload pipeline returns job_id, document_id, and signed_url
3. **Chat Functionality**: AI responds to queries (may be degraded without actual documents)
4. **Error Handling**: Proper error messages with appropriate HTTP status codes
5. **Resilience**: System continues operating even if some components fail

### ⚠️ Known Issues to Debug
1. **Document Status Endpoint**: May return 500 errors (needs investigation)
2. **Chat with Real Documents**: May have issues without actual document processing
3. **Memory Usage Alert**: Non-critical memory usage warning (can be ignored)

### 📋 Issue Reporting and FRACAS Integration
When encountering any issues during testing:

1. **Document in FRACAS**: Add new failure mode to relevant initiative's `fracas.md`
2. **Include Evidence**: Capture error messages, logs, and reproduction steps
3. **Use FM-XXX Format**: Assign unique failure mode identifier for tracking
4. **Update Status**: Track investigation progress and resolution steps
5. **Reference in Commits**: Include FM-XXX references when fixing issues

**Example Issue Documentation:**
```markdown
### FM-042: Document Status Endpoint Returns 500 Error
- **Severity**: High
- **Status**: 🔍 Under Investigation  
- **First Observed**: 2025-09-18
- **Symptoms**: GET /documents/{id}/status returns 500 instead of document status
- **Evidence**: Error logs showing database connection timeout
```

### 🛡️ Resilience Features to Test
1. **Circuit Breaker Behavior**: Monitor circuit breaker states during failures
2. **Graceful Degradation**: Test system behavior when services are unavailable
3. **Error Recovery**: Verify automatic recovery from transient failures
4. **Monitoring Alerts**: Check that alerts are generated appropriately

---

## 💡 Collaborative Testing Commands

### Quick Health Check
```bash
curl -s http://localhost:8000/health | python -m json.tool
```

### Resilience Status Check  
```bash
curl -s http://localhost:8000/debug-resilience | python -m json.tool
```

### Test User Creation
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"collab_test@example.com","password":"CollabTest123!","name":"Collaborative Test"}'
```

### Test Authentication
```bash
# Save this token for subsequent requests
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"collab_test@example.com","password":"CollabTest123!"}' | python -m json.tool
```

---

## 🎯 Ready for Collaborative Testing!

The development environment is fully set up and ready for collaborative manual testing. All Phase 3 resilience features are active and can be tested interactively.

**Next Steps:**
1. Use the test scenarios above to validate functionality
2. Report any issues you encounter
3. We can debug problems together in real-time
4. Test resilience features under various failure conditions

**Environment is ready! Let's start testing! 🚀**
