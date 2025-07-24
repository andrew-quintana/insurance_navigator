# RFC Generation Prompt Template

Create a comprehensive RFC001.md file for [PROJECT/FEATURE NAME], using the completed PRD001.md as foundational context.

**REFERENCE THE PRD:**
- PRD file location: [Path to your PRD001.md]
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

Generate a detailed RFC001.md that defines the technical architecture, key decisions with rationale, implementation phases, and testing strategy - all aligned with the PRD requirements.

## Document Serialization Note
Use the next available serial number (RFC001.md, RFC002.md, etc.) to maintain version control and enable parallel exploration of different technical approaches.