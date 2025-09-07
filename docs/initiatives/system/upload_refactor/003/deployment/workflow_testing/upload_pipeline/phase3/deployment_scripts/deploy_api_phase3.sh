#!/bin/bash

# Phase 3 API Service Deployment Script
# Cautious deployment with enhanced logging and monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_SERVICE_NAME="insurance-navigator-api-workflow-testing"
RENDER_CONFIG="config/render/render.workflow-testing.yaml"

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

# Function to check if we're logged into Render
check_render_auth() {
    print_status "Checking Render CLI authentication..."
    
    if ! render auth whoami &> /dev/null; then
        print_warning "Not logged into Render CLI. Please log in..."
        render auth login
    else
        USER=$(render auth whoami)
        print_success "Logged into Render as: $USER"
    fi
}

# Function to check current service status
check_service_status() {
    print_status "Checking current service status..."
    
    # Get service info
    SERVICE_INFO=$(render services list -o json | jq -r ".[] | select(.name==\"$API_SERVICE_NAME\")")
    
    if [[ -z "$SERVICE_INFO" ]]; then
        print_warning "Service $API_SERVICE_NAME not found. Will create new service."
        return 1
    else
        SERVICE_URL=$(echo "$SERVICE_INFO" | jq -r '.serviceUrl')
        SERVICE_STATUS=$(echo "$SERVICE_INFO" | jq -r '.serviceDetails.deploy.status')
        print_status "Service found: $SERVICE_URL"
        print_status "Current status: $SERVICE_STATUS"
        return 0
    fi
}

# Function to trigger deployment with monitoring
deploy_with_monitoring() {
    print_status "Starting API service deployment with enhanced monitoring..."
    
    # Deploy using Render config file
    print_status "Deploying service using Render configuration..."
    render deploy --config "$RENDER_CONFIG"
    
    print_success "Deployment triggered successfully!"
}

# Function to monitor deployment progress
monitor_deployment() {
    print_status "Monitoring deployment progress..."
    
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        attempt=$((attempt + 1))
        
        # Get service status
        SERVICE_INFO=$(render services list -o json | jq -r ".[] | select(.name==\"$API_SERVICE_NAME\")")
        
        if [[ -n "$SERVICE_INFO" ]]; then
            SERVICE_URL=$(echo "$SERVICE_INFO" | jq -r '.serviceUrl')
            SERVICE_STATUS=$(echo "$SERVICE_INFO" | jq -r '.serviceDetails.deploy.status')
            
            print_status "Attempt $attempt/$max_attempts - Status: $SERVICE_STATUS"
            
            case "$SERVICE_STATUS" in
                "LIVE")
                    print_success "Deployment completed successfully!"
                    print_success "API URL: $SERVICE_URL"
                    return 0
                    ;;
                "BUILD_FAILED"|"UPDATE_FAILED"|"DEPLOY_FAILED")
                    print_error "Deployment failed with status: $SERVICE_STATUS"
                    return 1
                    ;;
                "BUILDING"|"UPDATING"|"DEPLOYING")
                    print_status "Deployment in progress... waiting 30 seconds"
                    sleep 30
                    ;;
                *)
                    print_warning "Unknown status: $SERVICE_STATUS. Waiting 30 seconds..."
                    sleep 30
                    ;;
            esac
        else
            print_warning "Service not found yet. Waiting 30 seconds..."
            sleep 30
        fi
    done
    
    print_error "Deployment monitoring timed out after $((max_attempts * 30)) seconds"
    return 1
}

# Function to test the deployed service
test_deployed_service() {
    print_status "Testing deployed service..."
    
    # Get service URL
    SERVICE_INFO=$(render services list -o json | jq -r ".[] | select(.name==\"$API_SERVICE_NAME\")")
    
    if [[ -z "$SERVICE_INFO" ]]; then
        print_error "Service not found after deployment"
        return 1
    fi
    
    SERVICE_URL=$(echo "$SERVICE_INFO" | jq -r '.serviceUrl')
    print_status "Testing service at: $SERVICE_URL"
    
    # Test health endpoint
    if curl -f -s "$SERVICE_URL/health" > /dev/null; then
        print_success "Health check passed!"
        
        # Get health response for debugging
        HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health")
        print_status "Health response: $HEALTH_RESPONSE"
        
        return 0
    else
        print_error "Health check failed!"
        return 1
    fi
}

# Function to show deployment logs
show_deployment_logs() {
    print_status "Fetching deployment logs..."
    
    # Get recent logs
    render logs "$API_SERVICE_NAME" --tail 50
}

# Main deployment function
main() {
    print_status "Starting Phase 3 API Service Deployment"
    print_status "Service: $API_SERVICE_NAME"
    print_status "Config: $RENDER_CONFIG"
    echo ""
    
    # Check authentication
    check_render_auth
    
    # Deploy with monitoring
    deploy_with_monitoring
    
    # Monitor deployment
    if monitor_deployment; then
        # Test the service
        if test_deployed_service; then
            print_success "Phase 3 API deployment completed successfully!"
            echo ""
            print_status "Next steps:"
            print_status "1. Run: python3 phase3_cloud_test.py"
            print_status "2. Check logs: render logs $API_SERVICE_NAME"
            print_status "3. Monitor service: render service show $API_SERVICE_NAME"
        else
            print_error "Service deployment succeeded but health check failed"
            show_deployment_logs
            exit 1
        fi
    else
        print_error "Deployment failed or timed out"
        show_deployment_logs
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    "deploy")
        deploy_with_monitoring
        ;;
    "monitor")
        monitor_deployment
        ;;
    "test")
        test_deployed_service
        ;;
    "logs")
        show_deployment_logs
        ;;
    "status")
        check_service_status
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [deploy|monitor|test|logs|status|help]"
        echo ""
        echo "Commands:"
        echo "  deploy   Deploy the API service"
        echo "  monitor  Monitor deployment progress"
        echo "  test     Test the deployed service"
        echo "  logs     Show deployment logs"
        echo "  status   Check service status"
        echo "  help     Show this help message"
        echo ""
        echo "Default: Full deployment with monitoring and testing"
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
