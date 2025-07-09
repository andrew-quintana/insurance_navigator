# supabase/hooks/post-start.sh
#!/bin/bash

# Wait for Supabase to be fully up
sleep 5

# Apply bucket configuration
PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres << 'EOF'
UPDATE storage.buckets 
SET 
    allowed_mime_types = ARRAY[
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'text/csv',
        'text/markdown',
        'application/json',
        'application/xml',
        'text/xml',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'application/x-www-form-urlencoded',
        'multipart/form-data'
    ],
    file_size_limit = 52428800,
    public = false,
    updated_at = now()
WHERE id = 'files';

DO $$
BEGIN
    RAISE NOTICE 'Post-start hook: Bucket configuration updated: %', (
        SELECT row_to_json(b.*)
        FROM storage.buckets b
        WHERE id = 'files'
    );
END $$;
EOF