-- Migration: Create API Keys Table
-- Version: 004
-- Description: API keys storage for external service integrations

SET search_path TO autoseo, public;

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(workspace_id, service_name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_workspace_id ON api_keys(workspace_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_service_name ON api_keys(service_name);

-- Triggers
DROP TRIGGER IF EXISTS trigger_api_keys_updated_at ON api_keys;
CREATE TRIGGER trigger_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE api_keys IS 'Encrypted API keys for external service integrations (OpenAI, Google, etc.)';
COMMENT ON COLUMN api_keys.api_key_encrypted IS 'AES-256 encrypted API key value';
COMMENT ON COLUMN api_keys.service_name IS 'Name of the external service (e.g., openai, google, ahrefs)';
