# FM-027 Test Suite

This directory contains tests related to FM-027: Worker Storage Access 400 Bad Request issue.

## Test Organization

### Core Tests (`tests/fm_027/`)
- `test_auth_matrix.py` - Authentication matrix testing across different contexts
- `test_storage_endpoint_fix.py` - Tests for corrected Supabase storage API endpoints
- `test_pipeline_standardization.py` - Tests for standardized path generation
- `test_worker_path_mismatch.py` - Tests for worker path access issues

### Debug Tests (`tests/debug/fm_027/`)
- `test_worker_storage_debug.py` - Worker storage configuration debugging
- `test_database_investigation.py` - Database investigation tests
- `test_flexible_webhook_config.py` - Webhook configuration tests

### Integration Tests (`tests/integration/fm_027/`)
- `test_staging_upload_simulation.py` - End-to-end staging environment tests

## Security Notes

All test files have been audited for sensitive information:
- ✅ No hardcoded service role keys
- ✅ No hardcoded JWT secrets
- ✅ No hardcoded API keys
- ✅ All sensitive data loaded from environment variables

## Running Tests

### Using the Makefile (Recommended)
```bash
# Run FM-027 reproduction harness
cd tests/fm_027/
make -f Makefile.fm027 repro-fm027

# Show help
make -f Makefile.fm027 help
```

### Using pytest directly
```bash
# Run all FM-027 tests
pytest tests/fm_027/ -v

# Run debug tests
pytest tests/debug/fm_027/ -v

# Run integration tests
pytest tests/integration/fm_027/ -v

# Run specific test
python tests/fm_027/test_auth_matrix.py
```

## Environment Requirements

Tests require the following environment variables:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `DATABASE_URL`

Load from `.env.staging` for staging environment tests.

