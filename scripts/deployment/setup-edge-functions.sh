#!/bin/bash

set -e

ENV_TYPE=${1:-development}
PROJECT_ROOT=$(pwd)
SHARED_DIR="$PROJECT_ROOT/supabase/functions/_shared"
EDGE_FUNCTIONS=(
  "doc-processor"
  "vector-service"
  "chunking-service"
  "doc-parser"
  "processing-supervisor"
)

# Create _shared directory if it doesn't exist
mkdir -p "$SHARED_DIR"

# Copy environment module to _shared
cp "$PROJECT_ROOT/config/environment.ts" "$SHARED_DIR/environment.ts"

# For each edge function, set up its environment
for func in "${EDGE_FUNCTIONS[@]}"; do
  FUNC_DIR="$PROJECT_ROOT/supabase/functions/$func"
  
  # Create .env file for the function
  echo "Setting up environment for $func"
  
  # For test environment, use test-specific env file
  if [ "$ENV_TYPE" = "test" ]; then
    ENV_FILE="$PROJECT_ROOT/supabase/functions/tests/env.test"
  else
    ENV_FILE="$PROJECT_ROOT/.env.$ENV_TYPE"
  fi
  
  # Create function directory if it doesn't exist
  mkdir -p "$FUNC_DIR"
  
  # Extract relevant variables from env file
  grep -E '^(OPENAI_API_KEY|LLAMAPARSE_API_KEY|SUPABASE_URL|SUPABASE_SERVICE_ROLE_KEY|SUPABASE_DB_URL|TEST_USER_ID|TEST_USER_EMAIL|TEST_USER_PASSWORD|ENABLE_VECTOR_PROCESSING|ENABLE_REGULATORY_PROCESSING)=' \
    "$ENV_FILE" > "$FUNC_DIR/.env"
    
  # Add environment type
  echo "ENV=$ENV_TYPE" >> "$FUNC_DIR/.env"
done

echo "Edge function environments configured for $ENV_TYPE deployment"