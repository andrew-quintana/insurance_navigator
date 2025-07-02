-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    session_expires TIMESTAMP WITH TIME ZONE,
    -- Future HIPAA fields (commented for documentation):
    -- consent_version TEXT,
    -- data_access_log JSONB
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Create documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'error')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    storage_path TEXT NOT NULL,
    error_message TEXT,
    -- Future HIPAA fields (commented for documentation):
    -- encryption_key_id UUID,
    -- access_log JSONB
    CONSTRAINT valid_content_type CHECK (content_type IN ('application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))
);

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for documents table
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies for users table
CREATE POLICY "Users can read own record" ON users
    FOR SELECT
    TO authenticated
    USING (auth.uid() = id);

CREATE POLICY "Users can update own record" ON users
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = id);

CREATE POLICY "Allow signup" ON users
    FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "Service role has full access to users" ON users
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Create RLS Policies for documents table
CREATE POLICY "Users can read own documents" ON documents
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own documents" ON documents
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Service role has full access to documents" ON documents
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Create storage bucket for documents
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'documents',
    'documents',
    false,
    10485760, -- 10MB in bytes
    ARRAY['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
);

-- Create storage RLS policies
CREATE POLICY "Users can upload to own directory" ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'documents' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Users can read own files" ON storage.objects
    FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'documents' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Service role has full access to storage" ON storage.objects
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Comments for future HIPAA compliance and scaling considerations
COMMENT ON TABLE users IS 'User accounts with future HIPAA compliance fields planned';
COMMENT ON TABLE documents IS 'Document storage with future encryption and audit logging planned';
COMMENT ON COLUMN users.id IS 'Primary identifier for user accounts';
COMMENT ON COLUMN documents.storage_path IS 'Path to document in storage bucket, follows pattern: documents/{user_id}/{filename}'; 