# Deployment Agent Quick Start Guide

## Overview
This guide explains how to use the deployment agent to safely deploy and validate the Insurance Navigator system. The agent will guide you through the deployment process while requiring your verification at critical points.

## Prerequisites
1. Access to Supabase dashboard
2. Access to Vercel dashboard
3. Access to monitoring systems
4. All required API keys and credentials
5. Browser for manual verification

## MVP Deployment Process

### 1. Environment Setup
```markdown
📍 Required Checks:
- [ ] Supabase project ID configured
- [ ] Environment variables set
- [ ] API keys validated
- [ ] Local development stack verified

📋 Validation Steps:
1. Run environment validation script
2. Test local development stack
3. Verify API key permissions
```

### 2. Database Deployment
```markdown
📍 Required Checks:
- [ ] MVP schema validated
- [ ] Basic RLS policies enabled
- [ ] Storage buckets configured
- [ ] Backup procedure tested

📋 Validation Steps:
1. Run schema validation
2. Test RLS policies
3. Verify storage access
```

### 3. Edge Functions
```markdown
📍 Required Checks:
- [ ] Processing supervisor deployed
- [ ] Document parser working
- [ ] Chunking service active
- [ ] Basic vectorization functional

📋 Validation Steps:
1. Deploy edge functions
2. Test processing pipeline
3. Verify error handling
```

### 4. Frontend Deployment
```markdown
📍 Required Checks:
- [ ] Authentication flow working
- [ ] Document upload functional
- [ ] Processing status visible
- [ ] Basic error handling active

📋 Validation Steps:
1. Build and deploy frontend
2. Test user workflows
3. Verify UI feedback
```

### 5. Monitoring Setup
```markdown
📍 Required Checks:
- [ ] Basic error tracking enabled
- [ ] Critical alerts configured
- [ ] Performance metrics active
- [ ] Log ingestion working

📋 Validation Steps:
1. Configure monitoring
2. Test alert triggers
3. Verify metric collection
```

## MVP Communication Protocol

### Success Report
```markdown
✅ Component: [Name]
📋 Status: Deployed to [Environment]
🔍 Tests: [Pass/Fail]
📊 Metrics: Within MVP thresholds
```

### Issue Report
```markdown
❌ Error: [Description]
📍 Component: [Name]
🔍 Impact: [Scope]
📋 Action: [Next Steps]
```

## MVP Rollback Procedures

### Database Rollback
```bash
./scripts/deployment/rollback-production-schema.sh
```

### Edge Functions Rollback
```bash
supabase functions delete [function-name]
supabase functions deploy [function-name] --version [previous-version]
```

### Frontend Rollback
```bash
vercel rollback
```

## Support Contacts
- DevOps: [Contact]
- Backend: [Contact]
- Frontend: [Contact]

Remember:
1. Follow MVP validation thresholds
2. Focus on core functionality
3. Document all issues
4. Keep security in mind
5. Maintain deployment logs

## Verification Process

### 1. Environment Verification
When the agent asks you to verify environment:
1. Open Supabase dashboard
2. Navigate to Project Settings
3. Verify API keys and permissions
4. Confirm to agent: "Environment verified"

### 2. Database Verification
When checking database deployment:
1. Open Supabase Table Editor
2. Verify schema matches documentation
3. Check RLS policies
4. Confirm to agent: "Database verified"

### 3. Edge Function Verification
For Edge Function checks:
1. Open Edge Functions dashboard
2. Check deployment status
3. Review function logs
4. Confirm to agent: "Edge Functions verified"

### 4. Frontend Verification
When validating frontend:
1. Open production URL
2. Test user flows
3. Check document upload
4. Confirm to agent: "Frontend verified"

### 5. Monitoring Verification
For monitoring validation:
1. Open monitoring dashboards
2. Check alert configurations
3. Verify log collection
4. Confirm to agent: "Monitoring verified"

## Communication Guidelines

### 1. Reporting Success
```markdown
"Verified: [Component] is working as expected"
"Confirmed: [Action] completed successfully"
"Checked: [Item] meets requirements"
```

### 2. Reporting Issues
```markdown
"Issue found: [Description of problem]"
"Error in: [Component/Step]"
"Need assistance with: [Specific task]"
```

### 3. Asking Questions
```markdown
"Please clarify: [Specific point]"
"How do I verify: [Specific check]"
"What should I do if: [Scenario]"
```

## Emergency Procedures

### 1. If You Need to Stop
```markdown
Tell the agent: "STOP deployment process"
Reason: [Explain why]
```

### 2. If You Find an Issue
```markdown
Tell the agent: "Issue detected in [component]"
Details: [Describe the issue]
```

### 3. If You Need to Rollback
```markdown
Tell the agent: "Initiate rollback procedure"
Reason: [Explain why]
```

## Completion Checklist

Before concluding deployment:
- [ ] All verification steps completed
- [ ] No pending security issues
- [ ] All systems operational
- [ ] Monitoring active
- [ ] Documentation updated

## Support
If you need assistance:
1. Check the deployment documentation
2. Review error messages carefully
3. Provide clear details to the agent
4. Contact the development team if needed

Remember:
- Take your time with verifications
- Don't skip any checks
- Document any issues
- Keep security in mind
- Follow the agent's instructions carefully 