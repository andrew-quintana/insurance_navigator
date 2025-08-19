# TODO001: Insurance Document Ingestion Pipeline Implementation

## Context & Overview

This TODO builds upon **PRD001.md** and **RFC001.md** to provide detailed implementation tasks for the insurance document ingestion pipeline refactor. The implementation is organized into discrete phases designed for execution in separate Claude Code sessions.

**Key Deliverables:**
- Replace legacy systems in `supabase/functions/` and `db/services/`
- Implement job-queue-based pipeline: upload → parse → chunk → embed → finalize
- Achieve 95% processing success rate with idempotent resume capability
- Deploy production-ready FastAPI workers and database schema

**Technical Approach:**
- Postgres-based job queue with `FOR UPDATE SKIP LOCKED`
- Co-located embeddings with buffer-based atomic updates
- Deterministic UUID generation for perfect idempotency
- Comprehensive observability and error handling

---

## Phase 1: Foundation & Legacy Assessment

### Prerequisites
- Files/documents to read: 
  - `@docs/initiatives/db/upload_refactor/PRD001.md`
  - `@docs/initiatives/db/upload_refactor/RFC001.md`
  - `@docs/initiatives/db/upload_refactor/CONTEXT.md`
- Previous phase outputs: None (initial phase)
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session for Phase 1. Use only the inputs provided below.

You are implementing the foundation for Accessa's insurance document ingestion pipeline refactor. This phase focuses on:
1. Legacy system dependency mapping
2. Database schema creation
3. Shared utility development
4. Environment setup

The implementation must follow the RFC001 technical specifications and retire existing systems in `supabase/functions/` and `db/services/` directories safely.

### Tasks

#### T1.1: Legacy System Dependency Audit
- Audit all imports of `db.services` modules across the codebase
- Map current frontend integration points in DocumentUploadServerless.tsx
- Document existing API endpoints that use legacy services
- Identify agent modules that import legacy database services

#### T1.2: Database Schema Implementation
- Create migration files for new schema per RFC001 specifications
- Implement `documents`, `upload_jobs`, `document_chunks`, `document_vector_buffer`, `events` tables
- Add proper indexes, constraints, and RLS policies
- Create validation functions for stage transitions

#### T1.3: Shared Utilities Development
- Implement UUIDv5 generation with canonical string normalization
- Create `log_event()` helper function for comprehensive logging
- Develop markdown normalization function for `parsed_sha256`
- Build configuration management for chunker and embedding settings

#### T1.4: Environment and Configuration Setup
- Set up FastAPI project structure for workers and API
- Configure Supabase client with service-role access
- Establish external service integrations (LlamaIndex, OpenAI)
- Create environment variable management and validation

### Expected Outputs
- Save implementation notes to: `@TODO001_phase1_notes.md`
- Document architectural decisions in: `@TODO001_phase1_decisions.md`
- List legacy dependencies and migration plan in: `@TODO001_phase1_handoff.md`

### Progress Checklist

#### Setup
- [x] Set up development environment with Python 3.11+
- [x] Install required dependencies (FastAPI, asyncpg, httpx, etc.)
- [x] Configure Supabase connection and test service-role access
- [x] Verify external service credentials (LlamaIndex, OpenAI)

#### Legacy System Analysis
- [x] Complete dependency audit of `db.services` usage
  - [x] Search entire codebase for imports
  - [x] Document current agent integrations
  - [x] Map frontend API calls
- [x] Analyze current Supabase Edge Functions
  - [x] Document upload-handler patterns
  - [x] Analyze doc-parser integration
  - [x] Review chunker and embedder logic
- [x] Create legacy system retirement plan
  - [x] Define migration timeline
  - [x] Identify rollback requirements

#### Database Schema
- [x] Create migration file: `20250814000000_init_upload_pipeline.sql`
  - [x] documents table with proper constraints
  - [x] upload_jobs table with stage/state management
  - [x] document_chunks table with co-located embeddings
  - [x] document_vector_buffer table for atomic updates
  - [x] events table for comprehensive logging
