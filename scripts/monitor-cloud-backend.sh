#!/bin/bash

# Cloud Backend Monitoring Script
source .env

echo "🔍 Cloud Backend Status Report"
echo "================================"

# Check trigger processor status
echo ""
echo "📋 Trigger Processor Status:"
curl -s -X GET "$SUPABASE_URL/functions/v1/trigger-processor" \
    -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" | jq '.'

# Check job processor status  
echo ""
echo "⚙️ Job Processor Status:"
curl -s -X GET "$SUPABASE_URL/functions/v1/job-processor" \
    -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" | jq '.'

echo ""
echo "✅ Monitoring complete"
