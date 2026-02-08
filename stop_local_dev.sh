#!/bin/bash

# Insurance Navigator - Stop Local Development Services
# =====================================================

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

echo "🛑 Insurance Navigator - Stopping Local Development Services"
echo "=============================================================="

# Stop backend API
print_info "Stopping backend API..."
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill $BACKEND_PID 2>/dev/null; then
        print_success "Backend API stopped (PID: $BACKEND_PID)"
    else
        print_warning "Backend API process not found (PID: $BACKEND_PID)"
    fi
    rm -f .backend.pid
else
    # Try to find and kill the process
    BACKEND_PIDS=$(pgrep -f "python.*main.py")
    if [ ! -z "$BACKEND_PIDS" ]; then
        echo $BACKEND_PIDS | xargs kill 2>/dev/null
        print_success "Backend API stopped"
    else
        print_info "Backend API not running"
    fi
fi

# Stop frontend
print_info "Stopping frontend..."
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend stopped (PID: $FRONTEND_PID)"
    else
        print_warning "Frontend process not found (PID: $FRONTEND_PID)"
    fi
    rm -f .frontend.pid
else
    # Try to find and kill Next.js processes on port 3000
    FRONTEND_PIDS=$(lsof -ti:3000)
    if [ ! -z "$FRONTEND_PIDS" ]; then
        echo $FRONTEND_PIDS | xargs kill 2>/dev/null
        print_success "Frontend stopped"
    else
        print_info "Frontend not running"
    fi
fi

# Stop Supabase
print_info "Stopping Supabase..."
if curl -s http://localhost:54321/health > /dev/null; then
    supabase stop
    print_success "Supabase stopped"
else
    print_info "Supabase not running"
fi

# Kill any remaining processes
print_info "Cleaning up remaining processes..."

# Kill any remaining Python processes
PYTHON_PIDS=$(pgrep -f "python.*insurance_navigator")
if [ ! -z "$PYTHON_PIDS" ]; then
    echo $PYTHON_PIDS | xargs kill 2>/dev/null
    print_info "Cleaned up remaining Python processes"
fi

# Kill any remaining Node processes on ports 3000
NODE_PIDS=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$NODE_PIDS" ]; then
    echo $NODE_PIDS | xargs kill 2>/dev/null
    print_info "Cleaned up remaining Node processes"
fi

# Clean up log files (optional)
if [ "$1" = "--clean-logs" ]; then
    print_info "Cleaning log files..."
    rm -f backend.log frontend.log supabase_start.log
    print_success "Log files cleaned"
fi

echo ""
print_success "All services stopped successfully! 🛑"
echo ""
echo "📋 To restart services:"
echo "  • Full setup:       ./setup_local_dev.sh"
echo "  • Backend only:     python main.py"
echo "  • Frontend only:    cd ui && npm run dev"
echo "  • Supabase only:    supabase start"
echo ""
echo "📖 For setup help:    see SETUP_AND_TEST_LOCAL.md"