-- Initial Schema Migration
-- Version: 001
-- Description: Core tables for policy management and access control

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core Tables
CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_version INTEGER NOT NULL DEFAULT 1,
    key_status TEXT NOT NULL CHECK (key_status IN ('active', 'rotated', 'retired')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_at TIMESTAMPTZ,
    retired_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id),
    role_id UUID NOT NULL REFERENCES roles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE policy_records (
    policy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- File Storage
    raw_policy_path TEXT NOT NULL,
    -- Structured Data
    summary JSONB NOT NULL,
    structured_metadata JSONB NOT NULL,
    -- Encryption
    encrypted_policy_data JSONB NOT NULL,
    encryption_key_id UUID REFERENCES encryption_keys(id),
    -- Metadata
    source_type TEXT NOT NULL CHECK (source_type IN ('uploaded', 'fetched', 'admin_override')),
    coverage_start_date DATE NOT NULL,
    coverage_end_date DATE NOT NULL,
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE user_policy_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    policy_id UUID NOT NULL REFERENCES policy_records(policy_id),
    role TEXT NOT NULL CHECK (role IN (
        'subscriber', 'dependent', 'spouse', 'employee',
        'guardian', 'representative', 'self'
    )),
    relationship_verified BOOLEAN DEFAULT false,
    linked_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE policy_access_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID REFERENCES roles(id),
    policy_type TEXT NOT NULL,
    action TEXT NOT NULL,
    conditions JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE policy_access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policy_records(policy_id),
    user_id UUID NOT NULL,
    action TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('user', 'agent')),
    actor_id UUID NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    purpose TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE agent_policy_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id TEXT NOT NULL,
    session_id UUID NOT NULL,
    policy_id UUID REFERENCES policy_records(policy_id),
    user_id UUID NOT NULL,
    context_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    encrypted_context JSONB NOT NULL,
    encryption_key_id UUID REFERENCES encryption_keys(id),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_policy_access_logs_policy ON policy_access_logs(policy_id);
CREATE INDEX idx_policy_access_logs_user ON policy_access_logs(user_id);
CREATE INDEX idx_user_policy_links_user ON user_policy_links(user_id);
CREATE INDEX idx_user_policy_links_policy ON user_policy_links(policy_id);
CREATE INDEX idx_agent_policy_context_session ON agent_policy_context(session_id);
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);

-- RLS Policies
ALTER TABLE policy_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_policy_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_access_logs ENABLE ROW LEVEL SECURITY;

-- Policy Records RLS (temporarily disabled)
-- CREATE POLICY policy_records_access ON policy_records
--     USING (
--         EXISTS (
--             SELECT 1 FROM user_policy_links
--             WHERE user_policy_links.policy_id = policy_records.policy_id
--             AND user_policy_links.user_id = current_user::uuid
--             AND user_policy_links.relationship_verified = true
--         )
--     );

-- User Policy Links RLS (temporarily disabled)
-- CREATE POLICY user_policy_links_access ON user_policy_links
--     USING (user_id = current_user::uuid);

-- Policy Access Logs RLS (temporarily disabled)
-- CREATE POLICY policy_access_logs_access ON policy_access_logs
--     USING (
--         user_id = current_user::uuid OR
--         EXISTS (
--             SELECT 1 FROM roles
--             WHERE roles.id IN (
--                 SELECT role_id FROM user_roles
--                 WHERE user_id = current_user::uuid
--             )
--             AND roles.name = 'admin'
--         )
--     ); 