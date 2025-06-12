#!/bin/bash

# Real-time Job Queue Monitor
# Usage: ./scripts/monitoring/watch_jobs.sh [refresh_seconds]
# Default refresh: 5 seconds

set -e

REFRESH_INTERVAL=${1:-5}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL environment variable not set${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Real-time Job Queue Monitor${NC}"
echo -e "${YELLOW}Refreshing every ${REFRESH_INTERVAL} seconds. Press Ctrl+C to stop.${NC}"
echo ""

while true; do
    # Clear screen
    clear
    
    # Show timestamp
    echo -e "${BLUE}=== $(date) ===${NC}"
    echo ""
    
    # Show active jobs summary
    echo -e "${GREEN}📊 ACTIVE JOBS SUMMARY${NC}"
    psql $DATABASE_URL -t -c "
        SELECT 
            '🔄 ' || status || ': ' || COUNT(*) || ' jobs'
        FROM processing_jobs 
        WHERE status IN ('pending', 'running', 'retrying')
        GROUP BY status 
        ORDER BY 
            CASE status 
                WHEN 'running' THEN 1 
                WHEN 'pending' THEN 2 
                WHEN 'retrying' THEN 3 
            END;
    " 2>/dev/null || echo "No active jobs"
    
    echo ""
    
    # Show running jobs
    echo -e "${YELLOW}⚡ CURRENTLY RUNNING${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            LEFT(id::text, 8) as job_id,
            job_type,
            EXTRACT(EPOCH FROM (NOW() - started_at))::int as running_sec,
            LEFT(document_id::text, 8) as doc_id
        FROM processing_jobs 
        WHERE status = 'running'
        ORDER BY started_at;
    " 2>/dev/null || echo "No running jobs"
    
    echo ""
    
    # Show pending jobs
    echo -e "${BLUE}⏳ PENDING JOBS${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            LEFT(id::text, 8) as job_id,
            job_type,
            priority,
            EXTRACT(EPOCH FROM (NOW() - scheduled_at))::int as waiting_sec,
            LEFT(document_id::text, 8) as doc_id
        FROM processing_jobs 
        WHERE status = 'pending'
        ORDER BY priority DESC, scheduled_at
        LIMIT 5;
    " 2>/dev/null || echo "No pending jobs"
    
    echo ""
    
    # Show recent failures
    echo -e "${RED}❌ RECENT FAILURES${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            LEFT(id::text, 8) as job_id,
            job_type,
            retry_count,
            LEFT(error_message, 40) || '...' as error
        FROM processing_jobs 
        WHERE status = 'failed' AND updated_at > NOW() - INTERVAL '1 hour'
        ORDER BY updated_at DESC
        LIMIT 3;
    " 2>/dev/null || echo "No recent failures"
    
    echo ""
    
    # Show document status
    echo -e "${GREEN}📄 RECENT DOCUMENTS${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            LEFT(id::text, 8) as doc_id,
            LEFT(original_filename, 25) as filename,
            status,
            progress_percentage || '%' as progress
        FROM documents 
        WHERE created_at > NOW() - INTERVAL '2 hours'
        ORDER BY created_at DESC
        LIMIT 5;
    " 2>/dev/null || echo "No recent documents"
    
    echo ""
    echo -e "${YELLOW}Next refresh in ${REFRESH_INTERVAL}s... (Ctrl+C to stop)${NC}"
    
    # Wait for refresh interval
    sleep $REFRESH_INTERVAL
done 