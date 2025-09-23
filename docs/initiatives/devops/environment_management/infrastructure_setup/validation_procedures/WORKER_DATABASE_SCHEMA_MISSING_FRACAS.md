# FRACAS Item: Worker Database Schema Missing

## 🚨 **INCIDENT SUMMARY**

**Date**: 2025-09-22  
**Severity**: CRITICAL  
**Status**: INVESTIGATING  
**Component**: Enhanced Base Worker / Database Schema  

### **Problem Description**
The enhanced base worker is failing with critical database schema errors. Multiple database tables are missing from the `upload_pipeline` schema, causing complete failure of document processing workflows.

**Primary Error**: `relation "upload_pipeline.document_chunks" does not exist`  
**Secondary Error**: `relation "upload_pipeline.upload_jobs" does not exist`

### **Impact Assessment**
- **System Availability**: CRITICAL - Document processing completely broken
- **User Experience**: SEVERE - No document uploads can be processed
- **Business Impact**: CRITICAL - Core functionality unavailable
- **Data Integrity**: HIGH - No document storage possible

### **Error Details**

#### **Error 1: Document Chunking Failed**
```
Error Code: DOCUMENT_CHUNKING_FAILED
Message: Failed to chunk document content
Exception: relation "upload_pipeline.document_chunks" does not exist
Location: enhanced_base_worker.py:876 in _process_chunking_real
```

#### **Error 2: Job Processing Failed**
```
Error Code: JOB_PROCESSING_FAILED_PARSE_VALIDATED
Message: Failed to process job in parse_validated stage
Exception: relation "upload_pipeline.document_chunks" does not exist
Location: enhanced_base_worker.py:395 in _process_single_job_with_monitoring
```

#### **Error 3: Job State Update Failed**
```
Error Code: JOB_PROCESSING_LOOP_ERROR
Message: Error in job processing loop
Exception: relation "upload_pipeline.upload_jobs" does not exist
Location: enhanced_base_worker.py:1074 in _update_job_state
```

### **Affected Components**
- Enhanced Base Worker (`backend/workers/enhanced_base_worker.py`)
- Upload Pipeline Database Schema
- Document Processing Workflow
- Job Management System

### **Root Cause Analysis**

#### **Suspected Causes**
1. **Database Migration Not Applied**: Schema migrations not run in production
2. **Schema Creation Failed**: Database initialization failed silently
3. **Environment Mismatch**: Production using wrong database schema
4. **Permission Issues**: Database user lacks CREATE TABLE permissions
5. **Connection Issues**: Worker connecting to wrong database instance

#### **Investigation Areas**
- [ ] Database schema verification
- [ ] Migration status check
- [ ] Database connection configuration
- [ ] User permissions verification
- [ ] Environment variable validation

### **Investigation Steps**

#### **Step 1: Verify Database Schema**
```sql
-- Check if upload_pipeline schema exists
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'upload_pipeline';

-- Check if required tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'upload_pipeline' 
AND table_name IN ('document_chunks', 'upload_jobs', 'documents');
```

#### **Step 2: Check Migration Status**
```bash
# Check if migrations have been applied
# Look for migration files and their status
```

#### **Step 3: Verify Database Connection**
```python
# Check database connection configuration
# Verify DATABASE_URL and connection parameters
```

#### **Step 4: Check User Permissions**
```sql
-- Verify user has CREATE TABLE permissions
SELECT has_schema_privilege('upload_pipeline', 'CREATE');
```

### **Test Cases**

#### **Test 1: Schema Existence**
1. Connect to production database
2. Check if `upload_pipeline` schema exists
3. Verify all required tables are present

#### **Test 2: Table Structure**
1. Verify table structures match expected schema
2. Check for proper indexes and constraints
3. Validate data types and relationships

#### **Test 3: Worker Connection**
1. Test worker database connection
2. Verify worker can access required tables
3. Test basic CRUD operations

### **Expected Resolution**
- [ ] All required database tables exist
- [ ] Worker can successfully connect to database
- [ ] Document processing workflow functions normally
- [ ] Job management system operational
- [ ] No database schema errors in logs

### **Priority**
**CRITICAL** - This is a complete system failure

### **Assigned To**
Database Team / DevOps Team

### **Due Date**
2025-09-22 (Same day - immediate resolution required)

---

**FRACAS ID**: WORKER-SCHEMA-MISSING-001  
**Created**: 2025-09-22T23:15:00Z  
**Last Updated**: 2025-09-22T23:15:00Z
