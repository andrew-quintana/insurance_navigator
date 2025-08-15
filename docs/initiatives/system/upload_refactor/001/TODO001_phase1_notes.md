# Phase 1 Implementation Notes: Foundation & Legacy Assessment

## Overview
Phase 1 of the Accessa insurance document ingestion pipeline refactor has been completed. This phase focused on establishing the foundation for the new system while assessing legacy dependencies.

## Completed Tasks

### T1.1: Legacy System Dependency Audit ✅
**Legacy Systems Identified:**

#### Supabase Edge Functions (`supabase/functions/`)
- **upload-handler**: Main file upload endpoint (`/functions/v1/upload-handler`)
- **doc-parser**: PDF parsing integration with LlamaIndex
- **chunker**: Document chunking with markdown processing
- **embedder**: OpenAI embedding generation
- **processing-webhook**: LlamaIndex callback handling
- **_shared**: Common utilities and CORS handling

#### Python Database Services (`db/services/`)
**High-Impact Services (Direct imports found):**
- `document_service.py` - Core document management (imported in 8+ files)
- `db_pool.py` - Database connection management (imported in 15+ files)
- `user_service.py` - User management (imported in 5+ files)
- `storage_service.py` - File storage operations (imported in 4+ files)
- `embedding_service.py` - Vector operations (imported in 3+ files)
- `auth_service.py` - Authentication (imported in 2+ files)
- `conversation_service.py` - Chat/conversation management (imported in 2+ files)

**Medium-Impact Services:**
- `encryption_aware_embedding_service.py` - HIPAA-compliant embeddings
- `transaction_service.py` - Database transaction management

**Files with Legacy Dependencies:**
- `main.py` - Main application entry point
- `graph/agent_orchestrator.py` - Agent workflow management
- `scripts/workers/document_processor.py` - Background processing
- Multiple test files in `tests/` directory
- Various utility scripts in `scripts/` directory

#### Frontend Integration Points
**DocumentUploadServerless.tsx:**
- **Current Endpoint**: `/functions/v1/upload-handler` (Supabase Edge Function)
- **Upload Flow**: FormData → Edge Function → Supabase Storage → Processing Pipeline
- **Error Handling**: 409 status for duplicate files, general error handling
- **File Validation**: 50MB limit, multiple file types (PDF, DOC, DOCX, TXT)

### T1.2: Database Schema Implementation ✅
**New Schema Created: `upload_pipeline`**

#### Core Tables
1. **documents** - Document metadata and storage paths
   - Primary key: `document_id` (UUID)
   - User isolation: `user_id` field with RLS policies
   - Deduplication: Unique index on `(user_id, file_sha256)`
   - Storage paths: `raw_path` and `parsed_path` using `storage://` URI pattern

2. **upload_jobs** - Job queue and state management
   - Stages: `queued → job_validated → parsing → parsed → parse_validated → chunking → chunks_buffered → chunked → embedding → embeddings_buffered → embedded`
   - States: `queued | working | retryable | done | deadletter`
   - Idempotency: Unique constraint on active jobs per document/stage
   - Worker coordination: `claimed_by`, `claimed_at` fields

3. **document_chunks** - Chunks with co-located embeddings
   - Deterministic IDs: UUIDv5 generation for perfect idempotency
   - Vector storage: `vector(1536)` with HNSW indexing
   - Performance: `fillfactor=70` to reduce page splits
   - Partial index: HNSW index filtered by model/version

4. **document_vector_buffer** - Write-ahead buffer for embeddings
   - Atomic updates: Prevents partial embedding failures
   - Advisory locking: Enables conflict-free updates
   - Cleanup: Buffer rows deleted after successful commit

5. **events** - Comprehensive event logging
   - Event taxonomy: `stage_started`, `stage_done`, `retry`, `error`, `finalized`
   - Severity levels: `info`, `warn`, `error`
   - Correlation tracking: `correlation_id` for distributed tracing

#### Storage Buckets
- **raw**: Private bucket for PDF uploads (25MB limit)
- **parsed**: Private bucket for markdown files (10MB limit)
- **Access Pattern**: `storage://{bucket}/{user_id}/{document_id}.{ext}`

#### Security & RLS
- Row-level security enabled on all tables
- Users can only access their own documents and related data
- Service-role access for backend processing (bypasses RLS)
- Buffer table has no client access (workers only)

#### Helper Functions
- **Stage validation**: Ensures proper stage progression
- **State validation**: Enforces valid state transitions
- **Timestamp triggers**: Automatic `updated_at` maintenance

### T1.3: Shared Utilities Development ✅
**Core Utility Functions:**

#### UUID Generation (`utils/upload_pipeline_utils.py`)
- **Namespace**: `6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42` (from CONTEXT.md)
- **Canonicalization**: Lowercase, colon-separated, sorted JSON keys
- **Deterministic IDs**: `document_id`, `chunk_id`, `parse_id`

#### Event Logging
- **Event Codes**: Complete taxonomy from CONTEXT.md §7
- **Validation**: Type, severity, and code validation
- **Correlation**: Support for distributed tracing

#### Markdown Normalization
- **Rules Implementation**: All 9 normalization rules from CONTEXT.md §10
- **SHA256 Computation**: Deterministic hashing for content verification
- **Code Block Preservation**: Maintains formatting integrity

