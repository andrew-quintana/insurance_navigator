# Phase 2 Execution Prompt: Webhook Implementation & API Updates

## Context
You are implementing Phase 2 of the 002 Worker Refactor iteration. This phase builds on Phase 1's infrastructure to implement secure webhook handling and enhanced APIs for LlamaParse integration.

## Documentation References
Please review these documents before starting implementation:
- `@docs/initiatives/system/upload_refactor/002/CONTEXT002.md` - Core architecture and webhook contract
- `@docs/initiatives/system/upload_refactor/002/TODO002.md` - Detailed implementation checklist (Phase 2 section)
- `@docs/initiatives/system/upload_refactor/002/RFC002.md` - Technical design for webhook security
- `@TODO002_phase1_notes.md` - Phase 1 implementation details
- `@TODO002_phase1_decisions.md` - Previous architectural decisions
- `@TODO002_phase1_handoff.md` - API requirements from Phase 1

## Primary Objective
Implement secure webhook endpoint and API updates for LlamaParse integration including:
1. HMAC-secured webhook endpoint for LlamaParse callbacks
2. LlamaParse client integration with webhook URL support
3. Enhanced job status API with buffer-based progress tracking
4. Comprehensive security and authentication framework

## Key Implementation Requirements

### Secure Webhook Endpoint
- Implement `POST /webhooks/llamaparse` with HMAC signature verification
- Add payload validation and duplicate callback handling
- Integrate blob storage writes using backend service credentials
- Provide atomic job status updates with artifact persistence

### LlamaParse Client Integration
- Create LlamaParse API client with webhook URL support
- Implement signed URL generation for document uploads
- Add per-job webhook secret generation for enhanced security
- Support parse job submission with callback configuration

### Enhanced Job Status API
- Update job status endpoint with real-time progress from buffer tables
- Add detailed error reporting with correlation IDs
- Implement manual retry capability from failed states
- Provide stage-level progress percentages and estimated completion times

### Security Implementation
- Multi-layer webhook security (HMAC, timestamp, IP validation)
- Replay protection using nonce tracking
- Comprehensive input validation and sanitization
- Security monitoring and alerting framework

## Expected Outputs
Document your work in these files:
- `@TODO002_phase2_notes.md` - Webhook implementation details and integration patterns
- `@TODO002_phase2_decisions.md` - Security architecture decisions and trade-offs
- `@TODO002_phase2_handoff.md` - BaseWorker requirements and integration points for Phase 3
- `@TODO002_phase2_testing_summary.md` - Security testing results and validation

## Success Criteria
- Webhook endpoint handles LlamaParse callbacks securely with HMAC verification
- Job status API provides real-time progress tracking from buffer tables
- Security framework prevents replay attacks and validates all inputs
- Manual retry functionality works correctly from all failed states
- Integration tests demonstrate end-to-end webhook processing

## Implementation Notes
- Follow the webhook contract specification in CONTEXT002.md exactly
- Implement security-first design with defense in depth
- Use the detailed checklist in TODO002.md Phase 2 section as your guide
- Ensure atomic operations for all job status updates
- Document any security considerations or design decisions

Start by reading the referenced documentation and Phase 1 outputs, then proceed with implementation following the detailed security and webhook requirements.