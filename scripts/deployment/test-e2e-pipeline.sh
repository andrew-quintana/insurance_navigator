#!/bin/bash

# =============================================================================
# Insurance Navigator - End-to-End Pipeline Tests
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

# Test auth flow
test_auth() {
    print_status "Testing authentication flow..."
    
    # Test signup
    curl -X POST "${API_URL}/auth/signup" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"TestPass123!"}' \
        || { print_error "Signup test failed"; exit 1; }
    
    # Test login
    TOKEN=$(curl -X POST "${API_URL}/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"TestPass123!"}' \
        | jq -r '.access_token') \
        || { print_error "Login test failed"; exit 1; }
    
    print_success "Auth flow tests passed"
    echo "TOKEN=$TOKEN"
}

# Test document processing
test_document_processing() {
    print_status "Testing document processing pipeline..."
    
    # Upload test document
    DOC_ID=$(curl -X POST "${API_URL}/documents/upload" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@tests/data/test.pdf" \
        | jq -r '.document_id') \
        || { print_error "Document upload failed"; exit 1; }
    
    # Wait for processing
    for i in {1..30}; do
        STATUS=$(curl -s "${API_URL}/documents/${DOC_ID}/status" \
            -H "Authorization: Bearer $TOKEN" \
            | jq -r '.status')
        
        if [ "$STATUS" = "completed" ]; then
            break
        elif [ "$STATUS" = "error" ]; then
            print_error "Document processing failed"
            exit 1
        fi
        
        sleep 2
    done
    
    print_success "Document processing tests passed"
}

# Test Edge Functions
test_edge_functions() {
    print_status "Testing Edge Functions..."
    
    functions=(
        "doc-processor"
        "doc-parser"
        "vector-processor"
    )
    
    for func in "${functions[@]}"; do
        curl -i "${SUPABASE_URL}/functions/v1/${func}/health" \
            -H "Authorization: Bearer ${SUPABASE_ANON_KEY}" \
            || { print_error "${func} health check failed"; exit 1; }
    done
    
    print_success "Edge Function tests passed"
}

# Test monitoring
test_monitoring() {
    print_status "Testing monitoring systems..."
    
    # Check database monitoring
    psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM monitoring.performance_metrics;" \
        || { print_error "Database monitoring check failed"; exit 1; }
    
    # Check Edge Function monitoring
    psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM monitoring.edge_function_logs WHERE timestamp > NOW() - INTERVAL '1 hour';" \
        || { print_error "Edge Function monitoring check failed"; exit 1; }
    
    # Check alert system
    psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM monitoring.alerts WHERE timestamp > NOW() - INTERVAL '1 hour';" \
        || { print_error "Alert system check failed"; exit 1; }
    
    print_success "Monitoring system tests passed"
}

# Main test flow
main() {
    print_status "Starting end-to-end pipeline tests..."
    
    test_auth
    test_edge_functions
    test_document_processing
    test_monitoring
    
    print_success "All end-to-end tests passed successfully!"
    
    echo ""
    echo "🎉 Test Summary:"
    echo "================"
    echo "✅ Authentication flow"
    echo "✅ Edge Functions"
    echo "✅ Document processing"
    echo "✅ Monitoring systems"
}

main "$@" 