# TODO002: Worker Refactor Implementation - Single BaseWorker Architecture

## Context & Overview

This TODO provides detailed implementation tasks for the 002 Worker Refactor iteration, transitioning from specialized workers to a unified BaseWorker architecture with buffer-driven pipeline orchestration. The implementation prioritizes idempotency, resilience, and horizontal scalability.

**Key Deliverables:**
- Replace specialized workers with single BaseWorker class
- Implement buffer-driven persistence for all processing stages
- Deploy secure webhook endpoint for LlamaParse callbacks
- Enable micro-batch processing for efficient embedding generation

**Technical Approach:**
- State machine-driven processing with atomic status transitions
- Buffer tables (document_chunk_buffer, document_vector_buffer) for staging
- Idempotent operations with deterministic UUIDs
- External service integration with comprehensive retry logic

---

## Phase 1: Infrastructure & Buffer Tables

### Prerequisites
- Files/documents to read:
  - `@docs/initiatives/system/upload_refactor/CONTEXT.md`
  - `@docs/initiatives/system/upload_refactor/RFC002.md`
  - `@docs/initiatives/system/upload_refactor/PRD002.md`
- Previous work: Understanding of 001 iteration limitations and lessons learned
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session for Phase 1 of the 002 Worker Refactor. Use the provided documentation to understand the buffer-driven architecture.

You are implementing the foundation for the unified BaseWorker architecture. This phase focuses on:
1. Database schema updates for enhanced state management
2. Buffer table creation for staging persistence
3. Directory restructuring for better separation of concerns
4. Shared utility development for deterministic operations

### Tasks

#### T1.1: Enhanced Database Schema
- Update upload_jobs table with new status values and progress tracking
- Create document_chunk_buffer table for chunk staging
- Create document_vector_buffer table for embedding staging
- Add proper indexes for efficient worker polling and progress queries

#### T1.2: Directory Restructuring
- Reorganize codebase into backend/api/, backend/workers/, backend/shared/
- Move existing worker code to new structure
- Create shared utilities for database, storage, and external service clients
- Update import statements throughout codebase

#### T1.3: Shared Utilities Implementation
- Implement deterministic UUID generation with UUIDv5
- Create database connection and transaction management
- Develop storage client for Supabase blob operations
- Build structured logging framework with correlation IDs

#### T1.4: Buffer Management Foundation
- Implement idempotent buffer write operations
- Create buffer cleanup and archival processes
- Develop progress tracking utilities
- Build buffer-to-production promotion logic (optional)

### Expected Outputs
- Save implementation notes to: `@TODO002_phase1_notes.md`
- Document architectural decisions in: `@TODO002_phase1_decisions.md`
- List API implementation requirements in: `@TODO002_phase1_handoff.md`
- Create testing summary in: `@TODO002_phase1_testing_summary.md`

### Progress Checklist

#### Database Schema Updates
- [ ] Create enhanced upload_jobs table with new status values
  - [ ] Add status values: uploaded, parse_queued, parsed, parse_validated, chunking, chunks_stored, embedding_queued, embedding_in_progress, embeddings_stored, complete
  - [ ] Add error terminal states: failed_parse, failed_chunking, failed_embedding
  - [ ] Add progress JSONB field for counters
  - [ ] Add webhook_secret field for per-job webhook verification
- [ ] Create document_chunk_buffer staging table
  - [ ] Implement deterministic chunk_id as primary key
  - [ ] Add content integrity with chunk_sha field
  - [ ] Include metadata JSONB for processing context
  - [ ] Add unique constraint on (document_id, chunker_name, chunker_version, chunk_ord)
- [ ] Create document_vector_buffer staging table
  - [ ] Implement unique constraint on (chunk_id, embed_model, embed_version)
  - [ ] Add vector_sha for data integrity verification
  - [ ] Include batch_id for tracking micro-batch operations
  - [ ] Add foreign key relationship to document_chunk_buffer
- [ ] Add efficient indexes for worker operations
  - [ ] Status-based polling index with created_at ordering
  - [ ] Document-based lookups for progress tracking
  - [ ] Buffer table indexes for embedding progress queries

#### Directory Restructuring
- [ ] Create new backend/ directory structure
  - [ ] backend/api/ for FastAPI application and endpoints
  - [ ] backend/workers/ for BaseWorker and processing logic
  - [ ] backend/shared/ for common utilities and clients
  - [ ] backend/scripts/ for migrations and operational scripts
