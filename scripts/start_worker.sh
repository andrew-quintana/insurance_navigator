#!/bin/bash
# Script to start Simple Worker persistently

echo "⚙️  Starting Insurance Navigator Simple Worker"
echo "============================================="

# Set environment variables
export ENVIRONMENT=development
export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres?sslmode=disable"
export SUPABASE_URL="http://localhost:54321"

echo "🌍 Environment: $ENVIRONMENT"
echo "🗄️  Database: $DATABASE_URL"
echo ""

# Start simple worker
echo "⚙️  Starting Simple Worker..."
python simple_worker.py

# If we get here, the worker stopped
echo "❌ Simple Worker stopped unexpectedly"
echo "📋 Check logs: tail -f logs/simple_worker.log"
