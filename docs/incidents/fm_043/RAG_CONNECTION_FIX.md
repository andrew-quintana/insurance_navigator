# RAG Database Connection Fix

**Date**: 2025-11-13  
**Issue**: RAG returning 0 chunks due to `ConnectionRefusedError: [Errno 111] Connection refused`

## Root Cause Analysis

The RAG database manager is trying to connect to `localhost:54322` instead of `host.docker.internal:54322`. This happens because:

1. **Environment variable not loaded**: The container was started before `.env.development` was updated, so it's using old/cached values
2. **Wrong hostname**: The database manager parsed `DATABASE_URL_LOCAL` and extracted `localhost` instead of `host.docker.internal`
3. **Container networking**: Docker containers cannot access `localhost` on the host - they need `host.docker.internal`

## Error Logs

```
2025-11-13 20:09:02,190 - agents.tooling.rag.database_manager - INFO - Using local connection (SSL disabled) for host: localhost
2025-11-13 20:09:02,190 - agents.tooling.rag.database_manager - INFO - Connecting to database: postgres@localhost:54322/postgres
2025-11-13 20:09:02,191 - agents.tooling.rag.database_manager - WARNING - Failed to parse database URL, trying direct connection string: [Errno 111] Connection refused
ConnectionRefusedError: [Errno 111] Connection refused
```

## Solution

**Restart the containers via Overmind** to pick up the updated `.env.development`:

```bash
overmind restart docker-services
```

This will:
1. Export all variables from `.env.development` (including `DATABASE_URL_LOCAL`)
2. Start containers with the correct environment
3. RAG will connect to `host.docker.internal:54322` instead of `localhost:54322`

## Verification

After restart, check logs:
```bash
docker logs insurance_navigator-api-1 | grep -E "DATABASE_URL_LOCAL|Connecting to database"
```

Should see:
```
Using local connection (SSL disabled) for host: host.docker.internal
Connecting to database: postgres@host.docker.internal:54322/postgres
Database pool initialized successfully
```

## Environment Variable Status

✅ **`.env.development`** has correct value:
```bash
DATABASE_URL_LOCAL=postgresql://postgres:postgres@host.docker.internal:54322/postgres
```

❌ **Container** is using old value (needs restart)

## Why Overmind is Required

The `Procfile` exports variables from `.env.development`:
```bash
docker-services: sh -c 'export $(cat .env.development | grep -v "^#" | xargs) && ...'
```

Running `docker-compose up` directly doesn't export these variables, so containers don't get the updated values.

## Next Steps

1. **Restart via Overmind**: `overmind restart docker-services`
2. **Verify connection**: Check logs for successful pool initialization
3. **Test RAG**: Make a query and verify chunks are returned (not 0)

