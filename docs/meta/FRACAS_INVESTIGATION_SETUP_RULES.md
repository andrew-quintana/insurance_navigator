# FRACAS Investigation Setup Rules

**Document**: FRACAS Investigation Setup Standardization  
**Version**: 1.0  
**Created**: 2025-09-30 15:16:33 PDT  
**Status**: Active  
**Purpose**: Standardize the creation and setup of FRACAS investigation packages

## Overview

This document establishes the mandatory rules and procedures for setting up FRACAS (Failure Reporting, Analysis, and Corrective Actions System) investigations. These rules ensure consistency, thoroughness, and effectiveness in failure analysis across all incidents.

## Mandatory Investigation Package Components

### Core Required Documents

Every FRACAS investigation must include exactly these three documents:

#### 1. `investigation_prompt.md` - Comprehensive Investigation Brief
**Purpose**: Provides complete investigation scope, requirements, and technical context

**Required Sections**:
- **Executive Summary**: Brief failure description and current status
- **Failure Description**: Primary symptoms, error context, user impact
- **Root Cause Analysis Required**: Systematic investigation categories
- **Corrective Action Requirements**: Immediate and long-term actions
- **Investigation Deliverables**: Specific outputs required
- **Technical Context**: Current constraints, suspected issues, error details
- **Success Criteria**: Clear investigation and resolution completion criteria
- **Related Incidents**: Historical context and connected issues
- **Investigation Notes**: Key questions, tools available, priority/time estimates

**Content Requirements**:
- Detailed failure description with specific error messages
- Systematic investigation steps with expected outputs
- Clear technical context including code locations and constraints
- Evidence-based investigation approach
- Measurable success criteria

#### 2. `investigation_checklist.md` - Step-by-Step Progress Tracker
**Purpose**: Ensures systematic and thorough investigation process

**Required Structure** (10 Phases):
1. **Pre-Investigation Setup**: Environment and tool preparation
2. **Phase 1: Database Schema Analysis**: Constraint and schema investigation
3. **Phase 2: Code Analysis**: Status value mapping and code review
4. **Phase 3: Root Cause Determination**: Timeline and impact assessment
5. **Phase 4: Solution Design**: Option analysis and recommendations
6. **Phase 5: Implementation Planning**: Detailed implementation steps
7. **Phase 6: Prevention Measures**: Process improvements and tooling
8. **Phase 7: Documentation**: Investigation reporting and process updates
9. **Phase 8: Implementation**: Code changes and testing
10. **Phase 9: Validation**: Functionality and performance testing
11. **Phase 10: Closure**: Final validation and knowledge transfer

**Checklist Requirements**:
- Checkbox format for progress tracking
- Specific tasks and deliverables per phase
- Key questions to answer during investigation
- Decision tracking and issues encountered sections

#### 3. `README.md` - Investigation Overview and Quick Start
**Purpose**: Provides context and entry point for investigators

**Required Sections**:
- **Overview**: FRACAS ID, date, environment, service, severity, status
- **Incident Summary**: Key details and problem statement
- **Files in This Directory**: Description of investigation materials
- **Quick Start for Investigators**: Step-by-step getting started guide
- **Investigation Status**: Phase tracking with checkboxes
- **Key Technical Details**: Critical technical information
- **Related Incidents**: Historical context
- **Investigation Requirements**: Immediate and long-term actions
- **Success Criteria**: Investigation and resolution completion criteria
- **Contact Information**: Key personnel assignments
- **Last Updated**: Timestamp of latest changes

## Incident Pattern Analysis Requirement

### Mandatory Historical Review

Before starting any investigation, investigators MUST:

1. **Scan All Incidents**: Review `/docs/incidents/` directory for similar failures
2. **Pattern Identification**: Document recurring failure patterns or root causes
3. **Historical Context**: Reference related incidents in investigation documents
4. **Learning Integration**: Apply lessons learned from previous incidents

### Pattern Analysis Process

```bash
# Required commands for incident analysis
find docs/incidents -name "README.md" -exec grep -l "similar_keywords" {} \;
grep -r "constraint violation" docs/incidents/
grep -r "database schema" docs/incidents/
grep -r "status mismatch" docs/incidents/
```

**Documentation Requirement**: 
- Include findings in investigation_prompt.md under "Related Incidents"
- Note patterns or recurring themes in README.md
- Reference similar resolution approaches in investigation_checklist.md

## Directory Structure Requirements

### Standard Investigation Directory Layout

```
docs/incidents/fm_XXX/
├── README.md                    # Investigation overview and quick start
├── investigation_prompt.md      # Comprehensive investigation brief  
├── investigation_checklist.md   # 10-phase progress tracker
├── prompts/                     # Optional: Additional investigation prompts
└── docs/                        # Optional: Supporting documentation
```

### File Naming Conventions

- **FRACAS ID Format**: `FM-XXX` where XXX is zero-padded sequential number
- **Directory Name**: `fm_xxx` (lowercase, underscore-separated)
- **Core Files**: Exact names as specified (investigation_prompt.md, investigation_checklist.md, README.md)
- **Date Format**: ISO 8601 format (YYYY-MM-DD) in all documents
- **Status Tracking**: Use checkboxes (- [ ]) for progress tracking

