# FRACAS FM-025 Investigation Package

## Document Processing & Webhook System Failure

**FRACAS ID**: FM-025  
**Date**: September 30, 2025, 22:07 UTC  
**Environment**: Staging  
**Severity**: High  
**Status**: Under Investigation

---

## Quick Start Guide

### 1. Read the Investigation Prompt
Start with `investigation_prompt.md` for:
- Detailed failure description
- Root cause analysis requirements
- Technical context and evidence
- Success criteria and deliverables

### 2. Follow the Investigation Checklist
Use `investigation_checklist.md` for:
- Step-by-step investigation process
- 10 phases of systematic analysis
- Progress tracking and deliverables
- Key questions to answer

### 3. Use the Investigation Tools
Leverage available tools for:
- Render MCP for service inspection
- Supabase MCP for database queries
- Local testing environment
- Test scripts and validation

---

## Failure Summary

### What Happened
The upload pipeline is experiencing document processing failures after successful file uploads. Documents are being queued for processing but failing with "Document file is not accessible for processing" errors.

### Impact
- ✅ File uploads work (FM-024 resolved)
- ✅ Storage authentication working
- ❌ Document processing failing
- ❌ User-facing error messages
- ❌ No RAG functionality available

### Error Details
```json
{
  "job_id": "f3d824bd-7be8-4686-a437-7bdb5f7ab595",
  "document_id": "2f064818-4568-5ca2-ad05-e26484d8f1c4",
  "status": "failed_parse",
  "last_error": "Non-retryable error: user_facing_error: Document file is not accessible for processing. Please try uploading again. (Reference: 76421768-7eb0-45e7-8fb6-27001206b1df)"
}
```

---

## Investigation Focus Areas

### 1. Upload Worker Service
- **Service ID**: `srv-d37dlmvfte5s73b6uq0g`
- **Focus**: Service health, configuration, logs
- **Tools**: Render MCP, service inspection

### 2. Webhook System
- **Focus**: Webhook creation, delivery, processing
- **Key Questions**: Are webhooks working correctly?
- **Tools**: Log analysis, webhook testing

### 3. File Accessibility
- **Focus**: Can worker access files from storage?
- **Key Questions**: Storage permissions, file paths
- **Tools**: Supabase MCP, file access testing

### 4. Processing Pipeline
- **Focus**: Document processing workflow
- **Key Questions**: Where does processing fail?
- **Tools**: End-to-end testing, pipeline analysis

---

## Related Incidents

### FM-024: Storage Authentication (RESOLVED)
- **Issue**: Storage signature verification failed
- **Resolution**: Configured storage buckets, updated service role keys
- **Potential Impact**: May have introduced new processing issues

### FM-023: Database Constraint (RESOLVED)
- **Issue**: Database constraint violation
- **Resolution**: Updated status values in code
- **Potential Impact**: May have affected job processing logic

---

## Investigation Tools

### Render MCP Commands
```bash
# Check worker service
mcp_render_get_service srv-d37dlmvfte5s73b6uq0g

# Get worker logs
mcp_render_list_logs resource=srv-d37dlmvfte5s73b6uq0g

# Check metrics
mcp_render_get_metrics resourceId=srv-d37dlmvfte5s73b6uq0g metricTypes=["cpu_usage","memory_usage"]
```

### Supabase MCP Commands
```bash
# Query failed jobs
mcp_supabase_production_execute_sql query="SELECT * FROM upload_pipeline.upload_jobs WHERE status = 'failed_parse' ORDER BY created_at DESC LIMIT 10"

# Check storage buckets
mcp_supabase_production_execute_sql query="SELECT * FROM storage.buckets"
```

### Local Testing
```bash
# Start local environment
cd /Users/aq_home/1Projects/accessa/insurance_navigator
source .venv/bin/activate
supabase start
python main.py

# Test processing pipeline
python test_processing_pipeline.py
```

---

## Key Questions to Answer

1. **Is the upload worker service running and healthy?**
2. **Are webhooks being created and delivered correctly?**
3. **Can the worker access files from Supabase storage?**
4. **Are there configuration mismatches between services?**
5. **Is the processing pipeline properly configured?**
6. **Are there dependency failures (external APIs, database)?**

---

## Success Criteria

### Investigation Complete When:
- [ ] Root cause identified and documented
- [ ] Worker service configuration understood
- [ ] Webhook system status verified
- [ ] File accessibility issues identified
- [ ] Related incidents analyzed
- [ ] Recommended solution identified
- [ ] Implementation plan created
- [ ] Prevention measures defined

### Resolution Complete When:
- [ ] Document processing works end-to-end
- [ ] Webhook system functions correctly
- [ ] No user-facing errors occur
- [ ] All tests pass
- [ ] Staging deployment successful
- [ ] Monitoring in place
- [ ] Documentation updated

---

## Files in This Package

- **`investigation_prompt.md`** - Comprehensive investigation prompt
- **`investigation_checklist.md`** - Step-by-step investigation checklist
- **`README.md`** - This overview and quick start guide

---

## Next Steps

1. **Start Investigation**: Begin with Phase 1 of the checklist
2. **Gather Evidence**: Use available tools to collect data
3. **Analyze Findings**: Synthesize information to identify root cause
4. **Develop Solution**: Create and test fix
5. **Deploy and Monitor**: Implement solution and verify resolution

---

**Investigation Priority**: HIGH  
**Estimated Time**: 3-6 hours  
**Testing Requirement**: MANDATORY local testing before staging deployment
