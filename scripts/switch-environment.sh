#!/bin/bash

# Environment Switching Script for 003 Worker Refactor
# This script helps switch between mock, development, staging, and production environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [mock|development|staging|production]"
    echo ""
    echo "This script switches the environment configuration for the 003 Worker Refactor."
    echo ""
    echo "Options:"
    echo "  mock         - Switch to mock services (localhost:5001, mock APIs)"
    echo "  development  - Switch to local development with Supabase (127.0.0.1:54321, mock APIs)"
    echo "  staging      - Switch to staging environment"
    echo "  production   - Switch to production environment"
    echo ""
    echo "Examples:"
    echo "  $0 mock"
    echo "  $0 development"
    echo "  $0 staging"
    echo "  $0 production"
    echo ""
    echo "Current environment: $(grep 'UPLOAD_PIPELINE_ENVIRONMENT' docker-compose.yml | head -1 | cut -d'=' -f2)"
}

# Function to validate environment
validate_environment() {
    local env=$1
    case $env in
        mock|development|staging|production)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Function to switch to mock environment
switch_to_mock() {
    print_header "Switching to Mock Environment"
    
    print_status "Updating docker-compose.yml..."
    
    # Update environment variables
    sed -i.bak 's/UPLOAD_PIPELINE_ENVIRONMENT=.*/UPLOAD_PIPELINE_ENVIRONMENT=mock/' docker-compose.yml
    sed -i.bak 's/UPLOAD_PIPELINE_STORAGE_ENVIRONMENT=.*/UPLOAD_PIPELINE_STORAGE_ENVIRONMENT=mock/' docker-compose.yml
    sed -i.bak 's|UPLOAD_PIPELINE_STORAGE_URL=.*|UPLOAD_PIPELINE_STORAGE_URL=http://localhost:5001|' docker-compose.yml
    
    # Update API URLs to mock services
    sed -i.bak 's|UPLOAD_PIPELINE_LLAMAPARSE_API_URL=.*|UPLOAD_PIPELINE_LLAMAPARSE_API_URL=http://mock-llamaparse:8001|' docker-compose.yml
    sed -i.bak 's|UPLOAD_PIPELINE_OPENAI_API_URL=.*|UPLOAD_PIPELINE_OPENAI_API_URL=http://mock-openai:8002|' docker-compose.yml
    
    print_status "Mock environment configured!"
    print_status "Storage URLs will point to: http://localhost:5001 (mock storage service)"
    print_status "Mock services will be used for external APIs"
}

# Function to switch to development environment
switch_to_development() {
    print_header "Switching to Development Environment"
    
    print_status "Updating docker-compose.yml..."
    
    # Update environment variables
    sed -i.bak 's/UPLOAD_PIPELINE_ENVIRONMENT=.*/UPLOAD_PIPELINE_ENVIRONMENT=development/' docker-compose.yml
    sed -i.bak 's/UPLOAD_PIPELINE_STORAGE_ENVIRONMENT=.*/UPLOAD_PIPELINE_STORAGE_ENVIRONMENT=development/' docker-compose.yml
    sed -i.bak 's|UPLOAD_PIPELINE_STORAGE_URL=.*|UPLOAD_PIPELINE_STORAGE_URL=http://127.0.0.1:54321|' docker-compose.yml
    
    # Update API URLs to mock services (for development testing)
    sed -i.bak 's|UPLOAD_PIPELINE_LLAMAPARSE_API_URL=.*|UPLOAD_PIPELINE_LLAMAPARSE_API_URL=http://mock-llamaparse:8001|' docker-compose.yml
    sed -i.bak 's|UPLOAD_PIPELINE_OPENAI_API_URL=.*|UPLOAD_PIPELINE_OPENAI_API_URL=http://mock-openai:8002|' docker-compose.yml
    
    print_status "Development environment configured!"
    print_status "Storage URLs will point to: http://127.0.0.1:54321 (actual Supabase storage)"
    print_status "Mock services will be used for external APIs (for development testing)"
    print_status "Files will appear in Supabase dashboard at: http://127.0.0.1:54323"
}

