# Development Scripts

Scripts for managing the development environment.

## Development Environment

### Script Relationships

- **`dev-start.sh`** → Wrapper for `overmind start` (with prerequisites check)
- **`dev-stop.sh`** → Wrapper for `overmind stop` (with manual cleanup fallback)
- **`dev-cleanup.sh`** → Deep cleanup of stale containers/networks (run between sessions)

**Direct Overmind commands:**
- `overmind start` = `./scripts/dev-start.sh` (without prerequisites check)
- `overmind stop` = `./scripts/dev-stop.sh` (without manual cleanup)

### Usage

**Start services:**
```bash
./scripts/dev-start.sh              # Quiet mode (WARNING level) - minimal logs
./scripts/dev-start.sh --verbose    # Verbose mode (INFO level) - standard logs
./scripts/dev-start.sh --debug      # Debug mode (DEBUG level) - all logs
# or
overmind start

# Note: Use --cleanup flag with dev-stop.sh for cleanup
```

**Stop services:**
```bash
./scripts/dev-stop.sh           # Normal stop
./scripts/dev-stop.sh --cleanup # Stop with deep cleanup
# or
overmind stop
```

**Cleanup between sessions:**
```bash
# Option 1: Stop with cleanup flag
./scripts/dev-stop.sh --cleanup
./scripts/dev-start.sh

# Option 2: Stop, then cleanup separately
./scripts/dev-stop.sh
./scripts/dev-cleanup.sh
./scripts/dev-start.sh
```

**View logs:**
```bash
overmind logs
overmind logs frontend
overmind logs docker-services
overmind logs supabase
```

See [docs/environments/development/OVERMIND_SETUP.md](../../docs/environments/development/OVERMIND_SETUP.md) for complete documentation.

## Prerequisites

1. **Overmind**: `brew install overmind` (macOS) or see [Overmind installation](https://github.com/DarthSim/overmind#installation)
2. **Docker Desktop**: Running and accessible
3. **Supabase CLI**: `brew install supabase/tap/supabase` (macOS)
4. **Node.js** (v18+): For frontend development
5. **Environment file**: `.env.development` configured (copy from `config/env.development.example`)

## Services Started

- Supabase (local database)
- Docker Compose services (API + Worker)
- Frontend development server
