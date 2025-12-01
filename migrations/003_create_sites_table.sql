-- Migration: Create Sites Table
-- Version: 003
-- Description: Sites/blogs managed within workspaces

SET search_path TO autoseo, public;

CREATE TABLE IF NOT EXISTS sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    platform VARCHAR(50) DEFAULT 'wordpress',
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}'::jsonb,
    api_credentials JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(workspace_id, domain)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sites_workspace_id ON sites(workspace_id);
CREATE INDEX IF NOT EXISTS idx_sites_domain ON sites(domain);
CREATE INDEX IF NOT EXISTS idx_sites_is_active ON sites(is_active) WHERE is_active = true;

-- Triggers
DROP TRIGGER IF EXISTS trigger_sites_updated_at ON sites;
CREATE TRIGGER trigger_sites_updated_at
    BEFORE UPDATE ON sites
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE sites IS 'Websites/blogs managed for SEO content';
COMMENT ON COLUMN sites.platform IS 'CMS platform: wordpress, ghost, custom, etc.';
COMMENT ON COLUMN sites.api_credentials IS 'Encrypted API credentials for CMS integration';
