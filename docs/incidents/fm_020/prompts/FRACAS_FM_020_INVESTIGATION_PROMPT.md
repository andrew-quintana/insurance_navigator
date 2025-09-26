# FRACAS FM-020 Investigation Prompt

## Emergency Response Required

You are investigating a **CRITICAL** service outage caused by persistent SCRAM authentication failures in the API service. The service has been down since 2025-09-26 and requires immediate attention.

## Current Situation
- **Service**: insurance-navigator-staging-api (Render)
- **Status**: DOWN - Cannot start due to database authentication failure
- **Error**: `'NoneType' object has no attribute 'group'` in SCRAM authentication
- **Last Working**: Commit 0982fb1 (2025-09-24)

## Immediate Actions Required

### 1. Emergency Rollback (Priority 1)
```bash
# Revert to last working commit
git checkout 0982fb1
git push origin staging --force

# Verify service starts successfully
# Check Render deployment logs
```

### 2. Root Cause Analysis (Priority 2)
Analyze the differences between working and broken states:

```bash
# Compare working vs broken database configuration
git diff 0982fb1..HEAD core/database.py

# Check environment variable changes
git diff 0982fb1..HEAD config/environment_loader.py

# Review authentication changes
git diff 0982fb1..HEAD api/upload_pipeline/auth.py
```

### 3. Specific Investigation Areas

#### A. Database Configuration Changes
- **Working**: Simple `create_pool()` with connection string
- **Broken**: Complex pooler URL selection with cloud detection
- **Question**: Is the pooler URL selection logic causing authentication issues?

#### B. SSL Configuration Changes
- **Working**: Dynamic SSL config based on connection type
- **Broken**: Hardcoded `ssl="require"` for pooler connections
- **Question**: Is the SSL configuration incompatible with pooler authentication?

#### C. Environment Variable Loading
- **Working**: Direct environment variable access
- **Broken**: Complex environment loader with cloud detection
- **Question**: Are environment variables being loaded incorrectly?

## Investigation Questions

### 1. Pooler URL Compatibility
- Are the pooler URLs correctly formatted and accessible?
- Does the pooler service support SCRAM authentication?
- Are we using the correct pooler URL for the environment?

### 2. SSL/TLS Handshake Issues
- Is the hardcoded `ssl="require"` causing authentication problems?
- Are there SSL certificate compatibility issues?
- Does the pooler service require different SSL configuration?

### 3. Environment Variable Corruption
- Are pooler URLs being loaded correctly?
- Are authentication credentials being passed properly?
- Is cloud deployment detection selecting the wrong configuration?

## Testing Strategy

### 1. Isolate the Problem
```bash
# Test 1: Revert to working commit
git checkout 0982fb1
# Deploy and verify service starts

# Test 2: Reintroduce changes one by one
# Start with database configuration changes
# Test each change individually
```

### 2. Validate Pooler URLs
```bash
# Test pooler URL connectivity
psql "SUPABASE_SESSION_POOLER_URL"
psql "SUPABASE_POOLER_URL"

# Test authentication with pooler URLs
# Verify SCRAM authentication works
```

### 3. Test SSL Configuration
```bash
# Test with different SSL configurations
# ssl="disable"
# ssl="prefer" 
# ssl="require"

# Test authentication without SSL
# Isolate SSL-related issues
```

## Expected Outcomes

### 1. Immediate (Today)
- Service restored to working state
- Root cause identified
- Fix implemented and tested

### 2. Short-term (This Week)
- Comprehensive fix deployed
- Service stability restored
- Prevention measures implemented

### 3. Long-term (Next Week)
- Deployment procedures updated
- Testing pipeline enhanced
- Documentation updated

## Success Criteria
- ✅ API service starts successfully
- ✅ Database connections work reliably
- ✅ No SCRAM authentication errors
- ✅ Service remains stable
- ✅ Root cause documented and fixed

## Escalation Path
If unable to resolve within 2 hours:
1. **Notify**: Development team lead
2. **Escalate**: Engineering manager
3. **Emergency**: Consider complete environment rebuild

## Resources
- **Working Commit**: 0982fb1
- **Current Branch**: staging
- **Deployment Platform**: Render
- **Database**: Supabase (staging)
- **Related Incidents**: FM-011, FM-017, FM-018

---

**URGENT**: This is a critical service outage requiring immediate attention. Focus on restoring service first, then identifying and fixing the root cause.