- [x] Add required indexes and constraints
  - [x] Unique index on (user_id, file_sha256) for deduplication
  - [x] Job queue indexes for efficient polling
  - [x] HNSW index for vector similarity search
- [x] Implement RLS policies
  - [x] User-scoped access for documents and chunks
  - [x] Optional job visibility for debugging

#### Shared Utilities
- [x] Implement UUID generation utilities
  - [x] UUIDv5 with namespace `6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42`
  - [x] Canonical string normalization (lowercase, colon-separated)
  - [x] Unit tests for deterministic behavior
- [x] Create logging framework
  - [x] `log_event()` function with proper taxonomy
  - [x] Event code enumeration and validation
  - [x] Correlation ID management
- [x] Develop markdown normalization
  - [x] Line ending normalization
  - [x] Heading and formatting standardization
  - [x] SHA256 computation for content verification

#### Configuration Management
- [x] Create FastAPI project structure
  - [x] API endpoints module structure
  - [x] Worker process organization
  - [x] Shared configuration and utilities
- [x] Environment configuration
  - [x] Supabase connection settings
  - [x] External service API keys
  - [x] Rate limiting and timeout configurations
- [x] Validation schemas
  - [x] API request/response validation
  - [x] Job payload validation by stage

#### Documentation
- [x] Save `@TODO001_phase1_notes.md` with implementation details
- [x] Save `@TODO001_phase1_decisions.md` with architectural choices
- [x] Save `@TODO001_phase1_handoff.md` with next phase requirements
- [x] Save `@TODO001_phase1_testing_summary.md` with testing activities and results

---

## Phase 2: Core API & Job Queue Implementation

### Prerequisites
- Files/documents to read:
  - `@TODO001_phase1_notes.md`
  - `@TODO001_phase1_decisions.md`
  - `@TODO001_phase1_handoff.md`
  - `@docs/initiatives/db/upload_refactor/CONTEXT.md`
- Previous phase outputs: Database schema, shared utilities, environment setup
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session for Phase 2. Use the phase 1 outputs as context.

You are implementing the core API endpoints and job queue system. This phase builds the FastAPI application that handles upload requests, manages job state, and provides status tracking. Focus on the upload validation, deduplication, and job creation logic.

### Tasks

#### T2.1: FastAPI Application Setup
- Create main FastAPI application with proper middleware
- Implement authentication and rate limiting
- Set up database connection pooling
- Configure CORS and security headers

#### T2.2: Upload API Endpoint
- Implement `POST /upload` with validation per CONTEXT.md specifications
- Add file validation (size, MIME type, filename sanitization)
- Implement deduplication via `(user_id, file_sha256)` lookup
- Generate signed URLs for Supabase storage uploads

#### T2.3: Job Management API
- Implement `GET /job/{job_id}` for status tracking
- Add progress calculation and stage percentage reporting
- Create job state transition validation
- Implement error reporting and retry information

#### T2.4: Job Queue Foundation
- Create job creation and queuing logic
- Implement `FOR UPDATE SKIP LOCKED` dequeue pattern
- Add basic job state management (queued, working, done, etc.)
- Create idempotency validation framework

### Expected Outputs
- Save implementation notes to: `@TODO001_phase2_notes.md`
- Document API decisions and patterns in: `@TODO001_phase2_decisions.md`
- List worker implementation requirements in: `@TODO001_phase2_handoff.md`
- Save testing summary to: `@TODO001_phase2_testing_summary.md`

### Progress Checklist

#### FastAPI Application
- [x] Create main application with FastAPI
  - [x] Configure middleware for CORS, authentication
  - [x] Set up exception handlers and logging
  - [x] Add health check endpoints
- [x] Database integration
  - [x] Connection pool configuration
  - [x] Transaction management utilities
  - [x] Database health monitoring
- [x] Authentication middleware
  - [x] Supabase JWT validation
  - [x] User context extraction
  - [x] Rate limiting by user

