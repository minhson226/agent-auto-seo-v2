-- Migration: SEO Scores Table for SEO Scoring Engine
-- Version: 010
-- Description: Tables for storing SEO scoring data for articles (PHASE-009)

SET search_path TO autoseo, public;

-- SEO Scores table
CREATE TABLE IF NOT EXISTS seo_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    manual_score INTEGER,
    auto_score INTEGER,
    checklist JSONB DEFAULT '{
        "title_contains_keyword": false,
        "h1_present": false,
        "h2_count_adequate": false,
        "keyword_density_ok": false,
        "images_have_alt": false,
        "meta_description": false,
        "internal_links": false,
        "external_links": false,
        "word_count_adequate": false,
        "readability_ok": false
    }'::jsonb,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for seo_scores
CREATE INDEX IF NOT EXISTS idx_seo_scores_article_id ON seo_scores(article_id);
CREATE INDEX IF NOT EXISTS idx_seo_scores_workspace_id ON seo_scores(workspace_id);
CREATE INDEX IF NOT EXISTS idx_seo_scores_status ON seo_scores(status);
CREATE INDEX IF NOT EXISTS idx_seo_scores_created_at ON seo_scores(created_at);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS trigger_seo_scores_updated_at ON seo_scores;
CREATE TRIGGER trigger_seo_scores_updated_at
    BEFORE UPDATE ON seo_scores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE seo_scores IS 'SEO scoring data for articles';
COMMENT ON COLUMN seo_scores.article_id IS 'Reference to the article being scored';
COMMENT ON COLUMN seo_scores.workspace_id IS 'Workspace that owns this score';
COMMENT ON COLUMN seo_scores.manual_score IS 'Manually calculated score (0-100)';
COMMENT ON COLUMN seo_scores.auto_score IS 'Automatically calculated score (0-100) - reserved for PHASE-010';
COMMENT ON COLUMN seo_scores.checklist IS 'SEO checklist items with their status (true/false)';
COMMENT ON COLUMN seo_scores.status IS 'Score status: pending, completed, reviewed';
