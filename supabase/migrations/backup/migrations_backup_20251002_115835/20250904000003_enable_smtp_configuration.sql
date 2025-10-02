-- Enable SMTP configuration for email delivery
-- This migration documents the SMTP configuration needed in Supabase dashboard

-- Note: This migration is for documentation purposes only
-- The actual SMTP configuration must be done in the Supabase dashboard
-- under Authentication > SMTP Settings

-- Required SMTP Configuration:
-- SMTP Host: smtp.resend.com (or your chosen provider)
-- SMTP Port: 465
-- SMTP User: resend (or your provider's username)
-- SMTP Password: [Your SMTP API Key]
-- SMTP Admin Email: admin@yourdomain.com
-- SMTP Sender Name: Insurance Navigator

-- This configuration will allow all email addresses to be used for registration
-- instead of being restricted to organization domain emails only

-- No database changes needed - this is handled by Supabase's auth service

