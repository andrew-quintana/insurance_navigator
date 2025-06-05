#!/bin/bash

# CORS Auto-Prevention Monitoring Script
# This script starts the automated CORS monitoring system

echo "🚀 Starting CORS Auto-Prevention Monitoring System..."

# Check if Python virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: No virtual environment detected. Activating .venv..."
    source .venv/bin/activate || {
        echo "❌ Failed to activate virtual environment. Please run: source .venv/bin/activate"
        exit 1
    }
fi

# Create required directories
mkdir -p scripts/monitoring/logs scripts/monitoring/reports

# Check if the prevention script exists
if [[ ! -f "scripts/monitoring/cors_auto_prevention.py" ]]; then
    echo "❌ CORS prevention script not found: scripts/monitoring/cors_auto_prevention.py"
    exit 1
fi

echo "📋 Starting monitoring with the following settings:"
echo "   - Scan interval: 5 minutes (300 seconds)"
echo "   - Quick scan interval: 1 minute (for issues)"
echo "   - Batch size: 5 deployments per batch"
echo "   - Discovery count: 20 new deployments per scan"
echo ""
echo "📊 The system will:"
echo "   ✅ Test CORS functionality automatically"
echo "   🔍 Discover new Vercel deployments"
echo "   🚨 Detect security threats"
echo "   📈 Monitor server health"
echo "   📄 Generate reports in scripts/monitoring/reports/"
echo ""
echo "🛑 To stop monitoring, press Ctrl+C"
echo ""

# Start the monitoring system
python scripts/monitoring/cors_auto_prevention.py --verbose

echo "🏁 CORS monitoring stopped." 