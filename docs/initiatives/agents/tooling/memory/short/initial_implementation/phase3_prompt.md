# Phase 3 Prompt: Memory Processing & MCP Agent Integration

You are implementing **Phase 3** of the Short-Term Chat Memory MVP. This phase focuses on creating the MCP summarizer agent and sequential processing logic that handles memory updates.

## Project Context

**Goal**: Implement MCP summarizer agent and queue processing system for memory updates
**Scope**: Agent follows base MCP pattern, sequential processing handles queue management
**Architecture**: MCP agent generates summaries, processing step persists to database
**Memory Logic**: Three-field summary structure with token counting and size limits

## Required Reading

Before starting, read these files for complete context:
- `/Users/aq_home/1Projects/accessa/insurance_navigator/docs/initiatives/agents/tooling/memory/short/initial_implementation/RFC001.md` (MCP agent specification)
- `/Users/aq_home/1Projects/accessa/insurance_navigator/docs/initiatives/agents/tooling/memory/short/initial_implementation/PRD001.md` (memory field requirements)
- `/Users/aq_home/1Projects/accessa/insurance_navigator/docs/initiatives/agents/tooling/memory/short/initial_implementation/TODO001.md` (complete implementation plan)
- `@TODO001_phase1_notes.md` (database functions from Phase 1)
- `@TODO001_phase2_notes.md` (API implementation details from Phase 2)
- `@TODO001_phase1_handoff.md` (database interface from Phase 1)
- `@TODO001_phase2_handoff.md` (API interface from Phase 2)

## Processing Requirements

From RFC001.md, implement these core components:

### MCP Summarizer Agent
- Uses Claude Haiku as the underlying model
- Follows existing base MCP agent patterns for consistency
- Generates three-field summaries: `user_confirmed`, `llm_inferred`, `general_summary`
- Handles incremental updates (prior memory + new context snippet)
- Implements token counting and size threshold enforcement
- Includes comprehensive error handling and timeout management

### Sequential Processing Step
- Background process that monitors `chat_context_queue` table
- Processes entries with status 'pending_summarization' in FIFO order
- Invokes MCP summarizer agent with proper error handling
- Updates `chat_metadata` using Phase 1 CRUD functions
- Manages processing lifecycle and retry mechanisms

## Implementation Tasks

### 1. Environment Setup
- Review existing MCP agent implementations for pattern reference
- Identify MCP infrastructure components (permissions, monitoring)
- Locate Claude Haiku configuration and API integration patterns
- Set up development environment for MCP agent testing

### 2. MCP Summarizer Agent Implementation
- **Agent Foundation**: 
  - Follow existing base agent pattern structure
  - Configure Claude Haiku model initialization
  - Add agent configuration management
  - Implement basic agent lifecycle (start/stop/health)

- **Summarization Logic**:
  - Create prompts for three-field summary generation
  - Add logic to categorize facts into user_confirmed vs llm_inferred
  - Generate coherent general_summary from chat context
  - Handle incremental updates (merge prior memory + new context)

- **Token Management**:
  - Implement token counting for generated summaries
  - Check against size threshold from PRD requirements
  - Handle size threshold exceeded (return new chat prompt)
  - Optimize summary generation for token efficiency

- **Agent Interface**:
  - Create clean invocation interface for processing step
  - Add input validation for context and prior memory
  - Implement comprehensive error handling
  - Add timeout management and retry logic
  - Follow MCP monitoring and logging patterns

### 3. Sequential Processing Step Implementation
- **Queue Monitoring**:
  - Create background process for queue monitoring
  - Query `chat_context_queue` for pending entries
  - Implement FIFO processing with concurrency limits
  - Add processing status tracking and updates

- **Memory Update Pipeline**:
  - Retrieve existing memory from `chat_metadata`
  - Prepare context for MCP agent (prior memory + snippet)
  - Invoke MCP summarizer agent with proper error handling
  - Validate generated summary structure and fields
  - Update `chat_metadata` using Phase 1 CRUD functions
  - Mark queue entry as complete and clean up

- **Error Handling & Reliability**:
  - Add retry logic for failed MCP invocations
  - Handle partial failures (agent success, DB failure)
  - Implement circuit breaker for processing bottlenecks
  - Add comprehensive logging for debugging
  - Create monitoring hooks for processing metrics

### 4. Testing & Validation
- **MCP Agent Unit Tests**:
  - Test summary generation with various input scenarios
  - Test three-field categorization accuracy
  - Test token counting and size threshold handling
  - Test error handling and timeout scenarios

- **Sequential Processing Tests**:
  - Test queue processing with mock data
  - Test end-to-end memory update flow
  - Test retry mechanisms and error recovery
  - Test concurrent queue processing

- **Integration Testing**:
  - Test full pipeline: API trigger → queue → MCP → database
  - Test memory continuity across multiple updates
  - Test processing performance under load
  - Validate memory quality and accuracy

### 5. Monitoring & Observability
- Add key metrics for MCP agent performance
- Create monitoring dashboards for queue processing
- Implement alerting for processing bottlenecks
- Add comprehensive logging for debugging and troubleshooting

## Memory Structure Requirements

The MCP agent must generate summaries with this exact structure:

```json
{
  "user_confirmed": {
    // Facts explicitly confirmed by the user
    // E.g., {"insurance_type": "health", "budget": "under_500"}
  },
  "llm_inferred": {
    // Model-derived assumptions not directly confirmed
    // E.g., {"urgency": "high", "technical_comfort": "low"}
  },
  "general_summary": "Coherent summary of chat goals and progress"
}
```

## Expected Outputs

Save your work in these files:
- `@TODO001_phase3_notes.md`: MCP agent implementation details, processing architecture, testing results, performance characteristics
- `@TODO001_phase3_decisions.md`: MCP agent design choices, processing architecture decisions, error handling strategy, performance optimizations
- `@TODO001_phase3_handoff.md`: MCP agent interface and usage, processing configuration, monitoring tools, unresolved issues

## Success Criteria

- MCP summarizer agent operational following base agent patterns
- Three-field summary generation working accurately
- Token counting and size threshold enforcement implemented
- Sequential processing step handling queue entries correctly
- End-to-end memory update pipeline functional
- Comprehensive error handling and retry mechanisms working
- Integration tests passing for full API → queue → MCP → database flow
- Performance meets RFC requirements (2-second update completion)

## Development Notes

- Follow existing MCP infrastructure patterns for consistency
- Use Claude Haiku specifically as specified in RFC001.md
- Ensure agent integrates with existing MCP permissions and monitoring
- Test with realistic memory scenarios and edge cases
- Document any prompt engineering decisions or trade-offs made
- Verify integration with Phase 1 database and Phase 2 API functions

Begin by reading all required files to understand the complete system architecture, then proceed with MCP agent pattern research and implementation.