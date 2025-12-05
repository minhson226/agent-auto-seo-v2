-- Migration: Article Performance Sync Table
-- Version: 013
-- Description: Table for linking PostgreSQL articles with ClickHouse performance data

SET search_path TO autoseo, public;

-- Article performance sync table
-- Links articles to ClickHouse analytics and caches summary metrics
CREATE TABLE IF NOT EXISTS article_performance_sync (
    article_id UUID PRIMARY KEY REFERENCES articles(id) ON DELETE CASCADE,
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    avg_position_30d DECIMAL(5,2) DEFAULT 0.0,
    total_clicks_30d INTEGER DEFAULT 0,
    total_impressions_30d INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for article_performance_sync
CREATE INDEX IF NOT EXISTS idx_article_performance_sync_last_synced ON article_performance_sync(last_synced_at);
CREATE INDEX IF NOT EXISTS idx_article_performance_sync_avg_position ON article_performance_sync(avg_position_30d);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS trigger_article_performance_sync_updated_at ON article_performance_sync;
CREATE TRIGGER trigger_article_performance_sync_updated_at
    BEFORE UPDATE ON article_performance_sync
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE article_performance_sync IS 'Links articles to ClickHouse analytics with cached 30-day metrics';
COMMENT ON COLUMN article_performance_sync.article_id IS 'Reference to the article';
COMMENT ON COLUMN article_performance_sync.last_synced_at IS 'Last time metrics were synced from ClickHouse';
COMMENT ON COLUMN article_performance_sync.avg_position_30d IS 'Average search position over last 30 days';
COMMENT ON COLUMN article_performance_sync.total_clicks_30d IS 'Total clicks over last 30 days';
COMMENT ON COLUMN article_performance_sync.total_impressions_30d IS 'Total impressions over last 30 days';
