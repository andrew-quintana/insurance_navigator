-- Fix Specific Stuck Document from Production Logs
-- Document ID: 35fbb7ad-0714-4f60-ba81-0fff28f9ee71
-- This script should be run in Supabase SQL Editor

-- First, check the current status of the stuck document
SELECT 
    id, 
    original_filename, 
    user_id, 
    status, 
    progress_percentage, 
    created_at,
    error_message
FROM documents 
WHERE id = '35fbb7ad-0714-4f60-ba81-0fff28f9ee71';

-- Check if this document already has vectors
SELECT COUNT(*) as existing_vectors
FROM document_vectors 
WHERE document_record_id = '35fbb7ad-0714-4f60-ba81-0fff28f9ee71';

-- Create placeholder vector for the stuck document (only if no vectors exist)
-- This allows the document to be marked as completed and searchable
INSERT INTO document_vectors (
    user_id, 
    document_record_id, 
    chunk_index,
    content_embedding, 
    encrypted_chunk_text, 
    encrypted_chunk_metadata,
    document_source_type, 
    is_active, 
    created_at, 
    encryption_key_id
) 
SELECT 
    d.user_id,
    d.id,
    0,
    ('[' || string_agg('0', ',') || ']')::vector(1536), -- Create zero vector
    'Document: ' || d.original_filename || E'\n\nThis document was uploaded successfully but processed without semantic embeddings due to API limitations. The document is searchable by filename and basic text matching.',
    json_build_object(
        'filename', d.original_filename,
        'file_size', d.file_size,
        'content_type', d.content_type,
        'chunk_length', 200,
        'total_chunks', 1,
        'processed_at', NOW(),
        'extraction_method', 'emergency_fix',
        'embedding_method', 'zero_vector_fallback',
        'note', 'Fixed stuck document with placeholder vector - OpenAI API was unavailable'
    ),
    'user_document',
    true,
    NOW(),
    (SELECT id FROM encryption_keys WHERE key_status = 'active' ORDER BY created_at DESC LIMIT 1)
FROM documents d
CROSS JOIN generate_series(1, 1536) 
WHERE d.id = '35fbb7ad-0714-4f60-ba81-0fff28f9ee71'
AND NOT EXISTS (
    SELECT 1 FROM document_vectors 
    WHERE document_record_id = '35fbb7ad-0714-4f60-ba81-0fff28f9ee71'
)
GROUP BY d.user_id, d.id, d.original_filename, d.file_size, d.content_type;

-- Update the document status to completed
UPDATE documents 
SET 
    status = 'completed',
    progress_percentage = 100,
    updated_at = NOW(),
    error_message = COALESCE(error_message, '') || ' - Emergency fix applied: Document processed with placeholder vectors'
WHERE id = '35fbb7ad-0714-4f60-ba81-0fff28f9ee71';

-- Verify the fix worked
SELECT 
    'Document Status' as check_type,
    status,
    progress_percentage,
    error_message
FROM documents 
WHERE id = '35fbb7ad-0714-4f60-ba81-0fff28f9ee71'

UNION ALL

SELECT 
    'Vector Count' as check_type,
    COUNT(*)::text as status,
    NULL as progress_percentage,
    'vectors created' as error_message
FROM document_vectors 
WHERE document_record_id = '35fbb7ad-0714-4f60-ba81-0fff28f9ee71';

-- Show all documents that might be stuck (for comprehensive fix)
SELECT 
    id,
    original_filename,
    status,
    progress_percentage,
    created_at,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM document_vectors dv 
            WHERE dv.document_record_id = d.id
        ) THEN 'Has Vectors'
        ELSE 'Needs Vectors'
    END as vector_status
FROM documents d
WHERE status IN ('vectorizing', 'processing', 'parsing', 'failed')
AND created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC; 