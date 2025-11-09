#!/bin/bash
# ========== DEVELOPMENT ENVIRONMENT STOPPER ==========
# Convenience wrapper for Overmind to stop development environment

set -e

echo "🛑 Stopping Development Environment"
echo "===================================="

# Check if Overmind is installed
if ! command -v overmind &> /dev/null; then
    echo "❌ Overmind is not installed."
    echo "   Services may still be running. Check manually:"
    echo "   - Docker: docker-compose ps"
    echo "   - Supabase: supabase status"
    echo "   - Frontend: ps aux | grep 'npm run dev'"
    exit 1
fi

# Stop Overmind (this stops all processes)
echo "Stopping all services..."
overmind stop

echo ""
echo "✅ Development environment stopped!"
echo ""
echo "Note: If services are still running, you may need to:"
echo "  - Stop Docker services: docker-compose down"
echo "  - Stop Supabase: supabase stop"
echo "  - Kill frontend: pkill -f 'npm run dev'"

