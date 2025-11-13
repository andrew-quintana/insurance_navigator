# Docker Network Connection Fix

**Date**: 2025-11-13  
**Issue**: Using `host.docker.internal` for database connection when both services are on the same Docker network

## Root Cause

The API and Supabase database are both running in Docker containers on the same network (`supabase_network_insurance_navigator`). When containers are on the same Docker network, they should connect directly using the container name, not via `host.docker.internal`.

## The Problem

- **Wrong**: `postgresql://postgres:postgres@host.docker.internal:54322/postgres`
  - This tries to go through the host machine
  - Port 54322 is the host-mapped port
  - Adds unnecessary network hop

- **Correct**: `postgresql://postgres:postgres@supabase_db_insurance_navigator:5432/postgres`
  - Direct container-to-container connection
  - Uses internal port 5432 (not host-mapped 54322)
  - Faster and more reliable

## Supabase Container Details

From `supabase status`:
- **Container name**: `supabase_db_insurance_navigator`
- **Internal port**: `5432` (PostgreSQL default)
- **Host-mapped port**: `54322` (for host access)
- **Network**: `supabase_network_insurance_navigator`

## Changes Made

### 1. `.env.development`
```bash
# Before
# ⚠️ NOTE: "postgres:postgres" is the default local dev password - safe for local only
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:54322/postgres
DATABASE_URL_LOCAL=postgresql://postgres:postgres@host.docker.internal:54322/postgres

# After
# ⚠️ NOTE: "postgres:postgres" is the default local dev password - safe for local only
DATABASE_URL=postgresql://postgres:postgres@supabase_db_insurance_navigator:5432/postgres
DATABASE_URL_LOCAL=postgresql://postgres:postgres@supabase_db_insurance_navigator:5432/postgres
```

### 2. `docker-compose.yml`
```yaml
# Before
- DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:54322/postgres

# After
- DATABASE_URL=postgresql://postgres:postgres@supabase_db_insurance_navigator:5432/postgres
```

## Why This Works

1. **Same Docker Network**: Both containers are on `supabase_network_insurance_navigator`
2. **Container Name Resolution**: Docker's internal DNS resolves `supabase_db_insurance_navigator` to the container's IP
3. **Direct Connection**: No need to go through host networking
4. **Internal Port**: Use 5432 (container's internal port), not 54322 (host-mapped port)

## When to Use Each

### Use Container Name (Same Network):
- ✅ API container → Supabase database container
- ✅ Worker container → Supabase database container
- ✅ Any container-to-container communication on same network

### Use `host.docker.internal` (Host Access):
- ✅ Docker container → Service running on host machine (not in Docker)
- ✅ Frontend (host) → Supabase API (Docker) - but frontend uses `localhost` anyway

### Use `localhost` (Host Only):
- ✅ Frontend (Next.js on host) → Supabase API
- ✅ Frontend → Backend API
- ✅ Any host-to-host communication

## Next Steps

1. **Restart containers** to apply changes:
   ```bash
   overmind restart docker-services
   ```

2. **Verify connection**:
   ```bash
   docker logs insurance_navigator-api-1 | grep -E "Database pool initialized|Connecting to database"
   ```

3. **Test RAG** - should now connect successfully and return chunks

