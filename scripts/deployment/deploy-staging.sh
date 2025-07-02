#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ -f ".env.staging" ]; then
    source .env.staging
else
    echo "Error: .env.staging file not found"
    exit 1
fi

# Function to check required environment variables
check_required_vars() {
    local required_vars=(
        "SUPABASE_PROJECT_ID"
        "SUPABASE_ACCESS_TOKEN"
        "DATABASE_URL"
        "STORAGE_BUCKET"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Error: Required environment variable $var is not set"
            exit 1
        fi
    done
}

# Function to deploy database migrations
deploy_migrations() {
    echo "Deploying database migrations..."
    npx supabase db push --project-id "$SUPABASE_PROJECT_ID"
}

# Function to deploy Edge Functions
deploy_edge_functions() {
    echo "Deploying Edge Functions..."
    local functions=(
        "processing-supervisor"
        "document-parser"
        "chunking-service"
        "vectorization-service"
    )

    for func in "${functions[@]}"; do
        echo "Deploying $func..."
        npx supabase functions deploy "$func" --project-id "$SUPABASE_PROJECT_ID"
    done
}

# Function to configure storage buckets
configure_storage() {
    echo "Configuring storage buckets..."
    npx supabase storage create "$STORAGE_BUCKET" --project-id "$SUPABASE_PROJECT_ID"
}

# Function to run database validations
validate_database() {
    echo "Validating database setup..."
    # Run database validation scripts
    psql "$DATABASE_URL" -f scripts/deployment/validate-schema.sql
}

# Function to verify Edge Functions
verify_edge_functions() {
    echo "Verifying Edge Functions..."
    # Add verification for each function
    for func in processing-supervisor document-parser chunking-service vectorization-service; do
        curl -i "https://$SUPABASE_PROJECT_ID.functions.supabase.co/$func/healthcheck"
    done
}

# Function to run integration tests
run_integration_tests() {
    echo "Running integration tests..."
    npm run test:integration:staging
}

# Main deployment flow
main() {
    echo "Starting staging deployment..."
    
    # Check required environment variables
    check_required_vars
    
    # Deploy components
    deploy_migrations
    deploy_edge_functions
    configure_storage
    
    # Validate deployment
    validate_database
    verify_edge_functions
    run_integration_tests
    
    echo "Staging deployment completed successfully!"
}

# Execute main function
main "$@" 