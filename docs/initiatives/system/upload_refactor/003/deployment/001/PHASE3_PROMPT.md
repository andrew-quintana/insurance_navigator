# Phase 3 Prompt: Security & Accessibility Validation

## Context for Claude Code Agent

**IMPORTANT**: You are implementing Phase 3 of cloud deployment testing. Phases 1 (environment setup) and 2 (integration & performance) must be completed successfully before starting this phase. This phase validates production-grade security measures and WCAG 2.1 AA accessibility compliance in the cloud environment.

## Required Reading Before Starting

**Essential Documents (READ THESE FIRST):**
1. `TODO001_phase2_notes.md` - Phase 2 integration testing results and findings
2. `TODO001_phase2_decisions.md` - Performance optimization decisions and configurations
3. `TODO001_phase2_handoff.md` - Security considerations identified in Phase 2
4. `docs/initiatives/system/upload_refactor/003/deployment/001/TODO001.md` - Phase 3 specific tasks and requirements

**Security and Compliance References:**
5. `docs/initiatives/system/upload_refactor/003/deployment/001/RFC001.md` - Security validation interfaces
6. WCAG 2.1 AA Guidelines (external reference for accessibility compliance)
7. OWASP Top 10 Security Risks (external reference for security testing)

## Your Primary Objectives

1. **Security Validation**: Test authentication security, data protection, and access controls
2. **Accessibility Compliance**: Validate WCAG 2.1 AA compliance across all interfaces
3. **Data Protection Testing**: Validate user data isolation, privacy measures, and GDPR compliance
4. **Comprehensive UX Testing**: Test user experience across devices and accessibility tools
5. **Production Security Preparation**: Document security measures for production deployment

## Implementation Priority Order

1. **Security Framework Implementation**: Automated security testing based on RFC001.md
2. **Authentication Security Testing**: Password policies, session management, access controls
3. **Data Protection Validation**: Encryption, user data isolation, privacy compliance
4. **Accessibility Testing Framework**: WCAG 2.1 AA automated compliance testing
5. **Accessibility Manual Testing Preparation**: Document requirements for developer testing
6. **Security Documentation**: Comprehensive security posture documentation

## Autonomous Testing Framework to Implement

Based on RFC001.md interface contracts:

```python
class CloudSecurityAccessibilityValidator:
    async def test_security_measures(self) -> SecurityResult
    async def test_accessibility_compliance(self) -> AccessibilityResult
    async def test_data_protection(self) -> DataProtectionResult

class SecurityValidator:
    async def test_authentication_security(self) -> AuthSecurityResult
    async def test_data_encryption(self) -> EncryptionResult
    async def test_access_controls(self) -> AccessControlResult
    async def test_input_validation(self) -> InputValidationResult

class AccessibilityValidator:
    async def test_wcag_compliance(self) -> WCAGResult
    async def test_keyboard_navigation(self) -> KeyboardResult
    async def test_screen_reader_support(self) -> ScreenReaderResult
    async def test_mobile_accessibility(self) -> MobileAccessibilityResult
```

## Critical Security Testing Areas

### Authentication Security
- **Password Policies**: Strength requirements, complexity validation
- **Session Management**: Token security, session timeout, refresh mechanisms
- **Brute Force Protection**: Rate limiting, account lockout policies
- **Multi-Factor Authentication**: If implemented, validate security measures

### Data Protection and Privacy
- **Encryption in Transit**: HTTPS/TLS configuration and certificate validation
- **Encryption at Rest**: Database and file storage encryption validation
- **User Data Isolation**: RLS policies and access control validation
- **Data Retention**: GDPR compliance and user data management

### Access Control and Authorization
- **Role-Based Access Control**: User permission and role validation
- **API Security**: Endpoint authentication and authorization
- **Database Security**: Connection security and query access controls
- **File Upload Security**: Upload validation and malware prevention

## WCAG 2.1 AA Compliance Testing

### Automated Accessibility Testing
- **Color Contrast**: Minimum 4.5:1 ratio for normal text, 3:1 for large text
- **Keyboard Navigation**: All interactive elements accessible via keyboard
- **ARIA Labels**: Proper semantic markup and accessibility labels
- **Alternative Text**: Images and non-text content properly labeled

### Focus Management and Navigation
- **Focus Indicators**: Visible focus indicators for all interactive elements
- **Tab Order**: Logical tab order throughout the application
- **Skip Links**: Proper skip navigation for screen reader users
- **Heading Structure**: Proper heading hierarchy and structure

### Form and Interactive Element Accessibility
- **Form Labels**: All form inputs properly labeled and associated
- **Error Handling**: Accessible error messages and validation feedback
- **Button and Link Accessibility**: Proper button and link labeling
- **Dynamic Content**: Accessible handling of dynamic content changes

## Working with the Developer

### Your Autonomous Responsibilities
- Implement automated security testing framework
- Execute WCAG 2.1 AA automated compliance testing
- Validate data protection and encryption measures
- Test input validation and sanitization
- Generate comprehensive security and accessibility reports
- Document specific issues requiring manual developer testing

### Developer Interactive Tasks (They Will Handle)
- **Manual Security Audit**: Penetration testing and vulnerability assessment
- **Assistive Technology Testing**: Screen readers (NVDA, JAWS, VoiceOver)
- **Accessibility Manual Testing**: Keyboard navigation and usability testing
- **Cross-Device UX Testing**: Mobile, tablet, desktop accessibility validation
- **User Journey Testing**: Complete workflows with assistive technology

## Files to Create/Update