- [ ] Move existing worker code to new structure
  - [ ] Preserve existing functionality during transition
  - [ ] Update import statements throughout codebase
  - [ ] Maintain backward compatibility where needed
- [ ] Create shared utility modules
  - [ ] Database connection and transaction management
  - [ ] Storage client for Supabase operations
  - [ ] External service clients (LlamaParse, OpenAI)
  - [ ] Logging, rate limiting, and schema validation

#### Deterministic Operations
- [ ] Implement UUIDv5 generation utilities
  - [ ] Use namespace UUID: 6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42
  - [ ] Canonical string normalization (lowercase, colon-separated)
  - [ ] Unit tests for deterministic behavior across runs
- [ ] Create chunk ID generation
  - [ ] Format: "{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}"
  - [ ] Ensure consistency with existing chunk processing
  - [ ] Validate deterministic reproduction
- [ ] Implement content hashing utilities
  - [ ] SHA256 computation for chunk content
  - [ ] Vector hash generation for embedding verification
  - [ ] Parsed content normalization and hashing

#### Buffer Management
- [ ] Implement idempotent buffer operations
  - [ ] ON CONFLICT DO NOTHING for chunk buffer writes
  - [ ] UPSERT logic for vector buffer with vector_sha comparison
  - [ ] Atomic status updates tied to buffer writes
- [ ] Create buffer cleanup processes
  - [ ] Automated cleanup after job completion
  - [ ] Archival strategy for audit trail preservation
  - [ ] Monitoring for buffer table growth
- [ ] Develop progress tracking
  - [ ] Real-time progress calculation from buffer counts
  - [ ] Atomic progress updates per micro-batch
  - [ ] Progress API endpoint implementation

#### Testing & Validation
- [ ] Unit tests for deterministic operations
  - [ ] UUID generation consistency
  - [ ] Content hashing reproducibility
  - [ ] Buffer operation idempotency
- [ ] Integration tests for database operations
  - [ ] Schema migration validation
  - [ ] Buffer write and read operations
  - [ ] Index performance verification
- [ ] Load testing for buffer operations
  - [ ] Concurrent buffer writes
  - [ ] Large document processing
  - [ ] Progress tracking accuracy

#### Documentation
- [ ] Save `@TODO002_phase1_notes.md` with implementation details
- [ ] Save `@TODO002_phase1_decisions.md` with architectural choices
- [ ] Save `@TODO002_phase1_handoff.md` with API requirements
- [ ] Save `@TODO002_phase1_testing_summary.md` with test results

---

## Phase 2: Webhook Implementation & API Updates

### Prerequisites
- Files/documents to read:
  - `@TODO002_phase1_notes.md`
  - `@TODO002_phase1_decisions.md`
  - `@TODO002_phase1_handoff.md`
  - `@docs/initiatives/system/upload_refactor/CONTEXT.md`
- Previous phase outputs: Enhanced database schema, buffer tables, shared utilities
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session for Phase 2. Use previous phase outputs as context.

You are implementing the webhook endpoint and API updates for LlamaParse integration. This phase focuses on secure webhook handling, blob storage operations, and atomic job status updates tied to external service callbacks.

### Tasks

#### T2.1: Secure Webhook Endpoint
- Implement POST /webhooks/llamaparse with HMAC signature verification
- Add payload validation and duplicate callback handling
- Integrate blob storage writes using backend service credentials
- Provide atomic job status updates with artifact persistence

#### T2.2: LlamaParse Client Integration
- Create LlamaParse API client with webhook URL support
- Implement signed URL generation for document uploads
- Add per-job webhook secret generation for security
- Support parse job submission with callback configuration

#### T2.3: Enhanced Job Status API
- Update job status endpoint with buffer-based progress tracking
- Add real-time progress calculation from buffer table counts
- Implement detailed error reporting with correlation IDs
- Support manual retry capability from failed states

#### T2.4: Security & Authentication
- Implement multi-layer webhook security (HMAC, timestamp, IP validation)
- Add replay protection using nonce tracking
- Create comprehensive input validation and sanitization
- Develop security monitoring and alerting

### Expected Outputs
- Save implementation notes to: `@TODO002_phase2_notes.md`
- Document security decisions in: `@TODO002_phase2_decisions.md`
- List BaseWorker requirements in: `@TODO002_phase2_handoff.md`
- Create security testing summary in: `@TODO002_phase2_testing_summary.md`

