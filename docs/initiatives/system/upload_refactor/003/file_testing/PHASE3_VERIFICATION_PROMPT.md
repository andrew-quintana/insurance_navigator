# PHASE 3: Database Flow Verification and Processing Outcomes

## Objective
Verify the complete database flow from upload initiation through all processing stages, ensuring every database table captures and processes the upload data correctly with proper relationships and state transitions.

## Context
Phase 2.1 successfully validated the upload endpoint and file storage. Now Phase 3 focuses on the **database processing pipeline** - how each database table processes the upload data, maintains relationships, and tracks the complete lifecycle of uploaded documents.

## Prerequisites
- ✅ Phase 2.1 completed: Upload endpoint working, files stored in Supabase
- ✅ JWT authentication working correctly
- ✅ Environment configuration validated (development mode)
- ✅ Test document successfully uploaded and stored

## Core Focus: Database Processing Flow

### 1. Database Schema Flow Verification
Track the complete data flow through every database table:

#### Primary Flow Path
```
Upload Request → Documents Table → Upload Jobs Table → Events Table → Processing State
```

#### Secondary Flow Paths
```
User Authentication → User Sessions → Access Logs
File Storage → Storage Metadata → Bucket References
Job Processing → Worker Assignments → Status Updates
```

### 2. Table-by-Table Processing Verification

#### A. Documents Table (`upload_pipeline.documents`)
**Purpose**: Master record of uploaded documents
**Verification Tasks**:
- [ ] Document record created with correct metadata
- [ ] All required fields populated (document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path)
- [ ] Timestamps accurate (created_at, updated_at)
- [ ] File path follows expected naming convention
- [ ] SHA256 hash matches actual file content
- [ ] File size matches actual file size

**Expected Processing**:
- Record created immediately upon upload acceptance
- Status: "uploaded" or "pending_processing"
- Raw path points to actual Supabase storage location

#### B. Upload Jobs Table (`upload_pipeline.upload_jobs`)
**Purpose**: Processing queue and job lifecycle management
**Verification Tasks**:
- [ ] Job record created with correct document_id linkage
- [ ] Job payload contains complete upload metadata
- [ ] Initial state: "queued" or "pending"
- [ ] Progress field populated with job details
- [ ] Retry count initialized to 0
- [ ] Correlation ID generated for tracking

**Expected Processing**:
- Job created immediately after document record
- Links to document via document_id foreign key
- Contains enhanced payload with processing requirements
- Ready for worker pickup

#### C. Events Table (`upload_pipeline.events`)
**Purpose**: Audit trail and processing history
**Verification Tasks**:
- [ ] UPLOAD_ACCEPTED event logged
- [ ] Event payload contains upload metadata
- [ ] Correlation ID matches job correlation ID
- [ ] Timestamps accurate and sequential
- [ ] Event severity and type appropriate
- [ ] Job and document IDs properly linked

**Expected Processing**:
- Event logged for every state change
- Payload contains relevant context data
- Maintains complete processing history

#### D. User Sessions/Authentication Tables
**Purpose**: Track user authentication and access
**Verification Tasks**:
- [ ] User authentication recorded
- [ ] Session information captured
- [ ] Access permissions validated
- [ ] User ID properly linked across tables

#### E. Storage Metadata Tables (if applicable)
**Purpose**: Track file storage and bucket information
**Verification Tasks**:
- [ ] Storage location recorded
- [ ] Bucket references maintained
- [ ] File accessibility tracked
- [ ] Storage paths validated

### 3. Cross-Table Relationship Verification

#### Primary Relationships
- [ ] `documents.document_id` ↔ `upload_jobs.document_id`
- [ ] `upload_jobs.job_id` ↔ `events.job_id`
- [ ] `documents.user_id` ↔ `upload_jobs.user_id`
- [ ] `upload_jobs.correlation_id` ↔ `events.correlation_id`

#### Data Consistency Checks
- [ ] All foreign key relationships valid
- [ ] Referential integrity maintained
- [ ] No orphaned records
- [ ] Timestamps logically consistent

### 4. Processing State Validation

#### Expected State Progression
```
Upload → Document Created → Job Queued → Event Logged → Ready for Processing
```

#### State Verification
- [ ] Document status: "uploaded" or "pending_processing"
- [ ] Job status: "queued" or "pending"
- [ ] Event type: "UPLOAD_ACCEPTED"
- [ ] All timestamps within expected ranges
- [ ] No processing errors or failed states

### 5. Data Integrity Verification

