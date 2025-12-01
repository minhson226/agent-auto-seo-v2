-- Auto-SEO PostgreSQL Initialization Script
-- This script runs when PostgreSQL container is first started

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Note: pgvector extension requires separate installation
-- Uncomment below if pgvector is available in the image
-- CREATE EXTENSION IF NOT EXISTS "vector";

-- Create initial schema
CREATE SCHEMA IF NOT EXISTS autoseo;

-- Set default schema
SET search_path TO autoseo, public;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Auto-SEO PostgreSQL initialized successfully';
END $$;
