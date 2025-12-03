"""Event publisher for RabbitMQ."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import aio_pika
from aio_pika import Message, ExchangeType

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EventPublisher:
    """Publisher for events to RabbitMQ."""

    EXCHANGE_NAME = "auto_seo.events"

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None

    async def connect(self):
        """Connect to RabbitMQ."""
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
        """Disconnect from RabbitMQ."""
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
        """Publish an event to RabbitMQ."""
        if not self.exchange:
            logger.warning("RabbitMQ not connected, skipping event publish")
            return

        event = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workspace_id": str(workspace_id) if workspace_id else None,
            "payload": self._serialize_payload(payload),
            "metadata": {
                "source_service": "keyword-ingestion",
                "correlation_id": correlation_id or str(uuid4()),
            },
        }

        message = Message(
            json.dumps(event).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self.exchange.publish(message, routing_key=event_type)
        logger.info(f"Published event: {event_type}")

    def _serialize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize payload, converting UUIDs and datetimes to strings."""
        result = {}
        for key, value in payload.items():
            if isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = self._serialize_payload(value)
            else:
                result[key] = value
        return result


# Global event publisher instance
event_publisher = EventPublisher()
