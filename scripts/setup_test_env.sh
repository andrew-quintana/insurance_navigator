#!/bin/bash

# Check if .env.test exists, if not create it from example
if [ ! -f .env.test ]; then
    echo "Creating .env.test file with test configuration..."
    cat > .env.test << EOL
# Test Environment Configuration
NODE_ENV=test

# Supabase Configuration
SUPABASE_TEST_URL=http://127.0.0.1:54321
SUPABASE_TEST_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
SUPABASE_JWT_SECRET=your-super-secret-jwt-token-with-at-least-32-characters-long

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