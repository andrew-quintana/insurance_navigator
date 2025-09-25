# Staging Environment Setup and Validation Prompt

## 🎯 **Mission**
Set up and validate the staging environment for the Insurance Navigator application, ensuring all components are properly deployed and functional before manual testing.

## 🚨 **Current Status**
- **Development Environment**: ✅ Fully functional with successful document processing and chat interface
- **Git Status**: ✅ All fixes committed and pushed to both development and staging branches
- **Key Fixes Applied**: Environment variable loading, LlamaParse API authentication, chat configuration, and storage access issues resolved

## 📋 **Setup and Validation Tasks**

### **Task 1: Environment Preparation (P0 - Critical)**
**Time Estimate**: 15 minutes

**Objective**: Ensure staging environment has all necessary configuration and dependencies.

**Steps**:
1. **Verify Environment Variables**:
   - Confirm `.env.staging` file exists with all required variables
   - Validate `SUPABASE_SERVICE_ROLE_KEY`, `LLAMACLOUD_API_KEY`, `ELEVENLABS_API_KEY`, `FLASH_API_KEY`
   - Check `SUPABASE_URL`, `DATABASE_URL`, `OPENAI_API_KEY` are properly set

2. **Database Setup**:
   - Ensure Supabase staging instance is running and accessible
   - Verify database migrations are applied
   - Confirm storage buckets are properly configured

3. **External Service Configuration**:
   - Validate LlamaParse API key format (`llx-...` format)
   - Confirm OpenAI API key is valid
   - Test translation service API keys (ElevenLabs/Flash)

**Expected Output**:
- All environment variables properly configured
- Database connection successful
- External API keys validated

### **Task 2: Service Deployment and Startup (P0 - Critical)**
**Time Estimate**: 20 minutes

**Objective**: Deploy and start all staging services successfully.

**Steps**:
1. **API Server Deployment**:
   ```bash
   export ENVIRONMENT=staging
   python main.py
   ```
   - Verify server starts without configuration errors
   - Confirm all services initialize properly
   - Check for any missing dependencies or environment issues

2. **Worker Process Deployment**:
   ```bash
   export ENVIRONMENT=staging
   python backend/workers/enhanced_runner.py
   ```
   - Validate worker starts with correct configuration
   - Confirm environment variable validation passes
   - Verify database and storage connections

3. **Frontend Deployment** (if applicable):
   - Deploy frontend to staging environment
   - Verify build process completes successfully
   - Confirm all environment variables are properly injected

**Expected Output**:
- API server running on staging port (typically 8000)
- Worker process running and polling for jobs
- Frontend accessible via staging URL
- No startup errors or configuration failures

### **Task 3: Core Functionality Validation (P0 - Critical)**
**Time Estimate**: 25 minutes

**Objective**: Test all critical functionality to ensure staging environment works correctly.

**Steps**:
1. **Authentication Testing**:
   ```bash
   # Test login endpoint
   curl -X POST http://staging-url/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "testpassword123"}'
   ```
   - Verify JWT token generation
   - Confirm authentication works properly

2. **Document Upload Pipeline Testing**:
   ```bash
   # Test upload endpoint
   curl -X POST http://staging-url/api/upload-pipeline/upload \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <JWT_TOKEN>" \
     -d '{
       "filename": "test_document.pdf",
       "sha256": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
       "size": 1024,
       "content_type": "application/pdf"
     }'
   ```
   - Verify upload creates job successfully
   - Confirm signed URL generation works
   - Test file upload to storage

3. **Document Processing Testing**:
   - Upload a test PDF document
   - Monitor worker logs for processing
   - Verify LlamaParse API integration works
   - Confirm document parsing completes successfully
   - Check embeddings generation and storage

4. **Chat Interface Testing**:
   ```bash
   # Test chat endpoint
   curl -X POST http://staging-url/chat \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <JWT_TOKEN>" \
     -d '{
       "conversation_id": "test-conv-123",
       "message": "Hello, what is your purpose?",
       "user_id": "test-user-123"
     }'
   ```
   - Verify chat interface responds correctly
   - Confirm no configuration validation errors
   - Test basic conversation flow

**Expected Output**:
- All API endpoints respond correctly
- Document processing pipeline works end-to-end
- Chat interface functions without errors
- No authentication or configuration issues

### **Task 4: Error Handling and Edge Case Testing (P1 - High)**
**Time Estimate**: 15 minutes

**Objective**: Validate error handling and edge cases work properly in staging.

**Steps**:
1. **Invalid Authentication Testing**:
   - Test with invalid JWT tokens
   - Verify proper error responses
   - Confirm security measures work

