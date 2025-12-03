-- ClickHouse Analytics Database Initialization
-- Auto-SEO Analytics Schema

-- Create analytics database
CREATE DATABASE IF NOT EXISTS autoseo_analytics;

-- Use the analytics database
USE autoseo_analytics;

-- Page views tracking
CREATE TABLE IF NOT EXISTS page_views (
    event_time DateTime DEFAULT now(),
    event_date Date DEFAULT toDate(event_time),
    site_id UUID,
    page_url String,
    page_title String,
    user_agent String,
    referrer String,
    country_code String,
    device_type String,
    session_id String,
    user_id Nullable(UUID)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (site_id, event_date, event_time)
TTL event_date + INTERVAL 365 DAY;

-- Keyword rankings tracking
CREATE TABLE IF NOT EXISTS keyword_rankings (
    recorded_at DateTime DEFAULT now(),
    recorded_date Date DEFAULT toDate(recorded_at),
    site_id UUID,
    keyword String,
    position UInt32,
    search_volume UInt32,
    competition Float32,
    url String,
    search_engine String DEFAULT 'google'
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(recorded_date)
ORDER BY (site_id, keyword, recorded_date)
TTL recorded_date + INTERVAL 730 DAY;

-- Content performance metrics
CREATE TABLE IF NOT EXISTS content_performance (
    recorded_at DateTime DEFAULT now(),
    recorded_date Date DEFAULT toDate(recorded_at),
    site_id UUID,
    article_id UUID,
    page_views UInt64,
    unique_visitors UInt64,
    avg_time_on_page Float32,
    bounce_rate Float32,
    scroll_depth Float32,
    conversions UInt32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(recorded_date)
ORDER BY (site_id, article_id, recorded_date)
TTL recorded_date + INTERVAL 365 DAY;

-- SEO audit results
CREATE TABLE IF NOT EXISTS seo_audits (
    audit_time DateTime DEFAULT now(),
    audit_date Date DEFAULT toDate(audit_time),
    site_id UUID,
    article_id UUID,
    overall_score Float32,
    readability_score Float32,
    keyword_density Float32,
    meta_score Float32,
    structure_score Float32,
    issues Array(String),
    recommendations Array(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(audit_date)
ORDER BY (site_id, article_id, audit_date);
