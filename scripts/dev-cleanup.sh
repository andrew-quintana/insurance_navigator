#!/bin/bash
# ========== DEVELOPMENT ENVIRONMENT CLEANUP ==========
# Cleans up stale containers, networks, and processes between dev sessions
# Typically called from dev-stop.sh --cleanup, but can be run standalone

set -e

echo "🧹 Cleaning Up Development Environment"
echo "======================================="

# Stop Overmind if still running (may have already been stopped by dev-stop.sh)
if [ -S ./.overmind.sock ] || pgrep -f "overmind" > /dev/null 2>&1; then
    echo "Stopping Overmind..."
    overmind stop 2>/dev/null || true
fi

# Stop Docker Compose services
echo "Cleaning up Docker Compose services..."
docker-compose down --remove-orphans 2>/dev/null || true

# Remove any stuck containers
echo "Removing stale containers..."
docker ps -a --filter "name=insurance_navigator" --format "{{.ID}}" | xargs docker rm -f 2>/dev/null || true

# Remove any Supabase containers that might be stuck
echo "Removing stale Supabase containers..."
docker ps -a --filter "name=supabase_insurance_navigator" --format "{{.ID}}" | xargs docker rm -f 2>/dev/null || true

# Prune unused networks (this will remove networks not in use)
echo "Pruning unused Docker networks..."
docker network prune -f

# Stop Supabase if running
if supabase status >/dev/null 2>&1; then
    echo "Stopping Supabase..."
    supabase stop 2>/dev/null || true
fi

# Kill any remaining frontend processes
if pgrep -f "npm run dev" > /dev/null 2>&1; then
    echo "Stopping frontend processes..."
    pkill -f "npm run dev" 2>/dev/null || true
fi

# Clean up Overmind socket files
if [ -S ./.overmind.sock ]; then
    echo "Removing Overmind socket..."
    rm -f ./.overmind.sock
fi

if [ -f ./.overmind.pid ]; then
    echo "Removing Overmind PID file..."
    rm -f ./.overmind.pid
fi

echo ""
echo "✅ Cleanup complete! Ready for fresh start."

