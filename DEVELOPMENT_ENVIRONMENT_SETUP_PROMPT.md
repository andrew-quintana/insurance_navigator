# Development Environment Setup and Testing Prompt

## Context
You are tasked with setting up a fully functional local development environment for the Insurance Navigator project and ensuring the complete document processing pipeline works end-to-end. The current production system has several issues that need to be resolved through local development and testing.

## Current Issues Identified

### 1. **Critical: Supabase Storage URL Issue**
- **Problem**: Production API generates signed URLs using `storage.supabase.co` (unresolvable) instead of correct URL
- **Impact**: Blocks entire document processing pipeline
- **Status**: Code fixes applied but not deployed

### 2. **Database Connection Issues**
- **Problem**: Local backend fails to start due to missing Supabase environment variables
- **Error**: `SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set`
- **Impact**: Cannot test locally

### 3. **Service Initialization Issues**
- **Problem**: RAG tools, chat service, and document service not properly initialized
- **Errors**: 
  - "RAG tool not available"
  - "Chat service temporarily unavailable - missing required components"
  - "DocumentService.__init__() missing 1 required positional argument: 'supabase_client'"

### 4. **Missing Chunk Generation**
- **Problem**: No chunks are being generated in the database
- **Root Cause**: Document processing pipeline fails at content upload step

## Required Setup

### 1. **Local Supabase Instance**
```bash
# Install and start local Supabase
npx supabase start
# This will provide:
# - Database on port 54322
# - API on port 54321
# - Required environment variables
```

### 2. **Environment Configuration**
Create `.env.development` with:
```env
# Supabase Local Instance
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_ROLE_KEY=***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
SUPABASE_STORAGE_URL=http://127.0.0.1:54321

# Database
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres

***REMOVED*** (use your actual keys)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
LLAMAPARSE_API_KEY=your_llamaparse_key_here
```

### 3. **Database Schema Setup**
```bash
# Run database migrations
supabase db reset
# Or manually run the migration files in supabase/migrations/
```

## Testing Requirements

### 1. **Complete Pipeline Test**
Create a test that verifies:
1. ✅ User creation and authentication
2. ✅ Document upload initiation
3. ✅ Document content upload to local storage
4. ✅ Worker processing of document
5. ✅ Chunk generation and storage
6. ✅ RAG search functionality
7. ✅ Chat responses with deductible information
8. ✅ Similarity scores above 0.3 threshold

### 2. **Test Data**
Use realistic insurance policy content:
```
INSURANCE POLICY DOCUMENT
Policy Number: TEST-12345
Policyholder: test@example.com

COVERAGE DETAILS
- Annual Maximum: $1,000,000
- Deductible: $2,500 per year
- Coinsurance: 20% after deductible
- Office Visit Copay: $25
- Emergency Room Copay: $200

DENTAL COVERAGE
- Annual Maximum: $50,000
- Deductible: $500 per year
- Preventive Care: 100% covered

VISION COVERAGE
- Annual Maximum: $25,000
- Eye Exam: $25 copay
```

### 3. **Expected Test Results**
- Document uploads successfully to local storage
- Worker processes document and generates chunks
- RAG search returns relevant chunks with similarity > 0.3
- Chat responds with: "Your deductible is $2,500 per year"

## Implementation Steps

### Step 1: Environment Setup
1. Install and start local Supabase instance
2. Configure environment variables
3. Run database migrations
4. Verify database connectivity

### Step 2: Backend Startup
1. Start local backend with correct environment variables
2. Verify all services initialize properly
3. Check worker service is operational
4. Test health endpoints

### Step 3: Pipeline Testing
1. Create comprehensive end-to-end test
2. Test user creation and authentication
3. Test document upload and processing
4. Verify chunk generation
5. Test RAG search functionality
6. Test chat responses

### Step 4: Debug and Fix Issues
1. Identify any remaining service initialization issues
2. Fix RAG tool availability
3. Resolve chat service component issues
4. Fix DocumentService initialization

### Step 5: Performance Validation
1. Measure chunk generation time
2. Test RAG search performance
3. Verify similarity score accuracy
4. Test with multiple documents

## Success Criteria

### ✅ **Must Work**
- Local backend starts without errors
- Document upload completes successfully
- Chunks are generated and stored in database
- RAG search returns relevant results
- Chat responds with correct deductible information

### ✅ **Performance Targets**
- Document processing completes within 30 seconds
- RAG search returns results within 2 seconds
- Similarity scores are above 0.3 for relevant content
- System handles multiple concurrent users

### ✅ **Quality Assurance**
- All tests pass consistently
- Error handling works properly
- Logging provides clear debugging information
- System is stable under load

## Files to Focus On

### **Critical Files**
- `main.py` - Main application entry point
- `config/database.py` - Database configuration
- `api/upload_pipeline/endpoints/upload.py` - Upload endpoint
- `backend/workers/enhanced_base_worker.py` - Worker service
- `agents/tooling/rag/core.py` - RAG functionality

### **Test Files to Create**
- `test_local_pipeline_complete.py` - End-to-end pipeline test
- `test_chunk_generation.py` - Chunk generation verification
- `test_rag_search.py` - RAG search functionality test
- `test_chat_responses.py` - Chat response validation

## Debugging Tools

### **Database Inspection**
```python
# Check for chunks in database
async def check_chunks():
    conn = await asyncpg.connect(DATABASE_URL)
    chunks = await conn.fetch("SELECT * FROM upload_pipeline.document_chunks LIMIT 10")
    print(f"Found {len(chunks)} chunks")
```

### **Worker Status**
```python
# Check worker status
async def check_worker():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/api/v1/status") as response:
            status = await response.json()
            print(f"Worker status: {status}")
```

### **Storage Verification**
```python
# Check if files are uploaded to storage
async def check_storage():
    # Verify files exist in local Supabase storage
    # Check signed URL generation
    # Validate file upload process
```

## Expected Timeline

- **Setup**: 30 minutes
- **Initial Testing**: 45 minutes
- **Debug and Fix**: 60 minutes
- **Final Validation**: 30 minutes
- **Total**: ~3 hours

## Success Metrics

1. **Pipeline Completion**: 100% of test documents process successfully
2. **Chunk Generation**: Average 5-10 chunks per document
3. **RAG Accuracy**: >80% of queries return relevant results
4. **Response Time**: <2 seconds for RAG search, <5 seconds for chat
5. **Similarity Scores**: >0.3 for relevant content, <0.1 for irrelevant

## Notes

- Use local Supabase for faster iteration
- Enable detailed logging for debugging
- Test with realistic insurance policy content
- Verify all environment variables are set correctly
- Check database schema matches application expectations
- Ensure worker service can access all required services

The goal is to have a fully functional local development environment where the complete document processing pipeline works reliably, allowing for rapid development and testing of new features.
