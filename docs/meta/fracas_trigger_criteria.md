# FRACAS Automatic Trigger Criteria

**Document**: FRACAS Automatic Trigger Criteria  
**Version**: 1.0  
**Last Updated**: 2025-09-18  
**Status**: Active

## Overview

This document defines automatic criteria for when FRACAS (Failure Reporting, Analysis, and Corrective Actions System) documents must be created or updated. These criteria help ensure consistent failure tracking across all initiatives and development workflows.

## Automatic FRACAS Creation Triggers

### Critical Triggers (Immediate FRACAS Required)

#### Production Issues
- **Production system downtime** >5 minutes
- **Data loss or corruption** of any amount
- **Security breach or vulnerability** exploitation
- **User-reported critical bugs** affecting core functionality
- **API failure rates** >10% for >15 minutes
- **Database connection failures** >50% for >5 minutes

#### Development Issues
- **Build failures** taking >30 minutes to resolve
- **Test suite failures** with >10% failure rate
- **Integration test failures** affecting multiple components
- **Deployment failures** requiring rollback
- **Performance regression** >25% from baseline

#### Security Issues
- **Authentication bypass** or unauthorized access
- **Data exposure** outside intended scope
- **Privilege escalation** vulnerabilities
- **External security alerts** affecting dependencies
- **Failed security scans** with high/critical findings

### High Priority Triggers (FRACAS Required Within 4 Hours)

#### System Performance
- **Response time degradation** >50% from baseline
- **Memory usage alerts** above 90% for >30 minutes
- **Disk space alerts** above 85% on any system
- **Network connectivity issues** affecting service operation
- **Cache hit ratio** dropping below 70%

#### Development Workflow
- **Test failures** requiring >2 hours investigation
- **Code review failures** identifying architectural issues
- **Dependency conflicts** preventing builds
- **Environment configuration issues** affecting multiple developers
- **Git workflow problems** blocking team progress

#### External Dependencies
- **Third-party service outages** affecting functionality
- **API rate limiting** blocking operations
- **DNS resolution failures** for external services
- **SSL certificate issues** affecting secure connections
- **CDN or static asset delivery failures**

### Medium Priority Triggers (FRACAS Required Within 24 Hours)

#### Code Quality Issues
- **Static analysis failures** with >5 critical findings
- **Code coverage drops** below established thresholds
- **Technical debt accumulation** beyond defined limits
- **Refactoring needs** identified through code analysis
- **Documentation gaps** preventing team understanding

#### User Experience Issues
- **User interface bugs** affecting usability
- **Mobile responsiveness** issues on supported devices
- **Accessibility compliance** failures
- **Internationalization** problems in supported locales
- **Browser compatibility** issues on supported browsers

#### Operational Issues
- **Log aggregation failures** preventing monitoring
- **Monitoring alert noise** requiring tuning
- **Backup verification failures** for any system
- **Scheduled job failures** affecting automation
- **Resource allocation issues** in cloud environments

## FRACAS Creation Workflow

### Automatic Detection Methods

#### CI/CD Pipeline Integration
```bash
# Example GitHub Actions integration
if [[ $TEST_FAILURE_RATE -gt 10 ]]; then
  create_fracas_entry "FM-AUTO-$(date +%Y%m%d%H%M)" "Test failure rate exceeded threshold"
fi

if [[ $BUILD_TIME -gt 1800 ]]; then
  create_fracas_entry "FM-AUTO-$(date +%Y%m%d%H%M)" "Build time exceeded 30 minutes"
fi
```

#### Monitoring System Integration
```python
# Example monitoring alert handler
def handle_alert(alert):
    if alert.severity in ['critical', 'high']:
        fracas_manager.create_failure_mode(
            severity=alert.severity,
            trigger=alert.name,
            evidence=alert.details,
            auto_created=True
        )
```

#### Development Tool Integration
```python
# Example test runner integration
def on_test_failure(test_results):
    failure_rate = test_results.failed / test_results.total
    if failure_rate > 0.10:
        fracas_manager.create_failure_mode(
            title=f"Test failure rate {failure_rate:.1%}",
            trigger="automated_test_analysis",
            evidence=test_results.summary
        )
```

### Manual Trigger Procedures

#### Developer-Initiated FRACAS
When developers encounter issues not caught by automated triggers:

1. **Assess Impact**: Determine if issue meets manual trigger criteria
2. **Create Entry**: Use `create_fracas_entry` script or manual documentation
3. **Document Evidence**: Include logs, error messages, reproduction steps
4. **Assign Severity**: Based on business and technical impact
5. **Update Status**: Track investigation progress

#### Team Lead Override
Team leads can create FRACAS entries for:
- **Strategic technical decisions** requiring documentation
- **Architecture changes** with potential failure modes
- **Process improvements** based on recurring issues
- **Knowledge capture** for complex problem resolutions

## Automated FRACAS Entry Format

