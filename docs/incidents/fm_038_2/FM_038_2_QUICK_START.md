# FM-038-2 Investigation Quick Start Guide

## Overview
This investigation systematically tests chat flow components from lowest level (RAG tool) upward to identify the root cause of zero-chunk failures.

## Quick Start (5 Minutes)

### 1. Run Investigation Script
```bash
cd tests/fm_038
python fm_038_2_investigation.py
```

### 2. Review Results
The script will:
- Test each component in isolation
- Show success/failure for each test
- Identify where the issue occurs
- Generate a detailed report

### 3. Check Output
Look for:
- ✅ **Green checkmarks** = Component working
- ❌ **Red X marks** = Component failing
- 🎯 **Focus recommendations** = Where to investigate

## Test Sequence

The investigation runs tests in this order:

1. **RAG Tool Isolation** - Tests RAG tool directly with database
2. **Information Retrieval Agent** - Tests agent that calls RAG tool
3. **Input Processing Workflow** - Tests input handling with UserContext
4. **Supervisor Workflow** - Tests workflow prescription and routing
5. **Output Processing Workflow** - Tests response synthesis
6. **Two-Stage Synthesizer** - Tests final response generation

## Expected Outcomes

### If RAG Tool Test Fails
**Root Cause**: Database or embedding issue
**Action**: Check database connection, user data, embeddings

### If Agent Test Fails
**Root Cause**: Agent implementation issue
**Action**: Check agent methods, RAG tool integration

### If Workflow Tests Fail
**Root Cause**: Workflow configuration issue
**Action**: Check workflow setup, UserContext creation

### If All Tests Pass
**Root Cause**: Integration issue between components
**Action**: Check end-to-end flow, component handoffs

## Investigation Report

The script generates a JSON report with:
- Test results for each component
- Success/failure details
- Error messages and stack traces
- Performance metrics
- Root cause analysis

## Next Steps

After running the investigation:

1. **Review the report** to identify failing components
2. **Focus on the first failing test** - this is likely the root cause
3. **Implement fixes** for the identified issue
4. **Re-run the investigation** to verify the fix
5. **Test end-to-end** once all components pass

## Troubleshooting

### Import Errors
```bash
# Ensure you're in the project root
cd /path/to/insurance_navigator
python tests/fm_038/fm_038_2_investigation.py
```

### Environment Issues
```bash
# Check environment file
ls -la .env.production

# Load environment manually if needed
export $(cat .env.production | xargs)
```

### Database Connection Issues
- Check database credentials in `.env.production`
- Verify database is accessible
- Check user has data in the database

## Success Criteria

The investigation is successful when:
- ✅ All component tests pass
- ✅ RAG tool returns chunks for test user
- ✅ Complete chat flow works end-to-end
- ✅ Zero-chunk issue is resolved

---

**Quick Start Guide Created**: 2025-10-10  
**Investigation Script**: `fm_038_2_investigation.py`  
**Status**: Ready for execution
