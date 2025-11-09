# Git History Cleanup Plan - Sensitive Data Removal

**Date**: January 3, 2025  
**Status**: 📋 **ACTION PLAN READY**  
**Priority**: CRITICAL  
**Scope**: Remove sensitive data from entire git history  

---

## Executive Summary

**Objective**: Remove all sensitive information from git commit history  
**Method**: BFG Repo-Cleaner for comprehensive history cleanup  
**Risk**: Repository history will be rewritten (requires team coordination)  
**Timeline**: Immediate execution required  

---

## Sensitive Data Patterns Identified

### **1. Supabase Credentials**
```bash
# Patterns to remove:
https://your-project.supabase.co
https://your-staging-project.supabase.co
https://prod-project.supabase.co
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
```

### **2. Database URLs**
```bash
# Patterns to remove:
postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
postgresql://postgres:password@prod-db.example.com:5432/insurance_navigator_prod
```

### **3. API Keys**
```bash
# Patterns to remove:
sk-prod-
sk-ant-prod-
llx-prod-
your_prod_resend_api_key_here
your_sendgrid_api_key_here
your_postmark_api_key_here
```

### **4. Service URLs**
```bash
# Patterns to remove:
https://insurance-navigator-api.onrender.com
https://insurance-navigator-staging-api.onrender.com
```

---

## Cleanup Execution Plan

### **Phase 1: Preparation**
1. **Backup Repository**: Create full backup before cleanup
2. **Team Notification**: Inform all team members of cleanup
3. **Access Review**: Document who has repository access
4. **Credential Inventory**: List all credentials to be rotated

### **Phase 2: BFG Cleanup**
```bash
# Install BFG Repo-Cleaner
brew install bfg  # macOS
# or download from: https://rtyley.github.io/bfg-repo-cleaner/

# Create sensitive data file
cat > sensitive-data.txt << EOF
https://your-project.supabase.co
https://your-staging-project.supabase.co
https://prod-project.supabase.co
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
postgresql://postgres:password@prod-db.example.com:5432/insurance_navigator_prod
sk-prod-
sk-ant-prod-
llx-prod-
your_prod_resend_api_key_here
your_sendgrid_api_key_here
your_postmark_api_key_here
https://insurance-navigator-api.onrender.com
https://insurance-navigator-staging-api.onrender.com
EOF

# Run BFG cleanup
java -jar bfg.jar --replace-text sensitive-data.txt insurance_navigator.git

# Clean up and repack
cd insurance_navigator.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### **Phase 3: Force Push**
```bash
# Force push cleaned history
git push --force-with-lease origin main

# Verify cleanup
git log --all --full-history -S "supabase.co" --source --all
git log --all --full-history -S "sk-prod-" --source --all
```

---

## Credential Rotation Plan

### **Immediate Rotation Required**

#### **1. Supabase Credentials**
- **Project**: `your-project` (production)
- **Project**: `your-staging-project` (staging/wrong)
- **Action**: Rotate all API keys and JWT secrets
- **Impact**: All applications using these credentials

#### **2. Database Credentials**
- **Production DB**: `db.your-project.supabase.co`
- **Action**: Change database passwords
- **Impact**: All database connections

#### **3. API Service Keys**
- **OpenAI**: Rotate all API keys
- **Anthropic**: Rotate all API keys
- **Resend**: Rotate email service keys
- **SendGrid**: Rotate email service keys
- **Postmark**: Rotate email service keys

#### **4. Render Services**
- **API Service**: `insurance-navigator-api.onrender.com`
- **Staging API**: `insurance-navigator-staging-api.onrender.com`
- **Action**: Review and rotate service credentials

---

## File Sanitization Plan

### **Current Files to Clean**

#### **1. vercel.json**
```json
// Remove hardcoded Supabase credentials
// Use environment variables instead
{
  "build": {
    "env": {
      // Remove: "NEXT_PUBLIC_SUPABASE_URL": "https://..."
      // Remove: "NEXT_PUBLIC_SUPABASE_ANON_KEY": "eyJ..."
      "NEXT_PUBLIC_API_BASE_URL": "https://insurance-navigator-api.onrender.com",
      "NEXT_PUBLIC_API_URL": "https://insurance-navigator-api.onrender.com",
      "NODE_ENV": "staging"
    }
  }
}
```

#### **2. Environment Files**
```bash
# Replace sensitive values with placeholders
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
DATABASE_URL=postgresql://user:password@host:port/database
OPENAI_API_KEY=your_openai_api_key_here
```

#### **3. Configuration Files**
- Remove hardcoded credentials from all config files
- Use environment variables or secure configuration management
- Update documentation to use placeholder values

---

## Team Coordination Plan

### **Pre-Cleanup Communication**
1. **Team Meeting**: Schedule team meeting to discuss cleanup
2. **Timeline**: Communicate cleanup timeline and impact
3. **Access Review**: Review who needs repository access
4. **Backup Plan**: Ensure everyone has local backups

### **During Cleanup**
1. **Repository Lock**: Temporarily restrict repository access
2. **Progress Updates**: Regular updates on cleanup progress
3. **Issue Tracking**: Track any issues during cleanup
4. **Support**: Provide support for team members

### **Post-Cleanup**
1. **Team Sync**: Ensure all team members sync with cleaned history
2. **Access Review**: Review and update repository access
3. **Documentation**: Update all documentation with new procedures
4. **Training**: Train team on secure practices

---

## Verification Plan

### **Cleanup Verification**
```bash
# Verify sensitive data removal
git log --all --full-history -S "supabase.co" --source --all
git log --all --full-history -S "sk-prod-" --source --all
git log --all --full-history -S "postgresql://" --source --all
git log --all --full-history -S "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" --source --all

