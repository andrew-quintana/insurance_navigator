#!/bin/bash

# Edge Function Deployment Script
# Deploys updated edge functions to Supabase

set -e

echo "🚀 Deploying Edge Functions..."

# Check if Supabase CLI is available
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Installing..."
    npx supabase --version
fi

# Check if Docker is running (required for function deployment)
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Deploy doc-parser function
echo "📄 Deploying doc-parser function..."
npx supabase functions deploy doc-parser --project-ref jhrespvvhbnloxrieycf

# Deploy vector-processor function  
echo "🔤 Deploying vector-processor function..."
npx supabase functions deploy vector-processor --project-ref jhrespvvhbnloxrieycf

echo "✅ All edge functions deployed successfully!"
echo ""
echo "🔍 Testing edge function health..."

# Test edge function health
echo "Testing doc-parser..."
curl -s -X GET "https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/doc-parser" \
  -H "Authorization: Bearer $(echo $SUPABASE_ANON_KEY)" | jq .

echo "Testing vector-processor..."  
curl -s -X GET "https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/vector-processor" \
  -H "Authorization: Bearer $(echo $SUPABASE_ANON_KEY)" | jq .

echo "🎉 Edge function deployment and testing complete!" 