#!/bin/bash

# Job Processing Script for Medicare Navigator
# This script triggers the job processor to handle queued document processing jobs

# Load environment variables
source "$(dirname "$0")/../.env"

# Configuration
SUPABASE_URL="https://jhrespvvhbnloxrieycf.supabase.co"
JOB_PROCESSOR_URL="${SUPABASE_URL}/functions/v1/job-processor"
LOG_FILE="$(dirname "$0")/../logs/job-processor.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to process jobs
process_jobs() {
    log "🔄 Starting job processing cycle..."
    
    # Call job processor
    response=$(curl -s -X POST "$JOB_PROCESSOR_URL" \
        -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
        -H "Content-Type: application/json" \
        --max-time 30)
    
    # Check if curl succeeded
    if [ $? -eq 0 ]; then
        # Parse response
        processed=$(echo "$response" | jq -r '.processed // 0' 2>/dev/null)
        successful=$(echo "$response" | jq -r '.successful // 0' 2>/dev/null)
        failed=$(echo "$response" | jq -r '.failed // 0' 2>/dev/null)
        
        if [ "$processed" != "null" ] && [ "$processed" != "0" ]; then
            log "✅ Processed $processed jobs: $successful successful, $failed failed"
        else
            log "✅ No jobs to process"
        fi
    else
        log "❌ Failed to call job processor"
    fi
}

# Function to check for stuck jobs
check_stuck_jobs() {
    log "🔍 Checking for stuck jobs..."
    
    response=$(curl -s -X GET "$JOB_PROCESSOR_URL" \
        -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
        --max-time 10)
    
    if [ $? -eq 0 ]; then
        stuck_count=$(echo "$response" | jq -r '.stuckJobs | length' 2>/dev/null)
        failed_count=$(echo "$response" | jq -r '.failedJobs | length' 2>/dev/null)
        
        if [ "$stuck_count" != "null" ] && [ "$stuck_count" != "0" ]; then
            log "⚠️ Found $stuck_count stuck jobs"
        fi
        
        if [ "$failed_count" != "null" ] && [ "$failed_count" != "0" ]; then
            log "⚠️ Found $failed_count failed jobs"
        fi
    fi
}

# Main execution
main() {
    # Check if required environment variables are set
    if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
        log "❌ SUPABASE_SERVICE_ROLE_KEY not set"
        exit 1
    fi
    
    # Process jobs
    process_jobs
    
    # Check for issues (only every 5th run to reduce noise)
    if [ $(($(date +%M) % 5)) -eq 0 ]; then
        check_stuck_jobs
    fi
    
    log "✅ Job processing cycle complete"
}

# Run main function
main "$@" 