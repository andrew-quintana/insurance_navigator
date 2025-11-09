# Development Scripts

Scripts for managing the development environment.

## Development Environment

**Start services:**
```bash
./scripts/dev-start.sh
# or
overmind start
```

**Stop services:**
```bash
./scripts/dev-stop.sh
# or
overmind stop
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
