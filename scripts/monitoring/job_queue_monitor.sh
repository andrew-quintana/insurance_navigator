#!/bin/bash

# Job Queue Monitor for Medicare Navigator
# Usage: ./scripts/monitoring/job_queue_monitor.sh [option]
# Options: status, failed, running, recent, stats

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL environment variable not set${NC}"
    exit 1
fi

# Function to show job status summary
show_status() {
    echo -e "${BLUE}=== JOB QUEUE STATUS SUMMARY ===${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            status,
            job_type,
            COUNT(*) as count,
            MIN(created_at) as oldest,
            MAX(created_at) as newest
        FROM processing_jobs 
        GROUP BY status, job_type 
        ORDER BY status, job_type;
    "
}

# Function to show failed jobs
show_failed() {
    echo -e "${RED}=== FAILED JOBS ===${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            id,
            document_id,
            job_type,
            retry_count,
            max_retries,
            error_message,
            created_at
        FROM processing_jobs 
        WHERE status = 'failed'
        ORDER BY created_at DESC
        LIMIT 20;
    "
}

# Function to show running jobs
show_running() {
    echo -e "${YELLOW}=== RUNNING JOBS ===${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            id,
            document_id,
            job_type,
            started_at,
            EXTRACT(EPOCH FROM (NOW() - started_at)) as running_seconds
        FROM processing_jobs 
        WHERE status = 'running'
        ORDER BY started_at;
    "
}

# Function to show recent activity
show_recent() {
    echo -e "${GREEN}=== RECENT JOB ACTIVITY ===${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            id,
            document_id,
            job_type,
            status,
            priority,
            retry_count,
            scheduled_at,
            started_at,
            completed_at,
            CASE 
                WHEN error_message IS NOT NULL THEN LEFT(error_message, 50) || '...'
                ELSE NULL
            END as error_summary
        FROM processing_jobs 
        ORDER BY created_at DESC 
        LIMIT 15;
    "
}

# Function to show comprehensive stats
show_stats() {
    echo -e "${BLUE}=== COMPREHENSIVE STATISTICS ===${NC}"
    
    echo -e "\n${YELLOW}Job Status Distribution:${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            status,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM processing_jobs 
        GROUP BY status 
        ORDER BY count DESC;
    "
    
    echo -e "\n${YELLOW}Job Type Distribution:${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            job_type,
            COUNT(*) as count,
            AVG(CASE WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (completed_at - started_at)) 
                ELSE NULL END) as avg_duration_seconds
        FROM processing_jobs 
        GROUP BY job_type 
        ORDER BY count DESC;
    "
    
    echo -e "\n${YELLOW}Document Processing Status:${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            d.status,
            COUNT(*) as count,
            AVG(d.progress_percentage) as avg_progress
        FROM documents d
        GROUP BY d.status 
        ORDER BY count DESC;
    "
    
    echo -e "\n${YELLOW}Recent Processing Performance:${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            DATE_TRUNC('hour', created_at) as hour,
            COUNT(*) as jobs_created,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
        FROM processing_jobs 
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY DATE_TRUNC('hour', created_at)
        ORDER BY hour DESC
        LIMIT 12;
    "
}

# Function to show document status
show_documents() {
    echo -e "${GREEN}=== DOCUMENT PROCESSING STATUS ===${NC}"
    psql $DATABASE_URL -c "
        SELECT 
            d.id,
            d.original_filename,
            d.status,
            d.progress_percentage,
            d.processed_chunks,
            d.total_chunks,
            d.created_at,
            d.updated_at,
            COUNT(pj.id) as total_jobs,
            COUNT(CASE WHEN pj.status = 'completed' THEN 1 END) as completed_jobs,
            COUNT(CASE WHEN pj.status = 'failed' THEN 1 END) as failed_jobs
        FROM documents d
        LEFT JOIN processing_jobs pj ON d.id = pj.document_id
        GROUP BY d.id, d.original_filename, d.status, d.progress_percentage, 
                 d.processed_chunks, d.total_chunks, d.created_at, d.updated_at
        ORDER BY d.created_at DESC
        LIMIT 10;
    "
}

# Main script logic
case "${1:-status}" in
    "status")
        show_status
        ;;
    "failed")
        show_failed
        ;;
    "running")
        show_running
        ;;
    "recent")
        show_recent
        ;;
    "stats")
        show_stats
        ;;
    "documents")
        show_documents
        ;;
    "all")
        show_status
        echo ""
        show_running
        echo ""
        show_failed
        echo ""
        show_recent
        ;;
    *)
        echo -e "${YELLOW}Usage: $0 [option]${NC}"
        echo "Options:"
        echo "  status     - Show job status summary (default)"
        echo "  failed     - Show failed jobs"
        echo "  running    - Show currently running jobs"
        echo "  recent     - Show recent job activity"
        echo "  stats      - Show comprehensive statistics"
        echo "  documents  - Show document processing status"
        echo "  all        - Show all monitoring info"
        exit 1
        ;;
esac 