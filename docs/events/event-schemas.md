# Event Schemas Documentation

This document describes the event message formats used in the Auto-SEO Platform's event-driven architecture.

## Overview

The Auto-SEO Platform uses RabbitMQ as its message broker with a topic exchange pattern. All events are published to the `auto_seo.events` exchange and routed based on their event type.

## Message Format

All events follow this standard format:

```json
{
  "event_type": "string",
  "timestamp": "ISO 8601 datetime string",
  "workspace_id": "UUID or null",
  "payload": {
    // Event-specific data
  },
  "metadata": {
    "source_service": "string",
    "correlation_id": "UUID"
  }
}
```

### Fields Description

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | Yes | The type of event, used as the routing key |
| `timestamp` | string | Yes | ISO 8601 formatted timestamp |
| `workspace_id` | UUID | No | The workspace context for the event |
| `payload` | object | Yes | Event-specific data |
| `metadata.source_service` | string | Yes | Name of the service that published the event |
| `metadata.correlation_id` | UUID | Yes | Unique ID for request tracing |

## Core Events

### Authentication Events

#### user.registered

Published when a new user successfully registers.

```json
{
  "event_type": "user.registered",
  "timestamp": "2025-11-23T14:00:00Z",
  "workspace_id": null,
  "payload": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  },
  "metadata": {
    "source_service": "auth-service",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440001"
  }
}
```

### Workspace Events

#### workspace.created

Published when a new workspace is created.

```json
{
  "event_type": "workspace.created",
  "timestamp": "2025-11-23T14:00:00Z",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440002",
  "payload": {
    "workspace_id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "My Workspace",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "metadata": {
    "source_service": "auth-service",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440003"
  }
}
```

### Site Events

#### site.created

Published when a new site is added to a workspace.

```json
{
  "event_type": "site.created",
  "timestamp": "2025-11-23T14:00:00Z",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440002",
  "payload": {
    "site_id": "550e8400-e29b-41d4-a716-446655440004",
    "name": "My Blog",
    "domain": "myblog.com"
  },
  "metadata": {
    "source_service": "auth-service",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440005"
  }
}
```

### Content Events

#### article.published

Published when an article is successfully published to a site.

```json
{
  "event_type": "article.published",
  "timestamp": "2025-11-23T14:00:00Z",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440002",
  "payload": {
    "article_id": "550e8400-e29b-41d4-a716-446655440006",
    "title": "10 SEO Tips for 2025",
    "url": "https://myblog.com/seo-tips-2025",
    "site_id": "550e8400-e29b-41d4-a716-446655440004"
  },
  "metadata": {
    "source_service": "publishing-service",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440007"
  }
}
```

### Job Events

#### job.failed

Published when a background job fails.

```json
{
  "event_type": "job.failed",
  "timestamp": "2025-11-23T14:00:00Z",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440002",
  "payload": {
    "job_id": "550e8400-e29b-41d4-a716-446655440008",
    "job_type": "article_generation",
    "error": "OpenAI API rate limit exceeded",
    "retry_count": 3
  },
  "metadata": {
    "source_service": "content-service",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440009"
  }
}
```

### Notification Events

#### notification.requested

Published when a notification needs to be sent.

```json
{
  "event_type": "notification.requested",
  "timestamp": "2025-11-23T14:00:00Z",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440002",
  "payload": {
    "type": "email",
    "recipient": "user@example.com",
    "title": "Your article is ready",
    "message": "Your article 'SEO Tips' has been generated and is ready for review.",
    "level": "info"
  },
  "metadata": {
    "source_service": "content-service",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440010"
  }
}
```

## RabbitMQ Configuration

### Exchange

- **Name**: `auto_seo.events`
- **Type**: Topic
- **Durable**: Yes

### Queue Bindings

Each service subscribes to relevant events by binding to specific routing keys:

| Service | Queue Name | Subscribed Events |
|---------|------------|-------------------|
| notification-service | notification-service | user.registered, workspace.created, site.created, article.published, job.failed, notification.requested |

## Publishing Events

To publish an event, use the `EventPublisher` class:

```python
from app.services.event_publisher import event_publisher

await event_publisher.publish(
    event_type="user.registered",
    payload={"user_id": str(user.id), "email": user.email},
    workspace_id=None,  # Optional
    correlation_id=None,  # Auto-generated if not provided
)
```

## Best Practices

1. **Always include correlation_id**: This enables request tracing across services.
2. **Keep payloads minimal**: Include only necessary data; consumers can fetch details if needed.
3. **Use consistent event naming**: Follow the format `entity.action` (e.g., `user.registered`, `article.published`).
4. **Handle failures gracefully**: Implement retry mechanisms with exponential backoff.
5. **Log event processing**: Log both successful processing and failures for debugging.
