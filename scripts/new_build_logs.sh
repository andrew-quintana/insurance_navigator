#!/bin/bash

# Enhanced wrapper script for creating build logs with auto-fetched deployment logs
# Usage: 
#   ./scripts/new_build_logs.sh                    # Auto-fetch latest deployments
#   ./scripts/new_build_logs.sh 202506041530       # Use specific timestamp
#   ./scripts/new_build_logs.sh --render-only      # Only Render logs
#   ./scripts/new_build_logs.sh --vercel-only      # Only Vercel logs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Load .env file if it exists
load_env_file() {
    if [[ -f .env ]]; then
        echo "📄 Loading .env file..."
        set -a  # automatically export all variables
        source .env
        set +a  # stop automatically exporting
        echo "   ✅ Environment variables loaded"
    else
        echo "   ⚠️  No .env file found"
    fi
}

# Mask sensitive tokens for display
mask_token() {
    local token="$1"
    if [[ -z "$token" ]]; then
        echo "Not set"
    elif [[ ${#token} -lt 8 ]]; then
        printf '*%.0s' $(seq 1 ${#token})
    else
        echo "${token:0:4}$(printf '*%.0s' $(seq 1 $((${#token} - 8))))${token: -4}"
    fi
}

# Check if we have API tokens set
check_api_setup() {
    local has_vercel=false
    local has_render=false
    
    if [[ -n "$VERCEL_API_TOKEN" && -n "$VERCEL_PROJECT_ID" ]]; then
        has_vercel=true
    fi
    
    if [[ -n "$RENDER_API_TOKEN" && -n "$RENDER_SERVICE_ID" ]]; then
        has_render=true
    fi
    
    echo "🔍 API Setup Status:"
    if $has_vercel; then
        echo "   ✅ Vercel API configured"
        echo "      Token: $(mask_token "$VERCEL_API_TOKEN")"
        echo "      Project ID: $VERCEL_PROJECT_ID"
    else
        echo "   ⚠️  Vercel API not configured (will use manual entry)"
    fi
    
    if $has_render; then
        echo "   ✅ Render API configured"
        echo "      Token: $(mask_token "$RENDER_API_TOKEN")"
        echo "      Service ID: $RENDER_SERVICE_ID"
    else
        echo "   ⚠️  Render API not configured (will use manual entry)"
    fi
    echo
}

# Show API setup instructions
show_api_setup() {
    echo "💡 To enable automatic log fetching, set these environment variables:"
    echo
    echo "1. Create/edit your .env file:"
    echo "   touch .env"
    echo
    echo "2. Add your API credentials to .env:"
    echo "   # Vercel Configuration"
    echo "   VERCEL_API_TOKEN=your-vercel-token"
    echo "   VERCEL_PROJECT_ID=your-project-id"
    echo "   "
    echo "   # Render Configuration"
    echo "   RENDER_API_TOKEN=your-render-token"
    echo "   RENDER_SERVICE_ID=your-service-id"
    echo
    echo "3. Get your API tokens:"
    echo "   Vercel Token: https://vercel.com/account/tokens"
    echo "   Vercel Project ID: Project Settings → General → Project ID"
    echo "   Render Token: https://dashboard.render.com/account/api-keys"
    echo "   Render Service ID: From your service URL (srv-xxxxx)"
    echo
    echo "4. Test your setup:"
    echo "   python scripts/test_env_setup.py"
    echo
}

# Load environment variables first
load_env_file
echo

# Main execution
if [ $# -eq 0 ]; then
    echo "🚀 Creating build logs with latest deployment data..."
    check_api_setup
    python scripts/create_build_logs.py
elif [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Enhanced Build Log Creator"
    echo "========================="
    echo
    echo "Usage:"
    echo "  $0                    # Auto-fetch latest deployments (default)"
    echo "  $0 --latest           # Explicitly fetch most recent deployments"
    echo "  $0 202506041530       # Use specific timestamp"
    echo "  $0 --render-only      # Only fetch Render logs"
    echo "  $0 --vercel-only      # Only fetch Vercel logs"
    echo "  $0 --setup            # Show API setup instructions"
    echo "  $0 --test             # Test API configuration"
    echo
    show_api_setup
elif [[ "$1" == "--setup" ]]; then
    show_api_setup
elif [[ "$1" == "--test" ]]; then
    echo "🧪 Testing API configuration..."
    python scripts/test_env_setup.py
elif [[ "$1" == "--latest" ]]; then
    echo "🔄 Explicitly fetching most recent deployments..."
    check_api_setup
    python scripts/create_build_logs.py --latest
elif [[ "$1" == "--render-only" ]]; then
    echo "🔧 Creating Render logs only..."
    check_api_setup
    python scripts/create_build_logs.py --render-only
elif [[ "$1" == "--vercel-only" ]]; then
    echo "🌐 Creating Vercel logs only..."
    check_api_setup
    python scripts/create_build_logs.py --vercel-only
elif [[ "$1" =~ ^[0-9]{12}$ ]]; then
    echo "📅 Creating build logs with timestamp: $1"
    python scripts/create_build_logs.py "$1"
else
    echo "❌ Invalid argument: $1"
    echo "Use --help for usage information"
    exit 1
fi 