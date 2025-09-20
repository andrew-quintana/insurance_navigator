# Exposed Credentials Catalog

**Document**: Credential Exposure Inventory  
**Version**: 1.0  
**Date**: September 20, 2025  
**Classification**: CONFIDENTIAL - RESTRICTED ACCESS  

## Overview

This document catalogs all credentials found exposed in the repository. This is a working document that will be updated as the investigation progresses.

**⚠️ SECURITY WARNING**: This document contains sensitive information. Access is restricted to authorized security personnel only.

## Source File Analysis

**Primary Source**: `/docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md`  
**Discovery Date**: September 20, 2025  
**File Last Modified**: [TO BE DETERMINED IN INVESTIGATION]  
**Lines**: 142 total lines  

## Credential Inventory

### 🔴 CRITICAL - API Keys

| Service | Type | Key Prefix | Risk Level | Status |
|---------|------|------------|------------|---------|
| OpenAI | API Key | sk-proj-* | CRITICAL | 🔄 ACTIVE |
| Anthropic | API Key | sk-ant-api03-* | CRITICAL | 🔄 ACTIVE |
| LlamaCloud | API Key | llx-* | HIGH | 🔄 ACTIVE |
| LangChain | API Key | lsv2_pt_* | MEDIUM | 🔄 ACTIVE |

### 🔴 CRITICAL - Database Credentials

| Component | Type | Value Pattern | Risk Level | Status |
|-----------|------|---------------|------------|---------|
| Supabase URL | Connection String | https://dfgzeastcxnoqshgyotp.supabase.co | HIGH | 🔄 ACTIVE |
| Database Password | Plaintext | tukwof-pyVxo5-qejnoj | CRITICAL | 🔄 ACTIVE |
| Connection String | Full URL | postgresql://postgres.dfgzeastcxnoqshgyotp:* | CRITICAL | 🔄 ACTIVE |
| Anonymous Key | JWT Token | eyJhbGciOiJIUzI1NiIs* | HIGH | 🔄 ACTIVE |
| Service Role Key | JWT Token | eyJhbGciOiJIUzI1NiIs* | CRITICAL | 🔄 ACTIVE |

### 🟠 HIGH - Encryption Keys

| Component | Type | Key Format | Risk Level | Status |
|-----------|------|------------|------------|---------|
| Document Encryption | Base64 Key | iSUAmk2NHMNW5bsn8F0UnPSCk9L+IxZhu/v/UyDwFcc= | CRITICAL | 🔄 ACTIVE |

### 🟡 MEDIUM - Configuration Data

| Component | Type | Information | Risk Level | Status |
|-----------|------|-------------|------------|---------|
| Supabase Project ID | Identifier | dfgzeastcxnoqshgyotp | MEDIUM | 🔄 ACTIVE |
| Database Host | Hostname | aws-0-us-west-1.pooler.supabase.com | MEDIUM | 🔄 ACTIVE |
| Render Service URLs | Service Endpoints | insurance-navigator-staging-api.onrender.com | LOW | 🔄 ACTIVE |

## Detailed Credential Analysis

### OpenAI API Key
```
Key: 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
Location: Line 65 in RENDER_ENVIRONMENT_VARIABLES.md
Risk: CRITICAL - Allows API access, potential billing impact, model usage
```

### Anthropic API Key
```
Key: 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
Location: Line 68 in RENDER_ENVIRONMENT_VARIABLES.md
Risk: CRITICAL - Allows API access, potential billing impact, model usage
```

### Database Credentials
```
Password: tukwof-pyVxo5-qejnoj
Full URL: postgresql://postgres.dfgzeastcxnoqshgyotp:tukwof-pyVxo5-qejnoj@aws-0-us-west-1.pooler.supabase.com:6543/postgres
Location: Lines 33-41 in RENDER_ENVIRONMENT_VARIABLES.md
Risk: CRITICAL - Direct database access, data breach potential
```

### Document Encryption Key
```
Key: iSUAmk2NHMNW5bsn8F0UnPSCk9L+IxZhu/v/UyDwFcc=
Location: Line 81 in RENDER_ENVIRONMENT_VARIABLES.md
Risk: CRITICAL - Can decrypt sensitive documents
```

## Immediate Risk Assessment

### Critical Risks
1. **Database Compromise**: Full database access with read/write permissions
2. **API Abuse**: Unauthorized usage of AI services leading to billing and quota issues
3. **Document Decryption**: Ability to decrypt sensitive user documents
4. **Service Impersonation**: Ability to make API calls as the application

### Potential Impact
- **Data Breach**: Complete access to user data in Supabase database
- **Financial Loss**: Unauthorized API usage charges
- **Service Disruption**: Potential API key revocation or rate limiting
- **Compliance Violation**: Data protection regulation breaches
- **Reputation Damage**: Public exposure of security practices

## Immediate Actions Required

### 🚨 URGENT (Next 1 Hour)
1. Rotate OpenAI API key
2. Rotate Anthropic API key
3. Change Supabase database password
4. Generate new document encryption key

### 🔥 HIGH PRIORITY (Next 4 Hours)
1. Rotate LlamaCloud API key
2. Rotate LangChain API key
3. Review recent API usage logs for anomalies
4. Update all deployment configurations

### 📋 FOLLOW-UP (Next 24 Hours)
1. Audit git history for credential exposure timeline
2. Review access logs for unauthorized usage
3. Implement secrets management solution
4. Update security policies and procedures

## Investigation Status

- [x] Initial credential discovery and cataloging
- [ ] Git history analysis for exposure timeline
- [ ] Access log review for unauthorized usage
- [ ] Cloud deployment security audit
- [ ] Repository access control review

---

**Document Status**: ACTIVE INVESTIGATION  
**Next Update**: Upon completion of Phase 1 findings  
**Responsible**: DevOps Security Team