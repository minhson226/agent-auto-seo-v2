-- Migration: Create Keyword Tables
-- Version: 006
-- Description: Tables for keyword lists and keywords

SET search_path TO autoseo, public;

-- Keyword Lists table
CREATE TABLE IF NOT EXISTS keyword_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source VARCHAR(50), -- 'csv_upload', 'txt_upload', 'api', 'manual'
    source_file_url VARCHAR(500), -- S3/MinIO URL
    total_keywords INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'processing', -- 'processing', 'completed', 'failed'
    error_message TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Keywords table
CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id UUID NOT NULL REFERENCES keyword_lists(id) ON DELETE CASCADE,
    text VARCHAR(500) NOT NULL,
    normalized_text VARCHAR(500) NOT NULL, -- lowercase, trimmed
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processed', 'assigned'
    intent VARCHAR(50) DEFAULT 'unknown', -- 'unknown', 'informational', 'commercial', 'navigational', 'transactional'
    search_volume INTEGER,
    keyword_difficulty DECIMAL(5,2),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(list_id, normalized_text)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_keywords_list_id ON keywords(list_id);
CREATE INDEX IF NOT EXISTS idx_keywords_status ON keywords(status);
CREATE INDEX IF NOT EXISTS idx_keywords_normalized_text ON keywords(normalized_text);
CREATE INDEX IF NOT EXISTS idx_keyword_lists_workspace_id ON keyword_lists(workspace_id);
CREATE INDEX IF NOT EXISTS idx_keyword_lists_status ON keyword_lists(status);
CREATE INDEX IF NOT EXISTS idx_keyword_lists_created_by ON keyword_lists(created_by);

-- Triggers
DROP TRIGGER IF EXISTS trigger_keyword_lists_updated_at ON keyword_lists;
CREATE TRIGGER trigger_keyword_lists_updated_at
    BEFORE UPDATE ON keyword_lists
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_keywords_updated_at ON keywords;
CREATE TRIGGER trigger_keywords_updated_at
    BEFORE UPDATE ON keywords
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE keyword_lists IS 'Lists of keywords uploaded or imported by users';
COMMENT ON TABLE keywords IS 'Individual keywords belonging to a keyword list';
COMMENT ON COLUMN keyword_lists.source IS 'Source of the keyword list: csv_upload, txt_upload, api, manual';
COMMENT ON COLUMN keyword_lists.status IS 'Processing status: processing, completed, failed';
COMMENT ON COLUMN keywords.intent IS 'Search intent: unknown, informational, commercial, navigational, transactional';
COMMENT ON COLUMN keywords.normalized_text IS 'Normalized keyword: lowercase, trimmed, extra spaces removed';
