#!/bin/bash

# Mock Integration Environment Setup Script
# This script sets up the complete mock integration environment for testing
# upload pipeline + agent workflow integration.

set -e  # Exit on any error

echo "🚀 Setting up Mock Integration Environment..."
echo "=============================================="

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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
    
    # Check if required files exist
    if [ ! -f "docker-compose.mock-integration.yml" ]; then
        print_error "docker-compose.mock-integration.yml not found. Please run this script from the project root."
        exit 1
    fi
    
    if [ ! -f "sql/integration_schema_setup.sql" ]; then
        print_error "sql/integration_schema_setup.sql not found. Please run this script from the project root."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Stop any existing containers
stop_existing_containers() {
    print_status "Stopping any existing containers..."
    
    if docker-compose -f docker-compose.mock-integration.yml ps -q | grep -q .; then
        docker-compose -f docker-compose.mock-integration.yml down
        print_success "Existing containers stopped"
    else
        print_status "No existing containers to stop"
    fi
}

# Clean up any existing volumes (optional)
cleanup_volumes() {
    read -p "Do you want to clean up existing volumes? This will delete all data. (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up existing volumes..."
        docker-compose -f docker-compose.mock-integration.yml down -v
        print_success "Volumes cleaned up"
    else
        print_status "Keeping existing volumes"
    fi
}

# Launch Docker Compose stack
launch_docker_stack() {
    print_status "Launching Docker Compose stack with mock services..."
    
    # Start the services
    docker-compose -f docker-compose.mock-integration.yml up -d
    
    print_success "Docker stack launched"
}

# Wait for database readiness
wait_for_database() {
    print_status "Waiting for database to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.mock-integration.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
            print_success "Database is ready"
            return 0
        fi
        
        print_status "Database not ready yet (attempt $attempt/$max_attempts)..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Database failed to become ready after $max_attempts attempts"
    return 1
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for all services to be healthy..."
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local unhealthy_services=$(docker-compose -f docker-compose.mock-integration.yml ps --format "table {{.Name}}\t{{.Status}}" | grep -v "Up (healthy)" | grep -v "Name" | grep -v "^$" || true)
        
        if [ -z "$unhealthy_services" ]; then
            print_success "All services are healthy"
            return 0
        fi
        
        print_status "Some services not healthy yet (attempt $attempt/$max_attempts)..."
        echo "$unhealthy_services"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    print_error "Some services failed to become healthy after $max_attempts attempts"
    return 1
}

# Validate database schema
validate_schema() {
    print_status "Validating database schema..."
    
    # Check if upload_pipeline schema exists
    local schema_exists=$(docker-compose -f docker-compose.mock-integration.yml exec -T postgres psql -U postgres -d accessa_dev -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'upload_pipeline';" | tr -d ' ')
    
    if [ "$schema_exists" -eq "1" ]; then
        print_success "upload_pipeline schema exists"
    else
        print_error "upload_pipeline schema not found"
        return 1
    fi
    
    # Check if required tables exist
    local tables=("documents" "upload_jobs" "document_chunks")
    for table in "${tables[@]}"; do
        local table_exists=$(docker-compose -f docker-compose.mock-integration.yml exec -T postgres psql -U postgres -d accessa_dev -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'upload_pipeline' AND table_name = '$table';" | tr -d ' ')
        
        if [ "$table_exists" -eq "1" ]; then
            print_success "Table upload_pipeline.$table exists"
        else
            print_error "Table upload_pipeline.$table not found"
            return 1
        fi
    done
    
    # Check if pgvector extension is enabled
    local vector_enabled=$(docker-compose -f docker-compose.mock-integration.yml exec -T postgres psql -U postgres -d accessa_dev -t -c "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';" | tr -d ' ')
    
    if [ "$vector_enabled" -eq "1" ]; then
        print_success "pgvector extension is enabled"
    else
        print_error "pgvector extension not enabled"
        return 1
    fi
    
    return 0
}

# Validate mock services
validate_mock_services() {
    print_status "Validating mock services..."
    
    # Check LlamaParse mock service
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        print_success "LlamaParse mock service is responding"
    else
        print_error "LlamaParse mock service is not responding"
        return 1
    fi
    
    # Check OpenAI mock service
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        print_success "OpenAI mock service is responding"
    else
        print_error "OpenAI mock service is not responding"
        return 1
    fi
    
    # Check agent API service
    if curl -s http://localhost:8003/health > /dev/null 2>&1; then
        print_success "Agent API service is responding"
    else
        print_error "Agent API service is not responding"
        return 1
    fi
    
    return 0
}

# Test integration functionality
test_integration() {
    print_status "Testing integration functionality..."
    
    # Test document availability check
    local test_user_id="550e8400-e29b-41d4-a716-446655440001"
    local availability_response=$(curl -s "http://localhost:8003/integration/documents/$test_user_id/availability")
    
    if echo "$availability_response" | grep -q "policy"; then
        print_success "Document availability check working"
    else
        print_error "Document availability check failed"
        return 1
    fi
    
    # Test RAG-ready documents check
    local rag_ready_response=$(curl -s "http://localhost:8003/integration/documents/$test_user_id/rag-ready")
    
    if echo "$rag_ready_response" | grep -q "is_rag_ready.*true"; then
        print_success "RAG-ready documents check working"
    else
        print_error "RAG-ready documents check failed"
        return 1
    fi
    
    return 0
}

# Show service status
show_service_status() {
    print_status "Service Status:"
    echo "=================="
    docker-compose -f docker-compose.mock-integration.yml ps
    
    echo ""
    print_status "Service URLs:"
    echo "================"
    echo "Upload Pipeline API: http://localhost:8000"
    echo "LlamaParse Mock:    http://localhost:8001"
    echo "OpenAI Mock:        http://localhost:8002"
    echo "Agent API:          http://localhost:8003"
    echo "Monitoring:         http://localhost:3001"
    echo "Database:           localhost:5432"
}

# Main setup process
main() {
    local start_time=$(date +%s)
    
    echo "Starting mock integration environment setup at $(date)"
    echo ""
    
    # Run setup steps
    check_prerequisites
    stop_existing_containers
    cleanup_volumes
    launch_docker_stack
    wait_for_database
    wait_for_services
    validate_schema
    validate_mock_services
    test_integration
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    print_success "Mock integration environment setup completed successfully!"
    print_status "Total setup time: ${duration} seconds"
    echo ""
    
    show_service_status
    
    echo ""
    print_status "Next steps:"
    echo "1. Run integration tests: ./scripts/run-e2e-integration-test.sh"
    echo "2. Check integration health: curl http://localhost:8003/integration/health"
    echo "3. View logs: docker-compose -f docker-compose.mock-integration.yml logs -f"
    echo ""
    print_success "Setup complete! 🎉"
}

# Run main function
main "$@"
