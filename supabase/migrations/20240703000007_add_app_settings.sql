-- =============================================================================
-- ADD APPLICATION SETTINGS
-- Description: Add configuration settings for document processing
-- Version: 20240703_7
-- =============================================================================

BEGIN;

-- Safety check - ensure we're not in read-only mode
DO $$
BEGIN
    IF current_setting('transaction_read_only') = 'on' THEN
        RAISE EXCEPTION 'Database is in read-only mode';
    END IF;
END $$;

-- =============================================================================
-- STEP 1: CREATE APP SETTINGS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS app_settings (
    key text PRIMARY KEY,
    value text NOT NULL,
    description text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Add trigger for updated_at
CREATE TRIGGER update_app_settings_updated_at
    BEFORE UPDATE ON app_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- STEP 2: ADD INITIAL SETTINGS
-- =============================================================================

INSERT INTO app_settings (key, value, description)
VALUES 
    ('edge_function_url', 'http://127.0.0.1:54321/functions/v1/upload-handler', 'URL for the upload handler Edge Function'),
    ('service_role_key', '***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.p2fuVDatv5iaDizrYVeg2Gx_U1utFdpwLHwkiZfsRxs', 'Service role key for Edge Function authentication')
ON CONFLICT (key) DO UPDATE
SET value = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at = now();

-- =============================================================================
-- STEP 3: CREATE FUNCTION TO GET SETTINGS
-- =============================================================================

CREATE OR REPLACE FUNCTION get_app_setting(setting_key text)
RETURNS text AS $$
BEGIN
    RETURN (SELECT value FROM app_settings WHERE key = setting_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- STEP 4: SET UP CUSTOM SETTINGS PROVIDER
-- =============================================================================

-- Create function to handle custom settings
CREATE OR REPLACE FUNCTION app_settings_provider(
    config_key text,
    config_value text DEFAULT NULL
)
RETURNS text AS $$
BEGIN
    -- If value is provided, this is a SET operation
    IF config_value IS NOT NULL THEN
        INSERT INTO app_settings (key, value)
        VALUES (config_key, config_value)
        ON CONFLICT (key) DO UPDATE
        SET value = EXCLUDED.value,
            updated_at = now();
        RETURN config_value;
    END IF;
    
    -- Otherwise, this is a GET operation
    RETURN (SELECT value FROM app_settings WHERE key = config_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Register the custom settings provider
DO $$
BEGIN
    -- Set up custom settings provider
    PERFORM set_config('custom_settings.provider', 'app_settings_provider', false);
    
    -- Create aliases for app settings
    PERFORM set_config('app.settings.edge_function_url', 
        (SELECT value FROM app_settings WHERE key = 'edge_function_url'),
        false);
    PERFORM set_config('app.settings.service_role_key',
        (SELECT value FROM app_settings WHERE key = 'service_role_key'),
        false);
END $$;

-- =============================================================================
-- STEP 5: GRANT PERMISSIONS
-- =============================================================================

-- Only allow service role to access settings
ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to app settings"
ON app_settings
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

GRANT SELECT ON app_settings TO service_role;
GRANT EXECUTE ON FUNCTION get_app_setting TO service_role;
GRANT EXECUTE ON FUNCTION app_settings_provider TO service_role;

COMMIT; 