# Function to switch to staging environment
switch_to_staging() {
    print_header "Switching to Staging Environment"
    
    print_status "Updating docker-compose.yml..."
    
    # Update environment variables
    sed -i.bak 's/UPLOAD_PIPELINE_ENVIRONMENT=.*/UPLOAD_PIPELINE_ENVIRONMENT=staging/' docker-compose.yml
    sed -i.bak 's/UPLOAD_PIPELINE_STORAGE_ENVIRONMENT=.*/UPLOAD_PIPELINE_STORAGE_ENVIRONMENT=staging/' docker-compose.yml
    sed -i.bak 's|UPLOAD_PIPELINE_STORAGE_URL=.*|UPLOAD_PIPELINE_STORAGE_URL=https://staging-storage.supabase.co|' docker-compose.yml
    
    # Update API URLs to staging
    sed -i.bak 's|UPLOAD_PIPELINE_LLAMAPARSE_API_URL=.*|UPLOAD_PIPELINE_LLAMAPARSE_API_URL=${LLAMAPARSE_API_URL}|' docker-compose.yml
    sed -i.bak 's|UPLOAD_PIPELINE_OPENAI_API_URL=.*|UPLOAD_PIPELINE_OPENAI_API_URL=${OPENAI_API_URL}|' docker-compose.yml
    
    print_status "Staging environment configured!"
    print_status "Storage URLs will point to: https://staging-storage.supabase.co"
    print_status "Real external APIs will be used"
    print_warning "Make sure to set LLAMAPARSE_API_URL and OPENAI_API_URL environment variables for staging"
}

# Function to switch to production environment
switch_to_production() {
    print_header "Switching to Production Environment"
    
    print_status "Updating docker-compose.yml..."
    
    # Update environment variables
    sed -i.bak 's/UPLOAD_PIPELINE_ENVIRONMENT=.*/UPLOAD_PIPELINE_ENVIRONMENT=production/' docker-compose.yml
    sed -i.bak 's/UPLOAD_PIPELINE_STORAGE_ENVIRONMENT=.*/UPLOAD_PIPELINE_STORAGE_ENVIRONMENT=production/' docker-compose.yml
    sed -i.bak 's|UPLOAD_PIPELINE_STORAGE_URL=.*|UPLOAD_PIPELINE_STORAGE_URL=https://storage.supabase.co|' docker-compose.yml
    
    # Update API URLs to production
    sed -i.bak 's|UPLOAD_PIPELINE_LLAMAPARSE_API_URL=.*|UPLOAD_PIPELINE_LLAMAPARSE_API_URL=${LLAMAPARSE_API_URL}|' docker-compose.yml
    sed -i.bak 's|UPLOAD_PIPELINE_OPENAI_API_URL=.*|UPLOAD_PIPELINE_OPENAI_API_URL=${OPENAI_API_URL}|' docker-compose.yml
    
    print_status "Production environment configured!"
    print_status "Storage URLs will point to: https://storage.supabase.co"
    print_status "Real external APIs will be used"
    print_warning "Make sure to set LLAMAPARSE_API_URL and OPENAI_API_URL environment variables for production"
}

# Function to update docker-compose.yml
update_docker_compose() {
    local env=$1
    print_status "Updating docker-compose.yml..."

    case $env in
        mock)
            switch_to_mock
            ;;
        development)
            switch_to_development
            ;;
        staging)
            switch_to_staging
            ;;
        production)
            switch_to_production
            ;;
        *)
            print_error "Invalid environment: $env"
            exit 1
            ;;
    esac

    # Clean up backup files
    rm -f docker-compose.yml.bak
}

# Function to restart Docker services
restart_services() {
    read -p "Do you want to restart services now to apply the new configuration? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Restarting services to apply new configuration..."
        docker-compose down --remove-orphans
        docker-compose up -d --build
        print_status "Services restarted successfully!"
    else
        print_warning "Services not restarted. Please run 'docker-compose down --remove-orphans && docker-compose up -d --build' manually."
    fi
}

# Main logic
if [ -z "$1" ]; then
    print_header "Current Environment Configuration"
    grep UPLOAD_PIPELINE_ENVIRONMENT docker-compose.yml | head -1 | awk '{print "Environment:       " $NF}'
    grep UPLOAD_PIPELINE_STORAGE_ENVIRONMENT docker-compose.yml | head -1 | awk '{print "Storage Environment:       " $NF}'
    grep UPLOAD_PIPELINE_STORAGE_URL docker-compose.yml | head -1 | awk '{print "Storage URL:       " $NF}'
    grep UPLOAD_PIPELINE_LLAMAPARSE_API_URL docker-compose.yml | head -1 | awk '{print "LlamaParse API:       " $NF}'
    grep UPLOAD_PIPELINE_OPENAI_API_URL docker-compose.yml | head -1 | awk '{print "OpenAI API:       " $NF}'
    echo
    show_usage
    exit 1
fi

ENVIRONMENT=$1

if ! validate_environment "$ENVIRONMENT"; then
    print_error "Invalid environment: $ENVIRONMENT"
    show_usage
    exit 1
fi

update_docker_compose "$ENVIRONMENT"
restart_services
print_status "Environment switch completed!"
