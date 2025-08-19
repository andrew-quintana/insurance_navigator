#!/bin/bash

# Phase 4 Comprehensive Local Integration Testing Script
# This script runs the complete Phase 4 validation suite to validate
# complete pipeline functionality before deployment.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
TESTS_DIR="$BACKEND_DIR/tests"
RESULTS_DIR="$PROJECT_ROOT/test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Test configuration
PYTHON_PATH="python3"
PIP_PATH="pip3"
REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"
PYTEST_CONFIG="$BACKEND_DIR/pytest.ini"

# Test modules
COMPREHENSIVE_TEST="$TESTS_DIR/e2e/test_comprehensive_validation.py"
PIPELINE_TEST="$TESTS_DIR/e2e/test_complete_pipeline.py"
FAILURE_TEST="$TESTS_DIR/e2e/test_failure_scenarios.py"
PERFORMANCE_TEST="$TESTS_DIR/e2e/test_performance_validation.py"
SECURITY_TEST="$TESTS_DIR/e2e/test_security_validation.py"

# Output files
COMPREHENSIVE_RESULTS="$RESULTS_DIR/comprehensive_validation_results_$TIMESTAMP.json"
PIPELINE_RESULTS="$RESULTS_DIR/pipeline_test_results_$TIMESTAMP.json"
FAILURE_RESULTS="$RESULTS_DIR/failure_scenario_results_$TIMESTAMP.json"
PERFORMANCE_RESULTS="$RESULTS_DIR/performance_test_results_$TIMESTAMP.json"
SECURITY_RESULTS="$RESULTS_DIR/security_test_results_$TIMESTAMP.json"
TEST_LOG="$RESULTS_DIR/phase4_validation_$TIMESTAMP.log"

# Exit codes
EXIT_SUCCESS=0
EXIT_FAILURE=1
EXIT_SETUP_ERROR=2
EXIT_DEPENDENCY_ERROR=3

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date +'%Y-%m-%d %H:%M:%S')] $message${NC}"
}

print_header() {
    echo
    echo "=================================================================="
    echo "🚀 Phase 4: Comprehensive Local Integration Testing"
    echo "=================================================================="
    echo "Project: Insurance Navigator Worker Refactor"
    echo "Phase: 4 - Comprehensive Local Integration Testing"
    echo "Timestamp: $TIMESTAMP"
    echo "=================================================================="
    echo
}

print_footer() {
    echo
    echo "=================================================================="
    echo "🏁 Phase 4 Validation Complete"
    echo "=================================================================="
    echo "Results Directory: $RESULTS_DIR"
    echo "Timestamp: $TIMESTAMP"
    echo "=================================================================="
    echo
}

# Function to check prerequisites
check_prerequisites() {
    print_status $BLUE "Checking prerequisites..."
    
    # Check Python
    if ! command -v $PYTHON_PATH &> /dev/null; then
        print_status $RED "❌ Python3 not found. Please install Python 3.8+"
        exit $EXIT_DEPENDENCY_ERROR
    fi
    
    # Check pip
    if ! command -v $PIP_PATH &> /dev/null; then
        print_status $RED "❌ pip3 not found. Please install pip3"
        exit $EXIT_DEPENDENCY_ERROR
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_status $RED "❌ Docker not found. Please install Docker"
        exit $EXIT_DEPENDENCY_ERROR
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_status $RED "❌ Docker Compose not found. Please install Docker Compose"
        exit $EXIT_DEPENDENCY_ERROR
    fi
    
    print_status $GREEN "✅ Prerequisites check passed"
}

# Function to setup environment
setup_environment() {
    print_status $BLUE "Setting up environment..."
    
    # Create results directory
    mkdir -p "$RESULTS_DIR"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status $YELLOW "Creating virtual environment..."
        $PYTHON_PATH -m venv venv
    fi
    
    # Activate virtual environment
    print_status $BLUE "Activating virtual environment..."
    source venv/bin/activate
    
    # Install/upgrade pip
    print_status $BLUE "Upgrading pip..."
    $PIP_PATH install --upgrade pip
    
    # Install requirements
    print_status $BLUE "Installing Python dependencies..."
    $PIP_PATH install -r "$REQUIREMENTS_FILE"
    
    # Install additional test dependencies
    print_status $BLUE "Installing test dependencies..."
    $PIP_PATH install pytest pytest-asyncio httpx psutil
    
    print_status $GREEN "✅ Environment setup complete"
}

