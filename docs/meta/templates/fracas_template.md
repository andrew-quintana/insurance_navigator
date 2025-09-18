# FRACAS.md - Failure Reporting, Analysis, and Corrective Actions System

**Initiative:** [Initiative Name]  
**Status:** [Active | Complete | Archived]  
**Date Started:** [YYYY-MM-DD]  
**Last Updated:** [YYYY-MM-DD]  
**Maintainer:** [Team/Person]

## 📋 **How to Use This Document**

This document serves as a comprehensive failure tracking system for the [Initiative Name]. Use it to:

1. **Document new failures** as they occur during development/testing
2. **Track investigation progress** and findings
3. **Record root cause analysis** and solutions
4. **Maintain a knowledge base** of known issues and fixes

### **Documentation Guidelines:**
- **Be specific** about symptoms, timing, and context
- **Include evidence** (logs, error messages, screenshots)
- **Update status** as investigation progresses
- **Link related failures** when applicable
- **Record both successful and failed solutions**

---

## 🚨 **Active Failure Modes**

### **FM-XXX: [Failure Name]**
- **Severity**: [Low/Medium/High/Critical]
- **Frequency**: [Always/Often/Sometimes/Rarely/Once]
- **Status**: [🔍 Under Investigation | ⚠️ Known issue, workaround available | 🔧 Fix in progress]
- **First Observed**: [YYYY-MM-DD]
- **Last Updated**: [YYYY-MM-DD]

**Symptoms:**
- [Specific error messages or behaviors]
- [When the failure occurs]
- [What functionality is affected]

**Observations:**
- [What you noticed during testing]
- [Patterns or timing of the failure]
- [Any error messages or logs]

**Investigation Notes:**
- [Steps taken to investigate]
- [Hypotheses about the cause]
- [Tests performed or attempted]
- [Files or components involved]

**Root Cause:**
[The actual cause once identified, or \"Under investigation\" if unknown]

**Workaround:**
[Temporary solution if available, or \"None\" if no workaround exists]

**Permanent Fix:**
[How the issue will be fixed, or \"Pending\" if not yet determined]

**Related Issues:**
- [Links to related failures or dependencies]

---

## 🔧 **Resolved Failure Modes**

### **FM-XXX: [Failure Name] (RESOLVED)**
- **Severity**: [Low/Medium/High/Critical]
- **Status**: ✅ Fixed
- **First Observed**: [YYYY-MM-DD]
- **Resolution Date**: [YYYY-MM-DD]
- **Last Updated**: [YYYY-MM-DD]

**Symptoms:**
- [What the failure looked like]

**Observations:**
- [Key observations that led to understanding]

**Investigation Notes:**
- [What was investigated and how]

**Root Cause:**
[Confirmed root cause]

**Solution:**
[How the issue was actually fixed]

**Evidence:**
- [Code changes made]
- [Log entries or error messages]
- [Test results or screenshots]
- [Performance improvements]

**Related Issues:**
- [Links to related failures that this resolved or affected]

---

## 📝 **New Failure Documentation Template**

Use this template when documenting new failures:

```markdown
### **FM-XXX: [Failure Name]**
- **Severity**: [Low/Medium/High/Critical]
- **Status**: [🔍 Under Investigation | ⚠️ Known issue | 🔧 Fix in progress]
- **First Observed**: [YYYY-MM-DD]
- **Last Updated**: [YYYY-MM-DD]

**Symptoms:**
- [Specific error messages or behaviors]
- [When the failure occurs]
- [What functionality is affected]

**Observations:**
- [What you noticed during testing]
- [Patterns or timing of the failure]
- [Any error messages or logs]

**Investigation Notes:**
- [Steps taken to investigate]
- [Hypotheses about the cause]
- [Tests performed or attempted]
- [Files or components involved]

**Root Cause:**
[The actual cause once identified, or \"Under investigation\" if unknown]

**Solution:**
[How the issue was fixed, or \"Pending\" if not yet resolved]

**Evidence:**
- [Code changes made]
- [Log entries or error messages]
- [Test results or screenshots]

**Related Issues:**
- [Links to related failures or issues]
```

---

## 🧪 **Testing Scenarios**

### **Scenario 1: [Test Scenario Name]**
- **Steps**: [Step by step test procedure]
- **Expected**: [What should happen]
- **Current Status**: [✅ Working | ⚠️ Intermittent issues | ❌ Failing]
- **Last Tested**: [YYYY-MM-DD]
- **Known Issues**: [Reference to failure modes if any]

---

## 🔍 **Failure Tracking Guidelines**

### **When to Document a Failure:**
- Any unexpected behavior or error during development/testing
- Performance issues or slow responses
- Service unavailability or crashes
- Data inconsistencies or corruption
- Security concerns or vulnerabilities

### **What to Include:**
1. **Immediate Documentation**: Record symptoms and context as soon as possible
2. **Evidence Collection**: Screenshots, logs, error messages, stack traces
3. **Reproduction Steps**: Detailed steps to reproduce the issue
4. **Environment Details**: OS, browser, service versions, configuration
5. **Impact Assessment**: What functionality is affected and severity

### **Investigation Process:**
1. **Initial Assessment**: Determine severity and impact
2. **Data Gathering**: Collect logs, error messages, and context
3. **Hypothesis Formation**: Develop theories about the root cause
4. **Testing**: Attempt to reproduce and isolate the issue
5. **Root Cause Analysis**: Identify the actual cause
6. **Solution Development**: Implement and test fixes
7. **Documentation**: Update the failure record with findings

### **Status Updates:**
- **🔍 Under Investigation**: Issue is being analyzed and tested
- **⚠️ Known issue**: Issue understood, workaround available
- **🔧 Fix in progress**: Solution being implemented
- **✅ Fixed**: Issue has been resolved and verified
- **Won't Fix**: Issue is known but not planned to be addressed

## 📈 **System Health Metrics**

### **Current Performance:**
- [Key performance indicators]
- [Success rates]
- [Response times]
- [Error rates]

### **Known Limitations:**
- [Current system limitations]
- [Planned improvements]

## 🔍 **Investigation Areas**

### **High Priority:**
1. [High priority investigation areas]

### **Medium Priority:**
1. [Medium priority investigation areas]

### **Low Priority:**
1. [Low priority investigation areas]

## 📝 **Testing Notes**

### **Recent Tests ([Date]):**
- [Test results and observations]

### **Next Test Session:**
- [ ] [Planned tests]

---

**Last Updated**: [YYYY-MM-DD]  
**Next Review**: [When to review this document]  
**Maintainer**: [Team/Person responsible]