"""SEO Strategy Service - Main Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.services.event_publisher import event_publisher

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
    logger.info("Starting SEO Strategy Service...")

    # Connect to RabbitMQ
    try:
        await event_publisher.connect()
    except Exception as e:
        logger.warning(f"Could not connect to RabbitMQ: {e}")

    yield

    # Shutdown
    logger.info("Shutting down SEO Strategy Service...")
    await event_publisher.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    description="SEO Strategy & Planning Engine for Auto-SEO Platform",
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

# Include API router
app.include_router(api_router)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness probe endpoint."""
    return {"status": "healthy", "service": "seo-strategy"}


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe endpoint."""
    # Could add database connectivity check here
    return {"status": "ready", "service": "seo-strategy"}
