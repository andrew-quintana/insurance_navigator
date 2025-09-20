# Security Investigation Tools and Commands Reference

**Purpose**: Comprehensive reference for security investigation tools, commands, and procedures  
**Target Audience**: Security investigators, DevOps team, incident response personnel  
**Scope**: Tools for credential exposure investigation and security analysis  

## Tool Categories

### Git History Analysis Tools
- **Git Log Analysis**: Commands for analyzing commit history
- **Git Grep**: Repository-wide content searching
- **Git Blame**: File modification tracking
- **Git Show**: Detailed commit examination

### Credential Detection Tools
- **TruffleHog**: Git repository credential scanning
- **GitLeaks**: Git leak detection and prevention
- **Detect-Secrets**: Pre-commit credential detection
- **Git-Secrets**: AWS credential protection

### Repository Analysis Tools
- **Repo-Security-Scanner**: Repository security assessment
- **GitHub Security Advisories**: Vulnerability scanning
- **Dependabot**: Dependency security analysis
- **CodeQL**: Code security analysis

### Cloud Platform Investigation Tools
- **Render CLI**: Render platform investigation
- **Vercel CLI**: Vercel deployment analysis
- **Cloud Platform APIs**: Programmatic investigation
- **Infrastructure as Code Scanners**: Configuration analysis

### Network and API Analysis Tools
- **cURL/HTTPie**: API endpoint testing
- **Wireshark/tcpdump**: Network traffic analysis
- **Postman/Insomnia**: API security testing
- **Burp Suite**: Web application security testing

## Tool Inventory and Usage

### Git History Analysis Commands

#### 1. Git Log Analysis
```bash
# Search for credential-related commits
git log --grep="password\|key\|secret\|token\|credential" --oneline --all

# Search commits by author during exposure period
git log --author="username" --since="2024-01-01" --until="2025-01-21" --oneline

# Search for file modification history
git log --follow --patch -- "docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md"

# Find commits that added or removed specific content
git log -S "sk-proj-qpjdY0" --source --all --oneline

# Search for commits modifying sensitive file patterns
git log --name-only --grep="env\|config\|secret" --oneline
```

#### 2. Git Grep for Content Search
```bash
# Search for API key patterns across all history
git grep "sk-proj\|sk-ant\|llx-\|lsv2_pt" $(git rev-list --all)

# Search for credential keywords in all files
git grep -i "password\|secret\|token\|key\|credential" HEAD

# Search for specific exposed credentials
git grep "tukwof-pyVxo5-qejnoj\|iSUAmk2NHMNW5bsn8F0UnPSCk9L" $(git rev-list --all)

# Search in specific file types
git grep "api.*key" -- "*.md" "*.json" "*.yaml" "*.env*"
```

#### 3. Git Blame for Change Tracking
```bash
# Track line-by-line changes in sensitive files
git blame docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md

# Show blame with email addresses
git blame -e docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md

# Show blame for specific line ranges
git blame -L 64,82 docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md
```

#### 4. Git Show for Detailed Examination
```bash
# Show full commit details including diff
git show <commit-hash>

# Show only the files changed in a commit
git show --name-only <commit-hash>

# Show commit with word-level diff highlighting
git show --word-diff <commit-hash>
```

### Credential Detection Tools

#### 1. TruffleHog Installation and Usage
```bash
# Install TruffleHog
pip install truffleHog

# Scan entire repository history
trufflehog --regex --entropy=False https://github.com/yourusername/insurance_navigator.git

# Scan specific branch
trufflehog --branch=main --regex --entropy=False file://path/to/repo

# Scan with custom rules
trufflehog --rules=custom_rules.json file://path/to/repo
```

#### 2. GitLeaks Installation and Usage
```bash
# Install GitLeaks
brew install gitleaks  # macOS
# or download from https://github.com/zricethezav/gitleaks/releases

# Scan entire repository
gitleaks detect --source . --verbose

# Scan specific commits
gitleaks detect --source . --log-opts="--since=2024-01-01"

# Generate report
gitleaks detect --source . --report-path=gitleaks-report.json
```

#### 3. Detect-Secrets Setup
```bash
# Install detect-secrets
pip install detect-secrets

# Initialize baseline
detect-secrets scan --all-files > .secrets.baseline

# Scan for new secrets
detect-secrets scan --baseline .secrets.baseline

# Audit detected secrets
detect-secrets audit .secrets.baseline
```

### Repository Analysis Commands

#### 1. File Permission and Access Analysis
```bash
# Find files with sensitive content patterns
find . -type f \( -name "*.env*" -o -name "*.key" -o -name "*.pem" -o -name "*secret*" \) -exec ls -la {} \;

# Search for configuration files
find . -type f \( -name "*.conf" -o -name "*.config" -o -name "*.ini" -o -name "*.yaml" -o -name "*.json" \) | grep -E "(env|config|secret|key)"

# Check file modification times
find . -name "*environment*" -o -name "*config*" -exec stat {} \;
```

#### 2. Repository Statistics and Analysis
```bash
# Repository contributor analysis
git shortlog -sn --all

# File change frequency analysis
git log --name-only --pretty=format: | sort | uniq -c | sort -rg

# Large file identification
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | sed -n 's/^blob //p' | sort --numeric-sort --key=2 | tail -20
```

### Cloud Platform Investigation

#### 1. Render Platform Analysis
```bash
# Install Render CLI
npm install -g @render/cli

# Login to Render
render auth login

# List services
render services list

# Get service details
render services get <service-id>

# List environment variables (if accessible)
render services env list <service-id>

# Get deployment logs
render services logs <service-id>
```

