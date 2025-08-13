# Phased TODO Generation Prompt Template

Create a comprehensive TODO001.md implementation breakdown for [PROJECT/FEATURE NAME], using both the PRD001.md and RFC001.md as context. This TODO will be organized into phases designed for execution in separate coding agent sessions, optimized for Cursor's coding agent in 'auto-select model' mode.

**REFERENCE DOCUMENTS:**
- PRD file: [Path to PRD001.md] - for requirements and acceptance criteria
- RFC file: [Path to RFC001.md] - for technical architecture and implementation plan
- Key deliverables: [Main features/components from PRD]
- Technical approach: [Architecture decisions from RFC]

**CURRENT CODEBASE CONTEXT:**
- Existing code to modify: [Relevant files/directories]
- New components to create: [Based on RFC architecture]
- Integration points: [Existing APIs/services to connect with]
- Testing infrastructure: [Current test setup and frameworks]

**IMPLEMENTATION PREFERENCES:**
- Development approach: [Sequential vs parallel, pair programming, etc.]
- Code review process: [How you want code reviewed]
- Testing strategy: [Unit/integration/e2e testing priorities]
- Documentation needs: [Code comments, user docs, deployment guides]

**CONSTRAINTS:**
- Timeline: [From PRD constraints]
- Resource availability: [Team capacity, external dependencies]
- Technical limitations: [Platform constraints, performance requirements]

**VALIDATION REQUIREMENTS:**
- Acceptance criteria: [From PRD]
- Performance benchmarks: [From RFC]
- Security/compliance checks: [From PRD constraints]

**PHASED EXECUTION METHODOLOGY:**
Generate a detailed TODO.md organized into distinct phases. Each phase should:

1. **Be self-contained** - Executable in a separate Claude Code chat/REPL session
2. **Include clear inputs** - List all files, documents, and context needed for that phase
3. **Specify outputs** - Define what documentation/notes should be saved for future phases
4. **Reference previous phases** - Use saved outputs from earlier phases (e.g., @TODO001_phase1_notes.md)
5. **Include session reset instructions** - Remind to run `/clear` or restart before beginning each new phase
6. **Discrete, appropriately sized phases** - Phase scope should be limited to reduce potential for overwhelming the coding agent and developer reviewing the code

**PHASE STRUCTURE:**
Organize tasks into logical phases such as:
- **Phase 1: Setup & Foundation** (environment, dependencies, initial structure)
- **Phase 2: Core Implementation** (main functionality, key components)
- **Phase 3: Integration & Testing** (connecting components, validation)
- **Phase 4: Documentation & Deployment** (final docs, deployment preparation)

**PHASE TEMPLATE FORMAT:**
For each phase, include:
```
## Phase X: [Phase Name]

### Prerequisites
- Files/documents to read: [specific file paths]
- Previous phase outputs: [@TODO001_phaseX_notes.md, @TODO001_phaseX_decisions.md, etc.]
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session. Use only the inputs provided below, do not rely on prior conversation history.

[Provide all necessary context, file references, and background information needed for this phase]

### Tasks
[Detailed, actionable tasks for this phase]

### Expected Outputs
- Save implementation notes to: @TODO001_phase[X]_notes.md
- Document any architectural decisions in: @TODO001_phase[X]_decisions.md
- List any issues/blockers for next phase in: @TODO001_phase[X]_handoff.md
 - Save testing update in: @TODO001_phase[X]_test_update.md (include: tests executed, results, coverage deltas, assumptions validated, assumptions remaining, new risks/debt)

### Progress Checklist
#### Setup
- [ ] Task 1
- [ ] Task 2
  - [ ] Subtask 2a
  - [ ] Subtask 2b

#### Implementation
- [ ] Task 3
- [ ] Task 4

#### Validation
- [ ] Task 5
- [ ] Task 6
 - [ ] Save @TODO001_phase[X]_test_update.md (tests run, results, assumptions validated/remaining)

#### Documentation
- [ ] Save @TODO001_phase[X]_notes.md
- [ ] Save @TODO001_phase[X]_decisions.md
- [ ] Save @TODO001_phase[X]_handoff.md
 - [ ] Save @TODO001_phase[X]_test_update.md
```

**FINAL PROJECT CHECKLIST:**
At the end of the TODO.md, include a comprehensive project completion checklist:

```
## Project Completion Checklist

### Phase 1: Setup & Foundation
- [ ] Environment configured
- [ ] Dependencies installed
- [ ] Initial project structure created
- [ ] Phase 1 documentation saved

### Phase 2: Core Implementation
- [ ] Main components implemented
- [ ] Core functionality working
- [ ] Unit tests passing
- [ ] Phase 2 documentation saved

### Phase 3: Integration & Testing
- [ ] Components integrated
- [ ] Integration tests passing
- [ ] Performance requirements met
- [ ] Phase 3 documentation saved

### Phase 4: Documentation & Deployment
- [ ] User documentation complete
- [ ] Code documentation complete
- [ ] Deployment process verified
- [ ] Final validation complete
 - [ ] Technical debt summary saved as DEBT001.md (outstanding assumptions, known debt, mitigation plan)

### Project Sign-off
- [ ] All acceptance criteria met (from PRD)
- [ ] Performance benchmarks achieved (from RFC)
- [ ] Security/compliance requirements satisfied
- [ ] Stakeholder approval received
- [ ] Project ready for production
```

Generate the complete phased TODO001.md following this methodology with detailed progress checklists for each phase.

## Document Serialization Note
Use the serialization pattern TODO001.md, TODO002.md, etc. for different implementation approaches. Phase documentation should follow the pattern `@TODO001_phaseX_notes.md`, `@TODO001_phaseX_decisions.md`, etc. to prevent confusion when multiple TODO implementations exist.