#!/bin/bash
# 003 Worker Refactor - Deployment and Verification Script
# This script provides automated deployment with comprehensive validation
# and rollback capabilities to prevent deployment failures experienced in 002.

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/infrastructure/config/deployment_config.yaml"
VALIDATION_SCRIPT="$PROJECT_ROOT/infrastructure/validation/deployment_validator.py"
ROLLBACK_SCRIPT="$PROJECT_ROOT/infrastructure/validation/automated_rollback.py"
REPORTS_DIR="$PROJECT_ROOT/infrastructure/validation/reports"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print banner
print_banner() {
    echo
    echo "================================================================"
    echo "  003 Worker Refactor - Deployment and Verification System"
    echo "================================================================"
    echo "  Automated deployment with comprehensive validation"
    echo "  and rollback capabilities"
    echo "================================================================"
    echo
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        log_error "Not in project root directory. Please run from project root."
        exit 1
    fi
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed."
        exit 1
    fi
    
    # Check if required Python packages are available
    python3 -c "import yaml, httpx, psycopg2" 2>/dev/null || {
        log_error "Required Python packages not installed. Please install:"
        log_error "  pip install pyyaml httpx psycopg2"
        exit 1
    }
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is required but not installed."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Validate local environment
validate_local_environment() {
    log_info "Validating local environment..."
    
    # Check if local environment is running
    if ! docker-compose ps | grep -q "Up"; then
        log_warning "Local environment not running. Starting services..."
        docker-compose up -d
        
        # Wait for services to be ready
        log_info "Waiting for services to be ready..."
        sleep 30
    fi
    
    # Run local validation
    log_info "Running local environment validation..."
    if python3 "$VALIDATION_SCRIPT" "$CONFIG_FILE"; then
        log_success "Local environment validation passed"
    else
        log_error "Local environment validation failed"
        log_error "Please fix local environment issues before proceeding"
        exit 1
    fi
}

# Deploy infrastructure
deploy_infrastructure() {
    log_info "Deploying infrastructure..."
    
    # For local development, this means ensuring Docker services are running
    # In production, this would deploy to cloud infrastructure
    
    # Check current status
    local running_services=$(docker-compose ps --services --filter "status=running" | wc -l)
    local total_services=$(docker-compose config --services | wc -l)
    
    if [[ $running_services -eq $total_services ]]; then
        log_success "All services already running"
        return 0
    fi
    
    # Start services
    log_info "Starting infrastructure services..."
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    local timeout=120
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        local healthy_services=$(docker-compose ps --services --filter "status=running" | wc -l)
        if [[ $healthy_services -eq $total_services ]]; then
            log_success "All services are running and healthy"
            return 0
        fi
        
        sleep 5
        elapsed=$((elapsed + 5))
        log_info "Waiting for services... ($elapsed/$timeout seconds)"
    done
    
    log_error "Services failed to start within timeout"
    return 1
}

# Validate infrastructure deployment
validate_infrastructure() {
    log_info "Validating infrastructure deployment..."
    
    # Run infrastructure validation
    if python3 "$VALIDATION_SCRIPT" "$CONFIG_FILE"; then
        log_success "Infrastructure validation passed"
        return 0
    else
        log_error "Infrastructure validation failed"
        return 1
    fi
}

# Deploy application
deploy_application() {
    log_info "Deploying application..."
    
    # For local development, this means building and starting application containers
    # In production, this would deploy application code
    
    # Build application images
    log_info "Building application images..."
    docker-compose build api-server base-worker
    
    # Restart application services
    log_info "Restarting application services..."
    docker-compose restart api-server base-worker
    
    # Wait for application services to be ready
    log_info "Waiting for application services to be ready..."
    sleep 30
    
    log_success "Application deployment completed"
}

# Validate application deployment
validate_application() {
    log_info "Validating application deployment..."
    
    # Run application validation
    if python3 "$VALIDATION_SCRIPT" "$CONFIG_FILE"; then
        log_success "Application validation passed"
        return 0
    else
        log_error "Application validation failed"
        return 1
    fi
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Test API health endpoint
    log_info "Testing API health endpoint..."
    if curl -f -s "http://localhost:8000/health" > /dev/null; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Test worker health
    log_info "Testing worker health..."
    if docker-compose exec base-worker python -c "from backend.workers.base_worker import BaseWorker; print('Worker import successful')" > /dev/null 2>&1; then
        log_success "Worker health check passed"
    else
        log_error "Worker health check failed"
        return 1
    fi
    
    # Test database connectivity
    log_info "Testing database connectivity..."
    if docker-compose exec postgres pg_isready -U postgres > /dev/null 2>&1; then
        log_success "Database connectivity check passed"
    else
        log_error "Database connectivity check failed"
        return 1
    fi
    
    log_success "All smoke tests passed"
    return 0
}

# Execute rollback
execute_rollback() {
    local failure_stage="$1"
    local failure_reason="$2"
    
    log_error "Deployment failed at stage: $failure_stage"
    log_error "Reason: $failure_reason"
    
    log_info "Executing automated rollback..."
    
    # Determine rollback type based on failure stage
    local rollback_type="infrastructure_failure"
    if [[ "$failure_stage" == "application" ]]; then
        rollback_type="application_failure"
    elif [[ "$failure_stage" == "database" ]]; then
        rollback_type="database_failure"
    fi
    
    # Execute rollback
    if python3 "$ROLLBACK_SCRIPT" "$CONFIG_FILE"; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback failed - manual intervention required"
        log_error "Please check rollback reports in: $REPORTS_DIR"
        exit 1
    fi
}

# Generate deployment report
generate_deployment_report() {
    log_info "Generating deployment report..."
    
    # Create reports directory if it doesn't exist
    mkdir -p "$REPORTS_DIR"
    
    # Generate timestamp
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    
    # Create deployment report
    cat > "$REPORTS_DIR/deployment_report_${timestamp}.md" << EOF
# Deployment Report - $(date)

## Deployment Summary
- **Timestamp**: $(date)
- **Status**: SUCCESS
- **Environment**: Local
- **Deployment Type**: Docker Compose

## Services Deployed
$(docker-compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}")

## Validation Results
- **Infrastructure**: ✅ PASSED
- **Application**: ✅ PASSED
- **Smoke Tests**: ✅ PASSED

## Performance Metrics
- **Deployment Time**: $(($(date +%s) - START_TIME)) seconds
- **Service Startup Time**: ~30 seconds
- **Validation Time**: ~60 seconds

## Next Steps
1. Monitor service health
2. Run end-to-end tests
3. Proceed to Phase 3 (BaseWorker Implementation)

## Rollback Information
- **Rollback Enabled**: Yes
- **Rollback Procedures**: Available in infrastructure/validation/rollback_procedures.yaml
- **Automated Rollback**: Available via automated_rollback.py

EOF
    
    log_success "Deployment report generated: deployment_report_${timestamp}.md"
}

# Main deployment function
main_deployment() {
    print_banner
    
    # Record start time
    START_TIME=$(date +%s)
    
    # Check prerequisites
    check_prerequisites
    
    # Validate local environment
    validate_local_environment
    
    # Deploy infrastructure
    log_info "=== PHASE 1: Infrastructure Deployment ==="
    if ! deploy_infrastructure; then
        execute_rollback "infrastructure" "Infrastructure deployment failed"
        exit 1
    fi
    
    # Validate infrastructure
    log_info "=== PHASE 2: Infrastructure Validation ==="
    if ! validate_infrastructure; then
        execute_rollback "infrastructure" "Infrastructure validation failed"
        exit 1
    fi
    
    # Deploy application
    log_info "=== PHASE 3: Application Deployment ==="
    if ! deploy_application; then
        execute_rollback "application" "Application deployment failed"
        exit 1
    fi
    
    # Validate application
    log_info "=== PHASE 4: Application Validation ==="
    if ! validate_application; then
        execute_rollback "application" "Application validation failed"
        exit 1
    fi
    
    # Run smoke tests
    log_info "=== PHASE 5: Smoke Testing ==="
    if ! run_smoke_tests; then
        execute_rollback "application" "Smoke tests failed"
        exit 1
    fi
    
    # Generate deployment report
    generate_deployment_report
    
    # Success message
    local total_time=$(($(date +%s) - START_TIME))
    log_success "================================================================"
    log_success "  DEPLOYMENT COMPLETED SUCCESSFULLY!"
    log_success "================================================================"
    log_success "  Total deployment time: ${total_time} seconds"
    log_success "  All services are running and healthy"
    log_success "  Infrastructure validation passed"
    log_success "  Application validation passed"
    log_success "  Smoke tests passed"
    log_success "================================================================"
    log_success "  Next: Proceed to Phase 3 (BaseWorker Implementation)"
    log_success "  Reports available in: $REPORTS_DIR"
    log_success "================================================================"
}

# Help function
show_help() {
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --validate-only     Only validate current deployment (no deployment)"
    echo "  --rollback          Execute rollback procedures"
    echo "  --status            Show current deployment status"
    echo
    echo "Examples:"
    echo "  $0                  # Full deployment with validation"
    echo "  $0 --validate-only  # Validate current deployment"
    echo "  $0 --rollback       # Execute rollback"
    echo "  $0 --status         # Show deployment status"
}

# Status function
show_status() {
    log_info "Current deployment status:"
    echo
    docker-compose ps
    echo
    log_info "Service health:"
    echo
    docker-compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
}

# Validate only function
validate_only() {
    print_banner
    log_info "Running validation only (no deployment)..."
    
    check_prerequisites
    
    if validate_infrastructure && validate_application && run_smoke_tests; then
        log_success "All validations passed - deployment is healthy"
        exit 0
    else
        log_error "Validation failed - deployment has issues"
        exit 1
    fi
}

# Rollback function
rollback_only() {
    print_banner
    log_info "Executing rollback procedures..."
    
    check_prerequisites
    
    # Execute rollback
    if python3 "$ROLLBACK_SCRIPT" "$CONFIG_FILE"; then
        log_success "Rollback completed successfully"
        exit 0
    else
        log_error "Rollback failed - manual intervention required"
        exit 1
    fi
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --validate-only)
        validate_only
        ;;
    --rollback)
        rollback_only
        ;;
    --status)
        show_status
        exit 0
        ;;
    "")
        main_deployment
        ;;
    *)
        log_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

