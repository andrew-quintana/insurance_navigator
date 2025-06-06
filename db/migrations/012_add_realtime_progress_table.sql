-- =============================================================================
-- Migration: Add Realtime Progress Updates Table
-- Version: 012
-- Description: Add table for real-time progress tracking via Supabase Realtime
-- =============================================================================

BEGIN;

-- Create realtime progress updates table
CREATE TABLE realtime_progress_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Index for efficient cleanup
    CONSTRAINT chk_payload_has_type CHECK (payload ? 'type')
);

-- Indexes for efficient queries
CREATE INDEX idx_realtime_progress_user ON realtime_progress_updates(user_id);
CREATE INDEX idx_realtime_progress_document ON realtime_progress_updates(document_id);
CREATE INDEX idx_realtime_progress_created ON realtime_progress_updates(created_at);

-- Enable RLS
ALTER TABLE realtime_progress_updates ENABLE ROW LEVEL SECURITY;

-- RLS Policy - users can only see their own progress updates
CREATE POLICY "users_own_progress_updates" ON realtime_progress_updates
    FOR ALL USING (
        user_id = get_current_user_id() OR 
        user_id = auth.uid() OR 
        is_admin()
    );

-- Cleanup function to remove old progress updates (older than 24 hours)
CREATE OR REPLACE FUNCTION cleanup_realtime_progress_updates()
RETURNS void AS $$
BEGIN
    DELETE FROM realtime_progress_updates 
    WHERE created_at < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql SECURITY INVOKER;

COMMIT; 