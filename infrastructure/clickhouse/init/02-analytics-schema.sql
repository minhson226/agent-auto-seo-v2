-- ClickHouse Analytics Database - Performance Facts
-- Auto-SEO Analytics Schema - PHASE-013

-- Use the analytics database
USE autoseo_analytics;

-- Performance facts table for manual analytics data entry
-- Stores impressions, clicks, and position data from GA/GSC
CREATE TABLE IF NOT EXISTS fact_performance (
    date Date,
    url_hash String,
    url String,
    workspace_id String,
    article_id String,
    impressions UInt32,
    clicks UInt32,
    position Float32,
    ai_model_used String DEFAULT '',
    prompt_id String DEFAULT '',
    cost_usd Float32 DEFAULT 0.0,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (workspace_id, url_hash, date)
TTL date + INTERVAL 730 DAY;

-- Comments
COMMENT ON TABLE fact_performance IS 'Performance facts table for analytics data (impressions, clicks, position)';
