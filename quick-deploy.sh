#!/bin/bash

# Quick Deploy Script for Medicare Navigator Serverless Migration
# Usage: ./quick-deploy.sh PROJECT_REF SUPABASE_URL SUPABASE_ANON_KEY LLAMAPARSE_KEY

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Medicare Navigator Quick Deploy${NC}"
echo "=================================="

# Check arguments
if [ $# -lt 4 ]; then
    echo -e "${RED}Usage: $0 PROJECT_REF SUPABASE_URL SUPABASE_ANON_KEY LLAMAPARSE_KEY${NC}"
    echo ""
    echo "Example:"
    echo "$0 abcdefghijklmnop https://abcdefghijklmnop.supabase.co eyJ0eXAiOiJKV... llx_1234567890abcdef"
    exit 1
fi

PROJECT_REF=$1
SUPABASE_URL=$2
SUPABASE_ANON_KEY=$3
LLAMAPARSE_KEY=$4

echo -e "${BLUE}📋 Configuration:${NC}"
echo "Project Ref: $PROJECT_REF"
echo "Supabase URL: $SUPABASE_URL"
echo "Anon Key: ${SUPABASE_ANON_KEY:0:20}..."
echo "LlamaParse Key: ${LLAMAPARSE_KEY:0:20}..."
echo ""

# Navigate to Supabase directory
cd db/supabase

# Link project
echo -e "${BLUE}🔗 Linking Supabase project...${NC}"
supabase link --project-ref $PROJECT_REF

# Deploy functions
echo -e "${BLUE}🚀 Deploying Edge Functions...${NC}"
supabase functions deploy doc-processor
supabase functions deploy link-assigner  
supabase functions deploy doc-parser
supabase functions deploy vector-processor

# Set secrets
echo -e "${BLUE}🔑 Setting environment variables...${NC}"
supabase secrets set LLAMAPARSE_API_KEY="$LLAMAPARSE_KEY"
supabase secrets set RENDER_BACKEND_URL="https://insurance-navigator-api.onrender.com"
supabase secrets set SERVICE_AUTH_TOKEN="$(openssl rand -base64 32)"

# Create frontend env file
echo -e "${BLUE}⚙️ Configuring frontend...${NC}"
cd ../../ui
cat > .env.local << EOF
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=$SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY

# API Configuration (keep for backward compatibility)  
NEXT_PUBLIC_API_BASE_URL=https://insurance-navigator-api.onrender.com
EOF

echo -e "${GREEN}✅ Frontend environment configured${NC}"

# Test deployment
echo -e "${BLUE}🧪 Testing deployment...${NC}"
cd ..
export SUPABASE_URL=$SUPABASE_URL
export SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY
./test-serverless-pipeline.sh

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "📋 Next Steps:"
echo "1. Add database policies in Supabase SQL Editor:"
echo "   CREATE POLICY \"edge_functions_documents_access\" ON documents FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');"
echo "   CREATE POLICY \"edge_functions_vectors_access\" ON user_document_vectors FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');"
echo ""
echo "2. Update your frontend to use DocumentUploadServerless component"
echo ""
echo "3. Test upload with a small document"
echo ""
echo -e "${GREEN}🚀 Your serverless architecture is ready!${NC}" 