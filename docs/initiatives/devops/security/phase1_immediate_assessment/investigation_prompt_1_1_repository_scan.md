# Investigation Prompt 1.1: Repository-Wide Credential Scan

**Prompt ID**: SECURITY-P1.1  
**Area**: Current Repository Credential Scan  
**Priority**: 🚨 CRITICAL  
**Estimated Time**: 2 hours  

## Investigation Objective

Perform a comprehensive scan of the entire repository to identify all exposed credentials, API keys, passwords, tokens, and other sensitive information that should not be stored in plain text.

## Context and Background

**Known Exposure**: We have already identified multiple critical credentials in the file:
- `/docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md`

**Key exposed credentials include**:
- OpenAI API Key: `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`
- Anthropic API Key: `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`
- Database Password: `tukwof-pyVxo5-qejnoj`
- Document Encryption Key: `iSUAmk2NHMNW5bsn8F0UnPSCk9L+IxZhu/v/UyDwFcc=`

## Investigation Tasks

### Task 1.1.1: Search for Common Credential Patterns

Search the entire repository for common credential patterns:

**API Key Patterns to Search**:
```bash
# OpenAI API Keys
grep -r "sk-proj-" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Anthropic API Keys  
grep -r "sk-ant-api" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# LlamaCloud API Keys
grep -r "llx-" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Generic API Key patterns
grep -r -E "(api_key|apikey|api-key)" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Password patterns
grep -r -E "(password|passwd|pwd)" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Token patterns
grep -r -E "(token|secret|key)" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git
```

### Task 1.1.2: Search for Environment Variable Files

Find all environment variable and configuration files:

```bash
# Find .env files
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "*.env*" -type f

# Find config files
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "*config*" -type f | grep -v node_modules

# Find credential-related files
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "*credential*" -o -name "*secret*" -o -name "*key*" -type f | grep -v node_modules
```

### Task 1.1.3: Search for Database Connection Strings

Look for database connection strings and URLs:

```bash
# PostgreSQL connection strings
grep -r "postgresql://" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Supabase URLs
grep -r "supabase.co" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Database credential patterns
grep -r -E "(DATABASE_URL|DB_PASSWORD|DB_USER)" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git
```

### Task 1.1.4: Search for JWT Tokens and Base64 Keys

Look for JWT tokens and encoded keys:

```bash
# JWT token patterns (eyJ header)
grep -r "eyJ" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Base64 encoded keys (common patterns)
grep -r -E "[A-Za-z0-9+/]{32,}={0,2}" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git | grep -E "(key|secret|token)"
```

### Task 1.1.5: Search for Specific Exposed Values

Search for the specific credential values we know are exposed:

```bash
# Search for the specific exposed password
grep -r "tukwof-pyVxo5-qejnoj" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Search for the Supabase project ID
grep -r "dfgzeastcxnoqshgyotp" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git

# Search for encryption key
grep -r "iSUAmk2NHMNW5bsn8F0UnPSCk9L" /Users/aq_home/1Projects/accessa/insurance_navigator --exclude-dir=node_modules --exclude-dir=.git
```

### Task 1.1.6: Documentation and Configuration Analysis

Examine specific file types that commonly contain credentials:

```bash
# Markdown files that might contain credentials
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "*.md" -exec grep -l -E "(key|password|token|secret|credential)" {} \;

# YAML/JSON configuration files
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "*.yaml" -o -name "*.yml" -o -name "*.json" | grep -v node_modules | xargs grep -l -E "(key|password|token|secret)"

# Shell scripts and environment files
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "*.sh" -o -name "*.env*" | xargs grep -l -E "(key|password|token|secret)"
```

## Expected Findings

Document all findings in the following format:

```markdown
## Repository Credential Scan Results

### Critical Findings
- **File**: [absolute path]
- **Line**: [line number]
- **Credential Type**: [API key/password/token/etc.]
- **Service**: [OpenAI/Anthropic/Database/etc.]
- **Risk Level**: [CRITICAL/HIGH/MEDIUM/LOW]
- **Value**: [redacted or first/last 4 characters]

### Summary Statistics
- Total files scanned: [number]
- Files with credentials: [number]
- Critical credentials found: [number]
- Unique services affected: [number]
```

## Investigation Questions

1. **Scope**: How many files contain exposed credentials beyond the known RENDER_ENVIRONMENT_VARIABLES.md?
2. **Consistency**: Are the same credential values duplicated across multiple files?
3. **Types**: What types of credentials are exposed (API keys, passwords, tokens, certificates)?
4. **Services**: Which external services have exposed credentials?
5. **Patterns**: Are there common patterns in how credentials are stored?

## Deliverables

1. **Comprehensive Scan Report**: Complete list of all exposed credentials found
2. **File Inventory**: List of all files containing sensitive information
3. **Risk Classification**: Priority ranking of discovered credentials
4. **Immediate Actions**: List of credentials that need urgent rotation

## Success Criteria

- ✅ Complete repository scan performed using multiple search patterns
- ✅ All exposed credentials documented with file locations
- ✅ Risk levels assigned to each discovered credential
- ✅ No false positives (verified that findings are actual credentials)
- ✅ Scan results formatted for immediate action by security team

## Next Steps

Upon completion:
1. Compile findings into the credential inventory spreadsheet
2. Prioritize credentials for immediate rotation
3. Proceed to Investigation Prompt 1.2 (Git History Analysis)
4. Brief security team on urgent findings

---

**Time Allocation**: 2 hours maximum  
**Tools Required**: grep, find, text editor  
**Output**: Repository credential scan report