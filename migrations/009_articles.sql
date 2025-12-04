-- Migration: Articles Table for Content Generation
-- Version: 009
-- Description: Tables for storing generated articles

SET search_path TO autoseo, public;

-- Articles table
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID REFERENCES content_plans(id) ON DELETE SET NULL,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT, -- HTML or Markdown
    status VARCHAR(50) DEFAULT 'draft', -- 'draft' | 'published' | 'archived'
    ai_model_used VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
    cost_usd DECIMAL(10,4),
    word_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Article images table (for tracking uploaded images)
CREATE TABLE IF NOT EXISTS article_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500),
    content_type VARCHAR(100),
    size_bytes BIGINT,
    storage_path VARCHAR(1000) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for articles
CREATE INDEX IF NOT EXISTS idx_articles_workspace_id ON articles(workspace_id);
CREATE INDEX IF NOT EXISTS idx_articles_plan_id ON articles(plan_id);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);

-- Indexes for article_images
CREATE INDEX IF NOT EXISTS idx_article_images_article_id ON article_images(article_id);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS trigger_articles_updated_at ON articles;
CREATE TRIGGER trigger_articles_updated_at
    BEFORE UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE articles IS 'Generated articles with SEO content';
COMMENT ON TABLE article_images IS 'Images associated with articles';

COMMENT ON COLUMN articles.plan_id IS 'Reference to the content plan used to generate this article';
COMMENT ON COLUMN articles.content IS 'Article content in HTML or Markdown format';
COMMENT ON COLUMN articles.status IS 'Article status: draft, published, or archived';
COMMENT ON COLUMN articles.ai_model_used IS 'The AI model used to generate the content';
COMMENT ON COLUMN articles.cost_usd IS 'Cost of generating this article in USD';
COMMENT ON COLUMN articles.word_count IS 'Number of words in the generated content';
COMMENT ON COLUMN articles.metadata IS 'Additional metadata about the generation process';
