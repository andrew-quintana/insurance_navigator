#!/bin/bash
# Quick script to run the FM-038 Phase 1 Investigation
# This script provides a simple way to run the investigation with proper setup

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "FM-038 Phase 1: Comprehensive Chat Flow Investigation"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Change to project root
cd "$(dirname "$0")/../.."

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production not found"
    echo "   Please create .env.production with:"
    echo "   - PRODUCTION_API_URL=https://your-api-url.onrender.com"
    echo "   - OPENAI_API_KEY=sk-..."
    echo "   - DATABASE_URL=postgresql://..."
    exit 1
fi

echo "✅ Environment file found: .env.production"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    echo "   Please install Python 3.7 or higher"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import aiohttp" 2>/dev/null || {
    echo "⚠️  Warning: aiohttp not found"
    echo "   Installing dependencies..."
    pip3 install -q aiohttp python-dotenv
}

python3 -c "import dotenv" 2>/dev/null || {
    echo "⚠️  Warning: python-dotenv not found"
    echo "   Installing dependencies..."
    pip3 install -q python-dotenv
}

echo "✅ All dependencies available"
echo ""

# Run validation script first
echo "🔍 Validating investigation script..."
python3 tests/fm_038/validate_investigation_script.py
if [ $? -ne 0 ]; then
    echo "❌ Validation failed"
    exit 1
fi
echo ""

# Run the investigation
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "Starting Investigation"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "⏳ This will take approximately 20-30 seconds to complete..."
echo ""

python3 tests/fm_038/chat_flow_investigation.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo "✅ Investigation Complete!"
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "📄 Output files generated:"
    echo "   - Log file: chat_flow_investigation_*.log"
    echo "   - JSON report: chat_flow_investigation_report_*.json"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Review the investigation summary above"
    echo "   2. Check the JSON report for detailed metrics"
    echo "   3. Examine production logs in Render dashboard"
    echo "   4. Look for 'RAG Operation Started' and CHECKPOINT logs"
    echo "   5. Review PHASE_1_README.md for interpretation guide"
    echo ""
else
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo "❌ Investigation Failed"
    echo "═══════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Please review the error messages above and check:"
    echo "   1. .env.production configuration"
    echo "   2. Network connectivity to API"
    echo "   3. API service status in Render dashboard"
    echo ""
    exit 1
fi

