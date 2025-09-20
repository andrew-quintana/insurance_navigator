# Phase 1 Architectural Decisions: Upload Pipeline Refactor

## Overview
This document captures the key architectural decisions made during Phase 1 of the Insurance Navigator insurance document ingestion pipeline refactor. These decisions align with the technical specifications in RFC001 and CONTEXT.md.

## Database Architecture Decisions

### D1.1: Schema Organization
**Decision**: Create separate `upload_pipeline` schema instead of modifying existing `documents` schema

**Alternatives Considered**:
1. **Modify existing schema**: Update current `documents.documents` table
2. **Create new schema**: Separate `upload_pipeline` schema
3. **Hybrid approach**: Extend existing with new tables

**Chosen Approach**: Separate `upload_pipeline` schema

**Rationale**:
- **Risk Mitigation**: Prevents breaking existing functionality during migration
- **Parallel Operation**: Enables new system to run alongside legacy
- **Data Integrity**: Maintains existing data while building new system
- **Gradual Migration**: Allows incremental cutover without downtime
- **Testing**: Enables comprehensive validation before production deployment

**Implementation**: Created `supabase/migrations/20250814000000_init_upload_pipeline.sql`

### D1.2: Storage Path Pattern
**Decision**: Implement `storage://{bucket}/{user_id}/{document_id}.{ext}` pattern

**Alternatives Considered**:
1. **Current pattern**: Mixed patterns in `files` bucket
2. **User-first**: `{user_id}/{bucket}/{document_id}.{ext}`
3. **Bucket-first**: `{bucket}/{user_id}/{document_id}.{ext}` (chosen)

**Chosen Approach**: `storage://{bucket}/{user_id}/{document_id}.{ext}`

**Rationale**:
- **CONTEXT.md Compliance**: Matches authoritative specification from §0
- **User Isolation**: Clear separation of user data within buckets
- **Bucket Management**: Efficient bucket-level operations and policies
- **Scalability**: Supports future multi-tenant and organization features
- **Security**: Enables bucket-level access controls and policies

**Implementation**: 
- Created `raw` and `parsed` buckets
- Implemented `generate_storage_path()` utility function
- Applied consistent pattern across all storage operations

### D1.3: Co-located Embedding Storage
**Decision**: Store embeddings in same table as chunks (`document_chunks`)

**Alternatives Considered**:
1. **Separate embeddings table**: Dedicated table for vector data
2. **Co-located storage**: Embeddings in same row as chunks (chosen)
3. **External vector database**: Pinecone, Weaviate, Qdrant

**Chosen Approach**: Co-located storage in `document_chunks` table

**Rationale**:
- **RFC001 Alignment**: Matches technical decision from RFC001 §Technical Decisions
- **Performance**: Reduces join complexity for similarity search
- **Consistency**: Simplifies data consistency guarantees
- **pgvector Adequacy**: Sufficient performance for MVP scale
- **Operational**: Easier backup, recovery, and maintenance

**Implementation**:
- Added embedding columns to `document_chunks` table
- Implemented HNSW index with model/version filtering
- Set `fillfactor=70` for performance optimization

### D1.4: Buffer-Based Embedding Updates
**Decision**: Use write-ahead buffer (`document_vector_buffer`) for atomic embedding updates

**Alternatives Considered**:
1. **Direct updates**: Update embedding columns directly
2. **Buffer approach**: Write to buffer, then atomic copy (chosen)
3. **Versioning**: Multiple embedding columns with version management

**Chosen Approach**: Buffer-based atomic updates

**Rationale**:
- **Failure Prevention**: Prevents partial embedding updates during failures
- **Atomic Operations**: Enables clean rollback and recovery
- **Model Changes**: Supports future multi-model strategies
- **Lock Contention**: Reduces lock contention on main table
- **CONTEXT.md Compliance**: Aligns with §8 worker algorithm specification

**Implementation**:
- Created `document_vector_buffer` table
- Implemented advisory locking by `document_id`
- Atomic copy from buffer to final columns

## Utility and Configuration Decisions

### D1.5: UUID Generation Strategy
**Decision**: Use UUIDv5 with deterministic canonicalization for all IDs

**Alternatives Considered**:
1. **Random UUIDs**: `gen_random_uuid()` for uniqueness
2. **Sequential IDs**: Database sequences for ordering
3. **Deterministic UUIDs**: UUIDv5 with canonicalized input (chosen)

