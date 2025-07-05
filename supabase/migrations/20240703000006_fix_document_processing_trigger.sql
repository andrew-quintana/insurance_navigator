-- =============================================================================
-- FIX DOCUMENT PROCESSING TRIGGER
-- Description: Fix trigger function to properly handle document processing
-- Version: 20240703_6
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- =============================================================================
-- STEP 1: DROP EXISTING TRIGGER AND FUNCTION
-- =============================================================================

DROP TRIGGER IF EXISTS trigger_process_document ON documents;
DROP FUNCTION IF EXISTS process_document();

-- =============================================================================
-- STEP 2: CREATE IMPROVED TRIGGER FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION process_document()
RETURNS trigger AS $$
DECLARE
    edge_function_url text;
    service_role_key text;
BEGIN
    -- Get configuration from environment
    edge_function_url := current_setting('app.settings.edge_function_url', true);
    service_role_key := current_setting('app.settings.service_role_key', true);
    
    -- Validate configuration
    IF edge_function_url IS NULL THEN
        RAISE WARNING 'Edge function URL not configured';
        edge_function_url := 'http://127.0.0.1:54321/functions/v1/upload-handler';
    END IF;
    
    IF service_role_key IS NULL THEN
        RAISE WARNING 'Service role key not configured';
        -- Use a default key for development only
        service_role_key := '***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.p2fuVDatv5iaDizrYVeg2Gx_U1utFdpwLHwkiZfsRxs';
    END IF;

    -- Log processing attempt
    INSERT INTO processing_logs (
        document_id,
        stage,
        status,
        metadata
    ) VALUES (
        NEW.id,
        'trigger',
        'started',
        jsonb_build_object(
            'trigger_time', now(),
            'document_status', NEW.status,
            'content_type', NEW.content_type
        )
    );

    -- Call the Edge Function to process the document
    PERFORM
        net.http_post(
            url := edge_function_url,
            headers := jsonb_build_object(
                'Authorization', concat('Bearer ', service_role_key),
                'Content-Type', 'application/json'
            )::jsonb,
            body := jsonb_build_object(
                'document_id', NEW.id,
                'storage_path', NEW.storage_path,
                'content_type', NEW.content_type
            )::jsonb
        );

    -- Log successful trigger
    INSERT INTO processing_logs (
        document_id,
        stage,
        status,
        metadata
    ) VALUES (
        NEW.id,
        'trigger',
        'completed',
        jsonb_build_object(
            'completion_time', now(),
            'edge_function_url', edge_function_url
        )
    );

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    -- Log error
    INSERT INTO processing_logs (
        document_id,
        stage,
        status,
        error_message,
        metadata
    ) VALUES (
        NEW.id,
        'trigger',
        'error',
        SQLERRM,
        jsonb_build_object(
            'error_time', now(),
            'edge_function_url', edge_function_url,
            'sqlstate', SQLSTATE
        )
    );
    
    -- Re-raise the error
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- STEP 3: CREATE NEW TRIGGER
-- =============================================================================

CREATE TRIGGER trigger_process_document
    AFTER INSERT ON documents
    FOR EACH ROW
    WHEN (NEW.status = 'processing')
    EXECUTE FUNCTION process_document();

-- =============================================================================
-- STEP 4: GRANT NECESSARY PERMISSIONS
-- =============================================================================

-- Grant usage on net schema to postgres
GRANT USAGE ON SCHEMA net TO postgres;

-- Grant execute on net functions to postgres
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA net TO postgres;

COMMIT; 