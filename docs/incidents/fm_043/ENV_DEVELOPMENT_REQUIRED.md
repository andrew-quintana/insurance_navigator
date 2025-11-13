# Required .env.development Variables

**Date**: 2025-11-13  
**Based on**: docker-compose.yml, Procfile, and running container analysis

## Critical Variables for RAG Database Connection

Based on the logs and configuration, here are the **exact values** your `.env.development` should have:

### Database Configuration (CRITICAL for RAG)

```bash
# Primary database URL (used by docker-compose.yml)
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:54322/postgres

# RAG Database Manager looks for this FIRST - MUST be set!
DATABASE_URL_LOCAL=postgresql://postgres:postgres@host.docker.internal:54322/postgres

# Database schema
DATABASE_SCHEMA=upload_pipeline
```

**Important**: The RAG database manager checks `DATABASE_URL_LOCAL` first, then falls back to `DATABASE_URL`. Since docker-compose hardcodes `DATABASE_URL`, you **must** set `DATABASE_URL_LOCAL` for RAG to work.

### Supabase Configuration

```bash
# Supabase API URL (from: supabase status)
SUPABASE_URL=http://host.docker.internal:54321

# Supabase Keys (from: supabase status)
# ⚠️ SECURITY NOTE: These are DEFAULT LOCAL DEVELOPMENT DEMO KEYS
# These keys are publicly documented by Supabase and ONLY work for local dev instances
# They are SAFE to commit as they cannot access production data
# For production, use your actual Supabase project keys from the Supabase dashboard
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0

SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
```

**Note**: Get current values with: `supabase status`

### Required API Keys

```bash
# These are required - get from your accounts
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LLAMAPARSE_API_KEY=your_llamaparse_api_key_here
RESEND_API_KEY=your_resend_api_key_here
```

### Security Keys

```bash
# Generate secure random strings for these
JWT_SECRET=your_jwt_secret_here
DOCUMENT_ENCRYPTION_KEY=your_document_encryption_key_here
```

### Environment & Logging

```bash
ENVIRONMENT=development
LOG_LEVEL=INFO
WORKER_LOG_LEVEL=INFO
```

## Complete .env.development Template

```bash
# Environment
ENVIRONMENT=development

# Database Configuration (CRITICAL - RAG needs DATABASE_URL_LOCAL)
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:54322/postgres
DATABASE_URL_LOCAL=postgresql://postgres:postgres@host.docker.internal:54322/postgres
DATABASE_SCHEMA=upload_pipeline

# Supabase Configuration
# ⚠️ SECURITY NOTE: Demo keys below are SAFE for local development only
SUPABASE_URL=http://host.docker.internal:54321
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LLAMAPARSE_API_KEY=your_llamaparse_api_key_here
RESEND_API_KEY=your_resend_api_key_here

# Security
JWT_SECRET=your_jwt_secret_here
DOCUMENT_ENCRYPTION_KEY=your_document_encryption_key_here

# Logging
LOG_LEVEL=INFO
WORKER_LOG_LEVEL=INFO
```

## Key Points

1. **DATABASE_URL_LOCAL is CRITICAL**: The RAG database manager checks this first. Without it, RAG will fail to connect.

2. **Use `host.docker.internal`**: This is the Docker hostname that allows containers to access services on the host machine (like Supabase running locally).

3. **Port 54322**: This is Supabase's database port (not the standard 5432).

4. **Port 54321**: This is Supabase's API/Kong port.

5. **Get current Supabase values**: Run `supabase status` to get the latest keys if they've changed.

## Verification

After updating `.env.development`, restart the services:

```bash
overmind restart docker-services
```

Then check logs:
```bash
docker logs insurance_navigator-api-1 | grep "Database pool"
```

You should see: "Database pool initialized successfully"

