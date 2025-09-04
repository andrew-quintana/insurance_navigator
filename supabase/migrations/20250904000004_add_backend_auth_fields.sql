-- Add fields to support backend-only authentication
-- This migration adds fields to track email confirmation status and auth method

-- Add email_confirmed field to users table
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS auth_method VARCHAR(50) DEFAULT 'email';

-- Update existing users to have email_confirmed = true
-- (since we're implementing backend-only auth)
UPDATE public.users 
SET email_confirmed = TRUE, 
    auth_method = 'backend_only',
    created_at = COALESCE(created_at, NOW())
WHERE email_confirmed IS NULL;

-- Create index on email_confirmed for faster queries
CREATE INDEX IF NOT EXISTS idx_users_email_confirmed ON public.users (email_confirmed);

-- Create index on auth_method for analytics
CREATE INDEX IF NOT EXISTS idx_users_auth_method ON public.users (auth_method);

-- Add comment explaining the backend-only auth approach
COMMENT ON COLUMN public.users.email_confirmed IS 'Email confirmation status - set to TRUE for backend-only auth';
COMMENT ON COLUMN public.users.auth_method IS 'Authentication method used - backend_only for development, email for production';
COMMENT ON COLUMN public.users.created_at IS 'User creation timestamp';