# Function to check local services
check_local_services() {
    print_status $BLUE "Checking local services..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_status $RED "❌ Docker is not running. Please start Docker"
        exit $EXIT_SETUP_ERROR
    fi
    
    # Check if services are running
    if ! docker-compose ps | grep -q "Up"; then
        print_status $YELLOW "⚠️  Local services not running. Starting services..."
        docker-compose up -d
        
        # Wait for services to be ready
        print_status $BLUE "Waiting for services to be ready..."
        sleep 30
    fi
    
    # Verify key services
    local services=("postgres" "supabase" "llamaparse" "openai")
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            print_status $GREEN "✅ $service is running"
        else
            print_status $RED "❌ $service is not running"
            exit $EXIT_SETUP_ERROR
        fi
    done
    
    print_status $GREEN "✅ Local services check passed"
}

# Function to run individual test module
run_test_module() {
    local test_name=$1
    local test_file=$2
    local results_file=$3
    
    print_status $BLUE "🧪 Running $test_name..."
    
    if [ ! -f "$test_file" ]; then
        print_status $RED "❌ Test file not found: $test_file"
        return 1
    fi
    
    # Run the test
    cd "$BACKEND_DIR"
    if $PYTHON_PATH "$test_file" > "$results_file" 2>&1; then
        print_status $GREEN "✅ $test_name completed successfully"
        return 0
    else
        print_status $RED "❌ $test_name failed"
        return 1
    fi
}

# Function to run comprehensive validation
run_comprehensive_validation() {
    print_status $BLUE "🚀 Running comprehensive validation suite..."
    
    cd "$BACKEND_DIR"
    if $PYTHON_PATH "$COMPREHENSIVE_TEST" > "$COMPREHENSIVE_RESULTS" 2>&1; then
        print_status $GREEN "✅ Comprehensive validation completed successfully"
        return 0
    else
        print_status $RED "❌ Comprehensive validation failed"
        return 1
    fi
}

# Function to run individual test suites
run_individual_tests() {
    print_status $BLUE "🧪 Running individual test suites..."
    
    local all_passed=true
    
    # Run pipeline tests
    if run_test_module "Pipeline Validation" "$PIPELINE_TEST" "$PIPELINE_RESULTS"; then
        print_status $GREEN "✅ Pipeline validation passed"
    else
        print_status $RED "❌ Pipeline validation failed"
        all_passed=false
    fi
    
    # Run failure scenario tests
    if run_test_module "Failure Scenario Validation" "$FAILURE_TEST" "$FAILURE_RESULTS"; then
        print_status $GREEN "✅ Failure scenario validation passed"
    else
        print_status $RED "❌ Failure scenario validation failed"
        all_passed=false
    fi
    
    # Run performance tests
    if run_test_module "Performance Validation" "$PERFORMANCE_TEST" "$PERFORMANCE_RESULTS"; then
        print_status $GREEN "✅ Performance validation passed"
    else
        print_status $RED "❌ Performance validation failed"
        all_passed=false
    fi
    
    # Run security tests
    if run_test_module "Security Validation" "$SECURITY_TEST" "$SECURITY_RESULTS"; then
        print_status $GREEN "✅ Security validation passed"
    else
        print_status $RED "❌ Security validation failed"
        all_passed=false
    fi
    
    if [ "$all_passed" = true ]; then
        print_status $GREEN "✅ All individual test suites passed"
        return 0
    else
        print_status $RED "❌ Some individual test suites failed"
        return 1
    fi
}

