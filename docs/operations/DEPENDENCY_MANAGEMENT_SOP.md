# Dependency Management Standard Operating Procedure (SOP)

**Version**: 1.0  
**Date**: January 3, 2025  
**Based on**: Lessons learned from FM032, FM033, FM034 failure modes  
**Purpose**: Prevent dependency conflicts and ensure stable deployments  

---

## Executive Summary

This SOP establishes systematic dependency management practices to prevent the types of errors encountered in FM032-FM034. It provides clear procedures for dependency updates, validation, and deployment to ensure consistent, conflict-free environments.

---

## Background: Failure Mode Analysis

### **FM032**: Vercel deployment configuration issues
- **Root Cause**: Missing dependencies and module resolution errors
- **Lesson**: Dependency validation must occur before deployment

### **FM033**: Supabase authentication 400 errors  
- **Root Cause**: Configuration mismatches between environments
- **Lesson**: Environment consistency validation is critical

### **FM034**: Chat API 401 authorization errors
- **Root Cause**: Implementation errors in authentication service
- **Lesson**: Code changes must be validated against dependency compatibility

### **Current Issue**: React version conflict
- **Root Cause**: Incompatible React 19 with @testing-library/react < 16.0.0
- **Lesson**: Peer dependency validation must be systematic

---

## Dependency Management Principles

### **1. Compatibility First**
- Always validate peer dependency compatibility before updates
- Maintain compatibility matrix for major dependencies
- Test in clean environments before deployment

### **2. Systematic Validation**
- Run dependency validation before every build/deployment
- Use automated tools to detect conflicts early
- Document all dependency changes and their impact

### **3. Environment Consistency**
- Ensure all environments use identical dependency versions
- Validate configuration consistency across environments
- Test deployment process in staging before production

---

## Dependency Compatibility Matrix

### **React Ecosystem**
| React Version | @testing-library/react | @types/react | Notes |
|---------------|------------------------|--------------|-------|
| ^18.0.0       | ^14.0.0               | ^18.0.0      | Stable |
| ^19.0.0       | ^16.0.0               | ^19.0.0      | Latest |

### **Supabase Ecosystem**
| Supabase JS | Next.js | React | Notes |
|-------------|---------|-------|-------|
| ^2.50.0     | ^15.0.0 | ^18.0.0 or ^19.0.0 | Compatible |

### **Build Tools**
| Tool | Version | Compatibility |
|------|---------|---------------|
| Next.js | ^15.3.0 | React 18/19 |
| TypeScript | ^5.0.0 | All React versions |
| Tailwind | ^3.4.0 | All React versions |

---

## Dependency Update Procedures

### **Phase 1: Pre-Update Validation**

1. **Check Current Dependencies**
   ```bash
   npm ls --depth=0
   npm audit
   ```

2. **Review Compatibility Matrix**
   - Check if new version is compatible with existing dependencies
   - Verify peer dependency requirements
   - Review breaking changes in changelog

3. **Create Update Branch**
   ```bash
   git checkout -b update/dependency-name-version
   ```

### **Phase 2: Update Process**

1. **Update Package.json**
   ```bash
   npm install dependency@version
   ```

2. **Run Validation Script**
   ```bash
   npm run validate:deps
   ```

3. **Test Build Process**
   ```bash
   npm run build
   npm run test
   ```

4. **Test in Clean Environment**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

### **Phase 3: Deployment Validation**

1. **Staging Deployment Test**
   - Deploy to staging environment
   - Run end-to-end tests
   - Validate all functionality

2. **Production Deployment**
   - Deploy to production
   - Monitor for errors
   - Validate functionality

---

## Automated Validation Pipeline

### **Pre-commit Hooks**
```json
{
  "husky": {
    "hooks": {
      "pre-commit": "npm run validate:deps"
    }
  }
}
```

### **CI/CD Integration**
```yaml
# .github/workflows/dependency-validation.yml
name: Dependency Validation
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run validate:deps
      - run: npm run build
```

### **Validation Script Features**
- Dependency conflict detection
- Security vulnerability scanning
- React version compatibility validation
- Environment variable validation
- Peer dependency verification

---

## Environment Configuration Management

