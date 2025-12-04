-- Migration: Internal Link Map Table for Publishing Automation
-- Version: 012
-- Description: Tables for internal linking automation and article embeddings

SET search_path TO autoseo, public;

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Internal link map table
CREATE TABLE IF NOT EXISTS internal_link_map (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_post_id UUID REFERENCES published_posts(id) ON DELETE CASCADE,
    to_post_id UUID REFERENCES published_posts(id) ON DELETE CASCADE,
    anchor_text VARCHAR(255),
    similarity_score DECIMAL(5,2),
    link_type VARCHAR(50) DEFAULT 'string_match', -- 'string_match' | 'semantic'
    is_applied BOOLEAN DEFAULT false,
    applied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(from_post_id, to_post_id)
);

-- Add embedding column to articles table for semantic linking
-- Using 384 dimensions for all-MiniLM-L6-v2 model
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Add target_keywords column to articles if not exists
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS target_keywords TEXT[];

-- Indexes for internal_link_map
CREATE INDEX IF NOT EXISTS idx_internal_link_map_from_post ON internal_link_map(from_post_id);
CREATE INDEX IF NOT EXISTS idx_internal_link_map_to_post ON internal_link_map(to_post_id);
CREATE INDEX IF NOT EXISTS idx_internal_link_map_link_type ON internal_link_map(link_type);
CREATE INDEX IF NOT EXISTS idx_internal_link_map_is_applied ON internal_link_map(is_applied);

-- Index for embedding similarity search (using IVFFlat for performance)
-- This index enables efficient nearest neighbor searches
-- Note: lists=100 is optimized for ~100k rows. For larger datasets,
-- consider adjusting to lists = max(rows/1000, 10) for better performance
CREATE INDEX IF NOT EXISTS idx_articles_embedding 
ON articles USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Comments
COMMENT ON TABLE internal_link_map IS 'Mapping of internal links between published posts';
COMMENT ON COLUMN internal_link_map.from_post_id IS 'Post containing the link';
COMMENT ON COLUMN internal_link_map.to_post_id IS 'Post being linked to';
COMMENT ON COLUMN internal_link_map.anchor_text IS 'Text used for the link anchor';
COMMENT ON COLUMN internal_link_map.similarity_score IS 'Semantic similarity score if applicable';
COMMENT ON COLUMN internal_link_map.link_type IS 'How the link was determined: string_match or semantic';
COMMENT ON COLUMN internal_link_map.is_applied IS 'Whether the link has been applied to the source post';
COMMENT ON COLUMN internal_link_map.applied_at IS 'When the link was applied';
COMMENT ON COLUMN articles.embedding IS 'Sentence embedding vector for semantic similarity';
COMMENT ON COLUMN articles.target_keywords IS 'Target keywords for the article for linking';
