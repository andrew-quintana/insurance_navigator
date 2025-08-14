# Accessa Ingestion Context (MVP) — v0.3

**Purpose**: Single source of truth for the coding agent to implement the MVP ingestion pipeline (upload → parse → chunk → embed → finalize) for the insurance PDF workflow.

**Authoritative decisions captured from discussion on 2025-08-13.**

---

## 0) Final Clarification on Storage Paths

Your update had the bucket/key order flipped. We keep **fixed private buckets** (`raw`, `parsed`) and place `user_id` in the **path**. Final canonical form:

```json
{
  "parser_name": "llamaparse",
  "parser_version": "2025-08-01",
  "source_path": "storage://raw/{user_id}/{document_id}.pdf",
  "parsed_path": "storage://parsed/{user_id}/{document_id}.md",
  "parsed_sha256": "hex64"
}
```

- Buckets are **private**. Frontend access is only via **short-lived signed URLs**.
- All storage URIs in code use the `storage://{bucket}/{user_id}/{document_id}.{ext}` pattern.

---

## 1) Constraints & High-Level Architecture

- **Solo build**, single region.
- **Frontend**: Next.js (Vercel).  
- **API**: FastAPI on Render.  
- **DB**: Supabase Postgres + `pgvector`.  
- **Storage**: Supabase Storage (private buckets: `raw`, `parsed`).  
- **Workers**: Render-hosted. Poll Postgres, perform parse/chunk/embed.  
- **Queue**: `upload_jobs` table (Postgres). Workers use `FOR UPDATE SKIP LOCKED`.  
- **HIPAA-extensible**: Using hosted vendors for production is acceptable at this stage.

---

## 2) Authoritative State & Stages

- **Source of truth**: `upload_jobs.stage` + `upload_jobs.state`.  
- **`documents.processing_status`**: **derived** view of job progress (not authoritative).

**Stages** (sequential): `queued → job_validated → parsing → parsed → parse_validated → chunking → chunks_buffered → chunked → embedding → embeddings_buffered → embedded`  
**State**: `queued | working | retryable | done | deadletter`

Legal transitions and error branches are enforced by worker logic (see §8).

---

## 3) Deterministic IDs & Canonicalization

- **Namespace UUID (immutable)**: `6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42`
- **Canonicalization rules** (apply to all key strings before UUIDv5):
  - Lowercase; `:` as the only separator.
  - JSON configs serialized as **minified, sorted-keys** UTF‑8.
  - Model names use vendor canonical strings, e.g., `text-embedding-3-small`.

**Key strings**:
- `parse_id = "{document_id}:{parser_name}:{parser_version}"`  
- `chunk_id = "{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}"`  
- `embedding_key = "{chunk_id}:{embed_model}:{embed_version}"` (co-located but still computed)

---

## 4) Data Model (Final)

### `documents`
- `document_id uuid PK`
- `user_id uuid`
- `filename text`
- `mime text`
- `bytes_len bigint`
- `file_sha256 text` — SHA‑256 of **raw bytes**
- `parsed_sha256 text` — SHA‑256 of **normalized parsed markdown**
- `raw_path text` — `storage://raw/{user_id}/{document_id}.pdf`
- `parsed_path text` — `storage://parsed/{user_id}/{document_id}.md`
- `processing_status text` — derived cache (optional)
- `created_at timestamptz DEFAULT now()`, `updated_at timestamptz DEFAULT now()`

**Indexes/uniques**:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_filehash
  ON documents (user_id, file_sha256);
CREATE INDEX IF NOT EXISTS ix_documents_user ON documents (user_id);
```

---

### `upload_jobs`
- `job_id uuid PK`
- `document_id uuid FK → documents`
- `stage text` — `upload_validated|parsing|chunking|embedding|finalizing`
- `state text` — `queued|working|retryable|done|deadletter`
- `retry_count int DEFAULT 0`
- `idempotency_key text`
- `payload jsonb`
- `last_error jsonb`
- `claimed_by text`, `claimed_at timestamptz`
- `started_at timestamptz`, `finished_at timestamptz`
- Timestamps

**Indexes/uniques**:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_job_doc_stage_active
  ON upload_jobs (document_id, stage)
  WHERE state IN ('queued','working','retryable');

CREATE INDEX IF NOT EXISTS ix_jobs_state ON upload_jobs (state, created_at);
```

---

### `document_chunks` (chunks **+** single live embedding)
- `chunk_id uuid PK` (UUIDv5 per canonical rules)
- `document_id uuid NOT NULL FK → documents`
- `chunker_name text NOT NULL`, `chunker_version text NOT NULL`
- `chunk_ord int NOT NULL`
- `text text NOT NULL`
- `chunk_sha text NOT NULL` — SHA‑256 of `text`
- **Embedding fields (co-located)**:
  - `embed_model text NOT NULL`
  - `embed_version text NOT NULL`
  - `vector_dim int NOT NULL CHECK (vector_dim = 1536)`
  - `embedding vector(1536) NOT NULL`
  - `embed_updated_at timestamptz DEFAULT now()`
