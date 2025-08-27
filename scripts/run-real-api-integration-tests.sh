#!/bin/bash

# Real API Integration Test Runner for Phase 2
# This script runs comprehensive integration tests with real LlamaParse and OpenAI APIs
# and provides detailed reporting for the debug → fix → test cycle.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.real-api"
TEST_FILE="tests/integration/test_real_api_integration.py"
RESULTS_DIR="$PROJECT_ROOT/test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}=== Real API Integration Test Runner ===${NC}"
echo "Running comprehensive integration tests with real APIs for Phase 2"
echo "Timestamp: $TIMESTAMP"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file not found: $ENV_FILE"
        print_warning "Please run setup-real-api-environment.sh first"
        exit 1
    fi
    
    # Check if test file exists
    if [ ! -f "$PROJECT_ROOT/$TEST_FILE" ]; then
        print_error "Test file not found: $TEST_FILE"
        exit 1
    fi
    
    # Check if Python and pytest are available
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    if ! python -m pytest --version &> /dev/null; then
        print_error "pytest is not installed. Please install it: pip install pytest"
        exit 1
    fi
    
    # Check if real API environment is running
    if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_warning "API server not responding. Please ensure real API environment is running."
        print_warning "Run: ./scripts/setup-real-api-environment.sh"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Load environment variables
load_environment() {
    print_status "Loading environment variables..."
    
    if [ -f "$ENV_FILE" ]; then
        export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
        print_status "Environment variables loaded from $ENV_FILE"
    else
        print_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    # Validate critical environment variables
    if [ -z "$LLAMAPARSE_API_KEY" ] || [ "$LLAMAPARSE_API_KEY" = "your_actual_llamaparse_api_key_here" ]; then
        print_error "LLAMAPARSE_API_KEY not properly configured"
        exit 1
    fi
    
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_actual_openai_api_key_here" ]; then
        print_error "OPENAI_API_KEY not properly configured"
        exit 1
    fi
    
    print_status "Environment validation passed"
}

# Create results directory
create_results_directory() {
    print_status "Creating results directory..."
    
    mkdir -p "$RESULTS_DIR"
    RESULTS_FILE="$RESULTS_DIR/real_api_integration_results_$TIMESTAMP.json"
    
    print_status "Results will be saved to: $RESULTS_FILE"
}

# Run pre-test validation
run_pre_test_validation() {
    print_status "Running pre-test validation..."
    
    cd "$PROJECT_ROOT"
    
    # Check service health
    print_status "Checking service health..."
    
    local services=(
        "http://localhost:8000/health"
        "http://localhost:8003/health"
        "http://localhost:8004/health"
    )
    
    for service in "${services[@]}"; do
        if curl -f "$service" > /dev/null 2>&1; then
            print_status "Service healthy: $service"
        else
            print_error "Service unhealthy: $service"
            exit 1
        fi
    done
    
    # Check database connectivity
    print_status "Checking database connectivity..."
    if docker-compose -f docker-compose.real-api.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        print_status "Database connectivity: OK"
    else
        print_error "Database connectivity: Failed"
        exit 1
    fi
    
    print_status "Pre-test validation completed successfully"
}

# Run integration tests
run_integration_tests() {
    print_status "Running real API integration tests..."
    
    cd "$PROJECT_ROOT"
    
    # Set test environment variables
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export TESTING_MODE=true
    export ENVIRONMENT=real_api_testing
    
    # Run tests with detailed output and save results
    print_status "Executing test suite..."
    
    if python -m pytest "$TEST_FILE" -v --tb=short --json-report="$RESULTS_FILE" --json-report-summary; then
        print_status "All tests passed successfully!"
        TEST_RESULT="PASSED"
    else
        print_warning "Some tests failed. Check results for details."
        TEST_RESULT="FAILED"
    fi
    
    print_status "Test execution completed"
}

