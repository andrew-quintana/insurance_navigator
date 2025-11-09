# Standard Operating Procedures (SOP)

**Document**: Insurance Navigator Development SOP  
**Version**: 2.0  
**Created**: 2025-09-30 15:16:33 PDT  
**Last Updated**: 2025-09-30 15:16:33 PDT  
**Status**: Active  
**Purpose**: Comprehensive operational procedures for development, deployment, and incident management

## Table of Contents

1. [FRACAS Investigation Setup](#fracas-investigation-setup)
2. [Incident Management](#incident-management)
3. [Development Workflow](#development-workflow)
4. [Documentation Standards](#documentation-standards)
5. [Quality Assurance](#quality-assurance)
6. [Emergency Procedures](#emergency-procedures)

---

## FRACAS Investigation Setup

### Overview

All incidents requiring investigation MUST follow the standardized FRACAS (Failure Reporting, Analysis, and Corrective Actions System) investigation setup process. This ensures systematic, thorough, and consistent failure analysis.

### Mandatory Investigation Package

When a FRACAS item is requested or an incident requires investigation, the following investigation package MUST be created:

#### Core Required Documents (All 3 Required)

1. **`investigation_prompt.md`** - Comprehensive investigation brief
2. **`investigation_checklist.md`** - 10-phase step-by-step progress tracker  
3. **`README.md`** - Investigation overview and quick start guide

#### Document Content Requirements

**investigation_prompt.md** must include:
- Executive Summary with failure description and current status
- Detailed failure description with symptoms, error context, user impact
- Systematic root cause analysis requirements with investigation categories
- Corrective action requirements (immediate and long-term)
- Specific investigation deliverables with expected outputs
- Technical context including constraints, suspected issues, error details
- Clear success criteria for investigation and resolution completion
- Related incidents section with historical context
- Investigation notes with key questions, tools, priority, and time estimates

**investigation_checklist.md** must include:
- 10 standardized investigation phases:
  1. Pre-Investigation Setup
  2. Database Schema Analysis
  3. Code Analysis  
  4. Root Cause Determination
  5. Solution Design
  6. Implementation Planning
  7. Prevention Measures
  8. Documentation
  9. Implementation
  10. Validation
  11. Closure
- Checkbox format for progress tracking
- Specific tasks and deliverables per phase
- Key questions to answer and decision tracking sections

**README.md** must include:
- Incident summary with FRACAS ID, date, environment, service, severity
- Problem statement and technical details
- Files in directory description
- Quick start guide for investigators
- Investigation status with phase checkboxes
- Related incidents and contact information
- Success criteria and last updated timestamp

### Historical Pattern Analysis (Mandatory)

Before starting any investigation, investigators MUST:

1. **Scan All Incidents**: Review `/docs/incidents/` directory for similar failures
2. **Search for Patterns**: Use these required commands:
   ```bash
   find docs/incidents -name "README.md" -exec grep -l "similar_keywords" {} \;
   grep -r "relevant_error_pattern" docs/incidents/
   grep -r "failure_type" docs/incidents/
   ```
3. **Document Findings**: Include pattern analysis in all three core documents
4. **Reference Solutions**: Apply lessons learned from previous incidents

### Investigation Setup Process

#### Step 1: Create Investigation Directory
```bash
mkdir -p docs/incidents/fm_XXX
cd docs/incidents/fm_XXX
```

#### Step 2: Use FM-023 as Reference Template
```bash
cp docs/incidents/fm_023/README.md ./README.md
cp docs/incidents/fm_023/investigation_prompt.md ./investigation_prompt.md  
cp docs/incidents/fm_023/investigation_checklist.md ./investigation_checklist.md
```

#### Step 3: Customize for Specific Incident
- Update all FRACAS IDs (FM-XXX)
- Replace template content with specific failure details
- Customize investigation categories for failure type
- Update technical context with actual constraints
- Modify success criteria for specific incident

#### Step 4: Historical Analysis and Documentation
- Search for similar incidents in `/docs/incidents/`
- Document patterns and related incidents
- Reference applicable solutions from previous investigations

#### Step 5: Quality Verification
Verify all quality requirements before starting investigation:
- [ ] All three core documents created
- [ ] FRACAS ID consistent across documents
- [ ] Current timestamps in headers
- [ ] Specific failure details (not template placeholders)
- [ ] Historical incident analysis completed
- [ ] 10-phase checklist structure maintained
- [ ] Contact information assigned

---

## Incident Management

### Incident Classification

#### Severity Levels
- **Critical**: Production system failure, data loss, security breach
- **High**: Major functionality impacted, significant performance degradation  
- **Medium**: Minor functionality impacted, workaround available
- **Low**: Cosmetic issues, documentation gaps

#### Automatic FRACAS Triggers
Refer to [FRACAS Trigger Criteria](./meta/fracas_trigger_criteria.md) for complete automation rules.

**Critical Triggers (Immediate FRACAS Required)**:
- Production downtime >5 minutes
- Data loss or corruption
- Security breach
- API failure rates >10% for >15 minutes
- Build failures >30 minutes

### Incident Response Process

1. **Detection**: Automated monitoring or manual reporting
2. **Assessment**: Classify severity and determine FRACAS requirement
3. **Investigation Setup**: Create standardized investigation package
4. **Investigation**: Follow 10-phase checklist methodology
5. **Resolution**: Implement solution and validate
6. **Documentation**: Complete investigation documentation
7. **Prevention**: Implement measures to prevent recurrence

---

## Development Workflow

### Local Development Startup (Validated)

#### Prerequisites
- Docker and Docker Compose installed
- Git
- Bash shell
- At least 4GB available RAM
- Ports 3000, 5432, 8000 available
- ngrok installed (for webhook testing)
- Supabase CLI installed (`npm install -g supabase`)
- Node.js and npm installed
- jq installed (`brew install jq`)

#### One-Command Startup (NEW - RECOMMENDED)
```bash
# Start all services with one command
./scripts/start-dev-complete.sh

# Stop all services
./scripts/stop-dev-complete.sh

# Check health of all services
./scripts/health-check.sh
```

#### Manual Startup Commands (Alternative)
```bash
# Set required environment variables
export ENVIRONMENT="development"
export SUPABASE_SERVICE_ROLE_KEY="test-key"
export OPENAI_API_KEY="test-key"
export LLAMAPARSE_API_KEY="test-key"
export NGROK_URL="https://your-ngrok-url.ngrok-free.app"
export WEBHOOK_BASE_URL="https://your-ngrok-url.ngrok-free.app"

# Start Supabase local instance
supabase start

# Start ngrok tunnel
ngrok http 8000 --log=stdout

# Start application services
docker-compose up -d

# Verify all services
curl http://localhost:8000/health
curl http://localhost:54321/health
open http://localhost:3000
```

#### Validated Service Configuration
| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| Supabase (Local) | 54321 | Database & Auth | ✅ Working |
| API Server | 8000 | FastAPI application | ✅ Working |
| Frontend | 3000 | Next.js UI | ✅ Working |
| ngrok | 4040 | Webhook tunneling | ✅ Working |

#### Troubleshooting Common Issues
1. **Database Connection Refused**: Ensure `.env.development` uses `host.docker.internal:54322`
2. **Webhook 503 Error**: Verify API server running and ngrok URL configured
3. **Environment File Not Found**: Set `ENVIRONMENT="development"`
4. **Missing Required Variables**: Set all required API keys

### Branch Management

#### Branch Naming Conventions
```bash
# Feature development
feature/short-description

# Bug fixes  
bugfix/issue-description

# FRACAS investigations
investigation/fm-XXX-brief-description

# Hotfixes
hotfix/critical-issue
```

#### Commit Message Standards
```bash
# Standard commits
"feat: add user authentication endpoint"
"fix: resolve database connection timeout"
"docs: update API documentation"

# FRACAS commits
"FRACAS FM-XXX: Investigation setup with comprehensive documentation package"
"FRACAS FM-XXX: Root cause analysis and solution implementation"
```

### Code Review Requirements

#### Mandatory Reviews
- All code changes require review before merge
- FRACAS investigation documents require technical lead review
- Security-related changes require security team review
- Database schema changes require DBA review

#### Review Checklist
- [ ] Code follows established patterns and conventions
- [ ] Tests included and passing
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] Performance impact assessed

### Testing Standards

#### Required Testing Levels
- **Unit Tests**: >80% code coverage for new code
- **Integration Tests**: Critical user flows tested
- **End-to-End Tests**: Complete workflows validated
- **Performance Tests**: Response time and load testing

#### Testing Commands
```bash
# Run full test suite
npm run test

# Run specific test categories
npm run test:unit
npm run test:integration
npm run test:e2e

# Check code coverage
npm run test:coverage
```

---

## Documentation Standards

### Timestamp Requirements

All documentation MUST use CLI commands for timestamps to ensure accuracy:

```bash
# For document headers
date +"%Y-%m-%d %H:%M:%S %Z"

# For simple dates  
date +"%Y-%m-%d"

# For investigation logging
echo "Updated: $(date +"%Y-%m-%d %H:%M:%S")"
```

### Documentation Categories

#### Technical Documentation
- **API Documentation**: OpenAPI/Swagger specifications
- **Architecture Documents**: System design and component interactions
- **Database Schema**: Complete schema documentation with relationships
- **Deployment Guides**: Step-by-step deployment procedures

#### Process Documentation  
- **Investigation Procedures**: FRACAS investigation methodology
- **Incident Response**: Emergency response procedures
- **Development Workflow**: Git workflow and code review process
- **Testing Procedures**: Testing strategies and requirements

#### User Documentation
- **User Guides**: End-user functionality documentation
- **API Guides**: Developer integration documentation  
- **Troubleshooting**: Common issues and solutions
- **FAQ**: Frequently asked questions

### Document Review Process

#### Review Requirements
- Technical accuracy verified by subject matter expert
- Completeness checked against template requirements
- Cross-references validated
- Timestamps current and accurate

#### Review Schedule
- **Monthly**: Process documentation review
- **Quarterly**: Technical documentation audit
- **Annually**: Complete SOP review and update

---

## Quality Assurance

### Code Quality Standards

#### Static Analysis
- ESLint for JavaScript/TypeScript
- Black/Flake8 for Python
- Security scanning with appropriate tools
- Dependency vulnerability scanning

#### Performance Standards
- API response times <200ms for 95th percentile
- Frontend load times <3 seconds
- Database query optimization for >100ms queries
- Memory usage monitoring and optimization

### Documentation Quality

#### FRACAS Documentation Standards
- All three core documents required for investigations
- Evidence-based analysis with concrete examples
- Clear success criteria and progress tracking
- Historical context and pattern analysis

#### Technical Documentation Standards
- Code examples tested and verified
- Architecture diagrams current and accurate
- API documentation synchronized with implementation
- User guides validated through user testing

---

## Emergency Procedures

### Production Incidents

#### Immediate Response (0-15 minutes)
1. **Assess Impact**: Determine severity and user impact
2. **Stabilize System**: Implement immediate fixes or rollbacks
3. **Communicate**: Notify stakeholders and users
4. **Document**: Begin incident documentation

#### Investigation Phase (15 minutes - 4 hours)
1. **Create FRACAS Package**: Follow standardized setup process
2. **Investigate**: Use 10-phase methodology
3. **Coordinate**: Involve appropriate team members
4. **Update**: Regular stakeholder communication

#### Resolution Phase (4+ hours)
1. **Implement Solution**: Deploy validated fix
2. **Verify Resolution**: Confirm system stability
3. **Complete Documentation**: Finalize FRACAS documentation
4. **Conduct Review**: Post-incident review meeting

### Security Incidents

#### Immediate Actions
1. **Contain**: Isolate affected systems
2. **Assess**: Determine scope and impact
3. **Notify**: Security team and management
4. **Preserve**: Evidence for investigation

#### Investigation
1. **Create FRACAS**: Security-focused investigation package
2. **Analyze**: Forensic analysis of incident
3. **Remediate**: Fix vulnerabilities
4. **Report**: Complete security incident report

### Data Loss Incidents

#### Immediate Response
1. **Stop Operations**: Prevent further data loss
2. **Assess Scope**: Determine extent of data loss
3. **Initiate Recovery**: Begin backup restoration
4. **Notify Stakeholders**: Immediate communication

#### Recovery Process
1. **Validate Backups**: Confirm backup integrity
2. **Restore Data**: Systematic data restoration
3. **Verify Integrity**: Validate restored data
4. **Resume Operations**: Careful service restoration

---

## Process Improvement

### Continuous Improvement

#### Regular Reviews
- **Weekly**: Active incident review
- **Monthly**: Process effectiveness assessment
- **Quarterly**: SOP update review
- **Annually**: Complete methodology evaluation

#### Metrics Tracking
- Investigation completion time
- Resolution accuracy
- Prevention effectiveness
- Documentation quality

#### Training Requirements
- New team member SOP training
- Regular refresher training
- Tool-specific training
- Emergency response drills

### SOP Maintenance

#### Update Process
1. **Identify Need**: Process gaps or improvements
2. **Document Change**: Proposed modifications
3. **Review**: Team and stakeholder review
4. **Approve**: Management approval for changes
5. **Implement**: Update procedures and training
6. **Communicate**: Notify all team members

#### Version Control
- SOP versions tracked in git
- Change log maintained
- Previous versions archived
- Rollback procedures defined

---

## Related Documents

### FRACAS Documentation
- [FRACAS Investigation Setup Rules](./meta/FRACAS_INVESTIGATION_SETUP_RULES.md)
- [FRACAS Implementation](./meta/FRACAS_IMPLEMENTATION.md)
- [FRACAS Trigger Criteria](./meta/fracas_trigger_criteria.md)
- [FRACAS Templates](./meta/templates/)

### Technical Documentation
- [Architecture Overview](./architecture/README.md)
- [Deployment Guide](./deployment/)
- [Security Guidelines](./security/)
- [Development Setup](./development/)

### Reference Examples
- [FM-023 Investigation Package](./incidents/fm_023/) - Reference implementation
- [Incident Directory](./incidents/README.md) - Historical incidents

---

**Document Control**:
- **Version**: 2.0
- **Last Updated**: 2025-09-30 15:16:33 PDT
- **Next Review**: 2025-11-30
- **Approved By**: [Technical Lead]
- **Effective Date**: 2025-09-30

This SOP establishes comprehensive operational procedures with a focus on systematic FRACAS investigation methodology, ensuring consistent, thorough, and effective incident management and resolution across all team activities.