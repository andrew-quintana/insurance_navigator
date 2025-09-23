# FRACAS Investigation Prompt: Worker Database Schema Missing

## 🚨 **CRITICAL INCIDENT - IMMEDIATE ACTION REQUIRED**

### **Incident Summary**
The enhanced base worker is experiencing complete failure due to missing database schema. All document processing has stopped, affecting core system functionality.

**FRACAS ID**: WORKER-SCHEMA-MISSING-001  
**Severity**: CRITICAL  
**Status**: INVESTIGATING  

---

## **FRACAS INVESTIGATION FLOW**

### **Phase 1: Immediate Assessment (0-15 minutes)**

#### **1.1 System Status Check**
```bash
# Check worker service status
docker ps | grep worker
kubectl get pods | grep worker

# Check worker logs for current errors
docker logs <worker_container_id> --tail 100
kubectl logs <worker_pod_name> --tail 100
```

#### **1.2 Database Connectivity Test**
```bash
# Test database connection from worker environment
psql $DATABASE_URL -c "SELECT version();"

# Check if we can connect to the database at all
psql $DATABASE_URL -c "\\l"
```

#### **1.3 Schema Verification**
```sql
-- Connect to production database and check schema
\c postgres
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'upload_pipeline';

-- If schema exists, check tables
\c postgres
\dn upload_pipeline
SELECT table_name FROM information_schema.tables WHERE table_schema = 'upload_pipeline';
```

### **Phase 2: Root Cause Analysis (15-30 minutes)**

#### **2.1 Database Schema Investigation**
```sql
-- Check if upload_pipeline schema exists
SELECT 
    schema_name,
    schema_owner
FROM information_schema.schemata 
WHERE schema_name = 'upload_pipeline';

-- Check all tables in upload_pipeline schema
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'upload_pipeline'
ORDER BY table_name;

-- Check for any tables that might be in wrong schema
SELECT 
    table_schema,
    table_name
FROM information_schema.tables 
WHERE table_name IN ('document_chunks', 'upload_jobs', 'documents')
ORDER BY table_schema, table_name;
```

#### **2.2 Migration Status Check**
```bash
# Check if there are migration files
find . -name "*.sql" -path "*/migrations/*" | grep -i upload
find . -name "*.sql" -path "*/supabase/*" | grep -i upload

# Check migration history if available
psql $DATABASE_URL -c "SELECT * FROM schema_migrations;" 2>/dev/null || echo "No migration table found"
```

#### **2.3 Environment Configuration Check**
```bash
# Check environment variables
echo "DATABASE_URL: $DATABASE_URL"
echo "SUPABASE_DB_HOST: $SUPABASE_DB_HOST"
echo "SUPABASE_DB_NAME: $SUPABASE_DB_NAME"

# Check if we're connecting to the right database
psql $DATABASE_URL -c "SELECT current_database(), current_user;"
```

### **Phase 3: Immediate Resolution (30-60 minutes)**

#### **3.1 Create Missing Schema (If Schema Missing)**
```sql
-- Create upload_pipeline schema
CREATE SCHEMA IF NOT EXISTS upload_pipeline;

-- Grant permissions
GRANT USAGE ON SCHEMA upload_pipeline TO postgres;
GRANT CREATE ON SCHEMA upload_pipeline TO postgres;
```

#### **3.2 Create Missing Tables (If Tables Missing)**
```sql
-- Create upload_jobs table
CREATE TABLE IF NOT EXISTS upload_pipeline.upload_jobs (
    job_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    document_id UUID,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    error_message TEXT,
    metadata JSONB
);

-- Create documents table
CREATE TABLE IF NOT EXISTS upload_pipeline.documents (
    document_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- Create document_chunks table
CREATE TABLE IF NOT EXISTS upload_pipeline.document_chunks (
    chunk_id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES upload_pipeline.documents(document_id),
    chunk_ord INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_upload_jobs_user_id ON upload_pipeline.upload_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_status ON upload_pipeline.upload_jobs(status);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON upload_pipeline.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON upload_pipeline.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON upload_pipeline.document_chunks USING ivfflat (embedding vector_cosine_ops);
```

