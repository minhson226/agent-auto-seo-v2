"""Diagnostics and system health endpoints."""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/v1/diagnostics", tags=["Diagnostics"])


async def check_service_health(service_name: str, service_url: str) -> Dict[str, Any]:
    """Check health of a single service."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = datetime.now()
            response = await client.get(f"{service_url}/health")
            end_time = datetime.now()
            
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": service_name,
                    "status": "healthy",
                    "url": service_url,
                    "response_time_ms": round(response_time_ms, 2),
                    "details": data,
                }
            else:
                return {
                    "name": service_name,
                    "status": "unhealthy",
                    "url": service_url,
                    "response_time_ms": round(response_time_ms, 2),
                    "error": f"HTTP {response.status_code}",
                }
    except httpx.TimeoutException:
        return {
            "name": service_name,
            "status": "timeout",
            "url": service_url,
            "error": "Request timeout after 5 seconds",
        }
    except Exception as e:
        return {
            "name": service_name,
            "status": "error",
            "url": service_url,
            "error": str(e),
        }


@router.get("", response_model=None)
@router.get("/", response_model=None)
async def get_diagnostics() -> Dict[str, Any]:
    """
    Get comprehensive system diagnostics.
    
    Returns health status of all microservices and system information.
    """
    # Define all services
    services = [
        ("API Gateway", "http://localhost:8080"),
        ("Auth Service", settings.AUTH_SERVICE_URL),
        ("Notification Service", settings.NOTIFICATION_SERVICE_URL),
        ("Keyword Ingestion", settings.KEYWORD_INGESTION_URL),
        ("SEO Strategy", settings.SEO_STRATEGY_URL),
        ("SEO Scorer", settings.SEO_SCORER_URL),
        ("Content Generator", settings.CONTENT_GENERATOR_URL),
        ("Analytics", settings.ANALYTICS_URL),
    ]
    
    # Check all services concurrently
    tasks = [check_service_health(name, url) for name, url in services]
    service_statuses = await asyncio.gather(*tasks)
    
    # Calculate overall status
    healthy_count = sum(1 for s in service_statuses if s["status"] == "healthy")
    total_count = len(service_statuses)
    
    if healthy_count == total_count:
        overall_status = "healthy"
    elif healthy_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    # Get environment info (non-sensitive)
    environment_info = {
        "environment": settings.APP_ENV,
        "debug_mode": settings.DEBUG,
        "log_level": settings.LOG_LEVEL,
        "cors_origins": settings.CORS_ORIGINS,
    }
    
    # Build info
    build_info = {
        "version": "1.0.0",
        "git_commit": os.getenv("GIT_COMMIT", "unknown"),
        "build_date": os.getenv("BUILD_DATE", "unknown"),
        "image_tag": os.getenv("IMAGE_TAG", "latest"),
    }
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": overall_status,
        "healthy_services": healthy_count,
        "total_services": total_count,
        "services": service_statuses,
        "environment": environment_info,
        "build": build_info,
    }


@router.get("/health-summary", response_model=None)
async def get_health_summary() -> Dict[str, Any]:
    """
    Get a quick health summary of all services.
    
    Simpler endpoint for basic health checks.
    """
    services = [
        ("auth", settings.AUTH_SERVICE_URL),
        ("notifications", settings.NOTIFICATION_SERVICE_URL),
        ("keywords", settings.KEYWORD_INGESTION_URL),
        ("strategy", settings.SEO_STRATEGY_URL),
        ("scorer", settings.SEO_SCORER_URL),
        ("content", settings.CONTENT_GENERATOR_URL),
        ("analytics", settings.ANALYTICS_URL),
    ]
    
    tasks = [check_service_health(name, url) for name, url in services]
    statuses = await asyncio.gather(*tasks)
    
    summary = {}
    for status in statuses:
        summary[status["name"]] = {
            "status": status["status"],
            "response_time_ms": status.get("response_time_ms"),
        }
    
    healthy = sum(1 for s in statuses if s["status"] == "healthy")
    
    return {
        "healthy": healthy,
        "total": len(statuses),
        "services": summary,
    }
