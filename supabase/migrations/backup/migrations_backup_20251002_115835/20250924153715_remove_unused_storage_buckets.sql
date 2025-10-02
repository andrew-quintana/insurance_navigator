-- Remove unused storage buckets (raw, parsed) that are no longer needed
-- This migration ensures these buckets are removed during database reset/push

-- Remove raw bucket if it exists
DELETE FROM storage.buckets WHERE id = 'raw';

-- Remove parsed bucket if it exists  
DELETE FROM storage.buckets WHERE id = 'parsed';

-- Note: The 'files' bucket should remain as it's the active bucket for all document storage
-- This migration is idempotent - it can be run multiple times safely
