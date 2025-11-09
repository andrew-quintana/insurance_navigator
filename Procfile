# Overmind Procfile for Insurance Navigator Development Environment
# Services run with suppressed application logs by default (LOG_LEVEL=WARNING)
# Overmind system messages and service startup messages remain visible
# Use 'overmind logs <service>' to view individual service logs

# Supabase - Start local instance (manages own Docker containers)
# Must start first to create external network
# Always shows URLs after startup, then monitors
supabase: sh -c 'if supabase status >/dev/null 2>&1; then echo "✅ Supabase already running"; supabase status 2>/dev/null | head -15; echo "Monitoring..."; while supabase status >/dev/null 2>&1; do sleep 10; done; else if [ "${LOG_LEVEL:-WARNING}" = "WARNING" ]; then supabase start >/dev/null 2>&1; else supabase start; fi && echo "✅ Supabase started" && sleep 3 && echo "" && echo "📊 Supabase Services:" && supabase status 2>/dev/null | grep -E "(API URL|Database URL|Studio URL|GraphQL URL)" && echo "" && echo "Monitoring..."; while supabase status >/dev/null 2>&1; do sleep 10; done; fi'

# Docker Compose Services - Backend API and Worker
# Waits for Supabase network, then starts services
# Docker Compose startup messages visible, but service application logs suppressed
docker-services: sh -c 'export $(cat .env.development | grep -v "^#" | xargs) && export LOG_LEVEL="${LOG_LEVEL:-WARNING}" && export WORKER_LOG_LEVEL="${WORKER_LOG_LEVEL:-WARNING}" && until docker network inspect supabase_network_insurance_navigator >/dev/null 2>&1; do sleep 2; done && echo "✅ Starting Docker services (application logs suppressed - use '\''overmind logs docker-services'\'' to view)" && docker-compose up api worker'

# Frontend - Next.js Development Server (local for hot reload)
# Next.js startup messages visible, ongoing logs minimal
frontend: sh -c 'cd ui && [ -f ../.env.development ] && cp ../.env.development .env.local || true && echo "✅ Starting frontend..." && npm run dev'

