# Investigation Prompt 1.3: Active Service Assessment

**Prompt ID**: SECURITY-P1.3  
**Area**: Active Service Impact Evaluation  
**Priority**: 🚨 CRITICAL  
**Estimated Time**: 2 hours  

## Investigation Objective

Determine which of the exposed credentials are actively being used by deployed services, assess the immediate impact of credential exposure, and identify which services need urgent credential rotation.

## Context and Background

**Known Exposed Credentials**:
- OpenAI API Key: `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`
- Anthropic API Key: `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`
- Database Password: `tukwof-pyVxo5-qejnoj`
- Document Encryption Key: `iSUAmk2NHMNW5bsn8F0UnPSCk9L+IxZhu/v/UyDwFcc=`

**Current Deployment Context**:
- Primary staging service: `insurance-navigator-staging-api.onrender.com`
- Frontend: `insurance-navigator.vercel.app`
- Current branch: `deployment/cloud-infrastructure`

## Investigation Tasks

### Task 1.3.1: Render Deployment Analysis

Check current Render deployments and their environment variables:

```bash
# Check Render configuration files
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "render.yaml" -o -name "*render*" | grep -v node_modules

# Look for Render-specific configuration
grep -r "render" /Users/aq_home/1Projects/accessa/insurance_navigator/config/ 2>/dev/null || echo "No config directory or render references"

# Check for deployment scripts
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "deploy*" -o -name "*deployment*" | grep -v node_modules
```

**Manual Render Dashboard Investigation Required**:
> **CRITICAL**: A team member with Render dashboard access must check:
> 1. Login to Render dashboard
> 2. Navigate to `insurance-navigator-staging-api` service
> 3. Check Environment Variables tab
> 4. Document which exposed credentials are currently set
> 5. Note the last deployment date
> 6. Check service logs for recent activity

### Task 1.3.2: Vercel Deployment Analysis

Check Vercel deployments and configuration:

```bash
# Look for Vercel configuration files
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "vercel.json" -o -name ".vercel*" | grep -v node_modules

# Check for Vercel-specific environment variable references
grep -r "NEXT_PUBLIC" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Look for Vercel deployment configuration
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "package.json" -exec grep -l "vercel" {} \;
```

**Manual Vercel Dashboard Investigation Required**:
> **CRITICAL**: A team member with Vercel dashboard access must check:
> 1. Login to Vercel dashboard  
> 2. Find the `insurance-navigator` project
> 3. Check Environment Variables settings
> 4. Verify which credentials are deployed to production/preview
> 5. Check deployment history and activity

### Task 1.3.3: Application Code Analysis

Examine application code to understand credential usage:

```bash
# Find environment variable usage in application code
grep -r -E "(process\.env|os\.environ)" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Look for OpenAI API usage
grep -r -i "openai" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Look for Anthropic API usage  
grep -r -i "anthropic" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Look for Supabase usage
grep -r -i "supabase" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Look for document encryption usage
grep -r -i "encrypt" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git
```

### Task 1.3.4: Service Configuration Analysis

Check for service-specific configuration and startup files:

```bash
# Check for Docker configuration
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "Dockerfile*" -o -name "docker-compose*"

# Check for application startup files
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "server.*" -o -name "app.*" -o -name "main.*" | grep -v node_modules

# Look for environment loading in application
grep -r -E "(dotenv|loadenv|env)" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git | head -20
```

### Task 1.3.5: Database Connection Assessment

Analyze database connection usage:

```bash
# Look for database connection code
grep -r -E "(createClient|postgres|pool|connection)" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Check for Supabase client initialization
grep -r -E "(supabase.*createClient|new.*supabase)" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Look for database URL usage
grep -r "DATABASE_URL" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git
```

### Task 1.3.6: External Service Integration Analysis

Check for external service integrations that use the exposed credentials:

```bash
# Look for API key usage patterns
grep -r -E "(api.*key|apikey)" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Check for LlamaCloud/LlamaParse usage
grep -r -E "(llama|parse)" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Look for LangChain usage
grep -r -i "langchain" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git
```

