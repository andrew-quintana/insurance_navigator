#!/bin/bash

# Check if ngrok URL is provided
if [ -z "$1" ]; then
    echo "Please provide the ngrok URL as an argument"
    echo "Usage: ./set-ngrok-url.sh https://your-ngrok-url"
    exit 1
fi

NGROK_URL=$1

# Remove trailing slash if present
NGROK_URL=${NGROK_URL%/}

# Set the environment variable in Supabase
supabase secrets set NGROK_URL="$NGROK_URL"

echo "✅ NGROK_URL has been set to: $NGROK_URL"
echo "🔄 Please restart your Supabase Edge Functions for the changes to take effect"
echo "   Run: supabase functions deploy doc-parser" 