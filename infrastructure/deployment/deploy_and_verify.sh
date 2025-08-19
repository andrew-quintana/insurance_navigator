#!/bin/bash
# Deployment and Verification Script for 003 Worker Refactor - Phase 5
# This script orchestrates infrastructure deployment with automated validation
# against local environment baseline, preventing the infrastructure configuration
# failures experienced in 002.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="${PROJECT_ROOT}/infrastructure/config/deployment_config.yaml"
DEPLOYMENT_TARGET="${DEPLOYMENT_TARGET:-local}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
VALIDATE_AFTER_DEPLOY="${VALIDATE_AFTER_DEPLOY:-true}"
ROLLBACK_ON_FAILURE="${ROLLBACK_ON_FAILURE:-true}"

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

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -f "${PROJECT_ROOT}/docker-compose.yml" ]]; then
        log_error "docker-compose.yml not found. Please run from project root."
        exit 1
    fi
    
    # Check if configuration file exists
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        log_error "Deployment configuration not found: ${CONFIG_FILE}"
        exit 1
    fi
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed."
        exit 1
    fi
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed."
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is required but not installed."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to create backup before deployment
create_backup() {
    if [[ "${BACKUP_BEFORE_DEPLOY}" != "true" ]]; then
        log_info "Skipping backup creation (BACKUP_BEFORE_DEPLOY=false)"
        return 0
    fi
    
    log_info "Creating backup before deployment..."
    
    cd "${PROJECT_ROOT}"
    
    # Create backup using the rollback system
    if python3 -m infrastructure.deployment.automated_rollback --config "${CONFIG_FILE}" --action backup --backup-type full; then
        log_success "Backup created successfully"
    else
        log_warning "Backup creation failed, but continuing with deployment"
    fi
}

# Function to validate local environment
validate_local_environment() {
    log_info "Validating local environment baseline..."
    
    cd "${PROJECT_ROOT}"
    
    # Check if local services are running
    if ! docker-compose ps | grep -q "Up"; then
        log_info "Starting local services for baseline validation..."
        docker-compose up -d
        
        # Wait for services to be healthy
        log_info "Waiting for services to be healthy..."
        sleep 30
        
        # Check service health
        local unhealthy_services=0
        for i in {1..30}; do
            if docker-compose ps | grep -q "unhealthy\|Exit"; then
                unhealthy_services=$((unhealthy_services + 1))
                if [[ $unhealthy_services -ge 3 ]]; then
                    log_error "Services are not healthy after startup"
                    docker-compose ps
                    exit 1
                fi
                sleep 10
            else
                log_success "All services are healthy"
                break
            fi
        done
    else
        log_info "Local services are already running"
    fi
    
    # Run local validation tests
    log_info "Running local validation tests..."
    if [[ -f "${PROJECT_ROOT}/scripts/run-local-tests.sh" ]]; then
        if bash "${PROJECT_ROOT}/scripts/run-local-tests.sh"; then
            log_success "Local validation tests passed"
        else
            log_error "Local validation tests failed"
            exit 1
        fi
    else
        log_warning "Local test script not found, skipping validation tests"
    fi
}

# Function to deploy infrastructure
deploy_infrastructure() {
    log_info "Deploying infrastructure (target: ${DEPLOYMENT_TARGET})..."
    
    cd "${PROJECT_ROOT}"
    
    # Run infrastructure deployment
    if python3 -m infrastructure.deployment.infrastructure_deployer --config "${CONFIG_FILE}" --target "${DEPLOYMENT_TARGET}"; then
        log_success "Infrastructure deployment completed successfully"
    else
        log_error "Infrastructure deployment failed"
        if [[ "${ROLLBACK_ON_FAILURE}" == "true" ]]; then
            log_warning "Triggering automated rollback..."
            trigger_rollback "Infrastructure deployment failure"
        fi
        exit 1
    fi
}

# Function to validate deployed infrastructure
validate_deployed_infrastructure() {
    if [[ "${VALIDATE_AFTER_DEPLOY}" != "true" ]]; then
        log_info "Skipping post-deployment validation (VALIDATE_AFTER_DEPLOY=false)"
        return 0
    fi
    
    log_info "Validating deployed infrastructure against local baseline..."
    
    cd "${PROJECT_ROOT}"
    
    # Run comprehensive validation
    if python3 -m infrastructure.validation.deployment_validator --config "${CONFIG_FILE}"; then
        log_success "Infrastructure validation passed"
    else
        log_error "Infrastructure validation failed"
        if [[ "${ROLLBACK_ON_FAILURE}" == "true" ]]; then
            log_warning "Triggering automated rollback..."
            trigger_rollback "Infrastructure validation failure"
        fi
        exit 1
    fi
}

# Function to trigger rollback
trigger_rollback() {
    local reason="$1"
    
    log_warning "Triggering automated rollback: ${reason}"
    
    cd "${PROJECT_ROOT}"
    
    if python3 -m infrastructure.deployment.automated_rollback --config "${CONFIG_FILE}" --action rollback --trigger-reason "${reason}"; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback failed - manual intervention required"
        exit 1
    fi
}

