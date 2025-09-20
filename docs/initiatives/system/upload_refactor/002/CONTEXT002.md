# Insurance Navigator Ingestion Context (002 Worker Refactor) — v1.0

**Purpose**: Single source of truth for implementing the 002 Worker Refactor iteration - a unified BaseWorker architecture with buffer-driven pipeline orchestration for the insurance PDF workflow.

**Authoritative decisions captured from 002 iteration requirements on 2025-08-15.**

---

## 0) TL;DR (What's changing and why)

- **Single BaseWorker**: Replace specialized workers with one orchestrating worker that runs a state machine per upload_job
- **Buffer-first writes**: All handoffs persist via buffer tables (document_chunk_buffer, document_vector_buffer) for idempotency and observability
- **Webhook-driven parsing**: LlamaParse callbacks write parsed artifacts to blob storage and update upload_jobs.status
- **Micro-batch embeddings**: OpenAI calls are batched efficiently with per-batch persistence to prevent memory accumulation
- **Directory refactor**: Move workers from api/ to backend/workers/ and shared utilities to backend/shared/

---

## 1) Context & Goals

**Processing Profile:**
- Low-frequency per user, high total volume ingestion
- Deterministic processing with idempotent writes at each stage
- Decouple API from workers for future managed queue/worker platform migration

**Core Goals:**
1. **Robust idempotence and crash recovery**
2. **Clear stage boundaries** with buffer persistence
3. **Minimal coupling** between API and worker components
4. **Horizontal scalability** via micro-batching and stateless workers

---

## 2) State Machine (per upload_job)

### Status Values (authoritative in upload_jobs.status)
```
uploaded → parse_queued → parsed → parse_validated → chunking → chunks_stored → embedding_queued → embedding_in_progress → embeddings_stored → complete
```

**Error Terminals:** `failed_parse`, `failed_chunking`, `failed_embedding`

### Stage Transitions

1. **Upload → Parse Queue**: API inserts upload_jobs row with status=parse_queued. LlamaParse invoked with webhook URL
2. **Webhook → Parsed**: LlamaParse calls webhook → write parsed MD to blob storage → update status=parsed
3. **Parse Validation**: Worker validates parsed file, handles deduplication, advances to parse_validated
4. **Chunking**: Worker chunks internally → write to document_chunk_buffer → update status=chunks_stored
5. **Embedding Queue**: Worker prepares micro-batches → update status=embedding_queued
6. **Embedding**: Per micro-batch → call OpenAI → persist to document_vector_buffer → status=embeddings_stored
7. **Complete**: Optional consolidation step or leave buffers as source of truth

---

## 3) Data Model (Idempotent Keys & Buffers)

### upload_jobs (Job State Management)
```sql
CREATE TABLE upload_jobs (
    job_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    document_id UUID NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'uploaded', 'parse_queued', 'parsed', 'parse_validated', 
        'chunking', 'chunks_stored', 'embedding_queued', 
        'embedding_in_progress', 'embeddings_stored', 'complete',
        'failed_parse', 'failed_chunking', 'failed_embedding'
    )),
    raw_path TEXT NOT NULL,  -- storage://{user_id}/raw/{document_id}.pdf
    parsed_path TEXT,        -- storage://{user_id}/parsed/{document_id}.md
    parsed_sha256 TEXT,      -- hash of parsed content
    chunks_version TEXT NOT NULL, -- chunker@semver
    embed_model TEXT,        -- text-embedding-3-small
    embed_version TEXT,      -- internal version string
    progress JSONB,          -- {chunks_total, chunks_done, embeds_total, embeds_done}
    retry_count INT DEFAULT 0,
    last_error JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_upload_jobs_status ON upload_jobs (status, created_at);
CREATE INDEX idx_upload_jobs_document ON upload_jobs (document_id);
```

### document_chunk_buffer (Staging for Chunks)
```sql
CREATE TABLE document_chunk_buffer (
    chunk_id UUID NOT NULL,  -- UUIDv5(ns, "{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}")
    document_id UUID NOT NULL,
    chunk_ord INT NOT NULL,
    chunker_name TEXT NOT NULL,
    chunker_version TEXT NOT NULL,
    chunk_sha TEXT NOT NULL,  -- sha256(normalized_chunk_text)
    text TEXT NOT NULL,
    meta JSONB,              -- offsets, page, headings, etc.
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (chunk_id)
);

CREATE INDEX idx_chunk_buffer_document ON document_chunk_buffer (document_id);
```

