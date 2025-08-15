# PRD Generation Prompt Template

Create a comprehensive PRD{serial}.md file for [PROJECT/FEATURE NAME].

**DOCUMENT SERIAL NUMBER:**
- Serial number to use: [Specify the serial number (e.g., 001, 002, 003) or leave blank for auto-detection]
- Auto-detection: If no serial specified, check existing files to determine next available number

**PROJECT CONTEXT:**
- Project: [Your project name and brief description]
- Target users: [Who will use this feature]
- Current state: [What exists now, if extending existing functionality]

**FEATURE SCOPE:**
- Primary goal: [Main objective you want to achieve]
- Key functionality: [Core capabilities needed]
- Integration points: [How this connects to existing systems]

**CONSTRAINTS:**
- Timeline: [Your deadline/timeframe]
- Technical requirements: [Stack, platform, performance needs]
- Compliance/security: [Any regulatory or security requirements]
- Resource limitations: [Team size, budget, etc.]

**REFERENCE MATERIALS:**
Consider these existing files/docs when creating the PRD:
- [List relevant codebase files/directories]
- [Existing documentation files]
- [User research, mockups, etc.]

**COLLABORATION NOTES:**
- Stakeholder review needed: [Yes/No and who]
- Technical review required: [Yes/No and who]
- Decision authority: [Who approves final PRD]

Generate a structured PRD{serial}.md following your documentation generation agent system, focusing on problem definition, success metrics, user stories, functional/non-functional requirements, and acceptance criteria.

**SERIAL NUMBER DETERMINATION:**
1. **Specified in prompt**: Use the serial number provided in the "DOCUMENT SERIAL NUMBER" section
2. **Auto-detection**: If no serial specified, scan the initiatives directory for existing files:
   - Look for files matching pattern: `docs/initiatives/**/PRD*.md`
   - Find the highest existing serial number
   - Use the next available number (e.g., if PRD001.md and PRD003.md exist, use 004)
3. **New project**: If no existing files found, start with 001