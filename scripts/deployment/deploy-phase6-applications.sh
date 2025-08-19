#!/bin/bash

# =============================================================================
# Phase 6: Application Deployment and Verification
# 003 Worker Refactor - Application Deployment Script
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

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOYMENT_CONFIG="$PROJECT_ROOT/infrastructure/config/deployment_config.yaml"
BACKUP_DIR="$PROJECT_ROOT/infrastructure/backups"
LOGS_DIR="$PROJECT_ROOT/logs"

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOGS_DIR"

# Logging
LOG_FILE="$LOGS_DIR/phase6_deployment_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

print_status "Phase 6 Application Deployment Started"
print_status "Log file: $LOG_FILE"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env.local" ]; then
    print_status "Loading environment variables from .env.local"
    export $(cat "$PROJECT_ROOT/.env.local" | grep -v '^#' | xargs)
elif [ -f "$PROJECT_ROOT/.env" ]; then
    print_status "Loading environment variables from .env"
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
else
    print_warning "No environment file found, using system environment variables"
fi

# Verify environment configuration
verify_environment() {
    print_status "Verifying environment configuration..."
    
    required_vars=(
        "DATABASE_URL"
        "SUPABASE_URL"
        "SUPABASE_ANON_KEY"
        "SUPABASE_SERVICE_ROLE_KEY"
        "LLAMAPARSE_API_KEY"
        "OPENAI_API_KEY"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
    
    print_success "Environment verification complete"
}

# Backup current state
backup_current_state() {
    print_status "Creating backup of current state..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="$BACKUP_DIR/phase6_pre_deploy_${timestamp}.sql"
    
    # Database backup
    if command -v pg_dump >/dev/null 2>&1; then
        print_status "Creating database backup..."
        PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p') \
        pg_dump "$DATABASE_URL" > "$backup_file" 2>/dev/null || {
            print_warning "Database backup failed, continuing without backup"
        }
    else
        print_warning "pg_dump not available, skipping database backup"
    fi
    
    # Configuration backup
    config_backup="$BACKUP_DIR/phase6_config_${timestamp}.tar.gz"
    tar -czf "$config_backup" -C "$PROJECT_ROOT" \
        infrastructure/config/ \
        backend/api/ \
        backend/workers/ \
        backend/shared/ \
        2>/dev/null || {
        print_warning "Configuration backup failed, continuing without backup"
    }
    
    print_success "Backup completed: $backup_file, $config_backup"
}

# Deploy API server
deploy_api_server() {
    print_status "Deploying API server..."
    
    cd "$PROJECT_ROOT/backend/api"
    
    # Build API server Docker image
    print_status "Building API server Docker image..."
    docker build -t insurance-navigator-api:phase6 . || {
        print_error "Failed to build API server Docker image"
        return 1
    }
    
    # Stop existing API server if running
    if docker ps -q --filter "name=api-server" | grep -q .; then
        print_status "Stopping existing API server..."
        docker stop api-server || true
        docker rm api-server || true
    fi
    
    # Start API server with new image
    print_status "Starting API server..."
    docker run -d \
        --name api-server \
        --network insurance_navigator_network \
        -p 8000:8000 \
        --env-file "$PROJECT_ROOT/.env.local" \
        --restart unless-stopped \
        insurance-navigator-api:phase6 || {
        print_error "Failed to start API server"
        return 1
    }
    
    # Wait for API server to be ready
    print_status "Waiting for API server to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f "http://localhost:8000/health" >/dev/null 2>&1; then
            print_success "API server is ready"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "API server failed to become ready after $max_attempts attempts"
            return 1
        fi
        
        print_status "Waiting for API server... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_success "API server deployed successfully"
}

