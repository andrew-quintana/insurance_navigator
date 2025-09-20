# Investigation Prompt 2.1: Complete Git History Archaeology

**Prompt ID**: SECURITY-P2.1  
**Area**: Deep Git History Analysis  
**Priority**: 📚 HIGH  
**Estimated Time**: 16 hours  

## Investigation Objective

Perform comprehensive archaeological analysis of the entire git repository history to identify every instance of credential exposure, track credential lifecycle, and build a complete forensic timeline of security-relevant events.

## Context and Background

**Building on Phase 1**: This investigation expands beyond the immediate analysis from Phase 1 to examine the complete repository history across all branches, commits, and time periods.

**Known Starting Points**:
- Primary exposure file: `RENDER_ENVIRONMENT_VARIABLES.md` 
- Current branch: `deployment/cloud-infrastructure`
- Immediate findings from Phase 1 investigation

**Scope Expansion**: This analysis will examine every commit ever made to understand the full scope of credential exposure.

## Investigation Tasks

### Task 2.1.1: Complete Repository History Mapping

Create comprehensive map of repository structure and history:

```bash
# Get complete repository statistics
cd /Users/aq_home/1Projects/accessa/insurance_navigator

# Repository overview
git log --oneline --all | wc -l  # Total commits
git branch -a | wc -l  # Total branches
git tag | wc -l  # Total tags
git log --format="%an" | sort -u | wc -l  # Total unique authors

# Get complete commit history
git log --all --oneline --graph --decorate > git_history_complete.txt

# Get all branches and their commit counts
git for-each-ref --format='%(refname:short) %(committerdate) %(authorname)' refs/heads/ > branches_analysis.txt
git for-each-ref --format='%(refname:short) %(committerdate) %(authorname)' refs/remotes/ >> branches_analysis.txt
```

### Task 2.1.2: Comprehensive Credential Pattern Search

Search entire git history for all possible credential patterns:

```bash
# Search for every possible API key pattern across all history
git rev-list --all | while read commit; do
  echo "Checking commit: $commit"
  git show "$commit" | grep -E "(sk-[a-zA-Z0-9_-]{40,}|sk-proj-[a-zA-Z0-9_-]{50,}|sk-ant-api[a-zA-Z0-9_-]{40,})" && echo "Found in commit: $commit"
done > api_keys_history.txt

# Search for database credentials across all history
git rev-list --all | while read commit; do
  git show "$commit" | grep -E "(postgresql://|mysql://|mongodb://)" && echo "Found in commit: $commit"
done > database_urls_history.txt

# Search for password patterns across all history
git rev-list --all | while read commit; do
  git show "$commit" | grep -iE "(password|passwd|pwd).*=.*['\"][^'\"]{8,}['\"]" && echo "Found in commit: $commit"
done > passwords_history.txt

# Search for common environment variable patterns
git rev-list --all | while read commit; do
  git show "$commit" | grep -E "(API_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL).*=.*['\"][^'\"]{10,}['\"]" && echo "Found in commit: $commit"
done > env_vars_history.txt
```

### Task 2.1.3: Service-Specific Credential Archaeology

Look for credentials from all major services across complete history:

```bash
# OpenAI credential history
git log -S "OPENAI" --all --oneline > openai_history.txt
git log -S "sk-proj" --all --oneline >> openai_history.txt
git log -S "gpt" --all --oneline >> openai_history.txt

# Anthropic credential history  
git log -S "ANTHROPIC" --all --oneline > anthropic_history.txt
git log -S "sk-ant" --all --oneline >> anthropic_history.txt
git log -S "claude" --all --oneline >> anthropic_history.txt

# Database credential history
git log -S "supabase" --all --oneline > database_history.txt
git log -S "postgres" --all --oneline >> database_history.txt
git log -S "DATABASE_URL" --all --oneline >> database_history.txt

# Cloud service credential history
git log -S "render" --all --oneline > cloud_history.txt
git log -S "vercel" --all --oneline >> cloud_history.txt
git log -S "aws" --all --oneline >> cloud_history.txt

# Other service histories
git log -S "llama" --all --oneline > other_services_history.txt
git log -S "langchain" --all --oneline >> other_services_history.txt
git log -S "openapi" --all --oneline >> other_services_history.txt
```

