# FRACAS FM-026 Investigation Prompt

## Current Situation
- **Service**: insurance-navigator-staging-api (Render)
- **Status**: DOWN - Cannot start due to database authentication failure
- **Error**: `'NoneType' object has no attribute 'group'` in SCRAM authentication
- **Related**: Identical to FRACAS FM-020 (resolved)

## Immediate Actions Required

### 1. Apply FM-020 Solution
Since this is identical to FM-020, apply the proven solution:
- Use the exact working configuration from FM-020
- Verify port 6543 is being used correctly
- Test with known working Supabase project

### 2. Configuration Analysis
**Current Configuration**:
- Host: `aws-0-us-west-1.pooler.supabase.com`
- Port: `6543` (session pooler)
- Project: `your-project`
- SSL: `require`
- Connection String: `postgresql://postgres.your-project:ERaZFjC...`

**FM-020 Working Configuration**:
- Host: `aws-0-us-west-1.pooler.supabase.com`
- Port: `6543` (session pooler)
- Project: `your-staging-project`
- SSL: `require`
- Connection String: `postgresql://postgres.your-staging-project:password@aws-0-us-west-1.pooler.supabase.com:6543/postgres`

### 3. Root Cause Investigation
**Key Differences**:
1. **Supabase Project**: `your-project` vs `your-staging-project`
2. **Authentication Credentials**: Different password/credentials
3. **Project Configuration**: Possible differences in project setup

**Investigation Steps**:
1. Test connection to `your-staging-project` project (known working)
2. Compare project configurations
3. Verify authentication credentials for `your-project`
4. Test with different connection methods

### 4. Emergency Response
**Priority Actions**:
1. **Immediate**: Apply FM-020 working configuration
2. **Short-term**: Identify why `your-project` project fails
3. **Long-term**: Implement robust configuration validation

## Investigation Checklist

### Phase 1: Emergency Response
- [ ] Apply FM-020 working configuration
- [ ] Test with `your-staging-project` project
- [ ] Verify service starts successfully
- [ ] Monitor for stability

### Phase 2: Root Cause Analysis
- [ ] Compare project configurations
- [ ] Test authentication credentials
- [ ] Verify connection string format
- [ ] Check SSL/TLS configuration

### Phase 3: Solution Implementation
- [ ] Identify specific cause of failure
- [ ] Implement targeted fix
- [ ] Test fix thoroughly
- [ ] Deploy with monitoring

## Key Questions to Answer

1. **Why does `your-project` project fail while `your-staging-project` works?**
2. **Are the authentication credentials correct for the target project?**
3. **Is there a configuration difference between the projects?**
4. **Should we use the working project or fix the target project?**

## Expected Outcomes

### Immediate (Next 30 minutes)
- Service restored using FM-020 solution
- Clear understanding of project differences
- Working configuration identified

### Short-term (Next 2 hours)
- Root cause identified and documented
- Targeted fix implemented
- Service stable and monitored

### Long-term (Next 24 hours)
- Prevention measures implemented
- Configuration validation added
- Documentation updated

## Success Criteria
- ✅ Service starts successfully
- ✅ Database connection established
- ✅ No authentication errors
- ✅ Service remains stable
- ✅ Root cause identified and documented

## Risk Assessment
- **High Risk**: Service down, blocking development
- **Medium Risk**: Configuration complexity
- **Low Risk**: Well-documented solution available (FM-020)

## Resources
- **FM-020 Documentation**: Complete solution available
- **Working Configuration**: Proven to work
- **Supabase Projects**: Two projects to compare
- **Error Pattern**: Identical to resolved incident

---

**Status**: CRITICAL - Immediate Action Required  
**Priority**: P0 - Service Down  
**Assigned**: Development Team  
**Due Date**: 2025-09-30 EOD
