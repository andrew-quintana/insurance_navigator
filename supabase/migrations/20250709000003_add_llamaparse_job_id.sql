-- Add 'embedded' to the existing enum
ALTER TYPE "documents"."document_processing_status" ADD VALUE 'embedded'; 

-- Add llama_parse_job_id column to documents table
ALTER TABLE "documents"."documents"
ADD COLUMN llama_parse_job_id text;

-- Add index for faster lookups by job_id
CREATE INDEX idx_documents_llama_parse_job_id ON "documents"."documents"(llama_parse_job_id);

-- Add comment for documentation
COMMENT ON COLUMN "documents"."documents".llama_parse_job_id IS 'LlamaParse job ID for tracking and debugging purposes';

-- Ensure RLS policies are updated
ALTER TABLE "documents"."documents" ENABLE ROW LEVEL SECURITY;

-- Update RLS policies to include the new column
CREATE POLICY "Service role can update job IDs"
    ON "documents"."documents" FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true); 