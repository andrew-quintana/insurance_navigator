# FRACAS FM-025 Investigation Checklist

## Document Processing & Webhook System Failure

**FRACAS ID**: FM-025  
**Date**: September 30, 2025, 22:07 UTC  
**Environment**: Staging  
**Priority**: HIGH

---

## Phase 1: Initial Assessment
- [ ] **1.1** Review failure logs and error details
- [ ] **1.2** Identify affected services and components
- [ ] **1.3** Check system health and status
- [ ] **1.4** Document initial observations
- [ ] **1.5** Set up investigation workspace

**Deliverable**: Initial assessment report with system status

---

## Phase 2: Upload Worker Service Investigation
- [ ] **2.1** Check upload worker service status using Render MCP
  ```bash
  mcp_render_get_service srv-d37dlmvfte5s73b6uq0g
  ```
- [ ] **2.2** Analyze worker service logs for errors
  ```bash
  mcp_render_list_logs resource=srv-d37dlmvfte5s73b6uq0g
  ```
- [ ] **2.3** Check worker environment variables and configuration
- [ ] **2.4** Verify worker service connectivity to dependencies
- [ ] **2.5** Test worker service health endpoints

**Deliverable**: Worker service status and configuration report

---

## Phase 3: Webhook System Analysis
- [ ] **3.1** Examine webhook creation in upload pipeline
- [ ] **3.2** Check webhook URL configuration and generation
- [ ] **3.3** Verify webhook secret handling and security
- [ ] **3.4** Analyze webhook payload structure and content
- [ ] **3.5** Test webhook delivery and processing

**Deliverable**: Webhook system functionality assessment

---

## Phase 4: File Accessibility Investigation
- [ ] **4.1** Test file access from worker service perspective
- [ ] **4.2** Verify Supabase storage permissions and configuration
- [ ] **4.3** Check file path resolution and URL generation
- [ ] **4.4** Test file download and processing capabilities
- [ ] **4.5** Analyze storage bucket policies and access controls

**Deliverable**: File accessibility analysis and recommendations

---

## Phase 5: Processing Pipeline Analysis
- [ ] **5.1** Trace complete document processing workflow
- [ ] **5.2** Identify failure points in processing chain
- [ ] **5.3** Check external API dependencies (LLaParse, OpenAI)
- [ ] **5.4** Verify database connectivity and operations
- [ ] **5.5** Analyze error handling and retry mechanisms

**Deliverable**: Processing pipeline failure point identification

---

## Phase 6: Related Incident Review
- [ ] **6.1** Review FM-024 (Storage authentication) resolution
- [ ] **6.2** Check FM-023 (Database constraint) impact
- [ ] **6.3** Search for similar processing failures in incident history
- [ ] **6.4** Analyze common failure patterns across incidents
- [ ] **6.5** Identify systemic issues in upload pipeline

**Deliverable**: Related incident analysis and pattern identification

---

## Phase 7: Root Cause Analysis
- [ ] **7.1** Synthesize findings from all investigation phases
- [ ] **7.2** Identify primary root cause of document processing failure
- [ ] **7.3** Determine contributing factors and dependencies
- [ ] **7.4** Assess impact and scope of the issue
- [ ] **7.5** Document root cause with supporting evidence

**Deliverable**: Comprehensive root cause analysis report

---

## Phase 8: Solution Design
- [ ] **8.1** Develop solution options for identified root cause
- [ ] **8.2** Evaluate pros and cons of each solution option
- [ ] **8.3** Select recommended solution with justification
- [ ] **8.4** Create detailed implementation plan
- [ ] **8.5** Assess risks and mitigation strategies

**Deliverable**: Solution design and implementation plan

---

## Phase 9: Testing and Validation
- [ ] **9.1** Create test scripts for local validation
- [ ] **9.2** Test solution in local development environment
- [ ] **9.3** Validate fix resolves the identified issues
- [ ] **9.4** Run comprehensive integration tests
- [ ] **9.5** Document test results and validation

