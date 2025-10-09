#!/bin/bash

# Production Configuration Loader Script
# This script loads environment variables and generates a resolved production.config.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/production.config.json"
RESOLVED_CONFIG="$SCRIPT_DIR/production.config.resolved.json"

# Required environment variables for production
required_vars=(
    "SUPABASE_PROJECT_ID"
    "SUPABASE_ORG_ID"
    "DATABASE_HOST"
    "DATABASE_PORT"
    "DATABASE_NAME"
    "DATABASE_USER"
    "DATABASE_PASSWORD"
    "DATABASE_MAX_CONNECTIONS"
    "DATABASE_POOL_SIZE"
    "SITE_URL"
    "ADDITIONAL_REDIRECT_URLS"
    "JWT_EXPIRY"
    "STORAGE_BUCKET_NAME"
    "STORAGE_FILE_SIZE_LIMIT"
    "STORAGE_ALLOWED_MIME_TYPES"
    "REALTIME_MAX_CONNECTIONS"
    "EDGE_FUNCTIONS_MAX_EXECUTION_TIME"
    "MONITORING_METRICS_RETENTION_DAYS"
    "MONITORING_LOG_RETENTION_DAYS"
    "BACKUP_SCHEDULE"
    "BACKUP_RETENTION_DAYS"
    "SUPABASE_URL"
    "SUPABASE_ANON_KEY"
    "SUPABASE_SERVICE_ROLE_KEY"
)

# Check for missing required variables
missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "💡 Please set these variables in your environment or .env.production file"
    echo "📋 See production.env.template for reference values"
    echo ""
    echo "🔧 Example usage:"
    echo "   export DATABASE_PASSWORD='your-password'"
    echo "   export SUPABASE_PROJECT_ID='mrbigmtnadjtyepxqefa'"
    echo "   # ... set all required variables"
    echo "   ./load_production_config.sh"
    exit 1
fi

echo "🔧 Loading production configuration..."

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Use envsubst to substitute environment variables
if command -v envsubst >/dev/null 2>&1; then
    # Create a temporary file with proper envsubst syntax
    cp "$CONFIG_FILE" "$RESOLVED_CONFIG"
    
    # Replace ${VAR:-default} syntax with just ${VAR} for envsubst
    sed -i.bak 's/\${\([^:]*\):-[^}]*}/\${\1}/g' "$RESOLVED_CONFIG"
    
    # Now use envsubst
    envsubst < "$RESOLVED_CONFIG" > "$RESOLVED_CONFIG.tmp"
    mv "$RESOLVED_CONFIG.tmp" "$RESOLVED_CONFIG"
    
    # Clean up backup file
    rm -f "$RESOLVED_CONFIG.bak"
    echo "✅ Configuration resolved using envsubst"
else
    # Fallback: use sed for basic substitution
    cp "$CONFIG_FILE" "$RESOLVED_CONFIG"
    
    # Replace environment variables
    sed -i.bak "s/\${SUPABASE_PROJECT_ID}/$SUPABASE_PROJECT_ID/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${SUPABASE_ORG_ID}/$SUPABASE_ORG_ID/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${DATABASE_HOST}/$DATABASE_HOST/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${DATABASE_PORT:-5432}/$DATABASE_PORT/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${DATABASE_NAME:-postgres}/$DATABASE_NAME/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${DATABASE_USER:-postgres}/$DATABASE_USER/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${DATABASE_PASSWORD}/$DATABASE_PASSWORD/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${DATABASE_MAX_CONNECTIONS:-100}/$DATABASE_MAX_CONNECTIONS/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${DATABASE_POOL_SIZE:-20}/$DATABASE_POOL_SIZE/g" "$RESOLVED_CONFIG"
    sed -i.bak "s|\${SITE_URL}|$SITE_URL|g" "$RESOLVED_CONFIG"
    sed -i.bak "s|\${ADDITIONAL_REDIRECT_URLS}|$ADDITIONAL_REDIRECT_URLS|g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${JWT_EXPIRY:-3600}/$JWT_EXPIRY/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${STORAGE_BUCKET_NAME:-insurance_documents_prod}/$STORAGE_BUCKET_NAME/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${STORAGE_FILE_SIZE_LIMIT:-104857600}/$STORAGE_FILE_SIZE_LIMIT/g" "$RESOLVED_CONFIG"
    sed -i.bak "s|\${STORAGE_ALLOWED_MIME_TYPES}|$STORAGE_ALLOWED_MIME_TYPES|g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${REALTIME_MAX_CONNECTIONS:-1000}/$REALTIME_MAX_CONNECTIONS/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${EDGE_FUNCTIONS_MAX_EXECUTION_TIME:-30}/$EDGE_FUNCTIONS_MAX_EXECUTION_TIME/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${MONITORING_METRICS_RETENTION_DAYS:-30}/$MONITORING_METRICS_RETENTION_DAYS/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${MONITORING_LOG_RETENTION_DAYS:-7}/$MONITORING_LOG_RETENTION_DAYS/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${BACKUP_SCHEDULE:-0 2 \* \* \*}/$BACKUP_SCHEDULE/g" "$RESOLVED_CONFIG"
    sed -i.bak "s/\${BACKUP_RETENTION_DAYS:-30}/$BACKUP_RETENTION_DAYS/g" "$RESOLVED_CONFIG"
    
    # Clean up backup file
    rm -f "$RESOLVED_CONFIG.bak"
    echo "✅ Configuration resolved using sed"
fi

# Validate JSON
if command -v jq >/dev/null 2>&1; then
    if jq empty "$RESOLVED_CONFIG" 2>/dev/null; then
        echo "✅ JSON validation passed"
    else
        echo "❌ JSON validation failed"
        exit 1
    fi
else
    echo "⚠️  jq not available, skipping JSON validation"
fi

echo "📋 Configuration summary:"
echo "   - Project ID: $SUPABASE_PROJECT_ID"
echo "   - Database Host: $DATABASE_HOST"
echo "   - Site URL: $SITE_URL"
echo "   - Storage Bucket: $STORAGE_BUCKET_NAME"
echo "   - Resolved config saved to: $RESOLVED_CONFIG"
