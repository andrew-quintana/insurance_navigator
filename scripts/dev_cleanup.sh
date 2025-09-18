#!/bin/bash

# Development Environment Cleanup Script
# Stops ngrok and cleans up development processes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🧹 Starting Development Environment Cleanup..."

# Stop ngrok if running
if [ -f "/tmp/ngrok.pid" ]; then
    NGROK_PID=$(cat /tmp/ngrok.pid)
    if kill -0 $NGROK_PID 2>/dev/null; then
        print_status "Stopping ngrok (PID: $NGROK_PID)..."
        kill $NGROK_PID
        print_success "Ngrok stopped"
    else
        print_warning "Ngrok process not running"
    fi
    rm -f /tmp/ngrok.pid
else
    print_status "No ngrok PID file found, killing any ngrok processes..."
    pkill -f "ngrok" 2>/dev/null || true
fi

# Clean up log files
print_status "Cleaning up log files..."
rm -f /tmp/ngrok.log
rm -f logs/api_server.log
rm -f logs/enhanced_worker.log
rm -f logs/worker_service.log

# Restore backup files if they exist
print_status "Restoring backup files..."

if [ -f ".env.development.bak" ]; then
    mv .env.development.bak .env.development
    print_success "Restored .env.development"
fi

if [ -f "ui/.env.local.bak" ]; then
    mv ui/.env.local.bak ui/.env.local
    print_success "Restored ui/.env.local"
fi

if [ -f "backend/workers/enhanced_base_worker.py.bak" ]; then
    mv backend/workers/enhanced_base_worker.py.bak backend/workers/enhanced_base_worker.py
    print_success "Restored backend/workers/enhanced_base_worker.py"
fi

print_success "🎉 Development environment cleanup complete!"
echo ""
echo "📋 Cleaned up:"
echo "  • Ngrok processes"
echo "  • Log files"
echo "  • Configuration backups restored"
echo ""
echo "💡 To start development environment again:"
echo "  ./scripts/dev_setup.sh"