### Task 2.1.4: File-Level Credential Tracking

Track credential-containing files throughout their history:

```bash
# Find all files that have ever contained credentials
git log --all --name-only | grep -E "\.(env|config|yaml|yml|json|md)$" | sort -u > potential_credential_files.txt

# For each potential file, check its complete history
while read file; do
  echo "=== Analyzing file: $file ===" >> file_credential_history.txt
  git log --follow --oneline -- "$file" >> file_credential_history.txt
  echo "--- Credential patterns in $file ---" >> file_credential_history.txt
  git log --follow -p -- "$file" | grep -E "(api.*key|password|token|secret|credential)" >> file_credential_history.txt
  echo "" >> file_credential_history.txt
done < potential_credential_files.txt

# Check for deleted files that may have contained credentials
git log --all --name-status | grep "^D" | awk '{print $2}' | grep -E "\.(env|config|secret)" > deleted_credential_files.txt
```

### Task 2.1.5: Commit Message Analysis

Analyze commit messages for security-relevant information:

```bash
# Find commits with security-related messages
git log --all --grep="password" --oneline > security_commit_messages.txt
git log --all --grep="key" --oneline >> security_commit_messages.txt
git log --all --grep="secret" --oneline >> security_commit_messages.txt
git log --all --grep="credential" --oneline >> security_commit_messages.txt
git log --all --grep="api" --oneline >> security_commit_messages.txt
git log --all --grep="config" --oneline >> security_commit_messages.txt
git log --all --grep="env" --oneline >> security_commit_messages.txt

# Find commits that mention removal or rotation
git log --all --grep="remove" --oneline > removal_commit_messages.txt
git log --all --grep="delete" --oneline >> removal_commit_messages.txt
git log --all --grep="rotate" --oneline >> removal_commit_messages.txt
git log --all --grep="update" --oneline >> removal_commit_messages.txt

# Find commits that mention security
git log --all --grep="security" --oneline > security_related_commits.txt
git log --all --grep="fix" --oneline >> security_related_commits.txt
git log --all --grep="vulnerability" --oneline >> security_related_commits.txt
```

### Task 2.1.6: Author and Timeline Analysis

Comprehensive analysis of who committed what and when:

```bash
# Get complete author history with credential-related commits
git log --all --format="%h %an %ae %ad %s" --date=iso | grep -iE "(key|password|secret|credential|api|config|env)" > author_credential_commits.txt

# Timeline analysis of credential commits
git log --all --format="%ad %h %an %s" --date=short | grep -iE "(key|password|secret|credential|api)" | sort > credential_timeline.txt

# Find first and last commit for each author
git log --all --format="%an %ad" --date=short | sort | uniq > author_activity_timeline.txt

# Analyze commit frequency over time
git log --all --format="%ad" --date=short | sort | uniq -c > commit_frequency.txt
```

### Task 2.1.7: Binary and Archive Analysis

Check for credentials in binary files or archives:

```bash
# Find binary files that might contain credentials
git log --all --name-only | grep -E "\.(zip|tar|gz|bz2|env\.enc|key|pem|p12|pfx)$" | sort -u > binary_files.txt

# Check for base64 encoded data that might be credentials
git rev-list --all | while read commit; do
  git show "$commit" | grep -E "[A-Za-z0-9+/]{40,}={0,2}" | grep -v "^---" | grep -v "^+++" > base64_patterns_$commit.txt 2>/dev/null
done

# Look for encrypted files that might contain credentials
find /Users/aq_home/1Projects/accessa/insurance_navigator -name "*.enc" -o -name "*.gpg" -o -name "*.asc" 2>/dev/null > encrypted_files.txt
```

## Investigation Questions

1. **Complete Exposure Timeline**: What is the earliest credential exposure in repository history?
2. **Credential Evolution**: How have credentials changed, been rotated, or evolved over time?
3. **Author Patterns**: Which authors have historically committed credentials?
4. **File Evolution**: How have credential-containing files evolved over time?
5. **Removal Attempts**: Is there evidence of attempted credential removal or rotation?
6. **External References**: Are there references to external credential storage systems?
7. **Branch Patterns**: How are credentials distributed across different branches?

