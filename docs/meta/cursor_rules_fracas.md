# Cursor Rules for FRACAS Methodology

## Overview
These rules define how to use Cursor AI assistant with the FRACAS (Failure Reporting, Analysis, and Corrective Actions System) methodology for systematic failure tracking and resolution.

## Core Principles

### 1. Single FRACAS Document Per Initiative
- Each initiative must maintain exactly one `fracas.md` document
- All failure modes for that initiative are tracked in this single document
- Do not create separate RCA documents unless specifically requested
- The FRACAS document serves as the definitive failure knowledge base

### 2. Systematic Failure Documentation
When encountering any failure, bug, or unexpected behavior:
- Immediately assign a unique FM-XXX identifier (incremental numbering)
- Document using the standard FRACAS template
- Include all required sections: Symptoms, Observations, Investigation Notes, Root Cause, Solution, Evidence
- Update status as investigation progresses

### 3. Evidence-Based Analysis
- All conclusions must be supported by concrete evidence
- Include logs, error messages, screenshots, code references
- Document both successful and failed solution attempts
- Maintain chronological investigation timeline

## Cursor Usage Rules

### When to Create/Update FRACAS Documents

#### Create New FRACAS Document:
```
Initiative starts → Create docs/initiatives/[initiative_name]/fracas.md
```

#### Update Existing FRACAS Document:
- When any error, bug, or unexpected behavior occurs
- When investigating issues during development or testing
- When implementing fixes or workarounds
- When system behavior doesn't match expectations
- When performance issues are detected

### FRACAS Document Structure

#### Required Location:
```
docs/initiatives/[initiative_name]/fracas.md
```

#### Required Sections:
1. **How to Use This Document** - Instructions and guidelines
2. **Active Failure Modes** - Currently unresolved issues
3. **Resolved Failure Modes** - Historical knowledge base
4. **New Failure Documentation Template** - Template for consistency
5. **Testing Scenarios** - Current test status
6. **Failure Tracking Guidelines** - Process documentation
7. **System Health Metrics** - Current performance indicators

### Failure Mode Documentation Rules

#### Naming Convention:
- **Format**: `FM-XXX: [Descriptive Name]`
- **Numbering**: Sequential (FM-001, FM-002, FM-003...)
- **Scope**: Unique within each initiative
- **Descriptive Name**: Clear, specific description of the failure

#### Required Information:
```markdown
### **FM-XXX: [Failure Name]**
- **Severity**: [Critical/High/Medium/Low]
- **Status**: [🔍 Under Investigation | ⚠️ Known issue | 🔧 Fix in progress | ✅ Fixed]
- **First Observed**: [YYYY-MM-DD]
- **Last Updated**: [YYYY-MM-DD]

**Symptoms:**
- [Specific observable behaviors]
- [Error messages or codes]
- [Affected functionality]

**Observations:**
- [Key findings during investigation]
- [Patterns or timing]
- [Environmental factors]

**Investigation Notes:**
- [Steps taken to investigate]
- [Hypotheses explored]
- [Tests performed]
- [Files or components involved]

**Root Cause:**
[Confirmed cause or "Under investigation"]

**Solution:**
[How fixed or "Pending"]

**Evidence:**
- [Code changes made]
- [Log entries]
- [Test results]

**Related Issues:**
- [Links to related failures]
```

### Status Management Rules

#### Status Progression:
```
🔍 Under Investigation → ⚠️ Known issue (if workaround found)
                      → 🔧 Fix in progress (when implementing solution)
                      → ✅ Fixed (when resolved and verified)
```

#### Status Updates:
- Update status immediately when investigation state changes
- Update "Last Updated" field with each modification
- Move resolved issues from "Active" to "Resolved" section
- Maintain historical record of resolution process

### Investigation Process Rules

#### 1. Initial Documentation (Within 1 hour of detection):
- Assign FM-XXX identifier
- Document symptoms and immediate observations
- Assess severity and impact
- Set status to "🔍 Under Investigation"

#### 2. Evidence Collection:
- Collect all relevant logs, error messages, screenshots
- Document reproduction steps
- Record environmental context
- Include code references with file:line format

#### 3. Hypothesis Development:
- Document multiple theories about potential causes
- Prioritize theories based on evidence and likelihood
- Plan systematic testing approach
- Document all theories explored, even those ruled out

#### 4. Solution Implementation:
- Document both workarounds and permanent fixes
- Include code changes with file references
- Verify solution resolves the issue
- Update status to "✅ Fixed" only after verification

