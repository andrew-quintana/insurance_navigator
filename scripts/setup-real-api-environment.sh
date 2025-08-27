#!/bin/bash

# Real API Integration Environment Setup Script for Phase 2
# This script sets up the development environment with real LlamaParse and OpenAI APIs
# for comprehensive integration testing and validation.

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
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.real-api.yml"

echo -e "${BLUE}=== Real API Integration Environment Setup ===${NC}"
echo "Setting up development environment with real APIs for Phase 2 testing"
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
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        print_error "Real API Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Setup environment configuration
setup_environment() {
    print_status "Setting up environment configuration..."
    
    # Check if .env.real-api exists
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file not found: $ENV_FILE"
        print_status "Creating from template..."
        
        if [ -f "$PROJECT_ROOT/env.real-api.example" ]; then
            cp "$PROJECT_ROOT/env.real-api.example" "$ENV_FILE"
            print_warning "Please edit $ENV_FILE with your actual API credentials"
            print_warning "Then run this script again"
            exit 1
        else
            print_error "Environment template not found: env.real-api.example"
            exit 1
        fi
    fi
    
    # Load environment variables
    if [ -f "$ENV_FILE" ]; then
        print_status "Loading environment variables from $ENV_FILE"
        # Load environment variables, filtering out comments and empty lines
        while IFS= read -r line; do
            # Skip comments and empty lines
            if [[ ! "$line" =~ ^[[:space:]]*# ]] && [[ -n "$line" ]]; then
                # Extract variable name and value
                if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
                    var_name="${BASH_REMATCH[1]}"
                    var_value="${BASH_REMATCH[2]}"
                    # Remove leading/trailing whitespace
                    var_name=$(echo "$var_name" | xargs)
                    var_value=$(echo "$var_value" | xargs)
                    # Only export if it's a valid variable name
                    if [[ "$var_name" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
                        export "$var_name=$var_value"
                    fi
                fi
            fi
        done < "$ENV_FILE"
    fi
    
    # Validate required environment variables
    validate_environment_variables
    
    print_status "Environment configuration completed"
}

# Validate required environment variables
validate_environment_variables() {
    print_status "Validating required environment variables..."
    
    local missing_vars=()
    
    # Check required API keys
    if [ -z "$LLAMAPARSE_API_KEY" ] || [ "$LLAMAPARSE_API_KEY" = "your_actual_llamaparse_api_key_here" ]; then
        missing_vars+=("LLAMAPARSE_API_KEY")
    fi
    
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_actual_openai_api_key_here" ]; then
        missing_vars+=("OPENAI_API_KEY")
    fi
    
    # Check other required variables
    if [ -z "$DATABASE_URL" ]; then
        missing_vars+=("DATABASE_URL")
    fi
    
    if [ -z "$ENVIRONMENT" ]; then
        missing_vars+=("ENVIRONMENT")
    fi
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing or invalid environment variables:"
        for var in "${missing_vars[@]}"; do
            print_error "  - $var"
        done
        print_warning "Please update $ENV_FILE with valid values and run this script again"
        exit 1
    fi
    
    print_status "Environment variables validation passed"
}

# Stop existing services
stop_existing_services() {
    print_status "Stopping existing services..."
    
    # Stop mock integration services if running
    if [ -f "$PROJECT_ROOT/docker-compose.mock-integration.yml" ]; then
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.mock-integration.yml down --remove-orphans 2>/dev/null || true
    fi
    
    # Stop real API services if running
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        cd "$PROJECT_ROOT"
        docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    fi
    
    print_status "Existing services stopped"
}

# Start real API environment
start_real_api_environment() {
    print_status "Starting real API integration environment..."
    
    cd "$PROJECT_ROOT"
    
    # Start services
    print_status "Starting Docker Compose services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    wait_for_services
    
    print_status "Real API environment started successfully"
}

# Wait for services to be ready
wait_for_services() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Checking service health (attempt $attempt/$max_attempts)..."
        
        # Check database
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
            print_status "Database is ready"
        else
            print_warning "Database not ready yet, waiting..."
            sleep 10
            ((attempt++))
            continue
        fi
        
        # Check API server
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_status "API server is ready"
        else
            print_warning "API server not ready yet, waiting..."
            sleep 10
            ((attempt++))
            continue
        fi
        
        # Check agent API
        if curl -f http://localhost:8003/health > /dev/null 2>&1; then
            print_status "Agent API is ready"
        else
            print_warning "Agent API not ready yet, waiting..."
            sleep 10
            ((attempt++))
            continue
        fi
        
        # Check monitoring
        if curl -f http://localhost:8004/health > /dev/null 2>&1; then
            print_status "Monitoring is ready"
        else
            print_warning "Monitoring not ready yet, waiting..."
            sleep 10
            ((attempt++))
            continue
        fi
        
        print_status "All services are ready!"
        return 0
    done
    
    print_error "Services failed to become ready within expected time"
    print_status "Checking service logs for debugging..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50
    
    exit 1
}

# Validate real API connectivity
validate_api_connectivity() {
    print_status "Validating real API connectivity..."
    
    # Test LlamaParse API connectivity
    print_status "Testing LlamaParse API connectivity..."
    if curl -s -H "Authorization: Bearer $LLAMAPARSE_API_KEY" \
            "https://api.llamaindex.ai/v1/parsers" > /dev/null 2>&1; then
        print_status "LlamaParse API connectivity: OK"
    else
        print_warning "LlamaParse API connectivity: Failed (may be rate limited or invalid key)"
    fi
    
    # Test OpenAI API connectivity
    print_status "Testing OpenAI API connectivity..."
    if curl -s -H "Authorization: Bearer $OPENAI_API_KEY" \
            "https://api.openai.com/v1/models" > /dev/null 2>&1; then
        print_status "OpenAI API connectivity: OK"
    else
        print_warning "OpenAI API connectivity: Failed (may be rate limited or invalid key)"
    fi
    
    print_status "API connectivity validation completed"
}

# Run health checks
run_health_checks() {
    print_status "Running comprehensive health checks..."
    
    cd "$PROJECT_ROOT"
    
    # Check service status
    print_status "Service status:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    # Check service logs for errors
    print_status "Checking for service errors..."
    local error_logs=$(docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=100 | grep -i "error\|exception\|failed" || true)
    
    if [ -n "$error_logs" ]; then
        print_warning "Found potential errors in service logs:"
        echo "$error_logs"
    else
        print_status "No errors found in service logs"
    fi
    
    print_status "Health checks completed"
}

# Display next steps
display_next_steps() {
    echo ""
    echo -e "${GREEN}=== Real API Environment Setup Complete ===${NC}"
    echo ""
    echo "Your real API integration environment is now running with:"
    echo "  - Database: localhost:5432"
    echo "  - API Server: http://localhost:8000"
    echo "  - Agent API: http://localhost:8003"
    echo "  - Monitoring: http://localhost:8004"
    echo ""
    echo "Next steps:"
    echo "1. Run integration tests:"
    echo "   python -m pytest tests/integration/test_real_api_integration.py -v"
    echo ""
    echo "2. Monitor service logs:"
    echo "   docker-compose -f docker-compose.real-api.yml logs -f"
    echo ""
    echo "3. Check service health:"
    echo "   curl http://localhost:8000/health"
    echo "   curl http://localhost:8003/health"
    echo ""
    echo "4. Stop environment when done:"
    echo "   docker-compose -f docker-compose.real-api.yml down"
    echo ""
    echo -e "${YELLOW}Note: This environment uses real APIs and may incur costs.${NC}"
    echo -e "${YELLOW}Monitor your API usage and costs accordingly.${NC}"
}

# Main execution
main() {
    echo "Starting real API environment setup..."
    echo "Project root: $PROJECT_ROOT"
    echo ""
    
    check_prerequisites
    setup_environment
    stop_existing_services
    start_real_api_environment
    validate_api_connectivity
    run_health_checks
    display_next_steps
    
    echo ""
    print_status "Real API environment setup completed successfully!"
}

# Run main function
main "$@"
