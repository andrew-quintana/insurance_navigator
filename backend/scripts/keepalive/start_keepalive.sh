#!/bin/bash

# API Keep-Alive Service Starter
# Prevents API service from spinning down due to inactivity

set -e

# Configuration
API_URL="${API_URL:-***REMOVED***}"
INTERVAL="${INTERVAL:-300}"  # 5 minutes
LOG_FILE="${LOG_FILE:-api_keepalive.log}"
PID_FILE="${PID_FILE:-api_keepalive.pid}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 API Keep-Alive Service${NC}"
echo -e "${BLUE}========================${NC}"
echo -e "API URL: ${GREEN}$API_URL${NC}"
echo -e "Interval: ${GREEN}${INTERVAL}s${NC}"
echo -e "Log file: ${GREEN}$LOG_FILE${NC}"
echo -e "PID file: ${GREEN}$PID_FILE${NC}"
echo ""

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Keep-alive service is already running (PID: $PID)${NC}"
        echo -e "To stop it, run: ${RED}kill $PID${NC}"
        echo -e "Or run: ${RED}./stop_keepalive.sh${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠️  Stale PID file found, removing...${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Start the keep-alive service
echo -e "${BLUE}🔄 Starting keep-alive service...${NC}"

# Run in background and capture PID
nohup python3 "$(dirname "$0")/keep_api_warm_simple.py" "$API_URL" "$INTERVAL" > "$LOG_FILE" 2>&1 &
KEEPALIVE_PID=$!

# Save PID
echo "$KEEPALIVE_PID" > "$PID_FILE"

echo -e "${GREEN}✅ Keep-alive service started (PID: $KEEPALIVE_PID)${NC}"
echo -e "📝 Logs are being written to: ${GREEN}$LOG_FILE${NC}"
echo -e "🛑 To stop: ${RED}./stop_keepalive.sh${NC} or ${RED}kill $KEEPALIVE_PID${NC}"
echo -e "📊 To monitor: ${RED}tail -f $LOG_FILE${NC}"

# Wait a moment to check if it started successfully
sleep 2

if ps -p "$KEEPALIVE_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Service is running successfully${NC}"
else
    echo -e "${RED}❌ Service failed to start${NC}"
    echo -e "Check logs: ${YELLOW}cat $LOG_FILE${NC}"
    rm -f "$PID_FILE"
    exit 1
fi
