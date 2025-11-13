# Frontend Environment Variable Fix

**Date**: 2025-11-13  
**Issue**: Frontend cannot access Supabase - "A server with the specified hostname could not be found"

## Root Cause

The frontend (Next.js) runs on the **host machine** (not in Docker), but was trying to access Supabase using `host.docker.internal:54321`. The `host.docker.internal` hostname only works **inside Docker containers** to access the host machine.

## Solution

Updated `NEXT_PUBLIC_SUPABASE_URL` in `.env.development` from:
```bash
NEXT_PUBLIC_SUPABASE_URL=http://host.docker.internal:54321  # ❌ Wrong for frontend
```

To:
```bash
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321  # ✅ Correct for frontend
```

## Environment Variable Rules

### Frontend (Host Machine) - Use `localhost`:
- `NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- All other `NEXT_PUBLIC_*` variables

### Backend (Docker Containers) - Use `host.docker.internal`:
- `DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:54322/postgres`
- `DATABASE_URL_LOCAL=postgresql://postgres:postgres@host.docker.internal:54322/postgres`
- `SUPABASE_URL=http://host.docker.internal:54321`

## Why This Matters

- **Frontend** (Next.js dev server) runs on the host machine → uses `localhost`
- **Backend** (API, Worker) run in Docker containers → use `host.docker.internal` to access host services
- **Supabase** runs on the host machine (via `supabase start`)

## Next Steps

1. **Restart the frontend** to pick up the new environment variable:
   ```bash
   overmind restart frontend
   ```
   
   Or if running manually:
   ```bash
   cd ui && npm run dev
   ```

2. **Verify the fix**:
   - Open browser DevTools → Network tab
   - Try to log in
   - Should see successful requests to `http://localhost:54321/auth/v1/token`
   - No more "hostname could not be found" errors

## Related Files

- `.env.development` - Main environment file (used by Procfile)
- `ui/.env.local` - Frontend-specific env (created by Procfile from `.env.development`)
- `ui/lib/supabase-client.ts` - Supabase client initialization

