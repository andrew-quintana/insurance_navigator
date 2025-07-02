#!/bin/bash

# =============================================================================
# Insurance Navigator - Environment Validation Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Validate Supabase configuration
validate_supabase() {
    print_status "Validating Supabase configuration..."
    
    if ! curl -s "${SUPABASE_URL}/rest/v1/" -H "apikey: ${SUPABASE_ANON_KEY}" &>/dev/null; then
        print_error "Failed to connect to Supabase"
        exit 1
    fi
    
    print_success "Supabase configuration valid"
}

# Validate API keys
validate_api_keys() {
    print_status "Validating API keys..."
    
    # Validate LlamaParse API key
    if ! curl -s "https://api.llamaparse.com/health" -H "Authorization: Bearer ${LLAMAPARSE_API_KEY}" &>/dev/null; then
        print_error "Invalid LlamaParse API key"
        exit 1
    fi
    
    # Validate OpenAI API key
    if ! curl -s "https://api.openai.com/v1/models" -H "Authorization: Bearer ${OPENAI_API_KEY}" &>/dev/null; then
        print_error "Invalid OpenAI API key"
        exit 1
    }
    
    print_success "API keys valid"
}

# Validate database connection
validate_database() {
    print_status "Validating database connection..."
    
    if ! PGPASSWORD="${DB_PASSWORD}" psql "${DATABASE_URL}" -c '\dt' &>/dev/null; then
        print_error "Failed to connect to database"
        exit 1
    fi
    
    print_success "Database connection valid"
}

# Validate storage bucket
validate_storage() {
    print_status "Validating storage bucket..."
    
    if ! curl -s "${SUPABASE_URL}/storage/v1/bucket/documents" \
        -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" &>/dev/null; then
        print_error "Failed to access storage bucket"
        exit 1
    fi
    
    print_success "Storage bucket accessible"
}

# Validate Edge Functions
validate_edge_functions() {
    print_status "Validating Edge Functions..."
    
    functions=(
        "doc-processor"
        "link-assigner"
        "doc-parser"
        "vector-processor"
    )
    
    for func in "${functions[@]}"; do
        if ! supabase functions list | grep -q "$func"; then
            print_error "Edge Function $func not found"
            exit 1
        fi
    done
    
    print_success "Edge Functions validated"
}

# Validate environment variables
validate_env_vars() {
    print_status "Validating environment variables..."
    
    required_vars=(
        "SUPABASE_URL"
        "SUPABASE_ANON_KEY"
        "SUPABASE_SERVICE_ROLE_KEY"
        "LLAMAPARSE_API_KEY"
        "OPENAI_API_KEY"
        "DATABASE_URL"
        "DB_PASSWORD"
        "STORAGE_BUCKET"
        "JWT_SECRET"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi
    
    print_success "All required environment variables present"
}

# Main validation flow
main() {
    print_status "Starting environment validation..."
    
    validate_env_vars
    validate_supabase
    validate_api_keys
    validate_database
    validate_storage
    validate_edge_functions
    
    print_success "Environment validation completed successfully!"
    
    echo ""
    echo "🎉 Validation Summary:"
    echo "====================="
    echo "✅ Environment variables verified"
    echo "✅ Supabase connection tested"
    echo "✅ API keys validated"
    echo "✅ Database connection confirmed"
    echo "✅ Storage bucket accessible"
    echo "✅ Edge Functions available"
}

main "$@" 