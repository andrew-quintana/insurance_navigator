# FM-027 Real-Time Testing and Investigation Plan

## Mission Objective
**Real-time monitoring and analysis of the FM-027 Phase 2 Upload Pipeline Worker to identify the exact cause of 400 Bad Request errors using comprehensive logging.**

## Testing Scope

### 1. **Real-Time Log Monitoring**
- Monitor Render worker logs in real-time during test uploads
- Filter for FM-027 logs to capture comprehensive debugging information
- Track complete data flow from webhook reception to LlamaParse API calls

### 2. **Data Flow Analysis**
- **Webhook Reception**: Headers, body, URL, client information
- **Job Processing**: Database queries, document details, storage paths
- **Storage Operations**: File content analysis, binary data validation
- **LlamaParse API**: Request preparation, file content analysis, API calls
- **Response Analysis**: Status codes, headers, response bodies, error details

### 3. **Error Investigation**
- Identify exact failure points in the pipeline
- Analyze 400 Bad Request error responses
- Determine root cause of environment-specific issues
- Validate fixes for binary file reading and HEAD vs GET requests

## Testing Execution Plan

### Phase 1: Pre-Test Monitoring Setup
- [x] Verify comprehensive logging is active
- [x] Confirm worker is running with FM-027 logs
- [x] Validate all environment variables are loaded
- [x] Ensure storage and database connections are ready

### Phase 2: Real-Time Monitoring
- [ ] Monitor logs during test upload
- [ ] Capture webhook reception details
- [ ] Track job processing flow
- [ ] Analyze storage operations
- [ ] Monitor LlamaParse API calls
- [ ] Document any errors with complete context

### Phase 3: Analysis and Reporting
- [ ] Analyze captured log data
- [ ] Identify root cause of 400 errors
- [ ] Document findings and recommendations
- [ ] Implement targeted fixes if needed

## Expected Outcomes

### Success Criteria
1. **Complete visibility** into the upload pipeline data flow
2. **Root cause identification** of 400 Bad Request errors
3. **Validation** of binary file reading fixes
4. **Confirmation** of HEAD vs GET request fixes
5. **Documentation** of any remaining issues

### Deliverables
1. **Real-time log analysis** during test uploads
2. **Comprehensive error investigation** with complete context
3. **Root cause analysis** with specific recommendations
4. **Testing report** with findings and next steps

## Monitoring Tools and Methods

### MCP Render Tools
- `mcp_render_list_logs` - Real-time log monitoring
- `mcp_render_get_service` - Service status verification
- `mcp_render_list_deploys` - Deployment status tracking

### Log Analysis Focus
- **FM-027 prefixed logs** for comprehensive debugging
- **Webhook logs** for request reception analysis
- **Storage logs** for file operations validation
- **LlamaParse logs** for API call analysis
- **Error logs** for failure point identification

## Test Execution Status

**Status**: 🟡 **READY FOR EXECUTION**  
**Next Action**: Begin real-time monitoring during test upload  
**Expected Duration**: 5-10 minutes per test upload  
**Monitoring Window**: Continuous until root cause identified

---

*This testing plan provides comprehensive monitoring and analysis of the FM-027 Phase 2 Upload Pipeline Worker to identify and resolve the 400 Bad Request errors.*

