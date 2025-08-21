# Task: Implement Lightweight Documentation Contract System

You are implementing a documentation contract system that enforces "adjacent-first" investigation and dated citations for engineering initiatives. This system helps teams investigate adjacent components before building, without prescribing canonical toolchains.

## Input
You have the complete System Setup specification in markdown format, in @docs/initiatives/coding_agent/CONTEXT.md. Use it as your authoritative source for all file contents and structure.

## Objectives
1. Create a complete, working documentation contract system
2. Enforce adjacent-first scoping with freshness checks
3. Provide tooling for Cursor and Claude Code integration
4. Set up validation and CI guardrails
5. Make the system immediately usable for new initiatives

## Pre-Implementation Checklist
Before writing any files:
1. Run `date +%Y-%m-%d` to get the current date for any date placeholders
2. Check if this is a git repository (`ls -la .git/` or equivalent)
3. Identify existing conflicting files and plan merge strategy
4. Verify you have write permissions to create directories and files

## Implementation Plan

### Phase 1: Core Documentation Structure
Create the base documentation contract:

**Required Actions:**
- Create `/docs/` hierarchy: `initiatives/`, `knowledge/`, `summaries/rollups/`, `meta/`
- Write `/docs/README.md` with exact content from spec
- Write `/docs/DOCS_POLICY.md` with exact content from spec  
- Write `/docs/DOCS_READINESS_CHECKLIST.md` with exact content from spec
- Create `/docs/knowledge/ADJACENT_INDEX.md` with header row only

### Phase 2: Tool Integration
Set up Cursor and Claude Code configurations:

**Required Actions:**
- Create `/.cursor/rules.mdc` with exact content from spec
  - **CRITICAL:** Include the "Use-System-Date" guardrail and "today" command
- Write `/docs/meta/CLAUDE_CODE_SYSTEM_PROMPT.md` with exact content from spec
  - **CRITICAL:** Include the date handling warning about using `date +%Y-%m-%d`

### Phase 3: Templates and Meta Files
Create all templates and configuration:

**Required Actions:**
- Create `/docs/meta/templates/` directory
- Write all template files: `CONTEXT.md`, `PRD.md`, `RFC.md`, `TODO.md`, `ROLLUP.md`, `ADJACENT_INDEX.md`
- Create `/docs/meta/adjacency.json` with seed content (update date to current)
- Create `/docs/meta/search_config.json` with exact content from spec

### Phase 4: Automation and Validation
Set up scripts and tooling:

**Required Actions:**
- Create `/scripts/` directory
- Write `/scripts/scaffold_initiative.sh` with exact content from spec
- Make executable: `chmod +x scripts/scaffold_initiative.sh`
- Create `/tools/` directory  
- Write `/tools/validate_docs.py` with exact content from spec
- Make executable: `chmod +x tools/validate_docs.py`

### Phase 5: Git Integration and CI
Set up hooks and workflows:

**Required Actions:**
- Create `.git/hooks/pre-commit` with exact content from spec
- Make executable: `chmod +x .git/hooks/pre-commit`
- Create `.github/workflows/` directory
- Write `.github/workflows/docs-guard.yml` with exact content from spec

## Implementation Requirements

### File Handling Strategy
- **If file exists and is empty:** Overwrite with spec content
- **If file exists with content:** Preserve existing, append spec content with clear delimiters
- **If directory exists:** Continue, create missing subdirectories
- **Always:** Create parent directories as needed

### Content Accuracy
- Use EXACT content from the System Setup specification
- Replace any date placeholders (YYYY-MM-DD) with current system date from `date +%Y-%m-%d`
- Replace any {InitiativeName} or XXX placeholders appropriately in templates
- Preserve all formatting, including indentation and code block markers

### Executable Permissions
Must set executable permissions on:
- `scripts/scaffold_initiative.sh`
- `tools/validate_docs.py`  
- `.git/hooks/pre-commit`

### Validation Steps
After implementation:
1. Run `tools/validate_docs.py` to ensure the system works
2. Test scaffold script: `scripts/scaffold_initiative.sh test "Test Initiative"`
3. Verify Cursor can find `.cursor/rules.mdc`
4. Check that all template files are present and properly formatted

## Error Handling
- If git repository doesn't exist, skip git-specific files and warn user
- If directories can't be created, report specific permission issues
- If files can't be written, identify the blocking files and suggest solutions
- Continue with partial implementation if some steps fail, but report what's missing

## Output Requirements
Provide:
1. Summary of all files created/modified
2. List of any files that couldn't be created and why
3. Next steps for the user (how to use the system)
4. Any warnings about existing files that were preserved
5. Validation results from running the validator

## Success Criteria
- All required directories and files are created with correct content
- Scripts have proper executable permissions
- System passes its own validation (`tools/validate_docs.py`)
- Templates can generate initiative documents via scaffold script
- CI workflow is properly configured

Execute this implementation systematically, creating each file with exact content from the specification. Report progress and any issues encountered.