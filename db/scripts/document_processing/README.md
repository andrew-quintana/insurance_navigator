# Document Processing Database Setup

This directory contains SQL scripts for setting up the document processing pipeline in Supabase.

## Scripts

### Setup Scripts (Run in Order)
1. `cleanup-before-queue-setup.sql` - Cleans up any existing queue management components
2. `setup-queue-management.sql` - Sets up queue monitoring, triggers, and health checks
3. `setup-cron-with-validation.sql` - Sets up cron jobs with comprehensive validation and monitoring

## Features

### Queue Management (`setup-queue-management.sql`)
- Automatic job state transitions (pending → running → completed/failed)
- Job completion and failure triggers
- Queue health monitoring views
- Stuck job detection and retry logic

### Cron Jobs (`setup-cron-with-validation.sql`)
- Document processing job scheduler (every minute)
- Health monitoring (every 5 minutes)
- Cleanup jobs (daily at 2 AM)
- Comprehensive logging and error handling

### Cleanup (`cleanup-before-queue-setup.sql`)
- Removes old triggers and functions
- Handles permission errors gracefully
- Prepares database for fresh setup

## Usage

### Initial Setup
```bash
# 1. Clean up any existing components
psql "$DATABASE_URL" -f db/scripts/document_processing/cleanup-before-queue-setup.sql

# 2. Set up queue management
psql "$DATABASE_URL" -f db/scripts/document_processing/setup-queue-management.sql

# 3. Set up cron jobs and monitoring
psql "$DATABASE_URL" -f db/scripts/document_processing/setup-cron-with-validation.sql
```

### Monitoring
```sql
-- Check queue health
SELECT * FROM queue_health;

-- Check cron job status
SELECT * FROM cron_job_health;

-- View current job status
SELECT * FROM current_job_status;
```

## Requirements

- Supabase database with `pg_cron` and `pg_net` extensions enabled
- Service role key configured for cron jobs
- Edge functions deployed for job processing

## Security

- Scripts handle Supabase permission limitations gracefully
- Cron jobs require superuser privileges but fail safely if not available
- All operations use proper error handling and logging 