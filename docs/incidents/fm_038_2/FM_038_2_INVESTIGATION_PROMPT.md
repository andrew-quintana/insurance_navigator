# FM-038-2 Investigation Prompt

## Investigation Overview

**Incident**: FM-038-2  
**Objective**: Identify root cause of zero-chunk RAG failures through systematic component isolation testing  
**Strategy**: Bottom-up testing from RAG tool to complete chat flow  
**Method**: Python script-based investigation (not notebook)

## Problem Statement

The chat endpoint is returning zero chunks for RAG operations, causing empty responses to user queries about insurance coverage. This is a critical issue affecting core functionality.

**Symptoms**:
- User queries receive empty or generic responses
- RAG operations complete successfully but return 0 chunks
- No errors in logs, suggesting silent failure in retrieval logic
- High-priority user queries are not being answered

**Impact**: 
- Users cannot get information about their insurance coverage
- Core functionality of the application is broken
- Customer satisfaction is severely impacted

## Investigation Strategy

### Testing Philosophy
1. **Start Simple**: Test lowest-level components first
2. **Isolate Issues**: Test each component independently
3. **Build Up**: Test integration between components
4. **Verify Fixes**: Re-test after each fix
5. **Document Findings**: Record all results and decisions

### Test Sequence (Bottom-Up)

The investigation tests components in this specific order:

1. **RAG Tool Isolation** - Test RAG tool directly with database
2. **Information Retrieval Agent** - Test agent that calls RAG tool
3. **Input Processing Workflow** - Test input handling with UserContext
4. **Supervisor Workflow** - Test workflow prescription and routing
5. **Output Processing Workflow** - Test response synthesis
6. **Two-Stage Synthesizer** - Test final response generation

## Execution Instructions

### Step 1: Prepare Environment

```bash
# Navigate to project root
cd /path/to/insurance_navigator

# Ensure environment file exists
ls -la .env.production

# Activate virtual environment if needed
source venv/bin/activate  # or your preferred method
```

### Step 2: Run Investigation Script

```bash
# Navigate to investigation directory
cd tests/fm_038

# Execute the investigation script
python fm_038_2_investigation.py
```

### Step 3: Monitor Execution

The script will:
- Test each component in isolation
- Show success/failure for each test
- Generate detailed logs
- Create a JSON report
- Provide root cause analysis

**Watch for**:
- ✅ **Green checkmarks** = Component working
- ❌ **Red X marks** = Component failing
- 🎯 **Focus recommendations** = Where to investigate

### Step 4: Analyze Results

After execution, review:

1. **Console Output**: Check which tests passed/failed
2. **Log File**: Review detailed logs for errors
3. **JSON Report**: Analyze structured test results
4. **Root Cause Analysis**: Follow the focus recommendations

## Test Configuration

### Test Credentials
- **User ID**: `f0cfcc46-5fdb-48c4-af13-51c6cf53e408`
- **Test Query**: `"What does my insurance cover for preventive care?"`
- **Session ID**: Generated timestamp-based ID

### Environment Requirements
- **Environment File**: `.env.production` with database credentials
- **Database**: Production Supabase database access
- **Dependencies**: All Python packages installed

## Expected Outcomes

### Scenario 1: RAG Tool Test Fails
**Root Cause**: Database or embedding issue
**Evidence**: RAG tool returns zero chunks
**Action**: 
1. Check database connection
2. Verify user has data in database
3. Check embeddings exist for user's chunks
4. Verify similarity threshold (try lowering from 0.5 to 0.3)
5. Check embedding dimensions match (should be 1536)

### Scenario 2: Agent Test Fails
**Root Cause**: Agent implementation issue
**Evidence**: Agent cannot call RAG tool or process results
**Action**:
1. Check agent methods and signatures
2. Verify RAG tool integration
3. Check agent configuration
4. Verify method availability

### Scenario 3: Workflow Tests Fail
**Root Cause**: Workflow configuration issue
**Evidence**: Workflow cannot process input or generate output
**Action**:
1. Check workflow initialization
2. Verify UserContext creation
3. Check workflow configuration
4. Verify component integration

### Scenario 4: All Tests Pass
**Root Cause**: Integration issue between components
**Evidence**: Individual components work but end-to-end fails
**Action**:
1. Check component handoffs
2. Verify data flow between components
3. Check end-to-end integration
4. Verify complete pipeline

## Success Criteria

