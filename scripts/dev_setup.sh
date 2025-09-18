#!/bin/bash

# Development Environment Setup Script
# Automatically starts ngrok, extracts URL, and updates configuration files

set -e

echo "🚀 Starting Development Environment Setup..."

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

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    print_error "ngrok is not installed. Please install it first:"
    echo "  brew install ngrok  # on macOS"
    echo "  or download from https://ngrok.com/download"
    exit 1
fi

# Check if API server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_warning "API server is not running on port 8000"
    print_status "Please start the API server first:"
    echo "  ENVIRONMENT=development python main.py"
    exit 1
fi

print_status "API server is running ✅"

# Kill any existing ngrok processes
print_status "Cleaning up existing ngrok processes..."
pkill -f "ngrok" 2>/dev/null || true
sleep 2

# Start ngrok in background
print_status "Starting ngrok tunnel..."
ngrok http 8000 --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
print_status "Waiting for ngrok to initialize..."
sleep 5

# Extract ngrok URL
print_status "Extracting ngrok URL..."
NGROK_URL=""

# Try multiple methods to get the URL
for i in {1..10}; do
    # Method 1: Try ngrok API
    if command -v curl &> /dev/null; then
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('proto') == 'https':
            print(tunnel.get('public_url', ''))
            break
except:
    pass
" 2>/dev/null)
    fi
    
    # Method 2: Parse from log file
    if [ -z "$NGROK_URL" ]; then
        NGROK_URL=$(grep -o 'https://[a-z0-9]*\.ngrok-free\.app' /tmp/ngrok.log 2>/dev/null | head -1)
    fi
    
    if [ -n "$NGROK_URL" ]; then
        break
    fi
    
    print_status "Attempt $i/10: Waiting for ngrok URL..."
    sleep 2
done

if [ -z "$NGROK_URL" ]; then
    print_error "Failed to extract ngrok URL after 10 attempts"
    print_status "Ngrok log contents:"
    cat /tmp/ngrok.log
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

print_success "Ngrok URL extracted: $NGROK_URL"

# Update configuration files
print_status "Updating configuration files..."

# Update .env.development
if [ -f ".env.development" ]; then
    print_status "Updating .env.development..."
    sed -i.bak "s|NGROK_URL=.*|NGROK_URL=$NGROK_URL|" .env.development
    print_success "Updated .env.development"
else
    print_warning ".env.development not found, creating it..."
    echo "NGROK_URL=$NGROK_URL" > .env.development
    print_success "Created .env.development"
fi

# Update ui/.env.local
if [ -f "ui/.env.local" ]; then
    print_status "Updating ui/.env.local..."
    sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=$NGROK_URL|" ui/.env.local
    sed -i.bak "s|NEXT_PUBLIC_API_BASE_URL=.*|NEXT_PUBLIC_API_BASE_URL=$NGROK_URL|" ui/.env.local
    print_success "Updated ui/.env.local"
else
    print_warning "ui/.env.local not found, creating it..."
    cat > ui/.env.local << EOF
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0

# API Configuration
NEXT_PUBLIC_API_URL=$NGROK_URL
NEXT_PUBLIC_API_BASE_URL=$NGROK_URL

# Feature Flags
NEXT_PUBLIC_ENABLE_VECTOR_PROCESSING=true
NEXT_PUBLIC_ENABLE_REGULATORY_PROCESSING=true
EOF
    print_success "Created ui/.env.local"
fi

# Note: Worker now uses dynamic ngrok discovery
print_status "Worker uses dynamic ngrok discovery - no hardcoded URLs to update"

# Display summary
echo ""
print_success "🎉 Development environment setup complete!"
echo ""
echo "📋 Summary:"
echo "  • Ngrok URL: $NGROK_URL"
echo "  • API Server: http://localhost:8000"
echo "  • Frontend: http://localhost:3000 (if running)"
echo "  • Ngrok Dashboard: http://localhost:4040"
echo ""
echo "📁 Updated files:"
echo "  • .env.development (for reference)"
echo "  • ui/.env.local (frontend needs static URLs)"
echo "  • backend/workers/enhanced_base_worker.py (now uses dynamic discovery)"
echo ""
echo "🔄 Next steps:"
echo "  1. Restart the enhanced worker to pick up the new ngrok URL:"
echo "     python backend/workers/enhanced_runner.py"
echo "  2. Restart the frontend to pick up the new API URL:"
echo "     cd ui && npm run dev"
echo ""
echo "🛑 To stop ngrok: kill $NGROK_PID"
echo "📊 Monitor ngrok: http://localhost:4040"

# Save ngrok PID for easy cleanup
echo $NGROK_PID > /tmp/ngrok.pid
print_status "Ngrok PID saved to /tmp/ngrok.pid"
