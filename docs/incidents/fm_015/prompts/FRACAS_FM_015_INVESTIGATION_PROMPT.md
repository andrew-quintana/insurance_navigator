# FRACAS FM-015 Investigation Prompt: End-to-End Workflow Database Constraint Violation

## 🎯 **INVESTIGATION MISSION**

**Objective**: Investigate and resolve the database constraint violation preventing end-to-end workflow completion in the staging environment.

**Reference Document**: `docs/incidents/fm_015/docs/FRACAS_FM_015_DATABASE_CONSTRAINT_VIOLATION.md`

## 🚨 **CURRENT SITUATION**

### **Critical Issue**
- **Status**: Medium Priority (Active Investigation)
- **Impact**: End-to-end workflow testing blocked in staging environment
- **Error**: `new row for relation "upload_jobs" violates check constraint "ck_upload_jobs_status"`
- **Root Cause**: Database constraint violation during job creation

### **Evidence Summary**
```
Error: new row for relation "upload_jobs" violates check constraint "ck_upload_jobs_status"
DETAIL: Failing row contains (558bf8ff-f47c-4833-a7ff-183a61d84d74, 2eae1bdf-90cb-4105-8011-1479173fe4ce, working, 0, null, 2025-09-25 17:42:18.511656+00, 2025-09-25 17:42:18.511656+00, parsing, {"test": true, "stage": "parsing"}, null, markdown-simple@1, text-embedding-3-small, 1).
```

## 🔍 **INVESTIGATION TASKS**

### **Task 1: Database Schema Analysis (P1 - High)**
**Time Estimate**: 30 minutes

**Objective**: Understand the database constraint and its requirements.

**Investigation Steps**:
1. Connect to staging database and examine the `upload_jobs` table schema
2. Identify the `ck_upload_jobs_status` check constraint definition
3. Determine valid values for the `status` field
4. Compare current constraint with expected values in the failing row
5. Check if constraint was recently modified or if data format changed

**Expected Output**:
- Database schema documentation for `upload_jobs` table
- Constraint definition and valid status values
- Analysis of why "working" status violates the constraint
- Identification of correct status values to use

### **Task 2: Code Analysis - Job Creation Logic (P1 - High)**
**Time Estimate**: 25 minutes

**Objective**: Review the code that creates upload jobs and identify where the invalid status is being set.

**Investigation Steps**:
1. Search codebase for job creation logic in upload pipeline
2. Identify where the "working" status is being set
3. Review the job status state machine and valid transitions
4. Check if there are multiple places setting job status
5. Verify if the status field mapping is correct

**Expected Output**:
- Code locations where job status is set
- Analysis of status value assignment logic
- Identification of the source of the "working" status
- Understanding of the intended status flow

### **Task 3: Database Constraint History Analysis (P2 - Medium)**
**Time Estimate**: 20 minutes

**Objective**: Understand when and why the constraint was created or modified.

**Investigation Steps**:
1. Check database migration history for `upload_jobs` table
2. Look for recent changes to the constraint definition
3. Review any recent schema updates or migrations
4. Check if this is a new constraint or modified existing one
5. Identify if constraint changes align with code changes

**Expected Output**:
- Migration history for the constraint
- Timeline of when constraint was added/modified
- Analysis of whether constraint changes are intentional
- Identification of any recent breaking changes

### **Task 4: Test Data Analysis (P2 - Medium)**
**Time Estimate**: 15 minutes

**Objective**: Analyze the failing test data to understand the context and expected behavior.

**Investigation Steps**:
1. Examine the failing row data in detail
2. Identify what each field represents and its expected value
3. Check if the test data is realistic or artificially generated
4. Verify if the test is using correct status values
5. Determine if this is a test-specific issue or general problem

**Expected Output**:
- Analysis of the failing row data
- Understanding of test data generation
- Identification of whether issue is test-specific or general
- Recommendations for test data correction

### **Task 5: Fix Implementation (P1 - High)**
**Time Estimate**: 30 minutes

**Objective**: Implement the fix for the database constraint violation.

**Implementation Requirements**:
1. Update job creation code to use correct status values
2. Ensure status transitions follow the constraint requirements
3. Update any test data generation to use valid statuses
4. Add validation to prevent future constraint violations
5. Test the fix with the failing scenario