### Security Testing Implementation
- `backend/testing/cloud_deployment/phase3_security_validator.py`
- `backend/testing/cloud_deployment/phase3_accessibility_validator.py`
- `backend/testing/security/authentication_security_tests.py`
- `backend/testing/security/data_protection_tests.py`

### Accessibility Testing Framework
- `frontend/testing/accessibility/wcag_compliance_tests.js`
- `frontend/testing/accessibility/keyboard_navigation_tests.js`
- `scripts/accessibility/automated_accessibility_scan.py`

### Documentation (Required Outputs)
- `TODO001_phase3_notes.md` - Security and accessibility implementation details
- `TODO001_phase3_decisions.md` - Security findings and compliance decisions
- `TODO001_phase3_handoff.md` - Production readiness security requirements
- `TODO001_phase3_testing_summary.md` - Security and accessibility validation results

## Security Testing Framework Implementation

### Authentication Security Tests
```python
async def test_authentication_security():
    # Test password strength requirements
    # Validate session token security
    # Test brute force protection
    # Validate secure session management
    # Test password reset security
```

### Data Protection Tests
```python
async def test_data_protection():
    # Validate HTTPS/TLS configuration
    # Test data encryption at rest
    # Validate user data isolation (RLS)
    # Test data backup security
    # Validate privacy compliance (GDPR)
```

### Access Control Tests
```python
async def test_access_controls():
    # Test role-based permissions
    # Validate API endpoint authorization
    # Test unauthorized access prevention
    # Validate database access controls
```

## Accessibility Testing Framework Implementation

### WCAG Compliance Automated Tests
```javascript
// Color contrast validation
async function testColorContrast() {
    // Test all text elements meet WCAG contrast requirements
    // Validate contrast ratios across different themes
    // Test color-only information indicators
}

// Keyboard navigation tests  
async function testKeyboardNavigation() {
    // Test tab order and focus management
    // Validate skip links functionality
    // Test keyboard shortcuts and accessibility
}

// ARIA and semantic markup tests
async function testARIACompliance() {
    // Validate ARIA labels and roles
    // Test heading structure and hierarchy
    // Validate form label associations
}
```

## Success Criteria Validation

### Security Requirements (100% Achievement Required)
- [ ] All authentication security measures validated and working
- [ ] Data encryption in transit and at rest confirmed
- [ ] User data isolation and privacy measures functional
- [ ] Access controls and authorization properly configured
- [ ] Input validation and sanitization preventing common attacks
- [ ] Security logging and monitoring operational

### Accessibility Requirements (100% WCAG 2.1 AA Compliance)
- [ ] Color contrast ratios meet WCAG requirements (4.5:1 normal, 3:1 large text)
- [ ] All interactive elements accessible via keyboard navigation
- [ ] Screen reader compatibility validated for all content
- [ ] Form accessibility and error handling compliant
- [ ] Mobile accessibility meeting touch and navigation requirements
- [ ] Dynamic content accessibility properly implemented

### Data Protection and Privacy (100% Compliance)
- [ ] User data isolation validated and functional
- [ ] Data encryption and protection measures working
- [ ] Privacy compliance (GDPR) validated
- [ ] Data retention and deletion policies implemented
- [ ] Backup security and access controls validated

## Common Security Issues to Test and Address

1. **SQL Injection**: Test all database queries and input handling
2. **Cross-Site Scripting (XSS)**: Validate input sanitization and output encoding
3. **Cross-Site Request Forgery (CSRF)**: Test CSRF protection measures
4. **Insecure Direct Object References**: Test user data access controls
5. **Security Misconfiguration**: Validate cloud platform security settings
6. **Sensitive Data Exposure**: Test for information disclosure vulnerabilities

## Accessibility Testing Priorities

1. **Keyboard Navigation**: Complete keyboard-only navigation testing
2. **Screen Reader Compatibility**: Test with multiple screen reading technologies
3. **Color and Contrast**: Validate color accessibility and high contrast support
4. **Mobile Accessibility**: Touch target sizes and mobile navigation
5. **Form Accessibility**: Form validation and error message accessibility
6. **Dynamic Content**: AJAX and real-time content accessibility

## Integration with Phase 4 Preparation

Document for Phase 4 production readiness:
- Security monitoring and alerting requirements
- Accessibility monitoring and compliance tracking
- Security incident response procedures
- Accessibility support and user guidance documentation
- Production security configuration requirements

## Developer Handoff Points

After autonomous implementation, prepare detailed documentation for developer testing:

### Manual Security Testing Requirements
- Specific penetration testing scenarios to execute
- Vulnerability assessment tools and procedures
- Security configuration validation checklists
- Security incident simulation procedures

### Manual Accessibility Testing Requirements
- Screen reader testing procedures (NVDA, JAWS, VoiceOver)
- Keyboard navigation testing scenarios
- Mobile accessibility testing procedures
- User journey accessibility validation

## Success Validation Checklist

Before proceeding to Phase 4:
- [ ] All autonomous security tests achieving 100% pass rate
- [ ] WCAG 2.1 AA compliance validated through automated testing
- [ ] Data protection and privacy measures confirmed functional
- [ ] Security vulnerabilities identified and addressed
- [ ] Accessibility issues documented with remediation plans
- [ ] Manual testing requirements clearly documented for developer
- [ ] All required documentation completed
- [ ] Production security configuration documented

## Next Steps After Phase 3

Upon successful completion with 100% security and accessibility compliance, proceed to Phase 4 (Production Readiness & Monitoring) using `PHASE4_PROMPT.md`.

---

**Remember**: Security and accessibility are non-negotiable requirements. Any issues identified must be addressed before proceeding to production deployment in Phase 4. Document all findings clearly for developer manual validation and remediation.