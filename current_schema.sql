

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pg_cron" WITH SCHEMA "pg_catalog";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_net" WITH SCHEMA "public";






CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA "public";






CREATE OR REPLACE FUNCTION "public"."auto_create_processing_job"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
            BEGIN
                -- Only create job for newly uploaded documents
                IF NEW.status = 'pending' AND (OLD IS NULL OR OLD.status != 'pending') THEN
                    -- Create a parse job
                    INSERT INTO processing_jobs (
                        document_id, job_type, status, priority, 
                        max_retries, retry_count, created_at, scheduled_at
                    ) VALUES (
                        NEW.id, 'parse', 'pending', 5,
                        3, 0, NOW(), NOW() + INTERVAL '5 seconds'
                    );
                    
                    RAISE LOG 'Auto-created processing job for document %', NEW.original_filename;
                END IF;
                
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION "public"."auto_create_processing_job"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."backfill_stuck_documents"() RETURNS TABLE("document_id" "uuid", "filename" "text", "jobs_created" integer)
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    doc_record RECORD;
    job_count INTEGER;
BEGIN
    -- Find documents that are stuck (uploaded but no processing jobs)
    FOR doc_record IN 
        SELECT d.id, d.original_filename, d.file_path, d.user_id, d.status, d.processing_status
        FROM user_documents d
        LEFT JOIN processing_jobs pj ON d.id = pj.document_id
        WHERE d.status IN ('pending', 'uploaded') 
          AND d.processing_status IN ('pending', 'uploaded')
          AND pj.id IS NULL -- No existing jobs
          AND d.created_at > NOW() - INTERVAL '7 days' -- Only recent documents
    LOOP
        -- Create a parse job for this stuck document
        INSERT INTO processing_jobs (
            id,
            document_id,
            job_type,
            payload,
            status,
            priority,
            max_retries,
            retry_count,
            created_at,
            scheduled_at
        ) VALUES (
            gen_random_uuid(),
            doc_record.id,
            'parse',
            jsonb_build_object(
                'filename', doc_record.original_filename,
                'file_path', doc_record.file_path,
                'user_id', doc_record.user_id
            ),
            'pending',
            1, -- priority
            3, -- max_retries
            0, -- retry_count
            NOW(),
            NOW() + INTERVAL '10 seconds' -- process in 10 seconds
        );
        
        job_count := 1;
        
        -- Update document status
        UPDATE user_documents 
        SET 
            processing_status = 'processing',
            updated_at = NOW()
        WHERE id = doc_record.id;
        
        -- Return info about processed document
        document_id := doc_record.id;
        filename := doc_record.original_filename;
        jobs_created := job_count;
        
        RETURN NEXT;
        
        RAISE LOG 'Backfilled processing job for stuck document %: %', doc_record.id, doc_record.original_filename;
    END LOOP;
    
    RETURN;
END;
$$;


ALTER FUNCTION "public"."backfill_stuck_documents"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."can_access_policy"("policy_uuid" "uuid") RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Validate input parameter
    IF policy_uuid IS NULL THEN
        RETURN false;
    END IF;
    
    -- Admin users can access all policies
    IF public.is_admin() THEN
        RETURN true;
    END IF;
    
    -- Regular users can access policies they are linked to with verified relationships
    RETURN EXISTS (
        SELECT 1 
        FROM user_policy_links
        WHERE policy_id = policy_uuid
        AND user_id = public.get_current_user_id()
        AND relationship_verified = true
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Fail secure: if any error occurs, deny policy access
        RETURN false;
END;
$$;


ALTER FUNCTION "public"."can_access_policy"("policy_uuid" "uuid") OWNER TO "postgres";


COMMENT ON FUNCTION "public"."can_access_policy"("policy_uuid" "uuid") IS 'Securely check if the current user can access a specific policy record. Uses SECURITY INVOKER and fixed search path.';



CREATE OR REPLACE FUNCTION "public"."check_job_processing_health"() RETURNS TABLE("status" "text", "stuck_jobs_count" integer, "failed_jobs_count" integer, "processing_time_avg" numeric, "recommendation" "text")
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    RETURN QUERY
    WITH job_stats AS (
        SELECT 
            COUNT(*) FILTER (WHERE status = 'pending' AND created_at < NOW() - INTERVAL '10 minutes') as stuck_pending,
            COUNT(*) FILTER (WHERE status = 'running' AND started_at < NOW() - INTERVAL '30 minutes') as stuck_running,
            COUNT(*) FILTER (WHERE status = 'failed' AND updated_at > NOW() - INTERVAL '1 hour') as recent_failed,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) FILTER (WHERE status = 'completed' AND completed_at > NOW() - INTERVAL '1 hour') as avg_processing_time
        FROM processing_jobs
    )
    SELECT 
        CASE 
            WHEN stuck_pending + stuck_running = 0 AND recent_failed <= 2 THEN 'healthy'
            WHEN stuck_pending + stuck_running <= 3 AND recent_failed <= 5 THEN 'warning'
            ELSE 'critical'
        END as status,
        (stuck_pending + stuck_running)::INTEGER as stuck_jobs_count,
        recent_failed::INTEGER as failed_jobs_count,
        COALESCE(avg_processing_time, 0)::NUMERIC as processing_time_avg,
        CASE 
            WHEN stuck_pending > 5 THEN 'Multiple jobs stuck in pending - check cron jobs'
            WHEN stuck_running > 3 THEN 'Multiple jobs stuck running - check edge functions'
            WHEN recent_failed > 10 THEN 'High failure rate - check error logs'
            WHEN avg_processing_time > 300 THEN 'Slow processing - optimize edge functions'
            ELSE 'System operating normally'
        END as recommendation
    FROM job_stats;
END;
$$;


ALTER FUNCTION "public"."check_job_processing_health"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."check_queue_health"() RETURNS TABLE("status" "text", "details" "jsonb")
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    health_record RECORD;
BEGIN
    SELECT * INTO health_record FROM queue_health;
    
    -- Return overall health status
    RETURN QUERY
    SELECT
        CASE 
            WHEN health_record.stuck_jobs > 0 THEN 'WARNING'
            WHEN health_record.failed_jobs > health_record.completed_jobs THEN 'DEGRADED'
            WHEN health_record.pending_jobs = 0 AND health_record.running_jobs = 0 THEN 'IDLE'
            ELSE 'HEALTHY'
        END,
        jsonb_build_object(
            'pending_jobs', health_record.pending_jobs,
            'running_jobs', health_record.running_jobs,
            'failed_jobs', health_record.failed_jobs,
            'completed_jobs', health_record.completed_jobs,
            'stuck_jobs', health_record.stuck_jobs,
            'avg_completion_time_sec', health_record.avg_completion_time_sec,
            'uploading_docs', health_record.uploading_docs,
            'processing_docs', health_record.processing_docs,
            'completed_docs', health_record.completed_docs,
            'failed_docs', health_record.failed_docs,
            'checked_at', health_record.checked_at
        );
END;
$$;


ALTER FUNCTION "public"."check_queue_health"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."cleanup_old_jobs"() RETURNS integer
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM processing_jobs 
    WHERE status IN ('completed', 'failed') 
      AND updated_at < NOW() - INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;


ALTER FUNCTION "public"."cleanup_old_jobs"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."cleanup_realtime_progress_updates"() RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    DELETE FROM realtime_progress_updates 
    WHERE created_at < NOW() - INTERVAL '24 hours';
END;
$$;


ALTER FUNCTION "public"."cleanup_realtime_progress_updates"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."clear_user_context"() RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Clear the user context for testing purposes
    PERFORM set_config('rls.current_user_id', '', false);
EXCEPTION
    WHEN OTHERS THEN
        -- Silently fail if context clearing fails
        RETURN;
END;
$$;


ALTER FUNCTION "public"."clear_user_context"() OWNER TO "postgres";


COMMENT ON FUNCTION "public"."clear_user_context"() IS 'Clear user context for testing purposes. Uses SECURITY INVOKER and fixed search path.';



CREATE OR REPLACE FUNCTION "public"."complete_processing_job"("job_id_param" "uuid", "job_result" "jsonb" DEFAULT NULL::"jsonb") RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    UPDATE processing_jobs 
    SET 
        status = 'completed',
        completed_at = NOW(),
        updated_at = NOW(),
        result = job_result
    WHERE id = job_id_param AND status = 'running';
    
    RETURN FOUND;
END;
$$;