# Should return no results
```

### **Repository Health Check**
```bash
# Check repository integrity
git fsck --full
git gc --prune=now
git count-objects -vH
```

### **Access Verification**
1. **Repository Access**: Verify all team members can access cleaned repository
2. **Deployment**: Verify deployments work with new credentials
3. **Functionality**: Test all application functionality
4. **Monitoring**: Monitor for any issues post-cleanup

---

## Prevention Implementation

### **Git Hooks**
```bash
# Pre-commit hook to prevent sensitive data
#!/bin/bash
# .git/hooks/pre-commit

# Check for sensitive patterns
if git diff --cached --name-only | xargs grep -l "sk-prod-\|eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\|postgresql://\|supabase\.co"; then
    echo "ERROR: Sensitive data detected in commit!"
    echo "Please remove sensitive information before committing."
    exit 1
fi
```

### **Environment Management**
1. **Secrets Management**: Implement proper secrets management system
2. **Environment Variables**: Use environment variables for all sensitive data
3. **Configuration Templates**: Use templates with placeholder values
4. **Documentation**: Clear guidelines for handling sensitive data

### **Monitoring**
1. **Continuous Scanning**: Regular scans for sensitive data
2. **Access Monitoring**: Monitor repository access and changes
3. **Alert System**: Alerts for potential sensitive data exposure
4. **Audit Logging**: Comprehensive audit logging

---

## Success Criteria

### **Cleanup Complete** ✅
1. ✅ All sensitive data removed from git history
2. ✅ All exposed credentials rotated
3. ✅ All files sanitized of sensitive information
4. ✅ Repository integrity verified

### **Prevention Active** ✅
1. ✅ Git hooks preventing future exposure
2. ✅ Environment management procedures established
3. ✅ Monitoring and alerting implemented
4. ✅ Team trained on secure practices

---

## Risk Mitigation

### **Cleanup Risks**
- **Repository Corruption**: Mitigated by comprehensive backup
- **Team Disruption**: Mitigated by clear communication and support
- **Service Disruption**: Mitigated by credential rotation planning

### **Business Continuity**
- **Service Availability**: Ensure services remain available during cleanup
- **Data Integrity**: Verify data integrity throughout process
- **Access Control**: Maintain proper access control during cleanup

---

**Plan Status**: 📋 **READY FOR EXECUTION**  
**Risk Level**: **CRITICAL** - Sensitive data exposure requires immediate action  
**Execution Time**: **2-4 hours** - Including team coordination and verification  
**Business Impact**: **HIGH** - Prevents potential data breach  

---

*This cleanup plan provides comprehensive steps to remove sensitive data from git history while maintaining repository integrity and team productivity.*
