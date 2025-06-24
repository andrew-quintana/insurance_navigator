# Manual Testing Checklist - Database Refactoring

**Goal:** Ensure the database refactoring implementation works correctly and safely

## 🧪 **PRE-MIGRATION TESTING**

### 1. **Environment Preparation** ⏱️ 10 mins
- [ ] **Backup Database**
  ```bash
  # Run pre-migration validation
  python scripts/test_pre_migration.py
  ```
- [ ] **Check Current Schema**
  - Log into database and count tables: `SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';`
  - Should show 22+ tables currently
- [ ] **Verify Services Running**
  - [ ] API server accessible at `/health`
  - [ ] Database connections working
  - [ ] Supabase Storage accessible

### 2. **Functionality Baseline** ⏱️ 15 mins
- [ ] **User Authentication**
  - [ ] Register new test user
  - [ ] Login with test credentials
  - [ ] Access `/me` endpoint
- [ ] **Document Upload**
  - [ ] Upload a test PDF document
  - [ ] Verify file appears in storage
  - [ ] Check document metadata in database
- [ ] **Chat Functionality**
  - [ ] Send test message via `/chat`
  - [ ] Verify conversation is created
  - [ ] Check message history

## 🚀 **MIGRATION EXECUTION TESTING**

### 3. **Migration Dry Run** ⏱️ 5 mins
- [ ] **Review Migration File**
  ```bash
  # Check migration content
  cat db/migrations/V2.0.0__mvp_schema_refactor.sql | head -50
  ```
- [ ] **Validate SQL Syntax**
  ```bash
  # Connect to database and run EXPLAIN on key statements
  psql $DATABASE_URL -c "EXPLAIN (FORMAT JSON) SELECT 1;"
  ```

### 4. **Execute Migration** ⏱️ 10 mins
- [ ] **Run Migration**
  ```bash
  # Execute the migration (replace with your migration tool)
  psql $DATABASE_URL -f db/migrations/V2.0.0__mvp_schema_refactor.sql
  ```
- [ ] **Monitor for Errors**
  - [ ] Check for any SQL errors during execution
  - [ ] Verify all tables were created/modified successfully
  - [ ] Check that dropped tables are gone

### 5. **Post-Migration Validation** ⏱️ 10 mins
- [ ] **Run Validation Script**
  ```bash
  python scripts/validate_migration.py
  ```
- [ ] **Verify Schema Changes**
  ```sql
  -- Check table count (should be ~8)
  SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
  
  -- Check policy_basics column exists
  SELECT column_name FROM information_schema.columns 
  WHERE table_name = 'documents' AND column_name = 'policy_basics';
  
  -- Check audit_logs table exists
  SELECT COUNT(*) FROM audit_logs LIMIT 1;
  ```

## 🔧 **FUNCTIONALITY TESTING**

### 6. **Core Services Testing** ⏱️ 20 mins

#### **A. Document Service Testing**
- [ ] **Upload New Document**
  ```bash
  # Test upload endpoint
  curl -X POST http://localhost:8000/upload-document \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@test_policy.pdf" \
    -F "policy_id=test-123" \
    -F "document_type=policy"
  ```
- [ ] **Verify Policy Extraction**
  ```sql
  -- Check if policy_basics was populated
  SELECT id, policy_basics FROM documents 
  WHERE id = (SELECT MAX(id) FROM documents);
  ```
- [ ] **Test Hybrid Search**
  ```bash
  # Test search endpoint
  curl -X POST http://localhost:8000/search-documents \
    -H "Authorization: Bearer $TOKEN" \
    -F "query=coverage benefits" \
    -F "limit=5"
  ```

#### **B. Chat Service Testing**
- [ ] **Simple Chat Message**
  ```bash
  curl -X POST http://localhost:8000/chat \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "What coverage do I have?"}'
  ```
- [ ] **Chat with Document Context**
  ```bash
  curl -X POST http://localhost:8000/chat \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "Tell me about my deductible", "conversation_id": "test-conv"}'
  ```

#### **C. Conversation Management**
- [ ] **List Conversations**
  ```bash
  curl -X GET http://localhost:8000/conversations \
    -H "Authorization: Bearer $TOKEN"
  ```
- [ ] **Get Conversation Messages**
  ```bash
  curl -X GET http://localhost:8000/conversations/{conversation_id}/messages \
    -H "Authorization: Bearer $TOKEN"
  ```

### 7. **Performance Testing** ⏱️ 15 mins