2. **Invalid Document Testing**:
   - Upload non-PDF files
   - Test with corrupted documents
   - Verify appropriate error messages

3. **Missing Environment Variables Testing**:
   - Temporarily remove critical environment variables
   - Verify fail-fast behavior works
   - Confirm clear error messages

4. **Rate Limiting Testing**:
   - Test API rate limits
   - Verify proper throttling behavior
   - Confirm system stability under load

**Expected Output**:
- Proper error handling for all edge cases
- Clear, user-friendly error messages
- System remains stable under error conditions

### **Task 5: Performance and Monitoring Validation (P1 - High)**
**Time Estimate**: 10 minutes

**Objective**: Ensure staging environment performs adequately and monitoring works.

**Steps**:
1. **Performance Testing**:
   - Measure API response times
   - Test document processing speed
   - Verify memory usage is reasonable

2. **Monitoring Validation**:
   - Check health monitoring endpoints
   - Verify logging is working properly
   - Confirm error tracking is functional

3. **Resource Usage**:
   - Monitor CPU and memory usage
   - Check database connection pools
   - Verify external API usage

**Expected Output**:
- Acceptable performance metrics
- Monitoring systems functional
- Resource usage within expected ranges

## 🔍 **Validation Checklist**

### **Pre-Deployment Checklist**:
- [ ] Environment variables configured correctly
- [ ] Database migrations applied
- [ ] External API keys validated
- [ ] Dependencies installed and up-to-date

### **Post-Deployment Checklist**:
- [ ] API server starts without errors
- [ ] Worker process initializes successfully
- [ ] Frontend builds and deploys correctly
- [ ] All services communicate properly

### **Functionality Checklist**:
- [ ] Authentication works correctly
- [ ] Document upload pipeline functional
- [ ] Document processing completes successfully
- [ ] Chat interface responds properly
- [ ] Error handling works as expected

### **Performance Checklist**:
- [ ] API response times acceptable (< 2s for most requests)
- [ ] Document processing completes within reasonable time
- [ ] Memory usage stable
- [ ] No memory leaks detected

## 🚨 **Critical Success Criteria**

1. **Zero Configuration Errors**: All services start without environment variable or configuration issues
2. **End-to-End Functionality**: Complete document processing pipeline works from upload to chat
3. **Error Handling**: Proper error messages and graceful failure handling
4. **Performance**: System responds within acceptable time limits
5. **Monitoring**: Health checks and logging work correctly

## 📊 **Expected Test Results**

### **API Endpoints**:
- `/auth/login`: 200 OK with JWT token
- `/api/upload-pipeline/upload`: 200 OK with job creation
- `/chat`: 200 OK with proper response
- Health endpoints: 200 OK

### **Document Processing**:
- Upload: Successful job creation
- Processing: LlamaParse API integration works
- Storage: Files stored correctly
- Embeddings: Generated and stored successfully

### **Chat Interface**:
- Configuration: No validation errors
- Response: Proper AI-generated responses
- Performance: Response time < 15 seconds

## 🔧 **Troubleshooting Guide**

### **Common Issues**:
1. **Environment Variable Errors**: Check `.env.staging` file and ensure all required variables are set
2. **Database Connection Issues**: Verify Supabase staging instance is running and accessible
3. **API Key Errors**: Validate external API keys are correct and have proper permissions
4. **Worker Startup Issues**: Check worker logs for specific error messages

### **Debug Commands**:
```bash
# Check environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.staging'); print([k for k in os.environ.keys() if 'SUPABASE' in k or 'LLAMA' in k or 'ELEVEN' in k or 'FLASH' in k])"

# Test database connection
python -c "from core.database import get_database; print('Database connection test:', get_database())"

# Validate API keys
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.staging'); print('LLAMACLOUD_API_KEY format:', os.getenv('LLAMACLOUD_API_KEY', 'NOT_SET')[:10] + '...')"
```

## 📝 **Documentation Requirements**

1. **Deployment Log**: Record all deployment steps and any issues encountered
2. **Test Results**: Document all test results and performance metrics
3. **Configuration Notes**: Note any staging-specific configuration changes
4. **Known Issues**: Document any limitations or known issues in staging
5. **Manual Testing Guide**: Provide clear instructions for manual testing

## ⏱️ **Estimated Total Time**: 85 minutes

## 🎯 **Success Definition**
Staging environment is fully functional, all critical features work correctly, and the system is ready for comprehensive manual testing by the development team.

---

**Note**: This prompt assumes the staging environment follows the same architecture as development but with staging-specific configuration. Adjust URLs, ports, and environment-specific settings as needed for your actual staging setup.
