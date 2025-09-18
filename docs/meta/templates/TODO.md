# TODO XXX — {InitiativeName}

## Phase 0 — Context Harvest
- [ ] Review adjacent components in CONTEXT.md
- [ ] Update ADJACENT_INDEX.md with current dates
- [ ] Collect interface contracts from adjacent systems
- [ ] Validate token budget allocation
- [ ] **Create fracas.md** for failure tracking using FRACAS methodology
- [ ] Block: Implementation cannot proceed until Phase 0 complete

## Phase 1 — Planning
- [ ] Complete PRD.md
- [ ] Complete RFC.md
- [ ] Review with stakeholders
- [ ] Update adjacency.json if needed
- [ ] **Phase 1 Testing Summary** for handoff to Phase 2

## Phase 2 — Implementation
- [ ] {Implementation tasks}
- [ ] Unit tests
- [ ] Integration tests
- [ ] **Document any failures** in fracas.md immediately when encountered
- [ ] **Phase 2 Testing Summary** for handoff to Phase 3

## Phase 3 — Validation
- [ ] End-to-end testing
- [ ] Performance validation
- [ ] Documentation updates
- [ ] Deployment readiness
- [ ] **Resolve all critical failure modes** in fracas.md before deployment
- [ ] **Phase 3 Testing Summary** for handoff to Phase 4 (if applicable)

## Initiative Completion
- [ ] **Final Testing Summary** - Comprehensive testing report across all phases
- [ ] **Technical Debt Documentation** - Complete technical debt catalog and remediation roadmap

## Blockers
- {List current blockers and dependencies}

## Notes
- {Implementation notes and decisions}

## FRACAS Integration
- **Failure Tracking**: All failures, bugs, and unexpected behaviors must be documented in `fracas.md`
- **Investigation Process**: Follow systematic FRACAS methodology for root cause analysis
- **Knowledge Building**: Use failure modes to build organizational knowledge and prevent recurrence
- **Status Management**: Keep failure mode statuses current and move resolved issues to historical section

**FRACAS Document Location**: `docs/initiatives/{initiative_name}/fracas.md`