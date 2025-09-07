#!/bin/bash

echo "🚀 Frontend Upload Pipeline Test Suite"
echo "======================================"
echo ""

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found!"
    echo ""
    echo "Please create .env.production with the following variables:"
    echo "  SUPABASE_URL=https://znvwzkdblknkkztqyfnu.supabase.co"
    echo "  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here"
    echo "  DATABASE_URL=postgresql://postgres:password@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres"
    echo "  NEXT_PUBLIC_API_BASE_URL=https://insurance-navigator-api.onrender.com"
    echo ""
    echo "You can copy from env.production.example and fill in the values."
    exit 1
fi

echo "✅ Environment file found"
echo ""

# Run setup verification first
echo "🔍 Running setup verification..."
npx playwright test tests/playwright/setup-verification.spec.ts --project=chromium

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup verification passed!"
    echo ""
    echo "🎭 Running main upload tests..."
    npx playwright test tests/playwright/frontend-upload-test.spec.ts --project=chromium
else
    echo ""
    echo "❌ Setup verification failed!"
    echo "Please check the frontend and API services are running."
    exit 1
fi

echo ""
echo "📊 Test results available in:"
echo "  - HTML Report: test-results/index.html"
echo "  - JSON Report: test-results/results.json"
echo ""
echo "To view the HTML report: npx playwright show-report"
