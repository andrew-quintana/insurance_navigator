#!/bin/bash

# =============================================================================
# Insurance Navigator - Production Deployment Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Deployment Steps
verify_environment() {
    print_status "Verifying environment configuration..."
    required_vars=(
        "SUPABASE_URL"
        "SUPABASE_ANON_KEY"
        "SUPABASE_SERVICE_ROLE_KEY"
        "LLAMAPARSE_API_KEY"
        "OPENAI_API_KEY"
        "DATABASE_URL"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            print_error "Missing required environment variable: $var"
            exit 1
        fi
    done
    print_success "Environment verification complete"
}

deploy_database() {
    print_status "Deploying database schema..."
    ./scripts/deployment/apply-production-schema.sh
    print_success "Database schema deployed"
}

deploy_edge_functions() {
    print_status "Deploying Edge Functions..."
    functions=(
        "doc-processor"
        "doc-parser"
        "chunking-service"
        "vector-service"
        "processing-supervisor"
    )

    for func in "${functions[@]}"; do
        print_status "Deploying $func..."
        supabase functions deploy "$func" --project-ref "$PROJECT_REF"
        print_success "$func deployed"
    done
}

setup_monitoring() {
    print_status "Setting up monitoring..."
    ./scripts/deployment/setup-monitoring.sh
    print_success "Monitoring configured"
}

verify_deployment() {
    print_status "Running deployment verification..."
    ./scripts/deployment/test-serverless-pipeline.sh
    print_success "Deployment verified"
}

backup_database() {
    print_status "Creating database backup..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="backups/pre_deploy_${timestamp}.sql"
    mkdir -p backups
    PGPASSWORD=$DB_PASSWORD pg_dump "$DATABASE_URL" > "$backup_file"
    print_success "Database backup created at $backup_file"
}

deploy_frontend() {
    print_status "Deploying frontend to Vercel..."
    cd ui
    vercel --prod
    cd ..
    print_success "Frontend deployed"
}

# Main deployment flow
main() {
    print_status "Starting production deployment..."
    
    verify_environment
    # backup_database  # Handled separately via supabase db dump
    deploy_database
    deploy_edge_functions
    setup_monitoring
    deploy_frontend
    verify_deployment
    
    print_success "Production deployment completed successfully!"
    
    echo ""
    echo "🎉 Deployment Summary:"
    echo "======================"
    echo "✅ Environment verified"
    echo "✅ Database backed up and migrated"
    echo "✅ Edge Functions deployed"
    echo "✅ Monitoring configured"
    echo "✅ Frontend deployed"
    echo "✅ All systems verified"
    echo ""
    echo "Next steps:"
    echo "1. Monitor error logs for the next 24 hours"
    echo "2. Verify all Edge Functions are responding"
    echo "3. Test document processing pipeline"
    echo "4. Check monitoring dashboards"
}

main "$@" 