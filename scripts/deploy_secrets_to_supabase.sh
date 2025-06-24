#!/bin/bash

# Deploy Secrets to Supabase Edge Functions
# Based on: https://supabase.com/docs/guides/functions/secrets

set -e

echo "🔐 Deploying Secrets to Supabase Edge Functions"
echo "================================================"

# Check if we're logged in to Supabase CLI
if ! supabase projects list > /dev/null 2>&1; then
    echo "❌ Not logged in to Supabase CLI. Please run 'supabase login' first."
    exit 1
fi

# Check if we have required environment variables locally
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "❌ OPENAI_API_KEY not found in local environment"
    echo "💡 Please set it in your shell: export OPENAI_API_KEY=your_key_here"
    exit 1
fi

echo "✅ Found OPENAI_API_KEY in local environment"

# Create temporary secrets file for deployment
SECRETS_FILE="./supabase/.env.production"
echo "📝 Creating temporary secrets file: $SECRETS_FILE"

cat > "$SECRETS_FILE" << EOF
# Production secrets for Edge Functions
OPENAI_API_KEY=$OPENAI_API_KEY
EOF

echo "✅ Created secrets file with OPENAI_API_KEY"

# Deploy secrets to Supabase
echo "🚀 Deploying secrets to Supabase Edge Functions..."

if supabase secrets set --env-file "$SECRETS_FILE"; then
    echo "✅ Secrets deployed successfully!"
else
    echo "❌ Failed to deploy secrets"
    rm -f "$SECRETS_FILE"
    exit 1
fi

# Clean up temporary file
rm -f "$SECRETS_FILE"
echo "🧹 Cleaned up temporary secrets file"

# List current secrets to verify
echo ""
echo "📋 Current secrets in Supabase:"
supabase secrets list

echo ""
echo "🎉 Secret deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Test user document upload"
echo "2. Monitor Edge Function logs for successful OpenAI API calls"
echo "3. Verify vectors are created in the database"
echo ""
echo "🔍 To monitor logs:"
echo "   Go to: https://supabase.com/dashboard/project/jhrespvvhbnloxrieycf/functions"
echo "   Click on 'vector-processor' → 'Logs' tab" 