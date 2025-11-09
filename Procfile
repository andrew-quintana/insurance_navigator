# Overmind Procfile for Insurance Navigator Development Environment
# All services run in foreground for unified logging via Overmind

# Supabase - Start local instance (manages own Docker containers)
# Must start first to create external network
supabase: supabase start

# Docker Compose Services - Backend API and Worker (foreground for logging)
# Connects to supabase_network_insurance_navigator network created by Supabase
docker-services: sh -c 'export $(cat .env.development | grep -v "^#" | xargs) && docker-compose up api worker'

# Frontend - Next.js Development Server (local for hot reload)
# Copies .env.development to .env.local if needed, then starts dev server
frontend: sh -c 'cd ui && [ -f .env.development ] && cp .env.development .env.local || true && npm run dev'