### Code Reference Standards

#### File References:
```
file_path:line_number
Example: src/services/api.py:245
```

#### Log References:
```
Include timestamps and relevant context
Example: 
2025-09-18 10:30:15 - ERROR - Database connection failed: timeout after 30s
```

#### Error Message Format:
```
Include full error text with context
Example:
Error: 500 Internal Server Error
Details: {"error": "Database connection timeout", "timestamp": "2025-09-18T10:30:15Z"}
```

### Prevention and Learning Rules

#### Pattern Recognition:
- Regularly review failure modes for patterns
- Identify common root causes across failures
- Document systemic issues vs isolated incidents
- Update development processes based on learnings

#### Knowledge Transfer:
- Maintain detailed resolution procedures
- Document lessons learned for each failure mode
- Update team procedures based on failure analysis
- Create preventive measures for recurring patterns

## Cursor Interaction Guidelines

### When Asking for Help:
1. **Reference the FRACAS document**: "Check the fracas.md for initiative X"
2. **Specify failure mode**: "Looking at FM-025 in the fracas document"
3. **Request specific actions**: "Update FM-025 status to fixed and document the solution"

### When Reporting Issues:
1. **Immediate documentation**: "Document this error as a new failure mode in fracas.md"
2. **Evidence collection**: "Include these logs and error messages in the failure documentation"
3. **Investigation requests**: "Help investigate this failure mode using systematic approach"

### When Implementing Fixes:
1. **Solution documentation**: "Update the fracas document with the implemented solution"
2. **Evidence recording**: "Record the code changes and test results in the failure mode"
3. **Status updates**: "Move this failure mode to resolved section"

## Quality Assurance Rules

### Documentation Quality:
- All failure modes must have complete documentation
- Evidence must support all claims and conclusions
- Investigation steps must be reproducible
- Solutions must be verified and tested

### Process Compliance:
- Follow systematic investigation process
- Maintain chronological timeline of investigation
- Document both successful and failed approaches
- Update status promptly as situation changes

### Knowledge Management:
- Build comprehensive organizational memory
- Enable learning from failures
- Prevent recurrence through systematic analysis
- Share knowledge across team members

## Examples of Proper Usage

### Example 1: New Failure Detection
```
User: "The upload endpoint is returning 500 errors"
Cursor: "I'll document this as a new failure mode in the fracas.md. Let me add FM-XXX with the symptoms and begin investigation."
```

### Example 2: Investigation Update
```
User: "Found that the database connection is timing out"
Cursor: "I'll update FM-XXX in fracas.md with this finding in the Investigation Notes section and continue systematic analysis."
```

### Example 3: Solution Implementation
```
User: "Fixed the timeout by increasing connection pool size"
Cursor: "I'll update FM-XXX status to fixed, document the solution with code changes, and move it to the resolved section."
```

## Integration with Development Workflow

### Pre-Development:
- Review fracas.md for known issues in area of work
- Consider failure patterns when designing solutions
- Plan development to avoid known failure modes

### During Development:
- Document any unexpected behavior immediately
- Update investigation notes as understanding develops
- Implement solutions systematically with proper testing

### Post-Development:
- Verify all failure modes are resolved
- Update documentation with lessons learned
- Share knowledge with team members

## Testing and Technical Debt Requirements

### Phase Handoff Testing Summaries
Each phase completion must include:
- **Testing Summary Document**: Comprehensive validation results for handoff to next phase
- **Coverage Documentation**: What was tested and any limitations or gaps
- **Validation Results**: Both automated and manual testing outcomes
- **Next Phase Prerequisites**: Testing requirements that must be met before next phase can proceed

### Initiative Completion Requirements
At initiative completion, must provide:
- **Final Testing Summary**: Comprehensive testing report across all phases
- **Technical Debt Documentation**: Complete catalog of technical debt with:
  - Impact assessment for each debt item
  - Prioritization based on business impact
  - Remediation roadmap with timelines
  - Cost/benefit analysis for addressing debt

### Quality Standards for Testing Documentation
- Testing summaries must be actionable for next phase teams
- Technical debt must be catalogued with sufficient detail for future remediation
- All testing gaps must be explicitly documented
- Performance baselines and regression risks must be documented

---

These rules ensure consistent, systematic failure tracking and resolution using the FRACAS methodology. Following these guidelines builds organizational knowledge and prevents future issues through comprehensive failure analysis.