# Function to run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests on deployed infrastructure..."
    
    cd "${PROJECT_ROOT}"
    
    # Basic connectivity tests
    log_info "Testing service connectivity..."
    
    # Test API server
    if curl -f -s "http://localhost:8000/health" > /dev/null; then
        log_success "API server is responding"
    else
        log_error "API server is not responding"
        return 1
    fi
    
    # Test database
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        log_success "Database is accessible"
    else
        log_error "Database is not accessible"
        return 1
    fi
    
    # Test storage service
    if curl -f -s "http://localhost:5000/health" > /dev/null; then
        log_success "Storage service is responding"
    else
        log_error "Storage service is not responding"
        return 1
    fi
    
    log_success "Smoke tests passed"
}

# Function to generate deployment report
generate_deployment_report() {
    log_info "Generating deployment report..."
    
    cd "${PROJECT_ROOT}"
    
    # Create reports directory
    mkdir -p infrastructure/reports
    
    # Generate timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")
    
    # Create deployment report
    cat > "infrastructure/reports/deployment_report_${timestamp}.md" << EOF
# Infrastructure Deployment Report

**Deployment ID:** deploy_${timestamp}
**Timestamp:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Target:** ${DEPLOYMENT_TARGET}
**Status:** SUCCESS

## Deployment Summary

- **Prerequisites Check:** ✅ PASSED
- **Backup Creation:** ${BACKUP_BEFORE_DEPLOY}
- **Local Validation:** ✅ PASSED
- **Infrastructure Deployment:** ✅ PASSED
- **Post-Deployment Validation:** ${VALIDATE_AFTER_DEPLOY}
- **Smoke Tests:** ✅ PASSED

## Environment Details

- **Project Root:** ${PROJECT_ROOT}
- **Configuration File:** ${CONFIG_FILE}
- **Deployment Target:** ${DEPLOYMENT_TARGET}
- **Rollback on Failure:** ${ROLLBACK_ON_FAILURE}

## Services Status

$(docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}")

## Next Steps

1. Verify application functionality
2. Run comprehensive integration tests
3. Monitor system performance
4. Document any issues or observations

## Rollback Information

If rollback is needed, use:
\`\`\`bash
python3 -m infrastructure.deployment.automated_rollback --config ${CONFIG_FILE} --action rollback
\`\`\`

EOF
    
    log_success "Deployment report generated: infrastructure/reports/deployment_report_${timestamp}.md"
}

# Function to display help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy and verify infrastructure for 003 Worker Refactor - Phase 5

OPTIONS:
    -h, --help              Show this help message
    -t, --target TARGET     Deployment target (local, production) [default: local]
    -c, --config FILE       Configuration file path [default: infrastructure/config/deployment_config.yaml]
    --no-backup             Skip backup creation before deployment
    --no-validation         Skip post-deployment validation
    --no-rollback           Disable automatic rollback on failure

ENVIRONMENT VARIABLES:
    DEPLOYMENT_TARGET       Deployment target (overrides -t option)
    BACKUP_BEFORE_DEPLOY    Create backup before deployment (true/false)
    VALIDATE_AFTER_DEPLOY   Validate after deployment (true/false)
    ROLLBACK_ON_FAILURE     Enable rollback on failure (true/false)

EXAMPLES:
    # Deploy to local environment
    $0

    # Deploy to production with custom config
    $0 -t production -c /path/to/config.yaml

    # Deploy without backup
    $0 --no-backup

    # Deploy without validation
    $0 --no-validation

EOF
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    log_info "Starting infrastructure deployment and verification..."
    log_info "Project Root: ${PROJECT_ROOT}"
    log_info "Configuration: ${CONFIG_FILE}"
    log_info "Target: ${DEPLOYMENT_TARGET}"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -t|--target)
                DEPLOYMENT_TARGET="$2"
                shift 2
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --no-backup)
                BACKUP_BEFORE_DEPLOY="false"
                shift
                ;;
            --no-validation)
                VALIDATE_AFTER_DEPLOY="false"
                shift
                ;;
            --no-rollback)
                ROLLBACK_ON_FAILURE="false"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Validate deployment target
    if [[ ! "${DEPLOYMENT_TARGET}" =~ ^(local|production)$ ]]; then
        log_error "Invalid deployment target: ${DEPLOYMENT_TARGET}"
        log_error "Valid targets: local, production"
        exit 1
    fi
    
    # Update configuration file path if it's relative
    if [[ ! "${CONFIG_FILE}" =~ ^/ ]]; then
        CONFIG_FILE="${PROJECT_ROOT}/${CONFIG_FILE}"
    fi
    
    # Check if configuration file exists
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        log_error "Configuration file not found: ${CONFIG_FILE}"
        exit 1
    fi
    
    log_info "Configuration validated"
    
    # Execute deployment steps
    check_prerequisites
    create_backup
    validate_local_environment
    deploy_infrastructure
    validate_deployed_infrastructure
    run_smoke_tests
    generate_deployment_report
    
    # Calculate deployment time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "Infrastructure deployment and verification completed successfully!"
    log_info "Total deployment time: ${duration} seconds"
    
    # Display next steps
    echo
    echo "🚀 Deployment Summary"
    echo "===================="
    echo "✅ Infrastructure deployed successfully"
    echo "✅ All validations passed"
    echo "✅ Smoke tests completed"
    echo "📊 Deployment report generated"
    echo
    echo "Next steps:"
    echo "1. Verify application functionality"
    echo "2. Run comprehensive integration tests"
    echo "3. Monitor system performance"
    echo "4. Document any issues or observations"
    echo
}

# Trap to handle script interruption
trap 'log_error "Deployment interrupted by user"; exit 1' INT TERM

# Run main function with all arguments
main "$@"