### **Environment Variables Validation**
Required variables for all environments:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_BASE_URL`
- `NODE_ENV`

### **Configuration Consistency Checks**
1. **Supabase Configuration**
   - Verify URL format and accessibility
   - Validate API key permissions
   - Test authentication endpoints

2. **Vercel Configuration**
   - Ensure vercel.json is in correct location (ui/)
   - Validate build commands and environment variables
   - Test deployment process

3. **Docker Configuration**
   - Verify Dockerfile dependencies
   - Test container build process
   - Validate environment variable injection

---

## Error Prevention Checklist

### **Before Any Dependency Update**
- [ ] Review compatibility matrix
- [ ] Check peer dependency requirements
- [ ] Read changelog for breaking changes
- [ ] Create update branch
- [ ] Run current validation suite

### **During Update Process**
- [ ] Update package.json
- [ ] Run `npm run validate:deps`
- [ ] Test build process
- [ ] Run test suite
- [ ] Test in clean environment

### **Before Deployment**
- [ ] Deploy to staging
- [ ] Run end-to-end tests
- [ ] Validate all functionality
- [ ] Check error logs
- [ ] Monitor performance metrics

### **After Deployment**
- [ ] Monitor error rates
- [ ] Validate user functionality
- [ ] Check performance metrics
- [ ] Document any issues
- [ ] Update compatibility matrix if needed

---

## Troubleshooting Guide

### **Common Dependency Conflicts**

1. **React Version Conflicts**
   ```bash
   # Error: peer react@"^18.0.0" from @testing-library/react
   # Solution: Update @testing-library/react to version supporting React 19
   npm install @testing-library/react@^16.0.0
   ```

2. **TypeScript Version Conflicts**
   ```bash
   # Error: TypeScript version mismatch
   # Solution: Align TypeScript versions across all packages
   npm install typescript@^5.0.0
   ```

3. **Next.js Version Conflicts**
   ```bash
   # Error: Next.js version incompatible
   # Solution: Update to compatible Next.js version
   npm install next@^15.3.0
   ```

### **Environment Configuration Issues**

1. **Supabase Authentication Errors**
   - Verify `NEXT_PUBLIC_SUPABASE_URL` format
   - Check `NEXT_PUBLIC_SUPABASE_ANON_KEY` validity
   - Test Supabase connection

2. **Vercel Deployment Failures**
   - Ensure vercel.json is in ui/ directory
   - Verify build commands are correct
   - Check environment variable configuration

3. **Docker Build Failures**
   - Verify Dockerfile dependencies
   - Check base image compatibility
   - Validate environment variable injection

---

## Monitoring and Alerting

### **Dependency Monitoring**
- Automated dependency update notifications
- Security vulnerability alerts
- Peer dependency conflict detection
- Build failure notifications

### **Performance Monitoring**
- Build time tracking
- Bundle size monitoring
- Runtime error tracking
- User experience metrics

---

## Documentation Requirements

### **Update Documentation**
- Document all dependency changes
- Update compatibility matrix
- Record breaking changes
- Maintain changelog

### **Incident Documentation**
- Document all dependency-related incidents
- Record root cause analysis
- Update prevention measures
- Share lessons learned

---

## Success Metrics

### **Prevention Metrics**
- Zero dependency conflicts in production
- 100% validation script pass rate
- Zero security vulnerabilities in dependencies
- Consistent environment configurations

### **Efficiency Metrics**
- Reduced deployment failures
- Faster dependency update process
- Improved build success rate
- Reduced troubleshooting time

---

## Review and Updates

### **Regular Reviews**
- Monthly dependency audit
- Quarterly compatibility matrix review
- Annual SOP review and update
- Continuous improvement based on incidents

### **Update Triggers**
- New major dependency versions
- Security vulnerability discoveries
- Deployment failure incidents
- Process improvement opportunities

---

## Contact Information

**Primary Contact**: Development Team Lead  
**Secondary Contact**: DevOps Team  
**Escalation**: Technical Architecture Team  

---

**Document Status**: ✅ **ACTIVE**  
**Last Updated**: January 3, 2025  
**Next Review**: February 3, 2025  
**Approved By**: Development Team  

---

*This SOP is based on comprehensive analysis of FM032-FM034 failure modes and establishes systematic practices to prevent similar issues in the future.*