**Code Changes Needed**:
- Fix status value assignment in job creation logic
- Update test data generation if needed
- Add status validation before database insertion
- Ensure all status transitions are valid

**Success Criteria**:
- End-to-end workflow test passes without constraint violations
- All job status values comply with database constraints
- No regression in existing functionality
- Proper error handling for invalid status values

## 🧪 **TEST COMMANDS**

```bash
# Test 1: Connect to staging database and check constraint
psql "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres" -c "
SELECT conname, consrc 
FROM pg_constraint 
WHERE conname = 'ck_upload_jobs_status';"

# Test 2: Check upload_jobs table schema
psql "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres" -c "
\d upload_pipeline.upload_jobs"

# Test 3: Check valid status values
psql "postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres" -c "
SELECT DISTINCT status FROM upload_pipeline.upload_jobs;"

# Test 4: Test the failing scenario
python scripts/test_staging_communication.py

# Test 5: Test with corrected status values
python -c "
import asyncio
import asyncpg
from datetime import datetime

async def test_job_creation():
    conn = await asyncpg.connect('postgresql://postgres:beqhar-qincyg-Syxxi8@db.your-project.supabase.co:5432/postgres')
    
    # Test with different status values
    test_statuses = ['pending', 'queued', 'processing', 'completed', 'failed']
    
    for status in test_statuses:
        try:
            await conn.execute('''
                INSERT INTO upload_pipeline.upload_jobs 
                (job_id, document_id, status, priority, created_at, updated_at, processing_stage, job_data, error_message, parser_type, embedding_model, retry_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ''', 
            'test-job-id', 'test-doc-id', status, 0, datetime.utcnow(), datetime.utcnow(), 
            'parsing', '{\"test\": true}', None, 'markdown-simple@1', 'text-embedding-3-small', 1)
            print(f'✅ Status \"{status}\" is valid')
        except Exception as e:
            print(f'❌ Status \"{status}\" failed: {e}')
    
    await conn.close()

asyncio.run(test_job_creation())
"
```

## 📋 **EXPECTED OUTPUT**

### **Immediate Fix (P0)**
1. **Root Cause**: Clear understanding of why "working" status violates the constraint
2. **Database Schema**: Complete documentation of valid status values
3. **Code Fix**: Updated job creation logic with correct status values

### **Short-term Improvements (P1)**
1. **Validation**: Add status validation before database insertion
2. **Testing**: Update test data generation to use valid statuses
3. **Documentation**: Document the correct status flow and constraints

### **Long-term Improvements (P2)**
1. **Monitoring**: Add monitoring for constraint violations
2. **Error Handling**: Improve error messages for constraint violations
3. **Schema Management**: Better schema versioning and migration management

### **Success Metrics**
- ✅ End-to-end workflow test passes without constraint violations
- ✅ All job status values comply with database constraints
- ✅ Clear documentation of valid status values
- ✅ Proper error handling for invalid statuses
- ✅ No regression in existing functionality

## 📄 **DELIVERABLES**

1. **FRACAS Documentation**: Create `docs/incidents/fm_015/docs/FRACAS_FM_015_DATABASE_CONSTRAINT_VIOLATION.md` with complete analysis
2. **Code Fix**: Implement corrected job creation logic
3. **Database Analysis**: Document constraint requirements and valid values
4. **Testing**: Verify fix with end-to-end workflow test
5. **Documentation**: Update status flow documentation

## ⚠️ **CRITICAL NOTES**

- **Database Access**: Requires access to staging database
- **Constraint Understanding**: Must understand the exact constraint requirements
- **Status Flow**: Need to map the intended status flow to constraint requirements
- **Testing**: Must test with realistic scenarios, not just unit tests

## 🚨 **ESCALATION CRITERIA**

- If database constraint cannot be understood or modified
- If fixing the constraint requires breaking changes to existing data
- If the issue affects production environment
- If multiple constraints are involved in the violation

## ⏱️ **ESTIMATED DURATION**
- **Total Time**: 120 minutes
- **Investigation**: 60 minutes
- **Implementation**: 45 minutes
- **Testing**: 15 minutes

---

**Reference**: See `docs/incidents/fm_015/docs/FRACAS_FM_015_DATABASE_CONSTRAINT_VIOLATION.md` for complete failure details
