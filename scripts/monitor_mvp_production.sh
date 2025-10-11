#!/bin/bash
# MVP Async Fix Production Monitoring Script
# Simple monitoring script for production API

API_URL="${1:-http://localhost:8000}"
MONITOR_DURATION="${2:-24}"  # hours

echo "🚀 MVP Async Fix Production Monitoring"
echo "API URL: $API_URL"
echo "Duration: $MONITOR_DURATION hours"
echo "=================================="

# Create logs directory
mkdir -p logs

# Run Python monitoring script
python3 scripts/test_mvp_async_fix_production.py \
    --api-url "$API_URL" \
    --monitor \
    --monitor-hours "$MONITOR_DURATION"

echo "📊 Monitoring completed. Check logs/mvp_production_test.log for details."