- Timestamps

**Uniq/Index**:
```sql
UNIQUE (document_id, chunker_name, chunker_version, chunk_ord);
CREATE INDEX IF NOT EXISTS idx_hnsw_chunks_te3s_v1
  ON document_chunks USING hnsw (embedding)
  WHERE embed_model='text-embedding-3-small' AND embed_version='1';
```

**Storage/ops hints**:
```sql
ALTER TABLE document_chunks SET (fillfactor=70);
```

---

### `document_vector_buffer` (write-ahead for embedding stage)
- `buffer_id uuid PK DEFAULT gen_random_uuid()`
- `chunk_id uuid FK → document_chunks(chunk_id)`
- `embed_model text NOT NULL`, `embed_version text NOT NULL`
- `vector_dim int NOT NULL CHECK (vector_dim = 1536)`
- `embedding vector(1536) NOT NULL`
- `created_at timestamptz DEFAULT now()`

> Buffer rows are copied into `document_chunks` under advisory lock and then deleted.

---

### `events`
- `event_id uuid PK`
- `job_id uuid FK → upload_jobs`
- `document_id uuid FK → documents`
- `ts timestamptz DEFAULT now()`
- `type text` — `stage_started|stage_done|retry|error|finalized`
- `severity text` — `info|warn|error`
- `code text` — short enumerable (see §7)
- `payload jsonb`
- `correlation_id uuid`

**Indexes**:
```sql
CREATE INDEX IF NOT EXISTS idx_events_job_ts ON events (job_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_doc_ts ON events (document_id, ts DESC);
```

---

## 5) Storage & Access

- **Private buckets**: `raw`, `parsed`.  
- **URI pattern**: `storage://{bucket}/{user_id}/{document_id}.{ext}`.  
- **Frontend**: obtains **signed URLs** (TTL ≈ 5 minutes).  
- **Workers/API**: service-role access via server SDKs.

---

## 6) API Contracts (MVP)

### `POST /upload`
Request:
```json
{ "filename": "string", "bytes_len": 123, "mime": "application/pdf", "sha256": "hex64", "ocr": false }
```
Response:
```json
{ "job_id": "uuid", "document_id": "uuid", "signed_url": "url", "upload_expires_at": "iso8601" }
```

### `GET /job/{job_id}`
```json
{
  "job_id":"uuid",
  "stage":"embedding",
  "state":"working",
  "retry_count":0,
  "progress":{"stage_pct":72.5,"total_pct":80.0},
  "cost_cents":0,
  "document_id":"uuid",
  "last_error":null,
  "updated_at":"iso8601"
}
```

### `upload_jobs.payload` by stage (examples)
- `job_validated`:
```json
{
  "user_id":"uuid",
  "document_id":"uuid",
  "file_sha256":"hex64",
  "bytes_len":12345,
  "mime":"application/pdf",
  "storage_path":"storage://raw/{user_id}/{document_id}.pdf"
}
```
- `parsing` (see §0 snippet)  
- `chunking`:
```json
{ "chunker_name":"markdown-simple", "chunker_version":"1", "num_chunks":128 }
```
- `embedding`:
```json
{
  "embed_model":"text-embedding-3-small",
  "embed_version":"1",
  "vector_dim":1536,
  "num_vectors":128
}
```

---

## 7) Observability

**Taxonomy**:
- `type`: `stage_started|stage_done|retry|error|finalized`
- `severity`: `info|warn|error`
- `codes` (minimum set):  
  `UPLOAD_DEDUP_HIT`, `UPLOAD_ACCEPTED`,  
  `PARSE_REQUESTED`, `PARSE_STORED`, `PARSE_HASH_MISMATCH`,  
  `CHUNK_BUFFERED`, `CHUNK_COMMITTED`,  
  `EMBED_BUFFERED`, `EMBED_COMMITTED`, `EMBED_INDEX_TIMEOUT`,  
  `RETRY_SCHEDULED`, `DLQ_MOVED`

**Helper**: all services use `log_event(job_id, code, type, severity, payload)`.

**Metrics** (log-derived): per-stage latency, retry counts, DLQ depth, ANN probe p95.

---

## 8) Worker Algorithm (Polling + Idempotent Resume)

**Dequeue** (single winner):
```sql
WITH cte AS (
  SELECT job_id
  FROM upload_jobs
  WHERE state='queued'
  ORDER BY created_at
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
UPDATE upload_jobs u
SET state='working', claimed_by=:worker_id, claimed_at=now(),
    started_at=COALESCE(started_at, now())
FROM cte
WHERE u.job_id = cte.job_id
RETURNING u.*;
```

