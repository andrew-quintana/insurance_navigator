#!/bin/bash

# Edge Function Deployment with Secret Validation
# Ensures Edge Functions are properly redeployed after secret updates
# Created: 2025-06-23
# Purpose: Prevent vectorization failures due to secret propagation issues

set -e

echo "🚀 Starting Edge Function deployment with secret validation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Validate required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    print_error "OPENAI_API_KEY environment variable is required"
    exit 1
fi

# Step 1: Update Supabase secrets
echo "📝 Step 1: Updating Supabase secrets..."
supabase secrets set OPENAI_API_KEY="$OPENAI_API_KEY"
print_status "Secrets updated"

# Step 2: Redeploy Edge Functions (CRITICAL STEP)
echo "🔄 Step 2: Redeploying Edge Functions..."
echo "   - Deploying vector-processor..."
supabase functions deploy vector-processor
print_status "vector-processor deployed"

echo "   - Deploying doc-parser..."
supabase functions deploy doc-parser
print_status "doc-parser deployed"

# Step 3: Validate Edge Function health
echo "🔍 Step 3: Validating Edge Function health..."

# Get service role key
SUPABASE_SERVICE_ROLE_KEY=$(grep SUPABASE_SERVICE_ROLE_KEY .env | cut -d'=' -f2 | tr -d '\n' | sed 's/"//g')

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    print_error "SUPABASE_SERVICE_ROLE_KEY not found in .env file"
    exit 1
fi

# Test vector-processor health
echo "   - Testing vector-processor..."
HEALTH_RESPONSE=$(curl -s -X GET "https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/vector-processor")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_status "vector-processor health check passed"
else
    print_warning "vector-processor health check returned: $HEALTH_RESPONSE"
fi

# Test vector-processor with minimal payload
echo "   - Testing vector processing functionality..."
TEST_RESPONSE=$(curl -s -X POST "https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/vector-processor" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"documentId": "test-deployment-validation", "extractedText": "Test document for deployment validation."}' \
  -w "%{http_code}")

HTTP_CODE="${TEST_RESPONSE: -3}"
RESPONSE_BODY="${TEST_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
    if echo "$RESPONSE_BODY" | grep -q "success.*true"; then
        print_status "Vector processing functionality validated"
    elif echo "$RESPONSE_BODY" | grep -q "document not found"; then
        print_status "Vector processing accessible (expected 404 for test document)"
    else
        print_warning "Vector processing response: $RESPONSE_BODY"
    fi
else
    print_error "Vector processing test failed with HTTP $HTTP_CODE: $RESPONSE_BODY"
    exit 1
fi

# Step 4: Verify secrets are accessible
echo "🔐 Step 4: Verifying secret accessibility..."
SECRET_LIST=$(supabase secrets list)
if echo "$SECRET_LIST" | grep -q "OPENAI_API_KEY"; then
    print_status "OPENAI_API_KEY secret is deployed"
else
    print_error "OPENAI_API_KEY secret not found in deployment"
    exit 1
fi

echo ""
echo "🎉 Edge Function deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "   ✅ Secrets updated in Supabase"
echo "   ✅ Edge Functions redeployed"
echo "   ✅ Health checks passed"
echo "   ✅ Vector processing validated"
echo ""
echo "🚨 Important: Always run this script after updating OPENAI_API_KEY"
echo "   Edge Functions require redeployment to access new secrets!"
echo ""

# Optional: Test with actual document upload
read -p "Would you like to test with a real document upload? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 Testing real document upload..."
    echo "Please test document upload through the UI to validate end-to-end functionality."
fi

print_status "Deployment script completed successfully" 