## Investigation Questions

1. **Active Usage**: Which exposed credentials are currently active in deployed services?
2. **Service Dependencies**: Which services would break if credentials were rotated immediately?
3. **Environment Segregation**: Are different credentials used for staging vs production?
4. **Fallback Mechanisms**: Do services have fallback authentication or graceful degradation?
5. **Impact Assessment**: What is the immediate impact of rotating each credential?

## Expected Findings Format

```markdown
## Active Service Assessment Results

### Render Deployment Status
- **Service Name**: insurance-navigator-staging-api
- **Environment Variables**: [list of exposed credentials currently set]
- **Last Deployment**: [date/time]
- **Service Status**: [running/stopped/failed]
- **Recent Activity**: [API calls/errors in logs]

### Vercel Deployment Status  
- **Project Name**: insurance-navigator
- **Environment Variables**: [list of exposed credentials in Vercel]
- **Production Environment**: [credential usage status]
- **Preview Environment**: [credential usage status]

### Credential Usage Analysis
For each exposed credential:
- **OpenAI API Key**:
  - Used in: [list of services/files]
  - Critical path: [Yes/No - would service break without it]
  - Recent usage: [evidence from logs/code]
  
- **Anthropic API Key**:
  - Used in: [list of services/files] 
  - Critical path: [Yes/No]
  - Recent usage: [evidence]

### Impact Assessment Matrix
| Credential | Service | Impact Level | Rotation Urgency | Estimated Downtime |
|------------|---------|--------------|------------------|-------------------|
| OpenAI Key | API Service | HIGH | IMMEDIATE | 15 minutes |
| Anthropic Key | API Service | MEDIUM | HIGH | 10 minutes |
| DB Password | All Services | CRITICAL | IMMEDIATE | 30 minutes |
```

## Manual Dashboard Investigations Required

**Render Dashboard Checklist**:
- [ ] Login to Render dashboard
- [ ] Check `insurance-navigator-staging-api` service environment variables
- [ ] Document which exposed credentials are currently active
- [ ] Check service health and recent deployments
- [ ] Review service logs for recent API activity
- [ ] Check auto-deploy settings and branch configuration

**Vercel Dashboard Checklist**:
- [ ] Login to Vercel dashboard
- [ ] Find `insurance-navigator` project
- [ ] Check environment variables for production
- [ ] Check environment variables for preview environments  
- [ ] Review deployment history and frequency
- [ ] Check domain configuration and active deployments

## Risk Assessment Criteria

**Critical Risk Indicators**:
- Credential is required for core service functionality
- Service is currently active and receiving traffic
- No immediate fallback or redundancy available
- Credential rotation would cause service outage

**High Risk Indicators**:
- Credential is used but service has graceful degradation
- Alternative authentication methods available
- Service can operate with reduced functionality

**Medium Risk Indicators**:
- Credential is configured but not actively used
- Service has multiple authentication options
- Non-critical service functionality

## Deliverables

1. **Service Status Report**: Current status of all deployed services
2. **Credential Usage Matrix**: Which credentials are used by which services
3. **Impact Assessment**: Estimated downtime and service disruption for credential rotation
4. **Rotation Priority List**: Ordered list of credentials to rotate based on risk
5. **Service Health Baseline**: Current service performance metrics before rotation

## Success Criteria

- ✅ All deployed services identified and analyzed
- ✅ Credential usage confirmed for each exposed credential  
- ✅ Impact assessment completed for credential rotation
- ✅ Service health baseline established
- ✅ Rotation priority list created with timeline estimates

## Next Steps

Upon completion:
1. Create credential rotation plan with prioritized timeline
2. Notify service owners of required maintenance windows
3. Proceed to Investigation Prompt 1.4 (Risk Assessment)
4. Prepare for emergency credential rotation if critical services are affected

---

**Time Allocation**: 2 hours maximum  
**Tools Required**: CLI tools, dashboard access, code analysis  
**Output**: Active service assessment report with rotation plan