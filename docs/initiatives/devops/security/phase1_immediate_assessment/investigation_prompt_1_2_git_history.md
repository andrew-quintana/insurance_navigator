# Investigation Prompt 1.2: Git History Credential Analysis

**Prompt ID**: SECURITY-P1.2  
**Area**: Recent Git History Analysis  
**Priority**: 🔥 HIGH  
**Estimated Time**: 4 hours  

## Investigation Objective

Analyze git commit history to determine when credentials were first exposed, track their lifecycle in the repository, and identify any other sensitive information that may have been committed and later removed.

## Context and Background

**Known Exposure Source**: 
- Primary file: `/docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md`
- Current branch: `deployment/cloud-infrastructure`

**Key Investigation Areas**:
1. When were these credentials first committed?
2. Who committed them?
3. Are there other credentials in git history that have been removed?
4. Has this information been present in other branches?

## Investigation Tasks

### Task 1.2.1: Analyze Recent Commit History

Examine recent commits for credential-related changes:

```bash
# Current working directory
cd /Users/aq_home/1Projects/accessa/insurance_navigator

# Check recent commits in current branch
git log --oneline -n 20 deployment/cloud-infrastructure

# Look for commits related to environment variables or configuration
git log --grep="env" --grep="config" --grep="render" --grep="credential" --grep="key" --all --oneline

# Check recent commits that modified the known file
git log --follow --oneline -- "docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md"
```

### Task 1.2.2: Search Git History for Credential Patterns

Search the entire git history for credential patterns:

```bash
# Search for OpenAI API keys in git history
git log -S "sk-proj-" --all --oneline

# Search for Anthropic API keys in git history  
git log -S "sk-ant-api" --all --oneline

# Search for the specific exposed password
git log -S "tukwof-pyVxo5-qejnoj" --all --oneline

# Search for Supabase project ID
git log -S "dfgzeastcxnoqshgyotp" --all --oneline

# Search for encryption key
git log -S "iSUAmk2NHMNW5bsn8F0UnPSCk9L" --all --oneline
```

### Task 1.2.3: Examine Specific Commit Contents

For each commit found that contains credentials:

```bash
# Get detailed information about specific commits (replace COMMIT_HASH)
git show COMMIT_HASH

# Check what files were modified in credential-related commits
git diff-tree --no-commit-id --name-only -r COMMIT_HASH

# See the actual changes made
git show COMMIT_HASH --stat
git show COMMIT_HASH --name-only
```

### Task 1.2.4: Branch Analysis

Check if credentials exist in other branches:

```bash
# List all branches
git branch -a

# Check if the file exists in other branches
git ls-tree -r --name-only main | grep -i "render\|env\|config"
git ls-tree -r --name-only origin/main | grep -i "render\|env\|config"

# Search for credentials in specific branches
git log main -S "sk-proj-" --oneline
git log main -S "sk-ant-api" --oneline
```

### Task 1.2.5: Author and Timeline Analysis

Identify who committed credentials and when:

```bash
# Check commit authors for the specific file
git log --format="%h %an %ad %s" --date=short -- "docs/initiatives/devops/environment_management/infrastructure_setup/configuration_management/RENDER_ENVIRONMENT_VARIABLES.md"

# Check all authors who may have committed credentials
git log -S "sk-proj-" --format="%h %an %ad %s" --date=short --all
git log -S "sk-ant-api" --format="%h %an %ad %s" --date=short --all
```

### Task 1.2.6: Check for Removed Credentials

Look for credentials that may have been committed and later removed:

```bash
# Search for removed lines containing credentials
git log -p -S "api_key" --all | grep -C 5 -E "(\-.*api_key|\+.*api_key)"

# Look for environment variable removals
git log -p -S "OPENAI_API_KEY" --all
git log -p -S "ANTHROPIC_API_KEY" --all
git log -p -S "DATABASE_URL" --all

# Check for .env file history (if any)
git log --all --oneline -- "*.env*"
git log --all --oneline -- "**/.*env*"
```