# Generate test report
generate_test_report() {
    print_status "Generating comprehensive test report..."
    
    cd "$PROJECT_ROOT"
    
    # Create human-readable report
    REPORT_FILE="$RESULTS_DIR/real_api_integration_report_$TIMESTAMP.md"
    
    cat > "$REPORT_FILE" << EOF
# Real API Integration Test Report

**Generated**: $(date)
**Timestamp**: $TIMESTAMP
**Test Result**: $TEST_RESULT

## Test Summary

- **Test Suite**: Real API Integration Tests
- **Environment**: Real LlamaParse and OpenAI APIs
- **Total Tests**: $(grep -c "def test_" "$PROJECT_ROOT/$TEST_FILE" || echo "Unknown")
- **Result**: $TEST_RESULT

## Environment Configuration

- **LlamaParse API**: ${LLAMAPARSE_API_URL:-"Not configured"}
- **OpenAI API**: ${OPENAI_API_URL:-"Not configured"}
- **Database**: ${DATABASE_URL:-"Not configured"}
- **Environment**: ${ENVIRONMENT:-"Not configured"}

## Test Results

EOF
    
    # Add test results if available
    if [ -f "$RESULTS_FILE" ]; then
        echo "### Detailed Results" >> "$REPORT_FILE"
        echo "See JSON results file: \`$RESULTS_FILE\`" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        
        # Extract summary information if jq is available
        if command -v jq &> /dev/null; then
            echo "### Test Summary" >> "$REPORT_FILE"
            jq -r '.summary | "**Total Tests:** \(.total)\n**Passed:** \(.passed)\n**Failed:** \(.failed)\n**Skipped:** \(.skipped)"' "$RESULTS_FILE" >> "$REPORT_FILE" 2>/dev/null || echo "Could not parse JSON results" >> "$REPORT_FILE"
        fi
    fi
    
    # Add next steps
    cat >> "$REPORT_FILE" << EOF

## Next Steps

### If Tests Passed
1. Review test results for any warnings or performance issues
2. Proceed to Phase 3 (Documentation & Handoff)
3. Document any real API-specific configurations or learnings

### If Tests Failed
1. Review the debug → fix → test cycle approach
2. Check service logs for errors: \`docker-compose -f docker-compose.real-api.yml logs\`
3. Validate API credentials and connectivity
4. Fix identified issues and re-run tests

## Debug Information

- **Service Logs**: \`docker-compose -f docker-compose.real-api.yml logs -f\`
- **Health Checks**: 
  - API Server: \`curl http://localhost:8000/health\`
  - Agent API: \`curl http://localhost:8003/health\`
  - Monitoring: \`curl http://localhost:8004/health\`
- **Database**: \`docker-compose -f docker-compose.real-api.yml exec postgres psql -U postgres -d accessa_dev\`

## Cost Monitoring

**Note**: This test suite uses real APIs and may incur costs.
- Monitor your LlamaParse API usage
- Monitor your OpenAI API usage
- Set appropriate rate limits and quotas

EOF
    
    print_status "Test report generated: $REPORT_FILE"
}

# Display results summary
display_results_summary() {
    echo ""
    echo -e "${BLUE}=== Test Execution Summary ===${NC}"
    echo ""
    echo "Test Result: $TEST_RESULT"
    echo "Timestamp: $TIMESTAMP"
    echo ""
    echo "Files Generated:"
    echo "  - JSON Results: $RESULTS_FILE"
    echo "  - Test Report: $REPORT_FILE"
    echo ""
    
    if [ "$TEST_RESULT" = "PASSED" ]; then
        echo -e "${GREEN}🎉 All tests passed! Ready to proceed to Phase 3.${NC}"
    else
        echo -e "${YELLOW}⚠️  Some tests failed. Review results and fix issues before proceeding.${NC}"
        echo ""
        echo "Debug → Fix → Test Cycle:"
        echo "1. Review test failures in the report"
        echo "2. Check service logs for errors"
        echo "3. Fix identified issues"
        echo "4. Re-run tests: ./scripts/run-real-api-integration-tests.sh"
    fi
    
    echo ""
    echo "Next Steps:"
    echo "1. Review detailed results: $RESULTS_FILE"
    echo "2. Read test report: $REPORT_FILE"
    echo "3. Check service logs if needed"
    echo "4. Proceed based on test results"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    
    # Any cleanup tasks can go here
    print_status "Cleanup completed"
}

# Main execution
main() {
    echo "Starting real API integration test execution..."
    echo "Project root: $PROJECT_ROOT"
    echo ""
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    check_prerequisites
    load_environment
    create_results_directory
    run_pre_test_validation
    run_integration_tests
    generate_test_report
    display_results_summary
    
    echo ""
    print_status "Real API integration test execution completed!"
}

# Run main function
main "$@"
