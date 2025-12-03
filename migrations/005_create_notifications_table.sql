-- Migration: Create Notifications Table
-- Version: 005
-- Description: Notifications storage for email, Slack, and in-app notifications

SET search_path TO autoseo, public;

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('email', 'slack', 'in_app')),
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_workspace_id ON notifications(workspace_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Index for pending notifications (for retry processing)
CREATE INDEX IF NOT EXISTS idx_notifications_pending ON notifications(status, retry_count)
    WHERE status = 'pending';

-- Comments
COMMENT ON TABLE notifications IS 'Notification records for all notification types';
COMMENT ON COLUMN notifications.type IS 'Notification delivery channel: email, slack, or in_app';
COMMENT ON COLUMN notifications.status IS 'Delivery status: pending, sent, or failed';
COMMENT ON COLUMN notifications.retry_count IS 'Number of delivery retry attempts';