### Progress Checklist

#### Webhook Endpoint Implementation
- [ ] Create secure webhook handler
  - [ ] POST /webhooks/llamaparse endpoint with FastAPI
  - [ ] HMAC-SHA256 signature verification
  - [ ] Timestamp validation within 5-minute window
  - [ ] JSON payload validation and parsing
- [ ] Implement artifact processing
  - [ ] Parse LlamaParse callback payload structure
  - [ ] Write markdown artifacts to Supabase Storage
  - [ ] Generate storage paths: storage://{user_id}/parsed/{document_id}.md
  - [ ] Compute and verify content SHA256 hashes
- [ ] Add atomic job updates
  - [ ] Update upload_jobs.parsed_path and parsed_sha256
  - [ ] Transition status from parse_queued to parsed
  - [ ] Log webhook processing events with correlation IDs
  - [ ] Handle idempotent callback processing

#### LlamaParse Integration
- [ ] Create LlamaParse API client
  - [ ] Async HTTP client with retry logic
  - [ ] Parse job submission with webhook URL
  - [ ] Signed URL generation for document access
  - [ ] Error handling for API failures
- [ ] Implement webhook security
  - [ ] Per-job webhook secret generation
  - [ ] HMAC signature creation and verification
  - [ ] Webhook URL construction with proper routing
- [ ] Add parse job management
  - [ ] Job submission with document metadata
  - [ ] Status tracking and timeout handling
  - [ ] Callback processing and verification

#### Enhanced Job Status API
- [ ] Update GET /jobs/{document_id} endpoint
  - [ ] Real-time progress from buffer table counts
  - [ ] Stage-level progress percentages
  - [ ] Detailed error information with context
  - [ ] Processing cost tracking
- [ ] Add buffer-based progress calculation
  - [ ] Count chunks in document_chunk_buffer
  - [ ] Count vectors in document_vector_buffer
  - [ ] Calculate completion percentages per stage
  - [ ] Provide estimated time remaining
- [ ] Implement manual retry capability
  - [ ] POST /jobs/{document_id}/retry endpoint
  - [ ] Reset from failed states to last successful stage
  - [ ] Clear retry counters and error state
  - [ ] Log retry operations for audit trail

#### Security Implementation
- [ ] Multi-layer webhook security
  - [ ] HMAC signature verification with secret rotation
  - [ ] Timestamp validation to prevent replay attacks
  - [ ] IP address allowlisting for LlamaParse origins
  - [ ] Request size limits and rate limiting
- [ ] Replay protection
  - [ ] Nonce tracking in webhook_log table
  - [ ] Duplicate callback detection and handling
  - [ ] Cleanup of old nonce entries
- [ ] Input validation and sanitization
  - [ ] Strict JSON schema validation
  - [ ] Content type and encoding verification
  - [ ] XSS and injection prevention
  - [ ] Error message sanitization

#### Error Handling & Monitoring
- [ ] Comprehensive error handling
  - [ ] Webhook processing errors with proper HTTP status codes
  - [ ] External service failure handling
  - [ ] Database transaction rollback on failures
  - [ ] Structured error logging with context
- [ ] Security monitoring
  - [ ] Failed authentication attempt tracking
  - [ ] Suspicious traffic pattern detection
  - [ ] Webhook processing metrics and alerts
  - [ ] Security event logging and analysis

#### Testing & Validation
- [ ] Webhook security testing
  - [ ] HMAC signature validation with various payloads
  - [ ] Timestamp tampering and replay attack tests
  - [ ] Invalid payload and injection attempt tests
  - [ ] Rate limiting and DDoS protection tests
- [ ] Integration testing
  - [ ] End-to-end LlamaParse webhook flow
  - [ ] Blob storage integration with service credentials
  - [ ] Job status updates and progress tracking
  - [ ] Error scenarios and recovery testing
- [ ] Performance testing
  - [ ] Concurrent webhook processing
  - [ ] Large document artifact handling
  - [ ] Database performance under webhook load

#### Documentation
- [ ] Save `@TODO002_phase2_notes.md` with webhook implementation details
- [ ] Save `@TODO002_phase2_decisions.md` with security architecture
- [ ] Save `@TODO002_phase2_handoff.md` with BaseWorker requirements
- [ ] Save `@TODO002_phase2_testing_summary.md` with security test results

