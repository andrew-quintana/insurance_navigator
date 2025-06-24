#!/bin/bash

# Load environment variables
set -a
source .env
set +a

# Start document processing workers
echo "Starting document processing workers..."
python3 scripts/workers/document_processor.py &

# Store worker PIDs
echo $! > .worker.pid

# Trap SIGTERM and kill workers
trap 'kill $(cat .worker.pid) 2>/dev/null' SIGTERM

# Wait for workers to exit
wait 