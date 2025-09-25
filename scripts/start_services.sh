#!/bin/bash
# Script to start Insurance Navigator services persistently

echo "🚀 Starting Insurance Navigator Services"
echo "========================================"

# Set environment variables
export ENVIRONMENT=development
export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres?sslmode=disable"
export SUPABASE_URL="http://localhost:54321"

# Function to start API server
start_api_server() {
    echo "📡 Starting API Server..."
    python main.py > logs/api_server.log 2>&1 &
    API_PID=$!
    echo "✅ API Server started with PID: $API_PID"
    echo "📋 API Server logs: tail -f logs/api_server.log"
    echo "🌐 API Server URL: http://localhost:8000"
    echo "💊 Health check: curl http://localhost:8000/health"
}

# Function to start simple worker
start_simple_worker() {
    echo "⚙️  Starting Simple Worker..."
    python simple_worker.py > logs/simple_worker.log 2>&1 &
    WORKER_PID=$!
    echo "✅ Simple Worker started with PID: $WORKER_PID"
    echo "📋 Worker logs: tail -f logs/simple_worker.log"
}

# Function to check service health
check_health() {
    echo "🔍 Checking service health..."
    sleep 3
    
    # Check API server
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API Server is healthy"
    else
        echo "❌ API Server health check failed"
    fi
    
    # Check worker
    if ps -p $WORKER_PID > /dev/null 2>&1; then
        echo "✅ Simple Worker is running"
    else
        echo "❌ Simple Worker is not running"
    fi
}

# Function to show service status
show_status() {
    echo ""
    echo "📊 Service Status:"
    echo "=================="
    echo "API Server PID: $API_PID"
    echo "Worker PID: $WORKER_PID"
    echo ""
    echo "📋 Useful Commands:"
    echo "==================="
    echo "View API logs:     tail -f logs/api_server.log"
    echo "View Worker logs:  tail -f logs/simple_worker.log"
    echo "Check health:      curl http://localhost:8000/health"
    echo "Test upload:       curl -X POST http://localhost:8000/api/upload-pipeline/upload -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' -d '{\"filename\":\"test.pdf\",\"bytes_len\":1000,\"mime\":\"application/pdf\",\"sha256\":\"test\",\"ocr\":false}'"
    echo "Stop services:     kill $API_PID $WORKER_PID"
    echo ""
    echo "🔄 Services are running in the background..."
    echo "Press Ctrl+C to stop this script (services will continue running)"
}

# Main execution
start_api_server
start_simple_worker
check_health
show_status

# Keep script running to show status
while true; do
    sleep 30
    echo "⏰ $(date): Services still running..."
done
