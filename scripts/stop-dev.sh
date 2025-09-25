#!/bin/bash
# ========== STOP DEVELOPMENT ENVIRONMENT ==========

set -e

echo "🛑 Stopping Development Environment"
echo "=================================="

# Stop ngrok if running
if [ -f .ngrok.pid ]; then
    NGROK_PID=$(cat .ngrok.pid)
    if ps -p $NGROK_PID > /dev/null 2>&1; then
        echo "🛑 Stopping ngrok (PID: $NGROK_PID)..."
        kill $NGROK_PID
        rm .ngrok.pid
    else
        echo "ℹ️  Ngrok process not found"
        rm .ngrok.pid
    fi
else
    echo "ℹ️  No ngrok PID file found"
fi

# Stop Docker services
echo "🛑 Stopping Docker services..."
docker-compose down

# Stop Supabase
echo "🛑 Stopping Supabase..."
supabase stop

# Kill any remaining processes
echo "🛑 Cleaning up remaining processes..."
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "python main.py" 2>/dev/null || true
pkill -f "enhanced_runner.py" 2>/dev/null || true

echo "✅ Development environment stopped!"