### document_vector_buffer (Staging for Embeddings)
```sql
CREATE TABLE document_vector_buffer (
    document_id UUID NOT NULL,
    chunk_id UUID NOT NULL,
    embed_model TEXT NOT NULL,
    embed_version TEXT NOT NULL,
    vector VECTOR(1536) NOT NULL,
    vector_sha TEXT NOT NULL,  -- sha256(base64(vector)) for verification
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (chunk_id, embed_model, embed_version),
    FOREIGN KEY (chunk_id) REFERENCES document_chunk_buffer(chunk_id)
);

CREATE INDEX idx_vector_buffer_document ON document_vector_buffer (document_id);
CREATE INDEX idx_vector_buffer_embedding_progress ON document_vector_buffer (document_id, embed_model, embed_version);
```

---

## 4) Webhook Contract (LlamaParse → API)

### Endpoint: POST /webhooks/llamaparse

**Authentication:** HMAC header with signed secret
**Required:** job_id and document_id in payload

**Payload Structure:**
```json
{
  "job_id": "uuid",
  "document_id": "uuid", 
  "status": "parsed",
  "artifacts": [{
    "type": "markdown",
    "content": "# Document content...",
    "sha256": "hex64",
    "bytes": 12345
  }],
  "meta": {
    "parser_name": "llamaparse",
    "parser_version": "2025-08-01"
  }
}
```

**Handler Behavior:**
1. Verify HMAC signature and validate document_id
2. Deduplicate via sha256 comparison
3. Write artifact to blob storage using backend credentials
4. Update upload_jobs: parsed_path, parsed_sha256, status='parsed'
5. Optionally advance to parse_validated after validation

---

## 5) BaseWorker Orchestration Pattern

### Core Processing Loop
```python
class BaseWorker:
    def process_job(self, job):
        try:
            if job.status == "parsed":
                self._validate_parsed(job)        # → parse_validated
            elif job.status == "parse_validated":
                self._chunk(job)                  # → chunks_stored
            elif job.status == "chunks_stored":
                self._queue_embeddings(job)       # → embedding_queued
            elif job.status in ["embedding_queued", "embedding_in_progress"]:
                self._embed_batches(job)          # → embeddings_stored
            elif job.status == "embeddings_stored":
                self._finalize(job)               # → complete
        except RetryableError as e:
            self._schedule_retry(job, e)
        except Exception as e:
            self._mark_failed(job, e)
```

### Micro-batching Strategy
- **Batch size**: 256 vectors max per OpenAI call
- **Immediate persistence**: Write to document_vector_buffer after each batch
- **Progress tracking**: Update upload_jobs.progress atomically per batch
- **Memory management**: No in-memory accumulation of all vectors

### Rate Limiting
- Central rate limiter per worker process
- Exponential backoff on 429/5xx responses
- Idempotent resume on rate limit recovery

---

## 6) Idempotency Strategy

### Per-Stage Idempotency
- **Parse**: Dedupe by parsed_sha256; reuse canonical path if duplicate exists
- **Chunk**: Deterministic chunk_id + chunk_sha with `ON CONFLICT DO NOTHING`
- **Embed**: Unique (chunk_id, embed_model, embed_version) with UPSERT on vector_sha differences
- **Status**: Advance only after durable writes; never advance on partial failure

### Deterministic ID Generation
- **Namespace UUID**: `6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42`
- **Chunk ID**: UUIDv5(namespace, "{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}")
- **Canonicalization**: Lowercase, colon-separated, sorted JSON keys

---

## 7) Storage & Access Patterns

### Storage Organization
```
storage://raw/{user_id}/{document_id}.pdf
storage://parsed/{user_id}/{document_id}.md
```

**Security Model:**
- Private buckets with no public access
- Backend services use service-role credentials
- Frontend accesses via short-lived signed URLs (5 min TTL)
- User isolation via path-based organization

**Access Flow:**
- Upload: Frontend → Signed URL → Supabase Storage
- Parse: Worker → Service SDK → Supabase Storage  
- Webhook: API → Service SDK → Supabase Storage
- Read: Frontend → API → Signed URL → Supabase Storage

---

## 8) API Surface

### Core Endpoints
- **POST /webhooks/llamaparse** → Handle LlamaParse callbacks (see §4)
- **POST /jobs/{document_id}/advance** → Internal status advancement with invariant checks
- **GET /jobs/{document_id}** → Return job status and progress counters
- **POST /jobs/{document_id}/retry** → Reset from failure state to last successful stage

