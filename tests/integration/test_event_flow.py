"""
Integration tests for event-driven workflows.
Tests the complete flow from keyword import to content generation.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone


class MockEventBus:
    """Mock event bus for testing event-driven flows."""
    
    def __init__(self):
        self.published_events = []
        self.subscriptions = {}
    
    async def publish(self, event_type: str, payload: dict, workspace_id=None):
        """Publish an event to the mock bus."""
        event = {
            "event_type": event_type,
            "payload": payload,
            "workspace_id": str(workspace_id) if workspace_id else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.published_events.append(event)
        
        # Trigger any subscribed handlers
        if event_type in self.subscriptions:
            for handler in self.subscriptions[event_type]:
                await handler(event)
    
    def subscribe(self, event_type: str, handler):
        """Subscribe to an event type."""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(handler)
    
    def get_events(self, event_type: str = None):
        """Get published events, optionally filtered by type."""
        if event_type:
            return [e for e in self.published_events if e["event_type"] == event_type]
        return self.published_events
    
    def clear(self):
        """Clear all published events."""
        self.published_events = []


class TestKeywordToContentFlow:
    """Tests for the complete keyword to content generation flow."""
    
    @pytest.fixture
    def event_bus(self):
        """Create a mock event bus for testing."""
        return MockEventBus()
    
    @pytest.mark.asyncio
    async def test_keyword_import_triggers_event(self, event_bus):
        """Test that importing keywords triggers the correct event."""
        list_id = str(uuid4())
        workspace_id = str(uuid4())
        
        await event_bus.publish(
            "keyword.list.imported",
            {
                "list_id": list_id,
                "keyword_count": 100,
                "source": "csv",
            },
            workspace_id=workspace_id,
        )
        
        events = event_bus.get_events("keyword.list.imported")
        assert len(events) == 1
        assert events[0]["payload"]["list_id"] == list_id
        assert events[0]["payload"]["keyword_count"] == 100
    
    @pytest.mark.asyncio
    async def test_cluster_creation_triggers_event(self, event_bus):
        """Test that creating a cluster triggers the correct event."""
        cluster_id = str(uuid4())
        workspace_id = str(uuid4())
        
        await event_bus.publish(
            "cluster.created",
            {
                "cluster_id": cluster_id,
                "name": "Test Cluster",
                "keyword_count": 10,
            },
            workspace_id=workspace_id,
        )
        
        events = event_bus.get_events("cluster.created")
        assert len(events) == 1
        assert events[0]["payload"]["cluster_id"] == cluster_id
    
    @pytest.mark.asyncio
    async def test_content_plan_creation_triggers_event(self, event_bus):
        """Test that creating a content plan triggers the correct event."""
        plan_id = str(uuid4())
        cluster_id = str(uuid4())
        workspace_id = str(uuid4())
        
        await event_bus.publish(
            "content.plan.created",
            {
                "plan_id": plan_id,
                "cluster_id": cluster_id,
                "title": "Test Article Plan",
                "priority": "high",
            },
            workspace_id=workspace_id,
        )
        
        events = event_bus.get_events("content.plan.created")
        assert len(events) == 1
        assert events[0]["payload"]["plan_id"] == plan_id
        assert events[0]["payload"]["priority"] == "high"
    
    @pytest.mark.asyncio
    async def test_article_generation_triggers_event(self, event_bus):
        """Test that article generation triggers the correct event."""
        article_id = str(uuid4())
        plan_id = str(uuid4())
        workspace_id = str(uuid4())
        
        await event_bus.publish(
            "article.generated",
            {
                "article_id": article_id,
                "plan_id": plan_id,
                "word_count": 1500,
                "model": "gpt-4",
            },
            workspace_id=workspace_id,
        )
        
        events = event_bus.get_events("article.generated")
        assert len(events) == 1
        assert events[0]["payload"]["article_id"] == article_id
        assert events[0]["payload"]["word_count"] == 1500
    
    @pytest.mark.asyncio
    async def test_seo_scoring_triggers_approval_event(self, event_bus):
        """Test that SEO scoring with high score triggers approval event."""
        article_id = str(uuid4())
        workspace_id = str(uuid4())
        
        # Simulate article scoring with high score
        await event_bus.publish(
            "article.scored",
            {
                "article_id": article_id,
                "score": 85,
                "feedback": [],
            },
            workspace_id=workspace_id,
        )
        
        # High score should trigger approval
        await event_bus.publish(
            "article.approved_for_publishing",
            {
                "article_id": article_id,
                "score": 85,
            },
            workspace_id=workspace_id,
        )
        
        events = event_bus.get_events("article.approved_for_publishing")
        assert len(events) == 1
        assert events[0]["payload"]["score"] >= 80
    
    @pytest.mark.asyncio
    async def test_low_score_triggers_regeneration_event(self, event_bus):
        """Test that low SEO score triggers regeneration request."""
        article_id = str(uuid4())
        workspace_id = str(uuid4())
        
        # Simulate article scoring with low score
        await event_bus.publish(
            "article.scored",
            {
                "article_id": article_id,
                "score": 60,
                "feedback": ["Missing meta description", "Low keyword density"],
            },
            workspace_id=workspace_id,
        )
        
        # Low score should trigger regeneration
        await event_bus.publish(
            "article.generate.request",
            {
                "article_id": article_id,
                "reason": "low_seo_score",
                "previous_score": 60,
            },
            workspace_id=workspace_id,
        )
        
        events = event_bus.get_events("article.generate.request")
        assert len(events) == 1
        assert events[0]["payload"]["reason"] == "low_seo_score"
    
    @pytest.mark.asyncio
    async def test_article_publishing_triggers_event(self, event_bus):
        """Test that article publishing triggers the correct event."""
        article_id = str(uuid4())
        workspace_id = str(uuid4())
        
        await event_bus.publish(
            "article.published",
            {
                "article_id": article_id,
                "site_id": str(uuid4()),
                "wordpress_post_id": 12345,
                "url": "https://example.com/test-article",
            },
            workspace_id=workspace_id,
        )
        
        events = event_bus.get_events("article.published")
        assert len(events) == 1
        assert events[0]["payload"]["wordpress_post_id"] == 12345
    
    @pytest.mark.asyncio
    async def test_complete_event_flow(self, event_bus):
        """Test complete event flow from keyword import to publishing."""
        workspace_id = str(uuid4())
        list_id = str(uuid4())
        cluster_id = str(uuid4())
        plan_id = str(uuid4())
        article_id = str(uuid4())
        
        # Step 1: Import keywords
        await event_bus.publish(
            "keyword.list.imported",
            {"list_id": list_id, "keyword_count": 50},
            workspace_id=workspace_id,
        )
        
        # Step 2: Create cluster
        await event_bus.publish(
            "cluster.created",
            {"cluster_id": cluster_id, "list_id": list_id},
            workspace_id=workspace_id,
        )
        
        # Step 3: Create content plan
        await event_bus.publish(
            "content.plan.created",
            {"plan_id": plan_id, "cluster_id": cluster_id},
            workspace_id=workspace_id,
        )
        
        # Step 4: Generate article
        await event_bus.publish(
            "article.generated",
            {"article_id": article_id, "plan_id": plan_id},
            workspace_id=workspace_id,
        )
        
        # Step 5: Score article
        await event_bus.publish(
            "article.scored",
            {"article_id": article_id, "score": 90},
            workspace_id=workspace_id,
        )
        
        # Step 6: Approve for publishing
        await event_bus.publish(
            "article.approved_for_publishing",
            {"article_id": article_id},
            workspace_id=workspace_id,
        )
        
        # Step 7: Publish
        await event_bus.publish(
            "article.published",
            {"article_id": article_id, "url": "https://example.com/article"},
            workspace_id=workspace_id,
        )
        
        # Verify complete flow
        assert len(event_bus.get_events("keyword.list.imported")) == 1
        assert len(event_bus.get_events("cluster.created")) == 1
        assert len(event_bus.get_events("content.plan.created")) == 1
        assert len(event_bus.get_events("article.generated")) == 1
        assert len(event_bus.get_events("article.scored")) == 1
        assert len(event_bus.get_events("article.approved_for_publishing")) == 1
        assert len(event_bus.get_events("article.published")) == 1


class TestEventSubscriptions:
    """Tests for event subscription functionality."""
    
    @pytest.fixture
    def event_bus(self):
        return MockEventBus()
    
    @pytest.mark.asyncio
    async def test_event_handler_is_called(self, event_bus):
        """Test that subscribed handlers are called on event publish."""
        received_events = []
        
        async def handler(event):
            received_events.append(event)
        
        event_bus.subscribe("test.event", handler)
        
        await event_bus.publish("test.event", {"data": "test"})
        
        assert len(received_events) == 1
        assert received_events[0]["payload"]["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_multiple_handlers(self, event_bus):
        """Test that multiple handlers are called for same event."""
        results = []
        
        async def handler1(event):
            results.append("handler1")
        
        async def handler2(event):
            results.append("handler2")
        
        event_bus.subscribe("test.event", handler1)
        event_bus.subscribe("test.event", handler2)
        
        await event_bus.publish("test.event", {})
        
        assert "handler1" in results
        assert "handler2" in results
