# Overmind Development Environment Setup

This guide explains how to set up and use Overmind to manage the Insurance Navigator development environment.

## What is Overmind?

Overmind is a process manager that orchestrates multiple services with unified logging and process management.

## Prerequisites

Before setting up Overmind, ensure you have the following installed:

1. **Docker Desktop** - Running and accessible
2. **Supabase CLI** - For local database management
3. **Node.js** (v18+) - For frontend development
4. **npm** - Node package manager
5. **Overmind** - Process manager

## Installation

### Install Overmind

**macOS:**
```bash
brew install overmind
```

**Linux:**
```bash
# Using Go (recommended)
go install github.com/DarthSim/overmind/v2@latest

# Or download binary from releases
# https://github.com/DarthSim/overmind/releases
```

**Verify installation:**
```bash
overmind --version
```

### Install Other Prerequisites

**Supabase CLI:**
```bash
# macOS
brew install supabase/tap/supabase

# Linux / Other
# See: https://supabase.com/docs/guides/cli
```

**Docker Desktop:**
- Download from [docker.com](https://www.docker.com/products/docker-desktop)
- Ensure Docker Desktop is running before starting services

## Configuration

### Environment Variables

1. Copy the example environment file:
   ```bash
   cp config/env.development.example .env.development
   ```

2. Fill in your actual values in `.env.development`:
   - API keys (OpenAI, Anthropic, etc.)
   - Supabase credentials
   - Database configuration

### Procfile

The `Procfile` defines all services managed by Overmind:

- **supabase**: Starts local Supabase instance
- **docker-services**: Starts backend API and worker via Docker Compose
- **frontend**: Starts Next.js development server locally

No configuration needed - the Procfile is already set up in the repository root.

## Usage

### Starting All Services

**Option 1: Direct Overmind command**
```bash
overmind start
```

**Option 2: Convenience wrapper script**
```bash
./scripts/dev-start.sh
```

This will:
1. Check all prerequisites
2. Start Supabase (creates database network)
3. Start Docker Compose services (API + Worker)
4. Start frontend development server

### Stopping All Services

**Option 1: Direct Overmind command**
```bash
overmind stop
```

**Option 2: Convenience wrapper script**
```bash
./scripts/dev-stop.sh
```

### Viewing Logs

**All services (unified view):**
```bash
overmind logs
```

**Specific service:**
```bash
overmind logs supabase
overmind logs docker-services
overmind logs frontend
```

**Follow logs (real-time):**
```bash
overmind logs -f
```

### Managing Individual Services

**Start a specific service:**
```bash
overmind start supabase
overmind start docker-services
overmind start frontend
```

**Stop a specific service:**
```bash
overmind stop supabase
overmind stop docker-services
overmind stop frontend
```

**Restart a specific service:**
```bash
overmind restart supabase
overmind restart docker-services
overmind restart frontend
```

**Check service status:**
```bash
overmind status
```

## Service URLs

Once all services are started, access them at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Supabase API**: http://127.0.0.1:54321
- **Supabase Studio**: http://127.0.0.1:54323

## Service Dependencies

Services start in the following order (Overmind handles this automatically):

1. **Supabase** - Must start first (creates network)
2. **Docker Services** - Can start after Supabase (connects to network)
3. **Frontend** - Can start after API is ready

## Troubleshooting

### Overmind not found

```bash
# Verify installation
which overmind

# Reinstall if needed
brew reinstall overmind  # macOS
```

### Docker not running

```bash
# Check Docker status
docker info

# Start Docker Desktop if needed
# (macOS: Open Docker Desktop app)
```

### Port conflicts

If ports are already in use:

```bash
# Check what's using the port
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :54321 # Supabase

# Stop conflicting processes
# Or change ports in docker-compose.yml / Procfile
```

### Supabase network not found

If Docker services fail to connect to Supabase network:

```bash
# Ensure Supabase is started first
overmind start supabase

# Wait a few seconds, then start Docker services
overmind start docker-services
```

### Frontend not starting

```bash
# Check if .env.local exists
ls ui/.env.local

# If not, ensure .env.development exists in ui/ directory
# The Procfile will copy it automatically
```

### Services not stopping cleanly

```bash
# Force stop Overmind
overmind kill

# Manual cleanup if needed
docker-compose down
supabase stop
pkill -f "npm run dev"
```

### Environment variables not loading

Ensure `.env.development` exists in the project root:

```bash
# Check if file exists
ls -la .env.development

# Verify it's not empty
cat .env.development | grep -v "^#" | grep -v "^$"
```

### Docker Compose services not starting

```bash
# Check Docker Compose logs
docker-compose logs api
docker-compose logs worker

# Rebuild if needed
docker-compose build api worker
```

## Advanced Usage

### Custom Overmind Configuration

Create `.overmind.env` in the project root to set custom environment variables:

```bash
# .overmind.env
CUSTOM_VAR=value
```

### Running Services in Different Terminals

You can run Overmind in different modes:

```bash
# Start in background
overmind start -D

# Connect to running session
overmind connect
```

### Process Scaling

Overmind supports scaling processes (though not needed for this setup):

```bash
overmind scale docker-services=2
```

## Best Practices

1. **Always stop services cleanly**: Use `overmind stop` instead of Ctrl+C when possible
2. **Check prerequisites**: Run `./scripts/dev-start.sh` to validate setup
3. **Monitor logs**: Use `overmind logs -f` to watch for errors
4. **Start Supabase first**: If starting services individually, start Supabase before Docker services
5. **Keep .env.development updated**: Ensure all required environment variables are set

## Additional Resources

- [Overmind Documentation](https://github.com/DarthSim/overmind)
- [Supabase CLI Documentation](https://supabase.com/docs/guides/cli)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review service logs: `overmind logs`
3. Verify prerequisites are installed and running
4. Check that `.env.development` is properly configured
5. Ensure no port conflicts exist