**Chosen Approach**: UUIDv5 with canonicalization

**Rationale**:
- **CONTEXT.md Compliance**: Matches §3 specification exactly
- **Idempotency**: Perfect idempotency for retries and resume
- **Deduplication**: Prevents duplicate processing of identical content
- **Distributed Processing**: No coordination needed between workers
- **Debugging**: Facilitates correlation and troubleshooting

**Implementation**:
- Namespace UUID: `6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42`
- Canonicalization: Lowercase, colon-separated, sorted JSON keys
- Functions: `generate_document_id()`, `generate_chunk_id()`, `generate_parse_id()`

### D1.6: Event Logging Taxonomy
**Decision**: Implement comprehensive event logging with predefined codes and types

**Alternatives Considered**:
1. **Free-form logging**: Unstructured log messages
2. **Basic categorization**: Simple info/warn/error levels
3. **Structured taxonomy**: Predefined codes, types, and severities (chosen)

**Chosen Approach**: Structured event taxonomy

**Rationale**:
- **CONTEXT.md Compliance**: Implements §7 observability requirements
- **Consistency**: Standardized logging across all services
- **Monitoring**: Enables structured metrics and alerting
- **Debugging**: Facilitates correlation and troubleshooting
- **Compliance**: Supports audit and compliance requirements

**Implementation**:
- Event types: `stage_started`, `stage_done`, `retry`, `error`, `finalized`
- Severities: `info`, `warn`, `error`
- Event codes: Complete taxonomy from CONTEXT.md §7
- Validation: Input validation for all event parameters

### D1.7: Configuration Management
**Decision**: Use Pydantic BaseSettings with environment variable validation

**Alternatives Considered**:
1. **Environment variables only**: Direct `os.getenv()` usage
2. **Configuration files**: YAML/JSON configuration files
3. **Pydantic settings**: Type-safe configuration with validation (chosen)

**Chosen Approach**: Pydantic BaseSettings

**Rationale**:
- **Type Safety**: Compile-time validation of configuration values
- **Environment Support**: Native environment variable integration
- **Validation**: Built-in validation and constraint checking
- **Documentation**: Self-documenting configuration schema
- **Error Handling**: Clear error messages for misconfiguration

**Implementation**:
- `UploadPipelineConfig` class with Pydantic validation
- Environment variable prefix: `UPLOAD_PIPELINE_`
- Validation rules: File size limits, vector dimensions, API keys
- Default values: Sensible defaults aligned with CONTEXT.md

## Security and Access Control Decisions

### D1.8: Row-Level Security Implementation
**Decision**: Enable RLS on all tables with user-scoped access policies

**Alternatives Considered**:
1. **No RLS**: Application-level access control only
2. **Partial RLS**: RLS on some tables, application control on others
3. **Full RLS**: RLS on all tables with comprehensive policies (chosen)

**Chosen Approach**: Full RLS implementation

**Rationale**:
- **Security**: Defense in depth with database-level access control
- **User Isolation**: Ensures users can only access their own data
- **HIPAA Compliance**: Supports future HIPAA compliance requirements
- **Service Role**: Backend services bypass RLS for processing
- **Audit Trail**: Database-level access logging and monitoring

**Implementation**:
- RLS enabled on all `upload_pipeline` tables
- User-scoped policies for documents, chunks, jobs, and events
- Service role access for backend processing
- Buffer table has no client access (workers only)

### D1.9: Storage Bucket Security
**Decision**: Use private buckets with signed URL access for frontend

**Alternatives Considered**:
1. **Public buckets**: Direct access to storage files
2. **Mixed access**: Some public, some private buckets
3. **Private buckets**: All buckets private with signed URLs (chosen)

**Chosen Approach**: Private buckets with signed URLs

**Rationale**:
- **Security**: No direct access to stored files
- **Access Control**: Time-limited access via signed URLs
- **User Isolation**: Prevents cross-user file access
- **Audit Trail**: All access logged via signed URL generation
- **CONTEXT.md Compliance**: Matches §5 storage and access specification

**Implementation**:
- `raw` and `parsed` buckets created as private
- Frontend access via short-lived signed URLs (5 minute TTL)
- Backend services use service-role access
- User isolation via path-based organization

## Performance and Scalability Decisions

### D1.10: Database Indexing Strategy
**Decision**: Implement partial HNSW index with model/version filtering

