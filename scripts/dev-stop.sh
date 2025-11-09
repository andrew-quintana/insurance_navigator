#!/bin/bash
# ========== DEVELOPMENT ENVIRONMENT STOPPER ==========
# Convenience wrapper for Overmind to stop development environment
#
# Usage:
#   ./scripts/dev-stop.sh           # Stop services normally
#   ./scripts/dev-stop.sh --cleanup # Stop services and perform deep cleanup

set -e

# Parse arguments
CLEANUP_FLAG="false"

for arg in "$@"; do
    case $arg in
        --cleanup|-c)
            CLEANUP_FLAG="true"
            shift
            ;;
        *)
            # Unknown option
            ;;
    esac
done

echo "🛑 Stopping Development Environment"
echo "===================================="
if [ "${CLEANUP_FLAG}" = "true" ]; then
    echo "🧹 Cleanup mode: Will perform deep cleanup after stopping"
fi
echo ""

# Check if Overmind is installed
if ! command -v overmind &> /dev/null; then
    echo "❌ Overmind is not installed."
    echo "   Services may still be running. Check manually:"
    echo "   - Docker: docker-compose ps"
    echo "   - Supabase: supabase status"
    echo "   - Frontend: ps aux | grep 'npm run dev'"
    exit 1
fi

# Check if Overmind is running before trying to stop
if [ -S ./.overmind.sock ] || pgrep -f "overmind" > /dev/null 2>&1; then
    echo "Stopping all services..."
    overmind stop || true  # Don't fail if already stopped
else
    echo "ℹ️  Overmind is not running (nothing to stop)"
fi

# Clean up any remaining services manually
echo ""
echo "Cleaning up remaining services..."

# Stop Docker Compose services if running
if docker-compose ps 2>/dev/null | grep -q "Up"; then
    echo "  Stopping Docker services..."
    docker-compose down 2>/dev/null || true
fi

# Stop Supabase if running
if supabase status >/dev/null 2>&1; then
    echo "  Stopping Supabase..."
    supabase stop 2>/dev/null || true
fi

# Kill any remaining frontend processes
if pgrep -f "npm run dev" > /dev/null 2>&1; then
    echo "  Stopping frontend..."
    pkill -f "npm run dev" 2>/dev/null || true
fi

echo ""
echo "✅ Development environment stopped!"
# Perform deep cleanup if requested
if [ "${CLEANUP_FLAG}" = "true" ]; then
    echo ""
    "$(dirname "$0")/dev-cleanup.sh"
fi
