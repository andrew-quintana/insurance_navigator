#!/bin/bash
# Script to start API Server persistently

echo "🚀 Starting Insurance Navigator API Server"
echo "=========================================="

# Set environment variables
export ENVIRONMENT=development
export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres?sslmode=disable"
export SUPABASE_URL="http://localhost:54321"

echo "🌍 Environment: $ENVIRONMENT"
echo "🗄️  Database: $DATABASE_URL"
echo "☁️  Supabase: $SUPABASE_URL"
echo ""

# Start API server
echo "📡 Starting API Server..."
python main.py

# If we get here, the server stopped
echo "❌ API Server stopped unexpectedly"
echo "📋 Check logs: tail -f logs/api_server.log"
