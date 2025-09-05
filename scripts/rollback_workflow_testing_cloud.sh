#!/bin/bash

# Workflow Testing Cloud Rollback Script
# Phase 2: Cloud Deployment Testing
# Provides rollback and recovery procedures for cloud deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RENDER_CONFIG="$PROJECT_ROOT/config/render/render.workflow-testing.yaml"
VERCEL_CONFIG="$PROJECT_ROOT/ui/vercel.workflow-testing.json"
ENV_FILE="$PROJECT_ROOT/env.workflow-testing-cloud"

***REMOVED***
API_URL=""
WORKER_URL=""
FRONTEND_URL=""

# Rollback options
ROLLBACK_TO_PHASE1=false
ROLLBACK_API=false
ROLLBACK_FRONTEND=false
ROLLBACK_WORKER=false
FORCE_ROLLBACK=false

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking rollback prerequisites..."
    
    # Check if required tools are installed
    if ! command -v render &> /dev/null; then
        print_error "Render CLI is not installed. Please install it from https://render.com/docs/cli"
        exit 1
    fi
    
    if ! command -v vercel &> /dev/null; then
        print_error "Vercel CLI is not installed. Please install it from https://vercel.com/docs/cli"
        exit 1
    fi
    
    # Check if logged in to services
    if ! render auth whoami &> /dev/null; then
        print_error "Not logged in to Render CLI. Please run 'render auth login'"
        exit 1
    fi
    
    if ! vercel whoami &> /dev/null; then
        print_error "Not logged in to Vercel CLI. Please run 'vercel login'"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to get current service status
get_service_status() {
    print_status "Getting current service status..."
    
    # Get Render service status
    if render services list --format json &> /dev/null; then
        API_URL=$(render services list --format json | jq -r '.[] | select(.name=="insurance-navigator-api-workflow-testing") | .serviceUrl // empty')
        WORKER_URL=$(render services list --format json | jq -r '.[] | select(.name=="insurance-navigator-worker-workflow-testing") | .serviceUrl // empty')
    fi
    
    # Get Vercel deployment status
    if vercel ls --format json &> /dev/null; then
        FRONTEND_URL=$(vercel ls --format json | jq -r '.[] | select(.name=="insurance-navigator-frontend-workflow-testing") | .url // empty')
    fi
    
    print_status "Current service URLs:"
    print_status "  API: $API_URL"
    print_status "  Worker: $WORKER_URL"
    print_status "  Frontend: $FRONTEND_URL"
}

