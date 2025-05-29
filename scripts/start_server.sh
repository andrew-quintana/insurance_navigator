#!/bin/bash

# Start Insurance Navigator API Server
# Usage: ./scripts/start_server.sh

set -e

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "📁 Loading environment from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  No .env file found, using defaults..."
    export DATABASE_URL="postgresql://aq_home@localhost:5432/insurance_navigator"
    export JWT_SECRET_KEY="xJkQJHUYMp2sP2exX/zYoS25N4Kij+OLC8mjqKeF+bHj5cCneRU7z/A/sYtvvB4AYs/YkY/mJvzHYcFdR8a7/g=="
    export SECURITY_BYPASS_ENABLED="true"
fi

echo "🚀 Starting Insurance Navigator API server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python main.py 