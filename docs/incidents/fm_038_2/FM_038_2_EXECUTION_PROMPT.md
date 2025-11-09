# FM-038-2 Investigation Execution Prompt

## Task: Execute FM-038-2 Investigation

You are tasked with executing a systematic investigation to identify the root cause of zero-chunk RAG failures in the chat flow.

### Problem
Chat endpoint returns zero chunks for RAG operations, causing empty responses to user queries about insurance coverage. No errors in logs, suggesting silent failure in retrieval logic.

### Investigation Strategy
**Bottom-up component isolation testing** - Test components from lowest level (RAG tool) upward through the agent hierarchy.

### Execution Steps

#### 1. Prepare Environment
```bash
cd /Users/aq_home/1Projects/accessa/insurance_navigator
ls -la .env.production  # Verify environment file exists
```

#### 2. Run Investigation Script
```bash
cd tests/fm_038
python fm_038_2_investigation.py
```

#### 3. Monitor Execution
The script will test these components in order:
1. **RAG Tool Isolation** - Test RAG tool directly with database
2. **Information Retrieval Agent** - Test agent that calls RAG tool
3. **Input Processing Workflow** - Test input handling with UserContext
4. **Supervisor Workflow** - Test workflow prescription and routing
5. **Output Processing Workflow** - Test response synthesis
6. **Two-Stage Synthesizer** - Test final response generation

#### 4. Analyze Results
Look for:
- ✅ **Green checkmarks** = Component working
- ❌ **Red X marks** = Component failing
- 🎯 **Focus recommendations** = Where to investigate

### Test Configuration
- **User ID**: `f0cfcc46-5fdb-48c4-af13-51c6cf53e408`
- **Test Query**: `"What does my insurance cover for preventive care?"`
- **Database**: Production Supabase database

### Expected Outcomes

#### If RAG Tool Test Fails
**Root Cause**: Database or embedding issue
**Action**: Check database connection, user data, embeddings, similarity threshold

#### If Agent Test Fails
**Root Cause**: Agent implementation issue
**Action**: Check agent methods, RAG tool integration

#### If Workflow Tests Fail
**Root Cause**: Workflow configuration issue
**Action**: Check workflow setup, UserContext creation

#### If All Tests Pass
**Root Cause**: Integration issue between components
**Action**: Check end-to-end flow, component handoffs

### Success Criteria
- ✅ RAG tool returns chunks for test user
- ✅ Agent successfully processes RAG results
- ✅ Workflows handle input/output correctly
- ✅ Synthesizer creates final response
- ✅ Complete chat flow works end-to-end
- ✅ Zero-chunk issue resolved

### Deliverables
1. **Investigation Report**: JSON report with test results
2. **Log File**: Detailed investigation logs
3. **Root Cause Analysis**: Identification of failure point
4. **Fix Plan**: Specific actions to resolve the issue

### Next Steps After Investigation
1. **Implement Fixes**: Address identified issues
2. **Verify Resolution**: Confirm fixes work
3. **Test Integration**: Ensure components work together
4. **Deploy Resolution**: Deploy fixes to production

### Troubleshooting
- **Import Errors**: Ensure you're in project root
- **Environment Issues**: Check `.env.production` file
- **Database Issues**: Verify database credentials and connectivity
- **Permission Issues**: Make script executable with `chmod +x`

### Expected Duration
2-4 hours for complete investigation and resolution

---

**Execute this investigation now to identify and resolve the zero-chunk RAG failure issue.**
