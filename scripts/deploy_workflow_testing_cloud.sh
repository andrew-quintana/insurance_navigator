#!/bin/bash

# Workflow Testing Cloud Deployment Script
# Phase 2: Cloud Deployment Testing
# Deploys services to Render.com and Vercel with production Supabase integration

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

# Service URLs (will be updated after deployment)
API_URL=""
WORKER_URL=""
FRONTEND_URL=""

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
    print_status "Checking prerequisites..."
    
    # Check if required tools are installed
    if ! command -v render &> /dev/null; then
        print_error "Render CLI is not installed. Please install it from https://render.com/docs/cli"
        exit 1
    fi
    
    if ! command -v vercel &> /dev/null; then
        print_error "Vercel CLI is not installed. Please install it from https://vercel.com/docs/cli"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker Desktop"
        exit 1
    fi
    
    # Check if configuration files exist
    if [[ ! -f "$RENDER_CONFIG" ]]; then
        print_error "Render configuration file not found: $RENDER_CONFIG"
        exit 1
    fi
    
    if [[ ! -f "$VERCEL_CONFIG" ]]; then
        print_error "Vercel configuration file not found: $VERCEL_CONFIG"
        exit 1
    fi
    
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to deploy to Render.com
deploy_render() {
    print_status "Deploying to Render.com..."
    
    # Login to Render (if not already logged in)
    if ! render auth whoami &> /dev/null; then
        print_status "Please log in to Render CLI..."
        render auth login
    fi
    
    # Deploy services to Render
    print_status "Deploying API and Worker services to Render..."
    render deploy --config "$RENDER_CONFIG"
    
    # Get service URLs
    API_URL=$(render services list --format json | jq -r '.[] | select(.name=="insurance-navigator-api-workflow-testing") | .serviceUrl')
    WORKER_URL=$(render services list --format json | jq -r '.[] | select(.name=="insurance-navigator-worker-workflow-testing") | .serviceUrl')
    
    if [[ -z "$API_URL" || -z "$WORKER_URL" ]]; then
        print_error "Failed to get service URLs from Render"
        exit 1
    fi
    
    print_success "Render deployment completed"
    print_status "API URL: $API_URL"
    print_status "Worker URL: $WORKER_URL"
}

# Function to deploy to Vercel
deploy_vercel() {
    print_status "Deploying to Vercel..."
    
    # Navigate to UI directory
    cd "$PROJECT_ROOT/ui"
    
    # Login to Vercel (if not already logged in)
    if ! vercel whoami &> /dev/null; then
        print_status "Please log in to Vercel CLI..."
        vercel login
    fi
    
    # Deploy to Vercel
    print_status "Deploying frontend to Vercel..."
    vercel deploy --prod --config vercel.workflow-testing.json
    
    # Get deployment URL
    FRONTEND_URL=$(vercel ls --format json | jq -r '.[] | select(.name=="insurance-navigator-frontend-workflow-testing") | .url')
    
    if [[ -z "$FRONTEND_URL" ]]; then
        print_error "Failed to get frontend URL from Vercel"
        exit 1
    fi
    
    print_success "Vercel deployment completed"
    print_status "Frontend URL: $FRONTEND_URL"
    
    # Return to project root
    cd "$PROJECT_ROOT"
}

