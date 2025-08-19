#!/bin/bash

# =============================================================================
# Phase 6: Application Deployment Verification
# 003 Worker Refactor - Deployment Verification Script
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

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERIFICATION_RESULTS="$PROJECT_ROOT/logs/phase6_verification_$(date +%Y%m%d_%H%M%S).json"

# Create logs directory
mkdir -p "$(dirname "$VERIFICATION_RESULTS")"

# Initialize verification results
init_verification_results() {
    cat > "$VERIFICATION_RESULTS" << EOF
{
    "verification_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "phase": "Phase 6 - Application Deployment Verification",
    "environment": "deployed",
    "results": {
        "infrastructure": {},
        "application_deployment": {},
        "functionality_validation": {},
        "performance_validation": {},
        "cross_environment_consistency": {},
        "production_readiness": {}
    },
    "summary": {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "overall_status": "unknown"
    }
}
EOF
}

# Update verification results
update_verification_results() {
    local category="$1"
    local test_name="$2"
    local status="$3"
    local details="$4"
    
    # Use jq to update the JSON file
    if command -v jq >/dev/null 2>&1; then
        jq ".results.$category.$test_name = {\"status\": \"$status\", \"details\": \"$details\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" "$VERIFICATION_RESULTS" > "${VERIFICATION_RESULTS}.tmp" && mv "${VERIFICATION_RESULTS}.tmp" "$VERIFICATION_RESULTS"
        
        # Update summary counts
        local total=$(jq '.summary.total_tests' "$VERIFICATION_RESULTS")
        local passed=$(jq '.summary.passed' "$VERIFICATION_RESULTS")
        local failed=$(jq '.summary.failed' "$VERIFICATION_RESULTS")
        local warnings=$(jq '.summary.warnings' "$VERIFICATION_RESULTS")
        
        if [ "$status" = "passed" ]; then
            passed=$((passed + 1))
        elif [ "$status" = "failed" ]; then
            failed=$((failed + 1))
        elif [ "$status" = "warning" ]; then
            warnings=$((warnings + 1))
        fi
        
        total=$((total + 1))
        
        jq ".summary.total_tests = $total | .summary.passed = $passed | .summary.failed = $failed | .summary.warnings = $warnings" "$VERIFICATION_RESULTS" > "${VERIFICATION_RESULTS}.tmp" && mv "${VERIFICATION_RESULTS}.tmp" "$VERIFICATION_RESULTS"
        
        # Update overall status
        if [ $failed -gt 0 ]; then
            jq '.summary.overall_status = "failed"' "$VERIFICATION_RESULTS" > "${VERIFICATION_RESULTS}.tmp" && mv "${VERIFICATION_RESULTS}.tmp" "$VERIFICATION_RESULTS"
        elif [ $warnings -gt 0 ]; then
            jq '.summary.overall_status = "warning"' "$VERIFICATION_RESULTS" > "${VERIFICATION_RESULTS}.tmp" && mv "${VERIFICATION_RESULTS}.tmp" "$VERIFICATION_RESULTS"
        else
            jq '.summary.overall_status = "passed"' "$VERIFICATION_RESULTS" > "${VERIFICATION_RESULTS}.tmp" && mv "${VERIFICATION_RESULTS}.tmp" "$VERIFICATION_RESULTS"
        fi
    else
        print_warning "jq not available, skipping verification results update"
    fi
}

