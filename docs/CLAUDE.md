# Claude Code Rules

## Date and Time Documentation
When documenting dates or times in any file, always use CLI commands to get the current date and time instead of hardcoding them.

### Commands to use:
- `date` - Get current date and time
- `date +"%Y-%m-%d"` - Get date in YYYY-MM-DD format
- `date +"%Y-%m-%d %H:%M:%S"` - Get full timestamp
- `date +"%Y-%m-%d %H:%M:%S %Z"` - Get timestamp with timezone

### Examples:
```bash
# Instead of writing "Created on 2025-09-21"
echo "Created on $(date +"%Y-%m-%d")"

# Instead of writing "Last updated: 2025-09-21 10:30:00"
echo "Last updated: $(date +"%Y-%m-%d %H:%M:%S")"
```

This ensures timestamps are always accurate and current when documentation is generated.

## FRACAS Methodology Integration
For systematic failure tracking and resolution, reference the complete FRACAS (Failure Reporting, Analysis, and Corrective Actions System) methodology documented in `@docs/meta/cursor_rules_fracas.md`.

### Key FRACAS Requirements:
- Create incident documentation under `docs/incidents/fm_XXX/` for all significant failures
- Use systematic failure mode identifiers (FM-001, FM-002, etc.)
- Follow evidence-based root cause analysis process
- Document corrective actions with verification
- Include commit references using `Addresses: FM-XXX` format
- Maintain comprehensive failure knowledge base

### When to Create FRACAS Documentation:
- Production system downtime >5 minutes
- Data loss or corruption of any amount
- Security breach or vulnerability exploitation
- Build failures taking >30 minutes to resolve
- Performance degradation >50% from baseline
- Integration failures between system components
- Test failures requiring >2 hours investigation
- Any systemic issues affecting code quality or system reliability