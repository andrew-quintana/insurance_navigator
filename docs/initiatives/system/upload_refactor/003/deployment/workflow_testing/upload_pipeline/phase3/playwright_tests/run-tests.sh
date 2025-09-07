#!/bin/bash

# Frontend Upload Pipeline Test Runner
echo "🚀 Starting Frontend Upload Pipeline Tests"
echo "=============================================="

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found!"
    echo "Please create .env.production with the following variables:"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_SERVICE_ROLE_KEY" 
    echo "  - DATABASE_URL"
    echo "  - NEXT_PUBLIC_API_BASE_URL"
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Run Playwright tests
echo "🎭 Running Playwright tests..."
npx playwright test

# Check test results
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "📊 Test results available in:"
    echo "  - HTML Report: test-results/index.html"
    echo "  - JSON Report: test-results/results.json"
    echo "  - JUnit Report: test-results/results.xml"
else
    echo "❌ Some tests failed!"
    echo "📊 Check test-results/ for detailed reports"
    exit 1
fi