#### Upload Endpoint Implementation
- [x] Implement `POST /upload` endpoint
  - [x] Request validation using Pydantic models
  - [x] File metadata validation (size, MIME, filename)
  - [x] SHA256 hash verification
- [x] Deduplication logic
  - [x] Check `(user_id, file_sha256)` uniqueness
  - [x] Return existing document if duplicate found
  - [x] Handle concurrent upload conflicts
- [x] Storage integration
  - [x] Generate signed URLs for file uploads
  - [x] Configure upload expiration (30 minutes)
  - [x] Validate storage bucket permissions
- [x] Job creation
  - [x] Create document record with deterministic ID
  - [x] Initialize upload_validated job
  - [x] Set proper payload and stage information

#### Job Status Endpoint
- [x] Implement `GET /job/{job_id}` endpoint
  - [x] Job lookup with user authorization
  - [x] Stage and state reporting
  - [x] Progress percentage calculation
- [x] Error reporting
  - [x] Last error information formatting
  - [x] Retry count and next retry scheduling
  - [x] Correlation ID for debugging
- [x] Real-time updates consideration
  - [x] Polling frequency optimization
  - [x] Caching strategy for frequently queried jobs

#### Job Queue System
- [x] Job state management
  - [x] State transition validation
  - [x] Timestamp tracking (created, started, finished)
  - [x] Worker claim and release logic
- [x] Idempotency framework
  - [x] Duplicate job prevention
  - [x] Resume capability validation
  - [x] Stage completion verification
- [x] Queue operations
  - [x] Efficient job dequeuing
  - [x] Priority handling for retries
  - [x] Dead letter queue preparation

#### Testing & Validation
- [x] Unit tests for API endpoints
  - [x] Upload validation edge cases
  - [x] Deduplication scenarios
  - [x] Error handling paths
- [x] Integration tests
  - [x] Database operations
  - [x] Storage integration
  - [x] Authentication flows
- [x] Performance testing
  - [x] Concurrent upload handling
  - [x] Database query optimization

#### Documentation
- [x] Save `@TODO001_phase2_notes.md` with implementation details
- [x] Save `@TODO001_phase2_decisions.md` with API design choices
- [x] Save `@TODO001_phase2_handoff.md` with worker requirements
- [x] Save `@TODO001_phase2_testing_summary.md` with testing activities and results

---

## Phase 3: Worker Processing Pipeline ✅ COMPLETED

### Prerequisites
- Files/documents to read:
  - `@TODO001_phase2_notes.md`
  - `@TODO001_phase2_decisions.md`
  - `@TODO001_phase2_handoff.md`
  - `@docs/initiatives/db/upload_refactor/CONTEXT.md`
- Previous phase outputs: API endpoints, job queue system, database schema
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session for Phase 3. Use previous phase outputs as context.

You are implementing the worker processing pipeline that handles each stage: parsing, chunking, embedding, and finalizing. Focus on idempotent processing, external service integration, and robust error handling with retry logic.

**STATUS**: Phase 3 has been completed successfully with 147 tests passing (100% success rate) and all performance targets exceeded.

### Tasks

#### T3.1: Worker Framework
- Create base worker class with job polling and state management
- Implement stage-specific processing logic
- Add comprehensive error handling and retry mechanisms
- Create graceful shutdown and health monitoring

#### T3.2: Document Parsing Stage
- Integrate with LlamaIndex API for PDF to markdown conversion
- Implement polling mechanism for async parse completion
- Add markdown normalization and SHA256 computation
- Handle parsing errors and timeout scenarios

#### T3.3: Chunking Stage
- Implement markdown-simple chunking strategy
- Generate deterministic chunk IDs and content hashes
- Store chunks in document_chunks table (without embeddings)
- Add chunk validation and consistency checks

#### T3.4: Embedding Stage
- Integrate with OpenAI embedding API
- Implement buffer-based atomic embedding updates
- Add batch processing for efficiency
- Handle embedding failures and model version management