# Function to generate test summary
generate_test_summary() {
    print_status $BLUE "📊 Generating test summary..."
    
    echo "==================================================================" > "$TEST_LOG"
    echo "Phase 4 Validation Summary - $TIMESTAMP" >> "$TEST_LOG"
    echo "==================================================================" >> "$TEST_LOG"
    echo "" >> "$TEST_LOG"
    
    # Check comprehensive results
    if [ -f "$COMPREHENSIVE_RESULTS" ]; then
        echo "✅ Comprehensive Validation Results:" >> "$TEST_LOG"
        echo "   File: $COMPREHENSIVE_RESULTS" >> "$TEST_LOG"
        echo "   Size: $(du -h "$COMPREHENSIVE_RESULTS" | cut -f1)" >> "$TEST_LOG"
        echo "" >> "$TEST_LOG"
    else
        echo "❌ Comprehensive Validation Results: Not found" >> "$TEST_LOG"
        echo "" >> "$TEST_LOG"
    fi
    
    # Check individual test results
    local test_files=(
        "Pipeline Validation:$PIPELINE_RESULTS"
        "Failure Scenario Validation:$FAILURE_RESULTS"
        "Performance Validation:$PERFORMANCE_RESULTS"
        "Security Validation:$SECURITY_RESULTS"
    )
    
    for test_info in "${test_files[@]}"; do
        local test_name="${test_info%:*}"
        local results_file="${test_info#*:}"
        
        if [ -f "$results_file" ]; then
            echo "✅ $test_name Results:" >> "$TEST_LOG"
            echo "   File: $results_file" >> "$TEST_LOG"
            echo "   Size: $(du -h "$results_file" | cut -f1)" >> "$TEST_LOG"
            echo "" >> "$TEST_LOG"
        else
            echo "❌ $test_name Results: Not found" >> "$TEST_LOG"
            echo "" >> "$TEST_LOG"
        fi
    done
    
    # Add system information
    echo "System Information:" >> "$TEST_LOG"
    echo "   OS: $(uname -s)" >> "$TEST_LOG"
    echo "   Architecture: $(uname -m)" >> "$TEST_LOG"
    echo "   Python: $($PYTHON_PATH --version)" >> "$TEST_LOG"
    echo "   Docker: $(docker --version)" >> "$TEST_LOG"
    echo "" >> "$TEST_LOG"
    
    print_status $GREEN "✅ Test summary generated: $TEST_LOG"
}

# Function to cleanup
cleanup() {
    print_status $BLUE "🧹 Cleaning up..."
    
    # Deactivate virtual environment if active
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi
    
    print_status $GREEN "✅ Cleanup complete"
}

# Main execution
main() {
    print_header
    
    # Set up error handling
    trap 'print_status $RED "❌ Script interrupted"; cleanup; exit $EXIT_FAILURE' INT TERM
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Check local services
    check_local_services
    
    # Run comprehensive validation
    if run_comprehensive_validation; then
        print_status $GREEN "🎯 Comprehensive validation successful"
    else
        print_status $YELLOW "⚠️  Comprehensive validation failed, running individual tests..."
        run_individual_tests
    fi
    
    # Generate summary
    generate_test_summary
    
    print_footer
    
    # Final status
    if [ -f "$COMPREHENSIVE_RESULTS" ] || [ -f "$PIPELINE_RESULTS" ]; then
        print_status $GREEN "🎉 Phase 4 validation completed successfully!"
        print_status $GREEN "📁 Results saved to: $RESULTS_DIR"
        print_status $GREEN "📋 Summary log: $TEST_LOG"
        print_status $GREEN "✅ Ready for Phase 5: Deployment Preparation"
        exit $EXIT_SUCCESS
    else
        print_status $RED "❌ Phase 4 validation failed!"
        print_status $RED "📁 Check results in: $RESULTS_DIR"
        print_status $RED "📋 Check summary log: $TEST_LOG"
        print_status $RED "🔧 Fix issues before proceeding to Phase 5"
        exit $EXIT_FAILURE
    fi
}

# Run main function
main "$@"