### Component Level
- ✅ RAG tool returns chunks for test user
- ✅ Agent successfully processes RAG results
- ✅ Workflows handle input/output correctly
- ✅ Synthesizer creates final response

### Integration Level
- ✅ Components integrate correctly
- ✅ Data flows properly between components
- ✅ End-to-end pipeline works
- ✅ Zero-chunk issue resolved

### Performance Level
- ✅ Response time acceptable
- ✅ No timeouts or errors
- ✅ Consistent results across tests
- ✅ Proper error handling

## Investigation Process

### Phase 1: Execution
1. **Run Script**: Execute `fm_038_2_investigation.py`
2. **Monitor Output**: Watch for test results and errors
3. **Review Logs**: Check detailed logs for issues
4. **Analyze Report**: Review JSON report for patterns

### Phase 2: Analysis
1. **Identify Failures**: Determine which tests failed
2. **Root Cause Analysis**: Understand why tests failed
3. **Focus Area**: Determine where to investigate
4. **Action Plan**: Create specific fix plan

### Phase 3: Resolution
1. **Implement Fixes**: Address identified issues
2. **Re-test Components**: Verify fixes work
3. **Integration Testing**: Test component integration
4. **End-to-End Testing**: Test complete pipeline

### Phase 4: Validation
1. **Verify Resolution**: Confirm zero-chunk issue resolved
2. **Performance Testing**: Ensure acceptable performance
3. **Regression Testing**: Ensure no new issues introduced
4. **Documentation**: Update investigation report

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure you're in the project root
cd /path/to/insurance_navigator
python tests/fm_038/fm_038_2_investigation.py
```

#### Environment Issues
```bash
# Check environment file
ls -la .env.production

# Load environment manually if needed
export $(cat .env.production | xargs)
```

#### Database Connection Issues
- Check database credentials in `.env.production`
- Verify database is accessible
- Check user has data in the database
- Verify network connectivity

#### Permission Issues
```bash
# Make script executable
chmod +x tests/fm_038/fm_038_2_investigation.py
```

### Debugging Tips

1. **Check Logs**: Review the generated log file for detailed error information
2. **Test Individually**: Run individual test methods if needed
3. **Verify Dependencies**: Ensure all required packages are installed
4. **Check Environment**: Verify environment variables are loaded correctly

## Deliverables

### Investigation Report
- **JSON Report**: Detailed test results and metrics
- **Log File**: Complete investigation logs
- **Summary**: Executive summary of findings
- **Recommendations**: Specific action items

### Resolution Documentation
- **Root Cause**: Detailed explanation of issue
- **Fix Implementation**: How issue was resolved
- **Verification**: Proof that fix works
- **Prevention**: How to prevent recurrence

## Next Steps

### Immediate (Today)
1. **Execute Investigation**: Run the investigation script
2. **Analyze Results**: Review test results and failures
3. **Identify Root Cause**: Determine where issue occurs
4. **Create Fix Plan**: Plan specific fixes needed

### Short Term (This Week)
1. **Implement Fixes**: Address identified issues
2. **Verify Resolution**: Confirm fixes work
3. **Test Integration**: Ensure components work together
4. **Deploy Resolution**: Deploy fixes to production

### Medium Term (Next Sprint)
1. **Monitor Performance**: Ensure no regressions
2. **Document Learnings**: Record investigation process
3. **Improve Testing**: Enhance component testing
4. **Prevent Recurrence**: Implement preventive measures

## Success Metrics

The investigation is successful when:
- ✅ All component tests pass
- ✅ RAG tool returns chunks for test user
- ✅ Complete chat flow works end-to-end
- ✅ Zero-chunk issue is resolved
- ✅ Performance is acceptable
- ✅ No regressions introduced

## Risk Mitigation

### Technical Risks
- **Database Access**: Ensure production database access
- **Environment Issues**: Verify environment configuration
- **Import Errors**: Check all dependencies available
- **Timeout Issues**: Set appropriate timeouts

### Process Risks
- **Incomplete Testing**: Ensure all components tested
- **False Positives**: Verify test results are accurate
- **Missing Dependencies**: Check all imports available
- **Environment Differences**: Use production environment

## Support

For questions or issues:
1. Review the investigation plan document
2. Check the quick start guide
3. Run the investigation script
4. Analyze the generated report
5. Follow the troubleshooting section

---

**Investigation Prompt Created**: 2025-10-10  
**Status**: Ready for Execution  
**Script**: `fm_038_2_investigation.py`  
**Expected Duration**: 2-4 hours  
**Priority**: P0 - Critical