### Required Fields for Automated Entries
```markdown
### FM-AUTO-YYYYMMDDHHMMSS: [Auto-Generated Title]
- **Severity**: [Determined by trigger criteria]
- **Status**: 🔍 Under Investigation
- **Trigger**: [Automated trigger name]
- **First Observed**: [Timestamp]
- **Auto-Created**: Yes

**Symptoms:**
- [Automated description of observed behavior]
- [Relevant metrics or thresholds exceeded]

**Evidence:**
- [Automated log collection]
- [System metrics at time of trigger]
- [Relevant configuration snapshots]

**Next Actions:**
- [ ] Manual investigation required
- [ ] Assign to appropriate team member
- [ ] Gather additional evidence
- [ ] Determine root cause
```

## Integration with Development Tools

### GitHub Actions Integration
```yaml
# .github/workflows/fracas-auto-trigger.yml
name: FRACAS Auto-Trigger
on:
  workflow_run:
    workflows: ["CI/CD Pipeline"]
    types: [completed]

jobs:
  check-fracas-triggers:
    runs-on: ubuntu-latest
    steps:
      - name: Check Build Time
        run: |
          if [[ ${{ github.event.workflow_run.duration }} -gt 1800 ]]; then
            echo "BUILD_TIME_EXCEEDED=true" >> $GITHUB_ENV
          fi
      
      - name: Create FRACAS Entry
        if: env.BUILD_TIME_EXCEEDED == 'true'
        run: |
          python scripts/create_fracas_entry.py \
            --trigger "build_time_exceeded" \
            --evidence "Build duration: ${{ github.event.workflow_run.duration }}s"
```

### Monitoring System Integration
```bash
# Example Prometheus AlertManager webhook
curl -X POST http://localhost:8000/fracas-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "alert": "high_error_rate",
    "severity": "critical", 
    "threshold": "10%",
    "current": "15%",
    "duration": "20m"
  }'
```

### Testing Framework Integration
```python
# pytest plugin for automatic FRACAS creation
import pytest
from fracas_manager import FracasManager

def pytest_runtest_logreport(report):
    if report.failed and report.when == "call":
        failure_rate = get_current_failure_rate()
        if failure_rate > 0.10:
            FracasManager().create_auto_entry(
                trigger="test_failure_threshold",
                test_name=report.nodeid,
                failure_rate=failure_rate
            )
```

## FRACAS Entry Management

### Status Automation
```python
# Automatic status progression
class FracasStatusManager:
    def update_status(self, fm_id, new_evidence):
        entry = self.get_entry(fm_id)
        
        # Auto-progress from investigation to known issue
        if entry.status == "investigation" and self.has_workaround(entry):
            entry.status = "known_issue"
            entry.add_note("Workaround identified - auto-promoted to known issue")
        
        # Auto-close resolved entries
        if self.is_resolved(entry) and entry.status != "fixed":
            entry.status = "fixed"
            entry.add_note("Resolution verified - auto-closed")
```

### Assignment Rules
```python
# Automatic assignment based on trigger type
ASSIGNMENT_RULES = {
    "database_*": "database_team",
    "frontend_*": "ui_team", 
    "api_*": "backend_team",
    "security_*": "security_team",
    "performance_*": "performance_team"
}

def auto_assign_fracas(fm_id, trigger):
    for pattern, team in ASSIGNMENT_RULES.items():
        if fnmatch(trigger, pattern):
            assign_to_team(fm_id, team)
            break
```

## Quality Assurance

### Trigger Accuracy Monitoring
- **False Positive Rate**: <20% for automated triggers
- **False Negative Review**: Weekly analysis of missed issues
- **Threshold Tuning**: Monthly review and adjustment
- **Trigger Effectiveness**: Quarterly assessment

### Documentation Quality
- **Automated entries** must include sufficient context for manual investigation
- **Evidence collection** must be comprehensive and actionable
- **Status tracking** must be accurate and current
- **Resolution documentation** must prevent recurrence

### Team Training
- **New team members** trained on trigger criteria and FRACAS workflow
- **Regular reviews** of trigger effectiveness and accuracy
- **Process improvements** based on team feedback and outcomes
- **Tool updates** to improve automation and reduce manual overhead

## Maintenance and Improvement

### Regular Reviews
- **Weekly**: Review new automated FRACAS entries for accuracy
- **Monthly**: Analyze trigger patterns and adjust thresholds
- **Quarterly**: Assess overall FRACAS effectiveness
- **Annually**: Comprehensive trigger criteria review and update

### Continuous Improvement
- **Feedback Collection**: From team members using automated FRACAS
- **Pattern Analysis**: Identify common failure modes and improve triggers
- **Tool Enhancement**: Improve automation and integration capabilities
- **Process Refinement**: Streamline workflows based on usage patterns

---

**Next Review**: 2025-10-18  
**Owner**: Development Team  
**Approver**: Technical Lead

This document ensures consistent, proactive failure tracking through automated FRACAS creation while maintaining the quality and effectiveness of the failure analysis process.