### Transaction Requirements
All status changes must be transactional with the writes that justify the status change (same transaction as buffer inserts, or guarded by count/sha checks).

---

## 9) Directory Layout (Refactored)

```
backend/
├── api/                # FastAPI app (public endpoints + webhook)
│   ├── main.py
│   ├── webhooks/
│   └── jobs/
├── workers/            # BaseWorker + runner
│   ├── base_worker.py
│   ├── runner.py
│   └── processors/
├── shared/             # Common utilities
│   ├── db/
│   ├── storage/
│   ├── logging/
│   ├── hashing/
│   ├── rate_limit/
│   └── schemas/
└── scripts/            # Migrations, local runners
```

---

## 10) Security & Compliance

### Authentication & Authorization
- Backend service accounts with least privilege principles
- Webhook HMAC signatures with key rotation capability
- No direct client uploads without backend validation

### Data Protection
- Vectors are non-reversible representations
- No raw secrets in logs; redact sensitive payloads
- Replay protection via nonce + TTL for webhooks

### Storage Security
- Backend-issued signed URLs only
- No public bucket access
- Service-role access for all backend operations

---

## 11) Observability & Monitoring

### Key SLIs
- **Processing times**: time-to-parse, time-to-chunk, time-to-first-embedding, time-to-complete
- **Error rates**: by stage and error type
- **Queue metrics**: queue lag, longest-waiting jobs
- **Reprocessing rate**: jobs requiring retries

### Cost Telemetry
- Tokens per batch and cost per document
- Retry costs and efficiency metrics
- Storage utilization by user and document type

### Dashboards
- Job counts by status with real-time updates
- Top error causes and resolution patterns
- Processing throughput and capacity utilization

---

## 12) Buffer Strategy Rationale

### Why Keep Embedding Buffers?
- **Staging semantics**: Quality checks before promoting to production index
- **Model versioning**: Easy rollback and A/B testing of embedding models
- **Observability**: Clear per-batch cost and performance tracking
- **Atomic operations**: Prevent partial updates during failures

### Alternative: Direct to Final Table
- Simpler schema with (chunk_id, embed_model, embed_version) as final key
- Requires careful handling of partial failures
- Less visibility into batch-level operations

### Operational Guidelines
- Write per batch, not end-of-job accumulation
- Consider promoted_at flag or materialized views for production queries
- Maintain buffer cleanup processes for completed jobs

---

## 13) Validation & Quality Gates

### Parse Validation
- Verify parsed_sha256 matches expected content hash
- Validate markdown structure and content integrity
- Handle duplicate detection and canonical path assignment

### Chunk Validation  
- Verify chunk count matches expected based on document size
- Validate chunk_sha consistency for deterministic reproduction
- Check chunk ordering and overlap parameters

### Embedding Validation
- Verify vector dimensions match model specifications (1536 for text-embedding-3-small)
- Validate vector_sha for data integrity
- Check batch completion against chunk buffer counts

---

## 14) Error Handling & Recovery

### Error Classification
- **Transient**: Network timeouts, rate limits, temporary service unavailable
- **Permanent**: Invalid file format, parsing errors, quota exceeded  
- **Recoverable**: Partial processing, external service errors

### Retry Strategy
- Exponential backoff: 2^retry_count * 3 seconds
- Maximum retries: 3 attempts
- Dead letter handling for permanent failures
- Progress preservation across retries

### Recovery Procedures
- Resume from last successful stage using status and buffer state
- Idempotent operations prevent duplicate work
- Manual retry capability for permanent failure investigation

---

## 15) Performance Considerations

### Batch Optimization
- Adaptive batch sizes based on token estimates and rate limits
- Concurrent micro-batch processing within rate limit constraints
- Memory-efficient streaming for large document processing

### Database Performance
- Partial indexes on status for efficient worker polling
- Buffer table cleanup processes for completed jobs
- Connection pooling and prepared statement usage

### External Service Management
- Circuit breaker patterns for external service failures
- Timeout configuration for long-running parse operations
- Cost optimization through efficient batching strategies

---

## 16) Future Migration Considerations

### Cloud Platform Readiness
- Stateless worker design enables easy Kubernetes/container deployment
- Buffer-based handoffs support managed queue services (SQS, Pub/Sub)
- API/worker separation facilitates microservice architecture

### Scaling Strategies
- Horizontal worker scaling via additional instances
- Document-level parallelism through job queue partitioning
- Multi-region deployment support through deterministic operations

---

*End of Context 002*