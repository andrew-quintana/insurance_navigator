#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting production deployment..."

# Reset the database with clean schema
echo "📦 Resetting database with production schema..."
supabase db reset

# Deploy all Edge Functions
echo "🔧 Deploying Edge Functions..."
supabase functions deploy upload-handler --no-verify-jwt
supabase functions deploy job-processor --no-verify-jwt

# Set production secrets
echo "🔐 Setting production secrets..."
supabase secrets set --env-file ./config/environment/env.production

# Link to production project
echo "🔗 Linking to production project..."
supabase link --project-ref jhrespvvhbnloxrieycf

# Deploy database changes
echo "💾 Deploying database changes..."
supabase db push

echo "✅ Production deployment complete!" 