---

## Phase 3: BaseWorker Implementation

### Prerequisites
- Files/documents to read:
  - `@TODO002_phase2_notes.md`
  - `@TODO002_phase2_decisions.md`
  - `@TODO002_phase2_handoff.md`
  - `@docs/initiatives/system/upload_refactor/CONTEXT.md`
- Previous phase outputs: Webhook endpoint, enhanced APIs, security framework
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session for Phase 3. Use previous phase outputs as context.

You are implementing the unified BaseWorker class that orchestrates all processing stages through a state machine. This phase focuses on stage-specific processing logic, micro-batch embedding generation, and comprehensive error handling.

### Tasks

#### T3.1: BaseWorker Core Framework
- Implement BaseWorker class with state machine processing logic
- Create job polling mechanism with efficient database queries
- Add stage-specific processing methods with atomic transitions
- Implement comprehensive error handling and retry scheduling

#### T3.2: Parse Validation Stage
- Validate parsed content and compute normalized SHA256 hashes
- Handle duplicate detection and canonical path assignment
- Implement atomic status transition from parsed to parse_validated
- Add detailed logging and error reporting

#### T3.3: Chunking Stage Processing
- Generate deterministic chunks with UUIDv5 identifiers
- Write chunks to document_chunk_buffer with idempotent operations
- Update job status to chunks_stored after successful buffer writes
- Validate chunk counts and content integrity

#### T3.4: Micro-Batch Embedding Stage
- Implement OpenAI API client with rate limiting and retry logic
- Process embeddings in micro-batches with immediate buffer persistence
- Update progress counters atomically per batch
- Handle embedding failures and partial completion scenarios

#### T3.5: External Service Integration
- Integrate rate limiting for OpenAI API calls
- Implement circuit breaker patterns for external service failures
- Add comprehensive retry logic with exponential backoff
- Create cost tracking and monitoring for external API usage

### Expected Outputs
- Save implementation notes to: `@TODO002_phase3_notes.md`
- Document processing patterns in: `@TODO002_phase3_decisions.md`
- List integration testing requirements in: `@TODO002_phase3_handoff.md`
- Create performance testing summary in: `@TODO002_phase3_testing_summary.md`

### Progress Checklist

#### BaseWorker Core Framework
- [ ] Implement BaseWorker class structure
  - [ ] State machine processing with job status-based routing
  - [ ] Database connection management with transaction support
  - [ ] External service client initialization and configuration
  - [ ] Graceful shutdown handling and cleanup
- [ ] Create job polling mechanism
  - [ ] Efficient SQL query with FOR UPDATE SKIP LOCKED
  - [ ] Status-based filtering for eligible jobs
  - [ ] Retry scheduling with exponential backoff timing
  - [ ] Worker ID generation and job claiming
- [ ] Add comprehensive error handling
  - [ ] Error classification (transient, permanent, retryable)
  - [ ] Retry scheduling with maximum retry limits
  - [ ] Dead letter queue handling for permanent failures
  - [ ] Structured error logging with correlation IDs

#### Parse Validation Implementation
- [ ] Content validation and normalization
  - [ ] Load parsed content from Supabase Storage
  - [ ] Apply markdown normalization rules from CONTEXT.md
  - [ ] Compute SHA256 hash of normalized content
  - [ ] Validate content integrity and format
- [ ] Duplicate detection and handling
  - [ ] Check for existing documents with same parsed_sha256
  - [ ] Reuse canonical parsed_path for duplicates
  - [ ] Update job with canonical reference
  - [ ] Log deduplication events for audit trail
- [ ] Atomic status transition
  - [ ] Update upload_jobs.parsed_sha256 and status
  - [ ] Ensure transaction consistency
  - [ ] Log successful validation completion
  - [ ] Handle concurrent validation attempts

#### Chunking Stage Processing
- [ ] Deterministic chunk generation
  - [ ] Load parsed content and apply chunker configuration
  - [ ] Generate UUIDv5 chunk IDs with canonical strings
  - [ ] Compute SHA256 hashes for chunk content integrity
  - [ ] Create chunk metadata (page, section, headings, offsets)
- [ ] Buffer persistence operations
  - [ ] Write chunks to document_chunk_buffer with idempotent upserts
  - [ ] Handle ON CONFLICT DO NOTHING for deterministic operations
  - [ ] Validate chunk count matches expected based on content size
  - [ ] Update job progress counters atomically
