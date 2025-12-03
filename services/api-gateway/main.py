"""API Gateway - Main Application."""

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.core.config import get_settings
from app.core.proxy import proxy_service
from app.middleware.rate_limit import RateLimiter, RateLimitMiddleware
from app.middleware.logging import RequestLoggingMiddleware

settings = get_settings()

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Configure standard logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(message)s",
)
logger = logging.getLogger(__name__)


# Rate limiter instance
rate_limiter = RateLimiter(settings.REDIS_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting API Gateway...")
    yield
    # Shutdown
    logger.info("Shutting down API Gateway...")
    await proxy_service.close()
    await rate_limiter.close()


app = FastAPI(
    title=settings.APP_NAME,
    description="API Gateway for Auto-SEO Platform",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
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
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe endpoint."""
    return {"status": "ready", "service": "api-gateway"}


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    include_in_schema=False,
)
async def proxy_api(request: Request, path: str):
    """Proxy all /api/* requests to backend services."""
    return await proxy_service.proxy_request(request)
