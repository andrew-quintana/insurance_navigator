# Database Upgrade Paths and Future Considerations

## Schema Evolution

### HIPAA Compliance Fields

#### Users Table
1. Add consent tracking:
```sql
ALTER TABLE users
ADD COLUMN consent_version TEXT,
ADD COLUMN consent_timestamp TIMESTAMP WITH TIME ZONE,
ADD COLUMN consent_document_id UUID REFERENCES documents(id);
```

2. Add audit logging:
```sql
ALTER TABLE users
ADD COLUMN data_access_log JSONB DEFAULT '[]'::jsonb,
ADD COLUMN last_hipaa_review TIMESTAMP WITH TIME ZONE;
```

#### Documents Table
1. Add encryption support:
```sql
ALTER TABLE documents
ADD COLUMN encryption_key_id UUID,
ADD COLUMN encryption_algorithm TEXT,
ADD COLUMN encryption_metadata JSONB;
```

2. Add audit logging:
```sql
ALTER TABLE documents
ADD COLUMN access_log JSONB DEFAULT '[]'::jsonb,
ADD COLUMN last_access_review TIMESTAMP WITH TIME ZONE;
```

### Data Encryption Implementation

1. Create encryption keys table:
```sql
CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_version INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rotation_date TIMESTAMP WITH TIME ZONE,
    status TEXT CHECK (status IN ('active', 'rotating', 'retired')),
    metadata JSONB
);
```

2. Implement encryption at rest:
- Use AWS KMS or similar service for key management
- Implement transparent data encryption
- Set up key rotation policies

### Audit Trail Integration

1. Create audit logs table:
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID REFERENCES users(id),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID NOT NULL,
    metadata JSONB,
    ip_address INET,
    user_agent TEXT
);
```

2. Create audit trigger function:
```sql
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        user_id,
        action,
        resource_type,
        resource_id,
        metadata
    ) VALUES (
        auth.uid(),
        TG_OP,
        TG_TABLE_NAME,
        NEW.id,
        jsonb_build_object(
            'old_data', to_jsonb(OLD),
            'new_data', to_jsonb(NEW)
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

## Security Enhancements

### Enhanced RLS Policies

1. Add IP-based restrictions:
```sql
CREATE POLICY "IP restriction" ON users
    USING (
        request.jwt()->>'ip_address' = ANY(ARRAY['allowed_ip_1', 'allowed_ip_2'])
    );
```

2. Add time-based restrictions:
```sql
CREATE POLICY "Business hours only" ON documents
    USING (
        EXTRACT(HOUR FROM NOW()) BETWEEN 9 AND 17
        AND EXTRACT(DOW FROM NOW()) BETWEEN 1 AND 5
    );
```

### Encryption at Rest

1. Column-level encryption:
```sql
-- Add pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Example function for encrypting sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT, key TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, key);
END;
$$ LANGUAGE plpgsql;
```

2. Storage encryption:
- Enable server-side encryption for storage buckets
- Implement client-side encryption for sensitive files
- Set up key rotation policies

## Performance Optimization

### Table Partitioning

1. Partition documents table by date:
```sql
CREATE TABLE documents_partitioned (
    LIKE documents INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE documents_2024_q1 PARTITION OF documents_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
```

### Indexing Strategy

1. Create composite indexes:
```sql
CREATE INDEX idx_documents_user_status ON documents(user_id, status);
CREATE INDEX idx_documents_content_type ON documents(content_type, status);
```

2. Create partial indexes:
```sql
CREATE INDEX idx_documents_processing ON documents(created_at)
    WHERE status = 'processing';
```

## Monitoring and Maintenance

### Health Checks

1. Create monitoring views:
```sql
CREATE VIEW vw_table_stats AS
SELECT
    schemaname,
    relname,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables;
```

### Performance Tracking

1. Create performance logging:
```sql
CREATE TABLE performance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    query_id TEXT,
    execution_time INTERVAL,
    rows_affected INTEGER,
    query_plan JSONB
);
```

## Testing Procedures

### Schema Validation

```sql
-- Test user creation with email validation
INSERT INTO users (email, name)
VALUES ('test@example.com', 'Test User');

-- Test document creation with content type validation
INSERT INTO documents (
    user_id,
    filename,
    content_type,
    status,
    storage_path
) VALUES (
    'user_uuid',
    'test.pdf',
    'application/pdf',
    'processing',
    'documents/user_uuid/test.pdf'
);
```

### RLS Policy Testing

```sql
-- Test as authenticated user
SET LOCAL ROLE authenticated;
SET LOCAL auth.uid TO 'user_uuid';
SELECT * FROM documents;

-- Test as service role
SET LOCAL ROLE service_role;
SELECT * FROM documents;
```

## Backup and Recovery

### Backup Strategy

1. Regular backups:
```sql
-- Create backup function
CREATE OR REPLACE FUNCTION create_backup()
RETURNS void AS $$
BEGIN
    -- Implementation details
END;
$$ LANGUAGE plpgsql;
```

2. Point-in-time recovery setup:
- Enable WAL archiving
- Configure retention policies
- Set up automated backup verification

## Migration Notes

1. Always test migrations in staging environment first
2. Use transaction blocks for all migrations
3. Implement rollback procedures for each migration
4. Document all schema changes in version control
5. Monitor performance impact of changes
6. Update application code to handle schema changes gracefully 