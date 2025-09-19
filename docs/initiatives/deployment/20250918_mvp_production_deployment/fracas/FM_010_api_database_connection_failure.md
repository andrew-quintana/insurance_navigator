# FRACAS: FM-010 - API Service Database Connection Pool Failure

**Date**: 2025-09-18  
**Priority**: High  
**Status**: Active  
**Component**: API Service Database Connection  
**Failure Mode**: Prepared Statement Duplication Error  

## 🚨 **Failure Summary**

The API service is experiencing database connection pool failures due to prepared statement duplication errors when using pgbouncer with transaction/statement pool modes.

## 📋 **Failure Details**

### **Error Details (2025-09-19 02:26:11):**
```
❌ Legacy upload failed: prepared statement "__asyncpg_stmt_3__" already exists
HINT:  
NOTE: pgbouncer with pool_mode set to "transaction" or
"statement" does not support prepared statements properly.
```

**Error Type**: `asyncpg.exceptions.DuplicatePreparedStatementError`  
**Request ID**: `47f0fde2-703d-45cc-9835-72da8b8a421c`  
**Status Code**: 500 Internal Server Error  
**Processing Time**: 0.82s  

### **Root Cause Analysis:**

**Primary Issue**: pgbouncer Configuration Incompatibility
- pgbouncer with `pool_mode = "transaction"` or `"statement"` doesn't support prepared statements
- asyncpg is trying to reuse prepared statements across connections
- This causes duplicate prepared statement errors

**Secondary Issues:**
1. **Connection Pool Configuration**: Current setup incompatible with prepared statements
2. **Database Connection Management**: asyncpg prepared statement caching conflicts with pgbouncer
3. **Production Environment**: Supabase uses pgbouncer for connection pooling

## 🔍 **Technical Analysis**

### **Error Context:**
- **File**: `/app/main.py`, line 861
- **Function**: `upload_document_backend`
- **Operation**: `conn.fetchrow()` database query
- **Database**: Supabase PostgreSQL with pgbouncer

### **pgbouncer Pool Modes:**
- **Session Mode**: ✅ Supports prepared statements (but uses more connections)
- **Transaction Mode**: ❌ Doesn't support prepared statements (current issue)
- **Statement Mode**: ❌ Doesn't support prepared statements (current issue)

### **asyncpg Behavior:**
- **Prepared Statement Caching**: asyncpg caches prepared statements for performance
- **Connection Reuse**: Tries to reuse prepared statements across connections
- **pgbouncer Conflict**: pgbouncer doesn't maintain prepared statement state between connections

## 🔧 **Resolution Options**

### **Option 1: Disable Prepared Statement Caching (Recommended)**
```python
# Set statement_cache_size to 0 when creating asyncpg connection
connection = await asyncpg.connect(
    database_url,
    statement_cache_size=0
)
```

### **Option 2: Switch to asyncpg Connection Pooling**
```python
# Use asyncpg's built-in connection pooling instead of pgbouncer
pool = await asyncpg.create_pool(
    database_url,
    min_size=5,
    max_size=20
)
```

### **Option 3: Configure pgbouncer for Session Mode**
```yaml
# In pgbouncer configuration
pool_mode = session
```

## 📊 **Impact Assessment**

- **API Status**: Upload endpoint failing with 500 errors
- **User Impact**: Users cannot upload documents via API
- **Business Impact**: Core functionality completely broken
- **Priority**: CRITICAL - API service down

## 🎯 **Immediate Actions**

### **1. Quick Fix - Disable Prepared Statement Caching**
Update database connection configuration to disable prepared statement caching:

```python
# In database connection code
connection = await asyncpg.connect(
    database_url,
    statement_cache_size=0
)
```

### **2. Test Fix**
- Deploy the fix to production
- Test upload endpoint functionality
- Monitor for prepared statement errors

### **3. Long-term Solution**
- Evaluate switching to asyncpg connection pooling
- Consider pgbouncer configuration changes
- Implement proper connection management

## 📈 **Success Criteria**

- [ ] API upload endpoint returns 200 OK
- [ ] No prepared statement duplication errors
- [ ] Database queries execute successfully
- [ ] Upload functionality fully restored
- [ ] No performance degradation

## 🔍 **Investigation Steps**

### **Check Current Configuration:**
1. **Database Connection Code**: Review how asyncpg connections are created
2. **pgbouncer Settings**: Check Supabase pgbouncer configuration
3. **Connection Pooling**: Verify current pooling implementation
4. **Error Patterns**: Monitor for similar errors across endpoints

### **Code Locations to Check:**
- `main.py` line 861 (where error occurred)
- Database connection initialization code
- Connection pool configuration
- asyncpg connection parameters

---

**Created**: 2025-09-18  
**Updated**: 2025-09-18  
**Status**: Active  
**Assigned**: Development Team  
**Priority**: High
