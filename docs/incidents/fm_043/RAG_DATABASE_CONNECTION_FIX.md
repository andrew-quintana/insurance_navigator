# RAG Database Connection Fix

**Date**: 2025-11-13  
**Related**: FM-043 Concurrency Remediation  
**Issue**: RAG responses failing with "Connection refused" error

## Root Cause

The database connection pool was failing to initialize with error:
```
[Errno 111] Connection refused
```

### Analysis

1. **Connection String Format Issue**: The `DATABASE_URL` uses `host.docker.internal:54322`, which asyncpg's `create_pool()` doesn't handle correctly when passed as a connection string.

2. **Missing SSL Configuration**: Local connections need SSL disabled, but the code wasn't setting this.

3. **Connection String Parsing**: asyncpg works better with individual connection parameters rather than connection strings when dealing with Docker networking.

## Solution

### Changes Made

1. **Added Connection String Parser** (`_parse_database_url` method):
   - Parses PostgreSQL connection URLs into individual components
   - Handles `host.docker.internal` correctly

2. **Use Individual Parameters**:
   - Instead of passing the connection string directly to `asyncpg.create_pool()`, we now parse it and pass individual parameters (`host`, `port`, `user`, `password`, `database`)
   - This ensures `host.docker.internal` is resolved correctly by Docker

3. **SSL Mode Configuration**:
   - Automatically detects local vs production connections
   - Disables SSL for local connections (`host.docker.internal`, `localhost`, `127.0.0.1`)
   - Requires SSL for production Supabase connections

4. **Enhanced Error Logging**:
   - Added detailed logging for connection attempts
   - Logs connection parameters (with password masked)
   - Full traceback on connection failures

### Code Changes

**File**: `agents/tooling/rag/database_manager.py`

- Added `_parse_database_url()` method to parse connection strings
- Modified `initialize()` to:
  - Parse connection string into components
  - Use individual parameters for `create_pool()`
  - Configure SSL mode based on host
  - Add fallback to direct connection string if parsing fails

## Testing

After restarting the API container, check logs for:
- "Database pool initialized successfully"
- "Connecting to database: postgres@host.docker.internal:54322/postgres"
- No "Connection refused" errors

## Verification

1. **Check Database Pool Initialization**:
   ```bash
   docker logs insurance_navigator-api-1 | grep "Database pool"
   ```

2. **Test RAG Query**:
   - Make a query that should retrieve documents
   - Check logs for "Found X total chunks for user Y"
   - Verify chunks are returned instead of empty list

3. **Monitor for Errors**:
   ```bash
   docker logs insurance_navigator-api-1 -f | grep -i "error\|connection"
   ```

## Related Issues

- FM-043: Concurrency Remediation introduced connection pooling
- The pooling implementation needed proper handling of Docker networking

## Next Steps

1. Monitor production logs to ensure connections are stable
2. Consider adding connection retry logic for transient failures
3. Add health checks for the database pool