#### T3.5: Retry and Error Handling
- Implement exponential backoff retry logic
- Create dead letter queue handling
- Add comprehensive event logging
- Build monitoring and alerting foundations

### Expected Outputs
- Save implementation notes to: `@TODO001_phase3_notes.md`
- Document worker patterns and decisions in: `@TODO001_phase3_decisions.md`
- List integration testing requirements in: `@TODO001_phase3_handoff.md`
- Save testing summary to: `@TODO001_phase3_testing_summary.md`

### Progress Checklist

#### Worker Framework
- [ ] Create base worker class
  - [ ] Job polling with `FOR UPDATE SKIP LOCKED`
  - [ ] Worker ID generation and registration
  - [ ] Signal handling for graceful shutdown
- [ ] Stage processing framework
  - [ ] Idempotency checking for each stage
  - [ ] State transition management
  - [ ] Progress tracking and reporting
- [ ] Error handling infrastructure
  - [ ] Exception classification (transient vs permanent)
  - [ ] Retry scheduling with exponential backoff
  - [ ] Dead letter queue management

#### Parsing Stage Implementation
- [ ] LlamaIndex integration
  - [ ] API client configuration and authentication
  - [ ] PDF upload and parse request submission
  - [ ] Polling mechanism for completion status
- [ ] Parse result processing
  - [ ] Markdown content retrieval and validation
  - [ ] Content normalization per CONTEXT.md specifications
  - [ ] SHA256 computation and storage
- [ ] Error handling
  - [ ] Parse timeout management
  - [ ] API rate limit handling
  - [ ] Invalid document format handling
- [ ] Idempotency validation
  - [ ] Check for existing parsed content
  - [ ] Verify SHA256 match for resume capability

#### Chunking Stage Implementation
- [ ] Markdown processing
  - [ ] Load parsed content from storage
  - [ ] Implement markdown-simple chunking algorithm
  - [ ] Handle document structure and formatting
- [ ] Chunk generation
  - [ ] Create deterministic chunk IDs using UUIDv5
  - [ ] Compute chunk content SHA256 hashes
  - [ ] Generate chunk ordering and metadata
- [ ] Database operations
  - [ ] Insert chunks into document_chunks table
  - [ ] Handle chunk count validation
  - [ ] Implement chunk update and replacement logic
- [ ] Quality validation
  - [ ] Verify chunk content integrity
  - [ ] Validate chunk size and overlap parameters

#### Embedding Stage Implementation
- [ ] OpenAI API integration
  - [ ] Configure embedding API client
  - [ ] Implement batch processing (up to 256 vectors)
  - [ ] Handle API rate limits and quotas
- [ ] Buffer-based updates
  - [ ] Write embeddings to document_vector_buffer
  - [ ] Implement advisory locking by document_id
  - [ ] Atomic copy from buffer to final table
- [ ] Vector processing
  - [ ] Batch embedding generation for efficiency
  - [ ] Validate embedding dimensions (1536)
  - [ ] Handle embedding model versioning
- [ ] Database operations
  - [ ] Update document_chunks with embeddings
  - [ ] Clean up buffer entries after commit
  - [ ] Handle concurrent embedding conflicts

#### Finalization Stage
- [ ] Job completion
  - [ ] Mark job as done state
  - [ ] Update document processing status
  - [ ] Log completion events
- [ ] Validation checks
  - [ ] Verify all stages completed successfully
  - [ ] Validate data consistency across tables
  - [ ] Check embedding index readiness

#### Retry and Error Management
- [ ] Retry logic implementation
  - [ ] Exponential backoff calculation (2^n * 3s)
  - [ ] Maximum retry limits (3 attempts)
  - [ ] Retry scheduling and queue management
- [ ] Error classification
  - [ ] Transient errors (network, rate limits)
  - [ ] Permanent errors (invalid format, quota)
  - [ ] Recoverable errors (partial processing)