#### **3.3 Verify Table Creation**
```sql
-- Verify all tables exist and have correct structure
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'upload_pipeline'
ORDER BY table_name, ordinal_position;
```

### **Phase 4: Testing and Validation (60-90 minutes)**

#### **4.1 Worker Functionality Test**
```bash
# Restart worker service
docker restart <worker_container_id>
# OR
kubectl rollout restart deployment/worker

# Monitor logs for errors
docker logs <worker_container_id> -f
# OR
kubectl logs <worker_pod_name> -f
```

#### **4.2 Database Operations Test**
```sql
-- Test basic operations
INSERT INTO upload_pipeline.upload_jobs (job_id, user_id, status) 
VALUES (gen_random_uuid(), gen_random_uuid(), 'test');

SELECT * FROM upload_pipeline.upload_jobs WHERE status = 'test';

DELETE FROM upload_pipeline.upload_jobs WHERE status = 'test';
```

#### **4.3 End-to-End Test**
```bash
# Test document upload workflow
# Upload a test document and verify processing
```

### **Phase 5: Monitoring and Prevention (90+ minutes)**

#### **5.1 Add Monitoring**
```sql
-- Add monitoring queries
SELECT 
    'upload_jobs' as table_name,
    COUNT(*) as row_count,
    MAX(created_at) as latest_record
FROM upload_pipeline.upload_jobs
UNION ALL
SELECT 
    'documents' as table_name,
    COUNT(*) as row_count,
    MAX(created_at) as latest_record
FROM upload_pipeline.documents
UNION ALL
SELECT 
    'document_chunks' as table_name,
    COUNT(*) as row_count,
    MAX(created_at) as latest_record
FROM upload_pipeline.document_chunks;
```

#### **5.2 Health Check Implementation**
```python
# Add database schema health check to worker
async def check_database_schema():
    required_tables = ['upload_jobs', 'documents', 'document_chunks']
    for table in required_tables:
        result = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'upload_pipeline' AND table_name = $1)",
            table
        )
        if not result:
            raise Exception(f"Required table upload_pipeline.{table} does not exist")
```

### **Phase 6: Documentation and Prevention**

#### **6.1 Update Documentation**
- Document the schema creation process
- Add troubleshooting guide for schema issues
- Update deployment procedures

#### **6.2 Prevention Measures**
- Add schema validation to deployment pipeline
- Implement database health checks
- Add monitoring alerts for schema issues

---

## **IMMEDIATE ACTION ITEMS**

### **Priority 1 (0-15 minutes)**
1. ✅ Check worker service status
2. ✅ Verify database connectivity
3. ✅ Check if upload_pipeline schema exists

### **Priority 2 (15-30 minutes)**
1. ✅ Identify missing tables
2. ✅ Check migration status
3. ✅ Verify environment configuration

### **Priority 3 (30-60 minutes)**
1. ✅ Create missing schema/tables
2. ✅ Restart worker service
3. ✅ Test basic functionality

### **Priority 4 (60+ minutes)**
1. ✅ Full end-to-end testing
2. ✅ Implement monitoring
3. ✅ Document resolution

---

## **SUCCESS CRITERIA**

- [ ] All required database tables exist
- [ ] Worker service starts without errors
- [ ] Document processing workflow functions
- [ ] No database schema errors in logs
- [ ] End-to-end document upload test passes

---

## **ESCALATION CRITERIA**

If resolution is not achieved within 60 minutes:
1. Escalate to Database Team Lead
2. Escalate to DevOps Team Lead
3. Consider rolling back to last known working state
4. Implement temporary workaround if available

---

**Investigation Lead**: [Your Name]  
**Start Time**: [Current Time]  
**Expected Resolution**: [Current Time + 60 minutes]  
**Escalation Contact**: [Team Lead Contact]
