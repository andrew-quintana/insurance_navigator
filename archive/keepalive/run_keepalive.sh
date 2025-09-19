#!/bin/bash

# API Keep-Alive Service Runner
# Simple launcher script that can be run from anywhere

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the keepalive directory
cd "$SCRIPT_DIR"

# Run the appropriate script based on arguments
if [ "$1" = "start" ]; then
    ./start_keepalive.sh "${@:2}"
elif [ "$1" = "stop" ]; then
    ./stop_keepalive.sh "${@:2}"
elif [ "$1" = "status" ]; then
    ./status_keepalive.sh "${@:2}"
else
    echo "Usage: $0 {start|stop|status} [options]"
    echo ""
    echo "Commands:"
    echo "  start   - Start the keep-alive service"
    echo "  stop    - Stop the keep-alive service"
    echo "  status  - Check the status of the keep-alive service"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 start --interval 120"
    echo "  $0 status"
    echo "  $0 stop"
    exit 1
fi