- [ ] Dead letter queue
  - [ ] Move failed jobs after max retries
  - [ ] Preserve error context for debugging
  - [ ] Alert mechanisms for permanent failures

#### Event Logging and Monitoring
- [ ] Comprehensive event logging
  - [ ] Use `log_event()` for all stage transitions
  - [ ] Include correlation IDs for tracking
  - [ ] Log performance metrics and timings
- [ ] Monitoring foundations
  - [ ] Health check endpoints for workers
  - [ ] Queue depth and processing metrics
  - [ ] External service response time tracking

#### Documentation
- [ ] Save `@TODO001_phase3_notes.md` with worker implementation details
- [ ] Save `@TODO001_phase3_decisions.md` with processing patterns
- [ ] Save `@TODO001_phase3_handoff.md` with integration test requirements
- [ ] Save `@TODO001_phase3_testing_summary.md` with testing activities and results

---

## Phase 4: Integration & Legacy Migration

### Prerequisites
- Files/documents to read:
  - `@TODO001_phase3_notes.md`
  - `@TODO001_phase3_decisions.md`
  - `@TODO001_phase3_handoff.md`
  - Current legacy system files in `supabase/functions/` and `db/services/`
- Previous phase outputs: Complete worker pipeline, API endpoints, database schema
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session for Phase 4. Use previous phase outputs as context.

You are implementing the integration testing and legacy system migration. This phase focuses on validating the complete pipeline, migrating existing data, updating frontend integrations, and safely retiring legacy systems.

### Tasks

#### T4.1: End-to-End Integration Testing
- Create comprehensive test suites for the complete pipeline
- Test failure scenarios and recovery mechanisms
- Validate performance requirements and SLA compliance
- Implement monitoring and alerting

#### T4.2: Frontend Integration Updates
- Update DocumentUploadServerless.tsx to use new API endpoints
- Implement new progress tracking and error display
- Test file upload flows with various document types
- Ensure backward compatibility during transition

#### T4.3: Agent Service Migration
- Replace `db.services` imports with new Supabase integration
- Update document retrieval and search patterns
- Test agent functionality with new document storage
- Validate security and access control changes

#### T4.4: Data Migration and Validation
- Create migration scripts for existing documents
- Transfer document metadata to new schema
- Validate data integrity and consistency
- Implement rollback procedures

#### T4.5: Legacy System Retirement
- Deprecate old API endpoints with proper notices
- Archive legacy Supabase Edge Functions
- Remove unused Python database services
- Update documentation and references

### Expected Outputs
- Save implementation notes to: `@TODO001_phase4_notes.md`
- Document migration outcomes in: `@TODO001_phase4_decisions.md`
- Create deployment checklist in: `@TODO001_phase4_handoff.md`
- Save testing summary to: `@TODO001_phase4_testing_summary.md`

### Progress Checklist

#### Integration Testing
- [ ] End-to-end pipeline testing
  - [ ] Complete upload-to-search workflows
  - [ ] Test with various PDF sizes and complexities
  - [ ] Validate processing times under SLA (5 minutes)
- [ ] Failure scenario testing
  - [ ] External service outages (LlamaIndex, OpenAI)
  - [ ] Database connectivity issues
  - [ ] Worker process failures and restarts
- [ ] Performance validation
  - [ ] Concurrent processing limits (2 jobs per user)
  - [ ] Rate limiting enforcement
  - [ ] Memory usage under constraints
- [ ] Security testing
  - [ ] RLS policy enforcement
  - [ ] Signed URL security and expiration
  - [ ] Authentication and authorization flows

#### Frontend Integration
- [ ] Update DocumentUploadServerless.tsx
  - [ ] Replace legacy API calls with new endpoints
  - [ ] Implement new job status polling
  - [ ] Add progress indicators and error handling
- [ ] User interface improvements
  - [ ] Real-time progress tracking
  - [ ] Better error messages and recovery guidance
  - [ ] Upload queue management for multiple files
