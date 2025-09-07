#!/bin/bash

# API Keep-Alive Service Status Checker

set -e

# Configuration
PID_FILE="${PID_FILE:-api_keepalive.pid}"
LOG_FILE="${LOG_FILE:-api_keepalive.log}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 API Keep-Alive Service Status${NC}"
echo -e "${BLUE}===============================${NC}"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No PID file found. Service is not running.${NC}"
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Service is running (PID: $PID)${NC}"
    
    # Show process info
    echo -e "\n${BLUE}Process Information:${NC}"
    ps -p "$PID" -o pid,ppid,cmd,etime,pcpu,pmem
    
    # Show recent logs
    if [ -f "$LOG_FILE" ]; then
        echo -e "\n${BLUE}Recent Logs (last 10 lines):${NC}"
        tail -10 "$LOG_FILE"
    else
        echo -e "${YELLOW}⚠️  Log file not found: $LOG_FILE${NC}"
    fi
    
else
    echo -e "${RED}❌ Service is not running (stale PID file)${NC}"
    echo -e "${YELLOW}⚠️  Removing stale PID file...${NC}"
    rm -f "$PID_FILE"
fi
