# FRACAS Summary: Worker Database Schema Missing

## 🚨 **CRITICAL INCIDENT SUMMARY**

**FRACAS ID**: WORKER-SCHEMA-MISSING-001  
**Severity**: CRITICAL  
**Date**: 2025-09-22  
**Status**: INVESTIGATING  

### **Problem Statement**
The enhanced base worker is experiencing complete failure due to missing database schema. All document processing workflows have stopped, causing a critical system outage.

**Primary Error**: `relation "upload_pipeline.document_chunks" does not exist`  
**Secondary Error**: `relation "upload_pipeline.upload_jobs" does not exist`

---

## **IMMEDIATE ACTION REQUIRED**

### **Step 1: Run Diagnostic Script (5 minutes)**
```bash
cd /Users/aq_home/1Projects/accessa/insurance_navigator
python scripts/diagnose_worker_schema.py
```

### **Step 2: Create Missing Schema (10 minutes)**
```bash
# Connect to production database and run schema creation script
psql $DATABASE_URL -f sql/create_upload_pipeline_schema.sql
```

### **Step 3: Restart Worker Service (5 minutes)**
```bash
# Restart the worker service
docker restart <worker_container_id>
# OR
kubectl rollout restart deployment/worker
```

### **Step 4: Verify Resolution (10 minutes)**
```bash
# Check worker logs
docker logs <worker_container_id> --tail 50
# OR
kubectl logs <worker_pod_name> --tail 50
```

---

## **FILES CREATED FOR RESOLUTION**

### **1. FRACAS Documentation**
- `docs/incidents/WORKER_DATABASE_SCHEMA_MISSING_FRACAS.md` - Complete FRACAS item
- `docs/incidents/FRACAS_WORKER_SCHEMA_INVESTIGATION_PROMPT.md` - Detailed investigation flow

### **2. Diagnostic Tools**
- `scripts/diagnose_worker_schema.py` - Automated diagnostic script
- `sql/create_upload_pipeline_schema.sql` - Schema creation script

### **3. This Summary**
- `docs/incidents/FRACAS_SUMMARY_WORKER_SCHEMA.md` - Quick reference guide

---

## **ROOT CAUSE ANALYSIS**

### **Suspected Causes**
1. **Database Migration Not Applied**: Schema migrations not run in production
2. **Schema Creation Failed**: Database initialization failed silently
3. **Environment Mismatch**: Production using wrong database schema
4. **Permission Issues**: Database user lacks CREATE TABLE permissions

### **Most Likely Cause**
Database schema was never created in production environment, likely due to:
- Missing migration execution during deployment
- Silent failure during database initialization
- Environment configuration mismatch

---

## **RESOLUTION STEPS**

### **Immediate (0-30 minutes)**
1. ✅ Run diagnostic script to confirm missing schema
2. ✅ Execute schema creation script
3. ✅ Restart worker service
4. ✅ Verify no errors in logs

### **Short-term (30-60 minutes)**
1. ✅ Test document upload workflow
2. ✅ Monitor worker performance
3. ✅ Verify all tables are accessible

### **Long-term (1-7 days)**
1. ✅ Add schema validation to deployment pipeline
2. ✅ Implement database health checks
3. ✅ Add monitoring alerts for schema issues
4. ✅ Update deployment documentation

---

## **SUCCESS CRITERIA**

- [ ] All required database tables exist
- [ ] Worker service starts without errors
- [ ] Document processing workflow functions
- [ ] No database schema errors in logs
- [ ] End-to-end document upload test passes

---

## **PREVENTION MEASURES**

### **1. Schema Validation**
Add to deployment pipeline:
```bash
# Check schema exists before starting services
psql $DATABASE_URL -c "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'upload_pipeline';"
```

### **2. Health Checks**
Implement in worker service:
```python
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

### **3. Monitoring Alerts**
Set up alerts for:
- Database schema errors
- Worker service failures
- Document processing failures

---

## **ESCALATION PATH**

### **If Not Resolved in 30 minutes:**
1. Escalate to Database Team Lead
2. Escalate to DevOps Team Lead
3. Consider rolling back to last known working state

### **If Not Resolved in 60 minutes:**
1. Escalate to Engineering Manager
2. Implement temporary workaround
3. Consider emergency maintenance window

---

## **CONTACT INFORMATION**

**Investigation Lead**: [Your Name]  
**Database Team**: [Database Team Contact]  
**DevOps Team**: [DevOps Team Contact]  
**Engineering Manager**: [Manager Contact]  

---

## **QUICK REFERENCE**

### **Diagnostic Command**
```bash
python scripts/diagnose_worker_schema.py
```

### **Schema Creation Command**
```bash
psql $DATABASE_URL -f sql/create_upload_pipeline_schema.sql
```

### **Worker Restart Command**
```bash
docker restart <worker_container_id>
# OR
kubectl rollout restart deployment/worker
```

### **Log Check Command**
```bash
docker logs <worker_container_id> --tail 100
# OR
kubectl logs <worker_pod_name> --tail 100
```

---

**Last Updated**: 2025-09-22T23:20:00Z  
**Next Review**: 2025-09-23T00:00:00Z