### Task 1.2.7: Comprehensive Credential Archaeology

Perform deep analysis of git history for any credential patterns:

```bash
# Search for any JWT tokens in git history
git log -S "eyJ" --all --oneline | head -20

# Search for base64 encoded patterns that might be keys
git rev-list --all | xargs git grep -l -E "[A-Za-z0-9+/]{40,}={0,2}" | head -20

# Look for common credential variable names in history
git log -S "API_KEY" --all --oneline
git log -S "SECRET" --all --oneline
git log -S "PASSWORD" --all --oneline
git log -S "TOKEN" --all --oneline
```

## Investigation Questions

1. **First Appearance**: When were each of the exposed credentials first committed to the repository?
2. **Commit History**: How many commits have included these credentials?
3. **Author Identity**: Who committed the credentials originally and in subsequent commits?
4. **Branch Distribution**: In which branches do these credentials appear?
5. **Evolution**: Have any credentials been changed or rotated in git history?
6. **Removal Attempts**: Is there evidence of attempts to remove credentials?
7. **Other Exposure**: Are there other credentials in git history not currently visible?

## Expected Findings Format

Document findings in this structure:

```markdown
## Git History Credential Analysis Results

### Timeline of Exposure
- **First Commit**: [commit hash] by [author] on [date]
- **File Created**: [date] in commit [hash]
- **Total Commits with Credentials**: [number]
- **Branches Affected**: [list of branches]

### Credential Lifecycle Analysis
For each credential type:
- **OpenAI API Key**:
  - First appeared: [commit hash] on [date]
  - Last modified: [commit hash] on [date]
  - Total commits: [number]
  - Authors involved: [list]

### Historical Findings
- **Removed Credentials**: [any credentials found in history but not current]
- **Environmental Files**: [.env or config files found in history]
- **Other Sensitive Data**: [any other sensitive information discovered]

### Author Analysis
- [Author Name]: Committed credentials in [number] commits
- [Author Name]: Modified credential files on [dates]
```

## Risk Assessment Questions

1. **Repository Age**: How long have these credentials been exposed in the repository?
2. **Public Exposure**: If this is a public repository, how long have credentials been publicly visible?
3. **Access History**: How many people had access to the repository during the exposure period?
4. **Distribution**: Have these commits been pushed to any public repositories or forks?

## Deliverables

1. **Complete Timeline**: Chronological history of credential exposure
2. **Author Report**: Who committed credentials and when
3. **Branch Analysis**: Which branches contain exposed credentials
4. **Removed Credential Report**: Any credentials that were committed and later removed
5. **Risk Timeline**: Assessment of exposure duration and potential impact

## Success Criteria

- ✅ Complete git history analyzed for credential patterns
- ✅ Timeline of credential exposure documented
- ✅ All authors who committed credentials identified
- ✅ Branch analysis completed for credential distribution
- ✅ Evidence of any removed credentials documented
- ✅ Risk assessment of historical exposure completed

## Tools and Commands Reference

**Essential Git Commands**:
- `git log -S "pattern" --all --oneline` - Search for text in git history
- `git show COMMIT_HASH` - Show specific commit details
- `git log --follow -- filename` - Track file history including renames
- `git rev-list --all | xargs git grep pattern` - Search all commits for pattern

**Analysis Commands**:
- `git log --format="%h %an %ad %s" --date=short` - Formatted commit history
- `git diff-tree --no-commit-id --name-only -r COMMIT_HASH` - Files changed in commit
- `git log -p -S "pattern"` - Show actual changes for pattern

## Next Steps

Upon completion:
1. Update credential exposure timeline in main investigation report
2. Notify security team of historical exposure duration
3. Proceed to Investigation Prompt 1.3 (Active Service Assessment)
4. Prepare recommendations for git history cleanup if necessary

---

**Time Allocation**: 4 hours maximum  
**Tools Required**: git CLI, text processing tools  
**Output**: Git history credential analysis report