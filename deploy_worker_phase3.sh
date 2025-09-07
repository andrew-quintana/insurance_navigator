#!/bin/bash

# Phase 3 Worker Service Deployment Script
# Deploys worker service with SSL database connection fix

set -e

echo "🚀 Starting Phase 3 Worker Service Deployment..."

# Get the worker service ID
echo "📋 Getting worker service information..."
WORKER_SERVICE_ID=$(render services list -o json | jq -r '.[] | select(.name == "insurance-navigator-worker-workflow-testing") | .id')

if [ "$WORKER_SERVICE_ID" = "null" ] || [ -z "$WORKER_SERVICE_ID" ]; then
    echo "❌ Worker service not found. Available services:"
    render services list -o json | jq -r '.[] | "\(.name) (\(.id))"'
    exit 1
fi

echo "✅ Found worker service: $WORKER_SERVICE_ID"

# Deploy the worker service
echo "🔄 Deploying worker service with SSL fix..."
render deploys create $WORKER_SERVICE_ID

echo "⏳ Waiting for deployment to complete..."
echo "📊 Monitor deployment status with: render deploys list --service $WORKER_SERVICE_ID"

echo "✅ Worker service deployment initiated!"
echo "🔍 Check logs with: render logs --resources $WORKER_SERVICE_ID --output json"
