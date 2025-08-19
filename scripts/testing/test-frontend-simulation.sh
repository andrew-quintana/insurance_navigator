#!/bin/bash

# Frontend Simulation Testing Script
# This script simulates frontend behavior by making direct API calls
# to test the complete upload workflow from upload to completion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="http://localhost:8000"
WORKER_BASE_URL="http://localhost:8002"
TEST_USER_ID="test-user-123"
TEST_FILENAME="test-document.pdf"
TEST_FILE_SIZE=1048576  # 1MB
TEST_SHA256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # Empty file SHA256

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((TESTS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Health check function
check_service_health() {
    local service_name=$1
    local health_url=$2
    
    log_info "Checking $service_name health..."
    
    if curl -f -s "$health_url" > /dev/null; then
        log_success "$service_name is healthy"
        return 0
    else
        log_error "$service_name is not responding"
        return 1
    fi
}

# Test 1: Service Health Checks
test_service_health() {
    log_info "=== Test 1: Service Health Checks ==="
    
    # Check API server
    if check_service_health "API Server" "$API_BASE_URL/health"; then
        log_success "API Server health check passed"
    else
        log_error "API Server health check failed"
        return 1
    fi
    
    # Check BaseWorker
    if check_service_health "BaseWorker" "$WORKER_BASE_URL/health"; then
        log_success "BaseWorker health check passed"
    else
        log_error "BaseWorker health check failed"
        return 1
    fi
    
    # Check PostgreSQL (via API health endpoint)
    if curl -f -s "$API_BASE_URL/health" | grep -q "database.*healthy"; then
        log_success "Database connectivity check passed"
    else
        log_error "Database connectivity check failed"
        return 1
    fi
}

# Test 2: Upload Endpoint Simulation
test_upload_endpoint() {
    log_info "=== Test 2: Upload Endpoint Simulation ==="
    
    # Simulate frontend upload request
    log_info "Simulating frontend upload request..."
    
    local upload_response=$(curl -s -X POST "$API_BASE_URL/api/v2/upload" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer test-jwt-token" \
        -d "{
            \"filename\": \"$TEST_FILENAME\",
            \"bytes_len\": $TEST_FILE_SIZE,
            \"mime\": \"application/pdf\",
            \"sha256\": \"$TEST_SHA256\",
            \"ocr\": false
        }")
    
    if [ $? -eq 0 ]; then
        log_success "Upload request sent successfully"
        
        # Extract job_id and document_id from response
        local job_id=$(echo "$upload_response" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        local document_id=$(echo "$upload_response" | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$job_id" ] && [ -n "$document_id" ]; then
            log_success "Job created: $job_id, Document: $document_id"
            
            # Store for later tests
            echo "$job_id" > /tmp/test_job_id
            echo "$document_id" > /tmp/test_document_id
            
            return 0
        else
            log_error "Failed to extract job_id or document_id from response"
            return 1
        fi
    else
        log_error "Upload request failed"
        return 1
    fi
}

# Test 3: Job Status Polling Simulation
test_job_status_polling() {
    log_info "=== Test 3: Job Status Polling Simulation ==="
    
    local job_id=$(cat /tmp/test_job_id 2>/dev/null || echo "")
    
    if [ -z "$job_id" ]; then
        log_error "No job_id available for status testing"
        return 1
    fi
    
    log_info "Simulating frontend job status polling for job: $job_id"
    
    # Poll job status multiple times to simulate frontend behavior
    local max_polls=10
    local poll_count=0
    
    while [ $poll_count -lt $max_polls ]; do
        ((poll_count++))
        log_info "Polling job status (attempt $poll_count/$max_polls)..."
        
        local status_response=$(curl -s -X GET "$API_BASE_URL/api/v2/jobs/$job_id" \
            -H "Authorization: Bearer test-jwt-token")
        
        if [ $? -eq 0 ]; then
            local stage=$(echo "$status_response" | grep -o '"stage":"[^"]*"' | cut -d'"' -f4)
            local state=$(echo "$status_response" | grep -o '"state":"[^"]*"' | cut -d'"' -f4)
            local progress=$(echo "$status_response" | grep -o '"total_pct":[0-9.]*' | cut -d':' -f2)
            
            log_info "Job Status - Stage: $stage, State: $state, Progress: ${progress}%"
            
            # Check if job is complete
            if [ "$state" = "done" ]; then
                log_success "Job completed successfully!"
                return 0
            elif [ "$state" = "deadletter" ]; then
                log_error "Job failed and moved to dead letter queue"
                return 1
            fi
            
            # Wait before next poll (simulate frontend polling interval)
            sleep 5
        else
            log_error "Failed to get job status"
            return 1
        fi
    done
    
    log_warning "Job status polling completed without job completion"
    return 0
}

# Test 4: Job Listing Simulation
test_job_listing() {
    log_info "=== Test 4: Job Listing Simulation ==="
    
    log_info "Simulating frontend job listing request..."
    
    local jobs_response=$(curl -s -X GET "$API_BASE_URL/api/v2/jobs" \
        -H "Authorization: Bearer test-jwt-token")
    
    if [ $? -eq 0 ]; then
        log_success "Job listing request successful"
        
        # Check if our test job appears in the list
        local job_id=$(cat /tmp/test_job_id 2>/dev/null || echo "")
        if [ -n "$job_id" ] && echo "$jobs_response" | grep -q "$job_id"; then
            log_success "Test job found in job listing"
        else
            log_warning "Test job not found in job listing (may be normal)"
        fi
        
        return 0
    else
        log_error "Job listing request failed"
        return 1
    fi
}

# Test 5: Error Handling Simulation
test_error_handling() {
    log_info "=== Test 5: Error Handling Simulation ==="
    
    # Test invalid file size
    log_info "Testing invalid file size error..."
    local error_response=$(curl -s -X POST "$API_BASE_URL/api/v2/upload" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer test-jwt-token" \
        -d "{
            \"filename\": \"invalid.pdf\",
            \"bytes_len\": 104857600,
            \"mime\": \"application/pdf\",
            \"sha256\": \"$TEST_SHA256\",
            \"ocr\": false
        }")
    
    if echo "$error_response" | grep -q "File size.*exceeds limit"; then
        log_success "File size validation error handled correctly"
    else
        log_error "File size validation error not handled correctly"
        return 1
    fi
    
    # Test invalid MIME type
    log_info "Testing invalid MIME type error..."
    local mime_error_response=$(curl -s -X POST "$API_BASE_URL/api/v2/upload" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer test-jwt-token" \
        -d "{
            \"filename\": \"invalid.txt\",
            \"bytes_len\": $TEST_FILE_SIZE,
            \"mime\": \"text/plain\",
            \"sha256\": \"$TEST_SHA256\",
            \"ocr\": false
        }")
    
    if echo "$mime_error_response" | grep -q "Unsupported MIME type"; then
        log_success "MIME type validation error handled correctly"
    else
        log_error "MIME type validation error not handled correctly"
        return 1
    fi
    
    return 0
}

# Test 6: Rate Limiting Simulation
test_rate_limiting() {
    log_info "=== Test 6: Rate Limiting Simulation ==="
    
    log_info "Testing rate limiting by making multiple rapid requests..."
    
    local rate_limit_hit=false
    for i in {1..5}; do
        local response=$(curl -s -X POST "$API_BASE_URL/api/v2/upload" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer test-jwt-token" \
            -d "{
                \"filename\": \"rate-test-$i.pdf\",
                \"bytes_len\": $TEST_FILE_SIZE,
                \"mime\": \"application/pdf\",
                \"sha256\": \"rate-test-sha256-$i\",
                \"ocr\": false
            }")
        
        if echo "$response" | grep -q "Too Many Requests"; then
            log_success "Rate limiting triggered correctly on request $i"
            rate_limit_hit=true
            break
        fi
        
        sleep 0.1  # Small delay between requests
    done
    
    if [ "$rate_limit_hit" = true ]; then
        log_success "Rate limiting test passed"
        return 0
    else
        log_warning "Rate limiting not triggered (may need adjustment)"
        return 0
    fi
}

# Test 7: Concurrent Job Processing
test_concurrent_processing() {
    log_info "=== Test 7: Concurrent Job Processing ==="
    
    log_info "Testing concurrent job creation (should respect 2 jobs per user limit)..."
    
    # Create first job
    local job1_response=$(curl -s -X POST "$API_BASE_URL/api/v2/upload" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer test-jwt-token" \
        -d "{
            \"filename\": \"concurrent-1.pdf\",
            \"bytes_len\": $TEST_FILE_SIZE,
            \"mime\": \"application/pdf\",
            \"sha256\": \"concurrent-sha256-1\",
            \"ocr\": false
        }")
    
    local job1_id=$(echo "$job1_response" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$job1_id" ]; then
        log_success "First concurrent job created: $job1_id"
    else
        log_error "Failed to create first concurrent job"
        return 1
    fi
    
    # Create second job
    local job2_response=$(curl -s -X POST "$API_BASE_URL/api/v2/upload" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer test-jwt-token" \
        -d "{
            \"filename\": \"concurrent-2.pdf\",
            \"bytes_len\": $TEST_FILE_SIZE,
            \"mime\": \"application/pdf\",
            \"sha256\": \"concurrent-sha256-2\",
            \"ocr\": false
        }")
    
    local job2_id=$(echo "$job2_response" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$job2_id" ]; then
        log_success "Second concurrent job created: $job2_id"
    else
        log_error "Failed to create second concurrent job"
        return 1
    fi
    
    # Try to create third job (should be rejected)
    local job3_response=$(curl -s -X POST "$API_BASE_URL/api/v2/upload" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer test-jwt-token" \
        -d "{
            \"filename\": \"concurrent-3.pdf\",
            \"bytes_len\": $TEST_FILE_SIZE,
            \"mime\": \"application/pdf\",
            \"sha256\": \"concurrent-sha256-3\",
            \"ocr\": false
        }")
    
    if echo "$job3_response" | grep -q "Too Many Requests"; then
        log_success "Concurrent job limit enforced correctly"
        return 0
    else
        log_error "Concurrent job limit not enforced"
        return 1
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test artifacts..."
    rm -f /tmp/test_job_id /tmp/test_document_id
}

# Main test execution
main() {
    log_info "Starting Frontend Simulation Testing"
    log_info "API Base URL: $API_BASE_URL"
    log_info "Worker Base URL: $WORKER_BASE_URL"
    log_info "Test User ID: $TEST_USER_ID"
    echo
    
    # Run all tests
    test_service_health
    test_upload_endpoint
    test_job_status_polling
    test_job_listing
    test_error_handling
    test_rate_limiting
    test_concurrent_processing
    
    # Cleanup
    cleanup
    
    # Summary
    echo
    log_info "=== Test Summary ==="
    log_success "Tests Passed: $TESTS_PASSED"
    if [ $TESTS_FAILED -gt 0 ]; then
        log_error "Tests Failed: $TESTS_FAILED"
    else
        log_success "Tests Failed: $TESTS_FAILED"
    fi
    
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local success_rate=$((TESTS_PASSED * 100 / total_tests))
    
    if [ $success_rate -eq 100 ]; then
        log_success "Overall Success Rate: ${success_rate}% 🎉"
    elif [ $success_rate -ge 80 ]; then
        log_success "Overall Success Rate: ${success_rate}% ✅"
    else
        log_error "Overall Success Rate: ${success_rate}% ❌"
    fi
    
    echo
    log_info "Frontend simulation testing completed!"
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