ALTER FUNCTION "public"."complete_processing_job"("job_id_param" "uuid", "job_result" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."create_processing_job"("doc_id" "uuid", "job_type_param" "text", "job_payload" "jsonb" DEFAULT '{}'::"jsonb", "priority_param" integer DEFAULT 0, "max_retries_param" integer DEFAULT 3, "schedule_delay_seconds" integer DEFAULT 0) RETURNS "uuid"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    job_id UUID;
    schedule_time TIMESTAMPTZ;
BEGIN
    -- Calculate scheduled time
    schedule_time := NOW() + (schedule_delay_seconds || ' seconds')::INTERVAL;
    
    -- Insert job
    INSERT INTO processing_jobs (
        document_id, job_type, payload, priority, max_retries, scheduled_at
    ) VALUES (
        doc_id, job_type_param, job_payload, priority_param, max_retries_param, schedule_time
    ) RETURNING id INTO job_id;
    
    RETURN job_id;
END;
$$;


ALTER FUNCTION "public"."create_processing_job"("doc_id" "uuid", "job_type_param" "text", "job_payload" "jsonb", "priority_param" integer, "max_retries_param" integer, "schedule_delay_seconds" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."evaluate_feature_flag"("flag_name_param" "text", "user_id_param" "uuid" DEFAULT NULL::"uuid", "user_email_param" "text" DEFAULT NULL::"text") RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    flag_record feature_flags%ROWTYPE;
    user_hash INTEGER;
    evaluation_result BOOLEAN := false;
    reason TEXT := 'disabled';
BEGIN
    SELECT * INTO flag_record FROM feature_flags WHERE flag_name = flag_name_param;
    
    IF NOT FOUND OR NOT flag_record.is_enabled THEN
        reason := 'disabled';
        evaluation_result := false;
    ELSE
        IF user_id_param = ANY(flag_record.enabled_user_ids) OR 
           user_email_param = ANY(flag_record.enabled_user_emails) THEN
            reason := 'user_enabled';
            evaluation_result := true;
        ELSIF user_id_param = ANY(flag_record.disabled_user_ids) THEN
            reason := 'user_disabled';  
            evaluation_result := false;
        ELSE
            user_hash := hashtext(COALESCE(user_id_param::text, user_email_param, ''));
            IF (user_hash % 100) < flag_record.rollout_percentage THEN
                reason := 'percentage_enabled';
                evaluation_result := true;
            ELSE
                reason := 'percentage_disabled';
                evaluation_result := false;
            END IF;
        END IF;
    END IF;
    
    INSERT INTO feature_flag_evaluations (
        flag_name, user_id, user_email, evaluation_result, evaluation_reason
    ) VALUES (
        flag_name_param, user_id_param, user_email_param, evaluation_result, reason
    );
    
    RETURN evaluation_result;
END;
$$;


ALTER FUNCTION "public"."evaluate_feature_flag"("flag_name_param" "text", "user_id_param" "uuid", "user_email_param" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."fail_processing_job"("job_id_param" "uuid", "error_msg" "text", "error_details_param" "jsonb" DEFAULT NULL::"jsonb") RETURNS "text"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    job_record processing_jobs%ROWTYPE;
    next_retry_delay INTEGER;
BEGIN
    -- Get current job state
    SELECT * INTO job_record FROM processing_jobs WHERE id = job_id_param;
    
    IF NOT FOUND THEN
        RETURN 'job_not_found';
    END IF;
    
    -- Check if we can retry
    IF job_record.retry_count < job_record.max_retries THEN
        -- Calculate exponential backoff: 1min, 5min, 15min
        next_retry_delay := POWER(5, job_record.retry_count) * 60;
        
        UPDATE processing_jobs 
        SET 
            status = 'retrying',
            retry_count = retry_count + 1,
            error_message = error_msg,
            error_details = error_details_param,
            scheduled_at = NOW() + (next_retry_delay || ' seconds')::INTERVAL,
            updated_at = NOW()
        WHERE id = job_id_param;
        
        RETURN 'scheduled_retry';
    ELSE
        -- Max retries reached, mark as permanently failed
        UPDATE processing_jobs 
        SET 
            status = 'failed',
            error_message = error_msg,
            error_details = error_details_param,
            updated_at = NOW()
        WHERE id = job_id_param;
        
        RETURN 'permanently_failed';
    END IF;
END;
$$;


ALTER FUNCTION "public"."fail_processing_job"("job_id_param" "uuid", "error_msg" "text", "error_details_param" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_current_user_id"() RETURNS "uuid"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    session_user_id uuid;
    auth_user_id uuid;
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Try to get user ID from session context first (preferred method)
    BEGIN
        session_user_id := NULLIF(current_setting('rls.current_user_id', true), '')::uuid;
    EXCEPTION
        WHEN OTHERS THEN
            session_user_id := NULL;
    END;
    
    -- If session context is available, use it
    IF session_user_id IS NOT NULL THEN
        RETURN session_user_id;
    END IF;
    
    -- Try auth schema as fallback (only if auth context is explicitly set)
    BEGIN
        auth_user_id := (SELECT auth.uid());
        -- Only return auth user ID if it's actually set (not null)
        IF auth_user_id IS NOT NULL THEN
            RETURN auth_user_id;
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            -- Auth schema not available or error occurred
            NULL;
    END;
    
    -- No authenticated user context available
    RETURN NULL;
EXCEPTION
    WHEN OTHERS THEN
        -- If any error occurs, return null (no authenticated user)
        RETURN NULL;
END;
$$;


ALTER FUNCTION "public"."get_current_user_id"() OWNER TO "postgres";


COMMENT ON FUNCTION "public"."get_current_user_id"() IS 'Securely get the current authenticated user ID. Prefers session context over auth JWT. Returns null if no authenticated user. Uses SECURITY INVOKER and fixed search path.';



CREATE OR REPLACE FUNCTION "public"."get_pending_jobs"("limit_param" integer DEFAULT 10) RETURNS TABLE("id" "uuid", "document_id" "uuid", "job_type" character varying, "payload" "jsonb", "retry_count" integer, "priority" integer)
    LANGUAGE "plpgsql"
    AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                pj.id,
                pj.document_id,
                pj.job_type,
                pj.payload,
                pj.retry_count,
                pj.priority
            FROM processing_jobs pj
            WHERE pj.status IN ('pending', 'retrying')
              AND pj.scheduled_at <= NOW()
            ORDER BY pj.priority DESC, pj.created_at ASC
            LIMIT limit_param;
        END;
        $$;


ALTER FUNCTION "public"."get_pending_jobs"("limit_param" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_policy_facts"("document_uuid" "uuid") RETURNS "jsonb"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    policy_data JSONB;
BEGIN
    SELECT policy_basics INTO policy_data
    FROM user_documents 
    WHERE id = document_uuid;
    
    RETURN COALESCE(policy_data, '{}'::jsonb);
END;
$$;


ALTER FUNCTION "public"."get_policy_facts"("document_uuid" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_job_completion"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    doc_record documents%ROWTYPE;
BEGIN
    -- Only handle completed jobs
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        -- Get document info
        SELECT * INTO doc_record FROM documents WHERE id = NEW.document_id;
        
        -- Handle different job types
        CASE NEW.job_type
            WHEN 'parse' THEN
                -- Create embed job after successful parse
                INSERT INTO processing_jobs (
                    id, document_id, job_type, status, priority, 
                    max_retries, retry_count, created_at
                ) VALUES (
                    gen_random_uuid(), NEW.document_id, 'embed', 'pending',
                    1, 3, 0, NOW()
                );
                
                -- Update document progress
                UPDATE documents 
                SET progress_percentage = 50
                WHERE id = NEW.document_id;
                
            WHEN 'embed' THEN
                -- Mark document as completed after successful embed
                UPDATE documents 
                SET 
                    status = 'completed',
                    progress_percentage = 100,
                    updated_at = NOW()
                WHERE id = NEW.document_id;
        END CASE;
        
        RAISE LOG 'Processed job completion: % type % for document %', 
            NEW.id, NEW.job_type, doc_record.original_filename;
    END IF;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."handle_job_completion"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_job_failure"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    doc_record documents%ROWTYPE;
BEGIN
    -- Only handle newly failed jobs
    IF NEW.status = 'failed' AND OLD.status != 'failed' THEN
        -- Get document info
        SELECT * INTO doc_record FROM documents WHERE id = NEW.document_id;
        
        -- If max retries exceeded, mark document as failed
        IF NEW.retry_count >= NEW.max_retries THEN
            UPDATE documents 
            SET 
                status = 'failed',
                error_message = NEW.error_message,
                updated_at = NOW()
            WHERE id = NEW.document_id;
            
            RAISE LOG 'Document % failed after % retries: %', 
                doc_record.original_filename, NEW.retry_count, NEW.error_message;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."handle_job_failure"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."has_role"("role_name" "text") RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    current_user_id uuid;
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Validate input parameter
    IF role_name IS NULL OR trim(role_name) = '' THEN
        RETURN false;
    END IF;
    
    -- Get current user ID
    current_user_id := public.get_current_user_id();
    
    -- If no user context, definitely no roles
    IF current_user_id IS NULL THEN
        RETURN false;
    END IF;
    
    -- Check if current user has the specified role
    RETURN EXISTS (
        SELECT 1 
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = current_user_id
        AND r.name = trim(role_name)
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Fail secure: if any error occurs, deny role access
        RETURN false;
END;
$$;


ALTER FUNCTION "public"."has_role"("role_name" "text") OWNER TO "postgres";


COMMENT ON FUNCTION "public"."has_role"("role_name" "text") IS 'Securely check if the current authenticated user has a specific role. Uses SECURITY INVOKER and fixed search path.';



CREATE OR REPLACE FUNCTION "public"."is_admin"() RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    current_user_id uuid;
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Get current user ID
    current_user_id := public.get_current_user_id();
    
    -- If no user context, definitely not admin
    IF current_user_id IS NULL THEN
        RETURN false;
    END IF;
    
    -- Check if current user has admin role through proper authentication
    RETURN EXISTS (
        SELECT 1 
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = current_user_id
        AND r.name = 'admin'
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Fail secure: if any error occurs, deny admin access
        RETURN false;
END;
$$;


ALTER FUNCTION "public"."is_admin"() OWNER TO "postgres";


COMMENT ON FUNCTION "public"."is_admin"() IS 'Securely check if the current authenticated user has admin role. Uses SECURITY INVOKER and fixed search path.';



CREATE OR REPLACE FUNCTION "public"."log_policy_access"("policy_uuid" "uuid", "access_type" "text", "success" boolean DEFAULT true, "details" "jsonb" DEFAULT '{}'::"jsonb") RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Validate required parameters
    IF policy_uuid IS NULL OR access_type IS NULL THEN
        RETURN; -- Silently fail for audit logs to not break application flow
    END IF;
    
    -- Insert audit log entry
    INSERT INTO policy_access_logs (
        user_id,
        policy_id,
        access_type,
        success,
        access_details,
        timestamp
    ) VALUES (
        public.get_current_user_id(),
        policy_uuid,
        trim(access_type),
        success,
        details,
        CURRENT_TIMESTAMP
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Silently fail for audit logs to not break application flow
        RETURN;
END;
$$;


ALTER FUNCTION "public"."log_policy_access"("policy_uuid" "uuid", "access_type" "text", "success" boolean, "details" "jsonb") OWNER TO "postgres";


COMMENT ON FUNCTION "public"."log_policy_access"("policy_uuid" "uuid", "access_type" "text", "success" boolean, "details" "jsonb") IS 'Securely log policy access attempts for audit trail. Uses SECURITY INVOKER and fixed search path.';



CREATE OR REPLACE FUNCTION "public"."log_user_action"("user_uuid" "uuid", "action_type" "text", "resource_type" "text", "resource_id" "text" DEFAULT NULL::"text", "action_details" "jsonb" DEFAULT NULL::"jsonb", "client_ip" "inet" DEFAULT NULL::"inet", "client_user_agent" "text" DEFAULT NULL::"text") RETURNS "uuid"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    log_id UUID;
BEGIN
    INSERT INTO audit_logs (
        user_id, action, resource_type, resource_id, 
        details, ip_address, user_agent
    ) VALUES (
        user_uuid, action_type, resource_type, resource_id,
        action_details, client_ip, client_user_agent
    ) RETURNING id INTO log_id;
    
    RETURN log_id;
END;
$$;


ALTER FUNCTION "public"."log_user_action"("user_uuid" "uuid", "action_type" "text", "resource_type" "text", "resource_id" "text", "action_details" "jsonb", "client_ip" "inet", "client_user_agent" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."monitor_processing_queue"() RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    stuck_job RECORD;
    failed_job RECORD;
BEGIN
    -- Check for stuck jobs (running for too long)
    FOR stuck_job IN 
        SELECT 
            pj.id as job_id,
            pj.document_id,
            pj.job_type,
            pj.created_at,
            d.original_filename
        FROM processing_jobs pj
        JOIN documents d ON d.id = pj.document_id
        WHERE pj.status = 'running'
          AND pj.created_at < NOW() - INTERVAL '30 minutes'
    LOOP
        -- Mark stuck jobs as failed
        UPDATE processing_jobs 
        SET 
            status = 'failed',
            error_message = 'Job stuck in running state for over 30 minutes',
            updated_at = NOW()
        WHERE id = stuck_job.job_id;
        
        RAISE LOG 'Marked stuck job as failed: % for document %', stuck_job.job_id, stuck_job.original_filename;
    END LOOP;

    -- Retry failed jobs that haven't exceeded max retries
    FOR failed_job IN 
        SELECT 
            pj.id as job_id,
            pj.document_id,
            pj.job_type,
            pj.retry_count,
            pj.max_retries,
            d.original_filename
        FROM processing_jobs pj
        JOIN documents d ON d.id = pj.document_id
        WHERE pj.status = 'failed'
          AND pj.retry_count < pj.max_retries
          AND pj.created_at > NOW() - INTERVAL '24 hours'
    LOOP
        -- Reset failed job to pending
        UPDATE processing_jobs 
        SET 
            status = 'pending',
            retry_count = retry_count + 1,
            updated_at = NOW(),
            error_message = NULL
        WHERE id = failed_job.job_id;
        
        RAISE LOG 'Retrying failed job: % for document % (attempt %/%)', 
            failed_job.job_id, failed_job.original_filename, 
            failed_job.retry_count + 1, failed_job.max_retries;
    END LOOP;
END;
$$;


ALTER FUNCTION "public"."monitor_processing_queue"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."schedule_next_job_safely"("prev_job_id" "uuid", "doc_id" "uuid", "next_job_type" "text", "next_payload" "jsonb" DEFAULT '{}'::"jsonb", "required_data_keys" "text"[] DEFAULT ARRAY[]::"text"[]) RETURNS "uuid"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    next_job_id UUID;
BEGIN
    -- Validate previous job completion
    IF NOT validate_job_completion(prev_job_id, required_data_keys) THEN
        RAISE EXCEPTION 'Previous job % not properly completed, cannot schedule next job', prev_job_id;
    END IF;
    
    -- Create next job
    next_job_id := create_processing_job(
        doc_id, 
        next_job_type, 
        next_payload, 
        1, -- priority
        3, -- max_retries
        5  -- 5 second delay for processing
    );
    
    -- Log the transition
    INSERT INTO job_transitions (
        from_job_id, to_job_id, document_id, 
        transition_type, created_at
    ) VALUES (
        prev_job_id, next_job_id, doc_id,
        prev_job_id::text || '->' || next_job_type,
        NOW()
    );
    
    RETURN next_job_id;
END;
$$;


ALTER FUNCTION "public"."schedule_next_job_safely"("prev_job_id" "uuid", "doc_id" "uuid", "next_job_type" "text", "next_payload" "jsonb", "required_data_keys" "text"[]) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."search_by_policy_criteria"("criteria" "jsonb", "user_id_param" "uuid" DEFAULT NULL::"uuid", "limit_param" integer DEFAULT 10) RETURNS TABLE("document_id" "uuid", "policy_basics" "jsonb", "relevance_score" double precision)
    LANGUAGE "sql" STABLE
    AS $$
    SELECT 
        d.id as document_id,
        d.policy_basics,
        -- Simple relevance scoring based on matching criteria
        (CASE 
            WHEN d.policy_basics @> criteria THEN 1.0
            WHEN d.policy_basics ? ANY(SELECT jsonb_object_keys(criteria)) THEN 0.7
            ELSE 0.3
        END) as relevance_score
    FROM documents d
    WHERE d.user_id = COALESCE(user_id_param, d.user_id)
        AND d.policy_basics IS NOT NULL
        AND (d.policy_basics @> criteria 
             OR d.policy_basics ?| ARRAY(SELECT jsonb_object_keys(criteria)))
    ORDER BY relevance_score DESC, d.updated_at DESC
    LIMIT limit_param;
$$;


ALTER FUNCTION "public"."search_by_policy_criteria"("criteria" "jsonb", "user_id_param" "uuid", "limit_param" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."search_by_policy_criteria"("user_uuid" "uuid", "search_criteria" "jsonb", "limit_count" integer DEFAULT 10) RETURNS TABLE("id" "uuid", "original_filename" "text", "policy_basics" "jsonb", "relevance_score" double precision)
    LANGUAGE "plpgsql"
    AS $$ BEGIN RETURN QUERY SELECT ud.id, ud.original_filename, ud.policy_basics, 1.0::DOUBLE PRECISION as relevance_score FROM user_documents ud WHERE ud.user_id = user_uuid AND ud.policy_basics IS NOT NULL AND ud.policy_basics ?& (SELECT array_agg(key) FROM jsonb_object_keys(search_criteria) AS key) ORDER BY ud.updated_at DESC LIMIT limit_count; END; $$;


ALTER FUNCTION "public"."search_by_policy_criteria"("user_uuid" "uuid", "search_criteria" "jsonb", "limit_count" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."set_current_user_context"("user_uuid" "uuid") RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- Set fixed search path to prevent search path injection attacks
    SET search_path = public, pg_catalog;
    
    -- Validate input parameter
    IF user_uuid IS NULL THEN
        RAISE EXCEPTION 'User UUID cannot be null';
    END IF;
    
    -- Verify the user exists before setting context
    IF NOT EXISTS (SELECT 1 FROM users WHERE id = user_uuid) THEN
        RAISE EXCEPTION 'User does not exist';
    END IF;
    
    -- Set the user context for RLS policies
    PERFORM set_config('rls.current_user_id', user_uuid::text, false);
EXCEPTION
    WHEN OTHERS THEN
        -- Don't expose internal errors
        RAISE EXCEPTION 'Failed to set user context';
END;
$$;


ALTER FUNCTION "public"."set_current_user_context"("user_uuid" "uuid") OWNER TO "postgres";


COMMENT ON FUNCTION "public"."set_current_user_context"("user_uuid" "uuid") IS 'Securely set user context for RLS policies. Validates user existence. Uses SECURITY INVOKER and fixed search path.';



CREATE OR REPLACE FUNCTION "public"."start_processing_job"("job_id_param" "uuid") RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    UPDATE processing_jobs 
    SET 
        status = 'running',
        started_at = NOW(),
        updated_at = NOW()
    WHERE id = job_id_param AND status IN ('pending', 'retrying');
    
    RETURN FOUND;
END;
$$;


ALTER FUNCTION "public"."start_processing_job"("job_id_param" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."trigger_document_processing"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- Only create a job if the document is newly uploaded or status changed to uploaded
    IF (TG_OP = 'INSERT' AND NEW.status IN ('pending', 'uploaded')) OR 
       (TG_OP = 'UPDATE' AND OLD.status != NEW.status AND NEW.status IN ('pending', 'uploaded')) THEN
        
        -- Create a parse job for the document
        INSERT INTO processing_jobs (
            id,
            document_id,
            job_type,
            payload,
            status,
            priority,
            max_retries,
            retry_count,
            created_at,
            scheduled_at
        ) VALUES (
            gen_random_uuid(),
            NEW.id,
            'parse',
            jsonb_build_object(
                'filename', NEW.original_filename,
                'file_path', NEW.file_path,
                'user_id', NEW.user_id,
                'storage_provider', NEW.storage_provider,
                'bucket_name', NEW.bucket_name
            ),
            'pending',
            1, -- priority
            3, -- max_retries
            0, -- retry_count
            NOW(),
            NOW() + INTERVAL '5 seconds' -- process in 5 seconds
        );
        
        -- Log the job creation
        RAISE LOG 'Created processing job for document %: %', NEW.id, NEW.original_filename;
        
        -- Update document status to processing
        UPDATE user_documents 
        SET 
            processing_status = 'processing',
            updated_at = NOW()
        WHERE id = NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."trigger_document_processing"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_document_progress"("doc_id" "uuid", "new_status" "text" DEFAULT NULL::"text", "progress_pct" integer DEFAULT NULL::integer, "chunks_processed" integer DEFAULT NULL::integer, "chunks_failed" integer DEFAULT NULL::integer, "error_msg" "text" DEFAULT NULL::"text") RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    UPDATE documents 
    SET 
        status = COALESCE(new_status, status),
        progress_percentage = COALESCE(progress_pct, progress_percentage),
        processed_chunks = COALESCE(chunks_processed, processed_chunks),
        failed_chunks = COALESCE(chunks_failed, failed_chunks),
        error_message = COALESCE(error_msg, error_message),
        updated_at = NOW(),
        processing_completed_at = CASE 
            WHEN new_status = 'completed' THEN NOW()
            ELSE processing_completed_at
        END
    WHERE id = doc_id;
    
    RETURN FOUND;
END;
$$;


ALTER FUNCTION "public"."update_document_progress"("doc_id" "uuid", "new_status" "text", "progress_pct" integer, "chunks_processed" integer, "chunks_failed" integer, "error_msg" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_policy_basics"("document_uuid" "uuid", "policy_data" "jsonb") RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    UPDATE user_documents 
    SET 
        policy_basics = policy_data,
        updated_at = NOW()
    WHERE id = document_uuid;
    
    RETURN FOUND;
END;
$$;


ALTER FUNCTION "public"."update_policy_basics"("document_uuid" "uuid", "policy_data" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_policy_basics"("doc_id" integer, "policy_data" "jsonb", "user_id_param" "uuid" DEFAULT NULL::"uuid") RETURNS boolean
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    old_data JSONB;
BEGIN
    -- Get old data for audit
    SELECT policy_basics INTO old_data 
    FROM documents WHERE id = doc_id;
    
    -- Update policy basics
    UPDATE documents 
    SET policy_basics = policy_data,
        updated_at = NOW()
    WHERE id = doc_id;
    
    -- Log the change for HIPAA compliance
    INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values)
    VALUES (user_id_param, 'UPDATE_POLICY_BASICS', 'documents', doc_id::TEXT, 
            old_data, policy_data);
    
    RETURN FOUND;
END;
$$;


ALTER FUNCTION "public"."update_policy_basics"("doc_id" integer, "policy_data" "jsonb", "user_id_param" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_policy_basics"("doc_id" "uuid", "policy_data" "jsonb", "user_id_param" "uuid" DEFAULT NULL::"uuid") RETURNS boolean
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    old_data JSONB;
BEGIN
    -- Get old data for audit
    SELECT policy_basics INTO old_data 
    FROM documents WHERE id = doc_id;
    
    -- Update policy basics
    UPDATE documents 
    SET policy_basics = policy_data,
        updated_at = NOW()
    WHERE id = doc_id;
    
    -- Log the change for HIPAA compliance (only if audit_logs has the right columns)
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'table_name') THEN
        INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values)
        VALUES (user_id_param, 'UPDATE_POLICY_BASICS', 'documents', doc_id::TEXT, 
                old_data, policy_data);
    END IF;
    
    RETURN FOUND;
END;
$$;


ALTER FUNCTION "public"."update_policy_basics"("doc_id" "uuid", "policy_data" "jsonb", "user_id_param" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_updated_at_column"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_updated_at_column"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."validate_job_completion"("job_id_param" "uuid", "required_data_keys" "text"[] DEFAULT ARRAY[]::"text"[]) RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    job_record processing_jobs%ROWTYPE;
    result_data JSONB;
    key TEXT;
BEGIN
    -- Get job record
    SELECT * INTO job_record FROM processing_jobs WHERE id = job_id_param;
    
    IF NOT FOUND THEN
        RAISE WARNING 'Job % not found for validation', job_id_param;
        RETURN FALSE;
    END IF;
    
    -- Check if job is in completed status
    IF job_record.status != 'completed' THEN
        RAISE WARNING 'Job % not in completed status: %', job_id_param, job_record.status;
        RETURN FALSE;
    END IF;
    
    -- Check if result data contains required keys
    result_data := job_record.result;
    IF result_data IS NULL THEN
        RAISE WARNING 'Job % has no result data', job_id_param;
        RETURN FALSE;
    END IF;
    
    -- Validate required data keys exist
    FOREACH key IN ARRAY required_data_keys
    LOOP
        IF NOT (result_data ? key) THEN
            RAISE WARNING 'Job % missing required result key: %', job_id_param, key;
            RETURN FALSE;
        END IF;
    END LOOP;
    
    RETURN TRUE;
END;
$$;


ALTER FUNCTION "public"."validate_job_completion"("job_id_param" "uuid", "required_data_keys" "text"[]) OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."audit_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "action" character varying(100) NOT NULL,
    "resource_type" character varying(100) NOT NULL,
    "resource_id" character varying(255),
    "details" "jsonb",
    "ip_address" "inet",
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "table_name" character varying(100),
    "record_id" "text",
    "old_values" "jsonb",
    "new_values" "jsonb"
);


ALTER TABLE "public"."audit_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."conversations" (
    "id" "text" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "conversation_type" character varying(50) DEFAULT 'general'::character varying,
    "is_active" boolean DEFAULT true
);


ALTER TABLE "public"."conversations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."cron_job_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "job_name" "text" NOT NULL,
    "execution_time" timestamp with time zone DEFAULT "now"() NOT NULL,
    "http_status" integer,
    "response_content" "text",
    "success" boolean DEFAULT false NOT NULL,
    "error_message" "text"
);


ALTER TABLE "public"."cron_job_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."document_vectors" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "document_id" "uuid",
    "chunk_index" integer NOT NULL,
    "content_embedding" "public"."vector"(1536) NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "is_active" boolean DEFAULT true,
    "encrypted_chunk_text" "text",
    "encrypted_chunk_metadata" "text",
    "encryption_key_id" "uuid",
    "document_record_id" "uuid",
    "regulatory_document_id" "uuid",
    "document_source_type" "text" DEFAULT 'user_document'::"text" NOT NULL,
    CONSTRAINT "document_vectors_document_source_type_check" CHECK (("document_source_type" = ANY (ARRAY['user_document'::"text", 'regulatory_document'::"text"]))),
    CONSTRAINT "user_or_regulatory_document_check" CHECK (((("user_id" IS NOT NULL) AND ("document_id" IS NOT NULL) AND ("regulatory_document_id" IS NULL) AND ("document_source_type" = 'user_document'::"text")) OR (("user_id" IS NULL) AND ("document_id" IS NULL) AND ("regulatory_document_id" IS NOT NULL) AND ("document_source_type" = 'regulatory_document'::"text"))))
);


ALTER TABLE "public"."document_vectors" OWNER TO "postgres";


COMMENT ON TABLE "public"."document_vectors" IS 'Vector storage for user-uploaded documents with encryption support.';



COMMENT ON COLUMN "public"."document_vectors"."content_embedding" IS 'Vector embedding of the document chunk for semantic search';



COMMENT ON COLUMN "public"."document_vectors"."encryption_key_id" IS 'Reference to encryption key used for encrypting sensitive content and metadata.';



CREATE TABLE IF NOT EXISTS "public"."documents" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "original_filename" "text" NOT NULL,
    "file_size" bigint,
    "bucket_name" character varying(255) DEFAULT 'raw_documents'::character varying,
    "upload_status" character varying(50) DEFAULT 'pending'::character varying,
    "processing_status" character varying(50) DEFAULT 'pending'::character varying,
    "metadata" "jsonb",
    "status" character varying(50) DEFAULT 'pending'::character varying,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "document_type" character varying(50) DEFAULT 'policy'::character varying,
    "content_summary" "text",
    "is_active" boolean DEFAULT true,
    "content_type" character varying(255),
    "file_hash" character varying(255),
    "progress_percentage" integer DEFAULT 0,
    "total_chunks" integer,
    "processed_chunks" integer DEFAULT 0,
    "failed_chunks" integer DEFAULT 0,
    "storage_backend" character varying(50) DEFAULT 'supabase'::character varying,
    "storage_path" "text",
    "processing_progress" integer DEFAULT 0,
    "processing_stage" "text" DEFAULT 'pending'::"text",
    "jurisdiction" "text",
    "program" "text"[],
    "effective_date" "date",
    "expiration_date" "date",
    "source_url" "text",
    "tags" "text"[],
    CONSTRAINT "valid_document_type" CHECK ((("document_type")::"text" = ANY ((ARRAY['user_uploaded'::character varying, 'regulatory'::character varying, 'policy'::character varying, 'medical_record'::character varying, 'claim'::character varying])::"text"[])))
);


ALTER TABLE "public"."documents" OWNER TO "postgres";


COMMENT ON COLUMN "public"."documents"."processing_progress" IS 'Progress percentage (0-100) for async document processing';



COMMENT ON COLUMN "public"."documents"."processing_stage" IS 'Current processing stage for detailed status tracking';



CREATE TABLE IF NOT EXISTS "public"."encryption_keys" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "key_version" integer DEFAULT 1 NOT NULL,
    "key_status" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "rotated_at" timestamp with time zone,
    "retired_at" timestamp with time zone,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    CONSTRAINT "encryption_keys_key_status_check" CHECK (("key_status" = ANY (ARRAY['active'::"text", 'rotated'::"text", 'retired'::"text"])))
);


ALTER TABLE "public"."encryption_keys" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."messages" (
    "id" "text" DEFAULT ("gen_random_uuid"())::"text" NOT NULL,
    "conversation_id" "text" NOT NULL,
    "role" character varying(20) NOT NULL,
    "content" "text" NOT NULL,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "messages_role_check" CHECK ((("role")::"text" = ANY ((ARRAY['user'::character varying, 'assistant'::character varying, 'system'::character varying])::"text"[])))
);


ALTER TABLE "public"."messages" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."migration_progress" (
    "id" integer NOT NULL,
    "step_name" character varying(255) NOT NULL,
    "status" character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    "started_at" timestamp without time zone DEFAULT "now"(),
    "completed_at" timestamp without time zone,
    "details" "jsonb"
);


ALTER TABLE "public"."migration_progress" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."migration_progress_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE "public"."migration_progress_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."migration_progress_id_seq" OWNED BY "public"."migration_progress"."id";



CREATE TABLE IF NOT EXISTS "public"."roles" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."roles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_roles" (
    "user_id" "uuid" NOT NULL,
    "role_id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."user_roles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."users" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "email" "text" NOT NULL,
    "hashed_password" "text" NOT NULL,
    "full_name" "text",
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "last_login" timestamp with time zone,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "user_role" character varying(50) DEFAULT 'patient'::character varying,
    "access_level" integer DEFAULT 1
);


ALTER TABLE "public"."users" OWNER TO "postgres";


ALTER TABLE ONLY "public"."migration_progress" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."migration_progress_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."cron_job_logs"
    ADD CONSTRAINT "cron_job_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."encryption_keys"
    ADD CONSTRAINT "encryption_keys_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."migration_progress"
    ADD CONSTRAINT "migration_progress_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."migration_progress"
    ADD CONSTRAINT "migration_progress_step_name_key" UNIQUE ("step_name");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document_vectors"
    ADD CONSTRAINT "user_document_vectors_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."documents"
    ADD CONSTRAINT "user_documents_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_roles"
    ADD CONSTRAINT "user_roles_pkey" PRIMARY KEY ("user_id", "role_id");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");



CREATE INDEX "idx_audit_logs_created_at" ON "public"."audit_logs" USING "btree" ("created_at");



CREATE INDEX "idx_audit_logs_user_action" ON "public"."audit_logs" USING "btree" ("user_id", "action", "created_at");



CREATE INDEX "idx_audit_logs_user_id" ON "public"."audit_logs" USING "btree" ("user_id");



CREATE INDEX "idx_conversations_recent_active" ON "public"."conversations" USING "btree" ("created_at" DESC) WHERE ("is_active" = true);



CREATE INDEX "idx_conversations_user_active" ON "public"."conversations" USING "btree" ("user_id", "is_active", "updated_at" DESC);



CREATE INDEX "idx_conversations_user_id" ON "public"."conversations" USING "btree" ("user_id");



CREATE INDEX "idx_cron_job_logs_execution_time" ON "public"."cron_job_logs" USING "btree" ("execution_time");



CREATE INDEX "idx_cron_job_logs_job_name" ON "public"."cron_job_logs" USING "btree" ("job_name");



CREATE INDEX "idx_document_vectors_document_id" ON "public"."document_vectors" USING "btree" ("document_id");



CREATE INDEX "idx_document_vectors_regulatory_doc" ON "public"."document_vectors" USING "btree" ("regulatory_document_id") WHERE ("regulatory_document_id" IS NOT NULL);



CREATE INDEX "idx_document_vectors_regulatory_search" ON "public"."document_vectors" USING "btree" ("regulatory_document_id", "document_source_type", "is_active") WHERE ("document_source_type" = 'regulatory_document'::"text");



CREATE INDEX "idx_document_vectors_source_type" ON "public"."document_vectors" USING "btree" ("document_source_type");



CREATE INDEX "idx_document_vectors_user_id" ON "public"."document_vectors" USING "btree" ("user_id");



CREATE INDEX "idx_documents_active_recent" ON "public"."documents" USING "btree" ("updated_at" DESC) WHERE ("is_active" = true);



CREATE INDEX "idx_documents_bucket_name" ON "public"."documents" USING "btree" ("bucket_name");



CREATE INDEX "idx_documents_dates" ON "public"."documents" USING "btree" ("effective_date", "expiration_date") WHERE (("effective_date" IS NOT NULL) OR ("expiration_date" IS NOT NULL));



CREATE INDEX "idx_documents_file_hash" ON "public"."documents" USING "btree" ("file_hash");



CREATE INDEX "idx_documents_jurisdiction" ON "public"."documents" USING "btree" ("jurisdiction") WHERE ("jurisdiction" IS NOT NULL);



CREATE INDEX "idx_documents_progress" ON "public"."documents" USING "btree" ("progress_percentage", "status");



CREATE INDEX "idx_documents_storage_backend" ON "public"."documents" USING "btree" ("storage_backend");



CREATE INDEX "idx_documents_type" ON "public"."documents" USING "btree" ("document_type");



CREATE INDEX "idx_documents_user_type_active" ON "public"."documents" USING "btree" ("user_id", "document_type", "is_active");



CREATE INDEX "idx_messages_conversation_id" ON "public"."messages" USING "btree" ("conversation_id");



CREATE INDEX "idx_messages_created_at" ON "public"."messages" USING "btree" ("created_at");



CREATE INDEX "idx_messages_metadata_gin" ON "public"."messages" USING "gin" ("metadata");



CREATE INDEX "idx_roles_name" ON "public"."roles" USING "btree" ("name");



CREATE INDEX "idx_user_document_vectors_active" ON "public"."document_vectors" USING "btree" ("is_active") WHERE ("is_active" = true);



CREATE INDEX "idx_user_document_vectors_document_id" ON "public"."document_vectors" USING "btree" ("document_id");



CREATE INDEX "idx_user_document_vectors_document_record" ON "public"."document_vectors" USING "btree" ("document_record_id");



CREATE INDEX "idx_user_document_vectors_embedding" ON "public"."document_vectors" USING "ivfflat" ("content_embedding" "public"."vector_cosine_ops");



CREATE INDEX "idx_user_document_vectors_encryption_key" ON "public"."document_vectors" USING "btree" ("encryption_key_id");



CREATE INDEX "idx_user_document_vectors_user_id" ON "public"."document_vectors" USING "btree" ("user_id");



CREATE INDEX "idx_user_documents_metadata_gin" ON "public"."documents" USING "gin" ("metadata");



CREATE INDEX "idx_user_documents_status" ON "public"."documents" USING "btree" ("status");



CREATE INDEX "idx_user_documents_user_id" ON "public"."documents" USING "btree" ("user_id");



CREATE INDEX "idx_user_roles_role" ON "public"."user_roles" USING "btree" ("role_id");



CREATE INDEX "idx_user_roles_user" ON "public"."user_roles" USING "btree" ("user_id");



CREATE INDEX "idx_user_roles_user_id_role_name" ON "public"."user_roles" USING "btree" ("user_id") INCLUDE ("role_id");



CREATE INDEX "idx_users_email" ON "public"."users" USING "btree" ("email");



CREATE OR REPLACE TRIGGER "auto_job_creation_trigger" AFTER INSERT OR UPDATE ON "public"."documents" FOR EACH ROW EXECUTE FUNCTION "public"."auto_create_processing_job"();



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document_vectors"
    ADD CONSTRAINT "user_document_vectors_encryption_key_id_fkey" FOREIGN KEY ("encryption_key_id") REFERENCES "public"."encryption_keys"("id");



ALTER TABLE ONLY "public"."documents"
    ADD CONSTRAINT "user_documents_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_roles"
    ADD CONSTRAINT "user_roles_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");



ALTER TABLE ONLY "public"."user_roles"
    ADD CONSTRAINT "user_roles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");



ALTER TABLE "public"."audit_logs" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "audit_logs_admin_full" ON "public"."audit_logs" TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM "public"."users"
  WHERE (("users"."id" = "auth"."uid"()) AND (("users"."user_role")::"text" = 'admin'::"text")))));



CREATE POLICY "audit_logs_read_own" ON "public"."audit_logs" FOR SELECT TO "authenticated" USING (("user_id" = "auth"."uid"()));



ALTER TABLE "public"."conversations" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "conversations_user_access" ON "public"."conversations" TO "authenticated" USING ((("user_id" = "auth"."uid"()) OR (EXISTS ( SELECT 1
   FROM "public"."users"
  WHERE (("users"."id" = "auth"."uid"()) AND (("users"."user_role")::"text" = ANY ((ARRAY['admin'::character varying, 'provider'::character varying])::"text"[])))))));



ALTER TABLE "public"."document_vectors" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "document_vectors_user_access" ON "public"."document_vectors" TO "authenticated" USING ((("user_id" = "auth"."uid"()) OR (EXISTS ( SELECT 1
   FROM "public"."users"
  WHERE (("users"."id" = "auth"."uid"()) AND (("users"."user_role")::"text" = ANY ((ARRAY['admin'::character varying, 'provider'::character varying])::"text"[])))))));



ALTER TABLE "public"."encryption_keys" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "encryption_keys_admin_only" ON "public"."encryption_keys" USING ("public"."is_admin"());



ALTER TABLE "public"."roles" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "roles_admin_access" ON "public"."roles" USING ("public"."is_admin"());



CREATE POLICY "roles_read_access" ON "public"."roles" FOR SELECT USING (("auth"."uid"() IS NOT NULL));



CREATE POLICY "user_document_vectors_proper_access" ON "public"."document_vectors" USING ((("user_id" = "auth"."uid"()) OR (EXISTS ( SELECT 1
   FROM ("public"."user_roles" "ur"
     JOIN "public"."roles" "r" ON (("r"."id" = "ur"."role_id")))
  WHERE (("ur"."user_id" = "auth"."uid"()) AND ("r"."name" = 'admin'::"text"))))));



CREATE POLICY "user_is_self" ON "public"."users" USING (("auth"."uid"() = "id"));



ALTER TABLE "public"."user_roles" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "user_roles_admin_access" ON "public"."user_roles" USING ("public"."is_admin"());



CREATE POLICY "user_roles_self_access" ON "public"."user_roles" FOR SELECT USING (("user_id" = "public"."get_current_user_id"()));



ALTER TABLE "public"."users" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "users_admin_access" ON "public"."users" USING ("public"."is_admin"());



CREATE POLICY "users_delete_admin_only" ON "public"."users" FOR DELETE USING ((("auth"."jwt"() ->> 'role'::"text") = 'admin'::"text"));



CREATE POLICY "users_insert_registration" ON "public"."users" FOR INSERT WITH CHECK (true);



CREATE POLICY "users_self_select" ON "public"."users" FOR SELECT USING (("id" = "public"."get_current_user_id"()));



CREATE POLICY "users_self_update" ON "public"."users" FOR UPDATE USING (("id" = "public"."get_current_user_id"()));





ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";






ALTER PUBLICATION "supabase_realtime" ADD TABLE ONLY "public"."documents";






GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";






GRANT ALL ON FUNCTION "public"."halfvec_in"("cstring", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_in"("cstring", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_in"("cstring", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_in"("cstring", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_out"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_out"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_out"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_out"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_recv"("internal", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_recv"("internal", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_recv"("internal", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_recv"("internal", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_send"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_send"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_send"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_send"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_typmod_in"("cstring"[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_typmod_in"("cstring"[]) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_typmod_in"("cstring"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_typmod_in"("cstring"[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_in"("cstring", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_in"("cstring", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_in"("cstring", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_in"("cstring", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_out"("public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_out"("public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_out"("public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_out"("public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_recv"("internal", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_recv"("internal", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_recv"("internal", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_recv"("internal", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_send"("public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_send"("public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_send"("public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_send"("public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_typmod_in"("cstring"[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_typmod_in"("cstring"[]) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_typmod_in"("cstring"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_typmod_in"("cstring"[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_in"("cstring", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_out"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_recv"("internal", "oid", integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_send"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_typmod_in"("cstring"[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_halfvec"(real[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(real[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(real[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(real[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(real[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(real[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(real[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(real[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(real[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_halfvec"(double precision[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(double precision[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(double precision[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(double precision[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(double precision[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(double precision[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(double precision[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(double precision[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(double precision[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_halfvec"(integer[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(integer[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(integer[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(integer[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(integer[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(integer[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(integer[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(integer[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(integer[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_halfvec"(numeric[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(numeric[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(numeric[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_halfvec"(numeric[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(numeric[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(numeric[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(numeric[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_sparsevec"(numeric[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."array_to_vector"(numeric[], integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_to_float4"("public"."halfvec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_to_float4"("public"."halfvec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_to_float4"("public"."halfvec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_to_float4"("public"."halfvec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec"("public"."halfvec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec"("public"."halfvec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec"("public"."halfvec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec"("public"."halfvec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_to_sparsevec"("public"."halfvec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_to_sparsevec"("public"."halfvec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_to_sparsevec"("public"."halfvec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_to_sparsevec"("public"."halfvec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_to_vector"("public"."halfvec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_to_vector"("public"."halfvec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_to_vector"("public"."halfvec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_to_vector"("public"."halfvec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_to_halfvec"("public"."sparsevec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_to_halfvec"("public"."sparsevec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_to_halfvec"("public"."sparsevec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_to_halfvec"("public"."sparsevec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec"("public"."sparsevec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec"("public"."sparsevec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec"("public"."sparsevec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec"("public"."sparsevec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_to_vector"("public"."sparsevec", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_to_vector"("public"."sparsevec", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_to_vector"("public"."sparsevec", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_to_vector"("public"."sparsevec", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_to_float4"("public"."vector", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_to_halfvec"("public"."vector", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_to_halfvec"("public"."vector", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_to_halfvec"("public"."vector", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_to_halfvec"("public"."vector", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_to_sparsevec"("public"."vector", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_to_sparsevec"("public"."vector", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_to_sparsevec"("public"."vector", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_to_sparsevec"("public"."vector", integer, boolean) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "anon";
GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector"("public"."vector", integer, boolean) TO "service_role";
































































































































































































GRANT ALL ON FUNCTION "public"."auto_create_processing_job"() TO "anon";
GRANT ALL ON FUNCTION "public"."auto_create_processing_job"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."auto_create_processing_job"() TO "service_role";



GRANT ALL ON FUNCTION "public"."backfill_stuck_documents"() TO "anon";
GRANT ALL ON FUNCTION "public"."backfill_stuck_documents"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."backfill_stuck_documents"() TO "service_role";



GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."binary_quantize"("public"."vector") TO "service_role";



REVOKE ALL ON FUNCTION "public"."can_access_policy"("policy_uuid" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."can_access_policy"("policy_uuid" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."can_access_policy"("policy_uuid" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."can_access_policy"("policy_uuid" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."check_job_processing_health"() TO "anon";
GRANT ALL ON FUNCTION "public"."check_job_processing_health"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."check_job_processing_health"() TO "service_role";



GRANT ALL ON FUNCTION "public"."check_queue_health"() TO "anon";
GRANT ALL ON FUNCTION "public"."check_queue_health"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."check_queue_health"() TO "service_role";



GRANT ALL ON FUNCTION "public"."cleanup_old_jobs"() TO "anon";
GRANT ALL ON FUNCTION "public"."cleanup_old_jobs"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."cleanup_old_jobs"() TO "service_role";



GRANT ALL ON FUNCTION "public"."cleanup_realtime_progress_updates"() TO "anon";
GRANT ALL ON FUNCTION "public"."cleanup_realtime_progress_updates"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."cleanup_realtime_progress_updates"() TO "service_role";



GRANT ALL ON FUNCTION "public"."clear_user_context"() TO "anon";
GRANT ALL ON FUNCTION "public"."clear_user_context"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."clear_user_context"() TO "service_role";



GRANT ALL ON FUNCTION "public"."complete_processing_job"("job_id_param" "uuid", "job_result" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."complete_processing_job"("job_id_param" "uuid", "job_result" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."complete_processing_job"("job_id_param" "uuid", "job_result" "jsonb") TO "service_role";



GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."cosine_distance"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."create_processing_job"("doc_id" "uuid", "job_type_param" "text", "job_payload" "jsonb", "priority_param" integer, "max_retries_param" integer, "schedule_delay_seconds" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."create_processing_job"("doc_id" "uuid", "job_type_param" "text", "job_payload" "jsonb", "priority_param" integer, "max_retries_param" integer, "schedule_delay_seconds" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."create_processing_job"("doc_id" "uuid", "job_type_param" "text", "job_payload" "jsonb", "priority_param" integer, "max_retries_param" integer, "schedule_delay_seconds" integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."evaluate_feature_flag"("flag_name_param" "text", "user_id_param" "uuid", "user_email_param" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."evaluate_feature_flag"("flag_name_param" "text", "user_id_param" "uuid", "user_email_param" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."evaluate_feature_flag"("flag_name_param" "text", "user_id_param" "uuid", "user_email_param" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."fail_processing_job"("job_id_param" "uuid", "error_msg" "text", "error_details_param" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."fail_processing_job"("job_id_param" "uuid", "error_msg" "text", "error_details_param" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."fail_processing_job"("job_id_param" "uuid", "error_msg" "text", "error_details_param" "jsonb") TO "service_role";



REVOKE ALL ON FUNCTION "public"."get_current_user_id"() FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_current_user_id"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_current_user_id"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_current_user_id"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_pending_jobs"("limit_param" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."get_pending_jobs"("limit_param" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_pending_jobs"("limit_param" integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."get_policy_facts"("document_uuid" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."get_policy_facts"("document_uuid" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_policy_facts"("document_uuid" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_accum"(double precision[], "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_accum"(double precision[], "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_accum"(double precision[], "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_accum"(double precision[], "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_add"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_add"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_add"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_add"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_avg"(double precision[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_avg"(double precision[]) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_avg"(double precision[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_avg"(double precision[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_cmp"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_cmp"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_cmp"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_cmp"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_combine"(double precision[], double precision[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_combine"(double precision[], double precision[]) TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_combine"(double precision[], double precision[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_combine"(double precision[], double precision[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_concat"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_concat"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_concat"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_concat"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_eq"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_eq"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_eq"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_eq"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_ge"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_ge"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_ge"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_ge"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_gt"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_gt"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_gt"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_gt"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_l2_squared_distance"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_l2_squared_distance"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_l2_squared_distance"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_l2_squared_distance"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_le"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_le"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_le"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_le"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_lt"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_lt"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_lt"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_lt"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_mul"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_mul"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_mul"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_mul"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_ne"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_ne"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_ne"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_ne"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_negative_inner_product"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_negative_inner_product"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_negative_inner_product"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_negative_inner_product"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_spherical_distance"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_spherical_distance"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_spherical_distance"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_spherical_distance"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."halfvec_sub"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."halfvec_sub"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."halfvec_sub"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."halfvec_sub"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."hamming_distance"(bit, bit) TO "postgres";
GRANT ALL ON FUNCTION "public"."hamming_distance"(bit, bit) TO "anon";
GRANT ALL ON FUNCTION "public"."hamming_distance"(bit, bit) TO "authenticated";
GRANT ALL ON FUNCTION "public"."hamming_distance"(bit, bit) TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_job_completion"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_job_completion"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_job_completion"() TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_job_failure"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_job_failure"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_job_failure"() TO "service_role";



REVOKE ALL ON FUNCTION "public"."has_role"("role_name" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."has_role"("role_name" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."has_role"("role_name" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."has_role"("role_name" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."hnsw_bit_support"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."hnsw_bit_support"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."hnsw_bit_support"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."hnsw_bit_support"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."hnsw_halfvec_support"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."hnsw_halfvec_support"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."hnsw_halfvec_support"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."hnsw_halfvec_support"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."hnsw_sparsevec_support"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."hnsw_sparsevec_support"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."hnsw_sparsevec_support"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."hnsw_sparsevec_support"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."hnswhandler"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."inner_product"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."inner_product"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."inner_product"("public"."vector", "public"."vector") TO "service_role";



REVOKE ALL ON FUNCTION "public"."is_admin"() FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."is_admin"() TO "anon";
GRANT ALL ON FUNCTION "public"."is_admin"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."is_admin"() TO "service_role";



GRANT ALL ON FUNCTION "public"."ivfflat_bit_support"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."ivfflat_bit_support"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."ivfflat_bit_support"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."ivfflat_bit_support"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."ivfflat_halfvec_support"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."ivfflat_halfvec_support"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."ivfflat_halfvec_support"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."ivfflat_halfvec_support"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."ivfflathandler"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."jaccard_distance"(bit, bit) TO "postgres";
GRANT ALL ON FUNCTION "public"."jaccard_distance"(bit, bit) TO "anon";
GRANT ALL ON FUNCTION "public"."jaccard_distance"(bit, bit) TO "authenticated";
GRANT ALL ON FUNCTION "public"."jaccard_distance"(bit, bit) TO "service_role";



GRANT ALL ON FUNCTION "public"."l1_distance"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l1_distance"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l1_distance"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_distance"("public"."halfvec", "public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."halfvec", "public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."halfvec", "public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."halfvec", "public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_distance"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_distance"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_norm"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_norm"("public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_norm"("public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."l2_normalize"("public"."vector") TO "service_role";



REVOKE ALL ON FUNCTION "public"."log_policy_access"("policy_uuid" "uuid", "access_type" "text", "success" boolean, "details" "jsonb") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."log_policy_access"("policy_uuid" "uuid", "access_type" "text", "success" boolean, "details" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."log_policy_access"("policy_uuid" "uuid", "access_type" "text", "success" boolean, "details" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."log_policy_access"("policy_uuid" "uuid", "access_type" "text", "success" boolean, "details" "jsonb") TO "service_role";



GRANT ALL ON FUNCTION "public"."log_user_action"("user_uuid" "uuid", "action_type" "text", "resource_type" "text", "resource_id" "text", "action_details" "jsonb", "client_ip" "inet", "client_user_agent" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."log_user_action"("user_uuid" "uuid", "action_type" "text", "resource_type" "text", "resource_id" "text", "action_details" "jsonb", "client_ip" "inet", "client_user_agent" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."log_user_action"("user_uuid" "uuid", "action_type" "text", "resource_type" "text", "resource_id" "text", "action_details" "jsonb", "client_ip" "inet", "client_user_agent" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."monitor_processing_queue"() TO "anon";
GRANT ALL ON FUNCTION "public"."monitor_processing_queue"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."monitor_processing_queue"() TO "service_role";



GRANT ALL ON FUNCTION "public"."schedule_next_job_safely"("prev_job_id" "uuid", "doc_id" "uuid", "next_job_type" "text", "next_payload" "jsonb", "required_data_keys" "text"[]) TO "anon";
GRANT ALL ON FUNCTION "public"."schedule_next_job_safely"("prev_job_id" "uuid", "doc_id" "uuid", "next_job_type" "text", "next_payload" "jsonb", "required_data_keys" "text"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."schedule_next_job_safely"("prev_job_id" "uuid", "doc_id" "uuid", "next_job_type" "text", "next_payload" "jsonb", "required_data_keys" "text"[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."search_by_policy_criteria"("criteria" "jsonb", "user_id_param" "uuid", "limit_param" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."search_by_policy_criteria"("criteria" "jsonb", "user_id_param" "uuid", "limit_param" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."search_by_policy_criteria"("criteria" "jsonb", "user_id_param" "uuid", "limit_param" integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."search_by_policy_criteria"("user_uuid" "uuid", "search_criteria" "jsonb", "limit_count" integer) TO "anon";
GRANT ALL ON FUNCTION "public"."search_by_policy_criteria"("user_uuid" "uuid", "search_criteria" "jsonb", "limit_count" integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."search_by_policy_criteria"("user_uuid" "uuid", "search_criteria" "jsonb", "limit_count" integer) TO "service_role";



REVOKE ALL ON FUNCTION "public"."set_current_user_context"("user_uuid" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."set_current_user_context"("user_uuid" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."set_current_user_context"("user_uuid" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."set_current_user_context"("user_uuid" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_cmp"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_cmp"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_cmp"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_cmp"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_eq"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_eq"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_eq"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_eq"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_ge"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_ge"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_ge"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_ge"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_gt"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_gt"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_gt"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_gt"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_l2_squared_distance"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_l2_squared_distance"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_l2_squared_distance"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_l2_squared_distance"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_le"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_le"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_le"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_le"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_lt"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_lt"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_lt"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_lt"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_ne"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_ne"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_ne"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_ne"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sparsevec_negative_inner_product"("public"."sparsevec", "public"."sparsevec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sparsevec_negative_inner_product"("public"."sparsevec", "public"."sparsevec") TO "anon";
GRANT ALL ON FUNCTION "public"."sparsevec_negative_inner_product"("public"."sparsevec", "public"."sparsevec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sparsevec_negative_inner_product"("public"."sparsevec", "public"."sparsevec") TO "service_role";



GRANT ALL ON FUNCTION "public"."start_processing_job"("job_id_param" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."start_processing_job"("job_id_param" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."start_processing_job"("job_id_param" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."subvector"("public"."halfvec", integer, integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."subvector"("public"."halfvec", integer, integer) TO "anon";
GRANT ALL ON FUNCTION "public"."subvector"("public"."halfvec", integer, integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."subvector"("public"."halfvec", integer, integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."subvector"("public"."vector", integer, integer) TO "postgres";
GRANT ALL ON FUNCTION "public"."subvector"("public"."vector", integer, integer) TO "anon";
GRANT ALL ON FUNCTION "public"."subvector"("public"."vector", integer, integer) TO "authenticated";
GRANT ALL ON FUNCTION "public"."subvector"("public"."vector", integer, integer) TO "service_role";



GRANT ALL ON FUNCTION "public"."trigger_document_processing"() TO "anon";
GRANT ALL ON FUNCTION "public"."trigger_document_processing"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."trigger_document_processing"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_document_progress"("doc_id" "uuid", "new_status" "text", "progress_pct" integer, "chunks_processed" integer, "chunks_failed" integer, "error_msg" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."update_document_progress"("doc_id" "uuid", "new_status" "text", "progress_pct" integer, "chunks_processed" integer, "chunks_failed" integer, "error_msg" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_document_progress"("doc_id" "uuid", "new_status" "text", "progress_pct" integer, "chunks_processed" integer, "chunks_failed" integer, "error_msg" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."update_policy_basics"("document_uuid" "uuid", "policy_data" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."update_policy_basics"("document_uuid" "uuid", "policy_data" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_policy_basics"("document_uuid" "uuid", "policy_data" "jsonb") TO "service_role";



GRANT ALL ON FUNCTION "public"."update_policy_basics"("doc_id" integer, "policy_data" "jsonb", "user_id_param" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."update_policy_basics"("doc_id" integer, "policy_data" "jsonb", "user_id_param" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_policy_basics"("doc_id" integer, "policy_data" "jsonb", "user_id_param" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."update_policy_basics"("doc_id" "uuid", "policy_data" "jsonb", "user_id_param" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."update_policy_basics"("doc_id" "uuid", "policy_data" "jsonb", "user_id_param" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_policy_basics"("doc_id" "uuid", "policy_data" "jsonb", "user_id_param" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "service_role";



GRANT ALL ON FUNCTION "public"."validate_job_completion"("job_id_param" "uuid", "required_data_keys" "text"[]) TO "anon";
GRANT ALL ON FUNCTION "public"."validate_job_completion"("job_id_param" "uuid", "required_data_keys" "text"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."validate_job_completion"("job_id_param" "uuid", "required_data_keys" "text"[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_accum"(double precision[], "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_add"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_avg"(double precision[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_cmp"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "anon";
GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_combine"(double precision[], double precision[]) TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_concat"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_concat"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_concat"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_concat"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_dims"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_dims"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_eq"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_ge"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_gt"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_l2_squared_distance"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_le"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_lt"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_mul"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_ne"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_negative_inner_product"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_norm"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_spherical_distance"("public"."vector", "public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."vector_sub"("public"."vector", "public"."vector") TO "service_role";












GRANT ALL ON FUNCTION "public"."avg"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."avg"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."avg"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."avg"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."avg"("public"."vector") TO "service_role";



GRANT ALL ON FUNCTION "public"."sum"("public"."halfvec") TO "postgres";
GRANT ALL ON FUNCTION "public"."sum"("public"."halfvec") TO "anon";
GRANT ALL ON FUNCTION "public"."sum"("public"."halfvec") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sum"("public"."halfvec") TO "service_role";



GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "postgres";
GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "anon";
GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "authenticated";
GRANT ALL ON FUNCTION "public"."sum"("public"."vector") TO "service_role";















GRANT ALL ON TABLE "public"."audit_logs" TO "anon";
GRANT ALL ON TABLE "public"."audit_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."audit_logs" TO "service_role";



GRANT ALL ON TABLE "public"."conversations" TO "anon";
GRANT ALL ON TABLE "public"."conversations" TO "authenticated";
GRANT ALL ON TABLE "public"."conversations" TO "service_role";



GRANT ALL ON TABLE "public"."cron_job_logs" TO "anon";
GRANT ALL ON TABLE "public"."cron_job_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."cron_job_logs" TO "service_role";



GRANT ALL ON TABLE "public"."document_vectors" TO "anon";
GRANT ALL ON TABLE "public"."document_vectors" TO "authenticated";
GRANT ALL ON TABLE "public"."document_vectors" TO "service_role";



GRANT ALL ON TABLE "public"."documents" TO "anon";
GRANT ALL ON TABLE "public"."documents" TO "authenticated";
GRANT ALL ON TABLE "public"."documents" TO "service_role";



GRANT ALL ON TABLE "public"."encryption_keys" TO "anon";
GRANT ALL ON TABLE "public"."encryption_keys" TO "authenticated";
GRANT ALL ON TABLE "public"."encryption_keys" TO "service_role";



GRANT ALL ON TABLE "public"."messages" TO "anon";
GRANT ALL ON TABLE "public"."messages" TO "authenticated";
GRANT ALL ON TABLE "public"."messages" TO "service_role";



GRANT ALL ON TABLE "public"."migration_progress" TO "anon";
GRANT ALL ON TABLE "public"."migration_progress" TO "authenticated";
GRANT ALL ON TABLE "public"."migration_progress" TO "service_role";



GRANT ALL ON SEQUENCE "public"."migration_progress_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."migration_progress_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."migration_progress_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."roles" TO "anon";
GRANT ALL ON TABLE "public"."roles" TO "authenticated";
GRANT ALL ON TABLE "public"."roles" TO "service_role";



GRANT ALL ON TABLE "public"."user_roles" TO "anon";
GRANT ALL ON TABLE "public"."user_roles" TO "authenticated";
GRANT ALL ON TABLE "public"."user_roles" TO "service_role";



GRANT ALL ON TABLE "public"."users" TO "anon";
GRANT ALL ON TABLE "public"."users" TO "authenticated";
GRANT ALL ON TABLE "public"."users" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "service_role";






























RESET ALL;
