#!/bin/bash
# Simple monitoring script for insurance navigator
echo "$(date): Checking job processing health..."

# Trigger job processing
curl -X POST "https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/job-processor" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"source": "monitoring", "timestamp": "'$(date -Iseconds)'"}' \
  --max-time 30

echo ""
echo "$(date): Job processing check complete"
