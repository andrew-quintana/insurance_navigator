# Document Upload Pipeline MVP

## Summary
This specification defines the MVP testing effort for validating the document upload pipeline across multiple environments.

## Problem & Context
We need confidence that both small test files and large real-world insurance documents can move through the entire pipeline—from upload to storage, parsing, chunking, embedding, and metadata persistence—without failure across local, dev, and production cloud environments.

## Goals
- Ensure small and large documents process end-to-end successfully in all environments.
- Validate backend API and worker services can switch seamlessly between local, mock, dev, and production.
- Confirm real documents reach blob storage, are parsed/chunked, embeddings generated, and metadata/vector entries written.

## Non-goals
- No optimization for high throughput in MVP.
- No extended performance benchmarking or load testing.

## Stakeholders & Roles
- **Accountable Owner**: You (test lead).
- **Engineering Support**: Backend engineer (API + worker).
- **Reviewer**: Product owner for acceptance demo.

## Functional Requirements (RFC 2119)
- The pipeline **MUST** process both a small simulated document and a large real-world document end-to-end.  
- The backend API and worker services **MUST** support configuration switching across local, mock, dev, and production.  
- The pipeline **MUST** confirm document outputs exist in blob storage, parsed/chunked results, embeddings, and metadata tables.  

## Non-functional Requirements
- The system **SHOULD** recover automatically from transient failures to avoid unrecoverable failed uploads.  
- Minimal throughput requirement; resilience prioritized over performance.  
- Basic observability/logging required to diagnose failed uploads.  

## Constraints
- No hard deadlines; development timebox flexible.  
- No platform limitations called out.  
- Dependencies: blob storage, OpenAI embeddings API, relational DB/vector DB.  

## Milestones & Review Criteria
- **Phase 1**: Validate the current API service and worker service using the same framework created for local and development testing.  
  - **Goal**: Verify performance of the API service and worker service with the known working development/local Supabase instances.  

- **Phase 2**: Run the API service and worker service against local servers but connect them to the production Supabase database.  
  - **Goal**: Ensure the production Supabase is built and configured correctly by comparing behavior with the known-good local instances. Confirm that production matches local in functionality.  

- **Phase 3**: Deploy the API service and worker service in the cloud, integrated with the production Supabase database.  
  - **Goal**: Confirm cloud deployments behave consistently with local deployments, and identify any adjustments needed for alignment.  

- **MVP Demo Checkpoint**: Successful completion of Phase 3 with a full document upload pipeline running in the cloud.  
- **Acceptance Criteria**: End-to-end success demonstrated with one real document, verified outputs across all storage layers (blob, parsed/chunked, embeddings, metadata/vector DB).  

## Upload Pipeline Workflow

The document upload pipeline follows a specific sequence of status transitions, each representing a distinct processing stage:

### Pipeline Status Flow

1. **`uploaded`** - Initial state after file upload
   - Frontend (or simulated frontend) uses signed URL to upload file to blob storage
   - Document stored in `files` bucket with path: `files/user/{userId}/raw/{datetime}_{hash}.{ext}`

2. **`upload_validated`** - Worker validates uploaded document
   - Worker recognizes `uploaded` state and computes hash of uploaded file
   - Checks for duplicate documents by comparing hashes
   - If duplicate found: deletes duplicate file and completes job
   - If unique: proceeds to next stage

3. **`parse_queued`** - Document queued for parsing
   - Worker sends document to LlamaParse API for parsing
   - Provides signed URL for parsed markdown file upload
   - Sets up webhook to receive parsing completion notification
   - LlamaParse will upload parsed markdown and call webhook

4. **`parsed`** - Document parsing completed
   - LlamaParse webhook updates job status to `parsed`
   - Parsed markdown file stored in `parsed` bucket
   - Ready for validation stage

5. **`parse_validated`** - Parsed document validated
   - Worker validates parsed markdown document
   - Checks for duplicate parsed content via hashing
   - Ensures parsed content integrity

6. **`chunks_stored`** - Document chunked and stored
   - Document split into chunks and stored in `document_chunks` table
   - Each chunk hashed to prevent duplicates
   - Chunks ready for embedding generation

7. **`embedding_in_progress`** - Embeddings being generated
   - Cyclical process working through all document chunks
   - Only processes chunks without existing vectors
   - Resumable if worker or database crashes mid-process

8. **`embedded`** - Embeddings completed
   - All chunk embeddings generated and stored
   - Vector embeddings ready for search/retrieval

9. **`complete`** - Processing completed successfully
   - Final status indicating successful end-to-end processing
   - All artifacts created and validated

### Worker Responsibilities

The enhanced worker must handle all status transitions:
- **`uploaded` → `upload_validated`**: Validate file hash, check for duplicates
- **`upload_validated` → `parse_queued`**: Send to LlamaParse API
- **`parsed` → `parse_validated`**: Validate parsed content
- **`parse_validated` → `chunks_stored`**: Create and store document chunks
- **`chunks_stored` → `embedding_in_progress`**: Generate embeddings for chunks
- **`embedding_in_progress` → `embedded`**: Complete embedding generation
- **`embedded` → `complete`**: Mark processing complete

### External API Integration

- **LlamaParse API**: Handles document parsing via webhook pattern
- **OpenAI Embeddings API**: Generates vector embeddings for chunks
- **Supabase Storage**: Stores raw files, parsed markdown, and other artifacts

## Integration Points
- Blob storage (document persistence).  
- Parsing + chunking service.  
- OpenAI embeddings API.  
- Relational DB + vector DB (metadata + embeddings).  

## Edge Cases
- Large document near size limits.  
- Network failure during upload.  
- Configuration mismatch between services.  

## Assumptions
- Local/dev testing already validated; focus is on production cloud.  
- Small and large test documents available and representative.  

## Open Questions
- Do we need retries with exponential backoff or is simple retry sufficient?  
- Should MVP validate document ordering in DB or only presence?  

## Decision Log
- Resilience prioritized over throughput in MVP.  
- No dedicated performance benchmarking.  
- Acceptance requires full pipeline verification, not just unit test success.  

## References
- RFC 2119 requirement levels [oai_citation:0‡rfc2119.txt.pdf](file-service://file-GLs8KjnZYjKtuDFNUuVmCy)  
- Google SRE guidance on SLOs and error budgets [oai_citation:1‡Google SRE SLO.pdf](file-service://file-XBLWBphH6LtKgBby3n8NnS) [oai_citation:2‡Google SRE SLI.pdf](file-service://file-PsCACjMN6BXgNrhhVtxCbq)  
- Atlassian PRD structure for product requirements [oai_citation:3‡Product Requirements Documents (PRD) Explained | Atlassian.pdf](file-service://file-Dn7mUQvhUT2Bq5qUo7qwgp)  