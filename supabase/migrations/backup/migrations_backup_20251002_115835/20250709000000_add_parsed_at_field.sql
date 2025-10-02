-- Add parsed_at timestamp field to documents table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'documents'
        AND table_name = 'documents' 
        AND column_name = 'parsed_at'
    ) THEN
        ALTER TABLE "documents"."documents"
        ADD COLUMN parsed_at TIMESTAMP WITH TIME ZONE;
        
        -- Add comment for field documentation
        COMMENT ON COLUMN "documents"."documents".parsed_at IS 'Timestamp when document was successfully parsed by the system';
    END IF;
END $$; 