# Function to update cross-platform configuration
update_cross_platform_config() {
    print_status "Updating cross-platform configuration..."
    
    # Update Vercel configuration with actual API URL
    if [[ -n "$API_URL" ]]; then
        sed -i.bak "s|https://insurance-navigator-api-workflow-testing.onrender.com|$API_URL|g" "$VERCEL_CONFIG"
        print_status "Updated Vercel configuration with API URL: $API_URL"
    fi
    
    # Update environment file with actual URLs
    if [[ -n "$API_URL" && -n "$FRONTEND_URL" ]]; then
        sed -i.bak "s|RENDER_API_URL=.*|RENDER_API_URL=$API_URL|g" "$ENV_FILE"
        sed -i.bak "s|VERCEL_URL=.*|VERCEL_URL=$FRONTEND_URL|g" "$ENV_FILE"
        sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=$API_URL|g" "$ENV_FILE"
        sed -i.bak "s|NEXT_PUBLIC_API_BASE_URL=.*|NEXT_PUBLIC_API_BASE_URL=$API_URL|g" "$ENV_FILE"
        sed -i.bak "s|CORS_ORIGINS=.*|CORS_ORIGINS=$FRONTEND_URL|g" "$ENV_FILE"
        sed -i.bak "s|API_BASE_URL=.*|API_BASE_URL=$API_URL|g" "$ENV_FILE"
        print_status "Updated environment file with deployment URLs"
    fi
}

# Function to validate deployment
validate_deployment() {
    print_status "Validating deployment..."
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check API health
    if [[ -n "$API_URL" ]]; then
        print_status "Checking API health..."
        if curl -f "$API_URL/health" &> /dev/null; then
            print_success "API service is healthy"
        else
            print_warning "API service health check failed"
        fi
    fi
    
    # Check Frontend health
    if [[ -n "$FRONTEND_URL" ]]; then
        print_status "Checking Frontend health..."
        if curl -f "$FRONTEND_URL/health" &> /dev/null; then
            print_success "Frontend service is healthy"
        else
            print_warning "Frontend service health check failed"
        fi
    fi
    
    # Run comprehensive validation
    print_status "Running comprehensive validation..."
    if [[ -f "$PROJECT_ROOT/scripts/validate_workflow_testing_cloud.py" ]]; then
        python3 "$PROJECT_ROOT/scripts/validate_workflow_testing_cloud.py"
    else
        print_warning "Cloud validation script not found, skipping comprehensive validation"
    fi
}

# Function to display deployment summary
display_summary() {
    print_success "Cloud deployment completed successfully!"
    echo ""
    echo "=== DEPLOYMENT SUMMARY ==="
    echo "API Service: $API_URL"
    echo "Worker Service: $WORKER_URL"
    echo "Frontend Service: $FRONTEND_URL"
    echo ""
    echo "=== HEALTH CHECKS ==="
    echo "API Health: $API_URL/health"
    echo "Frontend Health: $FRONTEND_URL/health"
    echo ""
    echo "=== NEXT STEPS ==="
    echo "1. Run comprehensive validation: python3 scripts/validate_workflow_testing_cloud.py"
    echo "2. Test cross-platform integration"
    echo "3. Monitor service performance and error rates"
    echo "4. Proceed to Phase 3: End-to-End Integration Validation"
    echo ""
}

# Function to cleanup on error
cleanup() {
    print_error "Deployment failed. Cleaning up..."
    
    # Add cleanup logic here if needed
    # For now, just exit with error code
    exit 1
}

# Main deployment function
main() {
    print_status "Starting Phase 2: Cloud Deployment Testing"
    print_status "Deploying to Render.com and Vercel with production Supabase integration"
    echo ""
    
    # Set up error handling
    trap cleanup ERR
    
    # Check prerequisites
    check_prerequisites
    
    # Deploy to Render.com
    deploy_render
    
    # Deploy to Vercel
    deploy_vercel
    
    # Update cross-platform configuration
    update_cross_platform_config
    
    # Validate deployment
    validate_deployment
    
    # Display summary
    display_summary
    
    print_success "Phase 2 deployment completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    "render")
        check_prerequisites
        deploy_render
        ;;
    "vercel")
        check_prerequisites
        deploy_vercel
        ;;
    "validate")
        validate_deployment
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [render|vercel|validate|help]"
        echo ""
        echo "Commands:"
        echo "  render    Deploy only to Render.com"
        echo "  vercel    Deploy only to Vercel"
        echo "  validate  Validate existing deployment"
        echo "  help      Show this help message"
        echo ""
        echo "Default: Deploy to both platforms"
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
