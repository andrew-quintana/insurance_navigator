#!/bin/bash

# Deploy the cleanup function
echo "📦 Deploying cleanup function..."
supabase functions deploy cleanup-test-documents

# Run the cleanup
echo "🧹 Running cleanup..."
supabase functions invoke cleanup-test-documents

echo "✅ Cleanup process complete" 