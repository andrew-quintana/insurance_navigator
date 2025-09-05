#!/bin/bash

# Phase 1 Workflow Testing Execution Script
# Orchestrates the complete Phase 1 testing process as specified in workflow_testing_spec.md

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
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/phase1_workflow_testing_$TIMESTAMP.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Helper functions
log_info() {
    echo -e "${BLUE}[PHASE1-EXEC]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[PHASE1-EXEC]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[PHASE1-EXEC]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[PHASE1-EXEC]${NC} $1" | tee -a "$LOG_FILE"
}

log_phase() {
    echo -e "${PURPLE}[PHASE1-EXEC]${NC} $1" | tee -a "$LOG_FILE"
}

# Pre-flight checks
preflight_checks() {
    log_phase "=== Pre-flight Checks ==="
    
    # Check if we're in the right directory
    if [ ! -f "$PROJECT_ROOT/package.json" ] || [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
        log_error "Not in project root directory. Please run from insurance_navigator root."
        exit 1
    fi
    
    # Check if .env.production exists
    if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
        log_error "Production environment file not found: .env.production"
        log_info "Please create .env.production with production Supabase credentials"
        log_info "You can use env.production.example as a template"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if required files exist
    local required_files=(
        "docker-compose.phase1-workflow-testing.yml"
        "scripts/testing/phase1-workflow-testing.sh"
        "scripts/testing/phase1-workflow-testing.py"
        "scripts/testing/test-frontend-simulation.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$file" ]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    log_success "Pre-flight checks passed"
}

# Environment setup
setup_environment() {
    log_phase "=== Environment Setup ==="
    
    cd "$PROJECT_ROOT"
    
    # Make scripts executable
    log_info "Making test scripts executable..."
    chmod +x scripts/testing/phase1-workflow-testing.sh
    chmod +x scripts/testing/phase1-workflow-testing.py
    chmod +x scripts/testing/test-frontend-simulation.sh
    
    # Create test data directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/test_data"
    
    # Copy test documents if they exist
    if [ -f "$PROJECT_ROOT/examples/simulated_insurance_document.pdf" ]; then
        cp "$PROJECT_ROOT/examples/simulated_insurance_document.pdf" "$PROJECT_ROOT/test_data/"
        log_success "Test document copied to test_data/"
    fi
    
    if [ -f "$PROJECT_ROOT/examples/scan_classic_hmo_parsed.pdf" ]; then
        cp "$PROJECT_ROOT/examples/scan_classic_hmo_parsed.pdf" "$PROJECT_ROOT/test_data/"
        log_success "Additional test document copied to test_data/"
    fi
    
    log_success "Environment setup completed"
}

# Execute Phase 1 testing
execute_phase1_testing() {
    log_phase "=== Executing Phase 1 Testing ==="
    
    cd "$PROJECT_ROOT"
    
    # Choose testing method based on available dependencies
    if command -v python3 > /dev/null 2>&1 && python3 -c "import aiohttp" > /dev/null 2>&1; then
        log_info "Using Python-based comprehensive testing..."
        python3 scripts/testing/phase1-workflow-testing.py 2>&1 | tee -a "$LOG_FILE"
    else
        log_info "Using Bash-based testing (Python aiohttp not available)..."
        ./scripts/testing/phase1-workflow-testing.sh 2>&1 | tee -a "$LOG_FILE"
    fi
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "Phase 1 testing completed successfully"
    else
        log_error "Phase 1 testing failed with exit code $exit_code"
    fi
    
    return $exit_code
}

# Generate test report
generate_test_report() {
    log_phase "=== Generating Test Report ==="
    
    cd "$PROJECT_ROOT"
    
    # Check if test report was generated
    if [ -f "phase1_test_report.json" ]; then
        log_success "Test report found: phase1_test_report.json"
        
        # Pretty print the report
        if command -v jq > /dev/null 2>&1; then
            log_info "Test Report Summary:"
            jq '.summary' phase1_test_report.json
        else
            log_info "Test report generated but jq not available for pretty printing"
        fi
    else
        log_warning "No test report found"
    fi
    
    # List all log files
    log_info "Log files generated:"
    ls -la "$LOG_DIR"/phase1_workflow_testing_*.log 2>/dev/null || log_warning "No log files found"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up Phase 1 testing environment..."
    
    cd "$PROJECT_ROOT"
    
    # Stop any running Docker services
    if [ -f "docker-compose.phase1-workflow-testing.yml" ]; then
        docker-compose -f docker-compose.phase1-workflow-testing.yml down --remove-orphans || true
    fi
    
    # Clean up test artifacts
    rm -f /tmp/phase1_test_*
    rm -f /tmp/test_job_id
    rm -f /tmp/test_document_id
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    log_info "🚀 Starting Phase 1 Workflow Testing Execution"
    log_info "Project Root: $PROJECT_ROOT"
    log_info "Log File: $LOG_FILE"
    log_info "Timestamp: $TIMESTAMP"
    echo
    
    # Set up trap for cleanup
    trap cleanup EXIT
    
    # Execute phases
    preflight_checks
    setup_environment
    execute_phase1_testing
    local test_exit_code=$?
    generate_test_report
    
    # Final summary
    echo
    log_phase "=== Phase 1 Testing Execution Summary ==="
    if [ $test_exit_code -eq 0 ]; then
        log_success "✅ Phase 1 testing completed successfully!"
        log_info "Check the test report and logs for detailed results"
        exit 0
    else
        log_error "❌ Phase 1 testing failed!"
        log_info "Check the logs for error details: $LOG_FILE"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Phase 1 Workflow Testing Execution Script"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --cleanup      Only run cleanup (stop services, remove artifacts)"
        echo "  --preflight    Only run pre-flight checks"
        echo "  --setup        Only run environment setup"
        echo
        echo "Examples:"
        echo "  $0                    # Run complete Phase 1 testing"
        echo "  $0 --cleanup          # Clean up test environment"
        echo "  $0 --preflight        # Check prerequisites only"
        echo "  $0 --setup            # Set up environment only"
        exit 0
        ;;
    --cleanup)
        cleanup
        exit 0
        ;;
    --preflight)
        preflight_checks
        exit 0
        ;;
    --setup)
        preflight_checks
        setup_environment
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown option: $1"
        log_info "Use --help for usage information"
        exit 1
        ;;
esac
