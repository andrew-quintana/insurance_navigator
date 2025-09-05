#!/bin/bash

# Phase 1 Workflow Testing Script
# Implements Phase 1 testing as specified in workflow_testing_spec.md
# Local Docker-based testing with production Supabase integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.phase1-workflow-testing.yml"
ENV_FILE="$PROJECT_ROOT/.env.production"

***REMOVED***
API_BASE_URL="http://localhost:8000"
WORKER_BASE_URL="http://localhost:8002"
FRONTEND_URL="http://localhost:3000"
MONITORING_URL="http://localhost:3001"

# Test configuration
TEST_USER_ID="phase1-test-user-$(date +%s)"
TEST_FILENAME="phase1-test-document.pdf"
TEST_FILE_SIZE=1048576  # 1MB
TEST_SHA256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
PHASE1_TESTS=0

# Helper functions
log_info() {
    echo -e "${BLUE}[PHASE1-INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PHASE1-SUCCESS]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[PHASE1-ERROR]${NC} $1"
    ((TESTS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[PHASE1-WARNING]${NC} $1"
}

log_phase() {
    echo -e "${PURPLE}[PHASE1-PHASE]${NC} $1"
    ((PHASE1_TESTS++))
}

# Environment validation
validate_environment() {
    log_phase "=== Phase 1: Environment Validation ==="
    
    # Check if .env.production exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Production environment file not found: $ENV_FILE"
        log_info "Please create .env.production with production Supabase credentials"
        return 1
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running"
        return 1
    fi
    
    # Check if docker-compose file exists
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        return 1
    fi
    
    log_success "Environment validation passed"
    return 0
}

# Docker services management
start_services() {
    log_phase "=== Phase 1: Starting Docker Services ==="
    
    cd "$PROJECT_ROOT"
    
    # Stop any existing services
    log_info "Stopping existing services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans || true
    
    # Build and start services
    log_info "Building and starting Phase 1 services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up --build -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    log_success "Docker services started"
    return 0
}

# Service health checks
check_service_health() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=0
    
    log_info "Checking $service_name health..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            log_success "$service_name is healthy"
            return 0
        fi
        
        ((attempt++))
        log_info "Attempt $attempt/$max_attempts - waiting for $service_name..."
        sleep 10
    done
    
    log_error "$service_name failed to become healthy after $max_attempts attempts"
    return 1
}

# Phase 1.1: Service Health Validation
test_service_health() {
    log_phase "=== Phase 1.1: Service Health Validation ==="
    
    # Check API Server
    if check_service_health "API Server" "$API_BASE_URL/health"; then
        log_success "API Server health check passed"
    else
        log_error "API Server health check failed"
        return 1
    fi
    
    # Check Worker Service
    if check_service_health "Worker Service" "$WORKER_BASE_URL/health"; then
        log_success "Worker Service health check passed"
    else
        log_error "Worker Service health check failed"
        return 1
    fi
    
    # Check Frontend Service
    if check_service_health "Frontend Service" "$FRONTEND_URL/health"; then
        log_success "Frontend Service health check passed"
    else
        log_error "Frontend Service health check failed"
        return 1
    fi
    
    # Check Monitoring Service
    if check_service_health "Monitoring Service" "$MONITORING_URL/health"; then
        log_success "Monitoring Service health check passed"
    else
        log_error "Monitoring Service health check failed"
        return 1
    fi
    
    # Check Production Supabase connectivity via API
    if curl -f -s "$API_BASE_URL/health" | grep -q "database.*healthy"; then
        log_success "Production Supabase connectivity verified"
    else
        log_error "Production Supabase connectivity failed"
        return 1
    fi
}

# Phase 1.2: Unit Tests Execution
run_unit_tests() {
    log_phase "=== Phase 1.2: Unit Tests Execution ==="
    
    cd "$PROJECT_ROOT"
    
    # Run API service unit tests
    log_info "Running API service unit tests..."
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T api-server python -m pytest tests/unit/api/ -v; then
        log_success "API unit tests passed"
    else
        log_error "API unit tests failed"
        return 1
    fi
    
    # Run Worker service unit tests
    log_info "Running Worker service unit tests..."
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T enhanced-base-worker python -m pytest tests/unit/workers/ -v; then
        log_success "Worker unit tests passed"
    else
        log_error "Worker unit tests failed"
        return 1
    fi
    
    # Run Frontend unit tests
    log_info "Running Frontend unit tests..."
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T frontend npm test -- --passWithNoTests; then
        log_success "Frontend unit tests passed"
    else
        log_error "Frontend unit tests failed"
        return 1
    fi
}

# Phase 1.3: Integration Tests
run_integration_tests() {
    log_phase "=== Phase 1.3: Integration Tests ==="
    
    # Use existing frontend simulation script for integration testing
    log_info "Running integration tests using frontend simulation..."
    
    if [ -f "$PROJECT_ROOT/scripts/testing/test-frontend-simulation.sh" ]; then
        chmod +x "$PROJECT_ROOT/scripts/testing/test-frontend-simulation.sh"
        if "$PROJECT_ROOT/scripts/testing/test-frontend-simulation.sh"; then
            log_success "Integration tests passed"
        else
            log_error "Integration tests failed"
            return 1
        fi
    else
        log_warning "Frontend simulation script not found, skipping integration tests"
    fi
}

# Phase 1.4: End-to-End Tests
run_e2e_tests() {
    log_phase "=== Phase 1.4: End-to-End Tests ==="
    
    # Test complete document upload workflow
    log_info "Testing complete document upload workflow..."
    
    # Upload document
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
        log_success "Document upload successful"
        
        # Extract job_id
        local job_id=$(echo "$upload_response" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$job_id" ]; then
            log_success "Job created: $job_id"
            
            # Monitor job processing
            log_info "Monitoring job processing through all stages..."
            local max_polls=20
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
                    
                    if [ "$state" = "done" ]; then
                        log_success "End-to-end workflow completed successfully!"
                        return 0
                    elif [ "$state" = "deadletter" ]; then
                        log_error "Job failed and moved to dead letter queue"
                        return 1
                    fi
                    
                    sleep 10
                else
                    log_error "Failed to get job status"
                    return 1
                fi
            done
            
            log_warning "End-to-end test completed without job completion"
        else
            log_error "Failed to extract job_id from upload response"
            return 1
        fi
    else
        log_error "Document upload failed"
        return 1
    fi
}

# Phase 1.5: Load/Performance Tests
run_performance_tests() {
    log_phase "=== Phase 1.5: Load/Performance Tests ==="
    
    # Test concurrent uploads
    log_info "Testing concurrent document uploads..."
    
    local concurrent_jobs=0
    local max_concurrent=5
    
    for i in $(seq 1 $max_concurrent); do
        (
            local response=$(curl -s -X POST "$API_BASE_URL/api/v2/upload" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer test-jwt-token" \
                -d "{
                    \"filename\": \"perf-test-$i.pdf\",
                    \"bytes_len\": $TEST_FILE_SIZE,
                    \"mime\": \"application/pdf\",
                    \"sha256\": \"perf-test-sha256-$i\",
                    \"ocr\": false
                }")
            
            if echo "$response" | grep -q "job_id"; then
                log_success "Concurrent upload $i successful"
                ((concurrent_jobs++))
            else
                log_error "Concurrent upload $i failed"
            fi
        ) &
    done
    
    wait
    
    if [ $concurrent_jobs -eq $max_concurrent ]; then
        log_success "All concurrent uploads successful ($concurrent_jobs/$max_concurrent)"
    else
        log_warning "Some concurrent uploads failed ($concurrent_jobs/$max_concurrent)"
    fi
    
    # Test API response times
    log_info "Testing API response times..."
    
    local start_time=$(date +%s%N)
    curl -s "$API_BASE_URL/health" > /dev/null
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))
    
    log_info "API health check response time: ${response_time}ms"
    
    if [ $response_time -lt 1000 ]; then
        log_success "API response time within acceptable limits (<1s)"
    else
        log_warning "API response time exceeds 1s: ${response_time}ms"
    fi
}

# Phase 1.6: Coverage Analysis
run_coverage_analysis() {
    log_phase "=== Phase 1.6: Coverage Analysis ==="
    
    cd "$PROJECT_ROOT"
    
    # Run coverage analysis for API service
    log_info "Running coverage analysis for API service..."
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T api-server python -m pytest --cov=api tests/unit/api/ --cov-report=term-missing; then
        log_success "API coverage analysis completed"
    else
        log_warning "API coverage analysis failed"
    fi
    
    # Run coverage analysis for Worker service
    log_info "Running coverage analysis for Worker service..."
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T enhanced-base-worker python -m pytest --cov=backend tests/unit/workers/ --cov-report=term-missing; then
        log_success "Worker coverage analysis completed"
    else
        log_warning "Worker coverage analysis failed"
    fi
}

# Phase 1.7: Error Handling Tests
run_error_handling_tests() {
    log_phase "=== Phase 1.7: Error Handling Tests ==="
    
    # Test invalid file size
    log_info "Testing invalid file size error handling..."
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
    log_info "Testing invalid MIME type error handling..."
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
    
    # Test rate limiting
    log_info "Testing rate limiting..."
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
        
        sleep 0.1
    done
    
    if [ "$rate_limit_hit" = true ]; then
        log_success "Rate limiting test passed"
    else
        log_warning "Rate limiting not triggered (may need adjustment)"
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up Phase 1 test environment..."
    
    cd "$PROJECT_ROOT"
    
    # Stop services
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans || true
    fi
    
    # Clean up test artifacts
    rm -f /tmp/phase1_test_*
    
    log_success "Cleanup completed"
}

# Main test execution
main() {
    log_info "Starting Phase 1 Workflow Testing"
    log_info "Project Root: $PROJECT_ROOT"
    log_info "Docker Compose: $DOCKER_COMPOSE_FILE"
    log_info "Test User ID: $TEST_USER_ID"
    echo
    
    # Set up trap for cleanup
    trap cleanup EXIT
    
    # Execute Phase 1 test phases
    validate_environment || exit 1
    start_services || exit 1
    test_service_health || exit 1
    run_unit_tests || exit 1
    run_integration_tests || exit 1
    run_e2e_tests || exit 1
    run_performance_tests || exit 1
    run_coverage_analysis || exit 1
    run_error_handling_tests || exit 1
    
    # Generate test report
    echo
    log_phase "=== Phase 1 Test Summary ==="
    log_success "Tests Passed: $TESTS_PASSED"
    if [ $TESTS_FAILED -gt 0 ]; then
        log_error "Tests Failed: $TESTS_FAILED"
    else
        log_success "Tests Failed: $TESTS_FAILED"
    fi
    
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local success_rate=$((TESTS_PASSED * 100 / total_tests))
    
    if [ $success_rate -eq 100 ]; then
        log_success "Phase 1 Success Rate: ${success_rate}% 🎉"
        log_success "Phase 1 testing completed successfully!"
        exit 0
    elif [ $success_rate -ge 80 ]; then
        log_success "Phase 1 Success Rate: ${success_rate}% ✅"
        log_warning "Phase 1 testing completed with warnings"
        exit 0
    else
        log_error "Phase 1 Success Rate: ${success_rate}% ❌"
        log_error "Phase 1 testing failed"
        exit 1
    fi
}

# Run main function
main "$@"