# Function to check service health before rollback
check_service_health() {
    print_status "Checking service health before rollback..."
    
    local unhealthy_services=()
    
    # Check API health
    if [[ -n "$API_URL" ]]; then
        if curl -f "$API_URL/health" &> /dev/null; then
            print_success "API service is healthy"
        else
            print_warning "API service is unhealthy"
            unhealthy_services+=("api")
        fi
    fi
    
    # Check Frontend health
    if [[ -n "$FRONTEND_URL" ]]; then
        if curl -f "$FRONTEND_URL/health" &> /dev/null; then
            print_success "Frontend service is healthy"
        else
            print_warning "Frontend service is unhealthy"
            unhealthy_services+=("frontend")
        fi
    fi
    
    if [[ ${#unhealthy_services[@]} -gt 0 ]]; then
        print_warning "Unhealthy services detected: ${unhealthy_services[*]}"
        if [[ "$FORCE_ROLLBACK" == "false" ]]; then
            print_warning "Use --force to proceed with rollback despite unhealthy services"
            return 1
        fi
    fi
    
    return 0
}

# Function to rollback to Phase 1 (local Docker)
rollback_to_phase1() {
    print_status "Rolling back to Phase 1 (local Docker environment)..."
    
    # Stop cloud services
    print_status "Stopping cloud services..."
    
    if [[ "$ROLLBACK_API" == "true" || "$ROLLBACK_TO_PHASE1" == "true" ]]; then
        print_status "Stopping API service..."
        if render services list --format json | jq -r '.[] | select(.name=="insurance-navigator-api-workflow-testing") | .id' | xargs -I {} render services stop {} &> /dev/null; then
            print_success "API service stopped"
        else
            print_warning "Failed to stop API service (may already be stopped)"
        fi
    fi
    
    if [[ "$ROLLBACK_WORKER" == "true" || "$ROLLBACK_TO_PHASE1" == "true" ]]; then
        print_status "Stopping Worker service..."
        if render services list --format json | jq -r '.[] | select(.name=="insurance-navigator-worker-workflow-testing") | .id' | xargs -I {} render services stop {} &> /dev/null; then
            print_success "Worker service stopped"
        else
            print_warning "Failed to stop Worker service (may already be stopped)"
        fi
    fi
    
    # Start local Docker environment
    print_status "Starting local Docker environment..."
    if [[ -f "$PROJECT_ROOT/scripts/start_workflow_testing.sh" ]]; then
        "$PROJECT_ROOT/scripts/start_workflow_testing.sh"
        print_success "Local Docker environment started"
    else
        print_error "Local Docker startup script not found"
        return 1
    fi
    
    # Validate local environment
    print_status "Validating local environment..."
    if [[ -f "$PROJECT_ROOT/scripts/validate_workflow_testing.py" ]]; then
        python3 "$PROJECT_ROOT/scripts/validate_workflow_testing.py"
        print_success "Local environment validation completed"
    else
        print_warning "Local validation script not found, skipping validation"
    fi
}

# Function to rollback specific services
rollback_services() {
    print_status "Rolling back specific services..."
    
    if [[ "$ROLLBACK_API" == "true" ]]; then
        print_status "Rolling back API service..."
        if render services list --format json | jq -r '.[] | select(.name=="insurance-navigator-api-workflow-testing") | .id' | xargs -I {} render services stop {} &> /dev/null; then
            print_success "API service rolled back"
        else
            print_error "Failed to rollback API service"
            return 1
        fi
    fi
    
    if [[ "$ROLLBACK_WORKER" == "true" ]]; then
        print_status "Rolling back Worker service..."
        if render services list --format json | jq -r '.[] | select(.name=="insurance-navigator-worker-workflow-testing") | .id' | xargs -I {} render services stop {} &> /dev/null; then
            print_success "Worker service rolled back"
        else
            print_error "Failed to rollback Worker service"
            return 1
        fi
    fi
    
    if [[ "$ROLLBACK_FRONTEND" == "true" ]]; then
        print_status "Rolling back Frontend service..."
        # Vercel doesn't have a direct rollback command, but we can redeploy
        cd "$PROJECT_ROOT/ui"
        if vercel --prod &> /dev/null; then
            print_success "Frontend service rolled back"
        else
            print_error "Failed to rollback Frontend service"
            return 1
        fi
        cd "$PROJECT_ROOT"
    fi
}

# Function to restore from backup
restore_from_backup() {
    print_status "Restoring from backup..."
    
    # Check if backup exists
    local backup_dir="$PROJECT_ROOT/backups"
    if [[ ! -d "$backup_dir" ]]; then
        print_error "Backup directory not found: $backup_dir"
        return 1
    fi
    
    # Find latest backup
    local latest_backup=$(find "$backup_dir" -name "workflow_testing_*.tar.gz" | sort -r | head -1)
    if [[ -z "$latest_backup" ]]; then
        print_error "No backup files found in $backup_dir"
        return 1
    fi
    
    print_status "Found backup: $latest_backup"
    
    # Extract backup
    local temp_dir=$(mktemp -d)
    tar -xzf "$latest_backup" -C "$temp_dir"
    
    # Restore configuration files
    if [[ -f "$temp_dir/docker-compose.workflow-testing.yml" ]]; then
        cp "$temp_dir/docker-compose.workflow-testing.yml" "$PROJECT_ROOT/"
        print_success "Restored docker-compose configuration"
    fi
    
    if [[ -f "$temp_dir/env.workflow-testing" ]]; then
        cp "$temp_dir/env.workflow-testing" "$PROJECT_ROOT/"
        print_success "Restored environment configuration"
    fi
    
    # Cleanup
    rm -rf "$temp_dir"
    
    print_success "Backup restored successfully"
}

# Function to create emergency backup
create_emergency_backup() {
    print_status "Creating emergency backup..."
    
    local backup_dir="$PROJECT_ROOT/backups"
    mkdir -p "$backup_dir"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$backup_dir/workflow_testing_emergency_$timestamp.tar.gz"
    
    # Create backup
    tar -czf "$backup_file" \
        -C "$PROJECT_ROOT" \
        docker-compose.workflow-testing.yml \
        env.workflow-testing \
        env.workflow-testing-cloud \
        config/render/render.workflow-testing.yaml \
        ui/vercel.workflow-testing.json \
        scripts/ \
        --exclude="node_modules" \
        --exclude=".git" \
        --exclude="*.log"
    
    print_success "Emergency backup created: $backup_file"
}

# Function to validate rollback
validate_rollback() {
    print_status "Validating rollback..."
    
    # Wait for services to stabilize
    sleep 10
    
    # Check if we're rolling back to Phase 1
    if [[ "$ROLLBACK_TO_PHASE1" == "true" ]]; then
        # Validate local Docker environment
        if [[ -f "$PROJECT_ROOT/scripts/validate_workflow_testing.py" ]]; then
            python3 "$PROJECT_ROOT/scripts/validate_workflow_testing.py"
            print_success "Phase 1 rollback validation completed"
        fi
    else
        # Validate remaining cloud services
        if [[ -f "$PROJECT_ROOT/scripts/validate_workflow_testing_cloud.py" ]]; then
            python3 "$PROJECT_ROOT/scripts/validate_workflow_testing_cloud.py"
            print_success "Cloud rollback validation completed"
        fi
    fi
}

# Function to display rollback summary
display_rollback_summary() {
    print_success "Rollback completed successfully!"
    echo ""
    echo "=== ROLLBACK SUMMARY ==="
    
    if [[ "$ROLLBACK_TO_PHASE1" == "true" ]]; then
        echo "Rolled back to: Phase 1 (Local Docker)"
        echo "Local services:"
        echo "  - API: http://localhost:8000"
        echo "  - Frontend: http://localhost:3000"
        echo "  - Monitoring: http://localhost:3001"
    else
        echo "Rolled back services:"
        if [[ "$ROLLBACK_API" == "true" ]]; then
            echo "  - API: Stopped"
        fi
        if [[ "$ROLLBACK_WORKER" == "true" ]]; then
            echo "  - Worker: Stopped"
        fi
        if [[ "$ROLLBACK_FRONTEND" == "true" ]]; then
            echo "  - Frontend: Redeployed"
        fi
    fi
    
    echo ""
    echo "=== NEXT STEPS ==="
    echo "1. Verify all services are working correctly"
    echo "2. Check logs for any issues"
    echo "3. Investigate the cause of the rollback"
    echo "4. Plan remediation before redeploying"
    echo ""
}

# Function to cleanup on error
cleanup() {
    print_error "Rollback failed. Cleaning up..."
    
    # Add cleanup logic here if needed
    # For now, just exit with error code
    exit 1
}

# Main rollback function
main() {
    print_status "Starting Phase 2 rollback procedure"
    print_status "Rolling back cloud deployment to previous state"
    echo ""
    
    # Set up error handling
    trap cleanup ERR
    
    # Check prerequisites
    check_prerequisites
    
    # Get current service status
    get_service_status
    
    # Check service health
    if ! check_service_health; then
        if [[ "$FORCE_ROLLBACK" == "false" ]]; then
            print_error "Rollback aborted due to unhealthy services"
            exit 1
        fi
    fi
    
    # Create emergency backup
    create_emergency_backup
    
    # Perform rollback
    if [[ "$ROLLBACK_TO_PHASE1" == "true" ]]; then
        rollback_to_phase1
    else
        rollback_services
    fi
    
    # Validate rollback
    validate_rollback
    
    # Display summary
    display_rollback_summary
    
    print_success "Phase 2 rollback completed successfully!"
}

# Handle command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --phase1)
            ROLLBACK_TO_PHASE1=true
            shift
            ;;
        --api)
            ROLLBACK_API=true
            shift
            ;;
        --frontend)
            ROLLBACK_FRONTEND=true
            shift
            ;;
        --worker)
            ROLLBACK_WORKER=true
            shift
            ;;
        --force)
            FORCE_ROLLBACK=true
            shift
            ;;
        --restore-backup)
            restore_from_backup
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --phase1          Rollback to Phase 1 (local Docker)"
            echo "  --api             Rollback API service only"
            echo "  --frontend        Rollback Frontend service only"
            echo "  --worker          Rollback Worker service only"
            echo "  --force           Force rollback despite unhealthy services"
            echo "  --restore-backup  Restore from backup instead of rollback"
            echo "  --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --phase1                    # Rollback to local Docker"
            echo "  $0 --api --frontend           # Rollback API and Frontend"
            echo "  $0 --force --api              # Force rollback API service"
            echo "  $0 --restore-backup           # Restore from backup"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# If no specific services specified, rollback all
if [[ "$ROLLBACK_TO_PHASE1" == "false" && "$ROLLBACK_API" == "false" && "$ROLLBACK_FRONTEND" == "false" && "$ROLLBACK_WORKER" == "false" ]]; then
    ROLLBACK_API=true
    ROLLBACK_FRONTEND=true
    ROLLBACK_WORKER=true
fi

# Run main rollback
main