**Alternatives Considered**:
1. **Full HNSW index**: Index on all embeddings
2. **Partial index**: Filtered index by model/version (chosen)
3. **Multiple indexes**: Separate indexes for different models

**Chosen Approach**: Partial HNSW index with filtering

**Rationale**:
- **Performance**: Optimized index for current model (text-embedding-3-small)
- **Scalability**: Supports future multi-model strategies
- **Storage**: Reduces index size and maintenance overhead
- **Query Optimization**: Database can use filtered index efficiently
- **CONTEXT.md Compliance**: Aligns with §12 ANN and indexing notes

**Implementation**:
- Partial HNSW index on `embedding` column
- Filter: `WHERE embed_model='text-embedding-3-small' AND embed_version='1'`
- Table optimization: `fillfactor=70` to reduce page splits

### D1.11: Job Queue Implementation
**Decision**: Use Postgres with `FOR UPDATE SKIP LOCKED` for job queue

**Alternatives Considered**:
1. **Redis Streams**: Dedicated message queue system
2. **AWS SQS**: Cloud-based message queue
3. **Postgres queue**: Database-based queue with locking (chosen)

**Chosen Approach**: Postgres-based job queue

**Rationale**:
- **RFC001 Alignment**: Matches technical decision from RFC001 §Technical Decisions
- **Simplicity**: Single database for all operations
- **ACID Guarantees**: Transactional job state management
- **Observability**: Built-in persistence and monitoring
- **Proven Pattern**: Established pattern for moderate scale workloads

**Implementation**:
- `upload_jobs` table with stage/state management
- `FOR UPDATE SKIP LOCKED` for worker coordination
- Unique constraint on active jobs per document/stage
- Comprehensive state transition validation

## Migration and Compatibility Decisions

### D1.12: Legacy System Retirement Strategy
**Decision**: Implement parallel operation with gradual migration approach

**Alternatives Considered**:
1. **Big Bang**: Complete replacement of legacy systems
2. **Parallel operation**: Run both systems during transition (chosen)
3. **Feature flags**: Gradual feature rollout with flags

**Chosen Approach**: Parallel operation with gradual migration

**Rationale**:
- **Risk Mitigation**: Minimizes disruption to existing functionality
- **Validation**: Enables comprehensive testing before cutover
- **Rollback**: Maintains ability to revert if issues arise
- **User Experience**: Smooth transition without service interruption
- **Data Integrity**: Comprehensive validation during migration

**Implementation**:
- New system runs alongside legacy during development
- Frontend can be updated incrementally
- Agent services migrated gradually
- Legacy systems maintained until full validation

### D1.13: API Contract Design
**Decision**: Design new API contracts that align with CONTEXT.md specifications

**Alternatives Considered**:
1. **Maintain compatibility**: Keep existing API contracts
2. **New contracts**: Design new contracts per CONTEXT.md (chosen)
3. **Hybrid approach**: Mix of old and new contracts

**Chosen Approach**: New API contracts per CONTEXT.md

**Rationale**:
- **CONTEXT.md Compliance**: Implements §6 API contracts exactly
- **Consistency**: Unified API design across all endpoints
- **Validation**: Pydantic models for request/response validation
- **Documentation**: Self-documenting API contracts
- **Future-Proofing**: Designed for long-term maintainability

**Implementation**:
- Pydantic models for all API contracts
- Validation rules aligned with CONTEXT.md §9 limits
- Error handling with structured error responses
- Comprehensive type safety and documentation

## Conclusion

Phase 1 architectural decisions establish a solid foundation for the new upload pipeline system. All decisions align with the authoritative technical specifications in CONTEXT.md and RFC001, ensuring consistency and compliance with the established requirements.

**Key Success Factors**:
1. **Compliance**: All decisions align with CONTEXT.md specifications
2. **Risk Mitigation**: Conservative approach to minimize disruption
3. **Scalability**: Design supports future growth and requirements
4. **Security**: Comprehensive security model with RLS and private storage
5. **Migration**: Clear path for legacy system retirement

**Next Phase**: Phase 2 will build upon these architectural decisions to implement the core API endpoints and job queue system.

**Note**: Stage progression has been updated to include buffer states and validation steps:
- `queued → job_validated → parsing → parsed → parse_validated → chunking → chunks_buffered → chunked → embedding → embeddings_buffered → embedded`
