# API Startup Fix Summary

**Date**: 2025-11-13  
**Issue**: API failing to start with "role 'postgres' does not exist" error

## Root Cause

The `core/database.py` was parsing `DATABASE_URL` but the port was being lost during parsing, defaulting to 5432 instead of 54322. This caused the API to try connecting to the wrong port, resulting in authentication errors.

## Solution

Updated `.env.development` to use port **54322** (Supabase's database port) instead of 5432:

```bash
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:54322/postgres
DATABASE_URL_LOCAL=postgresql://postgres:postgres@host.docker.internal:54322/postgres
```

## Current Status

✅ **API Startup**: Successfully starting  
✅ **Core Database Pool**: Initialized with 5-20 connections  
✅ **Port**: Now correctly using 54322  

## Important Note

**DATABASE_URL_LOCAL must be set** for RAG to work. The RAG database manager checks this first.

## Next Steps

1. **Restart via Overmind** (not docker-compose directly):
   ```bash
   overmind restart docker-services
   ```
   
   This ensures `.env.development` variables are properly exported.

2. **Verify RAG is working**:
   - Make a test query
   - Check logs for "Found X total chunks for user Y"
   - Should see chunks returned instead of 0

3. **Monitor logs**:
   ```bash
   docker logs insurance_navigator-api-1 -f | grep -i "rag\|chunks\|database"
   ```

## Environment Variables Summary

### Backend (Docker containers) - Use `host.docker.internal`:
- `DATABASE_URL_LOCAL` (CRITICAL for RAG)
- `DATABASE_URL`
- `SUPABASE_URL`

### Frontend (Host machine) - Use `localhost`:
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- All other `NEXT_PUBLIC_*` variables

