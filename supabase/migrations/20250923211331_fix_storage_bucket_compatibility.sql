-- Fix storage.buckets compatibility issue
-- This migration handles the case where the 'public' column may not exist

DO $$
BEGIN
    -- Check if the public column exists
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'storage' 
        AND table_name = 'buckets' 
        AND column_name = 'public'
    ) THEN
        -- If public column exists, use the original insert
        INSERT INTO storage.buckets (
            id,
            name,
            public,
            file_size_limit,
            allowed_mime_types
        )
        VALUES (
            'files',
            'files',
            false,
            52428800,
            ARRAY[
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
            ]
        ) ON CONFLICT (id) DO NOTHING;
    ELSE
        -- If public column doesn't exist, use the compatible insert
        INSERT INTO storage.buckets (
            id,
            name,
            file_size_limit,
            allowed_mime_types
        )
        VALUES (
            'files',
            'files',
            52428800,
            ARRAY[
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
            ]
        ) ON CONFLICT (id) DO NOTHING;
    END IF;
END $$;