#### Metadata Accuracy
- [ ] File size matches actual file size exactly
- [ ] SHA256 hash matches file content
- [ ] MIME type correctly identified
- [ ] Filename preserved accurately
- [ ] User ID matches authenticated user

#### Processing Metadata
- [ ] Job payload contains all required fields
- [ ] Event payloads contain relevant context
- [ ] Correlation IDs unique and traceable
- [ ] Timestamps accurate and sequential

### 6. Performance and Capacity Verification

#### Processing Metrics
- [ ] Document creation time < 100ms
- [ ] Job creation time < 50ms
- [ ] Event logging time < 25ms
- [ ] Total database processing < 200ms

#### Capacity Verification
- [ ] Large files (>2MB) processed correctly
- [ ] Multiple concurrent uploads handled
- [ ] Database connection pool working
- [ ] No memory leaks or connection issues

## Database Connection and Tools

### Connection Details
- **Database**: PostgreSQL via Supabase
- **Schema**: `upload_pipeline`
- **Access**: Service role key for admin access
- **Connection**: From UPLOAD_PIPELINE_SUPABASE_URL

### Required Queries

#### 1. Document Verification Query
```sql
SELECT 
    d.document_id,
    d.user_id,
    d.filename,
    d.mime,
    d.bytes_len,
    d.file_sha256,
    d.raw_path,
    d.created_at,
    d.updated_at
FROM upload_pipeline.documents d
WHERE d.document_id = '[ACTUAL_DOCUMENT_ID]'
ORDER BY d.created_at DESC;
```

#### 2. Job Verification Query
```sql
SELECT 
    j.job_id,
    j.document_id,
    j.user_id,
    j.stage,
    j.state,
    j.payload,
    j.created_at,
    j.updated_at
FROM upload_pipeline.upload_jobs j
WHERE j.document_id = '[ACTUAL_DOCUMENT_ID]'
ORDER BY j.created_at DESC;
```

#### 3. Event Verification Query
```sql
SELECT 
    e.event_id,
    e.job_id,
    e.document_id,
    e.type,
    e.severity,
    e.payload,
    e.correlation_id,
    e.ts
FROM upload_pipeline.events e
WHERE e.job_id = '[ACTUAL_JOB_ID]'
ORDER BY e.ts DESC;
```

#### 4. Cross-Reference Verification Query
```sql
SELECT 
    d.document_id,
    d.filename,
    d.raw_path,
    j.job_id,
    j.state,
    j.stage,
    e.type as event_type,
    e.ts as event_time
FROM upload_pipeline.documents d
LEFT JOIN upload_pipeline.upload_jobs j ON d.document_id = j.document_id
LEFT JOIN upload_pipeline.events e ON j.job_id = e.job_id
WHERE d.document_id = '[ACTUAL_DOCUMENT_ID]'
ORDER BY e.ts DESC;
```

## Success Criteria

### Database Processing Success
- [ ] All required tables populated correctly
- [ ] Foreign key relationships maintained
- [ ] Data integrity preserved (no corruption)
- [ ] Processing state progression correct
- [ ] All metadata accurately captured

### Performance Success
- [ ] Processing times within acceptable limits
- [ ] No database connection issues
- [ ] No memory or capacity problems
- [ ] Concurrent processing working

### Traceability Success
- [ ] Complete audit trail maintained
- [ ] All processing steps logged
- [ ] Correlation IDs traceable end-to-end
- [ ] No missing or orphaned records

## Output Required

### 1. Database Processing Report
- Complete query results for all tables
- State progression verification
- Relationship validation results
- Performance metrics

### 2. Data Flow Analysis
- Complete traceability matrix
- Processing pipeline validation
- Error state analysis (if any)
- Capacity and performance assessment

### 3. Issues and Recommendations
- Any processing anomalies discovered
- Performance bottlenecks identified
- Data integrity issues found
- Recommendations for improvement

## Troubleshooting

### Common Issues
- **Missing Records**: Check database permissions and connection
- **Relationship Failures**: Verify foreign key constraints
- **Performance Issues**: Check connection pool and indexing
- **State Inconsistencies**: Verify processing logic

### Debugging Steps
1. Check database connection and permissions
2. Verify table schema and constraints
3. Review processing logic and state machines
4. Check for transaction rollbacks or failures
5. Validate correlation ID generation

## Next Phase
Once database flow verification is complete, proceed to Phase 4: Visual Inspection and Stakeholder Verification to provide human-readable access to the processed data.