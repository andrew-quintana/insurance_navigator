#!/bin/bash
# Quick Deployment Script for Insurance Navigator
# This script helps automate the deployment process

set -e  # Exit on any error

echo "🚀 Insurance Navigator - Quick Deploy Script"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if required files exist
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py not found${NC}"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required files found${NC}"

# Generate JWT secret
echo -e "${BLUE}🔐 Generating JWT secret...${NC}"
python3 scripts/generate_jwt_secret.py

# Test Docker build locally
echo -e "${BLUE}🐳 Testing Docker build...${NC}"
if docker build -t insurance-navigator-test . > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker build successful${NC}"
    docker rmi insurance-navigator-test > /dev/null 2>&1
else
    echo -e "${RED}❌ Docker build failed${NC}"
    echo "Check your Dockerfile and requirements.txt"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo -e "${BLUE}📝 Create a .env file with your Supabase credentials:${NC}"
    echo
    echo "SUPABASE_URL=https://your-project-ref.supabase.co"
    echo "SUPABASE_ANON_KEY=your-anon-key"
    echo "SUPABASE_SERVICE_ROLE_KEY=your-service-role-key"
    echo "DATABASE_URL=postgresql://postgres.your-project-ref:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    echo "JWT_SECRET_KEY=your-jwt-secret-from-above"
    echo
fi

# Git status check
echo -e "${BLUE}📦 Checking git status...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes${NC}"
    echo "Commit your changes before deploying:"
    echo "  git add ."
    echo "  git commit -m 'Prepare for deployment'"
    echo "  git push origin main"
else
    echo -e "${GREEN}✅ Git repository is clean${NC}"
fi

echo
echo -e "${GREEN}🎉 Pre-deployment checks complete!${NC}"
echo
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Create Supabase project: https://supabase.com"
echo "2. Create Render account: https://render.com"
echo "3. Push to GitHub if not already done"
echo "4. Create new Blueprint in Render with your repo"
echo "5. Configure environment variables in Render"
echo
echo -e "${BLUE}📖 See deploy-guide.md for detailed instructions${NC}" 