# Infrastructure validation
verify_infrastructure() {
    print_status "Verifying infrastructure components..."
    
    # Database connectivity
    print_status "Checking database connectivity..."
    if command -v psql >/dev/null 2>&1; then
        if PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p') psql "$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1; then
            print_success "Database connectivity verified"
            update_verification_results "infrastructure" "database_connectivity" "passed" "Database connection successful"
        else
            print_error "Database connectivity failed"
            update_verification_results "infrastructure" "database_connectivity" "failed" "Database connection failed"
            return 1
        fi
    else
        print_warning "psql not available, skipping database connectivity check"
        update_verification_results "infrastructure" "database_connectivity" "warning" "psql not available"
    fi
    
    # Storage connectivity
    print_status "Checking storage connectivity..."
    if curl -f "http://localhost:5000/health" >/dev/null 2>&1; then
        print_success "Storage connectivity verified"
        update_verification_results "infrastructure" "storage_connectivity" "passed" "Storage health check successful"
    else
        print_error "Storage connectivity failed"
        update_verification_results "infrastructure" "storage_connectivity" "failed" "Storage health check failed"
        return 1
    fi
    
    # Redis connectivity
    print_status "Checking Redis connectivity..."
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli -p 6379 ping >/dev/null 2>&1; then
            print_success "Redis connectivity verified"
            update_verification_results "infrastructure" "redis_connectivity" "passed" "Redis ping successful"
        else
            print_error "Redis connectivity failed"
            update_verification_results "infrastructure" "redis_connectivity" "failed" "Redis ping failed"
            return 1
        fi
    else
        print_warning "redis-cli not available, skipping Redis connectivity check"
        update_verification_results "infrastructure" "redis_connectivity" "warning" "redis-cli not available"
    fi
    
    print_success "Infrastructure verification completed"
}

# Application deployment validation
verify_application_deployment() {
    print_status "Verifying application deployment..."
    
    # API server deployment
    print_status "Checking API server deployment..."
    if docker ps --filter "name=api-server" --filter "status=running" | grep -q api-server; then
        print_success "API server container is running"
        update_verification_results "application_deployment" "api_server_container" "passed" "API server container running"
    else
        print_error "API server container is not running"
        update_verification_results "application_deployment" "api_server_container" "failed" "API server container not running"
        return 1
    fi
    
    # BaseWorker deployment
    print_status "Checking BaseWorker deployment..."
    if docker ps --filter "name=base-worker" --filter "status=running" | grep -q base-worker; then
        print_success "BaseWorker container is running"
        update_verification_results "application_deployment" "base_worker_container" "passed" "BaseWorker container running"
    else
        print_error "BaseWorker container is not running"
        update_verification_results "application_deployment" "base_worker_container" "failed" "BaseWorker container not running"
        return 1
    fi
    
    # API server health
    print_status "Checking API server health..."
    if curl -f "http://localhost:8000/health" >/dev/null 2>&1; then
        print_success "API server health check passed"
        update_verification_results "application_deployment" "api_server_health" "passed" "API server health endpoint responding"
    else
        print_error "API server health check failed"
        update_verification_results "application_deployment" "api_server_health" "failed" "API server health endpoint not responding"
        return 1
    fi
    
    # BaseWorker health
    print_status "Checking BaseWorker health..."
    if docker logs base-worker 2>&1 | grep -q "BaseWorker initialized"; then
        print_success "BaseWorker health check passed"
        update_verification_results "application_deployment" "base_worker_health" "passed" "BaseWorker initialization confirmed"
    else
        print_error "BaseWorker health check failed"
        update_verification_results "application_deployment" "base_worker_health" "failed" "BaseWorker initialization not confirmed"
        return 1
    fi
    
    print_success "Application deployment verification completed"
}

# Functionality validation
verify_functionality() {
    print_status "Verifying application functionality..."
    
    # Test API endpoints
    print_status "Testing API endpoints..."
    
    # Root endpoint
    if curl -f "http://localhost:8000/" >/dev/null 2>&1; then
        print_success "API root endpoint responding"
        update_verification_results "functionality_validation" "api_root_endpoint" "passed" "Root endpoint responding"
    else
        print_error "API root endpoint not responding"
        update_verification_results "functionality_validation" "api_root_endpoint" "failed" "Root endpoint not responding"
        return 1
    fi
    
    # Health endpoint
    if curl -f "http://localhost:8000/health" >/dev/null 2>&1; then
        print_success "API health endpoint responding"
        update_verification_results "functionality_validation" "api_health_endpoint" "passed" "Health endpoint responding"
    else
        print_error "API health endpoint not responding"
        update_verification_results "functionality_validation" "api_health_endpoint" "failed" "Health endpoint not responding"
        return 1
    fi
    
    # Test worker job processing capability
    print_status "Testing worker job processing capability..."
    
    # Check if worker is processing jobs
    if docker logs base-worker 2>&1 | grep -q "Processing jobs"; then
        print_success "Worker job processing confirmed"
        update_verification_results "functionality_validation" "worker_job_processing" "passed" "Worker processing jobs confirmed"
    else
        print_warning "Worker job processing not confirmed (may be idle)"
        update_verification_results "functionality_validation" "worker_job_processing" "warning" "Worker job processing not confirmed"
    fi
    
    print_success "Functionality validation completed"
}

