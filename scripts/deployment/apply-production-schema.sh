#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔄 Starting database deployment process..."

# Step 1: Link project if not already linked
echo "Checking project link..."
supabase link || {
    echo -e "${RED}Failed to link project. Please run 'supabase login' first and try again.${NC}"
    exit 1
}

# Step 2: Create backup before migration
echo "Creating pre-deployment backup..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/pre_deploy_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

supabase db dump -f "$BACKUP_DIR/pre_rollback.sql" || {
    echo -e "${RED}Failed to create backup. Aborting deployment.${NC}"
    exit 1
}

# Step 3: Apply migrations
echo "Applying migrations..."
supabase db push || {
    echo -e "${RED}Migration failed. Rolling back...${NC}"
    # Note: Manual intervention may be needed for rollback
    echo "Backup available at: $BACKUP_DIR/pre_rollback.sql"
    exit 1
}

# Step 4: Verify database state
echo "Verifying database state..."
supabase db reset --dry-run || {
    echo -e "${RED}Database state verification failed.${NC}"
    echo "Please check the migration logs and backup at: $BACKUP_DIR/pre_rollback.sql"
    exit 1
}

echo -e "${GREEN}✅ Database deployment completed successfully!${NC}"
echo "Backup location: $BACKUP_DIR/pre_rollback.sql" 