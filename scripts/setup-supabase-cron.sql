-- Setup Supabase Cron Job for Document Processing
-- This replaces the local cron job with a native Supabase cron job

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Create cron job to process document jobs every minute
SELECT cron.schedule(
  'process-document-jobs',           -- Job name
  '* * * * *',                      -- Every minute
  $$
  SELECT net.http_post(
    url := 'https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/job-processor',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.supabase_service_role_key', true)
    ),
    body := jsonb_build_object(
      'source', 'cron',
      'timestamp', now()
    ),
    timeout_milliseconds := 30000
  ) as request_id;
  $$
);

-- Create cron job for cleanup (runs daily at 2 AM)
SELECT cron.schedule(
  'cleanup-old-jobs',
  '0 2 * * *',                      -- Daily at 2 AM
  $$
  SELECT cleanup_old_jobs() as cleaned_count;
  $$
);

-- Create cron job for health monitoring (every 5 minutes)
SELECT cron.schedule(
  'monitor-stuck-jobs',
  '*/5 * * * *',                    -- Every 5 minutes
  $$
  SELECT net.http_post(
    url := 'https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/job-processor',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.supabase_service_role_key', true)
    ),
    body := jsonb_build_object(
      'source', 'health_check',
      'action', 'monitor_stuck_jobs'
    ),
    timeout_milliseconds := 10000
  ) as request_id;
  $$
);

-- View current cron jobs
SELECT * FROM cron.job WHERE jobname LIKE '%document%' OR jobname LIKE '%job%'; 