#### Validation Functions
- **Stage Transitions**: Enforces sequential processing
- **State Transitions**: Validates job state changes
- **Retry Logic**: Exponential backoff with max retry limits

### T1.4: Environment and Configuration Setup ✅
**FastAPI Project Structure:**

#### Configuration Management (`api/upload_pipeline/config.py`)
- **Environment Variables**: Supabase, LlamaIndex, OpenAI configuration
- **Processing Limits**: File size, pages, concurrent jobs, rate limits
- **Validation**: Pydantic validation with environment-specific constraints
- **Defaults**: Sensible defaults aligned with CONTEXT.md specifications

#### API Models (`api/upload_pipeline/models.py`)
- **Request/Response Models**: Pydantic models for API validation
- **Job Payloads**: Stage-specific payload structures
- **Validation Rules**: File size, MIME type, filename sanitization
- **Error Handling**: Structured error responses

#### Dependencies (`api/requirements.txt`)
- **FastAPI Stack**: FastAPI, Uvicorn, Pydantic
- **Database**: Supabase, asyncpg, psycopg2
- **External Services**: httpx, aiohttp for API calls
- **Development**: Testing, linting, and formatting tools

## Architectural Decisions Made

### 1. Schema Organization
**Decision**: Created separate `upload_pipeline` schema instead of modifying existing
**Rationale**: 
- Prevents breaking existing functionality during migration
- Enables parallel operation and gradual cutover
- Maintains data integrity during transition

### 2. Storage Path Pattern
**Decision**: Implemented `storage://{bucket}/{user_id}/{document_id}.{ext}` pattern
**Rationale**:
- Aligns with CONTEXT.md §0 specifications
- Provides clear user isolation
- Enables efficient bucket management

### 3. Co-located Embeddings
**Decision**: Store embeddings in same table as chunks
**Rationale**:
- Reduces join complexity for similarity search
- Simplifies data consistency guarantees
- Aligns with RFC001 technical decisions

### 4. Buffer-Based Updates
**Decision**: Implement write-ahead buffer for embedding updates
**Rationale**:
- Prevents partial updates during failures
- Enables atomic switchover for model changes
- Supports future multi-model strategies

## Legacy System Impact Assessment

### High-Impact Dependencies
1. **Document Service**: Core document operations across multiple agents
2. **Database Pool**: Connection management used throughout system
3. **Storage Service**: File operations in upload and processing flows
4. **Embedding Service**: Vector operations for RAG functionality

### Migration Complexity
- **Frontend**: Single component update (DocumentUploadServerless.tsx)
- **Agents**: Multiple import updates across patient navigator and RAG systems
- **Scripts**: Utility scripts and background workers
- **Tests**: Comprehensive test suite updates

### Risk Mitigation
- **Parallel Operation**: New system runs alongside legacy during transition
- **Gradual Migration**: Non-critical endpoints migrated first
- **Rollback Plan**: Legacy services maintained until validation complete
- **Data Integrity**: Comprehensive validation during migration

## Next Phase Requirements

### Phase 2 Dependencies
- Database schema deployed and validated
- Shared utilities tested and verified
- Configuration management operational
- Legacy dependency mapping complete

### Technical Debt Identified
- **File Type Support**: Frontend supports multiple types, new system PDF-only
- **File Size Limits**: Frontend 50MB vs. new system 25MB
- **Error Handling**: Different error response formats
- **Progress Tracking**: Current system vs. new job-based approach
- **Stage Naming**: Updated stage progression with buffer states and validation steps

### Integration Challenges
- **Authentication**: JWT token handling differences
- **Storage Access**: Signed URL generation and management
- **Error Codes**: Mapping between legacy and new error systems
- **Progress Updates**: Real-time vs. polling-based status updates

## Success Metrics

### Phase 1 Completion
- ✅ Database schema created and validated
- ✅ Shared utilities implemented and tested
- ✅ Configuration management established
- ✅ Legacy dependency mapping complete
- ✅ FastAPI project structure ready

### Quality Assurance
- **Schema Validation**: All tables, indexes, and constraints implemented
- **Utility Testing**: UUID generation and validation functions verified
- **Configuration**: Environment variable validation working
- **Documentation**: Complete implementation notes and decisions captured

## Notes and Observations

### Technical Insights
1. **Legacy Complexity**: Current system has more file type support than MVP requires
2. **Database Design**: New schema significantly improves on current structure
3. **Security Model**: RLS policies provide better user isolation than current approach
4. **Performance**: Co-located embeddings and HNSW indexing will improve search performance

### Migration Strategy
1. **Parallel Development**: New system can be built without breaking existing functionality
2. **Gradual Cutover**: Frontend and agents can be migrated incrementally
3. **Data Migration**: Existing documents can be transferred with deterministic ID generation
4. **Testing**: Comprehensive testing possible before production deployment

### Risk Assessment
1. **High Risk**: External service dependencies (LlamaIndex, OpenAI)
2. **Medium Risk**: Database performance with large embedding tables
3. **Low Risk**: Storage costs and user adoption

## Conclusion

Phase 1 has successfully established the foundation for the new upload pipeline system. The database schema, shared utilities, and configuration management are ready for Phase 2 implementation. The legacy system assessment provides a clear roadmap for safe migration and retirement of existing systems.

**Next Steps**: Proceed to Phase 2 (Core API & Job Queue Implementation) with the established foundation and clear understanding of legacy dependencies.
