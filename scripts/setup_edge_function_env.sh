#!/bin/bash

# Function to extract variables from env file
extract_env_vars() {
    local env_file=$1
    local output_file=$2
    
    # Extract only the variables we need for edge functions
    grep -E '^(OPENAI_API_KEY|LLAMAPARSE_API_KEY|SUPABASE_URL|SUPABASE_SERVICE_ROLE_KEY|SUPABASE_ANON_KEY)=' "$env_file" > "$output_file"
}

# Determine which environment to use
ENV_TYPE=${1:-test}  # Default to test environment if not specified
PROJECT_ROOT=$(pwd)
SOURCE_ENV_FILE="$PROJECT_ROOT/.env.$ENV_TYPE"
TARGET_DIR="$PROJECT_ROOT/supabase/functions/upload-handler"
TARGET_ENV_FILE="$TARGET_DIR/.env"

# Check if source env file exists
if [ ! -f "$SOURCE_ENV_FILE" ]; then
    echo "Error: Environment file $SOURCE_ENV_FILE not found"
    exit 1
fi

# Create edge function env directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Extract and copy environment variables
extract_env_vars "$SOURCE_ENV_FILE" "$TARGET_ENV_FILE"

echo "Environment variables copied to $TARGET_ENV_FILE"
echo "You can now run the edge function with:"
echo "supabase functions serve upload-handler --env-file .env --no-verify-jwt" 