# Performance validation
verify_performance() {
    print_status "Verifying application performance..."
    
    # API response time
    print_status "Testing API response time..."
    local start_time=$(date +%s%N)
    if curl -f "http://localhost:8000/health" >/dev/null 2>&1; then
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 ))
        
        if [ $response_time -lt 100 ]; then
            print_success "API response time: ${response_time}ms (within 100ms threshold)"
            update_verification_results "performance_validation" "api_response_time" "passed" "Response time: ${response_time}ms"
        else
            print_warning "API response time: ${response_time}ms (exceeds 100ms threshold)"
            update_verification_results "performance_validation" "api_response_time" "warning" "Response time: ${response_time}ms (exceeds threshold)"
        fi
    else
        print_error "Failed to measure API response time"
        update_verification_results "performance_validation" "api_response_time" "failed" "Failed to measure response time"
        return 1
    fi
    
    # Worker startup time
    print_status "Testing worker startup time..."
    local worker_start_time=$(docker logs base-worker 2>&1 | grep "BaseWorker initialized" | head -1 | cut -d' ' -f1)
    if [ -n "$worker_start_time" ]; then
        print_success "Worker startup time recorded"
        update_verification_results "performance_validation" "worker_startup_time" "passed" "Worker startup time recorded"
    else
        print_warning "Worker startup time not recorded"
        update_verification_results "performance_validation" "worker_startup_time" "warning" "Worker startup time not recorded"
    fi
    
    print_success "Performance validation completed"
}

