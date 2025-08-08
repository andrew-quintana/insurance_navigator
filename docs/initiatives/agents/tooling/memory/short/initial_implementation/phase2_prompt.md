# Phase 2 Prompt: API Infrastructure & Manual Triggers

You are implementing **Phase 2** of the Short-Term Chat Memory MVP. This phase focuses on creating the manual trigger API endpoints that initiate memory updates.

## Project Context

**Goal**: Create REST API endpoints for manually triggering memory updates and retrieving memories
**Scope**: Manual operation only (no automatic workflow integration)
**Architecture**: REST API with input validation, authentication, and error handling
**Database**: Built on Phase 1 foundation with existing CRUD operations

## Required Reading

Before starting, read these files for complete context:
- `/Users/aq_home/1Projects/accessa/insurance_navigator/docs/initiatives/agents/tooling/memory/short/initial_implementation/RFC001.md` (API specification)
- `/Users/aq_home/1Projects/accessa/insurance_navigator/docs/initiatives/agents/tooling/memory/short/initial_implementation/TODO001.md` (complete implementation plan)
- `@TODO001_phase1_notes.md` (database implementation details from Phase 1)
- `@TODO001_phase1_decisions.md` (database design context from Phase 1)  
- `@TODO001_phase1_handoff.md` (available database functions from Phase 1)

## API Requirements

From RFC001.md, implement these two core endpoints:

### Memory Update Endpoint
```http
POST /api/v1/memory/update
Content-Type: application/json

{
  "chat_id": "uuid",
  "context_snippet": "string", 
  "trigger_source": "manual|api|test"
}

Response: 201 Created
{
  "queue_id": "uuid",
  "status": "pending_summarization",
  "estimated_completion": "2025-08-07T12:34:58Z"
}
```

### Memory Retrieval Endpoint
```http
GET /api/v1/memory/{chat_id}

Response: 200 OK
{
  "chat_id": "uuid",
  "user_confirmed": {...},
  "llm_inferred": {...}, 
  "general_summary": "string",
  "last_updated": "2025-08-07T12:34:56Z"
}
```

## Implementation Tasks

### 1. Environment Setup
- Review existing API patterns and authentication in the codebase
- Identify API routing and middleware configuration
- Locate existing rate limiting and validation utilities
- Set up API testing environment
  - Ensure a way to obtain a valid `chat_id` by creating a conversation (e.g., `POST /conversations`) since memory endpoints validate existence in `public.conversations`

### 2. Memory Update Endpoint Implementation
- Create `POST /api/v1/memory/update` route handler
- Implement comprehensive input validation:
  - Validate chat_id as valid UUID format
  - Validate context_snippet as non-empty string
  - Validate trigger_source enum (manual|api|test)
  - Check chat_id exists in chats table
- Use Phase 1 CRUD functions to insert queue entry with 'pending_summarization' status
- Generate unique queue_id and calculate estimated completion time (2 seconds from RFC)
- Return proper HTTP status codes and error responses

### 3. Memory Retrieval Endpoint Implementation  
- Create `GET /api/v1/memory/{chat_id}` route handler
- Implement chat_id parameter validation (UUID format and existence)
- Use Phase 1 CRUD functions to query chat_metadata table
- Handle missing memory records gracefully (return default structure)
- Format response with all three memory fields and metadata
- Include last_updated timestamp and proper error handling

### 4. Security & Validation Implementation
- **Authentication**: Integrate existing platform authentication patterns
- **Rate Limiting**: Implement 100 requests/minute limit per user (from RFC)
- **Input Sanitization**: Sanitize context_snippet to prevent XSS/injection attacks
- **Request Validation**: Validate JSON structure and content-length limits
- **Audit Logging**: Add comprehensive request/response logging for debugging

### 5. Testing & Documentation
- Create manual testing interface or scripts for API validation
- Implement comprehensive API tests:
  - Test successful memory update and retrieval requests
  - Test input validation error cases
  - Test authentication and rate limiting
  - Test concurrent API requests
  - End-to-end flow: `POST /conversations` → `POST /api/v1/memory/update` → `GET /api/v1/memory/{chat_id}`
- Add API documentation with request/response examples
- Create load testing scripts for concurrent API usage

### 6. Error Handling & Monitoring
- Implement consistent error response format across endpoints
- Handle database connection errors gracefully
- Add comprehensive request/response logging
- Create monitoring hooks for API usage tracking
- Implement basic health check endpoint

## Expected Outputs

Save your work in these files:
- `@TODO001_phase2_notes.md`: API implementation details, authentication setup, testing procedures, performance considerations
- `@TODO001_phase2_decisions.md`: API design choices, security approach, error handling strategy, rate limiting decisions
- `@TODO001_phase2_handoff.md`: Available API endpoints and specifications, testing tools, authentication setup for Phase 3, any unresolved issues

## Success Criteria

- Both API endpoints implemented with proper validation and error handling
- Authentication and rate limiting working correctly
- Input sanitization preventing security vulnerabilities
- Comprehensive API tests passing for all scenarios
- Manual testing interface operational for validation
- Complete API documentation with examples
- Phase 1 CRUD functions successfully integrated

## Development Notes

- Follow existing codebase patterns for API routes, middleware, and authentication
- Use the exact API specifications from RFC001.md without modifications
- Ensure proper HTTP status codes for all response scenarios
- Test with realistic concurrent load to validate rate limiting
- Document any API design decisions or security trade-offs made
- Verify integration with Phase 1 database functions works correctly

Begin by reading all required files, then proceed with environment setup and API endpoint implementation.