# RFC Generation Prompt Template

Create a comprehensive RFC{serial}.md file for [PROJECT/FEATURE NAME], using the completed PRD{serial}.md as foundational context.

**DOCUMENT SERIAL NUMBER:**
- Serial number to use: [Specify the serial number (e.g., 001, 002, 003) or leave blank for auto-detection]
- Auto-detection: If no serial specified, check existing files to determine next available number

**REFERENCE THE PRD:**
- PRD file location: [Path to your PRD{serial}.md]
- Key requirements from PRD: [Summarize main functional requirements]
- Success metrics to achieve: [From PRD success criteria]

**TECHNICAL CONTEXT:**
- Current architecture: [Existing system components this will integrate with]
- Technology stack: [Languages, frameworks, databases, APIs]
- Performance requirements: [From PRD non-functional requirements]
- Integration points: [Existing services/APIs to connect with]

**DESIGN CONSIDERATIONS:**
- Primary technical challenges: [What are the hard problems to solve]
- Alternative approaches considered: [Other ways you might implement this]
- Architecture decisions needed: [Key technical choices to make]

**REFERENCE MATERIALS:**
Consider these when designing the technical solution:
- [Relevant existing code files/modules]
- [Architecture documentation]
- [API specifications]
- [Database schemas]

**IMPLEMENTATION PLANNING:**
- Phased rollout strategy: [How to implement incrementally]
- Risk mitigation: [Technical risks and how to handle them]
- Testing strategy: [How to validate the solution]

Generate a detailed RFC{serial}.md that defines the technical architecture, key decisions with rationale, implementation phases, and testing strategy - all aligned with the PRD requirements.

## Document Serialization Note
Use the next available serial number (RFC{serial}.md, RFC{serial+1}.md, etc.) to maintain version control and enable parallel exploration of different technical approaches.

**SERIAL NUMBER DETERMINATION:**
1. **Specified in prompt**: Use the serial number provided in the "DOCUMENT SERIAL NUMBER" section
2. **Auto-detection**: If no serial specified, scan the initiatives directory for existing files:
   - Look for files matching pattern: `docs/initiatives/**/RFC*.md`
   - Find the highest existing serial number
   - Use the next available number (e.g., if RFC001.md and RFC003.md exist, use 004)
3. **New project**: If no existing files found, start with 001