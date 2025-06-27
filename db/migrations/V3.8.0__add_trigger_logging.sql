-- Add logging to document processing trigger
BEGIN;

-- First create a trigger_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.trigger_logs (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    trigger_name text NOT NULL,
    document_id uuid,
    action text NOT NULL,
    status text NOT NULL,
    error_details jsonb,
    created_at timestamptz DEFAULT now()
);

-- Update the trigger function with logging
CREATE OR REPLACE FUNCTION public.create_document_processing_job()
RETURNS trigger AS $$
DECLARE
    v_job_id uuid;
    v_error_details jsonb;
BEGIN
    -- Log trigger start
    INSERT INTO trigger_logs (trigger_name, document_id, action, status)
    VALUES ('create_document_processing_job', NEW.id, TG_OP, 'started');

    BEGIN
        -- Attempt to insert the job
        INSERT INTO processing_jobs (
            job_type,
            status,
            priority,
            payload,
            scheduled_at
        ) VALUES (
            'parse',
            'pending',
            1,
            jsonb_build_object(
                'document_id', NEW.id,
                'document_type', NEW.document_type,
                'storage_path', NEW.storage_path,
                'content_type', NEW.content_type,
                'created_at', NEW.created_at
            ),
            NOW()
        ) RETURNING id INTO v_job_id;

        -- Log successful completion
        INSERT INTO trigger_logs (trigger_name, document_id, action, status, error_details)
        VALUES (
            'create_document_processing_job', 
            NEW.id, 
            TG_OP, 
            'completed',
            jsonb_build_object(
                'job_id', v_job_id,
                'success', true
            )
        );

    EXCEPTION WHEN OTHERS THEN
        -- Capture error details
        v_error_details := jsonb_build_object(
            'error_message', SQLERRM,
            'error_detail', SQLSTATE,
            'error_hint', sqlerrm_data(),
            'error_context', pg_exception_context()
        );

        -- Log error
        INSERT INTO trigger_logs (trigger_name, document_id, action, status, error_details)
        VALUES (
            'create_document_processing_job', 
            NEW.id, 
            TG_OP, 
            'error',
            v_error_details
        );

        -- Re-raise the error to ensure proper transaction handling
        RAISE;
    END;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMIT; 