- [ ] Status management
  - [ ] Transition from parse_validated to chunking during processing
  - [ ] Update to chunks_stored after successful buffer writes
  - [ ] Log chunk generation metrics and timing
  - [ ] Handle chunking errors and retry scenarios

#### Micro-Batch Embedding Implementation
- [ ] OpenAI client integration
  - [ ] Async HTTP client with proper authentication
  - [ ] Rate limiting with token bucket algorithm
  - [ ] Request batching up to 256 vectors per call
  - [ ] Error handling for rate limits and API failures
- [ ] Micro-batch processing
  - [ ] Query pending chunks from document_chunk_buffer
  - [ ] Calculate optimal batch size based on constraints
  - [ ] Generate embeddings with OpenAI text-embedding-3-small
  - [ ] Immediate persistence to document_vector_buffer per batch
- [ ] Progress tracking and status updates
  - [ ] Update job status to embedding_queued before starting
  - [ ] Transition to embedding_in_progress during processing
  - [ ] Update progress counters atomically per batch
  - [ ] Complete with embeddings_stored status
- [ ] Vector buffer management
  - [ ] Write vectors with idempotent UPSERT operations
  - [ ] Include batch_id for operational tracking
  - [ ] Compute vector_sha for data integrity verification
  - [ ] Handle partial completion and resume scenarios

#### External Service Management
- [ ] Rate limiting implementation
  - [ ] Token bucket rate limiter for OpenAI API
  - [ ] Respect rate limits: requests per minute and tokens per minute
  - [ ] Adaptive batch sizing based on rate limit status
  - [ ] Queue management during rate limit delays
- [ ] Circuit breaker patterns
  - [ ] Monitor external service success rates
  - [ ] Fail-fast during service outages
  - [ ] Automatic recovery when services restore
  - [ ] Fallback strategies for partial degradation
- [ ] Retry logic and backoff
  - [ ] Exponential backoff for transient failures
  - [ ] Maximum retry limits per job
  - [ ] Permanent failure detection and handling
  - [ ] Cost tracking for retry operations
- [ ] Service monitoring and alerting
  - [ ] Track external API response times and success rates
  - [ ] Monitor cost per document and batch efficiency
  - [ ] Alert on service degradation or quota issues
  - [ ] Log service interactions for debugging

#### Finalization and Cleanup
- [ ] Job completion handling
  - [ ] Transition from embeddings_stored to complete
  - [ ] Validate all processing stages completed successfully
  - [ ] Log final processing metrics and costs
  - [ ] Trigger optional buffer cleanup processes
- [ ] Buffer management
  - [ ] Optional promotion to production tables
  - [ ] Buffer cleanup after successful completion
  - [ ] Archival of processing artifacts for audit
  - [ ] Monitoring of buffer table growth and cleanup efficiency

#### Testing & Validation
- [ ] Unit testing for BaseWorker
  - [ ] State machine transitions and error handling
  - [ ] Deterministic operations and idempotency
  - [ ] External service integration mocking
  - [ ] Buffer operations and progress tracking
- [ ] Integration testing
  - [ ] End-to-end processing pipeline
  - [ ] External service integration with real APIs
  - [ ] Database transaction handling and rollbacks
  - [ ] Concurrent processing and worker coordination
- [ ] Performance testing
  - [ ] Large document processing within memory limits
  - [ ] Micro-batch efficiency and throughput
  - [ ] Database performance under concurrent workers
  - [ ] External API cost optimization

#### Documentation
- [ ] Save `@TODO002_phase3_notes.md` with BaseWorker implementation details
- [ ] Save `@TODO002_phase3_decisions.md` with processing patterns
- [ ] Save `@TODO002_phase3_handoff.md` with integration test requirements
- [ ] Save `@TODO002_phase3_testing_summary.md` with performance results

---

## Phase 4: Integration Testing & Migration

### Prerequisites
- Files/documents to read:
  - `@TODO002_phase3_notes.md`
  - `@TODO002_phase3_decisions.md` 
  - `@TODO002_phase3_handoff.md`
  - All previous phase outputs and documentation
- Previous phase outputs: Complete BaseWorker implementation, webhook system, buffer architecture
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session for Phase 4. Use previous phase outputs as context.

You are implementing comprehensive integration testing and migration from the 001 specialized worker architecture to the 002 BaseWorker system. This phase focuses on validation, performance testing, and safe migration procedures.

