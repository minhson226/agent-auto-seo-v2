"""Event consumer for processing RabbitMQ messages."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict

import aio_pika
from aio_pika import IncomingMessage

from app.core.config import get_settings
from app.services.email_service import email_service
from app.services.slack_service import slack_service

logger = logging.getLogger(__name__)
settings = get_settings()


class EventConsumer:
    """Consumer for RabbitMQ events."""

    EXCHANGE_NAME = "auto_seo.events"
    QUEUE_NAME = "notification-service"

    # Event types to listen for
    SUBSCRIBED_EVENTS = [
        "user.registered",
        "workspace.created",
        "site.created",
        "article.published",
        "job.failed",
        "notification.requested",
    ]

    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None

    async def connect(self):
        """Connect to RabbitMQ and set up queue."""
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()

            # Declare exchange
            exchange = await self.channel.declare_exchange(
                self.EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
            )

            # Declare queue
            self.queue = await self.channel.declare_queue(
                self.QUEUE_NAME, durable=True
            )

            # Bind queue to exchange for each event type
            for event_type in self.SUBSCRIBED_EVENTS:
                await self.queue.bind(exchange, routing_key=event_type)
                logger.info(f"Subscribed to event: {event_type}")

            logger.info("Connected to RabbitMQ")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def start_consuming(self):
        """Start consuming messages from the queue."""
        if not self.queue:
            raise RuntimeError("Not connected to RabbitMQ")

        await self.queue.consume(self._process_message)
        logger.info("Started consuming messages")

    async def _process_message(self, message: IncomingMessage):
        """Process an incoming message."""
        async with message.process():
            try:
                event = json.loads(message.body.decode())
                event_type = event.get("event_type")
                payload = event.get("payload", {})
                workspace_id = event.get("workspace_id")

                logger.info(f"Processing event: {event_type}")

                await self._handle_event(event_type, payload, workspace_id)

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Message will be acknowledged despite error to prevent infinite retry
                # In production, consider implementing dead letter queue

    async def _handle_event(
        self, event_type: str, payload: Dict[str, Any], workspace_id: str
    ):
        """Handle a specific event type."""
        handlers = {
            "user.registered": self._handle_user_registered,
            "workspace.created": self._handle_workspace_created,
            "site.created": self._handle_site_created,
            "article.published": self._handle_article_published,
            "job.failed": self._handle_job_failed,
            "notification.requested": self._handle_notification_requested,
        }

        handler = handlers.get(event_type)
        if handler:
            await handler(payload, workspace_id)
        else:
            logger.warning(f"No handler for event type: {event_type}")

    async def _handle_user_registered(self, payload: Dict[str, Any], workspace_id: str):
        """Handle user registration event."""
        email = payload.get("email")
        if email:
            logger.info(f"Sending welcome email to {email}")
            await email_service.send_email(
                to_email=email,
                subject="Welcome to Auto-SEO Platform",
                html_content=f"""
                <html>
                <body>
                    <h1>Welcome to Auto-SEO!</h1>
                    <p>Thank you for registering. Your account is now active.</p>
                    <p>Get started by creating your first workspace.</p>
                </body>
                </html>
                """,
            )

    async def _handle_workspace_created(
        self, payload: Dict[str, Any], workspace_id: str
    ):
        """Handle workspace creation event."""
        name = payload.get("name")
        logger.info(f"Workspace created: {name}")

        # Send Slack notification if configured
        if settings.SLACK_WEBHOOK_URL:
            await slack_service.send_notification(
                title="New Workspace Created",
                message=f"Workspace '{name}' has been created.",
                level="success",
            )

    async def _handle_site_created(self, payload: Dict[str, Any], workspace_id: str):
        """Handle site creation event."""
        name = payload.get("name")
        domain = payload.get("domain")
        logger.info(f"Site created: {name} ({domain})")

    async def _handle_article_published(
        self, payload: Dict[str, Any], workspace_id: str
    ):
        """Handle article published event."""
        title = payload.get("title")
        url = payload.get("url")
        logger.info(f"Article published: {title}")

        if settings.SLACK_WEBHOOK_URL:
            await slack_service.send_notification(
                title="Article Published",
                message=f"'{title}' has been published. View it at {url}",
                level="success",
            )

    async def _handle_job_failed(self, payload: Dict[str, Any], workspace_id: str):
        """Handle job failure event."""
        job_id = payload.get("job_id")
        error = payload.get("error")
        logger.error(f"Job failed: {job_id} - {error}")

        if settings.SLACK_WEBHOOK_URL:
            await slack_service.send_notification(
                title="Job Failed",
                message=f"Job {job_id} failed with error: {error}",
                level="error",
            )

    async def _handle_notification_requested(
        self, payload: Dict[str, Any], workspace_id: str
    ):
        """Handle explicit notification request."""
        notification_type = payload.get("type", "email")
        recipient = payload.get("recipient")
        title = payload.get("title")
        message = payload.get("message")

        if notification_type == "email" and recipient:
            await email_service.send_email(
                to_email=recipient,
                subject=title,
                html_content=f"<html><body>{message}</body></html>",
            )
        elif notification_type == "slack":
            await slack_service.send_notification(
                title=title,
                message=message,
                level=payload.get("level", "info"),
            )


# Global event consumer instance
event_consumer = EventConsumer()
