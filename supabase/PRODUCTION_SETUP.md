# Supabase Production Instance Setup Guide

## Overview

This guide explains how to configure and manage the Supabase production instance (`insurance-navigator-production`) using environment variables and automated configuration loading.

## Project Details

- **Project ID**: `mrbigmtnadjtyepxqefa`
- **Project Name**: `insurance-navigator-production`
- **Organization ID**: `olcuvzctdaqfqgwidwrp`
- **Region**: West US (North California)
- **Database Host**: `db.mrbigmtnadjtyepxqefa.supabase.co`
- **API URL**: `https://mrbigmtnadjtyepxqefa.supabase.co`

## Configuration System

### 1. Template Configuration

The `production.config.json` file contains a template with environment variable placeholders:

```json
{
  "project_id": "${SUPABASE_PROJECT_ID}",
  "database": {
    "host": "${DATABASE_HOST}",
    "password": "${DATABASE_PASSWORD}"
  }
}
```

### 2. Environment Variables

All configuration values are loaded from environment variables. **All variables are required** - the system will fail fast if any are missing:

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_PROJECT_ID` | ✅ | Supabase project identifier |
| `DATABASE_HOST` | ✅ | Database hostname |
| `SITE_URL` | ✅ | Application URL |
| `STORAGE_BUCKET_NAME` | ✅ | Storage bucket name |
| `DATABASE_PASSWORD` | ✅ | Database password (sensitive) |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Supabase service role key (sensitive) |

### 3. Configuration Loading

Use the provided script to generate a resolved configuration. **The system will fail if any required environment variables are missing:**

```bash
cd supabase/
./load_production_config.sh
```

This creates `production.config.resolved.json` with all environment variables substituted.

**Error Handling**: If any required environment variables are missing, the script will:
- List all missing variables
- Provide helpful error messages
- Exit with status code 1
- Show example usage

## API Keys

### Current Production Keys

- **Anon Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yYmlnbXRuYWRqdHllcHhxZWZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5NTA1NTIsImV4cCI6MjA3NTUyNjU1Mn0.PTDSvO868CTav2ArHMIfwqXw0RJDzS7-LuUuP1nKNxI`
- **Service Role Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yYmlnbXRuYWRqdHllcHhxZWZhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTk1MDU1MiwiZXhwIjoyMDc1NTI2NTUyfQ.QVhRPZmpdaeL13qnqifig64I-1izTaPMqovni_2hcgY`

### Getting Fresh Keys

```bash
supabase projects api-keys --project-ref mrbigmtnadjtyepxqefa
```

## Database Configuration

### Connection Details

- **Host**: `db.mrbigmtnadjtyepxqefa.supabase.co`
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `postgres`
- **Password**: `[REQUIRED - Set DATABASE_PASSWORD env var]`

### Connection URLs

- **Direct**: `postgresql://postgres:[PASSWORD]@db.mrbigmtnadjtyepxqefa.supabase.co:5432/postgres`
- **Pooler**: `postgresql://postgres.mrbigmtnadjtyepxqefa:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres`
- **Session Pooler**: `postgresql://postgres.mrbigmtnadjtyepxqefa:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:5432/postgres`

## Storage Configuration

### Bucket: `insurance_documents_prod`

- **Public**: `false` (private bucket)
- **File Size Limit**: `100MB` (104857600 bytes)
- **Allowed MIME Types**:
  - `application/pdf`
  - `application/msword`
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  - `text/plain`
  - `application/rtf`

## Authentication Configuration

### Settings

- **Site URL**: `https://insurance-navigator.vercel.app`
- **Redirect URLs**:
  - `https://insurance-navigator.vercel.app/auth/callback`
  - `https://insurance-navigator.vercel.app/dashboard`
- **JWT Expiry**: `3600` seconds (1 hour)
- **Refresh Token Rotation**: `enabled`
- **Secure Password Change**: `enabled`

## Security Features

### Row Level Security (RLS)

- **Enabled**: `true` on all tables
- **Audit Logging**: `true`
- **Encryption at Rest**: `true`
- **Encryption in Transit**: `true`

### Compliance

- **HIPAA**: `enabled`
- **GDPR**: `enabled`
- **Audit Trail**: `enabled`

## Monitoring & Backups

### Monitoring

- **Metrics Retention**: `30` days
- **Log Retention**: `7` days

### Backups

- **Schedule**: `0 2 * * *` (daily at 2 AM)
- **Retention**: `30` days

## Usage Examples

### 1. Load Configuration

```bash
# Load with default values
./load_production_config.sh

# Load with custom values
export DATABASE_PASSWORD="your-password"
export SITE_URL="https://your-custom-domain.com"
./load_production_config.sh
```

### 2. Connect to Database

```bash
# Using psql
psql "postgresql://postgres:your-password@db.mrbigmtnadjtyepxqefa.supabase.co:5432/postgres"

# Using Supabase CLI
supabase db remote commit --project-ref mrbigmtnadjtyepxqefa
```

### 3. Check Project Status

```bash
supabase projects list --output json | jq '.[] | select(.id == "mrbigmtnadjtyepxqefa")'
```

## Environment Variables Reference

### Required Variables

**All of these variables must be set before running the configuration loader:**

```bash
# Supabase Project Details
export SUPABASE_PROJECT_ID="mrbigmtnadjtyepxqefa"
export SUPABASE_ORG_ID="olcuvzctdaqfqgwidwrp"

# Database Configuration
export DATABASE_HOST="db.mrbigmtnadjtyepxqefa.supabase.co"
export DATABASE_PORT="5432"
export DATABASE_NAME="postgres"
export DATABASE_USER="postgres"
export DATABASE_PASSWORD="your-database-password"
export DATABASE_MAX_CONNECTIONS="100"
export DATABASE_POOL_SIZE="20"

# Authentication
export SITE_URL="https://insurance-navigator.vercel.app"
export ADDITIONAL_REDIRECT_URLS="https://insurance-navigator.vercel.app/auth/callback,https://insurance-navigator.vercel.app/dashboard"
export JWT_EXPIRY="3600"

# Storage
export STORAGE_BUCKET_NAME="insurance_documents_prod"
export STORAGE_FILE_SIZE_LIMIT="104857600"
export STORAGE_ALLOWED_MIME_TYPES="application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,application/rtf"

# Supabase API Keys
export SUPABASE_URL="https://mrbigmtnadjtyepxqefa.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Additional API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export LLAMAPARSE_API_KEY="your-llamaparse-key"
export RESEND_API_KEY="your-resend-key"
```

**Note**: There are no optional variables - all environment variables are required for production configuration.

## Troubleshooting

### Common Issues

1. **Docker not running**: Some Supabase CLI commands require Docker
2. **Invalid project reference**: Ensure you're linked to the correct project
3. **Authentication failed**: Check API keys and database password

### Verification Commands

```bash
# Check project status
supabase projects list

# Verify API keys
supabase projects api-keys --project-ref mrbigmtnadjtyepxqefa

# Test database connection
psql "postgresql://postgres:password@db.mrbigmtnadjtyepxqefa.supabase.co:5432/postgres" -c "SELECT version();"
```

## Next Steps

1. Set the `DATABASE_PASSWORD` environment variable
2. Configure additional API keys as needed
3. Test all services and endpoints
4. Set up monitoring and alerting
5. Configure CI/CD pipelines with production environment

---

**Note**: Never commit actual passwords or API keys to version control. Use environment variables or secure secret management systems.
