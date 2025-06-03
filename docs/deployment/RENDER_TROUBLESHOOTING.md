# Render.com Deployment Troubleshooting Guide

## 🔧 Critical Issue: Prepared Statement Errors

### Problem Description
**Error Message:**
```
db.services.db_pool - ERROR - Database connection error: prepared statement "__asyncpg_stmt_1__" does not exist
```

**Root Cause:**
Supabase transaction pooler (Supavisor) doesn't support prepared statements, but asyncpg creates them by default.

### Solution Status
✅ **FIXED** - Multiple layers of protection implemented:

1. **Environment Variable Detection**
   - `ASYNCPG_DISABLE_PREPARED_STATEMENTS=1` in render.yaml
   - Code checks for this variable and disables prepared statements

2. **AsyncPG Pool Configuration**
   - `statement_cache_size=0` when prepared statements disabled
   - Automatic detection of pooler URLs (`pooler.supabase.com`)

3. **SQLAlchemy Engine Configuration** 
   - Same `statement_cache_size=0` setting applied
   - Event handler that runs `DEALLOCATE ALL` on transaction begin

4. **Connection-Level Protection**
   - `DEALLOCATE ALL` executed on each raw connection acquire

## 📊 Verification Steps

### 1. Check Deployment Status
Visit your Render.com app root endpoint:
```
https://your-app.onrender.com/
```

Look for `deployment_info` section:
```json
{
  "deployment_info": {
    "prepared_statements_fix": "ACTIVE",
    "commit_hash": "068950d", 
    "environment_vars": {
      "ASYNCPG_DISABLE_PREPARED_STATEMENTS": "1",
      "DATABASE_URL_contains_pooler": true
    }
  }
}
```

### 2. Check Render.com Logs
Look for these SUCCESS indicators:
```
🔧 Prepared statements DISABLED for transaction pooler compatibility
🔧 SQLAlchemy prepared statements DISABLED for transaction pooler  
🔧 SQLAlchemy event handler added: DEALLOCATE ALL on transaction begin
Database pool initialized successfully
```

### 3. Monitor Error Logs
If you still see prepared statement errors after the fix:

**Check for:**
- Old logs vs new logs (after latest deployment)
- Different error patterns or reduced frequency
- Any remaining `__asyncpg_stmt_` references

## 🚨 If Still Seeing Errors

### Scenario 1: Fix Not Deployed
**Check:**
1. Is latest commit deployed? (Check commit hash in root endpoint)
2. Did Render.com build succeed?
3. Are environment variables set correctly?

**Action:**
```bash
# Force redeploy
git commit --allow-empty -m "Force redeploy for prepared statement fix"
git push origin buildout/mvp-integration
```

### Scenario 2: Additional Direct Connections
**Check for:**
- Other libraries creating direct asyncpg connections
- Migration scripts or background jobs
- Third-party packages bypassing our pool

**Diagnostic:**
```bash
# Search for direct asyncpg usage
grep -r "asyncpg.connect" --include="*.py" .
grep -r "create_pool" --include="*.py" .
```

### Scenario 3: Environment Variable Not Set
**Verify in Render.com Dashboard:**
- Go to Environment tab
- Confirm `ASYNCPG_DISABLE_PREPARED_STATEMENTS=1` exists
- Check `DATABASE_URL` points to transaction pooler (port 6543)

### Scenario 4: Database Connection Caching
**Try:**
1. Restart the Render.com service
2. Clear any connection pools
3. Force new database connections

## 🔍 Advanced Debugging

### Enable SQL Logging
Set in render.yaml:
```yaml
env_vars:
  - key: SQLALCHEMY_ECHO
    value: "true"
```

### Add Debug Logging
Temporary debug code:
```python
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('asyncpg').setLevel(logging.DEBUG)
```

### Monitor Connection Pool
Check pool status via health endpoint:
```
GET /health
```

Look for database service status and connection counts.

## 📈 Performance Impact

### Expected Changes After Fix:
- ✅ No more prepared statement errors
- ⚠️ Slightly higher CPU usage (no statement caching)
- ⚠️ Slightly higher latency per query (~1-2ms)
- ✅ Better stability with transaction poolers

### Monitoring:
- Response times via Render.com metrics
- Error rates in application logs
- Database connection pool utilization

## 🚀 Next Steps After Resolution

1. **Remove Debug Logging**
   - Turn off SQL echo in production
   - Reduce log verbosity once stable

2. **Performance Tuning**
   - Monitor query performance
   - Consider query optimization
   - Review connection pool settings

3. **Documentation**
   - Update deployment guide
   - Add monitoring alerts
   - Create runbook for future issues

## 📞 Escalation Path

If errors persist after all fixes:

1. **Check Supabase Status**
   - Visit status.supabase.com
   - Check for pooler-specific issues

2. **Contact Support**
   - Render.com support (if deployment issues)
   - Supabase support (if database issues)

3. **Alternative Solutions**
   - Switch to direct database connection (not pooler)
   - Use different connection pooling library
   - Implement connection retry logic

## 📋 Checklist

**Pre-Deployment:**
- [ ] Environment variables set in render.yaml
- [ ] Code changes committed and pushed
- [ ] Local testing passes deployment simulation
- [ ] Database URL points to transaction pooler

**Post-Deployment:**
- [ ] Root endpoint shows fix is active
- [ ] Logs show prepared statements disabled
- [ ] No more prepared statement errors
- [ ] Health endpoint returns healthy status
- [ ] Application responds normally

**Monitoring:**
- [ ] Set up error rate alerts
- [ ] Monitor database connection metrics
- [ ] Track response time changes
- [ ] Regular health checks automated 