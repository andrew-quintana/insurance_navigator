# Root Cause Analysis (RCA) Spec

## Summary
Brief description of the problem being investigated and the context that triggered the RCA.

## Problem Statement
- Observable symptoms and behavior
- Impact on users/system
- When the issue was first detected

## Initial Investigation
- Initial theories and observations
- Key log entries or error messages
- Frontend/backend behavior patterns

## Investigation Steps
Document each investigation phase with:

### Theory N: [Description]
- **Context**: Background information for this theory
- **Possible Issues**: 
  - Specific technical issues to investigate
  - System components that may be involved
- **Task**: Specific investigation actions to perform
- **Goal**: What the investigation should confirm or rule out

### Investigation Results N
- **Finding**: What was discovered
- **Evidence**: Specific data, logs, or test results
- **Impact**: How this affects the overall problem
- **Status**: ✅ COMPLETED / ❌ FAILED / ⚠️ PARTIAL

## Root Cause Identified
- **Primary Cause**: The main technical issue causing the problem
- **Contributing Factors**: Secondary issues that made the problem worse
- **Evidence Summary**: Key proof points that confirm the root cause

## Technical Details
- Architecture components involved
- Database schema issues (if applicable)
- Code/configuration problems
- Performance metrics or thresholds

## Solution Requirements
- **Immediate Fixes**: Critical changes needed right away
- **Configuration Changes**: Settings or parameters to adjust
- **Code Changes**: Development work required
- **Testing**: Validation steps to confirm fix

## Prevention
- **Monitoring**: What should be monitored to prevent recurrence
- **Alerts**: Warning systems to implement
- **Process Changes**: Development or operational improvements

## Follow-up Actions
- [ ] Immediate fix implementation
- [ ] Code review and testing
- [ ] Deployment verification
- [ ] Monitoring setup
- [ ] Documentation updates

## Priority and Impact
- **Priority**: 🚨 CRITICAL / ⚠️ HIGH / 📋 MEDIUM / 📝 LOW
- **Impact**: User-facing, system stability, performance, etc.
- **Timeline**: Expected resolution timeframe