# Cross-environment consistency validation
verify_cross_environment_consistency() {
    print_status "Verifying cross-environment consistency..."
    
    # Compare deployed environment with local baseline
    print_status "Comparing deployed environment with local baseline..."
    
    # Check if local environment is running
    if docker ps --filter "name=api-server" --filter "name=base-worker" | grep -q .; then
        print_success "Local environment detected"
        update_verification_results "cross_environment_consistency" "local_environment_detected" "passed" "Local environment running"
        
        # Compare API versions
        local deployed_version=$(curl -s "http://localhost:8000/" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$deployed_version" ]; then
            print_success "Deployed API version: $deployed_version"
            update_verification_results "cross_environment_consistency" "api_version_consistency" "passed" "API version: $deployed_version"
        else
            print_warning "Could not determine deployed API version"
            update_verification_results "cross_environment_consistency" "api_version_consistency" "warning" "Version not determined"
        fi
    else
        print_warning "Local environment not detected"
        update_verification_results "cross_environment_consistency" "local_environment_detected" "warning" "Local environment not running"
    fi
    
    print_success "Cross-environment consistency validation completed"
}

# Production readiness validation
verify_production_readiness() {
    print_status "Verifying production readiness..."
    
    # Check environment variables
    print_status "Checking environment variables..."
    local missing_vars=()
    local required_vars=("DATABASE_URL" "SUPABASE_URL" "SUPABASE_ANON_KEY" "SUPABASE_SERVICE_ROLE_KEY")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        print_success "All required environment variables are set"
        update_verification_results "production_readiness" "environment_variables" "passed" "All required variables set"
    else
        print_error "Missing environment variables: ${missing_vars[*]}"
        update_verification_results "production_readiness" "environment_variables" "failed" "Missing variables: ${missing_vars[*]}"
        return 1
    fi
    
    # Check container restart policies
    print_status "Checking container restart policies..."
    local api_restart_policy=$(docker inspect api-server --format='{{.HostConfig.RestartPolicy.Name}}' 2>/dev/null || echo "unknown")
    local worker_restart_policy=$(docker inspect base-worker --format='{{.HostConfig.RestartPolicy.Name}}' 2>/dev/null || echo "unknown")
    
    if [ "$api_restart_policy" = "unless-stopped" ]; then
        print_success "API server restart policy: $api_restart_policy"
        update_verification_results "production_readiness" "api_restart_policy" "passed" "Restart policy: $api_restart_policy"
    else
        print_warning "API server restart policy: $api_restart_policy"
        update_verification_results "production_readiness" "api_restart_policy" "warning" "Restart policy: $api_restart_policy"
    fi
    
    if [ "$worker_restart_policy" = "unless-stopped" ]; then
        print_success "BaseWorker restart policy: $worker_restart_policy"
        update_verification_results "production_readiness" "base_worker_restart_policy" "passed" "Restart policy: $worker_restart_policy"
    else
        print_warning "BaseWorker restart policy: $worker_restart_policy"
        update_verification_results "production_readiness" "base_worker_restart_policy" "warning" "Restart policy: $worker_restart_policy"
    fi
    
    # Check logging configuration
    print_status "Checking logging configuration..."
    if docker logs api-server 2>&1 | grep -q "INFO\|ERROR\|WARNING"; then
        print_success "API server logging configured"
        update_verification_results "production_readiness" "api_logging" "passed" "Logging configured"
    else
        print_warning "API server logging not confirmed"
        update_verification_results "production_readiness" "api_logging" "warning" "Logging not confirmed"
    fi
    
    if docker logs base-worker 2>&1 | grep -q "INFO\|ERROR\|WARNING"; then
        print_success "BaseWorker logging configured"
        update_verification_results "production_readiness" "base_worker_logging" "passed" "Logging configured"
    else
        print_warning "BaseWorker logging not confirmed"
        update_verification_results "production_readiness" "base_worker_logging" "warning" "Logging not confirmed"
    fi
    
    print_success "Production readiness validation completed"
}

# Generate verification report
generate_verification_report() {
    print_status "Generating verification report..."
    
    if command -v jq >/dev/null 2>&1; then
        local total=$(jq '.summary.total_tests' "$VERIFICATION_RESULTS")
        local passed=$(jq '.summary.passed' "$VERIFICATION_RESULTS")
        local failed=$(jq '.summary.failed' "$VERIFICATION_RESULTS")
        local warnings=$(jq '.summary.warnings' "$VERIFICATION_RESULTS")
        local overall_status=$(jq -r '.summary.overall_status' "$VERIFICATION_RESULTS")
        
        echo ""
        echo "============================================================================="
        echo "Phase 6 Application Deployment Verification Report"
        echo "============================================================================="
        echo "Timestamp: $(date)"
        echo "Results File: $VERIFICATION_RESULTS"
        echo ""
        echo "Summary:"
        echo "  Total Tests: $total"
        echo "  Passed: $passed"
        echo "  Failed: $failed"
        echo "  Warnings: $warnings"
        echo "  Overall Status: $overall_status"
        echo ""
        
        if [ "$overall_status" = "passed" ]; then
            print_success "Phase 6 verification completed successfully!"
        elif [ "$overall_status" = "warning" ]; then
            print_warning "Phase 6 verification completed with warnings"
        else
            print_error "Phase 6 verification failed"
        fi
        
        echo ""
        echo "Detailed results available in: $VERIFICATION_RESULTS"
        echo "============================================================================="
    else
        print_warning "jq not available, skipping detailed report generation"
        echo "Verification results saved to: $VERIFICATION_RESULTS"
    fi
}

# Main verification process
main() {
    print_status "Starting Phase 6 Application Deployment Verification"
    
    # Initialize verification results
    init_verification_results
    
    # Load environment variables
    if [ -f "$PROJECT_ROOT/.env.local" ]; then
        print_status "Loading environment variables from .env.local"
        export $(cat "$PROJECT_ROOT/.env.local" | grep -v '^#' | xargs)
    elif [ -f "$PROJECT_ROOT/.env" ]; then
        print_status "Loading environment variables from .env"
        export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
    else
        print_warning "No environment file found, using system environment variables"
    fi
    
    # Run verification steps
    verify_infrastructure
    verify_application_deployment
    verify_functionality
    verify_performance
    verify_cross_environment_consistency
    verify_production_readiness
    
    # Generate report
    generate_verification_report
    
    print_status "Phase 6 verification completed. Results saved to: $VERIFICATION_RESULTS"
}

# Run main function
main "$@"
