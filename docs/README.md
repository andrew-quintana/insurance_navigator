# Document Processing System

A Supabase-based document processing system that handles document uploads, parsing, and vectorization.

## Architecture

The system consists of several Edge Functions that work together to process documents:

1. `job-processor`: Main entry point that handles document uploads and orchestrates the processing pipeline
2. `doc-parser`: Parses uploaded documents and extracts text content
3. `vector-processor`: Converts parsed text into vector embeddings for semantic search

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
# Supabase project URL
export SUPABASE_URL=your_project_url
# Supabase service role key (for admin operations)
export SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
# Supabase anon key (for client operations)
export SUPABASE_ANON_KEY=your_anon_key
```

3. Deploy Edge Functions:
```bash
supabase functions deploy job-processor
supabase functions deploy doc-parser
supabase functions deploy vector-processor
```

4. Apply database migrations:
```bash
supabase db reset
```

## Testing

1. Run the test script:
```bash
npm run test:job-processor
```

This will:
- Create a test user
- Upload a test document
- Monitor the processing pipeline
- Report success/failure

## Database Schema

### Documents Table
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key to auth.users)
- `original_filename`: TEXT
- `content_type`: TEXT
- `file_size`: BIGINT
- `storage_path`: TEXT
- `status`: TEXT
- `metadata`: JSONB

### Jobs Table
- `id`: UUID (primary key)
- `document_id`: UUID (foreign key to documents)
- `status`: TEXT
- `error_message`: TEXT
- `error_details`: JSONB
- `metadata`: JSONB

## Error Handling

The system handles various types of errors:
- Upload failures
- Parsing errors
- Vectorization failures

Each error is properly logged with:
- Error message
- Error details
- Job status updates
- Document status updates

## Security

The system implements:
- Row Level Security (RLS) policies
- User-based access control
- Secure file storage
- Service role authentication for internal operations 

A Supabase-based document processing system that handles document uploads, parsing, and vectorization.

## Architecture

The system consists of several Edge Functions that work together to process documents:

1. `job-processor`: Main entry point that handles document uploads and orchestrates the processing pipeline
2. `doc-parser`: Parses uploaded documents and extracts text content
3. `vector-processor`: Converts parsed text into vector embeddings for semantic search

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
# Supabase project URL
export SUPABASE_URL=your_project_url
# Supabase service role key (for admin operations)
export SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
# Supabase anon key (for client operations)
export SUPABASE_ANON_KEY=your_anon_key
```

3. Deploy Edge Functions:
```bash
supabase functions deploy job-processor
supabase functions deploy doc-parser
supabase functions deploy vector-processor
```

4. Apply database migrations:
```bash
supabase db reset
```

## Testing

1. Run the test script:
```bash
npm run test:job-processor
```

This will:
- Create a test user
- Upload a test document
- Monitor the processing pipeline
- Report success/failure

## Database Schema

### Documents Table
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key to auth.users)
- `original_filename`: TEXT
- `content_type`: TEXT
- `file_size`: BIGINT
- `storage_path`: TEXT
- `status`: TEXT
- `metadata`: JSONB

### Jobs Table
- `id`: UUID (primary key)
- `document_id`: UUID (foreign key to documents)
- `status`: TEXT
- `error_message`: TEXT
- `error_details`: JSONB
- `metadata`: JSONB

## Error Handling

The system handles various types of errors:
- Upload failures
- Parsing errors
- Vectorization failures

Each error is properly logged with:
- Error message
- Error details
- Job status updates
- Document status updates

## Security

The system implements:
- Row Level Security (RLS) policies
- User-based access control
- Secure file storage
- Service role authentication for internal operations 