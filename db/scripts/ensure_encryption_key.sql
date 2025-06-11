-- Ensure encryption key exists for vector processing
-- This is required for the vector-processor Edge Function to work

-- Check if any active encryption key exists
DO $$
BEGIN
  -- If no active encryption key exists, create one
  IF NOT EXISTS (
    SELECT 1 FROM encryption_keys WHERE key_status = 'active'
  ) THEN
    INSERT INTO encryption_keys (key_version, key_status, metadata)
    VALUES (
      1, 'active',
      jsonb_build_object(
        'created_by', 'system', 
        'purpose', 'vector_processing', 
        'rotation_interval', '30d',
        'created_at', NOW()
      )
    );
    
    RAISE NOTICE 'Created active encryption key for vector processing';
  ELSE
    RAISE NOTICE 'Active encryption key already exists';
  END IF;
END
$$;

-- Verify the key exists
SELECT 
  id,
  key_version,
  key_status,
  created_at,
  metadata->>'purpose' as purpose
FROM encryption_keys 
WHERE key_status = 'active'
ORDER BY created_at DESC 
LIMIT 1; 