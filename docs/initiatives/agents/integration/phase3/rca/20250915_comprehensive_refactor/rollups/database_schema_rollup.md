# Database Schema Rollup

**Last Updated:** 2025-09-15  
**Maintainer:** Data Engineering Team  
**Status:** active

## Purpose
The database schema defines the data structure and relationships for the Insurance Navigator system, including user management, document storage, chunk processing, and vector embeddings. It provides the foundation for data persistence, user isolation, and efficient querying for the RAG system.

## Key Interfaces
```sql
-- Core tables
upload_pipeline.documents (document_id, user_id, filename, content_hash)
upload_pipeline.document_chunks (chunk_id, document_id, chunk_ord, text, embedding)
upload_pipeline.upload_jobs (job_id, document_id, status, progress)
auth.users (id, email, created_at)
```

## Dependencies
- Input: Document uploads, user data, processing results
- Output: Query results, user data, document metadata
- External: Supabase PostgreSQL, vector extensions, authentication system

## Current Status
- Performance: Good - proper indexing and query optimization
- Reliability: Stable - referential integrity maintained
- Technical Debt: Medium - schema inconsistencies need resolution

## Integration Points
- Main API service for data persistence and retrieval
- RAG system for vector similarity search and chunk retrieval
- Upload pipeline for document and chunk storage
- Authentication system for user data management
- Vector database for embedding storage and search

## Recent Changes
- Fixed table name references (chunks → document_chunks) (September 15, 2025)
- Added proper foreign key constraints (September 15, 2025)
- Implemented vector indexing for similarity search (September 15, 2025)
- Added user isolation and access control (September 15, 2025)

## Known Issues
- Code references incorrect table names in some components
- Schema validation needed for consistency
- Migration scripts needed for existing data
- Vector index optimization needed for performance

## Quick Start
```sql
-- Check schema status
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'upload_pipeline'
ORDER BY table_name, ordinal_position;

-- Query user documents
SELECT d.*, COUNT(dc.chunk_id) as chunk_count
FROM upload_pipeline.documents d
LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
WHERE d.user_id = $1
GROUP BY d.document_id;
```
