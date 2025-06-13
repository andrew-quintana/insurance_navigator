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

if [ ! -f "config/python/requirements.txt" ]; then
echo -e "${RED}❌ config/python/requirements.txt not found${NC}"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required files found${NC}"

# Check and validate .env file
echo -e "${BLUE}🔐 Checking environment configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file found${NC}"
    
    # Source .env file to check variables
    source .env 2>/dev/null || true
    
    # Check for required environment variables
    missing_vars=()
    
    if [ -z "$SUPABASE_URL" ]; then
        missing_vars+=("SUPABASE_URL")
    fi
    
    if [ -z "$SUPABASE_ANON_KEY" ]; then
        missing_vars+=("SUPABASE_ANON_KEY")
    fi
    
    if [ -z "$DATABASE_URL" ]; then
        missing_vars+=("DATABASE_URL")
    fi
    
    if [ -z "$JWT_SECRET_KEY" ]; then
        missing_vars+=("JWT_SECRET_KEY")
    fi
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All required environment variables found${NC}"
        echo -e "${BLUE}🔑 Using JWT secret from .env file${NC}"
        echo -e "${BLUE}🔗 Supabase URL: ${SUPABASE_URL}${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing environment variables: ${missing_vars[*]}${NC}"
        echo -e "${BLUE}📝 Add these to your .env file:${NC}"
        for var in "${missing_vars[@]}"; do
            echo "$var=your-value-here"
        done
        echo
    fi
else
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo -e "${BLUE}📝 Create a .env file with your Supabase credentials:${NC}"
    echo
    echo "SUPABASE_URL=https://your-project-ref.supabase.co"
    echo "SUPABASE_ANON_KEY=your-anon-key"
    echo "SUPABASE_SERVICE_ROLE_KEY=your-service-role-key"
    echo "DATABASE_URL=postgresql://postgres.your-project-ref:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    echo "JWT_SECRET_KEY=your-existing-supabase-jwt-secret"
    echo
fi

# Test Docker build locally
echo -e "${BLUE}🐳 Testing Docker build...${NC}"
if docker build -t insurance-navigator-test . > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker build successful${NC}"
    docker rmi insurance-navigator-test > /dev/null 2>&1
else
    echo -e "${RED}❌ Docker build failed${NC}"
    echo "Check your Dockerfile and config/python/requirements.txt"
    exit 1
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
echo -e "${BLUE}📋 Since you've already deployed the Blueprint on Render:${NC}"
echo "1. ✅ Render Blueprint created"
echo "2. 🔐 Add environment variables from your .env to Render dashboard"
echo "3. 🚀 Wait for deployment to complete"
echo "4. 🧪 Test your API endpoints"
echo
echo -e "${BLUE}📖 See DEPLOYMENT_SUMMARY.md for next steps${NC}" 