#### 2. Vercel Platform Analysis
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# List projects
vercel ls

# Get project information
vercel inspect <project-name>

# List environment variables
vercel env ls

# Get deployment logs
vercel logs <deployment-url>
```

### API and Service Investigation

#### 1. API Key Validation and Testing
```bash
# Test OpenAI API key
curl -H "Authorization: Bearer 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" https://api.openai.com/v1/models

# Test Anthropic API key
curl -H "Authorization: Bearer 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" -H "Content-Type: application/json" https://api.anthropic.com/v1/messages

# Test Supabase connection
curl -H "apikey: ***REMOVED***.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM" ***REMOVED***/rest/v1/

# Test LlamaCloud API
curl -H "Authorization: Bearer llx-CRtlURo7FT74ZMydik58KjPHC5aTpOSuGjWqOkTXjrPQucUS" https://api.cloud.llamaindex.ai/api/v1/parsing/upload
```

#### 2. Database Connection Testing
```bash
# Test Supabase database connection
psql "postgresql://postgres.dfgzeastcxnoqshgyotp:tukwof-pyVxo5-qejnoj@aws-0-us-west-1.pooler.supabase.com:6543/postgres" -c "\l"

# Test connection with timeout
timeout 10s psql "postgresql://postgres.dfgzeastcxnoqshgyotp:tukwof-pyVxo5-qejnoj@aws-0-us-west-1.pooler.supabase.com:6543/postgres" -c "SELECT version();"
```

## Investigation Procedures

### Phase 1: Immediate Assessment Procedures

#### Current Credential Exposure Analysis
```bash
# Step 1: Repository credential scan
cd /path/to/repository
gitleaks detect --source . --verbose --report-path=phase1-current-scan.json

# Step 2: Search for hardcoded credentials
grep -r "sk-proj\|sk-ant\|llx-\|lsv2_pt" . --exclude-dir=.git
grep -r "tukwof-pyVxo5-qejnoj\|iSUAmk2NHMNW5bsn8F0UnPSCk9L" . --exclude-dir=.git

# Step 3: Find configuration and environment files
find . -name "*.env*" -o -name "*config*" -o -name "*secret*" | grep -v .git
```

#### Git History Credential Scan
```bash
# Step 1: Comprehensive history scan
trufflehog --regex --entropy=False file://$(pwd)

# Step 2: Targeted credential search in history
git grep "sk-proj\|sk-ant\|llx-\|lsv2_pt" $(git rev-list --all) > phase1-git-grep-results.txt

# Step 3: Commit-by-commit analysis for sensitive files
git log --follow --patch -- "**/RENDER_ENVIRONMENT_VARIABLES.md" > phase1-sensitive-file-history.log
```

### Phase 2: Historical Analysis Procedures

#### Complete Repository Archaeology
```bash
# Step 1: Full repository timeline analysis
git log --all --full-history --oneline --decorate --graph > repository-timeline.log

# Step 2: All contributor analysis
git log --format='%H %an %ae %ad %s' --date=iso > contributor-analysis.log

# Step 3: File creation and modification tracking
git log --name-status --pretty=format:'%H %ad %an %ae' --date=iso > file-modification-history.log
```

### Phase 3: Cloud Deployment Security Procedures

#### Render Environment Audit
```bash
# Step 1: Service inventory
render services list --format=json > render-services-inventory.json

# Step 2: Environment variable audit (per service)
for service in $(render services list --format=json | jq -r '.[].id'); do
  echo "Service: $service"
  render services env list $service 2>/dev/null || echo "Access denied for $service"
done
```

## Security Tools Installation Guide

### macOS Installation
```bash
# Install package managers
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install security tools
brew install gitleaks git-secrets truffleHog
npm install -g @render/cli vercel
pip install detect-secrets truffleHog
```

### Linux Installation  
```bash
# Install security tools
curl -sSfL https://raw.githubusercontent.com/zricethezav/gitleaks/master/scripts/install.sh | sh -s -- -b /usr/local/bin
pip install truffleHog detect-secrets
npm install -g @render/cli vercel
```

## Investigation Checklists

### Pre-Investigation Setup
- [ ] Install required security tools
- [ ] Configure tool access and permissions
- [ ] Set up secure working directory
- [ ] Prepare investigation documentation templates
- [ ] Verify repository access and permissions

### Evidence Collection
- [ ] Create investigation baseline scan
- [ ] Document current repository state
- [ ] Capture screenshots of critical findings
- [ ] Export logs and scan results
- [ ] Create evidence chain of custody documentation

### Investigation Verification
- [ ] Cross-verify findings with multiple tools
- [ ] Validate credential exposure timelines
- [ ] Confirm access patterns and permissions
- [ ] Document investigation methodology
- [ ] Prepare findings for review and validation

## Emergency Response Commands

### Immediate Credential Deactivation
```bash
# Emergency: Revoke GitHub tokens (if applicable)
curl -X DELETE -H "Authorization: token <github-token>" https://api.github.com/authorizations/<token-id>

# Emergency: Test credential validity before rotation
curl -f -H "Authorization: Bearer <api-key>" <api-endpoint> && echo "Key still active" || echo "Key deactivated"
```

### Emergency Repository Cleanup
```bash
# Emergency: Remove sensitive files from git history (USE WITH EXTREME CAUTION)
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md' --prune-empty --tag-name-filter cat -- --all

# Emergency: Add sensitive files to .gitignore
echo "docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md" >> .gitignore
```

---

**⚠️ SECURITY WARNING**: These tools and commands are provided for legitimate security investigation purposes. Ensure proper authorization before running any commands against production systems or third-party services.