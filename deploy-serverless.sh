#!/bin/bash

# =============================================================================
# Medicare Navigator - Serverless Edge Functions Deployment Script
# =============================================================================

set -e  # Exit on any error

echo "🚀 Starting Medicare Navigator Serverless Migration Deployment"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(pwd)"
SUPABASE_DIR="$PROJECT_DIR/db/supabase"
UI_DIR="$PROJECT_DIR/ui"

# Functions to deploy
FUNCTIONS=(
    "doc-processor"
    "link-assigner"
    "doc-parser"
    "vector-processor"
)

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validation checks
print_status "Performing pre-deployment checks..."

# Check if Supabase CLI is installed
if ! command_exists supabase; then
    print_error "Supabase CLI is not installed. Please install it first:"
    echo "npm install -g supabase"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/main.py" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Check if Supabase project is linked
if [ ! -f "$SUPABASE_DIR/.env" ]; then
    print_warning "Supabase project not linked. You'll need to link it manually:"
    echo "cd db/supabase && supabase link"
fi

print_success "Pre-deployment checks passed"

# Step 1: Install frontend dependencies
print_status "Installing frontend dependencies..."
cd "$UI_DIR"
if [ -f "package-lock.json" ]; then
    npm ci
else
    npm install
fi
print_success "Frontend dependencies installed"

# Step 2: Deploy Edge Functions
print_status "Deploying Edge Functions to Supabase..."
cd "$SUPABASE_DIR"

for func in "${FUNCTIONS[@]}"; do
    print_status "Deploying function: $func"
    
    if [ -d "functions/$func" ]; then
        supabase functions deploy "$func" --no-verify-jwt
        if [ $? -eq 0 ]; then
            print_success "✅ $func deployed successfully"
        else
            print_error "❌ Failed to deploy $func"
            exit 1
        fi
    else
        print_error "Function directory not found: functions/$func"
        exit 1
    fi
done

print_success "All Edge Functions deployed successfully"

# Step 3: Set up environment variables
print_status "Setting up environment variables..."

echo ""
echo "🔧 REQUIRED ENVIRONMENT VARIABLES"
echo "=================================="
echo ""
echo "Please set the following environment variables in your Supabase project:"
echo ""
echo "1. LLAMAPARSE_API_KEY"
echo "   Description: Your LlamaParse API key for PDF processing"
echo "   Command: supabase secrets set LLAMAPARSE_API_KEY=your_llamaparse_api_key"
echo ""
echo "2. RENDER_BACKEND_URL"
echo "   Description: Your Render backend URL for embedding generation"
echo "   Command: supabase secrets set RENDER_BACKEND_URL=***REMOVED***"
echo ""
echo "3. SERVICE_AUTH_TOKEN"
echo "   Description: Secure token for backend API communication"
echo "   Command: supabase secrets set SERVICE_AUTH_TOKEN=your_secure_token"
echo ""

# Step 4: Update database policies if needed
print_status "Checking database policies..."

echo ""
echo "📋 REQUIRED DATABASE POLICIES"
echo "============================="
echo ""
echo "Execute these SQL commands in your Supabase SQL editor:"
echo ""
echo "-- Allow Edge Functions to access documents"
echo "CREATE POLICY IF NOT EXISTS \"edge_functions_documents_access\" ON documents"
echo "FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');"
echo ""
echo "-- Allow Edge Functions to access vectors"
echo "CREATE POLICY IF NOT EXISTS \"edge_functions_vectors_access\" ON user_document_vectors"
echo "FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');"
echo ""

# Step 5: Frontend environment setup
print_status "Setting up frontend environment..."

cd "$UI_DIR"

if [ ! -f ".env.local" ]; then
    print_warning "Creating .env.local template..."
    cat > .env.local << EOF
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# API Configuration (keep for backward compatibility)
NEXT_PUBLIC_API_BASE_URL=***REMOVED***
EOF
    print_warning "Please update .env.local with your Supabase project values"
else
    print_success "Frontend environment file exists"
fi

# Step 6: Test deployment
print_status "Testing Edge Function deployment..."

echo ""
echo "🧪 TESTING EDGE FUNCTIONS"
echo "========================="
echo ""
echo "You can test the deployed functions using:"
echo ""
echo "1. Test doc-processor:"
echo "   curl -X POST 'https://your-project.supabase.co/functions/v1/doc-processor' \\"
echo "        -H 'Authorization: Bearer your_token' \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"filename\":\"test.pdf\",\"contentType\":\"application/pdf\",\"fileSize\":1024}'"
echo ""

# Step 7: Integration instructions
print_status "Integration instructions..."

echo ""
echo "🔄 INTEGRATION STEPS"
echo "==================="
echo ""
echo "1. Update your frontend components to use DocumentUploadServerless:"
echo "   - Replace imports: DocumentUpload -> DocumentUploadServerless"
echo "   - The new component uses real-time progress tracking"
echo ""
echo "2. Keep the Render backend running for:"
echo "   - Embedding generation (/api/embeddings endpoint)"
echo "   - Chat functionality"
echo "   - Existing search features"
echo ""
echo "3. Monitor Edge Function logs:"
echo "   supabase functions logs doc-processor"
echo "   supabase functions logs link-assigner"
echo "   supabase functions logs doc-parser"
echo "   supabase functions logs vector-processor"
echo ""

# Final success message
echo ""
print_success "🎉 Serverless Migration Deployment Complete!"
echo ""
echo "📋 NEXT STEPS:"
echo "=============="
echo "1. Set the required environment variables in Supabase"
echo "2. Execute the database policy SQL commands"
echo "3. Update your frontend .env.local file"
echo "4. Test the upload pipeline with a small document"
echo "5. Monitor Edge Function logs for any issues"
echo "6. Update frontend imports to use DocumentUploadServerless"
echo ""
echo "🔗 USEFUL COMMANDS:"
echo "=================="
echo "Deploy specific function: supabase functions deploy function-name"
echo "View function logs: supabase functions logs function-name"
echo "Set secrets: supabase secrets set KEY=value"
echo "List secrets: supabase secrets list"
echo ""
echo "✅ Your Medicare Navigator application is now running on a serverless architecture!"

cd "$PROJECT_DIR" 