## Investigation Package Creation Process

### Step 1: Create Investigation Directory

```bash
# Create new FRACAS investigation directory
mkdir -p docs/incidents/fm_XXX
cd docs/incidents/fm_XXX
```

### Step 2: Generate Core Documents

Use the standardized templates from fm_023 as the reference implementation:

```bash
# Copy and customize templates
cp docs/incidents/fm_023/README.md ./README.md
cp docs/incidents/fm_023/investigation_prompt.md ./investigation_prompt.md  
cp docs/incidents/fm_023/investigation_checklist.md ./investigation_checklist.md
```

### Step 3: Customize for Specific Incident

**Required Customizations**:
- Update all FRACAS IDs (FM-XXX)
- Replace failure-specific details (error messages, locations, symptoms)
- Customize investigation categories based on failure type
- Update technical context with actual constraints and evidence
- Modify success criteria for specific incident

### Step 4: Conduct Historical Pattern Analysis

```bash
# Search for similar incidents
grep -r "keywords_from_current_incident" docs/incidents/
find docs/incidents -name "*.md" -exec grep -l "similar_error_patterns" {} \;
```

### Step 5: Document Pattern Findings

Add findings to:
- **README.md**: Related Incidents section
- **investigation_prompt.md**: Related Incidents section  
- **investigation_checklist.md**: Investigation Notes section

## Quality Assurance Requirements

### Document Completeness Checklist

Before starting investigation, verify:

- [ ] All three core documents created (README.md, investigation_prompt.md, investigation_checklist.md)
- [ ] FRACAS ID consistently used across all documents
- [ ] Current timestamp in all document headers
- [ ] Specific failure details (not template placeholders)
- [ ] Historical incident analysis completed
- [ ] Related incidents documented
- [ ] Success criteria clearly defined
- [ ] 10-phase checklist structure maintained
- [ ] Contact information assigned
- [ ] Technical context specific to incident

### Content Quality Standards

**Investigation Prompt Requirements**:
- Specific error messages and stack traces
- Exact file locations and line numbers
- Clear investigation categories with expected outputs
- Evidence-based approach with concrete steps
- Measurable success criteria

**Checklist Requirements**:
- Actionable tasks with clear deliverables
- Logical progression through investigation phases
- Specific testing and validation steps
- Documentation and knowledge transfer tasks

**README Requirements**:
- Clear incident summary with impact assessment
- Quick start guide for new investigators
- Technical details section with key information
- Progress tracking with phase checkboxes

## Automation and Tooling Integration

### Required CLI Commands

Investigators must use these commands for timestamps:

```bash
# For document headers
date +"%Y-%m-%d %H:%M:%S %Z"

# For simple dates
date +"%Y-%m-%d"

# For investigation logging
echo "Updated: $(date +"%Y-%m-%d %H:%M:%S")"
```

### Integration with Development Tools

**Git Branch Naming**:
```bash
git checkout -b investigation/fm-XXX-brief-description
```

**Commit Message Format**:
```bash
git commit -m "FRACAS FM-XXX: Investigation setup with comprehensive documentation package"
```

## Process Integration Requirements

### Phase 0: Investigation Setup (Mandatory)

Before any technical investigation:

1. **Create Investigation Package**: All three core documents
2. **Historical Analysis**: Review similar incidents
3. **Team Assignment**: Assign primary investigator and technical lead
4. **Tool Setup**: Environment access and investigation tools
5. **Timeline Planning**: Set investigation milestones

### During Investigation

- **Progress Tracking**: Update checklist regularly
- **Evidence Documentation**: Maintain investigation notes
- **Status Updates**: Update README.md status section
- **Decision Recording**: Document key decisions and rationale

### Investigation Completion

- **Documentation Updates**: Complete all investigation documents
- **Knowledge Transfer**: Share findings with team
- **Process Improvement**: Update rules based on lessons learned
- **Historical Record**: Archive investigation for future reference

## Compliance and Monitoring

### Mandatory Reviews

- **Setup Review**: Verify investigation package completeness before starting
- **Progress Reviews**: Weekly progress against checklist
- **Quality Review**: Ensure documentation meets standards
- **Completion Review**: Verify all success criteria met

### Process Improvement

- **Monthly Review**: Analyze investigation effectiveness
- **Template Updates**: Improve templates based on experience
- **Rule Refinement**: Update rules based on lessons learned
- **Training Updates**: Keep team training current

## Related Documents

- [FRACAS Implementation](./FRACAS_IMPLEMENTATION.md) - Overall FRACAS methodology
- [FRACAS Trigger Criteria](./fracas_trigger_criteria.md) - When to create FRACAS
- [FRACAS Template](./templates/fracas_template.md) - Initiative-level failure tracking
- [FM-023 Investigation Package](../incidents/fm_023/) - Reference implementation

---

**Last Updated**: 2025-09-30 15:16:33 PDT  
**Next Review**: 2025-10-30  
**Maintainer**: Development Team  
**Status**: Active - Mandatory for All Investigations

These rules ensure that every FRACAS investigation begins with a comprehensive, standardized foundation that enables systematic, thorough, and effective failure analysis and resolution.