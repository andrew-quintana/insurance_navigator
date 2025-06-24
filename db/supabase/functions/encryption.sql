-- =============================================================================
-- ENCRYPTION RPC FUNCTIONS
-- Description: Create RPC functions for encryption operations
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- Create encryption functions schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS encryption_functions;

-- Function to encrypt data
CREATE OR REPLACE FUNCTION encryption_functions.encrypt_data(
    data text,
    key_id uuid
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    key_record record;
    encrypted_data bytea;
    key_data text;
BEGIN
    -- Get the encryption key
    SELECT * INTO key_record
    FROM encryption_keys
    WHERE id = key_id AND key_status IN ('active', 'rotated');
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invalid or inactive encryption key';
    END IF;
    
    -- Get key data from metadata
    key_data := key_record.metadata->>'key_data';
    IF key_data IS NULL THEN
        RAISE EXCEPTION 'Key data not found in metadata';
    END IF;
    
    -- Encrypt the data using pgcrypto
    encrypted_data = pgp_sym_encrypt(
        data,
        decode(key_data, 'base64')::text,
        'compress-algo=2, cipher-algo=aes256'
    );
    
    RETURN jsonb_build_object(
        'encrypted_data', encode(encrypted_data, 'base64'),
        'key_id', key_id,
        'key_version', key_record.key_version
    );
END;
$$;

-- Function to decrypt data
CREATE OR REPLACE FUNCTION encryption_functions.decrypt_data(
    encrypted_data text,
    key_id uuid
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    key_record record;
    decrypted_data text;
    key_data text;
BEGIN
    -- Get the encryption key
    SELECT * INTO key_record
    FROM encryption_keys
    WHERE id = key_id AND key_status IN ('active', 'rotated');
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invalid or inactive encryption key';
    END IF;
    
    -- Get key data from metadata
    key_data := key_record.metadata->>'key_data';
    IF key_data IS NULL THEN
        RAISE EXCEPTION 'Key data not found in metadata';
    END IF;
    
    -- Decrypt the data using pgcrypto
    decrypted_data = pgp_sym_decrypt(
        decode(encrypted_data, 'base64')::bytea,
        decode(key_data, 'base64')::text
    );
    
    RETURN jsonb_build_object(
        'decrypted_data', decrypted_data,
        'key_id', key_id,
        'key_version', key_record.key_version
    );
END;
$$;

-- Function to generate a new encryption key
CREATE OR REPLACE FUNCTION encryption_functions.generate_encryption_key()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    new_key_id uuid;
    new_key_version int;
    new_key_data text;
BEGIN
    -- Generate a new key
    new_key_id := gen_random_uuid();
    new_key_data := encode(gen_random_bytes(32), 'base64');
    
    -- Get the next key version
    SELECT COALESCE(MAX(key_version), 0) + 1
    INTO new_key_version
    FROM encryption_keys;
    
    -- Insert the new key
    INSERT INTO encryption_keys (
        id,
        key_version,
        key_status,
        metadata
    ) VALUES (
        new_key_id,
        new_key_version,
        'active',
        jsonb_build_object(
            'key_data', new_key_data,
            'algorithm', 'aes-256-gcm',
            'created_by', 'system',
            'created_at', now()
        )
    );
    
    RETURN jsonb_build_object(
        'key_id', new_key_id,
        'version', new_key_version
    );
END;
$$;

-- Grant execute permissions to authenticated users
GRANT USAGE ON SCHEMA encryption_functions TO authenticated;
GRANT EXECUTE ON FUNCTION encryption_functions.encrypt_data TO authenticated;
GRANT EXECUTE ON FUNCTION encryption_functions.decrypt_data TO authenticated;
GRANT EXECUTE ON FUNCTION encryption_functions.generate_encryption_key TO authenticated;

COMMIT; 