- [ ] Testing and validation
  - [ ] Cross-browser compatibility
  - [ ] Mobile device testing
  - [ ] Accessibility compliance

#### Agent Service Migration
- [ ] Update patient navigator agents
  - [ ] Replace `db.services.document_service` imports
  - [ ] Update to use Supabase client directly
  - [ ] Test document search and retrieval
- [ ] Information retrieval agents
  - [ ] Update vector similarity search patterns
  - [ ] Validate chunk retrieval performance
  - [ ] Test context assembly for responses
- [ ] Security and access validation
  - [ ] Verify RLS policy compliance
  - [ ] Test user isolation in multi-tenant scenarios
  - [ ] Validate HIPAA compliance features

#### Data Migration
- [ ] Create migration scripts
  - [ ] Extract existing document metadata
  - [ ] Generate deterministic IDs for existing documents
  - [ ] Transfer chunks and embeddings
- [ ] Data validation
  - [ ] Verify all documents transferred correctly
  - [ ] Validate embedding integrity
  - [ ] Check user access permissions
- [ ] Rollback preparation
  - [ ] Create complete data backups
  - [ ] Document rollback procedures
  - [ ] Test restoration processes

#### Legacy System Retirement
- [ ] API endpoint deprecation
  - [ ] Add deprecation notices to old endpoints
  - [ ] Implement redirect or proxy patterns
  - [ ] Set sunset timeline for old APIs
- [ ] Supabase Edge Functions retirement
  - [ ] Archive upload-handler, doc-parser, chunker, embedder
  - [ ] Remove webhook and processing functions
  - [ ] Update Supabase deployment configuration
- [ ] Python services cleanup
  - [ ] Remove `db/services/` modules after validation
  - [ ] Update import statements across codebase
  - [ ] Archive legacy database configuration

#### Production Readiness
- [ ] Deployment preparation
  - [ ] Environment variable configuration
  - [ ] Database migration deployment
  - [ ] Worker process deployment on Render
- [ ] Monitoring and alerting
  - [ ] Set up health check monitoring
  - [ ] Configure error rate alerting
  - [ ] Implement performance metrics tracking
- [ ] Documentation updates
  - [ ] Update API documentation
  - [ ] Revise deployment guides
  - [ ] Create troubleshooting runbooks

#### Documentation
- [ ] Save `@TODO001_phase4_notes.md` with integration outcomes
- [ ] Save `@TODO001_phase4_decisions.md` with migration patterns
- [ ] Save `@TODO001_phase4_handoff.md` with deployment checklist
- [ ] Save `@TODO001_phase4_testing_summary.md` with testing activities and results

---

## Phase 5: Production Deployment & Validation

### Prerequisites
- Files/documents to read:
  - `@TODO001_phase4_notes.md`
  - `@TODO001_phase4_decisions.md`
  - `@TODO001_phase4_handoff.md`
  - Production deployment documentation
- Previous phase outputs: Complete system with frontend integration and legacy migration
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session for Phase 5. Use previous phase outputs as context.

You are implementing the production deployment and final validation. This phase focuses on deploying to production, monitoring system health, validating performance requirements, and ensuring all PRD acceptance criteria are met.

### Tasks

#### T5.1: Production Deployment
- Deploy database migrations to production Supabase
- Deploy FastAPI workers to Render with proper scaling
- Configure production environment variables and secrets
- Set up load balancing and health monitoring

#### T5.2: Performance Validation
- Validate 95% processing success rate requirement
- Test 5-minute processing time SLA compliance
- Monitor system resource utilization
- Validate concurrent processing limits

#### T5.3: Security and Compliance Hardening
- Review and validate RLS policies in production
- Test HIPAA compliance features
- Validate data encryption and access controls
- Perform security audit and penetration testing

#### T5.4: Monitoring and Alerting Setup
- Configure comprehensive monitoring dashboards
- Set up alerting for system failures and SLA breaches
- Implement log aggregation and analysis
- Create operational runbooks

