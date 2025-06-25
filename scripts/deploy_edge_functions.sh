#!/bin/bash

# Edge Function Deployment Script
# Ensures proper deployment and secret propagation

set -e

echo "🚀 Starting Edge Function deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    print_error "OPENAI_API_KEY environment variable is required"
    exit 1
fi

if [ -z "$SUPABASE_ACCESS_TOKEN" ]; then
    print_error "SUPABASE_ACCESS_TOKEN environment variable is required"
    exit 1
fi

# Step 1: Update secrets
echo "📝 Step 1: Updating Supabase secrets..."
supabase secrets set \
    OPENAI_API_KEY="$OPENAI_API_KEY"
print_status "Secrets updated"

# Step 2: Deploy Edge Functions
echo "🔄 Step 2: Deploying Edge Functions..."

# Deploy shared modules first
echo "   - Deploying shared modules..."
supabase functions deploy _shared
print_status "_shared modules deployed"

# Deploy core functions
for func in doc-parser vector-processor job-processor; do
    echo "   - Deploying $func..."
    supabase functions deploy "$func"
    print_status "$func deployed"
done

# Step 3: Verify deployments
echo "🔍 Step 3: Verifying deployments..."

# Get service role key
SUPABASE_SERVICE_ROLE_KEY=$(grep SUPABASE_SERVICE_ROLE_KEY .env | cut -d'=' -f2)

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    print_error "SUPABASE_SERVICE_ROLE_KEY not found in .env file"
    exit 1
fi

# Test each function
for func in doc-parser vector-processor job-processor; do
    echo "   - Testing $func..."
    RESPONSE=$(curl -s -X GET \
        -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
        "https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/$func")
    
    if echo "$RESPONSE" | grep -q "healthy\|ok"; then
        print_status "$func health check passed"
    else
        print_warning "$func health check returned: $RESPONSE"
    fi
done

echo ""
echo "🎉 Edge Function deployment completed!"
echo ""
echo "📋 Deployment Summary:"
echo "   ✅ Secrets updated"
echo "   ✅ Edge Functions deployed"
echo "   ✅ Health checks completed"
echo ""
echo "🔍 To monitor logs:"
echo "   supabase functions logs --filter [function-name]"
echo "" 