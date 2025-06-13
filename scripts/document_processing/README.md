# Document Processing Scripts

This directory contains scripts related to document upload and processing functionality.

## Scripts

### Python Scripts
- `check-and-fix-jobs.py` - Diagnostic and repair tool for stuck document processing jobs
- `process-stuck-document.py` - Utility to manually process documents that are stuck in the pipeline
- `test-upload-and-monitor.py` - Test script for uploading documents and monitoring their processing

### Database Setup Scripts
The SQL setup scripts have been moved to `db/scripts/document_processing/`:
- `setup-cron-with-validation.sql` - Comprehensive cron job setup with validation and monitoring
- `setup-queue-management.sql` - Queue management system with triggers and health monitoring
- `cleanup-before-queue-setup.sql` - Cleanup script to prepare for new queue setup

## Usage

### Testing Document Upload
```bash
python scripts/document_processing/test-upload-and-monitor.py
```

### Checking for Stuck Jobs
```bash
python scripts/document_processing/check-and-fix-jobs.py
```

### Processing Stuck Documents
```bash
python scripts/document_processing/process-stuck-document.py
```

### Setting Up Database Components
```bash
# Run in order:
psql "$DATABASE_URL" -f db/scripts/document_processing/cleanup-before-queue-setup.sql
psql "$DATABASE_URL" -f db/scripts/document_processing/setup-queue-management.sql
psql "$DATABASE_URL" -f db/scripts/document_processing/setup-cron-with-validation.sql
```

## Dependencies

These scripts require:
- Python 3.8+
- `requests` library
- `psycopg2` or `asyncpg` for database operations
- Access to Supabase database and edge functions 