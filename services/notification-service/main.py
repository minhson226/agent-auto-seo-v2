"""Notification Service - Main Application."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.core.config import get_settings
from app.services.event_consumer import event_consumer

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Notification Service...")

    # Connect to RabbitMQ and start consuming
    try:
        await event_consumer.connect()
        # Start consuming in background
        asyncio.create_task(event_consumer.start_consuming())
        logger.info("RabbitMQ consumer started")
    except Exception as e:
        logger.warning(f"Could not connect to RabbitMQ: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Notification Service...")
    await event_consumer.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    description="Notification Service for Auto-SEO Platform - Handles email, Slack, and in-app notifications",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness probe endpoint."""
    return {"status": "healthy", "service": "notification-service"}


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe endpoint."""
    return {"status": "ready", "service": "notification-service"}


@app.post("/api/v1/notifications/test-email", tags=["Testing"])
async def test_email(to_email: str, subject: str = "Test Email"):
    """Send a test email (for testing purposes only)."""
    from app.services.email_service import email_service

    success = await email_service.send_email(
        to_email=to_email,
        subject=subject,
        html_content="<html><body><h1>Test Email</h1><p>This is a test email from Auto-SEO Platform.</p></body></html>",
    )

    return {"success": success, "message": "Test email sent" if success else "Failed to send test email"}


@app.post("/api/v1/notifications/test-slack", tags=["Testing"])
async def test_slack(message: str = "Test notification from Auto-SEO Platform"):
    """Send a test Slack notification (for testing purposes only)."""
    from app.services.slack_service import slack_service

    success = await slack_service.send_notification(
        title="Test Notification",
        message=message,
        level="info",
    )

    return {"success": success, "message": "Slack notification sent" if success else "Failed to send Slack notification"}
