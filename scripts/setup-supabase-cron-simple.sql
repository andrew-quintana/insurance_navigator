-- Setup Supabase Cron Job for Document Processing
-- This replaces the local cron job with a native Supabase cron job

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Create cron job to process document jobs every minute
-- Note: Replace YOUR_SERVICE_ROLE_KEY with actual key when running
SELECT cron.schedule(
  'process-document-jobs',
  '* * * * *',
  $$
  SELECT net.http_post(
    url := 'https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/job-processor',
    headers := '{"Content-Type": "application/json", "Authorization": "Bearer YOUR_SERVICE_ROLE_KEY"}',
    body := '{"source": "cron"}',
    timeout_milliseconds := 30000
  ) as request_id;
  $$
);

-- Create cron job for cleanup (runs daily at 2 AM)
SELECT cron.schedule(
  'cleanup-old-jobs',
  '0 2 * * *',
  'SELECT cleanup_old_jobs() as cleaned_count;'
);

-- View current cron jobs
SELECT jobid, jobname, schedule, command, active FROM cron.job; 