# Security Guidelines

**Date**: January 3, 2025  
**Status**: ✅ **ACTIVE**  
**Priority**: HIGH  
**Scope**: Repository security and sensitive data management  

---

## Executive Summary

This document establishes security guidelines for the Insurance Navigator project to prevent sensitive data exposure and maintain secure development practices.

---

## Sensitive Data Management

### **What Constitutes Sensitive Data**

#### **1. Credentials and API Keys**
- Supabase URLs: `https://*.supabase.co`
- JWT Tokens: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- API Keys: `sk-prod-*`, `sk-ant-prod-*`, `llx-prod-*`
- Database passwords and connection strings
- Service API keys (Resend, SendGrid, Postmark)

#### **2. Service URLs**
- Production service URLs: `https://*.onrender.com`
- Database URLs: `postgresql://user:password@host:port/database`
- Internal service endpoints

#### **3. Configuration Data**
- Hardcoded environment-specific values
- Production database schemas
- Service-specific configuration

---

## Environment Variable Management

### **Best Practices**

#### **1. Use Environment Variables**
```bash
# ✅ CORRECT - Use environment variables
SUPABASE_URL=${SUPABASE_URL}
DATABASE_URL=${DATABASE_URL}
OPENAI_API_KEY=${OPENAI_API_KEY}

# ❌ INCORRECT - Hardcoded values
SUPABASE_URL=https://your-project.supabase.co
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
OPENAI_API_KEY=sk-prod-abc123...
```

#### **2. Environment File Structure**
```
.env                    # Base configuration (shared)
.env.development        # Development-specific
.env.testing           # Testing-specific  
.env.production        # Production-specific
.env.example           # Template with placeholders
```

#### **3. Placeholder Values**
```bash
# ✅ CORRECT - Placeholder values in examples
SUPABASE_URL=https://your-project.supabase.co
DATABASE_URL=postgresql://user:password@host:port/database
OPENAI_API_KEY=your_openai_api_key_here

# ❌ INCORRECT - Real values in examples
SUPABASE_URL=https://your-project.supabase.co
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
OPENAI_API_KEY=sk-prod-abc123...
```

---

## Configuration File Guidelines

### **1. Vercel Configuration**
```json
// ✅ CORRECT - Use environment variable substitution
{
  "build": {
    "env": {
      "NEXT_PUBLIC_SUPABASE_URL": "$NEXT_PUBLIC_SUPABASE_URL",
      "NEXT_PUBLIC_API_BASE_URL": "$NEXT_PUBLIC_API_BASE_URL"
    }
  }
}

// ❌ INCORRECT - Hardcoded values
{
  "build": {
    "env": {
      "NEXT_PUBLIC_SUPABASE_URL": "https://your-project.supabase.co",
      "NEXT_PUBLIC_API_BASE_URL": "https://insurance-navigator-api.onrender.com"
    }
  }
}
```

### **2. Docker Configuration**
```yaml
# ✅ CORRECT - Use environment variables
services:
  api:
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - DATABASE_URL=${DATABASE_URL}

# ❌ INCORRECT - Hardcoded values
services:
  api:
    environment:
      - SUPABASE_URL=https://your-project.supabase.co
      - DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

### **3. Render Configuration**
```yaml
# ✅ CORRECT - Use environment variables
services:
  - name: insurance-navigator-api
    envVars:
      - key: SUPABASE_URL
        value: ${SUPABASE_URL}
      - key: DATABASE_URL
        value: ${DATABASE_URL}

# ❌ INCORRECT - Hardcoded values
services:
  - name: insurance-navigator-api
    envVars:
      - key: SUPABASE_URL
        value: https://your-project.supabase.co
      - key: DATABASE_URL
        value: postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

---

## Documentation Guidelines

### **1. Example Files**
- Always use placeholder values
- Never include real credentials
- Provide clear instructions for setup

### **2. Configuration Guides**
- Use generic examples
- Reference environment variables
- Include setup instructions

