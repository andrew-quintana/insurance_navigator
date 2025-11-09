# FRACAS FM-011 Investigation Prompt: Render Worker IPv6 Connectivity Issue

## 🎯 **INVESTIGATION MISSION**

**Objective**: Investigate and resolve the staging worker service database connectivity issues due to IPv6 connectivity problems on Render platform.

**Reference Document**: `docs/incidents/failure_modes/connectivity/FRACAS_FM_011_RENDER_WORKER_IPV6_CONNECTIVITY.md`

## 🚨 **CURRENT SITUATION**

### **Critical Issue**
- **Status**: CRITICAL
- **Impact**: Worker service fails to connect to Supabase database
- **Error**: `OSError: [Errno 101] Network is unreachable`
- **Environment**: Staging Worker Service (Render)
- **Root Cause**: IPv6 connectivity issues between Render and Supabase

### **Evidence Summary**
```
Error: OSError: [Errno 101] Network is unreachable
Location: Worker initialization during database connection pool creation
Environment: Render staging environment
Database: Supabase (staging)
Issue: IPv6 connectivity problem
```

## 🔍 **INVESTIGATION TASKS**

### **Task 1: Network Connectivity Analysis (P0 - Critical)**
**Time Estimate**: 20 minutes

**Objective**: Understand the IPv6 connectivity issue between Render and Supabase.

**Investigation Steps**:
1. Analyze the error pattern and network configuration
2. Check if Supabase provides IPv4 alternatives (pooler URLs)
3. Verify environment variables for database connection
4. Test different connection methods

**Expected Output**:
- Clear understanding of IPv6 vs IPv4 connectivity issue
- Identification of available IPv4 alternatives
- Network configuration analysis

### **Task 2: Database Configuration Review (P0 - Critical)**
**Time Estimate**: 15 minutes

**Objective**: Review current database configuration and identify IPv4 alternatives.

**Investigation Steps**:
1. Check current `DATABASE_URL` configuration
2. Look for `SUPABASE_SESSION_POOLER_URL` and `SUPABASE_POOLER_URL` variables
3. Review database connection logic in worker code
4. Identify configuration changes needed

**Expected Output**:
- Current database configuration analysis
- Available pooler URL options
- Required configuration changes

### **Task 3: Pooler URL Implementation (P1 - High)**
**Time Estimate**: 30 minutes

**Objective**: Implement pooler URL usage for IPv4 connectivity.

**Implementation Requirements**:
1. Modify database configuration to use pooler URLs
2. Add cloud deployment detection logic
3. Implement fallback mechanisms
4. Add debugging logs for URL selection

**Code Changes Needed**:
- Update `core/database.py` for pooler URL support
- Modify worker database configuration
- Add cloud deployment detection
- Implement URL selection logic

**Success Criteria**:
- Worker uses pooler URL for database connection
- IPv4 connectivity works on Render
- Clear logging shows URL selection process

### **Task 4: Build Filter Analysis (P1 - High)**
**Time Estimate**: 15 minutes

**Objective**: Analyze and fix build filter limitations preventing deployment of fixes.

**Investigation Steps**:
1. Check worker service build filter configuration
2. Identify which directories are included/excluded
3. Determine if `core/` directory changes are deployed
4. Create workaround if needed

**Expected Output**:
- Build filter analysis
- Workaround implementation
- Deployment strategy

### **Task 5: Testing and Verification (P1 - High)**
**Time Estimate**: 20 minutes

**Objective**: Test the fix and verify worker connectivity.

**Testing Steps**:
1. Deploy updated worker configuration
2. Monitor worker logs for debugging information
3. Verify database connection success
4. Test worker functionality end-to-end

**Expected Output**:
- Successful worker deployment
- Database connection established
- Worker processing jobs successfully

## 🧪 **TEST COMMANDS**

```bash
# Test 1: Check environment variables
echo "DATABASE_URL: $DATABASE_URL"
echo "SUPABASE_SESSION_POOLER_URL: $SUPABASE_SESSION_POOLER_URL"
echo "SUPABASE_POOLER_URL: $SUPABASE_POOLER_URL"

# Test 2: Test database connectivity
python -c "
import asyncio
import asyncpg
from core.database import get_database

async def test_connection():
    try:
        db = get_database()
        await db.initialize()
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test_connection())
"

# Test 3: Test pooler URL specifically
python -c "
import asyncio
import asyncpg

async def test_pooler():
    try:
        conn = await asyncpg.connect('postgresql://postgres:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres')
        print('✅ Pooler URL connection successful')
        await conn.close()
    except Exception as e:
        print(f'❌ Pooler URL connection failed: {e}')

asyncio.run(test_pooler())
"
```

## 📋 **EXPECTED OUTPUT**

### **Immediate Fix (P0)**
1. **Pooler URL Usage**: Worker uses IPv4 pooler URL instead of direct IPv6 connection
2. **Database Connection**: Worker successfully connects to Supabase database
3. **Error Resolution**: No more "Network is unreachable" errors

### **Short-term Improvements (P1)**
1. **Build Filter Fix**: Ensure all necessary directories are included in deployment
2. **Debugging Logs**: Clear logging shows URL selection process
3. **Cloud Detection**: Proper cloud deployment detection logic

### **Success Metrics**
- ✅ Worker service starts without database connection errors
- ✅ Database operations work correctly
- ✅ Worker can process jobs successfully
- ✅ No IPv6 connectivity issues

## 📄 **DELIVERABLES**

1. **FRACAS Update**: Update `docs/incidents/failure_modes/connectivity/FRACAS_FM_011_RENDER_WORKER_IPV6_CONNECTIVITY.md` with findings
2. **Code Changes**: Implement pooler URL support
3. **Build Filter Fix**: Update worker service build configuration
4. **Testing Results**: Verify worker functionality
5. **Documentation**: Document IPv4 connectivity requirements

## ⚠️ **CRITICAL NOTES**

- **IPv6 Issue**: Render cannot reach Supabase IPv6 addresses
- **Pooler URLs**: Supabase provides IPv4 pooler URLs as alternative
- **Build Filter**: May prevent deployment of `core/` directory changes
- **Cloud Detection**: Need to detect Render environment for pooler URL usage

## 🚨 **ESCALATION CRITERIA**

- If pooler URLs are not available or don't work
- If build filter changes require infrastructure modifications
- If IPv4 connectivity still fails after pooler URL implementation
- If worker service requires complete architecture changes

## ⏱️ **ESTIMATED DURATION**
- **Total Time**: 100 minutes
- **Investigation**: 35 minutes
- **Implementation**: 45 minutes
- **Testing**: 20 minutes

---

**Reference**: See `docs/incidents/failure_modes/connectivity/FRACAS_FM_011_RENDER_WORKER_IPV6_CONNECTIVITY.md` for complete failure details