**Stage rules** (always check idempotency first):
- **Job validation**: dedupe via `(user_id, file_sha256)` unique; if hit → advance to `job_validated`.
- **Parse**: if `parsed_path` present and `parsed_sha256` set → advance to `parsed`; else request parse and poll until stored; compute `parsed_sha256` → advance to `parse_validated`.
- **Chunk**: if chunks exist for `(document_id, chunker_name, chunker_version)` and counts match → advance to `chunked`; else re-chunk to buffer → advance to `chunks_buffered`, then commit → advance to `chunked`.
- **Embed**: if `document_chunks` rows have matching `embed_model/version` populated (count check) → advance to `embedded`; else write vectors to buffer → advance to `embeddings_buffered`, **advisory lock by `document_id`**, copy buffer→final columns (`embedding`, `embed_model`, `embed_version`, `vector_dim`, `embed_updated_at`), delete buffer rows → advance to `embedded`.
- **Complete**: mark `done`; set derived status in `documents.processing_status`.

**Retries/backoff**:
- Transient error → `state='retryable'`, `retry_count++`, schedule with exponential backoff (2^n * base). A poller moves `retryable→queued` when delay elapses. Max retries → `deadletter`.

**DB idempotency**:
```sql
-- uploads
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_filehash
  ON documents (user_id, file_sha256);

-- one active job per (doc, stage)
CREATE UNIQUE INDEX IF NOT EXISTS uq_job_doc_stage_active
  ON upload_jobs (document_id, stage)
  WHERE state IN ('queued','working','retryable');
```

---

## 9) Limits & Validation (MVP)

- Max file size: **25 MB**
- Max pages: **200**
- MIME: `application/pdf` only
- Filename ≤ **120 chars**, strip control chars
- Concurrent active jobs/user: **2**
- Rate limits: **30 uploads/day/user**, **10 polls/min/job**
- Parse timeout: **≤120s per 50 pages** (cap 10 min)
- Embed batch: **≤256 vectors/batch**, ≤3 concurrent batches/worker

---

## 10) Normalization for `parsed_sha256`

1) Normalize line endings to `\n`.  
2) Collapse >1 blank line to 1.  
3) Trim trailing spaces per line.  
4) Ensure `#` headings have one space (`## Title`).  
5) Replace images with `![img]`; keep link text `[text](url)` → `[text]`.  
6) Bullets use `-` and 2-space indents.  
7) Collapse multiple spaces to one **outside code blocks**.  
8) Drop zero-width/non-printing chars.  
9) File ends with a single `\n`.  

`parsed_sha256 = sha256(utf8(normalized_md))`

---

## 11) Security & RLS

Enable RLS on all tables. Clients can **SELECT** only their rows; **no client writes**. Backend/worker uses service-role (bypasses RLS).

Policies (essential):
```sql
-- documents
CREATE POLICY doc_select_self ON documents
  FOR SELECT USING (user_id = auth.uid());

-- chunks
CREATE POLICY chunk_select_self ON document_chunks
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM documents d
            WHERE d.document_id = document_chunks.document_id
              AND d.user_id = auth.uid())
  );

-- jobs/events (optional user visibility)
CREATE POLICY job_select_self ON upload_jobs
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM documents d
            WHERE d.document_id = upload_jobs.document_id
              AND d.user_id = auth.uid())
  );
CREATE POLICY evt_select_self ON events
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM documents d
            WHERE d.document_id = events.document_id
              AND d.user_id = auth.uid())
  );
```

**Key management**: Render env only (`SUPABASE_SERVICE_ROLE`, `LLAMAPARSE_API_KEY`, `OPENAI_API_KEY`).  
**Logging**: use `log_event`; never log `text`, `embedding`, full storage paths, or tokens.

---

## 12) ANN & Indexing Notes

- One live embedding per chunk.  
- Partial HNSW index tied to `(embed_model, embed_version)` filter.  
- Place embedding columns **after** small columns; table `fillfactor=70` to reduce page splits.  
- Future multi-model plan: add `embedding_v2` column + second partial HNSW; backfill and cut over.

---

## 13) Out-of-Scope (MVP)

- No checklist/strategy tables; those live in a separate service.  
- No PHI-on vendor isolation or on-prem inference for this milestone (can be added later).

---

## 14) File/Schema Locations for the Agent

- `/schemas/upload.request.json` and `/schemas/upload.response.json` for API validation.  
- RFC should embed this document verbatim as “Context”.  
- Migrations create/alter: `documents`, `upload_jobs`, `document_chunks`, `document_vector_buffer`, `events`.  
- Shared utility: `uuidv5(ns_uuid, canonical_string)`; `log_event(...)` helper; normalization function for parsed MD.

---

## 15) Open TODOs for PRD/RFC Generation

- Publish chosen **chunker** config (`markdown-simple@1`) and example unit test.  
- Define `PARSE_REQUEST`/`POLL` cadence (initial delay, max backoff).  
- Decide base retry backoff (e.g., 2^n * 3s, n≤3).  
- Confirm index maintenance windows and `VACUUM` settings for `document_chunks` during bulk re-embeds.

---

*End of context.*