### **3. API Documentation**
- Use placeholder URLs
- Include environment variable references
- Provide example configurations

---

## Git Security

### **1. Pre-commit Hooks**
The repository includes pre-commit hooks that:
- Scan for sensitive data patterns
- Prevent commits with hardcoded credentials
- Warn about hardcoded URLs
- Enforce security best practices

### **2. Commit Messages**
```bash
# ✅ CORRECT - Descriptive commit messages
git commit -m "feat: add environment variable support for Supabase configuration"

# ❌ INCORRECT - Vague commit messages
git commit -m "fix stuff"
```

### **3. Branch Protection**
- Never commit sensitive data to any branch
- Use feature branches for development
- Review all changes before merging

---

## Development Workflow

### **1. Local Development**
```bash
# Copy example file
cp .env.example .env.development

# Edit with your local values
# Never commit .env files
echo ".env*" >> .gitignore
```

### **2. Testing**
```bash
# Use test-specific environment
cp .env.example .env.testing

# Use placeholder values for testing
# Never use production credentials in tests
```

### **3. Production Deployment**
```bash
# Set environment variables in deployment platform
# Never hardcode in configuration files
# Use platform-specific environment management
```

---

## Monitoring and Alerting

### **1. Continuous Scanning**
- Regular scans for sensitive data patterns
- Automated alerts for potential exposure
- Repository access monitoring

### **2. Access Control**
- Review repository access regularly
- Use least privilege principle
- Monitor commit activity

### **3. Audit Logging**
- Track all repository changes
- Monitor environment variable usage
- Log security-related events

---

## Incident Response

### **1. If Sensitive Data is Exposed**
1. **Immediate Action**: Rotate all exposed credentials
2. **Assessment**: Determine scope of exposure
3. **Cleanup**: Remove sensitive data from repository
4. **Prevention**: Implement additional safeguards

### **2. Credential Rotation**
- Supabase: Rotate API keys and JWT secrets
- Database: Change passwords and connection strings
- API Services: Rotate all service keys
- Email Services: Rotate email service keys

### **3. Repository Cleanup**
- Use BFG Repo-Cleaner for history cleanup
- Force push cleaned history
- Notify team of changes
- Update documentation

---

## Tools and Resources

### **1. Security Tools**
- **BFG Repo-Cleaner**: Remove sensitive data from git history
- **Git Hooks**: Prevent future exposure
- **Environment Scanners**: Detect sensitive data patterns

### **2. Documentation**
- Security cleanup tracking document
- Environment configuration guides
- Deployment best practices

### **3. Training**
- Security awareness training
- Environment management best practices
- Incident response procedures

---

## Compliance

### **1. HIPAA Considerations**
- Healthcare data protection requirements
- Access control and audit logging
- Data encryption and secure transmission

### **2. Privacy Regulations**
- Data minimization principles
- User consent management
- Right to deletion implementation

### **3. Security Standards**
- Industry best practices
- Regular security assessments
- Continuous improvement

---

## Success Criteria

### **✅ Security Measures Active**
- [x] Pre-commit hooks preventing sensitive data exposure
- [x] Environment variable management established
- [x] Documentation sanitized of sensitive information
- [x] Monitoring and alerting implemented

### **✅ Prevention Measures**
- [x] Git hooks preventing future exposure
- [x] Environment management procedures established
- [x] Security guidelines documented
- [x] Team training materials created

### **✅ Response Capabilities**
- [x] Incident response procedures documented
- [x] Credential rotation procedures established
- [x] Repository cleanup procedures documented
- [x] Monitoring and alerting configured

---

**Status**: ✅ **ACTIVE**  
**Risk Level**: **MANAGED** - Comprehensive security measures implemented  
**Compliance**: **HIPAA-READY** - Healthcare data protection measures in place  
**Maintenance**: **ONGOING** - Regular reviews and updates required  

---

*These security guidelines ensure the Insurance Navigator project maintains the highest standards of data protection and security throughout development and deployment.*
