#!/bin/bash

# Simple wrapper script for creating new build logs
# Usage: ./scripts/new_build_logs.sh [YYYYMMDDHHMM]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if [ $# -eq 0 ]; then
    echo "Creating build logs with current timestamp..."
    python scripts/create_build_logs.py
elif [ $# -eq 1 ]; then
    echo "Creating build logs with timestamp: $1"
    python scripts/create_build_logs.py "$1"
else
    echo "Usage: $0 [YYYYMMDDHHMM]"
    echo "Example: $0 202506041530"
    exit 1
fi 