#!/bin/bash

# Insurance Navigator - Local Development Setup Script
# ====================================================

set -e  # Exit on any error

echo "🚀 Insurance Navigator - Local Development Setup"
echo "=================================================="

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

# Check prerequisites
echo "🔍 Checking Prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc -l) -eq 1 ]]; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.11+ required (found $PYTHON_VERSION)"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    print_success "Node.js $NODE_VERSION found"
else
    print_error "Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm -v)
    print_success "npm $NPM_VERSION found"
else
    print_error "npm not found"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    print_success "Docker found"
else
    print_error "Docker not found. Please install Docker"
    exit 1
fi

# Check Supabase CLI
if command -v supabase &> /dev/null; then
    SUPABASE_VERSION=$(supabase --version)
    print_success "Supabase CLI found: $SUPABASE_VERSION"
else
    print_warning "Supabase CLI not found. Installing..."
    npm install -g @supabase/cli
    print_success "Supabase CLI installed"
fi

echo ""

# Step 1: Setup Python environment
echo "🐍 Setting up Python Environment..."

if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

print_info "Activating virtual environment..."
source .venv/bin/activate

print_info "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
print_success "Python dependencies installed"

echo ""

# Step 2: Setup Supabase
echo "🗄️  Setting up Supabase..."

# Check if Supabase is already running
if curl -s http://localhost:54321/health > /dev/null; then
    print_warning "Supabase already running"
else
    print_info "Starting Supabase..."
    supabase start > supabase_start.log 2>&1 &
    SUPABASE_PID=$!
    
    # Wait for Supabase to start (max 60 seconds)
    echo -n "Waiting for Supabase to start"
    for i in {1..60}; do
        if curl -s http://localhost:54321/health > /dev/null; then
            echo ""
            print_success "Supabase started successfully"
            break
        else
            echo -n "."
            sleep 1
        fi
    done
    
    if ! curl -s http://localhost:54321/health > /dev/null; then
        print_error "Supabase failed to start within 60 seconds"
        print_info "Check supabase_start.log for details"
        exit 1
    fi
fi

# Extract Supabase connection details
SUPABASE_STATUS=$(supabase status --output json 2>/dev/null)
if [ $? -eq 0 ]; then
    print_success "Supabase configuration retrieved"
else
    print_warning "Could not retrieve Supabase status"
fi

echo ""

# Step 3: Environment Configuration
echo "🔧 Configuring Environment..."

# Update environment variables for local development
export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
export DATABASE_URL_LOCAL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
export SUPABASE_URL="http://127.0.0.1:54321"

print_success "Environment variables configured for local development"

# Verify .env.development exists and has correct values
if [ -f ".env.development" ]; then
    print_info "Checking .env.development file..."
    
    # Check if DATABASE_URL is correctly set
    if grep -q "DATABASE_URL=.*127.0.0.1:54322" .env.development; then
        print_success ".env.development has correct database URL"
    else
        print_warning ".env.development needs database URL update"
        print_info "Updating .env.development..."
        
        # Create backup
        cp .env.development .env.development.backup
        
        # Update DATABASE_URL lines
        sed -i.tmp 's|DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres|g' .env.development
        sed -i.tmp 's|DATABASE_URL_LOCAL=.*|DATABASE_URL_LOCAL=postgresql://postgres:postgres@127.0.0.1:54322/postgres|g' .env.development
        sed -i.tmp 's|SUPABASE_URL=.*|SUPABASE_URL=http://127.0.0.1:54321|g' .env.development
        
        # Clean up temp files
        rm -f .env.development.tmp
        
        print_success ".env.development updated"
    fi
else
    print_warning ".env.development not found"
fi

echo ""

# Step 4: Setup Frontend
echo "🌐 Setting up Frontend..."

cd ui

if [ ! -d "node_modules" ]; then
    print_info "Installing frontend dependencies..."
    npm install --silent
    print_success "Frontend dependencies installed"
else
    print_info "Frontend dependencies already installed"
fi

cd ..

echo ""

# Step 5: Start Services
echo "🚀 Starting Services..."

# Start backend API
print_info "Starting backend API..."
if pgrep -f "python.*main.py" > /dev/null; then
    print_warning "Backend API already running"
else
    python main.py > backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to start
    echo -n "Waiting for backend API to start"
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null; then
            echo ""
            print_success "Backend API started successfully"
            break
        else
            echo -n "."
            sleep 1
        fi
    done
    
    if ! curl -s http://localhost:8000/health > /dev/null; then
        print_error "Backend API failed to start within 30 seconds"
        print_info "Check backend.log for details"
        exit 1
    fi
fi

# Start frontend
print_info "Starting frontend..."
cd ui

if lsof -i:3000 > /dev/null; then
    print_warning "Frontend already running on port 3000"
else
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    echo -n "Waiting for frontend to start"
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null; then
            echo ""
            print_success "Frontend started successfully"
            break
        else
            echo -n "."
            sleep 1
        fi
    done
fi

cd ..

echo ""

# Step 6: Validation
echo "🧪 Running Validation..."

python validate_local_setup.py

echo ""

# Summary
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "🌐 Your Insurance Navigator is now running:"
echo "  • Frontend:     http://localhost:3000"
echo "  • Backend API:  http://localhost:8000"
echo "  • API Docs:     http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health"
echo "  • Supabase:     http://localhost:54323"
echo ""
echo "📋 Useful Commands:"
echo "  • Validate setup:     python validate_local_setup.py"
echo "  • Test API:           python test_api_endpoint_direct.py"
echo "  • Stop Supabase:      supabase stop"
echo "  • View backend logs:  tail -f backend.log"
echo "  • View frontend logs: tail -f frontend.log"
echo ""
echo "📖 For detailed information, see: SETUP_AND_TEST_LOCAL.md"
echo ""

# Save process IDs for easy cleanup
if [ ! -z "$BACKEND_PID" ]; then
    echo $BACKEND_PID > .backend.pid
fi

if [ ! -z "$FRONTEND_PID" ]; then
    echo $FRONTEND_PID > .frontend.pid
fi

print_success "Setup completed successfully! 🚀"