#### **A. Policy Facts Lookup Speed**
- [ ] **Test JSONB Query Performance**
  ```sql
  -- Should complete in <50ms
  EXPLAIN ANALYZE 
  SELECT policy_basics FROM documents 
  WHERE policy_basics->>'policy_type' = 'health';
  ```
- [ ] **Test GIN Index Usage**
  ```sql
  -- Verify index is being used
  EXPLAIN (ANALYZE, BUFFERS) 
  SELECT * FROM documents 
  WHERE policy_basics @> '{"policy_type": "health"}';
  ```

#### **B. Hybrid Search Performance**
- [ ] **Measure Search Response Time**
  ```bash
  # Time the search request (should be <500ms)
  time curl -X POST http://localhost:8000/search-documents \
    -H "Authorization: Bearer $TOKEN" \
    -F "query=medical coverage" \
    -F "limit=10"
  ```

### 8. **HIPAA Compliance Testing** ⏱️ 10 mins

#### **A. Audit Logging**
- [ ] **Verify Audit Logs Created**
  ```sql
  -- Check recent audit entries
  SELECT action, table_name, created_at 
  FROM audit_logs 
  ORDER BY created_at DESC 
  LIMIT 10;
  ```
- [ ] **Test Policy Update Auditing**
  ```sql
  -- Update a policy and check audit
  SELECT update_policy_basics(1, '{"policy_type": "test"}');
  SELECT * FROM audit_logs WHERE action = 'UPDATE_POLICY_BASICS';
  ```

#### **B. Row Level Security**
- [ ] **Test User Data Isolation**
  ```sql
  -- Connect as different user and verify data access
  SET ROLE authenticated;
  SELECT COUNT(*) FROM documents; -- Should only see own documents
  ```

## 🔄 **ROLLBACK TESTING**

### 9. **Rollback Preparation** ⏱️ 10 mins
- [ ] **Test Rollback Script** (Optional - only if needed)
  ```bash
  # Create rollback migration if needed
  cat > db/migrations/V2.0.1__rollback_if_needed.sql << 'EOF'
  -- Rollback statements here
  EOF
  ```
- [ ] **Verify Backup Restore Process**
  - [ ] Confirm backup files are accessible
  - [ ] Test restore procedure on separate environment

## 📊 **FINAL VALIDATION**

### 10. **End-to-End User Journey** ⏱️ 20 mins
- [ ] **Complete User Workflow**
  1. [ ] User registers account
  2. [ ] User logs in
  3. [ ] User uploads insurance document
  4. [ ] System extracts policy information
  5. [ ] User asks questions about coverage
  6. [ ] System provides relevant answers
  7. [ ] User views conversation history

### 11. **Error Handling** ⏱️ 10 mins
- [ ] **Test Invalid Requests**
  - [ ] Upload non-PDF file
  - [ ] Send empty chat message
  - [ ] Access unauthorized endpoints
- [ ] **Verify Graceful Degradation**
  - [ ] System continues working if search fails
  - [ ] Appropriate error messages displayed

## 🎯 **SUCCESS CRITERIA**

### **Performance Targets**
- [ ] Policy facts lookup: **< 50ms**
- [ ] Document search: **< 500ms**  
- [ ] Database complexity: **65% reduction achieved**
- [ ] API response times: **< 2 seconds**

### **Functionality Requirements**
- [ ] All existing features work
- [ ] New hybrid search functions correctly
- [ ] Policy extraction working
- [ ] HIPAA compliance maintained
- [ ] No data loss occurred

### **Quality Assurance**
- [ ] No critical errors in logs
- [ ] All tests pass
- [ ] User experience improved
- [ ] System stability maintained

---

## 📝 **TESTING NOTES**

**Total Testing Time:** ~2 hours  
**Critical Path:** Steps 1-6, 10-11  
**Optional:** Step 9 (rollback) only if issues found  

**Test Environment:** Staging database  
**Required Tools:** curl, psql, python, browser  
**Test Data:** Sample PDF documents, test user accounts  

---

## ❗ **ISSUE TRACKING**

| Test | Status | Issues Found | Resolution |
|------|--------|--------------|------------|
| Pre-migration | ⏳ | | |
| Migration | ⏳ | | |
| Functionality | ⏳ | | |
| Performance | ⏳ | | |
| HIPAA | ⏳ | | |
| End-to-End | ⏳ | | |

**Status Legend:**  
⏳ Pending | ✅ Pass | ❌ Fail | ⚠️ Issues Found 