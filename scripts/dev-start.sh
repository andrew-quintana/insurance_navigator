#!/bin/bash
# ========== DEVELOPMENT ENVIRONMENT STARTER ==========
# Convenience wrapper for Overmind to start development environment
# This script checks prerequisites and starts all services via Overmind
#
# Usage:
#   ./scripts/dev-start.sh           # Quiet mode (WARNING level) - minimal logs
#   ./scripts/dev-start.sh --verbose # Verbose mode (INFO level) - standard logs
#   ./scripts/dev-start.sh --debug   # Debug mode (DEBUG level) - all logs

set -e

# Parse arguments
VERBOSITY="quiet"  # Default to quiet (WARNING level)

for arg in "$@"; do
    case $arg in
        --quiet|-q)
            VERBOSITY="quiet"
            shift
            ;;
        --debug|-d)
            VERBOSITY="debug"
            shift
            ;;
        --verbose|-v)
            VERBOSITY="verbose"
            shift
            ;;
        *)
            # Unknown option
            ;;
    esac
done

# Set log levels based on verbosity
# Default is quiet (WARNING) - suppresses service logs but keeps Overmind messages
case $VERBOSITY in
    quiet|*)
        # Default: quiet mode (WARNING level) - service logs suppressed, Overmind messages visible
        export LOG_LEVEL="WARNING"
        export WORKER_LOG_LEVEL="WARNING"
        export NEXT_LOG_LEVEL="error"
        export OVERMIND_VERBOSE="false"
        ;;
    verbose)
        # Verbose mode (INFO level) - standard logs from services
        export LOG_LEVEL="INFO"
        export WORKER_LOG_LEVEL="INFO"
        export NEXT_LOG_LEVEL="info"
        export OVERMIND_VERBOSE="false"
        ;;
    debug)
        # Debug mode (DEBUG level) - all logs from services
        export LOG_LEVEL="DEBUG"
        export WORKER_LOG_LEVEL="DEBUG"
        export NEXT_LOG_LEVEL="debug"
        export OVERMIND_VERBOSE="true"
        ;;
esac

echo "🚀 Starting Development Environment with Overmind"
echo "=================================================="
echo "📊 Log Level: ${VERBOSITY} (${LOG_LEVEL})"
echo ""

# Check if Overmind is installed
if ! command -v overmind &> /dev/null; then
    echo "❌ Overmind is not installed."
    echo ""
    echo "Installation instructions:"
    echo "  macOS:  brew install overmind"
    echo "  Linux:  See https://github.com/DarthSim/overmind#installation"
    echo ""
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI is not installed."
    echo ""
    echo "Installation:"
    echo "  macOS:  brew install supabase/tap/supabase"
    echo "  Linux:  See https://supabase.com/docs/guides/cli"
    echo ""
    exit 1
fi

# Check if .env.development exists
if [ ! -f .env.development ]; then
    echo "⚠️  Warning: .env.development not found"
    echo "   Create it from config/env.development.example"
    echo ""
fi

# Check if Node.js is installed (for frontend)
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed."
    echo "   Required for frontend development server"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed."
    echo "   Required for frontend development server"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Start Overmind
echo "Starting all services..."
echo ""
echo "💡 Service logs are suppressed by default."
echo "   View logs: overmind logs <service-name>"
echo "   Show URLs: ./scripts/show-dev-urls.sh"
echo ""

# Start Overmind (runs in foreground)
# A startup summary will appear after services initialize
overmind start