**Deliverable**: Test results and validation report

---

## Phase 10: Implementation and Monitoring
- [ ] **10.1** Deploy fix to staging environment
- [ ] **10.2** Monitor system behavior and performance
- [ ] **10.3** Verify no regression in existing functionality
- [ ] **10.4** Update monitoring and alerting systems
- [ ] **10.5** Document lessons learned and prevention measures

**Deliverable**: Implementation completion and monitoring setup

---

## Key Questions to Answer

### Service Health
- [ ] Is the upload worker service running and healthy?
- [ ] Are there any service-level errors or warnings?
- [ ] Is the worker service properly configured?

### Webhook System
- [ ] Are webhooks being created correctly?
- [ ] Is webhook delivery working as expected?
- [ ] Are webhook secrets properly handled?
- [ ] Is webhook processing functioning correctly?

### File Access
- [ ] Can the worker access files from Supabase storage?
- [ ] Are file paths being resolved correctly?
- [ ] Are storage permissions properly configured?
- [ ] Is file download working from worker context?

### Processing Pipeline
- [ ] Is the document processing pipeline properly configured?
- [ ] Are external API dependencies working?
- [ ] Is database connectivity functioning?
- [ ] Are error handling mechanisms working?

### System Integration
- [ ] Are all services communicating correctly?
- [ ] Are there configuration mismatches?
- [ ] Are there dependency failures?
- [ ] Is the overall system architecture sound?

---

## Investigation Tools and Commands

### Render MCP Commands
```bash
# Check service status
mcp_render_get_service srv-d37dlmvfte5s73b6uq0g

# Get service logs
mcp_render_list_logs resource=srv-d37dlmvfte5s73b6uq0g

# Check service metrics
mcp_render_get_metrics resourceId=srv-d37dlmvfte5s73b6uq0g metricTypes=["cpu_usage","memory_usage","instance_count"]
```

### Supabase MCP Commands
```bash
# Check database tables
mcp_supabase_production_list_tables schemas=["upload_pipeline"]

# Query upload jobs
mcp_supabase_production_execute_sql query="SELECT * FROM upload_pipeline.upload_jobs WHERE status = 'failed_parse' ORDER BY created_at DESC LIMIT 10"

# Check storage buckets
mcp_supabase_production_execute_sql query="SELECT * FROM storage.buckets"
```

### Local Testing Commands
```bash
# Start local environment
cd /Users/aq_home/1Projects/accessa/insurance_navigator
source .venv/bin/activate
supabase start
python main.py

# Start worker locally
python -m backend.workers.upload_worker

# Test processing pipeline
python test_processing_pipeline.py
```

---

## Progress Tracking

**Investigation Started**: [Date/Time]  
**Phase 1 Completed**: [Date/Time]  
**Phase 2 Completed**: [Date/Time]  
**Phase 3 Completed**: [Date/Time]  
**Phase 4 Completed**: [Date/Time]  
**Phase 5 Completed**: [Date/Time]  
**Phase 6 Completed**: [Date/Time]  
**Phase 7 Completed**: [Date/Time]  
**Phase 8 Completed**: [Date/Time]  
**Phase 9 Completed**: [Date/Time]  
**Phase 10 Completed**: [Date/Time]  

**Investigation Completed**: [Date/Time]  
**Resolution Deployed**: [Date/Time]  
**Monitoring Active**: [Date/Time]

---

## Notes and Observations

### Key Findings
- [ ] Finding 1: [Description]
- [ ] Finding 2: [Description]
- [ ] Finding 3: [Description]

### Critical Issues Identified
- [ ] Issue 1: [Description]
- [ ] Issue 2: [Description]
- [ ] Issue 3: [Description]

### Recommendations
- [ ] Recommendation 1: [Description]
- [ ] Recommendation 2: [Description]
- [ ] Recommendation 3: [Description]

---

**Investigator**: [Name]  
**Reviewer**: [Name]  
**Approval**: [Name]  
**Date**: [Date]