# Deploy BaseWorker
deploy_base_worker() {
    print_status "Deploying BaseWorker..."
    
    cd "$PROJECT_ROOT/backend/workers"
    
    # Build BaseWorker Docker image
    print_status "Building BaseWorker Docker image..."
    docker build -t insurance-navigator-worker:phase6 . || {
        print_error "Failed to build BaseWorker Docker image"
        return 1
    }
    
    # Stop existing worker if running
    if docker ps -q --filter "name=base-worker" | grep -q .; then
        print_status "Stopping existing BaseWorker..."
        docker stop base-worker || true
        docker rm base-worker || true
    fi
    
    # Start BaseWorker with new image
    print_status "Starting BaseWorker..."
    docker run -d \
        --name base-worker \
        --network insurance_navigator_network \
        -p 8001:8001 \
        --env-file "$PROJECT_ROOT/.env.local" \
        --restart unless-stopped \
        insurance-navigator-worker:phase6 || {
        print_error "Failed to start BaseWorker"
        return 1
    }
    
    # Wait for BaseWorker to be ready
    print_status "Waiting for BaseWorker to be ready..."
    local max_attempts=45
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker logs base-worker 2>&1 | grep -q "BaseWorker initialized"; then
            print_success "BaseWorker is ready"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "BaseWorker failed to become ready after $max_attempts attempts"
            return 1
        fi
        
        print_status "Waiting for BaseWorker... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_success "BaseWorker deployed successfully"
}

# Deploy database schema
deploy_database_schema() {
    print_status "Deploying database schema..."
    
    # Check if migrations directory exists
    if [ ! -d "$PROJECT_ROOT/supabase/migrations" ]; then
        print_warning "No migrations directory found, skipping schema deployment"
        return 0
    fi
    
    # Find the latest migration file
    latest_migration=$(find "$PROJECT_ROOT/supabase/migrations" -name "*.sql" | sort | tail -n 1)
    
    if [ -z "$latest_migration" ]; then
        print_warning "No migration files found, skipping schema deployment"
        return 0
    fi
    
    print_status "Applying migration: $(basename "$latest_migration")"
    
    # Apply migration using psql
    if command -v psql >/dev/null 2>&1; then
        PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p') \
        psql "$DATABASE_URL" -f "$latest_migration" || {
            print_error "Failed to apply database migration"
            return 1
        }
    else
        print_warning "psql not available, skipping schema deployment"
        return 0
    fi
    
    print_success "Database schema deployed successfully"
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check API server health
    print_status "Checking API server health..."
    if ! curl -f "http://localhost:8000/health" >/dev/null 2>&1; then
        print_error "API server health check failed"
        return 1
    fi
    
    # Check BaseWorker health
    print_status "Checking BaseWorker health..."
    if ! docker logs base-worker 2>&1 | grep -q "BaseWorker initialized"; then
        print_error "BaseWorker health check failed"
        return 1
    fi
    
    # Check database connectivity
    print_status "Checking database connectivity..."
    if command -v psql >/dev/null 2>&1; then
        PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p') \
        psql "$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1 || {
            print_error "Database connectivity check failed"
            return 1
        }
    fi
    
    # Check storage connectivity
    print_status "Checking storage connectivity..."
    if ! curl -f "http://localhost:5000/health" >/dev/null 2>&1; then
        print_error "Storage health check failed"
        return 1
    fi
    
    print_success "Deployment verification completed successfully"
}

# Run end-to-end tests
run_e2e_tests() {
    print_status "Running end-to-end tests..."
    
    cd "$PROJECT_ROOT"
    
    # Check if test script exists
    if [ -f "scripts/deployment/test-e2e-pipeline.sh" ]; then
        print_status "Running E2E pipeline tests..."
        ./scripts/deployment/test-e2e-pipeline.sh || {
            print_error "E2E pipeline tests failed"
            return 1
        }
    else
        print_warning "E2E test script not found, skipping tests"
    fi
    
    print_success "End-to-end tests completed successfully"
}

# Main deployment process
main() {
    print_status "Starting Phase 6 Application Deployment"
    
    # Verify environment
    verify_environment
    
    # Backup current state
    backup_current_state
    
    # Deploy database schema
    deploy_database_schema
    
    # Deploy API server
    deploy_api_server
    
    # Deploy BaseWorker
    deploy_base_worker
    
    # Verify deployment
    verify_deployment
    
    # Run end-to-end tests
    run_e2e_tests
    
    print_success "Phase 6 Application Deployment completed successfully!"
    print_status "API Server: http://localhost:8000"
    print_status "BaseWorker: Running on port 8001"
    print_status "Health Check: http://localhost:8000/health"
    print_status "Log file: $LOG_FILE"
}

# Run main function
main "$@"
