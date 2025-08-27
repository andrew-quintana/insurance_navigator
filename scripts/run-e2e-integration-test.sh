#!/bin/bash

# End-to-End Integration Test Runner
# This script runs the complete integration test suite for upload pipeline + agent workflows.

set -e  # Exit on any error

echo "🧪 Running End-to-End Integration Tests..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if integration environment is running
check_environment() {
    print_status "Checking integration environment..."
    
    # Check if Docker containers are running
    if ! docker-compose -f docker-compose.mock-integration.yml ps -q | grep -q .; then
        print_error "Integration environment is not running. Please run setup-mock-integration-environment.sh first."
        exit 1
    fi
    
    # Check if services are healthy
    local unhealthy_services=$(docker-compose -f docker-compose.mock-integration.yml ps --format "table {{.Name}}\t{{.Status}}" | grep -v "Up (healthy)" | grep -v "Name" | grep -v "^$" || true)
    
    if [ -n "$unhealthy_services" ]; then
        print_warning "Some services are not healthy:"
        echo "$unhealthy_services"
        print_warning "Tests may fail due to unhealthy services"
    else
        print_success "All services are healthy"
    fi
}

# Run the integration tests
run_tests() {
    print_status "Running integration test suite..."
    
    # Check if pytest is available
    if ! command -v python -m pytest &> /dev/null; then
        print_error "pytest is not available. Please install it and try again."
        exit 1
    fi
    
    # Run the tests
    local test_file="tests/integration/test_mock_e2e_integration.py"
    
    if [ ! -f "$test_file" ]; then
        print_error "Test file not found: $test_file"
        exit 1
    fi
    
    print_status "Executing tests from: $test_file"
    
    # Run tests with verbose output
    python -m pytest "$test_file" -v --tb=short
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "All integration tests passed! 🎉"
    else
        print_error "Some integration tests failed. Check the output above for details."
        print_status "This is expected during the debug → fix → test cycle. Fix the issues and run again."
    fi
    
    return $exit_code
}

# Run tests directly with Python (alternative to pytest)
run_tests_direct() {
    print_status "Running integration tests directly with Python..."
    
    local test_file="tests/integration/test_mock_e2e_integration.py"
    
    if [ ! -f "$test_file" ]; then
        print_error "Test file not found: $test_file"
        exit 1
    fi
    
    print_status "Executing tests from: $test_file"
    
    # Run the test runner directly
    python "$test_file"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "All integration tests passed! 🎉"
    else
        print_error "Some integration tests failed. Check the output above for details."
        print_status "This is expected during the debug → fix → test cycle. Fix the issues and run again."
    fi
    
    return $exit_code
}

# Show test results summary
show_results() {
    print_status "Test Results Summary:"
    echo "========================"
    
    # Check if there are any test artifacts or logs
    if [ -d "logs" ]; then
        print_status "Check logs directory for detailed test output"
    fi
    
    # Show service status
    print_status "Current Service Status:"
    docker-compose -f docker-compose.mock-integration.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    echo "Starting integration tests at $(date)"
    echo ""
    
    # Check environment
    check_environment
    
    # Run tests
    local test_method="pytest"
    
    # Check if pytest is preferred
    if [ "$1" = "--direct" ]; then
        test_method="direct"
    fi
    
    if [ "$test_method" = "pytest" ]; then
        run_tests
    else
        run_tests_direct
    fi
    
    local exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    print_status "Test execution completed in ${duration} seconds"
    
    # Show results
    show_results
    
    echo ""
    print_status "Next steps:"
    if [ $exit_code -eq 0 ]; then
        echo "✓ All tests passed - integration is working correctly"
        echo "1. Proceed to Phase 2 (real API testing)"
        echo "2. Run performance validation tests"
        echo "3. Document successful integration patterns"
    else
        echo "✗ Some tests failed - continue debug → fix → test cycle"
        echo "1. Review test failures and error messages"
        echo "2. Fix identified issues in the integration"
        echo "3. Run tests again to verify fixes"
        echo "4. Repeat until all tests pass"
    fi
    
    echo ""
    print_status "For debugging help:"
    echo "- Check service logs: docker-compose -f docker-compose.mock-integration.yml logs -f"
    echo "- Check integration health: curl http://localhost:8003/integration/health"
    echo "- View test file: $test_file"
    
    return $exit_code
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --direct     Run tests directly with Python instead of pytest"
        echo "  --help, -h   Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                    # Run tests with pytest (default)"
        echo "  $0 --direct           # Run tests directly with Python"
        echo ""
        echo "Prerequisites:"
        echo "  - Integration environment must be running (run setup-mock-integration-environment.sh first)"
        echo "  - All services must be healthy"
        echo "  - Python and pytest must be available"
        exit 0
        ;;
    --direct)
        # Will be handled in main()
        ;;
    "")
        # Default behavior
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac

# Run main function
main "$@"