### Tasks

#### T4.1: End-to-End Integration Testing
- Validate complete pipeline from upload through final embedding storage
- Test all error scenarios and recovery mechanisms
- Verify idempotency and deterministic processing
- Validate webhook security and external service integration

#### T4.2: Performance Validation & Optimization
- Conduct load testing with concurrent processing scenarios
- Validate micro-batch efficiency and external API cost optimization
- Test database performance under buffer write loads
- Verify horizontal scaling capabilities

#### T4.3: Migration Strategy Implementation
- Create migration procedures from 001 to 002 architecture
- Implement parallel operation for validation
- Develop rollback procedures and safety measures
- Update deployment configurations and monitoring

#### T4.4: Production Readiness Validation
- Validate security controls and compliance requirements
- Test monitoring, alerting, and operational procedures
- Verify backup and disaster recovery capabilities
- Complete stakeholder acceptance criteria validation

### Expected Outputs
- Save implementation notes to: `@TODO002_phase4_notes.md`
- Document migration outcomes in: `@TODO002_phase4_decisions.md`
- Create deployment guide in: `@TODO002_phase4_handoff.md`
- Create final testing summary in: `@TODO002_phase4_testing_summary.md`

### Progress Checklist

#### End-to-End Integration Testing
- [ ] Complete pipeline validation
  - [ ] Upload through LlamaParse webhook to final embedding storage
  - [ ] Validate all status transitions and buffer writes
  - [ ] Test various document sizes and complexities
  - [ ] Verify processing times meet SLA requirements
- [ ] Error scenario testing
  - [ ] External service outages (LlamaParse, OpenAI)
  - [ ] Database connectivity failures
  - [ ] Worker process crashes and restarts
  - [ ] Webhook security failures and invalid payloads
- [ ] Idempotency validation
  - [ ] Reprocess same document multiple times
  - [ ] Verify no duplicate chunks or embeddings created
  - [ ] Test resume capability from any stage
  - [ ] Validate deterministic UUID generation consistency
- [ ] Security testing
  - [ ] Webhook HMAC signature validation
  - [ ] Replay attack prevention
  - [ ] Input validation and injection prevention
  - [ ] Access control and authorization verification

#### Performance Testing & Optimization
- [ ] Load testing scenarios
  - [ ] Concurrent document processing (multiple BaseWorkers)
  - [ ] Large document processing within memory constraints
  - [ ] Database performance under heavy buffer writes
  - [ ] External API rate limiting and backoff behavior
- [ ] Micro-batch efficiency validation
  - [ ] Optimal batch size calculation
  - [ ] Cost per document tracking and optimization
  - [ ] Processing throughput measurement
  - [ ] Memory usage profiling and optimization
- [ ] Scalability testing
  - [ ] Horizontal worker scaling validation
  - [ ] Database connection pooling efficiency
  - [ ] Queue depth management under load
  - [ ] Buffer cleanup performance

#### Migration Implementation
- [ ] Migration procedures
  - [ ] Data migration from 001 schema to 002 buffer tables
  - [ ] Job status mapping and conversion
  - [ ] Worker deployment and configuration updates
  - [ ] API endpoint migration and testing
- [ ] Parallel operation validation
  - [ ] Run both 001 and 002 systems simultaneously
  - [ ] Compare processing results and performance
  - [ ] Validate data consistency between systems
  - [ ] Test gradual traffic migration
- [ ] Rollback procedures
  - [ ] Complete system state backup before migration
  - [ ] Rollback scripts for schema and deployment changes
  - [ ] Data recovery procedures
  - [ ] Service restoration validation

#### Production Readiness
- [ ] Security compliance validation
  - [ ] HIPAA compliance requirements verification
  - [ ] Data encryption in transit and at rest
  - [ ] Access logging and audit trail completeness
  - [ ] Security monitoring and alerting setup
- [ ] Operational procedures
  - [ ] Monitoring dashboard configuration
  - [ ] Alert threshold setup and escalation procedures
  - [ ] Backup and disaster recovery testing
  - [ ] Incident response runbook creation
- [ ] Performance benchmarking
  - [ ] Baseline performance metrics establishment
  - [ ] SLA compliance validation (>98% success rate)
  - [ ] Cost efficiency measurement and optimization
  - [ ] Resource utilization optimization

