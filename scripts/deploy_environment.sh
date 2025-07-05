#!/bin/bash

# Environment deployment script
# Usage: ./deploy_environment.sh <environment> [--migrate-only]

set -e

# Configuration
ENVIRONMENTS=("development" "staging" "production")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Environment-specific settings
declare -A ENV_SETTINGS
ENV_SETTINGS[development]='{
    "edge_function_url": "http://127.0.0.1:54321/functions/v1/doc-processor",
    "service_role_key": "your-dev-service-role-key"
}'
ENV_SETTINGS[staging]='{
    "edge_function_url": "https://staging-project.supabase.co/functions/v1/doc-processor",
    "service_role_key": "your-staging-service-role-key"
}'
ENV_SETTINGS[production]='{
    "edge_function_url": "https://production-project.supabase.co/functions/v1/doc-processor",
    "service_role_key": "your-production-service-role-key"
}'

# Functions
check_prerequisites() {
    command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
    command -v psql >/dev/null 2>&1 || { echo "❌ PostgreSQL client is required but not installed."; exit 1; }
}

validate_environment() {
    local env=$1
    if [[ ! " ${ENVIRONMENTS[@]} " =~ " ${env} " ]]; then
        echo "❌ Invalid environment: $env"
        echo "Valid environments are: ${ENVIRONMENTS[*]}"
        exit 1
    fi
}

run_migrations() {
    local env=$1
    echo "🔄 Running database migrations for $env environment..."
    
    cd "$PROJECT_ROOT/supabase/migrations"
    for migration in *.sql; do
        if [ -f "$migration" ]; then
            echo "  ▶️ Applying migration: $migration"
            psql -v ON_ERROR_STOP=1 -f "$migration" || {
                echo "❌ Migration failed: $migration"
                exit 1
            }
        fi
    done
    echo "✅ Migrations completed successfully"
}

update_settings() {
    local env=$1
    echo "🔄 Updating application settings for $env environment..."
    
    python3 "$SCRIPT_DIR/manage_db_settings.py" \
        --env "$env" \
        --action update \
        --settings "${ENV_SETTINGS[$env]}" || {
        echo "❌ Failed to update settings"
        exit 1
    }
    echo "✅ Settings updated successfully"
}

verify_deployment() {
    local env=$1
    echo "🔍 Verifying deployment for $env environment..."
    
    python3 "$SCRIPT_DIR/manage_db_settings.py" \
        --env "$env" \
        --action verify || {
        echo "❌ Deployment verification failed"
        exit 1
    }
    echo "✅ Deployment verified successfully"
}

# Main script
main() {
    local env=$1
    local migrate_only=$2
    
    echo "🚀 Starting deployment for $env environment..."
    
    check_prerequisites
    validate_environment "$env"
    
    run_migrations "$env"
    
    if [ "$migrate_only" != "--migrate-only" ]; then
        update_settings "$env"
        verify_deployment "$env"
    fi
    
    echo "✅ Deployment completed successfully"
}

# Script execution
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <environment> [--migrate-only]"
    echo "Valid environments: ${ENVIRONMENTS[*]}"
    exit 1
fi

main "$@" 