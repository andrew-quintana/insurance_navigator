# FM-033 Hypotheses Ledger

## Investigation Status: ACTIVE

**Date**: January 2025  
**Investigation**: Supabase Authentication 400 Errors  
**Status**: Hypotheses formulation and testing phase  

---

## Hypothesis Tracking

### **H1: Supabase API Key Configuration Issues**
**Status**: 🔍 PENDING TESTING  
**Priority**: HIGH  
**Confidence**: MEDIUM  

**Theory**: The Supabase API key lacks appropriate roles or permissions, causing 400 Bad Request errors during authentication.

**Evidence Supporting**:
- 400 errors typically indicate authorization problems
- Authentication token exchange failing
- All environment variables set to production values

**Evidence Against**:
- API key worked in previous deployments
- No recent changes to Supabase configuration

**Test Plan**:
1. Check API key permissions in Supabase dashboard
2. Verify roles and policies for the anon key
3. Test API key with direct curl requests
4. Review Supabase Log Explorer for authorization errors

**Expected Outcome**: API key permissions will be insufficient or misconfigured

---

### **H2: JWT Secret Configuration Mismatch**
**Status**: 🔍 PENDING TESTING  
**Priority**: HIGH  
**Confidence**: MEDIUM  

**Theory**: JWT secret mismatch between Vercel environment and Supabase configuration, causing token validation failures.

**Evidence Supporting**:
- Token endpoint returning 400 suggests invalid tokens
- Authentication state changes to "INITIAL_SESSION" then fails
- Environment variables may not match Supabase JWT settings

**Evidence Against**:
- JWT configuration hasn't changed recently
- Same Supabase instance used in previous working deployments

**Test Plan**:
1. Verify JWT secret in Supabase dashboard
2. Check JWT configuration in Vercel environment
3. Test token generation and validation
4. Compare JWT settings between environments

**Expected Outcome**: JWT secret mismatch will be identified

---

### **H3: Environment Variable Issues**
**Status**: 🔍 PENDING TESTING  
**Priority**: MEDIUM  
**Confidence**: LOW  

**Theory**: Environment variables not properly set or accessible at runtime in Vercel preview environment.

**Evidence Supporting**:
- Preview environment may have different variable scope
- Variables set to production values but authentication failing
- Build vs runtime environment mismatch possible

**Evidence Against**:
- Variables appear to be set correctly in Vercel dashboard
- No obvious typos or incorrect names

**Test Plan**:
1. Verify environment variables in Vercel dashboard
2. Test variable availability at runtime
3. Check for typos or incorrect variable names
4. Validate variable values match production settings

**Expected Outcome**: Environment variable configuration issues will be found

---

### **H4: Authentication Request Format Issues**
**Status**: 🔍 PENDING TESTING  
**Priority**: MEDIUM  
**Confidence**: MEDIUM  

**Theory**: Malformed authentication request payloads or missing required parameters causing 400 errors.

**Evidence Supporting**:
- 400 errors typically indicate client-side issues
- Authentication request structure may be incorrect
- Missing required parameters in auth requests

**Evidence Against**:
- Authentication code hasn't changed recently
- Same request format used in previous working deployments

**Test Plan**:
1. Review authentication request payloads
2. Check for missing required parameters
3. Validate request structure and format
4. Test with different authentication methods

**Expected Outcome**: Authentication request format issues will be identified

---

### **H5: Preview/Production Environment Conflicts**
**Status**: 🔍 PENDING TESTING  
**Priority**: LOW  
**Confidence**: LOW  

**Theory**: Both preview and production environments accessing the same Supabase instance causing conflicts.

**Evidence Supporting**:
- Shared resources may cause conflicts
- Rate limiting or session conflicts possible
- Both environments using same Supabase instance

**Evidence Against**:
- Supabase should handle multiple environments
- No rate limiting issues in previous deployments
- Shared resources are common in Supabase

**Test Plan**:
1. Check for rate limiting on Supabase
2. Review shared resource access
3. Test with different authentication methods
4. Verify session management

**Expected Outcome**: Environment conflicts will be minimal or non-existent

---

## Testing Schedule

### **Phase 1: Supabase Configuration (Day 1)**
- [ ] Test H1: API key permissions
- [ ] Test H2: JWT secret configuration
- [ ] Review Supabase Log Explorer

### **Phase 2: Environment Variables (Day 1)**
- [ ] Test H3: Environment variable configuration
- [ ] Verify variable availability at runtime
- [ ] Check variable values and formats

### **Phase 3: Authentication Flow (Day 2)**
- [ ] Test H4: Authentication request format
- [ ] Review authentication payloads
- [ ] Test different authentication methods

### **Phase 4: Conflict Detection (Day 2)**
- [ ] Test H5: Environment conflicts
- [ ] Check rate limiting and shared resources
- [ ] Verify session management

---

## Results Tracking

### **H1 Results**: TBD
**Test Date**: TBD  
**Outcome**: TBD  
**Confidence**: TBD  
**Next Steps**: TBD  

### **H2 Results**: TBD
**Test Date**: TBD  
**Outcome**: TBD  
**Confidence**: TBD  
**Next Steps**: TBD  

### **H3 Results**: TBD
**Test Date**: TBD  
**Outcome**: TBD  
**Confidence**: TBD  
**Next Steps**: TBD  

### **H4 Results**: TBD
**Test Date**: TBD  
**Outcome**: TBD  
**Confidence**: TBD  
**Next Steps**: TBD  

### **H5 Results**: TBD
**Test Date**: TBD  
**Outcome**: TBD  
**Confidence**: TBD  
**Next Steps**: TBD  

---

## Investigation Notes

### **Key Observations**
- Authentication state changes to "INITIAL_SESSION" then fails
- Token endpoint returning 400 Bad Request
- All environment variables set to production values
- Preview environment accessible but authentication failing

### **Critical Questions**
1. Are Supabase API key permissions correct?
2. Is JWT secret configuration aligned?
3. Are environment variables properly set?
4. Is authentication request format correct?
5. Are there environment conflicts?

### **Next Steps**
1. Begin systematic testing of hypotheses
2. Document all test results
3. Update confidence levels based on evidence
4. Refine hypotheses as new information emerges
5. Focus on highest priority hypotheses first

---

**Last Updated**: January 2025  
**Next Review**: After Phase 1 testing completion  
**Investigation Lead**: TBD
