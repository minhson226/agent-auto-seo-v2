-- Migration: SEO Strategy Tables
-- Version: 008
-- Description: Tables for topic clusters, cluster keywords, and content plans

SET search_path TO autoseo, public;

-- Topic Clusters table (for grouping keywords into topics)
CREATE TABLE IF NOT EXISTS topic_clusters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) DEFAULT 'cluster', -- 'pillar' | 'cluster'
    description TEXT,
    pillar_cluster_id UUID REFERENCES topic_clusters(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cluster Keywords table (links keywords to clusters)
CREATE TABLE IF NOT EXISTS cluster_keywords (
    cluster_id UUID NOT NULL REFERENCES topic_clusters(id) ON DELETE CASCADE,
    keyword_id UUID NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (cluster_id, keyword_id)
);

-- Content Plans table (for planning content with priorities)
CREATE TABLE IF NOT EXISTS content_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cluster_id UUID REFERENCES topic_clusters(id) ON DELETE SET NULL,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium', -- 'high' | 'medium' | 'low'
    target_keywords TEXT[],
    competitors_data JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft' | 'approved' | 'in_progress' | 'completed'
    estimated_word_count INTEGER,
    notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for topic_clusters
CREATE INDEX IF NOT EXISTS idx_topic_clusters_workspace_id ON topic_clusters(workspace_id);
CREATE INDEX IF NOT EXISTS idx_topic_clusters_type ON topic_clusters(type);
CREATE INDEX IF NOT EXISTS idx_topic_clusters_pillar_id ON topic_clusters(pillar_cluster_id);

-- Indexes for cluster_keywords
CREATE INDEX IF NOT EXISTS idx_cluster_keywords_cluster_id ON cluster_keywords(cluster_id);
CREATE INDEX IF NOT EXISTS idx_cluster_keywords_keyword_id ON cluster_keywords(keyword_id);

-- Indexes for content_plans
CREATE INDEX IF NOT EXISTS idx_content_plans_cluster_id ON content_plans(cluster_id);
CREATE INDEX IF NOT EXISTS idx_content_plans_workspace_id ON content_plans(workspace_id);
CREATE INDEX IF NOT EXISTS idx_content_plans_status ON content_plans(status);
CREATE INDEX IF NOT EXISTS idx_content_plans_priority ON content_plans(priority);
CREATE INDEX IF NOT EXISTS idx_content_plans_created_by ON content_plans(created_by);

-- Triggers for updated_at
DROP TRIGGER IF EXISTS trigger_topic_clusters_updated_at ON topic_clusters;
CREATE TRIGGER trigger_topic_clusters_updated_at
    BEFORE UPDATE ON topic_clusters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_content_plans_updated_at ON content_plans;
CREATE TRIGGER trigger_content_plans_updated_at
    BEFORE UPDATE ON content_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE topic_clusters IS 'Topic clusters for grouping related keywords';
COMMENT ON TABLE cluster_keywords IS 'Association table linking keywords to clusters';
COMMENT ON TABLE content_plans IS 'Content plans with priorities and target keywords';

COMMENT ON COLUMN topic_clusters.type IS 'Type of cluster: pillar (main topic) or cluster (supporting)';
COMMENT ON COLUMN topic_clusters.pillar_cluster_id IS 'Reference to parent pillar cluster (null if this is a pillar)';
COMMENT ON COLUMN cluster_keywords.is_primary IS 'Whether this keyword is the primary keyword for the cluster';
COMMENT ON COLUMN content_plans.priority IS 'Content priority: high, medium, or low';
COMMENT ON COLUMN content_plans.status IS 'Content plan status: draft, approved, in_progress, completed';
COMMENT ON COLUMN content_plans.competitors_data IS 'JSON data about competitor URLs and analysis';
