# Upload Service Rollup

**Last Updated:** 2025-08-21  
**Maintainer:** backend-team  
**Status:** active

## Purpose
The upload service is a local-first, Docker-based document processing pipeline that handles file uploads, parsing, chunking, and embedding generation. It implements a unified BaseWorker architecture with comprehensive state machine management, buffer operations, and enhanced monitoring capabilities.

## Key Interfaces
```python
# Core upload job processing
class BaseWorker:
    async def process_jobs_continuously(self)
    async def _process_single_job_with_monitoring(self, job)
    async def _update_job_status(self, job_id, status, progress=None)

# State machine transitions
VALID_TRANSITIONS = {
    'uploaded': ['parse_queued', 'failed_parse'],
    'parse_queued': ['parsed', 'failed_parse'],
    'parsed': ['parse_validated', 'failed_parse'],
    'parse_validated': ['chunking', 'failed_chunking'],
    'chunking': ['chunks_stored', 'failed_chunking'],
    'chunks_stored': ['embedding_queued', 'failed_embedding'],
    'embedding_queued': ['embedding_in_progress', 'failed_embedding'],
    'embedding_in_progress': ['embeddings_stored', 'failed_embedding'],
    'embeddings_stored': ['complete']
}

# API endpoints
POST /upload/webhook - LlamaParse callback processing
GET /upload/status/{job_id} - Job status and progress
POST /upload/jobs - Create new upload job
```

## Dependencies
- Input: Raw documents via file upload API
- Output: Processed documents with embeddings in vector database
- External: LlamaParse API, OpenAI API, Supabase storage
- Database: PostgreSQL with pgvector extension

## Current Status
- Performance: 2-5 second processing time per document
- Reliability: >98% success rate in production, >99% in local environment
- Technical Debt: Legacy state transitions need cleanup, monitoring improvements needed

## Integration Points
- Frontend uploads documents through API gateway
- Vector embeddings consumed by RAG pipeline and search
- Status updates provide real-time feedback to users
- Webhook integration with external parsing services

## Recent Changes
- Implemented local-first development with Docker Compose
- Enhanced monitoring with correlation IDs and structured logging
- Added comprehensive testing infrastructure with mock services
- Improved error handling with classification and retry logic

## Known Issues
- Some legacy error states need consolidation
- Mock service development still evolving
- Deployment verification framework under development

## Quick Start
```bash
# Setup local environment
./scripts/setup-local-env.sh

# Run comprehensive tests
./scripts/run-local-tests.sh

# Validate environment health
./scripts/validate-local-environment.sh
```