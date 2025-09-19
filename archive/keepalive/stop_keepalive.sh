#!/bin/bash

# API Keep-Alive Service Stopper

set -e

# Configuration
PID_FILE="${PID_FILE:-api_keepalive.pid}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping API Keep-Alive Service${NC}"
echo -e "${BLUE}=================================${NC}"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No PID file found. Service may not be running.${NC}"
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Process $PID is not running. Removing stale PID file.${NC}"
    rm -f "$PID_FILE"
    exit 0
fi

# Stop the process
echo -e "🔄 Stopping process $PID..."
kill "$PID"

# Wait for graceful shutdown
echo -e "⏳ Waiting for graceful shutdown..."
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Process stopped gracefully${NC}"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Force kill if still running
echo -e "${YELLOW}⚠️  Process still running, force killing...${NC}"
kill -9 "$PID" 2>/dev/null || true

# Clean up
rm -f "$PID_FILE"
echo -e "${GREEN}✅ Keep-alive service stopped${NC}"
