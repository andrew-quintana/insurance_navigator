# Testing the Document Processing Pipeline

This directory contains tests for the document processing pipeline, including:
- Document parsing with LlamaParse
- Section-based chunking
- Vector generation with OpenAI embeddings

## Setup

1. Create a `.env.test` file in the `supabase/functions` directory with the following content:
```env
SUPABASE_URL=http://localhost:54321
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
OPENAI_API_KEY=your-openai-api-key
LLAMA_CLOUD_API_KEY=your-llama-cloud-api-key

# Test configuration
TEST_USER_ID=test-user
TEST_DOCUMENT_ID=test-doc-123
TEST_STORAGE_BUCKET=documents
```

2. Replace the placeholder values with your actual API keys and configuration.

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage report
npm run test:coverage
```

## Test Structure

The tests are organized into several files:

- `doc_processor.test.ts`: Tests for the document processing service
- `chunking_service.test.ts`: Tests for the section-based chunking service
- `vector_service.test.ts`: Tests for the vector generation service
- `document_pipeline.test.ts`: End-to-end tests for the entire pipeline

Each test file focuses on a specific component of the pipeline and includes tests for:
- Happy path scenarios
- Error handling
- Edge cases

## Test Data

The tests use sample documents and text content to verify the pipeline's functionality. The test data includes:
- PDF documents with various sections
- Text content with different structures
- Invalid content for error handling tests

## Database Schema

The tests assume the following database tables exist:

### documents
```sql
create table documents (
  id uuid primary key default uuid_generate_v4(),
  user_id text not null,
  filename text not null,
  content_type text not null,
  status text not null,
  storage_path text not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);
```

### document_chunks
```sql
create table document_chunks (
  id uuid primary key default uuid_generate_v4(),
  document_id uuid references documents(id),
  content text not null,
  metadata jsonb not null,
  created_at timestamp with time zone default now()
);
```

### document_vectors
```sql
create table document_vectors (
  id uuid primary key default uuid_generate_v4(),
  document_id uuid references documents(id),
  chunk_id uuid references document_chunks(id),
  embedding vector(1536),
  metadata jsonb not null,
  created_at timestamp with time zone default now()
);
``` 

## Storage Buckets

The tests use the following storage paths:
- `buckets/raw/`: Raw uploaded documents
- `buckets/parsed/`: Parsed document content

Make sure these paths exist in your storage bucket. 