#### Stakeholder Acceptance
- [ ] Acceptance criteria validation
  - [ ] All PRD requirements met and tested
  - [ ] Performance improvements demonstrated
  - [ ] Reliability improvements measured
  - [ ] Operational complexity reduction achieved
- [ ] Documentation completion
  - [ ] Operational runbooks and procedures
  - [ ] Developer documentation and API guides
  - [ ] Architecture decision records
  - [ ] Migration and deployment guides
- [ ] Training and knowledge transfer
  - [ ] Operations team training on new architecture
  - [ ] Development team knowledge transfer
  - [ ] Incident response procedure training
  - [ ] Monitoring and alerting training

#### Final System Validation
- [ ] Complete system integration testing
  - [ ] All components working together correctly
  - [ ] No regressions from 001 functionality
  - [ ] Performance improvements validated
  - [ ] Security enhancements verified
- [ ] Production deployment readiness
  - [ ] Infrastructure configured and tested
  - [ ] Monitoring and alerting operational
  - [ ] Backup and recovery procedures validated
  - [ ] Rollback procedures tested and documented

#### Documentation
- [ ] Save `@TODO002_phase4_notes.md` with integration testing results
- [ ] Save `@TODO002_phase4_decisions.md` with migration outcomes
- [ ] Save `@TODO002_phase4_handoff.md` with deployment procedures
- [ ] Save `@TODO002_phase4_testing_summary.md` with final validation results

---

## Project Completion Checklist

### Phase 1: Infrastructure & Buffer Tables
- [ ] Enhanced database schema with buffer tables deployed
- [ ] Directory restructuring completed with proper separation
- [ ] Shared utilities implemented and tested
- [ ] Deterministic operations validated
- [ ] Phase 1 documentation complete

### Phase 2: Webhook Implementation & API Updates
- [ ] Secure webhook endpoint deployed with HMAC verification
- [ ] LlamaParse integration with callback support
- [ ] Enhanced job status API with buffer-based progress
- [ ] Security monitoring and validation complete
- [ ] Phase 2 documentation complete

### Phase 3: BaseWorker Implementation
- [ ] Unified BaseWorker class with state machine processing
- [ ] All processing stages implemented with buffer persistence
- [ ] Micro-batch embedding with rate limiting
- [ ] External service integration with retry logic
- [ ] Phase 3 documentation complete

### Phase 4: Integration Testing & Migration
- [ ] End-to-end integration testing completed
- [ ] Performance validation and optimization
- [ ] Migration from 001 architecture successful
- [ ] Production readiness validation complete
- [ ] Phase 4 documentation complete

### Project Success Criteria
- [ ] >98% processing pipeline reliability achieved
- [ ] Recovery time from failures <5 minutes validated
- [ ] Processing predictability <10% variance measured
- [ ] 50% reduction in operational complexity achieved
- [ ] All stakeholder acceptance criteria met
- [ ] Complete migration from 001 architecture
- [ ] Production deployment ready with monitoring

### Key Metrics Achieved
- [ ] Processing pipeline reliability: >98%
- [ ] Worker scaling efficiency: Linear throughput increase
- [ ] Buffer storage efficiency: <20% overhead
- [ ] External service integration: >99% success with retries
- [ ] Development velocity: 30% improvement in feature implementation

---

## Implementation Notes

**Architecture Strategy:**
This TODO is designed for execution across 4 phases with each building on documented outputs from previous phases. The BaseWorker architecture prioritizes simplicity, reliability, and future extensibility.

**Session Management:**
- Always run `/clear` before starting a new phase
- Each phase includes complete context for fresh Claude sessions
- Save all specified output files for continuity between phases
- Reference previous phase outputs using `@filename.md` syntax

**Quality Assurance:**
- Each phase includes comprehensive testing requirements
- Buffer-driven persistence ensures idempotency and crash recovery
- Detailed documentation maintains project continuity
- Final validation confirms all success criteria are met

**Migration Safety:**
- Parallel operation validation before full migration
- Comprehensive rollback procedures and testing
- Data integrity validation at each step
- Incremental migration with validation checkpoints

**Future Extensibility:**
The BaseWorker architecture is designed to facilitate:
- Migration to managed cloud platforms (Kubernetes, AWS ECS, Google Cloud Run)
- Integration with external queue services (SQS, Pub/Sub)
- Multi-model embedding support and A/B testing
- Advanced processing stages and workflow orchestration