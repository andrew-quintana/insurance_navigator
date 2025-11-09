# FM-024 Investigation Package Index

## 📋 Investigation Package Overview

This directory contains a complete investigation package for **FM-024: Supabase Storage Authentication Failure**. The package includes documentation, test scripts, and requirements to support another agent in resolving the issue.

## 📁 File Structure

### 📖 Documentation
- **[README.md](README.md)** - Main investigation prompt and detailed analysis
- **[INVESTIGATION_SUMMARY.md](INVESTIGATION_SUMMARY.md)** - High-level summary and context
- **[quick_reference.md](quick_reference.md)** - Quick commands and key information

### 🔧 Technical Documentation
- **[environment_configuration.md](environment_configuration.md)** - Environment analysis and comparison
- **[test_scripts.md](test_scripts.md)** - Test script documentation and usage
- **[development_testing_requirements.md](development_testing_requirements.md)** - Local testing requirements

### 🧪 Test Scripts
- **[test_staging_storage_error.py](test_staging_storage_error.py)** - Replicates staging error ✅
- **[test_storage_auth_error.py](test_storage_auth_error.py)** - Tests local storage (working)
- **[test_upload_with_auth.py](test_upload_with_auth.py)** - Full upload flow test
- **[test_upload_failure.py](test_upload_failure.py)** - Basic upload test
- **[test_upload_bypass_auth.py](test_upload_bypass_auth.py)** - Direct function test

## 🚀 Quick Start

### 1. Read the Investigation Prompt
Start with **[README.md](README.md)** for the complete investigation requirements.

### 2. Set Up Local Environment
Follow **[development_testing_requirements.md](development_testing_requirements.md)** for setup instructions.

### 3. Run Baseline Tests
```bash
cd /Users/aq_home/1Projects/accessa/insurance_navigator
source .venv/bin/activate
python docs/incidents/fm_024/test_staging_storage_error.py
```

### 4. Investigate Root Cause
Use **[environment_configuration.md](environment_configuration.md)** for investigation commands.

## 🎯 Issue Summary

**Problem**: Supabase storage authentication failing with "signature verification failed"  
**Impact**: File uploads cannot complete  
**Status**: Investigation required  
**Priority**: HIGH  

## ✅ What's Working
- User authentication
- Database operations
- Local development environment
- Local Supabase storage

## ❌ What's Broken
- Staging Supabase storage authentication
- Signed URL generation in staging
- File upload completion

## 🔍 Investigation Areas

1. **Service Role Key Permissions** - Does key have storage access?
2. **Storage Service Status** - Is storage enabled for project?
3. **Bucket Configuration** - Does "raw" bucket exist and have proper policies?
4. **Environment Differences** - Staging vs Development config differences

## 📋 Success Criteria

### Investigation Complete When:
- [ ] Root cause identified and documented
- [ ] Storage configuration status understood
- [ ] Service role key permissions verified
- [ ] Environment differences identified
- [ ] Recommended solution identified

### Resolution Complete When:
- [ ] Storage authentication works end-to-end
- [ ] File uploads complete successfully
- [ ] All tests pass locally
- [ ] Staging deployment successful
- [ ] No storage-related errors occur

## 🚨 Critical Requirements

### MANDATORY Local Testing
- All fixes must be tested locally before staging deployment
- Use provided test scripts for validation
- Ensure no regression in working functionality

### Deployment Process
1. Implement fix locally
2. Test with all provided scripts
3. Commit to feature branch
4. Create PR to staging branch
5. Deploy and validate in staging

## 📞 Support Information

**Original Investigator**: Claude (Anthropic)  
**Investigation Date**: September 30, 2025  
**Related Incidents**: FM-023 (RESOLVED)  
**Project**: Insurance Navigator  

---

## 🔗 Related Files

- **FM-023 Resolution**: Database constraint violation (RESOLVED)
- **Test Scripts Location**: `/Users/aq_home/1Projects/accessa/insurance_navigator/test_*.py`
- **Environment Files**: `.env.staging`, `.env.development`
- **Main Code**: `api/upload_pipeline/endpoints/upload.py`

---

**Ready to investigate? Start with [README.md](README.md) for the complete investigation prompt.**
