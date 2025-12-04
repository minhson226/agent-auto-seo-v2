-- Migration: Keyword Automation
-- Version: 007
-- Description: Add columns and tables for keyword automation (PHASE-004)

SET search_path TO autoseo, public;

-- Add new columns to keywords table for enrichment data
ALTER TABLE keywords
ADD COLUMN IF NOT EXISTS cpc DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS clicks INTEGER,
ADD COLUMN IF NOT EXISTS intent_confidence DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS trend_score INTEGER,
ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMP WITH TIME ZONE;

-- Create table for scheduled jobs
CREATE TABLE IF NOT EXISTS keyword_sync_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  job_type VARCHAR(50) NOT NULL, -- 'trends', 'competitor', 'enrichment'
  schedule JSONB, -- cron schedule config
  config JSONB DEFAULT '{}'::jsonb, -- job-specific config (e.g., competitor domain)
  last_run_at TIMESTAMP WITH TIME ZONE,
  next_run_at TIMESTAMP WITH TIME ZONE,
  status VARCHAR(50) DEFAULT 'active', -- 'active', 'paused', 'deleted'
  error_message TEXT,
  run_count INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create table for job execution history
CREATE TABLE IF NOT EXISTS keyword_job_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID REFERENCES keyword_sync_jobs(id) ON DELETE SET NULL,
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  job_type VARCHAR(50) NOT NULL,
  status VARCHAR(50) DEFAULT 'running', -- 'running', 'completed', 'failed'
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  keywords_processed INTEGER DEFAULT 0,
  keywords_enriched INTEGER DEFAULT 0,
  error_message TEXT,
  result_data JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_keyword_sync_jobs_workspace_id ON keyword_sync_jobs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_keyword_sync_jobs_status ON keyword_sync_jobs(status);
CREATE INDEX IF NOT EXISTS idx_keyword_sync_jobs_next_run_at ON keyword_sync_jobs(next_run_at);
CREATE INDEX IF NOT EXISTS idx_keyword_job_runs_workspace_id ON keyword_job_runs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_keyword_job_runs_job_id ON keyword_job_runs(job_id);
CREATE INDEX IF NOT EXISTS idx_keyword_job_runs_status ON keyword_job_runs(status);
CREATE INDEX IF NOT EXISTS idx_keywords_last_enriched_at ON keywords(last_enriched_at);

-- Triggers
DROP TRIGGER IF EXISTS trigger_keyword_sync_jobs_updated_at ON keyword_sync_jobs;
CREATE TRIGGER trigger_keyword_sync_jobs_updated_at
    BEFORE UPDATE ON keyword_sync_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE keyword_sync_jobs IS 'Scheduled jobs for automated keyword operations';
COMMENT ON TABLE keyword_job_runs IS 'Execution history for keyword automation jobs';
COMMENT ON COLUMN keyword_sync_jobs.job_type IS 'Type of job: trends, competitor, enrichment';
COMMENT ON COLUMN keyword_sync_jobs.schedule IS 'Cron schedule configuration in JSON format';
COMMENT ON COLUMN keywords.cpc IS 'Cost per click from SEO tools';
COMMENT ON COLUMN keywords.clicks IS 'Estimated monthly clicks';
COMMENT ON COLUMN keywords.intent_confidence IS 'Confidence score for intent classification (0-100)';
COMMENT ON COLUMN keywords.trend_score IS 'Google Trends score (0-100)';
COMMENT ON COLUMN keywords.last_enriched_at IS 'Timestamp of last enrichment';