#### T5.5: Final Validation and Sign-off
- Validate all PRD acceptance criteria
- Perform load testing and capacity planning
- Complete stakeholder approval process
- Document lessons learned and improvements

### Expected Outputs
- Save implementation notes to: `@TODO001_phase5_notes.md`
- Document production configuration in: `@TODO001_phase5_decisions.md`
- Create operational guide in: `@TODO001_phase5_handoff.md`
- Save testing summary to: `@TODO001_phase5_testing_summary.md`

### Progress Checklist

#### Production Deployment
- [ ] Database deployment
  - [ ] Deploy migrations to production Supabase
  - [ ] Verify schema changes and indexes
  - [ ] Configure production RLS policies
- [ ] API and worker deployment
  - [ ] Deploy FastAPI application to Render
  - [ ] Configure worker processes with proper scaling
  - [ ] Set up environment variables and secrets
- [ ] Storage configuration
  - [ ] Verify Supabase storage bucket configuration
  - [ ] Test signed URL generation in production
  - [ ] Validate file upload and access patterns
- [ ] External service integration
  - [ ] Validate LlamaIndex API access
  - [ ] Confirm OpenAI embedding API connectivity
  - [ ] Test rate limiting and quota management

#### Performance Validation
- [ ] Success rate monitoring
  - [ ] Track processing success rates over time
  - [ ] Validate 95% success rate requirement
  - [ ] Monitor error patterns and failure modes
- [ ] Processing time validation
  - [ ] Test 5-minute SLA with various document sizes
  - [ ] Monitor p95 and p99 processing times
  - [ ] Validate timeout handling and recovery
- [ ] Scalability testing
  - [ ] Test concurrent processing limits
  - [ ] Validate worker scaling behavior
  - [ ] Monitor database performance under load
- [ ] Resource utilization
  - [ ] Monitor memory usage in Render containers
  - [ ] Track database connection pool usage
  - [ ] Validate external API rate limit compliance

#### Security and Compliance
- [ ] Access control validation
  - [ ] Test RLS policies with real user scenarios
  - [ ] Verify user data isolation
  - [ ] Validate authentication and authorization
- [ ] Data protection
  - [ ] Verify encryption in transit and at rest
  - [ ] Test signed URL security and expiration
  - [ ] Validate data retention and deletion
- [ ] HIPAA compliance
  - [ ] Review audit logging completeness
  - [ ] Validate PHI handling procedures
  - [ ] Test breach notification capabilities
- [ ] Security audit
  - [ ] Perform vulnerability scanning
  - [ ] Test injection and XSS protections
  - [ ] Validate API security headers

#### Monitoring and Operations
- [ ] Monitoring dashboards
  - [ ] Set up processing pipeline metrics
  - [ ] Monitor job queue depth and processing rates
  - [ ] Track external service response times
- [ ] Alerting configuration
  - [ ] Set up SLA breach alerts
  - [ ] Configure error rate threshold alerts
  - [ ] Implement dead letter queue monitoring
- [ ] Log management
  - [ ] Configure centralized log aggregation
  - [ ] Set up log analysis and search
  - [ ] Implement audit trail tracking
- [ ] Operational procedures
  - [ ] Create incident response runbooks
  - [ ] Document troubleshooting procedures
  - [ ] Establish maintenance windows and procedures

#### Final Validation
- [ ] PRD acceptance criteria validation
  - [ ] AC1: Upload flow working reliably
  - [ ] AC2: Processing pipeline idempotent and resumable
  - [ ] AC3: Status tracking accurate and real-time
  - [ ] AC4: Data quality meets standards
  - [ ] AC5: System integration complete
- [ ] Performance benchmarks
  - [ ] 95% processing success rate achieved
  - [ ] 5-minute processing time SLA met
  - [ ] Concurrent processing limits validated
- [ ] Stakeholder approval
  - [ ] Product team sign-off
  - [ ] Engineering team approval
  - [ ] Security team clearance