## Expected Findings Format

```markdown
## Complete Git History Credential Analysis

### Repository Statistics
- **Total Commits Analyzed**: [number]
- **Total Branches Analyzed**: [number]  
- **Total Authors**: [number]
- **Analysis Period**: [earliest date] to [latest date]
- **Repository Age**: [duration]

### Credential Discovery Summary
- **Total Credential Instances Found**: [number]
- **Unique Credential Types**: [number]
- **Files Ever Containing Credentials**: [number]
- **Commits with Credential Changes**: [number]

### Historical Timeline
#### Earliest Credential Exposure
- **Date**: [date]
- **Commit**: [hash]
- **Author**: [name]
- **File**: [path]
- **Credential Type**: [type]

#### Major Credential Events
- [Date]: [Event description - commit hash - author]
- [Date]: [Event description - commit hash - author]

### Credential Lifecycle Analysis
For each credential type found:
#### OpenAI API Keys
- **First Appearance**: [date/commit]
- **Total Commits**: [number]
- **Authors Involved**: [list]
- **Branches Present**: [list]
- **Current Status**: [active/removed/rotated]

### Author Analysis
- **[Author Name]**: [number] credential-related commits
- **[Author Name]**: [number] credential-related commits

### File Analysis
- **[File Path]**: Contains credentials in [number] commits across [timespan]
- **[File Path]**: Contains credentials in [number] commits across [timespan]

### Removal and Rotation Evidence
- [Evidence of credential removal attempts]
- [Evidence of credential rotation]
- [Evidence of security improvements]
```

## Advanced Analysis Techniques

### Differential Analysis
```bash
# Compare credential patterns between branches
git diff main..deployment/cloud-infrastructure | grep -E "(key|password|secret|token)"

# Find commits where credentials were added vs removed
git log --all -p | grep -A5 -B5 "^\+.*\(key\|password\|secret\)" > credential_additions.txt
git log --all -p | grep -A5 -B5 "^\-.*\(key\|password\|secret\)" > credential_removals.txt
```

### Statistical Analysis
```bash
# Credential density by time period
git log --all --format="%ad" --date=format:"%Y-%m" | sort | uniq -c > monthly_activity.txt

# Author contribution to credential exposure
git log --all --format="%an" | grep -f <(git log --all -S "key" --format="%h" | xargs -I {} git show --format="%an" {} | head -1) | sort | uniq -c > author_credential_contributions.txt
```

## Tools and Automation

### Automated Scripts
Create analysis scripts for:
- Batch credential pattern searching
- Timeline visualization
- Statistical reporting
- Export for compliance documentation

### External Tools Integration
- git-secrets for additional pattern detection
- truffleHog for entropy analysis
- Custom regex patterns for organization-specific credentials

## Deliverables

1. **Complete Historical Credential Inventory**: Every credential instance ever in repository
2. **Forensic Timeline**: Chronological record of all credential-related events
3. **Author Accountability Report**: Who committed credentials and when
4. **File Evolution Report**: How credential-containing files have changed
5. **Statistical Analysis**: Patterns and trends in credential exposure
6. **Remediation History**: Evidence of past security improvement efforts

## Success Criteria

- ✅ Complete git history analyzed (every commit, every branch)
- ✅ All historical credential instances documented
- ✅ Timeline of credential exposure events established
- ✅ Author accountability for credential commits documented
- ✅ File evolution patterns analyzed
- ✅ Statistical analysis of credential exposure trends completed

## Next Steps

Upon completion:
1. Compile comprehensive historical credential database
2. Update overall security timeline with historical findings
3. Proceed to Investigation Prompt 2.2 (Credential Evolution Tracking)
4. Brief security team on historical exposure scope

---

**Time Allocation**: 16 hours (can be parallelized)  
**Tools Required**: Advanced git commands, analysis scripts, statistical tools  
**Output**: Complete git history credential archaeology report