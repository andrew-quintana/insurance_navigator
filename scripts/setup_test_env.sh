#!/bin/bash

# Check if .env.test exists, if not create it from example
if [ ! -f .env.test ]; then
    echo "Creating .env.test file with test configuration..."
    
    # Generate a secure JWT secret
    JWT_SECRET=$(openssl rand -base64 32)
    
    cat > .env.test << EOL
# Test Environment Configuration
NODE_ENV=test

# Supabase Configuration
SUPABASE_TEST_URL=http://127.0.0.1:54321
SUPABASE_TEST_KEY=${SUPABASE_JWT_TOKEN}
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_JWT_TOKEN}

# JWT Configuration
SUPABASE_JWT_SECRET=${JWT_SECRET}
JWT_SECRET=${JWT_SECRET}

# Database Configuration
DB_HOST=localhost
DB_PORT=54322
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres

# Security Settings
DOCUMENT_ENCRYPTION_KEY=$(openssl rand -base64 32)
AUDIT_LOGGING_ENABLED=true
CONSENT_VERSION=1.0

# HIPAA Compliance Settings
DATA_RETENTION_DAYS=2190  # 6 years in days
SSL_ENFORCE=true
NETWORK_RESTRICTIONS=true
EOL
fi

# Source the environment variables
source .env.test

# Ensure JWT secret is set and synchronized
if [ -z "$SUPABASE_JWT_SECRET" ] || [ -z "$JWT_SECRET" ]; then
    echo "Generating new JWT secret..."
    JWT_SECRET=$(openssl rand -base64 32)
    echo "SUPABASE_JWT_SECRET=${JWT_SECRET}" >> .env.test
    echo "JWT_SECRET=${JWT_SECRET}" >> .env.test
    source .env.test
fi

# Verify JWT secret is set and synchronized
if [ "$SUPABASE_JWT_SECRET" != "$JWT_SECRET" ]; then
    echo "Warning: JWT secrets do not match. Synchronizing..."
    JWT_SECRET=$SUPABASE_JWT_SECRET
    echo "JWT_SECRET=${JWT_SECRET}" >> .env.test
    source .env.test
fi

# Start Supabase services if not running
if ! supabase status | grep -q "Started"; then
    echo "Starting Supabase services..."
    supabase start
fi

# Run database migrations
echo "Running database migrations..."
supabase db reset --force

# Run the tests
echo "Running tests..."
pytest tests/ -v 