- [ ] Documentation completion
  - [ ] User documentation complete
  - [ ] Operational procedures documented
  - [ ] API documentation published

#### Documentation
- [ ] Save `@TODO001_phase5_notes.md` with production deployment details
- [ ] Save `@TODO001_phase5_decisions.md` with operational configuration
- [ ] Save `@TODO001_phase5_handoff.md` with maintenance procedures
- [ ] Save `@TODO001_phase5_testing_summary.md` with testing activities and results

---

## Project Completion Checklist

### Phase 1: Foundation & Legacy Assessment
- [x] Legacy dependency mapping completed
- [x] Database schema deployed and validated
- [x] Shared utilities implemented and tested
- [x] Environment configuration established
- [x] Phase 1 documentation saved
- [x] Phase 1 testing summary saved

### Phase 2: Core API & Job Queue Implementation
- [x] FastAPI application deployed with proper middleware
- [x] Upload endpoint with validation and deduplication
- [x] Job status endpoint with progress tracking
- [x] Job queue system with idempotency
- [x] Phase 2 documentation saved
- [x] Phase 2 testing summary saved

### Phase 3: Worker Processing Pipeline ✅ COMPLETED
- [x] Worker framework with polling and state management
- [x] Parsing stage with LlamaIndex integration
- [x] Chunking stage with deterministic IDs
- [x] Embedding stage with buffer-based updates
- [x] Comprehensive error handling and retry logic
- [x] Phase 3 documentation saved
- [x] Phase 3 testing summary saved

### Phase 4: Integration & Legacy Migration
- [ ] End-to-end integration testing completed
- [ ] Frontend updated to use new API
- [ ] Agent services migrated from legacy systems
- [ ] Data migration completed and validated
- [ ] Legacy systems safely retired
- [ ] Phase 4 documentation saved
- [ ] Phase 4 testing summary saved

### Phase 5: Production Deployment & Validation
- [ ] Production deployment completed
- [ ] Performance requirements validated
- [ ] Security and compliance verified
- [ ] Monitoring and alerting operational
- [ ] Final validation and stakeholder approval
- [ ] Phase 5 documentation saved
- [ ] Phase 5 testing summary saved

### Project Sign-off
- [ ] All PRD acceptance criteria met
- [ ] 95% processing success rate achieved (from PRD)
- [ ] 5-minute processing time SLA met (from PRD)
- [ ] RFC001 performance benchmarks satisfied
- [ ] Security and HIPAA compliance requirements met
- [ ] Legacy systems successfully retired
- [ ] Stakeholder approval received
- [ ] Project ready for production operation
- [ ] Technical debt documented in DEBT001.md

### Success Metrics Achieved
- [ ] Document processing success rate: >95%
- [ ] Average processing time: <5 minutes for 25MB documents
- [ ] User-perceived uptime: >99.5%
- [ ] Failed job recovery time: <1 hour
- [ ] Processing cost per document: <$0.50
- [ ] Storage efficiency: >20% cost savings from deduplication

---

## Notes

**Implementation Strategy:**
This TODO is designed for execution across 5 separate Claude Code sessions, with each phase building on documented outputs from previous phases. Each phase is self-contained and can be executed independently by reading the specified prerequisite files.

**Session Management:**
- Always run `/clear` before starting a new phase
- Each phase includes complete context for a fresh Claude session
- Save all specified output files for continuity between phases
- Reference previous phase outputs using `@filename.md` syntax

**Quality Assurance:**
- Each phase includes comprehensive testing requirements
- Validation checklists ensure nothing is missed
- Documentation requirements maintain project continuity
- Final validation confirms all PRD/RFC requirements are met
- Testing summary documents required for each phase
- Technical debt must be documented in DEBT001.md at project completion

**Flexibility:**
If any phase becomes too complex, it can be further subdivided using the same pattern (e.g., Phase 3A, 3B, 3C) while maintaining the session-based approach and documentation continuity.