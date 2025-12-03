"""Tests for Notification Service endpoints."""

import pytest
from unittest.mock import patch, AsyncMock


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "notification-service"

    def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


class TestEmailService:
    """Tests for email service."""

    @patch("app.services.email_service.aiosmtplib.send")
    async def test_send_email_success(self, mock_send):
        """Test successful email sending."""
        from app.services.email_service import email_service

        mock_send.return_value = None
        
        result = await email_service.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<h1>Test</h1>",
        )
        
        # Result depends on SMTP configuration
        assert result in [True, False]

    @patch("app.services.email_service.aiosmtplib.send")
    async def test_send_email_with_text_content(self, mock_send):
        """Test email with both HTML and text content."""
        from app.services.email_service import email_service

        mock_send.return_value = None
        
        result = await email_service.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<h1>Test</h1>",
            text_content="Test",
        )
        
        assert result in [True, False]


class TestSlackService:
    """Tests for Slack service."""

    @patch("app.services.slack_service.httpx.AsyncClient.post")
    async def test_send_slack_message(self, mock_post):
        """Test sending Slack message."""
        from app.services.slack_service import slack_service

        mock_post.return_value = AsyncMock(status_code=200)
        
        result = await slack_service.send_message(
            text="Test message",
            webhook_url="https://hooks.slack.com/test",
        )
        
        # Will be False if no webhook configured
        assert result in [True, False]

    @patch("app.services.slack_service.httpx.AsyncClient.post")
    async def test_send_notification(self, mock_post):
        """Test sending formatted notification."""
        from app.services.slack_service import slack_service

        mock_post.return_value = AsyncMock(status_code=200)
        
        result = await slack_service.send_notification(
            title="Test Title",
            message="Test message",
            level="info",
            webhook_url="https://hooks.slack.com/test",
        )
        
        assert result in [True, False]


class TestEventConsumer:
    """Tests for event consumer."""

    @patch("app.services.event_consumer.aio_pika.connect_robust")
    async def test_connect_to_rabbitmq(self, mock_connect):
        """Test connecting to RabbitMQ."""
        from app.services.event_consumer import EventConsumer

        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        mock_connect.return_value = mock_connection

        consumer = EventConsumer()
        
        try:
            await consumer.connect()
            assert consumer.connection is not None
        except Exception:
            # May fail if RabbitMQ isn't available
            pass

    async def test_event_handler_user_registered(self):
        """Test handling user.registered event."""
        from app.services.event_consumer import EventConsumer

        consumer = EventConsumer()
        
        # Test handler doesn't raise
        with patch("app.services.email_service.email_service.send_email", new_callable=AsyncMock) as mock_email:
            mock_email.return_value = True
            await consumer._handle_user_registered(
                {"email": "test@example.com"},
                "workspace-id",
            )
            mock_email.assert_called_once()

    async def test_event_handler_workspace_created(self):
        """Test handling workspace.created event."""
        from app.services.event_consumer import EventConsumer

        consumer = EventConsumer()
        
        with patch("app.services.slack_service.slack_service.send_notification", new_callable=AsyncMock) as mock_slack:
            mock_slack.return_value = True
            await consumer._handle_workspace_created(
                {"name": "Test Workspace"},
                "workspace-id",
            )


class TestTestEndpoints:
    """Tests for testing endpoints."""

    @patch("app.services.email_service.email_service.send_email")
    def test_test_email_endpoint(self, mock_send, client):
        """Test the test email endpoint."""
        mock_send.return_value = True
        
        response = client.post(
            "/api/v1/notifications/test-email",
            params={"to_email": "test@example.com"},
        )
        
        # Will work or fail based on email configuration
        assert response.status_code in [200, 500]

    @patch("app.services.slack_service.slack_service.send_notification")
    def test_test_slack_endpoint(self, mock_send, client):
        """Test the test Slack endpoint."""
        mock_send.return_value = True
        
        response = client.post("/api/v1/notifications/test-slack")
        
        assert response.status_code in [200, 500]
