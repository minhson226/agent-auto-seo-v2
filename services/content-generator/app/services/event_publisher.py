"""Event publisher for RabbitMQ.

Supports both real RabbitMQ connections and mock mode for testing.
When RABBITMQ_URL is set to 'mock://' or connection fails gracefully,
events are logged but not actually published.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from decimal import Decimal

import aio_pika
from aio_pika import Message, ExchangeType

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EventPublisher:
    """Publisher for events to RabbitMQ.

    Supports mock mode for testing when RabbitMQ is not available.
    In mock mode, events are stored in memory for inspection during tests.

    Mock mode is enabled when:
    - mock_mode=True is passed to constructor, OR
    - RABBITMQ_URL starts with 'mock://'
    """

    EXCHANGE_NAME = "auto_seo.events"

    def __init__(self, mock_mode: bool = False):
        """Initialize the event publisher.

        Args:
            mock_mode: If True, operates in mock mode without real RabbitMQ connection.
                      Also enabled automatically when RABBITMQ_URL starts with 'mock://'.
        """
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        # Mock mode is enabled by parameter OR by URL prefix
        self._mock_mode = mock_mode or settings.RABBITMQ_URL.startswith("mock://")
        self._published_events: List[Dict[str, Any]] = []  # Store events in mock mode

    @property
    def mock_mode(self) -> bool:
        """Check if publisher is in mock mode."""
        return self._mock_mode

    @property
    def published_events(self) -> List[Dict[str, Any]]:
        """Get list of published events (for testing in mock mode)."""
        return self._published_events

    def clear_events(self) -> None:
        """Clear the list of published events (for testing)."""
        self._published_events = []

    async def connect(self):
        """Connect to RabbitMQ.

        In mock mode, this is a no-op that logs the mock status.
        """
        if self._mock_mode:
            logger.info("EventPublisher running in mock mode - no RabbitMQ connection")
            return

        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                self.EXCHANGE_NAME, ExchangeType.TOPIC, durable=True
            )
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Disconnect from RabbitMQ.

        In mock mode, this is a no-op.
        """
        if self._mock_mode:
            logger.info("EventPublisher mock mode - no disconnection needed")
            return

        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        workspace_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None,
    ):
        """Publish an event to RabbitMQ.

        In mock mode, events are stored in memory for later inspection during tests.
        """
        event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workspace_id": str(workspace_id) if workspace_id else None,
            "payload": self._serialize_payload(payload),
            "metadata": {
                "source_service": "content-generator",
                "correlation_id": correlation_id or str(uuid4()),
            },
        }

        if self._mock_mode:
            # In mock mode, store event for testing
            self._published_events.append(event)
            logger.info(f"Mock published event: {event_type}")
            return

        if not self.exchange:
            logger.warning("RabbitMQ not connected, skipping event publish")
            return

        message = Message(
            json.dumps(event).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self.exchange.publish(message, routing_key=event_type)
        logger.info(f"Published event: {event_type}")

    def _serialize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize payload, converting UUIDs, datetimes, and Decimals to strings."""
        result = {}
        for key, value in payload.items():
            if isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = self._serialize_payload(value)
            else:
                result[key] = value
        return result


# Global event publisher instance
event_publisher = EventPublisher()
